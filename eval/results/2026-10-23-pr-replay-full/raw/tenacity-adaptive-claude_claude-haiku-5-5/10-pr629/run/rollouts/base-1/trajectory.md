# trajectory base-1

final message:
`wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated as you specified. The full project suite passes: 158 passed, 1 skipped, with the project's pytest command.

Changes, all in the worktree and uncommitted:

- **`tenacity/wait.py`**: `initial` stays first, so positional and keyword calls still work. `multiplier` is added at the end of the signature, so existing positional calls keep their meaning.
  - Passing `initial` emits a `DeprecationWarning` pointing at `multiplier`.
  - Passing both raises `ValueError`.
  - Both parameters default to `None`. That is what lets the code tell an explicit `multiplier=1` apart from the default; the effective default is still 1.
- **`tests/test_tenacity.py`**: four new tests cover the multiplier math, the deprecation warning (keyword and positional), no warning on the new path, and the conflict error. I left the existing tests untouched, per the project guardrail. They still pass, but they now emit the deprecation warning.
- **`releasenotes/notes/wait-exponential-jitter-multiplier-3e7a9c1d5b2f8a64.yaml`**: a new feature note and a deprecation note.

Two things to be aware of:

- The `self.initial` attribute is gone; the value is now stored as `self.multiplier`. Code that reads `.initial` off the instance would break. I didn't add a compatibility alias because the request didn't ask for one.
- ruff and mypy aren't installed in the project's test environment, so I couldn't run the linters. I checked added lines against the 88-column limit by hand; E501 is ignored in this project anyway.

Nothing has been committed.

## events
[tool_use Bash] {"command": "grep -n \"wait_exponential_jitter\" -r --include=*.py --include=*.md . | head -50; echo ---; grep -n \"class wait_exponential\\b\" -A60 tenacity/wait.py | head -90", "description": "Locate wait_exponential_jitter and related code"}
[tool_result] (eval):1: no matches found: --include=*.py
---
175:class wait_exponential(wait_base):
176-    """Wait strategy that applies exponential backoff.
177-
178-    It allows for a customized multiplier and an ability to restrict the
179-    upper and lower limits to some maximum and minimum value.
180-
181-    The intervals are fixed (i.e. there is no jitter), so this strategy is
182-    suitable for balancing retries against latency when a required resource is
183-    unavailable for an unknown durat
…[1713 chars elided]…
224-    Example::
225-
226-        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
227-                                max=60)          # max 60s timeout
228-
229-    When waiting for an unavailable resource to become available again, as
230-    opposed to trying to resolve contention for a shared resource, the
231-    wait_exponential strategy (which uses a fixed interval) may be preferable.
232-
233-    """
234-
235-    def __call__(self, retry_state: "RetryCallState") -> float:
[tool_use Bash] {"command": "grep -rn \"wait_exponential_jitter\\|DeprecationWarning\\|deprecat\" . --exclude-dir=.git | head -60; echo ---; ls; git log --oneline -3", "description": "Search for wait_exponential_jitter and deprecation usage"}
[tool_result] pyproject.toml:96:    "once::DeprecationWarning",
tests/test_tenacity.py:598:    def test_wait_exponential_jitter(self) -> None:
tests/test_tenacity.py:599:        fn = tenacity.wait_exponential_jitter(max=60)
tests/test_tenacity.py:612:        fn = tenacity.wait_exponential_jitter(10, 5)
tests/test_tenacity.py:617:        fn = tenacity.wait_exponential_jitter()
tests/test_tenacity.py:620:    def test_wait_exponential_jitter_min(self) -> None:
tests/test_tenacity.py:621:        fn = tenacity.wai
…[1084 chars elided]…
2f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml:4:    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
---
AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
8fb3be0 lithify: probe base
9f6d1ec eval setup at 3233040287fb
3233040 feat: add `min` param and `timedelta` support to `wait_exponential_jitter` (#628)
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py; echo ----; sed -n 235,300p tenacity/wait.py; echo ----; sed -n 590,650p tests/test_tenacity.py; echo ----; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml; echo ----; sed -n 85,105p pyproject.toml; echo ----; cat AGENTS.md | head -60; echo ----; grep -n \"def to_seconds\" -A12 tenacity/_utils.py; grep -rn \"warn\" tenacity/*.py | head", "description": "Read wait.py, tests, release notes, config"}
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
…[6450 chars elided]…
able[..., typing.Any]) -> bool:
91-    if inspect.isclass(call):
92-        return False
93-    if inspect.iscoroutinefunction(call):
94-        return True
95-    partial_call = isinstance(call, functools.partial) and call.func
96-    dunder_call = partial_call or getattr(call, "__call__", None)  # noqa: B004
tenacity/__init__.py:24:import warnings
tenacity/__init__.py:326:        .. warning:: The keys in this dictionary **should** be somewhat
tenacity/__init__.py:719:            warnings.warn(
[tool_use Bash] {"command": "sed -n 185,215p doc/source/index.rst; echo ----; grep -rn \"Optional\\|| None\" tenacity/*.py | head -5; echo ----; sed -n 712,725p tenacity/__init__.py; echo ----; grep -n \"assertWarns\\|warnings\" tests/*.py | head; echo ----; ls releasenotes/notes | tail -3; ls .lithify 2>/dev/null; ls <work>/env-tenacity/bin/python 2>&1 | head -2", "description": "Check docs, typing style, warnings usage, and test env"}
[tool_result] .. testcode::

    @retry(wait=wait_fixed(3) + wait_random(0, 2))
    def wait_fixed_jitter():
        print("Wait at least 3 seconds, and add up to 2 seconds of random delay")
        raise Exception

When multiple processes are in contention for a shared resource, exponentially
increasing jitter helps minimise collisions.

.. testcode::

    @retry(wait=wait_random_exponential(multiplier=1, max=60))
    def wait_exponential_jitter():
        print("Randomly wait up to 2^x * 1 seconds between e
…[1270 chars elided]…
(did you mean retry={f.__class__.__name__}(...)?)",
                stacklevel=2,
            )
        r: BaseRetrying
        sleep = dkw.get("sleep")
----
----
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
harness
library
state.json
<work>/env-tenacity/bin/python
[assistant] Now I'll implement the change in `tenacity/wait.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "import abc\nimport random\nimport typing\n\nfrom tenacity import _utils", "new_string": "import abc\nimport random\nimport typing\nimport warnings\n\nfrom tenacity import _utils"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait, jitter and minimum.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is max(min
…[2208 chars elided]…
ls.to_seconds(max)\n        self.exp_base = exp_base\n        self.jitter = _utils.to_seconds(jitter)\n        self.min = _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp + jitter"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now I'll add tests covering the new behaviour, placed after the existing jitter tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py", "old_string": "            self._assert_inclusive_range(fn(make_retry_state(5, 0)), 16, 17)\n            self.assertEqual(fn(make_retry_state(7, 0)), 60)\n\n    def test_wait_retry_state_attributes(self) -> None:", "new_string": 
…[1646 chars elided]…
it_exponential_jitter(2, 60)\n\n    def test_wait_exponential_jitter_initial_and_multiplier_conflict(self) -> None:\n        with self.assertRaises(ValueError):\n            tenacity.wait_exponential_jitter(initial=1, multiplier=1)\n        with self.assertRaises(ValueError):\n            tenacity.wait_exponential_jitter(1, multiplier=1)\n\n    def test_wait_retry_state_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,30p tests/test_tenacity.py | grep -n \"import\"", "description": "Check imports in test file"}
[tool_result] 16:import contextlib
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
[assistant] The test file doesn't import `warnings` yet, so I'll add it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py", "old_string": "import typing\nimport unittest\nfrom fractions import Fraction", "new_string": "import typing\nimport unittest\nimport warnings\nfrom fractions import Fraction"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/wait-exponential-jitter-multiplier-5c1d9e2a7f\u5404.yaml <<'EOF'\nEOF\nrm -f \"releasenotes/notes/wait-exponential-jitter-multiplier-5c1d9e2a7f\u5404.yaml\"; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k \"exponential\" 2>&1 | tail -15", "description": "Run exponential wait tests with project interpreter"}
[tool_result] tenacity/wait.py:271: DeprecationWarning
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:613: DeprecationWarning: wait_exponential_jitter(initial=...) is deprecated, use multiplier=...
    fn = tenacity.wait_exponential_jitter(10, 5)

tests/test_tenacity.py::T
…[191 chars elided]…
DeprecationWarning: wait_exponential_jitter(initial=...) is deprecated, use multiplier=...
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_multiplier_no_warning
1 failed, 14 passed, 109 deselected, 2 warnings, 2 subtests passed in 0.30s
[assistant] One of my new tests is wrong: `wait_exponential_jitter(2, 60)` passes `initial` positionally, so it correctly warns. I'll drop that line. I also ran a stray command that created and removed a junk file; I'll confirm nothing was left behind.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py", "old_string": "            tenacity.wait_exponential_jitter()\n            tenacity.wait_exponential_jitter(2, 60)\n", "new_string": "            tenacity.wait_exponential_jitter()\n            tenacity.wait_exponential_jitter(max=60)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "git status --short && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k \"exponential\" 2>&1 | tail -3", "description": "Confirm clean tree and rerun exponential tests"}
[tool_result]  M tenacity/wait.py
 M tests/test_tenacity.py

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
15 passed, 109 deselected, 2 warnings, 2 subtests passed in 0.26s
[assistant] Targeted tests pass. Next I'll add a release note, then run the full suite and the linters.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-3e7a9c1d5b2f8a64.yaml", "content": "---\nfeatures:\n  - |\n    Add ``multiplier`` parameter to ``wait_exponential_jitter`` for consistency\n    with ``wait_exponential``. It defaults to 1.\ndeprecations:\n  - |\n    The ``initial`` parameter of ``wait_exponential_jitter`` is deprecated in\n    favour of ``multiplier``. Passing ``initial`` still works but emits a\n    ``DeprecationWarning``. Passing both ``initial`` and ``multiplier`` raises\n    ``ValueError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-3e7a9c1d5b2f8a64.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; echo ---; $PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff check tenacity tests && $PY -m ruff format --check tenacity tests; echo \"ruff rc=$?\"; $PY -m mypy tenacity 2>&1 | tail -2", "description": "Write release note, run full tests, ruff, and mypy"}
[tool_result]     fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
158 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.95s
---
ruff rc=1
<work>/env-tenacity/bin/python: No module named mypy
[assistant] The full suite passes (158 passed). The ruff step exited 1, but that may just mean ruff isn't installed in this env. I'll check.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m ruff --version 2>&1; which ruff mypy 2>&1; (ruff check tenacity tests && ruff format --check tenacity tests) 2>&1 | tail -5; (mypy tenacity) 2>&1 | tail -2", "description": "Run ruff and mypy from available tooling"}
[tool_result] <work>/env-tenacity/bin/python: No module named ruff
ruff not found
mypy not found
(eval):1: command not found: ruff
(eval):1: command not found: mypy
[assistant] Ruff and mypy aren't installed here, so I'll check line lengths against the 88-column limit by hand.
[tool_use Bash] {"command": "git diff -U0 | grep '^+' | grep -v '^+++' | awk 'length($0)-1 > 88 {print length($0)-1\": \"$0}'; grep -n \"E501\\|ignore\" pyproject.toml | head", "description": "Find added lines over 88 characters"}
[tool_result] 90: +    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))
89: +                "wait_exponential_jitter(initial=...) is deprecated, use multiplier=...",
107:ignore = [
110:    "E501",  # line too long (formatter handles what it can)
126:ignore_missing_imports = true
[assistant] E501 is ignored in this project, but I'll tidy the two long lines anyway to match the surrounding code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count.", "new_string": "    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter),\n    maximum)) where n is the retry count."}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "                \"wait_exponential_jitter(initial=...) is deprecated, use multiplier=...\",", "new_string": "                \"'initial' is deprecated in wait_exponential_jitter, use 'multiplier'\","}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161458-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git status --short", "description": "Rerun full test suite and show changed files"}
[tool_result] 158 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.86s
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-jitter-multiplier-3e7a9c1d5b2f8a64.yaml
[assistant] `wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated as you specified. The full project suite passes: 158 passed, 1 skipped, with the project's pytest command.

Changes, all in the worktree and uncommitted:

- **`tenacity/wait.py`**: `initial` stays first, so positional and keyword calls still work. `multiplier` is added at the end of the signature, so existing positional calls keep their meaning.
  - Passing `initial` emits a `DeprecationWarning` pointing at `multiplier`.
  - Passing both raises `ValueError`.
  - Both parameters default to `None`. That is 
…[410 chars elided]…
 **`releasenotes/notes/wait-exponential-jitter-multiplier-3e7a9c1d5b2f8a64.yaml`**: a new feature note and a deprecation note.

Two things to be aware of:

- The `self.initial` attribute is gone; the value is now stored as `self.multiplier`. Code that reads `.initial` off the instance would break. I didn't add a compatibility alias because the request didn't ask for one.
- ruff and mypy aren't installed in the project's test environment, so I couldn't run the linters. I checked added lines against the 88-column limit by hand; E501 is ignored in this project anyway.

Nothing has been committed.
