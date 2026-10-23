import json

from lithify.adapters.agy import AgyAdapter
from lithify.adapters.claude import ClaudeAdapter
from lithify.adapters.codex import CodexAdapter
from lithify.gates import is_test_path, run_gates
from lithify.library import parse_reflection
from lithify.pipeline import _choice


def test_parse_reflection_rows_and_lesson():
    text = """<edits>
component: guardrails.md
candidates: dom-1
change: added AppError rule
observed: dom-1 used AppError
verdict: helped
component: `system.md`
candidates: inv-1, comp-1
change: verify step
observed: unclear
verdict: Confounded — two edits at once
</edits>
<experience>
cue: a task touches the api layer
lesson: put api conventions in skills/api-conventions
  as checkable rules
evidence: guardrails.md row
confidence: medium
</experience>"""
    r = parse_reflection(text)
    assert [(x.component, x.verdict) for x in r.rows] == [("guardrails.md", "helped"), ("system.md", "confounded")]
    assert r.helped() == {"guardrails.md"}
    assert r.lesson.endswith("as checkable rules")


def test_parse_reflection_no_entry():
    r = parse_reflection("<edits>\n</edits>\nNO_ENTRY")
    assert not r.has_entry and r.rows == []


def test_choice_parsing():
    assert _choice("<why>x</why>\n```choice\nc2\n```", ["c1", "c2"]) == "c2"
    assert _choice("garbage", ["c1", "c2"]) is None


def test_test_path_detection():
    for p in ("tests/test_a.py", "pkg/test_a.py", "a_test.go", "src/x.test.ts", "web/__tests__/a.js"):
        assert is_test_path(p), p
    for p in ("src/app.py", "testing_utils/readme.md", "contest.py"):
        assert not is_test_path(p), p


def test_gates_flag_edits_to_existing_tests(tmp_path):
    res = run_gates(tmp_path, [("test", "true")], [("M", "tests/test_x.py"), ("A", "tests/test_new.py")])
    assert not res.passed and res.protected_test_edits == ["M tests/test_x.py"]
    ok = run_gates(tmp_path, [("test", "true")], [("A", "tests/test_new.py")])
    assert ok.passed
    fail = run_gates(tmp_path, [("test", "exit 3")], [])
    assert not fail.passed and fail.runs[0].returncode == 3


def test_claude_stream_json_parse():
    lines = [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "a.py", "is_error": False}]}},
        {
            "type": "result",
            "result": "done",
            "total_cost_usd": 0.12,
            "is_error": False,
            "num_turns": 2,
            "usage": {
                "input_tokens": 100,
                "cache_creation_input_tokens": 50,
                "cache_read_input_tokens": 900,
                "output_tokens": 40,
            },
        },
    ]
    r = ClaudeAdapter().parse("\n".join(map(json.dumps, lines)), "", 0)
    assert r.ok and r.text == "done" and r.cost_usd == 0.12
    assert (r.tokens_in, r.tokens_cached, r.tokens_out) == (150, 900, 40)
    assert "[tool_use Bash]" in r.transcript and "[tool_result]" in r.transcript


def test_codex_jsonl_parse():
    lines = [
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"type": "command_execution", "command": "pytest", "exit_code": 1, "aggregated_output": "1 failed"},
        },
        {"type": "item.completed", "item": {"type": "agent_message", "text": "fixed it"}},
        {"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 600, "output_tokens": 50}},
    ]
    r = CodexAdapter().parse("\n".join(map(json.dumps, lines)), "", 0)
    assert r.ok and r.text == "fixed it"
    assert (r.tokens_in, r.tokens_cached, r.tokens_out) == (400, 600, 50)
    assert "exit=1" in r.transcript


def test_agy_json_parse_and_empty_stdout():
    env = {"conversation_id": "x", "status": "SUCCESS", "response": "ok", "usage": {"input_tokens": 10, "output_tokens": 5}}
    r = AgyAdapter().parse(json.dumps(env), "", 0)
    assert r.ok and r.text == "ok" and r.tokens_in == 10
    empty = AgyAdapter().parse("", "boom", 0)
    assert not empty.ok and "agy update" in empty.error


def test_adapter_args_replace_permission_defaults(tmp_path):
    assert "--dangerously-skip-permissions" in ClaudeAdapter().build_cmd("x", tmp_path)
    strict = ClaudeAdapter(["--permission-mode", "acceptEdits"]).build_cmd("x", tmp_path)
    assert "--dangerously-skip-permissions" not in strict and "acceptEdits" in strict


def test_cli_at_model_spec(tmp_path):
    from lithify.adapters import get_adapter, split_spec

    assert split_spec("claude@claude-haiku-5-5") == ("claude", "claude-haiku-5-5")
    cmd = get_adapter("claude@claude-haiku-5-5").build_cmd("x", tmp_path)
    assert cmd[-2:] == ["--model", "claude-haiku-5-5"]
    assert get_adapter("codex").build_cmd("x", tmp_path)[-1] == "x"
