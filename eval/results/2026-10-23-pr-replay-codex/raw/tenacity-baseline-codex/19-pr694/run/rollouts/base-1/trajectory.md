# trajectory base-1

final message:
Fixed all three regressions:

- `None`, `0`, and `sum([])` work as no-wait values for sync and async retries.
- Plain callables can be added to wait strategies.
- `wait_combine` passes retry state positionally.

Added regression tests. Full suite: **176 passed, 1 skipped**; diff checks passed.

## events
[assistant] I’ll inspect the retry and wait code, fix the three regressions, and run the project’s checks.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*wait*' -g '*async*' -g '*test*' -g '__init__.py'"
~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1
tenacity/asyncio/__init__.py
tenacity/__init__.py
tenacity/wait.py
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml
releasenotes/notes/fix_async-52b6594c8e75c4bc.yaml
releasenotes/notes/no-async-iter-6132a42e52348a75.yaml
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/no
…[357 chars elided]…
-fe5ac61940b0a5ed.yaml
releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
releasenotes/notes/wait-radd-int-6f1a3c9d84b2e057.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
releasenotes/notes/fix-async-loop-with-result-f68e913ccb425aca.yaml
AGENTS.md
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/__init__.py
tests/test_utils.py

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk rg -n 'def _run_wait|def __radd__|class wait_combine|self.wait|class TestWait|wait_combine' tenacity tests/test_tenacity.py tests/test_asyncio.py"
tests/test_tenacity.py:285:class TestWaitConditions(unittest.TestCase):
tests/test_tenacity.py:442:    def test_wait_combine(self) -> None:
tests/test_tenacity.py:444:            wait=tenacity.wait_combine(
tenacity/asyncio/__init__.py:149:    async def _run_wait(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
tenacity/asyncio/__init__.py:150:        retry_state.upcoming_sleep = await _utils.wrap_to_async_func(self.wait)(
tenacity/__init__.py:75:    wait_combine,
tenacity
…[729 chars elided]…
city/wait.py:76:        self.wait_random_min = _utils.to_seconds(min)
tenacity/wait.py:77:        self.wait_random_max = _utils.to_seconds(max)
tenacity/wait.py:81:        return self.wait_random_min + (
tenacity/wait.py:82:            random.random() * (self.wait_random_max - self.wait_random_min)
tenacity/wait.py:86:class wait_combine(wait_base):
tenacity/wait.py:90:        self.wait_funcs = strategies
tenacity/wait.py:94:        return sum(x(retry_state=retry_state) for x in self.wait_funcs)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,160p' tenacity/wait.py"
# Copyright 2016–2021 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS O
…[4119 chars elided]…
str) -> None:
            response = requests.get(url)
            response.raise_for_status()
    """

    def __init__(self, predicate: typing.Callable[[BaseException], float]) -> None:
        self.predicate = predicate

    @override
    def __call__(self, retry_state: "RetryCallState") -> float:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        exception = retry_state.outcome.exception()
        if exception is None:

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '410,428p' tenacity/__init__.py"

    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(fn)

    def _run_retry(self, retry_state: "RetryCallState") -> None:
        self.iter_state.retry_run_result = self.retry(retry_state)

    def _run_wait(self, retry_state: "RetryCallState") -> None:
        retry_state.upcoming_sleep = self.wait(retry_state)

    def _run_stop(self, retry_state: "RetryCallState") -> None:
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = self.stop(retry_state)

    def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:
            result = action(retry_state)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '135,165p' tenacity/asyncio/__init__.py"
            else:
                return do  # type: ignore[no-any-return]

    @override
    def _add_action_func(self, fn: t.Callable[..., t.Any]) -> None:
        self.iter_state.actions.append(_utils.wrap_to_async_func(fn))

    @override
    async def _run_retry(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.iter_state.retry_run_result = await _utils.wrap_to_async_func(self.retry)(
            retry_state
        )

    @override
    async def _run_wait
…[216 chars elided]…
 _run_stop(self, retry_state: "RetryCallState") -> None:  # type: ignore[override]
        self.statistics["delay_since_first_attempt"] = retry_state.seconds_since_start
        self.iter_state.stop_run_result = await _utils.wrap_to_async_func(self.stop)(
            retry_state
        )

    @override
    async def iter(self, retry_state: "RetryCallState") -> DoAttempt | DoSleep | t.Any:
        self._begin_iter(retry_state)
        result = None
        for action in self.iter_state.actions:

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '285,325p' tests/test_tenacity.py"
class TestWaitConditions(unittest.TestCase):
    def test_no_sleep(self) -> None:
        r = Retrying()
        self.assertEqual(0, r.wait(make_retry_state(18, 9879)))

    def test_fixed_sleep(self) -> None:
        for wait in (1, datetime.timedelta(seconds=1)):
            with self.subTest():
                r = Retrying(wait=tenacity.wait_fixed(wait))
                self.assertEqual(1, r.wait(make_retry_state(12, 6546)))

    def test_incrementing_sleep(self) -> None:
        for start, i
…[661 chars elided]…
medelta(seconds=20)),
        ):
            with self.subTest():
                r = Retrying(wait=tenacity.wait_random(min=min_, max=max_))
                times = set()
                for _ in range(1000):
                    times.add(r.wait(make_retry_state(1, 6546)))

                # this is kind of non-deterministic...
                self.assertTrue(len(times) > 1)
                for t in times:
                    self.assertTrue(t >= 1)
                    self.assertTrue(t < 20)


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '410,490p' tests/test_tenacity.py"
        self.assertEqual(r.wait(make_retry_state(20, 0)), 1048576)

    def test_exponential_with_min_wait_andmax__wait(self) -> None:
        for min_, max_ in (
            (10, 100),
            (datetime.timedelta(seconds=10), datetime.timedelta(seconds=100)),
        ):
            with self.subTest():
                r = Retrying(wait=tenacity.wait_exponential(min=min_, max=max_))
                self.assertEqual(r.wait(make_retry_state(1, 0)), 10)
                self.assertEqual(r.wait(m
…[2470 chars elided]…
ait(make_retry_state(1, 5))
            self.assertLess(w, 8)
            self.assertGreaterEqual(w, 5)

    def test_wait_triple_sum(self) -> None:
        r = Retrying(
            wait=tenacity.wait_fixed(1)
            + tenacity.wait_random(0, 3)
            + tenacity.wait_fixed(5)
        )
        # Test it a few time since it's random
        for _i in range(1000):
            w = r.wait(make_retry_state(1, 5))
            self.assertLess(w, 9)
            self.assertGreaterEqual(w, 6)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,150p' tests/test_asyncio.py"
# Copyright 2016 Étienne Bersac
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
# See the License for the spe
…[3460 chars elided]…
_retry_preserves_argument_defaults(self) -> None:
        async def function_with_defaults(a: int = 1) -> int:
            return a

        async def function_with_kwdefaults(*, a: int = 1) -> int:
            return a

        retrying = AsyncRetrying(
            wait=tenacity.wait_fixed(0.01), stop=tenacity.stop_after_attempt(3)
        )
        wrapped_defaults_function = retrying.wraps(function_with_defaults)
        wrapped_kwdefaults_function = retrying.wraps(function_with_kwdefaults)


[command exit=0] /bin/zsh -lc "rtk rg -n 'radd|NotImplemented|sum\\(|unsupported|wait=0|wait=None' tests/test_tenacity.py tests/test_asyncio.py"
tests/test_tenacity.py:472:    def test_wait_double_sum(self) -> None:
tests/test_tenacity.py:480:    def test_wait_triple_sum(self) -> None:
tests/test_tenacity.py:492:    def test_wait_arbitrary_sum(self) -> None:
tests/test_tenacity.py:494:            wait=sum(  # type: ignore[arg-type]
tests/test_tenacity.py:602:            return float(sum(lst)) / float(len(lst))
tests/test_tenacity.py:2233:        raise NotImplementedError

[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1/tenacity/__init__.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1/tenacity/asyncio/__init__.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1/tenacity/wait.py
[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1/tests/test_asyncio.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-202331-three-regressions-that-only-appe/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
................s............................................. [ 35%]
............................................................. [ 69%]
......................................................                   [100%]
176 passed, 1 skipped, 21 subtests passed in 1.84s

[assistant] The fixes are in place. New regression tests exercise an actual retry for each no-wait value in sync and async code, plus callable composition and positional state passing. The full test suite is running.
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/__init__.py         |  2 +-
 tenacity/asyncio/__init__.py |  9 ++++++---
 tenacity/wait.py             | 20 ++++++++++----------
 tests/test_asyncio.py        | 15 +++++++++++++++
 tests/test_tenacity.py       | 29 +++++++++++++++++++++++++++++
 5 files changed, 61 insertions(+), 14 deletions(-)

[assistant] Fixed all three regressions:

- `None`, `0`, and `sum([])` work as no-wait values for sync and async retries.
- Plain callables can be added to wait strategies.
- `wait_combine` passes retry state positionally.

Added regression tests. Full suite: **176 passed, 1 skipped**; diff checks passed.
