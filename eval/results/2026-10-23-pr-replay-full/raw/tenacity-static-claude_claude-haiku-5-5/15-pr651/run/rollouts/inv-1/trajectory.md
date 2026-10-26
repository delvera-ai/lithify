# trajectory inv-1

final message:
`retry_if_exception_message(message="")` now works, and so does `match=""`. Passing neither argument or both still raises `TypeError`. `retry_if_not_exception_message` gets the same fix, since it inherits the constructor. The full suite passes (172 passed, 1 skipped).

**The cause:** `tenacity/retry.py` tested truthiness (`if message`, `if self.message`) rather than whether the argument was given, so `""` counted as missing. I changed those checks to `is not None` in `__init__` and `_check`.

**Tests:** I added four regression tests to `tests/test_tenacity.py`, and ran them alone against the unfixed code first:
- `message=""` matches `RuntimeError()` and retries.
- `match=""` is accepted and matches a non-empty message.
- `retry_if_not_exception_message(message="")` does not retry on `RuntimeError()` and does retry on `RuntimeError("anything")`.
- `message=""` together with `match="negative"` raises `TypeError`.

Three failed with the reported `TypeError`, and the both-given case failed because no error was raised. All four pass after the fix.

**Release note:** I added `releasenotes/notes/retry-if-exception-message-empty-3f9c1a7d5b2e8064.yaml` as a `fixes:` entry. I did not change `doc/source/index.rst`, since no documented usage changed.

**Checks:** `check_changed.py` exited 0 with 0 problems. ruff, mypy and PyYAML could not run in this environment, so those checks are not run. The reno YAML is not validated by a parser.

**Choice to confirm:** `match=""` matches every exception, because an empty regex matches at the start of any string. I treated that as correct for a valid empty pattern. If you want empty `match` rejected instead, that is a one-line change.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"exception_message\" tenacity/ tests/ doc/ releasenotes/ 2>/dev/null | head -60; echo ---; ls .lithify/harness/scripts/ && cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Locate exception message retry code and harness files"}
[tool_result] tenacity/__init__.py:50:    retry_if_exception_message,
tenacity/__init__.py:52:    retry_if_not_exception_message,
tenacity/__init__.py:804:    "retry_if_exception_message",
tenacity/__init__.py:806:    "retry_if_not_exception_message",
tenacity/retry.py:218:class retry_if_exception_message(retry_if_exception):
tenacity/retry.py:247:class retry_if_not_exception_message(retry_if_exception_message):
tests/test_tenacity.py:920:    def test_retry_if_exception_message_negative_no_inputs(self) -> Non
…[2798 chars elided]…
ge(match="fail.*"),
tests/test_tenacity.py:2205:            tenacity.retry_if_not_exception_message(message="fail"),
doc/source/index.rst:258:    retry_if_exception_message
doc/source/index.rst:259:    retry_if_not_exception_message
---
check_changed.py
run_tests.py
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tenacity/retry.py", "offset": 200, "limit": 70}
[tool_result] 200	        return False
201	
202	
203	class retry_if_not_result(retry_base):
204	    """Retries if the result refutes a predicate."""
205	
206	    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
207	        self.predicate = predicate
208	
209	    def __call__(self, retry_state: "RetryCallState") -> bool:
210	        if retry_state.outcome is None:
211	            raise RuntimeError("__call__() called before outcome was set")
212	
213	        if not retry_state.outcom
…[1597 chars elided]…
lled before outcome was set")
256	
257	        if not retry_state.outcome.failed:
258	            return True
259	
260	        exception = retry_state.outcome.exception()
261	        if exception is None:
262	            raise RuntimeError("outcome failed but the exception is None")
263	        return self.predicate(exception)
264	
265	
266	class retry_any(retry_base):
267	    """Retries if any of the retries condition is valid."""
268	
269	    def __init__(self, *retries: "RetryBaseT") -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tests/test_tenacity.py", "offset": 915, "limit": 16}
[tool_result] 915	            reraise=True,
916	        )
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
930	    """Holds counter state for invoking a method several times in a row."""
[tool_use Bash] {"command": "grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md; ls releasenotes/notes 2>/dev/null | tail -5; ls; sed -n 1,60p .lithify/harness/scripts/run_tests.py | head -80", "description": "Check skill sections, reno dir, and test runner usage"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[2319 chars elided]…
meout = 300.0
    if args[:1] == ["--timeout"]:
        if len(args) < 2:
            print("usage: run_tests.py [--timeout SECS] [pytest args...]")
            return 2
        timeout = float(args[1])
        args = args[2:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "-rfE",
        "-p",
        "no:cacheprovider",
        "--color=no",
        *args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
[tool_use Bash] {"command": "sed -n 321,380p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; echo ----; sed -n 250,265p doc/source/index.rst; grep -n \"exception_message\" -A3 doc/source/index.rst | head; echo ----; grep -n \"exception_message\" -B2 -A8 tests/test_tenacity.py | sed -n 1,5p; sed -n 1385,1392p tests/test_tenacity.py; ls .lithify/harness/memory* 2>/dev/null; cat .lithify/harness/memory.md 2>/dev/null | head -5", "description": "Read contract sections for release note, docs, tests"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[3867 chars elided]…
f_exception_message_match(NoCustomErrorAfterCount(3))
            )
        except CustomError:
            self.fail("CustomError should've been retried from errormessage")

    def test_retry_if_not_exception_message_match(self) -> None:
.lithify/harness/memory.md
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[assistant] The bug is in `retry_if_exception_message.__init__` and `_check`: they test truthiness (`if message`, `if self.message`) instead of `is not None`, so `""` is treated as "not given". I'll write the regression tests first and confirm they fail on the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"negative\", match=\"negative\")\
…[1916 chars elided]…
ttempt(3),\n            wait=tenacity.wait_none(),\n            reraise=True,\n        )\n        with self.assertRaises(RuntimeError):\n            retrying(raise_empty)\n        self.assertEqual(1, retrying.statistics[\"attempt_number\"])\n\n        with self.assertRaises(RuntimeError):\n            retrying(raise_message)\n        self.assertEqual(3, retrying.statistics[\"attempt_number\"])\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the new tests alone against the unfixed code, through the harness runner.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py -k exception_message > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1
    
        retrying = tenacity.Retrying(
>           retry=tenacity.retry_if_not_exception_message(message=""),
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_none(),
            reraise=True,
        )

tests/test_tenacity.py:968: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tenacity.retry.retry_if_not_exception_message object at 0x106ecc6
…[776 chars elided]…
ditions::test_retry_if_exception_message_empty_match
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_empty_message
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_negative_empty_message_and_match
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_not_exception_message_empty_message
================= 4 failed, 7 passed, 123 deselected in 0.18s ==================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All four new tests fail on the unfixed code: three with the reported `TypeError`, and the both-given case because `message=""` slips past the "not both" check. Now the fix, using `is not None` throughout:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tenacity/retry.py", "old_string": "        if message and match:\n            raise TypeError(\n                f\"{self.__class__.__name__}() takes either 'message' or 'match', not both\"\n            )\n\n        if not message and not match:\n         
…[596 chars elided]…
atch is None:\n            raise TypeError(\n                f\"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'\"\n            )\n\n        self.message = message\n        self.match = re.compile(match) if match is not None else None\n        super().__init__(self._check)\n\n    def _check(self, exception: BaseException) -> bool:\n        if self.message is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/tenacity/retry.py has been updated successfully.
[assistant] Now the release note. The contract requires one for any user-visible fix, and this is a `fixes:` entry.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/releasenotes/notes/retry-if-exception-message-empty-3f9c1a7d5b2e8064.yaml", "content": "---\nfixes:\n  - |\n    ``retry_if_exception_message`` and ``retry_if_not_exception_message`` now accept an\n    empty ``message`` or ``match`` argument, so ``retry_if_exception_message(message=\"\")``\n    matches an exception whose message is empty (such as ``RuntimeError()``) instead of\n    raising ``TypeError``. Passing neither argument, or both, still raises ``TypeError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/inv-1/releasenotes/notes/retry-if-exception-message-empty-3f9c1a7d5b2e8064.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py -k exception_message > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; echo ===FULL; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/full.txt; echo ===CHECK; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt", "description": "Run targeted tests, full suite, and changed-file checks"}
[tool_result ERROR] Exit code 1
exit=0

====================== 11 passed, 123 deselected in 0.03s ======================
---
exit=0 (pytest); full log: /tmp/run_tests.log
(eval):1: ==FULL not found
[assistant] The targeted tests pass (11 passed). My `echo ===` label tripped zsh, so I'll rerun the full suite and checks without it.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/full.txt; echo \"---check\"; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] exit=0

============== 172 passed, 1 skipped, 12 subtests passed in 1.85s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
---check
exit=0
changed: releasenotes/notes/retry-if-exception-message-empty-3f9c1a7d5b2e8064.yaml, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] `retry_if_exception_message(message="")` now works, and so does `match=""`. Passing neither argument or both still raises `TypeError`. `retry_if_not_exception_message` gets the same fix, since it inherits the constructor. The full suite passes (172 passed, 1 skipped).

**The cause:** `tenacity/retry.py` tested truthiness (`if message`, `if self.message`) rather than whether the argument was given, so `""` counted as missing. I changed those checks to `is not None` in `__init__` and `_check`.

**Tests:** I added four regression tests to `tests/test_tenacity.py`, and ran them alone against the u
…[513 chars elided]…
if-exception-message-empty-3f9c1a7d5b2e8064.yaml` as a `fixes:` entry. I did not change `doc/source/index.rst`, since no documented usage changed.

**Checks:** `check_changed.py` exited 0 with 0 problems. ruff, mypy and PyYAML could not run in this environment, so those checks are not run. The reno YAML is not validated by a parser.

**Choice to confirm:** `match=""` matches every exception, because an empty regex matches at the start of any string. I treated that as correct for a valid empty pattern. If you want empty `match` rejected instead, that is a one-line change.

Nothing is committed.
