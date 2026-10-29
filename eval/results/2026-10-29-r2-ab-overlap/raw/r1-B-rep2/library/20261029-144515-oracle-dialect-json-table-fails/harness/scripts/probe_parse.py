"""Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output changes when transpiled again; the next line shows both

Exits 0 if every statement is OK, 1 if any statement is ERR or UNSTABLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
  <python> -I .lithify/harness/scripts/probe_parse.py --read oracle < variants.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Probe SQL statements read from stdin.")
    parser.add_argument("--read", default=None, help="input dialect, e.g. oracle")
    parser.add_argument("--write", default=None, help="output dialect; defaults to --read")
    args = parser.parse_args(argv)
    write = args.write or args.read

    count = 0
    failed = False
    for line in sys.stdin:
        sql = line.strip()
        if not sql or sql.startswith("--"):
            continue
        count += 1
        status, detail = probe(sql, args.read, write)
        if status != "OK":
            failed = True
        print(f"{status:9} {sql}")
        print(f"          {detail}")

    if count == 0:
        print("no statements on stdin", file=sys.stderr)
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
