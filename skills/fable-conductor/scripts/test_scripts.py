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
