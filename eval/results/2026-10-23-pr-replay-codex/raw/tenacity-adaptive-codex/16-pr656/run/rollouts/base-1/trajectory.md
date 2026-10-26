# trajectory base-1

final message:
Fixed `wait_exponential` to handle ratio underflow and nonfinite multipliers without taking an invalid logarithm. Ordinary-value calculations remain unchanged.

Added regression coverage. All checks passed: 172 tests passed, 1 skipped.

## events
[assistant] I’ll inspect the exponential wait calculation, add regression coverage, and run the project’s checks.
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

[command exit=0] /bin/zsh -lc "rg -n 'class wait_exponential|math.log|wait_exponential' tenacity/wait.py tests/test_tenacity.py; git status --short"
tenacity/wait.py:179:class wait_exponential(wait_base):
tenacity/wait.py:211:            and exponent > math.log(self.max / self.multiplier, self.exp_base)
tenacity/wait.py:222:class wait_random_exponential(wait_exponential):
tenacity/wait.py:244:    wait_exponential strategy (which uses a fixed interval) may be preferable.
tenacity/wait.py:253:class wait_exponential_jitter(wait_base):
tests/test_tenacity.py:340:        r = Retrying(wait=tenacity.wait_exponential())
tests/test_tenacity.py:351:  
…[1357 chars elided]…
y.py:656:        fn = tenacity.wait_exponential_jitter(multiplier=10, max=60, jitter=0)
tests/test_tenacity.py:662:    def test_wait_exponential_jitter_initial_deprecated(self) -> None:
tests/test_tenacity.py:664:            fn = tenacity.wait_exponential_jitter(initial=10, max=60, jitter=0)
tests/test_tenacity.py:668:    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:
tests/test_tenacity.py:670:            tenacity.wait_exponential_jitter(initial=5, multiplier=10)

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
…[4577 chars elided]…
ke_retry_state(5, 0)), 16)
                self.assertEqual(r.wait(make_retry_state(6, 0)), 32)
                self.assertEqual(r.wait(make_retry_state(7, 0)), 64)
                self.assertEqual(r.wait(make_retry_state(8, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(9, 0)), 100)
                self.assertEqual(r.wait(make_retry_state(20, 0)), 100)

    def test_legacy_explicit_wait_type(self) -> None:
        Retrying(wait="exponential_sleep")  # type: ignore[arg-type]

[command exit=0] /bin/zsh -lc 'rtk proxy find .. -name AGENTS.md'
../base-1/AGENTS.md

[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201932-bug-wait-exponential-can-raise-v/base-1/tenacity/wait.py, update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201932-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py
[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-201932-bug-wait-exponential-can-raise-v/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
...............s............................................................................................................... [ 73%]
..............................................                           [100%]
172 passed, 1 skipped, 17 subtests passed in 1.89s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[command exit=0] /bin/zsh -lc 'rtk git diff'
tenacity/wait.py       |  6 +++++-
 tests/test_tenacity.py | 20 ++++++++++++++++++++
 2 files changed, 25 insertions(+), 1 deletion(-)

--- Changes ---

tenacity/wait.py
  @@ -208,7 +208,11 @@ class wait_exponential(wait_base):
  -            and exponent > math.log(self.max / self.multiplier, self.exp_base)
  +            and math.isfinite(self.multiplier)
  +            and (
  +                self.max / self.multiplier == 0
  +                or exponent > math.log(self.max / self.multiplier
…[873 chars elided]…
oat("nan"), 0),
  +        ):
  +            with self.subTest(multiplier=multiplier):
  +                wait = tenacity.wait_exponential(multiplier=multiplier, max=40)
  +                for attempt in (1, 2, 50):
  +                    self.assertEqual(wait(make_retry_state(attempt, 0)), expected)
  +
       def test_exponential_with_min_wait(self) -> None:
           r = Retrying(wait=tenacity.wait_exponential(min=20))
           self.assertEqual(r.wait(make_retry_state(1, 0)), 20)
  +20 -0

[assistant] Fixed `wait_exponential` to handle ratio underflow and nonfinite multipliers without taking an invalid logarithm. Ordinary-value calculations remain unchanged.

Added regression coverage. All checks passed: 172 tests passed, 1 skipped.
