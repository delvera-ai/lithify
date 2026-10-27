---
name: sqlglot-upsert-on-conflict
description: Load when a task touches INSERT upsert syntax in sqlglot — `INSERT ... ON CONFLICT (...)` conflict targets (columns, expressions, COLLATE, ASC/DESC, the target's WHERE), `ON CONFLICT ON CONSTRAINT`, `DO NOTHING` / `DO UPDATE SET ... WHERE`, MySQL `ON DUPLICATE KEY UPDATE`, SQLite `INSERT OR REPLACE/IGNORE` or `UNIQUE (...) ON CONFLICT IGNORE`, or the `exp.OnConflict` node, `_parse_on_conflict` / `onconflict_sql` — in any dialect (SQLite, PostgreSQL, DuckDB, MySQL …).
---

# INSERT ... ON CONFLICT in sqlglot

## Who owns it (verified in source)
- Node: `exp.OnConflict` in `sqlglot/expressions/dml.py`. Args: `conflict_keys` (the target
  list), `index_predicate` (the `WHERE` between the target and `DO`), `constraint`
  (`ON CONSTRAINT name`), `action`, `expressions` (the `SET` list), `where` (the `WHERE` after
  `DO UPDATE SET ...`), `duplicate` (MySQL `ON DUPLICATE KEY`). `exp.Insert` holds it as `conflict`.
- Parser: base `Parser._parse_on_conflict` in `sqlglot/parser.py`; no dialect parser overrides
  it. It has TWO callers: `_parse_insert` and `_parse_unique` (the column/table constraint
  `UNIQUE (b, c) ON CONFLICT IGNORE`). A change must keep both paths round-tripping.
- Generator: base `Generator.onconflict_sql` in `sqlglot/generator.py`; only
  `sqlglot/generators/materialize.py` overrides it (drops the clause).
- Existing tests: SQLite `INSERT OR ...` / `UNIQUE ... ON CONFLICT` identities are in
  `tests/dialects/test_sqlite.py::test_ddl`; PostgreSQL `ON CONFLICT` cases (target `WHERE`,
  `ON CONSTRAINT`, `RETURNING`) are in `tests/dialects/test_postgres.py`. Add new SQLite
  upsert cases beside the existing ones in `test_ddl` rather than in a new method.

## INVARIANT: a conflict target is an INDEX-COLUMN list, not an expression list
- SQLite's conflict target is a list of `indexed-column` = `expr [COLLATE name] [ASC|DESC]`
  (the same grammar as `CREATE INDEX` columns). PostgreSQL's is
  `{ col | ( expr ) } [ COLLATE c ] [ opclass ]`. So `LOWER(y) COLLATE NOCASE ASC` and `y DESC`
  are LEGAL targets in SQLite. Judge a form's legality by the dialect the task names; do not
  dismiss a failing SQLite probe because PostgreSQL would reject it.
- The sibling construct is `_parse_index_params` (CREATE INDEX), which parses each column with
  `_parse_with_operator` -> `_parse_ordered(self._parse_opclass)`. Swapping the target parser to
  `_parse_assignment` (an expression parse) accepts `lower(y)` and `COLLATE` but still raises
  `Expecting )` at `ASC` / `DESC`. That is an unfinished fix.
- Do NOT wrap every key in `exp.Ordered`. `Generator.ordered_sql` adds `NULLS FIRST` /
  `NULLS LAST` whenever the reading and writing dialects' `NULL_ORDERING` differ, so a SQLite
  `ON CONFLICT(id)` transpiled to PostgreSQL would come out `ON CONFLICT(id NULLS FIRST)`, which
  PostgreSQL rejects (verified: the CREATE INDEX path does exactly this). Keep unordered keys as
  the bare expression and build `exp.Ordered` only when `ASC`/`DESC` follows. The parser
  already has that idiom: `_parse_pipe_syntax_aggregate_fields` does
  `if self._match_set((TokenType.ASC, TokenType.DESC), advance=False): return self._parse_ordered(lambda: this)`.
- Plain names: before the expression-level change they parsed as `exp.Identifier`; after it
  they parse as `exp.Column`. Nothing else in `sqlglot/` reads `conflict_keys`, so either is
  safe, but assert the shape you chose in a test.

## CONTRACT: parser and generator must agree on the key node types
If `onconflict_sql` special-cases key types (e.g. parenthesizing non-trivial expressions so
PostgreSQL accepts `ON CONFLICT((b + 1))`), every node type the parser can now produce must be
handled: `exp.Column`, `exp.Identifier`, `exp.Func` (this includes `exp.Collate`, a `Func`
subclass), `exp.Paren`, AND `exp.Ordered`. Parenthesizing an `Ordered` gives
`(y DESC)`, which is not a valid conflict target in either engine.

## Probe matrix (read=sqlite and read=postgres; identity round-trip, then write the other)
Run all forms in one call from the repo root and read the exit code after your last edit:
`<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read sqlite --write postgres --repr "<form1>" "<form2>" ...`
Target keys: `x`; `lower(y)`; `lower(y) COLLATE NOCASE`; `y DESC`; `lower(y) COLLATE NOCASE ASC`;
`x, lower(y)`; `b + 1`. Combine with: target `WHERE` (`index_predicate`), `DO NOTHING`,
`DO UPDATE SET c = excluded.c WHERE ...`, a `SELECT ... WHERE true` source (the WHERE belongs to
the SELECT, not the target), `ON CONFLICT ON CONSTRAINT pkey` (postgres), and
`CREATE TABLE a (b, c, UNIQUE (b, c) ON CONFLICT IGNORE)` (the `_parse_unique` caller).
For every output check: no `NULLS FIRST/LAST` appeared on a key written without ASC/DESC, no key gained parentheses it did not have
in a same-dialect round-trip, and the key nodes are the classes you intended. Any form legal in
the task's dialect that still fails is a bug to fix, not a caveat.
