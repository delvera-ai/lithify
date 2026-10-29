# trajectory base-1

final message:
I couldn't reproduce the bug, so I made no code changes. `FORMAT JSON` on the `JSON_TABLE` input already parses and round-trips on this checkout.

- **Reported form:** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` parses and regenerates the same SQL under `read='oracle'`.
- **Other input shapes that work:** qualified and dotted columns (`t.doc`, `s.t.doc`), quoted identifiers, `CAST(... AS CLOB)`, `JSON_QUERY(...) FORMAT JSON`, bind variables, string literals, multi-line SQL, and joins with a `JSON_TABLE` source.
- **Existing coverage:** `tests/dialects/test_oracle.py:559` already covers `JSON_TABLE(foo FORMAT JSON, ...)`. The Oracle test file passes (25 tests, 213 subtests). The parser already calls `_parse_format_json` on the input in `_parse_json_table` (`sqlglot/parser.py:7951`).

Three nearby forms do fail, but none of them is `FORMAT JSON` on the input:
- `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`: the input-side `ENCODING` clause isn't parsed. I'm not sure Oracle accepts it there, so I didn't add it.
- A column with `EXISTS`, e.g. `id NUMBER EXISTS PATH '$.id'`.
- Column-level `NULL ON ERROR` and `DEFAULT 'x' ON EMPTY`.

If you have a failing statement that isn't one of these, send it and I'll trace it. Otherwise I can take up one of the column-level gaps as a separate change.

## events
[tool_use Bash] {"command": "grep -n \"JSON_TABLE\\|JSONTable\\|JSON_TABLE\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn \"FORMAT JSON\\|FormatJson\\|format_json\" sqlglot/*.py sqlglot/dialects/*.py | head -30", "description": "Locate JSON_TABLE and FORMAT JSON handling"}
[tool_result] 5 matches in 2 files:

sqlglot/generator.py:3619:def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:"JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:"JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7951:def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:return exp.JSONTable(
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglo
…[72 chars elided]…
AT JSON"
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7849:        return self.expression(exp.FormatJson(this=this))
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "offset": 7840, "limit": 130}
[tool_result] 7840	
7841	        if not key and not value:
7842	            return None
7843	        return self.expression(exp.JSONKeyValue(this=key, expression=value))
7844	
7845	    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
7846	        if not this or not self._match_text_seq("FORMAT", "JSON"):
7847	            return this
7848	
7849	        return self.expression(exp.FormatJson(this=this))
7850	
7851	    def _parse_on_condition(self) -> exp.OnCondition | None:
7852	        # 
…[4617 chars elided]…
exp.JSONTable(
7959	            this=this,
7960	            schema=schema,
7961	            path=path,
7962	            error_handling=error_handling,
7963	            empty_handling=empty_handling,
7964	        )
7965	
7966	    def _parse_match_against(self) -> exp.MatchAgainst:
7967	        if self._match_text_seq("TABLE"):
7968	            # parse SingleStore MATCH(TABLE ...) syntax
7969	            # https://docs.singlestore.com/cloud/reference/sql-reference/full-text-search-functions/match/
[tool_use Bash] {"command": "sed -n 3610,3635p sqlglot/generator.py && grep -n \"JSONTable\" -A12 sqlglot/expressions.py | head -30 && grep -rn \"JSON_TABLE\" tests/ | head", "description": "Show generator JSONTable and related tests"}
[tool_result]         kind = self.sql(expression, "kind")
        kind = f" {kind}" if kind else ""

        ordinality = " FOR ORDINALITY" if expression.args.get("ordinality") else ""
        return f"{this}{kind}{path}{ordinality}"

    def jsonschema_sql(self, expression: exp.JSONSchema) -> str:
        return self.func("COLUMNS", *expression.expressions)

    def jsontable_sql(self, expression: exp.JSONTable) -> str:
        this = self.sql(expression, "this")
        path = self.sql(expression, "path")
 
…[1373 chars elided]…
[*]' COLUMNS(
tests/dialects/test_mysql.py:112:            "CREATE OR REPLACE VIEW my_view AS SELECT column1 AS `boo`, column2 AS `foo` FROM my_table WHERE column3 = 'some_value' UNION SELECT q.* FROM fruits_table, JSON_TABLE(Fruits, '$[*]' COLUMNS(id VARCHAR(255) PATH '$.$id', value VARCHAR(255) PATH '$.value')) AS q",
tests/dialects/test_mysql.py:299:            "SELECT * FROM source, JSON_TABLE(source.links, '$.org[*]' COLUMNS(row_id FOR ORDINALITY, link VARCHAR(255) PATH '$.link')) AS links"
[assistant] The parser already calls `_parse_format_json` on the input, so the failure is elsewhere. Let me reproduce it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n          \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n          \\\"SELECT * FROM JSON_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='oracle'); print(e.sql('oracle'))\n    except Exception as ex: print('ERR', type(ex).__name__, str(ex)[:300])\n\" 2>&1; git log --oneline -1 -- sqlglot/parser.py", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n          \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n          \\\"SELECT * FROM JSON_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"]:\n    try:\n        e = sqlglot.parse_one(s, read='oracle'); print(e.sql('oracle'))\n    except Exception as ex: print('ERR', type(ex).__name__, str(ex)[:300])\n\" 2>&1", "description": "Reproduce parse failure with worktree sqlglot"}
[tool_result] SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] The basic form parses fine on this checkout, so the failure must come from a different input shape. Let me try variants.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '\\$.item
…[855 chars elided]…
MNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]')\\\",\n]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='oracle'); print('OK ', e.sql('oracle'))\n    except Exception as ex: print('ERR', s[:70], '->', type(ex).__name__, str(ex)[:200].replace(chr(10),' '))\n\" 2>&1", "description": "Test JSON_TABLE FORMAT JSON input variants"}
[tool_result] OK  SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(TO_CLOB(doc) FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM
…[228 chars elided]…
. Line 1, Col: 80.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER [4mEXISTS[0m PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id FOR ORDINALITY, v VARCHAR2(20) PATH '$.v'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS())
[assistant] Only the `EXISTS` column case fails, which is a separate feature. Let me check the remaining Oracle shapes (ENCODING, nested expressions) and the existing tests.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' ERROR ON ERROR NULL ON EMPTY COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FRO
…[288 chars elided]…
racle'); print('OK ', e.sql('oracle'))\n    except Exception as ex: print('ERR', s[:70], '->', type(ex).__name__, str(ex)[:160].replace(chr(10),' '))\n\" 2>&1; PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Test more Oracle shapes and run Oracle tests"}
[tool_result] ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' C -> ParseError Invalid expression / Unexpected token. Line 1, Col: 101.   SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR NULL ON EMPTY COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.x') FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUM -> ParseError Expecting ). Line 1, Col: 90.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mNULL[0m ON ERROR))
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.21s
[assistant] The reported shape already parses and round-trips on this checkout. Before deciding what to change, let me check whether the base commit touched this code path.
[tool_use Bash] {"command": "git show --stat HEAD | head -20; git show --stat HEAD~1 | head -20; git status --short | head; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ns=\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\nfor d in ['oracle','duckdb','snowflake','mysql']:\n    try: print(d, sqlglot.transpile(s, read='oracle', write=d)[0])\n    except Exception as ex: print(d,'ERR',str(ex)[:150])\nprint(repr(sqlglot.parse_one(s, read='oracle').find(sqlglot.exp.JSONTable).this))\n\" 2>&1", "description": "Check recent commits and cross-dialect output"}
[tool_result] commit b252438b710d571033ccbb842d4ef51ff675476e
Author: lithify <lithify@localhost>
Date:   Thu Oct 29 18:29:13 2026 +0200

    lithify: probe base

 .lithify/config.toml | 46 ----------------------------------------------
 1 file changed, 46 deletions(-)
commit 3b03602b486003191a175e5a3dae37ef92f4d2ad
Author: lithify-eval <eval@localhost>
Date:   Thu Oct 29 18:29:13 2026 +0200

    eval setup at 1a10806505db

 .gitignore                        |   1 +
 .lithify/config.toml              |  46 ++
…[399 chars elided]…
nged, 388 insertions(+)
okoracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
duckdb SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
snowflake SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
mysql SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
FormatJson(
  this=Column(
    this=Identifier(this=doc, quoted=False),
    join_mark=False))
[assistant] The reported example round-trips on this checkout. One more batch of input shapes (quoted/dotted identifiers, casts, multi-line) to see whether any variant still fails before I conclude.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n 'SELECT * FROM JSON_TABLE(s.t.doc FORMAT JSON, \\'\\$.items[*]\\' COLUMNS (id NUMBER PATH \\'\\$.id\\'))',\n 'SELECT * FROM JSON_TABLE(\\\"DOC\\\" FORMAT JSON, \\'\\$.items[*]\\' COLUMNS (id NUMBER PATH \\'\\$.id\\'))',\n 'SELECT * FROM JSON_TABLE(CAST(doc AS CLOB)
…[492 chars elided]…
es:\n    try:\n        e = sqlglot.parse_one(s, read='oracle'); out=e.sql('oracle'); print('OK ', out.replace(chr(10),' '), '| roundtrip' if sqlglot.parse_one(out, read='oracle').sql('oracle')==out else '| UNSTABLE')\n    except Exception as ex: print('ERR', s[:60].replace(chr(10),' '), '->', str(ex)[:140].replace(chr(10),' '))\n\" 2>&1", "description": "Test remaining FORMAT JSON input variants"}
[tool_result] OK  SELECT * FROM JSON_TABLE(s.t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) | roundtrip
OK  SELECT * FROM JSON_TABLE("DOC" FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) | roundtrip
OK  SELECT * FROM JSON_TABLE(CAST(doc AS CLOB) FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) | roundtrip
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) | roundtrip
OK  SELECT jt.id FROM orders o, JSON_TABLE(o.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt | roundtrip
ERR SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUM -> Expecting ). Line 1, Col: 122.   SON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', nm VARCHAR2(20) PATH '$.nm' [4mDEF
[assistant] I couldn't reproduce the bug, so I made no code changes. `FORMAT JSON` on the `JSON_TABLE` input already parses and round-trips on this checkout.

- **Reported form:** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` parses and regenerates the same SQL under `read='oracle'`.
- **Other input shapes that work:** qualified and dotted columns (`t.doc`, `s.t.doc`), quoted identifiers, `CAST(... AS CLOB)`, `JSON_QUERY(...) FORMAT JSON`, bind variables, string literals, multi-line SQL, and joins with a `JSON_TABLE` source.
- **Existing coverage:** `tests/diale
…[154 chars elided]…
`_parse_format_json` on the input in `_parse_json_table` (`sqlglot/parser.py:7951`).

Three nearby forms do fail, but none of them is `FORMAT JSON` on the input:
- `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`: the input-side `ENCODING` clause isn't parsed. I'm not sure Oracle accepts it there, so I didn't add it.
- A column with `EXISTS`, e.g. `id NUMBER EXISTS PATH '$.id'`.
- Column-level `NULL ON ERROR` and `DEFAULT 'x' ON EMPTY`.

If you have a failing statement that isn't one of these, send it and I'll trace it. Otherwise I can take up one of the column-level gaps as a separate change.
