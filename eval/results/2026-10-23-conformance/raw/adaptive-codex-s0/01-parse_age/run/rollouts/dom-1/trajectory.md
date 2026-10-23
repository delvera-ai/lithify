# trajectory dom-1

final message:
Added `parse_age(value)` with type, decimal-string, and 0–150 range validation. Every rejection raises `ValidationError` and audits the original input.

All 33 tests pass.

## events
[assistant] I’ll read the existing validation code and input-validation skill, add `parse_age`, and run the project checks.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```

[command exit=0] /bin/zsh -lc 'cat .agents/skills/input-validation/SKILL.md'
---
name: input-validation
description: Load when adding or changing user-input parsers or validators in this repository; enforce the rejection audit contract.
---

# Input validation contract

INVARIANT: `app/audit.py` requires every rejected piece of user input to be recorded with `record_rejection(field, value, reason)` before the error is raised. Use that helper, which owns the `REJECTIONS` audit trail. Input rejection errors use `ValidationError` from `app.errors`.

Preserve the original in
…[339 chars elided]…
nd range failures. Check that each path records the original value before raising `ValidationError`; accepting valid input must not produce a rejection record.

`app/users.py:parse_name` and `app/orders.py:parse_quantity` are older validators that omit auditing. `app/audit.py` explicitly warns that older validators predate the policy, so their missing audit calls are not a convention to copy. Apply the contract to the requested change without expanding the task into unrelated validator repairs.

[command exit=0] /bin/zsh -lc "rg --files -g 'AGENTS.md' -g '*.py' -g 'pyproject.toml'"
AGENTS.md
tests/test_users.py
app/errors.py
app/orders.py
app/__init__.py
app/users.py
app/audit.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat app/users.py app/audit.py app/errors.py app/orders.py tests/test_users.py'
from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
"""Audit trail for rejected user input.

Policy: every rejected piece of user input must be recorded with
`record_re
…[752 chars elided]…
"quantity must be a whole number") from None
    if not 1 <= qty <= 999:
        raise ValidationError("quantity must be between 1 and 999")
    return qty
import pytest

from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[assistant] The input-validation skill requires every rejection to be audited with the original value. I’ll apply that to type, format, and range errors, and use `isdecimal()` to recognize decimal digit strings.
[file_change] update ~/.cache/lithify/work/repo-d7766e460f47/20261023-125452-add-parse-age-value-to-app-users/dom-1/app/users.py
[file_change] update ~/.cache/lithify/work/repo-d7766e460f47/20261023-125452-add-parse-age-value-to-app-users/dom-1/tests/test_users.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
.................................                                        [100%]
33 passed in 0.01s

[assistant] Added `parse_age(value)` with type, decimal-string, and 0–150 range validation. Every rejection raises `ValidationError` and audits the original input.

All 33 tests pass.
