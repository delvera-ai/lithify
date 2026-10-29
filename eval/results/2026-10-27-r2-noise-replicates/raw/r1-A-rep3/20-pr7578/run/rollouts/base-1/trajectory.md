# trajectory base-1

final message:
I couldn't reproduce the failure, so I made no code changes. `FORMAT JSON` on the JSON_TABLE input expression already parses and round-trips at HEAD.

- **Input expression:** `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(...))` parses and round-trips in Oracle. That held for a bare column, a qualified column, a bind variable, a string literal, a function call, a quoted identifier, lowercase `format json`, and with `ERROR ON ERROR`, `NESTED PATH`, and a table alias. `tests/dialects/test_oracle.py` already covers `JSON_TABLE(foo FORMAT JSON, ...)`, and all 25 tests pass. Transpiling to duckdb, postgres, snowflake, mysql, tsql and spark also works.
- **Likely actual failure:** a `FORMAT JSON` on a column inside `COLUMNS(...)`, e.g. `payload CLOB FORMAT JSON PATH '$.p'`. This is valid Oracle column syntax and fails with `Expecting )`. The parser's `_parse_json_column_def` doesn't handle it. It's a different clause from the one you described, so I didn't change it.
- **Other failures I saw:** `PASSING ... AS x` and a path alias `AS p` also fail to parse. Those aren't `FORMAT JSON` issues, so I didn't touch them.

Could you send the exact query that fails? If it's the column-level form, I can add `FORMAT JSON` to the column definition, with a round-trip test in `tests/dialects/test_oracle.py`.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|JSONFormat\\|format_json\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60; grep -rn -i \"json_table\" tests/dialects/test_oracle.py | head", "description": "Search JSON_TABLE and FORMAT JSON references"}
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
[tool_use Bash] {"command": "sed -n 7840,7990p sqlglot/parser.py; echo ----; sed -n 3530,3550p sqlglot/generator.py; echo ----; sed -n 3610,3640p sqlglot/generator.py; echo ----; sed -n 550,600p tests/dialects/test_oracle.py", "description": "Read JSON parsing and generation code and tests"}
[tool_result]         if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle 
…[8923 chars elided]…
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
[assistant] The existing test already covers `JSON_TABLE(foo FORMAT JSON, ...)`, so the failure must be in a different shape. I'll reproduce it first.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' COLUMNS(foo PATH 'bar'))\\\",\n]:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' COLUMNS(foo PATH 'bar'))
[assistant] Those all parse. I'll try more input shapes: bind variables, literals, lowercase, and a few more expression types.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$.items[*]' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '\\$.items[*]' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc format json, '\\$.items[*]
…[661 chars elided]…
 '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS(id NUMBER PATH '\\$.id')) jt\\\",\n]\nfor s in cases:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\"", "description": "Test more JSON_TABLE FORMAT JSON input variants"}
[tool_result] SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x[*]' COLUMNS(y PATH '$.y')))
SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.a') FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR ParseError Expecting ). Line 1, Col: 110.   CT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', name VARCHAR2(10) [4mFORMAT[0m JSON PATH '$.n'))
SELECT jt.* FROM t, JSON_TABLE(t.doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
[assistant] Input-expression `FORMAT JSON` parses in every shape so far. The one failure is a per-column `FORMAT JSON`, which is a different clause. I'll check the existing test and try a few more input forms before deciding.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(t.doc.payload FORMAT JSON, '\\$' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(\\\\\\\"DOC\\\\\\\" FORMAT JSON, '\\$' COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(NVL(doc, '{}') FORMAT JS
…[586 chars elided]…
.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\" ; PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Test more input forms and run Oracle test file"}
[tool_result] SELECT * FROM JSON_TABLE(t.doc.payload FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE("DOC" FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(NVL(doc, '{}') FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) WHERE 1 = 1
SELECT id FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.22s
[assistant] Every input-expression form I've tried parses and round-trips, and the existing Oracle tests pass (25 passed). Before concluding it doesn't reproduce, I'll check for compiled `.so` modules that could shadow the source, and try the other dialects and the parse/generate path.
[tool_use Bash] {"command": "ls sqlglot/*.so 2>/dev/null | head; git log --oneline -3 -- sqlglot/parser.py; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot, sqlglot.parser as p; print(sqlglot.__file__, p.__file__)\nfrom sqlglot import exp\ns=\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\ne=sqlglot.parse_one(s, read='oracle'); print(repr(e.args['from'])[:400])\nfor d in ['duckdb','postgres','snowflake','oracle','mysql','tsql']:\n    try: print(d, sqlglot.transpile(s, read='oracle', write=d)[0])\n    except Exception as x: print(d,'ERR',str(x)[:150])\n\"", "description": "Check compiled modules and cross-dialect output"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: sqlglot/*.so
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'from'
~/.cache/lithify/work/repo-90e86f132b84/20261028-121527-oracle-dialect-json-table-fails/base-1/sqlglot/__init__.py ~/.cache/lithify/work/repo-90e86f132b84/20261028-121527-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns=\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\nfor d in ['duckdb','postgres','snowflake','oracle','mysql','tsql','spark']:\n    try: print(d, sqlglot.transpile(s, read='oracle', write=d)[0])\n    except Exception as x: print(d,'ERR',str(x)[:150])\nprint(repr(sqlglot.parse_one(s, read='oracle').find(sqlglot.exp.JSONTable))[:500])\n\"", "description": "Cross-dialect output and JSONTable AST inspection"}
[tool_result] duckdb SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
postgres SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
snowflake SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
mysql SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
tsql SELECT * FROM JSO
…[79 chars elided]…
LECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
JSONTable(
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
[assistant] At HEAD the input-expression form parses and round-trips across dialects. I'll try a last set of Oracle-valid variants (path alias, PASSING, column-level FORMAT JSON) to find the actual failing shape.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' NULL ON EMPTY ERROR ON ERROR COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' AS p COLUMNS(id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON,
…[180 chars elided]…
ON PATH '\\$.p'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' COLUMNS(payload CLOB FORMAT JSON PATH '\\$.p'))\\\",\n]\nfor s in cases:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e:\n        print('ERR', type(e).__name__, str(e)[:120].replace(chr(10),' '))\n\"", "description": "Probe remaining Oracle JSON_TABLE variants"}
[tool_result] ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 68.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' NULL ON EMPTY ER
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 58.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' AS p [4mCOLUMNS
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 59.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' PASSING :x [4mA
ERR ParseError Expecting ). Line 1, Col: 105.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id', payload VA
ERR ParseError Expecting ). Line 1, Col: 73.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(payload CLOB [4mFORMAT[0m JSON P
[assistant] I couldn't reproduce the failure, so I made no code changes. `FORMAT JSON` on the JSON_TABLE input expression already parses and round-trips at HEAD.

- **Input expression:** `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(...))` parses and round-trips in Oracle. That held for a bare column, a qualified column, a bind variable, a string literal, a function call, a quoted identifier, lowercase `format json`, and with `ERROR ON ERROR`, `NESTED PATH`, and a table alias. `tests/dialects/test_oracle.py` already covers `JSON_TABLE(foo FORMAT JSON, ...)`, and all 25 tests pass. Transpiling to duckd
…[112 chars elided]…
mn inside `COLUMNS(...)`, e.g. `payload CLOB FORMAT JSON PATH '$.p'`. This is valid Oracle column syntax and fails with `Expecting )`. The parser's `_parse_json_column_def` doesn't handle it. It's a different clause from the one you described, so I didn't change it.
- **Other failures I saw:** `PASSING ... AS x` and a path alias `AS p` also fail to parse. Those aren't `FORMAT JSON` issues, so I didn't touch them.

Could you send the exact query that fails? If it's the column-level form, I can add `FORMAT JSON` to the column definition, with a round-trip test in `tests/dialects/test_oracle.py`.
