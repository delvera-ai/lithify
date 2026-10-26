# trajectory comp-1

final message:
`@retry` decoration no longer fails after `tenacity.tornado = None`. The regression test failed with the reported `AttributeError` before the fix and passes after it.

**Cause:** `retry()` checked `_HAS_TORNADO`, a value captured once at import time. With tornado installed it stayed `True` after the global was set to `None`, so `wrap` went on to read `tornado.gen` from `None`.

**Fix** (`tenacity/__init__.py`):
- Added `_has_tornado()`, which returns `tornado is not None` and reads the live global each time it is called.
- `wrap` now calls `_has_tornado()` instead of `_HAS_TORNADO`. The module-level `_HAS_TORNADO` and the import-time `TornadoRetrying` import are unchanged.
- I used a helper rather than testing the `tornado` name directly, because the project's contract notes that mypy would flag a direct truthiness or `is not None` check on the module name.

**Tests and checks:**
- Added `TestTornadoGlobalNone::test_retry_decorates_when_tornado_global_is_none` to `tests/test_tenacity.py`. It is red on the unfixed code and green after the fix.
- Full suite via `run_tests.py`: exit 0, 179 passed, 1 skipped, 15 subtests passed.
- `check_changed.py`: exit 0, 0 problems.
- Ruff and mypy were not run; the checker can't run them here. The new `_has_tornado()` line is the one place mypy could object, and I could not confirm it.
- No existing tests were edited.

**Release note:** added `releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml` under `fixes:`, following the project's contract for behaviour changes.

Nothing is committed. The changes are in the working tree: two modified files and one new release note.

## events
[assistant] I'll start by finding the tornado detection code and the contract headings the project requires before editing under `tenacity/`.
[tool_use Bash] {"command": "grep -rn 'tornado' tenacity/ --include='*.py' && echo --- && grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md && echo --- && cat memory.md 2>/dev/null | head -20; ls .lithify/harness/", "description": "Locate tornado references and list contract headings"}
[tool_result] tenacity/__init__.py:88:    import tornado
tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:805:    from tenacity.tornadoweb import
…[903 chars elided]…
a new accepted type for an existing one
350:## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
379:## 1e. Optional dependency detection: `tornado` in `tenacity/__init__.py`
401:## 2. A release note in `releasenotes/notes/` (reno)
423:## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
437:## 3. A regression test in the matching test file
451:## 4. Keep the change surface minimal
---
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "F=.lithify/harness/skills/tenacity-change-contract/SKILL.md && sed -n '1,18p;379,400p;437,450p' $F && echo ---- && sed -n '80,100p;780,815p' tenacity/__init__.py && echo ---- && cat .lithify/harness/memory.md", "description": "Read contract sections 0, 1e, 3 and tornado code"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, the attributes of a decorated function (`fn.statistics`/`fn.retry`/`fn.retry_with`, also seen through an outer `functools.wraps` decorator), the `for attempt in`/`async for`/`with attempt:` iterator pattern or `AttemptManager`, th
…[6118 chars elided]…
city.asyncio import AsyncRetrying  # noqa: E402

if _HAS_TORNADO:
    from tenacity.tornadoweb import TornadoRetrying


__all__ = [
    "NO_RESULT",
    "AsyncRetrying",
    "AttemptManager",
    "BaseAction",
    "BaseRetrying",
    "DoAttempt",
    "DoSleep",
----
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[assistant] The bug is clear: `_HAS_TORNADO` is a stale import-time snapshot, so `wrap` takes the tornado branch and then reads `tornado.gen` from the `None` global. The contract says the live check should go through a helper that returns a plain bool. Next I'll look at the existing tests and the harness runner before writing the regression test.
[tool_use Bash] {"command": "grep -rn 'tornado' tests/ --include='*.py' | head -40; echo ---; ls <work>/env-tenacity/bin/python && echo PYOK; sed -n '1,60p' .lithify/harness/scripts/run_tests.py | head -80", "description": "Find tornado references in tests and check python env"}
[tool_result] tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
---
<tmp>/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scrat
…[1551 chars elided]…
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
[tool_use Bash] {"command": "sed -n '1,80p' tests/test_tenacity.py | grep -n 'import\\|^class\\|^def' ; grep -n '^class \\|^def \\|^import\\|^from' tests/test_tenacity.py | head -60; tail -30 tests/test_tenacity.py", "description": "Inspect test file imports and structure"}
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
29:import tenacity
30:from tenacity import RetryCallState, RetryError, Retrying, retry
31:from tenacity._utils import override
32:from tenacity.retry import retry_all, retry_any
37:def _make_unset_exception(func_name: str, **kwargs: typing.Any) -> TypeError:
46:def _set_delay_sinc
…[3426 chars elided]…
    retry=tenacity.retry_if_exception_type(ValueError),
            reraise=True,
        )
        restored = pickle.loads(pickle.dumps(retrying))

        calls = 0

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
[assistant] The tests import `tornado` directly, so it is installed and the bug can reproduce. I'll add the regression test first, at the end of `tests/test_tenacity.py`, and run it against the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tests/test_tenacity.py", "old_string": "        result = restored(succeed_on_third)\n        assert result == \"ok\"\n        assert calls == 3\n\n\nif __name__ == \"__main__\":", "new_string": "        result = restored(succeed_on_third)\n        assert
…[126 chars elided]…
s_when_tornado_global_is_none(self) -> None:\n        \"\"\"Setting `tenacity.tornado = None` must not break `@retry` decoration.\"\"\"\n        with mock.patch.object(tenacity, \"tornado\", None):\n\n            @retry(stop=tenacity.stop_after_attempt(2))\n            def succeed() -> str:\n                return \"ok\"\n\n            assert succeed() == \"ok\"\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestTornadoGlobalNone::test_retry_decorates_when_tornado_global_is_none\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -40 /tmp/red.txt", "description": "Run regression test alone against unfixed code"}
[tool_result] exit=1

    def test_retry_decorates_when_tornado_global_is_none(self) -> None:
        """Setting `tenacity.tornado = None` must not break `@retry` decoration."""
        with mock.patch.object(tenacity, "tornado", None):
    
>           @retry(stop=tenacity.stop_after_attempt(2))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_tenacity.py:2377: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

f = <function TestTornadoGlobalNone.test_retry_
…[793 chars elided]…
   ^^^^^^^^^^^
            and tornado.gen.is_coroutine_function(f)
        ):
E       AttributeError: 'NoneType' object has no attribute 'gen'

tenacity/__init__.py:790: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tenacity.py::TestTornadoGlobalNone::test_retry_decorates_when_tornado_global_is_none
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The test fails with the reported error, `AttributeError: 'NoneType' object has no attribute 'gen'`, at `tenacity/__init__.py:790`. Now the fix: a helper that reads the live global at decoration time, used in `wrap` in place of the snapshot. The import-time `_HAS_TORNADO` stays as it is.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tenacity/__init__.py", "old_string": "_HAS_TORNADO = tornado is not None\n\nif t.TYPE_CHECKING:", "new_string": "_HAS_TORNADO = tornado is not None\n\n\ndef _has_tornado() -> bool:\n    # Read the live `tornado` global, so tests that set it to None take effect.\n    return tornado is not None\n\n\nif t.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tenacity/__init__.py", "old_string": "            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "            _has_tornado()\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/tenacity/__init__.py has been updated successfully.
[assistant] Next I'll re-run the regression test alone, then the full suite, then the stdlib checker. I'm running them one after another since each depends on the previous passing.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestTornadoGlobalNone::test_retry_decorates_when_tornado_global_is_none\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -6 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/check.txt", "description": "Run target test, full suite, and check_changed script"}
[tool_result] exit=0

============================== 1 passed in 0.01s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 99%]
tests/test_utils.py::test_find_ordinal PASSED                            [100%]

============== 179 passed, 1 skipped, 15 subtests passed in 1.89s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
changed: tenacity/__init__.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The target test passes, the full suite is green (179 passed, 1 skipped), and `check_changed.py` reports no problems. The contract also asks for a release note for behaviour changes, so I'll read §2 and check the existing notes.
[tool_use Bash] {"command": "sed -n '401,422p;451,470p' .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | grep -i 'falsy\\|none\\|wait' | tail -1) 2>/dev/null", "description": "Read release-note section and sample existing note"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[839 chars elided]…
# 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
---
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Bash] {"command": "cat releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml && python3 -c \"import secrets;print(secrets.token_hex(8))\"", "description": "Read a sample fixes note and generate a hex suffix"}
[tool_result] ---
fixes:
  - |
    `wait_base.__radd__` is now annotated as taking the `int` seed that
    `sum()` supplies, so `sum()` over a list of wait strategies type checks
    without `type: ignore` on the list items. A non-zero left operand now
    returns `NotImplemented`, raising `TypeError` at the point of the
    addition instead of building a wait strategy that fails when called.
6ba344291b11c6ea
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml", "content": "---\nfixes:\n  - |\n    Decorating a function with ``@retry`` no longer raises\n    ``AttributeError: 'NoneType' object has no attribute 'gen'`` after\n    ``tenacity.tornado`` has been set to ``None``. Whether tornado is\n    available is now read from the module at decoration time.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/comp-1/releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml (file state is current in your context — no need to Read it back)
[assistant] I added a release note, so I'll re-run the checker to validate its shape, and show the final diff.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"exit=$?\"; cat /tmp/check2.txt; git status --short; git diff -- tenacity/", "description": "Re-run change checker and show tenacity diff"}
[tool_result] exit=0
changed: releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml, tenacity/__init__.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tests/test_tenacity.py
?? releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 51925ef..bbd8e0f 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -94,6
…[190 chars elided]…
obal, so tests that set it to None take effect.
+    return tornado is not None
+
+
 if t.TYPE_CHECKING:
     if sys.version_info >= (3, 11):
         from typing import Self
@@ -786,7 +792,7 @@ def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
         ):
             r = AsyncRetrying(*dargs, **dkw)
         elif (
-            _HAS_TORNADO
+            _has_tornado()
             and hasattr(tornado.gen, "is_coroutine_function")
             and tornado.gen.is_coroutine_function(f)
         ):
[assistant] `@retry` decoration no longer fails after `tenacity.tornado = None`. The regression test failed with the reported `AttributeError` before the fix and passes after it.

**Cause:** `retry()` checked `_HAS_TORNADO`, a value captured once at import time. With tornado installed it stayed `True` after the global was set to `None`, so `wrap` went on to read `tornado.gen` from `None`.

**Fix** (`tenacity/__init__.py`):
- Added `_has_tornado()`, which returns `tornado is not None` and reads the live global each time it is called.
- `wrap` now calls `_has_tornado()` instead of `_HAS_TORNADO`. The module
…[450 chars elided]…
the fix.
- Full suite via `run_tests.py`: exit 0, 179 passed, 1 skipped, 15 subtests passed.
- `check_changed.py`: exit 0, 0 problems.
- Ruff and mypy were not run; the checker can't run them here. The new `_has_tornado()` line is the one place mypy could object, and I could not confirm it.
- No existing tests were edited.

**Release note:** added `releasenotes/notes/tornado-global-none-decoration-6ba344291b11c6ea.yaml` under `fixes:`, following the project's contract for behaviour changes.

Nothing is committed. The changes are in the working tree: two modified files and one new release note.
