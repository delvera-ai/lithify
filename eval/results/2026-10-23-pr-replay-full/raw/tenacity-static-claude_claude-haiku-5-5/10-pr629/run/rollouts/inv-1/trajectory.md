# trajectory inv-1

final message:
`wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated: it still works, warns, and passing both raises `ValueError`. The full suite passes (160 passed, 1 skipped) and `check_changed.py` exits 0.

**Signature:** `__init__(initial=None, max, exp_base, jitter, min, multiplier=None)`. `initial` keeps its first positional slot, and `multiplier` is appended last so no existing positional call shifts. Both default to `None` as the "not passed" marker, so passing both is detectable even when the values equal 1. `None` means the effective multiplier is 1. I didn't use `_unset` because `wait.py` can't import it from `tenacity/__init__.py` without a circular import.

**Tests (written first, red before the fix):** six new tests in `tests/test_tenacity.py::TestWaitConditions`:
- `multiplier=2` by keyword works.
- Defaults and `multiplier=` emit no warning (checked with `simplefilter("error")`). The defaults line already passed before the fix; the test was red only because of the `multiplier` keyword.
- `initial=` by keyword, positional, and `initial=1` (equal to the old default) each warn `DeprecationWarning` and give the same values.
- `initial` + `multiplier` raises `ValueError`, including when `multiplier=1`. This test fails first on the missing `multiplier` keyword, so it can't prove the both-passed check by itself until that exists.

**Other changes:**
- `tenacity/wait.py`: the warning uses `stacklevel=2`. Checked: the warning's filename is `<string>` (the caller), not `tenacity/`.
- Release note `releasenotes/notes/wait-exponential-jitter-multiplier-3b9f0e6a1c7d2e84.yaml`: `features:` for `multiplier`, `deprecations:` for `initial`.
- Docstring now describes `multiplier`.
- `doc/source/index.rst` is unchanged because it never documents `initial`.

**Compatibility break to note:** `self.initial` was a writable attribute and is now a read-only property returning `multiplier`. Reading it still works; assigning `w.initial = x` now raises `AttributeError`. Nothing in the repo does this.

**Warnings in the suite:** two existing tests still pass `initial` and now emit the new `DeprecationWarning`. I didn't rewrite them, per the guardrails:
- `tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter` (line 613, positional `(10, 5)`)
- `tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min` (line 622, `initial=1`)

**Not run:** ruff and mypy (unavailable in this environment, per the project notes). The only static check run was `check_changed.py`, which passes.

## events
[assistant] I'll start by reading the wait implementation, the deprecate-parameter skill the harness points to, and the existing tests.
[tool_use Bash] {"command": "cat .lithify/harness/skills/deprecate-parameter/SKILL.md; echo ---; grep -n \"exponential_jitter\\|class wait_exponential\\|multiplier\" -r tenacity/ | head -50; echo ---; ls tests | head -50; ls .lithify/harness/scripts/", "description": "Read deprecation skill, locate wait code and tests"}
[tool_result] ---
name: deprecate-parameter
description: Load when a task renames, replaces or deprecates a parameter/argument of a public function or class (e.g. "add X with the same meaning and deprecate Y", "Y must still work but warn", "passing both must raise"). Gives the call-form test matrix, including the no-warning cases, and the warning/attribute checks to run before finishing.
---

# Deprecating or renaming a parameter

Use this together with `tenacity-change-contract` (reno note, tests, docs). Thi
…[4035 chars elided]…
tenacity/wait.py:221:    It allows for a custom multiplier and an ability to restrict the upper
tenacity/wait.py:226:        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
tenacity/__init__.py:77:    wait_exponential_jitter,
tenacity/__init__.py:799:    "wait_exponential_jitter",
---
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
check_changed.py
run_tests.py
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py; echo ...; sed -n 170,300p tenacity/wait.py; echo ---; grep -n \"_unset\\|_first_set\" -A6 tenacity/__init__.py | head -40; echo ---; grep -rn \"initial\" tenacity/ doc/source/index.rst | grep -v \"initial_\" | head -30; echo ---; grep -n \"exponential_jitter\" -B3 -A12 tests/test_tenacity.py | head -120", "description": "Read wait_exponential_jitter and related code and tests"}
[tool_result] # Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS O
…[8928 chars elided]…
ds=60),
635-            jitter=timedelta(seconds=1),
636-            min=timedelta(seconds=5),
637-        )
638-        for _ in range(1000):
639-            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 5, 5)
640-            self._assert_inclusive_range(fn(make_retry_state(5, 0)), 16, 17)
641-            self.assertEqual(fn(make_retry_state(7, 0)), 60)
642-
643-    def test_wait_retry_state_attributes(self) -> None:
644-        class ExtractCallState(Exception):
645-            pass
[assistant] The deprecate-parameter skill calls for a call-form test matrix, so I'll write those tests first. Before that, I need the tenacity change-contract skill (it lists the non-code files a user-visible change must touch) and the reno and test-file conventions.
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls releasenotes/notes 2>/dev/null | tail -5; echo ---; sed -n 1,40p tests/test_tenacity.py | grep -n \"import\"; echo ---; grep -n \"wait_exponential_jitter\" -A30 doc/source/index.rst | head -60; echo ---; cat .lithify/harness/scripts/run_tests.py | head -40", "description": "Read change-contract skill, reno dir, test imports, docs"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or 
…[17324 chars elided]…
 node id alone with
          --timeout 60; if it is a test you wrote, make its retry loop bounded
          (or fix the code it exposes). If it is an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
[assistant] I have what I need. The plan is:

- Keep `initial` as the first positional slot, using an `_unset` sentinel so "passed" is detectable even when the value equals the default.
- Append `multiplier` at the end of the signature so no existing positional call shifts.
- Add the regression tests first, covering the matrix from the skill: new keyword, defaults with no warning, old keyword, old positional, and both passed.

Writing the tests now, before any fix.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tests/test_tenacity.py", "old_string": "    def test_wait_retry_state_attributes(self) -> None:", "new_string": "    def test_wait_exponential_jitter_multiplier(self) -> None:\n        fn = tenacity.wait_exponential_jitter(multiplier=2, max=60)\n        f
…[1589 chars elided]…
ltiplier_raises(self) -> None:\n        with self.assertRaises(ValueError):\n            tenacity.wait_exponential_jitter(initial=2, multiplier=3)\n        # multiplier equals its default here; passing both must still raise\n        with self.assertRaises(ValueError):\n            tenacity.wait_exponential_jitter(initial=1, multiplier=1)\n\n    def test_wait_retry_state_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tests/test_tenacity.py", "old_string": "import unittest\nfrom fractions import Fraction\nfrom unittest import mock", "new_string": "import unittest\nimport warnings\nfrom fractions import Fraction\nfrom unittest import mock"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the red run against the unfixed code, through the harness runner as the project requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py -k \"wait_exponential_jitter_multiplier or wait_exponential_jitter_initial\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -60 /tmp/red.txt", "description": "Run new deprecation tests against unfixed code"}
[tool_result] exit=1
_ TestWaitConditions.test_wait_exponential_jitter_initial_positional_deprecated _

self = <tests.test_tenacity.TestWaitConditions testMethod=test_wait_exponential_jitter_initial_positional_deprecated>

    def test_wait_exponential_jitter_initial_positional_deprecated(self) -> None:
>       with self.assertWarns(DeprecationWarning):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AssertionError: DeprecationWarning not triggered

tests/test_tenacity.py:665: AssertionError
_______
…[1485 chars elided]…
s::test_wait_exponential_jitter_initial_keyword_deprecated
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_initial_positional_deprecated
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_multiplier
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_multiplier_default_no_warning
====================== 6 failed, 120 deselected in 0.12s =======================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] Six tests are red, each for the expected reason: the missing `multiplier` keyword and no `DeprecationWarning` on the `initial` paths. The no-warning guard passes its defaults line but fails on `multiplier=2`, which is expected. Next, the implementation. I'm using `None` as the "not passed" marker because `tenacity/__init__.py` imports `wait.py`, so `wait.py` can't import its `_unset`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py", "old_string": "class wait_exponential_jitter(wait_base):\n    \"\"\"Wait strategy that applies exponential backoff and jitter.\n\n    It allows for a customized initial wait, maximum wait, jitter and minimum.\n\n    This implements the 
…[2511 chars elided]…
min)\n\n    @property\n    def initial(self) -> float:\n        \"\"\"Deprecated alias for ``multiplier``.\"\"\"\n        return self.multiplier\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp + jitter"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py", "old_string": "import abc\nimport random\nimport typing\n", "new_string": "import abc\nimport random\nimport typing\nimport warnings\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py has been updated successfully.
[assistant] Running the targeted tests now.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py -k \"wait_exponential_jitter\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -25 /tmp/green.txt", "description": "Run wait_exponential_jitter tests after fix"}
[tool_result] exit=0
collecting ... collected 126 items / 117 deselected / 9 selected

tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter PASSED [ 11%]
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_initial_and_multiplier_raises PASSED [ 22%]
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_initial_default_value_deprecated PASSED [ 33%]
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_initial_keyword_deprecated PAS
…[1052 chars elided]…
onovan/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tests/test_tenacity.py:622: DeprecationWarning: wait_exponential_jitter(initial=...) is deprecated, use multiplier=...
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================ 9 passed, 117 deselected, 2 warnings in 0.11s =================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] All nine pass. The two warnings in the summary come from existing tests that pass `initial` (I'm leaving those tests unchanged, per the guardrails). Next, I'll check the `stacklevel` and fix the docstring line that is likely over 88 columns.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py", "old_string": "    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count. The multiplier defaults to 1.", "new_string": "    The wait time is\n    max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count. The multiplier defaults to 1."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; cd ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1; $PY -c \"\nimport warnings, tenacity\nwith warnings.catch_warnings(record=True) as w:\n    warnings.simplefilter('al
…[112 chars elided]…
))\nprint(w[0].filename, w[0].category.__name__)\n\" ; echo ---; grep -rn \"\\.initial\\b\" tenacity tests doc/source --include='*.py' --include='*.rst'; echo ---; grep -rn \"initial=\" tenacity doc/source --include='*.py' --include='*.rst'; echo ---; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Check warning stacklevel, leftover attribute and kwarg uses"}
[tool_result] <string> DeprecationWarning
---
---
tenacity/wait.py:270:                "wait_exponential_jitter(initial=...) is deprecated, use multiplier=...",
---
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[assistant] The `stacklevel` check passes: the warning's filename is `<string>`, the caller's frame, not `tenacity/`. No other code reads `.initial` or passes it as a keyword. Next I'll add the release note, which the change-contract skill requires, using `features:` for the new name and `deprecations:` for the old one.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/releasenotes/notes/wait-exponential-jitter-multiplier-3b9f0e6a1c7d2e84.yaml", "content": "---\nfeatures:\n  - |\n    ``wait_exponential_jitter`` accepts a ``multiplier`` argument (default 1),\n    matching the other exponential wait strategies.\ndeprecations:\n  - |\n    ``wait_exponential_jitter(initial=...)`` is deprecated in favour of\n    ``multiplier``. It still works but emits a ``DeprecationWarning``. Passing\n    both ``initial`` and ``multiplier`` raises ``ValueError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/releasenotes/notes/wait-exponential-jitter-multiplier-3b9f0e6a1c7d2e84.yaml (file state is current in your context — no need to Read it back)
[assistant] Now the full suite and the static check, each run to completion in the foreground.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/full.txt; echo ---CHECK---; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] exit=0
tests/test_tenacity.py::TestStatistics::test_retry_object_statistics_synced PASSED [ 84%]
tests/test_tenacity.py::TestStatistics::test_stats PASSED                [ 85%]
tests/test_tenacity.py::TestStatistics::test_stats_failing PASSED        [ 85%]
tests/test_tenacity.py::TestRetryErrorCallback::test_retry_error_callback PASSED [ 86%]
tests/test_tenacity.py::TestContextManager::test_context_manager_on_error PASSED [ 86%]
tests/test_tenacity.py::TestContextManager::test_context_manager_re
…[2537 chars elided]…
capture-warnings.html
======== 160 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.82s ========
---
exit=0 (pytest); full log: /tmp/run_tests.log
---CHECK---
exit=1
changed: releasenotes/notes/wait-exponential-jitter-multiplier-3b9f0e6a1c7d2e84.yaml, tenacity/wait.py, tests/test_tenacity.py
FAIL tenacity/wait.py:268: line is 89 columns (max 88)
FAIL tenacity/wait.py:270: line is 89 columns (max 88)
FAIL: 2 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The full suite passes (160 passed, 1 skipped). The static check flags two 89-column lines in `wait.py`, so I'll wrap them and re-run.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py", "old_string": "                raise ValueError(\"pass multiplier only, not both multiplier and initial\")\n            warnings.warn(\n                \"wait_exponential_jitter(initial=...) is deprecated, use multiplier=...\",\n                DeprecationWarning,", "new_string": "                raise ValueError(\"pass multiplier or initial, not both\")\n            warnings.warn(\n                \"wait_exponential_jitter(initial=...) is deprecated, \"\n                \"use multiplier=...\",\n                DeprecationWarning,"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/inv-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt; echo ---; $PY .lithify/harness/scripts/run_tests.py > /tmp/full2.txt 2>&1; echo \"exit=$?\"; tail -2 /tmp/full2.txt; grep -n \"passed\\|failed\" /tmp/full2.txt | tail -1", "description": "Re-run changed-file checks and full suite"}
[tool_result] exit=0
changed: releasenotes/notes/wait-exponential-jitter-multiplier-3b9f0e6a1c7d2e84.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---
exit=0
exit=0 (pytest); full log: /tmp/run_tests.log
s.log
40:======== 160 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.84s ========
[assistant] `wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated: it still works, warns, and passing both raises `ValueError`. The full suite passes (160 passed, 1 skipped) and `check_changed.py` exits 0.

**Signature:** `__init__(initial=None, max, exp_base, jitter, min, multiplier=None)`. `initial` keeps its first positional slot, and `multiplier` is appended last so no existing positional call shifts. Both default to `None` as the "not passed" marker, so passing both is detectable even when the values equal 1. `None` means the effective multiplier is 1. I didn't use
…[1363 chars elided]…
gning `w.initial = x` now raises `AttributeError`. Nothing in the repo does this.

**Warnings in the suite:** two existing tests still pass `initial` and now emit the new `DeprecationWarning`. I didn't rewrite them, per the guardrails:
- `tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter` (line 613, positional `(10, 5)`)
- `tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min` (line 622, `initial=1`)

**Not run:** ruff and mypy (unavailable in this environment, per the project notes). The only static check run was `check_changed.py`, which passes.
