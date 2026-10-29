# trajectory base-1

final message:
Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`. Other dialects drop it with an unsupported warning. The full suite passes (1081 tests), and ruff and mypy are clean on the touched files. I haven't committed anything.

What changed:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, an optional `WHERE` is stored in that node's existing `where` arg. I didn't use `When.condition`, because that is the `WHEN ... AND ...` predicate, which is a different thing. The parser change is in the base parser, so any dialect can read Oracle's syntax.
- **Generator** (`sqlglot/generator.py`): new `MERGE_WHERE_CLAUSE = False` flag, next to `MATCHED_BY_SOURCE`. `when_sql` emits the `WHERE` when the flag is set. Otherwise it calls `self.unsupported("MERGE ... WHEN ... WHERE clause is not supported")` and drops the clause.
- **Oracle** (`sqlglot/generators/oracle.py`): sets `MERGE_WHERE_CLAUSE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_where` checks the Oracle round-trip with both clauses, and checks that transpiling to postgres drops the clause and logs the warning.

Things to know:

- The warning is logged once per dropped clause, so a MERGE with both clauses warns twice.
- `DELETE WHERE` (Oracle's other clause inside `UPDATE`) is not handled. The task didn't ask for it.
- Only Oracle enables the flag. Other dialects that might support the clause would need the same one-line change.

## events
[assistant] I'll start by checking how the parser and generator currently handle MERGE, and what the Oracle dialect already does with it.
[tool_use Bash] {"command": "git status --short | head && grep -n \"Merge\\|_parse_when_matched\\|WhenMatched\\|class When\" sqlglot/expressions.py | head -40 && grep -n \"MERGE\\|Merge\\|merge\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/oracle.py | head -60", "description": "Check repo state and find MERGE-related code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:320:    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:700:        exp.MergeBlockRatioProperty: exp.Properties.Location.POST_NAME,
sqlglot/generator.py:744:        exp.MergeTreeTTL: exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:2032:    def mergeblockratioproperty_sql(self, expression: exp.MergeBlockRatioProperty) -> str:
sqlglot/generator.py:2034:            return "NO 
…[1805 chars elided]…
ion(this=this, to_volume=self._parse_string())
sqlglot/parser.py:2219:            exp.MergeTreeTTL(
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:3039:    ) -> exp.MergeBlockRatioProperty:
sqlglot/parser.py:3042:                exp.MergeBlockRatioProperty(
sqlglot/parser.py:3047:        return self.expression(exp.MergeBlockRatioProperty(no=no, default=default))
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8895:            exp.Merge(
[tool_use Bash] {"command": "git status --short | head; ls; grep -n \"class Merge\\|class When\\b\\|class Whens\" -A 14 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -80", "description": "Check repo state and locate Merge expression classes"}
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
sqlglot/expressions/ddl.py:310:class MergeTreeTTLAction(Expression):
sqlglot/expressions/ddl.py-311-    arg_types = {
sqlglot/expressions/ddl.py-312-        "this": True,
sqlglot/expressions/ddl.py-313-        "delete": False,
sqlglot/expressions/ddl.py-314-        "recompress": False,
sqlglot/
…[2465 chars elided]…
.py-516-
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py:521:class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
[assistant] The `When` node has a `condition` arg, which is the `WHERE` slot. Next I'll read the parser's MERGE and WHEN parsing, plus the generator's `merge_sql`.
[tool_use Bash] {"command": "sed -n 8880,8990p sqlglot/parser.py; echo ----; grep -n \"def _parse_when_matched\\|WHEN_MATCHED\\|when_matched\" sqlglot/parser.py | head", "description": "Read MERGE and WHEN parsing code"}
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
…[3524 chars elided]…
exp.Expr:
        self._match_text_seq("TRANSACTION")
        characteristics = self._parse_csv(
            lambda: self._parse_var_from_options(self.TRANSACTION_CHARACTERISTICS)
        )
        return self.expression(
            exp.SetItem(expressions=characteristics, kind="TRANSACTION", global_=global_)
        )

----
1056:        exp.Whens: lambda self: self._parse_when_matched(),
8900:                whens=self._parse_when_matched(),
8905:    def _parse_when_matched(self) -> exp.Whens:
[tool_use Bash] {"command": "sed -n 4465,4560p sqlglot/generator.py; echo ----; grep -n \"def whens_sql\\|def when_sql\\|unsupported_args\\|MERGE_\" sqlglot/generator.py | head -30", "description": "Read merge_sql and whens generator code"}
[tool_result]     def whens_sql(self, expression: exp.Whens) -> str:
        return self.expressions(expression, sep=" ", indent=False)

    def merge_sql(self, expression: exp.Merge) -> str:
        table = expression.this
        table_alias = ""

        hints = table.args.get("hints")
        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
            table_alias = f" AS {self.sql(table.ar
…[3449 chars elided]…
ession, key="sorted_by", flat=True)
        sorted_by = f" SORTED BY ({sorted_by})" if sorted_by else ""
        buckets = self.sql(expression, "buckets")
        return f"CLUSTERED BY ({expressions}){sorted_by} INTO {buckets} BUCKETS"

----
30:def unsupported_args(
2529:    @unsupported_args("expressions")
4443:    def when_sql(self, expression: exp.When) -> str:
4466:    def whens_sql(self, expression: exp.Whens) -> str:
4500:    @unsupported_args("format")
5440:    @unsupported_args("format")
[assistant] The `When` node's `condition` is the `AND` predicate on the WHEN itself, so the branch-level `WHERE` belongs somewhere else. I'll check `Update`/`Insert` arg types, `when_sql`, and the existing Oracle MERGE tests.
[tool_use Bash] {"command": "sed -n 4440,4466p sqlglot/generator.py; echo ----; grep -n \"class Insert(\\|class Update(\" -A 16 sqlglot/expressions/dml.py; echo ----; grep -n \"def update_sql\\|def insert_sql\" -A 25 sqlglot/generator.py | head -90; echo ----; grep -n \"MERGE\" tests/dialects/test_oracle.py | head; grep -n \"SUPPORTS_MERGE\\|MERGE\" sqlglot/dialects/oracle.py sqlglot/generator.py | head -20", "description": "Read when/insert/update generators and Oracle MERGE tests"}
[tool_result]     def kwarg_sql(self, expression: exp.Kwarg) -> str:
        return self.binary(expression, "=>")

    def when_sql(self, expression: exp.When) -> str:
        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
        condition = self.sql(expression, "condition")
        condition = f" AND {condition}" if condition else ""

        then_expression = expression.args.get("then")
 
…[5056 chars elided]…
. WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:2034:            return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:            return "DEFAULT MERGEBLOCKRATIO"
sqlglot/generator.py:2039:        return f"MERGEBLOCKRATIO={self.sql(expression, 'this')}{percent}"
sqlglot/generator.py:4475:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
sqlglot/generator.py:4497:            f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
[assistant] `Insert` and `Update` both already have a `where` arg, so the branch `WHERE` can live there without a new node type. Before deciding, I need to check how the parser stores INSERT's `where` (Spark's `REPLACE WHERE` uses the same key) and look at the generator flags and Oracle's Generator class.
[tool_use Bash] {"command": "grep -n '\"where\"' sqlglot/parser.py | head -20; echo ----; sed -n 312,330p sqlglot/generator.py; echo ----; grep -n \"class Generator\" -A 30 sqlglot/dialects/oracle.py | head -60; echo ----; grep -n \"def unsupported\" -A3 sqlglot/generator.py | head; echo ----; grep -n \"MATCHED_BY_SOURCE\" sqlglot/dialects/*.py", "description": "Inspect where handling, generator flags, Oracle generator"}
[tool_result] 1505:        TokenType.WHERE: lambda self: ("where", self._parse_where()),
3610:                kwargs["where"] = self._parse_where()
----
    EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = True

    # Wrap derived values in parens, usually standard but spark doesn't support it
    WRAP_DERIVED_VALUES = True

    # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether
…[205 chars elided]…
LOWS_PLURAL_FORM = True

    # Whether limit and fetch are supported (possible values: "ALL", "LIMIT", "FETCH")
    LIMIT_FETCH = "ALL"
----
----
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
----
[assistant] The Oracle dialect file has no `class Generator`, so the layout must have changed. I'll locate Oracle's generator and the existing MERGE-related flags.
[tool_use Bash] {"command": "ls sqlglot/dialects | head -50; ls sqlglot/dialects/oracle* 2>/dev/null; grep -rn \"class Generator\" sqlglot/dialects/oracle* ; grep -rln \"MATCHED_BY_SOURCE\" sqlglot/", "description": "Locate Oracle dialect generator and flag usages"}
[tool_result] __init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
sqlglot/dialects/oracle.py
sqlglot/generator.py
sqlglot/generators/snowflake.py
[tool_use Bash] {"command": "grep -n \"class \\|^    [A-Z_]* = \" sqlglot/dialects/oracle.py | head -80; echo ----; grep -n \"MATCHED_BY_SOURCE\" -B2 -A2 sqlglot/generators/snowflake.py; echo ----; grep -n \"merge\\|Merge\\|MERGE\" sqlglot/dialects/oracle.py | head -20; echo; grep -n \"MERGE\" tests/dialects/test_oracle.py | head -5", "description": "List Oracle dialect classes and flag usage"}
[tool_result] 15:class Oracle(Dialect):
16:    ALIAS_POST_TABLESAMPLE = True
17:    LOCKING_READS_SUPPORTED = True
18:    TABLESAMPLE_SIZE_IS_PERCENT = True
19:    NULL_ORDERING = "nulls_are_large"
20:    ON_CONDITION_EMPTY_BEFORE_ERROR = False
21:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
22:    DISABLES_ALIAS_REF_EXPANSION = True
25:    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
29:    TIME_MAPPING = {
50:    PSEUDOCOLUMNS = {"ROWNUM", "ROWID", "OBJECT_ID", "OBJECT_VALUE", "LEVEL"}
5
…[5 chars elided]…
 class Tokenizer(tokens.Tokenizer):
----
376-    SELECT_KINDS: tuple[str, ...] = ()
377-    PARAMETER_TOKEN = "$"
378:    MATCHED_BY_SOURCE = False
379-    SINGLE_STRING_INTERVAL = True
380-    JOIN_HINTS = False
----

895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
[assistant] Oracle appears to use the base Generator. I'll confirm that and check how the other flags are declared in the Oracle file.
[tool_use Bash] {"command": "grep -n \"Generator\\|Parser\\|SUPPORTS\\|= True\\|= False\" sqlglot/dialects/oracle.py | head -40; wc -l sqlglot/dialects/oracle.py; ls sqlglot/generators | head -50", "description": "Check Oracle generator and flag declarations"}
[tool_result] 10:from sqlglot.generators.oracle import OracleGenerator
11:from sqlglot.parsers.oracle import OracleParser
16:    ALIAS_POST_TABLESAMPLE = True
17:    LOCKING_READS_SUPPORTED = True
18:    TABLESAMPLE_SIZE_IS_PERCENT = True
20:    ON_CONDITION_EMPTY_BEFORE_ERROR = False
21:    ALTER_TABLE_ADD_REQUIRED_FOR_EACH_COLUMN = False
22:    DISABLES_ALIAS_REF_EXPANSION = True
68:        NESTED_COMMENTS = False
88:    Parser = OracleParser
90:    Generator = OracleGenerator
      90 sqlglot/dialects/oracle.py
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
[assistant] The dialects are now split into `sqlglot/generators/<name>.py` and `sqlglot/parsers/<name>.py`. I'll read the Oracle generator's flags and its class header.
[tool_use Bash] {"command": "sed -n 1,80p sqlglot/generators/oracle.py; echo ----; grep -n \"def \\|TRANSFORMS\" sqlglot/generators/oracle.py | head -80", "description": "Read Oracle generator header and method list"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


class Oracl
…[2437 chars elided]…
sql(self, expression: exp.Expr) -> str:
123:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
130:    def coalesce_sql(self, expression: exp.Coalesce) -> str:
134:    def into_sql(self, expression: exp.Into) -> str:
141:    def hint_sql(self, expression: exp.Hint) -> str:
153:    def isascii_sql(self, expression: exp.IsAscii) -> str:
156:    def interval_sql(self, expression: exp.Interval) -> str:
159:    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
[assistant] I have the layout now. Before editing, I'll check whether the Oracle parser overrides the WHEN parsing, and how existing tests assert unsupported warnings for MERGE.
[tool_use Bash] {"command": "grep -rn \"when_matched\\|_parse_merge\" sqlglot/parsers/ | head; echo ----; grep -rn \"WHEN MATCHED THEN UPDATE SET\" tests/ | head -20; echo ----; grep -rn \"unsupported_level=ErrorLevel.IGNORE\\|unsupported_level=\" tests/dialects/test_oracle.py | head -5; sed -n 885,905p tests/dialects/test_oracle.py", "description": "Check Oracle parser overrides and existing MERGE tests"}
[tool_result] sqlglot/parsers/tsql.py:465:            merge = self._parse_merge()
----
tests/test_parser.py:29:                "WHEN MATCHED THEN UPDATE SET target.salary = COALESCE(source.salary, target.salary)",
tests/test_build.py:806:                    "WHEN MATCHED THEN UPDATE SET col1 = source.col1",
tests/test_build.py:812:                "MERGE INTO target_table USING source_table ON target_table.id = source_table.id WHEN MATCHED THEN UPDATE SET col1 = source.col1 WHEN NOT MATCHED THEN INSERT (col1) 
…[4038 chars elided]…
 THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )

    def test_pseudocolumns(self):
        ast = self.validate_identity(
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
        )
        self.assertIsNone(ast.find(exp.Pseudocolumn))

        qualified = qualify(ast, dialect="oracle")
        self.assertIsNotNone(qualified.find(exp.Pseudocolumn))
[assistant] Nothing in the Oracle parser overrides WHEN parsing, so the change lands in the base parser. Last check: how tests assert unsupported-warning output, so the new test matches the existing pattern.
[tool_use Bash] {"command": "grep -rn \"unsupported_level=ErrorLevel.RAISE\\|assertLogs\" tests/dialects/*.py | head -5; grep -n \"def validate_all\" -A 30 tests/dialects/test_dialect.py | grep -n \"unsupported\\|def \\|pretty\" | head", "description": "Find unsupported-warning test pattern in dialect tests"}
[tool_result] tests/dialects/test_clickhouse.py:1729:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2113:                unsupported_level=ErrorLevel.RAISE,
tests/dialects/test_bigquery.py:2120:                unsupported_level=ErrorLevel.RAISE,
tests/dialects/test_bigquery.py:2130:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2139:        with self.assertLogs(helper_logger) as cm:
1:68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
11:78-            pretty (bool): prettify both read and write
21:88-                        unsupported_level=ErrorLevel.IGNORE,
22:89-                        pretty=pretty,
[tool_use Bash] {"command": "sed -n 2125,2145p tests/dialects/test_bigquery.py; grep -n \"helper_logger\" tests/dialects/test_bigquery.py | head -2", "description": "View bigquery unsupported-warning test example"}
[tool_result]         with self.assertRaises(ParseError):
            transpile("DATE_ADD(x, day)", read="bigquery")

    def test_warnings(self):
        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "WITH cte(c) AS (SELECT * FROM t) SELECT * FROM cte",
                "WITH cte AS (SELECT * FROM t) SELECT * FROM cte",
            )

            self.assertIn("Can't push down CTE column names for star queries.", cm.output[0])
            self.assertIn("Named columns are not supported in table alias.", cm.output[1])

        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "SELECT * FROM t AS t(c1, c2)",
                "SELECT * FROM t AS t",
            )

            self.assertIn("Named columns are not supported in table alias.", cm.output[0])
15:from sqlglot.helper import logger as helper_logger
2130:        with self.assertLogs(helper_logger) as cm:
[assistant] I have what I need. The plan:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after the UPDATE/INSERT branch is built, parse an optional `WHERE` into that node's existing `where` arg. This is shared, since the base parser is where WHEN clauses are parsed.
- **Generator** (`sqlglot/generator.py`): a new `MERGE_WHERE_CLAUSE = False` flag, next to `MATCHED_BY_SOURCE`. `when_sql` emits the `WHERE` when the flag is set, and otherwise calls `self.unsupported(...)` and drops it.
- **Oracle** (`sqlglot/generators/oracle.py`): set the flag to `True`.

Starting with the parser:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(", "new_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)):\n                then.set(\"where\", self._parse_where())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    MATCHED_BY_SOURCE = True\n\n", "new_string": "    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN MATCHED THEN UPDATE / WHEN NOT MATCHED THEN INSERT can have a WHERE clause\n    MERGE_WHERE_CLAUSE = False\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        w
…[36 chars elided]…
hen_expression, (exp.Insert, exp.Update)) and then_expression.args.get(\n            \"where\"\n        ):\n            if self.MERGE_WHERE_CLAUSE:\n                where = f\" {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"MERGE ... WHEN ... WHERE clause is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_WHERE_CLAUSE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now the tests. The unsupported-warning assertion depends on which logger the generator writes to, so I'll confirm that first.
[tool_use Bash] {"command": "grep -n \"unsupported_messages\" -A4 sqlglot/generator.py | grep -n \"logger\\|warn\" | head -5; grep -n \"^from\\|^import\" tests/dialects/test_oracle.py; sed -n 876,882p tests/dialects/test_oracle.py", "description": "Check unsupported logger and test file imports"}
[tool_result] 20:928-                logger.warning(msg)
1:from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2:from tests.dialects.test_dialect import Validator
3:from sqlglot.optimizer.qualify import qualify
            parse_one("PRIOR as foo", read="oracle")

    def test_utc_time(self):
        self.validate_identity("UTC_TIME()").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)
[tool_use Bash] {"command": "grep -n \"^from sqlglot.helper\\|^logger\" sqlglot/generator.py sqlglot/helper.py | head; grep -n \"    def test_pseudocolumns\" tests/dialects/test_oracle.py", "description": "Confirm generator logger module and insertion point"}
[tool_result] sqlglot/generator.py:12:from sqlglot.helper import csv, name_sequence, seq_get
sqlglot/generator.py:24:logger = logging.getLogger("sqlglot")
sqlglot/helper.py:38:logger = logging.getLogger("sqlglot")
898:    def test_pseudocolumns(self):
[assistant] Both loggers are the `sqlglot` logger, so `assertLogs(helper_logger)` will capture the warning. I'll add the Oracle round-trip and transpile-warning tests before `test_pseudocolumns`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_where(self):\n        self.validate_identity(\n            \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id \"\n
…[589 chars elided]…
ol1 IS NOT NULL\",\n                    read=\"oracle\",\n                ).sql(\"postgres\"),\n                \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1\",\n            )\n            self.assertIn(\"MERGE ... WHEN ... WHERE clause is not supported\", cm.output[0])\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "from sqlglot.optimizer.qualify import qualify\n", "new_string": "from sqlglot.helper import logger as helper_logger\nfrom sqlglot.optimizer.qualify import qualify\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now I'll run the Oracle tests with the project's configured interpreter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Run Oracle dialect tests"}
[tool_result] .............F..........                                                      [100%]
=================================== FAILURES ===================================
_________________________ TestOracle.test_merge_where __________________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_where>

    def test_merge_where(self):
>       self.validate_identity(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id "
            "WHEN MATCHED
…[399 chars elided]…
lidate_identity
    self.assertEqual(
E   AssertionError: 'MERG[126 chars]col1 WHERE source_table.col1 IS NOT NULL WHEN [118 chars] > 0' != 'MERG[126 chars]col1  WHERE NOT source_table.col1 IS NULL WHEN[120 chars] > 0'
E   Diff is 1051 characters long. Set self.maxDiff to None to see it.
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 23 passed, 211 subtests passed in 0.38s
[assistant] The failure is in my test input, not the feature: the generator normalizes `IS NOT NULL` to `NOT x IS NULL`. The output also shows a doubled space before `WHERE`, so I'll print the real output rather than guess.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col1 = s.col1 WHERE s.col1 > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.col1) VALUES (s.id, s.col1) WHERE s.id > 0'\nprint(repr(sqlglot.transpile(s, read='oracle', write='oracle')[0]))\nprint(repr(sqlglot.transpile(s, read='oracle', write='postgres')[0]))\nprint(sqlglot.parse_one(s, read='oracle').find(sqlglot.exp.Update).args.get('where'))\n\"", "description": "Print actual Oracle MERGE WHERE round-trip output"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` drops the working directory from `sys.path`, so `sqlglot` can't import. This is code from the repo I'm editing, so I'll run without `-I`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col1 = s.col1 WHERE s.col1 > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.col1) VALUES (s.id, s.col1) WHERE s.id > 0'\nprint(repr(sqlglot.transpile(s, read='oracle', write='oracle')[0]))\nprint(repr(sqlglot.transpile(s, read='oracle', write='postgres')[0]))\nprint(sqlglot.parse_one(s, read='oracle').find(sqlglot.exp.Update).args.get('where'))\n\"", "description": "Print actual Oracle MERGE WHERE round-trip output"}
[tool_result] MERGE ... WHEN ... WHERE clause is not supported
MERGE ... WHEN ... WHERE clause is not supported
'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.col1 = s.col1  WHERE s.col1 > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.col1) VALUES (s.id, s.col1)  WHERE s.id > 0'
'MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET col1 = s.col1 WHEN NOT MATCHED THEN INSERT (id, col1) VALUES (s.id, s.col1)'
WHERE s.col1 > 0
[assistant] Two findings. The Oracle round-trip keeps both `WHERE` clauses and postgres drops them with the warning, so the flag works. But there is a doubled space before each `WHERE`, because `Where.sql()` already emits a leading space and I added another. I'll drop my extra space.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "                where = f\" {self.sql(then_expression, 'where')}\"", "new_string": "                where = self.sql(then_expression, \"where\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Next I'll change the test's `IS NOT NULL` predicate to `> 0` so the assertion checks the clause and not the unrelated `NOT x IS NULL` normalization.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "            \"WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 IS NOT NULL \"\n            \"WHEN NOT MATCHED", "new_string": "            \"WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0 \"\n            \"WHEN NOT MATCHED"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "                    \"WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 IS NOT NULL\",", "new_string": "                    \"WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now the full test suite with the project's command, which is the check the harness specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite", "timeout": 900000}
[tool_result]                     "MERGE INTO my_table USING source_table ON my_table.id = source_table.id "
                    "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0",
                    read="oracle",
                ).sql("postgres"),
                "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            )
E           AssertionError: 'MERG[68 chars]WHEN MATCH
…[308 chars elided]…
ource_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1
E           ?                                                                                                      +++++++++

tests/dialects/test_oracle.py:907: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 1080 passed, 17834 subtests passed in 42.27s
[assistant] The full suite passes except my new test. The remaining diff is existing postgres behavior: it drops the table qualifier from `SET` targets, which is unrelated to this change. I'll correct my expected string to match.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "                \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1\",\n            )\n            self.assertIn", "new_string": "                \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET col1 = source_table.col1\",\n            )\n            self.assertIn"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-162814-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3; git status --short", "description": "Rerun full suite, lint and format check, show status", "timeout": 900000}
[tool_result] ....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 42.19s
4 files already formatted
All checks passed!
 M sqlglot/generator.py
 M sqlglot/generators/oracle.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[assistant] The suite is green (1081 passed), and ruff check and format are clean. The repo's `make check` also runs mypy, so I'll run it on the touched modules.
[tool_use Bash] {"command": "timeout 600 <work>/env-sqlglot/bin/python -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py 2>&1 | tail -5", "description": "Type-check modified modules with mypy", "timeout": 620000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py 2>&1 | tail -5", "description": "Type-check modified modules with mypy", "timeout": 600000}
[tool_result] Success: no issues found in 3 source files
[assistant] Oracle now parses and round-trips the `WHERE` clause on the `UPDATE` and `INSERT` branches of a `MERGE`. Other dialects drop it with an unsupported warning. The full suite passes (1081 tests), and ruff and mypy are clean on the touched files. I haven't committed anything.

What changed:

- **Parser** (`sqlglot/parser.py`, `_parse_when_matched`): after an `INSERT` or `UPDATE` branch, an optional `WHERE` is stored in that node's existing `where` arg. I didn't use `When.condition`, because that is the `WHEN ... AND ...` predicate, which is a different thing. The parser change is in the base parse
…[320 chars elided]…
*Oracle** (`sqlglot/generators/oracle.py`): sets `MERGE_WHERE_CLAUSE = True`.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_merge_where` checks the Oracle round-trip with both clauses, and checks that transpiling to postgres drops the clause and logs the warning.

Things to know:

- The warning is logged once per dropped clause, so a MERGE with both clauses warns twice.
- `DELETE WHERE` (Oracle's other clause inside `UPDATE`) is not handled. The task didn't ask for it.
- Only Oracle enables the flag. Other dialects that might support the clause would need the same one-line change.
