# trajectory comp-1

final message:
Fixed: `find_ordinal` now returns "th" for numbers whose last two digits are 11, 12 or 13, so 111, 112 and 113 give "111th", "112th" and "113th". Every other suffix is unchanged. The full test suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/_utils.py`**: one new branch, `elif 11 <= pos_num % 100 <= 13: return "th"`, placed after the existing 4–20 branch. This covers 111–113 and 211–213 and so on, without touching 21, 22, 23 or 101.
- **`tests/test_utils.py`**: added `test_find_ordinal` (covers the boundaries and the 111–113 cases, which failed before the fix) and `test_to_ordinal` (checks the rendered "111th" text).
- **`releasenotes/notes/fix-find-ordinal-teens-3f9a1c7b2e4d8a60.yaml`**: a `fixes:` reno note describing the user-visible change.

I did not run mypy or ruff; the project interpreter doesn't have them installed. The new test functions are annotated `-> None` and follow the file's existing style. I didn't run the new tests against the old code to watch them fail, but the old code returns "st" for 111, so they would.

## events
[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include='*.py' . ; sed -n '1,80p' tenacity/_utils.py", "description": "Locate find_ordinal and show utils module"}
[tool_result] tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses
…[1443 chars elided]…
e produced ``repr(cb)`` is called and returned.
    """
    segments = []
    try:
        segments.append(cb.__qualname__)
    except AttributeError:
        try:
            segments.append(cb.__name__)
        except AttributeError:
            pass
    if not segments:
        return repr(cb)
    else:
        try:
            # When running under sphinx it appears this can be none?
            if cb.__module__:
                segments.insert(0, cb.__module__)
        except AttributeError:
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/comp-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex 
…[1825 chars elided]…
m; write
  code that satisfies the rules above by inspection, and say in the final message that
  they were not run.
- **Shared helpers in `tenacity/_utils.py` feed user-visible text.** `to_ordinal` /
  `find_ordinal` build the "Nth time calling it" messages in `tenacity/before.py` and
  `tenacity/after.py`, and `tests/test_after.py` computes its expected strings through
  `_utils.to_ordinal`. Fix such helpers in `_utils.py` itself (not at call sites), and test the
  helper directly in `tests/test_utils.py` — the logging tests will not catch a wrong helper
  because they call the same helper.

[tool_use Bash] {"command": "grep -rn \"ordinal\" tests/ | head -30; ls releasenotes/notes | tail -5; git log --oneline -1 -- releasenotes/notes | cat", "description": "Find existing ordinal tests and release note layout"}
[tool_result] tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
d4e868d Fix `retry()` annotations with async `sleep=` function (#555)
[tool_use Bash] {"command": "sed -n '1,40p' tests/test_utils.py; echo ----; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; echo ----; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml", "description": "Read test_utils and sample release notes"}
[tool_result] import functools

from tenacity import _utils


def test_is_coroutine_callable() -> None:
    async def async_func() -> None:
        pass

    def sync_func() -> None:
        pass

    class AsyncClass:
        async def __call__(self) -> None:
            pass

    class SyncClass:
        def __call__(self) -> None:
            pass

    lambda_fn = lambda: None  # noqa: E731

    partial_async_func = functools.partial(async_func)
    partial_sync_func = functools.partial(sync_func)
    part
…[731 chars elided]…
is False
    assert _utils.is_coroutine_callable(partial_async_class) is True
    assert _utils.is_coroutine_callable(partial_sync_class) is False
----
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
----
---
features:
  - |
    If you're using `Trio <https://trio.readthedocs.io>`__, then
    ``@retry`` now works automatically. It's no longer necessary to
    pass ``sleep=trio.sleep``.
[assistant] Now the fix in `_utils.py`: numbers whose last two digits are 11–13 take "th", which is the same rule the existing 4–20 branch applies.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/comp-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/comp-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "cat >> tests/test_utils.py <<'EOF'\n\n\ndef test_find_ordinal() -> None:\n    assert _utils.find_ordinal(0) == \"th\"\n    assert _utils.find_ordinal(1) == \"st\"\n    assert _utils.find_ordinal(2) == \"nd\"\n    assert _utils.find_ordinal(3) == \"rd\"\n    assert _utils.find_ordinal(4) == \"th\"\n    assert _utils.find_ordinal(11) == \"th\"\n    assert _utils.find_ordinal(12) == \"th
…[1174 chars elided]…
eater than 20 that end in 11, 12 or 13. They previously\n    produced \"111st\", \"112nd\" and \"113rd\".\nEOF\n<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Add regression tests, release note, and run test suite"}
[tool_result] ..........s................................................. [ 46%]
....................................................................     [100%]
127 passed, 1 skipped, 12 subtests passed in 1.79s
[tool_use Bash] {"command": "git status --short; git diff --stat", "description": "Show changed files"}
[tool_result]  M tenacity/_utils.py
 M tests/test_utils.py
?? releasenotes/notes/fix-find-ordinal-teens-3f9a1c7b2e4d8a60.yaml
 tenacity/_utils.py  |  2 ++
 tests/test_utils.py | 31 +++++++++++++++++++++++++++++++
 2 files changed, 33 insertions(+)
[assistant] Fixed: `find_ordinal` now returns "th" for numbers whose last two digits are 11, 12 or 13, so 111, 112 and 113 give "111th", "112th" and "113th". Every other suffix is unchanged. The full test suite passes (127 passed, 1 skipped).

Changes:
- **`tenacity/_utils.py`**: one new branch, `elif 11 <= pos_num % 100 <= 13: return "th"`, placed after the existing 4–20 branch. This covers 111–113 and 211–213 and so on, without touching 21, 22, 23 or 101.
- **`tests/test_utils.py`**: added `test_find_ordinal` (covers the boundaries and the 111–113 cases, which failed before the fix) and `test_to_ordinal` (checks the rendered "111th" text).
- **`releasenotes/notes/fix-find-ordinal-teens-3f9a1c7b2e4d8a60.yaml`**: a `fixes:` reno note describing the user-visible change.

I did not run mypy or ruff; the project interpreter doesn't have them installed. The new test functions are annotated `-> None` and follow the file's existing style. I didn't run the new tests against the old code to watch them fail, but the old code returns "st" for 111, so they would.
