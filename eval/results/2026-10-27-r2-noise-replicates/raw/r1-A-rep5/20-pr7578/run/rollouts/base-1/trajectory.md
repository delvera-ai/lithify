# trajectory base-1

final message:
I could not reproduce the failure, so I made no code changes.

**What I checked on this base (`b897f4c5e`, pure Python, no compiled extension):**

- The exact example, `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, parses and regenerates correctly as Oracle SQL.
- `FORMAT JSON` also works with a qualified column (`t.doc`, `s.t.doc`), a function call, a subquery, a string literal, a bind variable, a JOIN, a table alias, lowercase keywords, and `ERROR ON ERROR` / `NULL ON EMPTY` clauses.
- `tests/dialects/test_oracle.py` passes (25 tests, 213 subtests). Line 559 already covers `JSON_TABLE(foo FORMAT JSON, ...)`.

The parser already has the support you asked for. `_parse_json_table` in `sqlglot/parser.py:7952` calls `_parse_format_json`, and `jsontable_sql` plus `formatjson_sql` in `sqlglot/generator.py` handle the round-trip.

**Two related gaps I found, neither involving `FORMAT JSON` on the input:**

- Column-level `NULL ON ERROR` or `ERROR ON ERROR` inside `COLUMNS (...)` fails with `Expecting )`. For example, `COLUMNS(name VARCHAR2(20) PATH '$.name' NULL ON ERROR)`.
- Oracle's `EXISTS PATH` column form fails the same way.
- `FORMAT JSON ENCODING UTF8` on the input also fails. I'm not certain Oracle's `JSON_TABLE` accepts `ENCODING` at all, so I left it alone.

**Next step:** if your failure involves a different statement, the exact SQL that fails would let me pin it down. A pasted query or the error message would be enough. If it's one of the column-level gaps above, I can add support for those, with tests in `tests/dialects/test_oracle.py`.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|FormatJson\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60; grep -rn -i \"json_table\" tests/dialects/test_oracle.py | head", "description": "Locate JSON_TABLE and FORMAT JSON handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:        "JSON_TABLE": lambd
…[848 chars elided]…
(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:570:INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
tests/dialects/test_oracle.py:577:FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
[tool_use Bash] {"command": "sed -n 7840,7990p sqlglot/parser.py; sed -n 3535,3545p sqlglot/generator.py; sed -n 3615,3635p sqlglot/generator.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='oracle'); print(repr(e)[:800]); print(e.sql('oracle'))\n    except Exception as x: print('ERR', x)\n\"", "description": "Read JSON_TABLE parser and reproduce the failure"}
[tool_result]         if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle 
…[6776 chars elided]…
Identifier(this=doc, quoted=False),
            join_mark=False)),
        schema=JSONSchema(
          expressions=[
            JSONColumnDef(
              this=Identifier(this=id, quoted=False),
              kind=DataType(this=DType.DECIMAL, nested=False),
              path=Literal(this='$.id', is_string=True),
              ordinality=False)]),
        path=Literal(this='$.items[*]', is_string=True)))))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] The exact example parses here, so the failure must be in a variant. Let me probe several shapes.
[tool_use Bash] {"command": "cat > /tmp/probe_jt.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT jt.* FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM 
…[895 chars elided]…
cle\")\n        out = e.sql(\"oracle\")\n        print(\"OK \", out == s, \"|\", out)\n    except Exception as x:\n        print(\"ERR\", s, \"->\", str(x).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_jt.py').read())\"", "description": "Probe JSON_TABLE FORMAT JSON parse variants"}
[tool_result] OK  False | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  False | SELECT jt.* FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  False | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
OK  False | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON EMPTY COLUMNS(id NUMBER PATH '$.id'))
OK  False | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*
…[271 chars elided]…
ON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) -> Invalid expression / Unexpected token. Line 1, Col: 101.
OK  True | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS(empno NUMBER PATH '$'))
OK  True | SELECT * FROM JSON_TABLE(:emps FORMAT JSON, '$[*]' COLUMNS(empno NUMBER PATH '$'))
OK  True | SELECT * FROM JSON_TABLE(res FORMAT JSON, '$.info[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] Every `FORMAT JSON` variant with a supported shape already parses; the `OK False` lines are only the existing `COLUMNS (` spacing normalization. The remaining failures are `EXISTS PATH` and `ENCODING`, which are separate grammar gaps. Let me check the existing test and a few more input shapes (function calls, subqueries, literals).
[tool_use Bash] {"command": "cat > /tmp/probe_jt2.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.a') FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE((SELECT doc FROM t) FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE('[1,2]' FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$'))\",\n \"SELECT * FROM JSON_TA
…[572 chars elided]…
)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_jt2.py').read())\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Probe more JSON_TABLE shapes and run Oracle tests"}
[tool_result] OK  SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.a') FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) | False
OK  SELECT * FROM JSON_TABLE((SELECT doc FROM t) FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) | False
OK  SELECT * FROM JSON_TABLE('[1,2]' FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$')) | False
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS()) | False
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id') ERROR ON ERROR) jt -> Invalid expression / Unexpected token. Line 1, Col: 89.
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) jt | False
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) jt | False
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.22s
[assistant] The Oracle suite passes (25 tests) and `FORMAT JSON` parses in every shape I tried on the pure-Python path. Before concluding it doesn't reproduce, I'll check whether a compiled extension is being loaded, since that could behave differently.
[tool_use Bash] {"command": "find . -name \"*.so\" -not -path \"./.git/*\" | head; <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); import sqlglot.parser as p, sqlglot; print(p.__file__, sqlglot.__file__)\"; git log --oneline -3 -- sqlglot/parser.py; grep -rn \"FORMAT JSON\" tests/dialects/*.py | head -20", "description": "Check for compiled extensions and FORMAT JSON test coverage"}
[tool_result] ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101150-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101150-oracle-dialect-json-table-fails/base-1/sqlglot/__init__.py
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
tests/dialects/test_du
…[729 chars elided]…
:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:694:        for format_json in ("", " FORMAT JSON"):
[assistant] No compiled extension is loaded, so this is the real code path. Let me try the remaining plausible shapes (JOIN, lowercase keywords, pretty output, qualified columns) before deciding whether the bug is real on this base.
[tool_use Bash] {"command": "cat > /tmp/probe_jt3.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT e.id, jt.empno FROM emp e INNER JOIN JSON_TABLE(e.doc FORMAT JSON, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt ON 1 = 1\",\n \"select * from json_table(doc format json, '$.items[*]' columns (id number path '$.id'))\",\n \"SELECT * FROM s.t, JSON_TABLE(s.t.doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id'))\",\n \"
…[307 chars elided]…
\"oracle\")\n        out = e.sql(\"oracle\")\n        print(\"OK \", out)\n    except Exception as x:\n        print(\"ERR\", s, \"->\", str(x).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_jt3.py').read())\"", "description": "Probe JOIN, lowercase, and qualified FORMAT JSON cases"}
[tool_result] OK  SELECT e.id, jt.empno FROM emp e INNER JOIN JSON_TABLE(e.doc FORMAT JSON, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt ON 1 = 1
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM s.t, JSON_TABLE(s.t.doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id', name VARCHAR2(20) PATH '$.name' NULL ON ERROR)) -> Expecting ). Line 1, Col: 116.
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) jt WHERE jt.id > 1
[assistant] I could not reproduce the failure, so I made no code changes.

**What I checked on this base (`b897f4c5e`, pure Python, no compiled extension):**

- The exact example, `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, parses and regenerates correctly as Oracle SQL.
- `FORMAT JSON` also works with a qualified column (`t.doc`, `s.t.doc`), a function call, a subquery, a string literal, a bind variable, a JOIN, a table alias, lowercase keywords, and `ERROR ON ERROR` / `NULL ON EMPTY` clauses.
- `tests/dialects/test_oracle.py` passes (25 tests, 213 subtests). Line 559 already
…[395 chars elided]…
de `COLUMNS (...)` fails with `Expecting )`. For example, `COLUMNS(name VARCHAR2(20) PATH '$.name' NULL ON ERROR)`.
- Oracle's `EXISTS PATH` column form fails the same way.
- `FORMAT JSON ENCODING UTF8` on the input also fails. I'm not certain Oracle's `JSON_TABLE` accepts `ENCODING` at all, so I left it alone.

**Next step:** if your failure involves a different statement, the exact SQL that fails would let me pin it down. A pasted query or the error message would be enough. If it's one of the column-level gaps above, I can add support for those, with tests in `tests/dialects/test_oracle.py`.
