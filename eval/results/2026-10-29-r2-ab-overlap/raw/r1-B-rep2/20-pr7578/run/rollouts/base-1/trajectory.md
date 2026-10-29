# trajectory base-1

final message:
I couldn't reproduce this: `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` already parses and round-trips on this checkout, so I made no code changes.

- **Oracle tests:** `tests/dialects/test_oracle.py` passes (25 tests, 213 subtests). The existing `test_json_table` already covers `JSON_TABLE(foo FORMAT JSON, ...)`.
- **Variants that work:** qualified (`t.doc`) and bind (`:doc`) inputs, function and literal inputs, `CAST(...)`, lowercase keywords, `NESTED PATH`, `ERROR ON ERROR`, and placement in joins, CTEs, subqueries, and `IN (...)`. Pretty output is stable.
- **One failure I did reproduce:** `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$' COLUMNS (...))` raises a ParseError. I didn't add `ENCODING` support because I'm not certain Oracle accepts that clause on `JSON_TABLE`; the SQL standard does. If you want it, the fix means giving `FormatJson` an encoding argument and handling it in `_parse_format_json` and `formatjson_sql`.
- **Unrelated gap:** column-level `EXISTS PATH` and `NULL ON ERROR` inside `COLUMNS (...)` also fail to parse. That's separate from the reported bug.

If you have a failing statement, send it and I'll run it against this checkout. If your failure is on another version or commit, the base commit here is `d043b7a34`.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|FormatJson\\|JSONFormat\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60; grep -rn -i \"json_table\" tests/dialects/test_oracle.py | head -30", "description": "Search JSON_TABLE and FORMAT JSON references"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7849:        return self.expression(exp.FormatJson(this=this))
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglot/generator.py:3542:        return f"{self.sql(expressio
…[427 chars elided]…
(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
tests/dialects/test_oracle.py:570:INNER JOIN JSON_TABLE(:emps, '$[*]' COLUMNS(empno NUMBER PATH '$')) jt
tests/dialects/test_oracle.py:577:FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "offset": 7830, "limit": 150}
[tool_result] 7830	            return self.expression(exp.Decode(this=seq_get(args, 0), charset=seq_get(args, 1)))
7831	
7832	        return self.expression(exp.DecodeCase(expressions=args))
7833	
7834	    def _parse_json_key_value(self) -> exp.JSONKeyValue | None:
7835	        self._match_text_seq("KEY")
7836	        key = self._parse_column()
7837	        self._match_set(self.JSON_KEY_VALUE_SEPARATOR_TOKENS)
7838	        self._match_text_seq("VALUE")
7839	        value = self._parse_bitwise()
7840	
7841	   
…[5446 chars elided]…
  # parse SingleStore MATCH(TABLE ...) syntax
7969	            # https://docs.singlestore.com/cloud/reference/sql-reference/full-text-search-functions/match/
7970	            expressions = []
7971	            table = self._parse_table()
7972	            if table:
7973	                expressions = [table]
7974	        else:
7975	            expressions = self._parse_csv(self._parse_column)
7976	
7977	        self._match_text_seq(")", "AGAINST", "(")
7978	
7979	        this = self._parse_string()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/base-1/tests/dialects/test_oracle.py", "offset": 555, "limit": 30}
[tool_result] 555	        )
556	
557	    def test_json_table(self):
558	        self.validate_identity(
559	            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
560	        )
561	        self.validate_identity(
562	            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
563	            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
…[281 chars elided]…
NUMBER PATH '$')) jt
571	  ON ar.empno = jt.empno""",
572	            pretty=True,
573	        )
574	        self.validate_identity(
575	            """SELECT
576	  *
577	FROM JSON_TABLE(res, '$.info[*]' COLUMNS(
578	  tempid NUMBER PATH '$.tempid',
579	  NESTED PATH '$.calid[*]' COLUMNS(last_dt PATH '$.last_dt ')
580	)) src""",
581	            pretty=True,
582	        )
583	        self.validate_identity("CONVERT('foo', 'dst')")
584	        self.validate_identity("CONVERT('foo', 'dst', 'src')")
[assistant] The parser already calls `_parse_format_json` on the first argument, so the failure is somewhere else. I'll reproduce it before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\\\",\n]:\n  try:\n    print(sqlglot.transpile(s, read='oracle', write='oracle'))\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] ["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"]
["SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt"]
["SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"]
[assistant] Those three parse fine, so the failing shape is something else. I'll try more variants: qualified columns, bind variables, joins, pretty output, and `NESTED PATH`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id
…[493 chars elided]…
LUMNS (id NUMBER EXISTS PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt WHERE jt.id = 1\\\",\n]\nfor s in cases:\n  try:\n    print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:400])\n\"", "description": "Try more JSON_TABLE FORMAT JSON variants"}
[tool_result] SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x[*]' COLUMNS(y PATH '$.y')))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id')) jt
ERR ParseError Expecting ). Line 1, Col: 90.
  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mNULL[0m ON ERROR)) jt
ERR ParseError Expecting ). Line 1, Col: 80.
  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER [4mEXISTS[0m PATH '$.id')) jt
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt WHERE jt.id = 1
[assistant] Most variants parse. The column-level failures (`EXISTS`, `NULL ON ERROR`) are a different, unreported gap. Next I'll test input-expression shapes: function calls, literals, `ENCODING`, lowercase, and `FORMAT JSON` on a string.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(JSON_QUERY(x, '\\$') FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(CAST(doc AS CLOB) FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE('{\\\\\\\"a\
…[507 chars elided]…
alid[*]' COLUMNS(last_dt PATH '\\$.last_dt '))) src\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n]\nfor s in cases:\n  try:\n    print(sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Test FORMAT JSON on function and literal inputs"}
[tool_result] SELECT * FROM JSON_TABLE(JSON_QUERY(x, '$') FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(CAST(doc AS CLOB) FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE('{"a":1}' FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.a'))
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 91.
  SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$' COLUMNS (id NUMBER PATH '$.a')[4m)[0m
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
SELECT * FROM JSON_TABLE(res FORMAT JSON, '$.info[*]' COLUMNS(tempid NUMBER PATH '$.tempid', NESTED PATH '$.calid[*]' COLUMNS(last_dt PATH '$.last_dt '))) src
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
[assistant] The ENCODING case is a real failure. Before deciding it's the one in the report, I'll check the pretty-printed round-trip and recent history for `JSON_TABLE`.
[tool_use Bash] {"command": "git log --oneline -5 -S\"_parse_format_json\" -- sqlglot/parser.py; git log --oneline -5 -- sqlglot/parser.py | head -3; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$
…[138 chars elided]…
e='oracle', pretty=True)[0])\n  print(sqlglot.transpile(s, read='oracle', write='oracle')[0] == sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  print(repr(sqlglot.parse_one(s, read='oracle').find(sqlglot.exp.JSONTable).this))\n\"; grep -n \"FORMAT\\|ENCODING\" sqlglot/tokens.py sqlglot/dialects/oracle.py | head", "description": "Check pretty output, history, and FORMAT/ENCODING tokens"}
[tool_result] 5edc846cb Fix(mysql): move parsing logic for JSON_TABLE to base parser (#2387)
ba9a1283b Feat!(oracle): refactor parsing of 'FORMAT JSON', add support for JSON_ARRAY (#2190)
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
SELECT
  *
FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
True
Forma
…[201 chars elided]…
nm')) jt
True
FormatJson(
  this=Column(
    this=Identifier(this=doc, quoted=False),
    join_mark=False))
6 matches in 1 files:

sqlglot/tokens.py:84:_FORMAT_STRINGS: t.ClassVar[dict[str, tuple[str, TokenType]]]
sqlglot/tokens.py:97:cls._FORMAT_STRINGS = {
sqlglot/tokens.py:129:*cls._FORMAT_STRINGS,
sqlglot/tokens.py:205:_FORMAT_STRINGS: t.ClassVar[dict[str, tuple[str, TokenType]]] = {}
sqlglot/tokens.py:302:"FORMAT": TokenType.FORMAT,
sqlglot/tokens.py:568:format_strings=self._FORMAT_STRINGS,
[assistant] The plain `FORMAT JSON` case round-trips on this checkout, and pretty output is stable. The remaining untested dimension is the input column name, since keyword-like names can trip the parser. Testing a batch of those.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nnames = ['json','data','value','text','doc','input','result','payload','content','clob','blob','format','key','date','name','status','type','items','path','error','null','column','table','ordinality','nested','object','array','select','order']\nfor n in names:\n  s = f\\\"SELECT * FROM JSO
…[81 chars elided]…
\n  try:\n    out = sqlglot.transpile(s, read='oracle', write='oracle')[0]\n    if out != s.replace(\\\"COLUMNS (\\\",\\\"COLUMNS(\\\").replace(' jt', ' jt'): pass\n    print('OK ', n, out if 'FORMAT' not in out else '')\n  except Exception as e: print('ERR', n, str(e).splitlines()[0][:150])\n\" 2>&1 | grep -v \"^OK  $\" | head -40", "description": "Test FORMAT JSON with keyword-like input names"}
[tool_result] OK  json 
OK  data 
OK  value 
OK  text 
OK  doc 
OK  input 
OK  result 
OK  payload 
OK  content 
OK  clob 
OK  blob 
OK  format 
OK  key 
OK  date 
OK  name 
OK  status 
OK  type 
OK  items 
OK  path 
OK  error 
OK  null 
OK  column 
OK  table 
OK  ordinality 
OK  nested 
OK  object 
OK  array 
ERR select Invalid expression / Unexpected token. Line 1, Col: 31.
OK  order
[assistant] Every plain input name parses. The `select` failure is expected, since it's a reserved word. One more batch covers the JSON_TABLE placements a real query would use (JOIN, CTE, subquery, `IN`), then I'll run the Oracle test suite as a baseline.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nJ = \\\"JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\ncases = [\n f\\\"SELECT t.id FROM t INNER JOIN {J} jt ON t.id = jt.id\\\",\n f\\\"SELECT t.id FROM t LEFT OUTER JOIN {J} jt ON t.id = jt.id\\\",\n f\\\"WITH c AS (SELECT * FROM {J}) SELECT * FROM c\\
…[199 chars elided]…
nt('OK ', sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', str(e).splitlines()[0][:200], '|', s)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Test JSON_TABLE FORMAT JSON in joins and subqueries; run Oracle tests"}
[tool_result] OK  SELECT t.id FROM t INNER JOIN JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON t.id = jt.id
OK  SELECT t.id FROM t LEFT OUTER JOIN JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON t.id = jt.id
OK  WITH c AS (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))) SELECT * FROM c
OK  SELECT * FROM t WHERE t.id IN (SELECT jt.id FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt)
OK  SELECT * FROM (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))) s
OK  SELECT * FROM t INNER JOIN LATERAL JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) AS jt
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.27s
[assistant] I couldn't reproduce this: `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` already parses and round-trips on this checkout, so I made no code changes.

- **Oracle tests:** `tests/dialects/test_oracle.py` passes (25 tests, 213 subtests). The existing `test_json_table` already covers `JSON_TABLE(foo FORMAT JSON, ...)`.
- **Variants that work:** qualified (`t.doc`) and bind (`:doc`) inputs, function and literal inputs, `CAST(...)`, lowercase keywords, `NESTED PATH`, `ERROR ON ERROR`, and placement in joins, CTEs, subqueries, and `IN (...)`. Pretty output is stable.
- **One failure I did
…[70 chars elided]…
...))` raises a ParseError. I didn't add `ENCODING` support because I'm not certain Oracle accepts that clause on `JSON_TABLE`; the SQL standard does. If you want it, the fix means giving `FormatJson` an encoding argument and handling it in `_parse_format_json` and `formatjson_sql`.
- **Unrelated gap:** column-level `EXISTS PATH` and `NULL ON ERROR` inside `COLUMNS (...)` also fail to parse. That's separate from the reported bug.

If you have a failing statement, send it and I'll run it against this checkout. If your failure is on another version or commit, the base commit here is `d043b7a34`.
