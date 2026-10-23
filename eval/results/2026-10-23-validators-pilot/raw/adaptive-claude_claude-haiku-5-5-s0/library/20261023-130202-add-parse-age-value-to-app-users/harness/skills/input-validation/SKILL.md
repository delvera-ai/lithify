---
name: input-validation
description: Load when adding or changing any function in app/ that parses or validates user input (parse_* functions, anything that raises ValidationError), or when writing tests for one.
---

# Input validators in this repository

## Modules that own the concerns
- `app/errors.py`: `ValidationError(AppError)` is the error a validator raises for bad input.
  Do not raise `ValueError`/`TypeError` or define new exception classes for input rejection.
- `app/audit.py`: `record_rejection(field: str, value: object, reason: str)` appends a dict
  (`field`, `value`, `reason`) to the module-level list `REJECTIONS`. Its docstring is the
  policy: every rejected piece of user input is recorded **before** the error is raised.
- Validators live in the module for their domain: `app/users.py` (user fields),
  `app/orders.py` (order fields). Tests live in `tests/test_<module>.py`.

## INVARIANT: no rejection without an audit record
Every path that raises `ValidationError` for user input first calls `record_rejection`: type
rejections (None, floats, bools, lists), format rejections (non-digit or empty strings), range
rejections, and `except` branches — not just one of them.

- `field`: the input's name, the same noun the error message uses (`"name"`, `"quantity"`, …).
- `value`: the ORIGINAL argument exactly as passed in, not the stripped or converted value.
- `reason`: the same text as the `ValidationError` message.

`parse_name` and `parse_quantity` raise without recording. They are known exceptions to the
policy (the `app/audit.py` docstring says so), not the pattern to follow; "follow the surrounding
code" does not override this. Copy their shape and message style, not the missing call. Do not
retrofit them unless the task asks.

A module-private helper that records then raises is fine when a function has many rejection paths:

```python
from typing import NoReturn

def _reject(field: str, value: object, reason: str) -> NoReturn:
    record_rejection(field, value, reason)
    raise ValidationError(reason)
```

## CONTRACT: a new or changed validator touches
1. The domain module in `app/`: import `from app.audit import record_rejection` next to the
   `ValidationError` import; record before every raise.
2. `tests/test_<module>.py`: add the validator to the existing import line; add accept/reject
   cases. Rejection tests also check that `app.audit.REJECTIONS` gained an entry whose `value` is
   the original input. `REJECTIONS` is module-global and persists across tests, so compare
   entries added by the call (or clear it in a fixture), not the total length.
3. Check the invariant (AST-based; flags any `raise ValidationError` not directly preceded by
   `record_rejection(...)`; `--only` keeps the legacy validators out of the output):
   `<python from memory.md> .lithify/harness/skills/input-validation/scripts/check_audit.py app/<module>.py --only <function>`
