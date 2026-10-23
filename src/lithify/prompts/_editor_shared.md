# GROUND EDITS IN THIS REPOSITORY

The harness you produce governs future agent sessions in THIS repository. Verified facts about
the repository are the most valuable thing you can write down, because they are what the rollouts
paid to discover: which module owns a concern, which helper must be used instead of a raw call,
which command actually runs the tests, which directory a kind of file belongs in. When the
evidence establishes such a fact, write the fact itself ("errors in this repo are raised as
`AppError` from `app/errors.py`"), not merely a procedure for rediscovering it. Record only what
the evidence establishes — a guessed fact is worse than none.

Procedure, by contrast, should be written for the kind of task, not this one task: later tasks in
this repository read it.

`context/library/` holds harnesses and lessons from earlier tasks. They are examples, not part of
the harness you are editing. To reuse a component, COPY it into `context/harness/` and re-check
its facts against the current evidence.

# HOW TO DECIDE WHAT TO CHANGE

Every edit must trace to a moment in a rollout. Ask: which rollout did what, and would this text
have changed it? If you cannot name the moment, the edit is speculation. In order of preference:

1. a DIVERGENCE — rollouts disagreed, so the agent can already do it and just needs telling;
2. a repeated concrete failure — the same error or omission in every rollout;
3. a risk visible in a trajectory but not yet realised.

Do not fix what the rollouts already got right, and do not restate what the harness already says.

Gate output (tests, lint, typecheck) tells you THAT something failed. Use it to locate the failure
mode. Never copy test expectations, assertion values or fixture data into the harness, and never
write a rule that tells the agent to edit, skip or weaken existing tests.

@@CANDIDATE_LINE@@

# WHAT YOU CAN CHANGE

The harness in `context/harness/` is a tree of components with different costs:

| path | what it is | when it is in context |
|---|---|---|
| `system.md` | role and top-level procedure | ALWAYS ON — paid on every run |
| `guardrails.md` | hard rules | ALWAYS ON |
| `memory.md` | durable repository facts | ALWAYS ON |
| `tool_guidance.md` | how to use tools/commands here | ALWAYS ON |
| `skills/<name>/SKILL.md` | a reusable workflow | ON DEMAND, only when its description matches |
| `skills/<name>/scripts/*` | helpers a skill invokes | run via shell |
| `scripts/<name>.py` | deterministic helper | run via shell |
| `subagents/<name>/AGENT.md` | delegated worker brief | its own context; returns text |

ALWAYS-ON TEXT IS THE EXPENSIVE OPTION. Prefer, in order: a SKILL for anything with a recognisable
trigger; a SCRIPT for a deterministic operation the rollouts hand-rolled or got wrong; a SUBAGENT
for a bounded investigation with large input and small output; always-on text last, only for a
short rule that applies to every task. If you add always-on text, cut something to pay for it.

Rules that get a candidate DISCARDED before it is ever run:

1. `skills/<name>/SKILL.md` needs frontmatter `name: <name>` (equal to the directory) and a
   `description:` of at least 20 characters that says WHEN to load it. The description is the
   trigger — every CLI decides whether to load a skill from it.
2. Every script a skill or always-on file names must ship in the harness. A skill's own helpers go
   in `skills/<name>/scripts/`; reference them as `.lithify/harness/skills/<name>/scripts/<file>`.
3. Python scripts must compile. Never put credentials in the harness.

The harness changes HOW the agent works. It must never change WHAT the task asked for.

# HOW TO MAKE A CHANGE

Edit files in `context/harness/` in place with your normal tools; create or delete files as
needed. Your edits on disk ARE the proposal. Do not touch anything outside `context/harness/`.
Files you do not touch are inherited unchanged. If the evidence does not argue for any change,
leave everything as it is and say KEEP_BASE in your notes — that is a real answer.

Finish your reply with ONE `<notes>` block: for each change, the rollout moment that motivated it.

@@GUARD@@
