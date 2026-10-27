#!/usr/bin/env python3
"""Check that two spellings of one statement parse to the SAME AST, over many slot values.

Use it when a task makes a clause legal in a second position (properties before the
column list, options before/after a name, ...). A single example pair passing proves
little: the new position is usually next to a delimiter such as `(`, and only some
value kinds in front of that delimiter get swallowed (e.g. `KEY=ident (cols)` read as
a function call `ident(cols)`), so every value kind must be tried.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-ddl-statements/scripts/form_equiv.py --read snowflake \
        "CREATE TABLE t K={V} (id INT) => CREATE TABLE t (id INT) K={V}" \
        "CREATE DYNAMIC TABLE d K={V} W={V} (id) AS SELECT 1 => CREATE DYNAMIC TABLE d (id) K={V} W={V} AS SELECT 1"

Each PAIR is "NEW_FORM => ALREADY_SUPPORTED_FORM". Every `{V}` in a pair is replaced by
each value from --values (default: a boolean, a number, a string, a bare identifier,
a dotted name, a function call), one value per run of the pair.
Per expanded pair it prints one of:
  [SAME]         both parse and the ASTs are equal (round-trip of the new form shown)
  [AST DIFFERS]  both parse but the trees differ; both round-trips are printed
  [PARSE ERROR]  one side fails to parse (the side and message are printed)
If the ALREADY_SUPPORTED_FORM itself fails, the pair is a bad reference, not a fix defect.
Exit codes: 0 = all SAME; 1 = at least one AST DIFFERS / PARSE ERROR;
2 = bad arguments or sqlglot not importable from the current directory.
"""
import argparse
import os
import sys

DEFAULT_VALUES = "TRUE|1|'str'|my_wh|db.sch.obj|f(1)"


def expand(pair: str, values: list[str]) -> list[tuple[str, str]]:
    if "=>" not in pair:
        raise ValueError(f"pair has no '=>': {pair!r}")
    left, right = (s.strip() for s in pair.split("=>", 1))
    if "{V}" not in pair:
        return [(left, right)]
    return [(left.replace("{V}", v), right.replace("{V}", v)) for v in values]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+", help='"NEW_FORM => ALREADY_SUPPORTED_FORM"')
    ap.add_argument("--read", required=True, help="dialect, e.g. snowflake")
    ap.add_argument("--values", default=DEFAULT_VALUES, help="'|'-separated values for {V}")
    args = ap.parse_args()

    values = [v.strip() for v in args.values.split("|") if v.strip()]
    try:
        cases = [c for p in args.pairs for c in expand(p, values)]
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2

    sys.path.insert(0, os.getcwd())
    try:
        import sqlglot
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot from {os.getcwd()}: {e}", file=sys.stderr)
        return 2

    status = 0
    counts = {"SAME": 0, "AST DIFFERS": 0, "PARSE ERROR": 0}
    for left, right in cases:
        trees = []
        for side, sql in (("new", left), ("reference", right)):
            try:
                trees.append(sqlglot.parse_one(sql, read=args.read))
            except Exception as e:  # noqa: BLE001
                print(f"[PARSE ERROR] {side} form: {sql}\n    {str(e).splitlines()[0]}")
                break
        if len(trees) < 2:
            counts["PARSE ERROR"] += 1
            status = 1
            continue
        new, ref = trees
        if new == ref:
            counts["SAME"] += 1
            print(f"[SAME] {left}\n    -> {new.sql(args.read)}")
        else:
            counts["AST DIFFERS"] += 1
            status = 1
            print(f"[AST DIFFERS] {left}")
            print(f"    new       -> {new.sql(args.read)}")
            print(f"    reference -> {ref.sql(args.read)}")
    print("SUMMARY: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    return status


if __name__ == "__main__":
    sys.exit(main())
