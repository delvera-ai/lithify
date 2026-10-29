# trajectory dom-1

final message:
I could not reproduce this, so I made no code changes.

**Result:** On the current checkout, `JSON_TABLE` with `FORMAT JSON` on the input already parses and round-trips in the Oracle dialect. This includes the exact shape from the report:

```
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
→ SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
```

I also checked these, and all parse:
- a qualified column (`t.doc`), a bind variable (`:doc`), and a string literal as the input
- an alias (`jt`), a JOIN, lowercase keywords, and a trailing newline
- a nested `NESTED PATH` column inside `COLUMNS`
- `ERROR ON ERROR` / `NULL ON EMPTY` placed before `COLUMNS`

The shared parser already handles this. `_parse_json_table` calls `_parse_format_json` on the input (`sqlglot/parser.py:7952`), and `tests/dialects/test_oracle.py::test_json_table` already covers `foo FORMAT JSON`. `tests/dialects/test_oracle.py` and `tests/dialects/test_mysql.py` pass (75 tests). The history also shows `FORMAT JSON` support was added in earlier commits.

**Forms that still fail, which the report may have meant:**
- `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`: the `ENCODING` clause is not parsed.
- `COLUMNS (id NUMBER PATH '$.id' FORMAT JSON)`: `FORMAT JSON` on a column is not parsed. I didn't treat this as in scope, since the report is about the input expression.
- `... COLUMNS (...) ERROR ON ERROR)`: the error clause placed after `COLUMNS` is rejected. Oracle puts it before `COLUMNS`, so this input is not valid Oracle anyway.

If one of these is what you hit, or you have a failing statement from another environment, send it and I'll reproduce it against that. I'd expect a fix to go in `_parse_json_table` in the shared parser, plus a case in `test_json_table`. That would also affect MySQL, which shares the parser.

The working tree is clean.

## events
[tool_use Skill] {"skill": "dialect-syntax-change"}
[tool_result] Launching skill: dialect-syntax-change
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/dom-1/.claude/skills/dialect-syntax-change

# Changing how a SQL construct parses or generates

Where each part lives (verified against the source):

- **Tokens:** `sqlglot/tokens.py` (`KEYWORDS`, `SINGLE_TOKENS`, `TokenType`).
- **Function syntax:** `Parser.FUNCTION_PARSERS` in the base `sqlglot/parser.py` (around line 1485) maps a
  name such as `"JSON_TABLE"` to a `_parse_*` method. Dialects extend this dict; they do not re-implement
  shared functions.
- **Sha
…[737 chars elided]…
NTS.md, "The sqlglot Dialect").
2. A change to base-parser code reaches every dialect. JSON_TABLE parsing is covered in
   `tests/dialects/test_oracle.py` (`test_json_table`) and in `tests/dialects/test_mysql.py`. MySQL's
   JSON_TABLE parsing was moved into the base parser in commit `5edc846cb`, so a change there can affect
   MySQL too.
3. Add round-trip cases to the existing test method for that dialect with `validate_identity`, and
   cross-dialect output with `validate_all`. Read the existing method first, because it may already cover
   the case. Do not change existing expected outputs.

[tool_use Bash] {"command": "grep -rn -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|JSONFormat\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/*.py | head -80", "description": "Locate JSON_TABLE and FORMAT JSON code"}
[tool_result] sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py
…[48 chars elided]…
f._parse_bitwise())
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3542:        return f"{self.sql(expression, 'this')} FORMAT JSON"
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/expressions/json.py:141:class JSONFormat(Expression, Func):
sqlglot/expressions/json.py:202:class JSONTable(Expression, Func):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/dom-1/sqlglot/parser.py", "offset": 7840, "limit": 130}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/dom-1/sqlglot/generator.py", "offset": 3536, "limit": 12}
[tool_result] 3536	            escaped = expression.replace('"', '\\"')
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/dom-1/sqlglot/generator.py", "offset": 3617, "limit": 15}
[tool_result] 3617	        return self.func("COLUMNS", *expression.expressions)
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
[tool_use Bash] {"command": "grep -n -A30 \"def test_json_table\" tests/dialects/test_oracle.py; grep -n -B2 -A12 \"JSON_TABLE\" tests/dialects/test_mysql.py | head -60", "description": "Show existing JSON_TABLE tests for Oracle and MySQL"}
[tool_result] 557:    def test_json_table(self):
558-        self.validate_identity(
559-            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
560-        )
561-        self.validate_identity(
562-            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
563-            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))",
564-        )
565-
…[2203 chars elided]…
 BY BINARY a", "SELECT * FROM x ORDER BY CAST(a AS BINARY)"
303-        )
304-        self.validate_identity(
305-            """SELECT * FROM foo WHERE 3 MEMBER OF(JSON_EXTRACT(info, '$.value'))"""
306-        )
307-        self.validate_identity(
308-            "SELECT * FROM t1, t2, t3 FOR SHARE OF t1 NOWAIT FOR UPDATE OF t2, t3 SKIP LOCKED"
309-        )
310-        self.validate_identity(
311-            "REPLACE INTO table SELECT id FROM table2 WHERE cnt > 100", check_command_warning=True
[assistant] The shared parser already calls `_parse_format_json` on the input, so I need to reproduce the failure before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n]:\n  for d in ['oracle','mysql']:\n    try: print(d, sqlglot.transpile(s, read=d, write=d)[0])\n    except Exception as e: print(d, 'ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
mysql SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
oracle SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
mysql SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id')) AS jt
oracle SELECT JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
mysql SELECT JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id DECIMAL PATH '$.id'))
[assistant] The basic form parses on both Oracle and MySQL. I'll try more variants to find the one that actually fails.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id') ERROR ON ERROR)\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.item
…[500 chars elided]…
H '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id' FORMAT JSON))\\\",\n]\nfor s in cases:\n  try: print('OK ', sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:200].replace(chr(10),' '), '\\n    ', s)\n\"", "description": "Try more JSON_TABLE FORMAT JSON variants"}
[tool_result] OK  SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 95.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id') ERROR [4mON[0m ERROR) 
     SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id') ERROR ON ERROR)
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR NULL ON EMPTY COLUMNS(id NUMBER PATH '$.
…[356 chars elided]…

OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.a[*]' COLUMNS(x PATH '$.x')))
OK  SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.a') FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id'))
ERR ParseError Expecting ). Line 1, Col: 92.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [4mFORMAT[0m JSON)) 
     SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' FORMAT JSON))
[assistant] Most variants pass. The failures so far are an `ENCODING` clause, which the issue doesn't mention, and `FORMAT JSON` on a column, which isn't valid Oracle syntax. I'll check the remaining input shapes and casing.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n \\\"SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"select * from json_table(doc format json, '\\$.items[*]' columns (
…[374 chars elided]…
\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n]\nfor s in cases:\n  try: print('OK ', sqlglot.transpile(s, read='oracle', write='oracle')[0])\n  except Exception as e: print('ERR', str(e)[:120].replace(chr(10),' '), '|', s)\n\"; git -C . log --oneline -3 -- sqlglot/parser.py | cat", "description": "Test bind, literal, casing and join variants"}
[tool_result] OK  SELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE('{}' FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM t JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON 1 = 1
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
[assistant] Every form of the issue's example parses and round-trips here. I'll check whether the bug is already fixed upstream, look for an Oracle-specific override, and run the existing JSON_TABLE tests.
[tool_use Bash] {"command": "git log --oneline -i --grep=\"json_table\\|json table\\|FORMAT JSON\" | head; grep -n -i \"json\" sqlglot/dialects/oracle.py | head -30; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_mysql.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one(\\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\", read='oracle')\nprint(repr(e.find(exp.JSONTable).this))\nprint(e.sql('oracle', pretty=True))\n\"", "description": "Check history, Oracle overrides, and run related tests"}
[tool_result] 5edc846cb Fix(mysql): move parsing logic for JSON_TABLE to base parser (#2387)
7be3c14e6 Fix(oracle): make parentheses in JSON_TABLE's COLUMNS clause optional
7c407d4b7 Feat(oracle): add support for JSON_TABLE (#2191)
ba9a1283b Feat!(oracle): refactor parsing of 'FORMAT JSON', add support for J...
...........................................................................                        [100%]
75 passed, 694 subtests passed in 0.37s
FormatJson(
  this=Column(
    this=Identifier(this=doc, quoted=False),
    join_mark=False))
SELECT
  *
FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] The existing tests pass and the parsed tree is correct. I'll check whether a compiled extension is shadowing the Python source, since that could produce a failure the pure-Python path doesn't show.
[tool_use Bash] {"command": "find . -name \"*.so\" -not -path \"./.git/*\" | head; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\"; git status --short | head", "description": "Check for compiled extensions and clean tree"}
[tool_result] ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/dom-1/sqlglot/__init__.py
ok
[assistant] I could not reproduce this, so I made no code changes.

**Result:** On the current checkout, `JSON_TABLE` with `FORMAT JSON` on the input already parses and round-trips in the Oracle dialect. This includes the exact shape from the report:

```
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
→ SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
```

I also checked these, and all parse:
- a qualified column (`t.doc`), a bind variable (`:doc`), and a string literal as the input
- an alias (`jt`), a JOIN, lowercase keywords
…[718 chars elided]…
SON` on a column is not parsed. I didn't treat this as in scope, since the report is about the input expression.
- `... COLUMNS (...) ERROR ON ERROR)`: the error clause placed after `COLUMNS` is rejected. Oracle puts it before `COLUMNS`, so this input is not valid Oracle anyway.

If one of these is what you hit, or you have a failing statement from another environment, send it and I'll reproduce it against that. I'd expect a fix to go in `_parse_json_table` in the shared parser, plus a case in `test_json_table`. That would also affect MySQL, which shares the parser.

The working tree is clean.
