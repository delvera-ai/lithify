#!/usr/bin/env python3
"""Parse SQL once and generate it in EVERY sqlglot dialect, flagging silently dropped keywords.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-data-types/scripts/all_dialects.py \
        --read postgres --keep COLLATE "SELECT CAST(x AS VARCHAR(10) COLLATE \"C\")"

For each SQL string: the read-dialect round-trip, then one line per dialect with the generated
SQL and flags:
  [DROPPED: KW]      a --keep keyword occurs fewer times in the output than in the input and the
                     generator did NOT report it as unsupported: the new arg is lost silently.
  [UNSUPPORTED: ..]  the generator called self.unsupported(); the drop is reported, not silent.
  [REPARSE ERROR]    the output does not parse back in that same dialect.
  GENERATE ERROR     generation raised.
Exit codes: 0 = no silent drops, no generate errors; 1 = input failed to parse;
2 = bad arguments or sqlglot not importable from the current directory;
4 = at least one DROPPED or GENERATE ERROR line (read them; each needs a decision).
"""
import argparse
import os
import re
import sys


def _count(word: str, sql: str) -> int:
    return len(re.findall(rf"\b{re.escape(word)}\b", sql, flags=re.IGNORECASE))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="+", help="one or more SQL strings")
    ap.add_argument("--read", required=True, help="source dialect, e.g. postgres")
    ap.add_argument("--keep", action="append", default=[], help="keyword that must survive (repeatable)")
    ap.add_argument("--only", default="", help="comma-separated subset of target dialects")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    try:
        import sqlglot
        from sqlglot.dialects.dialect import Dialects
        from sqlglot.errors import ErrorLevel, UnsupportedError
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot from {os.getcwd()}: {e}", file=sys.stderr)
        return 2

    if args.only:
        targets = [d.strip() for d in args.only.split(",") if d.strip()]
    else:
        targets = sorted(d.value for d in Dialects if d.value)

    status = 0
    for sql in args.sql:
        print(f"== {sql}")
        try:
            tree = sqlglot.parse_one(sql, read=args.read)
        except Exception as e:  # noqa: BLE001
            print(f"  PARSE ERROR ({args.read}): {e}")
            status = 1
            continue
        print(f"  {args.read} (round-trip): {tree.sql(args.read)}")
        drops = 0
        for d in targets:
            flags = []
            try:
                try:
                    out = tree.sql(d, unsupported_level=ErrorLevel.RAISE)
                except UnsupportedError as e:
                    out = tree.sql(d, unsupported_level=ErrorLevel.IGNORE)
                    flags.append(f"[UNSUPPORTED: {str(e).splitlines()[0][:80]}]")
            except Exception as e:  # noqa: BLE001
                print(f"  {d}: GENERATE ERROR: {e}")
                status = status or 4
                drops += 1
                continue
            for kw in args.keep:
                if _count(kw, out) < _count(kw, sql) and not any(f.startswith("[UNSUP") for f in flags):
                    flags.append(f"[DROPPED: {kw.upper()}]")
                    status = status or 4
                    drops += 1
            try:
                sqlglot.parse_one(out, read=d)
            except Exception:  # noqa: BLE001
                flags.append("[REPARSE ERROR]")
            print(f"  {d}: {out}" + ("  " + " ".join(flags) if flags else ""))
        print(f"  -- {drops} silent drop/error line(s) across {len(targets)} dialects")
    return status


if __name__ == "__main__":
    sys.exit(main())
