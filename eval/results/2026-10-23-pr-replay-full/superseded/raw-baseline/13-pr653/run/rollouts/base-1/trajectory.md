# trajectory base-1

final message:
Statistics now stay visible through `functools.wraps` wrappers for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's and reflects the latest run. The full suite passes (167 passed, 1 skipped, including two new regression tests). I did not commit.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` onto the outer wrapper once, at decoration time. At that point `statistics` was the initial `{}`. Each call then rebound `statistics` only on the inner wrapper, so the outer copy never changed.

**Fix:**
- `tenacity/__init__.py`: added a small `_StatisticsView` mapping that reads through to the retry object's current statistics. Each `wraps()` now attaches one view instead of a dict that gets rebound per call.
- `tenacity/asyncio/__init__.py`: the async wrapper does the same.
- Tests: added `test_statistics_visible_through_functools_wraps` to `tests/test_tenacity.py` and `tests/test_asyncio.py`. Both assert identity with `__wrapped__.statistics` and the correct `attempt_number`.
- Release note: `releasenotes/notes/fix-statistics-through-wraps-3c9e1a7d5b2f8e04.yaml`.

**Behaviour changes to review:**
- `func.statistics` is now a `MutableMapping` view rather than a plain `dict`. Equality, indexing and iteration work, but `isinstance(f.statistics, dict)` and `json.dumps(f.statistics)` no longer do. I changed the `_RetryDecorated` protocol annotation to match.
- Reads now follow the calling thread's statistics, as the existing docstring already describes. Previously `func.statistics` was whichever call started last, across all threads.

**Not run:** ruff and mypy are not installed in the project's test environment, so I did not run lint or type checks. Only the test suite ran.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"statistics\" --include=*.py . | grep -v \"/\\.git/\" | head -60", "description": "Check git status and find statistics references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"statistics\" . --exclude-dir=.git | head -80", "description": "Search repo for statistics references"}
[tool_result] tests/test_asyncio.py:291:        self.assertEqual(2, retrying.statistics["attempt_number"])
tests/test_asyncio.py:501:        - statistics contains the value for the latest function run
tests/test_asyncio.py:503:        - retry object statistics are synced with function statistics
tests/test_asyncio.py:517:            _retryable_coroutine_with_2_attempts.statistics,
tests/test_asyncio.py:521:            _retryable_coroutine_with_2_attempts.retry.statistics,
tests/test_asyncio.py:542:           
…[5765 chars elided]…
/index.rst:368:`statistics` attribute attached to the function:
doc/source/index.rst:381:    print(raise_my_exception.statistics)
doc/source/index.rst:576:    print(raise_my_exception.statistics)
doc/source/index.rst:598:statistics should be read from the function `statistics` attribute.
doc/source/index.rst:614:    print(raise_my_exception.statistics)
releasenotes/notes/fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml:5:    clarify that those attributes are write-only and statistics should be
[tool_use Bash] {"command": "sed -n 300,400p tenacity/__init__.py; echo ----; sed -n 190,230p tenacity/asyncio/__init__.py; echo ----; cat releasenotes/notes/fix-retry-wrapper-attributes-f7a3a45b8e90f257.yaml; ls releasenotes/notes | tail -5", "description": "Read retry wrapper and statistics code"}
[tool_result]         )

    def __getstate__(self) -> dict[str, t.Any]:
        # Exclude threading.local which cannot be pickled
        return {k: v for k, v in self.__dict__.items() if k != "_local"}

    def __setstate__(self, state: dict[str, t.Any]) -> None:
        self.__dict__.update(state)
        self._local = threading.local()

    def __str__(self) -> str:
        return self._name if self._name is not None else "<unknown>"

    def __repr__(self) -> str:
        return (
            f"<{self.__
…[5370 chars elided]…

    "retry_any",
    "retry_if_exception",
----
---
fixes:
  - |
    Restore the value of the `retry` attribute for wrapped functions. Also,
    clarify that those attributes are write-only and statistics should be
    read from the function attribute directly.
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 1440,1540p tests/test_tenacity.py; echo ----; sed -n 1855,1910p tests/test_tenacity.py; echo ----; sed -n 2140,2165p tests/test_tenacity.py; echo ----; sed -n 495,560p tests/test_asyncio.py; git log --oneline -3 -- tenacity/__init__.py", "description": "Read existing statistics tests"}
[tool_result]         class Hello:
            def __call__(self) -> str:
                return "Hello"

        retrying = Retrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
        )
        h = retrying.wraps(Hello())
        self.assertEqual(h(), "Hello")

    def test_retry_function_attributes(self) -> None:
        """Test that the wrapped function attributes are exposed as intended.

        - statistics contains the value for the latest function run
        - re
…[8193 chars elided]…
           self.fail("RetryError should have been raised after 1 attempt")


# make sure mypy accepts passing an async sleep function
# https://github.com/jd/tenacity/issues/399
async def my_async_sleep(x: float) -> None:
    await asyncio.sleep(x)


@retry(sleep=my_async_sleep)
868c60b fix: respect enabled=False in iterator protocols (__iter__ / __aiter__) (#643)
e5179bd fix: reraise underlying exception when TryAgain wraps a cause (#640)
6a2a08b fix: add missing space in type annotation (#617)
[tool_use Bash] {"command": "sed -n 1,40p tenacity/__init__.py | grep -n \"import\"; sed -n 645,665p tenacity/__init__.py; grep -n \"^import\\|^from\" tenacity/asyncio/__init__.py; ls <work>/env-tenacity/bin/python 2>&1", "description": "Check imports, WrappedFn typing, and test python"}
[tool_result] 18:import dataclasses
19:import functools
20:import sys
21:import threading
22:import time
23:import typing as t
24:import warnings
25:from abc import ABC, abstractmethod
26:from concurrent import futures
28:from . import _utils
31:from .after import after_log, after_nothing
34:from .before import before_log, before_nothing
37:from .before_sleep import before_sleep_log, before_sleep_nothing
40:from .nap import sleep, sleep_using_event
        clsname = self.__class__.__name__
        return f"<{
…[350 chars elided]…
y_with(self, *args: t.Any, **kwargs: t.Any) -> "_RetryDecorated[P, R]": ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


class _AsyncRetryDecorator(t.Protocol):
    @t.overload
    def __call__(
18:import functools
19:import sys
20:import typing as t
22:import tenacity
23:from tenacity import (
37:from .retry import (
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run baseline test suite"}
[tool_result] ..............s............................................... [ 37%]
...................................................................... [ 79%]
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.87s
[tool_use Bash] {"command": "cat > /tmp/repro_stats.py <<'EOF'\nimport functools, asyncio\nimport tenacity\nfrom tenacity import retry\n\ndef timing(f):\n    @functools.wraps(f)\n    def inner(*a, **k):\n        return f(*a, **k)\n    return inner\n\ndef atiming(f):\n    @functools.wraps(f)\n    async def inner(*a, **k):\n        return await f(*a, **k)\n    return inner\n\n@timing\n@retry(stop=tenacity.stop_afte
…[398 chars elided]…
 async_f.statistics, \"is inner:\", async_f.statistics is async_f.__wrapped__.statistics)\nEOF\n<work>/env-tenacity/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_stats.py').read())\"", "description": "Reproduce empty statistics through wrapper"}
[tool_result] sync outer: {} is inner: False
async outer: {} is inner: False
[assistant] Reproduced: the outer wrapper's `statistics` is the `{}` that `functools.wraps` copied at decoration time, and the inner wrapper rebinds its own attribute on every call, so the outer copy never updates. I'll replace the per-call rebinding with a live view that both wrappers share.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "        @functools.wraps(\n            f, functools.WRAPPER_ASSIGNMENTS + (\"__defaults__\", \"__kwdefaults__\")\n        )\n        def wrapped_f(*args: t.Any, **kw: t.Any) -> t.Any:\n            if not self.enabled
…[1355 chars elided]…
kw)\n\n        def retry_with(*args: t.Any, **kwargs: t.Any) -> \"_RetryDecorated[P, R]\":\n            return self.copy(*args, **kwargs).wraps(f)\n\n        # Preserve attributes\n        wrapped_f.retry = self  # type: ignore[attr-defined]\n        wrapped_f.retry_with = retry_with  # type: ignore[attr-defined]\n        wrapped_f.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "from abc import ABC, abstractmethod\nfrom concurrent import futures", "new_string": "from abc import ABC, abstractmethod\nfrom collections.abc import MutableMapping\nfrom concurrent import futures"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py", "old_string": "class _RetryDecorated(t.Protocol[P, R]):\n    \"\"\"Protocol for functions decorated with @retry.\n\n    Provides the original callable signature plus retry control attributes.\n    \"\"\"\n\n    retry: \"BaseRetryin
…[935 chars elided]…
> int:\n        return len(self._retry.statistics)\n\n    def __repr__(self) -> str:\n        return repr(self._retry.statistics)\n\n\nclass _RetryDecorated(t.Protocol[P, R]):\n    \"\"\"Protocol for functions decorated with @retry.\n\n    Provides the original callable signature plus retry control attributes.\n    \"\"\"\n\n    retry: \"BaseRetrying\"\n    statistics: MutableMapping[str, t.Any]"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/__init__.py has been updated successfully.
[assistant] Now the async wrapper, which has the same per-call rebinding.
[tool_use Bash] {"command": "sed -n 15,40p tenacity/asyncio/__init__.py", "description": "View asyncio module imports"}
[tool_result] # See the License for the specific language governing permissions and
# limitations under the License.

import functools
import sys
import typing as t

import tenacity
from tenacity import (
    AttemptManager,
    BaseRetrying,
    DoAttempt,
    DoSleep,
    RetryCallState,
    RetryError,
    _RetryDecorated,
    _utils,
    after_nothing,
    before_nothing,
)

# Import all built-in retry strategies for easier usage.
from .retry import (
    RetryBaseT,
    retry_all,
    retry_any,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "    _RetryDecorated,\n    _utils,\n    after_nothing,", "new_string": "    _RetryDecorated,\n    _StatisticsView,\n    _utils,\n    after_nothing,"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py", "old_string": "            copy = self.copy()\n            async_wrapped.statistics = copy.statistics  # type: ignore[attr-defined]\n            self._local.statistics = copy.statistics\n            return await copy(fn, *a
…[347 chars elided]…
        self._local.statistics = copy.statistics\n            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]\n\n        # Preserve attributes\n        async_wrapped.retry = self  # type: ignore[attr-defined]\n        async_wrapped.retry_with = wrapped.retry_with  # type: ignore[attr-defined]\n        async_wrapped.statistics = _StatisticsView(self)  # type: ignore[attr-defined]"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now I'll re-run the reproduction and the full suite.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_stats.py').read())\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Re-run repro and full test suite"}
[tool_result] sync outer: {'start_time': 229145.465570541, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt': 2.7959002181887627e-05} is inner: True
async outer: {'start_time': 229145.465730916, 'attempt_number': 2, 'idle_for': 0.0, 'delay_since_first_attempt': 5.637502181343734e-05} is inner: True
..............s............................................... [ 37%]
...................................................................... [ 79%]
..................................                                       [100%]
165 passed, 1 skipped, 12 subtests passed in 1.82s
[assistant] The fix works and the existing suite still passes. Next I'll add regression tests for both sync and async, plus a release note, matching the repo's existing `releasenotes/notes` convention.
[tool_use Bash] {"command": "grep -n \"^import\\|^from\" tests/test_tenacity.py tests/test_asyncio.py; grep -n \"^class TestRetryErrorCallback\\|^class TestDecoratorWrapper\\|^def asynctest\\|^class TestAsync\" tests/test_tenacity.py tests/test_asyncio.py; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml 2>/dev/null || cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Inspect test imports and release note format"}
[tool_result] tests/test_tenacity.py:16:import contextlib
tests/test_tenacity.py:17:import datetime
tests/test_tenacity.py:18:import logging
tests/test_tenacity.py:19:import pickle
tests/test_tenacity.py:20:import re
tests/test_tenacity.py:21:import time
tests/test_tenacity.py:22:import typing
tests/test_tenacity.py:23:import unittest
tests/test_tenacity.py:24:from fractions import Fraction
tests/test_tenacity.py:25:from unittest import mock
tests/test_tenacity.py:27:import pytest
tests/test_tenacity.py:28:fr
…[1068 chars elided]…
:class TestAsyncEnabled(unittest.TestCase):
tests/test_asyncio.py:496:class TestDecoratorWrapper(unittest.TestCase):
tests/test_tenacity.py:1249:class TestDecoratorWrapper(unittest.TestCase):
tests/test_tenacity.py:1909:class TestRetryErrorCallback(unittest.TestCase):
---
features:
  - |
    Add ``min`` parameter to ``wait_exponential_jitter`` to set a minimum wait
    time floor, consistent with ``wait_exponential``. Also accept ``timedelta``
    for ``max``, ``jitter``, and ``min`` parameters.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "        _foobar()\n        self.assertEqual(attempts, [1, 2, 3])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):", "new_string": "        _foobar()\n        self.assertEqual(attempts, [1, 2, 3])\n\n    def te
…[441 chars elided]…
ng\n        @retry(stop=tenacity.stop_after_attempt(2))\n        def _foobar() -> None:\n            raise ValueError(\"retry\")\n\n        with contextlib.suppress(RetryError):\n            _foobar()\n        self.assertIs(_foobar.statistics, _foobar.__wrapped__.statistics)\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\nclass TestRetryErrorCallback(unittest.TestCase):"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "        def timing(f: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:\n            @functools.wraps(f)", "new_string": "        def timing(f: typing.Any) -> typing.Any:\n            @functools.wraps(f)"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py", "old_string": "import contextlib\nimport datetime\nimport logging", "new_string": "import contextlib\nimport datetime\nimport functools\nimport logging"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now the async regression test, next to the existing async statistics test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py", "old_string": "            else:\n                self.fail(\"RetryError should have been raised after 1 attempt\")\n\n\n# make sure mypy accepts passing an async sleep function", "new_string": "            else:\n                
…[492 chars elided]…
(stop=tenacity.stop_after_attempt(2))\n        async def _foobar() -> None:\n            raise ValueError(\"retry\")\n\n        with self.assertRaises(RetryError):\n            await _foobar()\n        self.assertIs(_foobar.statistics, _foobar.__wrapped__.statistics)\n        self.assertEqual(2, _foobar.statistics[\"attempt_number\"])\n\n\n# make sure mypy accepts passing an async sleep function"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/releasenotes/notes/fix-statistics-through-wraps-3c9e1a7d5b2f8e04.yaml", "content": "---\nfixes:\n  - |\n    Fix ``statistics`` being empty on a function decorated with ``@retry`` when\n    it is further wrapped by a decorator using ``functools.wraps``. The outer\n    wrapper now shares the live statistics of the inner one, for both sync and\n    async functions.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164301-bug-when-a-retry-decorated-funct/base-1/releasenotes/notes/fix-statistics-through-wraps-3c9e1a7d5b2f8e04.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tenacity.py -k functools_wraps tests/test_asyncio.py 2>&1 | tail -3; for t in ruff mypy; do $PY -m $t --version >/dev/null 2>&1 && echo \"$t available\"; done; $PY -m ruff check tenacity tests 2>&1 | tail -3; $PY -m ruff format --check tenacity tests 2>&1 | tail -3; $PY -m mypy tenacity 2>&1 | tail -3", "description": "Run full tests, targeted tests, and lint/type checks"}
[tool_result] ..............s............................................... [ 36%]
...................................................................... [ 78%]
....................................                                     [100%]
167 passed, 1 skipped, 12 subtests passed in 1.85s
..                                                                       [100%]
2 passed, 155 deselected in 0.02s
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
[tool_use Bash] {"command": "git status --short && git diff --stat && rm -f /tmp/repro_stats.py", "description": "Show changed files and clean up repro script"}
[tool_result]  M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-statistics-through-wraps-3c9e1a7d5b2f8e04.yaml
 tenacity/__init__.py         | 36 +++++++++++++++++++++++++++++++++---
 tenacity/asyncio/__init__.py |  4 ++--
 tests/test_asyncio.py        | 21 +++++++++++++++++++++
 tests/test_tenacity.py       | 21 +++++++++++++++++++++
 4 files changed, 77 insertions(+), 5 deletions(-)
[assistant] Statistics now stay visible through `functools.wraps` wrappers for both sync and async functions. The outer wrapper's `statistics` is the same object as the inner one's and reflects the latest run. The full suite passes (167 passed, 1 skipped, including two new regression tests). I did not commit.

**Cause:** `functools.wraps` copies the inner wrapper's `__dict__` onto the outer wrapper once, at decoration time. At that point `statistics` was the initial `{}`. Each call then rebound `statistics` only on the inner wrapper, so the outer copy never changed.

**Fix:**
- `tenacity/__init__.py`: add
…[562 chars elided]…
es to review:**
- `func.statistics` is now a `MutableMapping` view rather than a plain `dict`. Equality, indexing and iteration work, but `isinstance(f.statistics, dict)` and `json.dumps(f.statistics)` no longer do. I changed the `_RetryDecorated` protocol annotation to match.
- Reads now follow the calling thread's statistics, as the existing docstring already describes. Previously `func.statistics` was whichever call started last, across all threads.

**Not run:** ruff and mypy are not installed in the project's test environment, so I did not run lint or type checks. Only the test suite ran.
