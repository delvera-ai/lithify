# trajectory base-1

final message:
MySQL `UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests, 17844 subtests) and ruff lint and format are clean. I haven't committed.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`. The parser never consumed it, so these statements failed with "Expected table name". The change:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching what `Select` and `Insert` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` now call `_parse_hint()` before the table, as `_parse_insert` does.
- **`sqlglot/generator.py`**: `update_sql` emits the hint after `UPDATE`, and `delete_sql` emits it after `DELETE`. Non-MySQL generators still get the existing "Hints are not supported" warning through `hint_sql`.
- **`tests/dialects/test_mysql.py`**: three identity tests, covering `UPDATE` with a hint, `DELETE FROM` with a hint, and multi-table `DELETE` with a hint.

I put the hints in the generic parser and generator rather than in the MySQL dialect, since the tokenizer and the `Select` and `Insert` paths already work that way. Other dialects will now parse hints on these statements too, and generate them only where `QUERY_HINTS` allows.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n -i \"hint\" sqlglot/parser.py sqlglot/dialects/mysql.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -80", "description": "Find hint handling in parser and generator"}
[tool_result] oksqlglot/parser.py:950:    JOIN_HINTS: t.ClassVar[set[str]] = set()
sqlglot/parser.py:1042:        exp.Hint: lambda self: self._parse_hint_body(),
sqlglot/parser.py:1656:    TABLE_INDEX_HINT_TOKENS: t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
sqlglot/parser.py:3394:        hint = self._parse_hint()
sqlglot/parser.py:3428:                hint=hint,
sqlglot/parser.py:3798:            hint = self._parse_hint()
sqlglot/parser.py:3835:                    hint=hint,
sqlglot/parser
…[4294 chars elided]…
glot/generator.py:3109:        top_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{distinct}"
sqlglot/generator.py:4439:    def joinhint_sql(self, expression: exp.JoinHint) -> str:
sqlglot/generator.py:4484:        hints = table.args.get("hints")
sqlglot/generator.py:4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3385,3440p sqlglot/parser.py && echo ---- && sed -n 3790,3840p sqlglot/parser.py && echo ---- && grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_insert\" sqlglot/parser.py && grep -n -i \"hint\" sqlglot/dialects/mysql.py | head -30", "description": "Inspect select/insert hint parsing and update/delete parsers"}
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
…[3353 chars elided]…
= self._parse_limit(top=True)
            projections, exclude = self._parse_projections()

            this = self.expression(
                exp.Select(
                    kind=kind,
                    hint=hint,
                    distinct=distinct,
                    expressions=projections,
                    limit=limit,
                    exclude=exclude,
                    operation_modifiers=operation_modifiers or None,
----
4 matches in 4 files:

3392:0:
3450:0:
3582:0:
3605:0:
[tool_use Bash] {"command": "sed -n 3440,3460p sqlglot/parser.py; echo ----; sed -n 3570,3640p sqlglot/parser.py; echo ----; grep -n \"class Update\\|class Delete\" -A 22 sqlglot/expressions/*.py | grep -n \"arg_types\\|class\\|hint\" ; grep -n \"class Insert\\b\\|class Insert(\" -A 25 sqlglot/expressions/*.py | grep hint; grep -n \"class Select(\" -A 40 sqlglot/expressions/query.py | grep -n hint", "description": "Inspect update/delete parsers and expression arg types"}
[tool_result]                 conflict=self._parse_on_conflict(),
                returning=returning or self._parse_returning(),
                overwrite=overwrite,
                alternative=alternative,
                ignore=ignore,
                source=self._match(TokenType.TABLE) and self._parse_table(),
            ),
            comments=comments,
        )

    def _parse_insert_table(self) -> exp.Expr | None:
        this = self._parse_table(schema=True, parse_partition=True)
        if isinstan
…[3295 chars elided]…
se_var_from_options(self.USABLES, raise_unmatched=False),
                this=self._parse_table(schema=False),
            )
        )

    def _parse_uncache(self) -> exp.Uncache:
----
1:sqlglot/expressions/dml.py:71:class Delete(Expression, DML):
2:sqlglot/expressions/dml.py-72-    arg_types = {
25:sqlglot/expressions/dml.py:293:class Update(Expression, DML):
26:sqlglot/expressions/dml.py-294-    arg_types = {
sqlglot/expressions/dml.py-196-        "hint": False,
6:1127-        "hint": False,
[tool_use Bash] {"command": "sed -n 71,90p sqlglot/expressions/dml.py; sed -n 293,310p sqlglot/expressions/dml.py; sed -n 185,200p sqlglot/expressions/dml.py; echo ----; grep -n \"def update_sql\\|def delete_sql\" -A 30 sqlglot/generator.py | head -90; echo ----; grep -rn \"/\\*+\" tests/dialects/test_mysql.py | head -20; grep -n \"HINT\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/dialects/mysql.py | head", "description": "Read Delete/Update args, generator, and hint tests"}
[tool_result] class Delete(Expression, DML):
    arg_types = {
        "with_": False,
        "this": False,
        "using": False,
        "where": False,
        "returning": False,
        "order": False,
        "limit": False,
        "tables": False,  # Multiple-Table Syntax (MySQL)
        "cluster": False,  # Clickhouse
    }

    def delete(
        self,
        table: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
    ) -> De
…[4539 chars elided]…
ches in 2 files:

sqlglot/tokenizer_core.py:311:HINT = auto()
sqlglot/tokenizer_core.py:905:self._add(TokenType.HINT)
sqlglot/tokens.py:54:HINT_START: t.ClassVar[str]
sqlglot/tokens.py:64:TOKENS_PRECEDING_HINT: t.ClassVar[set[TokenType]]
sqlglot/tokens.py:106:if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107:cls._COMMENTS[cls.HINT_START] = "*/"
sqlglot/tokens.py:184:HINT_START = "/*+"
sqlglot/tokens.py:186:TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, T...
[tool_use Bash] {"command": "sed -n 184,190p sqlglot/tokens.py; grep -rn \"TOKENS_PRECEDING_HINT\" sqlglot | head; sed -n 240,262p tests/dialects/test_mysql.py; grep -n \"UPDATE\\|DELETE\" tests/dialects/test_mysql.py | grep \"/\\*\" | head; grep -rn \"/\\*+\" tests/dialects/*.py | grep -i \"update\\|delete\" | head", "description": "Check hint token preceding set and existing tests"}
[tool_result]     HINT_START = "/*+"

    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE}

    # Autofilled
    _COMMENTS: t.ClassVar[dict[str, str | None]] = {}
    _FORMAT_STRINGS: t.ClassVar[dict[str, tuple[str, TokenType]]] = {}
sqlglot/tokens.py:64:    TOKENS_PRECEDING_HINT: t.ClassVar[set[TokenType]]
sqlglot/tokens.py:186:    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE}
sqlglot/tokens.py:561:            
…[1311 chars elided]…
abc", 17, "ab", 10]')""")
        self.validate_identity("""SELECT * FROM foo WHERE 'ab' MEMBER OF(content)""")
        self.validate_identity("SELECT CURRENT_TIMESTAMP(6)")
        self.validate_identity("SELECT CURRENT_ROLE()")
        self.validate_identity("SELECT CURTIME()", "SELECT CURRENT_TIME()")
        self.validate_identity("x ->> '$.name'")
        self.validate_identity("SELECT CAST(`a`.`b` AS CHAR) FROM foo")
        self.validate_identity("SELECT TRIM(LEADING 'bla' FROM ' XXX ')")
[assistant] Tokenizer already emits hint tokens after `UPDATE`/`DELETE`; the parser just doesn't consume them. Let me confirm the current behavior.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2','DELETE /*+ QB_NAME(d) */ FROM t WHERE a = 1','DELETE /*+ X */ t1 FROM t1 JOIN t2 ON t1.a=t2.a', 'SELECT /*+ X */ 1']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(repr(e.args.get('hint')), '|', e.sql('mysql'))\n\"", "description": "Check current hint behavior on UPDATE and DELETE"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/__init__.py", line 176, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/dialects/dialect.py", line 1116, in parse
    r
…[2257 chars elided]…
"Expected table name but got {self._curr}")
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", line 1977, in raise_error
    raise error
sqlglot.errors.ParseError: Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX_MERGE(t) */, line: 1, col: 31, start: 7, end: 30, comments: [' NO_INDEX_MERGE(t) ']>. Line 1, Col: 31.
  UPDATE [4m/*+ NO_INDEX_MERGE(t) */[0m t SET a = 1 WHERE b = 2
[assistant] The cause is clear: the tokenizer emits a `HINT` token after `UPDATE`/`DELETE`, but `_parse_update` and `_parse_delete` never call `_parse_hint()`. I'll add a `hint` arg to both expressions, parse it, and generate it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.ex
…[34 chars elided]…
\n                tables=tables,", "new_string": "        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"hint\": False,\n        \"with_\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add round-trip tests next to the existing MySQL hint tests, then run them alongside a check of the cases I'm less sure about.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(d) */ FROM t WHERE a = 1\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(d) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174236-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2','DELETE /*+ QB_NAME(d) */ FROM t WHERE a = 1','DELETE /*+ X */ t1 FROM t1 JOIN t2 ON t1.a=t2.a', 'UPDATE t SET a = 1', 'DELETE FROM t']:\n    e = sqlglot.parse_one(s, read='mysql')\n    print(e.sql('mysql'), '| hint:', repr(e.args.get('hint'))[:40])\n    print('   tsql/duckdb:', e.sql('duckdb'))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5", "description": "Verify round trips and run MySQL dialect tests"}
[tool_result] Hints are not supported
Hints are not supported
Hints are not supported
UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2 | hint: Hint(
  expressions=[
    Anonymous(
   
   tsql/duckdb: UPDATE t SET a = 1 WHERE b = 2
DELETE /*+ QB_NAME(d) */ FROM t WHERE a = 1 | hint: Hint(
  expressions=[
    Anonymous(
   
   tsql/duckdb: DELETE FROM t WHERE a = 1
DELETE /*+ X */ t1 FROM t1 JOIN t2 ON t1.a = t2.a | hint: Hint(
  expressions=[
    Var(this=X)])
   tsql/duckdb: DELETE t1 FROM t1 JOIN t2 ON t1.a = t2.a
UPDATE t SET a = 1 | hint: None
   tsql/duckdb: UPDATE t SET a = 1
DELETE FROM t | hint: None
   tsql/duckdb: DELETE FROM t
.............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.23s
[assistant] MySQL tests pass (50 tests, 481 subtests). The "Hints are not supported" lines are the existing warning from non-MySQL generators, not a failure. Now the full suite with the project's check command, plus lint.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; $PY -m ruff check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ................................................... [ 52%]
.......................................................................................................................................................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 46.75s
All checks passed!
174 files already formatted
[tool_use Bash] {"command": "git diff --stat", "description": "Show diff stat of changes"}
[tool_result] sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 3 +++
 4 files changed, 12 insertions(+), 2 deletions(-)
[assistant] MySQL `UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests, 17844 subtests) and ruff lint and format are clean. I haven't committed.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`. The parser never consumed it, so these statements failed with "Expected table name". The change:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching what `Select` and `Insert` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` now call `_parse_hint()` before the ta
…[77 chars elided]…
s the hint after `UPDATE`, and `delete_sql` emits it after `DELETE`. Non-MySQL generators still get the existing "Hints are not supported" warning through `hint_sql`.
- **`tests/dialects/test_mysql.py`**: three identity tests, covering `UPDATE` with a hint, `DELETE FROM` with a hint, and multi-table `DELETE` with a hint.

I put the hints in the generic parser and generator rather than in the MySQL dialect, since the tokenizer and the `Select` and `Insert` paths already work that way. Other dialects will now parse hints on these statements too, and generate them only where `QUERY_HINTS` allows.
