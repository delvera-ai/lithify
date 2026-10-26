# trajectory base-1

final message:
Implemented the cap shortcut so attempts beyond `max` skip the power operation while preserving clamping behavior.

Added regression coverage that fails if power is computed beyond the cap.

Validation: 168 passed, 1 skipped; diff checks passed.

## events
[assistant] I’ll check the wait strategy and tests, add the cap shortcut, then run the project checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'class wait_exponential|wait_exponential' tenacity/wait.py tests; git status --short"
tenacity/wait.py:178:class wait_exponential(wait_base):
tenacity/wait.py:212:class wait_random_exponential(wait_exponential):
tenacity/wait.py:234:    wait_exponential strategy (which uses a fixed interval) may be preferable.
tenacity/wait.py:243:class wait_exponential_jitter(wait_base):
tests/test_tenacity.py:340:        r = Retrying(wait=tenacity.wait_exponential())
tests/test_tenacity.py:351:        r = Retrying(wait=tenacity.wait_exponential(max=40))
tests/test_tenacity.py:363:        r = Re
…[1141 chars elided]…
y.py:648:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:654:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:656:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:660:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:662:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,40p;178,245p' tenacity/wait.py"
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
…[2928 chars elided]…
ing for an unavailable resource to become available again, as
    opposed to trying to resolve contention for a shared resource, the
    wait_exponential strategy (which uses a fixed interval) may be preferable.

    """

    def __call__(self, retry_state: "RetryCallState") -> float:
        high = super().__call__(retry_state=retry_state)
        return random.uniform(self.min, high)


class wait_exponential_jitter(wait_base):
    """Wait strategy that applies exponential backoff and jitter.


[command exit=0] /bin/zsh -lc "rtk proxy sed -n '320,425p' tests/test_tenacity.py"
                self.assertTrue(len(times) > 1)
                for t in times:
                    self.assertTrue(t >= 1)
                    self.assertTrue(t < 20)

    def test_random_sleep_withoutmin_(self) -> None:
        r = Retrying(wait=tenacity.wait_random(max=2))
        times = set()
        times.add(r.wait(make_retry_state(1, 6546)))
        times.add(r.wait(make_retry_state(1, 6546)))
        times.add(r.wait(make_retry_state(1, 6546)))
        times.add(r.wait(make_retry_state(
…[4514 chars elided]…
100)

    def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

    def test_wait_func(self) -> None:
        def wait_func(retry_state: RetryCallState) -> typing.Any:
            return retry_state.attempt_number * retry_state.seconds_since_start  # type: ignore[operator]

        r = Retrying(wait=wait_func)
        self.assertEqual(r.wait(make_retry_state(1, 5)), 5)
        self.assertEqual(r.wait(make_retry_state(2, 11)), 22)

[command exit=0] /bin/zsh -lc 'rtk proxy cat pyproject.toml'
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
    { name = "Julien Danjou", email = "julien@danjou.info" },
]
classifiers = [
    "Intended Audience :: Developers",
    "Prog
…[2204 chars elided]…
ions
    "RUF003",  # ambiguous unicode characters in comments (copyright names)
    "RUF005",  # iterable unpacking vs concatenation (less readable for tuple +)
    "RUF012",  # mutable class default (test constant, never mutated)
    "SIM108",  # ternary instead of if-else (less readable in context)
]

[tool.mypy]
strict = true
files = ["tenacity", "tests"]
show_error_codes = true
exclude = ["tenacity/_version\\.py"]

[[tool.mypy.overrides]]
module = "tornado.*"
ignore_missing_imports = true


[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201707-performance-wait-exponential-max/base-1/tenacity/wait.py
[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201707-performance-wait-exponential-max/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...............s................................................................................................................ [ 75%]
.........................................                                [100%]
168 passed, 1 skipped, 16 subtests passed in 1.84s

[assistant] The shortcut now compares the exponent with the cap before computing the power. Regression tests use a base that raises if power is called, including at an extremely large attempt number. The full test suite is running.
[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff --stat'
tenacity/wait.py       | 12 ++++++++++++
 tests/test_tenacity.py | 19 +++++++++++++++++++
 2 files changed, 31 insertions(+)

[assistant] Implemented the cap shortcut so attempts beyond `max` skip the power operation while preserving clamping behavior.

Added regression coverage that fails if power is computed beyond the cap.

Validation: 168 passed, 1 skipped; diff checks passed.
