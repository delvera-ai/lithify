# trajectory inv-1

final message:
`@retry` now decorates normally when `tenacity.tornado` is set to `None`. The regression test failed on the unfixed code with the reported `AttributeError` and passes after the fix. The full suite passes.

**Cause:** the decoration check at `tenacity/__init__.py` tested the import-time snapshot `_HAS_TORNADO` but then read the live `tornado` global. Once a test set that global to `None`, `tornado.gen` raised.

**Fix:** I added `_has_tornado()`, which returns `tornado is not None` and reads the global at call time. The decoration check uses it. I kept `_HAS_TORNADO` for the one-time import at the bottom of the module, where a snapshot is correct. The helper returns a plain `bool`, which keeps the reason in the existing comment true: mypy can't see a module-truthiness check as always true.

**Other changes:**
- `tests/test_tenacity.py`: new class `TestTornadoAvailabilityAtDecoration` with one test that patches `tenacity.tornado` to `None` and decorates a sync function. No existing tests were edited.
- `releasenotes/notes/fix-tornado-none-decoration-3f9c2e7a1d864b05.yaml`: a `fixes:` reno note, as the contract requires for bug fixes.

**Checks:**
- Regression test alone, before the fix: failed at `tenacity/__init__.py:790` with `AttributeError: 'NoneType' object has no attribute 'gen'`.
- Regression test alone, after the fix: 1 passed.
- Full suite (`run_tests.py`, no args): `exit=0`, 179 passed, 1 skipped, 15 subtests passed.
- `check_changed.py`: `exit=0`, 0 problems.

**Skipped:** ruff and mypy were not run, because the environment doesn't have them. The reno YAML was checked only by `check_changed.py`, since PyYAML is unavailable here, so it has not been parsed.

Nothing is committed. The changes are in the working tree.

## events
[assistant] I'll start by finding the decoration path that reads `tornado` and the skill's section headings, since the project rules require loading the contract before the first edit under `tenacity/`.
[tool_use Bash] {"command": "git status --short && grep -n \"tornado\" tenacity/*.py | head -50 && grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Find tornado references and contract headings"}
[tool_result] tenacity/__init__.py:88:    import tornado
tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:805:    from tenacity.tornadoweb import
…[751 chars elided]…
on (`+`, `sum()`, `wait_combine`, `wait_chain`) and the `wait=` value
310:## 1c. CONTRACT: a new keyword on `Retrying`/`AsyncRetrying`/`@retry`, or a new accepted type for an existing one
350:## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
379:## 2. A release note in `releasenotes/notes/` (reno)
401:## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
415:## 3. A regression test in the matching test file
429:## 4. Keep the change surface minimal
[assistant] The contract's headings are in. I'll read §1 and §2–4 for the surrounding rules, and the code around the tornado check.
[tool_use Bash] {"command": "sed -n '10,18p;379,440p' .lithify/harness/skills/tenacity-change-contract/SKILL.md && echo ---- && sed -n '80,100p;770,815p' tenacity/__init__.py && echo ---- && grep -rn \"_HAS_TORNADO\\|tornado\" tenacity/ tests/ | grep -v \"^tenacity/tornadoweb\" | head -40", "description": "Read contract sections and tornado code"}
[tool_result] ## 1. Code goes in the module that owns the concern
- `tenacity/_utils.py` — shared helpers (`find_ordinal`/`to_ordinal`, `get_callback_name`,
  `LoggerProtocol`, `MAX_WAIT`). The logging callbacks in `tenacity/before.py`,
  `tenacity/after.py`, `tenacity/before_sleep.py` call these helpers; fix the helper, not the
  callers.
- Strategies live in `tenacity/wait.py`, `tenacity/stop.py`, `tenacity/retry.py`; the
  `Retrying`/`retry()` core and its type overloads in `tenacity/__init__.py`; async in
…[5954 chars elided]…
f)
tenacity/__init__.py:804:if _HAS_TORNADO:
tenacity/__init__.py:805:    from tenacity.tornadoweb import TornadoRetrying
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
[assistant] The bug is in the `elif` at `tenacity/__init__.py:789`: it checks the import-time snapshot `_HAS_TORNADO`, then dereferences the live `tornado` global, which is `None` after the test assignment. The comment beside `_HAS_TORNADO` says the availability answer must stay a plain bool so mypy doesn't treat a module truthiness check as always-true. A helper function returning `tornado is not None` keeps that property and reads the global at call time. Next I'll look at the test file's conventions and the release-note directory before writing the regression test.
[tool_use Bash] {"command": "sed -n '1,40p' tests/test_tenacity.py && echo ---- && grep -n \"^class \\|^def \\|mock.patch\" tests/test_tenacity.py | head -30 && echo ---- && ls releasenotes/notes | tail -5 && cat \"releasenotes/notes/$(ls releasenotes/notes | grep -i fix | tail -1)\" && echo ---- && cat memory.md 2>/dev/null; ls .lithify/ 2>/dev/null; ls ~/.claude/projects/-private-tmp-claude-501--Users-user-Coding-delvera-foundational-lithify-19d43989-6c6b-4090-9032-1fdbf9e87d20-scratchpad-pr-work-replay-pr-replay-full-tenacity-static-claude-claude-haiku-5-5-repo/memory/ 2>/dev/null", "description": "Inspect test file, release notes, and memory"}
[tool_result] # Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013 Ray Holder
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
…[2198 chars elided]…
tion_message_message(thing: typing.Any) -> typing.Any:
1282:def _retryable_test_if_not_exception_message_message(thing: typing.Any) -> typing.Any:
----
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
fixes:
  - "Fix issue #288 : __name__ and other attributes for async functions"
----
harness
library
state.json
[assistant] I have the conventions. Next I'll confirm the project interpreter path from CLAUDE.md exists, then write the regression test first, appended as a new class at the end of `tests/test_tenacity.py` (new tests, no edits to existing ones).
[tool_use Bash] {"command": "ls -la <work>/env-tenacity/bin/python; tail -15 tests/test_tenacity.py", "description": "Verify project python and test file tail"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12

        def succeed_on_third() -> str:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("not yet")
            return "ok"

        result = restored(succeed_on_third)
        assert result == "ok"
        assert calls == 3


if __name__ == "__main__":
    unittest.main()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tests/test_tenacity.py", "old_string": "        result = restored(succeed_on_third)\n        assert result == \"ok\"\n        assert calls == 3\n\n\nif __name__ == \"__main__\":", "new_string": "        result = restored(succeed_on_third)\n        assert 
…[257 chars elided]…
to None; decoration\n        # must read that live value rather than the import-time snapshot.\n        with mock.patch.object(tenacity, \"tornado\", None):\n            @retry(stop=tenacity.stop_after_attempt(2))\n            def succeed() -> str:\n                return \"ok\"\n\n        assert succeed.statistics is not None\n        assert succeed() == \"ok\"\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] I'll tidy two things in that test: the contract wants a blank line before a nested decorated `def`, and the `statistics` assertion adds nothing, so I'll drop it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tests/test_tenacity.py", "old_string": "        with mock.patch.object(tenacity, \"tornado\", None):\n            @retry(stop=tenacity.stop_after_attempt(2))\n            def succeed() -> str:\n                return \"ok\"\n\n        assert succeed.statistics is not None\n        assert succeed() == \"ok\"", "new_string": "        with mock.patch.object(tenacity, \"tornado\", None):\n\n            @retry(stop=tenacity.stop_after_attempt(2))\n            def succeed() -> str:\n                return \"ok\"\n\n        assert succeed() == \"ok\""}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the new test alone against the unfixed code, through the harness runner, as the procedure requires.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestTornadoAvailabilityAtDecoration::test_retry_decorates_sync_function_when_tornado_global_is_none\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red.txt", "description": "Run regression test against unfixed code"}
[tool_result] exit=1

f = <function TestTornadoAvailabilityAtDecoration.test_retry_decorates_sync_function_when_tornado_global_is_none.<locals>.succeed at 0x10930da80>

    def wrap(f: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        if isinstance(f, retry_base):
            warnings.warn(
                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
                f"this will probably hang indefinitely (did you mean retry={f.__class__.__name__}(...)?)",
                stackl
…[404 chars elided]…
nd tornado.gen.is_coroutine_function(f)
        ):
E       AttributeError: 'NoneType' object has no attribute 'gen'

tenacity/__init__.py:790: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestTornadoAvailabilityAtDecoration::test_retry_decorates_sync_function_when_tornado_global_is_none
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The test fails with the reported `AttributeError` at `tenacity/__init__.py:790`, so the regression is red for the right reason. Now the fix: a small helper that reads the live global, used at decoration time. The import-time `_HAS_TORNADO` stays for the one-off module import, where a snapshot is correct.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tenacity/__init__.py", "old_string": "_HAS_TORNADO = tornado is not None\n\nif t.TYPE_CHECKING:", "new_string": "_HAS_TORNADO = tornado is not None\n\n\ndef _has_tornado() -> bool:\n    # Read the live global at call time: tests set `tenacity.tornado = None` to\n    # hide tornado, and decoration must honour that rather than the snapshot.\n    return tornado is not None\n\n\nif t.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tenacity/__init__.py", "old_string": "            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "            _has_tornado()\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/tenacity/__init__.py has been updated successfully.
[assistant] The contract (§2) requires a reno note for a bug fix. I'll add one using the repo's `<slug>-<16 hex>.yaml` naming.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/releasenotes/notes/fix-tornado-none-decoration-3f9c2e7a1d864b05.yaml", "content": "---\nfixes:\n  - |\n    ``@retry`` no longer raises ``AttributeError: 'NoneType' object has no attribute 'gen'``\n    when the ``tenacity.tornado`` module global has been set to ``None``. Whether tornado is\n    available is now read at decoration time instead of from an import-time snapshot.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/inv-1/releasenotes/notes/fix-tornado-none-decoration-3f9c2e7a1d864b05.yaml (file state is current in your context — no need to Read it back)
[assistant] Now the regression test should be green. Then I'll run the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestTornadoAvailabilityAtDecoration::test_retry_decorates_sync_function_when_tornado_global_is_none\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"full exit=$?\"; tail -6 /tmp/full.txt", "description": "Run regression test green, then full suite"}
[tool_result] exit=0

============================== 1 passed in 0.01s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
full exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 179 passed, 1 skipped, 15 subtests passed in 1.88s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/chk.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/chk.txt; git status --short", "description": "Run changed-file checks and show status"}
[tool_result] exit=0
changed: releasenotes/notes/fix-tornado-none-decoration-3f9c2e7a1d864b05.yaml, tenacity/__init__.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-tornado-none-decoration-3f9c2e7a1d864b05.yaml
[assistant] `@retry` now decorates normally when `tenacity.tornado` is set to `None`. The regression test failed on the unfixed code with the reported `AttributeError` and passes after the fix. The full suite passes.

**Cause:** the decoration check at `tenacity/__init__.py` tested the import-time snapshot `_HAS_TORNADO` but then read the live `tornado` global. Once a test set that global to `None`, `tornado.gen` raised.

**Fix:** I added `_has_tornado()`, which returns `tornado is not None` and reads the global at call time. The decoration check uses it. I kept `_HAS_TORNADO` for the one-time import at t
…[551 chars elided]…
*Checks:**
- Regression test alone, before the fix: failed at `tenacity/__init__.py:790` with `AttributeError: 'NoneType' object has no attribute 'gen'`.
- Regression test alone, after the fix: 1 passed.
- Full suite (`run_tests.py`, no args): `exit=0`, 179 passed, 1 skipped, 15 subtests passed.
- `check_changed.py`: `exit=0`, 0 problems.

**Skipped:** ruff and mypy were not run, because the environment doesn't have them. The reno YAML was checked only by `check_changed.py`, since PyYAML is unavailable here, so it has not been parsed.

Nothing is committed. The changes are in the working tree.
