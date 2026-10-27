#!/usr/bin/env python3
"""Show what a SQL string parses into, how it round-trips, and how it transpiles.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py \
        --read clickhouse --write duckdb,mysql,postgres "SELECT groupConcat(', ')(x) FROM t"

Output per statement: the expression class of every projection (and the full repr
with --repr), the round-trip in the read dialect (flagged if it differs from input),
and the generated SQL for each --write dialect.
Exit codes: 0 = parsed; 1 = parse error (message printed); 2 = bad arguments
or sqlglot not importable from the current directory.
"""
import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="+", help="one or more SQL strings")
    ap.add_argument("--read", required=True, help="source dialect, e.g. clickhouse")
    ap.add_argument("--write", default="", help="comma-separated target dialects")
    ap.add_argument("--repr", action="store_true", help="print full AST repr")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    try:
        import sqlglot
        from sqlglot import exp
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot from {os.getcwd()}: {e}", file=sys.stderr)
        return 2

    targets = [d.strip() for d in args.write.split(",") if d.strip()]
    status = 0
    for sql in args.sql:
        print(f"== {sql}")
        try:
            tree = sqlglot.parse_one(sql, read=args.read)
        except Exception as e:  # noqa: BLE001
            print(f"  PARSE ERROR: {e}")
            status = 1
            continue
        nodes = tree.selects if isinstance(tree, exp.Query) and tree.selects else [tree]
        for node in nodes:
            inner = node.this if isinstance(node, exp.Alias) else node
            generic = isinstance(
                inner, (exp.Anonymous, exp.AnonymousAggFunc, exp.ParameterizedAgg)
            ) or type(inner).__name__.startswith("Combined")
            tag = "  <-- GENERIC node: is there a typed exp class for this function?" if generic else ""
            print(f"  node: {type(inner).__name__}{tag}")
            if args.repr:
                print("  " + repr(inner).replace("\n", "\n  "))
        rt = tree.sql(args.read)
        print(f"  {args.read} (round-trip){'' if rt == sql else '  [DIFFERS]'}: {rt}")
        for d in targets:
            try:
                print(f"  {d}: {tree.sql(d, unsupported_level=sqlglot.ErrorLevel.WARN)}")
            except Exception as e:  # noqa: BLE001
                print(f"  {d}: GENERATE ERROR: {e}")
    return status


if __name__ == "__main__":
    sys.exit(main())
