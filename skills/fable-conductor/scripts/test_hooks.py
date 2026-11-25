import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOKS = HERE / "hooks"
sys.path.insert(0, str(HOOKS))

import hooklib


def hook(name, payload, project, env_extra=None, raw=None):
    import os

    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(HOOKS / f"{name}.py")],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def asst(mid, model, i, o, cw, cr, ts):
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "id": mid,
            "model": model,
            "usage": {
                "input_tokens": i,
                "output_tokens": o,
                "cache_creation_input_tokens": cw,
                "cache_read_input_tokens": cr,
            },
        },
    }


def transcript(model="claude-sonnet-5-5"):
    return [
        {
            "type": "user",
            "isMeta": True,
            "timestamp": "2026-11-24T10:00:00.000Z",
            "message": {"content": "<meta>"},
        },
        {
            "type": "user",
            "timestamp": "2026-11-24T10:00:01.000Z",
            "message": {"content": [{"type": "text", "text": "  Build   the\nthing " + "x" * 100}]},
        },
        asst("m1", model, 10, 1, 100, 0, "2026-11-24T10:00:02.000Z"),
        asst("m1", model, 10, 20, 100, 0, "2026-11-24T10:00:03.000Z"),
        {"type": "user", "message": {"content": "tool result"}},
        asst("m2", model, 5, 7, 0, 300, "2026-11-24T10:01:01.000Z"),
        asst("m2", model, 5, 9, 0, 300, "2026-11-24T10:01:02.000Z"),
    ]


def write_tx(path, lines):
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return path


def test_parser_sums_and_final(tmp_path):
    r = hooklib.parse_transcript(write_tx(tmp_path / "t.jsonl", transcript()))
    assert r["input_tokens"] == 15
    assert r["output_tokens"] == 29
    assert r["cache_write_tokens"] == 100
    assert r["cache_read_tokens"] == 300
    assert r["final_context_tokens"] == 314
    assert r["messages"] == 2
    assert r["model"] == "sonnet"
    assert r["duration_ms"] == 62000
    assert r["task"] == "Build the thing " + "x" * 64
    assert len(r["task"]) == 80


def test_parser_model_mapping():
    for mid, short in [
        ("claude-haiku-4-5", "haiku"),
        ("claude-sonnet-5-5", "sonnet"),
        ("claude-opus-4-7", "opus"),
        ("claude-fable-1", "fable"),
        ("claude-mythos-x", "fable"),
        ("gpt-x", "gpt-x"),
    ]:
        lines = [json.dumps(x) for x in transcript(mid)]
        assert hooklib.parse_lines(lines)["model"] == short


def test_parser_no_assistant():
    assert hooklib.parse_lines(['{"type":"user"}', "garbage"]) is None


def stop_payload(tmp_path, tx, agent_id="a1", agent_type="builder"):
    return {
        "hook_event_name": "SubagentStop",
        "agent_id": agent_id,
        "agent_type": agent_type,
        "agent_transcript_path": str(tx),
    }


def test_subagent_stop_end_to_end(tmp_path):
    tx = write_tx(tmp_path / "t.jsonl", transcript())
    payload = stop_payload(tmp_path, tx)
    r = hook("subagent_stop", payload, tmp_path)
    assert r.returncode == 0
    msg = json.loads(r.stdout)["systemMessage"]
    assert "المايسترو" in msg
    assert "144" in msg  # 15 + 29 + 100 new work
    assert "300" in msg and "sonnet" in msg and "builder" in msg
    assert "hookSpecificOutput" not in r.stdout
    ledger = tmp_path / ".claude" / "conductor" / "ledger.jsonl"
    rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["source"] == "hook" and row["outcome"] == "unrated"
    assert row["tokens"] == 144 and row["cache_read_tokens"] == 300
    assert row["agent_id"] == "a1" and row["final_context_tokens"] == 314
    assert row["role"] == row["kind"] == "builder" and row["messages"] == 2
    r2 = hook("subagent_stop", payload, tmp_path)
    assert r2.returncode == 0 and r2.stdout == ""
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_subagent_stop_missing_transcript(tmp_path):
    payload = stop_payload(tmp_path, tmp_path / "nope.jsonl", agent_type="runner")
    r = hook("subagent_stop", payload, tmp_path)
    assert r.returncode == 0
    assert "تعذّر" in json.loads(r.stdout)["systemMessage"]
    assert not (tmp_path / ".claude" / "conductor" / "ledger.jsonl").exists()


def test_hooks_survive_garbage_stdin(tmp_path):
    for name in ("subagent_stop", "session_start", "stop_nudge", "statusline"):
        r = hook(name, None, tmp_path, raw="{not json")
        assert r.returncode == 0, name


def conductor_fixture(tmp_path, rows=2, unrated=1):
    c = tmp_path / ".claude" / "conductor"
    (c / "hooks").mkdir(parents=True)
    (c / "hooks" / "VERSION").write_text("2.4.0\n", encoding="utf-8")
    lines = []
    for i in range(rows):
        outcome = "unrated" if i < unrated else "pass"
        lines.append(
            json.dumps(
                {
                    "ts": f"2026-11-24T10:00:0{i}+00:00",
                    "model": "sonnet",
                    "kind": "builder",
                    "tokens": 5,
                    "outcome": outcome,
                    "task": "t",
                    "agent_id": f"ag{i}",
                }
            )
        )
    (c / "ledger.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return c


def test_session_start_silent_without_version(tmp_path):
    r = hook("session_start", {}, tmp_path)
    assert r.returncode == 0 and r.stdout == ""


def test_session_start_full(tmp_path):
    c = conductor_fixture(tmp_path)
    (c / "owner.md").write_text(
        "# owner\n- يحب الردود القصيرة\n- يسأل بخيارات\nnot a bullet\n",
        encoding="utf-8",
    )
    (c / "lessons.md").write_text("# L\n\nlesson one\nlesson two\n", encoding="utf-8")
    r = hook("session_start", {}, tmp_path)
    out = json.loads(r.stdout)
    assert "2.4.0" in out["systemMessage"]
    assert "2" in out["systemMessage"] and "1" in out["systemMessage"]
    assert "بدون تقييم" in out["systemMessage"]
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "- يحب الردود القصيرة" in ctx and "- يسأل بخيارات" in ctx
    assert "not a bullet" not in ctx
    assert "Owner profile (follow without being reminded):" in ctx
    assert "lesson two" in ctx and "Unrated dispatches: 1" in ctx
    assert len(ctx) < 3000


def test_session_start_caps_long_owner(tmp_path):
    c = conductor_fixture(tmp_path)
    (c / "owner.md").write_text(
        "\n".join(f"- line {i} " + "y" * 80 for i in range(100)) + "\n",
        encoding="utf-8",
    )
    ctx = json.loads(hook("session_start", {}, tmp_path).stdout)["hookSpecificOutput"]["additionalContext"]
    assert len(ctx) <= 3000 and "line 99" in ctx and "line 0 " not in ctx


def test_stop_nudge_flow(tmp_path):
    c = conductor_fixture(tmp_path, rows=2, unrated=1)
    active = hook("stop_nudge", {"stop_hook_active": True}, tmp_path)
    assert active.stdout == ""
    r = hook("stop_nudge", {}, tmp_path)
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "ledger.py unrated" in out["reason"]
    assert "export-store" not in out["reason"]
    assert json.loads((c / "state.json").read_text())["nudged_lines"] == 2
    assert hook("stop_nudge", {}, tmp_path).stdout == ""
    with (c / "ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"outcome": "unrated", "agent_id": "z"}) + "\n")
    assert json.loads(hook("stop_nudge", {}, tmp_path).stdout)["decision"] == "block"


def test_stop_nudge_dashboard_and_config(tmp_path):
    c = conductor_fixture(tmp_path, rows=2, unrated=0)
    assert hook("stop_nudge", {}, tmp_path).stdout == ""  # nothing to do
    with (c / "ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"outcome": "pass"}) + "\n")
    (c / "dashboard.md").write_text("address", encoding="utf-8")
    out = json.loads(hook("stop_nudge", {}, tmp_path).stdout)
    assert "export-store" in out["reason"] and "unrated dispatches" not in out["reason"]
    (c / "config.json").write_text('{"nudge": false}', encoding="utf-8")
    with (c / "ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"outcome": "unrated"}) + "\n")
    assert hook("stop_nudge", {}, tmp_path).stdout == ""


def test_statusline(tmp_path):
    full = {
        "model": {"display_name": "Sonnet 5.5"},
        "cost": {"total_cost_usd": 1.234},
        "workspace": {"project_dir": str(tmp_path)},
    }
    r = hook("statusline", full, tmp_path / "other")
    assert r.stdout.strip() == "Conductor ✓ | Sonnet 5.5 | $1.23"
    conductor_fixture(tmp_path, rows=3, unrated=2)
    r = hook("statusline", full, tmp_path / "other")
    assert r.stdout.strip() == "Conductor ✓ | Sonnet 5.5 | $1.23 | agents 3 (2 unrated)"
    nocost = {
        "model": {"display_name": "Haiku"},
        "workspace": {"project_dir": str(tmp_path)},
    }
    r = hook("statusline", nocost, tmp_path)
    assert r.stdout.strip() == "Conductor ✓ | Haiku | agents 3 (2 unrated)"
    assert hook("statusline", {}, tmp_path / "x").stdout.strip() == "Conductor ✓"


def test_error_goes_to_log_and_exits_zero(tmp_path):
    c = conductor_fixture(tmp_path)
    (c / "state.json").mkdir()  # unreadable as a file -> write_state fails
    (c / "ledger.jsonl").write_text('{"outcome":"unrated"}\n', encoding="utf-8")
    r = hook("stop_nudge", {}, tmp_path)
    assert r.returncode == 0 and r.stdout == ""
    assert (c / "hooks.log").read_text(encoding="utf-8").strip()
