You are reading the complete record of one improvement round in a software repository: a base
harness, the edits proposed against it, the rollouts those harnesses produced, their gate results,
and which deliverable was finally applied. Write two things for the library that future harness
edits in this repository read first.

# WHAT YOU HAVE

- `context/task.md`, `context/base_harness/`
- `context/candidates/<label>/` — each candidate harness, its `harness.diff` against base, notes
- `context/rollouts/<label>/` — trajectory, deliverable, gates for base and every candidate
- `context/selection.md` — which deliverable was applied and why, and which labels passed gates

# THE ADOPTED CANDIDATE IS NOT THE ONLY EVIDENCE

Selection compared deliverables with harnesses hidden, so it says which output was best, not which
edit worked. An edit that appeared only in a rejected candidate may still be the one that changed
behaviour; an edit inside the adopted candidate may have contributed nothing.

# WHAT EACH EDIT DID

For each component any candidate changed, write one row: what the edit changed, the observed
difference in execution it produced (cite the rollout and the trajectory moment), and a verdict:

- `helped`: a rollout whose harness carried this edit passed gates that the base rollout failed
  (or produced a clearly better deliverable), its trajectory shows the agent reading or acting on
  this component before the behaviour that made the difference, and no other edit in that
  candidate is an equally plausible cause. One such rollout is enough: every candidate is probed
  once, so say "single rollout" in `observed` rather than withholding the verdict.
- `hurt`: the rollout with this edit did worse than the base, and the trajectory ties the
  regression to the component.
- `no observed effect`: the component was never consulted, or the rollout behaved like the base.
- `confounded`: the candidate changed several components and its trajectory does not single out
  which one produced the difference, or the base also passed so there was nothing to explain.

The test for `helped` is the trajectory, not your opinion of the edit: if the record does not
show the component in use at the moment behaviour changed, it is not `helped`. A confounded row
is useful; an invented attribution poisons the library.

Use the component names exactly as they appear in the harness tree: `system.md`, `guardrails.md`,
`memory.md`, `tool_guidance.md`, `skills/<name>`, `scripts/<file>`, `subagents/<name>`.

# THE ONE LESSON THAT TRANSFERS

Write at most one durable entry, only if the edit rows support it. The `cue` describes the SHAPE
of situation it applies to in this repository, so it fires on a different task. The `lesson` is an
operation on the harness, naming the component. Too generic is useless ("be thorough"); too
specific never fires again. If the record shows no concrete, reusable contrast, write the single
line NO_ENTRY instead of the <experience> block.

@@GUARD@@

# OUTPUT FORMAT

<edits>
component: <name>
candidates: <labels that carried this edit>
change: <what the edit did>
observed: <the execution difference, and where you saw it>
verdict: <helped|hurt|no observed effect|confounded>

(repeat for each changed component, blank line between rows)
</edits>
<experience>
cue: <the shape of situation this applies to>
lesson: <the transferable operation, naming the component>
evidence: <the edit rows this rests on>
confidence: <high|medium|low, and why>
</experience>
