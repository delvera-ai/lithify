# trajectory base-1

final message:
Formatting is now idempotent for multi-line comments on `AND`/`OR` connectors. The full suite passes (1114 tests) and ruff lint and format are clean.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the connector's comment is folded into the operator string with its raw newlines. The enclosing `WHERE` indents every line of the output, so the continuation line gained two spaces on each pass. Ordinary comments avoid this through `_replace_line_breaks`, which swaps newlines for a sentinel that is restored at the end. The connector path skipped that step.

**Fix:** One line in `connector_sql` now wraps the sanitized comment in `self._replace_line_breaks(...)`, the same helper `maybe_comment` uses. The `ruff format` pass wrapped that line onto a continuation line.

**Test:** I added `test_pretty_connector_comment_is_idempotent` to `tests/test_transpile.py`. It checks the exact pretty output for a multi-line comment on an `AND`, then reparses and reformats to confirm the output is unchanged. The test file now imports `exp` from `sqlglot`.

Before the fix, three successive pretty-print passes produced three different outputs. After it, all three match:

```
SELECT
  *
FROM t
WHERE
  a = 1 AND /* line one
line two */ b = 2
```

The continuation line stays unindented. That is intentional, since the sentinel preserves comment text exactly, matching how other multi-line comments already behave.

I haven't committed. The changes are in the worktree: `sqlglot/generator.py` and `tests/test_transpile.py`.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"def maybe_comment\\|def binary\\|def connector_sql\\|def and_sql\\|def or_sql\\|def sep\\|def seg\" sqlglot/generator.py", "description": "Check status and locate comment/connector code in generator"}
[tool_result] 976:    def sep(self, sep: str = " ") -> str:
979:    def seg(self, sql: str, sep: str = " ") -> str:
993:    def maybe_comment(
3892:    def and_sql(self, expression: exp.And, stack: list[str | exp.Expr] | None = None) -> str:
3895:    def or_sql(self, expression: exp.Or, stack: list[str | exp.Expr] | None = None) -> str:
3901:    def connector_sql(
4429:    def binary(self, expression: exp.Binary, op: str) -> str:
[tool_use Bash] {"command": "sed -n 970,1040p sqlglot/generator.py && echo ---- && sed -n 3890,3945p sqlglot/generator.py", "description": "Read comment and connector generation code"}
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
[tool_use Bash] {"command": "cat > /tmp/repro_conn.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nsql = \"SELECT * FROM t WHERE a = 1 AND b = 2\"\ntree = sqlglot.parse_one(sql)\nand_ = tree.find(exp.And)\nand_.comments = [\"line one\\nline two\"]\nout1 = tree.sql(pretty=True)\nprint(repr(out1))\nout2 = sqlglot.parse_one(out1).sql(pretty=True)\nprint(repr(out2))\nout3 = sqlglot.parse_one(out2).sql(pretty=True)\nprint(repr(out3))\nprint(\"idempotent:\", out1 == out2 == out3)\nEOF\ntimeout 60 <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_conn.py').read())\"", "description": "Reproduce non-idempotent pretty output with AND comment"}
[tool_result ERROR] Exit code 127
(eval):16: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_conn.py').read())\"", "description": "Reproduce non-idempotent pretty output with AND comment"}
[tool_result] 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n  line two */ b = 2'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n    line two */ b = 2'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\n      line two */ b = 2'
idempotent: False
[assistant] Reproduced: each format pass adds two spaces to the continuation line of the comment. Let me check how `maybe_comment` avoids this, since it already calls `_replace_line_breaks`.
[tool_use Bash] {"command": "grep -n \"_replace_line_breaks\" -A6 sqlglot/generator.py | head -40; grep -rn \"_replace_line_breaks\\|line_breaks\" tests/*.py | head", "description": "Inspect _replace_line_breaks helper and its usages"}
[tool_result] 1016:        comments_sql = self._replace_line_breaks(comments_sql)
1017-
1018-        if separated or isinstance(expression, self.WITH_SEPARATED_COMMENTS):
1019-            return (
1020-                f"{self.sep()}{comments_sql}{sql}"
1021-                if not sql or sql[0].isspace()
1022-                else f"{comments_sql}{self.sep()}{sql}"
--
1960:                f"{self._identifier_start}{self._replace_line_breaks(text)}{self._identifier_end}"
1961-            )
1962-        return te
…[474 chars elided]…
00-        this = self.sql(expression, "this")
2901-
--
5201:    def _replace_line_breaks(self, string: str) -> str:
5202-        """We don't want to extra indent line breaks so we temporarily replace them with sentinels."""
5203-        if self.pretty:
5204-            return string.replace("\n", self.SENTINEL_LINE_BREAK)
5205-        return string
5206-
5207-    def copyparameter_sql(self, expression: exp.CopyParameter) -> str:
tests/test_transpile.py:985:    def test_pretty_line_breaks(self):
[assistant] The existing `_replace_line_breaks` sentinel mechanism is what keeps comment continuation lines from being re-indented. The connector path builds its comment inline without it, so I'll apply the same helper there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                            op += f\" /*{self._replace_line_breaks(self.sanitize_comment(comment))}*/\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_conn.py').read())\"", "description": "Rerun repro after fix to check idempotency"}
[tool_result] 'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2'
'SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2'
idempotent: True
[assistant] The output is now stable across passes. Next I'll add a regression test next to the existing pretty line-break test, then run the suite.
[tool_use Bash] {"command": "sed -n 980,1000p tests/test_transpile.py", "description": "Read existing pretty line-break test"}
[tool_result]             with self.subTest(sql[:100]):
                generated = transpile(sql, pretty=True)[0]
                self.assertEqual(generated, pretty)
                self.assertEqual(parse_one(sql), parse_one(pretty))

    def test_pretty_line_breaks(self):
        self.assertEqual(transpile("SELECT '1\n2'", pretty=True)[0], "SELECT\n  '1\n2'")
        self.assertEqual(
            transpile("SELECT '1\n2'", pretty=True, unsupported_level=ErrorLevel.IGNORE)[0],
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    def test_sql_security(self):", "new_string": "            'SELECT\\n  \"Product\\n(Foo, Bar)\" AS x\\nFROM t',\n        )\n\n    d
…[50 chars elided]…
f):\n        tree = parse_one(\"SELECT * FROM t WHERE a = 1 AND b = 2\")\n        tree.find(exp.And).comments = [\"line one\\nline two\"]\n        pretty = tree.sql(pretty=True)\n        self.assertEqual(pretty, \"SELECT\\n  *\\nFROM t\\nWHERE\\n  a = 1 AND /* line one\\nline two */ b = 2\")\n        self.assertEqual(parse_one(pretty).sql(pretty=True), pretty)\n\n    def test_sql_security(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" tests/test_transpile.py | head; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | tail -30", "description": "Check imports and run transpile tests"}
[tool_result] 1:import os
2:import unittest
3:from unittest import mock
5:from sqlglot import parse_one, transpile
6:from sqlglot.errors import ErrorLevel, ParseError, UnsupportedError
7:from sqlglot.helper import logger as helper_logger
8:from sqlglot.parser import logger as parser_logger
9:from tests.helpers import (
501:from base
.................F...........                              [100%]
=================================== FAILURES ===================================
__________ TestTranspile.test_pr
…[165 chars elided]…
etty_connector_comment_is_idempotent(self):
        tree = parse_one("SELECT * FROM t WHERE a = 1 AND b = 2")
>       tree.find(exp.And).comments = ["line one\nline two"]
                  ^^^
E       NameError: name 'exp' is not defined

tests/test_transpile.py:999: NameError
=========================== short test summary info ============================
FAILED tests/test_transpile.py::TestTranspile::test_pretty_connector_comment_is_idempotent
1 failed, 28 passed, 1022 subtests passed in 0.29s
[assistant] The test file doesn't import `exp`. I'll add it to the existing sqlglot import, then rerun the file and the full suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "from sqlglot import parse_one, transpile", "new_string": "from sqlglot import exp, parse_one, transpile"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155926-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Fix import and run transpile then full test suite"}
[tool_result] .............................                              [100%]
29 passed, 1022 subtests passed in 0.21s
.................................................................................................................................................................................................................................................................................. [ 24%]
........................... [ 27%]
............................................................................
…[391 chars elided]…
 65%]
............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 66.35s (0:01:06)
[assistant] All 1114 tests pass. Last, a style check on the two changed files, since the project's pre-commit uses ruff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/test_transpile.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/test_transpile.py) 2>&1 | tail -8; git diff --stat", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
Would reformat: sqlglot/generator.py
Would reformat: tests/test_transpile.py
2 files would be reformatted
 sqlglot/generator.py    | 2 +-
 tests/test_transpile.py | 9 ++++++++-
 2 files changed, 9 insertions(+), 2 deletions(-)
[assistant] Ruff wants to reformat both files. I'll check whether that's from my lines or was already there at HEAD.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/python; $R -m ruff format --diff sqlglot/generator.py tests/test_transpile.py 2>&1 | head -40; git show HEAD:sqlglot/generator.py > /tmp/orig_gen.py; $R -m ruff format --check /tmp/orig_gen.py", "description": "Show ruff format diff and check HEAD baseline"}
[tool_result] --- sqlglot/generator.py
+++ sqlglot/generator.py
@@ -3912,7 +3912,9 @@
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-                            op += f" /*{self._replace_line_breaks(self.sanitize_comment(comment))}*/"
+                            op += (
+                                f" /*{self._replace_line_breaks(self.sanitize_comment(comment))}*/"
+                            )
   
…[221 chars elided]…
       tree.find(exp.And).comments = ["line one\nline two"]
         pretty = tree.sql(pretty=True)
-        self.assertEqual(pretty, "SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2")
+        self.assertEqual(
+            pretty, "SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2"
+        )
         self.assertEqual(parse_one(pretty).sql(pretty=True), pretty)
 
     def test_sql_security(self):

2 files would be reformatted
1 file already formatted
[assistant] Both diffs come from my two lines, and the HEAD file was clean, so I'll apply the formatter and re-verify.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin/python; $R -m ruff format sqlglot/generator.py tests/test_transpile.py && $R -m ruff check sqlglot/generator.py tests/test_transpile.py && $R -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff", "description": "Apply ruff format, lint, and rerun full suite with diff"}
[tool_result] 2 files reformatted
All checks passed!
1114 passed, 18162 subtests passed in 69.04s (0:01:09)
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 7c9bd3c02..7c6c381ff 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -3912,7 +3912,9 @@ class Generator:
                 if expression.comments and self.comments:
                     for comment in expression.comments:
                         if comment:
-                            op += f" /*{self.sanitize_comment(commen
…[1016 chars elided]…
"line one\nline two"]
+        pretty = tree.sql(pretty=True)
+        self.assertEqual(
+            pretty, "SELECT\n  *\nFROM t\nWHERE\n  a = 1 AND /* line one\nline two */ b = 2"
+        )
+        self.assertEqual(parse_one(pretty).sql(pretty=True), pretty)
+
     def test_sql_security(self):
         sqlglot_sql = "CREATE VIEW v SQL SECURITY INVOKER AS SELECT 1"
[This command modified 2 files you've previously read: sqlglot/generator.py, tests/test_transpile.py. Call Read before editing.]
[assistant] Formatting is now idempotent for multi-line comments on `AND`/`OR` connectors. The full suite passes (1114 tests) and ruff lint and format are clean.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), the connector's comment is folded into the operator string with its raw newlines. The enclosing `WHERE` indents every line of the output, so the continuation line gained two spaces on each pass. Ordinary comments avoid this through `_replace_line_breaks`, which swaps newlines for a sentinel that is restored at the end. The connector path skipped that step.

**Fix:** One line in `connector_s
…[323 chars elided]…
 comment on an `AND`, then reparses and reformats to confirm the output is unchanged. The test file now imports `exp` from `sqlglot`.

Before the fix, three successive pretty-print passes produced three different outputs. After it, all three match:

```
SELECT
  *
FROM t
WHERE
  a = 1 AND /* line one
line two */ b = 2
```

The continuation line stays unindented. That is intentional, since the sentinel preserves comment text exactly, matching how other multi-line comments already behave.

I haven't committed. The changes are in the worktree: `sqlglot/generator.py` and `tests/test_transpile.py`.
