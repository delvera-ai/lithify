# trajectory comp-1

final message:
`metric()` now moves to the next prefix when rounding reaches 1000, so the three reported outputs are fixed:

- `metric(999.9, "V")` → `'1.00 kV'`
- `metric(999999, "V")` → `'1.00 MV'`
- `metric(0.0009999, "V")` → `'1.00 mV'`

The fix is in `src/humanize/number.py`. The mantissa is now formatted before the prefix is chosen. If it rounds to 1000 and the value is below Q, the exponent goes up one and the mantissa is recomputed. Q is the largest prefix, so `metric(999.9e30, "V")` still returns `'1000 QV'`. Negative values keep their sign (`-999.9` → `'-1.00 kV'`).

**Verification**
- Reproduced all three bugs on the unmodified code before editing.
- `compare_outputs.py` over 31 expressions: 18 changed, 13 same. The changes are the rounding-carry cases (including `0.9996` → `'1.00'`, and precision 0–2 variants). The unchanged ones are the normal-range cases and the Q boundary.
- Added six `test_metric` cases, one for each kind of changed input: `999.9 V`, `999999 V`, `-999.9 V`, `0.0009999 V`, `999.96 V` at precision 4, and `0.9996` with no unit. I didn't add a Q-boundary case because it already behaved correctly.
- Full suite: `710 passed, 69 skipped` (baseline was 704 passed, 69 skipped; the 6 new tests account for the difference).
- Lint was not run; ruff and black aren't installed. I checked added lines against 88 characters with awk and none exceed the limit.

**Not changed:** `metric(99.96, "V")` returns `'100.0 V'`. It has the same kind of extra digit, but it doesn't reach 1000, so it's outside this bug. It may be worth a separate issue.

I haven't committed anything.

## events
[assistant] I'll start by reading the project's memory file for the interpreter path, then the `metric` code.
[tool_use Bash] {"command": "ls -la && find . -name memory.md -not -path './.git/*' | head && grep -n \"def metric\" -A 80 src/humanize/number.py", "description": "List repo, find memory.md, show metric function"}
[tool_result] total 120
drwxr-xr-x@ 24 donovan  staff   768 Oct 23 14:51 .
drwxr-xr-x@ 11 donovan  staff   352 Oct 23 14:51 ..
drwxr-xr-x@  3 donovan  staff    96 Oct 23 14:51 .agents
drwxr-xr-x@  3 donovan  staff    96 Oct 23 14:51 .claude
-rw-r--r--@  1 donovan  staff   189 Oct 23 14:51 .git
drwxr-xr-x@ 11 donovan  staff   352 Oct 23 14:51 .github
-rw-r--r--@  1 donovan  staff  2770 Oct 23 14:51 .gitignore
drwxr-xr-x@  5 donovan  staff   160 Oct 23 14:51 .lithify
-rw-r--r--@  1 donovan  staff  1888 Oct 23 1
…[2576 chars elided]…
 value /= 10 ** (exponent // 3 * 3)
547-    if exponent >= 3:
548-        ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
549-    elif exponent < 0:
550-        ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
551-    else:
552-        ordinal_ = ""
553-    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
554-    if not (unit or ordinal_) or unit in ("°", "′", "″"):
555-        space = ""
556-    else:
557-        space = " "
558-
559-    return f"{value_}{space}{ordinal_}{unit}"
[tool_use Bash] {"command": "cat .lithify/harness/memory.md && echo ---- && grep -n \"metric\" -A 3 tests/*.py | head -150", "description": "Read harness memory and existing metric tests"}
[tool_result] - The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Style is ruff (`[tool.ruff]` selects `E`/`W`, no `line-length`, so the default 88 applies) plus black via pre-commit. Neither ruff, black nor mypy is installed, so don't probe for them. Keep every added line in `src/` and `tests/` at 88 characters o
…[140 chars elided]…
ssage that lint wasn't run.
----
tests/test_benchmarks.py:44:def test_metric(benchmark: BenchmarkFixture) -> None:
tests/test_benchmarks.py:45:    benchmark(humanize.metric, 1500, "W")
tests/test_benchmarks.py-46-
tests/test_benchmarks.py-47-
tests/test_benchmarks.py-48-def test_natural_list(benchmark: BenchmarkFixture) -> None:
tests/test_number.py:311:def test_metric(test_args: list[typing.Any], expected: str) -> None:
tests/test_number.py:312:    assert humanize.metric(*test_args) == expected
[tool_use Bash] {"command": "sed -n 270,315p tests/test_number.py && ls <work>/env-humanize/bin/python; cat .lithify/harness/scripts/compare_outputs.py | head -40", "description": "Show metric tests and check interpreter and compare script"}
[tool_result]         ([-1500, "V"], "-1.50 kV"),
        ([0.12], "120 m"),
        ([0.012], "12.0 m"),
        ([0.0012], "1.20 m"),
        ([0.00012], "120 μ"),
        ([1e-23], "10.0 y"),
        ([1e-24], "1.00 y"),
        ([1e-25], "100 r"),
        ([1e-26], "10.0 r"),
        ([1, "°"], "1.00°"),
        ([0.1, "°"], "100m°"),
        ([100], "100"),
        ([0.1], "100 m"),
        ([1.5123, "", 0], "2"),
        ([10.5123, "", 0], "11"),
        ([10.5123, "", 1], "11"),
        ([10.5123, "", 
…[2198 chars elided]…
ummary line
`N expressions, C changed, S same`.

Exit codes: 0 = comparison ran (whether or not anything changed); 2 = setup failed (not a git
repo, ref/src missing, setup code raised, or a side imported the package from the wrong place).
On exit 2 read the message; do not retry unchanged.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile

DEFAULT_SETUP = "import humanize\nfrom humanize import *\n"
[assistant] Next I'll reproduce the reported outputs on the unmodified code, plus the baseline test run.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && PYTHONPATH=src $PY -c 'from humanize import metric as m; print(repr(m(999.9,\"V\")), repr(m(999999,\"V\")), repr(m(0.0009999,\"V\")), repr(m(999.9e30,\"V\")), repr(m(999.9e-27,\"V\")))' && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Reproduce bug on unmodified code and run baseline tests"}
[tool_result] '1000 V' '1000 kV' '1000 μV' '1000 QV' '1000 rV'
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
704 passed, 69 skipped in 5.88s
[assistant] The bug reproduces on the unmodified code: `'1000 V'`, `'1000 kV'`, `'1000 μV'`. Baseline is 704 passed, 69 skipped.

The cause is that the mantissa is rounded after the prefix is picked, so a value like 999.9 V gets four digits. The fix is to re-scale to the next prefix when the rounded mantissa reaches 1000, except at Q, the largest prefix. I'll also need `abs()` so negative values are handled.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/src/humanize/number.py", "old_string": "    value /= 10 ** (exponent // 3 * 3)\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n
…[415 chars elided]…
the largest prefix, so values there are left as they are.\n        exponent += 1\n        value /= 1000\n        value_ = format(value, f\".{int(max(0, precision - exponent % 3 - 1))}f\")\n    if exponent >= 3:\n        ordinal_ = \"kMGTPEZYRQ\"[exponent // 3 - 1]\n    elif exponent < 0:\n        ordinal_ = \"m\u03bcnpfazyrq\"[(-exponent - 1) // 3]\n    else:\n        ordinal_ = \"\"\n    if not"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/src/humanize/number.py has been updated successfully.
[assistant] Next I'll sweep many inputs with the project's comparison script to see which outputs change, including negatives, carries at each prefix, and the Q boundary.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && D=$(mktemp -d /private/tmp/claude-501/metric-sweep-XXXX) && cat > $D/exprs.txt <<'EOF'\nmetric(999.9, \"V\")\nmetric(999999, \"V\")\nmetric(0.0009999, \"V\")\nmetric(-999.9, \"V\")\nmetric(-0.0009999, \"V\")\nmetric(999.9e30, 
…[565 chars elided]…
)\nmetric(2e8, \"W\")\nmetric(220e-6, \"F\")\nEOF\nPYTHONPATH=src $PY -c 'import humanize,sys; print(humanize.__file__)' && $PY .lithify/harness/scripts/compare_outputs.py --file $D/exprs.txt && echo \"=== changed only ===\" && $PY .lithify/harness/scripts/compare_outputs.py --file $D/exprs.txt --changed-only; echo \"$D\"", "description": "Compare committed and edited metric outputs over a sweep"}
[tool_result] ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/src/humanize/__init__.py
CHANGED metric(999.9, "V")
    HEAD: '1000 V'
    work: '1.00 kV'
CHANGED metric(999999, "V")
    HEAD: '1000 kV'
    work: '1.00 MV'
CHANGED metric(0.0009999, "V")
    HEAD: '1000 μV'
    work: '1.00 mV'
CHANGED metric(-999.9, "V")
    HEAD: '-1000 V'
    work: '-1.00 kV'
CHANGED metric(-0.0009999, "V")
    HEAD: '-1000 μV'
    work: '-1.00 mV'
same    metric(999
…[2922 chars elided]…
00 rV'
CHANGED metric(999999999999.9, "V")
    HEAD: '1000 GV'
    work: '1.00 TV'
CHANGED metric(0.99999999, "V")
    HEAD: '1000 mV'
    work: '1.00 V'
old side imported /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/compare-outputs-5e4fwqlf/src/humanize/__init__.py
new side imported ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/src/humanize/__init__.py
31 expressions, 18 changed, 13 same
/private/tmp/claude-501/metric-sweep-4a2I
[assistant] The sweep shows the intended changes. Values at 1000 now move up a prefix, negatives keep their sign, and the Q boundary (`999.9e30` → `'1000 QV'`) is unchanged. Next I'll add regression tests for the inputs that changed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/tests/test_number.py", "old_string": "        ([1, \"\u00b0\"], \"1.00\u00b0\"),", "new_string": "        ([999.9, \"V\"], \"1.00 kV\"),\n        ([999999, \"V\"], \"1.00 MV\"),\n        ([-999.9, \"V\"], \"-1.00 kV\"),\n        ([0.0009999, \"V\"], \"1.00 mV\"),\n        ([999.96, \"V\", 4], \"1.000 kV\"),\n        ([0.9996], \"1.00\"),\n        ([1, \"\u00b0\"], \"1.00\u00b0\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-144514-bug-humanize-metric-can-output-a/comp-1/tests/test_number.py has been updated successfully.
[assistant] Now the full test suite, plus the line-length check the project asks for.
[tool_use Bash] {"command": "PY=<work>/env-humanize/bin/python && PYTHONPATH=src $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; echo \"--- long lines (bytes, >88) in added lines:\"; git diff -U0 -- src tests | grep '^+' | grep -v '^+++' | awk 'length > 89' ; echo \"(end)\"; git diff --stat", "description": "Run full test suite and check added line lengths"}
[tool_result]   OPS: Operations Per Second, computed as 1 / Mean
710 passed, 69 skipped in 5.99s
--- long lines (bytes, >88) in added lines:
(end)
 src/humanize/number.py | 8 +++++++-
 tests/test_number.py   | 6 ++++++
 2 files changed, 13 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "git diff -- src", "description": "Show the source diff"}
[tool_result] diff --git a/src/humanize/number.py b/src/humanize/number.py
index 1cbfc2b..26a7f74 100644
--- a/src/humanize/number.py
+++ b/src/humanize/number.py
@@ -544,13 +544,19 @@ def metric(value: float, unit: str = "", precision: int = 3) -> str:
         return scientific(value, precision - 1) + unit
 
     value /= 10 ** (exponent // 3 * 3)
+    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
+    if abs(float(value_)) >= 1000 and exponent < 32:
+        # Rounding carried in
…[118 chars elided]…
eft as they are.
+        exponent += 1
+        value /= 1000
+        value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
     if exponent >= 3:
         ordinal_ = "kMGTPEZYRQ"[exponent // 3 - 1]
     elif exponent < 0:
         ordinal_ = "mμnpfazyrq"[(-exponent - 1) // 3]
     else:
         ordinal_ = ""
-    value_ = format(value, f".{int(max(0, precision - exponent % 3 - 1))}f")
     if not (unit or ordinal_) or unit in ("°", "′", "″"):
         space = ""
     else:
[assistant] `metric()` now moves to the next prefix when rounding reaches 1000, so the three reported outputs are fixed:

- `metric(999.9, "V")` → `'1.00 kV'`
- `metric(999999, "V")` → `'1.00 MV'`
- `metric(0.0009999, "V")` → `'1.00 mV'`

The fix is in `src/humanize/number.py`. The mantissa is now formatted before the prefix is chosen. If it rounds to 1000 and the value is below Q, the exponent goes up one and the mantissa is recomputed. Q is the largest prefix, so `metric(999.9e30, "V")` still returns `'1000 QV'`. Negative values keep their sign (`-999.9` → `'-1.00 kV'`).

**Verification**
- Reproduced a
…[397 chars elided]…
999 V`, `999.96 V` at precision 4, and `0.9996` with no unit. I didn't add a Q-boundary case because it already behaved correctly.
- Full suite: `710 passed, 69 skipped` (baseline was 704 passed, 69 skipped; the 6 new tests account for the difference).
- Lint was not run; ruff and black aren't installed. I checked added lines against 88 characters with awk and none exceed the limit.

**Not changed:** `metric(99.96, "V")` returns `'100.0 V'`. It has the same kind of extra digit, but it doesn't reach 1000, so it's outside this bug. It may be worth a separate issue.

I haven't committed anything.
