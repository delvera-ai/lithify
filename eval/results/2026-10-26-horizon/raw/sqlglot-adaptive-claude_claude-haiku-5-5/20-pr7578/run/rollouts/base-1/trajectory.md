# trajectory base-1

final message:
I couldn't reproduce the bug, so I made no changes. The `FORMAT JSON` input case already parses and round-trips on this base commit.

What I checked (all under pure Python, from this worktree):

- **Your example:** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t` returns the same SQL back.
- **Existing coverage:** `tests/dialects/test_oracle.py::test_json_table` already has `JSON_TABLE(foo FORMAT JSON, ...)` cases, and the Oracle suite passes (25 tests, 213 subtests).
- **Input variants that also work:** qualified columns (`t.doc`), bind variables (`:doc`), string literals, `CAST(... AS CLOB)`, `JSON_QUERY(...)`, `doc || x`, lowercase `format json`, keyword-like names (`json`, `value`, `data`, `text`, `date`), and a `FROM t, JSON_TABLE(...)` join.
- **Build:** no compiled `.so` modules are present, so the `sqlglotc` namespace package isn't a factor.

Two inputs do still fail. I did not fix them because they may be a different bug from the one you reported:

1. `FORMAT JSON` on a COLUMNS entry, e.g. `COLUMNS (name VARCHAR2(4000) FORMAT JSON PATH '$.n')`. This fails with `Expecting )`. I believe Oracle accepts this, but I haven't verified it against the Oracle docs.
2. `FORMAT JSON ENCODING UTF8` on the input. This fails with an unexpected-token error. I haven't checked whether Oracle accepts it.

A third failure, `ERROR ON ERROR` placed after the COLUMNS list, is not valid Oracle ordering, so I'm not treating it as a bug.

Could you send the exact SQL and error message that fails for you? If it's one of the two cases above, I'll add the parser support and round-trip tests. If it's something else, that will tell me which path to fix.

## events
[tool_use Bash] {"command": "grep -n -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Search JSON_TABLE and FORMAT JSON references"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
sqlglot/parser.py:7958:        return exp.JSONTable(
[tool_use Bash] {"command": "sed -n 7840,7975p sqlglot/parser.py && echo ---- && sed -n 3535,3545p sqlglot/generator.py && echo ---- && sed -n 3615,3635p sqlglot/generator.py && echo ---- && grep -n \"class JSONTable\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Read JSON_TABLE parser and generator code"}
[tool_result ERROR] Exit code 2

        if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) 
…[6286 chars elided]…
qlglot/expressions/json.py-206-        "path": False,
sqlglot/expressions/json.py-207-        "error_handling": False,
sqlglot/expressions/json.py-208-        "empty_handling": False,
sqlglot/expressions/json.py-209-    }
sqlglot/expressions/json.py-210-
sqlglot/expressions/json.py-211-
sqlglot/expressions/json.py-212-class JSONType(Expression, Func):
sqlglot/expressions/json.py-213-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/json.py-214-    _sql_names = ["JSON_TYPE"]
[tool_use Bash] {"command": "grep -rn \"JSON_TABLE\\|JSONTable\" tests/ | head -30; echo ----; grep -rn \"JSONTable\\|class JSONFormat\\|class FormatJson\" sqlglot/ | head; echo ----; grep -n \"JSON_TABLE\\|json_table\" sqlglot/dialects/oracle.py; <work>/env-sqlglot/bin/python -c \"\nimport sq
…[38 chars elided]…
N_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\", \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\"]:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Read JSON table code, grep tests, reproduce failure"}
[tool_result] tests/dialects/test_oracle.py:559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:570:INNER JOIN JSON
…[716 chars elided]…
glot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/expressions/query.py:1944:class FormatJson(Expression):
sqlglot/expressions/json.py:141:class JSONFormat(Expression, Func):
sqlglot/expressions/json.py:202:class JSONTable(Expression, Func):
----
["SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t"]
["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t"]
[assistant] The basic `FORMAT JSON` case already round-trips here, so the failure must be in a narrower form. I'll try variants.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id
…[855 chars elided]…
ELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' COLUMNS (id NUMBER PATH '\\$.id', name VARCHAR2(4000) FORMAT JSON PATH '\\$.n')) t\\\",\n]\nfor s in cases:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\"", "description": "Test JSON_TABLE FORMAT JSON variants on Oracle"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))
…[852 chars elided]…
ELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' COLUMNS (id NUMBER PATH '\\$.id', name VARCHAR2(4000) FORMAT JSON PATH '\\$.n')) t\\\",\n]\nfor s in cases:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\"", "description": "Test JSON_TABLE FORMAT JSON variants on Oracle"}
[tool_result] SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS(a VARCHAR2(10) PATH '$.a'))) t
SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) t
ERR P
…[240 chars elided]…
R ON ERROR COLUMNS(id NUMBER PATH '$.id')) t
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 92.   SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$' COLUMNS (id NUMBER PATH '$.id')[4m)[0m t
SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.a') FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) t
ERR ParseError Expecting ). Line 1, Col: 104.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS (id NUMBER PATH '$.id', name VARCHAR2(4000) [4mFORMAT[0m JSON PATH '$.n')) t
[assistant] Most variants parse. The remaining failures are either invalid Oracle (`ERROR ON ERROR` after `COLUMNS`) or nested-column `FORMAT JSON`, which is a different feature. Let me check the existing test and a few more input shapes before deciding what the reported bug is.
[tool_use Bash] {"command": "sed -n 550,590p tests/dialects/test_oracle.py; git log --oneline -3 -- sqlglot/parser.py | cat; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(doc format json, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) t\\\",\n
…[535 chars elided]…
t\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$' ERROR ON ERROR NULL ON EMPTY COLUMNS (id NUMBER PATH '\\$.a')) t\\\",\n]\nfor s in cases:\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\"", "description": "Inspect existing tests and probe more input shapes"}
[tool_result]     UP AS UP.units_sold > PREV(UP.units_sold),
    FLAT AS FLAT.units_sold = PREV(FLAT.units_sold),
    DOWN AS DOWN.units_sold < PREV(DOWN.units_sold)
) MR""",
            pretty=True,
        )

    def test_json_table(self):
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
        )
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL O
…[1487 chars elided]…
(CAST(doc AS CLOB) FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t WHERE t.id > 1
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
ERR ParseError Expecting ). Line 1, Col: 82.   SELECT id FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS (id NUMBER PATH '$.a' [4mERROR[0m ON ERROR)) t
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' ERROR ON ERROR NULL ON EMPTY COLUMNS(id NUMBER PATH '$.a')) t
[assistant] The reported example parses on this tree. Before concluding, I'll check whether the env is loading compiled `.so` modules that might differ from the Python source, and run the existing Oracle JSON test.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sys;print(sqlglot.__file__)\"; find sqlglot -name \"*.so\" | head -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k json 2>&1 | tail -5; git status --short | head", "description": "Check loaded sqlglot module and run Oracle JSON tests"}
[tool_result] ~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/base-1/sqlglot/__init__.py
..                                                       [100%]
2 passed, 23 deselected, 16 subtests passed in 0.12s
[assistant] The existing test passes and the module is pure Python from this worktree. One plausible trigger I haven't tried: input column names that collide with keywords or type names (for example `json`, which is also a type token). Let me probe that.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nnames = ['json','value','data','doc','text','date','format','clob','t.json','x.doc','doc || x','\\\"JSON\\\"']\nfor n in names:\n    s = f\\\"SELECT * FROM JSON_TABLE({n} FORMAT JSON, '\\$' COLUMNS (id NUMBER PATH '\\$.a')) t\\\"\n    try:\n        print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', n, type(e).__name__, str(e)[:120].replace(chr(10),' '))\n\"", "description": "Probe JSON_TABLE with keyword-like input names"}
[tool_result] SELECT * FROM JSON_TABLE(json FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(value FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(data FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(text FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(date FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(format FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(clob FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(t.json FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(x.doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE(doc || x FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
SELECT * FROM JSON_TABLE("JSON" FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a')) t
[assistant] Every input-shape variant I tried parses and round-trips. One last check: whether the compiled `sqlglotc` extension is installed in the project env, since that's the only other build that could behave differently.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import importlib.util as u;print('sqlglotc:', u.find_spec('sqlglotc'))\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -2; git status --short | wc -l", "description": "Check for compiled extension and run full Oracle tests"}
[tool_result] sqlglotc: ModuleSpec(name='sqlglotc', loader=None, submodule_search_locations=_NamespacePath(['~/.cache/lithify/work/repo-161bf5b46800/20261026-194859-oracle-dialect-json-table-fails/base-1/sqlglotc']))
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.17s
       0
[assistant] I couldn't reproduce the bug, so I made no changes. The `FORMAT JSON` input case already parses and round-trips on this base commit.

What I checked (all under pure Python, from this worktree):

- **Your example:** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) t` returns the same SQL back.
- **Existing coverage:** `tests/dialects/test_oracle.py::test_json_table` already has `JSON_TABLE(foo FORMAT JSON, ...)` cases, and the Oracle suite passes (25 tests, 213 subtests).
- **Input variants that also work:** qualified columns (`t.doc`), bind variables (`:
…[502 chars elided]…
H '$.n')`. This fails with `Expecting )`. I believe Oracle accepts this, but I haven't verified it against the Oracle docs.
2. `FORMAT JSON ENCODING UTF8` on the input. This fails with an unexpected-token error. I haven't checked whether Oracle accepts it.

A third failure, `ERROR ON ERROR` placed after the COLUMNS list, is not valid Oracle ordering, so I'm not treating it as a bug.

Could you send the exact SQL and error message that fails for you? If it's one of the two cases above, I'll add the parser support and round-trip tests. If it's something else, that will tell me which path to fix.
