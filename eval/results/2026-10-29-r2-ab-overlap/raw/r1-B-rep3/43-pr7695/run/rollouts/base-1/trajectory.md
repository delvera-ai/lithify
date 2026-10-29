# trajectory base-1

final message:
MySQL `SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS` instead of an empty statement. The full test suite passes (1114 passed), and ruff lint and format are clean.

The change is a `DATABASES` branch in `show_sql` in `sqlglot/generators/exasol.py`, next to the existing `TABLES` branch. Both spellings parse to the same `Show(this=DATABASES)` node, so one branch covers both. I also added `test_show_databases` to `tests/dialects/test_exasol.py`, covering each spelling.

I didn't commit anything.

One gap I left alone: `SHOW DATABASES LIKE 'pattern'` loses its `LIKE` filter, so it returns every schema. The existing `SHOW TABLES` branch has the same gap. Adding a `SCHEMA_NAME LIKE ...` filter would be a small follow-up if you want it.

## events
[tool_use Bash] {"command": "grep -n \"SHOW\\|Show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -80", "description": "Find SHOW handling in exasol and mysql dialects"}
[tool_result] 1 matches in 1 files:

sqlglot/dialects/mysql.py:154:COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
[tool_use Bash] {"command": "grep -n \"SHOW\\|Show\" sqlglot/dialects/mysql.py | head -60; echo ---; grep -n \"SHOW\\|Show\" sqlglot/dialects/exasol.py; echo ---; grep -rn \"SHOW\" tests/dialects/test_exasol.py | head -30; echo ---; grep -n \"class Exasol\" -A3 sqlglot/dialects/exasol.py", "description": "Search SHOW handling in MySQL and Exasol dialects and tests"}
[tool_result] 1 matches in 1 files:

sqlglot/dialects/mysql.py:154:COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
---
0 matches for 'SHOW\|Show'
---
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:997:            read={"mysql": "SHOW TABLES"},
---
14:class Exasol(Dialect):
15-    # https://docs.exasol.com/db/latest/sql_references/basiclanguageelements.htm#SQLidentifier
16-    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
17-    # https://docs.exasol.com/db/latest/sql_references/data_types/datatypesoverview.htm
[tool_use Bash] {"command": "sed -n 975,1010p tests/dialects/test_exasol.py; echo ---; grep -n \"_parse_show\\|def _show\\|ShowTables\\|SHOW_PARSERS\\|show_parsers\\|SHOW_\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/dialects/exasol.py | head -60; echo ---; grep -n \"class Show\\b\\|class Show(\" -A12 sqlglot/expressions.py", "description": "Inspect Exasol SHOW TABLES tests and show parsing code"}
[tool_result ERROR] Exit code 2
            read={"mysql": "USE `my_database`"},
            write={"exasol": 'OPEN SCHEMA "my_database"'},
        )
        # USE ROLE / USE WAREHOUSE have no Exasol equivalent — emit unsupported
        with self.assertRaises(UnsupportedError):
            transpile(
                "USE ROLE admin",
                read="snowflake",
                write="exasol",
                unsupported_level=ErrorLevel.RAISE,
            )

    def test_show_tables(self):
        self.valid
…[933 chars elided]…
t GROUP BY LOCAL.cnt"},
        )
        # GROUP BY expression alias -> LOCAL prefix
---
4 matches in 1 files:

sqlglot/parser.py:1559:SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9194:def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
---
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_\\|show_tables\\|EXA_ALL_TABLES\\|EXA_SCHEMAS\\|EXA_ALL_SCHEMAS\" sqlglot/ | head -40; echo ---; grep -n \"class Show\" -A6 sqlglot/expressions/*.py | head -30", "description": "Find SHOW parser registrations and Exasol metadata references"}
[tool_result] sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:321:        return self._parse_show_snowflake(*args, **kwargs)
sqlglot/parsers/snowflake.py:811:    SHOW_PARSERS = {
sqlglot/parsers/snowflake.py:843:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/snowflake.py:
…[896 chars elided]…
RS, self.SHOW_TRIE)
sqlglot/generators/exasol.py:914:                .from_(exp.table_("EXA_ALL_TABLES", db="SYS"))
---
sqlglot/expressions/ddl.py:191:class Show(Expression):
sqlglot/expressions/ddl.py-192-    arg_types = {
sqlglot/expressions/ddl.py-193-        "this": True,
sqlglot/expressions/ddl.py-194-        "history": False,
sqlglot/expressions/ddl.py-195-        "terse": False,
sqlglot/expressions/ddl.py-196-        "target": False,
sqlglot/expressions/ddl.py-197-        "offset": False,
[tool_use Bash] {"command": "sed -n 880,960p sqlglot/generators/exasol.py; echo ---; sed -n 418,470p sqlglot/parsers/mysql.py; echo ---; sed -n 165,185p sqlglot/parsers/mysql.py; echo; grep -n \"def show_sql\\|def show\" -A3 sqlglot/generators/exasol.py sqlglot/generator.py | head", "description": "Read Exasol SHOW TABLES generator and MySQL SHOW parser"}
[tool_result]     }

    def converttimezone_sql(self, expression: exp.ConvertTimezone) -> str:
        from_tz = expression.args.get("source_tz")
        to_tz = expression.args.get("target_tz")
        datetime = expression.args.get("timestamp")
        options = expression.args.get("options")

        return self.func("CONVERT_TZ", datetime, from_tz, to_tz, options)

    def if_sql(self, expression: exp.If) -> str:
        this = self.sql(expression, "this")
        true = self.sql(expression, "true")
    
…[5543 chars elided]…
l(self, expression: exp.Show) -> str:
sqlglot/generators/exasol.py-907-        if expression.name == "TABLES":
sqlglot/generators/exasol.py-908-            db_name = expression.text("db")
sqlglot/generators/exasol.py-909-            schema_filter: exp.Expression = (
--
sqlglot/generator.py:5968:    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generator.py-5969-        self.unsupported("Unsupported SHOW statement")
sqlglot/generator.py-5970-        return ""
sqlglot/generator.py-5971-
[assistant] Let me check how MySQL parses `SHOW DATABASES` / `SHOW SCHEMAS` today.
[tool_use Bash] {"command": "grep -n '\"DATABASES\"\\|\"SCHEMAS\"\\|\"TABLES\"' sqlglot/parsers/mysql.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SHOW DATABASES','SHOW SCHEMAS','SHOW TABLES']:\n    e = sqlglot.parse_one(q, read='mysql')\n    print(q, repr(e)[:300])\n    print(' ->', repr(sqlglot.transpile(q, read='mysql', write='exasol')))\n\"", "description": "Check MySQL SHOW DATABASES parse and Exasol output"}
[tool_result] 4 matches in 4 files:

186:0:_show_parser("DATABASES"),
187:0:_show_parser("DATABASES"),
216:0:_show_parser("TABLES", full=True),
217:0:_show_parser("TABLES"),
Unsupported SHOW statement
Unsupported SHOW statement
SHOW DATABASES Show(this=DATABASES, json=False)
 -> ['']
SHOW SCHEMAS Show(this=DATABASES, json=False)
 -> ['']
SHOW TABLES Show(this=TABLES, json=False)
 -> ['SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA']
[assistant] Both forms parse to `Show(this=DATABASES)` and currently fall through to the base generator, which emits nothing. I'll add a `DATABASES` branch next to the existing `TABLES` one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\":\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "    def test_group_by_alias_local(self):", "new_string": "    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SHOW DATABASES','SHOW SCHEMAS','SHOW TABLES']:\n    print(sqlglot.transpile(q, read='mysql', write='exasol'))\n\"", "description": "Run Exasol dialect tests and check transpiled output"}
[tool_result]         possibilities: Iterable[str],
    ) -> None:
        close_matches = get_close_matches(word, possibilities, n=1)
    
        similar = seq_get(close_matches, 0) or ""
        if similar:
            similar = f" Did you mean {similar}?"
    
>       raise ValueError(f"Unknown {kind} '{word}'.{similar}")
E       ValueError: Unknown dialect 'mariadb'.

sqlglot/helper.py:64: ValueError
=========================== short test summary info ============================
SUBFAILED[mariadb -> SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS] tests/dialects/test_exasol.py::TestExasol::test_show_databases
1 failed, 20 passed, 577 subtests passed in 0.25s
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA']
[assistant] The transpilation works; the failure is my test using a `mariadb` dialect that doesn't exist in this repo. MySQL covers both spellings, so I'll drop that key.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": \"SHOW DATABASES\", \"mariadb\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )", "new_string": "            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195303-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Rerun Exasol tests, full suite, and show git status"}
[tool_result] ....................                                                  [100%]
20 passed, 579 subtests passed in 0.13s
............................................................................ [ 94%]
....................... [ 96%]
.......................... [ 98%]
...............                 [100%]
1114 passed, 18166 subtests passed in 46.26s
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[assistant] Exasol tests and the full suite pass. Now the style check on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git diff", "description": "Lint and format-check changed files, show diff"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/generators/exasol.py  |  6 ++++++
 tests/dialects/test_exasol.py | 12 ++++++++++++
 2 files changed, 18 insertions(+)

--- Changes ---

sqlglot/generators/exasol.py
  @@ -916,6 +916,12 @@ class ExasolGenerator(generator.Generator):
  +        if expression.name == "DATABASES":
  +            select = exp.select(exp.column("SCHEMA_NAME")).from_(
  +                exp.table_("EXA_SCHEMAS", db="SYS")
  +            )
  +            return self.s
…[344 chars elided]…
",
  +            read={"mysql": "SHOW DATABASES"},
  +            write={"exasol": "SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS"},
  +        )
  +        self.validate_all(
  +            "SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS",
  +            read={"mysql": "SHOW SCHEMAS"},
  +            write={"exasol": "SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS"},
  +        )
  +
       def test_group_by_alias_local(self):
           # GROUP BY bare alias -> LOCAL prefix
           self.validate_all(
  +12 -0
[assistant] MySQL `SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS` instead of an empty statement. The full test suite passes (1114 passed), and ruff lint and format are clean.

The change is a `DATABASES` branch in `show_sql` in `sqlglot/generators/exasol.py`, next to the existing `TABLES` branch. Both spellings parse to the same `Show(this=DATABASES)` node, so one branch covers both. I also added `test_show_databases` to `tests/dialects/test_exasol.py`, covering each spelling.

I didn't commit anything.

One gap I left alone: `SHOW DATABASES LIKE 'pattern'` loses its `LIKE` filter, so it returns every schema. The existing `SHOW TABLES` branch has the same gap. Adding a `SCHEMA_NAME LIKE ...` filter would be a small follow-up if you want it.
