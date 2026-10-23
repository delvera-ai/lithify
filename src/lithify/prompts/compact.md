You are compacting the harness that coding agents use in a software repository. Self-editing
harnesses accumulate rules until the always-on context crowds out the agent's own reasoning. Your
job is to make the harness smaller without losing anything the evidence shows it needs.

Read `context/harness/` (editable), `context/library/` (lessons with evidence), and
`context/budget.md` (current always-on token estimate and the budget).

Apply, in order:

1. DEDUPLICATE: merge rules that say the same thing; delete rules the harness states twice.
2. DEMOTE: move rules that only apply to a recognisable kind of task out of always-on files and
   into an on-demand skill whose `description:` names that trigger.
3. MECHANISE: where a rule could be enforced by a linter, type checker, test or script, write it
   down under "## Candidates for mechanical enforcement" in `context/harness/README.md` with the
   rule and a suggested check. Do not delete the rule until the check exists.
4. RETIRE: delete rules whose library evidence is `hurt` or that every recent lesson contradicts.

Never delete a rule whose library evidence is `helped` without moving it somewhere it still fires.

@@SHARED@@
