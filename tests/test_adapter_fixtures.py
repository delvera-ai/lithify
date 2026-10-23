"""Parse tests against output captured from real CLI versions (tests/fixtures/, redacted)."""

from pathlib import Path

from lithify.adapters.agy import AgyAdapter
from lithify.adapters.claude import ClaudeAdapter
from lithify.adapters.codex import CodexAdapter

FIX = Path(__file__).parent / "fixtures"


def test_claude_2_1_309_stream_json():
    r = ClaudeAdapter().parse((FIX / "claude_2.1.309.jsonl").read_text(), "", 0)
    assert r.ok and r.text == "ok"
    assert "[assistant] ok" in r.transcript
    assert r.tokens_in > 0 and r.tokens_out > 0
    assert 0 < r.cost_usd < 0.01


def test_codex_0_163_0_exec_json():
    r = CodexAdapter().parse((FIX / "codex_0.163.0.jsonl").read_text(), "Reading additional input from stdin...\n", 0)
    assert r.ok and r.text
    assert "[command exit=0]" in r.transcript and "hello.txt" in r.transcript
    # input_tokens includes cached tokens; the adapter reports them separately
    assert r.tokens_cached == 48768 and r.tokens_in == 54232 - 48768 and r.tokens_out == 126
    assert r.cost_usd == 0.0  # codex reports no dollar cost


def test_codex_default_args_use_sandbox_flag():
    cmd = CodexAdapter().build_cmd("task", Path("/w"))
    assert "--full-auto" not in cmd  # removed in codex-cli 0.163.0
    assert cmd[cmd.index("--sandbox") + 1] == "workspace-write" and cmd[-1] == "task"


def test_agy_1_4_3_error_envelope_keeps_message():
    r = AgyAdapter().parse((FIX / "agy_1.4.3_quota_error.json").read_text(), "", 3)
    assert not r.ok
    assert r.error.startswith("agy status ERROR") and "quota" in r.error
    assert r.meta["conversation_id"]


def test_agy_usage_field_names_from_1_4_3():
    usage = '{"input_tokens":10,"output_tokens":3,"thinking_tokens":4,"cache_read_tokens":6}'
    env = '{"status":"SUCCESS","response":"done","usage":' + usage + "}"
    r = AgyAdapter().parse(env, "", 0)
    assert r.ok and r.text == "done"
    assert (r.tokens_in, r.tokens_cached, r.tokens_out) == (10, 6, 7)


def test_parsers_tolerate_garbage():
    for ad in (ClaudeAdapter(), CodexAdapter(), AgyAdapter()):
        r = ad.parse('not json\n{"type": "mystery"}\n{broken', "", 1)
        assert r.ok is False or r.text == ""


def test_claude_error_result_surfaces_limit_notice():
    """The 2.1.309 `result` event for a session-limit stop (reconstructed from a live eval trajectory:
    final message only, zero tokens) must report the notice as the error, not an empty string."""
    import json

    from lithify.adapters.base import hit_limit

    notice = "You've hit your session limit · resets 6:40pm (Africa/Johannesburg)"
    ev = {"type": "result", "subtype": "success", "is_error": True, "result": notice, "total_cost_usd": 0, "usage": {}}
    r = ClaudeAdapter().parse(json.dumps(ev) + "\n", "", 1)
    assert not r.ok and r.error == notice and hit_limit(r)
    ok = ClaudeAdapter().parse((FIX / "claude_2.1.309.jsonl").read_text(), "", 0)
    assert not hit_limit(ok)
