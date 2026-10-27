---
name: sqlglot-query-modifiers
description: Load when a task adds or changes a trailing SELECT clause / query modifier in sqlglot — anything dispatched through a parser's QUERY_MODIFIER_PARSERS or emitted by the generator's query_modifiers (T-SQL FOR XML / FOR JSON / FOR BROWSE, OPTION(...), ClickHouse SETTINGS / FORMAT, FOR UPDATE locks, LIMIT/FETCH/OFFSET …), including "support the X clause like the existing Y clause" requests and clauses that must round-trip in one dialect and be dropped with an "Unsupported query option." warning in the others.
---

# Query modifiers (trailing SELECT clauses) in sqlglot

## Who owns what (verified in the source)

- Dispatch: `Parser.QUERY_MODIFIER_PARSERS` (`sqlglot/parser.py`) maps ONE token type to a
  lambda returning `(key, value)`. `_parse_query_modifiers` calls it, and only if `value` is
  truthy does it `this.set(key, value)` and loop; a second clause with the same key raises
  "Found multiple '<TOKEN>' clauses". A falsy value ends the loop **without consuming the
  token**, so the statement then fails with `Invalid expression / Unexpected token` at that
  token.
- Dialects extend the dict with `**parser.Parser.QUERY_MODIFIER_PARSERS` (`parsers/tsql.py`,
  `parsers/oracle.py`, `parsers/clickhouse.py`). T-SQL REPLACES the base `TokenType.FOR` entry
  (base is `("locks", _parse_locks())`) with `_parse_for` in `sqlglot/parsers/tsql.py`.
- Generation: `Generator.query_modifiers` (`sqlglot/generator.py`) concatenates the pieces; the
  T-SQL tail is `options_modifier` (key `options`) then `for_modifiers` (key `for_`, emits
  `FOR XML` + `self.seg(...)` items). These live in the BASE generator, so every dialect runs them.
- Cross-dialect drop: clause items are `exp.QueryOption` (`expressions/query.py`). Base
  `Generator.queryoption_sql` calls `self.unsupported("Unsupported query option.")` and returns
  `""`; `generators/tsql.py` and `generators/oracle.py` override `queryoption_sql` to print the
  option. `self.expressions(...)` skips empty item SQL, so a clause whose items all render `""`
  disappears in other dialects. A new clause gets "warn and drop elsewhere" for free ONLY if
  every item it stores is a `QueryOption` (wrapping e.g. `XMLKeyValueOption` / `Var`).
- Option keywords: module-level `parser.OPTIONS_TYPE` dicts in `parsers/tsql.py`
  (`OPTIONS`, `XML_OPTIONS`) read with `self._parse_var_from_options(...)`.
- Warning asserts in tests use `with self.assertLogs(helper_logger)` (`from sqlglot.helper
  import logger as helper_logger`), as in `tests/dialects/test_bigquery.py`.

## INVARIANT: one token, whole grammar

When one token starts several clause forms, the token's parser owns ALL of them. Before
editing it, write down the clause's full grammar from the engine's reference and list each
alternative. For T-SQL the SELECT `FOR` clause is `[ FOR { BROWSE | <XML> | <JSON> } ]`
(Microsoft "SELECT (Transact-SQL)"): `BROWSE` is a bare keyword with no options; `XML` takes
`RAW|AUTO|EXPLICIT|PATH` + options; `JSON` takes `AUTO|PATH` + options.

A rollout that added `FOR JSON` restructured `_parse_for` but kept its "not XML/JSON → return
nothing" fallthrough, so `SELECT * FROM t FOR BROWSE` still died on the unconsumed `FOR` token,
and none of its probes or gates noticed. If you rework a shared-token dispatcher, every
alternative of its grammar must either parse and round-trip or be a deliberate, named error —
never the silent fallthrough.

## Procedure

1. List the alternatives (above). Probe each one BEFORE editing, in one call:
   `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read <d> --write duckdb,postgres "<sql1>" "<sql2>" ...`
   — each alternative top-level, the new option list in documented order and (if the engine's
   docs allow it) reordered, plus the clause inside a scalar subquery and a derived table.
   Record which already fail.
2. Implement, following how the existing sibling branch stores and generates its options
   (`pretty=True` output follows the sibling: `FOR XML` uses `self.sep()` + `self.seg()`).
3. **Done means**, from output taken after your last source edit:
   - the step-1 probe set rerun: every alternative running through your dispatcher parses and
     round-trips. A sibling that is a bare keyword or trivially handled by the dispatcher you
     rewrote gets supported and tested; anything else still failing is listed in the final
     message;
   - a non-owning dialect omits the clause and logs the warning, asserted in a test;
   - the dialect test file passes, then one `run_suite.py` full run ends with `EXIT: 0`.
