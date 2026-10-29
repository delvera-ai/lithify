# trajectory base-1

final message:
Exasol `LISTAGG` now parses `x` as the value and `','` as the separator, the same as Oracle, Snowflake and Trino, and it round-trips. The full suite passes (1126 tests).

**Cause:** `LISTAGG` was registered to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser. That parser folds the comma-separated arguments into a `CONCAT`, so the value became `CONCAT(x, ',')` and the separator was dropped.

**Fix** (`sqlglot/parsers/exasol.py`): `LISTAGG` now uses `_parse_string_agg()`, as Oracle, Snowflake and Trino do. `GROUP_CONCAT` stays on `_parse_group_concat()`, so its existing `SEPARATOR` behaviour is unchanged.

**Tests** (`tests/dialects/test_exasol.py`): I added a regression test for the `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` round-trip. It also checks that the same SQL read from Oracle, Snowflake, Trino and DuckDB produces the Exasol output. I did not edit any existing test.

Verification:
- Before the fix, the parse showed `CONCAT(x, ',')` with no separator; after it, the separator is `','` and the output is `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`.
- `tests/dialects/test_exasol.py`: 20 passed.
- Full suite with the project command: 1126 passed.

I haven't committed anything; the changes are in the working tree. I didn't run `make style`.

## events
[tool_use Bash] {"command": "grep -rn -i \"listagg\" sqlglot/ | head -50 && echo --- && grep -n -i \"listagg\" tests/dialects/test_exasol.py tests/dialects/test_oracle.py tests/dialects/test_snowflake.py | head -40", "description": "Find LISTAGG handling across sqlglot and tests"}
[tool_result] sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parsers/redshift.py:48:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/snowflake.py:738:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/oracle.py:60:        "LISTAGG": lambda self: self._parse_string_agg(),
sqlglot/parsers/spark.py:96:        "LISTAGG": exp.GroupConcat.from_arg_list,
sqlglot/parsers/trino.py:25:        "LISTAGG": lambda
…[3501 chars elided]…
SELECT LISTAGG({distinct}col, '|SEPARATOR|') WITHIN GROUP (ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5889:                    "duckdb": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|' ORDER BY col2) FROM t",
tests/dialects/test_oracle.py:900:    def test_listagg(self):
tests/dialects/test_oracle.py:902:            "SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) "
tests/dialects/test_oracle.py:906:            "SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) "
[tool_use Bash] {"command": "sed -n 110,130p sqlglot/parsers/exasol.py && echo ---GEN && sed -n 340,360p sqlglot/generators/exasol.py && echo ---PARSE_GC && grep -n \"_parse_group_concat\" -A30 sqlglot/parser.py | head -60 && echo ---DIALECT && sed -n 2420,2470p sqlglot/dialects/dialect.py && echo ---TEST && sed -n 320,340p tests/dialects/test_exasol.py", "description": "Read Exasol LISTAGG parser, generator, and helpers"}
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
…[5347 chars elided]…
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
[tool_use Bash] {"command": "sed -n 10087,10120p sqlglot/parser.py && echo ---STRINGAGG && grep -n \"def _parse_string_agg\" -A60 sqlglot/parser.py", "description": "Read group_concat tail and string_agg parser"}
[tool_result]             this = order or concat_exprs(args[0], args)
        else:
            this = None

        separator = self._parse_field() if self._match(TokenType.SEPARATOR) else None

        return self.expression(exp.GroupConcat(this=this, separator=separator))

    def _parse_initcap(self) -> exp.Initcap:
        expr = exp.Initcap.from_arg_list(self._parse_function_args())

        # attach dialect's default delimiters
        if expr.args.get("expression") is None:
            expr.set("expre
…[3455 chars elided]…
   separator=seq_get(args, 1),
7944-                on_overflow=on_overflow,
7945-            )
7946-        )
7947-
7948-    def _parse_convert(self, strict: bool, safe: bool | None = None) -> exp.Expr | None:
7949-        this = self._parse_bitwise()
7950-
7951-        if self._match(TokenType.USING):
7952-            to: exp.Expr | None = exp.DType.CHARACTER_SET.into_expr(kind=self._parse_charset_name())
7953-        elif self._match(TokenType.COMMA):
7954-            to = self._parse_types()
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='exasol'); print(repr(e.find(sqlglot.exp.GroupConcat)))\n    print(e.sql('exasol'))\n    print(sqlglot.parse_one(s, read='oracle').sql('exasol'))\n\"", "description": "Reproduce LISTAGG parsing bug on Exasol"}
[tool_result] GroupConcat(
  this=Concat(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False)),
      Literal(this=',', is_string=True)],
    safe=True,
    coalesce=True))
SELECT LISTAGG(CONCAT(x, ','), ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
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
SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC NULLS FIRST) FROM t
[assistant] Reproduced: `LISTAGG` shares the MySQL-style `GROUP_CONCAT` parser, which folds the comma-separated arguments into a `CONCAT`. I'll route `LISTAGG` to the same `_parse_string_agg` that Oracle, Snowflake and Trino use, and leave `GROUP_CONCAT` on its existing parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-143358-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-143358-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[assistant] Next I'll add a regression test to the Exasol test file covering the parse, the cross-dialect output, and the round-trip.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-143358-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\",", "new_string": "        self.validate_identity(\n            \"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\"
…[127 chars elided]…
           \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"trino\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"duckdb\": \"LISTAGG(x, ',' ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-143358-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", \\\"SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t\\\"]:\n    e = sqlglot.parse_one(s, read='exasol'); g=e.find(sqlglot.exp.GroupConcat); print(type(g.this).__name__, g.args.get('separator').sql())\n    print(e.sql('exasol'))\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Verify parse output and run Exasol dialect tests"}
[tool_result] Order ','
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
Order ','
SELECT LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC) FROM t
....................                                              [100%]
20 passed, 583 subtests passed in 0.23s
[assistant] The Exasol tests pass and the separator now parses correctly. Next I'll run the full project suite with the configured command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] ........................................................... [ 47%]
...................................... [ 50%]
................................................... [ 55%]
................................................... [ 59%]
..................... [ 61%]
........ [ 62%]
............................................................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
................................................. [ 82%]
........................................................................................................................................................ [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1126 passed, 18228 subtests passed in 52.02s
[tool_use Bash] {"command": "git diff --stat && git diff sqlglot/", "description": "Show final diff of source changes"}
[tool_result]  sqlglot/parsers/exasol.py     |  5 +++--
 tests/dialects/test_exasol.py | 12 ++++++++++++
 2 files changed, 15 insertions(+), 2 deletions(-)
diff --git a/sqlglot/parsers/exasol.py b/sqlglot/parsers/exasol.py
index 0d2156035..9dd504e56 100644
--- a/sqlglot/parsers/exasol.py
+++ b/sqlglot/parsers/exasol.py
@@ -118,9 +118,10 @@ class ExasolParser(parser.Parser):
 
     FUNCTION_PARSERS = {
         **parser.Parser.FUNCTION_PARSERS,
-        # https://docs.exasol.com/db/latest/sql_references/functi
…[269 chars elided]…
NCAT": lambda self: self._parse_group_concat(),
+        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm
+        "LISTAGG": lambda self: self._parse_string_agg(),
         # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
         "JSON_VALUE": lambda self: self._parse_json_value(),
         # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_extract.htm
[assistant] Exasol `LISTAGG` now parses `x` as the value and `','` as the separator, the same as Oracle, Snowflake and Trino, and it round-trips. The full suite passes (1126 tests).

**Cause:** `LISTAGG` was registered to `_parse_group_concat`, the MySQL-style `GROUP_CONCAT` parser. That parser folds the comma-separated arguments into a `CONCAT`, so the value became `CONCAT(x, ',')` and the separator was dropped.

**Fix** (`sqlglot/parsers/exasol.py`): `LISTAGG` now uses `_parse_string_agg()`, as Oracle, Snowflake and Trino do. `GROUP_CONCAT` stays on `_parse_group_concat()`, so its existing `SEPARATOR` b
…[74 chars elided]…
ed a regression test for the `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)` round-trip. It also checks that the same SQL read from Oracle, Snowflake, Trino and DuckDB produces the Exasol output. I did not edit any existing test.

Verification:
- Before the fix, the parse showed `CONCAT(x, ',')` with no separator; after it, the separator is `','` and the output is `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`.
- `tests/dialects/test_exasol.py`: 20 passed.
- Full suite with the project command: 1126 passed.

I haven't committed anything; the changes are in the working tree. I didn't run `make style`.
