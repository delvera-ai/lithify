# trajectory base-1

final message:
Callable wait strategies are now always called, in both the sync and async retry loops. The full suite passes (185 passed, 1 skipped), and the new regression tests fail on the original code.

**Cause:** `_run_wait` in `tenacity/__init__.py` and `AsyncRetrying._run_wait` in `tenacity/asyncio/__init__.py` both guarded with `if not self.wait:`. That treated any falsy strategy as "no wait", so a callable with `__bool__` or `__len__` returning 0 was never called and retries ran with no delay.

**Fix:** both guards are now `if not callable(self.wait) and not self.wait:`. Callables are always invoked. The non-callable no-wait values (`None`, `0`, `sum([])`) still skip the call, as before.

**Tests added:**
- `tests/test_tenacity.py`: `test_wait_falsy_callable_is_still_called`, covering a `__bool__`-False object and a `__len__`-0 container.
- `tests/test_asyncio.py`: `test_wait_falsy_callable_is_still_called` for `AsyncRetrying`.

**Release note:** `releasenotes/notes/fix-falsy-callable-wait-5c2e8d1f7a9b4e63.yaml`, in the repo's reno format.

I did not run mypy or ruff because neither is installed in the project's test environment. The two `# type: ignore[truthy-bool]` comments were kept, so the type checker behaviour is unverified. Nothing is committed.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -rn \"wait\" --include=*.py -l . | grep -v \"/\\.git/\" | head -50", "description": "Check repo state and find wait-related files"}
[tool_result] 277f17a lithify: probe base
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git ls-files | grep -v \"^\\.git\" | head -200 && echo --- && grep -rn \"wait\" $(git ls-files | grep \"\\.py$\") | head -80", "description": "List tracked files and grep for wait references"}
[tool_result] .editorconfig
.lithify/harness/guardrails.md
.lithify/harness/memory.md
.lithify/harness/system.md
.lithify/harness/tool_guidance.md
.lithify/library/INDEX.md
.lithify/state.json
.mergify.yml
.readthedocs.yml
AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc/source/api.rst
doc/source/changelog.rst
doc/source/conf.py
doc/source/index.rst
pyproject.toml
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/Use--for-formatting-and-validate-using-black-39ec9d57d4691778.yam
…[9729 chars elided]…
n await fn(*args, **kwargs)  # type: ignore[misc]
tenacity/asyncio/__init__.py:237:            return await copy(fn, *args, **kwargs)  # type: ignore[type-var]
tenacity/nap.py:35:    """Sleep strategy that waits on an event to be set."""
tenacity/nap.py:41:        # NOTE(harlowja): this may *not* actually wait for timeout
tenacity/nap.py:43:        self.event.wait(timeout=timeout)
tenacity/wait.py:30:class wait_base(abc.ABC):
tenacity/wait.py:31:    """Abstract base class for wait strategies."""
[tool_use Bash] {"command": "sed -n 412,435p tenacity/__init__.py && echo ---ASYNC--- && sed -n 150,166p tenacity/asyncio/__init__.py && echo --- && cat tenacity/releasenotes 2>/dev/null; cat releasenotes/notes/fix-falsy-wait-regression-3b7e91c4a5d20f68.yaml releasenotes/notes/fix-wait-chain-empty-strategies-d3a8f7c2b1e4f569.yaml; grep -n \"falsy\\|empty\\|_none\\|bool\" tests/*.py | head -40", "description": "Show retry wait code and related release notes/tests"}
[tool_result]         self.statistics["delay_since_first_attempt"] = 0

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)

    def _run_retry(self, retry_state: "RetryCallState") -> None:
        self.iter_state.retry_run_result = self.retry(retry_state)

    def _run_wait(self, retry_state: "RetryCallState") -> None:
        # `wait` is annotated as always set, so a type checker sees this guard
        # as always true -- but untyped callers legiti
…[5074 chars elided]…
00:        def fails_twice() -> bool:
tests/test_tenacity.py:1717:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1732:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1752:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1771:            wait=tenacity.wait_none(),
tests/test_tenacity.py:1936:    def test_before_sleep_log_returns(self, exc_info: bool = False) -> None:
tests/test_asyncio.py:87:    async def test_wait_falsy_values_mean_no_wait(self) -> None:
[tool_use Bash] {"command": "sed -n 505,530p tests/test_tenacity.py && echo ---ASYNC--- && sed -n 80,110p tests/test_asyncio.py && echo --- && cat AGENTS.md | head -60 && ls <work>/env-tenacity/bin/python 2>&1", "description": "Read existing falsy-wait tests and project notes"}
[tool_result]             w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

    def test_wait_falsy_values_mean_no_wait(self) -> None:
        # Untyped callers pass None or 0 to mean "no wait", and `sum([])`
        # over an empty list of strategies yields the int 0. All must reach
        # the retry path without blowing up inside iter().
        def make_flaky() -> typing.Callable[[], str]:
            attempts = []

            def flaky() -> 
…[2092 chars elided]…
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
<work>/env-tenacity/bin/python
[assistant] Both loops use the same `if not self.wait` guard. I'll confirm the failure on the current code first, then fix both.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python && $PY -c \"\nimport tenacity\nclass W:\n    calls=0\n    def __len__(self): return 0\n    def __call__(self, rs):\n        W.calls+=1; return 0.25\nattempts=[]\ndef f():\n    attempts.append(1)\n    if len(attempts)<2: raise ValueError\n    return 'ok'\nr=tenacity.Retrying(wait=W(), stop=tenacity.stop_after_attempt(3))\nprint(r(f), 'wait called:', W.calls)\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Reproduce bug and run baseline test suite"}
[tool_result] ok wait called: 0
..................s.............................................................................................................. [ 70%]
.......................................................                  [100%]
183 passed, 1 skipped, 15 subtests passed in 1.82s
[assistant] Reproduced: the callable wait object with `__len__` returning 0 is never called, and the retry proceeds with no sleep. Now the fix, in both loops. The guard becomes "not callable and falsy", so every callable is invoked and only the non-callable no-wait values (`None`, `0`, `sum([])`) skip the call.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tenacity/__init__.py", "old_string": "        # `wait` is annotated as always set, so a type checker sees this guard\n        # as always true -- but untyped callers legitimately pass `None` or `0`\n        # to mean \"no wait\", and `sum([])` over an em
…[216 chars elided]…
his guard\n        # as always true -- but untyped callers legitimately pass `None` or `0`\n        # to mean \"no wait\", and `sum([])` over an empty list of strategies\n        # yields the int 0. Keep honouring those. Callables are always invoked,\n        # even if they define a falsy `__bool__` or `__len__`.\n        if not callable(self.wait) and not self.wait:  # type: ignore[truthy-bool]"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tenacity/asyncio/__init__.py", "old_string": "        # See BaseRetrying._run_wait: falsy `wait` values mean \"no wait\" and\n        # reach us from untyped callers.\n        if not self.wait:  # type: ignore[truthy-bool]", "new_string": "        # See BaseRetrying._run_wait: falsy non-callable `wait` values mean\n        # \"no wait\" and reach us from untyped callers; callables are always\n        # invoked.\n        if not callable(self.wait) and not self.wait:  # type: ignore[truthy-bool]"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tenacity/asyncio/__init__.py has been updated successfully.
[assistant] Now regression tests for both loops, placed next to the existing falsy-wait tests, plus a release note in the repo's reno format.
[tool_use Bash] {"command": "sed -n 530,540p tests/test_tenacity.py && echo ---- && sed -n 1,30p tests/test_asyncio.py | grep -n \"import\\|class\\|^def\\|^async\" && grep -n \"class NoIOErrorAfterCount\" -A12 tests/test_asyncio.py | head -20", "description": "View end of sync falsy test and asyncio test imports"}
[tool_result]                 )
                self.assertEqual(r(flaky), "ok")

    def test_wait_radd_plain_callable(self) -> None:
        # A plain callable is a valid WaitBaseT, and functions have no
        # __add__, so `callable + strategy` goes through wait_base.__radd__.
        def cb(retry_state: RetryCallState) -> float:
            return 2.0

        combined = cb + tenacity.wait_fixed(1)
        self.assertIsInstance(combined, tenacity.wait_combine)
----
15:import asyncio
16:import inspect
17:import unittest
18:from collections.abc import Callable, Coroutine
19:from functools import wraps
20:from typing import Any, TypeVar
21:from unittest import mock
24:    import trio
30:import pytest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py", "old_string": "                self.assertEqual(r(flaky), \"ok\")\n\n    def test_wait_radd_plain_callable(self) -> None:", "new_string": "                self.assertEqual(r(flaky), \"ok\")\n\n    def test_wait_falsy_callable_is_
…[889 chars elided]…
nd(1)\n                    if len(attempts) < 2:\n                        raise ValueError(\"boom\")\n                    return \"ok\"\n\n                r = Retrying(wait=wait, stop=tenacity.stop_after_attempt(3))  # type: ignore[arg-type]\n                self.assertEqual(r(flaky), \"ok\")\n                self.assertEqual(wait.calls, 1)\n\n    def test_wait_radd_plain_callable(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py", "old_string": "            await retrying(_async_function, thing)\n            assert thing.counter == thing.count\n\n    @asynctest\n    async def test_iscoroutinefunction(self) -> None:", "new_string": "            await retryin
…[509 chars elided]…
= 1\n                return 0.0\n\n        wait = FalsyWait()\n        thing = NoIOErrorAfterCount(2)\n        retrying = AsyncRetrying(wait=wait, stop=stop_after_attempt(5))  # type: ignore[arg-type]\n        await retrying(_async_function, thing)\n        assert thing.counter == thing.count\n        assert wait.calls == 1\n\n    @asynctest\n    async def test_iscoroutinefunction(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "cat > releasenotes/notes/fix-falsy-callable-wait-5c2e8d1f7a9b4e63.yaml <<'EOF'\n---\nfixes:\n  - |\n    A callable ``wait`` strategy is now always called, even when it is falsy\n    (for example, an empty container or an object whose ``__bool__`` or\n    ``__len__`` returns False). Previously such a strategy was silently\n    skipped and retries happened with no delay. The sync and as
…[79 chars elided]…
an no wait.\nEOF\nPY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list >/dev/null; $PY -m pytest -q -p no:cacheprovider --color=no -k falsy 2>&1 | tail -2", "description": "Add release note and run full test suite"}
[tool_result] =========================== short test summary info ============================
FAILED tests/test_asyncio.py::TestAsyncio::test_wait_falsy_callable_is_still_called
1 failed, 184 passed, 1 skipped, 17 subtests passed in 2.38s
FAILED tests/test_asyncio.py::TestAsyncio::test_wait_falsy_callable_is_still_called
1 failed, 3 passed, 182 deselected, 5 subtests passed in 0.54s
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no -k test_wait_falsy_callable 2>&1 | grep -E \"Error|error|assert\" | head -20", "description": "Show the async regression test failure detail"}
[tool_result]         thing = NoIOErrorAfterCount(2)
        assert thing.counter == thing.count
>       assert wait.calls == 1
E       assert 2 == 1
tests/test_asyncio.py:118: AssertionError
[assistant] The failure is in my test's expectation, not the fix: `NoIOErrorAfterCount(2)` fails twice, so two waits are correct. I'll assert against the failure count.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py", "old_string": "        assert wait.calls == 1", "new_string": "        assert wait.calls == thing.count"}
[tool_result] The file ~/.cache/lithify/work/repo-38fec5e48183/20261023-193249-bug-retrying-skips-the-wait-stra/base-1/tests/test_asyncio.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list >/dev/null; git stash -h >/dev/null 2>&1; git diff --stat; (cp tenacity/__init__.py /tmp/_bak_init.py && cp tenacity/asyncio/__init__.py /tmp/_bak_as
…[82 chars elided]…
D:tenacity/asyncio/__init__.py > tenacity/asyncio/__init__.py && $PY -m pytest -q -p no:cacheprovider --color=no -k falsy_callable 2>&1 | tail -1; cp /tmp/_bak_init.py tenacity/__init__.py; cp /tmp/_bak_async.py tenacity/asyncio/__init__.py; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff --stat", "description": "Run suite, confirm new tests fail on old code, restore fix"}
[tool_result] ...........................................................              [100%]
185 passed, 1 skipped, 17 subtests passed in 2.29s
 tenacity/__init__.py         |  5 +++--
 tenacity/asyncio/__init__.py |  7 ++++---
 tests/test_asyncio.py        | 21 +++++++++++++++++++++
 tests/test_tenacity.py       | 35 +++++++++++++++++++++++++++++++++++
 4 files changed, 63 insertions(+), 5 deletions(-)
2 failed, 1 passed, 184 deselected, 1 subtests passed in 0.31s
185 passed, 1 skipped, 17 subtests passed in 2.26s
 tenacity/__init__.py         |  5 +++--
 tenacity/asyncio/__init__.py |  7 ++++---
 tests/test_asyncio.py        | 21 +++++++++++++++++++++
 tests/test_tenacity.py       | 35 +++++++++++++++++++++++++++++++++++
 4 files changed, 63 insertions(+), 5 deletions(-)
[assistant] The new tests fail on the original code and pass with the fix. Last, a type check, since the `type: ignore` comments depend on the guard's narrowing.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m mypy tenacity 2>&1 | tail -3; $PY -m ruff check tenacity tests 2>&1 | tail -2; git status --short", "description": "Run mypy and ruff on changed code"}
[tool_result] <work>/env-tenacity/bin/python: No module named mypy
<work>/env-tenacity/bin/python: No module named ruff
 M tenacity/__init__.py
 M tenacity/asyncio/__init__.py
 M tests/test_asyncio.py
 M tests/test_tenacity.py
?? releasenotes/notes/fix-falsy-callable-wait-5c2e8d1f7a9b4e63.yaml
[assistant] Callable wait strategies are now always called, in both the sync and async retry loops. The full suite passes (185 passed, 1 skipped), and the new regression tests fail on the original code.

**Cause:** `_run_wait` in `tenacity/__init__.py` and `AsyncRetrying._run_wait` in `tenacity/asyncio/__init__.py` both guarded with `if not self.wait:`. That treated any falsy strategy as "no wait", so a callable with `__bool__` or `__len__` returning 0 was never called and retries ran with no delay.

**Fix:** both guards are now `if not callable(self.wait) and not self.wait:`. Callables are always invoked
…[66 chars elided]…
kip the call, as before.

**Tests added:**
- `tests/test_tenacity.py`: `test_wait_falsy_callable_is_still_called`, covering a `__bool__`-False object and a `__len__`-0 container.
- `tests/test_asyncio.py`: `test_wait_falsy_callable_is_still_called` for `AsyncRetrying`.

**Release note:** `releasenotes/notes/fix-falsy-callable-wait-5c2e8d1f7a9b4e63.yaml`, in the repo's reno format.

I did not run mypy or ruff because neither is installed in the project's test environment. The two `# type: ignore[truthy-bool]` comments were kept, so the type checker behaviour is unverified. Nothing is committed.
