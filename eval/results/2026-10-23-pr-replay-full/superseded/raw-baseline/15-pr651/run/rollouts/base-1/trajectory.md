# trajectory base-1

final message:
`retry_if_exception_message(message="")` now works, and so does `match=""`. The same fix covers `retry_if_not_exception_message`. The full suite passes: 172 passed, 1 skipped.

**Cause:** `tenacity/retry.py` used truthiness checks (`if message`, `if not match`, and so on). An empty string is falsy, so `message=""` was treated as not supplied and raised the "missing argument" `TypeError`.

**Fix** (`tenacity/retry.py`): every check now uses `is not None`. That covers the both-supplied and neither-supplied checks, the regex compile, and the comparison in `_check`. Passing neither or both still raises `TypeError`, including when both are empty strings.

**Tests** (`tests/test_tenacity.py`): I added four tests next to the existing negative tests.
- `message=""` matches an empty-message `RuntimeError` and retries until the attempt limit.
- `match=""` matches and retries the same way.
- `retry_if_not_exception_message(message="")` does not retry an empty-message exception.
- Passing both `message=""` and `match=""` raises `TypeError`.

I ran the three bug tests against the original `retry.py` and they fail with the reported `TypeError`. The fourth test passes on both versions, as expected. I restored the fix afterwards.

I did not commit. `ruff` isn't installed here and `mypy` isn't in the test environment, so I didn't run lint or type checks.

## events
[tool_use Bash] {"command": "grep -n \"exception_message\\|_ExceptionMessage\\|def _retry_if\\|match\" tenacity/retry.py | head -80", "description": "Locate exception-message retry code"}
[tool_result] 218:class retry_if_exception_message(retry_if_exception):
219:    """Retries if an exception message equals or matches."""
224:        match: None | str | re.Pattern[str] = None,
226:        if message and match:
228:                f"{self.__class__.__name__}() takes either 'message' or 'match', not both"
231:        if not message and not match:
233:                f"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'"
237:        self.match = re.compile(match) if match else None
243:        assert self.match is not None
244:        return bool(self.match.match(str(exception)))
247:class retry_if_not_exception_message(retry_if_exception_message):
248:    """Retries until an exception message equals or matches."""
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "offset": 210, "limit": 50}
[tool_result] 210	        if retry_state.outcome is None:
211	            raise RuntimeError("__call__() called before outcome was set")
212	
213	        if not retry_state.outcome.failed:
214	            return not self.predicate(retry_state.outcome.result())
215	        return False
216	
217	
218	class retry_if_exception_message(retry_if_exception):
219	    """Retries if an exception message equals or matches."""
220	
221	    def __init__(
222	        self,
223	        message: str | None = None,
224	      
…[876 chars elided]…
n_message(retry_if_exception_message):
248	    """Retries until an exception message equals or matches."""
249	
250	    def _check(self, exception: BaseException) -> bool:
251	        return not super()._check(exception)
252	
253	    def __call__(self, retry_state: "RetryCallState") -> bool:
254	        if retry_state.outcome is None:
255	            raise RuntimeError("__call__() called before outcome was set")
256	
257	        if not retry_state.outcome.failed:
258	            return True
259	
[assistant] The bug is in the truthiness checks on lines 226, 231, 237 and 241: an empty string is falsy, so `message=""` is treated as not provided. I'll switch them to `is not None` checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "old_string": "        if message and match:\n            raise TypeError(\n                f\"{self.__class__.__name__}() takes either 'message' or 'match', not both\"\n            )\n\n        if not message and not match:\n        
…[597 chars elided]…
atch is None:\n            raise TypeError(\n                f\"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'\"\n            )\n\n        self.message = message\n        self.match = re.compile(match) if match is not None else None\n        super().__init__(self._check)\n\n    def _check(self, exception: BaseException) -> bool:\n        if self.message is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tenacity/retry.py has been updated successfully.
[assistant] Now I'll run a quick behavioural check and the project's test suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -c \"\nfrom tenacity.retry import retry_if_exception_message as r, retry_if_not_exception_message as n\nimport re\nprint(r(message='')(type('S',(object,),{})) if False else '')\nclass FakeState: pass\nfrom t
…[484 chars elided]…
)\nprint('not msg empty on empty -> retry?', n(message='')(state(e)))\nprint('not msg empty on \"x\" -> retry?', n(message='')(state(RuntimeError('x'))))\nfor kw in [{}, {'message':'a','match':'a'}, {'message':'', 'match':'' }]:\n    try: r(**kw); print(kw, 'no error')\n    except TypeError as ex: print(kw, 'TypeError:', ex)\nEOF", "description": "Check fixed behavior for empty message and match"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12

msg empty match True
match empty True
not msg empty on empty -> retry? False
not msg empty on "x" -> retry? True
{} TypeError: retry_if_exception_message() missing 1 required argument 'message' or 'match'
{'message': 'a', 'match': 'a'} TypeError: retry_if_exception_message() takes either 'message' or 'match', not both
{'message': '', 'match': ''} TypeError: retry_if_exception_message() takes either 'message' or 'match', not both
[assistant] The behaviour is right. Next I'll find the existing tests for these predicates so I can add regression coverage, then run the suite.
[tool_use Bash] {"command": "grep -rn \"exception_message\" tests/ | head -40", "description": "Find existing tests for exception message predicates"}
[tool_result] tests/test_tenacity.py:920:    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
tests/test_tenacity.py:922:            tenacity.retry_if_exception_message()
tests/test_tenacity.py:924:    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
tests/test_tenacity.py:926:            tenacity.retry_if_exception_message(message="negative", match="negative")
tests/test_tenacity.py:1188:    retry=tenacity.retry_if_exception_message(
tests/test_tenacity.py:1192
…[2012 chars elided]…
atch(self) -> None:
tests/test_tenacity.py:1395:                _retryable_test_if_not_exception_message_message(
tests/test_tenacity.py:1400:            s = _retryable_test_if_not_exception_message_message.statistics
tests/test_tenacity.py:2203:            tenacity.retry_if_exception_message(message="fail"),
tests/test_tenacity.py:2204:            tenacity.retry_if_exception_message(match="fail.*"),
tests/test_tenacity.py:2205:            tenacity.retry_if_not_exception_message(message="fail"),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "offset": 916, "limit": 14}
[tool_result] 916	        )
917	        self.assertRaises(tenacity.TryAgain, r, _r)
918	        self.assertEqual(5, r.statistics["attempt_number"])
919	
920	    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
921	        with self.assertRaises(TypeError):
922	            tenacity.retry_if_exception_message()
923	
924	    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
925	        with self.assertRaises(TypeError):
926	            tenacity.retry_if_exception_message(message="negative", match="negative")
927	
928	
929	class NoneReturnUntilAfterCount:
[assistant] I'll add regression tests next to the existing negative tests, using the public `retry` decorator so they don't depend on private methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"negative\", match=\"negative\")
…[1794 chars elided]…
ounter())\n        self.assertEqual(1, r.statistics[\"attempt_number\"])\n\n    def test_retry_if_exception_message_empty_inputs_both_raise(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"\", match=\"\")\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_not_exception_message(message=\"\", match=\"\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] I referenced two helpers that don't exist (`_Counter`, `_raise_runtime_error_no_message_until_count`). I'll replace them with a single unconditional-raise helper.
[tool_use Bash] {"command": "/usr/bin/sed -i '' 's/r(_raise_runtime_error_no_message_until_count, _Counter())/r(_raise_empty_runtime_error)/' tests/test_tenacity.py && grep -n \"_raise_empty_runtime_error\\|_Counter\\|until_count, _Counter\" tests/test_tenacity.py; grep -n \"^class NoneReturnUntilAfterCount\" tests/test_tenacity.py", "description": "Fix helper references in new tests"}
[tool_result] 937:            r(_raise_empty_runtime_error)
948:            r(_raise_empty_runtime_error)
960:            r(_raise_empty_runtime_error)
970:class NoneReturnUntilAfterCount:
[This command modified 1 file you've previously read: tests/test_tenacity.py. Call Read before editing.]
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "            tenacity.retry_if_not_exception_message(message=\"\", match=\"\")\n\n\nclass NoneReturnUntilAfterCount:", "new_string": "            tenacity.retry_if_not_exception_message(message=\"\", match=\"\")\n\n\ndef _raise_empty_runtime_error() -> None:\n    raise RuntimeError()\n\n\nclass NoneReturnUntilAfterCount:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164835-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the full test suite with the project's required command:
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ...............s.............................................. [ 35%]
...................................................................... [ 76%]
.........................................                                [100%]
172 passed, 1 skipped, 12 subtests passed in 1.88s
[assistant] All green. To confirm the new tests actually catch the bug, I'll run them against the original `retry.py` and then restore my fix.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cp tenacity/retry.py /tmp/retry_fixed_backup.py && git show HEAD:tenacity/retry.py > tenacity/retry.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k \"empty\" 2>&1 | tail -8; cp /tmp/retry_fixed_backup.py tenacity/retry.py && rm /tmp/retry_fixed_backup.py && git diff --stat", "description": "Confirm new tests fail on original code, then restore fix"}
[tool_result] E           TypeError: retry_if_not_exception_message() missing 1 required argument 'message' or 'match'

tenacity/retry.py:232: TypeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_empty_match
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_empty_message
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_not_exception_message_empty_message
3 failed, 1 passed, 130 deselected in 0.07s
 tenacity/retry.py      |  8 ++++----
 tests/test_tenacity.py | 45 +++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 49 insertions(+), 4 deletions(-)
[assistant] The three bug tests fail on the old code, as intended. The "both inputs raise" test passes on both versions, which is expected because that behaviour was already correct. I'll re-run the suite on the restored fix and the project's lint and type checks.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; (command -v ruff >/dev/null && ruff check tenacity tests && ruff format --check tenacity tests) 2>&1 | tail -3; ($PY -m mypy tenacity 2>&1 | tail -2) ; git status --short", "description": "Re-run tests, lint, and type checks"}
[tool_result] .........................................                                [100%]
172 passed, 1 skipped, 12 subtests passed in 1.81s
<work>/env-tenacity/bin/python: No module named mypy
 M tenacity/retry.py
 M tests/test_tenacity.py
[assistant] `retry_if_exception_message(message="")` now works, and so does `match=""`. The same fix covers `retry_if_not_exception_message`. The full suite passes: 172 passed, 1 skipped.

**Cause:** `tenacity/retry.py` used truthiness checks (`if message`, `if not match`, and so on). An empty string is falsy, so `message=""` was treated as not supplied and raised the "missing argument" `TypeError`.

**Fix** (`tenacity/retry.py`): every check now uses `is not None`. That covers the both-supplied and neither-supplied checks, the regex compile, and the comparison in `_check`. Passing neither or both still r
…[159 chars elided]…
sage=""` matches an empty-message `RuntimeError` and retries until the attempt limit.
- `match=""` matches and retries the same way.
- `retry_if_not_exception_message(message="")` does not retry an empty-message exception.
- Passing both `message=""` and `match=""` raises `TypeError`.

I ran the three bug tests against the original `retry.py` and they fail with the reported `TypeError`. The fourth test passes on both versions, as expected. I restored the fix afterwards.

I did not commit. `ruff` isn't installed here and `mypy` isn't in the test environment, so I didn't run lint or type checks.
