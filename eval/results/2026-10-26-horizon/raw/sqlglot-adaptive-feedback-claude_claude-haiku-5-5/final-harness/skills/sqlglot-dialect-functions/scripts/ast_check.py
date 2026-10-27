#!/usr/bin/env python3
"""Show what a SQL string parses into, how it round-trips, and how it transpiles.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py \
        --read clickhouse --write duckdb,mysql,postgres "SELECT groupConcat(', ')(x) FROM t"

Output per statement: the expression class of every projection (and the full repr
with --repr), the round-trip in the read dialect, and the generated SQL for each
--write dialect. The round-trip is compared with the input ignoring case and
whitespace (and a trailing ';'), so lowercase input is not flagged:
  [DIFFERS]          the round-trip text changed (quoting, defaults filled in, ...);
                     read it and decide whether the change is a harmless normalisation.
  [FUNCTION CHANGED] a function called in the input (e.g. DATE_SUB) is missing from
                     the round-trip. The user's spelling was rewritten into another
                     function; that is a failed round-trip, not a normalisation.
  [WORDS DROPPED]    a keyword/identifier in the input (outside string literals) is
                     missing from the round-trip, e.g. `ON OVERFLOW ERROR` silently
                     dropped. Defaults that are routinely elided (ASC, AS, INNER,
                     OUTER, ALL) are ignored. A dropped clause is a failed round-trip.
Each --write line is tagged [UNSUPPORTED: <message>] when generating it with
unsupported_level=RAISE raises UnsupportedError (what a test's write={d: UnsupportedError}
asserts). An untagged line means that target claims to express the construct.
Exit codes: 0 = parsed, nothing changed or dropped; 1 = parse error (message printed);
2 = bad arguments or sqlglot not importable from the current directory;
4 = parsed, but at least one statement has FUNCTION CHANGED or WORDS DROPPED.
"""
import argparse
import os
import re
import sys
from collections import Counter

_CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_WORD = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_STRING = re.compile(r"'(?:[^']|'')*'")
_ELIDED = {"ASC", "AS", "INNER", "OUTER", "ALL"}


def _norm(sql: str) -> str:
    return " ".join(sql.upper().split()).rstrip(";").rstrip()


def _calls(sql: str) -> Counter:
    return Counter(m.group(1).upper() for m in _CALL.finditer(sql))


def _words(sql: str) -> Counter:
    return Counter(
        w.upper() for w in _WORD.findall(_STRING.sub(" ", sql)) if w.upper() not in _ELIDED
    )


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
        lost = sorted((_calls(sql) - _calls(rt)).keys())
        flag = "" if _norm(rt) == _norm(sql) else "  [DIFFERS]"
        if lost:
            flag += f"  [FUNCTION CHANGED: {', '.join(lost)} missing]"
            status = status or 4
        dropped = sorted((_words(sql) - _words(rt) - _calls(sql)).keys())
        if dropped:
            flag += f"  [WORDS DROPPED: {', '.join(dropped)}]"
            status = status or 4
        print(f"  {args.read} (round-trip){flag}: {rt}")
        for d in targets:
            try:
                out = tree.sql(d, unsupported_level=sqlglot.ErrorLevel.IGNORE)
            except Exception as e:  # noqa: BLE001
                print(f"  {d}: GENERATE ERROR: {e}")
                continue
            # Same check the tests' validate_all uses for an expected UnsupportedError.
            try:
                tree.sql(d, unsupported_level=sqlglot.ErrorLevel.RAISE)
                tag = ""
            except sqlglot.errors.UnsupportedError as e:
                tag = f"  [UNSUPPORTED: {' '.join(str(e).split())}]"
            except Exception:  # noqa: BLE001
                tag = ""
            print(f"  {d}{tag}: {out}")
    return status


if __name__ == "__main__":
    sys.exit(main())
