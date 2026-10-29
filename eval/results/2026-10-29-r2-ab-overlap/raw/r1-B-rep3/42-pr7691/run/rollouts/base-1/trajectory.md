# trajectory base-1

final message:
Fixed: formatting a query with a multi-line comment on an `AND`/`OR` connector is now idempotent with `pretty=True`.

**Cause:** `connector_sql` in `sqlglot/generator.py` builds the connector comment by hand and puts the raw newline into the output. Other comments go through `maybe_comment`, which protects line breaks with `_replace_line_breaks`. Because the raw newline was not protected, the indenter added two spaces to the continuation line on every pass. Before the fix, four passes on `... AND /* line one\nline two */ ...` gave four different indents.

**Change:**
- `sqlglot/generator.py`: wrap the connector comment in `self._replace_line_breaks(...)`, the same protection `maybe_comment` uses.
- `tests/test_transpile.py`: added `test_pretty_connector_comment_is_idempotent`, which formats the query, re-formats the output, and checks both match the expected string.

**Verification:**
- Full suite: 1114 passed, 18162 subtests passed (run with the project's Python).
- `ruff check` and `ruff format --check` pass on both files.
- The output is now stable across passes: `a = 1 AND /* line one\nline two */ b = 2 AND c = 3`, with the continuation line unindented, the same as the non-pretty output.

I did not run the new test against the unfixed code. I did confirm the bug by reproducing it before the fix.

I have not committed anything. CLAUDE.md asks for the model name at the end of PR titles and commit messages, so I'll add that when you commit.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"def binary\\|def connector_sql\\|def _maybe_comment\\|def maybe_comment\\|def sep\\b\\|def sep(\" sqlglot/generator.py | head -30", "description": "Check status and locate generator helpers"}
[tool_result] okrg: regex parse error:
    (?:def binary|def connector_sql|def _maybe_comment|def maybe_comment|def sep\b|def sep()
    ^
error: unclosed group
0 matches for 'def binary\|def connector_sql\|def _maybe_comment\|def maybe_comment\|def sep\b\|def sep('
[tool_use Bash] {"command": "git status --short; grep -n \"def binary\\|def connector_sql\\|def maybe_comment\\|def sep(\" sqlglot/generator.py", "description": "Check status and locate generator helpers"}
[tool_result ERROR] Exit code 2
okrg: regex parse error:
    (?:def binary|def connector_sql|def maybe_comment|def sep()
    ^
error: unclosed group
0 matches for 'def binary\|def connector_sql\|def maybe_comment\|def sep('
[tool_use Grep] {"pattern": "def binary|def connector_sql|def maybe_comment|def sep\\(|def and_sql|def or_sql", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "-n": "true", "output_mode": "content"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "git status --short; /usr/bin/grep -n -E \"def binary|def connector_sql|def maybe_comment|def sep\\(|def and_sql|def or_sql|def seg\\(\" sqlglot/generator.py", "description": "Check status and locate generator helpers"}
[tool_result] ok976:    def sep(self, sep: str = " ") -> str:
979:    def seg(self, sql: str, sep: str = " ") -> str:
993:    def maybe_comment(
3892:    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
3895:    def or_sql(self, expression: exp.Or, stack: list[str | exp.Expr] | None = None) -> str:
3901:    def connector_sql(
4429:    def binary(self, expression: exp.Binary, op: str) -> str:
[tool_use Bash] {"command": "sed -n 970,1040p sqlglot/generator.py; echo ----; sed -n 3890,3945p sqlglot/generator.py", "description": "Read comment and connector generation code"}
[tool_result]     def unsupported(self, message: str) -> None:
        if self.unsupported_level == ErrorLevel.IMMEDIATE:
            raise UnsupportedError(message)
        self.unsupported_messages.append(message)

    def sep(self, sep: str = " ") -> str:
        return f"{sep.strip()}\n" if self.pretty else sep

    def seg(self, sql: str, sep: str = " ") -> str:
        return f"{self.sep(sep)}{sql}"

    def sanitize_comment(self, comment: str) -> str:
        comment = " " + comment if comment[0].strip
…[3566 chars elided]…
           else:
                    sqls.append(sql)

        sep = "\n" if self.pretty and self.too_wide(sqls) else " "
        return sep.join(sqls)

    def bitwiseand_sql(self, expression: exp.BitwiseAnd) -> str:
        return self.binary(expression, "&")

    def bitwiseleftshift_sql(self, expression: exp.BitwiseLeftShift) -> str:
        return self.binary(expression, "<<")

    def bitwisenot_sql(self, expression: exp.BitwiseNot) -> str:
        return f"~{self.sql(expression, 'this')}"
[assistant] Let me reproduce the problem before changing anything.
[tool_use Bash] {"command": "cat > /tmp/repro_conn.py <<'EOF'\nimport sqlglot\nsql = \"SELECT * FROM t WHERE a = 1 AND /* line one\\nline two */ b = 2 AND c = 3\"\nout = sqlglot.transpile(sql, pretty=True)[0]\nfor i in range(4):\n    print(repr(out))\n    out = sqlglot.transpile(out, pretty=True)[0]\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -I /tmp/repro_conn.py; sed -n 4429,4440p sqlglot/generator.py; /usr/bin/grep -n \"_replace_line_breaks\" sqlglot/generator.py | head", "description": "Reproduce non-idempotent pretty output with comments"}
[tool_result] Traceback (most recent call last):
  File "/tmp/repro_conn.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
    def binary(self, expression: exp.Binary, op: str) -> str:
        sqls: list[str] = []
        stack: list[None | str | exp.Expr] = [expression]
        binary_type = type(expression)

        while stack:
            node = stack.pop()

            if type(node) is binary_type:
                op_func = node.args.get("operator")
                if op_func:
                    op = f"OPERATOR({self.sql(op_func)})"
1016:        comments_sql = self._replace_line_breaks(comments_sql)
1960:                f"{self._identifier_start}{self._replace_line_breaks(text)}{self._identifier_end}"
2895:        return self._replace_line_breaks(text).replace(delimiter, escaped_delimiter)
5201:    def _replace_line_breaks(self, string: str) -> str:
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/repro_conn.py; sed -n 5201,5206p sqlglot/generator.py", "description": "Reproduce non-idempotent pretty output with comments"}
[tool_result] 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n  line two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n    line two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n      line two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n        line two */ b = 2 AND c = 3'
    def _replace_line_breaks(self, string: str) -> str:
        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
        if self.pretty:
            return string.replace("\n", self.SENTINEL_LINE_BREAK)
        return string
[assistant] Reproduced: each pass adds two more spaces to the continuation line of the comment. The cause is that `connector_sql` builds the connector comment with a raw newline, bypassing `maybe_comment`, which protects line breaks with `_replace_line_breaks`. I'll apply the same protection there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                            op += f\" {self._replace_line_breaks(f'/*{self.sanitize_comment(comment)}*/')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/repro_conn.py && PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT 1 WHERE a = 1 AND /* x\\ny */ b = 2 OR /* p\\nq */ c = 3', 'SELECT 1 WHERE a = 1 /* x\\ny */ AND b = 2']:\n    print(repr(sqlglot.transpile(s, pretty=True)[0]))\n    print(repr(sqlglot.transpile(s)[0]))\n\"", "description": "Verify fix and check non-pretty output"}
[tool_result] 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3'
'SELECT\n  1\nWHERE\n  a = 1 AND /* x\ny */ b = 2 OR /* p\nq */ c = 3'
'SELECT 1 WHERE a = 1 AND /* x\ny */ b = 2 OR /* p\nq */ c = 3'
'SELECT\n  1\nWHERE\n  a = 1 /* x\ny */ AND b = 2'
'SELECT 1 WHERE a = 1 /* x\ny */ AND b = 2'
[assistant] The output is now stable across passes. Next I'll add a regression test and run the suite.
[tool_use Bash] {"command": "/usr/bin/grep -n -E \"def test_comments|def test_pretty|line break\" tests/test_transpile.py tests/test_generator.py | head -20", "description": "Find existing comment and pretty tests"}
[tool_result] tests/test_transpile.py:118:    def test_comments(self):
tests/test_transpile.py:978:    def test_pretty(self):
tests/test_transpile.py:985:    def test_pretty_line_breaks(self):
tests/test_generator.py:70:    def test_pretty_nested_types(self):
[tool_use Bash] {"command": "sed -n 978,1010p tests/test_transpile.py", "description": "Read existing pretty line break tests"}
[tool_result]     def test_pretty(self):
        for _, sql, pretty in load_sql_fixture_pairs("pretty.sql"):
            with self.subTest(sql[:100]):
                generated = transpile(sql, pretty=True)[0]
                self.assertEqual(generated, pretty)
                self.assertEqual(parse_one(sql), parse_one(pretty))

    def test_pretty_line_breaks(self):
        self.assertEqual(transpile("SELECT '1\n2'", pretty=True)[0], "SELECT\n  '1\n2'")
        self.assertEqual(
            transpile("SELECT
…[586 chars elided]…
,
            ("trino", "CREATE VIEW v SECURITY INVOKER AS SELECT 1"),
            ("presto", "CREATE VIEW v SECURITY INVOKER AS SELECT 1"),
            ("starrocks", "CREATE VIEW v SECURITY INVOKER AS SELECT 1"),
            ("mysql", "CREATE SQL SECURITY INVOKER VIEW v AS SELECT 1"),
        ]:
            with self.subTest(dialect):
                self.validate(sql, read=dialect, identity=False, target=sqlglot_sql)
                self.validate(sql, write=dialect, identity=False, target=sql)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    def test_sql_security(self):", "new_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    d
…[52 chars elided]…
:\n        sql = \"SELECT * FROM t WHERE a = 1 AND /* line one\\nline two */ b = 2 AND c = 3\"\n        expected = \"SELECT\\n  *\\nFROM t\\nWHERE\\n  a = 1 AND /* line one\\nline two */ b = 2 AND c = 3\"\n        once = transpile(sql, pretty=True)[0]\n        self.assertEqual(once, expected)\n        self.assertEqual(transpile(once, pretty=True)[0], expected)\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py -k \"pretty\" 2>&1 | tail -5; git stash list >/dev/null; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run pretty tests then full test suite", "timeout": 900000}
[tool_result] ...                                         [100%]
3 passed, 26 deselected, 29 subtests passed in 0.05s
..................... [ 58%]
......................... [ 60%]
................................................. [ 65%]
............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 46.52s
[assistant] The full suite passes. I'll run the linter on the two changed files, then clean up the temp script.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generator.py tests/test_transpile.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/test_transpile.py) 2>&1 | tail -5; rm -f /tmp/repro_conn.py; git diff --stat", "description": "Lint changed files and show diff stats"}
[tool_result] All checks passed!
Would reformat: tests/test_transpile.py
1 file would be reformatted, 1 file already formatted
sqlglot/generator.py    | 2 +-
 tests/test_transpile.py | 7 +++++++
 2 files changed, 8 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --diff tests/test_transpile.py 2>&1 | head -30", "description": "Show formatting diff for test file"}
[tool_result] --- tests/test_transpile.py
+++ tests/test_transpile.py
@@ -996,7 +996,9 @@
 
     def test_pretty_connector_comment_is_idempotent(self):
         sql = "SELECT * FROM t WHERE a = 1 AND /* line one\nline two */ b = 2 AND c = 3"
-        expected = "SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3"
+        expected = (
+            "SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2 AND c = 3"
+        )
         once = transpile(sql, pretty=True)[0]
         self.assertEqual(once, expected)
         self.assertEqual(transpile(once, pretty=True)[0], expected)

1 file would be reformatted
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "        expected = \"SELECT\\n  *\\nFROM t\\nWHERE\\n  a = 1 AND /* line one\\nline two */ b = 2 AND c = 3\"", "new_string": "        expected = (\n            \"SELECT\\n  *\\nFROM t\\nWHERE\\n  a = 1 AND /* line one\\nline two */ b = 2 AND c = 3\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-195005-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/test_transpile.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1", "description": "Recheck formatting and rerun full suite", "timeout": 900000}
[tool_result] 2 files already formatted
1114 passed, 18162 subtests passed in 46.48s
[assistant] Fixed: formatting a query with a multi-line comment on an `AND`/`OR` connector is now idempotent with `pretty=True`.

**Cause:** `connector_sql` in `sqlglot/generator.py` builds the connector comment by hand and puts the raw newline into the output. Other comments go through `maybe_comment`, which protects line breaks with `_replace_line_breaks`. Because the raw newline was not protected, the indenter added two spaces to the continuation line on every pass. Before the fix, four passes on `... AND /* line one\nline two */ ...` gave four different indents.

**Change:**
- `sqlglot/generator.py`: 
…[265 chars elided]…
ected string.

**Verification:**
- Full suite: 1114 passed, 18162 subtests passed (run with the project's Python).
- `ruff check` and `ruff format --check` pass on both files.
- The output is now stable across passes: `a = 1 AND /* line one\nline two */ b = 2 AND c = 3`, with the continuation line unindented, the same as the non-pretty output.

I did not run the new test against the unfixed code. I did confirm the bug by reproducing it before the fix.

I have not committed anything. CLAUDE.md asks for the model name at the end of PR titles and commit messages, so I'll add that when you commit.
