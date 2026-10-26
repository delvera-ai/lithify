"""Per-repository settings and helpers shared by pr_select.py and pr_replay.py.

Environments live in a scratch directory outside this repository. They hold the repository's
dependencies but NOT the package itself, so tests always import the code in the checkout they
run in (a probe worktree, not some installed copy). Packages that import a gitignored,
build-generated version module get a stub written (and, in replay, committed) at every base.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

VERSION_STUB = '__version__ = version = "0.0.0+eval"\n__version_tuple__ = version_tuple = (0, 0, 0, "eval")\n'

REPOS: dict[str, dict] = {
    "humanize": {
        "slug": "python-humanize/humanize",
        "url": "https://github.com/python-humanize/humanize",
        "package": "humanize",
        "pythonpath": "src",
        "version_file": "src/humanize/_version.py",
        "extras": ["tests"],
        "groups": [],
    },
    "tenacity": {
        "slug": "jd/tenacity",
        "url": "https://github.com/jd/tenacity",
        "package": "tenacity",
        "pythonpath": "",
        "version_file": "tenacity/_version.py",
        "extras": ["test"],
        "groups": [],
        # Test deps of older bases in the replay window (setup.cfg era).
        "extra_deps": ["typeguard", "tornado>=4.5"],
    },
    "sqlglot": {
        "slug": "tobymao/sqlglot",
        "url": "https://github.com/tobymao/sqlglot",
        "package": "sqlglot",
        "pythonpath": "",
        "version_file": "sqlglot/_version.py",
        "extras": ["dev"],
        "groups": [],
    },
    "marshmallow": {
        "slug": "marshmallow-code/marshmallow",
        "url": "https://github.com/marshmallow-code/marshmallow",
        "package": "marshmallow",
        "pythonpath": "src",
        "version_file": "",
        "extras": [],
        "groups": ["tests"],
    },
    "platformdirs": {
        "slug": "tox-dev/platformdirs",
        "url": "https://github.com/tox-dev/platformdirs",
        "package": "platformdirs",
        "pythonpath": "src",
        "version_file": "src/platformdirs/version.py",
        "extras": [],
        "groups": ["test"],
    },
}
for _spec in REPOS.values():
    _pp = f"PYTHONPATH={_spec['pythonpath']} " if _spec["pythonpath"] else ""
    _spec["test_cmd"] = _pp + "{py} -m pytest -q -p no:cacheprovider --color=no"

TEST_DIR = re.compile(r"(^|/)tests?/")


def holdout_paths(repo: str, name_status: list[list[str]]) -> list[str]:
    """Test-directory files the PR added or modified (renames count as their new path)."""
    out = []
    for row in name_status:
        st, path = row[0][:1], row[-1]
        if st in ("A", "M", "R", "C") and TEST_DIR.search(path):
            out.append(path)
    return sorted(set(out))


def _group_reqs(pyproject: dict, group: str, seen: set[str] | None = None) -> list[str]:
    seen = seen or set()
    if group in seen:
        return []
    seen.add(group)
    out: list[str] = []
    for item in pyproject.get("dependency-groups", {}).get(group, []):
        if isinstance(item, dict) and "include-group" in item:
            out += _group_reqs(pyproject, item["include-group"], seen)
        elif isinstance(item, str):
            out.append(item)
    return out


def setup_env(repo: str, checkout: Path, work: Path) -> str:
    """Create (once) a venv with the repository's runtime + test dependencies; return its python."""
    spec = REPOS[repo]
    env = work / f"env-{repo}"
    py = env / "bin" / "python"
    if py.exists():
        return str(py)
    subprocess.run(["uv", "venv", "-q", "-p", "3.12", str(env)], check=True)
    extras = f"[{','.join(spec['extras'])}]" if spec["extras"] else ""
    subprocess.run(["uv", "pip", "install", "-q", "-p", str(py), f"{checkout}{extras}", "pytest"], check=True)
    pyproject = tomllib.loads((checkout / "pyproject.toml").read_text(encoding="utf-8"))
    reqs = [r for g in spec["groups"] for r in _group_reqs(pyproject, g)] + spec.get("extra_deps", [])
    if reqs:
        subprocess.run(["uv", "pip", "install", "-q", "-p", str(py), *reqs], check=True)
    # The package itself must come from whichever checkout the tests run in.
    subprocess.run(["uv", "pip", "uninstall", "-q", "-p", str(py), spec["package"]], check=True)
    return str(py)


def write_version_stub(repo: str, checkout: Path) -> str:
    vf = REPOS[repo]["version_file"]
    if vf:
        p = checkout / vf
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(VERSION_STUB, encoding="utf-8")
    return vf


def prepare_checkout(repo: str, checkout: Path, ref: str) -> None:
    subprocess.run(["git", "checkout", "-q", "-f", ref], cwd=checkout, check=True)
    subprocess.run(["git", "clean", "-qfdx", "-e", ".venv"], cwd=checkout, check=True)
    write_version_stub(repo, checkout)


def test_env(repo: str) -> dict[str, str]:
    env = dict(os.environ)
    for k in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
        env.pop(k, None)
    if REPOS[repo]["pythonpath"]:
        env["PYTHONPATH"] = REPOS[repo]["pythonpath"]
    return env


def run_holdout(repo: str, checkout: Path, hdir: Path, py: str, log: Path | None = None) -> int:
    """Copy the holdout files in, run the test files among them, restore the checkout. Returns pytest's exit code."""
    files = sorted(p.relative_to(hdir) for p in hdir.rglob("*") if p.is_file())
    backup = hdir.parent / f".{hdir.name}-backup"
    if backup.exists():
        shutil.rmtree(backup)
    created: list[Path] = []
    try:
        for rel in files:
            dst = checkout / rel
            if dst.exists():
                (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup / rel)
            else:
                created.append(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(hdir / rel, dst)
        tests = [str(r) for r in files if r.suffix == ".py" and (r.name.startswith("test_") or r.name.endswith("_test.py"))]
        if not tests:
            return 5
        try:
            p = subprocess.run(
                [py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no", *tests],
                cwd=checkout,
                env=test_env(repo),
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            if log is not None:
                log.write_text("exit 124\nholdout timed out after 600s\n", encoding="utf-8")
            return 124
        if log is not None:
            log.write_text(f"exit {p.returncode}\n{p.stdout[-6000:]}{p.stderr[-2000:]}", encoding="utf-8")
        return p.returncode
    finally:
        for rel in files:
            b = backup / rel
            if b.exists():
                shutil.copy2(b, checkout / rel)
        for c in created:
            c.unlink(missing_ok=True)
        shutil.rmtree(backup, ignore_errors=True)
