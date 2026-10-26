# trajectory dom-1

final message:
Added `parse_age(value)` with type, decimal-digit, and 0–150 range validation. Rejections raise `ValidationError` and audit the original input as required.

All 33 tests pass.

## events
[assistant] I’ll read the validation guidance, add `parse_age`, and run the project checks. I’m using the input-validation skill for this parser change.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; cat .agents/skills/input-validation/SKILL.md; rg --files -g 'AGENTS.md' -g '*.py' -g 'pyproject.toml'"
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
---
name: input-va
…[875 chars elided]…
 that successful parsing does not record a rejection.

The older `parse_name` in `app/users.py` and `parse_quantity` in `app/orders.py` raise errors without recording them. `app/audit.py` explicitly identifies older validators as predating the policy; their omission is not the contract for new validation. Keep changes within the task's scope rather than migrating unrelated validators.
AGENTS.md
tests/test_users.py
app/errors.py
app/orders.py
app/__init__.py
app/users.py
app/audit.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat app/users.py app/errors.py app/audit.py app/orders.py tests/test_users.py conftest.py'
from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
class AppError(Exception):
    """Base class for every error this service raises on purpose."""


class ValidationEr
…[832 chars elided]…
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
# Root conftest: puts the repository root on sys.path so tests can `import app`.

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/dom-1/app/users.py
[file_change] add ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/dom-1/tests/test_age.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
.................................                                        [100%]
33 passed in 0.01s

[assistant] Added `parse_age(value)` with type, decimal-digit, and 0–150 range validation. Rejections raise `ValidationError` and audit the original input as required.

All 33 tests pass.
