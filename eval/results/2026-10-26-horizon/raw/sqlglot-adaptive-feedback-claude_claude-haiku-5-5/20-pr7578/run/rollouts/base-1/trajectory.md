# trajectory base-1

final message:
`JSON_TABLE` now parses and round-trips `FORMAT JSON ENCODING <name>` on the input expression. The full suite passes: `1096 passed` with `EXIT: 0`, and ruff check and format are clean on the changed files.

One correction to the report: on this base, the exact example you gave, `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, already parsed and round-tripped. The form that failed was the one with an encoding clause, `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`, which is valid Oracle. I reproduced that failure before changing anything.

**Changes** (uncommitted in the worktree):
- `sqlglot/expressions/query.py`: `FormatJson` accepts an optional `encoding` arg.
- `sqlglot/parser.py`: `_parse_format_json` reads an optional `ENCODING <var>` after `FORMAT JSON`.
- `sqlglot/generator.py`: `formatjson_sql` prints ` ENCODING <x>` when it is set.
- `tests/dialects/test_oracle.py`: added a round-trip case for `FORMAT JSON ENCODING UTF8` in `test_json_table`.

I checked the AST: the input becomes `FormatJson(this=Column(doc), encoding=Var(UTF8))`.

**Behaviour change to review:** `_parse_format_json` is shared, so the `RETURNING <type> FORMAT JSON ENCODING <x>` form in `JSON_OBJECT` is now consumed into the return type's `FormatJson.encoding` rather than the `JSONObject.encoding` arg. The text round-trips unchanged (the `identity.sql` fixture passes), but the AST location moves. If you'd rather keep that untouched, I can scope the encoding to the JSON_TABLE input only.

**Not fixed:** Oracle's `EXISTS PATH` column form inside `COLUMNS (...)` still fails to parse. It is a separate gap from this report.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/expressions/*.py sqlglot/parser.py sqlglot/generator.py | head -60", "description": "Locate JSON_TABLE and FORMAT JSON handling"}
[tool_result] sqlglot/parsers/oracle.py:116:            expressions=self._parse_csv(lambda: self._parse_format_json(self._parse_bitwise())),
sqlglot/parsers/oracle.py:122:            this=self._parse_format_json(self._parse_bitwise()),
sqlglot/parsers/oracle.py:171:        this = self._parse_format_json(self._parse_bitwise())
sqlglot/expressions/json.py:202:class JSONTable(Expression, Func):
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    de
…[294 chars elided]…
e_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
sqlglot/parser.py:7958:        return exp.JSONTable(
[tool_use Bash] {"command": "sed -n 7840,7975p sqlglot/parser.py && echo ---- && sed -n 3530,3545p sqlglot/generator.py && echo ---- && sed -n 3615,3635p sqlglot/generator.py && echo ---- && sed -n 105,130p sqlglot/parsers/oracle.py && sed -n 165,180p sqlglot/parsers/oracle.py && echo ---- && sed -n 195,225p sqlglot/expressions/json.py", "description": "Read JSON_TABLE parser and related code"}
[tool_result]         if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle 
…[8036 chars elided]…
on, Func):
    arg_types = {
        "this": True,
        "schema": True,
        "path": False,
        "error_handling": False,
        "empty_handling": False,
    }


class JSONType(Expression, Func):
    arg_types = {"this": True, "expression": False}
    _sql_names = ["JSON_TYPE"]


class ObjectId(Expression, Func):
    arg_types = {"this": True, "expression": False}


class ObjectInsert(Expression, Func):
    arg_types = {
        "this": True,
        "key": True,
        "value": True,
[tool_use Bash] {"command": "cat > /tmp/repro_jt.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nsql = \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\"\nfor d in [\"oracle\", \"sqlglot\"]:\n    try:\n        e = sqlglot.parse_one(sql, read=\"oracle\")\n        print(repr(e.find(exp.JSONTable)))\n        print(e.sql(\"oracle\"))\n    except Exception as ex:\n        print(\"ERR\", type(ex).__name__, ex)\n    break\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_jt.py').read())\"", "description": "Reproduce the JSON_TABLE FORMAT JSON parse failure"}
[tool_result] JSONTable(
  this=FormatJson(
    this=Column(
      this=Identifier(this=doc, quoted=False),
      join_mark=False)),
  schema=JSONSchema(
    expressions=[
      JSONColumnDef(
        this=Identifier(this=id, quoted=False),
        kind=DataType(this=DType.DECIMAL, nested=False),
        path=Literal(this='$.id', is_string=True),
        ordinality=False)]),
  path=Literal(this='$.items[*]', is_string=True))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[tool_use Bash] {"command": "cat > /tmp/repro_jt2.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT jt.* FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT * FROM JSON_TABLE(
…[978 chars elided]…
s ex:\n        print(\"ERR\", sql[:80], \"->\", type(ex).__name__, str(ex).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_jt2.py').read())\"", "description": "Try JSON_TABLE FORMAT JSON variants on Oracle"}
[tool_result] OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT jt.* FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x'
…[139 chars elided]…
INALITY))
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER EXISTS -> ParseError Expecting ). Line 1, Col: 80.
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt(a)
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt WHERE 1 = 1
[tool_use Bash] {"command": "grep -rn \"JSON_TABLE\" tests/ | head -30; git log --oneline -3 -- sqlglot/parsers/oracle.py; cat > /tmp/repro_jt3.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(
…[844 chars elided]…
eption as ex:\n            print(\"ERR\", d, sql[:70], \"->\", str(ex).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_jt3.py').read())\"", "description": "Check existing JSON_TABLE tests and more variants"}
[tool_result] tests/dialects/test_oracle.py:559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:570:INNER JOIN JSON
…[2360 chars elided]…
 JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id VAR -> Expecting ). Line 1, Col: 86.
ERR sqlglot SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id VAR -> Unknown dialect 'sqlglot'. Did you mean sqlite?
ERR oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUM -> Invalid expression / Unexpected token. Line 1, Col: 102.
ERR sqlglot SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUM -> Unknown dialect 'sqlglot'. Did you mean sqlite?
[tool_use Bash] {"command": "cat > /tmp/repro_jt4.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(doc format json, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER FORMAT JSON PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' WITH WRAPPER))\",\n \"SELECT * FROM 
…[632 chars elided]…
    except Exception as ex:\n        print(\"ERR\", sql[:90], \"->\", str(ex).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_jt4.py').read())\"", "description": "Test more FORMAT JSON placements on Oracle"}
[tool_result] OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER FORMAT JSON PATH -> Expecting ). Line 1, Col: 80.
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' WITH -> Expecting ). Line 1, Col: 90.
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' E
…[6 chars elided]…
N ERROR COLUMNS(id NUMBER PATH '$.id'))
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8 COLUMNS (id NUMBER PATH '$.id')) -> Invalid expression / Unexpected token. Line 1, Col: 62.
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PA -> Invalid expression / Unexpected token. Line 1, Col: 101.
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PA -> Invalid expression / Unexpected token. Line 1, Col: 101.
[tool_use Bash] {"command": "grep -rn '\"ENCODING\"\\|FormatJson' sqlglot/ tests/ | head -30; grep -n \"class FormatJson\" -A4 sqlglot/expressions/*.py", "description": "Find ENCODING and FormatJson usages"}
[tool_result] sqlglot/parser.py:7849:        return self.expression(exp.FormatJson(this=this))
sqlglot/parser.py:7909:        encoding = self._match_text_seq("ENCODING") and self._parse_var()
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglot/expressions/query.py:1944:class FormatJson(Expression):
sqlglot/expressions/query.py:1944:class FormatJson(Expression):
sqlglot/expressions/query.py-1945-    pass
sqlglot/expressions/query.py-1946-
sqlglot/expressions/query.py-1947-
sqlglot/expressions/query.py-1948-class JSONKeyValue(Expression):
[tool_use Bash] {"command": "grep -rn \"ENCODING\" tests/ | head; grep -n \"encoding\" sqlglot/expressions/json.py sqlglot/generator.py | head", "description": "Find ENCODING usages in tests and generator"}
[tool_result] tests/dialects/test_tsql.py:67:            "COPY INTO test_1 FROM 'path' WITH (FORMAT_NAME = test, FILE_TYPE = 'CSV', CREDENTIAL = (IDENTITY='Shared Access Signature', SECRET='token'), FIELDTERMINATOR = ';', ROWTERMINATOR = '0X0A', ENCODING = 'UTF8', DATEFORMAT = 'ymd', MAXERRORS = 10, ERRORFILE = 'errorsfolder', IDENTITY_INSERT = 'ON')"
tests/fixtures/identity.sql:836:JSON_OBJECT('x': 1 RETURNING VARBINARY FORMAT JSON ENCODING UTF8)
sqlglot/expressions/json.py:162:        "encoding": False,
sqlglot/expressions/json.py:172:        "encoding": False,
sqlglot/generator.py:3565:        encoding = self.sql(expression, "encoding")
sqlglot/generator.py:3566:        encoding = f" ENCODING {encoding}" if encoding else ""
sqlglot/generator.py:3574:            suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
[tool_use Bash] {"command": "sed -n 1940,1946p sqlglot/expressions/query.py && sed -n 3540,3543p sqlglot/generator.py", "description": "View FormatJson class and generator"}
[tool_result] class JSONPathWildcard(JSONPathPart):
    pass


class FormatJson(Expression):
    pass


    def formatjson_sql(self, expression: exp.FormatJson) -> str:
        return f"{self.sql(expression, 'this')} FORMAT JSON"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/expressions/query.py", "old_string": "class FormatJson(Expression):\n    pass", "new_string": "class FormatJson(Expression):\n    arg_types = {\"this\": True, \"encoding\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/expressions/query.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py", "old_string": "        return f\"{self.sql(expression, 'this')} FORMAT JSON\"", "new_string": "        encoding = self.sql(expression, \"encoding\")\n        encoding = f\" ENCODING {encoding}\" if encoding else \"\"\n        return f\"{self.sql(expression, 'this')} FORMAT JSON{encoding}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "old_string": "        return self.expression(exp.FormatJson(this=this))", "new_string": "        encoding = self._match_text_seq(\"ENCODING\") and self._parse_var()\n        return self.expression(exp.FormatJson(this=this, encoding=encoding))"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 552,568p tests/dialects/test_oracle.py", "description": "View existing JSON_TABLE tests in Oracle test file"}
[tool_result]     DOWN AS DOWN.units_sold < PREV(DOWN.units_sold)
) MR""",
            pretty=True,
        )

    def test_json_table(self):
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
        )
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
        )
        self.validate_identity(
            """SELECT
  CASE WHEN DBMS_LOB.GETLENGTH(info) < 32000 THEN DBMS_LOB.SUBSTR(info) END AS info_txt,
  info AS info_clob
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            
…[186 chars elided]…
ON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON ENCODING UTF8, 'bla' COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-203349-oracle-dialect-json-table-fails/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one(\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\", read='oracle')\njt = e.find(exp.JSONTable); print(repr(jt.this)); print(jt.this.args.get('encoding').sql())\n\" && $PY -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_mysql.py tests/test_transpile.py tests/dialects/test_postgres.py 2>&1 | tail -5", "description": "Check AST node and run related dialect tests"}
[tool_result] FormatJson(
  this=Column(
    this=Identifier(this=doc, quoted=False),
    join_mark=False),
  encoding=Var(this=UTF8))
UTF8
................................................................................................................... [ 89%]
.............           [100%]
128 passed, 2094 subtests passed in 0.66s
[assistant] Oracle, MySQL, transpile and Postgres tests pass, and the input's `FORMAT JSON` now carries `encoding=Var(UTF8)` in the AST. Running the full suite next.
[tool_use Bash] {"command": "ls .lithify/harness/scripts/ && <work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] run_suite.py
WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-01:03:59 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-27177314d1.log
ELAPSED: 59s
SUMMARY: 1096 passed, 17880 subtests passed in 58.17s
EXIT: 0
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/query.py tests/dialects/test_oracle.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/query.py tests/dialects/test_oracle.py; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 sqlglot/expressions/query.py  | 2 +-
 sqlglot/generator.py          | 4 +++-
 sqlglot/parser.py             | 3 ++-
 tests/dialects/test_oracle.py | 3 +++
 4 files changed, 9 insertions(+), 3 deletions(-)
[assistant] `JSON_TABLE` now parses and round-trips `FORMAT JSON ENCODING <name>` on the input expression. The full suite passes: `1096 passed` with `EXIT: 0`, and ruff check and format are clean on the changed files.

One correction to the report: on this base, the exact example you gave, `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, already parsed and round-tripped. The form that failed was the one with an encoding clause, `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`, which is valid Oracle. I reproduced that failure before changing anything.

**Changes** (uncommitted in the worktree):
-
…[431 chars elided]…
=Column(doc), encoding=Var(UTF8))`.

**Behaviour change to review:** `_parse_format_json` is shared, so the `RETURNING <type> FORMAT JSON ENCODING <x>` form in `JSON_OBJECT` is now consumed into the return type's `FormatJson.encoding` rather than the `JSONObject.encoding` arg. The text round-trips unchanged (the `identity.sql` fixture passes), but the AST location moves. If you'd rather keep that untouched, I can scope the encoding to the JSON_TABLE input only.

**Not fixed:** Oracle's `EXISTS PATH` column form inside `COLUMNS (...)` still fails to parse. It is a separate gap from this report.
