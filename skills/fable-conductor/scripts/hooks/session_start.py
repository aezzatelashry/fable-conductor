"""SessionStart hook: show that the conductor is on and brief the model."""

import sys

import hooklib as h

LIMIT = 3000
INTRO = (
    "fable-conductor is installed in this project. Use its skill for any request with "
    "two or more substantial pieces, on your own. If the user's first message is not a "
    "concrete task (a greeting, 'continue', something vague) show the menu from the "
    "skill's references/menu.md as pick-an-option choices. Subagent runs are logged "
    "automatically by a hook: do not log them by hand; rate them with "
    "`python3 .claude/conductor/ledger.py rate --agent-id ID --outcome "
    "pass|rework|escalated|fail` when you have judged them."
)
OWNER_HEAD = "Owner profile (follow without being reminded):"


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def newest_within(lines, cap):
    kept, size = [], 0
    for line in reversed(lines):
        if size + len(line) + 1 > cap:
            break
        kept.append(line)
        size += len(line) + 1
    return list(reversed(kept))


def main(payload, cdir):
    version_file = cdir / "hooks" / "VERSION"
    if not version_file.is_file():
        return
    version = read(version_file).strip() or "?"
    lines = h.ledger_lines(cdir) or []
    total = len(h.ledger_rows(lines))
    unrated = h.count_unrated(lines)
    msg = f"المايسترو شغّال هنا · الإصدار {h.ltr(version)} · {h.ltr(total)} تكليف مسجّل"
    if unrated:
        msg += f", {h.ltr(unrated)} بدون تقييم"

    parts = [INTRO]
    lessons = [x.strip() for x in read(cdir / "lessons.md").splitlines() if x.strip()]
    if lessons:
        tail = newest_within(lessons[-5:], 500)
        if tail:
            parts.append("Project lessons:\n" + "\n".join(tail))
    if unrated:
        parts.append(f"Unrated dispatches: {unrated} (run `python3 .claude/conductor/ledger.py unrated`)")
    owner = [x.rstrip() for x in read(cdir / "owner.md").splitlines() if x.startswith("- ")]
    budget = min(2000, LIMIT - len("\n\n".join(parts)) - len(OWNER_HEAD) - 4)
    kept = newest_within(owner, budget) if budget > 0 else []
    if kept:
        parts.insert(1, OWNER_HEAD + "\n" + "\n".join(kept))
    context = "\n\n".join(parts)[:LIMIT]
    h.emit(
        {
            "systemMessage": msg,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            },
        }
    )


if __name__ == "__main__":
    sys.exit(h.run_hook(main))
