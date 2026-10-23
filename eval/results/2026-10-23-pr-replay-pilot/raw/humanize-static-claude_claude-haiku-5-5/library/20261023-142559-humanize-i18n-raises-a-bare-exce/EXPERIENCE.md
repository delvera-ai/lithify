# 20261023-142559-humanize-i18n-raises-a-bare-exce

**Task:** `humanize.i18n` raises a bare `Exception` when it cannot determine the default location of its locale folder. `Exception` is too broad: raise `FileNotFoundError` instead (keep the same message). This is not a breaking change, since `FileNotFoundError` is a subclass of `Exception`.

## Transferable lesson

- **cue:** A humanize task that narrows or changes behaviour that existing tests only check loosely. For example, `pytest.raises(Exception, match=...)` still passes after the type is narrowed to a subclass, and would pass if the change were never made. So the existing suite cannot show the new behaviour, and the agent is tempted to "tighten" those assertions.
- **lesson:** In the `skills/<name>` that covers the change, write the verification step as "pin the new behaviour by adding a NEW test function beside the existing one (same setup, same `match`); do not modify any pre-existing test line, even to make it stricter." Do not phrase it as "make sure some test asserts the new type". Agents satisfy that wording by rewriting the existing assertions, which counts as editing existing tests.
- **evidence:** The skills/humanize-error-contract row. dom-1's step-3 wording led it to edit lines 237/246, and its gates failed (`edited-existing-tests=1`). comp-1's wording led it to add a new test function; its gates passed and it was adopted. base-1, with no skill, passed gates but added no test that pins the type.
- **confidence:** medium. The link between the instruction's wording and the test edit is direct: both trajectories cite the skill in their final messages, and the gate outcome follows mechanically from which lines were edited. But there is one rollout per wording, on a single task, and comp-1's wording was written after seeing dom-1's failure.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| `skills/humanize-error-contract` | confounded | Adds a skill to load when a task changes which exception a humanize function raises. Steps 1–2 are the same in both versions: build the message as `msg = ...; raise X(msg)` (ruff `EM`), and update the Google-style `Raises:` docstring, because that docstring is the published doc and there is no CHANGELOG. The two versions differ only in step 3. dom-1: "make sure some test asserts the NEW specific type… Passing the suite is not evidence the new type is raised." comp-1: "Existing tests stay as they are… Do NOT rewrite those lines… add a NEW test function next to the existing ones," plus the note "ruff is not installed in the test env or on PATH". | Both rollouts loaded the skill as their first action. The source change (raise site and docstring) is byte-identical across base-1, dom-1 and comp-1, and base-1 also updated `Raises:` with no skill. So steps 1–2 changed nothing observable. Step 3 is where the runs diverge. |
