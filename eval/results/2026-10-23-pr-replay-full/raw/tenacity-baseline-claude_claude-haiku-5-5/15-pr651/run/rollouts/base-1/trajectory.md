# trajectory base-1

final message:
An empty `message` or `match` is now accepted by both `retry_if_exception_message` and `retry_if_not_exception_message`. Passing neither or both still raises `TypeError`. The full suite passes: 173 passed, 1 skipped.

**Cause:** `tenacity/retry.py` tested `message` and `match` for truthiness, so `""` looked the same as "not given". `_check` used the same test to pick a branch.

**Fix** (`tenacity/retry.py`):
- The constructor now checks `is not None`, so only a real value counts as provided.
- `_check` picks its branch by whether a compiled pattern exists (`self.match is None`), so an empty `message` compares exactly against `str(exception)`.

**Tests added** (`tests/test_tenacity.py`, existing tests untouched):
- `message=""` with `match=""` raises `TypeError`.
- `message=""` matches only an exception whose str is empty, for both the positive and negated variants.
- `match=""` matches any exception, for both variants.

Mypy and ruff are not installed in the project's test environment, so I did not run them. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"exception_message\" --include=*.py . | grep -v \"^./.venv\" | head -50", "description": "Locate exception_message references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"exception_message\" . --exclude-dir=.git | head -50", "description": "Search repo for exception_message references"}
[tool_result] tests/test_tenacity.py:920:    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
tests/test_tenacity.py:922:            tenacity.retry_if_exception_message()
tests/test_tenacity.py:924:    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
tests/test_tenacity.py:926:            tenacity.retry_if_exception_message(message="negative", match="negative")
tests/test_tenacity.py:1188:    retry=tenacity.retry_if_exception_message(
tests/test_tenacity.py:1192
…[2530 chars elided]…
.py:50:    retry_if_exception_message,
tenacity/__init__.py:52:    retry_if_not_exception_message,
tenacity/__init__.py:804:    "retry_if_exception_message",
tenacity/__init__.py:806:    "retry_if_not_exception_message",
tenacity/retry.py:218:class retry_if_exception_message(retry_if_exception):
tenacity/retry.py:247:class retry_if_not_exception_message(retry_if_exception_message):
doc/source/index.rst:258:    retry_if_exception_message
doc/source/index.rst:259:    retry_if_not_exception_message
[tool_use Bash] {"command": "sed -n 200,275p tenacity/retry.py && echo ---- && sed -n 915,930p tests/test_tenacity.py", "description": "Read retry_if_exception_message implementation and tests"}
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
[assistant] The cause is in `retry_if_exception_message.__init__` and `_check`: they test `message` and `match` for truthiness, so an empty string counts as "not given". I'll switch to `is None` checks and make `_check` choose the branch by whether a pattern was supplied.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192327-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "old_string": "        if message and match:\n            raise TypeError(\n                f\"{self.__class__.__name__}() takes either 'message' or 'match', not both\"\n            )\n\n        if not message and not match:\n        
…[842 chars elided]…
1 required argument 'message' or 'match'\"\n            )\n\n        self.message = message\n        self.match = re.compile(match) if match is not None else None\n        super().__init__(self._check)\n\n    def _check(self, exception: BaseException) -> bool:\n        if self.match is None:\n            return self.message == str(exception)\n        return bool(self.match.match(str(exception)))"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192327-bug-retry-if-exception-message-m/base-1/tenacity/retry.py has been updated successfully.
[tool_use Bash] {"command": "ls <work>/env-tenacity/bin/python && git status --short", "description": "Check project test interpreter exists and git status"}
[tool_result] <work>/env-tenacity/bin/python
 M tenacity/retry.py
[assistant] Now I'll add regression tests next to the existing negative tests. I'm adding new cases only and leaving the existing ones untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-192327-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"negative\", match=\"negative\")
…[1086 chars elided]…
(message=\"\")\n        self.assertFalse(retry._check(RuntimeError()))\n        self.assertTrue(retry._check(RuntimeError(\"boom\")))\n\n    def test_retry_if_not_exception_message_empty_match(self) -> None:\n        retry = tenacity.retry_if_not_exception_message(match=\"\")\n        self.assertFalse(retry._check(RuntimeError()))\n        self.assertFalse(retry._check(RuntimeError(\"boom\")))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-192327-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] ...............s.............................................. [ 35%]
...................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.83s
[assistant] All 173 tests pass. I'll run a quick type and lint check on the changed files, since the `is None` narrowing affects the `match` attribute's type.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin; ($P/python -m mypy tenacity/retry.py 2>&1 | tail -3); ($P/python -m ruff check tenacity/retry.py tests/test_tenacity.py 2>&1 | tail -3); git diff --stat", "description": "Run mypy and ruff on changed files"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
 tenacity/retry.py      |  9 ++++-----
 tests/test_tenacity.py | 24 ++++++++++++++++++++++++
 2 files changed, 28 insertions(+), 5 deletions(-)
[assistant] An empty `message` or `match` is now accepted by both `retry_if_exception_message` and `retry_if_not_exception_message`. Passing neither or both still raises `TypeError`. The full suite passes: 173 passed, 1 skipped.

**Cause:** `tenacity/retry.py` tested `message` and `match` for truthiness, so `""` looked the same as "not given". `_check` used the same test to pick a branch.

**Fix** (`tenacity/retry.py`):
- The constructor now checks `is not None`, so only a real value counts as provided.
- `_check` picks its branch by whether a compiled pattern exists (`self.match is None`), so an empty `message` compares exactly against `str(exception)`.

**Tests added** (`tests/test_tenacity.py`, existing tests untouched):
- `message=""` with `match=""` raises `TypeError`.
- `message=""` matches only an exception whose str is empty, for both the positive and negated variants.
- `match=""` matches any exception, for both variants.

Mypy and ruff are not installed in the project's test environment, so I did not run them. Nothing is committed.
