# 20261023-125452-add-parse-age-value-to-app-users

**Task:** Add `parse_age(value)` to app/users.py. It accepts an int, or a string of decimal digits with optional surrounding whitespace, and returns the age as an int. Valid ages are 0 to 150 inclusive. Anything else (other types, booleans, non-digit strings, negative numbers, ages over 150) must be rejected with `ValidationError`.

## Transferable lesson

- **cue:** Adding or changing a user-input validator where nearby legacy validators omit a documented rejection side effect.
- **lesson:** In skills/input-validation, require reading the authoritative rejection contract before copying neighboring validators, preserving original inputs for required audit calls, and testing rejection side effects alongside accepted results. Explain explicitly when legacy validators predate the contract.
- **evidence:** Both edit rows show pre-edit inspection of app/audit.py and audited rejection implementations. All three candidate rollouts passed the recorded audit gates; base-1 inspected only the target and tests, omitted auditing, and passed local tests while failing rejection-audit gates.
- **confidence:** medium — three skill-bearing rollouts support the same concrete contrast, but each harness variant ran once, and the record does not isolate explicit contract wording from investigation and verification instructions.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `skills/validation-workflow` | confounded | Added a workflow requiring investigation of exception definitions, related validators, documented rejection side effects, and tests of those effects. | In context/rollouts/inv-1/trajectory.md, after loading the skill and before editing, the agent read app/errors.py, app/orders.py, and app/audit.py and searched for validation and rejection references. Base-1 read only the target module and its tests. Inv-1’s deliverable records original rejected inputs and restores audit state after rejection tests; its gates passed 14/14 cases. Base-1 passed local tests but failed nine rejection-audit cases (context/rollouts/base-1/gates.md). |
| `skills/input-validation` | confounded | Both versions added the explicit rejection-audit contract, original-input preservation, and a warning against copying older unaudited validators. Comp-1 additionally required source investigation and focused side-effect tests. | In both trajectories, the agent loaded the skill, read app/audit.py before editing, and explicitly committed to auditing original inputs. Both deliverables added audit calls and acceptance/rejection audit assertions; both gates passed 14/14 cases, unlike base-1. Comp-1 also restored audit state in rejection tests and normalized accepted int subclasses; dom-1 did neither (their deliverable.patch files). These differences do not isolate the added workflow instructions, and selection of comp-1 does not establish their cause. |
