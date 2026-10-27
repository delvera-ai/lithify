# trajectory inv-1

final message:
The reported example already parsed and round-tripped on this tree, so the bug is a neighbouring form in the same position. `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)` failed to parse under Oracle, and that's now fixed.

**What reproduced**
- `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t` already parses under `--read oracle`. Its output differs only in spacing (`COLUMNS(`) and the implicit alias, which matches the existing Oracle tests.
- `FORMAT JSON ENCODING UTF8` and `ENCODING UTF16` in that input position failed with a `ParseError`.
- Out of scope, not fixed: a column-level `NULL ON EMPTY` inside `COLUMNS (...)` fails to parse. That's a different construct, and I left it alone.

**What I changed**
- `sqlglot/expressions/query.py`: `FormatJson` now declares an optional `encoding` arg.
- `sqlglot/parser.py`: `_parse_format_json` accepts an optional `ENCODING <var>` after `FORMAT JSON`. This mirrors how `JSON_OBJECT` already parses encoding.
- `sqlglot/generator.py`: `formatjson_sql` emits `ENCODING <x>` when present.
- `tests/dialects/test_oracle.py`: in `test_json_table`, added identity tests for the verbatim example and the `ENCODING UTF8` variant.

**Verification**
- Round-trip via `roundtrip.py --read oracle`:
  - `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t` → `SAME`
  - `SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t` → `SAME`
- Targeted tests (`test_oracle`, `test_mysql`, `test_snowflake`): 170 passed.
- Full suite with the project command: 1096 passed, 17880 subtests passed.

I haven't committed anything.

## events
[tool_use Bash] {"command": "ls -la .lithify 2>/dev/null; find . -name memory.md -not -path './.git/*' | head; grep -n \"JSON_TABLE\\|JSONTable\\|JsonTable\" -i sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/expressions.py sqlglot/generator.py | head -50", "description": "Inspect harness files and JSON_TABLE references"}
[tool_result] total 16
drwxr-xr-x@  5 user  staff   160 Oct 26 19:52 .
drwxr-xr-x@ 30 user  staff   960 Oct 26 19:52 ..
drwxr-xr-x@  8 user  staff   256 Oct 26 19:51 harness
drwxr-xr-x@  3 user  staff    96 Oct 26 19:52 library
-rw-r--r--@  1 user  staff  8011 Oct 26 19:52 state.json
./.lithify/harness/memory.md
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
[tool_use Bash] {"command": "cat .lithify/harness/memory.md; echo ----; sed -n 7940,8000p sqlglot/parser.py; echo ----; sed -n 3615,3635p sqlglot/generator.py; echo ----; grep -n \"class JSONTable\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; echo ----; grep -n \"_parse_format_json\\|FORMAT JSON\\|FORMAT_JSON\\|format_json\" sqlglot/parser.py sqlglot/generator.py | head -30", "description": "Read memory notes and JSON_TABLE parser code"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
----
            )
        )

    def _parse_json_schema(self) -> exp.JSONSchema:
        self._match_text_seq("COLUMNS")
        return self.expression(
            exp.JSONSchema(
                expressions=self._parse_wrapped_csv(self._parse_json_column_def, option
…[3774 chars elided]…
--
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
[assistant] The parser already calls `_parse_format_json` on the input, so I need to reproduce the failure before deciding what's missing.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY .lithify/harness/scripts/roundtrip.py --help 2>&1 | head -20; $PY .lithify/harness/scripts/roundtrip.py <<'SQL'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSQL\nsed -n 7840,7860p sqlglot/parser.py; sed -n 3535,3545p sqlglot/generator.py", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
usage: roundtrip.py [-h] [--read READ] [--write WRITE] [sql ...]

positional arguments:
  sql

options:
  -h, --help     show this help message and exit
  --read READ    source dialect, e.g. oracle
  --write WRITE 
…[1250 chars elided]…
n_handling("EMPTY", *self.ON_CONDITION_TOKENS)

        null = self._parse_on_handling("NULL", *self.ON_CONDITION_TOKENS)
        else:
            escaped = expression.replace('"', '\\"')
            escaped = f'"{escaped}"'

        return escaped

    def formatjson_sql(self, expression: exp.FormatJson) -> str:
        return f"{self.sql(expression, 'this')} FORMAT JSON"

    def formatphrase_sql(self, expression: exp.FormatPhrase) -> str:
        # Output the Teradata column FORMAT override.
[assistant] The default dialect parses it. The task is about Oracle, so I'll reproduce with `--read oracle`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/roundtrip.py --read oracle <<'SQL'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSQL\ngrep -n \"JSON_TABLE\\|json_table\" tests/dialects/test_oracle.py | head; grep -n \"JSON_TABLE\\|JSONTable\\|json_table\" -i sqlglot/dialects/oracle.py", "description": "Reproduce JSON_TABLE failure under Oracle dialect"}
[tool_result] # sqlglot loaded from ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot
CHANGED  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
CHANGED  SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
5
…[15 chars elided]…
_json_table(self):
559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
570:INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
577:FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
[assistant] The reproduction case already parses under Oracle in this worktree, so the failure must depend on a different input shape. I'll try variants.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/roundtrip.py --read oracle <<'SQL'\nSELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER 
…[539 chars elided]…
' COLUMNS (id NUMBER PATH '$.id')) AS t WHERE 1 = 1\nSELECT x FROM t, JSON_TABLE(t.doc FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id')) jt\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSQL\ngrep -n \"FORMAT JSON\\|ENCODING\" sqlglot/dialects/oracle.py sqlglot/parser.py | head", "description": "Try more JSON_TABLE FORMAT JSON variants under Oracle"}
[tool_result] # sqlglot loaded from ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot
CHANGED  SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
CHANGED  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS (y VARCHAR2(10) PATH '$.y'))) t  =>  SELECT * 
…[1388 chars elided]…
')) t WHERE 1 = 1
CHANGED  SELECT x FROM t, JSON_TABLE(t.doc FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id')) jt  =>  SELECT x FROM t, JSON_TABLE(t.doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) jt
CHANGED  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
sqlglot/parser.py:7909:        encoding = self._match_text_seq("ENCODING") and self._parse_var()
[assistant] One variant fails: `FORMAT JSON ENCODING UTF8`. The plain `FORMAT JSON` case from the report still parses here. Before deciding whether that's the real bug, I'll check for a stale compiled extension that could shadow the Python source.
[tool_use Bash] {"command": "find . -name \"*.so\" -not -path './.git/*' | head; git status --short | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sqlglot.parser as p; print(sqlglot.__file__, p.__file__)\"; sed -n 7900,7935p sqlglot/parser.py; sed -n 550,580p tests/dialects/test_oracle.py", "description": "Check for compiled extensions and read related parser/test code"}
[tool_result] ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/__init__.py ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py
            unique_keys = True
        elif self._match_text_seq("WITHOUT", "UNIQUE"):
            unique_keys = False

        self._match_text_seq("KEYS")

        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
     
…[1776 chars elided]…
            """SELECT
  CASE WHEN DBMS_LOB.GETLENGTH(info) < 32000 THEN DBMS_LOB.SUBSTR(info) END AS info_txt,
  info AS info_clob
FROM schemaname.tablename ar
INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
  ON ar.empno = jt.empno""",
            pretty=True,
        )
        self.validate_identity(
            """SELECT
  *
FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
  tempid NUMBER PATH '$.tempid',
  NESTED PATH '$.calid[*]' COLUMNS(last_dt PATH '$.last_dt ')
)) src""",
[assistant] Plain `FORMAT JSON` parses and generates correctly here, and the existing `test_json_table` covers it. The harness says to load `repro-already-passes` when the task's example already works, so I'll do that before deciding what to change.
[tool_use Skill] {"skill": "repro-already-passes", "args": "Oracle JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)) reported as failing to parse; reproduction shows it parses and round-trips already."}
[tool_result] Launching skill: repro-already-passes
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/.claude/skills/repro-already-passes

# The reported example already works

Sessions here are non-interactive: nobody will answer a question. A final message that asks
for "the exact SQL and error" ends the task with an empty patch. Do this instead.

1. **Rule out a false pass (2 checks, then stop checking).**
   - Confirm the code under test is this working tree (`.lithify/harness/scripts/roundtrip.py` prints where `sqlglot`
     was loaded from; it must be 
…[1126 chars elided]…
that pins the task's verbatim example
     (parse + round-trip) next to the existing tests for that construct. This is the deliverable.
   - Failures in a different construct or invalid syntax → mention them in the final message;
     do not fix them.

4. **Finish** with the verification in `system.md`, then report what reproduced, what you
   changed, and any out-of-scope failures you noticed, as statements. Do not end with a question.


ARGUMENTS: Oracle JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)) reported as failing to parse; reproduction shows it parses and round-trips already.
[assistant] The skill's step 1 holds: the reproduction ran against this worktree (`sqlglot loaded from .../inv-1/sqlglot`), and the verbatim example parses under `--read oracle`. Step 2 is to probe the other grammar positions of `FORMAT JSON` inside `JSON_TABLE` in one batch, and check sibling functions for the `ENCODING` form.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/roundtrip.py --read oracle <<'SQL'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON ERROR COLUMN
…[543 chars elided]…
H '$.id', NESTED PATH '$.x' COLUMNS (y NUMBER PATH '$.y'))) t\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (rn FOR ORDINALITY, id NUMBER PATH '$.id')) t\nSQL\necho ---; grep -n \"ENCODING\" tests/dialects/test_oracle.py tests/dialects/test_*.py | head; grep -n \"FORMAT JSON\" tests/dialects/*.py | head -20", "description": "Probe FORMAT JSON grammar positions inside JSON_TABLE"}
[tool_result] # sqlglot loaded from ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot
CHANGED  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
CHANGED  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON ERROR COLUMNS (id NUMBER PATH '$.id')) t  =>  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*
…[2789 chars elided]…
:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:694:        for format_json in ("", " FORMAT JSON"):
[assistant] Two variants fail. `FORMAT JSON ENCODING UTF8` / `UTF16` in the input position is the same construct in the same host, so it is the bug to fix. `NULL ON EMPTY` on a column path is a different construct (column-level error/empty clauses), so I'll note it and leave it alone. Next I'll look at how `FormatJson` is defined before changing it.
[tool_use Bash] {"command": "grep -rn \"class FormatJson\" -A 6 sqlglot/expressions/; grep -rn \"FormatJson\" sqlglot --include=*.py | grep -v \"expressions/\" | head -20; grep -n \"encoding\" sqlglot/generator.py | head", "description": "Inspect FormatJson expression and its usages"}
[tool_result] sqlglot/expressions/query.py:1944:class FormatJson(Expression):
sqlglot/expressions/query.py-1945-    pass
sqlglot/expressions/query.py-1946-
sqlglot/expressions/query.py-1947-
sqlglot/expressions/query.py-1948-class JSONKeyValue(Expression):
sqlglot/expressions/query.py-1949-    arg_types = {"this": True, "expression": True}
sqlglot/expressions/query.py-1950-
(eval):1: no matches found: --include=*.py
3565:        encoding = self.sql(expression, "encoding")
3566:        encoding = f" ENCODING {encoding}" if encoding else ""
3574:            suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
[assistant] `FormatJson` has no declared args, and its generator ignores encoding. The sibling `JSON_OBJECT` path already parses `ENCODING <var>` and emits it the same way, so I'll mirror that: give `FormatJson` an optional `encoding` arg, parse it in `_parse_format_json`, and emit it in `formatjson_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/expressions/query.py", "old_string": "class FormatJson(Expression):\n    pass", "new_string": "class FormatJson(Expression):\n    arg_types = {\"this\": True, \"encoding\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/expressions/query.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py", "old_string": "        if not this or not self._match_text_seq(\"FORMAT\", \"JSON\"):\n            return this\n\n        return self.expression(exp.FormatJson(this=this))", "new_string": "        if not this or not self._match_text_seq(\"FORMAT\", \"JSON\"):\n            return this\n\n        encoding = self._match_text_seq(\"ENCODING\") and self._parse_var()\n        return self.expression(exp.FormatJson(this=this, encoding=encoding))"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py", "old_string": "    def formatjson_sql(self, expression: exp.FormatJson) -> str:\n        return f\"{self.sql(expression, 'this')} FORMAT JSON\"", "new_string": "    def formatjson_sql(self, expression: exp.FormatJson) -> str:\n        encoding = self.sql(expression, \"encoding\")\n        encoding = f\" ENCODING {encoding}\" if encoding else \"\"\n        return f\"{self.sql(expression, 'this')} FORMAT JSON{encoding}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py has been updated successfully.
[assistant] Next I'll add identity tests next to `test_json_table`, pinning the task's verbatim example and the `ENCODING` variant.
[tool_use Bash] {"command": "sed -n 580,600p tests/dialects/test_oracle.py", "description": "Read end of test_json_table to place new tests"}
[tool_result] )) src""",
            pretty=True,
        )
        self.validate_identity("CONVERT('foo', 'dst')")
        self.validate_identity("CONVERT('foo', 'dst', 'src')")

    def test_connect_by(self):
        start = "START WITH last_name = 'King'"
        connect = "CONNECT BY PRIOR employee_id = manager_id AND LEVEL <= 4"
        body = """
            SELECT last_name "Employee",
            LEVEL, SYS_CONNECT_BY_PATH(last_name, '/') "Path"
            FROM employees
            WHERE level <= 3 AND department_id = 80
        """
        pretty = """SELECT
  last_name AS "Employee",
  LEVEL,
  SYS_CONNECT_BY_PATH(last_name, '/') AS "Path"
FROM employees
WHERE
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\"CONVERT('foo', 'dst')\")\n        self.validate_identity(\"CONVERT('foo', 'dst', 'src')\")\n\n    def test_connect_by(self):", "new_string": "        self.validate_identity(\n 
…[39 chars elided]…
oc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t\"\n        )\n        self.validate_identity(\"CONVERT('foo', 'dst')\")\n        self.validate_identity(\"CONVERT('foo', 'dst', 'src')\")\n\n    def test_connect_by(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/roundtrip.py --read oracle <<'SQL'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t\nSELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t\nSQL\n$PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_mysql.py tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Verify round-trip and run oracle and JSON-adjacent dialect tests"}
[tool_result] # sqlglot loaded from ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/inv-1/sqlglot
SAME     SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
SAME     SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
............................................................................................ [ 54%]
..................................... [ 75%]
.......... [ 81%]
...............................                [100%]
170 passed, 2263 subtests passed in 1.57s
[assistant] Both forms now round-trip (`SAME`), and the targeted dialect tests pass. Now the full suite with the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; echo \"exit=${PIPESTATUS[0]}\"; git status --short", "description": "Run full test suite and check changed files", "timeout": 300000}
[tool_result] ....................................... [ 66%]
......................................... [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 72.60s (0:01:12)
exit=
 M sqlglot/expressions/query.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_oracle.py
[assistant] The reported example already parsed and round-tripped on this tree, so the bug is a neighbouring form in the same position. `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)` failed to parse under Oracle, and that's now fixed.

**What reproduced**
- `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t` already parses under `--read oracle`. Its output differs only in spacing (`COLUMNS(`) and the implicit alias, which matches the existing Oracle tests.
- `FORMAT JSON ENCODING UTF8` and `ENCODING UTF16` in that input position failed with a `ParseError`.
- Out o
…[491 chars elided]…
ts/dialects/test_oracle.py`: in `test_json_table`, added identity tests for the verbatim example and the `ENCODING UTF8` variant.

**Verification**
- Round-trip via `roundtrip.py --read oracle`:
  - `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t` → `SAME`
  - `SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t` → `SAME`
- Targeted tests (`test_oracle`, `test_mysql`, `test_snowflake`): 170 passed.
- Full suite with the project command: 1096 passed, 17880 subtests passed.

I haven't committed anything.
