# trajectory base-1

final message:
Formatting a query with a multi-line comment on an `AND`/`OR` is now idempotent. Repeated `pretty=True` passes return the same output.

**Cause:** `Generator.connector_sql` (`sqlglot/generator.py`) appends connector comments to the operator string with the raw text. Pretty-printing then re-indents every line of that string, so each continuation line of the comment gains two spaces per pass. `maybe_comment` avoids this by wrapping comments in `_replace_line_breaks`, which swaps newlines for a sentinel that is restored at the end. The connector path skipped that step.

**Fix:** one change in `sqlglot/generator.py`: the connector comment now goes through `self._replace_line_breaks(...)`, the same protection `maybe_comment` uses.

**Verification:**
- Before the fix, `x = 1 AND /* line one\n   line two */ y = 2` gained indentation on each pass (pass 1 through 3 all differed). After the fix, the output is identical on every pass, for both `AND` and `OR`.
- Added `test_pretty_connector_comment_line_breaks_are_idempotent` in `tests/test_transpile.py`. It checks the exact pretty output and that re-formatting it changes nothing.
- Full suite: 1114 passed. `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything. The changes are in the worktree for you to review.

## events
[tool_use Bash] {"command": "grep -n \"def connector_sql\\|def and_sql\\|def or_sql\\|def binary\\|def _connector_sql\\|connector_sql\" sqlglot/generator.py | head -30", "description": "Locate connector generation code"}
[tool_result] 3892:    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
3893:        return self.connector_sql(expression, "AND", stack)
3895:    def or_sql(self, expression: exp.Or, stack: list[str | exp.Expr] | None = None) -> str:
3896:        return self.connector_sql(expression, "OR", stack)
3899:        return self.connector_sql(expression, "XOR", stack)
3901:    def connector_sql(
4429:    def binary(self, expression: exp.Binary, op: str) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "offset": 3885, "limit": 80}
[tool_result] 3885	        this = self.sql(expression, "this")
3886	        zone = self.sql(expression, "zone")
3887	        return f"{this} AT TIME ZONE {zone} AT TIME ZONE 'UTC'"
3888	
3889	    def add_sql(self, expression: exp.Add) -> str:
3890	        return self.binary(expression, "+")
3891	
3892	    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
3893	        return self.connector_sql(expression, "AND", stack)
3894	
3895	    def or_sql(self, expression: exp.Or, 
…[2649 chars elided]…
format_sql}" if format_sql else ""
3958	        to_sql = self.sql(expression, "to")
3959	        to_sql = f" {to_sql}" if to_sql else ""
3960	        action = self.sql(expression, "action")
3961	        action = f" {action}" if action else ""
3962	        default = self.sql(expression, "default")
3963	        default = f" DEFAULT {default} ON CONVERSION ERROR" if default else ""
3964	        return f"{safe_prefix or ''}CAST({self.sql(expression, 'this')} AS{to_sql}{default}{format_sql}{action})"
[assistant] Let me reproduce the non-idempotent formatting before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nsql = '''SELECT a FROM t WHERE x = 1 AND /* first long comment line that is quite long to force wrap */ y = 2 AND /* second comment that is also fairly long to exceed width */ z = 3'''\nout = sqlglot.transpile(sql, read='duckdb', write='duckdb', pretty=True)[0]\nprint(repr(out))\nfor i in range(3):\n    out2 = sqlglot.transpile(out, read='duckdb', write='duckdb', pretty=True)[0]\n    print(i, repr(out2), out2 == out)\n    out = out2\n\" 2>&1 | tail -20", "description": "Reproduce non-idempotent pretty-print with connector comments"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "cat > /tmp/repro_conn.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1\")\nimport sqlglot\nsql = '''SELECT a FROM t WHERE x = 1 AND /* first long comment line that is quite long to force wrap */ y = 2 AND /* second comment that is also fairly long to exceed width */ z = 3'''\nout =
…[32 chars elided]…
ckdb', write='duckdb', pretty=True)[0]\nprint(repr(out))\nfor i in range(3):\n    out2 = sqlglot.transpile(out, read='duckdb', write='duckdb', pretty=True)[0]\n    print(i, repr(out2), out2 == out)\n    out = out2\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_conn.py 2>&1 | tail -20", "description": "Run reproduction script against worktree sqlglot"}
[tool_result] 'SELECT\n  a\nFROM t\nWHERE\n  x = 1\n  AND /* first long comment line that is quite long to force wrap */ y = 2\n  AND /* second comment that is also fairly long to exceed width */ z = 3'
0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1\n  AND /* first long comment line that is quite long to force wrap */ y = 2\n  AND /* second comment that is also fairly long to exceed width */ z = 3' True
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1\n  AND /* first long comment line that is quite long to force wrap */ y = 2\n  AND /* second comment that is also fairly long to exceed width */ z = 3' True
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1\n  AND /* first long comment line that is quite long to force wrap */ y = 2\n  AND /* second comment that is also fairly long to exceed width */ z = 3' True
[assistant] The single-line comments are stable. The report says *multi-line* comments, so I'll try comments containing newlines, attached directly to the connector.
[tool_use Bash] {"command": "cd /tmp && cat > /tmp/repro_conn2.py <<'EOF'\nimport sys\nsys.path.insert(0, \"~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1\")\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n  \"SELECT a FROM t WHERE x = 1 AND /* line one\\n   line two */ y = 2\",\n  \"SELECT a FROM t WHERE x = 1 /* line one\\n line two */ AND y = 2
…[400 chars elided]…
nge(3):\n        out2 = sqlglot.parse_one(out, read=\"duckdb\").sql(\"duckdb\", pretty=True)\n        if out2 != out:\n            print(\"  NOT IDEMPOTENT at pass\", i+1, repr(out2))\n        out = out2\n    print(\"---\")\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_conn2.py 2>&1 | tail -40", "description": "Try multi-line comments on connectors"}
[tool_result] connector comments: [' line one\n   line two ']
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n     line two */ y = 2'
  NOT IDEMPOTENT at pass 1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n       line two */ y = 2'
  NOT IDEMPOTENT at pass 2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n         line two */ y = 2'
  NOT IDEMPOTENT at pass 3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n           line two */ y = 2'
---
connector comments: None
'SELECT\n  a\nFROM
…[321 chars elided]…
z = 3'
  NOT IDEMPOTENT at pass 2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* line one\n       line two */ y = 2 OR z = 3'
  NOT IDEMPOTENT at pass 3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* line one\n         line two */ y = 2 OR z = 3'
---
connector comments: None
connector comments: None
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND y = 2 /* c1\n c2 */ AND z = 3'
---
Shell cwd was reset to ~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1
[assistant] Reproduced: the multi-line `AND`/`OR` comment gains indentation on every pass. Next I'll check `sanitize_comment`, which is where the continuation lines get their padding.
[tool_use Bash] {"command": "grep -n \"def sanitize_comment\" -A 12 sqlglot/generator.py && grep -n \"def maybe_comment\" -A 40 sqlglot/generator.py | head -60", "description": "Inspect sanitize_comment and maybe_comment"}
[tool_result] 982:    def sanitize_comment(self, comment: str) -> str:
983-        comment = " " + comment if comment[0].strip() else comment
984-        comment = comment + " " if comment[-1].strip() else comment
985-
986-        # Escape block comment markers to prevent premature closure or unintended nesting.
987-        # This is necessary because single-line comments (--) are converted to block comments
988-        # (/* */) on output, and any */ in the original text would close the comment early.
989-  
…[1123 chars elided]…
sep()}{comments_sql}{sql}"
1021-                if not sql or sql[0].isspace()
1022-                else f"{comments_sql}{self.sep()}{sql}"
1023-            )
1024-
1025-        return f"{sql} {comments_sql}"
1026-
1027-    def wrap(self, expression: exp.Expr | str) -> str:
1028-        this_sql = (
1029-            self.sql(expression)
1030-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
1031-            else self.sql(expression, "this")
1032-        )
1033-        if not this_sql:
[tool_use Bash] {"command": "grep -n \"def _replace_line_breaks\" -A 12 sqlglot/generator.py", "description": "Inspect _replace_line_breaks helper"}
[tool_result] 5201:    def _replace_line_breaks(self, string: str) -> str:
5202-        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
5203-        if self.pretty:
5204-            return string.replace("\n", self.SENTINEL_LINE_BREAK)
5205-        return string
5206-
5207-    def copyparameter_sql(self, expression: exp.CopyParameter) -> str:
5208-        option = self.sql(expression, "this")
5209-
5210-        if expression.expressions:
5211-            upper = option.upper()
5212-
5213-            # Snowflake FILE_FORMAT options are separated by whitespace
[assistant] `maybe_comment` protects newlines with `_replace_line_breaks` so the indentation pass doesn't re-indent them. The connector path appends the raw comment and skips that protection. I'll confirm the sentinel is restored at the end of generation, then apply the same treatment there.
[tool_use Bash] {"command": "grep -n \"SENTINEL_LINE_BREAK\" sqlglot/generator.py", "description": "Find sentinel usages in generator"}
[tool_result] 829:    SENTINEL_LINE_BREAK = "__SQLGLOT__LB__"
936:            sql = sql.replace(self.SENTINEL_LINE_BREAK, "\n")
5204:            return string.replace("\n", self.SENTINEL_LINE_BREAK)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                        if comment:\n                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                        if comment:\n                            comment_sql = f\"/*{self.sanitize_comment(comment)}*/\"\n                            op += f\" {self._replace_line_breaks(comment_sql)}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_conn2.py 2>&1 | tail -40", "description": "Re-run reproduction after fix"}
[tool_result] connector comments: [' line one\n   line two ']
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* line one\n   line two */ y = 2'
---
connector comments: None
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* line one\n line two */ AND y = 2'
---
connector comments: None
connector comments: [' line one\n line two ']
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* line one\n line two */ y = 2 OR z = 3'
---
connector comments: None
connector comments: None
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND y = 2 /* c1\n c2 */ AND z = 3'
---
[assistant] The output is now stable across passes. Next I'll find the existing pretty-print comment tests so I can add a regression test beside them.
[tool_use Bash] {"command": "grep -rn \"line_break\\|multi.line\\|multiline\" tests/test_transpile.py tests/test_generator.py tests/test_expressions.py 2>/dev/null | head -20; grep -n \"def test_comments\" tests/test_transpile.py", "description": "Locate existing comment and pretty tests"}
[tool_result] tests/test_transpile.py:985:    def test_pretty_line_breaks(self):
118:    def test_comments(self):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "offset": 980, "limit": 40}
[tool_result] 980	            with self.subTest(sql[:100]):
981	                generated = transpile(sql, pretty=True)[0]
982	                self.assertEqual(generated, pretty)
983	                self.assertEqual(parse_one(sql), parse_one(pretty))
984	
985	    def test_pretty_line_breaks(self):
986	        self.assertEqual(transpile("SELECT '1\n2'", pretty=True)[0], "SELECT\n  '1\n2'")
987	        self.assertEqual(
988	            transpile("SELECT '1\n2'", pretty=True, unsupported_level=ErrorLevel.IGNORE)
…[1079 chars elided]…
write=dialect, identity=False, target=sql)
1010	
1011	    @mock.patch("sqlglot.parser.logger")
1012	    def test_error_level(self, logger):
1013	        invalid = "x + 1. ("
1014	        expected_messages = [
1015	            "Required keyword: 'expressions' missing for <class 'sqlglot.expressions.core.Aliases'>. Line 1, Col: 8.\n  x + 1. \033[4m(\033[0m",
1016	            "Expecting ). Line 1, Col: 8.\n  x + 1. \033[4m(\033[0m",
1017	        ]
1018	        expected_errors = [
1019	            {
[assistant] I'll add a regression test next to `test_pretty_line_breaks`. It checks the exact output and that a second pass is a no-op.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    def test_sql_security(self):", "new_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    d
…[82 chars elided]…
\"SELECT a FROM t WHERE x = 1 AND /* line one\\n   line two */ y = 2 OR z = 3\"\n        pretty = transpile(sql, pretty=True)[0]\n        self.assertEqual(\n            pretty,\n            \"SELECT\\n  a\\nFROM t\\nWHERE\\n  x = 1 AND /* line one\\n   line two */ y = 2 OR z = 3\",\n        )\n        self.assertEqual(transpile(pretty, pretty=True)[0], pretty)\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-095942-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[assistant] Now I'll run the new test, then the full suite using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py -k \"connector_comment or pretty\" 2>&1 | tail -15", "description": "Run targeted pretty-print tests"}
[tool_result] ...                                         [100%]
3 passed, 26 deselected, 29 subtests passed in 0.06s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite"}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
........................... [ 27%]
.......................................................................................................................................................................................
…[274 chars elided]…
........ [ 65%]
............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 55.16s
[assistant] All 1114 tests pass. I'll run the linter on the two changed files and review the diff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -I -m ruff check sqlglot/generator.py tests/test_transpile.py 2>&1; <work>/env-sqlglot/bin/python -I -m ruff format --check sqlglot/generator.py tests/test_transpile.py 2>&1) | tail -5; git diff --stat; git diff sqlglot/generator.py", "description": "Lint changed files and show generator diff"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generator.py    | 3 ++-
 tests/test_transpile.py | 9 +++++++++
 2 files changed, 11 insertions(+), 1 deletion(-)
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 7c9bd3c02..f57ee1d7b 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -3912,7 +3912,8 @@ class Generator:
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-                            op += f" /*{self.sanitize_comment(comment)}*/"
+                            comment_sql = f"/*{self.sanitize_comment(comment)}*/"
+                            op += f" {self._replace_line_breaks(comment_sql)}"
                 stack.extend((op, expression.left))
             return op
[assistant] Formatting a query with a multi-line comment on an `AND`/`OR` is now idempotent. Repeated `pretty=True` passes return the same output.

**Cause:** `Generator.connector_sql` (`sqlglot/generator.py`) appends connector comments to the operator string with the raw text. Pretty-printing then re-indents every line of that string, so each continuation line of the comment gains two spaces per pass. `maybe_comment` avoids this by wrapping comments in `_replace_line_breaks`, which swaps newlines for a sentinel that is restored at the end. The connector path skipped that step.

**Fix:** one change in `sq
…[106 chars elided]…
tection `maybe_comment` uses.

**Verification:**
- Before the fix, `x = 1 AND /* line one\n   line two */ y = 2` gained indentation on each pass (pass 1 through 3 all differed). After the fix, the output is identical on every pass, for both `AND` and `OR`.
- Added `test_pretty_connector_comment_line_breaks_are_idempotent` in `tests/test_transpile.py`. It checks the exact pretty output and that re-formatting it changes nothing.
- Full suite: 1114 passed. `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything. The changes are in the worktree for you to review.
