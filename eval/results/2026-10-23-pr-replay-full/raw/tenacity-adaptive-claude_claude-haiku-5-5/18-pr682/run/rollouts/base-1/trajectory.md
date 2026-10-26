# trajectory base-1

final message:
Every method that overrides a tenacity base-class method now carries `@override`, and `from tenacity._utils import override` works on Python 3.10+. Changes are uncommitted in the worktree.

**What changed**
- **`tenacity/_utils.py`**: `override` is `typing.override` on 3.12+. Below 3.12 it is a PEP 698 fallback that sets `__override__ = True` and returns the function. It tolerates objects that reject attribute assignment.
- **57 override sites** across `retry.py`, `wait.py`, `stop.py`, `__init__.py` (`Retrying`), `tornadoweb.py`, `asyncio/__init__.py` and `asyncio/retry.py`. Each file gets one `from tenacity._utils import override` import. `tenacity/__init__.py` uses the relative form to match its existing imports.
- **`tests/test_tenacity.py`**: `ConcreteRetrying.__call__`, the one test helper that subclasses a tenacity base.

**Scope choice:** I marked overrides of methods defined on tenacity's own bases. I did not mark overrides of stdlib methods, such as `RetryError.__init__`/`__str__`, `Future.__init__`, `CustomError`, `CapturingHandler.emit`, `ExplodingPower.__pow__`, and the `setUp` methods. Those cannot be orphaned by renaming a tenacity base method, so the requirement's rationale does not reach them. If you want them marked too, say so and I'll add them.

**Verification**
- Project tests: `173 passed, 1 skipped`.
- Ruff 0.16.1 and mypy 2.3.0 (the dev-group pins, installed in a scratch venv under `/tmp`): ruff check and format clean, mypy strict clean on 19 files.
- Runtime check: all 57 expected tenacity methods carry the marker, with no extras.
- The Python 3.10/3.11 fallback path is not run by the 3.12 env, and no interpreter below 3.12 is installed here. I exec'd that branch with the version check forced to false, and it returns the function and sets the marker.

I did not commit anything.

## events
[assistant] I'll start by finding the base classes and every override site in the repo.
[tool_use Bash] {"command": "git status --short | head && ls && cat tenacity/_utils.py | head -80 && grep -n \"python_requires\\|requires-python\\|Programming Language\" pyproject.toml setup.cfg 2>/dev/null; ls tenacity tests"}
[tool_result] AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
# Copyright 2016 Julien Danjou
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
# distributed
…[2033 chars elided]…
6:    "Programming Language :: Python :: 3.10",
27:    "Programming Language :: Python :: 3.11",
28:    "Programming Language :: Python :: 3.12",
29:    "Programming Language :: Python :: 3.13",
30:    "Programming Language :: Python :: 3.14",
tenacity:
__init__.py
_utils.py
_version.py
after.py
asyncio
before.py
before_sleep.py
nap.py
py.typed
retry.py
stop.py
tornadoweb.py
wait.py

tests:
__init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
[tool_use Bash] {"command": "cat AGENTS.md | head -60; cat CLAUDE.md | head -40; grep -rn \"^class \\|    def \\|    async def \" tenacity/ | grep -v \"_utils.py\" | head -300"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[16229 chars elided]…
") -> DoAttempt | DoSleep | t.Any:
tenacity/asyncio/__init__.py:162:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
tenacity/asyncio/__init__.py:165:    def __aiter__(self) -> "AsyncRetrying":
tenacity/asyncio/__init__.py:175:    async def __anext__(self) -> AttemptManager:
tenacity/asyncio/__init__.py:197:    def wraps(self, fn: t.Callable[P, R]) -> _RetryDecorated[P, R]:
tenacity/asyncio/__init__.py:204:        async def async_wrapped(*args: t.Any, **kwargs: t.Any) -> t.Any:
[assistant] Scope is clear: overrides of methods defined on tenacity's base classes, plus the test helpers. Before editing, I'll check the test environment and the lint/type config, then scan for every override with introspection rather than by hand.
[tool_use Bash] {"command": "ls <work>/env-tenacity/bin/python 2>&1; which python3; python3 --version; sed -n 1,200p pyproject.toml | grep -n -A15 \"\\[tool\\.\\(mypy\\|ruff\\|pyright\\)\\]\\|dependency-groups\\|optional-dependencies\" | head -80; ls .github 2>/dev/null; ls -a"}
[tool_result] <work>/env-tenacity/bin/python
<work>/env-tenacity/bin/python3
Python 3.12.13
41:[project.optional-dependencies]
42-doc = [
43-    "reno",
44-    "sphinx",
45-]
46-test = [
47-    "pytest",
48-    "tornado>=6.0",
49-]
50-
51:[dependency-groups]
52-dev 
…[1450 chars elided]…
ff.
121-warn_unreachable = true
122-disallow_any_unimported = true
123-extra_checks = true
124-enable_error_code = [
125-    "deprecated",
126-    "exhaustive-match",
127-    "ignore-without-code",
128-    "mutable-override",
129-    "possibly-undefined",
130-    "redundant-expr",
dependabot.yml
workflows
.
..
.agents
.claude
.editorconfig
.git
.github
.gitignore
.lithify
.mergify.yml
.readthedocs.yml
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
[assistant] The project's checks are pytest plus ruff and mypy (strict). I'll scan with introspection: any class defined in `tenacity` or `tests` whose function shadows a method on a base class defined in those packages.
[tool_use Bash] {"command": "mkdir -p /tmp/override_scan && cat > /tmp/override_scan/scan.py <<'EOF'\nimport importlib, inspect, pkgutil, sys, types\nsys.path.insert(0, \".\")\nmods = []\nfor pkg_name in (\"tenacity\", \"tests\"):\n    pkg = importlib.import_module(pkg_name)\n    mods.append(pkg)\n    for m in pkgutil.walk_packages(pkg.__path__, pkg_name + \".\"):\n        try:\n            mods.append(importlib.
…[1196 chars elided]…
nd local(obj):\n        walk(obj)\nfor row in sorted(set(out)):\n    print(*row, sep=\" | \")\nEOF\ncd ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1 && <work>/env-tenacity/bin/python -I /tmp/override_scan/scan.py"}
[tool_result] tenacity | Retrying | __call__ | BaseRetrying | 517
tenacity.asyncio | AsyncRetrying | __call__ | BaseRetrying | 111
tenacity.asyncio | AsyncRetrying | __init__ | BaseRetrying | 75
tenacity.asyncio | AsyncRetrying | __iter__ | BaseRetrying | 162
tenacity.asyncio | AsyncRetrying | _add_action_func | BaseRetrying | 136
tenacity.asyncio | AsyncRetrying | _run_retry | BaseRetrying | 139
tenacity.asyncio | AsyncRetrying | _run_stop | BaseRetrying | 149
tenacity.asyncio | AsyncRetrying | _run_wait | B
…[2797 chars elided]…
| 89
tenacity.wait | wait_exception | __call__ | wait_base | 149
tenacity.wait | wait_exponential | __call__ | wait_base | 206
tenacity.wait | wait_exponential_jitter | __call__ | wait_base | 297
tenacity.wait | wait_fixed | __call__ | wait_base | 57
tenacity.wait | wait_incrementing | __call__ | wait_base | 176
tenacity.wait | wait_none | __init__ | wait_fixed | 64
tenacity.wait | wait_random | __call__ | wait_base | 77
tenacity.wait | wait_random_exponential | __call__ | wait_exponential | 252
[assistant] The scan finds 69 override sites in `tenacity/`, and none in `tests/`. That's suspicious for "the test helpers", so I'll check the test classes by hand.
[tool_use Bash] {"command": "grep -rn \"class \\|    def \\|    async def \" tests/ | grep -v \"def test_\" | head -80"}
[tool_result] tests/test_utils.py:7:    async def async_func() -> None:
tests/test_utils.py:10:    def sync_func() -> None:
tests/test_utils.py:13:    class AsyncClass:
tests/test_utils.py:14:        async def __call__(self) -> None:
tests/test_utils.py:17:    class SyncClass:
tests/test_utils.py:18:        def __call__(self) -> None:
tests/test_utils.py:25:    partial_async_class = functools.partial(AsyncClass().__call__)
tests/test_utils.py:26:    partial_sync_class = functools.partial(SyncClass().__call__)
…[4716 chars elided]…
nacity.py:431:        def wait_func(retry_state: RetryCallState) -> typing.Any:
tests/test_tenacity.py:452:        def predicate(exc: BaseException) -> float:
tests/test_tenacity.py:506:    def _assert_range(self, wait: float, min_: float, max_: float) -> None:
tests/test_tenacity.py:510:    def _assert_inclusive_range(self, wait: float, low: float, high: float) -> None:
tests/test_tenacity.py:514:    def _assert_inclusive_epsilon(
tests/test_tenacity.py:548:        def always_return_1() -> int:
[assistant] The scan missed test helpers because they are nested in test methods and only exist at run time. I'll grep for them directly.
[tool_use Bash] {"command": "sed -n 80,112p tests/test_tenacity.py; grep -rn \"class .*(\" tests/ | grep -v \"unittest.TestCase\\|testing.AsyncTestCase\\|Exception)\\|Error)\"; grep -rn \"__call__\\|def __init__\\|def iter\\|def _check\\|def wait\\|def stop\" tests/ | head -30"}
[tool_result]     retry_state.upcoming_sleep = upcoming_sleep

    _set_delay_since_start(retry_state, delay_since_first_attempt)
    return retry_state


class TestBase(unittest.TestCase):
    def test_retrying_repr(self) -> None:
        class ConcreteRetrying(tenacity.BaseRetrying):
            def __call__(
                self, fn: typing.Any, *args: typing.Any, **kwargs: typing.Any
            ) -> typing.Any:
                pass

        repr(ConcreteRetrying())

    def test_callstate_repr(self) -> N
…[2049 chars elided]…
nit__(self, count: int) -> None:
tests/test_tenacity.py:1083:    def __init__(self, count: int) -> None:
tests/test_tenacity.py:1109:    def __init__(self, value: str) -> None:
tests/test_tenacity.py:1121:    def __init__(self, count: int) -> None:
tests/test_tenacity.py:1139:    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
tests/test_tenacity.py:1502:            def __call__(self) -> str:
tests/test_tenacity.py:2240:            def __call__(self, seconds: float) -> None:
[assistant] Test helpers in scope: `ConcreteRetrying.__call__` in `tests/test_tenacity.py`. The request says "every method", so I also want to see what the scan turns up if stdlib base classes (e.g. `Exception`, `futures.Future`, `logging.Handler`) count too.
[tool_use Bash] {"command": "sed -e 's/if base is object or not local(base):/if base is object:/' /tmp/override_scan/scan.py > /tmp/override_scan/scan_all.py && <work>/env-tenacity/bin/python -I /tmp/override_scan/scan_all.py > /tmp/override_scan/all.txt; <work>/env-tenacity/bin/python -I /tmp/override_scan/scan.py > /tmp/override_scan/local.txt; wc -l /tmp/override_scan/*.txt; comm -23 <(sort /tmp/override_scan/all.txt) <(sort /tmp/override_scan/local.txt)"}
[tool_result]       66 /tmp/override_scan/all.txt
      57 /tmp/override_scan/local.txt
     123 total
tenacity | Future | __init__ | Future | 545
tenacity | RetryError | __init__ | Exception | 187
tenacity | RetryError | __str__ | BaseException | 204
tests.test_after | TestAfterLogFormat | setUp | TestCase | 14
tests.test_tenacity | CapturingHandler | __init__ | Handler | 1139
tests.test_tenacity | CapturingHandler | emit | Handler | 1143
tests.test_tenacity | CustomError | __init__ | Exception | 1109
tests.test_tenacity | CustomError | __str__ | BaseException | 1112
tests.test_tenacity | TestRetryErrorCallback | setUp | TestCase | 1999
[assistant] The stdlib-base hits (`RetryError.__str__`, `Future.__init__`, `setUp`, `CapturingHandler.emit`, and so on) are overrides of stdlib methods, not of anything this package defines. I'll leave them alone and note that in the summary. So the scope is the 57 tenacity-hierarchy sites plus `ConcreteRetrying.__call__` in the tests. Next I'll check the import headers and confirm nothing already decorates those lines.
[tool_use Bash] {"command": "for f in tenacity/retry.py tenacity/wait.py tenacity/stop.py tenacity/__init__.py tenacity/asyncio/__init__.py tenacity/asyncio/retry.py tenacity/tornadoweb.py tests/test_tenacity.py; do echo \"== $f\"; awk '/^(import|from)|^if TYPE|^    from|^    import/{print NR\": \"$0} /^class /{exit}' $f; done; echo; grep -rn \"^\\s*@\" tenacity tests | grep -v \"@retry\\|@wraps\\|@functools\\|@pytest\\|@override\" | head; grep -n \"_utils\" tenacity/*.py tenacity/asyncio/*.py | grep import"}
[tool_result] == tenacity/retry.py
17: import abc
18: import re
19: import typing
22:     from tenacity import RetryCallState
== tenacity/wait.py
17: import abc
18: import math
19: import random
20: import typing
21: import warnings
23: from tenacity import _utils
26:     from tenacity import RetryCallState
== tenacity/stop.py
16: import abc
17: import typing
19: from tenacity import _utils
22:     import threading
24:     from tenacity import RetryCallState
== tenacity/__init__.py
18: import dataclasses
19: 
…[2165 chars elided]…
@property
tenacity/__init__.py:504:    @abstractmethod
tenacity/__init__.py:549:    @property
tenacity/__init__.py:554:    @classmethod
tenacity/__init__.py:28:from . import _utils
tenacity/after.py:19:from tenacity import _utils
tenacity/before.py:19:from tenacity import _utils
tenacity/before_sleep.py:20:from tenacity import _utils
tenacity/wait.py:23:from tenacity import _utils
tenacity/stop.py:19:from tenacity import _utils
tenacity/asyncio/retry.py:19:from tenacity import _utils, retry_base
[assistant] One thing to fix before running the inserter: `TornadoRetrying.__call__` is wrapped by `@gen.coroutine`, so the scan's line number points into tornado's source, not ours. Rather than trust line numbers, I'll locate each target by AST (module, class qualname, method name) and insert `@override` above any existing decorators.
[tool_use Bash] {"command": "cat > /tmp/override_scan/apply.py <<'EOF'\nimport ast, os, sys\nROOT = sys.argv[1]\ntargets = {}\nfor line in open(\"/tmp/override_scan/local.txt\"):\n    if not line.strip():\n        continue\n    mod, cls, name, *_ = [p.strip() for p in line.split(\"|\")]\n    if mod.startswith(\"tests\"):\n        continue  # handled manually\n    path = os.path.join(ROOT, *mod.split(\".\"))\n    
…[1194 chars elided]…
h, \"w\").write(\"\".join(lines))\n    print(path, len(inserts))\nEOF\ncd ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1 && <work>/env-tenacity/bin/python -I /tmp/override_scan/apply.py \"$PWD\" && git diff --stat"}
[tool_result] ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/__init__.py 1
~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py 9
~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/retry.py 11
~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-meth
…[267 chars elided]…
e-1/tenacity/tornadoweb.py 2
~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/wait.py 10
 tenacity/__init__.py         |  1 +
 tenacity/asyncio/__init__.py |  9 +++++++++
 tenacity/asyncio/retry.py    | 11 +++++++++++
 tenacity/retry.py            | 17 +++++++++++++++++
 tenacity/stop.py             |  7 +++++++
 tenacity/tornadoweb.py       |  2 ++
 tenacity/wait.py             | 10 ++++++++++
 7 files changed, 57 insertions(+)
[assistant] 57 insertions, matching the scan. Now the `override` helper in `_utils.py`, which is the one piece that needs real design. I'll put it after `MAX_WAIT`, which is the module's existing version-independent constant block.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/_utils.py", "old_string": "MAX_WAIT = sys.maxsize / 2\n", "new_string": "MAX_WAIT = sys.maxsize / 2\n\nif sys.version_info >= (3, 12):\n    from typing import override\nelse:\n    _F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\n\n    def override(method: _F) -> _F:\n        \"\"\"Backport of PEP 698 ``typing.override`` for Python < 3.12.\"\"\"\n        try:\n            method.__override__ = True  # type: ignore[attr-defined]\n        except (AttributeError, TypeError):\n            pass\n        return method\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/_utils.py has been updated successfully.
[assistant] Now the imports. I'll check the exact import blocks so each addition follows the file's isort layout.
[tool_use Bash] {"command": "for f in tenacity/retry.py tenacity/wait.py tenacity/stop.py tenacity/asyncio/__init__.py tenacity/asyncio/retry.py tenacity/tornadoweb.py; do echo \"== $f\"; sed -n '14,32p' $f | cat -A | cut -c1-90 | sed 's/\\$$//' ; done 2>/dev/null | head -150; echo ==__init__; sed -n 26,31p tenacity/__init__.py; echo ==test; sed -n 26,40p tests/test_tenacity.py"}
[tool_result ERROR] Exit code 1
== tenacity/retry.py
== tenacity/wait.py
== tenacity/stop.py
== tenacity/asyncio/__init__.py
== tenacity/asyncio/retry.py
== tenacity/tornadoweb.py
(eval):1: =__init__ not found
[tool_use Bash] {"command": "for f in tenacity/retry.py tenacity/wait.py tenacity/stop.py tenacity/asyncio/__init__.py tenacity/asyncio/retry.py tenacity/tornadoweb.py tenacity/__init__.py tests/test_tenacity.py; do echo \"--- $f\"; sed -n '14,40p' $f | grep -n \"\" | sed -n '1,27p' | grep -v \"^\\s*$\" | head -22; done"}
[tool_result] --- tenacity/retry.py
1:# See the License for the specific language governing permissions and
2:# limitations under the License.
3:
4:import abc
5:import re
6:import typing
7:
8:if typing.TYPE_CHECKING:
9:    from tenacity import RetryCallState
10:
11:
12:class retry_base(abc.ABC):
13:    """Abstract base class for retry strategies."""
14:
15:    @abc.abstractmethod
16:    def __call__(self, retry_state: "RetryCallState") -> bool:
17:        pass
18:
19:    def __and__(self, other: "RetryBaseT")
…[3813 chars elided]…
py
1:# See the License for the specific language governing permissions and
2:# limitations under the License.
3:import contextlib
4:import datetime
5:import logging
6:import pickle
7:import re
8:import time
9:import typing
10:import unittest
11:from fractions import Fraction
12:from unittest import mock
13:
14:import pytest
15:
16:import tenacity
17:from tenacity import RetryCallState, RetryError, Retrying, retry
18:from tenacity.retry import retry_all, retry_any
19:
20:_unset = object()
21:
22:
[assistant] Each file's layout is clear. I'll add `from tenacity._utils import override` in each file's first-party import block (relative style in `tenacity/__init__.py`, matching how that file already imports `_utils`).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/retry.py", "old_string": "import typing\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState", "new_string": "import typing\n\nfrom tenacity._utils import override\n\nif typing.TYPE_CHECKING:\n    from tenacity import RetryCallState"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/wait.py", "old_string": "from tenacity import _utils\n\nif typing.TYPE_CHECKING:", "new_string": "from tenacity import _utils\nfrom tenacity._utils import override\n\nif typing.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/stop.py", "old_string": "from tenacity import _utils\n\nif typing.TYPE_CHECKING:", "new_string": "from tenacity import _utils\nfrom tenacity._utils import override\n\nif typing.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/stop.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/__init__.py", "old_string": "from . import _utils\n\n# Import all built-in after strategies", "new_string": "from . import _utils\nfrom ._utils import override\n\n# Import all built-in after strategies"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py", "old_string": "    after_nothing,\n    before_nothing,\n)\n", "new_string": "    after_nothing,\n    before_nothing,\n)\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/retry.py", "old_string": "from tenacity import _utils, retry_base\n\nif typing.TYPE_CHECKING:", "new_string": "from tenacity import _utils, retry_base\nfrom tenacity._utils import override\n\nif typing.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/asyncio/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/tornadoweb.py", "old_string": "from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState\n", "new_string": "from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/tornadoweb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tests/test_tenacity.py", "old_string": "from tenacity.retry import retry_all, retry_any\n\n_unset", "new_string": "from tenacity._utils import override\nfrom tenacity.retry import retry_all, retry_any\n\n_unset"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tests/test_tenacity.py", "old_string": "        class ConcreteRetrying(tenacity.BaseRetrying):\n            def __call__(", "new_string": "        class ConcreteRetrying(tenacity.BaseRetrying):\n            @override\n            def __call__("}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] All edits applied. Now the test suite, using the project's command, plus a check that the 3.10/3.11 fallback branch behaves like the PEP 698 reference, since the 3.12 env would never exercise it.
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ls /usr/bin/python3* /opt/homebrew/bin/python3* /usr/local/bin/python3* 2>/dev/null; which uv ruff mypy 2>/dev/null; <work>/env-tenacity/bin/python -c \"import ruff\" 2>&1 | tail -1; <work>/env-tenacity/bin/python -m mypy --version 2>&1 | tail -1"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.88s
/opt/homebrew/bin/python3
/opt/homebrew/bin/python3-config
/opt/homebrew/bin/python3.14
/opt/homebrew/bin/python3.14-config
/usr/bin/python3
/usr/local/bin/python3
/usr/local/bin/python3-config
/usr/local/bin/python3-intel64
/usr
…[35 chars elided]…
n/python3.13-config
/usr/local/bin/python3.13-intel64
/usr/local/bin/python3.13t
/usr/local/bin/python3.13t-config
/usr/local/bin/python3.13t-intel64
/usr/local/bin/python3t
/usr/local/bin/python3t-config
/usr/local/bin/python3t-intel64
uv not found
ruff not found
mypy not found
ModuleNotFoundError: No module named 'ruff'
<work>/env-tenacity/bin/python: No module named mypy
[assistant] The suite passes: 173 passed, 1 skipped. Ruff and mypy are not in the project env, but the dev group pins them, so I'll install those exact versions in a scratch venv under `/tmp`. I'll also check the runtime behaviour of the override marker.
[tool_use Bash] {"command": "cd /tmp/override_scan && python3 -m venv venv >/dev/null 2>&1 && ./venv/bin/pip install -q ruff==0.16.1 mypy==2.3.0 tornado pytest trio 2>&1 | tail -3; ./venv/bin/ruff --version; ./venv/bin/mypy --version"}
[tool_result] [notice] A new release of pip is available: 25.0.1 -> 26.2.2
[notice] To update, run: python3.12 -m pip install --upgrade pip
ruff 0.16.1
mypy 2.3.0 (compiled: yes)
Shell cwd was reset to ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1
[tool_use Bash] {"command": "/tmp/override_scan/venv/bin/ruff check tenacity tests; /tmp/override_scan/venv/bin/ruff format --check tenacity tests; /tmp/override_scan/venv/bin/mypy 2>&1 | tail -15; echo \"--- baseline mypy:\"; git stash list >/dev/null; git show HEAD:tenacity/_utils.py >/dev/null && echo ok"}
[tool_result] SIM105 Use `contextlib.suppress(AttributeError, TypeError)` instead of `try`-`except`-`pass`
  --> tenacity/_utils.py:34:9
   |
32 |       def override(method: _F) -> _F:
33 |           """Backport of PEP 698 ``typing.override`` for Python < 3.12."""
34 | /         try:
35 | |             method.__override__ = True  # type: ignore[attr-defined]
36 | |         except (AttributeError, TypeError):
37 | |             pass
   | |________________^
38 |           return method
   |
help: Replace `try`-
…[670 chars elided]…
xplicitly export attribute "override"  [attr-defined]
tenacity/asyncio/__init__.py:35: error: Module "tenacity._utils" does not explicitly export attribute "override"  [attr-defined]
tenacity/__init__.py:29: error: Module "tenacity._utils" does not explicitly export attribute "override"  [attr-defined]
tests/test_tenacity.py:31: error: Module "tenacity._utils" does not explicitly export attribute "override"  [attr-defined]
Found 8 errors in 8 files (checked 19 source files)
--- baseline mypy:
ok
[assistant] Ruff flags one `try`/`except`/`pass` (SIM105), and mypy strict doesn't re-export `override` from the 3.12 branch of `_utils`. I'll fix both: `contextlib.suppress` (already imported in `_utils`) and an explicit `as override` re-export.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/_utils.py", "old_string": "if sys.version_info >= (3, 12):\n    from typing import override\nelse:\n    _F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\n\n    def override(method: _F) -> _F:\n        \"\"\"Backport of PEP 698 
…[264 chars elided]…
n    from typing import override as override\nelse:\n    _F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\n\n    def override(method: _F) -> _F:\n        \"\"\"Backport of PEP 698 ``typing.override`` for Python < 3.12.\"\"\"\n        with contextlib.suppress(AttributeError, TypeError):\n            method.__override__ = True  # type: ignore[attr-defined]\n        return method"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-162837-refactor-mark-every-method-that/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "/tmp/override_scan/venv/bin/ruff check tenacity tests && /tmp/override_scan/venv/bin/ruff format --check tenacity tests && /tmp/override_scan/venv/bin/mypy 2>&1 | tail -5; <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2"}
[tool_result] All checks passed!
19 files already formatted
Success: no issues found in 19 source files
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.83s
[assistant] Ruff, format, mypy (strict) and pytest are all clean. The 3.12 env never runs the fallback branch, so I'll exec that branch with the version check forced to `False`, then confirm at runtime that every intended method carries the marker.
[tool_use Bash] {"command": "cat > /tmp/override_scan/verify.py <<'EOF'\nimport sys, types, importlib, pkgutil\nsys.path.insert(0, \".\")\n# 1. exec the pre-3.12 branch of _utils by forcing the version check false\nsrc = open(\"tenacity/_utils.py\").read().replace(\"sys.version_info >= (3, 12)\", \"False\")\nns = {\"__name__\": \"fallback_utils\"}\nexec(compile(src, \"fallback_utils\", \"exec\"), ns)\nfb = ns[\"o
…[919 chars elided]…
(marked))\nEOF\n<work>/env-tenacity/bin/python -I /tmp/override_scan/verify.py && <work>/env-tenacity/bin/python -I /tmp/override_scan/scan.py | wc -l"}
[tool_result] fallback ok: fallback_utils
real override from: typing
marked in tenacity: 56
      57
[assistant] The marker check finds 56 marked methods, but the scan found 57 sites. I need to find the missing one rather than assume.
[tool_use Bash] {"command": "cat >> /tmp/override_scan/verify.py <<'EOF'\nexpected = set()\nfor line in open(\"/tmp/override_scan/local.txt\"):\n    if line.strip():\n        mod, cls, name, *_ = [p.strip() for p in line.split(\"|\")]\n        expected.add(f\"{cls}.{name}\")\nprint(\"missing:\", sorted(expected - set(marked)))\nprint(\"extra:\", sorted(set(marked) - expected))\nEOF\n<work>/env-tenacity/bin/python -I /tmp/override_scan/verify.py | tail -2; grep -n \"Retrying.__call__\\|class TornadoRetrying\" /tmp/override_scan/local.txt"}
[tool_result] missing: ['Retrying.__call__']
extra: []
[assistant] The missing one is `Retrying.__call__` in `tenacity/__init__.py`. The apply step reported only one insertion for that file, so I'll look at the source.
[tool_use Bash] {"command": "grep -n -B2 -A3 \"^class Retrying\" tenacity/__init__.py; grep -n \"@override\" tenacity/__init__.py"}
[tool_result] 513-
514-
515:class Retrying(BaseRetrying):
516-    """Retrying controller."""
517-
518-    @override
518:    @override
[tool_use Bash] {"command": "sed -n 515,530p tenacity/__init__.py; grep -n \"__call__\\|__iter__\\|def wraps\\|def iter\" tenacity/__init__.py | head"}
[tool_result] class Retrying(BaseRetrying):
    """Retrying controller."""

    @override
    def __call__(
        self,
        fn: t.Callable[..., WrappedFnReturnT],
        *args: t.Any,
        **kwargs: t.Any,
    ) -> WrappedFnReturnT:
        self.begin()

        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)
        while True:
            do = self.iter(retry_state=retry_state)
            if isinstance(do, DoAttempt):
358:    def iter_state(self) -> IterState:
363:    def wraps(self, f: t.Callable[P, R]) -> "_RetryDecorated[P, R]":
418:    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
484:    def __iter__(self) -> t.Generator[AttemptManager, None, None]:
506:    def __call__(
519:    def __call__(
673:    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
694:    def __call__(
698:    def __call__(
702:    def __call__(
[assistant] The source is correct. The bug is in my verify script: `pkgutil.walk_packages` yields submodules only, so the top-level `tenacity` package (which holds `Retrying`) was never checked. I'll include it and rerun.
[tool_use Bash] {"command": "sed -i 's/^for m in pkgutil.walk_packages(tenacity.__path__, \"tenacity.\"):/for m in [types.SimpleNamespace(name=\"tenacity\")] + list(pkgutil.walk_packages(tenacity.__path__, \"tenacity.\")):/' /tmp/override_scan/verify.py && <work>/env-tenacity/bin/python -I /tmp/override_scan/verify.py"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/override_scan/veri ...": invalid command code o
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -I -c '\nimport sys, types, importlib, pkgutil\nsys.path.insert(0, \".\")\nimport tenacity\nmarked = []\nmods = [\"tenacity\"] + [m.name for m in pkgutil.walk_packages(tenacity.__path__, \"tenacity.\")]\nfor name in mods:\n    mod =
…[179 chars elided]…
tems():\n                if getattr(o, \"__override__\", False) is True:\n                    marked.append(f\"{cls.__qualname__}.{n}\")\nexpected = {f\"{p[1].strip()}.{p[2].strip()}\" for p in (l.split(\"|\") for l in open(\"/tmp/override_scan/local.txt\") if l.strip())}\nprint(\"marked:\", len(marked), \"missing:\", sorted(expected - set(marked)), \"extra:\", sorted(set(marked) - expected))\n'"}
[tool_result] marked: 57 missing: [] extra: []
[assistant] All 57 sites are marked, with no extras. A final look at the diff for the tricky spots: the `_utils` helper, the decorated tornado method, and the stacked asyncio decorator.
[tool_use Bash] {"command": "git diff --stat && git diff tenacity/_utils.py tenacity/tornadoweb.py && git diff tenacity/asyncio/retry.py | head -40 && git status --short"}
[tool_result]  tenacity/__init__.py         |  2 ++
 tenacity/_utils.py           | 11 +++++++++++
 tenacity/asyncio/__init__.py | 10 ++++++++++
 tenacity/asyncio/retry.py    | 12 ++++++++++++
 tenacity/retry.py            | 19 +++++++++++++++++++
 tenacity/stop.py             |  8 ++++++++
 tenacity/tornadoweb.py       |  3 +++
 tenacity/wait.py             | 11 +++++++++++
 tests/test_tenacity.py       |  2 ++
 9 files changed, 78 insertions(+)
diff --git a/tenacity/_utils.py b/tenacity/_utils.py
index 195f
…[2494 chars elided]…
_base | async_retry_base"
     ) -> "retry_all":
         return retry_all(other, self)
 
+    @override
     def __or__(  # type: ignore[override]
         self, other: "retry_base | async_retry_base"
     ) -> "retry_any":
         return retry_any(self, other)
 
+    @override
 M tenacity/__init__.py
 M tenacity/_utils.py
 M tenacity/asyncio/__init__.py
 M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tenacity/stop.py
 M tenacity/tornadoweb.py
 M tenacity/wait.py
 M tests/test_tenacity.py
[assistant] Every method that overrides a tenacity base-class method now carries `@override`, and `from tenacity._utils import override` works on Python 3.10+. Changes are uncommitted in the worktree.

**What changed**
- **`tenacity/_utils.py`**: `override` is `typing.override` on 3.12+. Below 3.12 it is a PEP 698 fallback that sets `__override__ = True` and returns the function. It tolerates objects that reject attribute assignment.
- **57 override sites** across `retry.py`, `wait.py`, `stop.py`, `__init__.py` (`Retrying`), `tornadoweb.py`, `asyncio/__init__.py` and `asyncio/retry.py`. Each file gets one
…[632 chars elided]…
you want them marked too, say so and I'll add them.

**Verification**
- Project tests: `173 passed, 1 skipped`.
- Ruff 0.16.1 and mypy 2.3.0 (the dev-group pins, installed in a scratch venv under `/tmp`): ruff check and format clean, mypy strict clean on 19 files.
- Runtime check: all 57 expected tenacity methods carry the marker, with no extras.
- The Python 3.10/3.11 fallback path is not run by the 3.12 env, and no interpreter below 3.12 is installed here. I exec'd that branch with the version check forced to false, and it returns the function and sets the marker.

I did not commit anything.
