# trajectory base-1

final message:
Exasol `LISTAGG` now keeps the separator as the separator, so `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` parses with `x` as the value and `','` as the separator, and round-trips. The full suite passes (1126 tests).

**Cause:** `sqlglot/parsers/exasol.py` mapped `LISTAGG` to the same handler as `GROUP_CONCAT`. That handler folds the extra argument into a `CONCAT`, which is where the separator was lost.

**Fix:** `LISTAGG` now uses `_parse_string_agg()`, the same path Oracle, Snowflake and Trino use. `GROUP_CONCAT` keeps its own handler, so its existing tests are unchanged.

**Test:** I added a round-trip check and an Oracle/Snowflake → Exasol check to `tests/dialects/test_exasol.py`, next to the existing `LISTAGG` coverage. No existing test was edited.

Before the fix, `LISTAGG` re-parsed with a nested `CONCAT` on each pass, so the output was unstable. It is now stable for the probed variants (separator, `DISTINCT`, no separator). I have not changed the generator, and I have not committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"listagg\" sqlglot/ | head -50 && echo --- && grep -n -i \"listagg\\|GroupConcat\" tests/dialects/test_exasol.py | head", "description": "Find LISTAGG handling in sqlglot and Exasol tests"}
[tool_result] sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/trino.py:25:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/snowflake.py:738:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/oracle.py:60:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/exasol.py:121:        # https://docs.exasol.com/db/latest/sql
…[1067 chars elided]…
tagg",
sqlglot/generators/duckdb.py:2105:        SELECT LISTAGG(
---
326:            "SELECT id, department, hire_date, LISTAGG(id, ',') WITHIN GROUP (ORDER BY hire_date) OVER (PARTITION BY department rows BETWEEN 1 preceding AND 1 following) AS GROUP_CONCAT_RESULT FROM employee_table ORDER BY department, hire_date",
331:                "exasol": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
334:                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
[tool_use Bash] {"command": "sed -n 110,130p sqlglot/parsers/exasol.py && echo --- && grep -n \"_parse_group_concat\" -A30 sqlglot/parser.py | head -60 && echo --- && sed -n 340,360p sqlglot/generators/exasol.py && echo --- && sed -n 2420,2470p sqlglot/dialects/dialect.py && echo --- && sed -n 7895,7930p sqlglot/parser.py", "description": "Read Exasol LISTAGG parser, generator, and helpers"}
[tool_result]         TokenType.SYSTIMESTAMP,
    }

    NO_PAREN_FUNCTIONS = {
        **parser.Parser.NO_PAREN_FUNCTIONS,
        TokenType.SYSTIMESTAMP: exp.Systimestamp,
        TokenType.CURRENT_SCHEMA: exp.CurrentSchema,
    }

    FUNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_conca
…[5928 chars elided]…
])
            # bigquery: STRING_AGG([DISTINCT] expression [, separator] [ORDER BY key [{ASC | DESC}] [, ... ]] [LIMIT n])
            # The order is parsed through `this` as a canonicalization for WITHIN GROUPs
            args[0] = self._parse_limit(this=self._parse_order(this=args[0]))
            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))

        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
[tool_use Bash] {"command": "grep -n \"def _parse_string_agg\" -A45 sqlglot/parser.py | head -70; echo ---; sed -n 318,340p tests/dialects/test_exasol.py; echo ---; cat .lithify/harness/scripts/probe_parse.py | head -30", "description": "Read string_agg parser and related Exasol tests"}
[tool_result] 7894:    def _parse_string_agg(self) -> exp.GroupConcat:
7895-        if self._match(TokenType.DISTINCT):
7896-            args: list[exp.Expr | None] = [
7897-                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
7898-            ]
7899-            if self._match(TokenType.COMMA):
7900-                args.extend(self._parse_csv(self._parse_disjunction))
7901-        else:
7902-            args = self._parse_csv(self._parse_disjunction)  # type: ignore
7903-
790
…[4045 chars elided]…
hows both

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
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\" \"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(x, ',') ON OVERFLOW ERROR WI
…[113 chars elided]…
; $PY -I -c \"\nimport sqlglot\nfor d in ['oracle','snowflake','trino','duckdb']:\n    print(d, repr(sqlglot.parse_one(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read=d).selects[0]))\nprint(repr(sqlglot.parse_one(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read='exasol').selects[0]))\n\" ", "description": "Reproduce LISTAGG separator bug across dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sys;print(sqlglot.__file__)\"; ls $(dirname $(dirname $PY))/lib/*/site-packages | grep -i sqlglot", "description": "Check which sqlglot the env imports"}
[tool_result] ~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/sqlglot/__init__.py
sqlglot_mypy-2.3.0.post2.dist-info/
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\" \"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(x, ',') ON OVERFLOW ERROR WI
…[4 chars elided]…
 GROUP (ORDER BY y) FROM t\" | PYTHONPATH=. $PY .lithify/harness/scripts/probe_parse.py --read exasol; echo \"exit $?\"; $PY -c \"\nimport sqlglot\nfor d in ['oracle','snowflake','trino','duckdb','exasol']:\n    print(d, repr(sqlglot.parse_one(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read=d).selects[0]))\n\" ", "description": "Probe LISTAGG statements and compare dialects"}
[tool_result] UNSTABLE  SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
          SELECT LISTAGG(CONCAT(x, ','), ',') WITHIN GROUP (ORDER BY y) FROM t
           -> SELECT LISTAGG(CONCAT(CONCAT(x, ','), ','), ',') WITHIN GROUP (ORDER BY y) FROM t
UNSTABLE  SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
          SELECT LISTAGG(CONCAT(x, ';'), ',') WITHIN GROUP (ORDER BY y) FROM t
           -> SELECT LISTAGG(CONCAT(CONCAT(x, ';'), ','), ',') WITHIN GROUP (ORDER BY y) FROM t
UNSTABLE  SELECT L
…[1707 chars elided]…
   this=Identifier(this=y, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this=',', is_string=True))
exasol WithinGroup(
  this=GroupConcat(
    this=Concat(
      expressions=[
        Column(
          this=Identifier(this=x, quoted=False)),
        Literal(this=',', is_string=True)],
      safe=True,
      coalesce=True)),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=y, quoted=False)),
        nulls_first=False)]))
[assistant] The bug is in the Exasol parser: `LISTAGG` shares the `GROUP_CONCAT` handler, which folds extra arguments into a `CONCAT`. Oracle, Snowflake and Trino route `LISTAGG` to `_parse_string_agg`, which keeps the separator. I'll make Exasol do the same and leave `GROUP_CONCAT` on its own handler.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\" \"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t\" \"SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR 
…[341 chars elided]…
 y) FROM t\\\", read='exasol', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read='oracle', write='exasol'))\n\"; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Verify fix: round-trip and cross-dialect output, run dialect tests"}
[tool_result] OK        SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
          SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
OK        SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
          SELECT LISTAGG(x, ';') WITHIN GROUP (ORDER BY y) FROM t
OK        SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t
          SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t
OK        SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t
          SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
OK        SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR ',') FROM t
          SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
exit 0
["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
["SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t"]
.............................................                          [100%]
45 passed, 794 subtests passed in 0.25s
[assistant] The fix works and the Oracle and Exasol tests pass. Now I'll add a regression test next to the existing `LISTAGG` coverage.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\",", "new_string": "        self.validate_identity(\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\")\n        sel
…[234 chars elided]…
 (ORDER BY y)\",\n            },\n            write={\n                \"exasol\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-170818-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3; time $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run Exasol tests then full suite as final gate"}
[tool_result] ....................                                             [100%]
20 passed, 584 subtests passed in 0.14s
.......................................... [ 78%]
......................................................................................................................................................................................................... [ 96%]
.......................... [ 98%]
..................              [100%]
1126 passed, 18229 subtests passed in 46.86s
$PY -m pytest -q -p no:cacheprovider --color=no 2>&1  115.48s user 13.20s system 273% cpu 47.054 total
tail -5  0.00s user 0.00s system 0% cpu 47.054 total
[assistant] Exasol `LISTAGG` now keeps the separator as the separator, so `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` parses with `x` as the value and `','` as the separator, and round-trips. The full suite passes (1126 tests).

**Cause:** `sqlglot/parsers/exasol.py` mapped `LISTAGG` to the same handler as `GROUP_CONCAT`. That handler folds the extra argument into a `CONCAT`, which is where the separator was lost.

**Fix:** `LISTAGG` now uses `_parse_string_agg()`, the same path Oracle, Snowflake and Trino use. `GROUP_CONCAT` keeps its own handler, so its existing tests are unchanged.

**Test:** I added a round-trip check and an Oracle/Snowflake → Exasol check to `tests/dialects/test_exasol.py`, next to the existing `LISTAGG` coverage. No existing test was edited.

Before the fix, `LISTAGG` re-parsed with a nested `CONCAT` on each pass, so the output was unstable. It is now stable for the probed variants (separator, `DISTINCT`, no separator). I have not changed the generator, and I have not committed anything.
