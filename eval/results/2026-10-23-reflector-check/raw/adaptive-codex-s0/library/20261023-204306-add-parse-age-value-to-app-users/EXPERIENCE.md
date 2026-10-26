# 20261023-204306-add-parse-age-value-to-app-users

**Task:** Add `parse_age(value)` to app/users.py. It accepts an int, or a string of decimal digits with optional surrounding whitespace, and returns the age as an int. Valid ages are 0 to 150 inclusive. Anything else (other types, booleans, non-digit strings, negative numbers, ages over 150) must be rejected with `ValidationError`.

## Transferable lesson

- **cue:** Adding or changing input validation where nearby older validators omit a shared rejection-reporting policy.
- **lesson:** Add or retain skills/input-validation with an explicit pointer to app/audit.py, instructions to record the original supplied value before raising, and an explanation that legacy validators are incomplete examples.
- **evidence:** The skills/input-validation row links skill consultation to audited rejection paths and passing gates. The system.md row shows that general helper-inspection guidance alone left the same omission as the base.
- **confidence:** medium — the skill was the sole harness edit in one successful rollout and was visibly consulted before implementation, but the result has not been replicated.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `skills/input-validation` | helped | Added a validation skill requiring rejection auditing through app.audit.record_rejection, preservation of original inputs, and checks for audit behavior; explained that older validators predate the policy. | In a single rollout, context/rollouts/dom-1/trajectory.md shows the agent announcing skill use and reading SKILL.md in its first command, then reading app/audit.py before editing. Its deliverable records original inputs before raising and tests rejection auditing and successful parsing without auditing. context/rollouts/dom-1/gates.md reports all gates passing, with 14/14 holdout cases, versus base-1's 5/14 and missing rejection records. This was dom-1's only harness edit. |
| `system.md` | no observed effect | Replaced the instruction to follow surrounding patterns with an instruction to inspect directly used shared helper contracts, including errors and reporting, before copying patterns. | context/rollouts/inv-1/trajectory.md shows the agent reading app/errors.py alongside app/users.py before editing, but no read of app/audit.py. A later file listing exposed app/audit.py without inspection. Its deliverable still raised ValidationError without recording rejections. context/rollouts/inv-1/gates.md reports the same missing-audit failures and 5/14 holdout cases as base-1; both passed their project tests. |
