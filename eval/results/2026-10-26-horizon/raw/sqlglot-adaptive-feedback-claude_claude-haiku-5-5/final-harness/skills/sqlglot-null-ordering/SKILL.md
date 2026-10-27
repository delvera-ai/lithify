---
name: sqlglot-null-ordering
description: Load when a task touches ORDER BY / Ordered generation in sqlglot — NULLS FIRST / NULLS LAST, the `CASE WHEN <x> IS NULL THEN 1 ELSE 0 END, <x>` sort-key simulation for targets without null ordering (MySQL, T-SQL, Doris, StarRocks, Fabric), NULL_ORDERING / NULL_ORDERING_SUPPORTED, or an ORDER BY transpile that is wrong or ambiguous in the target engine (e.g. "Column ... in order clause is ambiguous"). Also useful for any base `Generator` fix where the output repeats one expression.
---

# ORDER BY null-ordering simulation in sqlglot

## Who owns it
- The simulation is in the BASE generator: `Generator.ordered_sql` in `sqlglot/generator.py`.
  No dialect overrides it. The CASE is emitted only on the `self.NULL_ORDERING_SUPPORTED is None`
  branch (`False` is BigQuery's branch: it reports unsupported and emits no CASE).
- `NULL_ORDERING_SUPPORTED = None` is set in `sqlglot/generators/mysql.py` and
  `sqlglot/generators/tsql.py`. `DorisGenerator` and `StarRocksGenerator` subclass
  `MySQLGenerator`, and `FabricGenerator` subclasses `TSQLGenerator`, so they inherit it.
  `SingleStoreGenerator` (also a MySQL subclass) sets it back to `True`.
- Whether a simulation is needed at all comes from the reading dialect's `NULL_ORDERING`
  (`nulls_are_small` / `nulls_are_large` / `nulls_are_last`; DuckDB is `nulls_are_last`).

## CONTRACT: changing the simulation
1. A fix in `ordered_sql` changes MySQL AND T-SQL output (plus their subclasses). Probe both
   `write="mysql"` and `write="tsql"` (or every dialect at once with
   `<python> .lithify/harness/skills/sqlglot-data-types/scripts/all_dialects.py --read <src> "<sql>" ...`
   and look for `IS NULL THEN`). Existing shared coverage is
   `tests/dialects/test_dialect.py::test_unsupported_null_ordering` (its comment says it targets
   "MySQL / T-SQL"). Put new regression tests in each affected target's file
   (`tests/dialects/test_mysql.py`, `tests/dialects/test_tsql.py`), not only the source dialect's.
2. INVARIANT: the simulation emits the expression twice: the `CASE WHEN <e> IS NULL …` key and
   the sort key `<e>`. They must be the SAME expression. If you resolve or rewrite the ordered
   expression (e.g. to its projection), compute it once and use it for both keys. Rewriting only
   the CASE operand and leaving the sort key as the original text is an unfinished fix, not a
   design choice: a bare name in either key can still be ambiguous, and if it is also a
   projection alias it can resolve to something different from the CASE.
3. Resolving an ORDER BY reference against the SELECT's projections: the ORDER BY is
   `Ordered.parent` (`exp.Order`), whose parent is the `exp.Select`. Match on the projection's
   `alias_or_name` and take `projection.unalias()`. The optimizer's equivalent is
   `_expand_order_by_and_distinct_on` in `sqlglot/optimizer/qualify_columns.py`.
4. Do not regress the existing branches: positional ordering (`expression.this.is_int` reports
   unsupported), `exp.Rand` (no CASE), window ORDER BY (`find_ancestor(exp.Window, exp.Select)`,
   `WINDOW_FUNCS_WITH_NULL_ORDERING`). Window ORDER BY has no projection to resolve against.

## Probe matrix (run before AND after editing; multi-table FROM in each)
Bare column that is also a projected qualified column; qualified column (`t.c`); alias over a
column (`t.c AS v ... ORDER BY v`); alias over a non-column expression (`a.x + b.y AS s ...
ORDER BY s`); alias that reuses a source column name (`a.x - 1 AS x ... ORDER BY x`);
`JOIN ... USING (...)`; `ON TRUE`; each with ASC and DESC. Write the expected output of each
from the task's wording (e.g. "qualified the same way as …") BEFORE running your edited code;
test expectations come from that, never from pasting what your generator printed. After the
edit, check that the two copies of `<e>` in every output are textually identical.

## Done means
From output taken after your last source edit: the matrix rerun for MySQL and T-SQL with
identical copies; `run_suite.py tests/dialects/test_mysql.py tests/dialects/test_tsql.py
tests/dialects/test_dialect.py` passing; then one full `run_suite.py` run ending `EXIT: 0`.
