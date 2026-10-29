# trajectory base-1

final message:
Formatting with `pretty=True` is now idempotent for comments attached to `AND`/`OR` connectors. Re-formatting the output no longer adds whitespace.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), a connector's comment was appended to the operator string with raw newlines. Multi-line comments elsewhere go through `_replace_line_breaks`, which protects the newlines until the final output is built. Here the raw newlines were re-indented on every pass.

**Fix:** One line in `sqlglot/generator.py`. The connector comment now goes through `_replace_line_breaks`, the same way `maybe_comment` and `binary` handle comments.

**Test:** I added a regression case to `test_comments` in `tests/test_transpile.py`. It covers `AND` and `OR` with a multi-line comment, and checks that formatting the expected output again gives the same result. I confirmed the test fails without the fix and passes with it.

**Results:** The full suite passes (1113 tests). I did not run `make style` (ruff/mypy), and I did not commit.

## events
[tool_use Bash] {"command": "git status --short && cat > /tmp/probe_idem.py <<'EOF'\nimport sqlglot\nsqls = [\n  \"SELECT a FROM t WHERE x = 1 /* multi\\nline */ AND y = 2\",\n  \"SELECT a FROM t WHERE x = 1 AND /* multi\\nline */ y = 2\",\n  \"SELECT a FROM t WHERE x = 1 OR /* multi\\nline */ y = 2\",\n]\nfor s in sqls:\n    out = s\n    for i in range(4):\n        out = sqlglot.transpile(out, read=\"duckdb\", write=\"duckdb\", pretty=True)[0]\n        print(i, repr(out))\n    print()\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_idem.py').read())\"", "description": "Reproduce non-idempotent pretty-print with AND/OR comments"}
[tool_result] 0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'

0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\n  line */ y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\n    line */ y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\n      line */ y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\n        line */ y = 2'

0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\n  line */ y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\n    line */ y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\n      line */ y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\n        line */ y = 2'
[assistant] Reproduced: the `AND /* ... */` and `OR /* ... */` cases gain two spaces of indentation on every pass, while the comment-before-`AND` case is stable. Next I'll look at how the generator emits connector comments.
[tool_use Bash] {"command": "grep -n \"def connector_sql\\|def maybe_comment\\|def binary\\|def _comment\\|def sep\\b\\|def seg\" -A30 sqlglot/generator.py | head -250", "description": "Locate connector and comment generation code"}
[tool_result] 976:    def sep(self, sep: str = " ") -> str:
977-        return f"{sep.strip()}\n" if self.pretty else sep
978-
979:    def seg(self, sql: str, sep: str = " ") -> str:
980-        return f"{self.sep(sep)}{sql}"
981-
982-    def sanitize_comment(self, comment: str) -> str:
983-        comment = " " + comment if comment[0].strip() else comment
984-        comment = comment + " " if comment[-1].strip() else comment
985-
986-        # Escape block comment markers to prevent premature closure or uni
…[3425 chars elided]…
       sqls.append(self.sql(node))
4447-
4448-        return "".join(sqls)
4449-
4450-    def ceil_floor(self, expression: exp.Ceil | exp.Floor) -> str:
4451-        to_clause = self.sql(expression, "to")
4452-        if to_clause:
4453-            return f"{expression.sql_name()}({self.sql(expression, 'this')} TO {to_clause})"
4454-
4455-        return self.function_fallback_sql(expression)
4456-
4457-    def function_fallback_sql(self, expression: exp.Func) -> str:
4458-        args = []
4459-
[tool_use Bash] {"command": "sed -n 3928,3960p sqlglot/generator.py; grep -n \"def _replace_line_breaks\" -A12 sqlglot/generator.py; grep -n \"def and_sql\\|def or_sql\" -A8 sqlglot/generator.py; grep -n \"_replace_line_breaks\" sqlglot/generator.py", "description": "Inspect connector loop and line-break helper"}
[tool_result]                 sql = self.sql(node)
                if sqls and sqls[-1] in ops:
                    sqls[-1] += f" {sql}"
                else:
                    sqls.append(sql)

        sep = "\n" if self.pretty and self.too_wide(sqls) else " "
        return sep.join(sqls)

    def bitwiseand_sql(self, expression: exp.BitwiseAnd) -> str:
        return self.binary(expression, "&")

    def bitwiseleftshift_sql(self, expression: exp.BitwiseLeftShift) -> str:
        return self.binary(expr
…[1846 chars elided]…
 str:
3899-        return self.connector_sql(expression, "XOR", stack)
3900-
3901-    def connector_sql(
3902-        self,
3903-        expression: exp.Connector,
4 matches in 2 files:

5201:0:str) -> str:
sqlglot/generator.py:1016:comments_sql = self._replace_line_breaks(comments_sql)
sqlglot/generator.py:1960:...{self._identifier_start}{self._replace_line_breaks(text)}{self._identifier_end}"
sqlglot/generator.py:2895:return self._replace_line_breaks(text).replace(delimiter, escaped_delimiter)
[assistant] The bug is in `connector_sql`: the connector comment is appended to `op` with raw newlines, while `maybe_comment` routes them through `_replace_line_breaks`. I'll check how the sentinel is restored so the fix matches.
[tool_use Bash] {"command": "grep -n \"SENTINEL_LINE_BREAK\" -B3 -A3 sqlglot/generator.py | head -60; grep -n \"def indent\" -A40 sqlglot/generator.py | grep -n \"SENTINEL\\|split\\|\\\\\\\\n\" ", "description": "Check how line-break sentinel is restored"}
[tool_result] 826-
827-    SAFE_JSON_PATH_KEY_RE: t.ClassVar = exp.SAFE_IDENTIFIER_RE
828-
829:    SENTINEL_LINE_BREAK = "__SQLGLOT__LB__"
830-
831-    __slots__ = (
832-        "pretty",
--
933-        sql = self.sql(expression).strip()
934-
935-        if self.pretty:
936:            sql = sql.replace(self.SENTINEL_LINE_BREAK, "\n")
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
13:1065-        lines = sql.split("\n")
15:1067-        return "\n".join(
[assistant] The sentinel is restored only at the top level, so the raw newline in the connector comment gets re-indented on every pass. I'll route the comment through `_replace_line_breaks`, the same way `maybe_comment` does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                        if comment:\n                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                        if comment:\n                            op += f\" {self._replace_line_breaks(f'/*{self.sanitize_comment(comment)}*/')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-run the probe and look for an existing pretty-print comment test to extend.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_idem.py').read())\" && grep -rn \"multi\\|pretty=True\" tests/test_transpile.py | grep -i \"comment\" | head -20", "description": "Re-run probe and find existing comment tests"}
[tool_result] 0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 /* multi\nline */ AND y = 2'

0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\nline */ y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\nline */ y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\nline */ y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 AND /* multi\nline */ y = 2'

0 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\nline */ y = 2'
1 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\nline */ y = 2'
2 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\nline */ y = 2'
3 'SELECT\n  a\nFROM t\nWHERE\n  x = 1 OR /* multi\nline */ y = 2'
[assistant] Output is now stable across passes. Next I'll add a regression test next to the existing comment tests.
[tool_use Bash] {"command": "grep -n \"def test_comments\" -A3 tests/test_transpile.py | head; grep -n \"pretty=True\" tests/test_transpile.py | head -5", "description": "Find comment tests in transpile test file"}
[tool_result] 118:    def test_comments(self):
119-        self.validate(
120-            "select /* asfd /* asdf */ asdf */ 1",
121-            "/* asfd / * asdf * / asdf */ SELECT 1",
26 matches in 1 files:

tests/test_transpile.py:88:pretty=True,
tests/test_transpile.py:96:pretty=True,
tests/test_transpile.py:102:pretty=True,
[tool_use bash] {"command": "cd ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1 && sed -n 118,160p tests/test_transpile.py", "description": "Read the comments test block"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: bash. Tool names are case-sensitive: call Bash instead.</tool_use_error>
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "offset": 118, "limit": 45}
[tool_result] 118	    def test_comments(self):
119	        self.validate(
120	            "select /* asfd /* asdf */ asdf */ 1",
121	            "/* asfd / * asdf * / asdf */ SELECT 1",
122	        )
123	        self.validate(
124	            "SELECT c /* foo */ AS alias",
125	            "SELECT c AS alias /* foo */",
126	        )
127	        self.validate(
128	            "SELECT c AS /* foo */ (a, b, c) FROM t",
129	            "SELECT c AS (a, b, c) /* foo */ FROM t",
130	        )
131	        self.valid
…[961 chars elided]…
       "SELECT * FROM a /* comment 1 */ /* comment 2 */ LEFT OUTER JOIN b",
154	        )
155	        self.validate(
156	            "SELECT CASE /* test */ WHEN a THEN b ELSE c END",
157	            "SELECT CASE WHEN a THEN b ELSE c END /* test */",
158	        )
159	        self.validate("SELECT 1 /*/2 */", "SELECT 1 /* /2 */")
160	        self.validate("SELECT */*comment*/", "SELECT * /* comment */")
161	        self.validate(
162	            "SELECT * FROM table /*comment 1*/ /*comment 2*/",
[tool_use Bash] {"command": "grep -n \"def test_comments\" -A200 tests/test_transpile.py | grep -n \"pretty\" | head -3; grep -n \"    def test_\" tests/test_transpile.py | awk -F: '$1>118' | head -1", "description": "Find the end of test_comments method"}
[tool_result] 106:223-            pretty=True,
129:246-            pretty=True,
155:272-            pretty=True,
28 matches in 28 files:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "offset": 215, "limit": 50}
[tool_result] 215	-- comment 1
216	-- comment 2
217	-- comment 3
218	SELECT * FROM foo""",
219	            """/* comment 1 */ /* comment 2 */ /* comment 3 */
220	SELECT
221	  *
222	FROM foo""",
223	            pretty=True,
224	        )
225	        self.validate(
226	            """
227	SELECT * FROM tbl /*line1
228	line2
229	line3*/ /*another comment*/ where 1=1 -- comment at the end""",
230	            """SELECT * FROM tbl /* line1
231	line2
232	line3 */ /* another comment */ WHERE 1 = 1 /* comment at the e
…[406 chars elided]…
           """
250	            /* multi
251	               line
252	               comment
253	            */
254	            SELECT
255	              tbl.cola /* comment 1 */ + tbl.colb /* comment 2 */,
256	              CAST(x AS CHAR), # comment 3
257	              y               -- comment 4
258	            FROM
259	              bar /* comment 5 */,
260	              tbl #          comment 6
261	            """,
262	            """/* multi
263	               line
264	               comment
[assistant] I'll add a regression case after the existing pretty-print comment test. It checks the formatted output from the source and also that formatting that output again is a no-op.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "  1 = 1 /* comment at the end */\"\"\",\n            pretty=True,\n        )\n        self.validate(\n            \"\"\"\n            /* multi", "new_string": "  1 = 1 /* comment at the end */\"\"\",\n            
…[263 chars elided]…
*\\nFROM t\\nWHERE\\n  x = 1 \"\n                + (\"AND\" if \" AND \" in sql else \"OR\")\n                + \" /* multi\\nline */ \"\n                + (\"y = 2\" if \" AND \" in sql else \"y = 2\")\n            )\n            self.validate(sql, expected, pretty=True)\n            self.validate(expected, expected, pretty=True)\n        self.validate(\n            \"\"\"\n            /* multi"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[assistant] That loop is clumsier than it needs to be, with redundant conditionals. I'll rewrite it as explicit cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py", "old_string": "        for sql in (\n            \"SELECT * FROM t WHERE x = 1 AND /* multi\\nline */ y = 2\",\n            \"SELECT * FROM t WHERE x = 1 OR /* multi\\nline */ y = 2\",\n        ):\n            expected = (\n    
…[375 chars elided]…
        for connector in (\"AND\", \"OR\"):\n            sql = f\"SELECT * FROM t WHERE x = 1 {connector} /* multi\\nline */ y = 2\"\n            expected = f\"SELECT\\n  *\\nFROM t\\nWHERE\\n  x = 1 {connector} /* multi\\nline */ y = 2\"\n            self.validate(sql, expected, pretty=True)\n            # Formatting must be idempotent\n            self.validate(expected, expected, pretty=True)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/tests/test_transpile.py has been updated successfully.
[assistant] Now I'll run the transpile tests, then the full suite with the project's command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run transpile tests then full test suite"}
[tool_result] ............................                               [100%]
28 passed, 1022 subtests passed in 0.28s
............................................................................................................................................................................................................................ [ 84%]
............................................................................................................ [ 94%]
....................... [ 96%]
....................................                      [100%]
1113 passed, 18162 subtests passed in 59.77s
[assistant] The full suite passes (1113 tests). To confirm the new test actually catches the bug, I'll temporarily revert the one-line fix and re-run it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" {self._replace_line_breaks(f'/*{self.sanitize_comment(comment)}*/')}\"", "new_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_transpile.py 2>&1 | grep -E \"passed|failed\" | tail -2", "description": "Confirm new test fails without the fix"}
[tool_result] 1 failed, 27 passed, 1022 subtests passed in 0.34s
[assistant] The test fails without the fix, so it catches the bug. Restoring the fix now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py", "old_string": "                            op += f\" /*{self.sanitize_comment(comment)}*/\"", "new_string": "                            op += f\" {self._replace_line_breaks(f'/*{self.sanitize_comment(comment)}*/')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-161656-pretty-printing-a-multi-line-com/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; git diff --stat", "description": "Re-run full suite with fix restored and show diff stat"}
[tool_result] 1113 passed, 18162 subtests passed in 54.53s
sqlglot/generator.py    | 2 +-
 tests/test_transpile.py | 6 ++++++
 2 files changed, 7 insertions(+), 1 deletion(-)
[assistant] Formatting with `pretty=True` is now idempotent for comments attached to `AND`/`OR` connectors. Re-formatting the output no longer adds whitespace.

**Cause:** In `connector_sql` (`sqlglot/generator.py`), a connector's comment was appended to the operator string with raw newlines. Multi-line comments elsewhere go through `_replace_line_breaks`, which protects the newlines until the final output is built. Here the raw newlines were re-indented on every pass.

**Fix:** One line in `sqlglot/generator.py`. The connector comment now goes through `_replace_line_breaks`, the same way `maybe_comment` and `binary` handle comments.

**Test:** I added a regression case to `test_comments` in `tests/test_transpile.py`. It covers `AND` and `OR` with a multi-line comment, and checks that formatting the expected output again gives the same result. I confirmed the test fails without the fix and passes with it.

**Results:** The full suite passes (1113 tests). I did not run `make style` (ruff/mypy), and I did not commit.
