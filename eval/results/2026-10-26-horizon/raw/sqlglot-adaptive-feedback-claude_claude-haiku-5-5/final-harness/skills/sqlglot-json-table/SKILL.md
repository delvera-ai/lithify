---
name: sqlglot-json-table
description: Load when a task touches SQL/JSON syntax in sqlglot — JSON_TABLE (its COLUMNS / NESTED PATH / FOR ORDINALITY column definitions), the FORMAT JSON / ENCODING clauses, JSON_OBJECT / JSON_OBJECTAGG RETURNING, Oracle JSON_ARRAY / JSON_ARRAYAGG / JSON_EXISTS, or T-SQL OPENJSON — including any "fails to parse" report that mentions one of them in any dialect.
---

# SQL/JSON syntax (JSON_TABLE, FORMAT JSON) in sqlglot

## Who owns what (verified in the source)
- `JSON_TABLE` is parsed by the BASE parser, not by a dialect parser:
  `FUNCTION_PARSERS["JSON_TABLE"] -> _parse_json_table` in `sqlglot/parser.py`. Oracle and MySQL
  both go through it (tests: `test_json_table` in `tests/dialects/test_oracle.py`, plus
  `JSON_TABLE` cases in `tests/dialects/test_mysql.py`). A fix there changes every dialect.
- The parse chain in `sqlglot/parser.py`, next to each other:
  `_parse_json_table` (input expr → `, path` → ON ERROR / ON EMPTY → schema) →
  `_parse_json_schema` (`COLUMNS` + wrapped csv) → `_parse_json_column_def` (one column).
  `_parse_json_column_def` carries the comment "currently incomplete; it only implements the
  JSON_value_column part": it parses `name [FOR ORDINALITY] [type] [PATH 'p']` and
  `NESTED [PATH 'p'] COLUMNS(...)`, nothing else.
- Nodes: `exp.JSONTable` (`sqlglot/expressions/json.py`); `exp.JSONSchema`,
  `exp.JSONColumnDef` (args `this, kind, path, nested_schema, ordinality`) and `exp.FormatJson`
  (`sqlglot/expressions/query.py`).
- Generator methods in `sqlglot/generator.py`: `jsontable_sql`, `jsonschema_sql`,
  `jsoncolumndef_sql`, `formatjson_sql`. `jsoncolumndef_sql` emits only the args above, in the
  order `this kind PATH ... FOR ORDINALITY`: a new arg the parser stores is silently dropped
  unless this method prints it.

## INVARIANT: FORMAT JSON has several positions; the helper is shared
`_parse_format_json(this)` (`sqlglot/parser.py`) wraps an already-parsed node in
`exp.FormatJson` when `FORMAT JSON` follows. It is the one helper for this clause; reuse it
rather than matching `FORMAT JSON` by hand. Its callers (grep `_parse_format_json` in
`sqlglot/parser.py` and `sqlglot/parsers/oracle.py`) are:
- the JSON_TABLE input expression (`_parse_json_table`);
- JSON_OBJECT key/values and the `RETURNING <type>` clause (`_parse_json_object`);
- Oracle's `_parse_oracle_json_array`, `_parse_oracle_json_arrayagg` and `_parse_json_exists`
  in `sqlglot/parsers/oracle.py`.
It is NOT called inside `_parse_json_column_def`, so `FORMAT JSON` after a column's type (Oracle's
JSON_query_column form, `name <type> FORMAT JSON PATH '...'`) fails with "Expecting )" at the
`FORMAT` token.

Consequences you can check:
- "JSON_TABLE fails with FORMAT JSON" can mean the input-expression position OR a column
  definition position. Probe `FORMAT JSON` in every position above (input and column def, with
  and without the column type) before choosing what to change.
- Changing `_parse_format_json` itself changes every caller. Example: making it consume
  `ENCODING` would move JSON_OBJECT's `RETURNING <type> FORMAT JSON ENCODING x` from
  `JSONObject.encoding` into the return type's `FormatJson` (the `identity.sql` fixture still
  passes as text, so only an AST check shows it). Prefer a change at the call site you need.

## CONTRACT: adding a clause to a JSON_TABLE column definition
Touch all of these and make them agree:
1. `exp.JSONColumnDef.arg_types` in `sqlglot/expressions/query.py`: a new optional arg.
   Precedent for a "this column holds JSON" flag: `exp.OpenJSONColumnDef` (same file) has
   `as_json: False`, printed as ` AS JSON` by `openjsoncolumndef_sql`.
2. `_parse_json_column_def` in `sqlglot/parser.py`: parse it at its position in the column
   grammar (after `kind`, before `PATH` for FORMAT JSON) and pass it to `exp.JSONColumnDef`.
   Keep the `NESTED` branch and `FOR ORDINALITY` working.
3. `jsoncolumndef_sql` in `sqlglot/generator.py`: emit it in the same position, only when set.
4. Tests in `test_json_table` (`tests/dialects/test_oracle.py`), next to the existing
   JSON_TABLE identities; MySQL's JSON_TABLE tests must still pass since the parser is shared.

## Done means, read from output after your last edit
- The exact SQL from the task parses, and so does each `FORMAT JSON` position you probed.
- `repr()` of the parsed `exp.JSONTable` shows the clause stored on the node it belongs to
  (`this` → `FormatJson` for the input; the `JSONColumnDef` for a column), and the Oracle
  round-trip prints it back in place.
- `tests/dialects/test_oracle.py` and `tests/dialects/test_mysql.py` pass, then the full suite.
