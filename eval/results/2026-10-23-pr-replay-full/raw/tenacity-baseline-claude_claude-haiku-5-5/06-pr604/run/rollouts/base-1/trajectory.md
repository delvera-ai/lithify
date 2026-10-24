# trajectory base-1

final message:
`enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`. With `enabled=False` the function is called once, with no retry logic, and its exception propagates unchanged. The full suite passes: 151 passed, 1 skipped (trio is not installed here).

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` is added to `BaseRetrying`, which the sync and async classes share. `copy()` carries it through, so `retry_with(...)` keeps the setting. The `@retry` overloads and `Retrying.__call__` got the bypass.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying` accepts `enabled` and bypasses in `__call__`. It awaits the result only when the function is a coroutine.
- `tenacity/tornadoweb.py`: `TornadoRetrying` inherits the parameter, so I added the same bypass there. Without it, `enabled=False` would have been silently ignored on that class.
- Tests: `tests/test_enabled.py` is new and covers sync, async, and `retry_with`. I added `test_disabled` to `tests/test_tornado.py` and a `_failing_coroutine` helper. No existing tests were changed.
- Release note: `releasenotes/notes/add-enabled-parameter-3f9c1e2a7b5d4c60.yaml`.

**Choices I made**
- With `enabled=False`, `statistics` is not populated and `before`/`after`/`before_sleep` callbacks don't run. Callbacks and statistics are part of the retry machinery, so skipping them is consistent with "no retry logic".
- The bypass lives in each `__call__` rather than in `wraps()`, so direct `Retrying(...)(fn)` calls also honour it.

**Not run:** `mypy` and `ruff` aren't installed in the project's test environment, so the type-check and lint steps in the project config are unverified. Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"class Retrying\\|class AsyncRetrying\\|def retry\\b\\|def retry(\" --include=*.py . | grep -v test | head -20", "description": "Check status and locate retry classes"}
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
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "cat AGENTS.md | head -80; ls tenacity; grep -rn \"class Retrying\\|class AsyncRetrying\\|^def retry\" tenacity/*.py", "description": "Read agents notes and locate retry classes"}
[tool_result] <!-- lithify:begin — managed by `lithify sync`; edit .lithify/harness/ instead -->
## Project harness (lithify)

### Role and procedure

You are a careful engineer working in this repository. Make the smallest change that fully
satisfies the task, following the patterns the surrounding code already uses. Read the relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
-
…[266 chars elided]…
/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
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
tenacity/__init__.py:478:class Retrying(BaseRetrying):
tenacity/__init__.py:653:def retry(func: t.Callable[P, R]) -> _RetryDecorated[P, R]: ...
tenacity/__init__.py:657:def retry(
tenacity/__init__.py:674:def retry(
tenacity/__init__.py:690:def retry(*dargs: t.Any, **dkw: t.Any) -> t.Any:
[tool_use Bash] {"command": "cat tenacity/__init__.py", "description": "Read main tenacity module"}
[tool_result] # Copyright 2016-2018 Julien Danjou
# Copyright 2017 Elisey Zanko
# Copyright 2016 Étienne Bersac
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
# distributed under the License is distrib
…[24695 chars elided]…
ult",
    "retry_never",
    "retry_unless_exception_type",
    "sleep",
    "sleep_using_event",
    "stop_after_attempt",
    "stop_after_delay",
    "stop_all",
    "stop_any",
    "stop_before_delay",
    "stop_never",
    "stop_when_event_set",
    "wait_chain",
    "wait_combine",
    "wait_exception",
    "wait_exponential",
    "wait_exponential_jitter",
    "wait_fixed",
    "wait_full_jitter",
    "wait_incrementing",
    "wait_none",
    "wait_random",
    "wait_random_exponential",
]
[tool_use Bash] {"command": "cat tenacity/asyncio/__init__.py; ls tenacity/asyncio; ls releasenotes/notes | tail -3; cat tenacity/_utils.py | head -5", "description": "Read asyncio retry module and release notes"}
[tool_result] # Copyright 2016 Étienne Bersac
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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT
…[7067 chars elided]…
st("_RetryDecorated[P, R]", async_wrapped)


__all__ = [
    "AsyncRetrying",
    "WrappedFn",
    "retry_all",
    "retry_any",
    "retry_if_exception",
    "retry_if_result",
]
__init__.py
retry.py
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
[tool_use Bash] {"command": "cat tenacity/tornadoweb.py | sed -n 15,80p; cat releasenotes/notes/trio-support-retry-22bd544800cd1f36.yaml; ls doc; grep -rn \"reraise\" doc/*.rst | head; git log --oneline -3 -- releasenotes | head -3", "description": "Read tornado retry, release note format, docs"}
[tool_result] import sys
import typing

from tornado import gen

from tenacity import BaseRetrying, DoAttempt, DoSleep, RetryCallState

if typing.TYPE_CHECKING:
    from tornado.concurrent import Future

_RetValT = typing.TypeVar("_RetValT")


class TornadoRetrying(BaseRetrying):
    sleep: typing.Callable[..., "Future[None]"]

    def __init__(
        self,
        sleep: "typing.Callable[[float], Future[None]]" = gen.sleep,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(**kwargs)
   
…[915 chars elided]…
_attempt()
                yield self.sleep(do)
            else:
                raise gen.Return(do)
---
features:
  - |
    If you're using `Trio <https://trio.readthedocs.io>`__, then
    ``@retry`` now works automatically. It's no longer necessary to
    pass ``sleep=trio.sleep``.
source
(eval):1: no matches found: doc/*.rst
d4e868d Fix `retry()` annotations with async `sleep=` function (#555)
24415eb support async sleep for sync fn (#551)
3bf33b4 chore: drop Python 3.9 support (EOL) (#552)
[assistant] I have the picture: `BaseRetrying` holds the shared constructor and `copy()`, `Retrying.__call__` and `AsyncRetrying.__call__` hold the loops, and `retry()` forwards kwargs. I'll put `enabled` on `BaseRetrying` so `copy()` and `retry_with` carry it through, and add the bypass at the top of each call loop.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None = None,\n    ):\n        self.sleep = sleep\n        self.stop = stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        
…[375 chars elided]…
= stop\n        self.wait = wait\n        self.retry = retry\n        self.before = before\n        self.after = after\n        self.before_sleep = before_sleep\n        self.reraise = reraise\n        self._local = threading.local()\n        self.retry_error_cls = retry_error_cls\n        self.retry_error_callback = retry_error_callback\n        self._name = name\n        self.enabled = enabled"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        name: str | None | object = _unset,\n    ) -> \"Self\":\n        \"\"\"Copy this object with some parameters changed if needed.\"\"\"\n        return self.__class__(\n            sleep=_first_set(sleep, self.
…[1228 chars elided]…
 self.before_sleep),\n            reraise=_first_set(reraise, self.reraise),\n            retry_error_cls=_first_set(retry_error_cls, self.retry_error_cls),\n            retry_error_callback=_first_set(\n                retry_error_callback, self.retry_error_callback\n            ),\n            name=_first_set(name, self._name),\n            enabled=_first_set(enabled, self.enabled),\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "        self.begin()\n\n        retry_state = RetryCallState(retry_object=self, fn=fn, args=args, kwargs=kwargs)\n        while True:\n            do = self.iter(retry_state=retry_state)\n            if isinstance(do
…[900 chars elided]…
     except BaseException:\n                    retry_state.set_exception(sys.exc_info())  # type: ignore[arg-type]\n                else:\n                    retry_state.set_result(result)\n            elif isinstance(do, DoSleep):\n                retry_state.prepare_for_next_attempt()\n                self.sleep(do)\n            else:\n                return do  # type: ignore[no-any-return]"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n) -> _AsyncRetryDecorator: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = ...,\n    enabled: bool = ...,\n) -> _AsyncRetryDecorator: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py", "old_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ...", "new_string": "    retry_error_callback: t.Callable[[\"RetryCallState\"], t.Any | t.Awaitable[t.Any]]\n    | None = None,\n    enabled: bool = True,\n) -> t.Callable[[t.Callable[P, R]], _RetryDecorated[P, R]]: ..."}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/__init__.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Now the async class, and the Tornado subclass, which inherits the new kwarg and would otherwise accept `enabled=False` and silently ignore it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py", "old_string": "        name: str | None = None,\n    ) -> None:\n        super().__init__(\n            sleep=sleep,  # type: ignore[arg-type]\n            stop=stop,\n            wait=wait,\n            retry=retry,  # typ
…[1152 chars elided]…
ed,\n        )\n\n    async def __call__(  # type: ignore[override]\n        self, fn: WrappedFn, *args: t.Any, **kwargs: t.Any\n    ) -> WrappedFnReturnT:\n        if not self.enabled:\n            result = fn(*args, **kwargs)\n            if _utils.is_coroutine_callable(fn):\n                result = await result\n            return result  # type: ignore[no-any-return]\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py", "old_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        self.begin()", "new_string": "    ) -> \"typing.Generator[typing.Any, typing.Any, _RetValT]\":\n        if not self.enabled:\n            result = yield fn(*args, **kwargs)\n            raise gen.Return(result)\n\n        self.begin()"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tenacity/tornadoweb.py has been updated successfully.
[assistant] Now a release note (the repo uses reno) and tests. I'll check the test layout first.
[tool_use Bash] {"command": "ls tests; grep -n \"^def test_retry_with\\|^async def test_retry_with\" -A12 tests/test_tenacity.py | head -30; ls <work>/env-tenacity/bin/python", "description": "Inspect test layout and existing test style"}
[tool_result] __init__.py
test_after.py
test_asyncio.py
test_issue_478.py
test_tenacity.py
test_tornado.py
test_utils.py
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "sed -n 1,30p tests/test_asyncio.py | grep -n \"import\\|^$\" | head -20; grep -n \"def test_\" tests/test_asyncio.py | head -5", "description": "Check async test imports and style"}
[tool_result] 14:
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
22:
24:    import trio
29:
30:import pytest
81:    async def test_retry(self) -> None:
87:    async def test_iscoroutinefunction(self) -> None:
92:    async def test_retry_using_async_retying(self) -> None:
99:    async def test_stop_after_attempt(self) -> None:
106:    def test_repr(self) -> None:
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_enabled.py", "content": "import asyncio\n\nimport pytest\n\nfrom tenacity import AsyncRetrying, RetryError, Retrying, retry, stop_after_attempt\n\n\ndef test_disabled_sync_calls_once_and_propagates_exception() -> None:\n    calls = []\n\n    @retry(enabled=False, s
…[2701 chars elided]…
       fails.retry_with(stop=stop_after_attempt(5))()\n    assert len(calls) == 1\n\n\ndef test_retry_with_can_enable_retrying() -> None:\n    calls = []\n\n    @retry(enabled=False)\n    def fails() -> None:\n        calls.append(1)\n        raise ValueError\n\n    with pytest.raises(RetryError):\n        fails.retry_with(enabled=True, stop=stop_after_attempt(2))()\n    assert len(calls) == 2\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_enabled.py (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "cat > releasenotes/notes/add-enabled-parameter-3f9c1e2a7b5d4c60.yaml <<'EOF'\n---\nfeatures:\n  - |\n    ``Retrying``, ``AsyncRetrying`` and the ``@retry`` decorator accept a new\n    ``enabled`` parameter (default ``True``). When set to ``False``, the wrapped\n    function is called directly, exactly once, with no retry logic, and any\n    exception it raises propagates unchanged. This is useful during development\n    and testing.\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Add release note and run full test suite"}
[tool_result] ...........s........................................................................................................................ [ 87%]
...................                                                      [100%]
150 passed, 1 skipped, 12 subtests passed in 1.90s
[assistant] The suite passes. I'll check which test was skipped, and whether the project runs a linter or type checker, since the new overloads and bypass need to satisfy them too.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no -rs 2>&1 | grep SKIP; grep -n \"mypy\\|ruff\" pyproject.toml | head; ($PY -m mypy tenacity 2>&1 | tail -3); ($PY -m ruff check tenacity tests 2>&1 | tail -3); ($PY -m ruff format --check tenacity tests 2>&1 | tail -3)", "description": "Check skipped test and run type and lint checks"}
[tool_result] SKIPPED [1] tests/test_asyncio.py:165: trio not installed
59:    "ruff",
60:    "mypy",
72:mypy = "mypy"
77:    { cmd = "ruff check --fix ." },
78:    { cmd = "ruff format ." },
83:    { cmd = "ruff check ." },
84:    { cmd = "ruff format --check ." },
90:    { ref = "mypy" },
99:[tool.ruff]
105:[tool.ruff.lint]
<work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
[assistant] The full suite passes (the one skip is trio, which isn't installed). `mypy` and `ruff` aren't in the project env, so I'll check whether the Tornado bypass I added has any coverage, since nothing exercises it yet.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -c \"import tornado; print(tornado.version)\"; grep -n \"^import\\|^from\\|def test_\\|class \" tests/test_tornado.py | head -20", "description": "Check tornado availability and test style"}
[tool_result] 6.6
15:import unittest
16:from collections.abc import Generator
17:from typing import Any
19:from tornado import gen, testing
21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
23:from .test_tenacity import NoIOErrorAfterCount
42:class TestTornado(testing.AsyncTestCase):
44:    def test_retry(self) -> Generator[Any, Any, None]:
51:    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
59:    def test_repr(self) -> None:
62:    def test_old_tornado(self) -> None:
[tool_use Bash] {"command": "sed -n 40,60p tests/test_tornado.py", "description": "Read existing tornado test pattern"}
[tool_result] class TestTornado(testing.AsyncTestCase):
    @testing.gen_test
    def test_retry(self) -> Generator[Any, Any, None]:
        assert gen.is_coroutine_function(_retryable_coroutine)
        thing = NoIOErrorAfterCount(5)
        yield _retryable_coroutine(thing)
        assert thing.counter == thing.count

    @testing.gen_test
    def test_stop_after_attempt(self) -> Generator[Any, Any, None]:
        assert gen.is_coroutine_function(_retryable_coroutine)
        thing = NoIOErrorAfterCount(2)
        try:
            yield _retryable_coroutine_with_2_attempts(thing)
        except RetryError:
            assert thing.counter == 2

    def test_repr(self) -> None:
        repr(tornadoweb.TornadoRetrying())
[tool_use Bash] {"command": "cat >> tests/test_enabled.py <<'EOF'\n\n\ndef test_disabled_tornado_calls_once_and_propagates_exception() -> None:\n    from tornado import gen, testing\n\n    from tenacity import tornadoweb\n\n    class _Case(testing.AsyncTestCase):\n        @testing.gen_test\n        def test_disabled(self):  # type: ignore[no-untyped-def]\n            calls = []\n\n            @gen.coroutine\n    
…[427 chars elided]…
Up()\n    try:\n        case.test_disabled()\n    finally:\n        case.tearDown()\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_enabled.py 2>&1 | tail -15", "description": "Add tornado bypass test and run enabled tests"}
[tool_result] ............                                                             [100%]
12 passed in 0.03s
[assistant] The file changed on disk, but the new content is just my append, so nothing to undo. The Tornado test I appended is awkward, though: it drives a `testing.AsyncTestCase` by hand. The existing pattern lives in `TestTornado`, so I'll move it there.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY - <<'EOF'\nimport pathlib\np = pathlib.Path(\"tests/test_enabled.py\")\ns = p.read_text()\ni = s.index(\"\\n\\ndef test_disabled_tornado_calls_once\")\np.write_text(s[:i] + \"\\n\")\nEOF\ntail -3 tests/test_enabled.py", "description": "Remove tornado test block from new test file"}
[tool_result]         fails.retry_with(enabled=True, stop=stop_after_attempt(2))()
    assert len(calls) == 2
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())", "new_string": "    @testing.gen_test\n    def test_disabled(self) -> Generator[Any, Any, None]:\n        thing = NoIOErrorAfterCount(5)\n        r = tornadoweb.TornadoRetrying(enabled=False, stop=stop_after_attempt(3))\n        try:\n            yield r(_failing_coroutine, thing)\n        except OSError:\n            assert thing.counter == 1\n        else:\n            raise AssertionError(\"expected OSError to propagate\")\n\n    def test_repr(self) -> None:\n        repr(tornadoweb.TornadoRetrying())"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[assistant] I referenced a `_failing_coroutine` helper that doesn't exist yet. Let me check the existing helpers in that file before adding one.
[tool_use Bash] {"command": "sed -n 22,40p tests/test_tornado.py; grep -n \"class NoIOErrorAfterCount\" -A14 tests/test_tenacity.py", "description": "Read tornado test helpers and NoIOErrorAfterCount"}
[tool_result] from .test_tenacity import NoIOErrorAfterCount


@retry
@gen.coroutine
def _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()


@retry(stop=stop_after_attempt(2))
@gen.coroutine
def _retryable_coroutine_with_2_attempts(
    thing: NoIOErrorAfterCount,
) -> Generator[Any, Any, None]:
    yield gen.sleep(0.00001)
    thing.go()

839:class NoIOErrorAfterCount:
840-    """Holds counter state for invoking a method several times in a row."""
841-
842-    def __init__(self, count: int) -> None:
843-        self.counter = 0
844-        self.count = count
845-
846-    def go(self) -> typing.Any:
847-        """Raise an IOError until after count threshold has been crossed.
848-
849-        Then return True.
850-        """
851-        if self.counter < self.count:
852-            self.counter += 1
853-            raise OSError("Hi there, I'm an IOError")
[assistant] I'll add a plain (non-retrying) coroutine helper next to the existing ones. It mirrors `_retryable_coroutine` without the `@retry` decorator, so the test exercises the `TornadoRetrying` bypass path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py", "old_string": "@retry\n@gen.coroutine\ndef _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:\n    yield gen.sleep(0.00001)\n    thing.go()\n", "new_string": "@retry\n@gen.coroutine\ndef _retryable_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:\n    yield gen.sleep(0.00001)\n    thing.go()\n\n\n@gen.coroutine\ndef _failing_coroutine(thing: NoIOErrorAfterCount) -> Generator[Any, Any, None]:\n    yield gen.sleep(0.00001)\n    thing.go()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-190714-feature-add-an-enabled-parameter/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_tornado.py -k disabled -v 2>&1 | grep -i \"passed\\|failed\"; git status --short", "description": "Run full suite and show changed files"}
[tool_result] ...........s........................................................................................................................ [ 86%]
....................                                                     [100%]
151 passed, 1 skipped, 12 subtests passed in 1.79s
======================= 1 passed, 4 deselected in 0.02s ========================
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tenacity/tornadoweb.py
 M tests/test_tornado.py
?? releasenotes/notes/add-enabled-parameter-3f9c1e2a7b5d4c60.yaml
?? tests/test_enabled.py
[assistant] `enabled` is in place on `Retrying`, `AsyncRetrying`, and `@retry`. With `enabled=False` the function is called once, with no retry logic, and its exception propagates unchanged. The full suite passes: 151 passed, 1 skipped (trio is not installed here).

**What changed**
- `tenacity/__init__.py`: `enabled: bool = True` is added to `BaseRetrying`, which the sync and async classes share. `copy()` carries it through, so `retry_with(...)` keeps the setting. The `@retry` overloads and `Retrying.__call__` got the bypass.
- `tenacity/asyncio/__init__.py`: `AsyncRetrying` accepts `enabled` and bypasse
…[474 chars elided]…
releasenotes/notes/add-enabled-parameter-3f9c1e2a7b5d4c60.yaml`.

**Choices I made**
- With `enabled=False`, `statistics` is not populated and `before`/`after`/`before_sleep` callbacks don't run. Callbacks and statistics are part of the retry machinery, so skipping them is consistent with "no retry logic".
- The bypass lives in each `__call__` rather than in `wraps()`, so direct `Retrying(...)(fn)` calls also honour it.

**Not run:** `mypy` and `ruff` aren't installed in the project's test environment, so the type-check and lint steps in the project config are unverified. Nothing is committed.
