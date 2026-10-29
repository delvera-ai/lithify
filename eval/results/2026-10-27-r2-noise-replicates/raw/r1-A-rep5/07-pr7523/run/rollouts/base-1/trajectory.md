# trajectory base-1

final message:
MySQL `UPDATE` and `DELETE` now accept optimizer hints, parse them, and round-trip them. The full suite passes (1087 tests) and ruff lint and format are clean on the changed files.

Changes:
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` read the hint right after the keyword, the same way `_parse_insert` does.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ table ...` and `delete_sql` emits `DELETE /*+ ... */ ...`, including the multi-table `DELETE /*+ ... */ t1 FROM ...` form.
- **`tests/dialects/test_mysql.py`**: three `validate_identity` cases covering an UPDATE hint, a single-table DELETE hint, and a multi-table DELETE hint with a join.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`, so the fix was limited to the parser and generator. Nothing is committed.

One thing I noticed but did not change: `UPDATE ... LOW_PRIORITY t` is parsed with `LOW_PRIORITY` as an alias. That is a separate gap in how `UPDATE` modifiers are parsed, not part of this hint change. Say if you want it handled here too.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"HINT\\|hint\" sqlglot/parser.py | head -80 && grep -n \"hint\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -40", "description": "Find hint handling in parser and generator"}
[tool_result] 950:    JOIN_HINTS: t.ClassVar[set[str]] = set()
1042:        exp.Hint: lambda self: self._parse_hint_body(),
1656:    TABLE_INDEX_HINT_TOKENS: t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
3394:        hint = self._parse_hint()
3428:                hint=hint,
3798:            hint = self._parse_hint()
3835:                    hint=hint,
4098:    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
4106:    def _parse_hint_function_call(self) -> exp.Expr | None:
4109:  
…[2848 chars elided]…
glot/generator.py:3109:        top_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{distinct}"
sqlglot/generator.py:4439:    def joinhint_sql(self, expression: exp.JoinHint) -> str:
sqlglot/generator.py:4484:        hints = table.args.get("hints")
sqlglot/generator.py:4485:        if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:            # T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3380,3440p sqlglot/parser.py && echo ---- && sed -n 3780,3850p sqlglot/parser.py && echo ---- && sed -n 4095,4140p sqlglot/parser.py && echo ---- && grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_merge\" sqlglot/parser.py", "description": "Read hint parsing and statement parsers"}
[tool_result]             )

        expression = parse_conditional_insert()
        while expression is not None:
            expressions.append(expression)
            expression = parse_conditional_insert()

        return self.expression(
            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
            comments=comments,
        )

    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
        comments: list[str] = []
        hint = self._parse_hin
…[5572 chars elided]…
-> exp.Hint | None:
        if self._match(TokenType.HINT) and self._prev_comments:
            return exp.maybe_parse(self._prev_comments[0], into=exp.Hint, dialect=self.dialect)

        return None

    def _parse_into(self) -> exp.Into | None:
        if not self._match(TokenType.INTO):
            return None

----
3049:    def _parse_mergeblockratio(
3582:    def _parse_delete(self) -> exp.Delete:
3605:    def _parse_update(self) -> exp.Update:
8896:    def _parse_merge(self) -> exp.Merge:
[tool_use Bash] {"command": "sed -n 3582,3630p sqlglot/parser.py && echo ---- && grep -n \"class Update\\|class Delete\\|class Insert(\" -A 22 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | grep -n \"arg_types\\|class \\|hint\" | head -30; echo ----; sed -n 2150,2160p sqlglot/generator.py; echo ----; grep -n \"def update_sql\\|def delete_sql\" -A 25 sqlglot/generator.py | head -80", "description": "Read UPDATE/DELETE parsing and generation"}
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
…[4982 chars elided]…
: exp.Values, values_as_table: bool = True) -> str:
2487-        values_as_table = values_as_table and self.VALUES_AS_TABLE
2488-
2489-        # The VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
[tool_use Bash] {"command": "sed -n 71,90p sqlglot/expressions/dml.py && sed -n 293,310p sqlglot/expressions/dml.py && echo ---- && grep -n \"HINT\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/dialects/mysql.py | head; echo ----; grep -rn \"/\\*+\" tests/dialects/test_mysql.py | head -20; echo ----; grep -n \"/\\*+\" tests/dialects/test_dialect.py tests/test_transpile.py tests/test_parser.py | head -30", "description": "Inspect DML arg types, hint tokens and existing tests"}
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
…[979 chars elided]…
kens.py:561:            tokens_preceding_hint=self.TOKENS_PRECEDING_HINT,
sqlglot/tokenizer_core.py:311:    HINT = auto()
----
tests/dialects/test_mysql.py:249:        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
tests/dialects/test_mysql.py:250:        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
tests/dialects/test_mysql.py:251:        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
----
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2','DELETE /*+ QB_NAME(x) */ FROM t WHERE a = 1','DELETE /*+ QB_NAME(x) */ t1 FROM t1 JOIN t2 ON t1.a=t2.a','INSERT /*+ NO_ENGINE */ INTO t VALUES (1)','SELECT /*+ MERGE(dt) */ * FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('hint'))); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Probe current hint parsing on UPDATE/DELETE"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2','DELETE /*+ QB_NAME(x) */ FROM t WHERE a = 1','DELETE /*+ QB_NAME(x) */ t1 FROM t1 JOIN t2 ON t1.a=t2.a','INSERT /*+ NO_ENGINE */ INTO t VALUES (1)','SELECT /*+ MERGE(dt) */ * FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('hint'))); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Probe current hint parsing with worktree on path"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "ls; ls <work>/env-sqlglot/bin/ | head; <work>/env-sqlglot/bin/python -c \"import sys;print(sys.path)\"", "description": "Check repo layout and the project venv"}
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
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
dmypy
f2py
['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot; print(sqlglot.__file__)\nfor s in ['UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2','DELETE /*+ QB_NAME(x) */ FROM t WHERE a = 1','DELETE /*+ QB_NAME(x) */ t1 FROM t1 JOIN t2 ON t1.a=t2.a','INSERT /*+ NO_ENGINE */ INTO t VALUES (1)','SELECT /*+ MERGE(dt) */ * FROM t']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.args.get('hint'))); print(e.sql('mysql'))\n    except Exception as ex: print('ERR', ex)\n\"", "description": "Probe current hint parsing on UPDATE/DELETE"}
[tool_result] ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/__init__.py
ERR Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX_MERGE(t) */, line: 1, col: 31, start: 7, end: 30, comments: [' NO_INDEX_MERGE(t) ']>. Line 1, Col: 31.
  UPDATE [4m/*+ NO_INDEX_MERGE(t) */[0m t SET a = 1 WHERE b = 2
ERR Expected table name but got <Token token_type: TokenType.HINT, text: /*+ QB_NAME(x) */, line: 1, col: 24, start:
…[122 chars elided]…
ted table name but got <Token token_type: TokenType.HINT, text: /*+ QB_NAME(x) */, line: 1, col: 24, start: 7, end: 23, comments: [' QB_NAME(x) ']>. Line 1, Col: 24.
  DELETE [4m/*+ QB_NAME(x) */[0m t1 FROM t1 JOIN t2 ON t1.a=t2.a
Hint(
  expressions=[
    Var(this=NO_ENGINE)])
INSERT /*+ NO_ENGINE */ INTO t VALUES (1)
Hint(
  expressions=[
    Anonymous(
      this=MERGE,
      expressions=[
        Column(
          this=Identifier(this=dt, quoted=False))])])
SELECT /*+ MERGE(dt) */ * FROM t
[tool_use Bash] {"command": "sed -n 1829,1840p sqlglot/generator.py; sed -n 3060,3066p sqlglot/generator.py; grep -n \"UPDATE\\|DELETE\" tests/dialects/test_mysql.py | grep -i hint; grep -n \"hint\" tests/dialects/test_mysql.py | head -20; sed -n 240,256p tests/dialects/test_mysql.py", "description": "Check hint_sql and existing MySQL hint tests"}
[tool_result]     def hint_sql(self, expression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"

    def indexparameters_sql(self, expression: exp.IndexParameters) -> str:
        using = self.sql(expression, "using")
        using = f" USING {using}" if using else ""
        columns = self.expressions(expression, key="columns", flat=True)
…[1375 chars elided]…
alidate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
        self.validate_identity("""SELECT 'ab' MEMBER OF('[23, "abc", 17, "ab", 10]')""")
        self.validate_identity("""SELECT * FROM foo WHERE 'ab' MEMBER OF(content)""")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.ex
…[34 chars elided]…
\n                tables=tables,", "new_string": "        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_INDEX_MERGE(t) */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(x) */ FROM t WHERE a = 1\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(x) */ t1 FROM t1 INNER JOIN t2 ON t1.a = t2.a\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092025-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Edits are in. Now I'll run the MySQL tests and the full suite using the project's test command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run MySQL tests and full project test suite"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.32s
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
.................................................................................................................................................................................
…[318 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 49.07s
[assistant] Full suite passes (1087 tests). Next I'll check lint and type checks on the changed files and a few more edge cases.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py && $PY/ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py) 2>&1 | tail -5; $PY -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ X */ LOW_PRIORITY t SET a = 1 ORDER BY a LIMIT 1','DELETE /*+ X */ FROM t ORDER BY a LIMIT 1','UPDATE t SET a = 1']:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n\"", "description": "Run ruff lint/format and edge-case round trips"}
[tool_result ERROR] Exit code 126
All checks passed!
4 files already formatted
(eval):1: permission denied: <work>/env-sqlglot/bin
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['UPDATE /*+ X */ LOW_PRIORITY t SET a = 1 ORDER BY a LIMIT 1','DELETE /*+ X */ FROM t ORDER BY a LIMIT 1','UPDATE t SET a = 1']:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n\"; git diff --stat", "description": "Round-trip edge cases and show diff stats"}
[tool_result] UPDATE /*+ X */ `LOW_PRIORITY` AS t SET a = 1 ORDER BY a LIMIT 1
DELETE /*+ X */ FROM t ORDER BY a LIMIT 1
UPDATE t SET a = 1
 sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 3 +++
 4 files changed, 12 insertions(+), 2 deletions(-)
[assistant] MySQL `UPDATE` and `DELETE` now accept optimizer hints, parse them, and round-trip them. The full suite passes (1087 tests) and ruff lint and format are clean on the changed files.

Changes:
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` read the hint right after the keyword, the same way `_parse_insert` does.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ table ...` and `delete_sql` emits `DELETE /*+ ... */ ...`, including the multi-table `DELETE /*+ ... */ t1 FROM ...` form.
- **`tests/dialects/test_mysql.py`**: three `validate_identity` cases covering an UPDATE hint, a single-table DELETE hint, and a multi-table DELETE hint with a join.

The tokenizer already emitted the hint token after `UPDATE` and `DELETE`, so the fix was limited to the parser and generator. Nothing is committed.

One thing I noticed but did not change: `UPDATE ... LOW_PRIORITY t` is parsed with `LOW_PRIORITY` as an alias. That is a separate gap in how `UPDATE` modifiers are parsed, not part of this hint change. Say if you want it handled here too.
