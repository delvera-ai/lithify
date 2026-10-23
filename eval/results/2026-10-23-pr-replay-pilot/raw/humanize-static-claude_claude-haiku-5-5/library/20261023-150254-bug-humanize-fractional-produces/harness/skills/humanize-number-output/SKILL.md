---
name: humanize-number-output
description: Load when a task fixes or changes the string a number/filesize formatter returns (fractional, intword, intcomma, apnumber, ordinal, scientific, clamp, metric in src/humanize/number.py, or naturalsize in filesize.py), e.g. wrong output for negative, zero, float or string inputs.
---

# Changing what a humanize number formatter returns

Check each item against your finished diff.

1. **Input guard stays first.** Every public function in `number.py` sends NaN/±Inf to
   `_format_not_finite(...)` before it formats anything. All except `clamp` and `metric` also
   convert the input inside `try` and return `str(value)` on `TypeError`/`ValueError`. Put the
   fix *after* that guard and leave those paths alone. Existing `nan`/`inf`/`"ten"`/`None` cases
   pin them.
2. **Sign check.** Negative output carries exactly one leading `-` (as in `intword`'s
   `negative_prefix` and `naturalsize`'s `abs_bytes`). Check this on the finished diff: run each
   `return` branch of the function you touched with a negative input and confirm there is one
   `-`. This is a check. It is not a reason to restructure the function, so fix only the
   branches that are wrong.
3. **Tests go in the existing parametrize list.** Each public function has one
   `@pytest.mark.parametrize("test_input, expected", ...)` (or `"test_args, expected"`, where
   the args are a list) in `tests/test_<module>.py`. Ruff `PT` requires csv names. Add the new cases to that
   list instead of writing a new test function.
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
