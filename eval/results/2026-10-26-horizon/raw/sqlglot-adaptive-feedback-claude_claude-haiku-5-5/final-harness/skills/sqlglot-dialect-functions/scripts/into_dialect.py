#!/usr/bin/env python3
"""Read the TARGET dialect's own SQL under EVERY other dialect and write it back to the target.

A hand-picked probe ("Postgres @> -> StarRocks") checks only the source spellings you thought
of. Other dialects may parse the very same text (e.g. a function named like the target's) into
a DIFFERENT expression class (an inverse/argument-swapped operator, a generic node, ...) that
the target generator still emits in a foreign form. This script finds those paths.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/into_dialect.py \
        --write starrocks "SELECT ARRAY_CONTAINS_ALL([1, 2, 3], [1, 2])" "SELECT MAX_BY(a, b) FROM t"

Pass the target-native spelling of EVERY construct the task names (with literal arguments, and
with column arguments). For each SQL string: the target round-trip, then one line per other
dialect that parses it:
  [DIFFERS]       reading it in that dialect and writing the target gives something other
                  than the target's own round-trip. The node classes are printed. Decide per
                  line: either the source dialect documents a DIFFERENT meaning for that text
                  (say which, from its docs), or the target generator is missing a mapping
                  for that node class: fix it.
  (no parse)      that dialect cannot parse the text; ignored.
  GENERATE ERROR  generation raised.
Exit codes: 0 = no DIFFERS / errors; 1 = the SQL does not parse in the target dialect;
2 = bad arguments or sqlglot not importable from the current directory;
4 = at least one DIFFERS or GENERATE ERROR line (each needs a decision; see above).
"""
import argparse
import os
import sys


def _norm(sql: str) -> str:
    return " ".join(sql.upper().split()).rstrip(";").rstrip()


def _classes(tree, exp) -> str:
    names = [type(n).__name__ for n in tree.find_all(exp.Func, exp.Binary)]
    return ",".join(dict.fromkeys(names)) or type(tree).__name__


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="+", help="one or more SQL strings in the TARGET dialect")
    ap.add_argument("--write", required=True, help="target dialect, e.g. starrocks")
    ap.add_argument("--only", default="", help="comma-separated subset of source dialects")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    try:
        import sqlglot
        from sqlglot import exp
        from sqlglot.dialects.dialect import Dialects
        from sqlglot.errors import ErrorLevel
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot from {os.getcwd()}: {e}", file=sys.stderr)
        return 2

    if args.only:
        sources = [d.strip() for d in args.only.split(",") if d.strip()]
    else:
        sources = sorted(d.value for d in Dialects if d.value and d.value != args.write)

    status = 0
    for sql in args.sql:
        print(f"== {sql}")
        try:
            own = sqlglot.parse_one(sql, read=args.write)
        except Exception as e:  # noqa: BLE001
            print(f"  PARSE ERROR ({args.write}): {e}")
            status = 1
            continue
        expected = own.sql(args.write)
        print(f"  {args.write} (round-trip) [{_classes(own, exp)}]: {expected}")
        bad = parsed = 0
        for d in sources:
            try:
                tree = sqlglot.parse_one(sql, read=d)
            except Exception:  # noqa: BLE001
                print(f"  {d}: (no parse)")
                continue
            parsed += 1
            try:
                out = tree.sql(args.write, unsupported_level=ErrorLevel.IGNORE)
            except Exception as e:  # noqa: BLE001
                print(f"  {d}: GENERATE ERROR: {e}")
                bad += 1
                continue
            if _norm(out) == _norm(expected):
                print(f"  {d}: ok")
            else:
                print(f"  {d}: [DIFFERS] [{_classes(tree, exp)}] -> {out}")
                bad += 1
        print(f"  -- {bad} DIFFERS/error line(s) among {parsed} dialects that parse it")
        if bad:
            status = status or 4
    return status


if __name__ == "__main__":
    sys.exit(main())
