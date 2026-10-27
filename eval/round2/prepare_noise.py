"""Rebuild frozen Phase-0 inputs without selecting tasks or calling an agent."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repos import REPOS, setup_env


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    work = Path(sys.argv[1]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    mirror = work / "sqlglot.git"
    if not mirror.exists():
        subprocess.run(["git", "clone", "--mirror", REPOS["sqlglot"]["url"], str(mirror)], check=True)
    prs_file = root / "eval/prs/sqlglot/prs.json"
    prs = [p for p in json.loads(prs_file.read_text())["prs"] if p["split"] == "eval"][:60]
    assert len(prs) == 60
    manifest = {"prs_sha256": hashlib.sha256(prs_file.read_bytes()).hexdigest(), "tasks": []}
    for position, pr in enumerate(prs, 1):
        task = root / f"eval/prs/sqlglot/tasks/{pr['number']}.md"
        manifest["tasks"].append(
            {
                "position": position,
                "number": pr["number"],
                "base": pr["base"],
                "merge": pr["merge"],
                "task_sha256": hashlib.sha256(task.read_bytes()).hexdigest(),
            }
        )
        for name in pr["holdout"]:
            data = subprocess.run(["git", "show", f"{pr['merge']}:{name}"], cwd=mirror, capture_output=True, check=True).stdout
            target = work / "holdouts/sqlglot" / str(pr["number"]) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    (root / "eval/round2/INPUT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    checkout = work / "sqlglot-env-setup"
    if not checkout.exists():
        subprocess.run(["git", "clone", str(mirror), str(checkout)], check=True)
    subprocess.run(["git", "checkout", "--detach", prs[0]["base"]], cwd=checkout, check=True)
    print(setup_env("sqlglot", checkout, work))


if __name__ == "__main__":
    main()
