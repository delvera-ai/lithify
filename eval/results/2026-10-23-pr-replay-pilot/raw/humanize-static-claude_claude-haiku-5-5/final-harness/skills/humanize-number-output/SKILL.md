---
name: humanize-number-output
description: Load when a task fixes or changes the string a number/filesize formatter returns (fractional, intword, intcomma, apnumber, ordinal, scientific, clamp, metric in src/humanize/number.py, or naturalsize in filesize.py), e.g. wrong output or an exception (OverflowError on very large ints) for negative, zero, float, huge-int or string inputs.
---

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Keep the
   NaN/±Inf and `str(value)` results as they are; existing `nan`/`inf`/`"ten"`/`None` cases
   pin them.
   The guard itself calls `float(value)`: `if not math.isfinite(float(value))` in `ordinal`,
   `intword`, `apnumber` and `intcomma` (both its `str` and non-`str` branches);
   `float(value)` first in `fractional` and `scientific`. For an `int` beyond float range
   (about `10**309`) that raises `OverflowError`, which the `except (TypeError, ValueError)`
   does not catch. If the task's bug is that guard, change it for the input type the task names
   only (an `int` can't be NaN/Inf). Leave the `str` branch and the other input types going
   through `float()`. Then run the same large input through the other functions that share the
   guard and name any that still raise in the final message, without fixing them.
   Also: `bool` is an `int` subclass, and `f"{value:,.{ndigits}f}"` converts an `int` to float,
   so explicit `ndigits` still overflows on such an int.
2. **Sign check.** Negative output carries exactly one leading `-` (as in `intword`'s
   `negative_prefix` and `naturalsize`'s `abs_bytes`). Check this on the finished diff: run each
   `return` branch of the function you touched with a negative input and confirm there is one
   `-`. This is a check. It is not a reason to restructure the function, so fix only the
   branches that are wrong.
3. **Tests go in the existing parametrize list.** Each public function has one
   `@pytest.mark.parametrize("test_input, expected", ...)` (or `"test_args, expected"`, where
   the args are a list) in `tests/test_<module>.py`. Ruff `PT` requires csv names. Add the new cases to that
   list instead of writing a new test function. Inputs may be expressions (`[10**100]`);
   `expected` is a string literal in every existing case. Don't build it with the same
   format call the function uses (e.g. `f"{x:,}"` for `intcomma`), since that test passes for
   any grouping. If a literal is too long, assemble it from pieces such as `"10" + ",000" * 132 + ",123"`.
   `tests/test_filesize.py::test_naturalsize` asserts each case a second time with the first
   argument negated (`*-1` for ints, `"-"` prefixed for strings and floats). Only positive
   inputs belong there. Its positional args are `(value, binary, gnu, format)`. `gnu=True`
   uses base 1024 even when `binary=False` (so `999999` with gnu is `976.6K`, not a carry case).
4. **Docstring `Examples:` are not checked.** They are written as doctests (```` ```pycon ````),
   but the project's pytest command does not collect them, because pyproject `[tool.pytest]`
   with `testpaths = ["tests"]` overrides `--doctest-modules` in tox.ini's `[pytest]`. If your
   change alters an output that an `Examples:` block shows, edit that block by hand. The
   `docs/*.md` files are `::: humanize.<module>` mkdocstrings stubs, so the docstring is the
   published documentation.
