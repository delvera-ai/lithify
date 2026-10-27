# trajectory base-1

final message:
MySQL optimizer hints now parse and round-trip on `UPDATE` and `DELETE`, the same way they already did on `SELECT` and `INSERT`. The full suite passes: `SUMMARY: 1087 passed, 17844 subtests passed in 73.43s`, `EXIT: 0`, taken after my last edit.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`, so the gap was in the parser and generator. The changes:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` at the start of the statement, as `_parse_insert` does.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t ...` and `delete_sql` emits `DELETE /*+ ... */ ...`.
- **`tests/dialects/test_mysql.py`**: three round-trip cases next to the existing hint tests, covering `UPDATE`, `DELETE FROM`, and multi-table `DELETE`.

I checked the AST as well as the string. On `UPDATE /*+ NO_INDEX(t) */ t SET a=1` the `hint` arg is a `Hint` node whose first expression is `NO_INDEX`. Statements without a hint still have no `hint` arg.

The parser change is in the base `Parser`, not the MySQL subclass. That matches how `SELECT` and `INSERT` already handle hints, and the tokenizer that produces the hint token is also generic. Dialects that don't emit hints are unaffected. I also ran ruff check and ruff format on the four changed files; both are clean.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"hint\" sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py | head -80; grep -rn \"class Hint\\|class Update\\|class Delete\\|class Insert\" sqlglot/expressions/*.py", "description": "Locate hint handling and DML expression classes"}
[tool_result] sqlglot/generators/mysql.py:120:    JOIN_HINTS = False
sqlglot/generators/mysql.py:121:    TABLE_HINTS = True
sqlglot/generators/mysql.py:123:    QUERY_HINT_SEP = " "
sqlglot/parser.py:950:    JOIN_HINTS: t.ClassVar[set[str]] = set()
sqlglot/parser.py:1042:        exp.Hint: lambda self: self._parse_hint_body(),
sqlglot/parser.py:1656:    TABLE_INDEX_HINT_TOKENS: t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
sqlglot/parser.py:3394:        hint = self._parse_hint()
sqlglot/parser
…[4782 chars elided]…
s = table.args.get("hints")
sqlglot/generator.py:4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
sqlglot/expressions/dml.py:71:class Delete(Expression, DML):
sqlglot/expressions/dml.py:194:class Insert(Expression, DDL, DML):
sqlglot/expressions/dml.py:293:class Update(Expression, DML):
sqlglot/expressions/core.py:1758:class Hint(Expression):
[tool_use Bash] {"command": "sed -n 3385,3440p sqlglot/parser.py; echo ----; sed -n 3790,3840p sqlglot/parser.py; echo ----; sed -n 60,110p sqlglot/expressions/dml.py; echo ----; sed -n 190,200p sqlglot/expressions/dml.py; sed -n 290,310p sqlglot/expressions/dml.py; echo ----; grep -n \"_parse_update\\|_parse_delete\\|def _parse_insert\" sqlglot/parser.py | head; grep -n \"hint\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py", "description": "Read SELECT/INSERT hint parsing and DML classes"}
[tool_result]             expression = parse_conditional_insert()

        return self.expression(
            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
            comments=comments,
        )

    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
        comments: list[str] = []
        hint = self._parse_hint()
        overwrite = self._match(TokenType.OVERWRITE)
        ignore = self._match(TokenType.IGNORE)
        local = self._match_text_seq("LO
…[5710 chars elided]…
False,
    }

    def table(
        self,
        expression: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
----
1075:        TokenType.DELETE: lambda self: self._parse_delete(),
1093:        TokenType.UPDATE: lambda self: self._parse_update(),
3392:    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
3450:    def _parse_insert_table(self) -> exp.Expr | None:
3582:    def _parse_delete(self) -> exp.Delete:
3605:    def _parse_update(self) -> exp.Update:
[tool_use Bash] {"command": "sed -n 3582,3640p sqlglot/parser.py; echo ----; sed -n 4098,4135p sqlglot/parser.py; echo ----; grep -n \"def delete_sql\\|def update_sql\\|def insert_sql\" -A12 sqlglot/generator.py | head -90; echo ----; grep -rn \"/\\*+\" tests/dialects/test_mysql.py | head -20", "description": "Read DELETE/UPDATE parse and generate code, MySQL hint tests"}
[tool_result]     def _parse_delete(self) -> exp.Delete:
        # This handles MySQL's "Multiple-Table Syntax"
        # https://dev.mysql.com/doc/refman/8.0/en/delete.html
        tables = None
        if not self._match(TokenType.FROM, advance=False):
            tables = self._parse_csv(self._parse_table) or None

        returning = self._parse_returning()

        return self.expression(
            exp.Delete(
                tables=tables,
                this=self._match(TokenType.FROM) and self._par
…[5291 chars elided]…
       expression_sql = f"{returning}{from_sql}{where_sql}"
2481-        options = self.expressions(expression, key="options")
----
tests/dialects/test_mysql.py:249:        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
tests/dialects/test_mysql.py:250:        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
tests/dialects/test_mysql.py:251:        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls -la $P 2>&1; grep -rn \"TokenType.HINT\\|HINT\" sqlglot/tokens.py sqlglot/dialects/mysql.py sqlglot/tokenizer_core.py 2>/dev/null | head; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT /*+ NO_INDEX(t) */ 1 FROM t','UPDATE /*+ NO_INDEX(t) */ t SET a=1','DELETE /*+ NO_INDEX(t) */ FROM t','INSERT /*+ NO_INDEX(t) */ INTO t VALUES (1)']:\n    try:\n        e=sqlglot.parse_one(s,read='mysql'); print(repr(e.args.get('hint')), '|', e.sql('mysql'))\n    except Exception as ex: print('ERR',s,ex)\n\"", "description": "Check interpreter and current hint behaviour"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
sqlglot/tokens.py:54:    HINT_START: t.ClassVar[str]
sqlglot/tokens.py:64:    TOKENS_PRECEDING_HINT: t.ClassVar[set[TokenType]]
sqlglot/tokens.py:106:        if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107
…[858 chars elided]…
Col: 25.
  UPDATE [4m/*+ NO_INDEX(t) */[0m t SET a=1
ERR DELETE /*+ NO_INDEX(t) */ FROM t Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX(t) */, line: 1, col: 25, start: 7, end: 24, comments: [' NO_INDEX(t) ']>. Line 1, Col: 25.
  DELETE [4m/*+ NO_INDEX(t) */[0m FROM t
Hint(
  expressions=[
    Anonymous(
      this=NO_INDEX,
      expressions=[
        Column(
          this=Identifier(this=t, quoted=False))])]) | INSERT /*+ NO_INDEX(t) */ INTO t VALUES (1)
[assistant] The tokenizer already emits a `HINT` token after `UPDATE`/`DELETE`, so the gap is in the parser and the generator. Let me read the full generator bodies.
[tool_use Bash] {"command": "sed -n 1699,1712p sqlglot/generator.py; echo ----; sed -n 2481,2500p sqlglot/generator.py; echo ----; sed -n 2196,2200p sqlglot/generator.py", "description": "Read full delete and update generator bodies"}
[tool_result]         tables = f" {tables}" if tables else ""
        if self.RETURNING_END:
            expression_sql = f"{this}{using}{cluster}{where}{returning}{order}{limit}"
        else:
            expression_sql = f"{returning}{this}{using}{cluster}{where}{order}{limit}"
        return self.prepend_ctes(expression, f"DELETE{tables}{expression_sql}")

    def drop_sql(self, expression: exp.Drop) -> str:
        this = self.sql(expression, "this")
        expressions = self.expressions(expression, flat
…[995 chars elided]…
values})"
                if self.WRAP_DERIVED_VALUES
                and (alias or isinstance(expression.parent, (exp.From, exp.Table)))
                else values
            )
            values = self.query_modifiers(expression, values)
----

        sql = f"INSERT{hint}{alternative}{ignore}{this}{stored}{by_name}{exists}{partition_by}{settings}{where}{expression_sql}{source}"
        return self.prepend_ctes(expression, sql)

    def introducer_sql(self, expression: exp.Introducer) -> str:
[assistant] Now the edits: add a `hint` arg to `Update` and `Delete`, parse it at the statement start the way `INSERT` does, and emit it in the generators.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.ex
…[34 chars elided]…
\n                tables=tables,", "new_string": "        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        hint = self.sql(expression, \"hint\")\n        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests. I'll add round-trip cases beside the existing MySQL hint tests and check the AST node directly.
[tool_use Bash] {"command": "sed -n 244,256p tests/dialects/test_mysql.py", "description": "View existing MySQL hint tests"}
[tool_result]         self.validate_identity("SELECT @var1 := 1, @var2")
        self.validate_identity("UNLOCK TABLES")
        self.validate_identity("LOCK TABLES `app_fields` WRITE", check_command_warning=True)
        self.validate_identity("SELECT 1 XOR 0")
        self.validate_identity("SELECT 1 && 0", "SELECT 1 AND 0")
        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
    
…[10 chars elided]…
alidate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("""SELECT 'ab' MEMBER OF('[23, "abc", 17, "ab", 10]')""")
        self.validate_identity("""SELECT * FROM foo WHERE 'ab' MEMBER OF(content)""")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_INDEX(t) */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t) */ FROM t WHERE a = 1\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t1) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183737-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_INDEX(t) */ t SET a=1','DELETE /*+ NO_INDEX(t) */ FROM t','DELETE /*+ NO_INDEX(t1) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a', 'UPDATE t SET a=1']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e.args.get('hint')).__name__, '|', e.sql('mysql'))\ne=sqlglot.parse_one('UPDATE /*+ NO_INDEX(t) */ t SET a=1',read='mysql'); print(e.args['hint'].expressions[0].name)\n\"; $P .lithify/harness/scripts/run_suite.py tests/dialects/test_mysql.py 2>&1 | tail -15", "description": "Check AST hint nodes and run MySQL dialect tests", "timeout": 600000}
[tool_result] Hint | UPDATE /*+ NO_INDEX(t) */ t SET a = 1
Hint | DELETE /*+ NO_INDEX(t) */ FROM t
Hint | DELETE /*+ NO_INDEX(t1) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a
NoneType | UPDATE t SET a = 1
NO_INDEX
WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 02-23:06:59 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  90161       00:34 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no tests/dialects/test_mysql.py
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-f7ab83d28d.log
ELAPSED: 1s
SUMMARY: 50 passed, 481 subtests passed in 0.53s
EXIT: 0
[assistant] The MySQL dialect file passes and the AST nodes are correct. Now the full suite, once, after the last edit.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P .lithify/harness/scripts/run_suite.py 2>&1 | tail -25", "description": "Run full test suite once after final edits", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 02-23:11:12 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  90161       04:47 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-f7ab83d28d.log
ELAPSED: 74s
SUMMARY: 1087 passed, 17844 subtests passed in 73.43s (0:01:13)
EXIT: 0
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py; $P -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py; git status --short", "description": "Lint and format-check the changed files", "timeout": 120000}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/dml.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_mysql.py
[assistant] MySQL optimizer hints now parse and round-trip on `UPDATE` and `DELETE`, the same way they already did on `SELECT` and `INSERT`. The full suite passes: `SUMMARY: 1087 passed, 17844 subtests passed in 73.43s`, `EXIT: 0`, taken after my last edit.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`, so the gap was in the parser and generator. The changes:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` at the start of the statement, as `_parse_insert` does.

…[202 chars elided]…
ng hint tests, covering `UPDATE`, `DELETE FROM`, and multi-table `DELETE`.

I checked the AST as well as the string. On `UPDATE /*+ NO_INDEX(t) */ t SET a=1` the `hint` arg is a `Hint` node whose first expression is `NO_INDEX`. Statements without a hint still have no `hint` arg.

The parser change is in the base `Parser`, not the MySQL subclass. That matches how `SELECT` and `INSERT` already handle hints, and the tokenizer that produces the hint token is also generic. Dialects that don't emit hints are unaffected. I also ran ruff check and ruff format on the four changed files; both are clean.
