# trajectory base-1

final message:
Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`, and other dialects drop it with an unsupported warning. The full suite passes (1081 tests, 17835 subtests) and ruff format and lint are clean.

What changed:

- **Parser** (`sqlglot/parser.py`): `_parse_when_matched` reads an optional `WHERE` into the existing `where` arg of `Update` and `Insert`. The `UPDATE *` and `INSERT *` forms are unchanged.
- **Generator** (`sqlglot/generator.py`): `when_sql` emits the clause when the new flag `MERGE_WHEN_WHERE_SUPPORTED` is set. Otherwise it calls `self.unsupported(...)` and drops the clause.
- **Oracle** (`sqlglot/generators/oracle.py`): sets the flag to `True`.
- **Test** (`tests/dialects/test_oracle.py`): a new `test_merge_when_where` covers the Oracle round-trip, the DuckDB output with the clause dropped, and the warning text.

Decisions to check:

- **Flag default is `False`.** Only Oracle opts in, so the base `sqlglot` dialect also drops the clause with a warning. Base-dialect output is therefore lossy for this syntax. Parsing is shared, so any dialect can read it. If you want the base dialect to keep it, the flip is one line, but it then needs `False` in every dialect that lacks support.
- **Oracle's `DELETE WHERE` sub-clause is not handled.** Oracle also allows `UPDATE SET ... WHERE ... DELETE WHERE ...`. That was outside the request, so I did not touch it.
- **mypy was not run.** The pre-commit config includes mypy; the changes are small and typed, but I did not verify them with it.

## events
[assistant] I'll start by finding how MERGE is parsed and generated, and how Oracle currently handles it.
[tool_use Bash] {"command": "grep -n \"Merge\\|_parse_when_matched\\|WhenMatched\\|NOT MATCHED\\|MATCHED\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/oracle.py | head -80", "description": "Find MERGE-related code across parser, generator, expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> 
…[1428 chars elided]…
 default=default))
sqlglot/parser.py:4183:            elif self._match_text_seq("WITH", "UNMATCHED", "ROWS"):
sqlglot/parser.py:4184:                text += " WITH UNMATCHED ROWS"
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8905:    def _parse_when_matched(self) -> exp.Whens:
sqlglot/parser.py:8910:            self._match_text_seq("MATCHED")
[tool_use Bash] {"command": "sed -n 8880,8940p sqlglot/parser.py && echo ---- && sed -n 4425,4500p sqlglot/generator.py && echo ---- && grep -n \"class Whens\\|class When\\b\\|class When(\" -A 12 sqlglot/expressions/*.py | head -40", "description": "Show MERGE parser, generator, and When expression definitions"}
[tool_result]                 update_options=update_options,
            )
        )

    def _parse_merge(self) -> exp.Merge:
        self._match(TokenType.INTO)
        target = self._parse_table()

        if target and self._match(TokenType.ALIAS, advance=False):
            target.set("alias", self._parse_table_alias())

        self._match(TokenType.USING)
        using = self._parse_table()

        return self.expression(
            exp.Merge(
                this=target,
                using=using,
…[4971 chars elided]…
t")
----
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py:521:class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[tool_use Bash] {"command": "grep -rn \"class Whens\\|class When(\" sqlglot/ ; grep -n \"MERGE\\|Merge\\|merge\" sqlglot/dialects/oracle.py sqlglot/dialects/dialect.py | head; grep -rn \"unsupported_args\\|self.unsupported(\" sqlglot/generator.py | head -5; grep -rln \"MERGE\" tests/dialects/ | head -20", "description": "Locate When expression class and Oracle MERGE handling"}
[tool_result] sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py:521:class Whens(Expression):
sqlglot/dialects/dialect.py:238:        # Merge class-defined INVERSE_TIME_MAPPING with auto-generated mappings
sqlglot/dialects/dialect.py:2030:def merge_without_target_sql(self: Generator, expression: exp.Merge) -> str:
sqlglot/dialects/dialect.py:2063:    return self.merge_sql(expression)
sqlglot/generator.py:30:def unsupported_args(
sqlglot/generator.py:1125:            self.unsuppo
…[184 chars elided]…
erator.py:1558:                self.unsupported("Unsupported transpilation from BINARY/BLOB hex string")
sqlglot/generator.py:1640:            self.unsupported(
tests/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_spark.py
tests/dialects/test_oracle.py
tests/dialects/test_teradata.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_tsql.py
tests/dialects/test_mysql.py
tests/dialects/test_postgres.py
tests/dialects/test_clickhouse.py
[tool_use Bash] {"command": "sed -n 8940,8975p sqlglot/parser.py && echo ---- && sed -n 2025,2065p sqlglot/dialects/dialect.py && echo ---- && grep -n \"MERGE\" tests/dialects/test_oracle.py | head -20 && grep -n \"class Oracle\\|class Generator\\|class Parser\\|MATCHED\" sqlglot/dialects/oracle.py | head; grep -n \"class Insert(\\|class Update(\" -A 12 sqlglot/expressions/dml.py | head -40", "description": "Read rest of parser, merge helper, Oracle tests, and Insert/Update classes"}
[tool_result]                             expressions=self._match(TokenType.SET)
                            and self._parse_csv(self._parse_equality)
                        )
                    )
            elif self._match(TokenType.DELETE):
                then = self.expression(exp.Var(this=self._prev.text))
            else:
                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)

            whens.append(
                self.expression(
                    exp.When(matched=matched
…[3295 chars elided]…
 False,
202-        "returning": False,
203-        "overwrite": False,
204-        "exists": False,
205-        "alternative": False,
206-        "where": False,
--
293:class Update(Expression, DML):
294-    arg_types = {
295-        "with_": False,
296-        "this": False,
297-        "expressions": False,
298-        "from_": False,
299-        "where": False,
300-        "returning": False,
301-        "order": False,
302-        "limit": False,
303-        "options": False,
304-    }
305-
[assistant] The parser already has `where` slots on `Insert` and `Update`, and `when_sql` builds the branch text by hand, so the change is small. Next I'll check the existing flag convention and how tests assert unsupported warnings.
[tool_use Bash] {"command": "grep -rn \"MATCHED_BY_SOURCE\" sqlglot/ | head; echo ----; sed -n 310,325p sqlglot/generator.py; echo ----; sed -n 885,905p tests/dialects/test_oracle.py; echo ----; grep -rn \"unsupported_level=ErrorLevel.WARN\\|assertLogs\\|self.assertRaises\" tests/dialects/test_oracle.py | head -5; grep -n \"def validate_all\" -A 25 tests/dialects/test_dialect.py | head -50; echo ----; sed -n 1,40p sqlglot/dialects/oracle.py | grep -n \"import\"; grep -n \"class Generator\" -A 30 sqlglot/dialects/oracle.py | head -50", "description": "Inspect flag convention, Oracle tests, and Oracle generator"}
[tool_result] sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/generators/snowflake.py:378:    MATCHED_BY_SOURCE = False
----

    # Whether the EXCEPT and INTERSECT operations can return duplicates
    EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = True

    # Wrap derived values in parens, usually standard but spark doesn't support it
    WRAP_DERIVED_VALUES = True

    # Whether c
…[2349 chars elided]…
               unsupported_level=ErrorLevel.IGNORE,
89-                        pretty=pretty,
90-                        identify=identify,
91-                    ),
92-                    sql,
93-                )
----
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, tokens
6:from sqlglot.dialects.dialect import (
10:from sqlglot.generators.oracle import OracleGenerator
11:from sqlglot.parsers.oracle import OracleParser
12:from sqlglot.tokens import TokenType
[assistant] The layout has moved into `sqlglot/generators/` and `sqlglot/parsers/`. The generator flag convention is `MATCHED_BY_SOURCE`, which Snowflake overrides. Next I'll look at the Oracle generator/parser files and how existing tests assert unsupported warnings.
[tool_use Bash] {"command": "ls sqlglot/generators sqlglot/parsers | head -80; echo ----; grep -n \"class OracleGenerator\" -A 25 sqlglot/generators/oracle.py | head -40; echo ----; grep -rn \"unsupported_level=ErrorLevel.WARN\\|assertLogs\\|_unsupported\\|unsupported_messages\" tests/dialects/*.py tests/*.py | head -8", "description": "Inspect Oracle generator and test warning assertions"}
[tool_result] sqlglot/generators:
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py

sqlglot/parsers:
__init__.py
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
du
…[1422 chars elided]…
 self.assertLogs(generator_logger, level="WARNING") as cm:
tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2130:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2139:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2147:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2167:        with self.assertLogs(helper_logger) as cm:
[tool_use Bash] {"command": "sed -n 5040,5075p tests/dialects/test_dialect.py; echo ----; grep -n \"def merge\\|merge\" tests/dialects/test_dialect.py | head -20; echo ----; grep -n \"def when_sql\\|def _parse_when_matched\\|MERGE\" sqlglot/generators/*.py sqlglot/parsers/*.py | head; echo ----; cat .venv 2>/dev/null; ls <work>/env-sqlglot/bin/python && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Check unsupported-warning test pattern and baseline Oracle tests"}
[tool_result]         assert_custom_duckdb_sql("INITCAP(col, NULL)", includes=("REGEXP_MATCHES(", "REPLACE("))
        assert_custom_duckdb_sql("INITCAP(col, ' ')", includes=("' '",))
        assert_custom_duckdb_sql("INITCAP(col, '@')", includes=("'@'",), excludes=("CHR(",))
        assert_custom_duckdb_sql("INITCAP(col, '_@')", includes=("'_@'",))
        assert_custom_duckdb_sql(r"INITCAP(col, '\\\\')", includes=("\\\\",))
        assert_custom_duckdb_sql(
            "INITCAP(col, '\u000b')",
            
…[1741 chars elided]…
sers/spark2.py:88:        "MERGEJOIN": lambda self: self._parse_join_hint("MERGEJOIN"),
sqlglot/parsers/tsql.py:84:    "MERGE": ("JOIN", "UNION"),
sqlglot/parsers/tsql.py:376:    JOIN_HINTS = {"LOOP", "HASH", "MERGE", "REMOTE"}
sqlglot/parsers/tsql.py:463:        if self._match(TokenType.MERGE):
----
<work>/env-sqlglot/bin/python
.......................                                                       [100%]
23 passed, 211 subtests passed in 0.35s
[assistant] Baseline Oracle tests pass (23 tests, 211 subtests). Design, which I'll state in the final message:

- **Parser (base `parser.py`)**: parse an optional `WHERE` on the non-star `UPDATE` and `INSERT` branches into the existing `where` args of `Update`/`Insert`.
- **Generator (base `generator.py`)**: new flag `MERGE_WHEN_WHERE_SUPPORTED`, default `False`. When the flag is off and a `WHERE` is present, call `self.unsupported(...)` and drop the clause. Oracle sets it to `True`.

I'll confirm the `_parse_where` signature first.
[tool_use Bash] {"command": "grep -n \"def _parse_where\" -A 3 sqlglot/parser.py; grep -n \"def unsupported\" -A 3 sqlglot/generator.py", "description": "Confirm _parse_where and unsupported signatures"}
[tool_result] 5183:    def _parse_where(self, skip_where_token: bool = False) -> exp.Where | None:
5184-        if not skip_where_token and not self._match(TokenType.WHERE):
5185-            return None
5186-
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
[assistant] Now the parser edits, for the non-star `INSERT` and `UPDATE` branches:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                    then = self.expression(\n                        exp.Insert(\n                            this=exp.var(\"ROW\")\n                            if self._match_text_seq(\"ROW\")\n                        
…[273 chars elided]…
   exp.Insert(\n                            this=exp.var(\"ROW\")\n                            if self._match_text_seq(\"ROW\")\n                            else self._parse_value(values=False),\n                            expression=self._match_text_seq(\"VALUES\") and self._parse_value(),\n                            where=self._parse_where(),\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality)\n                        )\n                    )", "new_string": "                    then = self.expression(\n                        exp.Update(\n                            expressions=self._match(TokenType.SET)\n                            and self._parse_csv(self._parse_equality),\n                            where=self._parse_where(),\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next, the generator: the flag, the `when_sql` change, and Oracle opting in.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether the WHERE clause is allowed on the UPDATE and INSERT branches of a MERGE WHEN clause\n    MERGE_WHEN_WHERE_SUPPORTED = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        then_expression = expression.args.get(\"then\")\n        if isinstance(then_expression, exp.Insert):\n            this = self.sql(then_expression, \"this\")\n            this = f\"INSERT {this}\" if this else
…[1585 chars elided]…
        then = f\"UPDATE {self.sql(then_expression, 'expressions')}\"\n            else:\n                expressions_sql = self.expressions(then_expression)\n                then = f\"UPDATE SET{self.sep()}{expressions_sql}\" if expressions_sql else \"UPDATE\"\n\n        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_WHEN_WHERE_SUPPORTED = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now I'll check the behaviour directly: Oracle round-trip, a transpile to a non-supporting dialect with the warning captured, and the base dialect.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nsql = 'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 DELETE WHERE 1=1 WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a) WHERE s.id > 1'\nsql2 = 'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN
…[252 chars elided]…
for d in ['duckdb','tsql','sqlglot']:\n    e = sqlglot.parse_one(sql2, read='oracle')\n    print(d, '=>', e.sql(d, unsupported_level=ErrorLevel.WARN))\ntry:\n    sqlglot.parse_one(sql2, read='oracle').sql('duckdb', unsupported_level=ErrorLevel.RAISE)\nexcept Exception as ex: print('RAISE:', type(ex).__name__, ex)\n\"\n", "description": "Check Oracle round-trip and unsupported transpile behaviour"}
[tool_result ERROR] Exit code 1
WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
Traceback (most recent call last):
  File "<string>", line 10, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/core.py", line 1097,
…[812 chars elided]…
.id, s.a)  WHERE s.id > 1']
['MERGE INTO t\nUSING s\nON t.id = s.id\nWHEN MATCHED THEN UPDATE SET\n  t.a = s.a \nWHERE\n  s.a > 0\nWHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a) \nWHERE\n  s.id > 1']
duckdb => MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
tsql => MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
[assistant] Two things to fix. The output has a double space before `WHERE`, because `where_sql` already emits its own leading space, so my extra space is redundant. The `'sqlglot'` dialect name is simply not registered here, so I'll use the default dialect instead. The warnings firing once per clause is expected.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "                where = f\" {self.sql(then_expression, 'where')}\"", "new_string": "                where = self.sql(then_expression, \"where\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel, UnsupportedError\nsql2 = 'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a) WHERE s.id > 1'\nprint(sqlglot.transpile(sql2, read='oracle', write='oracle'
…[558 chars elided]…
rorLevel.RAISE)\nexcept UnsupportedError as ex: print('RAISE:', ex)\nprint(sqlglot.parse_one('MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id) VALUES (s.id)', read='oracle').sql('oracle'))\nprint(sqlglot.parse_one(sql2, read='oracle').sql('oracle', pretty=True))\n\" 2>&1\n", "description": "Re-run behaviour checks after whitespace fix"}
[tool_result] MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a) WHERE s.id > 1
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.a = s.a
WHERE
  s.a > 0
WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
WHERE
  s.id > 1
duckdb: MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
tsql  : MERGE INTO t US
…[193 chars elided]…
t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
RAISE: WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported

WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHEN NOT MATCHED THEN INSERT (t.id) VALUES (s.id)
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.a = s.a
WHERE
  s.a > 0
WHEN NOT MATCHED THEN INSERT (t.id, t.a) VALUES (s.id, s.a)
WHERE
  s.id > 1
[assistant] Oracle round-trips, the non-supporting dialects drop the clause, and `ErrorLevel.RAISE` raises. Next, tests. I'll look at the Oracle test file's imports and the enclosing test name to place them.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_oracle.py; grep -n \"    def test_\" tests/dialects/test_oracle.py | awk -F: '$1<900' | tail -2; grep -n \"generator_logger\" tests/dialects/test_dialect.py | head -2", "description": "Inspect Oracle test imports and nearby test names"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
884:    def test_merge_builder_alias(self):
898:    def test_pseudocolumns(self):
17:from sqlglot.generator import logger as generator_logger
5058:                with self.assertLogs(generator_logger, level="WARNING") as cm:
[assistant] I'll add one Oracle test covering identity round-trip, the drop on a non-supporting dialect, and the warning, placed after `test_merge_builder_alias`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_when_where(self):\n        self.validate_identity(\n            \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = 
…[553 chars elided]…
.assertLogs(generator_logger, level=\"WARNING\") as cm:\n            parse_one(\n                \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0\",\n                read=\"oracle\",\n            ).sql(\"duckdb\")\n        self.assertIn(\"WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported\", cm.output[0])\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "from sqlglot.optimizer.qualify import qualify\n", "new_string": "from sqlglot.generator import logger as generator_logger\nfrom sqlglot.optimizer.qualify import qualify\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-110245-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now the project's check command from the harness instructions, the full suite:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite with project's pytest command", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
................................................................................................... [ 38%]
........................................
…[241 chars elided]…
]
........................................................................................................................... [ 74%]
........................................................................................................................................................................................................................... [ 94%]
....................... [ 96%]
.....................................                     [100%]
1081 passed, 17835 subtests passed in 41.09s
[assistant] The full suite passes (1081 tests, 17835 subtests), including the new test. Next, the repo's lint and format checks on the files I touched.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff --version && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py; $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py; git status --short", "description": "Run ruff format and lint checks on changed files"}
[tool_result] ruff 0.15.6
Would reformat: tests/dialects/test_oracle.py
1 file would be reformatted, 3 files already formatted
All checks passed!
 M sqlglot/generator.py
 M sqlglot/generators/oracle.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff tests/dialects/test_oracle.py 2>&1 | head -30", "description": "Show the formatting diff for the test file"}
[tool_result] --- tests/dialects/test_oracle.py
+++ tests/dialects/test_oracle.py
@@ -912,7 +912,9 @@
                 "MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.a = s.a WHERE s.a > 0",
                 read="oracle",
             ).sql("duckdb")
-        self.assertIn("WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported", cm.output[0])
+        self.assertIn(
+            "WHERE clause in MERGE WHEN MATCHED/NOT MATCHED is not supported", cm.output[0]
+        )
 
     def test_pseudocolumns(self):
         ast = self.validate_identity(

1 file would be reformatted
[assistant] The only formatting issue is one line in my new test, so I'll apply the formatter to that file and re-run the Oracle tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_oracle.py && $PY -m ruff format --check sqlglot tests/dialects/test_oracle.py | tail -1 && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -2 && git diff --stat", "description": "Apply formatter and re-run Oracle tests with diff stat"}
[tool_result] 1 file reformatted
174 files already formatted
........................                                                     [100%]
24 passed, 212 subtests passed in 0.27s
 sqlglot/generator.py          | 14 +++++++++++++-
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  4 +++-
 tests/dialects/test_oracle.py | 21 +++++++++++++++++++++
 4 files changed, 38 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: tests/dialects/test_oracle.py. Call Read before editing.]
[assistant] Let me review the final source diff before reporting.
[tool_use Bash] {"command": "git diff -- sqlglot/", "description": "Show the final source diff"}
[tool_result] diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index d9f08c480..ca9cf3610 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -320,6 +320,9 @@ class Generator:
     # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
     MATCHED_BY_SOURCE = True
 
+    # Whether the WHERE clause is allowed on the UPDATE and INSERT branches of a MERGE WHEN clause
+    MERGE_WHEN_WHERE_SUPPORTED = False
+
     # Whether the INTERVAL expression works only with values like '1 day'
     SINGL
…[2088 chars elided]…
kenType.UPDATE):
@@ -8938,7 +8939,8 @@ class Parser:
                     then = self.expression(
                         exp.Update(
                             expressions=self._match(TokenType.SET)
-                            and self._parse_csv(self._parse_equality)
+                            and self._parse_csv(self._parse_equality),
+                            where=self._parse_where(),
                         )
                     )
             elif self._match(TokenType.DELETE):
[assistant] Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`, and other dialects drop it with an unsupported warning. The full suite passes (1081 tests, 17835 subtests) and ruff format and lint are clean.

What changed:

- **Parser** (`sqlglot/parser.py`): `_parse_when_matched` reads an optional `WHERE` into the existing `where` arg of `Update` and `Insert`. The `UPDATE *` and `INSERT *` forms are unchanged.
- **Generator** (`sqlglot/generator.py`): `when_sql` emits the clause when the new flag `MERGE_WHEN_WHERE_SUPPORTED` is set. Otherwise it calls `
…[361 chars elided]…
 so the base `sqlglot` dialect also drops the clause with a warning. Base-dialect output is therefore lossy for this syntax. Parsing is shared, so any dialect can read it. If you want the base dialect to keep it, the flip is one line, but it then needs `False` in every dialect that lacks support.
- **Oracle's `DELETE WHERE` sub-clause is not handled.** Oracle also allows `UPDATE SET ... WHERE ... DELETE WHERE ...`. That was outside the request, so I did not touch it.
- **mypy was not run.** The pre-commit config includes mypy; the changes are small and typed, but I did not verify them with it.
