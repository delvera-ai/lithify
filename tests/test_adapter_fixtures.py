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


def test_claude_accounts_for_every_result_from_captured_fixture():
    """Replay the real 2.1.309 capture twice to model a notification follow-up result.

    This is a constructed multi-result stream, not a claimed new live capture.
    """
    import json

    capture = (FIX / "claude_2.1.309.jsonl").read_text()
    followup = json.loads(capture.splitlines()[-1])
    followup["result"] = "Background test completed"
    r = ClaudeAdapter().parse(capture + json.dumps(followup) + "\n", "", 0)
    assert r.ok and r.text == "Background test completed"
    assert "[assistant] ok" in r.transcript
    assert (r.tokens_in, r.tokens_cached, r.tokens_out) == (25838, 22668, 8)
    assert abs(r.cost_usd - 0.00539788) < 1e-12
    assert r.meta["result_count"] == 2 and r.meta["num_turns"] == 2
    model = r.meta["model_usage"]["claude-haiku-5-5"]
    assert model["inputTokens"] == 4 and model["outputTokens"] == 8
    assert abs(model["costUSD"] - r.cost_usd) < 1e-12
    assert model["contextWindow"] == 1000000
    assert r.meta["calls"][0]["context_tokens"] == 24253
    assert r.raw_stream == capture + json.dumps(followup) + "\n"


def test_claude_call_usage_deduplicates_streamed_message_blocks():
    capture = (FIX / "claude_2.1.309.jsonl").read_text()
    message = capture.splitlines()[1] + "\n"
    r = ClaudeAdapter().parse(message + capture, "", 0)
    assert len(r.meta["calls"]) == 1
    assert r.meta["calls"][0]["model"] == "claude-haiku-5-5"


def test_claude_timeout_retains_usage_and_raw_stream(monkeypatch, tmp_path):
    import subprocess

    capture = (FIX / "claude_2.1.309.jsonl").read_text()

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=capture.encode())

    monkeypatch.setattr(subprocess, "run", timeout)
    r = ClaudeAdapter().run("task", tmp_path, timeout_s=1)
    assert not r.ok and r.returncode == 124 and "timeout" in r.error
    assert r.raw_stream == capture
    assert r.cost_usd > 0 and r.tokens_out == 4


def test_pipeline_archives_session_streams_and_billing(tmp_path):
    import gzip
    import json

    from lithify.config import Config
    from lithify.pipeline import Pipeline

    pipe = Pipeline(tmp_path, Config())
    pipe.runs_dir = tmp_path / ".lithify/runs/test"
    capture = (FIX / "claude_2.1.309.jsonl").read_text()
    result = ClaudeAdapter().parse(capture, "", 0)
    pipe._account(result, role=False)
    pipe._account(result, role=True)
    sessions = pipe.runs_dir / "sessions"
    assert gzip.decompress((sessions / "001-execute.jsonl.gz").read_bytes()).decode() == capture
    assert gzip.decompress((sessions / "002-role.jsonl.gz").read_bytes()).decode() == capture
    billing = json.loads((sessions / "001-execute.json").read_text())
    assert billing["model_usage"]["claude-haiku-5-5"]["outputTokens"] == 4
    assert pipe.usage["exec"] == pipe.usage["roles"] == 1
