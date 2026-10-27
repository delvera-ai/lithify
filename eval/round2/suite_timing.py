"""Zero-token suite timing at the frozen first horizon base."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evalkit import redact
from repos import prepare_checkout

root = Path(__file__).resolve().parents[2]
work = Path.home() / ".cache/lithify-dev/r2-noise-scratch"
clone = work / "suite-timing"
if not clone.exists():
    subprocess.run(["git", "clone", "-q", str(work / "sqlglot.git"), str(clone)], check=True)
base = json.loads((root / "eval/round2/INPUT_MANIFEST.json").read_text())["tasks"][0]["base"]
py = work / "env-sqlglot/bin/python"
out = root / "eval/results/2026-10-27-r2-suite-timing"
out.mkdir(parents=True, exist_ok=True)
env = {k: os.environ[k] for k in ("HOME", "USER", "TMPDIR") if k in os.environ}
env["PATH"] = os.pathsep.join([str(py.parent), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])
rows = []
for label in ("isolated", "planned-replicate-load"):
    prepare_checkout("sqlglot", clone, base)
    start = time.time()
    result = subprocess.run(
        [str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no"],
        cwd=clone,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    elapsed = time.time() - start
    (out / f"{label}.log").write_text(redact(result.stdout + result.stderr, {str(work): "<scratch>"}))
    row = {
        "label": label,
        "base": base,
        "suite_concurrency": 1,
        "replicate_concurrency": 1,
        "pipeline_concurrency": 4,
        "executor_timeout_s": 900,
        "returncode": result.returncode,
        "wall_s": round(elapsed, 3),
        "round1_range_s": [60, 80],
        "over_2x_upper_reference": elapsed > 160,
    }
    rows.append(row)
    (out / "timings.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(row), flush=True)
    if result.returncode or elapsed > 160:
        raise SystemExit("Timing preflight blocked: investigate before any paid execution")
