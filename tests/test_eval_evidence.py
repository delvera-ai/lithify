"""Session timing and compressed evidence export tests; zero live calls."""

import gzip
import json
from pathlib import Path

import pytest
from eval.evalkit import COLUMNS, HOME, USER, copy_redacted, require_redacted, scan_leaks, session_timing

from lithify.adapters.claude import ClaudeAdapter


def test_session_timing_uses_per_result_active_and_cumulative_api(tmp_path):
    capture = (Path(__file__).parent / "fixtures/claude_2.1.310_background_results.jsonl").read_text()
    meta = ClaudeAdapter().parse(capture, "", 0).meta
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "001.json").write_text(json.dumps(meta))
    assert session_timing(tmp_path, 2705.6) == {"active_s": 163.325, "api_s": 134.645, "idle_s": 2542.275}
    assert {"active_s", "api_s", "idle_s"} <= set(COLUMNS)
    assert session_timing(None, 10) == {"active_s": "", "api_s": "", "idle_s": ""}


def test_gzip_session_leaks_are_detected_and_export_is_redacted(tmp_path):
    source = tmp_path / "source"
    stream = source / ".lithify/runs/task/sessions/001.gz"
    stream.parent.mkdir(parents=True)
    secret = "sk-" + "a" * 25
    stream.write_bytes(gzip.compress(f"{HOME} {USER.upper()} {secret}".encode()))
    assert scan_leaks(source) == [".lithify/runs/task/sessions/001.gz: credential or unredacted identity"]
    with pytest.raises(RuntimeError, match="export blocked"):
        require_redacted(source)
    exported = tmp_path / "exported"
    copy_redacted(source, exported)
    text = gzip.decompress((exported / stream.relative_to(source)).read_bytes()).decode()
    assert HOME not in text and USER.casefold() not in text.casefold() and secret not in text
    assert scan_leaks(exported) == []


def test_corrupt_compressed_session_blocks_copy_and_scan(tmp_path):
    source = tmp_path / "source"
    stream = source / ".lithify/runs/task/sessions/001.gz"
    stream.parent.mkdir(parents=True)
    stream.write_bytes(b"not gzip")
    with pytest.raises(RuntimeError, match="unreadable compressed"):
        require_redacted(source)
    with pytest.raises(OSError):
        copy_redacted(source, tmp_path / "exported")
