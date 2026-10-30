"""Phase 0b task-12 causal test: 4 harness arms x 5 replicates on PR #7549 (see TASK12_PLAN.md).

Arms: c_skill (primary), d_placebo (control), a_full and b_minus (secondary, approximate).
Replicates are interleaved (all four arms at replicate 1, then replicate 2, ...), so a budget stop
affects every arm equally. Every run is one `pr_replay.py --only 7549 --strategy baseline` invocation with
--harness-dir set to the arm directory, under the same executor, CLI pin and work directory as A2-A5.

    eval/round2/run_task12.py --product-commit <full sha of the installed build>

Requires the arm manifest built outside the repository (MANIFEST.json, with hashes) and the scratch venv that
has lithify installed non-editably from that commit.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRATCH = Path("/Users/donovan/.cache/lithify-dev")
ROOT = Path(__file__).resolve().parents[2]
ARMS = ["c_skill", "d_placebo", "a_full", "b_minus"]
REPLICATES = 5
PR = "7549"
PER_RUN_LIMIT = 1.0
TOTAL_CAP = 5.0
CLI_VERSION = "2.1.310"
EXPERIMENT = "r2-task12"
OUT = ROOT / "eval/results/2026-10-30-r2-task12"
WORK = SCRATCH / "r2-noise-scratch"
PYTHON = SCRATCH / "r2-task12-venv/bin/python"
HARNESS = SCRATCH / "r2-task12-harness"


def check_inputs(product_commit: str) -> dict:
    manifest = json.loads((HARNESS / "MANIFEST.json").read_text(encoding="utf-8"))
    for arm in ARMS:
        assert manifest[arm]["errors"] == [], f"arm {arm} fails validation"
        now = subprocess.run(
            [
                str(PYTHON),
                "-c",
                "import sys;from pathlib import Path;from lithify.harness import harness_hash;"
                "print(harness_hash(Path(sys.argv[1])))",
                manifest[arm]["path"],
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert now == manifest[arm]["sha256"], f"arm {arm} changed since the manifest was written"
    env = clean_env()
    version = subprocess.run(["claude", "--version"], env=env, capture_output=True, text=True, check=True).stdout
    assert version.startswith(f"{CLI_VERSION} "), f"pinned CLI is {version.strip()!r}, expected {CLI_VERSION}"
    installed = subprocess.run(
        [str(PYTHON), "-c", "import lithify,json;print(json.dumps(lithify.__file__))"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "r2-task12-venv" in installed, installed
    assert len(product_commit) == 40, "pass the full commit sha"
    return manifest


def clean_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in ("HOME", "USER", "TMPDIR") if k in os.environ}
    env["DISABLE_AUTOUPDATER"] = "1"
    env["PATH"] = os.pathsep.join(
        [
            str(WORK / "claude-2.1.310/node_modules/.bin"),
            str(WORK / "env-sqlglot/bin"),
            str(WORK / "runtime-node24/node_modules/.bin"),
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
    )
    return env


def run_one(arm: str, replicate: int, manifest: dict, product_commit: str) -> int:
    label = f"task12-{arm}-r{replicate}"
    command = [
        str(PYTHON),
        str(ROOT / "eval/pr_replay.py"),
        "sqlglot",
        "--strategy",
        "baseline",
        "--split",
        "eval",
        "--only",
        PR,
        "--executor",
        "claude@claude-haiku-5-5",
        "--roles",
        "claude",
        "--timeout",
        "900",
        "--concurrency",
        "4",
        "--limit-usd",
        str(PER_RUN_LIMIT),
        "--total-cap",
        str(TOTAL_CAP),
        "--budget-glob",
        "*-r2-task12*",
        "--work",
        str(WORK),
        "--out",
        str(OUT),
        "--experiment",
        f"{EXPERIMENT}-{arm}",
        "--label",
        label,
        "--replicate",
        label,
        "--seed-label",
        str(replicate),
        "--arm",
        arm,
        "--product-commit",
        product_commit,
        "--harness-dir",
        manifest[arm]["path"],
    ]
    proc = subprocess.run(command, cwd=ROOT, env=clean_env(), capture_output=True, text=True)
    (OUT / f"console-{label}.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--product-commit", required=True)
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    manifest = check_inputs(a.product_commit)
    if a.check_only:
        print(json.dumps({k: v["sha256"] for k, v in manifest.items()}, indent=2))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    status = []
    for replicate in range(1, REPLICATES + 1):
        for arm in ARMS:
            code = run_one(arm, replicate, manifest, a.product_commit)
            status.append({"arm": arm, "replicate": replicate, "exit": code})
            print(f"{arm} r{replicate}: exit {code}", flush=True)
            (OUT / "STATUS.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
            if code != 0:
                # a nonzero exit is a budget stop or a crash; stop and report rather than continue silently
                return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
