#!/usr/bin/env python3
"""Dispatch ledger for fable-conductor.

  ledger.py add --model sonnet --role builder --tokens 48211 \
      --duration-ms 93000 --outcome pass --task "users import endpoint" [--kind implement]
  ledger.py report [--last N] [--json] [--file F | --all DIR]

The ledger lives at <project>/.claude/conductor/ledger.jsonl, where <project> is the
git root of the current directory (or the current directory). Override with --file
or CONDUCTOR_LEDGER. It records subagent dispatches only; the conductor's own token
use is not visible to this script.
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

OUTCOMES = ("pass", "rework", "escalated", "fail")
TIERS = ("haiku", "sonnet", "opus", "fable")
MIN_SAMPLE = 4  # dispatches before a rate means anything
REWORK_LIMIT = 0.30  # above this, route up or fix the brief
SMALL_TOKENS = 25_000  # an Opus dispatch this small that passed first time may be over-routed


def project_root():
    """Git root of the current directory, or the current directory."""
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        root = os.getcwd()
    return Path(root)


def ledger_path(arg):
    if arg:
        return Path(arg)
    if os.environ.get("CONDUCTOR_LEDGER"):
        return Path(os.environ["CONDUCTOR_LEDGER"])
    return project_root() / ".claude" / "conductor" / "ledger.jsonl"


def cmd_add(a):
    path = ledger_path(a.file)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "model": a.model.lower(),
        "role": a.role.lower(),
        "kind": (a.kind or a.role).lower(),
        "tokens": a.tokens,
        "duration_ms": a.duration_ms,
        "outcome": a.outcome,
        "task": a.task,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"logged: {row['model']}/{row['role']} {row['outcome']} {row['tokens']} tok -> {path}")


def load(path, last):
    if not path.exists():
        return [], 0
    rows, bad = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return (rows[-last:] if last else rows), bad


def summarise(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r.get("model", "?"), r.get("kind") or r.get("role", "?"))].append(r)
    out = []
    for (model, kind), rs in sorted(groups.items()):
        n = len(rs)
        counts = {o: sum(1 for r in rs if r.get("outcome") == o) for o in OUTCOMES}
        tokens = sum(int(r.get("tokens") or 0) for r in rs)
        out.append(
            {
                "model": model,
                "kind": kind,
                "n": n,
                **counts,
                "tokens": tokens,
                "avg_tokens": tokens // n,
                "first_pass_rate": round(counts["pass"] / n, 2),
            }
        )
    return out


def flags(summary):
    notes = []
    for s in summary:
        if s["n"] < MIN_SAMPLE:
            continue
        label = f"{s['model']} on '{s['kind']}'"
        not_first = 1 - s["first_pass_rate"]
        if not_first > REWORK_LIMIT:
            notes.append(
                f"UNDER-ROUTED or weak briefs: {label} passed first time only "
                f"{s['pass']}/{s['n']}. Route this kind up a tier, or fix its brief template."
            )
        if s["model"] == "opus" and s["first_pass_rate"] == 1 and s["avg_tokens"] < SMALL_TOKENS:
            notes.append(
                f"POSSIBLY OVER-ROUTED: {label} passed {s['n']}/{s['n']} first time at "
                f"~{s['avg_tokens']} tokens each. Try Sonnet for this kind and compare."
            )
        if (
            s["model"] == "sonnet"
            and s["first_pass_rate"] == 1
            and s["kind"] in ("runner", "scout", "search", "extract", "summarise", "summarize")
        ):
            notes.append(f"POSSIBLY OVER-ROUTED: {label} is mechanical work passing every time. Try Haiku.")
    return notes


def load_all(base, last):
    """Rows from every ledger in base and its immediate subdirectories."""
    base = Path(base)
    candidates = [base] + sorted(d for d in base.iterdir() if d.is_dir())
    rows, bad, found = [], 0, 0
    for d in candidates:
        f = d / ".claude" / "conductor" / "ledger.jsonl"
        if not f.is_file():
            continue
        found += 1
        got, b = load(f, 0)
        bad += b
        name = d.resolve().name
        for r in got:
            r["project"] = name
        rows.extend(got)
    return (rows[-last:] if last else rows), bad, found


def by_project(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r.get("project", "?")].append(r)
    return [
        {
            "project": name,
            "dispatches": len(rs),
            "tokens": sum(int(r.get("tokens") or 0) for r in rs),
            "first_pass": sum(1 for r in rs if r.get("outcome") == "pass"),
        }
        for name, rs in sorted(groups.items())
    ]


def cmd_report(a):
    projects = None
    if a.all:
        base = Path(a.all)
        if not base.is_dir():
            print(f"not a directory: {base}", file=sys.stderr)
            return 2
        path = base
        rows, bad, found = load_all(base, a.last)
        if not found:
            print(f"no ledgers found under {base}")
            return 0
        projects = by_project(rows)
    else:
        path = ledger_path(a.file)
        rows, bad = load(path, a.last)
    if not rows:
        print(f"no dispatches recorded at {path}")
        return
    summary = summarise(rows)
    notes = flags(summary)
    by_tier = defaultdict(lambda: {"n": 0, "tokens": 0})
    for r in rows:
        t = by_tier[r.get("model", "?")]
        t["n"] += 1
        t["tokens"] += int(r.get("tokens") or 0)
    total_tokens = sum(t["tokens"] for t in by_tier.values())
    passed = sum(1 for r in rows if r.get("outcome") == "pass")

    if a.json:
        out = {
            "ledger": str(path),
            "dispatches": len(rows),
            "unreadable_lines": bad,
            "total_tokens": total_tokens,
            "first_pass_rate": round(passed / len(rows), 2),
            "by_tier": by_tier,
            "by_kind": summary,
            "flags": notes,
            "rows": rows[-50:],
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        if projects is not None:
            out["by_project"] = projects
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"ledger: {path}")
    print(f"dispatches: {len(rows)}   subagent tokens: {total_tokens:,}   first-time pass: {passed}/{len(rows)}")
    if bad:
        print(f"warning: {bad} unreadable line(s) skipped")
    if projects is not None:
        print("\nby project")
        print(f"  {'project':<20} {'dispatches':>10} {'tokens':>10} {'first-time pass':>16}")
        for p in projects:
            print(
                f"  {p['project']:<20} {p['dispatches']:>10} {p['tokens']:>10,} {p['first_pass']:>9}/{p['dispatches']}"
            )
    print("\nby tier")
    order = {t: i for i, t in enumerate(TIERS)}
    for tier, t in sorted(by_tier.items(), key=lambda kv: order.get(kv[0], 99)):
        share = (100 * t["tokens"] // total_tokens) if total_tokens else 0
        print(f"  {tier:<8} {t['n']:>3} dispatches  {t['tokens']:>10,} tokens  {share:>3}%")
    print("\nby tier and kind")
    print(f"  {'model':<8} {'kind':<14} {'n':>3} {'pass':>4} {'rework':>6} {'escal':>5} {'fail':>4} {'avg tok':>9}")
    for s in summary:
        print(
            f"  {s['model']:<8} {s['kind']:<14} {s['n']:>3} {s['pass']:>4} {s['rework']:>6} "
            f"{s['escalated']:>5} {s['fail']:>4} {s['avg_tokens']:>9,}"
        )
    print("\nflags")
    if notes:
        for n in notes:
            print(f"  - {n}")
    else:
        print(f"  none (rates are only judged from {MIN_SAMPLE} dispatches of a kind upward)")


def main():
    p = argparse.ArgumentParser(description="fable-conductor dispatch ledger")
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="record one dispatch")
    add.add_argument("--model", required=True, help="haiku | sonnet | opus | fable")
    add.add_argument("--role", required=True, help="scout | runner | builder | reviewer | ...")
    add.add_argument("--kind", help="kind of work, for grouping (defaults to the role)")
    add.add_argument("--tokens", type=int, default=0)
    add.add_argument("--duration-ms", type=int, default=0)
    add.add_argument("--outcome", required=True, choices=OUTCOMES)
    add.add_argument("--task", required=True, help="a few words naming the piece")
    add.add_argument("--file")
    add.set_defaults(func=cmd_add)

    rep = sub.add_parser("report", help="summarise the ledger and print routing flags")
    rep.add_argument("--last", type=int, default=0, help="only the last N dispatches")
    rep.add_argument("--json", action="store_true")
    grp = rep.add_mutually_exclusive_group()
    grp.add_argument("--file")
    grp.add_argument(
        "--all",
        metavar="DIR",
        help="combine every project ledger in DIR and its immediate subdirectories",
    )
    rep.set_defaults(func=cmd_report)

    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
