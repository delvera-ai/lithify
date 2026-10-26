# trajectory base-1

final message:
Fixed: `retry_if_exception_message(message="")` and `match=""` now construct and match correctly, and `retry_if_not_exception_message` gets the same fix. Passing both or neither still raises `TypeError`. The changes are uncommitted in the worktree.

**The cause:** the constructor and `_check` used truthiness (`if message and match`, `if self.message:`), so `""` was treated as "not given". With `message=""`, `_check` would also have fallen through to the `match` branch and hit an assertion, so both spots needed the change.

**Changes:**
- `tenacity/retry.py`: the constructor checks `is not None` / `is None`, and `_check` tests `self.message is not None`. `retry_if_not_exception_message` inherits the fix.
- `tests/test_tenacity.py` (in `TestRetryConditions`): five new tests.
  - Red before the fix: empty message with a retry on `RuntimeError()`, empty match with a retry on `RuntimeError("boom")`, `not` variant with empty message, and `message=""` with `match="negative"` (which should raise `TypeError`).
  - Guard, passing before and after: `message=""` with `match=""` raises `TypeError`.
  - The new tests call `Retrying(...)(fn)` rather than `@retry(...)`. The checker's nested-def rule flags a `def` directly after a multi-line decorator, and ruff puts no blank line there, so the plain call avoids the conflict.
- `releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml`: a `fixes:` note, as the tenacity contract requires for user-visible changes.

**Checks (project harness):**
- Red run: the four tests that should fail did fail with the reported reason. The both-empty guard passed, as intended.
- Targeted run after the fix: 5 passed, exit 0.
- Full suite: 173 passed, 1 skipped, exit 0.
- `check_changed.py`: PASS, 0 problems, exit 0.
- **Not run:** ruff and mypy (the harness says they can't run here).

**Choices I made:**
- No docs change in `doc/source/index.rst`: the documented usage doesn't change, and the contract only requires docs for new API or usage forms.
- A bare `match=""` is a valid empty regex that matches every message, so it's accepted as "match anything", consistent with regex semantics.

I did not commit, since you didn't ask for one.

## events
[assistant] I'll start by finding the predicate and its tests.
[tool_use Bash] {"command": "grep -rn \"exception_message\" --include='*.py' --include='*.rst' . | head -50; echo ---; cat .lithify/memory.md 2>/dev/null | head -30; ls .lithify/harness/scripts/", "description": "Locate exception-message predicates and harness files"}
[tool_result] tests/test_tenacity.py:920:    def test_retry_if_exception_message_negative_no_inputs(self) -> None:
tests/test_tenacity.py:922:            tenacity.retry_if_exception_message()
tests/test_tenacity.py:924:    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:
tests/test_tenacity.py:926:            tenacity.retry_if_exception_message(message="negative", match="negative")
tests/test_tenacity.py:1188:    retry=tenacity.retry_if_exception_message(
tests/test_tenacity.py:1192
…[2564 chars elided]…
age,
tenacity/__init__.py:52:    retry_if_not_exception_message,
tenacity/__init__.py:804:    "retry_if_exception_message",
tenacity/__init__.py:806:    "retry_if_not_exception_message",
tenacity/retry.py:218:class retry_if_exception_message(retry_if_exception):
tenacity/retry.py:247:class retry_if_not_exception_message(retry_if_exception_message):
doc/source/index.rst:258:    retry_if_exception_message
doc/source/index.rst:259:    retry_if_not_exception_message
---
check_changed.py
run_tests.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "offset": 200, "limit": 70}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "offset": 915, "limit": 15}
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
[assistant] The bug is in `retry_if_exception_message.__init__` and `_check`: they use truthiness (`if message and match`, `if self.message:`) where they need `is None` checks. Since this changes tenacity user-facing behaviour, the project's contract skill applies, so I'll read it before editing.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; head -40 .lithify/harness/scripts/run_tests.py; echo ---; ls releasenotes/notes 2>/dev/null | tail -5; git status --short", "description": "Read tenacity change contract skill and harness script header"}
[tool_result] <persisted-output>
Output too large (30.9KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-8ffc43e3927e-20261023-214407-bug-retry-if-exception-message-m-base-1/b9f2f5cf-4115-42e4-be67-57a432e5fa35/tool-results/bp34cw7n2.txt

Preview (first 2KB):
---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`,
…[1273 chars elided]…
ository history and config. Check each item before finishing.

## 1. Code goes in the module that owns the concern
- `tenacity/_utils.py` — shared helpers (`find_ordinal`/`to_ordinal`, `get_callback_name`,
  `LoggerProtocol`, `MAX_WAIT`). The logging callbacks in `tenacity/before.py`,
  `tenacity/after.py`, `tenacity/before_sleep.py` call these helpers; fix the helper, not the
  callers.
- Strategies live in `tenacity/wait.py`, `tenacity/stop.py`, `tenacity/retry.py`; the
...
</persisted-output>
[tool_use Bash] {"command": "sed -n '1,200p' .lithify/harness/skills/tenacity-change-contract/SKILL.md | tail -n +12 | head -150; echo ---; ls releasenotes/notes | tail -5; ls .lithify/; cat .lithify/memory.md 2>/dev/null", "description": "Read rest of tenacity contract skill and reno notes dir"}
[tool_result ERROR] Exit code 1
  `LoggerProtocol`, `MAX_WAIT`). The logging callbacks in `tenacity/before.py`,
  `tenacity/after.py`, `tenacity/before_sleep.py` call these helpers; fix the helper, not the
  callers.
- Strategies live in `tenacity/wait.py`, `tenacity/stop.py`, `tenacity/retry.py`; the
  `Retrying`/`retry()` core and its type overloads in `tenacity/__init__.py`; async in
  `tenacity/asyncio/`.

## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
- `BaseRetrying` owns the loop once
…[9039 chars elided]…
ing`, `AsyncRetrying` and `TornadoRetrying` add no instance state of their own beyond
  `sleep`, so they inherit them; no async copy needed.
- `BaseRetrying.copy()` (used by `wraps`' per-call copy and `retry_with`) rebuilds through
---
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
harness
library
state.json
[assistant] The contract requires a reno note, a test and possibly user docs. I'll check the exact requirements and an existing note's format.
[tool_use Bash] {"command": "grep -n -i \"reno\\|index.rst\\|## [0-9]\" .lithify/harness/skills/tenacity-change-contract/SKILL.md | head -60; echo ---; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml; echo ---; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; echo ---; cat .lithify/state.json | head -c 600", "description": "Find reno and docs requirements in contract skill"}
[tool_result] 3:description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, the `enabled` switch, which excepti
…[3791 chars elided]…
tils-find-ordinal",
      "k": 1,
      "first_pass": true,
      "delivered": true,
      "churn_lines": 43,
      "executions": 4,
      "tokens_in": 271294,
      "tokens_cached": 2302153,
      "tokens_out": 35584,
      "cost_usd": 2.0616,
      "wall_s": 355.6,
      "always_on_tokens": 186,
      "stability_after": 0.14
    },
    {
      "task_id": "20261023-190230-bug-tenacity-after-log-crashes-w",
      "k": 1,
      "first_pass": true,
      "delivered": true,
      "churn_lines": 153
[tool_use Bash] {"command": "sed -n '321,370p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls releasenotes/notes | grep -i \"bug\\|fix\" | head; echo ---; for f in $(ls releasenotes/notes | grep -i \"fix\" | head -2); do echo \"== $f\"; cat releasenotes/notes/$f; done; echo ---; sed -n '250,265p' doc/source/index.rst; cat .lithify/harness/scripts/run_tests.py | head -30 | grep -n \"python\\|PY\\|usage\" ", "description": "Read reno and test requirements, and example fix notes"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[3698 chars elided]…

    retry_if_exception
    retry_if_exception_type
    retry_if_not_exception_type
    retry_unless_exception_type
    retry_if_result
    retry_if_not_result
    retry_if_exception_message
    retry_if_not_exception_message
    retry_any
    retry_all

We can also combine several conditions:

.. testcode::
1:#!/usr/bin/env python3
9:Usage (from the repo root, with the project python from memory.md):
10:    <project python> .lithify/harness/scripts/run_tests.py [--timeout SECS] [pytest args...]
[assistant] The existing negative tests sit around `tests/test_tenacity.py:920`. I'll add the regression tests there first, then run them against the unfixed code. I'm checking that the project interpreter from `memory.md` exists before running anything.
[tool_use Bash] {"command": "ls -la <work>/env-tenacity/bin/python && grep -n \"^class \\|^import\\|^from\" tests/test_tenacity.py | head -40", "description": "Verify project python exists and list test classes"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
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
27:import
…[693 chars elided]…
class NoCustomErrorAfterCount:
1109:class CapturingHandler(logging.Handler):
1257:class TestDecoratorWrapper(unittest.TestCase):
1501:class TestStatisticsKeys:
1547:class TestEnabled:
1634:class TestRetryWith:
1672:class TestBeforeAfterAttempts(unittest.TestCase):
1825:class TestReraiseExceptions(unittest.TestCase):
1894:class TestStatistics(unittest.TestCase):
1946:class TestRetryErrorCallback(unittest.TestCase):
1979:class TestContextManager(unittest.TestCase):
2034:class TestInvokeAsCallable:
[assistant] Now I'll add the regression tests to `TestRetryConditions`, after the existing negative tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_negative_too_many_inputs(self) -> None:\n        with self.assertRaises(TypeError):\n            tenacity.retry_if_exception_message(message=\"negative\", match=\"negative\")
…[1931 chars elided]…
           stop=tenacity.stop_after_attempt(3),\n            wait=tenacity.wait_none(),\n        )\n        def raise_empty_message() -> None:\n            calls.append(1)\n            raise RuntimeError()\n\n        # The message is \"\", so it matches and is not retried.\n        with self.assertRaises(RuntimeError):\n            raise_empty_message()\n        self.assertEqual(1, len(calls))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Next, the red run: each new test must fail against the unfixed code for the reported reason.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; T=tests/test_tenacity.py::TestRetryConditions; $P .lithify/harness/scripts/run_tests.py --timeout 60 $T::test_retry_if_exception_message_negative_empty_message_and_match $T::test_retry_if_exception_message_negative_empty_message_with_match $T::test_retry_if_exception_message_empty_message $T::test_retry_if_exception_message_empty_match $T::test_retry_if_not_exception_message_empty_message > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red.txt", "description": "Run new regression tests against unfixed code"}
[tool_result] exit=1

    def test_retry_if_not_exception_message_empty_message(self) -> None:
        calls: list[int] = []
    
        @tenacity.retry(
>           retry=tenacity.retry_if_not_exception_message(message=""),
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_none(),
        )

tests/test_tenacity.py:972: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <
…[842 chars elided]…
itions::test_retry_if_exception_message_negative_empty_message_with_match
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_empty_message
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_exception_message_empty_match
FAILED tests/test_tenacity.py::TestRetryConditions::test_retry_if_not_exception_message_empty_message
========================= 4 failed, 1 passed in 0.10s ==========================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The red run is as expected. Four tests fail for the reported reason, and the both-empty guard passes because that case already raised. Now the fix: switch the truthiness checks to `is None` checks in both `__init__` and `_check`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tenacity/retry.py", "old_string": "        if message and match:\n            raise TypeError(\n                f\"{self.__class__.__name__}() takes either 'message' or 'match', not both\"\n            )\n\n        if not message and not match:\n        
…[597 chars elided]…
atch is None:\n            raise TypeError(\n                f\"{self.__class__.__name__}() missing 1 required argument 'message' or 'match'\"\n            )\n\n        self.message = message\n        self.match = re.compile(match) if match is not None else None\n        super().__init__(self._check)\n\n    def _check(self, exception: BaseException) -> bool:\n        if self.message is not None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tenacity/retry.py has been updated successfully.
[assistant] Next I'll run the five targeted tests green, then the full suite.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; T=tests/test_tenacity.py::TestRetryConditions; $P .lithify/harness/scripts/run_tests.py --timeout 60 $T::test_retry_if_exception_message_negative_empty_message_and_match $T::test_retry_if_exception_message_negative_empty_message_
…[11 chars elided]…
$T::test_retry_if_exception_message_empty_message $T::test_retry_if_exception_message_empty_match $T::test_retry_if_not_exception_message_empty_message > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; echo ===FULL; $P .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt", "description": "Run targeted tests green, then full test suite"}
[tool_result ERROR] Exit code 1
exit=0

============================== 5 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
(eval):1: ==FULL not found
[assistant] The targeted tests pass (5 passed). My `echo ===FULL` line was rejected by the shell, so the full suite did not run. Re-running it with a safe separator.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt", "description": "Run full test suite"}
[tool_result] exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 173 passed, 1 skipped, 12 subtests passed in 1.83s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] The full suite passes: 173 passed, 1 skipped, exit 0. The contract requires a reno `fixes:` note for this user-visible change, so I'll add one. The docs need no update because no documented usage changes.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml", "content": "---\nfixes:\n  - |\n    ``retry_if_exception_message`` and ``retry_if_not_exception_message`` now accept\n    an empty string for ``message`` or ``match`` and match it correctly, instead of\n    raising ``TypeError``. Passing both arguments, or neither, still raises ``TypeError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/check.txt; echo ---; git status --short; git diff --stat", "description": "Run stdlib lint substitute and show changed files"}
[tool_result] exit=1
changed: releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml, tenacity/retry.py, tests/test_tenacity.py
FAIL tests/test_tenacity.py:944: nested def needs a blank line before it
FAIL tests/test_tenacity.py:960: nested def needs a blank line before it
FAIL tests/test_tenacity.py:976: nested def needs a blank line before it
FAIL: 3 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---
 M tenacity/retry.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml
 tenacity/retry.py      |  8 +++----
 tests/test_tenacity.py | 57 ++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 61 insertions(+), 4 deletions(-)
[assistant] The stdlib checker flags three nested defs. Before changing anything I'll look at the exact lines, since the skill's rule is specific about where the blank line goes.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "offset": 936, "limit": 12}
[tool_result] 936	    def test_retry_if_exception_message_empty_message(self) -> None:
937	        calls: list[int] = []
938	
939	        @tenacity.retry(
940	            retry=tenacity.retry_if_exception_message(message=""),
941	            stop=tenacity.stop_after_attempt(3),
942	            wait=tenacity.wait_none(),
943	        )
944	        def raise_empty_message() -> None:
945	            calls.append(1)
946	            raise RuntimeError()
947	
[assistant] The file has the blank line before the `@` but none after the `)`, which the skill's rule says is correct. The checker disagrees, so I'll read its rule rather than guess.
[tool_use Bash] {"command": "grep -n -B12 -A6 \"nested def needs\" .lithify/harness/scripts/check_changed.py | head -80", "description": "Read the checker's nested-def rule"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"blank\" .lithify/harness/scripts/check_changed.py | head; ", "description": "Search checker for blank-line rule"}
[tool_result] 12:      * a nested `def`/`class` is preceded by a blank line (ruff format)
99:                    f"{path}:{no}: nested {m.group(2)} needs a blank line before it"
[tool_use Bash] {"command": "sed -n '80,105p' .lithify/harness/scripts/check_changed.py", "description": "Read checker's nested-def logic"}
[tool_result]     errs += check_annotations(path, src, changed)
    lines = src.splitlines()
    for no in sorted(changed):
        if no > len(lines):
            continue
        line = lines[no - 1]
        if len(line) > MAX_LEN:
            errs.append(f"{path}:{no}: line is {len(line)} columns (max {MAX_LEN})")
        if "\t" in line:
            errs.append(f"{path}:{no}: tab character")
        if line != line.rstrip():
            errs.append(f"{path}:{no}: trailing whitespace")
        m = DEF_RE.m
…[22 chars elided]…
m and no >= 2:
            prev = lines[no - 2]
            prev_s = prev.strip()
            opener = prev_s.endswith(":") or prev_s.startswith(("@", "#"))
            if prev_s and not opener:
                errs.append(
                    f"{path}:{no}: nested {m.group(2)} needs a blank line before it"
                )
    return errs


def check_annotations(path: str, src: str, changed: set[int]) -> list[str]:
    """mypy-strict proxy: an added def must annotate every param and return."""
[assistant] The checker's rule is a heuristic: it flags any nested `def` whose previous line is a non-blank line that doesn't end in `:`, which includes the `)` closing a multi-line decorator. The skill says ruff format puts no blank line there. Rather than fight the checker, I'll drop the decorator and call `tenacity.Retrying(...)(fn)` directly. That keeps each nested `def` after a blank line, which satisfies both the checker and ruff.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py", "old_string": "    def test_retry_if_exception_message_empty_message(self) -> None:\n        calls: list[int] = []\n\n        @tenacity.retry(\n            retry=tenacity.retry_if_exception_message(message=\"\"),\n            sto
…[2766 chars elided]…
    retrying = Retrying(\n            retry=tenacity.retry_if_not_exception_message(message=\"\"),\n            stop=tenacity.stop_after_attempt(3),\n            wait=tenacity.wait_none(),\n        )\n        # The message is \"\", so it matches and is not retried.\n        with self.assertRaises(RuntimeError):\n            retrying(raise_empty_message)\n        self.assertEqual(1, len(calls))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-214407-bug-retry-if-exception-message-m/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] I changed the tests, so I'll re-run the targeted tests, the full suite and the checker, reading each `exit=` line.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; T=tests/test_tenacity.py::TestRetryConditions; $P .lithify/harness/scripts/run_tests.py --timeout 60 $T::test_retry_if_exception_message_negative_empty_message_and_match $T::test_retry_if_exception_message_negative_empty_message_
…[107 chars elided]…
h $T::test_retry_if_not_exception_message_empty_message > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green.txt; $P .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full.txt; $P .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -8 /tmp/check.txt", "description": "Re-run targeted tests, full suite, and checker"}
[tool_result] exit=0
============================== 5 passed in 0.04s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
============== 173 passed, 1 skipped, 12 subtests passed in 1.80s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
changed: releasenotes/notes/fix-retry-if-exception-message-empty-4c1e9a07d2b35f68.yaml, tenacity/retry.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Fixed: `retry_if_exception_message(message="")` and `match=""` now construct and match correctly, and `retry_if_not_exception_message` gets the same fix. Passing both or neither still raises `TypeError`. The changes are uncommitted in the worktree.

**The cause:** the constructor and `_check` used truthiness (`if message and match`, `if self.message:`), so `""` was treated as "not given". With `message=""`, `_check` would also have fallen through to the `match` branch and hit an assertion, so both spots needed the change.

**Changes:**
- `tenacity/retry.py`: the constructor checks `is not None
…[1007 chars elided]…
-empty guard passed, as intended.
- Targeted run after the fix: 5 passed, exit 0.
- Full suite: 173 passed, 1 skipped, exit 0.
- `check_changed.py`: PASS, 0 problems, exit 0.
- **Not run:** ruff and mypy (the harness says they can't run here).

**Choices I made:**
- No docs change in `doc/source/index.rst`: the documented usage doesn't change, and the contract only requires docs for new API or usage forms.
- A bare `match=""` is a valid empty regex that matches every message, so it's accepted as "match anything", consistent with regex semantics.

I did not commit, since you didn't ask for one.
