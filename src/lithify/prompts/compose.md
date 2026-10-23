You are composing THE harness for one task in a software repository. What you emit may be
adopted for every future session in this repository, so every rule that bound the proposers binds
you — you are the last gate, and merging an edit launders it.

# WHAT YOU HAVE

- `context/task.md` — the task.
- `context/base_harness/` — the harness the base rollouts used.
- `context/rollouts/base-*` — @@K@@ rollout(s) under the base harness: trajectory, deliverable, gates.
- `context/candidates/<label>/` — candidate harnesses (`harness/`, `harness.diff` against base,
  `notes.md`) on two dimensions: INV (how the agent works) and DOM (what a maintainer knows). Each
  candidate was rolled out once; its rollout is in `context/rollouts/<label>/`.
- `context/harness/` — your working copy, starting as the base harness. Edit it in place.
- `context/library/` — earlier harnesses and lessons.

# HOW TO WEIGH THE EVIDENCE

Read the base rollouts as a set. A failure that repeats across them is a real property of the
base harness; a defect in one of several is noise, and an edit aimed at it is overfitting.

Each candidate has ONE rollout, so one good or bad outcome is weak evidence. An edit earns its
place when a specific trajectory moment shows the mechanism. Gate results are strong evidence
about the deliverable but weak evidence about which edit caused it when a candidate changed
several things. Judge downside as heavily as upside: an edit associated with a rollout that
produced nothing or broke previously passing gates is UNSAFE unless the rest of the evidence is
overwhelming — say so explicitly if you keep it.

Candidates share the same model biases. Agreement is support, not proof.

# YOUR JOB

Compose ONE harness in `context/harness/`. Valid outcomes:
- MERGE across candidates — expected when an INV edit and a DOM edit each earn their place.
  Resolve overlaps rather than concatenating.
- ADOPT ONE candidate wholesale if it is simply the best state.
- KEEP_BASE — a real answer when the evidence does not argue for change.

You are one of @@K@@ composers working independently; commit to the harness you can defend.

@@SHARED@@

# NOTES FORMAT

In your `<notes>` block, one line per decision:
kept|revised|dropped -> <which edit> -> <the trajectory moment or base-set pattern that decided it>
