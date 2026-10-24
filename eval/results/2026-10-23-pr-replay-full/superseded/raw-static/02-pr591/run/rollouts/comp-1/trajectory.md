# trajectory comp-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It now logs the message with `?` in place of the elapsed seconds. The full suite passes: 127 passed, 1 skipped.

**Changes**
- `tenacity/after.py`: when `seconds_since_start` is `None`, the elapsed value is `"?"`. Otherwise it is formatted with `sec_format` as before, so the existing output is unchanged.
- `tests/test_after.py`: new `test_03_seconds_since_start_unset`. It builds a retry state with no outcome timestamp and checks that the message reads `after ?(s), ...`.
- `releasenotes/notes/fix-after-log-unset-seconds-dcffa3ecb9db7414.yaml`: a `fixes:` note describing the change.

**Verification**
- `fails_on_base.py` on the new test: it fails on `HEAD` with `TypeError: must be real number, not NoneType` at `tenacity/after.py:45`, which is the reported bug.
- Full suite (last run, after all edits): 127 passed, 1 skipped, 12 subtests passed.
- `git status`: the three expected files, and no stash entries.
- mypy and ruff were not run; they are not installed in the project interpreter.

## events
[tool_use Bash] {"command": "cat tenacity/after.py && grep -n \"seconds_since_start\" -r tenacity | head -30 && ls releasenotes/notes | tail -5 && cat memory.md 2>/dev/null | head -20", "description": "Read after_log source and locate related code"}
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] # Copyright 2016 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[1818 chars elided]…
tate.seconds_since_start + retry_state.upcoming_sleep
tenacity/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
tenacity/asyncio/__init__.py:146:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/comp-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex
…[3408 chars elided]…
rt not isolated) — correct the id once, then
   report "not verified" instead of improvising a stash/revert round-trip.
2. The full suite command from `memory.md`, **last**, after every edit (an edit after the
   last run invalidates it). Quote its pass/fail counts in the final message.
3. `git status --short` — expect exactly the code file(s), the test file, and one new
   `releasenotes/notes/*.yaml` (untracked, so `git diff --stat` will not list it); no stray
   stash entries or scratch files.

Final message: what changed per file, the results of steps 1–2, and that mypy/ruff were not run.


[assistant] The skill's checklist is: fix the code, add a release note and a regression test, then run the checks. Next I'll look at the existing after-log tests and a recent note for style.
[tool_use Bash] {"command": "cat tests/test_after.py && cat releasenotes/notes/fix-local-context-overwrite-*.yaml 2>/dev/null; ls releasenotes/notes | grep -i fix | head -3; cat releasenotes/notes/$(ls releasenotes/notes | grep -i fix | head -1); ls .lithify/harness/skills/tenacity-change-contract/scripts 2>&1; ls <work>/env-tenacity/bin/python 2>&1", "description": "Read existing after_log tests, release note style, and check tooling paths"}
[tool_result] import logging
import random
import unittest.mock

from tenacity import (
    _utils,
    after_log,
)

from . import test_tenacity


class TestAfterLogFormat(unittest.TestCase):
    def setUp(self) -> None:
        self.log_level = random.choice(
            (
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            )
        )
        self.previous_attempt_number = random.randint(1
…[1962 chars elided]…
er)} time calling it.",
        )
---
fixes:
  - |
    Avoid overwriting local contexts when applying the retry decorator.
Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
fix-async-loop-with-result-f68e913ccb425aca.yaml
fix-async-retry-type-overloads-27f3e0c239ed6b.yaml
---
fixes:
  - "Fixes test failures with typeguard 3.x"
fails_on_base.py
<work>/env-tenacity/bin/python
[assistant] Now the `seconds_since_start` property and the `make_retry_state` helper, so the regression test can build a state with no outcome timestamp.
[tool_use Bash] {"command": "sed -n 535,560p tenacity/__init__.py && grep -n \"def make_retry_state\" -A 25 tests/test_tenacity.py && grep -n \"^    @\\|^def \\|sec_format\" tenacity/before_sleep.py | head; grep -n \"sec_format\" -r tenacity | head", "description": "Inspect seconds_since_start property and make_retry_state helper"}
[tool_result]         self.outcome: Future | None = None
        #: Timestamp of the last outcome
        self.outcome_timestamp: float | None = None
        #: Time spent sleeping in retries
        self.idle_for: float = 0.0
        #: Next action as decided by the retry manager
        self.next_action: RetryAction | None = None
        #: Next sleep time as decided by the retry manager.
        self.upcoming_sleep: float = 0.0

    @property
    def seconds_since_start(self) -> float | None:
        if se
…[1525 chars elided]…
CallState") -> None:
29:def before_sleep_log(
33:    sec_format: str = "%.3g",
67:            f"in {sec_format % retry_state.next_action.sleep} seconds as it {verb} {value}.",
tenacity/before_sleep.py:33:    sec_format: str = "%.3g",
tenacity/before_sleep.py:67:            f"in {sec_format % retry_state.next_action.sleep} seconds as it {verb} {value}.",
tenacity/after.py:32:    sec_format: str = "%.3g",
tenacity/after.py:45:            f"after {sec_format % retry_state.seconds_since_start}(s), "
[assistant] The cause is clear: `seconds_since_start` is `None` when `outcome_timestamp` is unset, and `"%.3g" % None` raises `TypeError`. I'll fix it in `after.py`, keeping the message format and showing `?` for the missing value.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/comp-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        if retry_state.seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % retry_state.seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/comp-1/tenacity/after.py has been updated successfully.
[assistant] Next, the regression test, following the style of the existing class in `tests/test_after.py`.
[tool_use Bash] {"command": "cat >> tests/test_after.py <<'EOF'\n\n    def test_03_seconds_since_start_unset(self) -> None:\n        \"\"\"Test log formatting when seconds_since_start is None.\"\"\"\n        log = unittest.mock.MagicMock(spec=\"logging.Logger.log\")\n        logger = unittest.mock.MagicMock(spec=\"logging.Logger\", log=log)\n\n        retry_state = test_tenacity.make_retry_state(self.previous_att
…[1083 chars elided]…
/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python .lithify/harness/skills/tenacity-change-contract/scripts/fails_on_base.py tests/test_after.py::TestAfterLogFormat::test_03_seconds_since_start_unset 2>&1 | tail -15; echo \"exit=$?\"", "description": "Add regression test and release note, then check it fails on base"}
[tool_result] fix-after-log-unset-seconds-dcffa3ecb9db7414.yaml
        logger.log(
            log_level,
            f"Finished call to '{fn_name}' "
>           f"after {sec_format % retry_state.seconds_since_start}(s), "
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )
E       TypeError: must be real number, not NoneType

tenacity/after.py:45: TypeError
=========================== short test summary info ============================
FAILED tests/test_after.py::TestAfterLogFormat::test_03_seconds_since_start_unset
1 failed in 0.04s
---
GOOD: tests FAIL on HEAD. Confirm the failure reason above.
exit=0
[assistant] The new test fails on `HEAD` with the reported `TypeError`, as expected. Now the full suite, run last.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short; git stash list | head -3", "description": "Run full test suite and check git status"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.91s
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/fix-after-log-unset-seconds-dcffa3ecb9db7414.yaml
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It now logs the message with `?` in place of the elapsed seconds. The full suite passes: 127 passed, 1 skipped.

**Changes**
- `tenacity/after.py`: when `seconds_since_start` is `None`, the elapsed value is `"?"`. Otherwise it is formatted with `sec_format` as before, so the existing output is unchanged.
- `tests/test_after.py`: new `test_03_seconds_since_start_unset`. It builds a retry state with no outcome timestamp and checks that the message reads `after ?(s), ...`.
- `releasenotes/notes/fix-after-log-unset-seconds-dcffa3ecb9db7414.yaml`: a `fixes:` note describing the change.

**Verification**
- `fails_on_base.py` on the new test: it fails on `HEAD` with `TypeError: must be real number, not NoneType` at `tenacity/after.py:45`, which is the reported bug.
- Full suite (last run, after all edits): 127 passed, 1 skipped, 12 subtests passed.
- `git status`: the three expected files, and no stash entries.
- mypy and ruff were not run; they are not installed in the project interpreter.
