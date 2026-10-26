# trajectory base-1

final message:
Added `parse_age(value)` with type, decimal-string, and 0–150 range validation. Invalid inputs raise `ValidationError`, including booleans.

Added coverage for boundaries and invalid inputs. All 34 tests pass.

## events
[assistant] I’ll check the existing validation patterns, add `parse_age`, and run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*users*' -g '*test*' -g 'pyproject.toml' -g 'requirements*'"
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
~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/base-1
AGENTS.md
tests/test_users.py
app/users.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat app/users.py tests/test_users.py AGENTS.md'
from app.errors import ValidationError


def parse_name(value: str) -> str:
    """Return a display name: surrounding whitespace removed, 1-80 characters."""
    if not isinstance(value, str):
        raise ValidationError("name must be a string")
    name = value.strip()
    if not 1 <= len(name) <= 80:
        raise ValidationError("name must be 1-80 characters")
    return name
import pytest
from app.errors import ValidationError
from app.users import parse_name


def test_parse_name_strips()
…[539 chars elided]…
he relevant
code before editing it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `python -m pytest -q`.
<!-- lithify:end -->

[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[file_change] update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/base-1/app/users.py, update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/base-1/tests/test_users.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
..................................                                       [100%]
34 passed in 0.02s

[assistant] Added `parse_age(value)` with type, decimal-string, and 0–150 range validation. Invalid inputs raise `ValidationError`, including booleans.

Added coverage for boundaries and invalid inputs. All 34 tests pass.
