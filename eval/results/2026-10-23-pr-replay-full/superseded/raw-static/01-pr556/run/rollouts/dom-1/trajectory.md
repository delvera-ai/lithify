# trajectory dom-1

final message:
The fix is in place. `find_ordinal` now returns "th" for 111, 112 and 113, and the project test suite passes (126 passed, 1 skipped).

- **Fix:** in `tenacity/_utils.py`, I added a branch before the last-digit fallback: if `pos_num % 100` is 11–13, return "th". Other numbers take the same path as before.
- **Regression test:** `test_to_ordinal` in `tests/test_utils.py` covers 0–4, 11–13, 21–23, 101, 111–113, 121 and 1011. Against the original `_utils.py`, 111–113 produced `['111st', '112nd', '113rd']`, which confirms the test reproduces the bug.
- **Release note:** `releasenotes/notes/fix-find-ordinal-teens-3f9c2a7d1e8b5a40.yaml` describes the user-visible fix as a `fixes:` entry.

I did not run mypy or ruff: neither is installed in the project's check environment, so the strict typing and formatting checks are unverified. The change adds no new signatures and follows the existing style, so I don't expect issues, but please run `tox -e pep8` and mypy before merging.

I haven't committed anything. The three changed files are `tenacity/_utils.py`, `tests/test_utils.py` and the new release note.

## events
[tool_use Skill] {"skill": "tenacity-change-contract"}
[tool_result] Launching skill: tenacity-change-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/.claude/skills/tenacity-change-contract

# What a maintainer-complete tenacity change contains

Facts below are taken from this repository's history and config; re-check with
`git log --name-only` if in doubt.

## CONTRACT: behaviour-changing change = code + release note + regression test

1. **Release note (reno).** Recent fix/feature commits (#555, #552, #551, #497, #484, #479)
   each add one file under `releasenotes/notes/`. Name: `<kebab-slug>-<16 hex c
…[1539 chars elided]…
8`), line length 88, target py310 (`pyproject.toml`).
  Use py310+ syntax; no compatibility shims for older Pythons.
- **Shared helpers in `tenacity/_utils.py` feed user-visible text.** `to_ordinal` /
  `find_ordinal` build the "Nth time calling it" messages in `tenacity/before.py` and
  `tenacity/after.py`, and `tests/test_after.py` computes its expected strings through
  `_utils.to_ordinal`. Fix such helpers in `_utils.py` itself (not at call sites), and test the
  helper directly in `tests/test_utils.py` — the logging tests will not catch a wrong helper
  because they call the same helper.

[tool_use Bash] {"command": "grep -rn \"find_ordinal\" --include=*.py . ; ls releasenotes/notes | tail -5; cat tenacity/_utils.py", "description": "Locate find_ordinal and list release notes"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\\|to_ordinal\" . --include=*.py; ls releasenotes/notes | tail -5; cat tenacity/_utils.py", "description": "Locate ordinal helpers and list release notes"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"find_ordinal\\|to_ordinal\" tenacity tests; ls releasenotes/notes | tail -5; cat tenacity/_utils.py", "description": "Locate ordinal helpers and list release notes"}
[tool_result] tenacity/before.py:43:            f"this is the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tenacity/after.py:46:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tenacity/_utils.py:40:def find_ordin
…[3160 chars elided]…
   partial_call = isinstance(call, functools.partial) and call.func
    dunder_call = partial_call or getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(dunder_call)


def wrap_to_async_func(
    call: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
    if is_coroutine_callable(call):
        return call

    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return call(*args, **kwargs)

    return inner
[assistant] The bug is in the `else` branch: `111 % 10` gives 1, so 111 maps to "st" and never reaches the 11–13 exception. I'll read the existing test module and a sample release note before editing.
[tool_use Bash] {"command": "cat tests/test_utils.py; echo ----; cat releasenotes/notes/timedelta-for-stop-ef6bf71b88ce9988.yaml; echo ----; grep -n \"ordinal\" -i tests/test_utils.py", "description": "Show utils tests and a sample release note"}
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
…[571 chars elided]…
ne_callable(lambda_fn) is False

    assert _utils.is_coroutine_callable(partial_async_func) is True
    assert _utils.is_coroutine_callable(partial_sync_func) is False
    assert _utils.is_coroutine_callable(partial_async_class) is True
    assert _utils.is_coroutine_callable(partial_sync_class) is False
    assert _utils.is_coroutine_callable(partial_lambda_fn) is False
----
---
features:
  - |
    - accept ``datetime.timedelta`` instances as argument to ``tenacity.stop.stop_after_delay``
----
[assistant] Now the fix: check the last two digits for the 11–13 exception before falling back to the last digit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:\n        return find_ordinal(pos_num % 10)", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:\n        return find_ordinal(pos_num % 10)"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/tenacity/_utils.py has been updated successfully.
[assistant] Next, a regression test in `tests/test_utils.py` that pins the new behaviour and the unchanged suffixes.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/tests/test_utils.py", "old_string": "def test_is_coroutine_callable() -> None:", "new_string": "def test_to_ordinal() -> None:\n    assert _utils.to_ordinal(0) == \"0th\"\n    assert _utils.to_ordinal(1) == \"1st\"\n    assert _utils.to_ordinal(2) == \"2nd
…[305 chars elided]…
22) == \"22nd\"\n    assert _utils.to_ordinal(23) == \"23rd\"\n    assert _utils.to_ordinal(101) == \"101st\"\n    assert _utils.to_ordinal(111) == \"111th\"\n    assert _utils.to_ordinal(112) == \"112th\"\n    assert _utils.to_ordinal(113) == \"113th\"\n    assert _utils.to_ordinal(121) == \"121st\"\n    assert _utils.to_ordinal(1011) == \"1011th\"\n\n\ndef test_is_coroutine_callable() -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/tests/test_utils.py has been updated successfully.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/releasenotes/notes/fix-find-ordinal-teens-3f9c2a7d1e8b5a40.yaml", "content": "---\nfixes:\n  - |\n    Fixed the ordinal suffix used in ``before`` and ``after`` log messages for\n    numbers greater than 20 that end in 11, 12 or 13. For example, attempt 111\n    was logged as \"111st\", \"112nd\" and \"113rd\"; these now read \"111th\",\n    \"112th\" and \"113th\".\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-366c021c9ddc/20261023-155945-bug-tenacity-utils-find-ordinal/dom-1/releasenotes/notes/fix-find-ordinal-teens-3f9c2a7d1e8b5a40.yaml (file state is current in your context — no need to Read it back)
[assistant] Now I'll run the test suite with the project's check command, and confirm the new test fails on the original code.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"--- ruff/mypy\"; <work>/env-tenacity/bin
…[108 chars elided]…
ional-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python -m ruff check tenacity tests 2>&1 | tail -3; <work>/env-tenacity/bin/python -m ruff format --check tenacity tests 2>&1 | tail -3", "description": "Run pytest, mypy, and ruff checks"}
[tool_use Bash] {"command": "git show HEAD:tenacity/_utils.py > /tmp/orig_utils_check.py && <work>/env-tenacity/bin/python -I -c \"\nimport importlib.util\ns=importlib.util.spec_from_file_location('o','/tmp/orig_utils_check.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nprint([m.to_ordinal(n) for n in (111,112,113)])\"; rm -f /tmp/orig_utils_check.py", "description": "Run checks and confirm old behaviour on original code"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.79s
--- ruff/mypy
<work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[tool_result] ['111st', '112nd', '113rd']
[assistant] The fix is in place. `find_ordinal` now returns "th" for 111, 112 and 113, and the project test suite passes (126 passed, 1 skipped).

- **Fix:** in `tenacity/_utils.py`, I added a branch before the last-digit fallback: if `pos_num % 100` is 11–13, return "th". Other numbers take the same path as before.
- **Regression test:** `test_to_ordinal` in `tests/test_utils.py` covers 0–4, 11–13, 21–23, 101, 111–113, 121 and 1011. Against the original `_utils.py`, 111–113 produced `['111st', '112nd', '113rd']`, which confirms the test reproduces the bug.
- **Release note:** `releasenotes/notes/fix-find-ordinal-teens-3f9c2a7d1e8b5a40.yaml` describes the user-visible fix as a `fixes:` entry.

I did not run mypy or ruff: neither is installed in the project's check environment, so the strict typing and formatting checks are unverified. The change adds no new signatures and follows the existing style, so I don't expect issues, but please run `tox -e pep8` and mypy before merging.

I haven't committed anything. The three changed files are `tenacity/_utils.py`, `tests/test_utils.py` and the new release note.
