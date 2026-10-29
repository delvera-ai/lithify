# trajectory comp-1

final message:
I didn't change any code. The `FORMAT JSON` form in your report already parses and round-trips on this snapshot, so there is nothing to fix for that case.

Results from `sqlglot.parse_one(sql, read='oracle').sql('oracle')`:

- `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` → round-trips (the generator adds a space before `COLUMNS(`, which is the usual output format, not a change in meaning).
- Same statement with a table alias `jt` → round-trips.
- Same statement with `ERROR ON ERROR` before `COLUMNS` → round-trips.

The other clauses on the known-unsupported list also still fail, but your report doesn't mention them:

- `FORMAT JSON ENCODING UTF8` on the input.
- `EXISTS PATH` on a column.
- Column-level `NULL ON ERROR` after `PATH`.
- Column-level `DEFAULT 'x' ON EMPTY`.
- `FORMAT JSON` on a column.

Your statement may differ from my version in a way that matters. Please send me the exact failing statement, the dialect it's read as, and the commit you're on. If it's one of the failing clauses above, I'll implement that in the shared parser and generator in `sqlglot/parser.py` and `sqlglot/generator.py`, with Oracle tests added to `tests/dialects/test_oracle.py`. I haven't run the test suite, since no edits were made.

## events
[tool_use Skill] {"skill": "sqlglot-json-table"}
[tool_result] Launching skill: sqlglot-json-table
[user] Base directory for this skill: ~/.cache/lithify/work/repo-6e430de19896/20261029-182913-oracle-dialect-json-table-fails/comp-1/.claude/skills/sqlglot-json-table

# JSON_TABLE and FORMAT JSON in sqlglot

## Where the code lives

- `sqlglot/parser.py`: `JSON_TABLE` is registered in `FUNCTION_PARSERS` and calls `_parse_json_table`.
  - `_parse_json_table` reads the input with `_parse_format_json(self._parse_bitwise())`, then the optional path string, then `ERROR ON ERROR` / `NULL ON EMPTY`, then the `COLUMNS(...)` schema.
  - `_parse_format_json` is the shared `<expr> FORMAT JSON` hel
…[1848 chars elided]…
fied (`t.doc`, `s.t.doc`), quoted, `CAST(... AS CLOB)`, bind-variable, string-literal, and `JSON_QUERY(...) FORMAT JSON` forms; `FORMAT JSON` in joins; `ERROR ON ERROR NULL ON EMPTY` before `COLUMNS`; `NESTED PATH` and `FOR ORDINALITY` columns.

Fails with a parse error on that snapshot (not implemented; confirm Oracle's documented syntax before implementing):

- `FORMAT JSON ENCODING UTF8` on the JSON_TABLE input.
- `EXISTS PATH` on a column, e.g. `id NUMBER EXISTS PATH '$.id'`.
- Column-level `NULL ON ERROR` after `PATH`.
- Column-level `DEFAULT '<x>' ON EMPTY`.
- `FORMAT JSON` on a column.

[tool_use Bash] {"command": "cat AGENTS.md; echo ---; grep -rn \"JSON_TABLE\\|JSONTable\\|JSON_TABLE\" sqlglot/ | head -50", "description": "Read AGENTS.md and find JSON_TABLE references"}
[tool_result] # Contributing to [SQLGlot](https://github.com/tobymao/sqlglot/blob/main/README.md)
## About SQLGlot

SQLGlot is a no-dependency SQL parser, transpiler, optimizer, and engine written in pure Python. It supports 31+ SQL dialects and can transpile between them while preserving semantics. The codebase is performance-critical despite being pure Python, with an optional mypyc-compiled C extension for speed improvements (`sqlglotc/`).

## Development Commands
Before contributing read CONTRIBUTING.md


…[18662 chars elided]…
thify:end -->
---
sqlglot/parser.py:1504:        "JSON_TABLE": lambda self: self._parse_json_table(),
sqlglot/parser.py:7951:    def _parse_json_table(self) -> exp.JSONTable:
sqlglot/parser.py:7958:        return exp.JSONTable(
sqlglot/generator.py:3619:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:3629:            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
sqlglot/expressions/json.py:202:class JSONTable(Expression, Func):
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id')) jt\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*
…[88 chars elided]…
qlglot.parse_one(sql, read='oracle').sql('oracle')\n        print('OK  ', out)\n    except Exception as e:\n        print('FAIL', type(e).__name__, str(e)[:300])\n\"; echo; sed -n 7945,7975p sqlglot/parser.py; echo ---; grep -n \"_parse_format_json\" sqlglot/parser.py | head; echo ---; sed -n 3615,3635p sqlglot/generator.py", "description": "Test JSON_TABLE FORMAT JSON forms and view parser code"}
[tool_result] OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id'))
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS(id NUMBER PATH '$.id')) jt
OK   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' ERROR ON ERROR COLUMNS(id NUMBER PATH '$.id'))

        return self.expression(
            exp.JSONSchema(
                expressions=self._parse_wrapped_csv(self._parse_json_column_def, optional=True)
            )
        )

    def _parse_json_tabl
…[1809 chars elided]…
g = expression.args.get("empty_handling")
        empty_handling = f" {empty_handling}" if empty_handling else ""
        schema = self.sql(expression, "schema")
        return self.func(
            "JSON_TABLE", this, suffix=f"{path}{error_handling}{empty_handling} {schema})"
        )

    def openjsoncolumndef_sql(self, expression: exp.OpenJSONColumnDef) -> str:
        this = self.sql(expression, "this")
        kind = self.sql(expression, "kind")
        path = self.sql(expression, "path")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor sql in [\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '\\$.items[*]' COLUMNS (id NUMBER PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER EXISTS PATH '\\$.id'))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT 
…[169 chars elided]…
' DEFAULT 'x' ON EMPTY))\\\",\n \\\"SELECT * FROM JSON_TABLE(doc FORMAT JSON, '\\$.items[*]' COLUMNS (id NUMBER FORMAT JSON PATH '\\$.id'))\\\",\n]:\n    try:\n        print('OK  ', sqlglot.parse_one(sql, read='oracle').sql('oracle'))\n    except Exception as e:\n        print('FAIL', str(e)[:120].replace(chr(10),' '))\n\"", "description": "Check other documented JSON_TABLE variants under Oracle"}
[tool_result] FAIL Invalid expression / Unexpected token. Line 1, Col: 101.   SELECT * FROM JSON_TABLE(doc FORMAT JSON ENCODING UTF8, '$.it
FAIL Expecting ). Line 1, Col: 80.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER [4mEXISTS[0m
FAIL Expecting ). Line 1, Col: 90.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [
FAIL Expecting ). Line 1, Col: 93.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id' [
FAIL Expecting ). Line 1, Col: 80.   SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER [4mFORMAT[0m
[assistant] I didn't change any code. The `FORMAT JSON` form in your report already parses and round-trips on this snapshot, so there is nothing to fix for that case.

Results from `sqlglot.parse_one(sql, read='oracle').sql('oracle')`:

- `SELECT * FROM JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (id NUMBER PATH '$.id'))` → round-trips (the generator adds a space before `COLUMNS(`, which is the usual output format, not a change in meaning).
- Same statement with a table alias `jt` → round-trips.
- Same statement with `ERROR ON ERROR` before `COLUMNS` → round-trips.

The other clauses on the known-uns
…[81 chars elided]…
SON ENCODING UTF8` on the input.
- `EXISTS PATH` on a column.
- Column-level `NULL ON ERROR` after `PATH`.
- Column-level `DEFAULT 'x' ON EMPTY`.
- `FORMAT JSON` on a column.

Your statement may differ from my version in a way that matters. Please send me the exact failing statement, the dialect it's read as, and the commit you're on. If it's one of the failing clauses above, I'll implement that in the shared parser and generator in `sqlglot/parser.py` and `sqlglot/generator.py`, with Oracle tests added to `tests/dialects/test_oracle.py`. I haven't run the test suite, since no edits were made.
