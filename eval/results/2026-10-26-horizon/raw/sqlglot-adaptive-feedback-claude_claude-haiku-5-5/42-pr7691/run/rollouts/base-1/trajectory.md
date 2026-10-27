# trajectory base-1

final message:
Fixed: formatting a query with a multi-line comment on an `AND`/`OR` connector is now idempotent. Full suite after the last edit: `SUMMARY: 1114 passed, 18162 subtests passed in 53.54s`, `EXIT: 0`.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the comment attached to a connector was appended without going through `_replace_line_breaks`. Every other comment path protects newlines with a sentinel, so `indent()` never touches them. The raw newline inside the comment got the pretty-print indent added on each pass.

**Fix:** The comment text is now wrapped in `self._replace_line_breaks(...)` in that branch. The sentinel is restored to `\n` at the end of `generate`, so the output is unchanged apart from the stable indentation.

Before the fix, repeated formatting of `... AND /* first line\nsecond line */ y = 2 ...` drifted to 2, then 6 spaces of indent. After the fix it stays at:
```
WHERE
  x = 1 AND /* first line
second line */ y = 2 OR z = 3
```

**Test:** Added `test_pretty_connector_multiline_comment_is_idempotent` in `tests/test_transpile.py`. It formats three times and checks the output matches the expected string each time. It sits beside `test_pretty_line_breaks`. Lint and format checks pass.

Nothing is committed; the changes are in the working tree.

## events
[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null | head -20; ls .lithify/harness 2>/dev/null; grep -n \"def maybe_comment\" -A40 sqlglot/generator.py | head -80", "description": "Check harness memory and locate comment handling"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 
…[1224 chars elided]…
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
[tool_use Bash] {"command": "cat > /tmp/probe_c.py <<'EOF'\nimport sqlglot\nsql = \"SELECT a FROM t WHERE x = 1 AND /* first line\\nsecond line */ y = 2 OR z = 3\"\nfor i in range(3):\n    print(repr(sqlglot.transpile(sql, pretty=True)[0]))\n    sql = sqlglot.transpile(sql, pretty=True)[0]\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_c.py", "description": "Locate comment handling and reproduce the bug"}
[tool_result] 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\n  second line */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\n    second line */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\n      second line */ y = 2 OR z = 3'
[assistant] The bug reproduces: each pass adds indentation inside the multi-line comment. Next I'll look at how line breaks in comments are handled.
[tool_use Bash] {"command": "grep -n \"_replace_line_breaks\\|def sanitize_comment\" -A8 sqlglot/generator.py | head -60; grep -n \"def sep\\b\\|def seg\\b\\|def indent\\b\" -A6 sqlglot/generator.py; grep -n \"def parse_comments\\|comments\" sqlglot/parser.py | head -5; grep -n \"CONNECTOR\\|connector\" sqlglot/generator.py | head -20", "description": "Inspect comment line-break and indent helpers"}
[tool_result] 982:    def sanitize_comment(self, comment: str) -> str:
983-        comment = " " + comment if comment[0].strip() else comment
984-        comment = comment + " " if comment[-1].strip() else comment
985-
986-        # Escape block comment markers to prevent premature closure or unintended nesting.
987-        # This is necessary because single-line comments (--) are converted to block comments
988-        # (/* */) on output, and any */ in the original text would close the comment early.
989-  
…[2256 chars elided]…
   skip_first: bool = False,
1059-        skip_last: bool = False,
320:        "_prev_comments",
1864:        self._prev_comments: list[str] = []
1879:        self._prev_comments = []
1896:            self._prev_comments = prev.comments
1899:            self._prev_comments = []
3893:        return self.connector_sql(expression, "AND", stack)
3896:        return self.connector_sql(expression, "OR", stack)
3899:        return self.connector_sql(expression, "XOR", stack)
3901:    def connector_sql(
[tool_use Bash] {"command": "sed -n 3901,3940p sqlglot/generator.py; grep -n \"SENTINEL_LINE_BREAK\" sqlglot/generator.py; sed -n 1053,1080p sqlglot/generator.py", "description": "Read connector_sql and sentinel usage"}
[tool_result]     def connector_sql(
        self,
        expression: exp.Connector,
        op: str,
        stack: list[str | exp.Expr] | None = None,
    ) -> str:
        if stack is not None:
            if expression.expressions:
                stack.append(self.expressions(expression, sep=f" {op} "))
            else:
                stack.append(expression.right)
                if expression.comments and self.comments:
                    for comment in expression.comments:
                        
…[1322 chars elided]…
turn sql

        pad = self.pad if pad is None else pad
        lines = sql.split("\n")

        return "\n".join(
            (
                line
                if (skip_first and i == 0) or (skip_last and i == len(lines) - 1)
                else f"{' ' * (level * self._indent + pad)}{line}"
            )
            for i, line in enumerate(lines)
        )

    def sql(
        self,
        expression: str | exp.Expr | None,
        key: str | None = None,
        comment: bool = True,
[assistant] The AND/OR comment path in `connector_sql` builds the comment without `_replace_line_breaks`, so the raw newline gets indented by `indent()`. Checking that the sentinel is restored at the end of generation before I change it.
[tool_use Bash] {"command": "sed -n 925,940p sqlglot/generator.py", "description": "Check sentinel restore in generate"}
[tool_result]             The SQL string corresponding to `expression`.
        """
        if copy:
            expression = expression.copy()

        expression = self.preprocess(expression)

        self.unsupported_messages = []
        sql = self.sql(expression).strip()

        if self.pretty:
            sql = sql.replace(self.SENTINEL_LINE_BREAK, "\n")

        if self.unsupported_level == ErrorLevel.IGNORE:
            return sql
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103219-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                            op += f\" {self._replace_line_breaks(f'/*{self.sanitize_comment(comment)}*/')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103219-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_c.py", "description": "Apply fix and rerun the repeated-format probe"}
[tool_result] 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\nsecond line */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\nsecond line */ y = 2 OR z = 3'
'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* first line\nsecond line */ y = 2 OR z = 3'
[assistant] Output is now stable across passes. Next I'll find the existing comment-formatting tests so I can add a regression test beside them.
[tool_use Bash] {"command": "grep -n \"def test_comments\\|def test_pretty\\|multi\\|\\\\\\\\n.*/\\*\" tests/test_transpile.py | head -30", "description": "Find comment and pretty tests in transpile tests"}
[tool_result] 99:            "SELECT FOO, /*x*/\nBAR, /*y*/\nBAZ",
100:            "SELECT\n  FOO /* x */\n  , BAR /* y */\n  , BAZ",
118:    def test_comments(self):
132:            "SELECT * FROM t1\n/*x*/\nUNION ALL SELECT * FROM t2",
140:            "SELECT * FROM t1\n/*x*/\nINTERSECT ALL SELECT * FROM t2",
144:            "SELECT\n  foo\n/* comments */\n;",
167:            "SELECT * FROM\n/* comment */\ndb.schema1.tbl PIVOT (SUM(a) FOR b IN ('x', 'y'))",
170:        self.validate("SELECT --+5\nx FROM foo", "/* +5 */ SELECT x FROM foo")
171:        self.validate("SELECT --!5\nx FROM foo", "/* !5 */ SELECT x FROM foo")
250:            /* multi
262:            """/* multi
436:            "SELECT\n  a /* sqlglot.meta case_sensitive */ -- noqa\nFROM tbl",
978:    def test_pretty(self):
985:    def test_pretty_line_breaks(self):
[tool_use Bash] {"command": "sed -n 978,1000p tests/test_transpile.py", "description": "Read existing pretty line break tests"}
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
…[9 chars elided]…
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
[assistant] I'll add a regression test next to `test_pretty_line_breaks`. It checks the exact output and that re-formatting is stable.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-103219-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    def test_sql_security(self):", "new_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    d
…[15 chars elided]…
connector_multiline_comment_is_idempotent(self):\n        sql = \"SELECT a FROM t WHERE x = 1 AND /* first\\nsecond */ y = 2 OR z = 3\"\n        expected = \"SELECT\\n  a\\nFROM t\\nWHERE\\n  x = 1 AND /* first\\nsecond */ y = 2 OR z = 3\"\n        for _ in range(3):\n            sql = transpile(sql, pretty=True)[0]\n            self.assertEqual(sql, expected)\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-103219-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py tests/test_generator.py tests/test_expressions.py 2>&1 | tail -5; /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34
…[43 chars elided]…
/python -m ruff check sqlglot/generator.py tests/test_transpile.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/test_transpile.py 2>&1 | tail -2", "description": "Add idempotence regression test and run related tests and lint"}
[tool_result] ..................................................................................................... [ 96%]
....                                                                     [100%]
105 passed, 1051 subtests passed in 0.48s
All checks passed!
2 files already formatted
[assistant] Related tests and lint pass. Now the full suite, run through the harness script as the project requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
   6504       00:46 <work>/env-sqlglot/b
  34207 03-15:01:39 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-42f7570c61.log
ELAPSED: 54s
SUMMARY: 1114 passed, 18162 subtests passed in 53.54s
EXIT: 0
[assistant] Fixed: formatting a query with a multi-line comment on an `AND`/`OR` connector is now idempotent. Full suite after the last edit: `SUMMARY: 1114 passed, 18162 subtests passed in 53.54s`, `EXIT: 0`.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the comment attached to a connector was appended without going through `_replace_line_breaks`. Every other comment path protects newlines with a sentinel, so `indent()` never touches them. The raw newline inside the comment got the pretty-print indent added on each pass.

**Fix:** The comment text is now wrapped in `self._replace_line_breaks(.
…[85 chars elided]…
e output is unchanged apart from the stable indentation.

Before the fix, repeated formatting of `... AND /* first line\nsecond line */ y = 2 ...` drifted to 2, then 6 spaces of indent. After the fix it stays at:
```
WHERE
  x = 1 AND /* first line
second line */ y = 2 OR z = 3
```

**Test:** Added `test_pretty_connector_multiline_comment_is_idempotent` in `tests/test_transpile.py`. It formats three times and checks the output matches the expected string each time. It sits beside `test_pretty_line_breaks`. Lint and format checks pass.

Nothing is committed; the changes are in the working tree.
