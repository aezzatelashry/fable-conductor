import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETUP = str(HERE / "setup.py")
LEDGER = str(HERE / "ledger.py")
AGENTS = ["builder", "deep-reviewer", "reviewer", "runner"]


def run(script, *args, cwd=None):
    return subprocess.run(
        [sys.executable, script, *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def add(ledger_file, tokens=100, outcome="pass"):
    r = run(
        LEDGER,
        "add",
        "--model",
        "sonnet",
        "--role",
        "builder",
        "--tokens",
        tokens,
        "--outcome",
        outcome,
        "--task",
        "t",
        "--file",
        ledger_file,
    )
    assert r.returncode == 0, r.stderr


def test_plan_changes_nothing(tmp_path):
    r = run(SETUP, "plan", "--project", tmp_path)
    assert r.returncode == 0
    assert "would: installed" in r.stdout
    assert list(tmp_path.rglob("*")) == []


def test_apply_installs_and_is_idempotent(tmp_path):
    r = run(SETUP, "apply", "--project", tmp_path)
    assert r.returncode == 0
    for name in AGENTS:
        assert (tmp_path / ".claude" / "agents" / f"{name}.md").is_file()
    lessons = tmp_path / ".claude" / "conductor" / "lessons.md"
    assert lessons.read_text(encoding="utf-8").startswith("# Conductor lessons for this project\n\n")
    r2 = run(SETUP, "apply", "--project", tmp_path)
    assert "installed:" not in r2.stdout
    assert r2.stdout.count("unchanged:") == 5


def test_differing_agent_kept(tmp_path):
    agent = tmp_path / ".claude" / "agents" / "builder.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("my own builder\n", encoding="utf-8")
    r = run(SETUP, "apply", "--project", tmp_path)
    assert "kept existing (differs)" in r.stdout
    assert agent.read_text(encoding="utf-8") == "my own builder\n"


def test_bad_project_exits_2(tmp_path):
    assert run(SETUP, "plan", "--project", tmp_path / "nope").returncode == 2


def test_report_json_has_rows_and_generated_at(tmp_path):
    f = tmp_path / "l.jsonl"
    add(f)
    data = json.loads(run(LEDGER, "report", "--json", "--file", f).stdout)
    assert len(data["rows"]) == 1
    assert "generated_at" in data


def test_report_all_aggregates(tmp_path):
    for name, n in (("alpha", 1), ("beta", 2)):
        for _ in range(n):
            add(tmp_path / name / ".claude" / "conductor" / "ledger.jsonl")
    data = json.loads(run(LEDGER, "report", "--all", tmp_path, "--json").stdout)
    assert data["dispatches"] == 3
    assert {p["project"] for p in data["by_project"]} == {"alpha", "beta"}
    assert "by project" in run(LEDGER, "report", "--all", tmp_path).stdout


def test_report_all_none(tmp_path):
    r = run(LEDGER, "report", "--all", tmp_path)
    assert r.returncode == 0
    assert f"no ledgers found under {tmp_path}" in r.stdout


def test_all_and_file_exclusive(tmp_path):
    r = run(LEDGER, "report", "--all", tmp_path, "--file", tmp_path / "x")
    assert r.returncode != 0


def test_rules_line_is_appended_once_and_never_overwrites(tmp_path):
    rules = tmp_path / ".claude" / "CLAUDE.md"
    rules.parent.mkdir(parents=True)
    rules.write_text("# Project rules\n\nkeep me\n", encoding="utf-8")
    assert run(SETUP, "plan", "--rules", "--project", tmp_path).returncode == 0
    assert rules.read_text(encoding="utf-8") == "# Project rules\n\nkeep me\n"
    assert run(SETUP, "apply", "--rules", "--project", tmp_path).returncode == 0
    first = rules.read_text(encoding="utf-8")
    assert first.startswith("# Project rules\n\nkeep me\n")
    assert first.count("fable-conductor") >= 1
    second = run(SETUP, "apply", "--rules", "--project", tmp_path)
    assert "unchanged" in second.stdout
    assert rules.read_text(encoding="utf-8") == first


def test_without_rules_flag_the_rules_file_is_untouched(tmp_path):
    assert run(SETUP, "apply", "--project", tmp_path).returncode == 0
    assert not (tmp_path / ".claude" / "CLAUDE.md").exists()


def add_model(ledger_file, model, tokens):
    r = run(
        LEDGER,
        "add",
        "--model",
        model,
        "--role",
        "builder",
        "--tokens",
        tokens,
        "--outcome",
        "pass",
        "--task",
        "t",
        "--file",
        ledger_file,
    )
    assert r.returncode == 0, r.stderr


def priced_ledger(tmp_path):
    f = tmp_path / "l.jsonl"
    add_model(f, "haiku", 1_500_000)
    add_model(f, "sonnet", 123_456)
    add_model(f, "zeta", 1000)
    add_model(f, "alpha", 5)
    return f


def write_prices(directory, text):
    p = directory / "prices.json"
    p.write_text(text, encoding="utf-8")
    return p


def test_prices_json_cost_and_unpriced(tmp_path):
    f = priced_ledger(tmp_path)
    p = write_prices(tmp_path, '{"Haiku": 1.0, "sonnet": 3.33}')
    r = run(LEDGER, "report", "--json", "--file", f, "--prices", p)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    # haiku 1.5; sonnet 123456 * 3.33 / 1e6 = 0.41110848 -> 0.4111
    assert data["by_tier"]["haiku"]["cost"] == 1.5
    assert data["by_tier"]["sonnet"]["cost"] == 0.4111
    assert data["by_tier"]["zeta"]["cost"] == 0
    assert data["by_tier"]["alpha"]["cost"] == 0
    assert data["unpriced_models"] == ["alpha", "zeta"]
    assert data["estimated_cost"] == 1.9111


def test_prices_total_sums_unrounded_costs(tmp_path):
    f = tmp_path / "l.jsonl"
    add_model(f, "haiku", 1)
    add_model(f, "sonnet", 1)
    p = write_prices(tmp_path, '{"haiku": 30000, "sonnet": 30000}')
    data = json.loads(run(LEDGER, "report", "--json", "--file", f, "--prices", p).stdout)
    assert data["by_tier"]["haiku"]["cost"] == 0.03
    assert data["estimated_cost"] == 0.06
    assert data["unpriced_models"] == []


def test_prices_text_lines(tmp_path):
    f = priced_ledger(tmp_path)
    p = write_prices(tmp_path, '{"haiku": 1.0, "sonnet": 3.33}')
    lines = run(LEDGER, "report", "--file", f, "--prices", p).stdout.splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith("dispatches:"))
    assert lines[i + 1] == "estimated cost: $1.91"
    assert lines[i + 2] == "unpriced: alpha, zeta"
    full = write_prices(tmp_path, '{"haiku": 1, "sonnet": 1, "zeta": 1, "alpha": 1}')
    out = run(LEDGER, "report", "--file", f, "--prices", full).stdout
    assert "estimated cost: $" in out
    assert "unpriced" not in out


def test_report_without_prices_is_unchanged(tmp_path):
    f = priced_ledger(tmp_path)
    out = run(LEDGER, "report", "--file", f).stdout
    assert "estimated cost" not in out
    assert "unpriced" not in out
    data = json.loads(run(LEDGER, "report", "--json", "--file", f).stdout)
    assert "estimated_cost" not in data
    assert "unpriced_models" not in data
    assert all("cost" not in t for t in data["by_tier"].values())


def test_bad_prices_exit_2(tmp_path):
    f = priced_ledger(tmp_path)
    cases = [
        tmp_path / "nope.json",
        write_prices(tmp_path, "{not json"),
        write_prices(tmp_path, "[1, 2]"),
        write_prices(tmp_path, '{"haiku": "1.0"}'),
        write_prices(tmp_path, '{"haiku": true}'),
        write_prices(tmp_path, '{"haiku": -1}'),
        write_prices(tmp_path, '{"haiku": NaN}'),
        write_prices(tmp_path, '{"haiku": Infinity}'),
    ]
    for p in cases:
        r = run(LEDGER, "report", "--file", f, "--prices", p)
        assert r.returncode == 2, p
        assert r.stderr.strip(), p
        assert r.stdout == ""


def test_bad_prices_exit_2_even_without_ledger(tmp_path):
    r = run(
        LEDGER,
        "report",
        "--file",
        tmp_path / "none.jsonl",
        "--prices",
        tmp_path / "nope.json",
    )
    assert r.returncode == 2
    assert "nope.json" in r.stderr


def test_prices_underscore_keys_ignored(tmp_path):
    f = priced_ledger(tmp_path)
    p = write_prices(tmp_path, '{"_note": "made up", "_n": 3, "haiku": 1.0}')
    r = run(LEDGER, "report", "--json", "--file", f, "--prices", p)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["unpriced_models"] == ["alpha", "sonnet", "zeta"]


def test_prices_with_all(tmp_path):
    add_model(tmp_path / "a" / ".claude" / "conductor" / "ledger.jsonl", "haiku", 500_000)
    add_model(tmp_path / "b" / ".claude" / "conductor" / "ledger.jsonl", "haiku", 500_000)
    p = write_prices(tmp_path / "a", '{"haiku": 2}')
    data = json.loads(run(LEDGER, "report", "--all", tmp_path, "--json", "--prices", p).stdout)
    assert data["estimated_cost"] == 2.0
    assert data["by_tier"]["haiku"]["cost"] == 2.0
    assert "by_project" in data
    out = run(LEDGER, "report", "--all", tmp_path, "--prices", p).stdout
    assert "estimated cost: $2.00" in out.splitlines()
    assert "by project" in out


def test_prices_with_empty_ledger_reports_no_dispatches(tmp_path):
    p = write_prices(tmp_path, '{"haiku": 1}')
    r = run(LEDGER, "report", "--file", tmp_path / "none.jsonl", "--prices", p)
    assert r.returncode == 0
    assert "no dispatches recorded" in r.stdout
    assert "estimated cost" not in r.stdout


def test_example_prices_file_loads(tmp_path):
    example = HERE.parent / "assets" / "prices.example.json"
    raw = json.loads(example.read_text(encoding="utf-8"))
    assert "_note" in raw
    f = priced_ledger(tmp_path)
    data = json.loads(run(LEDGER, "report", "--json", "--file", f, "--prices", example).stdout)
    assert data["by_tier"]["haiku"]["cost"] == 1.5
    assert data["unpriced_models"] == ["alpha", "zeta"]
