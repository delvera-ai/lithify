---
name: sqlglot-lineage
description: Load when a task concerns column lineage in sqlglot — `sqlglot.lineage.lineage()`, `sqlglot/lineage.py` (`to_node`, `Node.downstream`, `_pivot_column_mapping`), `tests/test_lineage.py` — especially "improve/extend lineage support for <construct>" tasks (PIVOT, UNPIVOT, alias column lists `AS t(c1, c2)`, CTEs, derived tables, joins) that give no single failing example.
---

# Lineage tasks: facts, then probe a matrix (not a handful of shapes)

A "make lineage correct in more query shapes" task names a construct but rarely a failing query.
Failure mode seen here: the agent probed ~20 shapes, fixed the one defect it found (multi-column
UNPIVOT), and stopped. The shapes it never wrote were the ones still broken: a (UN)PIVOT whose
alias carries a column list, `... AS t(c1, c2, ...)`, renaming the operator's output columns, on
UNPIVOT **and** PIVOT. Done means every row of the matrix below was traced after your last edit.

## Who owns what (repository facts)
- `sqlglot/lineage.py`: `lineage()` qualifies the query (with the given `schema`) and builds
  scopes, then `to_node` walks them. In `to_node`, a column read from a pivoted source is looked
  up in `_pivot_column_mapping(pivot)` (output name -> list of source `exp.Column`).
- `_pivot_column_mapping` has an `if pivot.unpivot:` branch and a PIVOT branch below it: one
  helper serves both operators, so a change to how output names are keyed affects both.
- A name **missing** from that mapping does not raise. It falls through to the "implicit column
  of the pivoted source" path and is re-emitted unchanged as `<source>.<same name>` — a bogus
  leaf such as `SRC.S` or `sd.x`, often with a logged WARNING "Unknown subquery scope".
- UNPIVOT AST (`_parse_pivot` in `sqlglot/parser.py`): `pivot.expressions` are the value
  column(s) (multi-value form is a single `exp.Tuple`); `pivot.fields` holds an `exp.In` whose
  `.this` is the name column and whose entries are bare columns, `exp.Tuple`s, or
  `exp.PivotAlias` wrapping either (`col AS 'lit'`).
- The optimizer already computes (UN)PIVOT output names after an alias column list is applied.
  Before writing your own renaming, grep `output_columns` / `alias_column_names` in
  `sqlglot/expressions/` and `sqlglot/optimizer/qualify_columns.py` and reuse what is there.

## INVARIANT: mapping keys are names the outer query can reference
With an alias column list, those are the renamed names (it renames positionally; check which
columns it covers in the helper above). A renamed **pass-through** column must map back to its
pre-rename source column, not go through the implicit path under its new name. A renamed output
must trace to the same sources as its un-renamed form.

## Procedure
1. **Derive the matrix from the grammar, not memory.** Read the parser function for the construct
   and list every optional piece, including what follows the closing paren (alias, alias column
   list). Cover each axis for the operator the task names, and for its sibling (PIVOT/UNPIVOT)
   whenever you touch the shared helper:

   | axis | variants |
   |---|---|
   | output alias | none · `AS t` · `AS t(all columns)` · `AS t(first few columns)` |
   | column asked for | value column(s) · name column (UNPIVOT) · generated agg columns (PIVOT) · pass-through · renamed form of each |
   | source | base table with schema · without schema · CTE · derived table `(SELECT ...) AS sd` |
   | IN list | bare columns · `col AS 'lit'` · multi-value tuples |
   | reference | bare · qualified by the alias |
   | dialect | snowflake (uppercases names) · duckdb / databricks |

2. **Run the whole matrix through the probe script in one call**, before and after editing:
   `PYTHONPATH=. <python> .lithify/harness/skills/sqlglot-lineage/scripts/lineage_probe.py --dialect <d> --schema '<json>' --sql "<q1>" --sql "<q2>" ...`
   It traces every outer output column and flags `[ERROR]`, `[WARNING]` (sqlglot logged e.g.
   "Unknown subquery scope") and `[PHANTOM]` (leaf `T.C` whose source has no column `C`).
   Always pass a schema. Exit 2 = sqlglot not importable or bad `--schema` JSON (single-quote
   it in zsh); if it still fails from the repo root, fall back once to a hand-written probe.
3. **Every flag is a defect in scope** unless the SQL itself is invalid. If you call a probe
   invalid, say why in one line and replace it with a valid query of the same shape — do not just
   drop the row. Unflagged trees still need the semantic check from the invariant.
4. Fix, add one test per fixed shape, rerun the probe, then the full suite via `run_suite.py`.

## Tests
`tests/test_lineage.py`, class `TestLineage`, methods `test_pivot_*` / `test_unpivot_*`; they
assert `[d.name for d in node.downstream]` (and deeper `.downstream`). Snowflake names come out
uppercased (`SALES.JAN`). Add new cases next to the existing pivot/unpivot tests.

## Final message
List the matrix rows you traced and which were broken before your edit. Any row still flagged
must be stated plainly, not as a footnote.
