---
name: sqlglot-clause-element-lists
description: Load when a sqlglot parse fix widens what a parenthesised list inside a clause or statement accepts — e.g. an INSERT ... ON CONFLICT (...) / upsert conflict target, an index or constraint column list, PARTITION BY / CLUSTER BY / key lists — from bare column names to expressions (function calls, arithmetic, COLLATE, ASC/DESC, opclasses), or when such a list fails with "Expecting )".
---

# Widening a clause's element list

For an `INSERT ... ON CONFLICT` / upsert target, also load `sqlglot-upsert-on-conflict`: it has
the verified owners, callers and the parser/generator contract for that clause.

The usual defect: the list is parsed with a narrow helper (`_parse_id_var`, `_parse_column`).
The task shows one failing element, and the agent widens the helper just far enough for that
element. The task's dialect accepts a whole element grammar, and the forms the example did not
show are left broken.

## Procedure (before the first source edit)
1. **Write down the element grammar for the dialect the TASK names**, from that engine's docs.
   Do not use a related engine's docs. For an index-backed target, the element is usually the
   engine's indexed-column form: `expr [COLLATE name] [ASC|DESC]`, sometimes also
   `NULLS FIRST|LAST` or an operator class. List the clause's other optional parts too: a
   trailing `WHERE`, `ON CONSTRAINT`, and the action forms.
2. **Find the sibling that already parses the same element grammar.** For an index-backed
   target this is the dialect's `CREATE INDEX` / `UNIQUE (...)` column list. Grep for its
   helper and print one parsed sibling with `--repr`. In this repo the `CREATE INDEX` column
   list (`_parse_index_params`) parses each column with `_parse_with_operator`, i.e.
   `_parse_ordered(self._parse_opclass)`, and builds `exp.Ordered` nodes (`desc=True` for DESC).
   Accept the sibling's full element grammar. Do not stop at a narrower helper such as
   `_parse_assignment`, which handles `COLLATE` alone but fails on `COLLATE x ASC`. But an
   `exp.Ordered` around a key written without ASC/DESC can gain `NULLS FIRST/LAST` when
   transpiled (`Generator.ordered_sql` compares `NULL_ORDERING`), so build `Ordered` only when
   `ASC`/`DESC` follows (idiom: `_parse_pipe_syntax_aggregate_fields`). If you diverge from
   the sibling, write down which grammar item makes the difference.
3. **Build the probe matrix in one call.** Include each grammar item alone, the combination of
   all items in one element (`f(x) COLLATE c DESC`), several elements mixed with plain columns,
   the optional `WHERE`, and the task's literal example. Run every form under the task's
   dialect:
   `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read <task dialect> --write <other upsert dialects> --repr "<form1>" "<form2>" ...`
   Run it from the repo root. It keeps going after a `PARSE ERROR` and exits 1 if any form failed.
4. Edit, then rerun the SAME matrix after your last source edit.

## Done means
- In the task's dialect, every form in the matrix parses without `PARSE ERROR` and has no
  `[DIFFERS]` you cannot name as a normalisation. That is the `ast_check.py` exit code read
  after the last edit.
- Under the task's dialect, a failing form that the engine's docs allow is a defect. Do not
  dismiss it because some other dialect rejects the form. A form that another target engine
  rejects is a generation question (drop it, or emit what that engine accepts). It is never a
  reason to leave the source dialect's parse broken.
- The tests cover the combined form from step 3, not only the task's example.
- Then the dialect test file passes, and one full `run_suite.py` run passes (`tool_guidance.md`).
