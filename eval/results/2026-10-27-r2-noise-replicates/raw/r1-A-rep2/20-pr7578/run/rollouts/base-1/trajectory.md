# trajectory base-1

final message:
I didn't change any code, because the case you described already parses and round-trips on this base commit.

**What I checked**
- `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` parses on the Oracle dialect and generates the same SQL back. The generic parser already handles `FORMAT JSON` on the input expression in `_parse_json_table` (`sqlglot/parser.py:7951`), and `jsontable_sql` writes it back out.
- `tests/dialects/test_oracle.py::test_json_table` already covers `JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(...))`. All 25 Oracle tests pass (213 subtests).
- I also tried qualified columns, binds, quoted identifiers, `CAST(...)`/function inputs, joins, `ERROR ON ERROR` and `NULL ON ERROR`, `WHERE`, and table aliases. All of these pass.

**What does fail**

The `FORMAT JSON` and `EXISTS` clauses on column definitions inside `COLUMNS (...)` don't parse:
- `COLUMNS (id VARCHAR2(4000) FORMAT JSON PATH '$.id')`
- `COLUMNS (id NUMBER EXISTS PATH '$.id')`
- `COLUMNS (id NUMBER PATH '$.id' ERROR ON ERROR)`

Oracle accepts all three. `_parse_json_column_def` (`sqlglot/parser.py:7922`) only handles `name [FOR ORDINALITY] type [PATH 'x']` and nested paths. Fixing this means adding new args to `exp.JSONColumnDef` and matching generator output. I can do that if it's what you meant.

If your failing query looks different from all of the above, send me the exact SQL and I'll reproduce it against this commit.

## events
[tool_use Bash] {"command": "grep -n -i \"json_table\\|JSONTable\\|FORMAT JSON\\|format_json\\|JSONFormat\" sqlglot/dialects/oracle.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Search for JSON_TABLE and FORMAT JSON handling"}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-232448-oracle-dialect-json-table-fails/base-1/sqlglot/parser.py", "offset": 7840, "limit": 130}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-232448-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py", "offset": 3535, "limit": 15}
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-232448-oracle-dialect-json-table-fails/base-1/sqlglot/generator.py", "offset": 3615, "limit": 20}
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
[assistant] The generic parser already calls `_parse_format_json` in `_parse_json_table`, so the failure is somewhere else. Reproducing it first.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nsql = \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id', name VARCHAR2(10) PATH '\\$.name')) t\\\"\nfor d in ['oracle', 'sqlglot']:\n    try:\n        e = sqlglot.parse_one(sql, read='oracle')\n        print(d, repr(e.args['from_'].this if 'from_' in e.args else e.args))\n        print(e.sql(dialect='oracle'))\n    except Exception as ex:\n        print(d, 'ERR', type(ex).__name__, ex)\n    break\n\" 2>&1 | head -40; grep -n -i \"json_table\\|JSONTable\" sqlglot/dialects/oracle.py", "description": "Reproduce JSON_TABLE FORMAT JSON parse failure"}
[tool_result] oracle Table(
  this=JSONTable(
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
          ordinality=False),
        JSONColumnDef(
          this=Identifier(this=name, quoted=False),
          kind=DataT
…[2 chars elided]…
e(
            this=DType.VARCHAR,
            expressions=[
              DataTypeParam(
                this=Literal(this=10, is_string=False))],
            nested=False),
          path=Literal(this='$.name', is_string=True),
          ordinality=False)]),
    path=Literal(this='$.items[*]', is_string=True)),
  alias=TableAlias(
    this=Identifier(this=t, quoted=False)))
SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', name VARCHAR2(10) PATH '$.name')) t
[assistant] The plain case parses and round-trips. Trying variants (qualified column, function input, error clauses, nested paths) to find the real failing shape.
[tool_use Bash] {"command": "cat > /tmp/jt_probe.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(TO_CLOB(x) FORMAT JSON, '$.a' COLUMNS (id NUMBER PATH '$.id'))\",\n \"SELECT * FROM JSON_TABLE(doc FORMAT JS
…[595 chars elided]…
qlglot.parse_one(sql, read='oracle')\n        out = e.sql(dialect='oracle')\n        print('OK ', out == sql, out)\n    except Exception as ex:\n        print('ERR', type(ex).__name__, str(ex).splitlines()[0], '|', sql)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -I /tmp/jt_probe.py", "description": "Probe JSON_TABLE FORMAT JSON variants on Oracle"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/jt_probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/jt_probe.py", "description": "Run JSON_TABLE variant probe script"}
[tool_result] OK  False SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  False SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK  False SELECT * FROM JSON_TABLE(TO_CLOB(x) FORMAT JSON, '$.a' COLUMNS(id NUMBER PATH '$.id'))
OK  False SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 77. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON ERROR EMPTY ON EMPTY COLUMNS (id NUMBER PATH '$.id'))
OK  False SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS(y NUMBER PATH '$.y')))
ERR ParseError Expecting ). Line 1, Col: 104. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id FOR ORDINALITY, v VARCHAR2(20) FORMAT JSON PATH '$.v'))
OK  False SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
[assistant] Most `FORMAT JSON` shapes already parse. The one real error is my own invalid input (`EMPTY ON EMPTY`). Checking existing Oracle tests and any Oracle-specific overrides to find the shape that actually fails.
[tool_use Bash] {"command": "grep -rn -i \"json_table\" tests/ | head -30; echo ---; grep -n -i \"format\\|json\" sqlglot/dialects/oracle.py | head -40; echo ---; git log --oneline -3 -- sqlglot/parser.py | cat", "description": "Find JSON_TABLE tests and Oracle JSON overrides"}
[tool_result] tests/dialects/test_oracle.py:557:    def test_json_table(self):
tests/dialects/test_oracle.py:559:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))"
tests/dialects/test_oracle.py:562:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')",
tests/dialects/test_oracle.py:563:            "SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo
…[580 chars elided]…
BLE(source.links, '$.org[*]' COLUMNS(row_id FOR ORDINALITY, link VARCHAR(255) PATH '$.link')) AS links"
---
28:    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
47:        "FF6": "%f",  # only 6 digits are supported in python formats
---
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
[assistant] The existing Oracle test already covers `JSON_TABLE(foo FORMAT JSON, ...)`. Let me look at that test and run it to see whether the current code passes.
[tool_use Bash] {"command": "sed -n 555,600p tests/dialects/test_oracle.py; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -15", "description": "Show Oracle JSON_TABLE test and run Oracle tests"}
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
…[786 chars elided]…
_id = manager_id AND LEVEL <= 4"
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
.........................                                                   [100%]
25 passed, 213 subtests passed in 0.23s
[assistant] All 25 Oracle tests pass on the base commit, so the reported shape must be narrower. Broadening the probe to joins, binds, quoted identifiers, casts, pretty output, and the `ERROR ON ERROR` clause ordering.
[tool_use Bash] {"command": "cat > /tmp/jt_probe2.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) jt\",\n \"SELECT jt.id FROM t INNER JOIN JSON_TABLE(:doc FORMAT JSON, '$[*]' COLUMNS (id NUMBER PATH '$.id')) jt ON t.id = jt.id\",\n \"SELECT * FROM JSON_TABLE(\\\"DOC\\\" FORMAT JSON, '$' COLUMNS (id NUMBER PATH '$.id'))\",\n \"S
…[1084 chars elided]…
')) t\",\n]\nfor sql in cases:\n    try:\n        e = sqlglot.parse_one(sql, read='oracle')\n        print('OK ', e.sql(dialect='oracle'))\n    except Exception as ex:\n        print('ERR', str(ex).splitlines()[0], '|', sql)\nEOF\nPYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/jt_probe2.py", "description": "Probe broader JSON_TABLE shapes on Oracle"}
[tool_result] OK  SELECT * FROM t, JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK  SELECT jt.id FROM t INNER JOIN JSON_TABLE(:doc FORMAT JSON, '$[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON t.id = jt.id
OK  SELECT * FROM JSON_TABLE("DOC" FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(CAST(x AS CLOB) FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id'))
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.i
…[517 chars elided]…
]' COLUMNS (id NUMBER PATH '$.id' ERROR ON ERROR)) t
ERR Expecting ). Line 1, Col: 88. | SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id VARCHAR2(4000) FORMAT JSON PATH '$.id')) t
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) WHERE 1 = 1
OK  SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) t(a)
OK  SELECT * FROM JSON_TABLE(JSON_QUERY(doc, '$.x') FORMAT JSON, '$' COLUMNS(id NUMBER PATH '$.id')) t
[assistant] Every `FORMAT JSON` on the input expression parses and round-trips. The failures are all inside column definitions (`datatype FORMAT JSON`, `EXISTS`, column-level `ERROR ON ERROR`), which Oracle does allow. Checking whether the base commit touched these paths before deciding scope.
[tool_use Bash] {"command": "git show --stat HEAD | head -20; git status --short | head; grep -n \"class JSONColumnDef\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -30; grep -rn \"def jsoncolumndef_sql\" -A 25 sqlglot/generator.py", "description": "Check base commit changes and JSONColumnDef definition"}
[tool_result] commit 5877b127db81564ed92756395a4eb5877f516719
Author: lithify <lithify@localhost>
Date:   Tue Oct 27 23:24:48 2026 +0200

    lithify: probe base

 .lithify/config.toml | 46 ----------------------------------------------
 1 file changed, 46 deletions(-)
sqlglot/expressions/query.py:1952:class JSONColumnDef(Expression):
sqlglot/expressions/query.py-1953-    arg_types = {
sqlglot/expressions/query.py-1954-        "this": False,
sqlglot/expressions/query.py-1955-        "kind": False,
sqlglot/exp
…[1790 chars elided]…
rator.py-3621-        path = self.sql(expression, "path")
sqlglot/generator.py-3622-        path = f", {path}" if path else ""
sqlglot/generator.py-3623-        error_handling = expression.args.get("error_handling")
sqlglot/generator.py-3624-        error_handling = f" {error_handling}" if error_handling else ""
sqlglot/generator.py-3625-        empty_handling = expression.args.get("empty_handling")
sqlglot/generator.py-3626-        empty_handling = f" {empty_handling}" if empty_handling else ""
[tool_use Bash] {"command": "rm -f /tmp/jt_probe.py /tmp/jt_probe2.py; echo done", "description": "Remove temporary probe scripts"}
[tool_result] done
[assistant] I didn't change any code, because the case you described already parses and round-trips on this base commit.

**What I checked**
- `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))` parses on the Oracle dialect and generates the same SQL back. The generic parser already handles `FORMAT JSON` on the input expression in `_parse_json_table` (`sqlglot/parser.py:7951`), and `jsontable_sql` writes it back out.
- `tests/dialects/test_oracle.py::test_json_table` already covers `JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(...))`. All 25 Oracle tests pass (213 subtests)
…[254 chars elided]…
definitions inside `COLUMNS (...)` don't parse:
- `COLUMNS (id VARCHAR2(4000) FORMAT JSON PATH '$.id')`
- `COLUMNS (id NUMBER EXISTS PATH '$.id')`
- `COLUMNS (id NUMBER PATH '$.id' ERROR ON ERROR)`

Oracle accepts all three. `_parse_json_column_def` (`sqlglot/parser.py:7922`) only handles `name [FOR ORDINALITY] type [PATH 'x']` and nested paths. Fixing this means adding new args to `exp.JSONColumnDef` and matching generator output. I can do that if it's what you meant.

If your failing query looks different from all of the above, send me the exact SQL and I'll reproduce it against this commit.
