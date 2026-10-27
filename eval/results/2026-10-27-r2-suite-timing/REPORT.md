# Zero-token suite timing before A replicates

At frozen task-1 base 8c8d06264d320ff40fcbb0044ab1345e1994f2bb,
the unchanged repository test command passed twice:

| load | wall seconds | pytest exit |
|---|---:|---:|
| isolated | 43.003 | 0 |
| planned replicate load | 42.442 | 0 |

Both are below the round-1 60–80 second range and below the 160 second
blocking threshold. No environment or test fix was needed. Zero tokens/$0.
A replicates will run sequentially, keeping internal --concurrency 4 and
--timeout 900. A's k=0/no-escalation produces only one active probe/suite;
therefore isolated and planned-load suite concurrency are both 1. No other
replicate was running during either measurement. This does not benchmark
four simultaneous suites or establish B's multi-probe timing.

Use absolute env-sqlglot/bin/python (3.12.13) with its bin on PATH, pytest
-q -p no:cacheprovider --color=no, and the existing version stub. The launch
environment is minimal as in the original horizon command. Evidence:
timings.json and the two logs; reproduce with eval/round2/suite_timing.py.
Round-1 launch commands were recovered from the original coordinator session:
they supplied no timeout/concurrency overrides; f964993 defaults are 900/4.
