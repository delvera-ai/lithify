# 20261023-204358-humanize-i18n-raises-a-bare-exce

**Task:** `humanize.i18n` raises a bare `Exception` when it cannot determine the default location of its locale folder. `Exception` is too broad: raise `FileNotFoundError` instead (keep the same message). This is not a breaking change, since `FileNotFoundError` is a subclass of `Exception`.

## Transferable lesson

- **cue:** A behavior change needs a more specific regression assertion, while existing tests must remain untouched.
- **lesson:** In guardrails.md, explicitly prohibit modifying existing tests even to strengthen assertions, and direct the agent to add separate regression tests.
- **evidence:** The guardrails.md row contrasts base-2’s existing-assertion edits and gate failure with inv-1 and comp-1’s separate regression tests and passing gates. inv-2 preserved existing tests but added no coverage.
- **confidence:** medium — two rollouts carrying the explicit separate-test direction added focused coverage, but baseline behavior varied and each harness variant had only one rollout; causality remains uncertain.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `guardrails.md` | confounded | All variants explicitly prohibited strengthening existing tests. inv-1 and comp-1 additionally directed separate regression tests. inv-2 and comp-1 shortened the secrets prohibition. | In context/rollouts/base-2/trajectory.md, the file_change event modified two existing exception assertions; gates.md reports edited-existing-tests failure despite 684 passing tests. base-1’s file_change touched only source and passed gates, showing baseline variability. In inv-1 and comp-1, the file_change events added separate regression tests asserting FileNotFoundError and the unchanged message; their pytest events report 685 passed, 53 skipped, and both passed gates. inv-2’s file_change touched only source; its pytest event reports 684 passed, 53 skipped, and gates passed. The deliverable patches confirm these differences. No execution effect attributable to shortening the secrets rule was observed. Selection preferred inv-1’s importlib convention, but that does not establish a harness effect. |
