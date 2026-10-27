# trajectory base-1

final message:
`UPDATE` and `DELETE` now accept optimizer hints and round-trip them. The full suite passes (1087 tests), and ruff is clean on the changed files.

Before the change, both statements failed to parse with `Expected table name but got ... TokenType.HINT`.

The changes follow the existing `INSERT` hint pattern:

- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` read the hint right after the keyword, as `_parse_insert` does.
- **`sqlglot/expressions/dml.py`**: `Update` and `Delete` gained a `hint` arg.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t ...` and `delete_sql` emits `DELETE /*+ ... */ FROM t ...`.
- **`tests/dialects/test_mysql.py`**: three round-trip cases next to the existing MySQL hint tests. They cover `UPDATE` with a hint, `DELETE ... FROM` with a hint, and the multi-table `DELETE` form.

The hint sits directly after the keyword. That matches MySQL's placement of optimizer hints.

I did not add `UPDATE`/`DELETE` cases to the `hint`-specific tests in other dialects, and I did not commit.

## events
[tool_use Bash] {"command": "grep -n -i \"hint\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py | head -80", "description": "Find hint handling in parser and generator"}
[tool_result] sqlglot/generator.py:351:    # Whether join hints should be generated
sqlglot/generator.py:352:    JOIN_HINTS = True
sqlglot/generator.py:357:    # Whether table hints should be generated
sqlglot/generator.py:358:    TABLE_HINTS = True
sqlglot/generator.py:360:    # Whether query hints should be generated
sqlglot/generator.py:361:    QUERY_HINTS = True
sqlglot/generator.py:363:    # What kind of separator to use for query hints
sqlglot/generator.py:364:    QUERY_HINT_SEP = ", "
sqlglot/generator
…[4292 chars elided]…
               hint.set("expressions", self._parse_wrapped_id_vars())
sqlglot/parser.py:4533:                hints.append(hint)
sqlglot/parser.py:4535:        return hints or None
sqlglot/parser.py:4790:        this.set("hints", self._parse_table_hints())
sqlglot/parser.py:6339:        # Column type hint: col_name Type
sqlglot/parser.py:7994:    def _parse_join_hint(self, func_name: str) -> exp.JoinHint:
sqlglot/parser.py:7996:        return exp.JoinHint(this=func_name.upper(), expressions=args)
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parser.py >/dev/null; grep -n \"_parse_hint()\" -B8 -A12 sqlglot/parser.py | sed -n 1,200p; echo ----; sed -n 2140,2200p sqlglot/generator.py; echo ----; sed -n 3050,3070p sqlglot/generator.py", "description": "Show hint usage in parser and generator"}
[tool_result] 3386-
3387-        return self.expression(
3388-            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
3389-            comments=comments,
3390-        )
3391-
3392-    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
3393-        comments: list[str] = []
3394:        hint = self._parse_hint()
3395-        overwrite = self._match(TokenType.OVERWRITE)
3396-        ignore = self._match(TokenType.IGNORE)
3397-        local = self._match_text
…[4320 chars elided]…
pression: exp.Select) -> str:
        into = expression.args.get("into")
        if not self.SUPPORTS_SELECT_INTO and into:
            into.pop()

        hint = self.sql(expression, "hint")
        distinct = self.sql(expression, "distinct")
        distinct = f" {distinct}" if distinct else ""
        kind = self.sql(expression, "kind")

        limit = expression.args.get("limit")
        if isinstance(limit, exp.Limit) and self.LIMIT_IS_TOP:
            top = self.limit_sql(limit, top=True)
[tool_use Bash] {"command": "grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_insert\\|def _parse_select\\b\\|def _parse_delete\" sqlglot/parser.py; grep -n \"hint\" tests/dialects/test_mysql.py | head -40; grep -n \"def update_sql\\|def delete_sql\" -A25 sqlglot/generator.py | head -80", "description": "Locate update/delete parsing and generation"}
[tool_result] 3392:    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
3450:    def _parse_insert_table(self) -> exp.Expr | None:
3582:    def _parse_delete(self) -> exp.Delete:
3605:    def _parse_update(self) -> exp.Update:
3735:    def _parse_select(
126:            "/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
127:            "/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
298:        # Index hints
1687:    def delete_sql(self, expression: exp.Delete) -> str:
16
…[2377 chars elided]…
: exp.Values, values_as_table: bool = True) -> str:
2487-        values_as_table = values_as_table and self.VALUES_AS_TABLE
2488-
2489-        # The VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
[tool_use Bash] {"command": "sed -n 3582,3640p sqlglot/parser.py; echo ----; sed -n 4095,4140p sqlglot/parser.py; echo ----; grep -n \"class Delete\\|class Update\\|class Insert\\|class Hint\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -90; echo ----; grep -n \"hint\" tests/dialects/test_mysql.py tests/test_transpile.py tests/dialects/test_dialect.py | head -40", "description": "Read delete/update parsers, hint expr, tests"}
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
…[6136 chars elided]…
types = {"this": True, "quoted": False, "global_": False, "temporary": False}
sqlglot/expressions/core.py-1768-    is_primitive = True
sqlglot/expressions/core.py-1769-    _hash_raw_args = True
sqlglot/expressions/core.py-1770-
----
tests/dialects/test_mysql.py:126:            "/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
tests/dialects/test_mysql.py:127:            "/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
tests/dialects/test_mysql.py:298:        # Index hints
[tool_use Bash] {"command": "grep -rn \"/\\*+\" tests/ | head -40; git status --short; git log --oneline -1", "description": "Find existing optimizer hint tests"}
[tool_result] tests/test_lineage.py:519:        INSERT /*+ HINT1 */
tests/test_lineage.py:523:          SELECT /*+ HINT2 */
tests/test_build.py:143:                "SELECT /*+ REPARTITION(100) */ x FROM tbl",
tests/test_build.py:148:                "SELECT /*+ COALESCE(3), BROADCAST(x) */ x FROM tbl",
tests/dialects/test_oracle.py:333:            "SELECT /*+ ORDERED */* FROM tbl", "SELECT /*+ ORDERED */ * FROM tbl"
tests/dialects/test_oracle.py:336:            "SELECT /* test */ /*+ ORDERED */* FROM tbl",
tes
…[4583 chars elided]…
              "spark": "SELECT /*+ BROADCASTJOIN(table) */ cola FROM table",
tests/dialects/test_spark.py:231:            "SELECT /*+ MAPJOIN(table) */ cola FROM table",
tests/dialects/test_spark.py:233:                "spark": "SELECT /*+ MAPJOIN(table) */ cola FROM table",
tests/dialects/test_spark.py:238:            "SELECT /*+ MERGE(table) */ cola FROM table",
tests/dialects/test_spark.py:240:                "spark": "SELECT /*+ MERGE(table) */ cola FROM table",
cc2f91a87 lithify: probe base
[tool_use Bash] {"command": "grep -n \"/\\*+\" tests/dialects/test_mysql.py; ls <work>/env-sqlglot/bin/python && <work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.i
…[23 chars elided]…
lglot\nfor s in ['SELECT /*+ NO_INDEX(t i) */ * FROM t','INSERT /*+ X */ INTO t VALUES (1)','UPDATE /*+ NO_INDEX(t i) */ t SET a = 1 WHERE b = 2','DELETE /*+ NO_INDEX(t i) */ FROM t WHERE b = 2']:\n    try:\n        e = sqlglot.parse_one(s, read='mysql'); print(repr(e.sql('mysql')))\n    except Exception as ex: print('ERR', s, ex)\n\"", "description": "Check mysql hint tests and current behavior"}
[tool_result] 249:        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
250:        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
251:        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
<work>/env-sqlglot/bin/python
'SELECT /*+ NO_INDEX(t i) */ * FROM t'
'INSERT /*+ X */ INTO t VAL
…[88 chars elided]…
 got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX(t i) */, line: 1, col: 27, start: 7, end: 26, comments: [' NO_INDEX(t i) ']>. Line 1, Col: 27.
  UPDATE [4m/*+ NO_INDEX(t i) */[0m t SET a = 1 WHERE b = 2
ERR DELETE /*+ NO_INDEX(t i) */ FROM t WHERE b = 2 Expected table name but got <Token token_type: TokenType.HINT, text: /*+ NO_INDEX(t i) */, line: 1, col: 27, start: 7, end: 26, comments: [' NO_INDEX(t i) ']>. Line 1, Col: 27.
  DELETE [4m/*+ NO_INDEX(t i) */[0m FROM t WHERE b = 2
[assistant] Reproduced: `UPDATE` and `DELETE` fail on the hint token. The `INSERT` path already has the pattern (`_parse_hint()` first, `hint` arg, generator emits it after the keyword), so I'll mirror it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        # https://dev.mysql.com/doc/refman/8.0/en/delete.html\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n      
…[160 chars elided]…
ps://dev.mysql.com/doc/refman/8.0/en/delete.html\n        hint = self._parse_hint()\n        tables = None\n        if not self._match(TokenType.FROM, advance=False):\n            tables = self._parse_csv(self._parse_table) or None\n\n        returning = self._parse_returning()\n\n        return self.expression(\n            exp.Delete(\n                hint=hint,\n                tables=tables,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py", "old_string": "        kwargs: dict[str, object] = {\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }", "new_string": "        kwargs: dict[str, object] = {\n            \"hint\": self._parse_hint(),\n            \"this\": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,", "new_string": "class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py", "old_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"this\": False,", "new_string": "class Update(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n        \"hint\": False,\n        \"this\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def delete_sql(self, expression: exp.Delete) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        return self.prepend_ctes(expression, f\"DELETE{tables}{expression_sql}\")", "new_string": "        return self.prepend_ctes(expression, f\"DELETE{hint}{tables}{expression_sql}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "    def update_sql(self, expression: exp.Update) -> str:\n        this = self.sql(expression, \"this\")", "new_string": "    def update_sql(self, expression: exp.Update) -> str:\n        hint = self.sql(expression, \"hint\")\n        this = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py", "old_string": "        sql = f\"UPDATE {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\"", "new_string": "        sql = f\"UPDATE{hint} {this}{join_sql} SET {set_sql}{expression_sql}{order}{limit}{options}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add tests next to the existing MySQL hint tests, then run them.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "offset": 246, "limit": 8}
[tool_result] 246	        self.validate_identity("LOCK TABLES `app_fields` WRITE", check_command_warning=True)
247	        self.validate_identity("SELECT 1 XOR 0")
248	        self.validate_identity("SELECT 1 && 0", "SELECT 1 AND 0")
249	        self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN t2")
250	        self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS dt")
251	        self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
252	        self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
253	        self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n", "new_string": "        self.validate_identity(\"SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'\")\n        self.validate_identity(\"UPDATE /*+ NO_INDEX(t i) */ t SET a = 1 WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t i) */ FROM t WHERE b = 2\")\n        self.validate_identity(\"DELETE /*+ NO_INDEX(t1 i) */ t1 FROM t1 JOIN t2 ON t1.a = t2.a\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-134315-mysql-dialect-mysql-allows-optim/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -30", "description": "Run MySQL dialect tests"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.42s
[assistant] MySQL tests pass. Next, the full suite with the project's checks, plus lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; ($PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_mysql.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[212 chars elided]…
................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 53.73s
All checks passed!
4 files already formatted
[assistant] Full suite passes: 1087 tests, and ruff check and format are clean on the changed files. I'll leave the changes uncommitted, since you didn't ask for a commit.
[tool_use Bash] {"command": "git diff --stat", "description": "Show changed files summary"}
[tool_result]  sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 3 +++
 4 files changed, 12 insertions(+), 2 deletions(-)
[assistant] `UPDATE` and `DELETE` now accept optimizer hints and round-trip them. The full suite passes (1087 tests), and ruff is clean on the changed files.

Before the change, both statements failed to parse with `Expected table name but got ... TokenType.HINT`.

The changes follow the existing `INSERT` hint pattern:

- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` read the hint right after the keyword, as `_parse_insert` does.
- **`sqlglot/expressions/dml.py`**: `Update` and `Delete` gained a `hint` arg.
- **`sqlglot/generator.py`**: `update_sql` emits `UPDATE /*+ ... */ t ...` and `delete_sql` emits `DELETE /*+ ... */ FROM t ...`.
- **`tests/dialects/test_mysql.py`**: three round-trip cases next to the existing MySQL hint tests. They cover `UPDATE` with a hint, `DELETE ... FROM` with a hint, and the multi-table `DELETE` form.

The hint sits directly after the keyword. That matches MySQL's placement of optimizer hints.

I did not add `UPDATE`/`DELETE` cases to the `hint`-specific tests in other dialects, and I did not commit.
