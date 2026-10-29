# trajectory base-1

final message:
Pretty-printing is now idempotent for multi-line comments attached to `AND`/`OR`. Formatting the same query again no longer adds indentation to the comment's continuation line.

**Cause:** `connector_sql` in `sqlglot/generator.py` appended comment text to the operator string without going through `_replace_line_breaks`. `maybe_comment` does go through it. So the raw newline survived into the output, and the next parse-and-format pass re-indented it.

**Fix:** the comment text in that branch now goes through `self._replace_line_breaks`, the same as `maybe_comment`. This is a one-line change in `sqlglot/generator.py`.

**Verification:**
- Before the fix, four consecutive pretty-print passes on `... AND /* first line\nsecond line */ b = 2 ...` grew the continuation line by two spaces each pass.
- After the fix, all four passes produce the same output.
- I added a regression test to `tests/test_transpile.py` that checks a second pass is a no-op and that the comment stays on its line.
- Full suite: 1113 passed, 18162 subtests passed. `ruff check` is clean and `ruff format` was applied to the test file.

The continuation line stays unindented (`second */ b = 2`). That matches how multi-line block comments already render elsewhere, so I didn't change it. Nothing has been committed.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"def maybe_comment\\|def binary\\|def connector_sql\\|def and_sql\\|def or_sql\\|def _pretty\\|pretty and\" sqlglot/generator.py | head -50", "description": "Check status and locate comment/connector code"}
[tool_result] 993:    def maybe_comment(
3477:        if self.pretty and self.too_wide(statements):
3892:    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
3895:    def or_sql(self, expression: exp.Or, stack: list[str | exp.Expr] | None = None) -> str:
3901:    def connector_sql(
3934:        sep = "\n" if self.pretty and self.too_wide(sqls) else " "
4429:    def binary(self, expression: exp.Binary, op: str) -> str:
4491:        if self.pretty and self.too_wide(arg_sqls):
4554:        if self.pretty and (not dynamic or self.too_wide(result_sqls)):
5278:            elif not self.pretty and (files or credentials):
[tool_use Bash] {"command": "sed -n 993,1040p sqlglot/generator.py && echo ---- && sed -n 3888,3950p sqlglot/generator.py", "description": "Read maybe_comment and connector_sql"}
[tool_result]     def maybe_comment(
        self,
        sql: str,
        expression: exp.Expr | None = None,
        comments: list[str] | None = None,
        separated: bool = False,
    ) -> str:
        comments = (
            ((expression and expression.comments) if comments is None else comments)  # type: ignore
            if self.comments
            else None
        )

        if not comments or isinstance(expression, self.EXCLUDE_COMMENTS):
            return sql

        comments_sql = " ".jo
…[2896 chars elided]…
self.binary(expression, "&")

    def bitwiseleftshift_sql(self, expression: exp.BitwiseLeftShift) -> str:
        return self.binary(expression, "<<")

    def bitwisenot_sql(self, expression: exp.BitwiseNot) -> str:
        return f"~{self.sql(expression, 'this')}"

    def bitwiseor_sql(self, expression: exp.BitwiseOr) -> str:
        return self.binary(expression, "|")

    def bitwiserightshift_sql(self, expression: exp.BitwiseRightShift) -> str:
        return self.binary(expression, ">>")
[assistant] Let me reproduce the bug before changing anything.
[tool_use Bash] {"command": "cat > /tmp/repro_idem.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport sqlglot\nsql = \"SELECT * FROM t WHERE a = 1 AND /* first line\\nsecond line */ b = 2 OR c = 3\"\nout = sql\nfor i in range(4):\n    out = sqlglot.transpile(out, read=\"duckdb\", write=\"duckdb\", pretty=True)[0]\n    print(i, repr(out))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/repro_idem.py \"$PWD\"; grep -n \"_replace_line_breaks\\|def sanitize_comment\" -A6 sqlglot/generator.py | head -40", "description": "Reproduce non-idempotent pretty-print with AND comment"}
[tool_result] 0 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\n  second line */ b = 2 OR c = 3'
1 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\n    second line */ b = 2 OR c = 3'
2 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\n      second line */ b = 2 OR c = 3'
3 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\n        second line */ b = 2 OR c = 3'
982:    def sanitize_comment(self, comment: str) -> str:
983-        comment = " " + comment if comment[0].strip() else comm
…[1280 chars elided]…
")
2899-        overwrite = " OVERWRITE" if is_overwrite else ""
2900-        this = self.sql(expression, "this")
2901-
--
5201:    def _replace_line_breaks(self, string: str) -> str:
5202-        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
5203-        if self.pretty:
5204-            return string.replace("\n", self.SENTINEL_LINE_BREAK)
5205-        return string
5206-
5207-    def copyparameter_sql(self, expression: exp.CopyParameter) -> str:
[assistant] Reproduced: each pass adds two spaces to the continuation line. The connector path appends comment text to the operator without going through `_replace_line_breaks`, which `maybe_comment` uses. Let me check how the sentinel is restored before patching.
[tool_use Bash] {"command": "grep -n \"SENTINEL_LINE_BREAK\" sqlglot/*.py | head; grep -n \"SENTINEL_LINE_BREAK\" -B3 -A3 sqlglot/generator.py | sed -n 1,30p", "description": "Find where sentinel line breaks are restored"}
[tool_result] sqlglot/generator.py:829:    SENTINEL_LINE_BREAK = "__SQLGLOT__LB__"
sqlglot/generator.py:936:            sql = sql.replace(self.SENTINEL_LINE_BREAK, "\n")
sqlglot/generator.py:5204:            return string.replace("\n", self.SENTINEL_LINE_BREAK)
826-
827-    SAFE_JSON_PATH_KEY_RE: t.ClassVar = exp.SAFE_IDENTIFIER_RE
828-
829:    SENTINEL_LINE_BREAK = "__SQLGLOT__LB__"
830-
831-    __slots__ = (
832-        "pretty",
--
933-        sql = self.sql(expression).strip()
934-
935-        if self.pre
…[43 chars elided]…
.SENTINEL_LINE_BREAK, "\n")
937-
938-        if self.unsupported_level == ErrorLevel.IGNORE:
939-            return sql
--
5201-    def _replace_line_breaks(self, string: str) -> str:
5202-        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
5203-        if self.pretty:
5204:            return string.replace("\n", self.SENTINEL_LINE_BREAK)
5205-        return string
5206-
5207-    def copyparameter_sql(self, expression: exp.CopyParameter) -> str:
[assistant] The sentinel is restored only at the end of `generate`, so the fix is to route the connector's comment text through `_replace_line_breaks`, the same way `maybe_comment` does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122751-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                        if comment:\n                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                        if comment:\n                            comment_sql = f\"/*{self.sanitize_comment(comment)}*/\"\n                            op += f\" {self._replace_line_breaks(comment_sql)}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122751-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/repro_idem.py \"$PWD\"", "description": "Re-run idempotency repro after fix"}
[tool_result] 0 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\nsecond line */ b = 2 OR c = 3'
1 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\nsecond line */ b = 2 OR c = 3'
2 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\nsecond line */ b = 2 OR c = 3'
3 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* first line\nsecond line */ b = 2 OR c = 3'
[assistant] Output is now stable across passes. Next I'll add a regression test next to the existing pretty-print comment tests.
[tool_use Bash] {"command": "grep -n \"multi\\|line\" tests/test_transpile.py | grep -i \"comment\\|pretty\" | head -20; grep -n \"def test_comments\" tests/test_transpile.py tests/test_generator.py", "description": "Find existing comment pretty-print tests"}
[tool_result] 173:            "SELECT 1 /* inline */ FROM foo -- comment",
174:            "SELECT 1 /* inline */ FROM foo /* comment */",
229:line3*/ /*another comment*/ where 1=1 -- comment at the end""",
232:line3 */ /* another comment */ WHERE 1 = 1 /* comment at the end */""",
238:line3*/ /*another comment*/ where 1=1 -- comment at the end""",
243:line3 */ /* another comment */
642:    def test_comment_single_line_with_block_close(self):
643:        # Single-line comments containing */ must be escaped when converted to block comments,
985:    def test_pretty_line_breaks(self):
tests/test_transpile.py:118:    def test_comments(self):
[tool_use Bash] {"command": "sed -n 222,260p tests/test_transpile.py", "description": "Read multi-line comment pretty test block"}
[tool_result] FROM foo""",
            pretty=True,
        )
        self.validate(
            """
SELECT * FROM tbl /*line1
line2
line3*/ /*another comment*/ where 1=1 -- comment at the end""",
            """SELECT * FROM tbl /* line1
line2
line3 */ /* another comment */ WHERE 1 = 1 /* comment at the end */""",
        )
        self.validate(
            """
SELECT * FROM tbl /*line1
line2
line3*/ /*another comment*/ where 1=1 -- comment at the end""",
            """SELECT
  *
FROM tbl /* line1
line2
line3 */ /* another comment */
WHERE
  1 = 1 /* comment at the end */""",
            pretty=True,
        )
        self.validate(
            """
            /* multi
               line
               comment
            */
            SELECT
              tbl.cola /* comment 1 */ + tbl.colb /* comment 2 */,
              CAST(x AS CHAR), # comment 3
              y               -- comment 4
            FROM
              bar /* comment 5 */,
              tbl #          comment 6
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122751-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "WHERE\n  1 = 1 /* comment at the end */\"\"\",\n            pretty=True,\n        )\n        self.validate(\n            \"\"\"\n            /* multi", "new_string": "WHERE\n  1 = 1 /* comment at the end */\"\"\",
…[31 chars elided]…
     )\n        pretty_connector_comment = \"SELECT * FROM t WHERE a = 1 AND /* first\\nsecond */ b = 2 OR c = 3\"\n        formatted = transpile(pretty_connector_comment, pretty=True)[0]\n        self.assertEqual(formatted, transpile(formatted, pretty=True)[0])\n        self.assertIn(\"AND /* first\\nsecond */ b = 2\", formatted)\n        self.validate(\n            \"\"\"\n            /* multi"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122751-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" tests/test_transpile.py; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py tests/test_generator.py tests/test_parser.py 2>&1 | tail -15", "description": "Run transpile, generator, parser tests"}
[tool_result] 1:import os
2:import unittest
3:from unittest import mock
5:from sqlglot import parse_one, transpile
6:from sqlglot.errors import ErrorLevel, ParseError, UnsupportedError
7:from sqlglot.helper import logger as helper_logger
8:from sqlglot.parser import logger as parser_logger
9:from tests.helpers import (
505:from base
....................................................................................................                              [100%]
100 passed, 1095 subtests passed in 12.02s
[assistant] Targeted tests pass. Now the full suite and the style check.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff --version && $PY -m ruff format --check sqlglot/generator.py tests/test_transpile.py && $PY -m ruff check sqlglot/generator.py tests/test_transpile.py) 2>&1 | tail -8", "description": "Run full test suite and ruff checks"}
[tool_result] ............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1113 passed, 18162 subtests passed in 60.99s (0:01:00)
ruff 0.15.6
Would reformat: tests/test_transpile.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_transpile.py && $PY -m ruff check sqlglot/generator.py tests/test_transpile.py && git diff --stat && git diff", "description": "Apply ruff format and review final diff"}
[tool_result] 1 file reformatted
All checks passed!
 sqlglot/generator.py    | 3 ++-
 tests/test_transpile.py | 6 ++++++
 2 files changed, 8 insertions(+), 1 deletion(-)
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 7c9bd3c02..f57ee1d7b 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -3912,7 +3912,8 @@ class Generator:
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-      
…[583 chars elided]…
y_connector_comment = (
+            "SELECT * FROM t WHERE a = 1 AND /* first\nsecond */ b = 2 OR c = 3"
+        )
+        formatted = transpile(pretty_connector_comment, pretty=True)[0]
+        self.assertEqual(formatted, transpile(formatted, pretty=True)[0])
+        self.assertIn("AND /* first\nsecond */ b = 2", formatted)
         self.validate(
             """
             /* multi
[This command modified 1 file you've previously read: tests/test_transpile.py. Call Read before editing.]
[assistant] The diff note is from my own `ruff format` run. I'll re-run the transpile tests against the final file.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | tail -2", "description": "Re-run transpile tests on final file"}
[tool_result] ............................                               [100%]
28 passed, 1022 subtests passed in 0.24s
[assistant] Pretty-printing is now idempotent for multi-line comments attached to `AND`/`OR`. Formatting the same query again no longer adds indentation to the comment's continuation line.

**Cause:** `connector_sql` in `sqlglot/generator.py` appended comment text to the operator string without going through `_replace_line_breaks`. `maybe_comment` does go through it. So the raw newline survived into the output, and the next parse-and-format pass re-indented it.

**Fix:** the comment text in that branch now goes through `self._replace_line_breaks`, the same as `maybe_comment`. This is a one-line change in 
…[95 chars elided]…
es on `... AND /* first line\nsecond line */ b = 2 ...` grew the continuation line by two spaces each pass.
- After the fix, all four passes produce the same output.
- I added a regression test to `tests/test_transpile.py` that checks a second pass is a no-op and that the comment stays on its line.
- Full suite: 1113 passed, 18162 subtests passed. `ruff check` is clean and `ruff format` was applied to the test file.

The continuation line stays unindented (`second */ b = 2`). That matches how multi-line block comments already render elsewhere, so I didn't change it. Nothing has been committed.
