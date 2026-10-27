---
name: sqlglot-data-types
description: Load when a task changes how sqlglot parses or generates a data type (exp.DataType) — CAST / TRY_CAST / `::` target types, nested types (ARRAY<…>, STRUCT<…>, MAP, Nullable(…)), type modifiers or trailing clauses such as COLLATE, CHARACTER SET, WITH TIME ZONE — or when a fix adds a new arg to any existing expression class (DataType, Cast, Column, …) that must survive generation in every dialect.
---

# Data types and new node args in sqlglot

## Who owns what (verified in the source)
- `exp.DataType` is in `sqlglot/expressions/datatypes.py`; its slots are `arg_types`
  (`this`, `expressions`, `nested`, `values`, `kind`, `nullable`, …). `exp.DType` is the enum.
  `DType.X.into_expr()` and `exp.DataType.build(...)` create a FRESH node carrying only what
  you pass, so any other arg on the original node is lost.
- `Parser._parse_types` in `sqlglot/parser.py` parses every type. Callers include
  `_parse_cast` (CAST target, `to = self._parse_types()`), the `::` operator, column defs, and
  the nested `<…>` / `(…)` element lists inside `_parse_types` itself. STRUCT fields go through
  `_parse_struct_types`.
- A clause added directly inside `_parse_types` changes ALL of those callers. Example:
  `x::TEXT COLLATE "C"` parses as `exp.Collate(this=Cast(...))` (the operator form) and
  generates `CAST(x AS TEXT) COLLATE "C"` — it is not an identity, and a generic hook in
  `_parse_types` would steal that COLLATE. Hook only the call sites the task names, then probe
  the `::` and plain-expression forms again.
- `Generator.datatype_sql` in `sqlglot/generator.py` renders the node for the base generator.

## INVARIANT: dialect overrides can silently drop a new arg
Dialect generators (`sqlglot/generators/<d>.py`) override `<node>_sql` and inherit from one
another. An override that rebuilds the node (`into_expr()`, `DataType.build`) or returns a
literal string before reaching the base method drops any arg it never knew about, with no
error; the source-dialect round-trip and the existing suite stay green.
- Known case: `sqlglot/generators/hive.py` `datatype_sql` replaces STRING/VARCHAR with
  `exp.DType.TEXT.into_expr()`. Spark2/Spark/Databricks inherit it, so a new DataType arg
  added only in the base `datatype_sql` vanished: reading Postgres
  `CAST('a' AS STRING COLLATE foo)` and writing Spark printed `CAST('a' AS STRING)`.
- Find the others with `grep -n "def datatype_sql" sqlglot/generators/*.py` (use the node's
  own `<node>_sql` name for other nodes) and grep each generator's `TRANSFORMS` for the node
  and its enclosing node (e.g. `exp.Cast`).

Rule: every override that rebuilds the node or returns early must carry the new arg over
(copy it onto the replacement node, or render it on the returned string). Only if the target
engine cannot express it, call `self.unsupported(...)` there. A dialect you did not probe is
not "out of scope": round-trip includes transpiling the parsed node.

## Procedure (after the parse side works)
1. From the repo root, with the project's python (`memory.md`), AFTER your last source edit:
   `<python> .lithify/harness/skills/sqlglot-data-types/scripts/all_dialects.py --read <dialect> --keep <KEYWORD> "<sql>" "<sql2>"`
   Pass every form the task names plus an ordinary-expression form (e.g. `x COLLATE "C"`).
   It generates each SQL in every dialect; exit 4 means a `[DROPPED: KW]` or generate error.
2. For each dropped dialect, read its override and its parents' (see above) and fix it.
   Rerun until it exits 0. If the script exits 2, run it from the repo root; if it still
   fails, probe by hand once, including hive/spark and any dialect with an override.
3. Tests: `validate_identity` in the source dialect file next to existing tests of the same
   clause, plus a `validate_all(..., read={<source>: ...})` in the test file of a dialect whose
   generator overrides the method (e.g. `tests/dialects/test_spark.py`), with the expected
   string written from that engine's syntax, not copied from the script output.
4. Then the normal done-check: dialect test files, then `run_suite.py` (see `tool_guidance.md`).
