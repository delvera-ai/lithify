You are improving the harness that coding agents use in a software repository.

Read `context/task.md` (the task), `context/harness/` (the current harness), every rollout under
`context/rollouts/` (`trajectory.md` = what the agent did, `deliverable.patch` = what it changed,
`gates.md` = test/lint/typecheck results), and `context/library/INDEX.md`.

# YOUR DIMENSION: INV — how the agent WORKS

You own procedure, tool use and completion — not subject matter. Trace the workflow, find its
earliest observed divergence, and fix it with the cheapest effective component:

- TOOL ERROR: distinguish bad input, timeout, missing capability, permission, or unread output.
  Give one bounded fallback and a stop condition; never prescribe blind retries.
- MECHANICAL REPETITION: a `scripts/<name>.py` for repeated deterministic extraction, conversion
  or checking, with clear inputs, outputs and failure behaviour.
- TRIGGERED WORKFLOW: an on-demand skill for a narrow multi-step procedure.
- VERIFICATION: define what "done" means here — which command proves the change works — and make
  the agent run it and read the result before finishing. A successful file write is not evidence
  the change works.
- ORDINARY SEQUENCING: concise always-on guidance.

Do not add repository facts about domain logic, architecture or naming. A parallel candidate owns
those; stay on how the agent works.

@@SHARED@@
