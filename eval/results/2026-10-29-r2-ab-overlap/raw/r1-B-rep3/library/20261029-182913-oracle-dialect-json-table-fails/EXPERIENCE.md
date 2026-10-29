# 20261029-182913-oracle-dialect-json-table-fails

**Task:** Oracle dialect: `JSON_TABLE` fails to parse when the input expression carries `FORMAT JSON` (e.g. `JSON_TABLE(doc FORMAT JSON, '$.items[*]' COLUMNS (...))`). Support `FORMAT JSON` there so it parses and round-trips.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `memory.md` | confounded | Adds a pointer to `AGENTS.md` as the maintainer conventions doc, a note that expression classes live in `sqlglot/expressions/` with no `sqlglot/expressions.py`, and (comp-1 only) a note that `python -I` drops the cwd so `import sqlglot` fails. | dom-1's trajectory opens with `cat AGENTS.md` and says it is following the skill the harness pointed to. comp-1 also runs `cat AGENTS.md` early. base-1 never opens `AGENTS.md` (zero matches in its trajectory). inv-1's grep returned "sqlglot/expressions.py: No such file or directory", which supports the expressions note. base-1's `ModuleNotFoundError` under `-I` is visible in its trajectory. The comp-1 notes say base-1 also got the expressions.py error, but that span is elided in the trajectory, so I could not confirm it. All four rollouts reached the same no-edit conclusion and passed the same test gate, so the consulted file did not change the deliverable. |
| `skills/sqlglot-json-table` | confounded | New on-demand skill with a code map (parser, generator, expression classes, shared not dialect-specific), the existing test locations, a reproduce-first procedure with a "make no edit and report" branch, and a list of unsupported forms (input-side ENCODING, column EXISTS PATH, column NULL ON ERROR, column DEFAULT ON EMPTY, FORMAT JSON on a column). | comp-1 calls the skill as its first action, runs the exact reported statement, then tests the unsupported forms the skill lists and stops with no edit. dom-1 calls the skill after AGENTS.md and does the same. base-1 spends its early calls grepping across parser, generator and expressions before reaching the same conclusion. Cost per run: base $0.0151 (8,079 output tokens), dom-1 $0.0107 (4,283), comp-1 $0.0099 (2,416). The outcome is identical in all three. Each candidate has a single rollout. Both candidates also changed memory.md, so the cost difference cannot be assigned to the skill alone. |
| `tool_guidance.md` | no observed effect | Adds one line: run Python snippets from the repo root with `PYTHONPATH=.` and the project interpreter, and do not use `-I`. | base-1's trajectory shows `ModuleNotFoundError: No module named 'sqlglot'` and then recovery with `PYTHONPATH=.`. inv-1 never runs with `-I`, never hits the error, and does not open `tool_guidance.md` in its visible trajectory. Its own snippets run from the repo root without trouble, and its outcome matches base-1's. |
