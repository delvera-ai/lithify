# 20261024-214815-three-regressions-that-only-appe

**Task:** Three regressions that only appear once a retry actually happens:
1. `Retrying(wait=None)`, `wait=0` and `wait=sum([])` now raise `TypeError: 'NoneType' object is not callable`; these values mean "no wait" and must work again (sync and async).
2. Adding a plain callable to a wait strategy (`my_callable + wait_fixed(1)`) must produce a `wait_combine` that sums both.
3. `wait_combine` must pass the retry state to its strategies positionally, so plain callables with any parameter name work.

## Transferable lesson

- **cue:** A tenacity task restores behaviour that a recent typing/strictness commit removed or narrowed (git history shows a #677/#679/#682-style commit with a release note). The fix extends an operator or guard that the commit deliberately left rejecting some inputs, so a broad "everything else" branch would quietly undo the commit's stated promise.
- **lesson:** In `skills/tenacity-change-contract`, put the strictness commit's stated invariant at the site the fix will touch, as an explicit branch condition with the commit and reno as source (e.g. "`__radd__`: combine only when `callable(other)`; a non-zero number still returns `NotImplemented`"). Add a grep that lists every annotation site to widen. Wherever the skill says "widen the annotation", say in the same place that an existing test's now-unused `# type: ignore` stays as it is and gets reported, not removed.
- **evidence:** Row skills/tenacity-change-contract: base-1 saw the #677 history but wrote `isinstance(other, int)`; dom-1 and comp-1, with §1b5, both wrote `callable(other)` and covered the `retry()` overloads. Row guardrails.md: dom-1 removed the test ignore after the widen advice and failed the gate; comp-1, with the caveat, left it and passed (confounded with its guardrails edit).
- **confidence:** medium. Two candidate rollouts agree against base, and dom-1 nearly isolates the skill edit. But each harness ran once, and the test-ignore clause rests on the single dom-1 failure.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `skills/tenacity-change-contract` | confounded | Added §1b5, "Wait composition (`+`, `sum()`, `wait_combine`, `wait_chain`) and the `wait=` value". It says: |  |
| `guardrails.md` | confounded | Broadened "Never edit, skip or weaken an existing test to make it pass" to cover any change to existing test lines, including cosmetic ones such as dropping a now-unused `# type: ignore`, and said to name such a line in the final message instead. | comp-1 left the `test_wait_arbitrary_sum` ignore untouched and wrote "I did not touch it, per the guardrails" (trajectory l.24/603). It passed the gate; dom-1 failed it by editing that line. comp-1 also carried the matching sentence in the §1b5 skill bullet, and no rollout has one change without the other. base-1 also left the line alone with neither change, though it never widened the alias, so the ignore was less clearly unused there. |
| `tool_guidance.md` | no observed effect | Updated the quoted size of `tenacity-change-contract` from ~30 KB to ~35 KB. | All three agents read the skill the same way: `grep -n '^## '` followed by `sed -n` ranges (base l.64/100, dom-1 l.33/81, comp-1 l.156/173). No behaviour differed. |
