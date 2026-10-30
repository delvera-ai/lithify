---
name: sqlglot-optimizer-placebo
description: Load when a task changes a sqlglot optimizer pass (sqlglot/optimizer/*.py — qualify_tables, qualify_columns, qualify, annotate_types, simplify, …) or any code that rewrites an existing AST in place (`.set(...)`, `.replace(...)`, rebuilding aliases / alias column lists / identifiers / ColumnDefs from pieces of the input tree), including crashes such as "Name needs to be a string or an Identifier" or "'NoneType' object has no attribute ..." on a missing `.type` / arg (canonicalize, simplify, annotate_types).
---

# Changing a Compiler Optimizer Pass

Optimizer passes are small rewrite steps that run in sequence over a parsed program tree. A change to one pass can alter output for many unrelated inputs, so work in small, verified steps and keep the blast radius of each edit as narrow as possible.

## Before editing

- Read the pass's docstring first. It states the contract the pass promises: which inputs it accepts, what shape it returns, and which invariants later steps rely on.
- Read the existing tests for that pass, including the edge cases they name. Tests usually record decisions a previous author made on purpose, and they show the expected output format better than prose does.
- Find out which other steps call into the code you are about to change. A helper used by one pass is often used by two or three more.

## Reproduce first

- Write a minimal input that triggers the bug. Strip it down until removing any further piece makes the failure disappear.
- Run the pass on that input and record the exact output or traceback. Keep the record so you can compare it after the fix.
- If the failure is a crash such as a missing attribute or a type error on a value that is sometimes absent, confirm which branch sees the absent value before changing anything.

## Making the change

- Keep the fix in the smallest function that owns the behavior. Prefer guarding the one branch that fails over restructuring the whole pass.
- Do not change the shape of data that other steps receive unless the task asks for it.
- Keep the code style of the surrounding module. Use the same helper names and error types the file already uses.
- Leave unrelated cleanups for a separate change, even when they are tempting.

## Verifying

- Run the full test file for the pass, not only the new test. A passing single test can hide a regression in a neighboring case.
- Run the tests for dialects and other integration suites that exercise the same pass. Unrelated dialect tests catch changes that alter output for syntax you did not intend to touch.
- Run the project's linter and type checker on the changed files.
- Compare the output for your minimal input before and after the change. The only difference should be the one you intended.

## Adding a regression test

- Add the regression test next to the existing tests for the pass, using the same fixture format and naming scheme.
- Use the minimal reproduction from earlier as the input, and assert the exact expected output rather than only that no error is raised.
- Include one neighboring case that worked before, so the test guards both the fix and the unchanged behavior.

## Reporting

- State in the summary which branch was broken, what the minimal input was, and which other test suites you ran.
- Note any output change you saw in unrelated tests, even if you judged it acceptable.

## Edge inputs

- Think about every input shape the pass can receive, not only the common one. Consider empty inputs, nested inputs, inputs where an optional part is missing, and inputs produced by an earlier step rather than by the parser.
- For each shape, decide what the pass should do and write that down in a sentence before writing code. A sentence makes it easier to notice when the code and the intent disagree.
- When two behaviors are both defensible, prefer the one the existing tests already assume, and mention the choice in the summary.
- Check whether the pass is idempotent on its own output. Running it twice on the same input should give the same result as running it once, unless the contract says otherwise.
- Try inputs that are valid but unusual, such as very long names, mixed letter case, or quoted and unquoted forms of the same word. Passes that look correct on plain input often break on these.
- Confirm that an input the pass should reject still produces the same error message as before. Changed error text can break callers that match on it.

## Common pitfalls

- Fixing a symptom at the crash site instead of at the point where the bad value first appeared. Trace back to the step that produced the missing or wrong value.
- Adding a broad exception handler that hides the failure. A narrow check on the specific condition is almost always the better fix.
- Changing the order in which steps run. Ordering often matters more than the code inside any single step, and the effect may only appear in later tests.
- Assuming that a value is present because the common case always has it. Optional parts are absent far more often than new readers expect.
- Updating a test expectation to match new output without understanding why the output changed. Expectations are evidence of intent, so a changed expectation needs its own justification.

## Keeping the review small

- Split large changes into a fix commit and a cleanup commit. The reviewer can then check the behavior change without reading unrelated formatting.
- Describe the minimal input in the commit message, so a future reader can reproduce the bug without rereading the whole thread.
- Name the test file and the test that guards the fix. A reviewer should be able to find the regression check in one step.
- If a second bug appears while you work, record it separately rather than widening the current change to cover it.

## Working in a shared codebase

- Assume that other contributors depend on the current behavior of shared helpers, even when the behavior looks accidental.
- If a helper needs a new option, add the option with a default that preserves the old behavior, then update the callers one at a time.
- Keep public names and signatures stable unless the task explicitly covers a rename.
- When you finish, list the files you touched so the reviewer knows the scope of the change at a glance.
