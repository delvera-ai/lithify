# trajectory base-1

final message:
Fixed: `@tenacity.retry` now decorates normally after `tenacity.tornado = None`.

**Cause:** the decorator tested `_HAS_TORNADO`, a bool computed once at import time. Setting the global to `None` left that bool `True`, so the code went on to read `tornado.gen` and hit the `AttributeError`.

**Change:**
- `tenacity/__init__.py` (in `retry()`): the check is now `tornado is not None`, read from the live global at decoration time. `_HAS_TORNADO` stays for the one-time import gate that conditionally imports `TornadoRetrying`.
- `tests/test_tornado.py`: added `test_tornado_global_unset_at_decoration_time`, which patches `tenacity.tornado` to `None` and decorates a plain function. I added `from unittest import mock` for it.

**Verification:**
- Reproduced the exact `AttributeError` with the project interpreter before editing.
- New test fails without the fix and passes with it.
- Full suite with the project's pytest command: 179 passed, 1 skipped (up from 178 passed, the extra being the new test).
- I did not run ruff or mypy: `ruff` isn't on the PATH here, and I didn't look for a mypy setup.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"tornado\" tenacity/ | head -50", "description": "Find tornado references in tenacity package"}
[tool_result] tenacity/__init__.py:88:    import tornado
tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:805:    from tenacity.tornadoweb import TornadoRetrying
tenacity/tornadoweb.py:18:from tornado import gen
tenacity/tornadoweb.py:24:    from tornado.concurrent import Future
[tool_use Bash] {"command": "sed -n 84,96p tenacity/__init__.py && echo ---- && sed -n 780,815p tenacity/__init__.py", "description": "Show tornado detection and decorator code"}
[tool_result] )
from .wait import wait_random_exponential as wait_full_jitter

try:
    import tornado
except ImportError:
    tornado = None  # type: ignore[assignment]

# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
# so testing the module object for truthiness reads as an always-true check.
# Keep the availability answer in a plain bool instead.
_HAS_TORNADO = tornado is not None

----
                stacklevel=2,
            )
        r: BaseRetrying
        sleep = dkw.get
…[267 chars elided]…
routine_function")
            and tornado.gen.is_coroutine_function(f)
        ):
            r = TornadoRetrying(*dargs, **dkw)
        else:
            r = Retrying(*dargs, **dkw)

        return r.wraps(f)

    return wrap


from tenacity.asyncio import AsyncRetrying  # noqa: E402

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
[assistant] The decorator reads `_HAS_TORNADO`, a bool frozen at import time, and then dereferences `tornado.gen` on the live global. Setting the global to `None` leaves the bool `True`, so the `tornado.gen` access fails. Let me check where else the flag is used and how tests set it.
[tool_use Bash] {"command": "grep -rn \"_HAS_TORNADO\\|tornado = None\\|tenacity.tornado\\|\\.tornado\" --include=*.py . | grep -v \"^./.venv\" | head -30; git log --oneline -1; git status --short", "description": "Find _HAS_TORNADO usages and test patches"}
[tool_result] (eval):1: no matches found: --include=*.py
8bd0241 lithify: probe base
[tool_use Bash] {"command": "grep -rn -e \"_HAS_TORNADO\" -e \"tornado = None\" -e \"tenacity.tornado\" -e \"\\.tornado\" . --exclude-dir=.git --exclude-dir=.venv | head -30", "description": "Search repo for tornado flag and patch usages"}
[tool_result] tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:789:            _HAS_TORNADO
tenacity/__init__.py:804:if _HAS_TORNADO:
tenacity/__init__.py:805:    from tenacity.tornadoweb import TornadoRetrying
doc/source/api.rst:17:.. autoclass:: tenacity.tornadoweb.TornadoRetrying
[assistant] Before editing, I'll reproduce the failure with the project's test interpreter.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint('ok', f())\n\" 2>&1 | tail -3", "description": "Reproduce the AttributeError with project interpreter"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
    and hasattr(tornado.gen, "is_coroutine_function")
                ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'gen'
[assistant] Reproduced: `AttributeError: 'NoneType' object has no attribute 'gen'`. The fix is to make the decorator's check read the live `tornado` global at decoration time, not the import-time bool. I'll keep `_HAS_TORNADO` for the import-time gate that only runs once.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "old_string": "        elif (\n            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "        elif (\n            tornado is not None\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now I'll rerun the reproduction and the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint('ok', f(), type(f.retry))\n\" 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Rerun repro and project test suite"}
[tool_result] ok 1 <class 'tenacity.Retrying'>
................s................................................................................................................ [ 72%]
..................................................                       [100%]
178 passed, 1 skipped, 15 subtests passed in 1.87s
[assistant] The repro passes and the suite is green (178 passed, 1 skipped). I'll add a regression test next to the existing tornado tests.
[tool_use Bash] {"command": "grep -rln \"tornado\" tests/ ; grep -n \"tornado\" tests/*.py | head -30", "description": "Locate existing tornado tests"}
[tool_result] tests/test_tornado.py
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
[tool_use Bash] {"command": "sed -n 1,90p tests/test_tornado.py", "description": "Read existing tornado test file"}
[tool_result] # Copyright 2017 Elisey Zanko
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the speci
…[1377 chars elided]…
    def test_old_tornado(self) -> None:
        old_attr = gen.is_coroutine_function
        try:
            del gen.is_coroutine_function

            # is_coroutine_function was introduced in tornado 4.5;
            # verify that we don't *completely* fall over on old versions
            @retry
            def retryable(thing: NoIOErrorAfterCount) -> None:
                pass

        finally:
            gen.is_coroutine_function = old_attr


if __name__ == "__main__":
    unittest.main()
[assistant] I'll add a test in the same style as `test_old_tornado`, patching the live global to `None` and decorating a plain function.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n\nif __name__", "new_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n    def test_tornado_global_unset_at_decoration_time(self) -> None:\n        # Tests that exercise the non-tornado path set the module global to None\n        # rather than uninstalling tornado; decorating must still work then.\n        with mock.patch(\"tenacity.tornado\", None):\n            @retry\n            def retryable(thing: NoIOErrorAfterCount) -> None:\n                pass\n\n\nif __name__"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\n", "new_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\nfrom unittest import mock\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165608-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll confirm the new test fails without the fix, then passes with it, and run the full suite plus lint.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; echo \"== with fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tornado.py 2>&1 | tail -3; echo \"== without fix\"; cp tenacity/__init__.py /tmp/fixed_init.py && git show HEAD:tenacity/__init__.py > tenacity/__i
…[69 chars elided]…
t_tornado.py -k global_unset 2>&1 | tail -3; cp /tmp/fixed_init.py tenacity/__init__.py && rm /tmp/fixed_init.py; echo \"== full\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; (command -v ruff >/dev/null && ruff check tenacity tests && ruff format --check tenacity tests) 2>&1 | tail -4; git diff --stat", "description": "Verify regression test fails before and passes after fix"}
[tool_result] == with fix
.....                                                                    [100%]
5 passed in 0.03s
== without fix
=========================== short test summary info ============================
FAILED tests/test_tornado.py::TestTornado::test_tornado_global_unset_at_decoration_time
1 failed, 4 deselected in 0.04s
== full
...................................................                      [100%]
179 passed, 1 skipped, 15 subtests passed in 1.84s
 tenacity/__init__.py  | 2 +-
 tests/test_tornado.py | 9 +++++++++
 2 files changed, 10 insertions(+), 1 deletion(-)
[This command modified 1 file you've previously read: tenacity/__init__.py. Call Read before editing.]
[assistant] Test fails without the fix and passes with it; full suite is 179 passed. Let me confirm the source diff is exactly my intended change, since I restored the file via copy.
[tool_use Bash] {"command": "git diff tenacity/__init__.py", "description": "Show source diff of the fix"}
[tool_result] diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 51925ef..bcc3d61 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -786,7 +786,7 @@ def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
         ):
             r = AsyncRetrying(*dargs, **dkw)
         elif (
-            _HAS_TORNADO
+            tornado is not None
             and hasattr(tornado.gen, "is_coroutine_function")
             and tornado.gen.is_coroutine_function(f)
         ):
[assistant] Fixed: `@tenacity.retry` now decorates normally after `tenacity.tornado = None`.

**Cause:** the decorator tested `_HAS_TORNADO`, a bool computed once at import time. Setting the global to `None` left that bool `True`, so the code went on to read `tornado.gen` and hit the `AttributeError`.

**Change:**
- `tenacity/__init__.py` (in `retry()`): the check is now `tornado is not None`, read from the live global at decoration time. `_HAS_TORNADO` stays for the one-time import gate that conditionally imports `TornadoRetrying`.
- `tests/test_tornado.py`: added `test_tornado_global_unset_at_decoration_time`, which patches `tenacity.tornado` to `None` and decorates a plain function. I added `from unittest import mock` for it.

**Verification:**
- Reproduced the exact `AttributeError` with the project interpreter before editing.
- New test fails without the fix and passes with it.
- Full suite with the project's pytest command: 179 passed, 1 skipped (up from 178 passed, the extra being the new test).
- I did not run ruff or mypy: `ruff` isn't on the PATH here, and I didn't look for a mypy setup.

Nothing is committed.
