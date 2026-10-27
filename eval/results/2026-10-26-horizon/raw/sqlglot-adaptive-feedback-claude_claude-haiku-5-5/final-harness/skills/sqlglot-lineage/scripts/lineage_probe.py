#!/usr/bin/env python3
"""Probe sqlglot lineage() for a matrix of queries and flag suspicious results.

Usage (from the repository root, with the project's python from memory.md):
    PYTHONPATH=. <python> .lithify/harness/skills/sqlglot-lineage/scripts/lineage_probe.py \
        --dialect snowflake --schema '{"sales": {"id": "int", "jan": "int", "feb": "int"}}' \
        --sql "SELECT id, m, s FROM sales UNPIVOT (s FOR m IN (jan, feb)) AS u(i, m2, s2)" \
        --sql "..."            # repeat --sql for every row of the probe matrix
    Optional: --columns a,b    # output columns to trace (default: every outer named select)

For every (query, output column) it prints the lineage tree and flags:
    [ERROR]    lineage() raised.
    [WARNING]  sqlglot logged a warning (e.g. "Unknown subquery scope") while tracing.
    [PHANTOM]  a node "T.C" whose column C does not exist in its source: not in the schema of
               table T, or not among the named selects of the subquery/CTE it points at.
               A phantom node means lineage followed a name that the source never had
               (typically an output alias treated as a source column).
Flags are evidence of a bug, not proof that unflagged trees are right: still compare each
tree with the semantics you expect.

Exit codes: 0 = nothing flagged; 1 = at least one flag; 2 = sqlglot not importable / bad args.
"""
import argparse
import json
import logging
import sys


class _Collect(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


def _strip(name):
    return name.strip().strip('"`[]').lower()


def _schema_columns(schema, table):
    """Find the column set of `table` anywhere in a (possibly nested) schema dict."""
    found = None
    stack = [schema]
    while stack:
        d = stack.pop()
        for k, v in d.items():
            if isinstance(v, dict):
                if v and all(not isinstance(x, dict) for x in v.values()):
                    if _strip(k) == table:
                        found = {_strip(c) for c in v}
                else:
                    stack.append(v)
    return found


def _phantom(node, schema, exp):
    if "." not in node.name:
        return None
    col = _strip(node.name.rsplit(".", 1)[1])
    src = node.source
    if isinstance(src, exp.Table):
        cols = _schema_columns(schema, _strip(src.name)) if schema else None
        if cols is not None and col not in cols:
            return f"column {col!r} not in schema of table {src.name!r}"
    elif isinstance(src, exp.Query):
        names = [_strip(n) for n in src.named_selects]
        if names and "*" not in names and not src.find(exp.Star) and col not in names:
            return f"column {col!r} not among source selects {names}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", action="append", required=True)
    ap.add_argument("--dialect", default=None)
    ap.add_argument("--schema", default=None, help="JSON schema dict")
    ap.add_argument("--columns", default=None, help="comma-separated output columns")
    args = ap.parse_args()

    try:
        import sqlglot
        from sqlglot import exp
        from sqlglot.lineage import lineage
    except Exception as e:  # noqa: BLE001
        print(f"cannot import sqlglot ({e}); run from the repo root with PYTHONPATH=.")
        return 2

    try:
        schema = json.loads(args.schema) if args.schema else None
    except json.JSONDecodeError as e:
        print(f"--schema is not valid JSON: {e}")
        return 2

    handler = _Collect()
    root_logger = logging.getLogger("sqlglot")
    root_logger.addHandler(handler)
    root_logger.propagate = False

    flagged = 0
    for sql in args.sql:
        print(f"== {sql.strip()}")
        if args.columns:
            columns = [c.strip() for c in args.columns.split(",") if c.strip()]
        else:
            try:
                columns = sqlglot.parse_one(sql, read=args.dialect).named_selects
            except Exception as e:  # noqa: BLE001
                print(f"  [ERROR] parse: {type(e).__name__}: {e}")
                flagged += 1
                continue
            if not columns or "*" in columns:
                print("  (outer SELECT is * or empty; pass --columns)")
                continue
        for column in columns:
            handler.records.clear()
            try:
                node = lineage(column, sql, schema=schema, dialect=args.dialect)
            except Exception as e:  # noqa: BLE001
                print(f"  {column}: [ERROR] {type(e).__name__}: {e}")
                flagged += 1
                continue
            lines = []

            def walk(n, depth):
                nonlocal flagged
                note = _phantom(n, schema, exp) if depth else None
                tag = f"   [PHANTOM] {note}" if note else ""
                if note:
                    flagged += 1
                lines.append("  " * (depth + 1) + n.name + tag)
                for d in n.downstream:
                    walk(d, depth + 1)

            walk(node, 0)
            print("\n".join(lines))
            for msg in handler.records:
                print(f"    [WARNING] {msg[:200]}")
                flagged += 1

    print(f"FLAGS: {flagged}")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
