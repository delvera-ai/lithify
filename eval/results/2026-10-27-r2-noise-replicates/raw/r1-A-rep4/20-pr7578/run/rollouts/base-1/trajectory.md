# trajectory base-1

final message:
I could not reproduce the failure you described: `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` already parses and round-trips on this base. The form that does fail is `FORMAT JSON` on a column inside `COLUMNS (...)`, which Oracle's grammar also allows. I implemented support for that, so it is a guess at what you hit.

**What I tested**
- Input-position `FORMAT JSON` with a column, qualified name, bind variable, literal, function call, expression, and about 20 identifier names (including `data`, `json`, `value`). All parse.
- It also works in FROM, joins, CTEs, subqueries, IN, the select list, and INSERT ... SELECT.
- Still failing, and not changed: `ENCODING UTF8` after `FORMAT JSON`, per-column `EXISTS PATH`, and per-column `ERROR ON ERROR` / `NULL ON ERROR`. Those are separate Oracle features, not `FORMAT JSON`.

**Change**
- `sqlglot/parser.py`: `_parse_json_column_def` accepts an optional `FORMAT JSON` after the column's datatype and records it.
- `sqlglot/expressions/query.py`: `JSONColumnDef` gets a `format_json` flag.
- `sqlglot/generator.py`: `jsoncolumndef_sql` emits ` FORMAT JSON` back in the same position.
- `tests/dialects/test_oracle.py`: added a round-trip case for `data CLOB FORMAT JSON PATH '$.data'`.

**Verification**
- Oracle tests: 25 passed. Full suite: 1096 passed.
- `ruff check` and `ruff format --check` pass on the changed files.
- I did not commit.

If your failing SQL is different from what I tried, send it and I'll reproduce that exact form.

## events
[tool_use Bash] {"command": "grep -n -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|JSONFormat\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80; grep -rn -i \"json_table\" tests/dialects/test_oracle.py | head -20", "description": "Search JSON_TABLE and FORMAT JSON references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7845:    def _parse_format_json(self, t
…[676 chars elided]…
(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:570:INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
tests/dialects/test_oracle.py:577:FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
[tool_use Bash] {"command": "sed -n 7840,7990p sqlglot/parser.py; echo ----; sed -n 3530,3545p sqlglot/generator.py; echo ----; sed -n 3615,3635p sqlglot/generator.py; echo ----; grep -n \"class JSONTable\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; echo ----; sed -n 550,600p tests/dialects/test_oracle.py", "description": "Read JSON_TABLE parser, generator, and tests"}
[tool_result]         if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle 
…[8945 chars elided]…
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
[assistant] The base parser already calls `_parse_format_json` in `_parse_json_table`, so the failure is probably elsewhere. Reproducing before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ntests = [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMN
…[110 chars elided]…
R COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n]\nfor t in tests:\n    try:\n        print(sqlglot.transpile(t, read='oracle', write='oracle'))\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:300])\n\" 2>&1 | head -60", "description": "Reproduce JSON_TABLE FORMAT JSON parse failures"}
[tool_result] ["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"]
["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt"]
["SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"]
["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))"]
["SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"]
[assistant] Every obvious shape parses, so the failing input must be a different shape. Trying a wider set of input forms.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ntests = [\n \\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE('{\\\\\\\"a\\\\\\\":1}' FORMAT JSON, '\\$.a' COLUMNS (id NUMBER PATH '\\$'))\\\",\n \\\"SELECT * FROM JSON_TABLE(JSON_QUERY(x, '\\$.y') FORMAT JS
…[810 chars elided]…
 * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id', x FOR ORDINALITY))\\\",\n]\nfor t in tests:\n    try:\n        print(sqlglot.transpile(t, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:400].replace(chr(10),' '))\n\" 2>&1 | head -80", "description": "Test more JSON_TABLE FORMAT JSON input variants"}
[tool_result] SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE('{"a":1}' FORMAT JSON, '$.a' COLUMNS(id NUMBER PATH '$'))
SELECT * FROM JSON_TABLE(JSON_QUERY(x, '$.y') FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x[*]' COLUMNS(y PATH '$.y')))
SELECT 
…[139 chars elided]…
token. Line 1, Col: 101.   SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')[4m)[0m
ERR ParseError Expecting ). Line 1, Col: 120.   ON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', name VARCHAR2(10) PATH '$.n' [4mNULL[0m ON ERROR))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', x FOR ORDINALITY))
[assistant] Two shapes fail, but neither is a plain `FORMAT JSON` case. Probing more expression shapes to find the real trigger.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ntests = [\n \\\"SELECT * FROM JSON_TABLE(a || b FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(NVL(doc, '{}') FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(s.t.doc FORMAT JSON, '\\$.ite
…[1067 chars elided]…
[*]' COLUMNS (id NUMBER PATH '\\$.id' NULL ON ERROR))\\\",\n]\nfor t in tests:\n    try:\n        print(sqlglot.transpile(t, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:400].replace(chr(10),' '))\n\" 2>&1 | head -80; git log --oneline -3 -- sqlglot/parser.py", "description": "Probe more JSON_TABLE shapes and recent parser history"}
[tool_result] SELECT * FROM JSON_TABLE(a || b FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(NVL(doc, '{}') FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(s.t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR NULL ON EMPTY COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM J
…[612 chars elided]…
l: 91.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mERROR[0m ON ERROR))
ERR ParseError Expecting ). Line 1, Col: 90.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mNULL[0m ON ERROR))
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
[assistant] Every `FORMAT JSON` input shape I've tried parses and round-trips. Next I'll check whether the trigger is the identifier name (keywords like `data`, `json`, `value`) or a column-level `FORMAT JSON`, which Oracle also allows.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nnames = ['doc','data','json','value','key','path','name','order','result','input','text','col','payload','text','date','level','status','items','text','type','column','output','size']\nfor n in names:\n    t = f\\\"SELECT * FROM JSON_TABLE({n} FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER
…[537 chars elided]…
))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (data CLOB FORMAT JSON PATH '\\$.data'))\\\",\n]:\n    try:\n        print(sqlglot.transpile(t, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', str(e)[:200].replace(chr(10),' '))\nprint('done')\n\" 2>&1 | head -60", "description": "Test identifier names and column-level FORMAT JSON"}
[tool_result] ERR Expecting ). Line 1, Col: 68.   SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (data CLOB [4mFORMAT[0m JSON PATH '$.data'))
ERR Expecting ). Line 1, Col: 78.   SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (data VARCHAR2(4000) [4mFORMAT[0m JSON WITH WRAPPER PATH '$.data'))
ERR Expecting ). Line 1, Col: 68.   SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (data CLOB [4mFORMAT[0m JSON PATH '$.data' ERROR ON ERROR))
ERR Expecting ). Line 1, Col: 80.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (data CLOB [4mFORMAT[0m JSON PATH '$.data'))
done
[assistant] Input-position `FORMAT JSON` parses for every identifier I tried. Checking other contexts (CTE, subquery, select list) and running the existing Oracle tests to see whether anything is already red.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\njt = \\\"JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\nfor t in [\n f'WITH x AS (SELECT * FROM {jt}) SELECT * FROM x',\n f'SELECT * FROM (SELECT * FROM {jt})',\n f'SELECT id FROM t WHERE id IN (SELECT id FROM {jt})',\n f'SELECT (SELECT COUNT(*) FROM {jt
…[165 chars elided]…
      print(sqlglot.transpile(t, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', str(e)[:200].replace(chr(10),' '))\n\" 2>&1; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Test JSON_TABLE in other contexts and run Oracle tests"}
[tool_result] WITH x AS (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))) SELECT * FROM x
SELECT * FROM (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')))
SELECT id FROM t WHERE id IN (SELECT id FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')))
SELECT (SELECT COUNT(*) FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))) FROM dual
SELECT * FROM t, JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ORDER BY jt.id
INSERT INTO tgt SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM t JOIN JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt USING (id)
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.22s
[assistant] The input-position form works in every context I tried, and the existing Oracle tests pass (25 passed). The only `FORMAT JSON` form that fails is the column-level one inside `COLUMNS (...)`, which Oracle's JSON_TABLE grammar also allows (`name CLOB FORMAT JSON PATH '$.x'`). Looking at how that node is modeled before deciding on the fix.
[tool_use Bash] {"command": "grep -n \"class JSONColumnDef\" -A 12 sqlglot/expressions/json.py; grep -n \"def jsoncolumndef_sql\" -A 22 sqlglot/generator.py; grep -rn \"JSONColumnDef\" sqlglot --include=*.py | grep -v \"^sqlglot/expressions/json.py\" | head; grep -rn \"FormatJson\\|FORMAT JSON\" tests/dialects/*.py | head -20", "description": "Inspect JSONColumnDef model and generator"}
[tool_result] 3601:    def jsoncolumndef_sql(self, expression: exp.JSONColumnDef) -> str:
3602-        path = self.sql(expression, "path")
3603-        path = f" PATH {path}" if path else ""
3604-        nested_schema = self.sql(expression, "nested_schema")
3605-
3606-        if nested_schema:
3607-            return f"NESTED{path} {nested_schema}"
3608-
3609-        this = self.sql(expression, "this")
3610-        kind = self.sql(expression, "kind")
3611-        kind = f" {kind}" if kind else ""
3612-
3613- 
…[1361 chars elided]…
:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:694:        for format_json in ("", " FORMAT JSON"):
[tool_use Bash] {"command": "grep -rn \"class JSONColumnDef\" -A 12 sqlglot/expressions/; sed -n 685,715p tests/dialects/test_oracle.py", "description": "Find JSONColumnDef class and related Oracle test"}
[tool_result] sqlglot/expressions/query.py:1952:class JSONColumnDef(Expression):
sqlglot/expressions/query.py-1953-    arg_types = {
sqlglot/expressions/query.py-1954-        "this": False,
sqlglot/expressions/query.py-1955-        "kind": False,
sqlglot/expressions/query.py-1956-        "path": False,
sqlglot/expressions/query.py-1957-        "nested_schema": False,
sqlglot/expressions/query.py-1958-        "ordinality": False,
sqlglot/expressions/query.py-1959-    }
sqlglot/expressions/query.py-1960-
sqlglo
…[956 chars elided]…
                  f"SELECT * FROM t WHERE JSON_EXISTS(name{format_json}, '$[1].middle'{passing}{on_cond})"
                        )

    def test_grant(self):
        grant_cmds = [
            "GRANT purchases_reader_role TO george, maria",
            "GRANT USAGE ON TYPE price TO finance_role",
            "GRANT USAGE ON DERBY AGGREGATE types.maxPrice TO sales_role",
        ]

        for sql in grant_cmds:
            with self.subTest(f"Testing Oracles's GRANT command statement: {sql}"):
[assistant] The plan: accept an optional `FORMAT JSON` after the column's datatype in `COLUMNS (...)`, record it as a `format_json` flag on `JSONColumnDef`, and emit it back in the same position. Input-position `FORMAT JSON` already works, so I'll leave that path alone.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "old_string": "            this = self._parse_id_var()\n            ordinality = self._match_pair(TokenType.FOR, TokenType.ORDINALITY)\n            kind = self._parse_types(allow_identifiers=False)\n            nested = None\n        e
…[937 chars elided]…
ATH\") and self._parse_string()\n        nested_schema = nested and self._parse_json_schema()\n\n        return self.expression(\n            exp.JSONColumnDef(\n                this=this,\n                kind=kind,\n                path=path,\n                nested_schema=nested_schema,\n                ordinality=ordinality,\n                format_json=format_json,\n            )\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/expressions/query.py", "old_string": "        \"nested_schema\": False,\n        \"ordinality\": False,\n    }\n\n\nclass JSONSchema(Expression):", "new_string": "        \"nested_schema\": False,\n        \"ordinality\": False,\n        \"format_json\": False,\n    }\n\n\nclass JSONSchema(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/expressions/query.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py", "old_string": "        kind = f\" {kind}\" if kind else \"\"\n\n        ordinality = \" FOR ORDINALITY\" if expression.args.get(\"ordinality\") else \"\"\n        return f\"{this}{kind}{path}{ordinality}\"", "new_string": "        kind = f\" {kind}\" if kind else \"\"\n        format_json = \" FORMAT JSON\" if expression.args.get(\"format_json\") else \"\"\n\n        ordinality = \" FOR ORDINALITY\" if expression.args.get(\"ordinality\") else \"\"\n        return f\"{this}{kind}{format_json}{path}{ordinality}\""}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\"CONVERT('foo', 'dst')\")\n        self.validate_identity(\"CONVERT('foo', 'dst', 'src')\")", "new_string": "        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', data CLOB FORMAT JSON PATH '$.data'))\"\n        )\n        self.validate_identity(\"CONVERT('foo', 'dst')\")\n        self.validate_identity(\"CONVERT('foo', 'dst', 'src')\")"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174109-oracle-dialect-json-table-fails/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Edits are in. Running the Oracle tests, a repro of the column-level case, and the project's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id', data CLOB FORMAT JSON PATH '\\$.data', n FOR ORDINALITY))\\\", read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.a' COLUMNS (NESTED PATH '\\$.b[*]' COLUMNS (x CLOB FORMAT JSON PATH '\\$.x')))\\\", read='oracle', write='oracle')[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run Oracle tests, repro column case, and full test suite"}
[tool_result] .........................                                                   [100%]
25 passed, 213 subtests passed in 0.22s
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', data CLOB FORMAT JSON PATH '$.data', n FOR ORDINALITY))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.a' COLUMNS(NESTED PATH '$.b[*]' COLUMNS(x CLOB FORMAT JSON PATH '$.x')))
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 48.57s
[assistant] The full suite passes (1096 tests). Running the linter on the changed files, then reviewing the diff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/query.py tests/dialects/test_oracle.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/query.py tests/dialects/test_oracle.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
4 files already formatted
 sqlglot/expressions/query.py  | 1 +
 sqlglot/generator.py          | 3 ++-
 sqlglot/parser.py             | 9 ++++++++-
 tests/dialects/test_oracle.py | 3 +++
 4 files changed, 14 insertions(+), 2 deletions(-)
[assistant] I could not reproduce the failure you described: `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` already parses and round-trips on this base. The form that does fail is `FORMAT JSON` on a column inside `COLUMNS (...)`, which Oracle's grammar also allows. I implemented support for that, so it is a guess at what you hit.

**What I tested**
- Input-position `FORMAT JSON` with a column, qualified name, bind variable, literal, function call, expression, and about 20 identifier names (including `data`, `json`, `value`). All parse.
- It also works in FROM, joins, CTEs, subqueries, IN, the s
…[303 chars elided]…
ts an optional `FORMAT JSON` after the column's datatype and records it.
- `sqlglot/expressions/query.py`: `JSONColumnDef` gets a `format_json` flag.
- `sqlglot/generator.py`: `jsoncolumndef_sql` emits ` FORMAT JSON` back in the same position.
- `tests/dialects/test_oracle.py`: added a round-trip case for `data CLOB FORMAT JSON PATH '$.data'`.

**Verification**
- Oracle tests: 25 passed. Full suite: 1096 passed.
- `ruff check` and `ruff format --check` pass on the changed files.
- I did not commit.

If your failing SQL is different from what I tried, send it and I'll reproduce that exact form.
