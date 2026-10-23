---
name: humanize-time-output
description: Load when a task fixes or changes what a time formatter in src/humanize/time.py returns or raises (naturaldelta, naturaltime, precisedelta, naturalday, naturaldate), e.g. wrong output or an exception for nan/inf, huge, negative or non-numeric inputs.
---

# Changing what a humanize time formatter returns

Check each item against your finished diff.

1. **Unconvertible input returns `str(value)`.** `naturaldelta` (the `try` around
   `int(value)` / `dt.timedelta(seconds=value)`) and `naturaltime` (via `_date_and_delta`, which
   returns `(None, value)`) hand back `str(value)` for input they cannot convert. That is not
   `number.py`'s `_format_not_finite` (`"NaN"`/`"+Inf"`/`"-Inf"`); don't call it from `time.py`.
   `naturaltime` calls `naturaldelta` only after `_date_and_delta` has built a timedelta, so a
   numeric guard inside `naturaldelta` does not reach `naturaltime` or `precisedelta`. Fix only
   the function the task names, and mention the others in the final message.
2. **Imports.** `math` and `datetime as dt` are imported inside the function body in `time.py`
   (`precisedelta` has `import math`); follow that rather than adding a top-level import.
3. **Tests.** `tests/test_time.py::test_naturaldelta` asserts each non-`str` case a second time
   negated (`naturaldelta(-test_input) == expected`), so only inputs whose negation gives the
   same string belong there; `float("inf")` does not (`-inf` → `"-inf"`). Put sign-dependent
   cases in a new parametrized function next to it, with csv names `"test_input, expected"`.
   Error cases use `pytest.raises(<Type>, match=...)` (see `test_time.py` near the
   `minimum_unit="years"` check).
4. **Docstring is the documentation.** `docs/*.md` are `::: humanize.<module>` mkdocstrings
   stubs. If behaviour now matches what the `Returns:`/`Raises:` text already says, leave it;
   if it no longer matches, edit that text.
