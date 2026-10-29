# trajectory inv-1

final message:
`JSON_TABLE` now accepts `FORMAT JSON ENCODING <x>` on the input, and it round-trips. The full suite reports 1096 passed with no failures.

The statement in the report, `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, already parsed and round-tripped before my change. The failing variant was the one with `ENCODING` after `FORMAT JSON`, which hit a parse error at the `ENCODING` token.

**Change**
- `sqlglot/parser.py` `_parse_json_table`: parses an optional `ENCODING <var>` right after the input expression.
- `sqlglot/expressions/json.py` `JSONTable`: new optional `encoding` arg.
- `sqlglot/generator.py` `jsontable_sql`: emits ` ENCODING <x>` directly after the input.
- `tests/dialects/test_oracle.py` `test_json_table`: one added `validate_identity` case for `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)`.

**Choices I made**
- I put `encoding` on `JSONTable` rather than on `FormatJson` or in the shared `_parse_format_json`. That helper is also used by `JSON_OBJECT ... RETURNING ... FORMAT JSON ENCODING`, and changing it would move that clause onto a different node and could skip Singlestore's unsupported-arg check for `JSONObject.encoding`. `JSONObject` already has an `encoding` arg, so this follows its pattern.
- `ENCODING` is parsed without requiring `FORMAT JSON` first, so `JSON_TABLE(doc ENCODING UTF8, ...)` also parses and emits. Oracle's grammar only allows it after `FORMAT JSON`. I left that looser because it is harmless here.

**Probe results after the fix (oracle)**
All lines OK: `FORMAT JSON` with a bare column, qualified column, bind variable, `JSON_QUERY(...)`, `CAST(...)`, and a literal; the `ENCODING UTF8` variant; `ERROR ON ERROR NULL ON EMPTY`; JOIN; CTE; subquery; and nested `COLUMNS`. Before the fix, the only ERR was the `ENCODING` variant.

**Checks**
- `tests/dialects/test_oracle.py`: 25 passed.
- Full suite: 1096 passed, 17880 subtests passed. My shell did not capture the process exit code, but the output shows no failures.
- I did not run `make style` (ruff/mypy). The test changes are not committed.

**Setup note**
`probe_parse.py` fails under `python -I` with `No module named 'sqlglot'`, because `-I` drops the working directory from `sys.path`. I ran it with `PYTHONPATH=$PWD` on the CLAUDE.md interpreter instead. The memory file the skill points to is empty.

## events
[tool_use Skill] {"skill": "parse-failure-triage"}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/.claude/skills/parse-failure-triage

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: input 
…[510 chars elided]…
s
   fix: list it in your final message.

4. Add a case for each fixed statement to the existing test function for that dialect, using the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.

[tool_use Bash] {"command": "ls .lithify/harness/scripts/ && grep -rn \"JSON_TABLE\\|JSONTable\\|JsonTable\" sqlglot/ | head -40 && grep -n \"FORMAT JSON\\|JSON_TABLE\\|json_table\" tests/dialects/test_oracle.py | head", "description": "Locate JSON_TABLE handling and existing tests"}
[tool_result] probe_parse.py  2.2K
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/expressions/json.py:202:class JSONTable(Expression, Fun
…[96 chars elided]…
 COLUMNS(empno NUMBER PATH '$')) jt
694:0:
tests/dialects/test_oracle.py:81:"SELECT JSON_ARRAY(FOO() FORMAT JSON, BAR() NULL ON NULL RETURNING CLOB STRICT)"
tests/dialects/test_oracle.py:84:"SELECT JSON_ARRAYAGG(FOO() FORMAT JSON ORDER BY bar NULL ON NULL RETURNING C...
tests/dialects/test_oracle.py:559:"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY...
tests/dialects/test_oracle.py:562:"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY...
[tool_use Bash] {"command": "cat .lithify/harness/scripts/probe_parse.py; sed -n 7940,7975p sqlglot/parser.py; sed -n 3615,3635p sqlglot/generator.py; sed -n 200,215p sqlglot/expressions/json.py; sed -n 550,575p tests/dialects/test_oracle.py; grep -n \"_parse_format_json\\|def _parse_json_column_def\\|FORMAT JSON\\|def _parse_json_\" sqlglot/parser.py | head -30", "description": "Read probe script, JSON table parser, generator, tests"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[5366 chars elided]…
lidate_identity(
            """SELECT
13 matches in 12 files:

6343:0:
7834:0:
7845:0:exp.Expr | None) -> exp.Expr | None:
7884:0:t.Literal[False]) -> exp.JSONObject: ...
7887:0:t.Literal[True]) -> exp.JSONObjectAgg: ...
7889:0:
7894:0:self._parse_format_json(self._parse_json_key_value()))
7922:0:
7943:0:
7951:0:
9828:0:
sqlglot/parser.py:7906:return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7952:this = self._parse_format_json(self._parse_bitwise())
[assistant] The existing tests already cover `FORMAT JSON` on the input, so I'll probe the reported statement and its variants before changing anything.
[tool_use Bash] {"command": "mkdir -p /tmp/jt-probe && cat > /tmp/jt-probe/stmts.sql <<'EOF'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\nSELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\nSELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))\nSELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$.items[*]' COLUMNS (
…[871 chars elided]…
.id')))\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS (y VARCHAR2(10) PATH '$.y')))\nEOF\n<work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read oracle < /tmp/jt-probe/stmts.sql; echo \"exit=$?\"", "description": "Probe JSON_TABLE FORMAT JSON variants on oracle"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit=1
[assistant] The `-I` flag blocks the cwd from being on `sys.path`, so `sqlglot` doesn't import. I'll check the project memory for the interpreter setup.
[tool_use Bash] {"command": "ls ~/.claude/projects/-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-noise-verified-r1-B-rep2-repo/memory/ 2>/dev/null; cat ~/.claude/projects/-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-noise-verified-r1-B-rep2-repo/memory/MEMORY.md 2>/dev/null; ls <work>/env-sqlglot/bin/ | head; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\"", "description": "Check memory notes and sqlglot import location"}
[tool_result] (empty)
activate  4.0K
activate.bat  2.6K
activate.csh  2.6K
activate.fish  4.1K
activate.nu  3.7K
activate.ps1  2.7K
activate_this.py  2.3K
deactivate.bat  1.7K
dmypy  374B
f2py  356B
~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/__init__.py
[assistant] The memory file is empty, so I'm using the interpreter from CLAUDE.md. `-I` drops the working directory from `sys.path`, so I'll run the probe with `PYTHONPATH` pointing at this worktree.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read oracle < /tmp/jt-probe/stmts.sql; echo \"exit=$?\"", "description": "Run JSON_TABLE probe with worktree on path"}
[tool_result] OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK        SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK        SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE
…[1886 chars elided]…
M JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')))
          SELECT * FROM (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')))
OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS (y VARCHAR2(10) PATH '$.y')))
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS(y VARCHAR2(10) PATH '$.y')))
exit=1
[assistant] The reported statement and most variants already parse. The one ERR is `FORMAT JSON ENCODING UTF8`, which has the same shape as the report: `FORMAT JSON` on the input fails. Next I'll look at how `_parse_format_json` handles `ENCODING` and whether any other code path already supports it.
[tool_use Bash] {"command": "grep -rn \"ENCODING\" sqlglot/ | head -20; grep -n \"def _parse_format_json\" -A 12 sqlglot/parser.py; grep -rn \"ENCODING\" tests/ | head", "description": "Find how FORMAT JSON and ENCODING are parsed"}
[tool_result] Binary file sqlglot/__pycache__/generator.cpython-312.pyc matches
Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:7909:        encoding = self._match_text_seq("ENCODING") and self._parse_var()
sqlglot/generator.py:3566:        encoding = f" ENCODING {encoding}" if encoding else ""
7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
7846-        if not this or not self._match_text_seq("FORMAT", "JSON"):
7847-            return this
784
…[529 chars elided]…
 = self._parse_on_handling("ERROR", *self.ON_CONDITION_TOKENS)
tests/dialects/test_tsql.py:67:            "COPY INTO test_1 FROM 'path' WITH (FORMAT_NAME = test, FILE_TYPE = 'CSV', CREDENTIAL = (IDENTITY='Shared Access Signature', SECRET='token'), FIELDTERMINATOR = ';', ROWTERMINATOR = '0X0A', ENCODING = 'UTF8', DATEFORMAT = 'ymd', MAXERRORS = 10, ERRORFILE = 'errorsfolder', IDENTITY_INSERT = 'ON')"
tests/fixtures/identity.sql:836:JSON_OBJECT('x': 1 RETURNING VARBINARY FORMAT JSON ENCODING UTF8)
[tool_use Bash] {"command": "sed -n 7900,7920p sqlglot/parser.py; grep -n \"class FormatJson\" -A 6 sqlglot/expressions/json.py; grep -n \"def formatjson_sql\" -A 8 sqlglot/generator.py; sed -n 3555,3575p sqlglot/generator.py", "description": "Read FormatJson expression, generator, and encoding usage"}
[tool_result]             unique_keys = True
        elif self._match_text_seq("WITHOUT", "UNIQUE"):
            unique_keys = False

        self._match_text_seq("KEYS")

        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
            self._parse_type()
        )
        encoding = self._match_text_seq("ENCODING") and self._parse_var()

        return self.expression(
            (exp.JSONObjectAgg if agg else exp.JSONObject)(
                expressions=expressions,
        
…[1063 chars elided]…
xpression, "return_type")
        return_type = f" RETURNING {return_type}" if return_type else ""
        encoding = self.sql(expression, "encoding")
        encoding = f" ENCODING {encoding}" if encoding else ""

        if not name:
            name = "JSON_OBJECT" if isinstance(expression, exp.JSONObject) else "JSON_OBJECTAGG"

        return self.func(
            name,
            *expression.expressions,
            suffix=f"{null_handling}{unique_keys}{return_type}{encoding})",
        )
[tool_use Bash] {"command": "grep -rn \"class FormatJson\" -A 5 sqlglot/; grep -rn \"FormatJson\" sqlglot/ | grep -v pyc", "description": "Locate FormatJson expression class definition"}
[tool_result] sqlglot/expressions/query.py:1944:class FormatJson(Expression):
sqlglot/expressions/query.py-1945-    pass
sqlglot/expressions/query.py-1946-
sqlglot/expressions/query.py-1947-
sqlglot/expressions/query.py-1948-class JSONKeyValue(Expression):
sqlglot/expressions/query.py-1949-    arg_types = {"this": True, "expression": True}
sqlglot/parser.py:7849:        return self.expression(exp.FormatJson(this=this))
sqlglot/generator.py:3541:    def formatjson_sql(self, expression: exp.FormatJson) -> str:
sqlglot/expressions/query.py:1944:class FormatJson(Expression):
[assistant] `FormatJson` is a bare `Expression` with no args, and `ENCODING` is only parsed inside the `JSON_OBJECT` path. Before I decide where `ENCODING` belongs, I'll check whether any dialect reads the `encoding` arg.
[tool_use Bash] {"command": "grep -rn \"\\\"encoding\\\"\\|\\.args.get(\\\"encoding\\|encoding=\" sqlglot/ --include=*.py | head; grep -rn \"_parse_format_json\" sqlglot/ --include=*.py", "description": "Check consumers of encoding arg and _parse_format_json callers"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -e '\"encoding\"' -e 'encoding=' sqlglot/ ; grep -rn \"_parse_format_json\" sqlglot/", "description": "Check consumers of encoding arg and _parse_format_json callers"}
[tool_result] sqlglot/parsers/postgres.py:114:        "LENGTH": lambda args: exp.Length(this=seq_get(args, 0), encoding=seq_get(args, 1)),
sqlglot/parser.py:7917:                encoding=encoding,
sqlglot/generator.py:3565:        encoding = self.sql(expression, "encoding")
sqlglot/expressions/string.py:70:    arg_types = {"this": True, "binary": False, "encoding": False}
sqlglot/expressions/json.py:162:        "encoding": False,
sqlglot/expressions/json.py:172:        "encoding": False,
sqlglot/generators/si
…[534 chars elided]…
son(self._parse_bitwise())
Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:7845:    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
sqlglot/parser.py:7906:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7952:        this = self._parse_format_json(self._parse_bitwise())
[assistant] Oracle has its own parser module, and line 171 of `sqlglot/parsers/oracle.py` also calls `_parse_format_json`. I'll read that section.
[tool_use Bash] {"command": "sed -n 105,130p sqlglot/parsers/oracle.py; sed -n 160,200p sqlglot/parsers/oracle.py", "description": "Read Oracle parser JSON clauses"}
[tool_result]                 if len(lower_upper) == 2:
                    lower, upper = lower_upper

            return exp.Rand(lower=lower, upper=upper)

        self._retreat(self._index - 1)
        return None

    def _parse_oracle_json_array(self) -> exp.JSONArray:
        return self._parse_json_array(
            exp.JSONArray,
            expressions=self._parse_csv(lambda: self._parse_format_json(self._parse_bitwise())),
        )

    def _parse_oracle_json_arrayagg(self) -> exp.JSONArrayAgg:
 
…[1458 chars elided]…
 if not bulk_collect and not self._match(TokenType.INTO):
            return None

        index = self._index

        expressions = self._parse_expressions()
        if len(expressions) == 1:
            self._retreat(index)
            self._match(TokenType.TABLE)
            return self.expression(
                exp.Into(this=self._parse_table(schema=True), bulk_collect=bulk_collect)
            )

        return self.expression(exp.Into(bulk_collect=bulk_collect, expressions=expressions))
[assistant] The reported statement already parses, so the real gap is `ENCODING` after `FORMAT JSON`. I'm scoping the fix to `JSON_TABLE`: `_parse_format_json` is shared with `JSON_OBJECT RETURNING ... FORMAT JSON ENCODING`, and changing it there would move that clause onto a different node and could hide Singlestore's unsupported-arg check. `JSONTable` already holds its own clause args, and `JSONObject` already has an `encoding` arg, so I'll add `encoding` to `JSONTable` following that pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py", "old_string": "        this = self._parse_format_json(self._parse_bitwise())\n        path = self._match(TokenType.COMMA) and self._parse_string()\n        error_handling = self._parse_on_handling(\"ERROR\", \"ERROR\", \"NULL\")\n      
…[356 chars elided]…
r()\n        path = self._match(TokenType.COMMA) and self._parse_string()\n        error_handling = self._parse_on_handling(\"ERROR\", \"ERROR\", \"NULL\")\n        empty_handling = self._parse_on_handling(\"EMPTY\", \"ERROR\", \"NULL\")\n        schema = self._parse_json_schema()\n\n        return exp.JSONTable(\n            this=this,\n            encoding=encoding,\n            schema=schema,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/expressions/json.py", "old_string": "class JSONTable(Expression, Func):\n    arg_types = {\n        \"this\": True,\n        \"schema\": True,", "new_string": "class JSONTable(Expression, Func):\n    arg_types = {\n        \"this\": True,\n        \"encoding\": False,\n        \"schema\": True,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py", "old_string": "        this = self.sql(expression, \"this\")\n        path = self.sql(expression, \"path\")\n        path = f\", {path}\" if path else \"\"\n        error_handling = expression.args.get(\"error_handling\")", "new_string": "        this = self.sql(expression, \"this\")\n        encoding = self.sql(expression, \"encoding\")\n        encoding = f\" ENCODING {encoding}\" if encoding else \"\"\n        path = self.sql(expression, \"path\")\n        path = f\", {path}\" if path else \"\"\n        error_handling = expression.args.get(\"error_handling\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py has been updated successfully.
[assistant] The generator still needs to place `ENCODING` directly after the input expression, so I'll fold it into the first argument.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py", "old_string": "        return self.func(\n            \"JSON_TABLE\", this, suffix=f\"{path}{error_handling}{empty_handling} {schema})\"\n        )", "new_string": "        return self.func(\n            \"JSON_TABLE\",\n            f\"{this}{encoding}\",\n            suffix=f\"{path}{error_handling}{empty_handling} {schema})\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read oracle < /tmp/jt-probe/stmts.sql; echo \"exit=$?\"", "description": "Re-run JSON_TABLE probe after fix"}
[tool_result] OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK        SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK        SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))
          SELECT * FROM JSON_TABLE
…[1918 chars elided]…
M JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')))
          SELECT * FROM (SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')))
OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS (y VARCHAR2(10) PATH '$.y')))
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id', NESTED PATH '$.x' COLUMNS(y VARCHAR2(10) PATH '$.y')))
exit=0
[assistant] Every probe line now reads OK. I'll add the `ENCODING` case to the existing `test_json_table` using its `validate_identity` style, then run the dialect test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            \
…[199 chars elided]…
ORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS foo PATH 'bar')\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/inv-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -15", "description": "Run Oracle dialect test file"}
[tool_result] .........................                                                   [100%]
25 passed, 213 subtests passed in 0.32s
[assistant] Oracle tests pass. Now the full suite as the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run full test suite", "timeout": 400000}
[tool_result] ........................................................................ [ 32%]
..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 55%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
.....................................
…[19 chars elided]…
................................ [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 62.91s (0:01:02)
exit=
[assistant] `JSON_TABLE` now accepts `FORMAT JSON ENCODING <x>` on the input, and it round-trips. The full suite reports 1096 passed with no failures.

The statement in the report, `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`, already parsed and round-tripped before my change. The failing variant was the one with `ENCODING` after `FORMAT JSON`, which hit a parse error at the `ENCODING` token.

**Change**
- `sqlglot/parser.py` `_parse_json_table`: parses an optional `ENCODING <var>` right after the input expression.
- `sqlglot/expressions/json.py` `JSONTable`: new optional `encoding` arg.
- `s
…[1132 chars elided]…
`COLUMNS`. Before the fix, the only ERR was the `ENCODING` variant.

**Checks**
- `tests/dialects/test_oracle.py`: 25 passed.
- Full suite: 1096 passed, 17880 subtests passed. My shell did not capture the process exit code, but the output shows no failures.
- I did not run `make style` (ruff/mypy). The test changes are not committed.

**Setup note**
`probe_parse.py` fails under `python -I` with `No module named 'sqlglot'`, because `-I` drops the working directory from `sys.path`. I ran it with `PYTHONPATH=$PWD` on the CLAUDE.md interpreter instead. The memory file the skill points to is empty.
