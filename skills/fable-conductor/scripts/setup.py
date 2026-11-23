#!/usr/bin/env python3
"""Prepare a project for the fable-conductor skill.

  setup.py plan  [--project DIR]   print what apply would do, change nothing
  setup.py apply [--project DIR]   do it
  add --rules to either to include the rules-file line

Installs the agent definitions from <skill>/assets/agents/ into
<project>/.claude/agents/ and creates <project>/.claude/conductor/lessons.md.
With --rules it also appends a short section to the project's CLAUDE.md
(.claude/CLAUDE.md, else CLAUDE.md, else a new .claude/CLAUDE.md) unless the
file already mentions the skill. Never deletes or overwrites an existing file;
the rules file is only ever appended to.
"""

import argparse
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


def run(project, apply, rules=False):
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

    print(
        f"{prefix}summary: {counts['installed']} installed, "
        f"{counts['unchanged']} unchanged, "
        f"{counts['kept existing (differs)']} kept existing (differs)"
    )


def main():
    p = argparse.ArgumentParser(description="fable-conductor project setup")
    p.add_argument("cmd", choices=("plan", "apply"))
    p.add_argument("--project", help="project directory (default: git root or cwd)")
    p.add_argument(
        "--rules",
        action="store_true",
        help="also append a short rule to the project's CLAUDE.md so the skill starts on its own",
    )
    a = p.parse_args()
    project = Path(a.project) if a.project else project_root()
    if not project.is_dir():
        print(f"not a directory: {project}", file=sys.stderr)
        return 2
    run(project, a.cmd == "apply", a.rules)
    return 0


if __name__ == "__main__":
    sys.exit(main())
