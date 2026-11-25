#!/usr/bin/env python3
"""Prepare a project for the fable-conductor skill.

  setup.py plan  [--project DIR]   print what apply would do, change nothing
  setup.py apply [--project DIR]   do it
  add --rules to either to include the rules-file line
add --hooks to also install the deterministic hooks (copies scripts/hooks/*.py and
ledger.py into <project>/.claude/conductor/, writes hooks/VERSION, merges the hook and
status-line entries into <project>/.claude/settings.json); --update-hooks (implies
--hooks) overwrites the copied scripts and VERSION. Settings entries are only added.

Installs the agent definitions from <skill>/assets/agents/ into
<project>/.claude/agents/ and creates <project>/.claude/conductor/lessons.md.
With --rules it also appends a short section to the project's CLAUDE.md
(.claude/CLAUDE.md, else CLAUDE.md, else a new .claude/CLAUDE.md) unless the
file already mentions the skill. Never deletes or overwrites an existing file;
the rules file is only ever appended to.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from ledger import project_root

SKILL_DIR = Path(__file__).resolve().parent.parent
LESSONS = (
    "# Conductor lessons for this project\n\n"
    "One line per lesson, dated, with its evidence. "
    "Read at the start of every fable-conductor run.\n"
)


RULES_MARK = "fable-conductor"
RULES = (
    "\n## Multi-piece work\n\n"
    "- Run any task with two or more substantial pieces through the `fable-conductor` skill, "
    "on your own and without waiting for a command: the main model plans, briefs, verifies and "
    "integrates; subagents execute.\n"
    "- Ask for the owner's decisions as pick-an-option questions, recommendation first.\n"
    "- When a session opens with anything other than a concrete task, show the skill's menu as "
    "pick-an-option choices; end every run with next-step choices.\n"
    "- Project lessons: `.claude/conductor/lessons.md`. Dispatch ledger: `.claude/conductor/ledger.jsonl`.\n"
    "- The rules in this file outrank the skill.\n"
)


HOOK_EVENTS = (
    ("SessionStart", "session_start"),
    ("SubagentStop", "subagent_stop"),
    ("Stop", "stop_nudge"),
)


def skill_version():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^\s+version:\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
    return m.group(1) if m else "?"


def hook_command(name):
    path = f'"$CLAUDE_PROJECT_DIR/.claude/conductor/hooks/{name}.py"'
    return f"python3 {path} || python {path}"


def load_settings(project):
    """(path, settings dict or None if absent); ValueError if present but unusable."""
    path = project / ".claude" / "settings.json"
    if not path.exists():
        return path, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{path} is not valid JSON ({e}); nothing changed") from e
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError(  # noqa: TRY004
            f"{path} has an unexpected shape; nothing changed"
        )
    return path, data


def merge_settings(data):
    """Add our entries to data in place; return the list of what was added."""
    added = []
    hooks = data.setdefault("hooks", {})
    for event, name in HOOK_EVENTS:
        entries = hooks.get(event)
        if not isinstance(entries, list):
            entries = hooks[event] = [] if entries is None else entries
        if not isinstance(entries, list):
            continue
        mark = f".claude/conductor/hooks/{name}.py"
        present = any(
            mark in str(h.get("command", ""))
            for e in entries
            if isinstance(e, dict)
            for h in (e.get("hooks") if isinstance(e.get("hooks"), list) else [])
            if isinstance(h, dict)
        )
        if not present:
            entries.append(
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(name),
                            "timeout": 10,
                        }
                    ]
                }
            )
            added.append(event)
    if "statusLine" not in data:
        data["statusLine"] = {"type": "command", "command": hook_command("statusline")}
        added.append("statusLine")
    if not data["hooks"]:
        del data["hooks"]
    return added


def run(project, apply, rules=False, hooks=False, update=False):
    prefix = "" if apply else "would: "
    counts = {"installed": 0, "unchanged": 0, "kept existing (differs)": 0}

    def report(status, what):
        counts[status] += 1
        print(f"{prefix}{status}: {what}")

    for src in sorted((SKILL_DIR / "assets" / "agents").glob("*.md")):
        dest = project / ".claude" / "agents" / src.name
        if dest.exists():
            same = dest.is_file() and dest.read_bytes() == src.read_bytes()
            report("unchanged" if same else "kept existing (differs)", dest)
        else:
            if apply:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
            report("installed", dest)

    lessons = project / ".claude" / "conductor" / "lessons.md"
    if lessons.exists():
        report("unchanged", lessons)
    else:
        if apply:
            lessons.parent.mkdir(parents=True, exist_ok=True)
            with lessons.open("x", encoding="utf-8", newline="") as f:
                f.write(LESSONS)
        report("installed", lessons)

    if rules:
        candidates = [project / ".claude" / "CLAUDE.md", project / "CLAUDE.md"]
        target = next((c for c in candidates if c.is_file()), candidates[0])
        if target.is_file() and RULES_MARK in target.read_text(encoding="utf-8"):
            report("unchanged", target)
        else:
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("a", encoding="utf-8", newline="") as f:
                    f.write(RULES)
            report("installed", f"{target} (rule appended)")

    if hooks:
        install_hooks(project, apply, update, report)

    print(
        f"{prefix}summary: {counts['installed']} installed, "
        f"{counts['unchanged']} unchanged, "
        f"{counts['kept existing (differs)']} kept existing (differs)"
    )


def install_hooks(project, apply, update, report):
    cdir = project / ".claude" / "conductor"
    sources = [(p, cdir / "hooks" / p.name) for p in sorted((SKILL_DIR / "scripts" / "hooks").glob("*.py"))]
    sources.append((SKILL_DIR / "scripts" / "ledger.py", cdir / "ledger.py"))
    version = (skill_version() + "\n").encode()
    for src, dest in sources:
        copy_file(src.read_bytes(), dest, apply, update, report)
    copy_file(version, cdir / "hooks" / "VERSION", apply, update, report)

    path, data = load_settings(project)
    fresh = data is None
    data = {} if fresh else data
    added = merge_settings(data)
    if not added:
        report("unchanged", path)
        return
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report("installed", f"{path} ({', '.join(added)})")


def copy_file(content, dest, apply, update, report):
    if dest.exists():
        same = dest.is_file() and dest.read_bytes() == content
        if same:
            report("unchanged", dest)
            return
        if not update:
            report("kept existing (differs)", dest)
            return
        what = f"{dest} (updated)"
    else:
        what = dest
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    report("installed", what)


def main():
    p = argparse.ArgumentParser(description="fable-conductor project setup")
    p.add_argument("cmd", choices=("plan", "apply"))
    p.add_argument("--project", help="project directory (default: git root or cwd)")
    p.add_argument(
        "--rules",
        action="store_true",
        help="also append a short rule to the project's CLAUDE.md so the skill starts on its own",
    )
    p.add_argument(
        "--hooks",
        action="store_true",
        help="install the hooks, status line and ledger copy into the project",
    )
    p.add_argument(
        "--update-hooks",
        action="store_true",
        help="like --hooks, and overwrite changed hook scripts, ledger.py and VERSION",
    )
    a = p.parse_args()
    project = Path(a.project) if a.project else project_root()
    if not project.is_dir():
        print(f"not a directory: {project}", file=sys.stderr)
        return 2
    hooks = a.hooks or a.update_hooks
    if hooks:
        try:
            load_settings(project)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
    run(project, a.cmd == "apply", a.rules, hooks, a.update_hooks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
