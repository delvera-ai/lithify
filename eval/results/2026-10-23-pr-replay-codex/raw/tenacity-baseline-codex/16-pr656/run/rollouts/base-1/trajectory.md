# trajectory base-1

final message:
Fixed the logarithm guard to avoid zero ratios, allowing the existing calculation to return the capped wait. Ordinary values retain their existing behavior.

Added regression coverage for underflow and nonfinite multipliers.

Validation: 172 tests passed, 1 skipped; diff check passed.

## events
[assistant] I’ll inspect the exponential wait calculation, add regression coverage, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg -n 'class wait_exponential|math.log|wait_exponential' tenacity/wait.py tests/test_tenacity.py; rg --files -g AGENTS.md"
~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201933-bug-wait-exponential-can-raise-v/base-1
tenacity/wait.py:179:class wait_exponential(wait_base):
tenacity/wait.py:211:            and exponent > math.log(self.max / self.multiplier, self.exp_base)
tenacity/wait.py:222:class wait_random_exponential(wait_exponential):
tenacity/wait.py:244:    wait_exponential strategy (which uses a fixed interval) may be preferable.
tenacity/wait.py:253:class wait_exponential_jitter(wait_base):
te
…[1476 chars elided]…
       fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:662:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:664:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:668:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:670:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '175,225p' tenacity/wait.py"
        result = self.start + (self.increment * (retry_state.attempt_number - 1))
        return max(0, min(result, self.max))


class wait_exponential(wait_base):
    """Wait strategy that applies exponential backoff.

    It allows for a customized multiplier and an ability to restrict the
    upper and lower limits to some maximum and minimum value.

    The intervals are fixed (i.e. there is no jitter), so this strategy is
    suitable for balancing retries against latency when a required re
…[873 chars elided]…
 / self.multiplier, self.exp_base)
        ):
            return max(max(0, self.min), self.max)
        try:
            exp = self.exp_base**exponent
            result = self.multiplier * exp
        except OverflowError:
            return self.max
        return max(max(0, self.min), min(result, self.max))


class wait_random_exponential(wait_exponential):
    """Random wait with exponentially widening window.

    An exponential backoff strategy used to mediate contention between multiple

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '320,430p' tests/test_tenacity.py"
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
…[4789 chars elided]…
try_state(8, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(9, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)

    def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

    def test_wait_func(self) -> None:
        def wait_func(retry_state: RetryCallState) -> typing.Any:
            return retry_state.attempt_number * retry_state.seconds_since_start  # type: ignore[operator]


[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201933-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py, update ~/.cache/lithify/work/repo-d0c7726da9a8/20261023-201933-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...............s....................................................................................................... [ 68%]
......................................................                   [100%]
172 passed, 1 skipped, 25 subtests passed in 1.98s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Fixed the logarithm guard to avoid zero ratios, allowing the existing calculation to return the capped wait. Ordinary values retain their existing behavior.

Added regression coverage for underflow and nonfinite multipliers.

Validation: 172 tests passed, 1 skipped; diff check passed.
