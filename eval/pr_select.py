"""Phase 3C step 1: choose replayable PRs from a repository's history (no LLM calls).

    python eval/pr_select.py humanize --since 2024-06-01 --work <scratch>/pr-work

For every merged, human-authored PR that changes both source and test files, in merge order:

  base     = first parent of the merge commit (main just before the PR landed)
  holdout  = the test-directory files the PR added or modified, as of the merge commit

A PR is kept only if, in a clean checkout, the existing suite passes at base, the holdout fails
at base (it tests new behaviour), passes at the merge commit (the environment works), and the
tests that existed at base still pass against the merged source (the PR does not change pinned
behaviour, which lithify's default test-edit gate would make undeliverable for every strategy). The
oldest ~20% of kept PRs form the development set; the rest are the evaluation set. Output:
eval/prs/<name>/prs.json plus each PR's original title, body and linked issues under source/
(the redacted task texts are written separately, by hand, under tasks/).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repos import REPOS, holdout_paths, prepare_checkout, run_holdout, setup_env, test_env

EVAL = Path(__file__).resolve().parent
BOTS = ("dependabot", "pre-commit-ci", "renovate", "github-actions")


def sh(cmd: list[str], cwd: Path, check: bool = True) -> str:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {p.stderr[-1500:]}")
    return p.stdout


def fetch_prs(slug: str, since: str, limit: int, until: str = "") -> list[dict]:
    q = (f"merged:{since}..{until} " if until else f"merged:>={since} ") + " ".join(f"-author:app/{b}" for b in BOTS)
    out = subprocess.run(
        [
            "gh", "pr", "list", "-R", slug, "--state", "merged", "--search", q, "--limit", str(limit),
            "--json", "number,title,body,mergedAt,mergeCommit,author,closingIssuesReferences,url",
        ],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    prs = json.loads(out)
    return sorted(prs, key=lambda p: p["mergedAt"])


def issue_text(slug: str, refs: list[dict]) -> list[dict]:
    out = []
    for r in refs or []:
        n = r.get("number")
        if not n:
            continue
        p = subprocess.run(
            ["gh", "issue", "view", str(n), "-R", slug, "--json", "number,title,body"], capture_output=True, text=True
        )
        if p.returncode == 0:
            out.append(json.loads(p.stdout))
    return out


def run_suite(cmd: str, cwd: Path, env: dict[str, str]) -> int:
    try:
        return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=env, timeout=900).returncode
    except subprocess.TimeoutExpired:
        return 124


def merge_shards(repo: str, dev_share: float, max_keep: int = 0) -> int:
    """Combine shards in merge order; `max_keep` applies the same cap a single run would have."""
    out_dir = EVAL / "prs" / repo
    kept = sorted(
        (p for f in sorted(out_dir.glob("prs-*.json")) for p in json.loads(f.read_text())["prs"]), key=lambda p: p["merged_at"]
    )
    if max_keep:
        kept = kept[:max_keep]
    n_dev = max(1, round(len(kept) * dev_share)) if kept else 0
    for i, k in enumerate(kept):
        k["split"] = "dev" if i < n_dev else "eval"
    (out_dir / "prs.json").write_text(json.dumps({"repo": repo, "prs": kept}, indent=2) + "\n", encoding="utf-8")
    logs = sorted(out_dir.glob("selection-*.log"))
    (out_dir / "selection.log").write_text("".join(p.read_text() for p in logs), encoding="utf-8")
    print(f"{len(kept)} kept ({n_dev} dev, {len(kept) - n_dev} eval) from {len(logs)} shard(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", choices=sorted(REPOS))
    ap.add_argument("--since", required=True)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--max-src-lines", type=int, default=400, help="skip PRs with larger source diffs")
    ap.add_argument("--work", required=True, help="scratch directory (outside this repository)")
    ap.add_argument("--dev-share", type=float, default=0.2)
    ap.add_argument("--until", default="", help="last merge date (inclusive), for sharding a window")
    ap.add_argument("--tag", default="", help="shard name: own clone, writes prs-<tag>.json; merge with --merge-shards")
    ap.add_argument("--merge-shards", action="store_true", help="combine prs-*.json shards into prs.json and split")
    ap.add_argument("--max-keep", type=int, default=0, help="stop once this many PRs are kept (0 = no limit)")
    a = ap.parse_args(argv)

    spec = REPOS[a.repo]
    work = Path(a.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    mirror = work / f"{a.repo}.git"
    if not mirror.exists():
        sh(["git", "clone", "-q", "--mirror", spec["url"], str(mirror)], work)
    elif not a.tag:  # shards share the mirror: refresh it once, before launching them
        sh(["git", "remote", "update", "--prune"], mirror)
    if a.merge_shards:
        return merge_shards(a.repo, a.dev_share, a.max_keep)
    clone = work / f"{a.repo}-select{'-' + a.tag if a.tag else ''}"
    if clone.exists():
        shutil.rmtree(clone)
    sh(["git", "clone", "-q", str(mirror), str(clone)], work)
    py = setup_env(a.repo, clone, work)

    out_dir = EVAL / "prs" / a.repo
    (out_dir / "source").mkdir(parents=True, exist_ok=True)
    kept: list[dict] = []
    log: list[str] = []
    for pr in fetch_prs(spec["slug"], a.since, a.limit, a.until):
        n, merge = pr["number"], (pr.get("mergeCommit") or {}).get("oid")
        if not merge:
            continue
        try:
            base = sh(["git", "rev-parse", f"{merge}^1"], clone).strip()
        except RuntimeError:
            log.append(f"#{n}: merge commit not in history")
            continue
        names = sh(["git", "diff", "--name-status", base, merge], clone).splitlines()
        rows = [ln.split("\t") for ln in names if ln.strip()]
        tests = holdout_paths(a.repo, rows)
        src = [r[-1] for r in rows if r[-1].endswith(".py") and r[-1] not in tests and not re.search(r"(^|/)tests?/", r[-1])]
        if not tests or not src:
            log.append(f"#{n}: needs both test and source changes (tests={len(tests)}, src={len(src)})")
            continue
        stat = sh(["git", "diff", "--numstat", base, merge, "--", *src], clone)
        src_lines = sum(
            int(x) + int(y) for x, y, _ in (ln.split("\t") for ln in stat.splitlines()) if x.isdigit() and y.isdigit()
        )
        if src_lines > a.max_src_lines:
            log.append(f"#{n}: source diff {src_lines} lines > {a.max_src_lines}")
            continue
        hdir = work / "holdouts" / a.repo / str(n)
        if hdir.exists():
            shutil.rmtree(hdir)
        for p in tests:
            dst = hdir / p
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(subprocess.run(["git", "show", f"{merge}:{p}"], cwd=clone, capture_output=True, check=True).stdout)
        # Cheap holdout checks first; the two full-suite runs only for PRs that survive them.
        suite_rc = old_tests_rc = -1
        prepare_checkout(a.repo, clone, base)
        at_base = run_holdout(a.repo, clone, hdir, py)
        at_merge = -1
        if at_base != 0:
            prepare_checkout(a.repo, clone, merge)
            at_merge = run_holdout(a.repo, clone, hdir, py)
        if at_base != 0 and at_merge == 0:
            # The PR must not contradict tests that existed before it: lithify's default gate fails
            # any edit to existing test lines, so such a PR is undeliverable for every strategy.
            modified = [r[-1] for r in rows if r[0][:1] == "M" and r[-1] in tests]
            if modified:
                sh(["git", "checkout", "-q", base, "--", *modified], clone)
            old_tests_rc = run_suite(spec["test_cmd"].format(py=py), clone, test_env(a.repo))
            if old_tests_rc == 0:
                prepare_checkout(a.repo, clone, base)
                suite_rc = run_suite(spec["test_cmd"].format(py=py), clone, test_env(a.repo))
        verdict = suite_rc == 0 and at_base != 0 and at_merge == 0 and old_tests_rc == 0
        log.append(
            f"#{n}: suite@base={suite_rc} holdout@base={at_base} holdout@merge={at_merge} "
            f"old-tests@merge={old_tests_rc} -> " + ("keep" if verdict else "drop")
        )
        if not verdict:
            continue
        issues = issue_text(spec["slug"], pr.get("closingIssuesReferences") or [])
        (out_dir / "source" / f"{n}.md").write_text(
            f"# PR #{n}: {pr['title']}\n\n{pr['url']}\n\n## PR body\n\n{pr.get('body') or '(empty)'}\n"
            + "".join(f"\n## Issue #{i['number']}: {i['title']}\n\n{i.get('body') or '(empty)'}\n" for i in issues),
            encoding="utf-8",
        )
        kept.append(
            {
                "number": n,
                "title": pr["title"],
                "merged_at": pr["mergedAt"],
                "merge": merge,
                "base": base,
                "holdout": tests,
                "src_files": src,
                "src_lines": src_lines,
                "issues": [i["number"] for i in issues],
            }
        )
        print(f"kept #{n} ({len(kept)})", flush=True)
        if a.max_keep and len(kept) >= a.max_keep:
            break
    if a.tag:
        (out_dir / f"prs-{a.tag}.json").write_text(
            json.dumps({"repo": a.repo, "since": a.since, "until": a.until, "prs": kept}, indent=2) + "\n", encoding="utf-8"
        )
        (out_dir / f"selection-{a.tag}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
        print(f"{len(kept)} kept in shard {a.tag}")
        return 0
    n_dev = max(1, round(len(kept) * a.dev_share)) if kept else 0
    for i, k in enumerate(kept):
        k["split"] = "dev" if i < n_dev else "eval"
    (out_dir / "prs.json").write_text(
        json.dumps({"repo": a.repo, "since": a.since, "prs": kept}, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "selection.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"{len(kept)} kept ({n_dev} dev, {len(kept) - n_dev} eval); log in {out_dir / 'selection.log'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
