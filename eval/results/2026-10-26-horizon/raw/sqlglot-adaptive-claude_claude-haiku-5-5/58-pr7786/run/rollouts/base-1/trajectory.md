# trajectory base-1

final message:
Exasol `LISTAGG` now parses its second argument as the separator, and the SQL round-trips. The full suite passes (1126 tests) and ruff is clean.

The cause was in `sqlglot/parsers/exasol.py`: `LISTAGG` was routed to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser, which folds every argument into a concatenation. I split it out so `LISTAGG` uses `_parse_string_agg`, the same parser Oracle, Snowflake and Trino use. `GROUP_CONCAT` still uses `_parse_group_concat`.

Results after the change:
- `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` gives value `x`, separator `','`, and regenerates identically.
- `LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)` also round-trips.
- `LISTAGG(x)` with no separator still parses, and the generator writes the default `','`.

In `tests/dialects/test_exasol.py` I added identity tests for the two round-trip forms and a `validate_all` case that reads from Oracle and Snowflake and writes to Exasol and Oracle. I did not change any existing test expectations; the `GROUP_CONCAT` tests still pass unchanged.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-103303-exasol-dialect-the-second-argume/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn -i \"listagg\\|GroupConcat\" sqlglot/ --include=*.py | head -80", "description": "Find LISTAGG handling across sqlglot sources"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"listagg\" sqlglot/ tests/dialects/test_exasol.py | head -80; echo ---; ls sqlglot/parsers/ sqlglot/generators/ | grep -i exasol; ls sqlglot/dialects | grep -i exasol", "description": "Locate LISTAGG references in sqlglot and Exasol files"}
[tool_result] sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/trino.py:25:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/snowflake.py:738:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/exasol.py:121:        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg
…[1187 chars elided]…
RDER BY hire_date) OVER (PARTITION BY department rows BETWEEN 1 preceding AND 1 following) AS GROUP_CONCAT_RESULT FROM employee_table ORDER BY department, hire_date",
tests/dialects/test_exasol.py:331:                "exasol": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
tests/dialects/test_exasol.py:334:                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
sqlglot/generators/duckdb.py:2105:        SELECT LISTAGG(
---
exasol.py
exasol.py
exasol.py
[tool_use Bash] {"command": "sed -n 110,135p sqlglot/parsers/exasol.py; echo ---; sed -n 340,365p sqlglot/generators/exasol.py; echo ---; sed -n 2420,2470p sqlglot/dialects/dialect.py; echo ---; grep -n \"_parse_group_concat\\|def _parse_string_agg\" -A40 sqlglot/parser.py | sed -n 1,140p; echo ---; sed -n 7890,7960p sqlglot/parser.py; echo ---; sed -n 320,340p tests/dialects/test_exasol.py", "description": "Read Exasol LISTAGG parser, generator, and helper code"}
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
…[12168 chars elided]…
                "exasol": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
                "mysql": "GROUP_CONCAT(DISTINCT x ORDER BY y DESC SEPARATOR ',')",
                "tsql": "STRING_AGG(x, ',') WITHIN GROUP (ORDER BY y DESC)",
                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
            },
        )
        self.validate_all(
            "EDIT_DISTANCE(col1, col2)",
            read={
                "exasol": "EDIT_DISTANCE(col1, col2)",
[assistant] The Exasol dialect maps `LISTAGG` to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser that folds every argument into a concatenation. Oracle, Snowflake and Trino use `_parse_string_agg`, which keeps the second argument as the separator. I'll switch `LISTAGG` to that parser and leave `GROUP_CONCAT` alone.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103303-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103303-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\nfor s in ['SELECT LISTAGG(x, \\',\\') WITHIN GROUP (ORDER BY y) FROM t', 'SELECT LISTAGG(DISTINCT x, \\',\\') WITHIN GROUP (ORDER BY y DESC) FROM t', 'SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t', 'SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR \\',\\') FROM t']:\n    e = sqlglot.parse_one(s, read='exasol')\n    print(repr(e.find(sqlglot.exp.GroupConcat).args.get('this')), '|', e.find(sqlglot.exp.GroupConcat).args.get('separator'))\n    print(e.sql('exasol'))\n\"", "description": "Check Exasol LISTAGG parse and round-trip output"}
[tool_result] <work>/env-sqlglot/bin/python
Order(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  expressions=[
    Ordered(
      this=Column(
        this=Identifier(this=y, quoted=False)),
      nulls_first=False)]) | ','
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
Order(
  this=Distinct(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=Fa
…[227 chars elided]…
der(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  expressions=[
    Ordered(
      this=Column(
        this=Identifier(this=y, quoted=False)),
      nulls_first=False)]) | None
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
Order(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  expressions=[
    Ordered(
      this=Column(
        this=Identifier(this=y, quoted=False)),
      nulls_first=False)]) | ','
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
[assistant] The parse is now correct: `x` is the value, `','` is the separator, and the SQL round-trips. Next I'll add regression tests next to the existing `GROUP_CONCAT` test and run the Exasol and Oracle suites.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103303-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\",", "new_string": "        self.validate_identity(\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\")\n        sel
…[262 chars elided]…
 (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n            write={\n                \"exasol\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103303-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_oracle.py tests/dialects/test_snowflake.py tests/dialects/test_trino.py 2>&1 | tail -30", "description": "Run Exasol, Oracle, Snowflake, Trino dialect tests"}
[tool_result] ................................................... [ 34%]
........................................................ [ 72%]
.........................................  [100%]
148 passed, 2371 subtests passed in 1.35s
[assistant] Those pass. Now the full suite, plus the formatter and linter, since one of my new test lines may be over the length limit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff format --check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py || true) 2>&1 | tail -3; ($PY -m ruff check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py || true) 2>&1 | tail -3", "description": "Run full test suite, ruff format and lint checks"}
[tool_result] ........................................................................................................................................................ [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1126 passed, 18228 subtests passed in 56.78s
Would reformat: tests/dialects/test_exasol.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_exasol.py && $PY -m ruff format --check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -2; git diff --stat", "description": "Apply ruff formatting and recheck Exasol tests"}
[tool_result] 1 file reformatted
2 files already formatted
....................                                              [100%]
20 passed, 583 subtests passed in 0.27s
 sqlglot/parsers/exasol.py     |  5 +++--
 tests/dialects/test_exasol.py | 15 +++++++++++++++
 2 files changed, 18 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: tests/dialects/test_exasol.py. Call Read before editing.]
[tool_use Bash] {"command": "git diff", "description": "Show final diff of the changes"}
[tool_result] diff --git a/sqlglot/parsers/exasol.py b/sqlglot/parsers/exasol.py
index 0d2156035..9dd504e56 100644
--- a/sqlglot/parsers/exasol.py
+++ b/sqlglot/parsers/exasol.py
@@ -118,9 +118,10 @@ class ExasolParser(parser.Parser):
 
     FUNCTION_PARSERS = {
         **parser.Parser.FUNCTION_PARSERS,
-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
         # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/grou
…[1646 chars elided]…
ROUP (ORDER BY y)",
+            read={
+                "oracle": "LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)",
+                "snowflake": "LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)",
+            },
+            write={
+                "exasol": "LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)",
+                "oracle": "LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)",
+            },
+        )
         self.validate_all(
             "GROUP_CONCAT(DISTINCT x ORDER BY y DESC)",
             write={
[assistant] Exasol `LISTAGG` now parses its second argument as the separator, and the SQL round-trips. The full suite passes (1126 tests) and ruff is clean.

The cause was in `sqlglot/parsers/exasol.py`: `LISTAGG` was routed to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser, which folds every argument into a concatenation. I split it out so `LISTAGG` uses `_parse_string_agg`, the same parser Oracle, Snowflake and Trino use. `GROUP_CONCAT` still uses `_parse_group_concat`.

Results after the change:
- `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` gives value `x`, separator `','`, and regenerates identically.
- `LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)` also round-trips.
- `LISTAGG(x)` with no separator still parses, and the generator writes the default `','`.

In `tests/dialects/test_exasol.py` I added identity tests for the two round-trip forms and a `validate_all` case that reads from Oracle and Snowflake and writes to Exasol and Oracle. I did not change any existing test expectations; the `GROUP_CONCAT` tests still pass unchanged.
