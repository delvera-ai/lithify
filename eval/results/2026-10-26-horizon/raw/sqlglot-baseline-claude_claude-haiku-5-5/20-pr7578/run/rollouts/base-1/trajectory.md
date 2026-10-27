# trajectory base-1

final message:
I couldn't reproduce this on the base commit, so I made no changes.

The example from the report already parses and round-trips:

```
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
```

It produces `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))`. The generic parser already handles `FORMAT JSON` in `_parse_json_table` (`sqlglot/parser.py:7951`), and the generator emits it. `tests/dialects/test_oracle.py::test_json_table` already covers `FORMAT JSON` and passes: 25 passed.

I also tried these and they parse:
- qualified and bind-variable inputs, string literals, quoted identifiers, and a function-call input
- lowercase keywords
- `FROM` lists, `CROSS JOIN`, `LEFT JOIN`, CTEs, aliases, and `WHERE`
- `NESTED PATH`
- pretty printing

The only valid-looking variant that fails is `FORMAT JSON ENCODING UTF8`, which raises `ParseError`. I believe Oracle accepts an `ENCODING` clause after `FORMAT JSON`, but I haven't verified that against the Oracle docs. It's the one plausible gap I found, but I'm not sure it's the bug you hit. Two other variants I tried, `COLUMNS (...) ERROR ON ERROR` and `EXISTS PATH` with a trailing `NULL ON ERROR`, fail too, but I left them out of the list because I think they're not valid Oracle syntax as I wrote them.

Could you send the exact SQL that fails, along with the error text? If it's the `ENCODING` case, I can add support in `_parse_format_json` and the generator, plus a round-trip test in `test_oracle.py`.

## events
[tool_use Bash] {"command": "grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|FormatJson\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Search JSON_TABLE and FORMAT JSON handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:        "JSON_TABLE": lambd
…[151 chars elided]…
7849:        return self.expression(exp.FormatJson(this=this))
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
sqlglot/parser.py:7958:        return exp.JSONTable(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143857-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "offset": 7840, "limit": 130}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143857-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py", "offset": 3615, "limit": 18}
[tool_result] 3615	
3616	    def jsonschema_sql(self, expression: exp.JSONSchema) -> str:
3617	        return self.func("COLUMNS", *expression.expressions)
3618	
3619	    def jsontable_sql(self, expression: exp.JSONTable) -> str:
3620	        this = self.sql(expression, "this")
3621	        path = self.sql(expression, "path")
3622	        path = f", {path}" if path else ""
3623	        error_handling = expression.args.get("error_handling")
3624	        error_handling = f" {error_handling}" if error_handling else ""
3625	        empty_handling = expression.args.get("empty_handling")
3626	        empty_handling = f" {empty_handling}" if empty_handling else ""
3627	        schema = self.sql(expression, "schema")
3628	        return self.func(
3629	            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
3630	        )
3631	
3632	    def openjsoncolumndef_sql(self, expression: exp.OpenJSONColumnDef) -> str:
[assistant] The generic parser already accepts `FORMAT JSON` after the input, so I need to reproduce to see where Oracle fails.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nq = \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"\nfor d in ['oracle','', 'postgres']:\n    try:\n        e = sqlglot.parse_one(q, read='oracle' if d=='oracle' else d or None)\n        print(d, '->', repr(e.sql(dialect='oracle')))\n    except Exception as ex: print(d, 'ERR', type(ex).__name__, str(ex)[:300])\n\"", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] oracle -> "SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"
 -> "SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"
postgres -> "SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))"
[assistant] That basic form already parses. I'll try more Oracle-shaped variants to find the one that actually fails.
[tool_use Bash] {"command": "cat > /private/tmp/claude-501/jt_probe.py <<'EOF'\nimport sqlglot\nqs = [\n \"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELE
…[844 chars elided]…
oundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python -I /private/tmp/claude-501/jt_probe.py; PYTHONPATH=. <work>/env-sqlglot/bin/python -I /private/tmp/claude-501/jt_probe.py", "description": "Probe JSON_TABLE Oracle syntax variants"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/private/tmp/claude-501/jt_probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "/private/tmp/claude-501/jt_probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores PYTHONPATH and cwd, so the import failed. I'll run it via `-c` so the repo is on the path.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"exec(open('/private/tmp/claude-501/jt_probe.py').read())\"", "description": "Run JSON_TABLE probe from repo root"}
[tool_result] OK   SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
FAIL ParseError Invalid expression / Unexpected token. Line 1, Col: 101. | SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x[*]' COLUMNS(y VARCHAR2(10) PATH '$.y')))
FAIL ParseError Expecting ). Line 1, Col: 71. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$' COLUMNS (id NUMBER EXISTS PATH '$.id'))
FAIL ParseError Expecting ). Line 1, Col: 90. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' NULL ON ERROR))
OK   SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] The basic `FORMAT JSON` form parses on this base, so the failure must be in a context I haven't hit yet. I'll check existing Oracle tests and the FROM/JOIN contexts.
[tool_use Bash] {"command": "grep -rn -i \"json_table\" tests/ | head -30; cat > /private/tmp/claude-501/jt_probe2.py <<'EOF'\nimport sqlglot\nqs = [\n \"SELECT jt.id FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT jt.id FROM t CROSS JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT jt.id FROM t LEFT JOIN JSON_TAB
…[646 chars elided]…
xcept Exception as ex:\n        print(\"FAIL\", type(ex).__name__, str(ex).splitlines()[0][:200], \"|\", q)\nEOF\n<work>/env-sqlglot/bin/python -c \"exec(open('/private/tmp/claude-501/jt_probe2.py').read())\"", "description": "Check existing JSON_TABLE tests and FROM contexts"}
[tool_result] tests/dialects/test_mysql.py:112:            "CREATE OR REPLACE VIEW my_view AS SELECT column1 AS `boo`, column2 AS `foo` FROM my_table WHERE column3 = 'some_value' UNION SELECT q.* FROM fruits_table, JSON_TABLE(Fruits, '$[*]' COLUMNS(id VARCHAR(255) PATH '$.$id', value VARCHAR(255) PATH '$.value')) AS q",
tests/dialects/test_mysql.py:299:            "SELECT * FROM source, JSON_TABLE(source.links, '$.org[*]' COLUMNS(row_id FOR ORDINALITY, link VARCHAR(255) PATH '$.link')) AS links"
tests/dialect
…[934 chars elided]…
IN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON 1 = 1
OK   WITH c AS (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.a[*]' COLUMNS(id NUMBER PATH '$.id'))) SELECT * FROM c
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.a[*]' COLUMNS(id NUMBER PATH '$.id')) jt(x)
OK   SELECT * FROM JSON_TABLE(JSON_OBJECT('a': 1) FORMAT JSON, '$.a' COLUMNS(id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.a[*]' COLUMNS(id NUMBER PATH '$.id')) WHERE 1 = 1
[assistant] Every variant I tried parses, and an existing Oracle test already covers `FORMAT JSON`. I'll check the test body and whether compiled `.so` modules are shadowing the Python source.
[tool_use Bash] {"command": "sed -n 555,600p tests/dialects/test_oracle.py; echo ---; find . -name \"*.so\" -not -path \"./.git/*\" | head; echo ---; git status --short | head; git log --oneline -3", "description": "Inspect Oracle JSON_TABLE tests and build artifacts"}
[tool_result]         )

    def test_json_table(self):
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
        )
        self.validate_identity(
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
        )
        self.validate_ide
…[822 chars elided]…
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
---
---
284a13cc5 lithify: probe base
cbc558fbf eval setup at 1a10806505db
1a1080650 feat(mypyc): Enable incremental compilation, deprecate Python 3.9 (#7574)
[assistant] The base parses the reported form and an existing test covers it. I'll try the remaining input shapes (bind variables, literals, lowercase, pretty printing) before concluding.
[tool_use Bash] {"command": "cat > /private/tmp/claude-501/jt_probe3.py <<'EOF'\nimport sqlglot\nqs = [\n \"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE('{\\\"a\\\":1}' FORMAT JSON, '$.a' COLUMNS (id NUMBER PATH '$.id'))\",\n \"select * from json_table(doc format json, '$.items[*]' columns (id number path '$.id'))\",\n \"SELECT * FROM JSO
…[709 chars elided]…
  except Exception as ex:\n            print(\"FAIL\", pretty, type(ex).__name__, str(ex).splitlines()[0][:160], \"|\", q)\nEOF\n<work>/env-sqlglot/bin/python -c \"exec(open('/private/tmp/claude-501/jt_probe3.py').read())\"", "description": "Probe more JSON_TABLE input shapes"}
[tool_result] OK   SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK-P SELECT   * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE('{"a":1}' FORMAT JSON, '$.a' COLUMNS(id NUMBER PATH '$.id'))
OK-P SELECT   * FROM JSON_TABLE('{"a":1}' FORMAT JSON, '$.a' COLUMNS(id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK-P SELECT   * FROM JSON_TABLE(doc 
…[548 chars elided]…
TH '$.id')) jt ORDER BY 1
OK-P SELECT   * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ORDER BY   1
FAIL False ParseError Invalid expression / Unexpected token. Line 1, Col: 95. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id') ERROR ON ERROR)
FAIL True ParseError Invalid expression / Unexpected token. Line 1, Col: 95. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id') ERROR ON ERROR)
[assistant] None of the valid Oracle inputs I tried fail on this base. I'll run the Oracle test module to confirm the existing coverage passes as-is.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Run Oracle dialect tests on base"}
[tool_result] .........................                                                   [100%]
25 passed, 213 subtests passed in 0.21s
[assistant] I couldn't reproduce this on the base commit, so I made no changes.

The example from the report already parses and round-trips:

```
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
```

It produces `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))`. The generic parser already handles `FORMAT JSON` in `_parse_json_table` (`sqlglot/parser.py:7951`), and the generator emits it. `tests/dialects/test_oracle.py::test_json_table` already covers `FORMAT JSON` and passes: 25 passed.

I also tried these and they parse:
- qual
…[336 chars elided]…
le accepts an `ENCODING` clause after `FORMAT JSON`, but I haven't verified that against the Oracle docs. It's the one plausible gap I found, but I'm not sure it's the bug you hit. Two other variants I tried, `COLUMNS (...) ERROR ON ERROR` and `EXISTS PATH` with a trailing `NULL ON ERROR`, fail too, but I left them out of the list because I think they're not valid Oracle syntax as I wrote them.

Could you send the exact SQL that fails, along with the error text? If it's the `ENCODING` case, I can add support in `_parse_format_json` and the generator, plus a round-trip test in `test_oracle.py`.
