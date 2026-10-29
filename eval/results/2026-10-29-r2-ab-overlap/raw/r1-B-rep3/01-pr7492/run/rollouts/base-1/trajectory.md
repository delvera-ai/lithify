# trajectory base-1

final message:
The Oracle dialect now parses and round-trips the optional `WHERE` on the `UPDATE` and `INSERT` branches of `MERGE`. Transpiling to a dialect without that support emits an unsupported warning per clause and drops the clause. The full test suite passes (1081 tests), and ruff check and format are clean on the changed files.

Changes:
- **`sqlglot/parser.py`** (`_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` into that branch's existing `where` arg.
- **`sqlglot/generator.py`** (`when_sql`): emit the clause when present. If the dialect doesn't support it, call `self.unsupported(...)` and drop it. The new flag `MERGE_WHEN_WHERE_SUPPORTED` defaults to `False`.
- **`sqlglot/generators/oracle.py`**: sets `MERGE_WHEN_WHERE_SUPPORTED = True`.
- **`tests/dialects/test_oracle.py`**: new `test_merge_when_where` covers the Oracle round-trip, and checks that duckdb output drops both clauses and logs two warnings.

Choices I made:
- I used a generator flag defaulting to `False`, so every dialect other than Oracle drops the clause. This matches the request, but it means the generic `sqlglot` dialect also drops it. If you want a different set of dialects to keep it, that's a one-line change per dialect.
- The `WHERE` is stored on the `Insert`/`Update` branch node rather than on `When`. That is the only place Oracle's grammar puts it.
- I didn't commit. The repo's CLAUDE.md asks for a model name in commit messages and PR titles, so tell me when you want a commit and I'll add it.

I could not run the new test against a live Oracle instance, so the round-trip is verified only by the sqlglot unit test, not by Oracle itself.

## events
[tool_use Bash] {"command": "rtk grep -n \"_parse_merge\\|class Merge\\|When(\\|def merge_sql\\|_parse_when_matched\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/oracle.py sqlglot/dialects/dialect.py | head -50; rtk grep -rn \"Merge\" sqlglot/dialects/oracle.py | head", "description": "Locate MERGE parsing and generation code"}
[tool_result] rg: regex parse error:
    (?:_parse_merge|class Merge|When(|def merge_sql|_parse_when_matched)
    ^
error: unclosed group
0 matches for '_parse_merge\|class Merge\|When(\|def merge_sql\|_parse_when_matched'
[tool_use Bash] {"command": "rg -n \"_parse_merge|class Merge|class When|def merge_sql|_parse_when_matched|MERGE\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/oracle.py | head -60", "description": "Locate MERGE parsing and generation code"}
[tool_result] 16 matches in 2 files:

sqlglot/generator.py:320:# Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
sqlglot/generator.py:2034:return "NO MERGEBLOCKRATIO"
sqlglot/generator.py:2036:return "DEFAULT MERGEBLOCKRATIO"
sqlglot/generator.py:2039:return f"MERGEBLOCKRATIO={self.sql(expression, 'this')}{percent}"
sqlglot/generator.py:4469:def merge_sql(self, expression: exp.Merge) -> str:
sqlglot/generator.py:4475:# T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_...
sqlglot/
…[151 chars elided]…
nType.MERGE,
sqlglot/parser.py:1056:exp.Whens: lambda self: self._parse_when_matched(),
sqlglot/parser.py:1080:TokenType.MERGE: lambda self: self._parse_merge(),
sqlglot/parser.py:1271:"MERGEBLOCKRATIO": lambda self, **kwargs: self._parse_mergeblockratio(**kwargs),
sqlglot/parser.py:3037:def _parse_mergeblockratio(
sqlglot/parser.py:8884:def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8900:whens=self._parse_when_matched(),
sqlglot/parser.py:8905:def _parse_when_matched(self) -> exp.Whens:
[tool_use Bash] {"command": "sed -n 8884,8975p sqlglot/parser.py; echo ----; sed -n 4469,4500p sqlglot/generator.py; rg -n \"def whens_sql\" -A 45 sqlglot/generator.py; rg -n \"class When\\b|class Whens|class Merge\" -A 12 sqlglot/expressions.py; rg -n \"class Merge|MERGE\" sqlglot/dialects/oracle.py", "description": "Read MERGE parser, generator, and expression defs"}
[tool_result ERROR] Exit code 1
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
                on=self._match(TokenType.ON) and self._pars
…[5755 chars elided]…
  def tonumber_sql(self, expression: exp.ToNumber) -> str:
4505-        if not self.SUPPORTS_TO_NUMBER:
4506-            self.unsupported("Unsupported TO_NUMBER function")
4507-            return self.sql(exp.cast(expression.this, exp.DType.DOUBLE))
4508-
4509-        fmt = expression.args.get("format")
4510-        if not fmt:
4511-            self.unsupported("Conversion format is required for TO_NUMBER")
grep: sqlglot/expressions.py: No such file or directory
0 matches for 'class Merge|MERGE'
[tool_use Bash] {"command": "rg -n \"class When\\b|class Whens|class Insert\\b|class Update\\b|class Merge\\b\" -A 14 sqlglot/expressions/ | head -120; rg -n \"def when_sql\" -A 40 sqlglot/generator.py; rg -n \"def insert_sql|def update_sql\" -A 3 sqlglot/generator.py; ls tests/dialects | grep -i oracle; rg -n \"MERGE\" tests/dialects/test_oracle.py | head", "description": "Inspect When/Whens/Insert/Update definitions and generator"}
[tool_result] grep: sqlglot/expressions/: Is a directory
4443:    def when_sql(self, expression: exp.When) -> str:
4444-        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
4445-        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
4446-        condition = self.sql(expression, "condition")
4447-        condition = f" AND {condition}" if condition else ""
4448-
4449-        then_expression = expression.args.get("then")
4450-        if isinstan
…[1344 chars elided]…
table_alias]
4476-            table_alias = f" AS {self.sql(table.args['alias'].pop())}"
4477-
4478-        this = self.sql(table)
4479-        using = f"USING {self.sql(expression, 'using')}"
4480-        whens = self.sql(expression, "whens")
4481-
4482-        on = self.sql(expression, "on")
4483-        on = f"ON {on}" if on else ""
test_oracle.py  42.4K
1 matches in 1 files:

tests/dialects/test_oracle.py:895:"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id...
[tool_use Bash] {"command": "rg -n \"class When\\(|class Whens|class Insert\\(|class Update\\(|class Merge\\(\" -A 14 sqlglot/expressions/ | head -120; rg -n \"MERGE|merge\" tests/dialects/test_oracle.py | head -20; sed -n 885,910p tests/dialects/test_oracle.py; rg -n \"unsupported|warning\" sqlglot/dialects/dialect.py | head -5; rg -n \"class Oracle|MERGE|Merge\" sqlglot/dialects/oracle.py | head; rg -ln \"WHEN MATCHED\" tests/dialects/ | head", "description": "Inspect expression classes and existing MERGE tests"}
[tool_result] grep: parentheses not balanced
4 matches in 2 files:

884:0:
tests/dialects/test_oracle.py:885:merge_stmt = exp.merge(
tests/dialects/test_oracle.py:894:merge_stmt.sql("oracle"),
tests/dialects/test_oracle.py:895:"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table...
        merge_stmt = exp.merge(
            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, 
…[883 chars elided]…
))

        self.assertEqual(
            qualified.sql(dialect="oracle"),
            'WITH "T" AS (SELECT 1 AS "COL") SELECT "T"."COL" AS "COL", ROWID AS "ROWID" FROM "T" "T" WHERE ROWNUM = 1',
        )
21 matches in 2 files:

987:0:
sqlglot/dialects/dialect.py:15:from sqlglot.generator import Generator, unsupported_args
sqlglot/dialects/dialect.py:270:# Remove transforms that correspond to unsupported JSONPathPart expressions
1 matches in 1 files:

15:0:
grep: tests/dialects/: Is a directory
[tool_use Bash] {"command": "grep -rn \"^class When\\|^class Whens\\|^class Insert\\|^class Update\\|^class Merge\" -A 12 sqlglot/expressions/ | head -120; grep -rln \"WHEN MATCHED\" tests/ | head; grep -n \"MERGE\\|Merge\\|Whens\" sqlglot/dialects/oracle.py | head", "description": "Inspect expression classes and find MERGE tests"}
[tool_result] sqlglot/expressions/ddl.py:310:class MergeTreeTTLAction(Expression):
sqlglot/expressions/ddl.py-311-    arg_types = {
sqlglot/expressions/ddl.py-312-        "this": True,
sqlglot/expressions/ddl.py-313-        "delete": False,
sqlglot/expressions/ddl.py-314-        "recompress": False,
sqlglot/expressions/ddl.py-315-        "to_disk": False,
sqlglot/expressions/ddl.py-316-        "to_volume": False,
sqlglot/expressions/ddl.py-317-    }
sqlglot/expressions/ddl.py-318-
sqlglot/expressions/ddl.py-3
…[3747 chars elided]…
pressions/dml.py:521:class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
tests/test_parser.py
tests/test_build.py
tests/dialects/test_oracle.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_tsql.py
tests/dialects/test_postgres.py
tests/fixtures/pretty.sql
0 matches for 'MERGE\|Merge\|Whens'
[tool_use Bash] {"command": "sed -n 315,324p sqlglot/generator.py; grep -n \"def seg\\|def where_sql\\|def sep\" -A 4 sqlglot/generator.py | head -30; grep -n \"def _parse_where\" -A 6 sqlglot/parser.py; grep -n \"unsupported_level\" tests/dialects/test_dialect.py | head -3; grep -n \"class Generator\\|SUPPORTS\\|= True\" sqlglot/dialects/oracle.py | head -30; grep -n \"_parse_where()\" sqlglot/parser.py | head -3", "description": "Inspect generator flags, seg/where helpers, Oracle settings"}
[tool_result]     WRAP_DERIVED_VALUES = True

    # Whether create function uses an AS before the RETURN
    CREATE_FUNCTION_RETURN_AS = True

    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
    MATCHED_BY_SOURCE = True

    # Whether the INTERVAL expression works only with values like '1 day'
    SINGLE_STRING_INTERVAL = False
958:    def sep(self, sep: str = " ") -> str:
959-        return f"{sep.strip()}\n" if self.pretty else sep
960-
961:    def seg(self, sql: str, sep: str = " ") -> str:
962- 
…[694 chars elided]…
ssion(
5189-            exp.Where(this=self._parse_disjunction()),
3 matches in 1 files:

tests/dialects/test_dialect.py:88:unsupported_level=ErrorLevel.IGNORE,
4 matches in 1 files:

sqlglot/dialects/oracle.py:16:ALIAS_POST_TABLESAMPLE = True
sqlglot/dialects/oracle.py:17:LOCKING_READS_SUPPORTED = True
sqlglot/dialects/oracle.py:18:TABLESAMPLE_SIZE_IS_PERCENT = True
sqlglot/dialects/oracle.py:22:DISABLES_ALIAS_REF_EXPANSION = True
12 matches in 6 files:

1057:0:lambda self: self._parse_where(),
[tool_use Bash] {"command": "grep -n \"class Generator\" -A 25 sqlglot/dialects/oracle.py; grep -rn \"MATCHED_BY_SOURCE\\|LOCKING_READS_SUPPORTED\" sqlglot/ | head; sed -n 80,100p tests/dialects/test_dialect.py", "description": "Inspect Oracle generator flags and validate_all helper"}
[tool_result] sqlglot/generator.py:309:    LOCKING_READS_SUPPORTED = False
sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:2761:        if not self.LOCKING_READS_SUPPORTED:
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/dialects/oracle.py:17:    LOCKING_READS_SUPPORTED = True
sqlglot/generators/redshift.py:21:    LOCKING_READS_SUPPORTED = False
sqlglot/generators/risingwave.py:9:    LOCKING_READS_SU
…[579 chars elided]…
ORE,
                        pretty=pretty,
                        identify=identify,
                    ),
                    sql,
                )

        for write_dialect, write_sql in (write or {}).items():
            with self.subTest(f"{sql} -> {write_dialect}"):
                if write_sql is UnsupportedError:
                    with self.assertRaises(UnsupportedError):
                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
                else:
[tool_use Bash] {"command": "sed -n 15,40p sqlglot/generators/oracle.py; sed -n 300,312p sqlglot/generator.py; grep -n \"MERGE\" -B3 -A3 tests/dialects/test_tsql.py | head -30", "description": "Read Oracle generator flags and base flag block"}
[tool_result]     position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


class OracleGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    LOCKING_READS_SUPPORTED = True
    JOIN_HINTS = False
    TABLE_HINTS = False
    DATA_TYPE_SPECIFIERS_ALLOWED = True
    ALTER_TABLE_INCLUDE_COLUMN_KEYWORD = Fals
…[1434 chars elided]…
T.user_id = S.user_id) WHEN NOT MATCHED THEN INSERT (c1, c2) VALUES (S.c1, S.c2)"
339-        )
340-        self.validate_identity("UPDATE STATISTICS x", check_command_warning=True)
--
564-            "ORDER GROUP",
565-            "CONCAT UNION",
566-            "HASH UNION",
567:            "MERGE UNION",
568-            "LOOP JOIN",
569:            "MERGE JOIN",
570-            "HASH JOIN",
571-            "DISABLE_OPTIMIZED_PLAN_FORCING",
572-            "EXPAND VIEWS",
--
595-        ]
596-
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            whens.append(", "new_string": "            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)):\n                then.set(\"where\", self._parse_where())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether the WHERE clause is allowed in MERGE's WHEN [NOT] MATCHED ... THEN UPDATE/INSERT branches\n    MERGE_WHEN_WHERE_SUPPORTED = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "            else:\n                then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "            else:\n                then = self.sql(then_expression)\n\n        where = self.sql(then_expression, \"where\")\n        if where and not self.MERGE_WHEN_WHERE_SUPPORTED:\n            self.unsupported(\"WHERE clause in MERGE WHEN ... THEN is not supported\")\n            where = \"\"\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:             else:
                then = self.sql(then_expression)
        return f"WHEN {matched}{source}{condition} THEN {then}"</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_WHEN_WHERE_SUPPORTED = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(then_expression, \"where\")\n        if where and not self.MERGE_WHEN_WHERE_SUPPORTED:\n            self.unsupported(\"WHERE clause in MERGE WHEN ... THEN is not supported\")\n            where = \"\"\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}{where}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a quick check of the round-trip and the cross-dialect behavior before writing tests.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot, logging\nlogging.basicConfig()\nsql='MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c WHERE s.c > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.c) VALUES (s.id, s.c) WHERE s.id > 0'\nprint(sqlglot.transpile(sql, read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(sql, read='oracle', write='duckdb')[0])\nprint(sqlglot.transpile(sql, read='oracle', write='oracle', pretty=True)[0])\n\" 2>&1", "description": "Check Oracle MERGE round-trip and duckdb transpile"}
[tool_result] WARNING:sqlglot:WHERE clause in MERGE WHEN ... THEN is not supported
WARNING:sqlglot:WHERE clause in MERGE WHEN ... THEN is not supported
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c WHERE s.c > 0 WHEN NOT MATCHED THEN INSERT (t.id, t.c) VALUES (s.id, s.c) WHERE s.id > 0
MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c WHEN NOT MATCHED THEN INSERT (t.id, t.c) VALUES (s.id, s.c)
MERGE INTO t
USING s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
  t.c = s.c
WHERE
  s.c > 0
WHEN NOT MATCHED THEN INSERT (t.id, t.c) VALUES (s.id, s.c)
WHERE
  s.id > 0
[assistant] Round-trip and the duckdb drop both behave as intended. Now the tests, next to the existing Oracle MERGE test.
[tool_use Bash] {"command": "grep -rn \"assertLogs\" tests/dialects/*.py | head -3; grep -n \"unsupported_level\" tests/dialects/test_oracle.py | head -3; sed -n 880,884p tests/dialects/test_oracle.py", "description": "Find existing unsupported-warning test pattern"}
[tool_result] tests/dialects/test_bigquery.py:2130:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2139:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2147:        with self.assertLogs(helper_logger) as cm:
0 matches for 'unsupported_level'
        self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)

    def test_merge_builder_alias(self):
[tool_use Bash] {"command": "sed -n 2125,2135p tests/dialects/test_bigquery.py; grep -n \"^helper_logger\\|helper_logger =\" tests/dialects/test_bigquery.py; sed -n 1,12p tests/dialects/test_oracle.py", "description": "Read bigquery logger pattern and oracle test imports"}
[tool_result]         with self.assertRaises(ParseError):
            transpile("DATE_ADD(x, day)", read="bigquery")

    def test_warnings(self):
        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "WITH cte(c) AS (SELECT * FROM t) SELECT * FROM cte",
                "WITH cte AS (SELECT * FROM t) SELECT * FROM cte",
            )

0 matches for '^helper_logger\|helper_logger ='
from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "            \"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my
…[1104 chars elided]…
",\n                ).sql(\"duckdb\"),\n                \"MERGE INTO t USING s ON t.id = s.id \"\n                \"WHEN MATCHED THEN UPDATE SET t.c = s.c \"\n                \"WHEN NOT MATCHED THEN INSERT (t.id, t.c) VALUES (s.id, s.c)\",\n            )\n        self.assertEqual(len(cm.output), 2)\n        self.assertIn(\"WHERE clause in MERGE WHEN ... THEN is not supported\", cm.output[0])\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite"}
[tool_result] ................................................................................. [  7%]
................................ [ 10%]
................................................................................................................................... [ 22%]
..................................................... [ 27%]
................ [ 28%]
.................................................................................................... [ 38%]
.......................................
…[242 chars elided]…
................ [ 64%]
........................................................................................................................................................................................................................................................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 38.47s
[assistant] All 1081 tests pass. Let me run the linter on the changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/oracle.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[assistant] The Oracle dialect now parses and round-trips the optional `WHERE` on the `UPDATE` and `INSERT` branches of `MERGE`. Transpiling to a dialect without that support emits an unsupported warning per clause and drops the clause. The full test suite passes (1081 tests), and ruff check and format are clean on the changed files.

Changes:
- **`sqlglot/parser.py`** (`_parse_when_matched`): after an `INSERT` or `UPDATE` branch, parse an optional `WHERE` into that branch's existing `where` arg.
- **`sqlglot/generator.py`** (`when_sql`): emit the clause when present. If the dialect doesn't support it, ca
…[469 chars elided]…
. This matches the request, but it means the generic `sqlglot` dialect also drops it. If you want a different set of dialects to keep it, that's a one-line change per dialect.
- The `WHERE` is stored on the `Insert`/`Update` branch node rather than on `When`. That is the only place Oracle's grammar puts it.
- I didn't commit. The repo's CLAUDE.md asks for a model name in commit messages and PR titles, so tell me when you want a commit and I'll add it.

I could not run the new test against a live Oracle instance, so the round-trip is verified only by the sqlglot unit test, not by Oracle itself.
