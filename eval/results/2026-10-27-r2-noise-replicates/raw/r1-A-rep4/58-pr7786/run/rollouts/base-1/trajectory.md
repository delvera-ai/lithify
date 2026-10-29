# trajectory base-1

final message:
Exasol `LISTAGG` now parses its second argument as the separator, and round-trips as `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`. The full suite passes (1126 tests).

**Cause:** `sqlglot/parsers/exasol.py` mapped `LISTAGG` to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser. That parser folds comma-separated arguments into a `CONCAT`, which is why the separator was lost. Oracle and Snowflake use `_parse_string_agg`, and that is what I switched Exasol to.

**Changes:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now uses `_parse_string_agg()`. `GROUP_CONCAT` stays on `_parse_group_concat()`, since Exasol's `GROUP_CONCAT` uses `SEPARATOR` syntax and the existing tests depend on that.
- `tests/dialects/test_exasol.py`: added a round-trip check for `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` and cross-dialect reads from Oracle, Snowflake, Trino and DuckDB. I did not modify any existing test assertions.

I checked `LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)` by hand: the separator is `','` and the output is correct, but I did not add a test case for it.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n -i \"listagg\\|GroupConcat\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py | head -50; grep -n -i \"class ListAgg\\|class GroupConcat\" -A8 sqlglot/expressions.py"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls; git rev-parse --show-toplevel; grep -rn -i \"listagg\" --include=*.py . | grep -v tests | head -50"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
~/.cache/lithify/work/repo-d5521a213087/20261029-084605-exasol-dialect-the-second-argume/base-1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"listagg\" sqlglot/ | head -50; echo ---; grep -rn -i \"listagg\" tests/ | head -40"}
[tool_result] sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/trino.py:25:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/snowflake.py:738:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/oracle.py:60:        "LISTAGG": lambda
…[5750 chars elided]…
         "databricks": "LISTAGG(DISTINCT x, '') WITHIN GROUP (ORDER BY y DESC)",
tests/dialects/test_mysql.py:1148:                "databricks": "LISTAGG(CONCAT(a, b, c), ',')",
tests/dialects/test_mysql.py:1158:                "databricks": "LISTAGG(CONCAT(a, b, c), '')",
tests/dialects/test_mysql.py:1168:                "databricks": "LISTAGG(DISTINCT CONCAT(a, b, c), '')",
tests/dialects/test_mysql.py:1178:                "databricks": "LISTAGG(CONCAT(a, b, c), '') WITHIN GROUP (ORDER BY d)",
[tool_use Bash] {"command": "sed -n 110,130p sqlglot/parsers/exasol.py; echo ---; grep -n \"_parse_group_concat\" -A30 sqlglot/parser.py | head -60; echo ---; sed -n 7890,7940p sqlglot/parser.py; echo ---; sed -n 340,360p sqlglot/generators/exasol.py; echo ---; sed -n 2420,2470p sqlglot/dialects/dialect.py; echo; sed -n 320,340p tests/dialects/test_exasol.py"}
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
…[7904 chars elided]…
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
[assistant] The Exasol parser maps `LISTAGG` to `_parse_group_concat`, which is the MySQL-style `GROUP_CONCAT` parser that folds comma-separated arguments into a `CONCAT`. Oracle and Snowflake use `_parse_string_agg` instead. I'll reproduce first, then switch `LISTAGG` over and keep `GROUP_CONCAT` on the existing parser.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\", \\\"SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR ',') FROM t\\\"]:\n    e=sqlglot.parse_one(s, read='exasol'); print(repr(e.find(sqlglot.exp.GroupConcat))); print(e.sql('exasol'))\n\""}
[tool_result] GroupConcat(
  this=Concat(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False)),
      Literal(this=',', is_string=True)],
    safe=True,
    coalesce=True))
SELECT LISTAGG(CONCAT(x, ','), ',') WITHIN GROUP (ORDER BY y) FROM t
GroupConcat(
  this=Distinct(
    expressions=[
      Concat(
        expressions=[
          Column(
            this=Identifier(this=x, quoted=False)),
          Literal(this=',', is_string=True)],
        safe=True,
        coalesce=True)]))
SELECT LISTAGG(DISTINCT CONCAT(x, ','), ',') WITHIN GROUP (ORDER BY y DESC) FROM t
GroupConcat(
  this=Order(
    this=Column(
      this=Identifier(this=x, quoted=False)),
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=y, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this=',', is_string=True))
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
[assistant] Reproduced: `LISTAGG` is folded into `CONCAT(x, ',')` and the separator is lost. Switching `LISTAGG` to `_parse_string_agg`, as Oracle and Snowflake do, and leaving `GROUP_CONCAT` on the existing parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-084605-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-084605-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\", \\\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y) FROM t\\\"]:\n    e=sqlglot.parse_one(s, read='exasol'); g=e.find(sqlglot.exp.GroupConcat); print(g.args.get('separator'), e.sql('exasol'), '|', e.sql('oracle'), '|', e.sql('snowflake'))\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30"}
[tool_result] ',' SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
',' SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t | SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FROM t | SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS LAST) FROM t
None SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t | SELECT LISTAGG(x, ','
…[928 chars elided]…
....................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 53.35s
[assistant] All 1126 tests pass and the separator now survives. I'll add a regression test to the Exasol test file, then run it alone.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_exasol.py | head -30"}
[tool_result] 9:    def test_exasol(self):
39:    def test_exasol_keywords(self):
46:    def test_qualify_unscoped_star(self):
84:    def test_type_mappings(self):
140:    def test_mod(self):
151:    def test_bits(self):
252:    def test_aggregateFunctions(self):
302:    def test_stringFunctions(self):
434:    def test_datetime_functions(self):
621:    def test_number_functions(self):
670:    def test_scalar(self):
805:    def test_odbc_date_literals(self):
812:    def test_local_prefix_for_alias(self):
871:    def test_regexp_like(self):
889:    def test_json(self):
902:    def test_group_by_all(self):
966:    def test_use_to_open_schema(self):
987:    def test_show_tables(self):
1003:    def test_show_databases(self):
1015:    def test_group_by_alias_local(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-084605-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\",", "new_string": "        self.validate_identity(\"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\")\n        self.validate_all
…[88 chars elided]…
           \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"trino\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"duckdb\": \"LISTAGG(x, ',' ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-084605-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -30; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3"}
[tool_result] ....................                                              [100%]
20 passed, 583 subtests passed in 0.16s
.............. [ 98%]
.................               [100%]
1126 passed, 18228 subtests passed in 49.76s
[assistant] Exasol `LISTAGG` now parses its second argument as the separator, and round-trips as `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`. The full suite passes (1126 tests).

**Cause:** `sqlglot/parsers/exasol.py` mapped `LISTAGG` to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser. That parser folds comma-separated arguments into a `CONCAT`, which is why the separator was lost. Oracle and Snowflake use `_parse_string_agg`, and that is what I switched Exasol to.

**Changes:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now uses `_parse_string_agg()`. `GROUP_CONCAT` stays on `_parse_group_concat()`, since Exasol's `GROUP_CONCAT` uses `SEPARATOR` syntax and the existing tests depend on that.
- `tests/dialects/test_exasol.py`: added a round-trip check for `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` and cross-dialect reads from Oracle, Snowflake, Trino and DuckDB. I did not modify any existing test assertions.

I checked `LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)` by hand: the separator is `','` and the output is correct, but I did not add a test case for it.

Nothing is committed.
