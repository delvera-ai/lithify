# trajectory comp-1

final message:
The reported statement already parses in this checkout, so I made no code changes. I could not reproduce the failure, and I couldn't confirm Oracle grammar for the one variant that does fail.

**Probe results** (`oracle` dialect, `.lithify/harness/scripts/probe_parse.py`):

| Statement | Result |
|---|---|
| `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt` (the report's form) | OK |
| `JSON_TABLE(t.doc FORMAT JSON, ...)`, `JSON_TABLE(:doc FORMAT JSON, ...)`, `JSON_TABLE(CAST(x AS CLOB) FORMAT JSON, ...)` | OK |
| `JSON_TABLE(doc FORMAT JSON, ... ERROR ON ERROR COLUMNS (...))` and `... NULL ON EMPTY COLUMNS (...)` | OK |
| `FROM t JOIN JSON_TABLE(t.doc FORMAT JSON, ...) AS jt ON 1 = 1` | OK |
| `JSON_TABLE(doc, ...)` without FORMAT JSON | OK |
| `JSON_TABLE(doc FORMAT JSON ENCODING UTF8, ...)` | **ERR**, unexpected token at `ENCODING` |
| `JSON_TABLE(doc FORMAT JSON, ... COLUMNS (... ) ERROR ON ERROR)` (error clause after COLUMNS) | **ERR**, out of scope: Oracle places it before COLUMNS, and the OK form above is that placement |
| `COLUMNS (id NUMBER PATH '$.id' NULL ON ERROR)` (column-level handling) | **ERR**, out of scope: a column-level clause, not the input's FORMAT JSON |
| `JSON_EXISTS(doc FORMAT JSON ENCODING UTF8, '$.a')` | **ERR**, outside JSON_TABLE, out of scope |

**Existing coverage:** `tests/dialects/test_oracle.py` already has `SELECT * FROM JSON_TABLE(foo FORMAT JSON, 'bla' ERROR ON ERROR NULL ON EMPTY COLUMNS(foo PATH 'bar'))` (line 559). `pytest -k json` on that file passes (2 passed, 16 subtests).

**Why I didn't add `ENCODING`:** It is the only in-scope-looking failure, but I could not establish that Oracle's JSON_TABLE grammar allows `FORMAT JSON ENCODING`. The Oracle pages I found ([JSON_TABLE, 18c](https://docs.oracle.com/en/database/oracle/oracle-database/18/adjsn/function-JSON_TABLE.html), [COLUMNS clause, 23](https://docs.oracle.com/en/database/oracle/oracle-database/23/adjsn/columns-clause-sql-json-function-json_table.html)) did not show it. The only grammar I found was a MariaDB ticket quoting the SQL standard, which is not Oracle documentation. Changing the shared `_parse_format_json` helper would also loosen JSON_OBJECT, JSON_ARRAY and JSON_EXISTS, so I left it alone.

**Next step:** Could you send the exact statement that fails for you, and the error text? If it's the `ENCODING` form, confirm it against your Oracle release's `format_clause` reference and I'll add it, scoped to JSON_TABLE.

## events
[tool_use Skill] {"skill": "parse-failure-triage", "args": "Oracle JSON_TABLE fails to parse when the input expression carries FORMAT JSON, e.g. JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)). Support FORMAT JSON so it parses and round-trips."}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144515-oracle-dialect-json-table-fails/comp-1/.claude/skills/parse-failure-triage

# Parse failure triage and syntax changes

Locations of the code are in memory.md. Shared syntax goes in the base parser or generator, because every dialect inherits it. Dialect-only behaviour goes in that dialect's own module (for example `sqlglot/parsers/oracle.py`).

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the repository, one statement per line, and probe it:
   `PYTHONPATH=$
…[1422 chars elided]…
 the probe. Every in-scope line must read OK; out-of-scope ERR lines stay and are listed. Then run the dialect's test file, then the full suite (command in memory.md), and read its output. You are done when the in-scope lines read OK and the full suite exits 0.

7. If nothing in scope reproduces, say so and quote the probe output for every variant you tried. Do not change code on speculation.


ARGUMENTS: Oracle JSON_TABLE fails to parse when the input expression carries FORMAT JSON, e.g. JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...)). Support FORMAT JSON so it parses and round-trips.
[tool_use Bash] {"command": "grep -n \"_parse_json_table\\|_parse_format_json\\|JSON_TABLE\" sqlglot/parser.py sqlglot/parsers/oracle.py sqlglot/generator.py sqlglot/expressions/json.py sqlglot/expressions/query.py", "description": "Locate JSON_TABLE and FORMAT JSON parsing code"}
[tool_result] 10 matches in 3 files:

sqlglot/generator.py:3629:"JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/parser.py:1504:"JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7845:def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
sqlglot/parser.py:7894:else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_val...
sqlglot/parser.py:7906:return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:7951:def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7952:this = self._parse_format_json(self._parse_bitwise())
sqlglot/parsers/oracle.py:116:expressions=self._parse_csv(lambda: self._parse_format_json(self._parse_bitwi...
sqlglot/parsers/oracle.py:122:this=self._parse_format_json(self._parse_bitwise()),
sqlglot/parsers/oracle.py:171:this = self._parse_format_json(self._parse_bitwise())
[assistant] Skill loaded. Next I'll reproduce the failure with the probe script and read the JSON parsing code.
[tool_use Bash] {"command": "mkdir -p /tmp/oracle-fj && cat > /tmp/oracle-fj/stmts.sql <<'EOF'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt\nSELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt\nSELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt\nSELECT * FROM JSON_TABLE(:doc FORMAT JSON, '$
…[349 chars elided]…
id') ERROR ON ERROR) AS jt\nSELECT * FROM t JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt ON 1 = 1\nEOF\nPYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read oracle < /tmp/oracle-fj/stmts.sql 2>&1 | head -60", "description": "Probe FORMAT JSON variants in Oracle JSON_TABLE"}
[tool_result] OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK        SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt
          SELECT * FROM JSON_TABLE(doc, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK        SELECT * FROM JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt
          
…[659 chars elided]…
Error: Invalid expression / Unexpected token. Line 1, Col: 101.
ERR       SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id') ERROR ON ERROR) AS jt
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 95.
OK        SELECT * FROM t JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt ON 1 = 1
          SELECT * FROM t JOIN JSON_TABLE(t.doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt ON 1 = 1
[tool_use Bash] {"command": "sed -n 7840,7990p sqlglot/parser.py", "description": "Read FORMAT JSON and JSON_TABLE parser code"}
[tool_result]         if not key and not value:
            return None
        return self.expression(exp.JSONKeyValue(this=key, expression=value))

    def _parse_format_json(self, this: exp.Expr | None) -> exp.Expr | None:
        if not this or not self._match_text_seq("FORMAT", "JSON"):
            return this

        return self.expression(exp.FormatJson(this=this))

    def _parse_on_condition(self) -> exp.OnCondition | None:
        # MySQL uses "X ON EMPTY Y ON ERROR" (e.g. JSON_VALUE) while Oracle 
…[4763 chars elided]…
      if self._match_text_seq("IN", "NATURAL", "LANGUAGE", "MODE"):
            modifier = "IN NATURAL LANGUAGE MODE"
            if self._match_text_seq("WITH", "QUERY", "EXPANSION"):
                modifier = f"{modifier} WITH QUERY EXPANSION"
        elif self._match_text_seq("IN", "BOOLEAN", "MODE"):
            modifier = "IN BOOLEAN MODE"
        elif self._match_text_seq("WITH", "QUERY", "EXPANSION"):
            modifier = "WITH QUERY EXPANSION"
        else:
            modifier = None
[tool_use Bash] {"command": "sed -n 100,185p sqlglot/parsers/oracle.py", "description": "Read Oracle JSON parser overrides"}
[tool_result]     def _parse_dbms_random(self) -> exp.Expr | None:
        if self._match_text_seq(".", "VALUE"):
            lower, upper = None, None
            if self._match(TokenType.L_PAREN, advance=False):
                lower_upper = self._parse_wrapped_csv(self._parse_bitwise)
                if len(lower_upper) == 2:
                    lower, upper = lower_upper

            return exp.Rand(lower=lower, upper=upper)

        self._retreat(self._index - 1)
        return None

    def _parse_oracl
…[2086 chars elided]…
      path=self.dialect.to_json_path(self._parse_bitwise()),
                passing=self._match_text_seq("PASSING")
                and self._parse_csv(lambda: self._parse_alias(self._parse_bitwise())),
                on_condition=self._parse_on_condition(),
            )
        )

    def _parse_into(self) -> exp.Into | None:
        # https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/SELECT-INTO-statement.html
        bulk_collect = self._match(TokenType.BULK_COLLECT_INTO)
[assistant] The reported statement already parses in this checkout, so the bug may be in a variant. Next I'll check the existing tests, the FORMAT JSON generator, and the correct placement of the error clause.
[tool_use Bash] {"command": "cat > /tmp/oracle-fj/stmts2.sql <<'EOF'\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS (id NUMBER PATH '$.id')) AS jt\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON EMPTY COLUMNS (id NUMBER PATH '$.id')) AS jt\nSELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' NULL ON ERROR)) AS jt\nSELECT * FROM JSON
…[355 chars elided]…
---\ngrep -n \"FORMAT JSON\\|ENCODING\" tests/dialects/test_oracle.py | head -40\necho ---\ngrep -n \"def formatjson_sql\\|def jsontable_sql\" -A 12 sqlglot/generator.py\necho ---\ngrep -n \"class FormatJson\\|class JSONTable\" -A 6 sqlglot/expressions/*.py\necho ---\ngit log --oneline -5 -- sqlglot/parser.py | cat", "description": "Probe placement and ENCODING variants; read tests and generator"}
[tool_result] OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS (id NUMBER PATH '$.id')) AS jt
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id')) jt
OK        SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON EMPTY COLUMNS (id NUMBER PATH '$.id')) AS jt
          SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' NULL ON EMPTY COLUMNS(id NUMBER PATH '$.id')) jt
ERR       SELECT * FROM JSON_TABLE
…[3201 chars elided]…
947-
sqlglot/expressions/query.py-1948-class JSONKeyValue(Expression):
sqlglot/expressions/query.py-1949-    arg_types = {"this": True, "expression": True}
sqlglot/expressions/query.py-1950-
---
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
fc6e7cb09 perf(parser): short-circuit _parse_pivots when next token isn't PIVOT/UNPIVOT (#7557)
dc461daa9 Fixup
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
[assistant] The reported form already parses and is covered by an existing test. The remaining failing variants are `ENCODING` after `FORMAT JSON` and a column-level `NULL ON ERROR`, which is out of scope. Before deciding on `ENCODING`, I'll check Oracle's grammar for it.
[tool_use ToolSearch] {"query": "select:WebSearch", "max_results": 1}
[tool_result] 
[tool_use WebSearch] {"query": "Oracle JSON_TABLE \"FORMAT JSON\" ENCODING syntax format_clause", "mode": "standard"}
[tool_result] Web search results for query: "Oracle JSON_TABLE "FORMAT JSON" ENCODING syntax format_clause"

Links: [{"title":"17 SQL/JSON Function JSON_TABLE","url":"https://docs.oracle.com/en/database/oracle/oracle-database/18/adjsn/function-JSON_TABLE.html"},{"title":"DEV Community","url":"https://dev.to/rmaurodev/oracle-jsontable-transforming-json-into-relational-format-2kg5"},{"title":"Mastering JSON in Oracle Database: Types, Functions, Indexing, and Best Practices","url":"https://www.cleverence.com/art
…[3325 chars elided]…
ptional PATH. The same section notes that Oracle extends the SQL/JSON standard in the case when the returning data type for a column is VARCHAR2(N), by allowing optional keyword TRUNCATE.

For the exact `format_clause` syntax, the best next step is Oracle's JSON_TABLE reference page for your release (for example, the 23 or 26 "function-JSON_TABLE" page), which I could not retrieve in full here.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] The search did not establish Oracle's `ENCODING` grammar for JSON_TABLE, so I won't add it on guesswork. I'll run the Oracle test file to confirm the current state.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py -k json 2>&1 | tail -5; echo \"exit=$?\"; git status --short", "description": "Run Oracle JSON tests and confirm clean tree"}
[tool_result] ..                                                       [100%]
2 passed, 23 deselected, 16 subtests passed in 0.12s
exit=0
ok
[assistant] The reported statement already parses in this checkout, so I made no code changes. I could not reproduce the failure, and I couldn't confirm Oracle grammar for the one variant that does fail.

**Probe results** (`oracle` dialect, `.lithify/harness/scripts/probe_parse.py`):

| Statement | Result |
|---|---|
| `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id')) AS jt` (the report's form) | OK |
| `JSON_TABLE(t.doc FORMAT JSON, ...)`, `JSON_TABLE(:doc FORMAT JSON, ...)`, `JSON_TABLE(CAST(x AS CLOB) FORMAT JSON, ...)` | OK |
| `JSON_TABLE(doc FORMAT JSON, ... ERROR ON ERROR 
…[1295 chars elided]…
 23](https://docs.oracle.com/en/database/oracle/oracle-database/23/adjsn/columns-clause-sql-json-function-json_table.html)) did not show it. The only grammar I found was a MariaDB ticket quoting the SQL standard, which is not Oracle documentation. Changing the shared `_parse_format_json` helper would also loosen JSON_OBJECT, JSON_ARRAY and JSON_EXISTS, so I left it alone.

**Next step:** Could you send the exact statement that fails for you, and the error text? If it's the `ENCODING` form, confirm it against your Oracle release's `format_clause` reference and I'll add it, scoped to JSON_TABLE.
