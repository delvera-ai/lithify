# trajectory base-1

final message:
`UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests) and ruff check and format are clean. I haven't committed anything.

The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so the change was in three places:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, as `Insert` and `Select` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` right after the keyword.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t1 ...` and `delete_sql` emits `DELETE /*+ ... */ ...`.

The tests are three round-trip cases in `tests/dialects/test_mysql.py`: an `UPDATE` with a hint, a `DELETE FROM` with a hint, and a multi-table `DELETE` with a hint.

The parser change is in the base parser, not the MySQL dialect class. That matches how `SELECT` and `INSERT` hints are handled, so other dialects that emit hints will also get `UPDATE`/`DELETE` hints. I did not check the other dialects' output.

## events
[tool_use Bash] {"command": "grep -n -i \"hint\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find hint handling code"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:351:    # Whether join hints should be generated
sqlglot/generator.py:352:    JOIN_HINTS = True
sqlglot/generator.py:357:    # Whether table hints should be generated
sqlglot/generator.py:358:    TABLE_HINTS = True
sqlglot/generator.py:360:    # Whether query hints should be generated
sqlglot/generator.py:361:    QUERY_HINTS = True
sqlglot/generator.py:363:    # What kind of separator to use for query hints
sq
…[4358 chars elided]…
               hint.set("expressions", self._parse_wrapped_id_vars())
sqlglot/parser.py:4533:                hints.append(hint)
sqlglot/parser.py:4535:        return hints or None
sqlglot/parser.py:4790:        this.set("hints", self._parse_table_hints())
sqlglot/parser.py:6339:        # Column type hint: col_name Type
sqlglot/parser.py:7994:    def _parse_join_hint(self, func_name: str) -> exp.JoinHint:
sqlglot/parser.py:7996:        return exp.JoinHint(this=func_name.upper(), expressions=args)
[tool_use Bash] {"command": "sed -n 4095,4135p sqlglot/parser.py && echo ---- && sed -n 3780,3845p sqlglot/parser.py && echo ---- && sed -n 3385,3435p sqlglot/parser.py && echo ---- && grep -n \"_parse_update\\|_parse_delete\\|def _parse_statement\" sqlglot/parser.py | head -30", "description": "Read hint parsing and select/insert code"}
[tool_result]         return this

    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
        start = self._curr
        while self._curr:
            self._advance()

        end = self._tokens[self._index - 1]
        return exp.Hint(expressions=[self._find_sql(start, end)])

    def _parse_hint_function_call(self) -> exp.Expr | None:
        return self._parse_function_call()

    def _parse_hint_body(self) -> exp.Hint | None:
        start_index = self._index
        should_fallback_to_strin
…[4885 chars elided]…
 by_name=self._match_text_seq("BY", "NAME"),
                exists=self._parse_exists(),
                where=self._match_pair(TokenType.REPLACE, TokenType.WHERE)
                and self._parse_disjunction(),
----
1075:        TokenType.DELETE: lambda self: self._parse_delete(),
1093:        TokenType.UPDATE: lambda self: self._parse_update(),
2253:    def _parse_statement(self) -> exp.Expr | None:
3582:    def _parse_delete(self) -> exp.Delete:
3605:    def _parse_update(self) -> exp.Update:
[tool_use Bash] {"command": "grep -n \"HINT\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/dialects/mysql.py | head; grep -n \"class Update\\|class Delete\\|class Insert\" -A 25 sqlglot/expressions/*.py 2>/dev/null | head -120; ls sqlglot | head -50", "description": "Locate hint tokens and DML expressions"}
[tool_result] sqlglot/tokenizer_core.py:311:    HINT = auto()
sqlglot/tokenizer_core.py:905:            self._add(TokenType.HINT)
sqlglot/tokens.py:54:    HINT_START: t.ClassVar[str]
sqlglot/tokens.py:64:    TOKENS_PRECEDING_HINT: t.ClassVar[set[TokenType]]
sqlglot/tokens.py:106:        if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107:            cls._COMMENTS[cls.HINT_START] = "*/"
sqlglot/tokens.py:184:    HINT_START = "/*+"
sqlglot/tokens.py:186:    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenT
…[4295 chars elided]…
15-
sqlglot/expressions/dml.py-316-        Example:
sqlglot/expressions/dml.py-317-            >>> Update().table("my_table").set_("x = 1").sql()
sqlglot/expressions/dml.py-318-            'UPDATE my_table SET x = 1'
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
[tool_use Bash] {"command": "sed -n 3582,3640p sqlglot/parser.py; echo ----; grep -n \"def delete_sql\\|def update_sql\" -A 22 sqlglot/generator.py; echo ----; grep -n \"/\\*+\" tests/dialects/test_mysql.py | head -30; grep -n \"TOKENS_PRECEDING_HINT\" -B2 -A8 sqlglot/tokenizer_core.py | sed -n 1,40p", "description": "Read delete/update parsing and generation"}
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
…[4477 chars elided]…
 VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
----
249:        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
250:        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
251:        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
[assistant] The tokenizer already emits hint tokens after `UPDATE` and `DELETE`, so the gap is in the parser and generator. `INSERT` and `SELECT` handle it the same way, so I'll mirror that pattern.
[tool_use Bash] {"command": "sed -n 2150,2160p sqlglot/generator.py; sed -n 3060,3066p sqlglot/generator.py; sed -n 1826,1835p sqlglot/generator.py; git status --short", "description": "Check insert/select hint generation and tree state"}
[tool_result]         sql = f"SYSTEM_VERSIONING={on_sql}"

        return f"WITH({sql})" if expression.args.get("with_") else sql

    def insert_sql(self, expression: exp.Insert) -> str:
        hint = self.sql(expression, "hint")
        overwrite = expression.args.get("overwrite")

        if isinstance(expression.this, exp.Directory):
            this = " OVERWRITE" if overwrite else " INTO"
        if not self.SUPPORTS_SELECT_INTO and into:
            into.pop()

        hint = self.sql(expression, "hin
…[9 chars elided]…
   distinct = self.sql(expression, "distinct")
        distinct = f" {distinct}" if distinct else ""
        kind = self.sql(expression, "kind")
        agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
        return self.sql(agg)

    def hint_sql(self, expression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"
[assistant] Now the edits: expression args, parser, and generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_delete(self) -> exp.Delete:\n        # This handles MySQL's \"Multiple-Table Syntax\"\n        # https://dev.mysql.com/doc/refman/8.0/en/delete.html\n        tables = None\n        if not self._match(Toke
…[364 chars elided]…
ps://dev.mysql.com/doc/refman/8.0/en/delete.html\n        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "    def _parse_update(self) -> exp.Update:\n        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a test next to the existing SELECT hint cases in the MySQL test file.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "offset": 244, "limit": 12}
[tool_result] 244	        self.validate_identity("SELECT @var1 := 1, @var2")
245	        self.validate_identity("UNLOCK TABLES")
246	        self.validate_identity("LOCK TABLES `app_fields` WRITE", check_command_warning=True)
247	        self.validate_identity("SELECT 1 XOR 0")
248	        self.validate_identity("SELECT 1 && 0", "SELECT 1 AND 0")
249	        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
250	        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
251	        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
252	        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
253	        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
254	        self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
255	        self.validate_identity("""SELECT 'ab' MEMBER OF('[23, "abc", 17, "ab", 10]')""")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_MERGE(t1) */ t1 SET c1 = 1 WHERE c2 = 2\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(del) */ FROM t1 WHERE c1 = 1\")\n        self.validate_identity(\"DELETE /*+ QB_NAME(del) */ t1 FROM t1 INNER JOIN t2 ON t1.id = t2.id\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164625-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30", "description": "Run MySQL dialect tests"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.37s
[assistant] MySQL tests pass. Running the full suite and the linter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py && ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py) 2>&1 | tail -10", "description": "Run full test suite and ruff checks"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[286 chars elided]…
 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 49.07s
All checks passed!
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "ruff format tests/dialects/test_mysql.py && git diff --stat && git diff tests/ && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Format test file and re-run MySQL tests"}
[tool_result] 1 file reformatted
 sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 5 +++++
 4 files changed, 14 insertions(+), 2 deletions(-)
diff --git a/tests/dialects/test_mysql.py b/tests/dialects/test_mysql.py
index adce51119..f15812aee 100644
--- a/tests/dialects/test_mysql.py
+++ b/tests/dialects/test_mysql.py
@@ -249,6 +249,11 @@ class TestMySQL(Validator):
         self.validate_identity("SELECT /*+ BKA(
…[502 chars elided]…
id = t2.id"
+        )
         self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
         self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
         self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
....................                                              [100%]
50 passed, 481 subtests passed in 0.17s
[This command modified 1 file you've previously read: tests/dialects/test_mysql.py. Call Read before editing.]
[assistant] `UPDATE` and `DELETE` now accept optimizer hints, and they parse and round-trip. The full suite passes (1087 tests) and ruff check and format are clean. I haven't committed anything.

The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so the change was in three places:

- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, as `Insert` and `Select` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` call `_parse_hint()` right after the keyword.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t1 ...` and `delete_sql` emits `DELETE /*+ ... */ ...`.

The tests are three round-trip cases in `tests/dialects/test_mysql.py`: an `UPDATE` with a hint, a `DELETE FROM` with a hint, and a multi-table `DELETE` with a hint.

The parser change is in the base parser, not the MySQL dialect class. That matches how `SELECT` and `INSERT` hints are handled, so other dialects that emit hints will also get `UPDATE`/`DELETE` hints. I did not check the other dialects' output.
