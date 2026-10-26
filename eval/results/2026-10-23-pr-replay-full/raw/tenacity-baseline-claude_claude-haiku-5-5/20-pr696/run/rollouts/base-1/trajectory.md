# trajectory base-1

final message:
Fixed: decorating with `@tenacity.retry` now works after `tenacity.tornado = None`.

**Cause:** `tenacity/__init__.py` computes `_HAS_TORNADO` once at import time, but `wrap()` in `retry()` checked that flag and then dereferenced `tornado.gen` on the live global. Once a test set the global to `None`, the stale flag was still `True` and the lookup raised `AttributeError`.

**Fix** (`tenacity/__init__.py`): the branch in `wrap()` now tests the live global, `tornado is not None`, instead of `_HAS_TORNADO`. I kept `_HAS_TORNADO` because the bottom-of-module import still uses it.

**Regression test** (`tests/test_tornado.py`): `test_tornado_global_unset_at_decoration_time` patches `tenacity.tornado` to `None` with `mock.patch.object`, decorates a function, and checks that it retries correctly. I confirmed it fails on the original code and passes with the fix. I did not weaken or edit any existing test.

**Results:** the project suite passes with the fix: 179 passed, 1 skipped.

**Not run:** `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run lint or type checks. The change is a one-line condition swap, but the `_HAS_TORNADO` comment mentions mypy and you may want to check that.

I haven't committed anything. The changes are in `tenacity/__init__.py` and `tests/test_tornado.py` in this worktree.

## events
[tool_use Bash] {"command": "grep -rn \"tornado\" tenacity/__init__.py | head -50; echo ---; grep -rn \"tornado\" tenacity/*.py | grep -v \"__init__\" | head -30", "description": "Find tornado references in tenacity source"}
[tool_result] tenacity/__init__.py:88:    import tornado
tenacity/__init__.py:90:    tornado = None  # type: ignore[assignment]
tenacity/__init__.py:92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
tenacity/__init__.py:95:_HAS_TORNADO = tornado is not None
tenacity/__init__.py:790:            and hasattr(tornado.gen, "is_coroutine_function")
tenacity/__init__.py:791:            and tornado.gen.is_coroutine_function(f)
tenacity/__init__.py:805:    from tenacity.tornadoweb import TornadoRetrying
---
tenacity/tornadoweb.py:18:from tornado import gen
tenacity/tornadoweb.py:24:    from tornado.concurrent import Future
[tool_use Bash] {"command": "sed -n 80,100p tenacity/__init__.py; echo ---; sed -n 770,815p tenacity/__init__.py", "description": "Read tornado import and retry decoration code"}
[tool_result]     wait_incrementing,
    wait_none,
    wait_random,
    wait_random_exponential,
)
from .wait import wait_random_exponential as wait_full_jitter

try:
    import tornado
except ImportError:
    tornado = None  # type: ignore[assignment]

# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
# so testing the module object for truthiness reads as an always-true check.
# Keep the availability answer in a plain bool instead.
_HAS_TORNADO = tornado is not None

if t.TYPE_CH
…[915 chars elided]…
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
[assistant] The cause is visible: `_HAS_TORNADO` is computed once at import, but `wrap()` reads it and then dereferences `tornado.gen` on the live global. I'll reproduce it with the project's test interpreter before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ls -la $PY 2>&1; $PY -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint(f())\n\" 2>&1 | tail -3; echo ---; grep -rn \"tornado\" tests/*.py | head -20", "description": "Reproduce the bug and locate tornado tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
    and hasattr(tornado.gen, "is_coroutine_function")
                ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'gen'
---
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
[assistant] Reproduced: `AttributeError: 'NoneType' object has no attribute 'gen'`. The fix is to read the live `tornado` global inside `wrap()` rather than the import-time `_HAS_TORNADO` snapshot.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "old_string": "        elif (\n            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "        elif (\n            tornado is not None\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"\nimport tenacity\ntenacity.tornado = None\n@tenacity.retry\ndef f(): return 1\nprint(type(f.retry).__name__, f())\n\" 2>&1 | tail -3; echo ---; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run the project test suite"}
[tool_result] Retrying 1
---
................s................................................................................................................ [ 72%]
..................................................                       [100%]
178 passed, 1 skipped, 15 subtests passed in 1.82s
[assistant] The fix works and the existing suite passes (178 passed, 1 skipped). I'll add a regression test so this doesn't come back.
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1; sed -n 1,70p tests/test_tornado.py; grep -n \"^import\\|^from\" tests/test_tenacity.py | head; grep -rln \"mock.patch\\|monkeypatch\" tests | head -3", "description": "Inspect tornado test file and conventions"}
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
…[1487 chars elided]…
del gen.is_coroutine_function

            # is_coroutine_function was introduced in tornado 4.5;
            # verify that we don't *completely* fall over on old versions
            @retry
            def retryable(thing: NoIOErrorAfterCount) -> None:
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
tests/test_asyncio.py
tests/test_tenacity.py
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1; sed -n 70,95p tests/test_tornado.py", "description": "Read rest of tornado test file"}
[tool_result]             def retryable(thing: NoIOErrorAfterCount) -> None:
                pass

        finally:
            gen.is_coroutine_function = old_attr


if __name__ == "__main__":
    unittest.main()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n\nif __name__", "new_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n    def test_tornado_global_unset_at_decorat
…[92 chars elided]…
non-tornado\n        # path; decorating must read that live global, not an import-time flag.\n        with mock.patch.object(tenacity, \"tornado\", None):\n\n            @retry\n            def retryable(thing: NoIOErrorAfterCount) -> None:\n                thing.go()\n\n        thing = NoIOErrorAfterCount(2)\n        retryable(thing)\n        assert thing.counter == thing.count\n\n\nif __name__"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\n\nfrom tornado import gen, testing\n\nfrom tenacity import RetryError, retry, stop_after_attempt, tornadoweb", "new_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\nfrom unittest import mock\n\nfrom tornado import gen, testing\n\nimport tenacity\nfrom tenacity import RetryError, retry, stop_after_attempt, tornadoweb"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully.
[assistant] Now I'll confirm the new test fails without the fix, then run the full suite with the fix in place.
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-38fec5e48183/20261023-193113-bug-setting-the-module-global-te/base-1; PY=<work>/env-tenacity/bin/python; git stash list >/dev/null; cp tenacity/__init__.py /tmp/fixed_init.py && git show HEAD:tenacity/__init__.py > tenac
…[60 chars elided]…
lor=no tests/test_tornado.py -k global_unset 2>&1 | tail -2; cp /tmp/fixed_init.py tenacity/__init__.py; echo \"--- with fix:\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; echo \"--- lint/type:\"; $PY -m ruff check tenacity tests 2>&1 | tail -2; $PY -m mypy tenacity 2>&1 | tail -2; git status --short", "description": "Check regression test fails pre-fix and full suite passes"}
[tool_result] FAILED tests/test_tornado.py::TestTornado::test_tornado_global_unset_at_decoration_time
1 failed, 4 deselected in 0.05s
--- with fix:
...................................................                      [100%]
179 passed, 1 skipped, 15 subtests passed in 1.81s
--- lint/type:
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
 M tenacity/__init__.py
 M tests/test_tornado.py
[assistant] Fixed: decorating with `@tenacity.retry` now works after `tenacity.tornado = None`.

**Cause:** `tenacity/__init__.py` computes `_HAS_TORNADO` once at import time, but `wrap()` in `retry()` checked that flag and then dereferenced `tornado.gen` on the live global. Once a test set the global to `None`, the stale flag was still `True` and the lookup raised `AttributeError`.

**Fix** (`tenacity/__init__.py`): the branch in `wrap()` now tests the live global, `tornado is not None`, instead of `_HAS_TORNADO`. I kept `_HAS_TORNADO` because the bottom-of-module import still uses it.

**Regression test
…[144 chars elided]…
rates a function, and checks that it retries correctly. I confirmed it fails on the original code and passes with the fix. I did not weaken or edit any existing test.

**Results:** the project suite passes with the fix: 179 passed, 1 skipped.

**Not run:** `ruff` and `mypy` aren't installed in the project's test environment, so I didn't run lint or type checks. The change is a one-line condition swap, but the `_HAS_TORNADO` comment mentions mypy and you may want to check that.

I haven't committed anything. The changes are in `tenacity/__init__.py` and `tests/test_tornado.py` in this worktree.
