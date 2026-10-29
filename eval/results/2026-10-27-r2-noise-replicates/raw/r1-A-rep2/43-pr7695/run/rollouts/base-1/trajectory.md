# trajectory base-1

final message:
`SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full suite passes (1114 tests) and ruff is clean.

The change is in `sqlglot/generators/exasol.py`, in `show_sql`, next to the existing `SHOW TABLES` branch. `SHOW SCHEMAS` parses to the same node as `SHOW DATABASES`, so one branch covers both. I added `test_show_databases` to `tests/dialects/test_exasol.py` with one case for each MySQL statement.

One choice beyond your spec: `SHOW DATABASES LIKE 'x'` (or a `WHERE` clause) still hits the existing unsupported path and emits an empty string. I left it that way because the `SYS.EXA_SCHEMAS` query has no place for the filter, and dropping it silently would return the wrong rows. If you want the filter handled, that would be a `WHERE SCHEMA_NAME LIKE ...` translation.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n -i \"show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -80; grep -rn -i \"EXA_SCHEMAS\\|EXA_ALL_TABLES\\|SHOW TABLES\\|show_tables\\|ShowTables\" tests/dialects/test_exasol.py tests/dialects/test_mysql.py | head -30"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
tests/dialects/test_exasol.py:987:    def test_show_tables(self):
tests/dialects/test_exasol.py:989:            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'TEST'",
tests/dialects/test_exasol.py:990:            read={"mysql": "SHOW TABLES FROM test"},
tests/dialects/test_exasol.py:992:                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TAB
…[136 chars elided]…
T_SCHEMA",
tests/dialects/test_exasol.py:997:            read={"mysql": "SHOW TABLES"},
tests/dialects/test_exasol.py:999:                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
tests/dialects/test_mysql.py:1433:    def test_show_tables(self):
tests/dialects/test_mysql.py:1434:        show = self.validate_identity("SHOW TABLES")
tests/dialects/test_mysql.py:1444:        show = self.validate_identity("SHOW TABLES IN test", "SHOW TABLES FROM test")
[tool_use Bash] {"command": "grep -n -i \"_show\\|ShowTables\\|_parse_show\\|SHOW\" sqlglot/dialects/mysql.py sqlglot/dialects/exasol.py sqlglot/dialects/dialect.py | head -40; grep -n \"class Show\\|ShowTables\\|ShowSchemas\\|ShowDatabases\" sqlglot/expressions.py; sed -n 980,1010p tests/dialects/test_exasol.py"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
ugrep: warning: sqlglot/expressions.py: No such file or directory
            transpile(
                "USE ROLE admin",
                read="snowflake",
                write="exasol",
                unsupported_level=ErrorLevel.RAISE,
            )

    def test_show_tables(self):
        self.validate_all(
            "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SC
…[440 chars elided]…
FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
            },
        )

    def test_group_by_alias_local(self):
        # GROUP BY bare alias -> LOCAL prefix
        self.validate_all(
            "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt",
            read={"mysql": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY cnt"},
            write={"exasol": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt"},
        )
        # GROUP BY expression alias -> LOCAL prefix
[tool_use Bash] {"command": "grep -n -i \"show\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py; grep -rn \"_parse_show_mysql\\|def _parse_show\\|SHOW_PARSERS\\|SHOW_TRIE\" sqlglot/dialects/mysql.py sqlglot/parser.py | head; grep -n \"ShowTables\\|ShowDatabases\\|SCHEMAS\" sqlglot/expressions.py | head"}
[tool_result] sqlglot/dialects/mysql.py:154:        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE} - {TokenType.SHOW}
sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9194:    def _parse_show(self) -> exp.Expr | None:
sqlglot/parser.py:9195:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"SHOW_PARSERS\\|_parse_show_mysql\\|show_tables\\|def _show_tables\\|SHOW_DATABASES\\|SCHEMAS\\\"\" sqlglot/ | head -20"}
[tool_result] sqlglot/parser.py:1559:    SHOW_PARSERS: t.ClassVar[dict[str, t.Callable]] = {}
sqlglot/parser.py:1845:    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parser.py:9195:        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
sqlglot/parsers/singlestore.py:193:    SHOW_PARSERS = {
sqlglot/parsers/singlestore.py:194:        **MySQLParser.SHOW_PARSERS,
sqlglot/parsers/singlestore.py:234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PAR
…[634 chars elided]…
l(*args, **kwargs)
sqlglot/parsers/mysql.py:170:    SHOW_PARSERS = {
sqlglot/parsers/mysql.py:187:        "SCHEMAS": _show_parser("DATABASES"),
sqlglot/parsers/mysql.py:240:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
sqlglot/parsers/mysql.py:418:    def _parse_show_mysql(
sqlglot/generators/clickhouse.py:295:        exp.CurrentSchemas: rename_func("CURRENT_SCHEMAS"),
sqlglot/generators/snowflake.py:445:        exp.CurrentSchemas: lambda self, e: self.func("CURRENT_SCHEMAS"),
[tool_use Bash] {"command": "sed -n 165,195p sqlglot/parsers/mysql.py; grep -n \"def _show_parser\" -A12 sqlglot/parsers/mysql.py sqlglot/dialects/dialect.py sqlglot/parser.py | head -40; grep -rn \"Show\\b\\|ShowTables\\|exp.Show\" sqlglot/generators/exasol.py sqlglot/generators/mysql.py | head; grep -n \"SHOW\" sqlglot/generators/exasol.py sqlglot/dialects/exasol.py sqlglot/generators/mysql.py sqlglot/generator.py | head"}
[tool_result]     STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    SHOW_PARSERS = {
        "BINARY LOGS": _show_parser("BINARY LOGS"),
        "MASTER LOGS": _show_parser("BINARY LOGS"),
        "BINLOG EVENTS": _show_parser("BINLOG EVENTS"),
        "CHARACTER SET": _show_parser("CHARACTER SET"),
        "CHARSET": _show_parser("CHARACTER SET"),
        "COLLATION": _show_parser("COLLATION"),
        "FULL COLUMNS": _show_pa
…[1971 chars elided]…
str:
sqlglot/generators/mysql.py:764:    def _oldstyle_limit_sql(self, expression: exp.Show) -> str:
sqlglot/generators/exasol.py:906:    def show_sql(self, expression: exp.Show) -> str:
sqlglot/generators/mysql.py:744:        return f"SHOW{full}{global_}{this}{json}{target}{for_table}{types}{db}{query}{log}{position}{channel}{mutex_or_status}{like}{where}{offset}{limit}{for_group}{for_user}{for_role}{into_outfile}"
sqlglot/generator.py:5969:        self.unsupported("Unsupported SHOW statement")
[tool_use Bash] {"command": "sed -n 895,960p sqlglot/generators/exasol.py; sed -n 5960,5972p sqlglot/generator.py"}
[tool_result]     # https://docs.exasol.com/db/latest/sql/open_schema.htm
    def use_sql(self, expression: exp.Use) -> str:
        kind = expression.args.get("kind")
        if kind and self.sql(kind).upper() != "SCHEMA":
            self.unsupported(f"'USE {self.sql(kind)}' is not supported in Exasol")
            return super().use_sql(expression)
        this = self.sql(expression, "this")
        return f"OPEN SCHEMA {this}"

    # https://docs.exasol.com/db/latest/sql_references/metadata/metadata_syste
…[1870 chars elided]…
ession.name, *expression.expressions)

    def combinedaggfunc_sql(self, expression: exp.CombinedAggFunc) -> str:
        return self.anonymousaggfunc_sql(expression)

    def combinedparameterizedagg_sql(self, expression: exp.CombinedParameterizedAgg) -> str:
        return self.parameterizedagg_sql(expression)

    def show_sql(self, expression: exp.Show) -> str:
        self.unsupported("Unsupported SHOW statement")
        return ""

    def install_sql(self, expression: exp.Install) -> str:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfor s in ['SHOW DATABASES','SHOW SCHEMAS','SHOW DATABASES LIKE \\'a%\\'','SHOW TABLES']:\n    e=sqlglot.parse_one(s, read='mysql'); print(repr(e.name), e.args.keys())\n\""}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor s in ['SHOW DATABASES','SHOW SCHEMAS','SHOW DATABASES LIKE \\'a%\\'','SHOW TABLES']:\n    e=sqlglot.parse_one(s, read='mysql'); print(repr(e.name), {k:v for k,v in e.args.items() if v})\n\""}
[tool_result] 'DATABASES' {'this': 'DATABASES'}
'DATABASES' {'this': 'DATABASES'}
'DATABASES' {'this': 'DATABASES', 'like': Literal(this='a%', is_string=True)}
'TABLES' {'this': 'TABLES'}
[assistant] I'll add a `DATABASES` branch next to the existing `TABLES` one. `SHOW SCHEMAS` already parses to the same `DATABASES` show node, so one branch covers both.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "            return self.sql(select)\n\n        return super().show_sql(expression)", "new_string": "            return self.sql(select)\n\n        if expression.name == \"DATABASES\" and not expression.args.get(\"like\"):\n            select = exp.select(exp.column(\"SCHEMA_NAME\")).from_(\n                exp.table_(\"EXA_SCHEMAS\", db=\"SYS\")\n            )\n            return self.sql(select)\n\n        return super().show_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "        if expression.name == \"DATABASES\" and not expression.args.get(\"like\"):", "new_string": "        if expression.name == \"DATABASES\" and not expression.args.get(\"like\", \"where\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] That edit was wrong: `args.get("like", "where")` uses the string `"where"` as a default rather than checking the `where` key. Fixing it to check both keys explicitly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py", "old_string": "        if expression.name == \"DATABASES\" and not expression.args.get(\"like\", \"where\"):", "new_string": "        if expression.name == \"DATABASES\" and not (expression.args.get(\"like\") or expression.args.get(\"where\")):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll add a test next to `test_show_tables`, then check the output and run the Exasol and MySQL tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "                \"exasol\": \"SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA\"\n            },\n        )\n\n    def test_group_by_alias_local(self):", "new_string": "         
…[94 chars elided]…
HEMA\"\n            },\n        )\n\n    def test_show_databases(self):\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            },\n        )\n\n    def test_group_by_alias_local(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] The `""` read key is wrong, since `SHOW SCHEMAS` is a MySQL statement. Splitting it into two explicit MySQL reads.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\", \"\": \"SHOW SCHEMAS\"},\n            write={\n                \"exasol\
…[142 chars elided]…
CHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW DATABASES\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )\n        self.validate_all(\n            \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\",\n            read={\"mysql\": \"SHOW SCHEMAS\"},\n            write={\"exasol\": \"SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-100219-exasol-dialect-transpiling-mysql/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot import ErrorLevel\nfor s in ['SHOW DATABASES','SHOW SCHEMAS','SHOW DATABASES LIKE \\'a%\\'']:\n    print(sqlglot.transpile(s, read='mysql', write='exasol', unsupported_level=ErrorLevel.IGNORE))\n\" ; $P -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py tests/dialects/test_mysql.py 2>&1 | tail -5"}
[tool_result] ['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS']
['']
.......................................................................                 [100%]
71 passed, 1065 subtests passed in 0.34s
[assistant] Targeted tests pass. Running the full project test suite, plus a lint pass on the two changed files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($P -I -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && $P -I -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5"}
[tool_result] ............................................................................ [ 94%]
....................... [ 96%]
.......................... [ 98%]
...............                 [100%]
1114 passed, 18166 subtests passed in 53.66s
All checks passed!
Would reformat: sqlglot/generators/exasol.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -m ruff format sqlglot/generators/exasol.py && git diff && $P -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -1"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/generators/exasol.py b/sqlglot/generators/exasol.py
index 644619941..8bca1976d 100644
--- a/sqlglot/generators/exasol.py
+++ b/sqlglot/generators/exasol.py
@@ -916,6 +916,14 @@ class ExasolGenerator(generator.Generator):
             )
             return self.sql(select)
 
+        if expression.name == "DATABASES" and not (
+            expression.args.get("like") or expression.args.get("where")
+        ):
+            select = exp.select(exp.column("SC
…[731 chars elided]…
AS"},
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
20 passed, 579 subtests passed in 0.16s
[This command modified 1 file you've previously read: sqlglot/generators/exasol.py. Call Read before editing.]
[assistant] `SHOW DATABASES` and `SHOW SCHEMAS` now transpile to Exasol as `SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS`. The full suite passes (1114 tests) and ruff is clean.

The change is in `sqlglot/generators/exasol.py`, in `show_sql`, next to the existing `SHOW TABLES` branch. `SHOW SCHEMAS` parses to the same node as `SHOW DATABASES`, so one branch covers both. I added `test_show_databases` to `tests/dialects/test_exasol.py` with one case for each MySQL statement.

One choice beyond your spec: `SHOW DATABASES LIKE 'x'` (or a `WHERE` clause) still hits the existing unsupported path and emits an empty string. I left it that way because the `SYS.EXA_SCHEMAS` query has no place for the filter, and dropping it silently would return the wrong rows. If you want the filter handled, that would be a `WHERE SCHEMA_NAME LIKE ...` translation.

I haven't committed anything.
