# trajectory base-1

final message:
Oracle now parses and round-trips `LISTAGG` with `ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT]` and `ON OVERFLOW ERROR`. The full test suite passes (1094 passed) and ruff is clean. I left the changes uncommitted in the worktree.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` routes through the existing `_parse_string_agg`, the same path Snowflake uses.
- `sqlglot/generators/oracle.py`: `GroupConcat` generates as `LISTAGG(... ON OVERFLOW ...) WITHIN GROUP (ORDER BY ...)`. I used `sep=""` because Oracle's delimiter is optional and should not default to `,`.
- `tests/dialects/test_oracle.py`: a new `test_listagg` covering the clause variants, plus a Trino output check.

**Behaviour notes**
- **Default count:** when `WITH`/`WITHOUT COUNT` is omitted, output gains an explicit `WITH COUNT`. Oracle's default is `WITH COUNT`, so this is equivalent, but the text is not identical. Trino and Snowflake parsing behave the same way.
- **Snowflake drops the clause:** transpiling Oracle `ON OVERFLOW` to Snowflake silently drops it, because Snowflake's generator doesn't emit `on_overflow`. This predates my change and is out of scope.
- **Parser drops the clause without `WITHIN GROUP`:** `_parse_string_agg` discards `on_overflow` when there is no `WITHIN GROUP`. Oracle requires `WITHIN GROUP`, so I left it alone. Say if you want that fixed too.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\" sqlglot/ | head -50; echo ---; grep -rn -i \"listagg\" sqlglot/ tests/ | head -60", "description": "Search for overflow and listagg handling"}
[tool_result] sqlglot/parsers/clickhouse.py:142:    "sumWithOverflow",
sqlglot/parsers/bigquery.py:114:                {"null_if_pos_overflow": dialect.REGEXP_EXTRACT_POSITION_OVERFLOW_RETURNS_NULL}
sqlglot/parsers/snowflake.py:67:        allow_overflow=True,
sqlglot/parsers/snowflake.py:237:                {"null_if_pos_overflow": dialect.REGEXP_EXTRACT_POSITION_OVERFLOW_RETURNS_NULL}
sqlglot/parsers/snowflake.py:567:            lower=exp.Literal.number(-9223372036854775808.0),  # -2^63 as float to avoid ove
…[9890 chars elided]…
"SELECT LISTAGG(DISTINCT col, ',') WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:59:            "SELECT LISTAGG(col, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:62:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:65:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
[tool_use Bash] {"command": "sed -n 7690,7760p sqlglot/parser.py; echo ---; sed -n 5480,5500p sqlglot/generator.py; echo ---; sed -n 1875,1895p sqlglot/expressions/query.py; echo ---; sed -n 125,140p sqlglot/expressions/aggregate.py; echo ---; ls sqlglot/parsers sqlglot/generators | grep -i oracle; grep -n \"LISTAGG\\|GroupConcat\\|STRING_AGG\\|_parse_string_agg\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py; ls tests/dialects | grep oracle", "description": "Inspect listagg parsing and generation code"}
[tool_result]             safe=safe,
            action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
            default=default,
        )

    def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disj
…[4164 chars elided]…
(self) -> str:
---
class First(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class FirstValue(Expression, AggFunc):
    pass


class GroupConcat(Expression, AggFunc):
    arg_types = {"this": True, "separator": False, "on_overflow": False}


class Grouping(Expression, AggFunc):
    arg_types = {"expressions": True}
    is_var_len_args = True

---
oracle.py  6.3K
oracle.py  8.5K
0 matches for 'LISTAGG\|GroupConcat\|STRING_AGG\|_parse_string_agg'
test_oracle.py  43.4K
[tool_use Bash] {"command": "grep -rn \"GroupConcat\\|groupconcat\" sqlglot/generators/*.py sqlglot/generator.py | head -30; echo ---; grep -n \"ON OVERFLOW\" -B3 -A3 tests/dialects/test_snowflake.py | head -40; echo ---; sed -n 1,80p sqlglot/parsers/oracle.py; echo; sed -n 2405,2452p sqlglot/dialects/dialect.py; ls sqlglot/generators | head -50", "description": "Find GroupConcat generation and Snowflake tests"}
[tool_result] sqlglot/generators/bigquery.py:26:    groupconcat_sql,
sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/clickhouse.py:419:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/databricks.py:8:    groupconcat_sql,
sqlglot/generators/databricks.py:47:            exp.GroupConcat: groupconcat_sql,
sqlglot/generators/doris.py:60:        exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/duckdb.p
…[6164 chars elided]…
cks.py  3.8K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  174.9K
dune.py  323B
exasol.py  29.0K
fabric.py  6.5K
hive.py  21.0K
materialize.py  2.0K
mysql.py  25.3K
oracle.py  6.3K
postgres.py  21.5K
presto.py  25.1K
prql.py  192B
python.py  3.9K
redshift.py  10.1K
risingwave.py  1.1K
singlestore.py  42.1K
snowflake.py  46.6K
solr.py  192B
spark.py  7.7K
spark2.py  9.6K
sqlite.py  11.9K
starrocks.py  9.9K
tableau.py  1.6K
teradata.py  7.0K
trino.py  2.3K
tsql.py  25.2K
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor q in [\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\", \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\\\", \\\"SELECT LISTAGG(last_nam
…[151 chars elided]…
ranspile(q, read='oracle', write=d)[0])\n    except Exception as e: print(d, 'ERR', type(e).__name__, str(e)[:200])\n\"; grep -n \"OVERFLOW\" tests/dialects/*.py | head; grep -n \"class Generator\\|TRANSFORMS\\|exp.Anonymous\\|def .*_sql\" sqlglot/generators/oracle.py | head -40; sed -n 725,735p sqlglot/parsers/snowflake.py", "description": "Check current Oracle LISTAGG behavior and related code"}
[tool_result] oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
snowflake ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
trino ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
oracle ERR P
…[2218 chars elided]…
 for k, v in FUNCTIONS.items() if k != "PREDICT"}

    FUNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        "DATE_PART": lambda self: self._parse_date_part(),
        "DIRECTORY": lambda self: self._parse_directory(),
        "OBJECT_CONSTRUCT_KEEP_NULL": lambda self: self._parse_json_object(),
        "LISTAGG": lambda self: self._parse_string_agg(),
        "SEMANTIC_VIEW": lambda self: self._parse_semantic_view(),
        "SUBSTR": lambda self: self._parse_substring(),
    }
[tool_use Bash] {"command": "sed -n 1,12p sqlglot/generators/oracle.py; sed -n 60,80p sqlglot/generators/oracle.py; grep -n \"groupconcat_sql\" -B2 -A4 sqlglot/generators/snowflake.py | head -20; grep -rn \"GROUP_CONCAT\\|LISTAGG\" tests/dialects/test_oracle.py | head", "description": "Read Oracle generator header and TRANSFORMS"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)

        exp.DType.BINARY: "BLOB",
        exp.DType.VARBINARY: "BLOB",
        exp.DType.ROWVERSION: "BLOB",
    }

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.DateStrToDate: lambda self, e: self.func(
            "TO_DATE", e.this, exp.Literal.
…[534 chars elided]…
date_delta_sql,
10-    datestrtodate_sql,
11:    groupconcat_sql,
12-    if_sql,
13-    inline_array_sql,
14-    map_date_part,
15-    max_or_greatest,
--
496-        ),
497-        exp.GetExtract: rename_func("GET"),
498:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=""),
499-        exp.If: if_sql(name="IFF", false_value="NULL"),
500-        exp.JSONArray: lambda self, e: self.func(
501-            "TO_VARIANT", self.func("ARRAY_CONSTRUCT", *e.expressions)
502-        ),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=\"\", on_overflow=True),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-143401-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[assistant] Now let me check the round-trip and cross-dialect output.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nqs = [\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n \\\"SELECT LISTAGG(last_nam
…[668 chars elided]…
rite=d)[0])\n    except Exception as e: print('  ',d,'ERR',str(e)[:120])\nprint(sqlglot.transpile(\\\"SELECT STRING_AGG(x, ', ') FROM t\\\", read='duckdb', write='oracle'))\nprint(sqlglot.transpile(\\\"SELECT LISTAGG(x, ', ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY y) FROM t\\\", read='snowflake', write='oracle'))\n\"", "description": "Verify Oracle LISTAGG round-trip and transpilation"}
[tool_result] RT  False | SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t
   snowflake | SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
   trino | SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t
   duckdb | SELECT LISTAGG(last_name, '; ' ORDER BY last_name) FROM t
RT  True | SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP 
…[1708 chars elided]…
OM t
RT  True | SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
   snowflake | SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
   trino | SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
   duckdb | SELECT LISTAGG(DISTINCT last_name, '; ' ORDER BY last_name) FROM t
["SELECT LISTAGG(x, ', ') FROM t"]
["SELECT LISTAGG(x, ', ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY y) FROM t"]
[assistant] Oracle round-trips and transpiles to Trino correctly. Snowflake's generator drops `ON OVERFLOW`, which is pre-existing and out of scope. Now I'll add tests next to the existing Oracle tests.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_oracle.py | head -60", "description": "List test methods in Oracle test file"}
[tool_result] 24 matches in 24 files:

378:0:
393:0:
468:0:
532:0:
557:0:
586:0:
608:0:
617:0:
693:0:
707:0:
725:0:
743:0:
760:0:
780:0:
846:0:
870:0:
878:0:
884:0:
899:0:
9:0:
913:0:
927:0:
931:0:
973:0:
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_oracle.py | head -60; sed -n 1,12p tests/dialects/test_oracle.py", "description": "List test methods in Oracle test file"}
[tool_result] 24 matches in 24 files:

378:0:
393:0:
468:0:
532:0:
557:0:
586:0:
608:0:
617:0:
693:0:
707:0:
725:0:
743:0:
760:0:
780:0:
846:0:
870:0:
878:0:
884:0:
899:0:
9:0:
913:0:
927:0:
931:0:
973:0:
from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
[tool_use Bash] {"command": "wc -l tests/dialects/test_oracle.py && tail -n 30 tests/dialects/test_oracle.py", "description": "Show end of Oracle test file"}
[tool_result] 988
        ) AS
        BEGIN
            c := c + a + b;
            d := 42 + c;
        END;
        """

        expected_sqls = [
            "CREATE OR REPLACE PROCEDURE test_proc(a NUMBER, b IN NUMBER, c IN OUT NUMBER, d OUT NUMBER) AS BEGIN c := c + a + b; d := 42 + c; END",
        ]

        for expr, expected_sql in zip(parse(sql, read="oracle"), expected_sqls):
            self.assertEqual(expr.sql(dialect="oracle"), expected_sql)

    def test_create_trigger(self):
        """Test 
…[336 chars elided]…
t_trigger AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (:OLD.id, :OLD.balance, :NEW.balance, SYSDATE) END",
            check_command_warning=True,
        )

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view FOR EACH ROW BEGIN INSERT INTO employees (id, name, dept_id) VALUES (:NEW.id, :NEW.name, :NEW.dept_id) END",
            check_command_warning=True,
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_oracle.py <<'EOF'\n\n    def test_listagg(self):\n        self.validate_identity(\"LISTAGG(x, ', ') WITHIN GROUP (ORDER BY y)\")\n        self.validate_identity(\"LISTAGG(DISTINCT x, ', ') WITHIN GROUP (ORDER BY y)\")\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM emplo
…[889 chars elided]…
   \"trino\": \"LISTAGG(x, ', ') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_snowflake.py tests/dialects/test_trino.py 2>&1 | tail -30", "description": "Add Oracle LISTAGG tests and run dialect tests"}
[tool_result] .................................... [ 28%]
....................................... [ 59%]
....................................................                             [100%]
127 passed, 1789 subtests passed in 0.65s
[assistant] Targeted tests pass. Now the full suite, using the project's check command.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; echo \"exit=$?\"; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/oracle.py sqlglot/parsers/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/oracle.py sqlglot/parsers/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Run full test suite and lint checks"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.....................................................................................................................................................
…[334 chars elided]…
..... [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
.............................................. [ 86%]
................................................................................................................................................                                         [100%]
1094 passed, 17874 subtests passed in 53.99s
exit=0
All checks passed!
3 files already formatted
[tool_use Bash] {"command": "git status --short && git diff -- sqlglot | head -60", "description": "Show final source diff"}
[tool_result]  M sqlglot/generators/oracle.py
 M sqlglot/parsers/oracle.py
 M tests/dialects/test_oracle.pysqlglot/generators/oracle.py | 2 ++
 sqlglot/parsers/oracle.py    | 1 +
 2 files changed, 3 insertions(+)

--- Changes ---

sqlglot/generators/oracle.py
  @@ -3,6 +3,7 @@ from __future__ import annotations
  +    groupconcat_sql,
       no_ilike_sql,
       rename_func,
       strposition_sql,
  @@ -69,6 +70,7 @@ class OracleGenerator(generator.Generator):
  +        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep="", on_overflow=True),
           exp.ILike: no_ilike_sql,
           exp.LogicalOr: rename_func("MAX"),
           exp.LogicalAnd: rename_func("MIN"),
  +2 -0

sqlglot/parsers/oracle.py
  @@ -56,6 +56,7 @@ class OracleParser(parser.Parser):
  +        "LISTAGG": lambda self: self._parse_string_agg(),
       }
   
       PROPERTY_PARSERS = {
  +1 -0
[assistant] Oracle now parses and round-trips `LISTAGG` with `ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT]` and `ON OVERFLOW ERROR`. The full test suite passes (1094 passed) and ruff is clean. I left the changes uncommitted in the worktree.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` routes through the existing `_parse_string_agg`, the same path Snowflake uses.
- `sqlglot/generators/oracle.py`: `GroupConcat` generates as `LISTAGG(... ON OVERFLOW ...) WITHIN GROUP (ORDER BY ...)`. I used `sep=""` because Oracle's delimiter is optional and should not default to `,`.
- `tests/dialects/test_oracl
…[158 chars elided]…
omitted, output gains an explicit `WITH COUNT`. Oracle's default is `WITH COUNT`, so this is equivalent, but the text is not identical. Trino and Snowflake parsing behave the same way.
- **Snowflake drops the clause:** transpiling Oracle `ON OVERFLOW` to Snowflake silently drops it, because Snowflake's generator doesn't emit `on_overflow`. This predates my change and is out of scope.
- **Parser drops the clause without `WITHIN GROUP`:** `_parse_string_agg` discards `on_overflow` when there is no `WITHIN GROUP`. Oracle requires `WITHIN GROUP`, so I left it alone. Say if you want that fixed too.
