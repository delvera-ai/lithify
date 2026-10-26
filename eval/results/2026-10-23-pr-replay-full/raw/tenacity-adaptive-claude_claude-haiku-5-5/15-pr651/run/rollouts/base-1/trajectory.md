# trajectory base-1

final message:
`retry_if_exception_message(message="")` now works, and `retry_if_not_exception_message(message="")` does too. The full suite passes: 173 passed, 1 skipped, using the project's test command from CLAUDE.md.

**Cause:** `tenacity/retry.py` tested truthiness (`if message`, `if match`), so an empty string counted as "not provided". That made `message=""` raise the "missing argument" `TypeError`, and it would have sent an empty `match` down the wrong branch in `_check`.

**Fix (`tenacity/retry.py`):**
- The constructor checks `is None` / `is not None`. Passing both (including `message=""` with a `match`) still raises `TypeError`, and passing neither still raises it.
- `_check` now branches on whether `self.match` was set, not on whether `self.message` is truthy. An empty `message` is compared for equality, so it matches only exceptions whose string is `""`.

**Tests (`tests/test_tenacity.py`):** I added tests and did not change any existing ones.
- Negative: `message=""` together with `match` raises `TypeError`.
- Positive: `message=""` matches `RuntimeError()` and not `RuntimeError("boom")`, for both the positive and negated predicates.
- Positive: `match=""` matches any exception, since an empty regex matches everything.
- A small `_call_with_exception` helper builds a `RetryCallState` with a set exception and calls the predicate, so the tests go through the public `__call__` path.

I haven't run ruff or mypy, because neither is installed in the project env. I also haven't committed; say if you want a commit.

## events
[tool_use Bash] {"command": "grep -rn \"retry_if_exception_message\\|retry_if_not_exception_message\\|missing 1 required\" --include=*.py . | grep -v \"/\\.git/\"", "description": "Locate exception-message retry helpers"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"exception_message\\|missing 1 required\" . --exclude-dir=.git | head -50", "description": "Search repo for exception-message helpers"}
[tool_result] tests/test_tenacity.py:920:    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
tests/test_tenacity.py:922:            tenacity.retry_if_exception_message()
tests/test_tenacity.py:924:    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
tests/test_tenacity.py:926:            tenacity.retry_if_exception_message(message="negative", match="negative")
tests/test_tenacity.py:1188:    retry=tenacity.retry_if_exception_message(
tests/test_tenacity.py:1192
…[2648 chars elided]…
y:804:    "retry_if_exception_message",
tenacity/__init__.py:806:    "retry_if_not_exception_message",
tenacity/retry.py:218:class retry_if_exception_message(retry_if_exception):
tenacity/retry.py:233:                f"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'"
tenacity/retry.py:247:class retry_if_not_exception_message(retry_if_exception_message):
doc/source/index.rst:258:    retry_if_exception_message
doc/source/index.rst:259:    retry_if_not_exception_message
[tool_use Bash] {"command": "sed -n 200,275p tenacity/retry.py && echo ---- && sed -n 915,930p tests/test_tenacity.py", "description": "Read helper class and related tests"}
[tool_result]         return False


class retry_if_not_result(retry_base):
    """Retries if the result refutes a predicate."""

    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
        self.predicate = predicate

    def __call__(self, retry_state: "RetryCallState") -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        if not retry_state.outcome.failed:
            return not self.predicate(retry_st
…[2171 chars elided]…
t_number"])

    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
        with self.assertRaises(TypeError):
            tenacity.retry_if_exception_message()

    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
        with self.assertRaises(TypeError):
            tenacity.retry_if_exception_message(message="negative", match="negative")


class NoneReturnUntilAfterCount:
    """Holds counter state for invoking a method several times in a row."""
[assistant] The bug is in `retry_if_exception_message.__init__` and `_check`: they test truthiness (`if message`), so `""` is treated as "not provided". I'll switch to `is None` checks and make `_check` branch on `self.match` so an empty `message` is compared directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "old_string": "        if message and match:\n            raise TypeError(\n                f\"{self.__class__.__name__}() takes either 'message' or 'match', not both\"\n            )\n\n        if not message and not match:\n        
…[842 chars elided]…
1 required argument 'message' or 'match'\"\n            )\n\n        self.message = message\n        self.match = re.compile(match) if match is not None else None\n        super().__init__(self._check)\n\n    def _check(self, exception: BaseException) -> bool:\n        if self.match is None:\n            return self.message == str(exception)\n        return bool(self.match.match(str(exception)))"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tenacity/retry.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing negative tests. First I'll check how the test file exercises these predicates.
[tool_use Bash] {"command": "sed -n 1184,1200p tests/test_tenacity.py && sed -n 1354,1362p tests/test_tenacity.py && grep -n \"_check\\|RetryCallState(\" tests/test_tenacity.py | head; ls <work>/env-tenacity/bin/python", "description": "Inspect test helpers and project python env"}
[tool_result] @retry(
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_message(
        message=NoCustomErrorAfterCount.derived_message
    ),
)
def _retryable_test_if_exception_message_message(thing: typing.Any) -> typing.Any:
    return thing.go()


@retry(
    retry=tenacity.retry_if_not_exception_message(
        message=NoCustomErrorAfterCount.derived_message
    )
)
    def test_retry_if_exception_message(self) -> None:
        try:
            self.assertTrue(
            
…[184 chars elided]…
atistics)
            self.fail("CustomError should've been retried from errormessage")

74:    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
98:        rs = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
151:        rs = RetryCallState(r, None, (), {})
157:        rs = RetryCallState(r, None, (), {})
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 145,165p tests/test_tenacity.py", "description": "Read existing RetryCallState test pattern"}
[tool_result]         assert captured
        assert "my_func" in captured[0].get_fn_name()

    def test_get_fn_name_context_manager_no_name(self) -> None:
        """get_fn_name() returns '<unknown>' in context manager mode without a name."""
        r = Retrying(stop=tenacity.stop_after_attempt(1))
        rs = RetryCallState(r, None, (), {})
        assert rs.get_fn_name() == "<unknown>"

    def test_get_fn_name_context_manager_with_name(self) -> None:
        """get_fn_name() returns the given name in context manager mode."""
        r = Retrying(name="ws_listener", stop=tenacity.stop_after_attempt(1))
        rs = RetryCallState(r, None, (), {})
        assert rs.get_fn_name() == "ws_listener"

    def test_logging_uses_name(self) -> None:
        """before_log uses the name parameter in context manager mode."""
        import unittest.mock

        log = unittest.mock.MagicMock()
        logger = unittest.mock.MagicMock(log=log)
[tool_use Bash] {"command": "grep -n \"def set_exception\" -A3 tenacity/__init__.py; grep -n \"^from\\|^import\" tests/test_tenacity.py | head -30", "description": "Check set_exception signature and test imports"}
[tool_result] 630:    def set_exception(
631-        self,
632-        exc_info: tuple[
633-            type[BaseException], BaseException, "types.TracebackType | None"
16:import contextlib
17:import datetime
18:import logging
19:import pickle
20:import re
21:import time
22:import typing
23:import unittest
24:from fractions import Fraction
25:from unittest import mock
27:import pytest
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"negative\", match=\"negative\")
…[1200 chars elided]…
(retry, RuntimeError()) is True\n        assert _call_with_exception(retry, RuntimeError(\"boom\")) is True\n\n    def test_retry_if_not_exception_message_empty_match(self) -> None:\n        retry = tenacity.retry_if_not_exception_message(match=\"\")\n        assert _call_with_exception(retry, RuntimeError()) is False\n        assert _call_with_exception(retry, RuntimeError(\"boom\")) is False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] The new tests call a `_call_with_exception` helper that doesn't exist yet, so I'll add it at module level beside the other test helpers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "class NoneReturnUntilAfterCount:\n    \"\"\"Holds counter state for invoking a method several times in a row.\"\"\"", "new_string": "def _call_with_exception(retry: typing.Any, exc: BaseException) -> typing.Any:\n    \"\"\"Invoke a retry predicate as if the attempt had raised ``exc``.\"\"\"\n    retry_state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]\n    retry_state.set_exception((type(exc), exc, None))\n    return retry(retry_state)\n\n\nclass NoneReturnUntilAfterCount:\n    \"\"\"Holds counter state for invoking a method several times in a row.\"\"\""}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162552-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next I'll run the project's test command, which is the one given in CLAUDE.md.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run project test suite with project python"}
[tool_result] ...............s.............................................. [ 35%]
...................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.89s
[assistant] All 173 tests pass. I'll run the repo's linters on the two changed files as well.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; for t in ruff mypy; do if [ -x $PY/$t ]; then echo \"== $t\"; $PY/$t $( [ $t = ruff ] && echo \"check tenacity/retry.py tests/test_tenacity.py\" && $PY/ruff format --check tenacity/retry.py tests/test_tenacity.py || echo \"tenacity/retry.py tests/test_tenacity.py\" ) 2>&1 | tail -5; fi; done; git status --short; git diff --stat", "description": "Run ruff/mypy if available and show diff stats"}
[tool_result]  M tenacity/retry.py
 M tests/test_tenacity.py
 tenacity/retry.py      |  9 ++++-----
 tests/test_tenacity.py | 31 +++++++++++++++++++++++++++++++
 2 files changed, 35 insertions(+), 5 deletions(-)
[assistant] `retry_if_exception_message(message="")` now works, and `retry_if_not_exception_message(message="")` does too. The full suite passes: 173 passed, 1 skipped, using the project's test command from CLAUDE.md.

**Cause:** `tenacity/retry.py` tested truthiness (`if message`, `if match`), so an empty string counted as "not provided". That made `message=""` raise the "missing argument" `TypeError`, and it would have sent an empty `match` down the wrong branch in `_check`.

**Fix (`tenacity/retry.py`):**
- The constructor checks `is None` / `is not None`. Passing both (including `message=""` with a `m
…[331 chars elided]…
hange any existing ones.
- Negative: `message=""` together with `match` raises `TypeError`.
- Positive: `message=""` matches `RuntimeError()` and not `RuntimeError("boom")`, for both the positive and negated predicates.
- Positive: `match=""` matches any exception, since an empty regex matches everything.
- A small `_call_with_exception` helper builds a `RetryCallState` with a set exception and calls the predicate, so the tests go through the public `__call__` path.

I haven't run ruff or mypy, because neither is installed in the project env. I also haven't committed; say if you want a commit.
