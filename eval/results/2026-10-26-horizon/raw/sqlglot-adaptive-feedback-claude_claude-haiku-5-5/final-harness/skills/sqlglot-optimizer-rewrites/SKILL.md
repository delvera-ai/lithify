---
name: sqlglot-optimizer-rewrites
description: Load when a task changes a sqlglot optimizer pass (sqlglot/optimizer/*.py — qualify_tables, qualify_columns, qualify, annotate_types, simplify, …) or any code that rewrites an existing AST in place (`.set(...)`, `.replace(...)`, rebuilding aliases / alias column lists / identifiers / ColumnDefs from pieces of the input tree), including crashes such as "Name needs to be a string or an Identifier" or "'NoneType' object has no attribute ..." on a missing `.type` / arg (canonicalize, simplify, annotate_types).
---

# Rewriting existing sqlglot ASTs (optimizer passes and transforms)

A fix that only stops the crash can still put the wrong node *objects* into the result. The
round-tripped SQL and the full suite can both look right while it is wrong.

## INVARIANT: a node taken from the tree goes back in as a copy
sqlglot expressions are mutable and each node has one `parent`/`arg_key`. `Expr.set` re-parents
whatever it is given, and `_set_parent` (`sqlglot/expressions/core.py`) only overwrites
`parent`/`arg_key`/`index`; it never detaches the node from its old slot. So if you read a node
out of the tree (or out of an `args` list you are about to overwrite) and `.set()` it into a new
or rebuilt parent, attach a copy — unless the code clearly *moves* it (`.pop()` / `.replace()`
first). "Keep it intact" means same class and children, not the same Python object.

Copy helpers (all in `sqlglot/expressions/core.py`):
- `node.copy()` — deep copy. `sqlglot/optimizer/qualify_tables.py` already uses it:
  `table.set("db", db.copy())`, `column.set("table", table_alias.copy())`.
- `exp.maybe_copy(node, copy=True)` — copies when `copy` is set and the node is not None.
- `exp.to_identifier(x, copy=True)` — copies an `Identifier` (default), builds one from a `str`,
  and raises `ValueError("Name needs to be a string or an Identifier, ...")` for anything else.

Consequence: a new branch added beside a converter that copies (e.g. a `ColumnDef` case next to
`exp.to_identifier(c)`) must copy too (`c.copy()`), not pass `c` through.

## FACT: table alias column lists hold Identifier OR ColumnDef
`exp.TableAlias.columns`: `t(a, b)` gives `Identifier`s; a typed list such as
`fn() AS t(col INT)` gives `exp.ColumnDef` (`this` = Identifier, `kind` = DataType).
- Read names with `.name` (works for both; see `alias_column_names` in `core.py`).
- Code that rebuilds alias columns must accept both kinds, keep a ColumnDef's `kind`, and copy
  either kind. In `qualify_tables.py`, a table function's alias columns reach
  `_set_alias(..., columns=...)` from `table_alias.columns` in the `exp.Func` branch; grep the
  module for other paths that feed alias columns through `to_identifier`.

## INVARIANT: a missing type (`None`) behaves exactly like `DType.UNKNOWN`
Passes such as `canonicalize` may run without `annotate_types`, so `node.type` can be `None`.
With `annotate_types` (which the pass's own tests run first), an unresolved column gets
`DType.UNKNOWN` instead. A None-guard picks a branch for every untyped input, so picking the
branch IS the fix: send `None` down the branch the unedited code already takes for `UNKNOWN`.
Do not create a third behaviour.
- The None-safe check is `Expr.is_type(*dtypes)` (`sqlglot/expressions/core.py`): it returns
  `False` for `None`. Prefer it to `node.type.this in ...`, which crashes on `None`.
- Copy the guard from the sibling with the SAME action shape, not just the nearest helper.
  In `sqlglot/optimizer/canonicalize.py`:
  - "cast to DATETIME unless already temporal" (the `exp.Extract` branch of `coerce_type`) uses
    `not x.is_type(*exp.DataType.TEMPORAL_TYPES)`, so untyped and UNKNOWN args are cast.
  - "cast only when the type is known to be TEXT/DATE" (`_coerce_date`,
    `_coerce_timeunit_arg`) uses `if not x.type`, so untyped args are skipped.
- Check before editing: run the crashing input both as `pass(parse_one(sql))` and as
  `pass(annotate_types(parse_one(sql)))` on the UNEDITED code, and print the second output.
  After the fix both runs must print that same SQL. Take the regression test's expected string
  from that annotated output, not from what your edited code prints.
- If you justify a guard with "the sibling helpers do X", quote the sibling lines you read.
- Task wording such as "left alone" can describe not crashing rather than the output. If it
  disagrees with the sibling-consistent result, say so in the final message, show both outputs,
  and say which one you shipped and why.

## Procedure
1. Reproduce with the task's exact call, then `repr()` the rejected node and the arg holding it.
2. Read the whole function you change and note how it already re-attaches nodes (`.copy()`,
   `to_identifier`); new node kinds in the same list follow the same rule.
3. Fix runtime behaviour first; widen type hints (`Sequence[str | exp.Identifier]` →
   `... | exp.ColumnDef`) afterwards.

## Done means, read from output after your last edit
- A probe on the task input prints the output SQL, the type and children of every rewritten arg,
  and for each kept node `before is after` (capture `before` from the tree before the call, find
  the node again after). It must be `False` unless the function already reuses that kind unchanged.
- Run with the task's option on and off (e.g. `canonicalize_table_aliases`), and once with a
  column reference to the alias to confirm references are rewritten.
- Tests: `tests/test_optimizer.py` has one `test_<pass>` method per pass — direct `assertEqual`
  calls, then `self.check_file("<pass>", ...)` over `tests/fixtures/optimizer/<pass>.sql`
  (input/expected pairs with `# title:` and optional `# dialect:` /
  `# canonicalize_table_aliases:` headers). Fixtures compare SQL text only, so a node-level fix
  needs a direct test that holds the original node and asserts type, children and
  independence from it afterwards.
- `tests/test_optimizer.py` passes, then one full-suite `run_suite.py` run ends with `EXIT: 0`.
