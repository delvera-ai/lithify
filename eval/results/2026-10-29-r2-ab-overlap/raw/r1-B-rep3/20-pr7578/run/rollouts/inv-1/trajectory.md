# trajectory inv-1

final message:
I couldn't reproduce the failure, so I made no code changes. On this checkout (`f8c8a3e40`), `JSON_TABLE` with `FORMAT JSON` already parses and round-trips in Oracle.

- **Your example parses and round-trips.** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` comes back as the same statement, apart from the existing `COLUMNS(` spacing.
- **The code path already exists.** `_parse_json_table` in `sqlglot/parser.py` calls `_parse_format_json` on the input expression, and the generator writes `FORMAT JSON` back out.
- **Existing coverage passes.** `tests/dialects/test_oracle.py::test_json_table` already covers `JSON_TABLE(foo FORMAT JSON, ...)`. All 25 Oracle tests pass (213 subtests), and the import resolves to this worktree's source.
- **More input shapes also parse.** I tried bind variables, `t.doc`, keyword-like identifiers (`data`, `json`, `value`), lowercase `format json`, joins with aliases, and `TO_CLOB(x)` as the input. All of them parse.

Three other JSON_TABLE forms fail, but they are different features from `FORMAT JSON` on the input:
- `FORMAT JSON ENCODING UTF8` as the input
- `EXISTS PATH` on a column
- a per-column `NULL ON ERROR`

I didn't add support for these, since you asked about `FORMAT JSON` only and I'd be guessing at Oracle's grammar. If one of them is the failure you're seeing, send me the exact SQL and the sqlglot version or commit you're running. The example you gave works here, so the failure may be in a different version or a different query.

## events
[tool_use Bash] {"command": "grep -n -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|JSONFormat\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find JSON_TABLE and FORMAT JSON handling"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py", "offset": 7840, "limit": 130}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py", "offset": 3535, "limit": 15}
[tool_result] 3535	        else:
3536	            escaped = expression.replace('"', '\\"')
3537	            escaped = f'"{escaped}"'
3538	
3539	        return escaped
3540	
3541	    def formatjson_sql(self, expression: exp.FormatJson) -> str:
3542	        return f"{self.sql(expression, 'this')} FORMAT JSON"
3543	
3544	    def formatphrase_sql(self, expression: exp.FormatPhrase) -> str:
3545	        # Output the Teradata column FORMAT override.
3546	        # https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/SQL-Data-Types-and-Literals/Data-Type-Formats-and-Format-Phrases/FORMAT
3547	        this = self.sql(expression, "this")
3548	        fmt = self.sql(expression, "format")
3549	        return f"{this} (FORMAT {fmt})"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py", "offset": 3615, "limit": 20}
[tool_result] 3615	
3616	    def jsonschema_sql(self, expression: exp.JSONSchema) -> str:
3617	        return self.func("COLUMNS", *expression.expressions)
3618	
3619	    def jsontable_sql(self, expression: exp.JSONTable) -> str:
3620	        this = self.sql(expression, "this")
3621	        path = self.sql(expression, "path")
3622	        path = f", {path}" if path else ""
3623	        error_handling = expression.args.get("error_handling")
3624	        error_handling = f" {error_handling}" if error_handling e
…[34 chars elided]…
 = expression.args.get("empty_handling")
3626	        empty_handling = f" {empty_handling}" if empty_handling else ""
3627	        schema = self.sql(expression, "schema")
3628	        return self.func(
3629	            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
3630	        )
3631	
3632	    def openjsoncolumndef_sql(self, expression: exp.OpenJSONColumnDef) -> str:
3633	        this = self.sql(expression, "this")
3634	        kind = self.sql(expression, "kind")
[assistant] The generic parser already calls `_parse_format_json` in `_parse_json_table`, so I need to reproduce the failure before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(doc, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\"]\nfor q in qs:\n  for d in ['oracle','']:\n    try: print(d, sqlglot.transpile(q, read='oracle', write='oracle')[0] if d=='oracle' else sqlglot.parse_one(q, read=d).sql(d))\n    except Exception as e: print(d,'ERR',type(e).__name__, str(e)[:300])\n\" 2>&1 | head -40; git status --short; git log --oneline -1", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
 SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
oracle SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
 SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
 SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
okf8c8a3e40 lithify: probe base
[assistant] The basic case parses on this base commit. I'll check the existing Oracle JSON_TABLE tests and try more input shapes to find what actually fails.
[tool_use Bash] {"command": "grep -rn -i \"json_table\" tests/ | head -30; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\n\\\"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM 
…[469 chars elided]…
'\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id' NULL ON ERROR))\\\",\n]\nfor q in qs:\n    try: print('OK ', sqlglot.transpile(q, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '))\n\" 2>&1", "description": "Check existing tests and more JSON_TABLE variants"}
[tool_result] tests/dialects/test_oracle.py:557:    def test_json_table(self):
tests/dialects/test_oracle.py:559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo
…[1202 chars elided]…
' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS(y VARCHAR2(10) PATH '$.y')))
ERR ParseError Expecting ). Line 1, Col: 80.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER [4mEXISTS[0m PATH '$.id'))
ERR ParseError Expecting ). Line 1, Col: 90.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mNULL[0m ON ERROR))
[assistant] The existing Oracle test already covers `foo FORMAT JSON`, and the exact example from the report parses. I'll try more input shapes (bind variables, keyword-like identifiers, aliases, joins, lowercase) to find the real failing case.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\n\\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(data FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n\\\"SELECT * FROM JSON_TABLE(json FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMB
…[688 chars elided]…
2(20) PATH '\\$.name' ))\\\",\n\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n]\nfor q in qs:\n    try: print('OK ', sqlglot.transpile(q, read='oracle', write='oracle')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:160].replace(chr(10),' '))\n\" 2>&1", "description": "Probe more JSON_TABLE FORMAT JSON input shapes"}
[tool_result] OK  SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(data FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(json FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(value FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(TO_CLOB(x) FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT jt.id FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT jt.id FROM t CROSS JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', name VARCHAR2(20) PATH '$.name'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
[assistant] Every variant I tried parses. Before concluding, I'll confirm which `sqlglot` is being imported (a compiled `.so` could shadow the source) and run the existing Oracle tests.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"import sqlglot,sqlglot.parser as p; print(sqlglot.__file__, p.__file__)\"; find . -name \"*.so\" | head -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Verify imported sqlglot path and run Oracle tests"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/inv-1/sqlglot/__init__.py ~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.21s
[assistant] I couldn't reproduce the failure, so I made no code changes. On this checkout (`f8c8a3e40`), `JSON_TABLE` with `FORMAT JSON` already parses and round-trips in Oracle.

- **Your example parses and round-trips.** `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` comes back as the same statement, apart from the existing `COLUMNS(` spacing.
- **The code path already exists.** `_parse_json_table` in `sqlglot/parser.py` calls `_parse_format_json` on the input expression, and the generator writes `FORMAT JSON` back out.
- **Existing coverage passes.** `tests/di
…[333 chars elided]…
s with aliases, and `TO_CLOB(x)` as the input. All of them parse.

Three other JSON_TABLE forms fail, but they are different features from `FORMAT JSON` on the input:
- `FORMAT JSON ENCODING UTF8` as the input
- `EXISTS PATH` on a column
- a per-column `NULL ON ERROR`

I didn't add support for these, since you asked about `FORMAT JSON` only and I'd be guessing at Oracle's grammar. If one of them is the failure you're seeing, send me the exact SQL and the sqlglot version or commit you're running. The example you gave works here, so the failure may be in a different version or a different query.
