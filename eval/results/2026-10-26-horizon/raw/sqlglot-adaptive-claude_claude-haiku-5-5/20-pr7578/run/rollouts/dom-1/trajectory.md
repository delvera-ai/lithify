# trajectory dom-1

final message:
The example you gave already parsed and round-tripped before I changed anything. The failure is the column-level form: `FORMAT JSON` after a column's type inside `COLUMNS(...)` (Oracle's JSON_query column). That raised `Expecting )`. I fixed that.

**Change**
- `sqlglot/parser.py`, `_parse_json_column_def`: the column type is now wrapped with the existing `_parse_format_json` idiom, so `doc2 CLOB FORMAT JSON PATH '$.x'` parses. The generator already prints the wrapped type as `CLOB FORMAT JSON`, so the round-trip works without generator changes.
- `tests/dialects/test_oracle.py::test_json_table`: added a `validate_identity` case for `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(doc2 CLOB FORMAT JSON PATH '$.x'))`.

**Verification**
- Full test suite: 1096 passed.
- `ruff check` and `ruff format --check`: clean.

**Not done**
- I did not commit. Per the repo's workflow, say if you want a commit.
- Per-column `ERROR ON ERROR` is still unparsed, as the skill notes flagged. I left it out of scope because you asked for `FORMAT JSON`.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support", "args": "Oracle JSON_TABLE fails to parse when the input expression has FORMAT JSON: JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)). Make it parse and round-trip."}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/dom-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes wit
…[2484 chars elided]…
 quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.


ARGUMENTS: Oracle JSON_TABLE fails to parse when the input expression has FORMAT JSON: JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)). Make it parse and round-trip.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nqs=[\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\",\n\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id', doc2 CLOB FORMAT JSON PATH '\\$.x')) t\\\",\n\\\"SELECT * FROM JSON_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\"]\nfor q in qs:\n  try:\n    print(sqlglot.transpile(q, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" ; grep -n \"json_table\\|JSON_TABLE\" tests/dialects/test_oracle.py | head; grep -n \"def _parse_json_column_def\" -A40 sqlglot/parser.py | head -70", "description": "Test JSON_TABLE Oracle variants and inspect parser"}
[tool_result] SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
ERR ParseError Expecting ). Line 1, Col: 103.
  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', doc2 CLOB [4mFORMAT[0m JSON PATH '$.x')) t
SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
557:    def test_json_table(self):
559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
…[1612 chars elided]…
_parse_format_json(self._parse_bitwise())
7953-        path = self._match(TokenType.COMMA) and self._parse_string()
7954-        error_handling = self._parse_on_handling("ERROR", "ERROR", "NULL")
7955-        empty_handling = self._parse_on_handling("EMPTY", "ERROR", "NULL")
7956-        schema = self._parse_json_schema()
7957-
7958-        return exp.JSONTable(
7959-            this=this,
7960-            schema=schema,
7961-            path=path,
7962-            error_handling=error_handling,
[tool_use Bash] {"command": "grep -n \"_parse_format_json\" -A12 sqlglot/parser.py | head -60; grep -n \"def jsoncolumndef_sql\" -A20 sqlglot/generator.py; grep -n \"def formatjson_sql\" -A4 sqlglot/generator.py; sed -n 555,570p tests/dialects/test_oracle.py", "description": "Inspect format JSON parse and generator helpers"}
[tool_result] 7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
7846-        if not this or not self._match_text_seq("FORMAT", "JSON"):
7847-            return this
7848-
7849-        return self.expression(exp.FormatJson(this=this))
7850-
7851-    def _parse_on_condition(self) -> exp.OnCondition | None:
7852-        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle uses the opposite (e.g. JSON_EXISTS)
7853-        if self.dialect.ON_CONDITION_EMPTY_BEFORE_ERRO
…[3387 chars elided]…
       "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
        )
        self.validate_identity(
            """SELECT
  CASE WHEN DBMS_LOB.GETLENGTH(info) < 32000 THEN DBMS_LOB.SUBSTR(info) END AS info_txt,
  info AS info_clob
FROM schemaname.tablename ar
INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
[assistant] The literal example already parses. The gap is the column-level form: `FORMAT JSON` after a column's type (`doc2 CLOB FORMAT JSON PATH '$.x'`) fails. I'll apply the existing `FormatJson` wrapping idiom to the column type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/dom-1/sqlglot/parser.py", "old_string": "            kind = self._parse_types(allow_identifiers=False)\n            nested = None", "new_string": "            kind = self._parse_format_json(self._parse_types(allow_identifiers=False))\n            nested = None"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/dom-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/dom-1/tests/dialects/test_oracle.py", "old_string": "    def test_json_table(self):\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )", "new_string": "    def test_json_table(self):\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(doc2 CLOB FORMAT JSON PATH '$.x'))\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/dom-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY >/dev/null 2>&1 || PY=python3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects tests/test_parser.py tests/test_transpile.py 2>&1 | tail -15", "description": "Run dialect and parser test suites"}
[tool_result] ................................................................................. [  9%]
............................................................................................................................................ [ 26%]
............................................................ [ 34%]
........................................................................ [ 43%]
..................................................................... [ 51%]
......................................
…[4 chars elided]…
...... [ 57%]
...................................................................................................................................... [ 73%]
.................. [ 75%]
...................... [ 78%]
............................................ [ 83%]
....................................... [ 88%]
................................ [ 92%]
.............................................................                                      [100%]
820 passed, 12103 subtests passed in 15.69s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY >/dev/null 2>&1 || PY=python3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m ruff check sqlglot tests/dialects/test_oracle.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot tests/dialects/test_oracle.py 2>&1 | tail -2", "description": "Run full test suite and lint checks"}
[tool_result] ............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 76.28s (0:01:16)
All checks passed!
175 files already formatted
[assistant] The example you gave already parsed and round-tripped before I changed anything. The failure is the column-level form: `FORMAT JSON` after a column's type inside `COLUMNS(...)` (Oracle's JSON_query column). That raised `Expecting )`. I fixed that.

**Change**
- `sqlglot/parser.py`, `_parse_json_column_def`: the column type is now wrapped with the existing `_parse_format_json` idiom, so `doc2 CLOB FORMAT JSON PATH '$.x'` parses. The generator already prints the wrapped type as `CLOB FORMAT JSON`, so the round-trip works without generator changes.
- `tests/dialects/test_oracle.py::test_json_table`: added a `validate_identity` case for `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(doc2 CLOB FORMAT JSON PATH '$.x'))`.

**Verification**
- Full test suite: 1096 passed.
- `ruff check` and `ruff format --check`: clean.

**Not done**
- I did not commit. Per the repo's workflow, say if you want a commit.
- Per-column `ERROR ON ERROR` is still unparsed, as the skill notes flagged. I left it out of scope because you asked for `FORMAT JSON`.
