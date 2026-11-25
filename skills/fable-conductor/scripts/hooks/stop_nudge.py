"""Stop hook: once per batch of new ledger rows, ask the model to rate them and sync the dashboard."""

import json
import sys

import hooklib as h


def main(payload, cdir):
    if payload.get("stop_hook_active"):
        return
    try:
        cfg = json.loads((cdir / "config.json").read_text(encoding="utf-8"))
        if isinstance(cfg, dict) and cfg.get("nudge") is False:
            return
    except (OSError, ValueError):
        pass
    lines = h.ledger_lines(cdir)
    if lines is None:
        return
    total = len(lines)
    state = h.read_state(cdir)
    if total <= state.get("nudged_lines", 0):
        return
    state["nudged_lines"] = total
    h.write_state(cdir, state)
    unrated = h.count_unrated(lines)
    dashboard = (cdir / "dashboard.md").is_file() and total > state.get("synced_lines", 0)
    if not unrated and not dashboard:
        return
    reason = "Conductor housekeeping (one short step, then stop; do not start other work): "
    if unrated:
        reason += (
            f"rate the {unrated} unrated dispatches shown by "
            "`python3 .claude/conductor/ledger.py unrated`, judging for each whether its "
            "result was accepted first time (pass), after correction (rework), after "
            "moving to a stronger model (escalated) or not at all (fail): "
            "`python3 .claude/conductor/ledger.py rate --agent-id ID --outcome <value>`. "
        )
    if dashboard:
        reason += (
            "Then run `python3 .claude/conductor/ledger.py export-store`, and write each "
            "printed line, which is a JSON list, as the `writes` of one ArtifactData batch "
            "call to the dashboard address in .claude/conductor/dashboard.md."
        )
    h.emit({"decision": "block", "reason": reason.rstrip()})


if __name__ == "__main__":
    sys.exit(h.run_hook(main))
