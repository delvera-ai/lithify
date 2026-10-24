# trajectory base-1

final message:
Added `parse_email(value)` with the requested normalization and validation. Rejections raise `ValidationError` and audit the original input, as required by project policy.

Added tests for valid and invalid inputs. All 57 tests pass; `git diff --check` passes.

## events
[assistant] I’ll read the validation guidance and existing code, add `parse_email`, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; cat .agents/skills/input-validation/SKILL.md; cat app/users.py; rg --files -g '*test*' -g AGENTS.md"
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
…[1985 chars elided]…
value.strip().isdecimal():
        age = 0
        for digit in value.strip():
            age = age * 10 + int(digit)
            if age > 150:
                break
    else:
        record_rejection("age", value, reason)
        raise ValidationError(reason)

    if not 0 <= age <= 150:
        reason = "age must be between 0 and 150"
        record_rejection("age", value, reason)
        raise ValidationError(reason)
    return age
AGENTS.md
tests/test_users.py
tests/test_age.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat tests/test_users.py tests/test_age.py app/audit.py app/errors.py'
import pytest
from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips():
    assert parse_name("  Ada Lovelace ") == "Ada Lovelace"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 81, None, 42])
def test_parse_name_rejects(bad):
    with pytest.raises(ValidationError):
        parse_name(bad)
import pytest

from app.audit import REJECTIONS
from app.errors import ValidationError
from app.users import parse_age


@pytest.mark.parametrize(
    "value
…[965 chars elided]…
eason)` before the error is raised, so that support can see
what users actually typed. Some older validators predate this policy and do not follow it yet.
"""

REJECTIONS: list[dict] = []


def record_rejection(field: str, value: object, reason: str) -> None:
    REJECTIONS.append({"field": field, "value": value, "reason": reason})
class AppError(Exception):
    """Base class for every error this service raises on purpose."""


class ValidationError(AppError):
    """User input was rejected."""

[assistant] I’m applying the `input-validation` skill, which requires auditing rejected inputs with their original values. I’ll include that in `parse_email` and test both normalization and rejection behavior.
[file_change] update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204645-add-parse-email-value-to-app-use/base-1/app/users.py, add ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204645-add-parse-email-value-to-app-use/base-1/tests/test_email.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
.........................................................                [100%]
57 passed in 0.02s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Added `parse_email(value)` with the requested normalization and validation. Rejections raise `ValidationError` and audit the original input, as required by project policy.

Added tests for valid and invalid inputs. All 57 tests pass; `git diff --check` passes.
