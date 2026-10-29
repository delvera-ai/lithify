# trajectory base-1

final message:
Pretty-printing is now idempotent for multi-line comments on `AND`/`OR` connectors. Formatting the same query repeatedly gives the same output each time.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the comment text was appended to the operator without the line-break sentinel that `maybe_comment` uses. Each re-format re-indented the comment's continuation line, so the whitespace grew every pass.

**Fix:** One line in `sqlglot/generator.py`. The connector comment now goes through `self._replace_line_breaks(...)`, the same as `maybe_comment`.

**Test:** Added `test_pretty_connector_comment_is_idempotent` to `tests/test_transpile.py`. It checks the first format and then three re-formats of the output.

**Verification:**
- Before the fix, the repro grew the indent on each pass. After the fix, the output is stable from the first pass on.
- Full suite: 1114 passed, 18162 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

I did not run the new test against the unfixed code. The before/after repro above is the evidence it catches the bug.

I did not commit anything. The branch has uncommitted edits to the two files above.

## events
[tool_use Bash] {"command": "grep -n \"def connector_sql\\|def binary\\|def _comments\\|def maybe_comment\\|def sep\\|def seg\" sqlglot/generator.py | head -30", "description": "Locate connector and comment helpers in generator"}
[tool_result] 976:    def sep(self, sep: str = " ") -> str:
979:    def seg(self, sql: str, sep: str = " ") -> str:
993:    def maybe_comment(
3901:    def connector_sql(
4429:    def binary(self, expression: exp.Binary, op: str) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "offset": 3895, "limit": 40}
[tool_result] 3895	    def or_sql(self, expression: exp.Or, stack: list[str | exp.Expr] | None = None) -> str:
3896	        return self.connector_sql(expression, "OR", stack)
3897	
3898	    def xor_sql(self, expression: exp.Xor, stack: list[str | exp.Expr] | None = None) -> str:
3899	        return self.connector_sql(expression, "XOR", stack)
3900	
3901	    def connector_sql(
3902	        self,
3903	        expression: exp.Connector,
3904	        op: str,
3905	        stack: list[str | exp.Expr] | None = None
…[687 chars elided]…

3923	        while stack:
3924	            node = stack.pop()
3925	            if isinstance(node, exp.Connector):
3926	                ops.add(getattr(self, f"{node.key}_sql")(node, stack))
3927	            else:
3928	                sql = self.sql(node)
3929	                if sqls and sqls[-1] in ops:
3930	                    sqls[-1] += f" {sql}"
3931	                else:
3932	                    sqls.append(sql)
3933	
3934	        sep = "\n" if self.pretty and self.too_wide(sqls) else " "
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "offset": 970, "limit": 50}
[tool_result] 970	
971	    def unsupported(self, message: str) -> None:
972	        if self.unsupported_level == ErrorLevel.IMMEDIATE:
973	            raise UnsupportedError(message)
974	        self.unsupported_messages.append(message)
975	
976	    def sep(self, sep: str = " ") -> str:
977	        return f"{sep.strip()}\n" if self.pretty else sep
978	
979	    def seg(self, sql: str, sep: str = " ") -> str:
980	        return f"{self.sep(sep)}{sql}"
981	
982	    def sanitize_comment(self, comment: str) -> str
…[993 chars elided]…
f not comments or isinstance(expression, self.EXCLUDE_COMMENTS):
1007	            return sql
1008	
1009	        comments_sql = " ".join(
1010	            f"/*{self.sanitize_comment(comment)}*/" for comment in comments if comment
1011	        )
1012	
1013	        if not comments_sql:
1014	            return sql
1015	
1016	        comments_sql = self._replace_line_breaks(comments_sql)
1017	
1018	        if separated or isinstance(expression, self.WITH_SEPARATED_COMMENTS):
1019	            return (
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "offset": 4425, "limit": 25}
[tool_result] 4425	        this = self.sql(expression, "this") or self.expressions(expression, flat=True)
4426	        this = f" {this}" if this else ""
4427	        return f"USE{kind}{this}"
4428	
4429	    def binary(self, expression: exp.Binary, op: str) -> str:
4430	        sqls: list[str] = []
4431	        stack: list[None | str | exp.Expr] = [expression]
4432	        binary_type = type(expression)
4433	
4434	        while stack:
4435	            node = stack.pop()
4436	
4437	            if type(node) is binary_type:
4438	                op_func = node.args.get("operator")
4439	                if op_func:
4440	                    op = f"OPERATOR({self.sql(op_func)})"
4441	
4442	                stack.append(node.args.get("expression"))
4443	                stack.append(f" {self.maybe_comment(op, comments=node.comments)} ")
4444	                stack.append(node.args.get("this"))
4445	            else:
4446	                sqls.append(self.sql(node))
4447	
4448	        return "".join(sqls)
4449	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "offset": 3934, "limit": 15}
[tool_result] 3934	        sep = "\n" if self.pretty and self.too_wide(sqls) else " "
3935	        return sep.join(sqls)
3936	
3937	    def bitwiseand_sql(self, expression: exp.BitwiseAnd) -> str:
3938	        return self.binary(expression, "&")
3939	
3940	    def bitwiseleftshift_sql(self, expression: exp.BitwiseLeftShift) -> str:
3941	        return self.binary(expression, "<<")
3942	
3943	    def bitwisenot_sql(self, expression: exp.BitwiseNot) -> str:
3944	        return f"~{self.sql(expression, 'this')}"
3945	
3946	    def bitwiseor_sql(self, expression: exp.BitwiseOr) -> str:
3947	        return self.binary(expression, "|")
3948	
[tool_use Bash] {"command": "grep -n \"def too_wide\\|def _replace_line_breaks\" -A8 sqlglot/generator.py", "description": "Show too_wide and line-break helper definitions"}
[tool_result] 4497:    def too_wide(self, args: t.Iterable) -> bool:
4498-        return sum(len(arg) for arg in args) > self.max_text_width
4499-
4500-    def format_time(
4501-        self,
4502-        expression: exp.Expr,
4503-        inverse_time_mapping: dict[str, str] | None = None,
4504-        inverse_time_trie: dict | None = None,
4505-    ) -> str | None:
--
5201:    def _replace_line_breaks(self, string: str) -> str:
5202-        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
5203-        if self.pretty:
5204-            return string.replace("\n", self.SENTINEL_LINE_BREAK)
5205-        return string
5206-
5207-    def copyparameter_sql(self, expression: exp.CopyParameter) -> str:
5208-        option = self.sql(expression, "this")
5209-
[assistant] Found the likely spot: in `connector_sql`, the stack branch appends sanitized comments to `op` without `_replace_line_breaks`, unlike `maybe_comment`. Let me reproduce before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nsql = 'SELECT a FROM t WHERE x = 1 AND /* line one\\nline two */ y = 2 OR z = 3'\ns = sql\nfor i in range(3):\n    s = sqlglot.transpile(s, read='duckdb', write='duckdb', pretty=True)[0]\n    print(repr(s))\n\"", "description": "Reproduce non-idempotent pretty printing of connector comments"}
[tool_result] 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n  line two */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n    line two */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n      line two */ y = 2 OR z = 3'
[assistant] Reproduced: each re-format indents the continuation line further. The fix is to route the connector comment through `_replace_line_breaks` the same way `maybe_comment` does, so the newline is protected by the sentinel.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                            op += self._replace_line_breaks(f\" /*{self.sanitize_comment(comment)}*/\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nsql = 'SELECT a FROM t WHERE x = 1 AND /* line one\\nline two */ y = 2 OR z = 3'\ns = sql\nfor i in range(4):\n    s = sqlglot.transpile(s, read='duckdb', write='duckdb', pretty=True)[0]\n    print(repr(s))\n\"", "description": "Apply fix and re-run the repeated-format check"}
[tool_result] 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\nline two */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\nline two */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\nline two */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\nline two */ y = 2 OR z = 3'
[assistant] Output is now stable across repeated formatting. Next I'll add a regression test next to the existing pretty-print comment tests, then run the suite.
[tool_use Bash] {"command": "grep -n \"def test_comments\\|pretty=True\" tests/test_transpile.py | head -30; grep -n \"def test_comments\" -A3 tests/test_transpile.py | head", "description": "Find existing comment pretty-print tests"}
[tool_result] 88:            pretty=True,
96:            pretty=True,
102:            pretty=True,
118:    def test_comments(self):
223:            pretty=True,
246:            pretty=True,
272:            pretty=True,
314:            pretty=True,
335:            pretty=True,
372:            pretty=True,
396:            pretty=True,
411:            pretty=True,
424:            pretty=True,
433:            pretty=True,
440:            pretty=True,
482:            pretty=True,
516:            pretty=True,
523: 
…[244 chars elided]…
ELECT '1\n2'", pretty=True)[0], "SELECT\n  '1\n2'")
988:            transpile("SELECT '1\n2'", pretty=True, unsupported_level=ErrorLevel.IGNORE)[0],
991:        self.assertEqual(transpile('SELECT "1\n2"', pretty=True)[0], 'SELECT\n  "1\n2"')
993:            transpile('SELECT "Product\n(Foo, Bar)" AS x FROM t', pretty=True)[0],
118:    def test_comments(self):
119-        self.validate(
120-            "select /* asfd /* asdf */ asdf */ 1",
121-            "/* asfd / * asdf * / asdf */ SELECT 1",
[tool_use Bash] {"command": "sed -n 975,1000p tests/test_transpile.py", "description": "View the pretty-print multi-line string tests"}
[tool_result]             with self.subTest(sql):
                self.assertEqual(transpile(sql, error_level=ErrorLevel.IGNORE)[0], sql.strip())

    def test_pretty(self):
        for _, sql, pretty in load_sql_fixture_pairs("pretty.sql"):
            with self.subTest(sql[:100]):
                generated = transpile(sql, pretty=True)[0]
                self.assertEqual(generated, pretty)
                self.assertEqual(parse_one(sql), parse_one(pretty))

    def test_pretty_line_breaks(self):
        sel
…[142 chars elided]…
 pretty=True, unsupported_level=ErrorLevel.IGNORE)[0],
            "SELECT\n  '1\n2'",
        )
        self.assertEqual(transpile('SELECT "1\n2"', pretty=True)[0], 'SELECT\n  "1\n2"')
        self.assertEqual(
            transpile('SELECT "Product\n(Foo, Bar)" AS x FROM t', pretty=True)[0],
            'SELECT\n  "Product\n(Foo, Bar)" AS x\nFROM t',
        )

    def test_sql_security(self):
        sqlglot_sql = "CREATE VIEW v SQL SECURITY INVOKER AS SELECT 1"

        for dialect, sql in [
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    def test_sql_security(self):", "new_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    d
…[182 chars elided]…
y=True)[0]\n        self.assertEqual(\n            once, \"SELECT\\n  a\\nFROM t\\nWHERE\\n  x = 1 AND /* line one\\nline two */ y = 2 OR z = 3\"\n        )\n        for _ in range(3):\n            once = transpile(once, pretty=True)[0]\n            self.assertEqual(once, \"SELECT\\n  a\\nFROM t\\nWHERE\\n  x = 1 AND /* line one\\nline two */ y = 2 OR z = 3\")\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[assistant] That second assertion line is long, so I'll tidy it with a local variable before running the checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "        sql = \"SELECT a FROM t WHERE x = 1 AND /* line one\\nline two */ y = 2 OR z = 3\"\n        once = transpile(sql, pretty=True)[0]\n        self.assertEqual(\n            once, \"SELECT\\n  a\\nFROM t\\nWHE
…[268 chars elided]…
z = 3\")", "new_string": "        sql = \"SELECT a FROM t WHERE x = 1 AND /* line one\\nline two */ y = 2 OR z = 3\"\n        expected = \"SELECT\\n  a\\nFROM t\\nWHERE\\n  x = 1 AND /* line one\\nline two */ y = 2 OR z = 3\"\n        self.assertEqual(transpile(sql, pretty=True)[0], expected)\n        for _ in range(3):\n            self.assertEqual(transpile(expected, pretty=True)[0], expected)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-133314-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite with the repo's test command", "timeout": 600000}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
........................... [ 27%]
.......................................................................................................................................................................................
…[274 chars elided]…
........ [ 65%]
............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 50.09s
[assistant] All 1114 tests pass. I'll run the linter on the two touched files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generator.py tests/test_transpile.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/test_transpile.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files, show diff stat"}
[tool_result] All checks passed!
Would reformat: sqlglot/generator.py
1 file would be reformatted, 1 file already formatted
 sqlglot/generator.py    | 2 +-
 tests/test_transpile.py | 7 +++++++
 2 files changed, 8 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --diff sqlglot/generator.py 2>&1 | head -20", "description": "Show the formatter diff for generator.py"}
[tool_result] --- sqlglot/generator.py
+++ sqlglot/generator.py
@@ -3912,7 +3912,9 @@
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-                            op += self._replace_line_breaks(f" /*{self.sanitize_comment(comment)}*/")
+                            op += self._replace_line_breaks(
+                                f" /*{self.sanitize_comment(comment)}*/"
+                            )
                 stack.extend((op, expression.left))
             return op
 

1 file would be reformatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format sqlglot/generator.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/test_transpile.py && git diff", "description": "Apply formatter fix and show final diff"}
[tool_result] 1 file reformatted
2 files already formatted
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 7c9bd3c02..2f7b64676 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -3912,7 +3912,9 @@ class Generator:
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-                            op += f" /*{self.sanitize_comment(comment)}*/"
+                            op += self._r
…[598 chars elided]…
 = 2 OR z = 3"
+        expected = "SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\nline two */ y = 2 OR z = 3"
+        self.assertEqual(transpile(sql, pretty=True)[0], expected)
+        for _ in range(3):
+            self.assertEqual(transpile(expected, pretty=True)[0], expected)
+
     def test_sql_security(self):
         sqlglot_sql = "CREATE VIEW v SQL SECURITY INVOKER AS SELECT 1"
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The formatter only re-wrapped that line, but I'll re-run the transpile tests to confirm the final state.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | tail -2", "description": "Re-run transpile tests after formatting", "timeout": 300000}
[tool_result] .............................                              [100%]
29 passed, 1022 subtests passed in 0.26s
[assistant] Pretty-printing is now idempotent for multi-line comments on `AND`/`OR` connectors. Formatting the same query repeatedly gives the same output each time.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the comment text was appended to the operator without the line-break sentinel that `maybe_comment` uses. Each re-format re-indented the comment's continuation line, so the whitespace grew every pass.

**Fix:** One line in `sqlglot/generator.py`. The connector comment now goes through `self._replace_line_breaks(...)`, the same as `maybe_comment`.

**Test:** Added `test_pretty_connector_comment_is_idempotent` to `tests/test_transpile.py`. It checks the first format and then three re-formats of the output.

**Verification:**
- Before the fix, the repro grew the indent on each pass. After the fix, the output is stable from the first pass on.
- Full suite: 1114 passed, 18162 subtests passed.
- `ruff check` and `ruff format --check` pass on both files.

I did not run the new test against the unfixed code. The before/after repro above is the evidence it catches the bug.

I did not commit anything. The branch has uncommitted edits to the two files above.
