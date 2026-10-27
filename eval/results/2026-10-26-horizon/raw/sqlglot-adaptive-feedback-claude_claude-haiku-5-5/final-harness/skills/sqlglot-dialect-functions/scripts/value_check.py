#!/usr/bin/env python3
"""Transpile SQL into DuckDB and EXECUTE it, to compare result VALUES with the source engine.

A string match proves nothing about semantics: a transpile can produce valid DuckDB SQL that
returns a different value (e.g. a different default for an omitted date part). This script
runs each transpiled statement in an in-memory DuckDB and prints the result row and types.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/value_check.py \
        --read bigquery "SELECT PARSE_DATETIME('%H:%M', '14:30')" "SELECT ..."

Compare each printed value with the SOURCE engine's documented result for that input
(write the expected value down before running). Exit codes:
  0 = every statement transpiled and executed;
  1 = at least one statement failed to transpile or DuckDB rejected it (message printed);
  2 = bad arguments, or sqlglot not importable from the current directory;
  3 = the `duckdb` python module is not installed. Do not try to install it: fall back to
      the source engine's documentation and state in the final message that values were
      checked against docs, not executed.
"""
import argparse
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="+", help="one or more SQL statements in the source dialect")
    ap.add_argument("--read", required=True, help="source dialect, e.g. bigquery")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    try:
        import sqlglot
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot from {os.getcwd()}: {e}; run from the repo root")
        return 2
    try:
        import duckdb
    except Exception:  # noqa: BLE001
        print("duckdb python module not installed: check values against documentation instead")
        return 3

    con = duckdb.connect(":memory:")
    status = 0
    for sql in args.sql:
        print(f"INPUT:  {sql}")
        try:
            out = sqlglot.transpile(sql, read=args.read, write="duckdb")
        except Exception as e:  # noqa: BLE001
            print(f"  TRANSPILE ERROR: {e}")
            status = 1
            continue
        for stmt in out:
            print(f"  DUCKDB: {stmt}")
            try:
                rel = con.execute(stmt)
                rows = rel.fetchall()
                types = [d[1] for d in rel.description or []]
                print(f"  TYPES:  {types}")
                print(f"  VALUE:  {rows[:5]}")
            except Exception as e:  # noqa: BLE001
                print(f"  REJECTED BY DUCKDB: {e}")
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
