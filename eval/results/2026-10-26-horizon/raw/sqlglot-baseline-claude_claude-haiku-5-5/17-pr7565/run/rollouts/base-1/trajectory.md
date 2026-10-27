# trajectory base-1

final message:
Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff lint and format are clean. I haven't committed anything.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` now goes through the shared `_parse_string_agg()` parser, the same route Snowflake and Exasol take. Before this, Oracle failed with `Expecting )` at `ON`.
- `sqlglot/generators/oracle.py`: added a `GroupConcat` generator that emits `LISTAGG(x, sep ON OVERFLOW ...) WITHIN GROUP (ORDER BY ...)`. It uses the shared `groupconcat_sql` with no default delimiter, since Oracle's default is empty.
- `tests/dialects/test_oracle.py`: new `test_listagg` covering `ERROR`, `TRUNCATE` with and without `WITH`/`WITHOUT COUNT`, `DISTINCT`, and a Trino cross-dialect check.

**Things you should know**
- Snowflake doesn't get the clause fixed. Its parser already accepts `ON OVERFLOW`, but the generator drops it on output, so `LISTAGG(x, ',' ON OVERFLOW ERROR)` comes back out as plain `LISTAGG(x, ',')`. Snowflake's LISTAGG doesn't actually support this clause, so I left it alone. The clause comes from Trino's support.
- Oracle's `LISTAGG(x)` with no delimiter is now a `GroupConcat` with no separator, and DuckDB fills in `','` when transpiling. Snowflake has the same behavior today. Fixing it means deciding whether the AST should carry an explicit `''`, which changes Oracle identity output, so I didn't.
- Trino drops `ON OVERFLOW` when `WITHIN GROUP` is absent, e.g. `LISTAGG(x, ',' ON OVERFLOW ERROR)`. That's an existing bug in the shared parser. Oracle always requires `WITHIN GROUP`, so it doesn't affect this change.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\\|GroupConcat\\|ListAgg\" sqlglot/ --include=*.py | grep -v \"^sqlglot/optimizer\" | head -80", "description": "Find overflow and listagg references in source"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"overflow\\|ListAgg\" sqlglot/ tests/ | grep -v \"\\.pyc\" | head -80", "description": "Search source and tests for overflow and listagg"}
[tool_result] sqlglot/generator.py:5489:    def overflowtruncatebehavior_sql(self, expression: exp.OverflowTruncateBehavior) -> str:
sqlglot/parser.py:7705:        if self._match_text_seq("ON", "OVERFLOW"):
sqlglot/parser.py:7706:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7708:                on_overflow: exp.Expr | None = exp.var("ERROR")
sqlglot/parser.py:7711:                on_overflow = self.expression(
sqlglot/parser.py:7712:                 
…[7736 chars elided]…
test_exasol.py:331:                "exasol": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
tests/dialects/test_exasol.py:334:                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
tests/dialects/test_redshift.py:45:            "LISTAGG(sellerid, ', ')",
tests/dialects/test_redshift.py:51:                # GROUP_CONCAT, LISTAGG and STRING_AGG are aliases in DuckDB
tests/dialects/test_redshift.py:52:                "duckdb": "LISTAGG(sellerid, ', ')",
[tool_use Bash] {"command": "sed -n 7690,7760p sqlglot/parser.py; echo ----; sed -n 5480,5500p sqlglot/generator.py; echo ----; sed -n 1880,1895p sqlglot/expressions/query.py; echo ----; sed -n 2400,2452p sqlglot/dialects/dialect.py; echo ----; grep -n \"GroupConcat\\|_parse_string_agg\\|WITHIN\\|ListAgg\\|LISTAGG\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/dialects/oracle.py; echo ----; grep -n \"def _parse_string_agg\" -A40 sqlglot/parser.py | head -60", "description": "Read parser, generator, and expression code for overflow"}
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
…[7459 chars elided]…
s=args[0], separator=seq_get(args, 1)))
7730-
7731-        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
7732-        # This is done "manually", instead of letting _parse_window parse it into an exp.WithinGroup node, so that
7733-        # the STRING_AGG call is parsed like in MySQL / SQLite and can thus be transpiled more easily to them.
7734-        if not self._match_text_seq("WITHIN", "GROUP"):
7735-            self._retreat(index)
[tool_use Bash] {"command": "ls sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/dialects/oracle.py && grep -n \"FUNCTIONS\\|_parse_string_agg\\|GROUP_CONCAT\\|WITHIN\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py | head -40; grep -n -i \"listagg\\|within group\" tests/dialects/test_oracle.py | head; grep -n -i \"on overflow\" -B3 -A10 tests/dialects/test_snowflake.py | head -60; cat tests/dialects/test_oracle.py | head -30", "description": "Inspect Oracle parser/generator and existing tests"}
[tool_result] sqlglot/dialects/oracle.py
sqlglot/generators/oracle.py
sqlglot/parsers/oracle.py
sqlglot/parsers/oracle.py:26:    FUNCTIONS = {
sqlglot/parsers/oracle.py:27:        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k != "TO_BOOLEAN"},
sqlglot/parsers/oracle.py:48:    NO_PAREN_FUNCTIONS = {
sqlglot/parsers/oracle.py:49:        **parser.Parser.NO_PAREN_FUNCTIONS,
sqlglot/generators/snowflake.py:31:    RANKING_WINDOW_FUNCTIONS_WITH_FRAME,
sqlglot/generators/snowflake.py:142:    number_sequenc
…[2380 chars elided]…
MS_RANDOM.VALUE(low, high)").assert_is(exp.Rand)
        self.validate_identity("DBMS_RANDOM.VALUE()").assert_is(exp.Rand)
        self.validate_identity("CAST(value AS NUMBER DEFAULT 0 ON CONVERSION ERROR)")
        self.validate_identity("SYSDATE")
        self.validate_identity("CREATE GLOBAL TEMPORARY TABLE t AS SELECT * FROM orders")
        self.validate_identity("CREATE PRIVATE TEMPORARY TABLE t AS SELECT * FROM orders")
        self.validate_identity("REGEXP_REPLACE('source', 'search')")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import parse_one\nqs = [\n \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '.
…[514 chars elided]…
ame, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n]\nfor d in ['oracle','snowflake']:\n  for q in qs:\n    try:\n      e = parse_one(q, read=d)\n      print(d, '|', e.sql(d), '|', e.sql('snowflake'))\n    except Exception as ex: print(d, 'ERR', type(ex).__name__, str(ex)[:200])\n\"", "description": "Probe current LISTAGG overflow parsing in Oracle and Snowflake"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "cat > /tmp/probe_listagg.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1\")\nfrom sqlglot import parse_one\nqs = [\n \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\",\n \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '..
…[706 chars elided]…
|', e.sql(d), '|', e.sql('snowflake'))\n        except Exception as ex:\n            print(d, 'ERR', type(ex).__name__, str(ex)[:200])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe_listagg.py", "description": "Probe current LISTAGG overflow parsing in Oracle and Snowflake"}
[tool_result] oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t
oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_na
…[1285 chars elided]…
 t
snowflake | SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t | SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
snowflake | SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t | SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
snowflake | SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t | SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
[tool_use Bash] {"command": "grep -rn \"groupconcat_sql\\|GroupConcat\" sqlglot/generators/*.py sqlglot/generator.py | head -40; echo ----; sed -n 80,100p sqlglot/parsers/oracle.py; echo ----; grep -n \"GroupConcat\" -A6 sqlglot/expressions/aggregate.py | head -30", "description": "Check GroupConcat generator usage across dialects"}
[tool_result] sqlglot/generators/databricks.py:8:    groupconcat_sql,
sqlglot/generators/databricks.py:47:            exp.GroupConcat: groupconcat_sql,
sqlglot/generators/doris.py:60:        exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/bigquery.py:26:    groupconcat_sql,
sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/clickhouse.py:419:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/duckdb.p
…[2299 chars elided]…
   QUERY_RESTRICTIONS: t.ClassVar[OPTIONS_TYPE] = {
        "WITH": (
            ("READ", "ONLY"),
            ("CHECK", "OPTION"),
        ),
    }

    def _parse_dbms_random(self) -> exp.Expr | None:
        if self._match_text_seq(".", "VALUE"):
----
133:class GroupConcat(Expression, AggFunc):
134-    arg_types = {"this": True, "separator": False, "on_overflow": False}
135-
136-
137-class Grouping(Expression, AggFunc):
138-    arg_types = {"expressions": True}
139-    is_var_len_args = True
[tool_use Bash] {"command": "grep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/oracle.py; grep -n \"^from\\|^import\\|    groupconcat\\|rename_func,\\|^)\" sqlglot/generators/oracle.py | head -30; sed -n 20,60p sqlglot/parsers/oracle.py; sed -n 335,345p sqlglot/generators/exasol.py; cat > /tmp/probe2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-
…[221 chars elided]…
ER BY y) FROM t\"]:\n    e = parse_one(q, read=\"trino\"); print(repr(e.find(__import__('sqlglot').exp.GroupConcat)) [:300]); print(e.sql(\"trino\"))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe2.py", "description": "Inspect Oracle generator and Trino overflow round-trip"}
[tool_result] 65:    TRANSFORMS = {
66-        **generator.Generator.TRANSFORMS,
67-        exp.DateStrToDate: lambda self, e: self.func(
68-            "TO_DATE", e.this, exp.Literal.string("YYYY-MM-DD")
1:from __future__ import annotations
4:from sqlglot import exp, generator, transforms
5:from sqlglot.dialects.dialect import (
7:    rename_func,
11:)


class OracleParser(parser.Parser):
    WINDOW_BEFORE_PAREN_TOKENS = {TokenType.OVER, TokenType.KEEP}
    VALUES_FOLLOWED_BY_PAREN = False

    FUNCTIONS = {
…[2329 chars elided]…
r(this=x, quoted=False)),
  separator=Literal(this=',', is_string=True))
SELECT LISTAGG(x, ',') FROM t
GroupConcat(
  this=Order(
    this=Column(
      this=Identifier(this=x, quoted=False)),
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=y, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this=',', is_string=True),
  on_overflow=OverflowTruncat
SELECT LISTAGG(x, ',' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY y) FROM t
[tool_use Bash] {"command": "sed -n 1,12p sqlglot/generators/oracle.py; sed -n 65,80p sqlglot/generators/oracle.py; grep -n \"exp.Trim\\|exp.Mod\\|exp.Ln\\|exp.Length\" sqlglot/generators/oracle.py | head -5", "description": "View Oracle generator imports and TRANSFORMS"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.DateStrToDate: lambda self, e: self.func(
            "TO_DATE", e.this, exp.Literal.string("YYYY-MM-DD")
        ),
        exp.DateTrunc: lambda self, e: self.func("TRUNC", e.this, e.unit),
        e
…[53 chars elided]…
     exp.ILike: no_ilike_sql,
        exp.LogicalOr: rename_func("MAX"),
        exp.LogicalAnd: rename_func("MIN"),
        exp.Mod: rename_func("MOD"),
        exp.Rand: rename_func("DBMS_RANDOM.VALUE"),
        exp.Select: transforms.preprocess(
            [
                transforms.eliminate_distinct_on,
                transforms.eliminate_qualify,
14:def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
75:        exp.Mod: rename_func("MOD"),
96:        exp.Trim: _trim_sql,
[assistant] Now the edits: register `LISTAGG` in the Oracle parser (as Snowflake and Exasol do) and give Oracle a `GroupConcat` generator that keeps `ON OVERFLOW`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"L2_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"NVL\": lambda args: build_coalesce(args, is_nvl=True),", "new_string": "        \"L2_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        \"NVL\": lambda args: build_coalesce(args, is_nvl=True),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None, on_overflow=True),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] I put the `LISTAGG` entry in `FUNCTIONS`, but it takes `self`, so it belongs in `FUNCTION_PARSERS` (as Snowflake does). Fixing that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        \"NVL\": lambda args: build_coalesce(args, is_nvl=True),", "new_string": "        \"NVL\": lambda args: build_coalesce(args, is_nvl=True),"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/probe3.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-b63a38b63828/20261026-142857-oracle-dialect-support-listagg-e/base-1\")\nfrom sqlglot import parse_one\nqs = [\n \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\",\n \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH
…[867 chars elided]…
', e.sql(\"duckdb\"), '\\n   snowflake:', e.sql(\"snowflake\"))\n    except Exception as ex:\n        print('ERR', type(ex).__name__, str(ex)[:300])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe3.py", "description": "Verify Oracle LISTAGG overflow round-trips after change"}
[tool_result] SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t 
   duckdb: SELECT LISTAGG(last_name, '; ' ORDER BY last_name) FROM t 
   snowflake: SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t 
   duckdb: SELECT LISTAGG(last_name, '; ' ORDER BY last_name) FROM t 
   snowflake: SELECT LISTAGG(last_name, '; ') WIT
…[1390 chars elided]…
 
   duckdb: SELECT LISTAGG(DISTINCT last_name, '; ' ORDER BY last_name) FROM t 
   snowflake: SELECT LISTAGG(DISTINCT last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name DESC) OVER (PARTITION BY d) FROM t 
   duckdb: SELECT LISTAGG(last_name, '; ' ORDER BY last_name DESC NULLS FIRST) OVER (PARTITION BY d) FROM t 
   snowflake: SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name DESC) OVER (PARTITION BY d) FROM t
[assistant] Parsing and round-trip now work. One thing I'll flag rather than fix: a bare `LISTAGG(x)` in Oracle has no delimiter, but the shared `GroupConcat` AST leaves it unset, so DuckDB fills in `','` (Snowflake has the same behavior today). Next, the tests. Checking the end of the Oracle test file and the cross-dialect output first.
[tool_use Bash] {"command": "tail -30 tests/dialects/test_oracle.py; grep -n \"    def test_\" tests/dialects/test_oracle.py | tail -5; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nfor s in [\\\"LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name)\\\", \\\"LISTAGG(DISTINCT last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name)\\\"]:\n    e = parse_one(s, read='oracle')\n    for d in ['trino','postgres','oracle']: print(d, e.sql(d))\n\"", "description": "Check test file tail and cross-dialect LISTAGG output"}
[tool_result]         ) AS
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
        """Test that
…[1039 chars elided]…
_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name)
postgres STRING_AGG(last_name, '; ' ORDER BY last_name)
oracle LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name)
trino LISTAGG(DISTINCT last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name)
postgres STRING_AGG(DISTINCT last_name, '; ' ORDER BY last_name)
oracle LISTAGG(DISTINCT last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name)
[assistant] Adding a test method at the end of the Oracle test class.
[tool_use Bash] {"command": "cat >> tests/dialects/test_oracle.py <<'EOF'\n\n    def test_listagg(self):\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t\"\n        )\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM t\"\n        )\n        self.validate_id
…[875 chars elided]…
ITH COUNT) WITHIN GROUP (ORDER BY last_name)\",\n            },\n        )\nEOF\n<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Add LISTAGG tests to Oracle dialect tests and run them"}
[tool_result] .........................                                                 [100%]
25 passed, 215 subtests passed in 0.16s
[assistant] Oracle tests pass. Now the full suite using the project's configured command, plus a lint/format check on the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30; <work>/env-sqlglot/bin/python -m ruff check sqlglot/
…[36 chars elided]…
/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Run full test suite, ruff lint, and format check"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.....................................................................................................................................................
…[327 chars elided]…
............ [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
.............................................. [ 86%]
................................................................................................................................................                                         [100%]
1094 passed, 17874 subtests passed in 52.93s
All checks passed!
3 files already formatted
[tool_use Bash] {"command": "git status --short && git diff -- sqlglot/", "description": "Show final source diff"}
[tool_result]  M sqlglot/generators/oracle.py
 M sqlglot/parsers/oracle.py
 M tests/dialects/test_oracle.py
diff --git a/sqlglot/generators/oracle.py b/sqlglot/generators/oracle.py
index d3f2e99e2..1e6d334e2 100644
--- a/sqlglot/generators/oracle.py
+++ b/sqlglot/generators/oracle.py
@@ -3,6 +3,7 @@ from __future__ import annotations
 
 from sqlglot import exp, generator, transforms
 from sqlglot.dialects.dialect import (
+    groupconcat_sql,
     no_ilike_sql,
     rename_func,
     strposition_sql,
@@ -69,
…[441 chars elided]…
t/parsers/oracle.py b/sqlglot/parsers/oracle.py
index 169b1bcd7..0aede77c3 100644
--- a/sqlglot/parsers/oracle.py
+++ b/sqlglot/parsers/oracle.py
@@ -56,6 +56,7 @@ class OracleParser(parser.Parser):
         "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
         "JSON_ARRAYAGG": lambda self: self._parse_oracle_json_arrayagg(),
         "JSON_EXISTS": lambda self: self._parse_json_exists(),
+        "LISTAGG": lambda self: self._parse_string_agg(),
     }
 
     PROPERTY_PARSERS = {
[assistant] Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff lint and format are clean. I haven't committed anything.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` now goes through the shared `_parse_string_agg()` parser, the same route Snowflake and Exasol take. Before this, Oracle failed with `Expecting )` at `ON`.
- `sqlglot/generators/oracle.py`: added a `GroupConcat` generator that emits `LISTAGG(x, sep ON OVERFLOW ...) WITHIN GROUP (ORDER BY ...)`. It uses the shared `groupco
…[496 chars elided]…
't actually support this clause, so I left it alone. The clause comes from Trino's support.
- Oracle's `LISTAGG(x)` with no delimiter is now a `GroupConcat` with no separator, and DuckDB fills in `','` when transpiling. Snowflake has the same behavior today. Fixing it means deciding whether the AST should carry an explicit `''`, which changes Oracle identity output, so I didn't.
- Trino drops `ON OVERFLOW` when `WITHIN GROUP` is absent, e.g. `LISTAGG(x, ',' ON OVERFLOW ERROR)`. That's an existing bug in the shared parser. Oracle always requires `WITHIN GROUP`, so it doesn't affect this change.
