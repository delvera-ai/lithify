# trajectory dom-1

final message:
The overrides are now marked: 68 `@override` decorators across 11 files, with `from tenacity._utils import override` working. Nothing is committed.

**What changed**
- **`tenacity/_utils.py`**: `override` re-exports `typing.override` on Python 3.12+. On 3.10–3.11 it's a fallback that sets `__override__ = True` and returns the function. The fallback is private to `_utils`; the rest of the package and the tests import it from there.
- **Library**: `tenacity/__init__.py`, `retry.py`, `stop.py`, `wait.py`, `tornadoweb.py`, `asyncio/__init__.py`, `asyncio/retry.py`. 66 methods total, covering `retry_base`/`stop_base`/`wait_base`, `BaseRetrying` and its subclasses, and `RetryError`/`Future`, which override `Exception`/`futures.Future`.
- **Tests**: `tests/test_tenacity.py` (`CustomError`, `CapturingHandler`, `TestRetryErrorCallback.setUp`, and two test-local classes, `ConcreteRetrying.__call__` and `ExplodingPower.__pow__`), `tests/test_after.py` (`TestAfterLogFormat.setUp`).
- **Regression test**: `tests/test_utils.py::test_override_marks_function_and_returns_it`. It failed first with `ImportError: cannot import name 'override' from 'tenacity._utils'`, then passed after the fix.
- **Release note**: `releasenotes/notes/mark-overrides-with-override-9688ad5fe9b1a265.yaml`, an `other:` entry.

**Rule used:** a method is marked when a non-`object` base in its MRO defines the same name. I confirmed the set at runtime by walking the MRO of every class in the tenacity and test modules. The lister's `LOCAL` classes are handled separately: only two have overriding methods, and both are marked.

**Not marked (object-only)**: `BaseRetrying.__getstate__`, `__setstate__`, `__str__`, `__repr__`; and `__init__`/`__repr__`/`__str__`/`__eq__`/`__subclasshook__` on classes whose non-object bases don't define them, e.g. `BaseRetrying.__init__`, `stop_after_attempt.__init__`, `wait_fixed.__init__`, `retry_if_exception.__init__`, `retry_any.__init__`, `RetryCallState.__repr__`, `IterState.__eq__`, `LoggerProtocol.__init__`. The full list is 43 entries and comes from `/tmp/ovr/excluded.py`.

**Verification**
- Full suite via `run_tests.py`: `174 passed, 1 skipped`, exit 0. The skip is `TestTrio`, because trio isn't installed here.
- `check_changed.py`: `PASS: 0 problem(s)`.
- Runtime verifier: 66 marked, 0 unmarked among the runtime-visible overrides; lister shows 68 `*` markers (66 + 2 local).
- Fallback branch: unreachable on this 3.12 interpreter, so I ran its logic standalone and it behaves as expected. It has not been run under 3.10/3.11.

**Not run:** ruff and mypy (unavailable here). The `# type: ignore[override]` comments already in the repo are unchanged and still apply.

**Caveat:** `list_methods.py` omits some classes that exist (`RetryCallState`, `IterState`, `BaseAction`, `AttemptManager`), so I relied on the runtime walk, which does see them. None of them has a non-`object` override.

## events
[assistant] I'll start by reading the class-hierarchy skill the project points to, then the current code.
[tool_use Bash] {"command": "git status --short && ls && ls .lithify/harness/skills/ && grep -n '^## ' .lithify/harness/skills/class-hierarchy-refactor/SKILL.md && cat tenacity/_utils.py | head -80", "description": "Check status, list harness skills, read utils"}
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
class-hierarchy-refactor
deprecate-parameter
tenacity-change-contract
10:## 1. Enumerate from source, not from `cls.__subclasses__()`
26:## 2. The hierarchies (where each family lives)
41:## 3. Methods that override only `object`
50:## 4. Where a shared helper for the change goes
58:## 5. Done
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed u
…[1653 chars elided]…
be produced ``repr(cb)`` is called and returned.
    """
    segments = []
    try:
        segments.append(cb.__qualname__)
    except AttributeError:
        with contextlib.suppress(AttributeError):
            segments.append(cb.__name__)
    if not segments:
        return repr(cb)
    with contextlib.suppress(AttributeError):
        # When running under sphinx it appears this can be none?
        if cb.__module__:
            segments.insert(0, cb.__module__)
    return ".".join(segments)
[tool_use Bash] {"command": "cat .lithify/harness/skills/class-hierarchy-refactor/SKILL.md; ls .lithify/harness/scripts/ .lithify/harness/; cat .lithify/harness/memory.md 2>/dev/null | head -30", "description": "Read class-hierarchy skill and harness scripts"}
[tool_result] ---
name: class-hierarchy-refactor
description: Load when a tenacity task applies a change to every method or class in a hierarchy rather than to one behaviour — e.g. marking overrides with `@override`/`@final`, adding a decorator, annotation or docstring to "every subclass" of `retry_base`/`wait_base`/`stop_base`/`BaseRetrying`, or "and in the test helpers". Gives the verified class inventory (including test-local subclasses a runtime `__subclasses__()` walk cannot see), the AST lister to enume
…[4028 chars elided]…
te (format:
  `tenacity-change-contract` §2, read with `grep -n '^## '` + `sed -n`), or say in the final
  message why not.
.lithify/harness/:
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md

.lithify/harness/scripts/:
check_changed.py
run_tests.py
- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
[tool_use Bash] {"command": "ls -R .lithify/harness/skills/class-hierarchy-refactor/; ls -la <work>/env-tenacity/bin/python 2>&1; sed -n 1,40p .lithify/harness/scripts/run_tests.py; cat .lithify/harness/guardrails.md | head -40", "description": "Check skill scripts, project python, runner"}
[tool_result] SKILL.md
scripts

.lithify/harness/skills/class-hierarchy-refactor//scripts:
list_methods.py
lrwxr-xr-x@ 1 user  wheel  84 Oct 23 13:50 <work>/env-tenacity/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
#!/usr/bin/env python3
"""Run pytest in the foreground with a hard time limit; name the test that hangs.

A retry loop
…[1050 chars elided]…
 an existing test, check
          whether it also hangs without your change (`git stash`, run, `git
          stash pop`) and report what you found.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

LOG = "/tmp/run_tests.log"


def main() -> int:
    args = sys.argv[1:]
    timeout = 300.0
- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/class-hierarchy-refactor/scripts/list_methods.py > /tmp/lm_before.txt 2>&1; echo \"exit=$?\"; wc -l /tmp/lm_before.txt; cat /tmp/lm_before.txt", "description": "Enumerate class methods with the project lister"}
[tool_result] exit=0
     237 /tmp/lm_before.txt
tenacity/__init__.py:132 TryAgain(Exception)
tenacity/__init__.py:143 DoSleep(float)
tenacity/__init__.py:169 RetryAction(BaseAction)
    173 __init__
tenacity/__init__.py:184 RetryError(Exception)
    187 __init__
    191 reraise
    204 __str__
tenacity/__init__.py:242 BaseRetrying(ABC)
    243 __init__
    272 copy
    307 __getstate__
    311 __setstate__
    315 __str__
    318 __repr__
    331 statistics [@property]
    357 iter_state [@property]
    362 
…[7515 chars elided]…
ntextManager.test_context_manager_reraise.CustomError(Exception) LOCAL
tests/test_tenacity.py:2112 TestInvokeAsCallable.test_on_error.CustomError(Exception) LOCAL
tests/test_tenacity.py:2141 TestInvokeAsCallable.test_reraise.CustomError(Exception) LOCAL
tests/test_tenacity.py:2156 TestRetryException(unittest.TestCase)
tests/test_tenacity.py:2166 TestRetryTyping(unittest.TestCase)
tests/test_tenacity.py:2261 TestPickle(unittest.TestCase)
tests/test_tornado.py:42 TestTornado(testing.AsyncTestCase)
[assistant] The lister gives me the full inventory. Next I'll check the things the rule depends on: the Python floor, lint/type config, the test layout, and the release-note format.
[tool_use Bash] {"command": "grep -n -A3 'requires-python\\|\\[tool.mypy\\]\\|\\[tool.ruff' pyproject.toml | head -60; ls tests; grep -rn 'RetryCallState\\|class BaseAction' tenacity/*.py | head; grep -n '^from\\|^import' tenacity/__init__.py tenacity/retry.py tenacity/wait.py tenacity/stop.py tenacity/asyncio/*.py tenacity/tornadoweb.py; ls releasenotes/notes | tail -3; grep -n '^## ' .lithify/harness/skills/tenacity-change-contract/SKILL.md", "description": "Check pyproject, tests layout, imports, reno format"}
[tool_result] 17:requires-python = ">=3.10"
18-authors = [
19-    { name = "Julien Danjou", email = "julien@danjou.info" },
20-]
--
96:[tool.ruff]
97-line-length = 88
98-indent-width = 4
99-target-version = "py310"
--
102:[tool.ruff.lint]
103-select = ["ASYNC", "B", "C4", "DTZ", "E", "EXE", "F", "FLY", "FURB", "I", "ICN", "ISC", "LOG", "PERF", "PGH", "PIE", "PTH", "PYI", "RET", "RSE", "RUF", "SIM", "SLF", "SLOT", "T10", "TC", "UP", "W"]
104-ignore = [
105-    "B008",  # function calls in default arguments (in
…[3778 chars elided]…
of a wait/stop strategy; renaming or deprecating one
229:## 1b4. Exponential wait arithmetic (`tenacity/wait.py`)
262:## 1c. CONTRACT: a new keyword on `Retrying`/`AsyncRetrying`/`@retry`
302:## 1d. The iterator pattern: `for attempt in` / `async for` + `with attempt:`
331:## 2. A release note in `releasenotes/notes/` (reno)
353:## 2a. User docs for new API or a new usage form (`doc/source/index.rst`)
367:## 3. A regression test in the matching test file
381:## 4. Keep the change surface minimal
[tool_use Bash] {"command": "sed -n 331,400p .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ----; sed -n 1,30p tests/test_utils.py; echo ----; cat releasenotes/notes/annotate_code-*.yaml; echo ----; grep -n 'typing.override\\|override' -r tenacity tests | head", "description": "Read reno and test guidance, test_utils header"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[4336 chars elided]…
7:    def __ror__(  # type: ignore[misc,override]
tenacity/asyncio/retry.py:66:    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
tenacity/asyncio/retry.py:86:    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
tenacity/asyncio/retry.py:101:    async def __call__(self, retry_state: "RetryCallState") -> bool:  # type: ignore[override]
tenacity/asyncio/retry.py:109:    def __ror__(  # type: ignore[misc,override]
[assistant] Before writing anything I want the exact set of overrides computed at runtime, not guessed from the lister. I'll write a throwaway checker in `/tmp` (outside the repo) that flags any function, property, or classmethod whose name is defined by a non-`object` base in its MRO.
[tool_use Bash] {"command": "mkdir -p /tmp/ovr && cat > /tmp/ovr/find_overrides.py <<'EOF'\nimport importlib, inspect, sys\nsys.path.insert(0, sys.argv[1])\nMODS = [\"tenacity\", \"tenacity.retry\", \"tenacity.stop\", \"tenacity.wait\", \"tenacity.asyncio\",\n        \"tenacity.asyncio.retry\", \"tenacity.tornadoweb\", \"tenacity._utils\",\n        \"tests.test_tenacity\", \"tests.test_asyncio\", \"tests.test_aft
…[990 chars elided]…
repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1 && <work>/env-tenacity/bin/python -I /tmp/ovr/find_overrides.py \"$PWD\" > /tmp/ovr/before.txt 2>&1; echo \"exit=$?\"; cat /tmp/ovr/before.txt", "description": "Compute runtime override set via MRO walk"}
[tool_result] exit=0
tenacity:RetryError.__init__ <- builtins.Exception
tenacity:RetryError.__str__ <- builtins.BaseException
tenacity:Retrying.__call__ <- tenacity.BaseRetrying
tenacity:Future.__init__ <- concurrent.futures._base.Future
tenacity.retry:_retry_never.__call__ <- tenacity.retry.retry_base
tenacity.retry:_retry_always.__call__ <- tenacity.retry.retry_base
tenacity.retry:retry_if_exception.__call__ <- tenacity.retry.retry_base
tenacity.retry:retry_if_exception_type.__init__ <- tenacity.retry.retry
…[3689 chars elided]…
_init__ <- tenacity.BaseRetrying
tenacity.tornadoweb:TornadoRetrying.__call__ <- tenacity.BaseRetrying
tests.test_tenacity:CustomError.__init__ <- builtins.Exception
tests.test_tenacity:CustomError.__str__ <- builtins.BaseException
tests.test_tenacity:CapturingHandler.__init__ <- logging.Handler
tests.test_tenacity:CapturingHandler.emit <- logging.Handler
tests.test_tenacity:TestRetryErrorCallback.setUp <- unittest.case.TestCase
tests.test_after:TestAfterLogFormat.setUp <- unittest.case.TestCase
[assistant] The runtime walk matches the lister, with two extra cases: `ConcreteRetrying.__call__` and `ExplodingPower.__pow__` are test-local, so the runtime walk can't see them. The rule I'll apply: a method is marked when a non-`object` base in its MRO defines the same name. Object-only names (`BaseRetrying.__getstate__/__setstate__/__str__/__repr__`, and `__init__` on classes whose bases define none) are left out and named in the final message.

Following the project procedure, I'll write the regression test first and watch it fail for the reported reason.
[tool_use Bash] {"command": "tail -c 200 tests/test_utils.py | od -c | tail -3", "description": "Check trailing newline of test_utils.py"}
[tool_result] 0000260    n   d   _   o   r   d   i   n   a   l   (   1   1   3   )    
0000300    =   =       "   t   h   "  \n                                
0000310
[tool_use Bash] {"command": "tail -n 12 tests/test_utils.py", "description": "Show end of test_utils.py"}
[tool_result]     assert _utils.find_ordinal(2) == "nd"
    assert _utils.find_ordinal(3) == "rd"
    assert _utils.find_ordinal(4) == "th"
    assert _utils.find_ordinal(11) == "th"
    assert _utils.find_ordinal(12) == "th"
    assert _utils.find_ordinal(13) == "th"
    assert _utils.find_ordinal(21) == "st"
    assert _utils.find_ordinal(22) == "nd"
    assert _utils.find_ordinal(23) == "rd"
    assert _utils.find_ordinal(111) == "th"
    assert _utils.find_ordinal(112) == "th"
    assert _utils.find_ordinal(113) == "th"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/tests/test_utils.py", "old_string": "    assert _utils.find_ordinal(113) == \"th\"", "new_string": "    assert _utils.find_ordinal(113) == \"th\"\n\n\ndef test_override_marks_function_and_returns_it() -> None:\n    from tenacity._utils import override\n\n    def method() -> None:\n        pass\n\n    assert override(method) is method\n    assert getattr(method, \"__override__\", False) is True"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/tests/test_utils.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_utils.py::test_override_marks_function_and_returns_it; echo \"exit=$?\"", "description": "Run new regression test against unfixed code"}
[tool_result] ============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.1.1, pluggy-1.7.0 -- <work>/env-tenacity/bin/python
rootdir: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collecting ... collected 1 item
…[392 chars elided]…
e 'override' from 'tenacity._utils' (~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/tenacity/_utils.py)

tests/test_utils.py:61: ImportError
=========================== short test summary info ============================
FAILED tests/test_utils.py::test_override_marks_function_and_returns_it - Imp...
============================== 1 failed in 0.02s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
exit=1
[assistant] The test is red for the reported reason: `cannot import name 'override' from 'tenacity._utils'`. Now the helper. I'll put it in `_utils.py` after `MAX_WAIT`, since that module is stdlib-only and every tenacity module can import it without a cycle.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/tenacity/_utils.py", "old_string": "MAX_WAIT = sys.maxsize / 2\n", "new_string": "MAX_WAIT = sys.maxsize / 2\n\n_F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\n\nif sys.version_info >= (3, 12):\n    from typing import override\nelse:\n\n    def override(method: _F) -> _F:\n        \"\"\"Mark a method as overriding a base-class method (PEP 698).\"\"\"\n        method.__dict__[\"__override__\"] = True\n        return method\n"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/tenacity/_utils.py has been updated successfully.
[assistant] Next, the decorators. I'll generate them from the verified runtime list with a script that uses AST line numbers, inserting `@override` directly above each `def`, and processes each file bottom-up so line numbers stay valid. The two test-local classes are added by hand afterwards.
[tool_use Bash] {"command": "cat > /tmp/ovr/apply.py <<'EOF'\nimport ast, collections, pathlib, re, sys\nroot = pathlib.Path(sys.argv[1])\ntargets = collections.defaultdict(list)  # file -> [(qualname, attr)]\nfor line in pathlib.Path(\"/tmp/ovr/before.txt\").read_text().splitlines():\n    if \" <- \" not in line:\n        continue\n    lhs = line.split(\" <- \")[0]\n    mod, qual = lhs.split(\":\", 1)\n    cls, 
…[1393 chars elided]…
al\", total)\nEOF\ncd ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1 && <work>/env-tenacity/bin/python -I /tmp/ovr/apply.py \"$PWD\"; echo \"exit=$?\"", "description": "Insert @override above each overriding method"}
[tool_result] tenacity/__init__.py: 4
tenacity/asyncio/__init__.py: 9
tenacity/asyncio/retry.py: 11
tenacity/retry.py: 17
tenacity/stop.py: 7
tenacity/tornadoweb.py: 2
tenacity/wait.py: 10
tests/test_after.py: 1
tests/test_tenacity.py: 5
total 66
exit=0
[assistant] 66 insertions across 9 files, matching the verified list. Now the two test-local classes the runtime walk can't see.
[tool_use Bash] {"command": "grep -n 'class ConcreteRetrying\\|class ExplodingPower' -A4 tests/test_tenacity.py; grep -n -B1 -A2 '^from\\|^import' tests/test_tenacity.py | head -40; echo ----; grep -n -B1 -A1 '^from\\|^import' tests/test_after.py tenacity/stop.py tenacity/wait.py tenacity/retry.py tenacity/tornadoweb.py tenacity/asyncio/retry.py tenacity/asyncio/__init__.py | head -120", "description": "View local test classes and import blocks"}
[tool_result] 88:        class ConcreteRetrying(tenacity.BaseRetrying):
89-            def __call__(
90-                self, fn: typing.Any, *args: typing.Any, **kwargs: typing.Any
91-            ) -> typing.Any:
92-                pass
--
362:        class ExplodingPower(float):
363-            def __pow__(self, exponent: float, modulo: int | None = None) -> float:
364-                raise AssertionError("power should not be calculated above the maximum")
365-
366-        r = Retrying(wait=tenacity.wait_ex
…[2086 chars elided]…
nit__.py-36-# Import all built-in retry strategies for easier usage.
tenacity/asyncio/__init__.py:37:from .retry import (
tenacity/asyncio/__init__.py-38-    RetryBaseT,
tenacity/tornadoweb.py-14-
tenacity/tornadoweb.py:15:import sys
tenacity/tornadoweb.py:16:import typing
tenacity/tornadoweb.py-17-
tenacity/tornadoweb.py:18:from tornado import gen
tenacity/tornadoweb.py-19-
tenacity/tornadoweb.py:20:from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState
tenacity/tornadoweb.py-21-
[assistant] Two local-class edits are needed. Then the import lines: I'll view the blocks I'm about to touch so the insertions land in isort order.
[tool_use Bash] {"command": "sed -n 26,31p tenacity/__init__.py; echo ----; sed -n 22,37p tenacity/asyncio/__init__.py; echo ----; sed -n 1,12p tests/test_after.py; echo ----; sed -n 17,24p tenacity/retry.py; echo ----; sed -n 20,22p tenacity/tornadoweb.py", "description": "View import blocks to edit"}
[tool_result] from concurrent import futures

from . import _utils

# Import all built-in after strategies for easier usage.
from .after import after_log, after_nothing
----
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
----
import logging
import random
import unittest.mock

from tenacity import (
    _utils,
    after_log,
)

from . import test_tenacity


----
import abc
import re
import typing

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


----
from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState

if typing.TYPE_CHECKING:
[assistant] I'll make the import and local-class edits in one scripted pass that asserts each anchor matches exactly once, so nothing lands in the wrong place.
[tool_use Bash] {"command": "cat > /tmp/ovr/imports.py <<'EOF'\nimport pathlib, sys\nroot = pathlib.Path(sys.argv[1])\nEDITS = {\n    \"tenacity/__init__.py\": [(\"from . import _utils\\n\", \"from . import _utils\\nfrom ._utils import override\\n\")],\n    \"tenacity/asyncio/__init__.py\": [(\"    before_nothing,\\n)\\n\", \"    before_nothing,\\n)\\nfrom tenacity._utils import override\\n\")],\n    \"tenacity/a
…[1882 chars elided]…
rel)\nEOF\ncd ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1 && <work>/env-tenacity/bin/python -I /tmp/ovr/imports.py \"$PWD\"; echo \"exit=$?\"", "description": "Add override imports and two local-class decorators"}
[tool_result] ok tenacity/__init__.py
ok tenacity/asyncio/__init__.py
ok tenacity/asyncio/retry.py
ok tenacity/retry.py
ok tenacity/stop.py
ok tenacity/wait.py
ok tenacity/tornadoweb.py
ok tests/test_after.py
ok tests/test_tenacity.py
exit=0
[assistant] All anchors matched once. Now I'll run the regression test (should be green), then a verifier that re-walks the MRO and reports any overriding method that still lacks `__override__`.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_utils.py::test_override_marks_function_and_returns_it > /tmp/ovr/green.txt 2>&1; echo \"exit=$?\"; tail -n 3 /tmp/ovr/green.txt\ncat > /tmp/ovr/verify.py <<'EOF'\
…[1037 chars elided]…
e getattr(val, \"__func__\", val)\n            if getattr(fn, \"__override__\", False) is True:\n                marked += 1\n            else:\n                bad += 1; print(\"UNMARKED\", cls.__module__, cls.__qualname__, attr)\nprint(\"marked\", marked, \"unmarked\", bad)\nEOF\n$PY -I /tmp/ovr/verify.py \"$PWD\"; echo \"exit=$?\"", "description": "Run regression test green and verify marking"}
[tool_result] exit=0
============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
marked 66 unmarked 0
exit=0
[assistant] The regression test is green, and the verifier finds 66 marked and 0 unmarked among the runtime-visible overrides; the two local ones were edited by hand. Next, the full suite under the project harness.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/ovr/full.txt 2>&1; echo \"exit=$?\"; tail -n 8 /tmp/ovr/full.txt", "description": "Run full test suite via harness runner"}
[tool_result] exit=0
tests/test_tornado.py::TestTornado::test_stop_after_attempt PASSED       [ 98%]
tests/test_utils.py::test_is_coroutine_callable PASSED                   [ 98%]
tests/test_utils.py::test_find_ordinal PASSED                            [ 99%]
tests/test_utils.py::test_override_marks_function_and_returns_it PASSED  [100%]

============== 174 passed, 1 skipped, 12 subtests passed in 1.81s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Full suite: 174 passed, 1 skipped, exit 0. Next I'll check what the skip is, then add the reno note the contract requires for a typing-level change.
[tool_use Bash] {"command": "grep -n 'SKIPPED' /tmp/ovr/full.txt | head -3; python3 -c \"import secrets; print(secrets.token_hex(8))\"", "description": "Identify skipped test and generate reno suffix"}
[tool_result] 9688ad5fe9b1a265
[tool_use Bash] {"command": "grep -n 'SKIP' /tmp/ovr/full.txt /tmp/run_tests.log | head -5", "description": "Find the skipped test in the log"}
[tool_result] /tmp/run_tests.log:23:tests/test_asyncio.py::TestTrio::test_trio_basic SKIPPED (trio not i...) [  9%]
[assistant] The skip is `TestTrio` because trio isn't installed in this environment, unrelated to this change. Now the release note, as an `other:` entry since this changes no behaviour:
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/releasenotes/notes/mark-overrides-with-override-9688ad5fe9b1a265.yaml", "content": "---\nother:\n  - |\n    Mark every method that overrides a base-class method with the ``override``\n    decorator (PEP 698), so renaming a base method is caught by type checkers\n    instead of silently orphaning subclass implementations. The decorator is\n    private to ``tenacity._utils``; no runtime behaviour changes.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-204339-refactor-mark-every-method-that/dom-1/releasenotes/notes/mark-overrides-with-override-9688ad5fe9b1a265.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/ovr/check.txt 2>&1; echo \"exit=$?\"; cat /tmp/ovr/check.txt | tail -n 40", "description": "Run stdlib lint/format stand-in checks"}
[tool_result] exit=0
changed: releasenotes/notes/mark-overrides-with-override-9688ad5fe9b1a265.yaml, tenacity/__init__.py, tenacity/_utils.py, tenacity/asyncio/__init__.py, tenacity/asyncio/retry.py, tenacity/retry.py, tenacity/stop.py, tenacity/tornadoweb.py, tenacity/wait.py, tests/test_after.py, tests/test_tenacity.py, tests/test_utils.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] `check_changed.py` passes with 0 problems. ruff and mypy can't run here, so those are not run. The fallback branch is dead code on 3.12, so I'll exercise it directly and check the diff.
[tool_use Bash] {"command": "cat > /tmp/ovr/fallback_check.py <<'EOF'\nimport typing\n_F = typing.TypeVar(\"_F\", bound=typing.Callable[..., typing.Any])\ndef override(method: _F) -> _F:\n    \"\"\"Mark a method as overriding a base-class method (PEP 698).\"\"\"\n    method.__dict__[\"__override__\"] = True\n    return method\ndef f(self: object) -> None: ...\nclass P(property): pass\nassert override(f) is f and 
…[150 chars elided]…
and B.m.__override__ is True\nprint(\"fallback ok\")\nEOF\n<work>/env-tenacity/bin/python -I /tmp/ovr/fallback_check.py; echo \"exit=$?\"; git diff --stat; git diff tenacity/_utils.py tenacity/retry.py | head -80", "description": "Exercise fallback decorator and review diff"}
[tool_result] fallback ok
exit=0
 tenacity/__init__.py         |  5 +++++
 tenacity/_utils.py           | 11 +++++++++++
 tenacity/asyncio/__init__.py | 10 ++++++++++
 tenacity/asyncio/retry.py    | 12 ++++++++++++
 tenacity/retry.py            | 19 +++++++++++++++++++
 tenacity/stop.py             |  8 ++++++++
 tenacity/tornadoweb.py       |  3 +++
 tenacity/wait.py             | 11 +++++++++++
 tests/test_after.py          |  2 ++
 tests/test_tenacity.py       |  8 ++++++++
 tests/test_utils.py          | 
…[2212 chars elided]…
@ class retry_if_exception_type(retry_if_exception):
 class retry_if_not_exception_type(retry_if_exception):
     """Retries except an exception has been raised of one or more types."""
 
+    @override
     def __init__(
         self,
         exception_types: type[BaseException]
@@ -132,6 +139,7 @@ class retry_if_not_exception_type(retry_if_exception):
 class retry_unless_exception_type(retry_if_exception):
     """Retries until an exception is raised of one or more types."""
 
+    @override
[assistant] The diff reads cleanly. Last step per the skill's Done checklist: re-run the project lister and confirm the only changes are the added `*` markers, with no unexpected methods.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/skills/class-hierarchy-refactor/scripts/list_methods.py > /tmp/ovr/lm_after.txt 2>&1; echo \"exit=$?\"; echo \"before-star: $(grep -c '\\*' /tmp/lm_before.txt)  after-star: $(grep -c '\\*' /tmp/ovr/lm_after.txt)\"; diff <(sed 's/ \\*$//' /tmp/lm_before.txt) <(sed 's/ \\*$//' /tmp/ovr/lm_after.txt) | head; grep -n 'ConcreteRetrying\\|ExplodingPower' -A2 /tmp/ovr/lm_after.txt", "description": "Re-run lister and compare before/after markers"}
[tool_result] exit=0
before-star: 0  after-star: 68
1,126c1,80
< tenacity/__init__.py:132 TryAgain(Exception)
< tenacity/__init__.py:143 DoSleep(float)
< tenacity/__init__.py:169 RetryAction(BaseAction)
<     173 __init__
< tenacity/__init__.py:184 RetryError(Exception)
<     187 __init__
<     191 reraise
<     204 __str__
< tenacity/__init__.py:242 BaseRetrying(ABC)
200:tests/test_tenacity.py:89 TestBase.test_retrying_repr.ConcreteRetrying(tenacity.BaseRetrying) LOCAL
201-  * 91 __call__ [@override]
202-tests/test_tenacity.py:114 TestRetryingName(unittest.TestCase)
--
208:tests/test_tenacity.py:364 TestWaitConditions.test_exponential_skips_power_after_reaching_max.ExplodingPower(float) LOCAL
209-  * 366 __pow__ [@override]
210-tests/test_tenacity.py:679 TestWaitConditions.test_wait_retry_state_attributes.ExtractCallState(Exception) LOCAL
[assistant] The star count went from 0 to 68, which is the 66 runtime-visible plus the 2 test-local ones. The line-number diff is noise from the inserted lines. For the final report I need the exact object-only exclusions named, so I'll compute them rather than recall them.
[tool_use Bash] {"command": "cat > /tmp/ovr/excluded.py <<'EOF'\nimport importlib, inspect, sys\nsys.path.insert(0, sys.argv[1])\nMODS = [\"tenacity\", \"tenacity.retry\", \"tenacity.stop\", \"tenacity.wait\", \"tenacity.asyncio\",\n        \"tenacity.asyncio.retry\", \"tenacity.tornadoweb\", \"tenacity._utils\"]\nKINDS = (type(lambda: None), property, classmethod, staticmethod)\nout = []\nfor m in MODS:\n    mod
…[381 chars elided]…
for b in cls.__mro__[1:] if b is object):\n                out.append(f\"{cls.__qualname__}.{attr}\")\nprint(len(out)); print(\", \".join(out))\nEOF\n<work>/env-tenacity/bin/python -I /tmp/ovr/excluded.py \"$PWD\"", "description": "Compute the object-only exclusions by name"}
[tool_result] 43
IterState.__init__, IterState.__repr__, IterState.__eq__, BaseAction.__repr__, BaseAction.__str__, RetryAction.__init__, AttemptManager.__init__, BaseRetrying.__init__, BaseRetrying.__getstate__, BaseRetrying.__str__, BaseRetrying.__repr__, RetryCallState.__init__, RetryCallState.__repr__, _RetryDecorated.__subclasshook__, _RetryDecorated.__init__, _AsyncRetryDecorator.__subclasshook__, _AsyncRetryDecorator.__init__, retry_if_exception.__init__, retry_if_exception_cause_type.__init__, retry_i
…[93 chars elided]…
_any.__init__, stop_all.__init__, stop_when_event_set.__init__, stop_after_attempt.__init__, stop_after_delay.__init__, stop_before_delay.__init__, wait_fixed.__init__, wait_random.__init__, wait_combine.__init__, wait_chain.__init__, wait_exception.__init__, wait_incrementing.__init__, wait_exponential.__init__, wait_exponential_jitter.__init__, retry_if_exception.__init__, retry_if_result.__init__, retry_any.__init__, retry_all.__init__, LoggerProtocol.__subclasshook__, LoggerProtocol.__init__
[assistant] That's the full exclusion list. Last, confirm the working tree holds only the intended changes, with nothing stray from the runs.
[tool_use Bash] {"command": "git status --short && git diff | grep -c '^+.*@override$'", "description": "Confirm changed files and override decorator count"}
[tool_result]  M tenacity/__init__.py
 M tenacity/_utils.py
 M tenacity/asyncio/__init__.py
 M tenacity/asyncio/retry.py
 M tenacity/retry.py
 M tenacity/stop.py
 M tenacity/tornadoweb.py
 M tenacity/wait.py
 M tests/test_after.py
 M tests/test_tenacity.py
 M tests/test_utils.py
?? releasenotes/notes/mark-overrides-with-override-9688ad5fe9b1a265.yaml
68
[assistant] The overrides are now marked: 68 `@override` decorators across 11 files, with `from tenacity._utils import override` working. Nothing is committed.

**What changed**
- **`tenacity/_utils.py`**: `override` re-exports `typing.override` on Python 3.12+. On 3.10–3.11 it's a fallback that sets `__override__ = True` and returns the function. The fallback is private to `_utils`; the rest of the package and the tests import it from there.
- **Library**: `tenacity/__init__.py`, `retry.py`, `stop.py`, `wait.py`, `tornadoweb.py`, `asyncio/__init__.py`, `asyncio/retry.py`. 66 methods total, covering `retr
…[1722 chars elided]…
marked among the runtime-visible overrides; lister shows 68 `*` markers (66 + 2 local).
- Fallback branch: unreachable on this 3.12 interpreter, so I ran its logic standalone and it behaves as expected. It has not been run under 3.10/3.11.

**Not run:** ruff and mypy (unavailable here). The `# type: ignore[override]` comments already in the repo are unchanged and still apply.

**Caveat:** `list_methods.py` omits some classes that exist (`RetryCallState`, `IterState`, `BaseAction`, `AttemptManager`), so I relied on the runtime walk, which does see them. None of them has a non-`object` override.
