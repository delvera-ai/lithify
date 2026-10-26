# trajectory dom-1

final message:
`after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/after.py`**: the elapsed value is computed first. It is `"?"` when `seconds_since_start` is `None`, otherwise `sec_format % seconds_since_start` as before.
- **`tests/test_after.py`**: new `test_03_unset_seconds_since_start`. It sets `outcome_timestamp` to `None`, checks that the log line reads `after ?(s), ...`, and follows the existing test style.
- **`releasenotes/notes/after-log-unset-seconds-3c1f7e2a9b5d4e60.yaml`**: a `fixes:` note in the repo's reno format, per the `tenacity-change-contract` skill.

I did not run the new test against the old code. The old code applies `sec_format % None`, which raises `TypeError`, so the test should fail there. I also could not run ruff because it is not in the project env. I checked the 88-column limit by hand on the lines I changed.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"seconds_since_start\" -r tenacity tests | head -50 && sed -n 1,80p tenacity/after.py", "description": "Locate seconds_since_start usages and read after.py"}
[tool_result] tenacity/__init__.py:365:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/__init__.py:546:    def seconds_since_start(self) -> float | None:
tenacity/asyncio/__init__.py:146:        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
tenacity/stop.py:108:        if retry_state.seconds_since_start is None:
tenacity/stop.py:109:            raise RuntimeError("__call__() called but seconds_since_start is not set")
tenacity/st
…[2078 chars elided]…
      if retry_state.fn is None:
            # NOTE(sileht): can't really happen, but we must please mypy
            fn_name = "<unknown>"
        else:
            fn_name = _utils.get_callback_name(retry_state.fn)
        logger.log(
            log_level,
            f"Finished call to '{fn_name}' "
            f"after {sec_format % retry_state.seconds_since_start}(s), "
            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
        )

    return log_it
[tool_use Bash] {"command": "cat tests/test_after.py | sed -n 1,90p; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | grep -v '^\\.' | tail -1); cat ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/CLAUDE.md >/dev/null; ls .claude 2>/dev/null; find / -name SKILL.md -path '*tenacity-change-contract*' 2>/dev/null | head -3", "description": "Read after_log tests, release notes, and locate contract skill"}
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
…[2366 chars elided]…
ge/docs/retry-strategy
skills
~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/harness-start/skills/tenacity-change-contract/SKILL.md
~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/inv-1/.agents/skills/tenacity-change-contract/SKILL.md
~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/inv-1/.claude/skills/tenacity-change-contract/SKILL.md
[tool_use Bash] {"command": "cat .claude/skills/tenacity-change-contract/SKILL.md; ls .claude/skills; git log --oneline -3 -- releasenotes/notes | cat; cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml; cat <work>/env-tenacity/bin/python -V 2>&1 | head -1", "description": "Read the change-contract skill and release note example"}
[tool_result] <persisted-output>
Output too large (52.5KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-366c021c9ddc-20261023-160401-bug-tenacity-after-log-crashes-w-dom-1/d9dccaee-c8ae-4957-bc81-c010f6cc5c5d/tool-results/bqfkjm1a0.txt

Preview (first 2KB):
---
name: tenacity-change-contract
description: Load before finishing any change that alters tenacity's runtime behaviour or public API (bug fix, new feature, changed default, changed log/error text) — list
…[1292 chars elided]…
 as `tests/test_issue_<N>.py`. Add a test that fails on the old code. Follow the
   existing style in that file (plain `def test_...() -> None:` functions with bare `assert` in
   `test_utils.py`).
3. **Confirm they agree:** the note describes the same behaviour the test pins down; the diff
   touches `tenacity/…`, `tests/…` and `releasenotes/notes/…`.

Pure refactors, CI, typing-only, or docs-only changes may skip the test; a user-visible change
should still get a note.

...
</persisted-output>
[tool_use Bash] {"command": "grep -n \"def make_retry_state\" -A 22 tests/test_tenacity.py; sed -n 90,120p tests/test_after.py; sed -n 536,556p tenacity/__init__.py; cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml", "description": "Inspect make_retry_state and seconds_since_start property"}
[tool_result] 55:def make_retry_state(
56-    previous_attempt_number: typing.Any,
57-    delay_since_first_attempt: typing.Any,
58-    last_result: typing.Any = None,
59-    upcoming_sleep: typing.Any = 0,
60-) -> RetryCallState:
61-    """Construct RetryCallState for given attempt number & delay.
62-
63-    Only used in testing and thus is extra careful about timestamp arithmetics.
64-    """
65-    required_parameter_unset = (
66-        previous_attempt_number is _unset or delay_since_first_attempt is _un
…[806 chars elided]…
p: float = 0.0

    @property
    def seconds_since_start(self) -> float | None:
        if self.outcome_timestamp is None:
            return None
        return self.outcome_timestamp - self.start_time

    def prepare_for_next_attempt(self) -> None:
        self.outcome = None
        self.outcome_timestamp = None
        self.attempt_number += 1
        self.next_action = None

---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tenacity/after.py", "old_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {sec_format % retry_state.seconds_since_start}(s), \"", "new_string": "            fn_name = _utils.get_callback_name(retry_state.fn)\n        seconds_since_start = retry_state.seconds_since_start\n        elapsed = \"?\" if seconds_since_start is None else sec_format % seconds_since_start\n        logger.log(\n            log_level,\n            f\"Finished call to '{fn_name}' \"\n            f\"after {elapsed}(s), \""}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tenacity/after.py has been updated successfully.
[assistant] Now the regression test, following the existing style in `tests/test_after.py`.
[tool_use Bash] {"command": "tail -c 200 tests/test_after.py | od -c | tail -3 && cat >> tests/test_after.py <<'EOF'\n\n    def test_03_unset_seconds_since_start(self) -> None:\n        \"\"\"Test log formatting when the outcome timestamp is not set.\"\"\"\n        log = unittest.mock.MagicMock(spec=\"logging.Logger.log\")\n        logger = unittest.mock.MagicMock(spec=\"logging.Logger\", log=log)\n\n        retr
…[907 chars elided]…
ome timestamp yet. The log message is still emitted, showing ``?``\n    in place of the elapsed seconds.\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add regression test, reno note, and run the test suite"}
[tool_result] 0000260    c   a   l   l   i   n   g       i   t   .   "   ,  \n        
0000300                            )  \n                                
0000310
...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.82s
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin; ($P/ruff --version && $P/ruff format --check tenacity/after.py tests/test_after.py && $P/ruff check tenacity/after.py tests/test_after.py) 2>&1 | tail -8; git status --short", "description": "Run ruff format and lint checks on changed files"}
[tool_result] (eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
 M tenacity/after.py
 M tests/test_after.py
?? releasenotes/notes/after-log-unset-seconds-3c1f7e2a9b5d4e60.yaml
[tool_use Bash] {"command": "grep -n \"line-length\\|line_length\\|max-line\" pyproject.toml setup.cfg tox.ini .pre-commit-config.yaml 2>/dev/null; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/after.py tests/test_after.py", "description": "Check configured line length and long lines"}
[tool_result] 100:line-length = 88
tenacity/after.py: 43: 90
tenacity/after.py: 48: 93
tests/test_after.py: 50: 93
tests/test_after.py: 75: 93
tests/test_after.py: 99: 93
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tenacity/after.py", "old_string": "        elapsed = \"?\" if seconds_since_start is None else sec_format % seconds_since_start", "new_string": "        if seconds_since_start is None:\n            elapsed = \"?\"\n        else:\n            elapsed = sec_format % seconds_since_start"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tenacity/after.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tests/test_after.py", "old_string": "        retry_state = test_tenacity.make_retry_state(\n            self.previous_attempt_number, 0.1\n        )\n        retry_state.outcome_timestamp = None", "new_string": "        retry_state = test_tenacity.make_retry_state(self.previous_attempt_number, 0.1)\n        retry_state.outcome_timestamp = None"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-160401-bug-tenacity-after-log-crashes-w/dom-1/tests/test_after.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff", "description": "Rerun tests and show final diff"}
[tool_result] ...........s................................................ [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.76s
diff --git a/tenacity/after.py b/tenacity/after.py
index a4b8922..a12c8eb 100644
--- a/tenacity/after.py
+++ b/tenacity/after.py
@@ -39,10 +39,15 @@ def after_log(
             fn_name = "<unknown>"
         else:
             fn_name = _utils.get_callback_name(retry_state.fn)
+        seconds_since_
…[1330 chars elided]…
s None
+        fun = after_log(logger=logger, log_level=self.log_level)
+        fun(retry_state)
+        fn_name = (
+            "<unknown>"
+            if retry_state.fn is None
+            else _utils.get_callback_name(retry_state.fn)
+        )
+        log.assert_called_once_with(
+            self.log_level,
+            f"Finished call to '{fn_name}' "
+            "after ?(s), "
+            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
+        )
[assistant] `after_log` no longer crashes when `seconds_since_start` is `None`. It logs the message with `?` in place of the elapsed seconds. The full suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/after.py`**: the elapsed value is computed first. It is `"?"` when `seconds_since_start` is `None`, otherwise `sec_format % seconds_since_start` as before.
- **`tests/test_after.py`**: new `test_03_unset_seconds_since_start`. It sets `outcome_timestamp` to `None`, checks that the log line reads `after ?(s), ...`, and follows the existing test style.
- **`releasenotes/notes/after-log-unset-seconds-3c1f7e2a9b5d4e60.yaml`**: a `fixes:` note in the repo's reno format, per the `tenacity-change-contract` skill.

I did not run the new test against the old code. The old code applies `sec_format % None`, which raises `TypeError`, so the test should fail there. I also could not run ruff because it is not in the project env. I checked the 88-column limit by hand on the lines I changed.

I did not commit anything.
