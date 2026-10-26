# trajectory base-1

final message:
The `@override` marking is done across the tenacity package and tests. The project's pytest suite passes (173 passed, 1 skipped), and mypy strict is clean on both Python 3.12 and 3.10. Changes are uncommitted in the worktree.

**What changed**

- **`tenacity/_utils.py`**: `override` is re-exported from `typing` on Python 3.12+. On older versions it's a fallback that sets `__override__ = True` and returns the function. `from tenacity._utils import override` works on every supported version.
- **66 decorators** added across `tenacity/__init__.py`, `retry.py`, `wait.py`, `stop.py`, `asyncio/__init__.py`, `asyncio/retry.py`, `tornadoweb.py`, `tests/test_tenacity.py` and `tests/test_after.py`. Each import of `override` sits in the module's existing import block.

**How the set was chosen**

I found overrides by introspecting the real class hierarchy: a method counts if any non-`object` base in its MRO defines the same name. That covers the `retry_base`, `wait_base`, `stop_base` and `BaseRetrying` subclasses, the async and tornado subclasses, and the test helpers.

Some decorated methods are not tenacity's own hierarchy, since the rule was "every method that overrides a base-class method":
- `__init__` and `__str__` on `RetryError` and the test `CustomError`, which override `Exception`/`BaseException`.
- `Future.__init__`, which overrides `concurrent.futures.Future`.
- `CapturingHandler.__init__` and `emit`, which override `logging.Handler`.
- `setUp` in `TestRetryErrorCallback` and `TestAfterLogFormat`, which override `unittest.TestCase`.

If you want only the tenacity-hierarchy overrides, those are the ones to drop.

**Verification**

- Every one of the 66 overrides carries `__override__`, checked by introspection.
- `ruff check` reports one `ICN001` in `tests/test_tenacity.py:17`. It also fires on `HEAD` (`ruff` 0.17.2 in a temp venv, not the pinned 0.16.1), so I left it alone.
- The fallback body was exercised on 3.12 by extracting that branch. No 3.10 or 3.11 interpreter is installed here, so the real fallback path hasn't run on those versions.

## events
[tool_use Bash] {"command": "git status --short && ls && cat pyproject.toml | head -80 && ls tenacity tests && cat tenacity/_utils.py", "description": "Inspect repo layout and utils module"}
[tool_use Bash] {"command": "grep -rn \"def \\|^class \" tenacity/*.py | grep -v \"^tenacity/_utils\" | wc -l; grep -rn \"^class \" tenacity/ tests/ | head -80", "description": "Check status and list classes"}
[tool_result]      196
tenacity/wait.py:29:class wait_base(abc.ABC):
tenacity/wait.py:51:class wait_fixed(wait_base):
tenacity/wait.py:61:class wait_none(wait_fixed):
tenacity/wait.py:68:class wait_random(wait_base):
tenacity/wait.py:83:class wait_combine(wait_base):
tenacity/wait.py:93:class wait_chain(wait_base):
tenacity/wait.py:120:class wait_exception(wait_base):
tenacity/wait.py:159:class wait_incrementing(wait_base):
tenacity/wait.py:181:class wait_exponential(wait_base):
tenacity/wait.py:226:class wai
…[3770 chars elided]…
4:class NoIOErrorAfterCount:
tests/test_tenacity.py:992:class NoNameErrorAfterCount:
tests/test_tenacity.py:1010:class NoNameErrorCauseAfterCount:
tests/test_tenacity.py:1035:class NoIOErrorCauseAfterCount:
tests/test_tenacity.py:1060:class NameErrorUntilCount:
tests/test_tenacity.py:1080:class IOErrorUntilCount:
tests/test_tenacity.py:1098:class CustomError(Exception):
tests/test_tenacity.py:1116:class NoCustomErrorAfterCount:
tests/test_tenacity.py:1136:class CapturingHandler(logging.Handler):
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
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "tenacity/_version.py"

[project]
name = "tenacity"
dynamic = ["version"]
description = "Retry code until it succeeds"
readme = "README.rst"
license = "Apache-2.0"
requires-python = ">=3.10"
authors = [
    { name = "Julien Danjou", em
…[4384 chars elided]…
l = isinstance(call, functools.partial) and call.func
    dunder_call = partial_call or getattr(call, "__call__", None)  # noqa: B004
    return inspect.iscoroutinefunction(dunder_call)


def wrap_to_async_func(
    call: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
    if is_coroutine_callable(call):
        return call

    async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return call(*args, **kwargs)

    return inner
[tool_use Bash] {"command": "sed -n 80,200p pyproject.toml; cat AGENTS.md | head -80; ls <work>/env-tenacity/bin/python 2>&1; which python3; python3 --version", "description": "Read rest of pyproject and agent notes"}
[tool_result]     { cmd = "ruff check ." },
    { cmd = "ruff format --check ." },
]

[tool.poe.tasks.all]
sequence = [
    { ref = "lint" },
    { ref = "mypy" },
    { ref = "check" },
]

[tool.pytest.ini_options]
filterwarnings = [
    "once::DeprecationWarning",
]

[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"
exclude = ["tenacity/_version.py"]

[tool.ruff.lint]
select = ["ASYNC", "B", "C4", "DTZ", "E", "EXE", "F", "FLY", "FURB", "I", "ICN", "ISC", "LOG", "PERF", "PGH", "PIE", "PT
…[1824 chars elided]…
elvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
<work>/env-tenacity/bin/python
<work>/env-tenacity/bin/python3
Python 3.12.13
[tool_use Bash] {"command": "cat > /tmp/find_overrides.py <<'EOF'\nimport importlib, inspect, pkgutil, sys, pathlib\nsys.path.insert(0, \".\")\nmods = [\"tenacity\", \"tenacity.asyncio\", \"tenacity.tornadoweb\", \"tenacity.retry\", \"tenacity.wait\", \"tenacity.stop\", \"tenacity.asyncio.retry\", \"tenacity.before\", \"tenacity.after\", \"tenacity.before_sleep\", \"tenacity.nap\"]\nnames = [m for m in mods]\nfor
…[1085 chars elided]…
 vars(base):\n                    print(f\"{cls.__module__}.{cname}.{attr}  <- {base.__module__}.{base.__qualname__}\")\n                    break\nEOF\n<work>/env-tenacity/bin/python -I /tmp/find_overrides.py", "description": "Introspect classes for overridden base methods"}
[tool_result] tenacity.RetryError.__init__  <- builtins.Exception
tenacity.RetryError.__str__  <- builtins.BaseException
tenacity.Retrying.__call__  <- tenacity.BaseRetrying
tenacity.Future.__init__  <- concurrent.futures._base.Future
tenacity.asyncio.AsyncRetrying.__init__  <- tenacity.BaseRetrying
tenacity.asyncio.AsyncRetrying.__call__  <- tenacity.BaseRetrying
tenacity.asyncio.AsyncRetrying._add_action_func  <- tenacity.BaseRetrying
tenacity.asyncio.AsyncRetrying._run_retry  <- tenacity.BaseRetrying
tenac
…[3748 chars elided]…
retry_base
tenacity.asyncio.retry.retry_all.__rand__  <- tenacity.asyncio.retry.async_retry_base
tests.test_tenacity.CustomError.__init__  <- builtins.Exception
tests.test_tenacity.CustomError.__str__  <- builtins.BaseException
tests.test_tenacity.CapturingHandler.__init__  <- logging.Handler
tests.test_tenacity.CapturingHandler.emit  <- logging.Handler
tests.test_tenacity.TestRetryErrorCallback.setUp  <- unittest.case.TestCase
tests.test_after.TestAfterLogFormat.setUp  <- unittest.case.TestCase
[tool_use Bash] {"command": "grep -rnE \"^\\s+class |^\\s+def (setUp|tearDown|get_new_ioloop|run|__call__|__init__)\\b\" tenacity tests | grep -v \"^tests/test_tenacity.py:.*    def test_\" | head -60; grep -rn \"from tenacity._utils\\|_utils import\" tenacity tests | head", "description": "Find nested classes and common overridable methods"}
[tool_result] tenacity/wait.py:33:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:54:    def __init__(self, wait: _utils.time_unit_type) -> None:
tenacity/wait.py:57:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:64:    def __init__(self) -> None:
tenacity/wait.py:71:    def __init__(
tenacity/wait.py:77:    def __call__(self, retry_state: "RetryCallState") -> float:
tenacity/wait.py:86:    def __init__(self, *strategies: wait_base) -> None:
t
…[3352 chars elided]…
(
tenacity/retry.py:146:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/retry.py:167:    def __init__(
tenacity/retry.py:174:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/retry.py:196:    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
tenacity/retry.py:199:    def __call__(self, retry_state: "RetryCallState") -> bool:
tenacity/retry.py:211:    def __init__(self, predicate: typing.Callable[[typing.Any], bool]) -> None:
[tool_use Bash] {"command": "for f in tenacity/__init__.py tenacity/retry.py tenacity/wait.py tenacity/stop.py tenacity/asyncio/__init__.py tenacity/asyncio/retry.py tenacity/tornadoweb.py tests/test_tenacity.py tests/test_after.py; do echo \"== $f\"; grep -n \"^import\\|^from\\|^if \\|^    from\\|^    import\" $f; done; sed -n 495,530p tenacity/__init__.py", "description": "Check import styles and overloaded __call__"}
[tool_result] == tenacity/__init__.py
18:import dataclasses
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
43:from .retry import (
61:from .stop
…[2798 chars elided]…
rying(BaseRetrying):
    """Retrying controller."""

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
                try:
                    result = fn(*args, **kwargs)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/_utils.py", "old_string": "MAX_WAIT = sys.maxsize / 2\n\n", "new_string": "MAX_WAIT = sys.maxsize / 2\n\nif sys.version_info >= (3, 12):\n    from typing import override as override\nelse:\n    _F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\n\n    def override(method: _F) -> _F:\n        \"\"\"Fallback for ``typing.override`` (PEP 698) on Python < 3.12.\"\"\"\n        method.__override__ = True  # type: ignore[attr-defined]\n        return method\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/_utils.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin; ls $P | tr '\\n' ' '; echo; for t in ruff mypy; do $P/$t --version 2>&1 | head -1; done", "description": "Check which lint tools exist in test env"}
[tool_result] activate activate.bat activate.csh activate.fish activate.nu activate.ps1 activate_this.py deactivate.bat py.test pydoc.bat pygmentize pytest python python3 python3.12 
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
[tool_use Bash] {"command": "which ruff mypy uvx pipx 2>&1; cd ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1 && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Locate ruff/mypy and run baseline tests"}
[tool_result] ruff not found
mypy not found
uvx not found
pipx not found
...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.87s
[tool_use Bash] {"command": "cat > /tmp/apply_override.py <<'EOF'\nimport ast, importlib, inspect, pathlib, sys\nsys.path.insert(0, \".\")\n\ntargets = []  # (file, class, method)\nnames = [\"tenacity\", \"tenacity.asyncio\", \"tenacity.tornadoweb\", \"tenacity.retry\", \"tenacity.wait\",\n         \"tenacity.stop\", \"tenacity.asyncio.retry\", \"tenacity.before\", \"tenacity.after\",\n         \"tenacity.before_
…[1792 chars elided]…
e: after last top-level import statement\n    last_import = max(n.end_lineno for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)))\n    lines.insert(last_import, \"\\nfrom tenacity._utils import override\\n\" if False else \"\")\n    pathlib.Path(f).write_text(\"\".join(lines))\n    print(f, len(items))\nEOF\necho written", "description": "Write script to insert @override decorators"}
[tool_result] written
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np=\"/tmp/apply_override.py\"\ns=open(p).read()\ns=s.replace('''    # import line: after last top-level import statement\n    last_import = max(n.end_lineno for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)))\n    lines.insert(last_import, \"\\\\nfrom tenacity._utils import override\\\\n\" if False else \"\")\n''','')\nopen(p,\"w\").write(s)\nEOF\ngrep -n \"last_import\" /tmp/apply_override.py; <work>/env-tenacity/bin/python -I /tmp/apply_override.py && git diff --stat", "description": "Apply @override decorators across files"}
[tool_result] tenacity/__init__.py 4
tenacity/asyncio/__init__.py 9
tenacity/asyncio/retry.py 11
tenacity/retry.py 17
tenacity/stop.py 7
tenacity/tornadoweb.py 2
tenacity/wait.py 10
tests/test_after.py 1
tests/test_tenacity.py 5
 tenacity/__init__.py         |  4 ++++
 tenacity/_utils.py           | 10 ++++++++++
 tenacity/asyncio/__init__.py |  9 +++++++++
 tenacity/asyncio/retry.py    | 11 +++++++++++
 tenacity/retry.py            | 17 +++++++++++++++++
 tenacity/stop.py             |  7 +++++++
 tenacity/tornadoweb.py       |  2 ++
 tenacity/wait.py             | 10 ++++++++++
 tests/test_after.py          |  1 +
 tests/test_tenacity.py       |  5 +++++
 10 files changed, 76 insertions(+)
[tool_use Bash] {"command": "sed -n 15,50p tenacity/__init__.py; echo ====; sed -n 15,45p tenacity/asyncio/__init__.py; echo ====; sed -n 14,25p tenacity/asyncio/retry.py; echo ====; sed -n 14,25p tenacity/retry.py; echo ====; sed -n 14,30p tenacity/stop.py; echo ====; sed -n 14,24p tenacity/tornadoweb.py; echo ====; sed -n 14,30p tenacity/wait.py; echo ====; sed -n 1,12p tests/test_after.py; echo ====; sed -n 14,35p tests/test_tenacity.py", "description": "Read import blocks of modified files"}
[tool_result ERROR] Exit code 1
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import dataclasses
import functools
import sys
import threading
import time
import typing as t
import warnings
from abc import ABC, abstractmethod
from concurrent import futures

from . import _utils

# Import all built-in after strategies for easier usage.
from .after import after_log, after_nothing

# Impor
…[74 chars elided]…
ore_log, before_nothing

# Import all built-in before sleep strategies for easier usage.
from .before_sleep import before_sleep_log, before_sleep_nothing

# Import all nap strategies for easier usage.
from .nap import sleep, sleep_using_event

# Import all built-in retry strategies for easier usage.
from .retry import (
    retry_all,
    retry_always,
    retry_any,
    retry_base,
    retry_if_exception,
    retry_if_exception_cause_type,
    retry_if_exception_message,
(eval):1: === not found
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py", "offset": 18, "limit": 22}
[tool_result] 18	import functools
19	import sys
20	import typing as t
21	
22	import tenacity
23	from tenacity import (
24	    AttemptManager,
25	    BaseRetrying,
26	    DoAttempt,
27	    DoSleep,
28	    RetryCallState,
29	    RetryError,
30	    _RetryDecorated,
31	    _utils,
32	    after_nothing,
33	    before_nothing,
34	)
35	
36	# Import all built-in retry strategies for easier usage.
37	from .retry import (
38	    RetryBaseT,
39	    retry_all,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tests/test_after.py", "limit": 12}
[tool_result] 1	import logging
2	import random
3	import unittest.mock
4	
5	from tenacity import (
6	    _utils,
7	    after_log,
8	)
9	
10	from . import test_tenacity
11	
12	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/__init__.py", "old_string": "from concurrent import futures\n\nfrom . import _utils", "new_string": "from concurrent import futures\n\nfrom tenacity._utils import override\n\nfrom . import _utils"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py", "old_string": "    before_nothing,\n)\n\n# Import all built-in retry strategies for easier usage.", "new_string": "    before_nothing,\n)\nfrom tenacity._utils import override\n\n# Import all built-in retry strategies for easier usage."}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/asyncio/retry.py", "old_string": "from tenacity import _utils, retry_base\n", "new_string": "from tenacity import _utils, retry_base\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/asyncio/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/retry.py", "old_string": "import typing\n\nif typing.TYPE_CHECKING:", "new_string": "import typing\n\nfrom tenacity._utils import override\n\nif typing.TYPE_CHECKING:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/retry.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/stop.py", "old_string": "from tenacity import _utils\n", "new_string": "from tenacity import _utils\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/stop.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/wait.py", "old_string": "from tenacity import _utils\n", "new_string": "from tenacity import _utils\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/tornadoweb.py", "old_string": "from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState\n", "new_string": "from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tenacity/tornadoweb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tests/test_after.py", "old_string": "from tenacity import (\n    _utils,\n    after_log,\n)\n", "new_string": "from tenacity import (\n    _utils,\n    after_log,\n)\nfrom tenacity._utils import override\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tests/test_after.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tests/test_tenacity.py", "old_string": "from tenacity import RetryCallState, RetryError, Retrying, retry\nfrom tenacity.retry import retry_all, retry_any\n", "new_string": "from tenacity import RetryCallState, RetryError, Retrying, retry\nfrom tenacity._utils import override\nfrom tenacity.retry import retry_all, retry_any\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-tenacity/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $P -I -c '\nimport sys, importlib, inspect, pathlib; sys.path.insert(0, \".\")\nimport tenacity._utils as u; print(\"override from:\", u.override.__module__)\nbad = [
…[423 chars elided]…
y(attr in vars(b) for b in cls.__mro__[1:] if b is not object):\n                n += 1\n                f = val.fget if isinstance(val, property) else getattr(val, \"__func__\", val)\n                if not getattr(f, \"__override__\", False): bad.append((cname, attr))\nprint(\"overrides checked:\", n, \"undecorated:\", bad)\n'", "description": "Run test suite and verify all overrides decorated"}
[tool_result] ...............s.................................................................................................................... [ 75%]
..........................................                               [100%]
173 passed, 1 skipped, 12 subtests passed in 1.88s
override from: typing
overrides checked: 66 undecorated: []
[tool_use Bash] {"command": "ls /usr/bin/python3* /opt/homebrew/bin/python3* /usr/local/bin/python3* 2>/dev/null; for v in 3.10 3.11; do command -v python$v; done; cd ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1 && python3 -c '\nimport ast,sys\nsrc=open(\"tenacity/_utils.py\").read()\n# compile the fallback branch as if on py3.10 by extracting it\ntree=ast.parse(src)\nifnode=[n for n in tree.body if isinstance(n,ast.If)][0]\nmod=ast.Module(body=ifnode.orelse,type_ignores=[])\nns={\"typing\":__import__(\"typing\")}\nexec(compile(mod,\"fallback\",\"exec\"),ns)\ndef f(x): return x\ng=ns[\"override\"](f); print(g is f, f.__override__)\n'", "description": "Look for older Pythons and exercise fallback branch"}
[tool_result] /opt/homebrew/bin/python3
/opt/homebrew/bin/python3-config
/opt/homebrew/bin/python3.14
/opt/homebrew/bin/python3.14-config
/usr/bin/python3
/usr/local/bin/python3
/usr/local/bin/python3-config
/usr/local/bin/python3-intel64
/usr/local/bin/python3.13
/usr/local/bin/python3.13-config
/usr/local/bin/python3.13-intel64
/usr/local/bin/python3.13t
/usr/local/bin/python3.13t-config
/usr/local/bin/python3.13t-intel64
/usr/local/bin/python3t
/usr/local/bin/python3t-config
/usr/local/bin/python3t-intel64
True True
[tool_use Bash] {"command": "git diff -U1 -- tenacity/retry.py tenacity/__init__.py tenacity/asyncio/__init__.py | head -150", "description": "Review diff for representative files"}
[tool_result] diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index e993396..a90e8f4 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -27,2 +27,4 @@ from concurrent import futures
 
+from tenacity._utils import override
+
 from . import _utils
@@ -186,2 +188,3 @@ class RetryError(Exception):
 
+    @override
     def __init__(self, last_attempt: "Future") -> None:
@@ -203,2 +206,3 @@ class RetryError(Exception):
 
+    @override
     def __str__(self) -> str:
@@ -516,2 +520,3 @@ class 
…[3800 chars elided]…
93,3 @@ class retry_any(retry_base):
 
+    @override
     def __call__(self, retry_state: "RetryCallState") -> bool:
@@ -281,2 +297,3 @@ class retry_any(retry_base):
 
+    @override
     def __ror__(self, other: "RetryBaseT") -> "retry_any":
@@ -293,2 +310,3 @@ class retry_all(retry_base):
 
+    @override
     def __call__(self, retry_state: "RetryCallState") -> bool:
@@ -296,2 +314,3 @@ class retry_all(retry_base):
 
+    @override
     def __rand__(self, other: "RetryBaseT") -> "retry_all":
[tool_use Bash] {"command": "cd /tmp && python3 -m venv /tmp/lint-venv >/dev/null 2>&1 && timeout 120 /tmp/lint-venv/bin/pip install -q ruff==0.16.1 mypy==2.3.0 2>&1 | tail -2; ls /tmp/lint-venv/bin | grep -E \"^(ruff|mypy)$\"", "description": "Try installing pinned ruff and mypy in temp venv"}
[tool_result] (eval):1: command not found: timeout
mypy
ruff
Shell cwd was reset to ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1
[tool_use Bash] {"command": "L=/tmp/lint-venv/bin; $L/ruff --version; $L/ruff check . 2>&1 | tail -15; $L/ruff format --check . 2>&1 | tail -5; git stash list >/dev/null; echo \"--- mypy\"; $L/mypy 2>&1 | tail -15", "description": "Run ruff check, format check, and mypy"}
[tool_result] ruff 0.17.2
--------------------------------------------------------------------------------
310 |             (1, 20),
    -             (datetime.timedelta(seconds=1), datetime.timedelta(seconds=20)),
311 +             (dt.timedelta(seconds=1), dt.timedelta(seconds=20)),
312 |         ):
--------------------------------------------------------------------------------
412 |             (10, 100),
    -             (datetime.timedelta(seconds=10), datetime.timedelta(seconds=100)),
413 +         
…[1402 chars elided]…
3: error: Untyped decorator makes function "test_retry" untyped  [untyped-decorator]
tests/test_tornado.py:50: error: Untyped decorator makes function "test_stop_after_attempt" untyped  [untyped-decorator]
tests/test_asyncio.py:24: error: Cannot find implementation or library stub for module named "trio"  [import-not-found]
tests/test_asyncio.py:30: error: Cannot find implementation or library stub for module named "pytest"  [import-not-found]
Found 23 errors in 6 files (checked 19 source files)
[tool_use Bash] {"command": "/tmp/lint-venv/bin/ruff check . --output-format concise 2>&1 | head -3; rm -rf /tmp/base-head && mkdir /tmp/base-head && git archive HEAD | tar -x -C /tmp/base-head && cd /tmp/base-head && /tmp/lint-venv/bin/ruff check . --output-format concise 2>&1 | head -3; /tmp/lint-venv/bin/pip install -q pytest tornado trio 2>&1 | tail -1; cd ~/.cache/lithify/work/repo-b58808c83cd1/20261023-165101-refactor-mark-every-method-that/base-1 && /tmp/lint-venv/bin/mypy 2>&1 | tail -3", "description": "Compare ruff result against HEAD and install mypy deps"}
[tool_result] tests/test_tenacity.py:17:8: ICN001 `datetime` should be imported as `dt`
Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
tests/test_tenacity.py:17:8: ICN001 `datetime` should be imported as `dt`
Found 1 error.
1 unsafe fix available with `--fix --unsafe-fixes`.
[notice] To update, run: python3.12 -m pip install --upgrade pip
Success: no issues found in 19 source files
[tool_use Bash] {"command": "/tmp/lint-venv/bin/mypy --python-version 3.10 2>&1 | tail -3; /tmp/lint-venv/bin/mypy --python-version 3.10 tenacity/_utils.py 2>&1 | tail -2; git status --short; rm -rf /tmp/base-head /tmp/find_overrides.py /tmp/apply_override.py", "description": "Type-check against Python 3.10 branch and clean up"}
[tool_result] Success: no issues found in 19 source files
Success: no issues found in 1 source file
 M tenacity/__init__.py
 M tenacity/_utils.py
 M tenacity/asyncio/__init__.py
 M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tenacity/stop.py
 M tenacity/tornadoweb.py
 M tenacity/wait.py
 M tests/test_after.py
 M tests/test_tenacity.py
[assistant] The `@override` marking is done across the tenacity package and tests. The project's pytest suite passes (173 passed, 1 skipped), and mypy strict is clean on both Python 3.12 and 3.10. Changes are uncommitted in the worktree.

**What changed**

- **`tenacity/_utils.py`**: `override` is re-exported from `typing` on Python 3.12+. On older versions it's a fallback that sets `__override__ = True` and returns the function. `from tenacity._utils import override` works on every supported version.
- **66 decorators** added across `tenacity/__init__.py`, `retry.py`, `wait.py`, `stop.py`, `asyncio/__ini
…[879 chars elided]…
etryErrorCallback` and `TestAfterLogFormat`, which override `unittest.TestCase`.

If you want only the tenacity-hierarchy overrides, those are the ones to drop.

**Verification**

- Every one of the 66 overrides carries `__override__`, checked by introspection.
- `ruff check` reports one `ICN001` in `tests/test_tenacity.py:17`. It also fires on `HEAD` (`ruff` 0.17.2 in a temp venv, not the pinned 0.16.1), so I left it alone.
- The fallback body was exercised on 3.12 by extracting that branch. No 3.10 or 3.11 interpreter is installed here, so the real fallback path hasn't run on those versions.
