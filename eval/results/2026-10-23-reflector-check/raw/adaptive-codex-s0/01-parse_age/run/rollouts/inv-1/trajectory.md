# trajectory inv-1

final message:
Added `parse_age(value)` with type checking, whitespace trimming, decimal digit validation, and inclusive 0–150 bounds. Invalid inputs raise `ValidationError`, including booleans.

All 34 tests pass.

## events
[assistant] I’ll check the existing validation helpers, add `parse_age`, and run the project checks.
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

[command exit=0] /bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '*users*' -g '*error*' -g '*test*' -g 'pyproject.toml' -g 'requirements*'"
~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/inv-1
AGENTS.md
tests/test_users.py
app/errors.py
app/users.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat app/users.py app/errors.py tests/test_users.py conftest.py AGENTS.md'
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
…[796 chars elided]…
g,
before copying surrounding patterns. Finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `python -m pytest -q`.
<!-- lithify:end -->

[command exit=0] /bin/zsh -lc 'rtk git status --short; rtk rg --files app tests'
oktests/test_users.py
app/errors.py
app/orders.py
app/__init__.py
app/users.py
app/audit.py

[file_change] update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/inv-1/app/users.py, update ~/.cache/lithify/work/repo-04dafa58d9f0/20261023-204306-add-parse-age-value-to-app-users/inv-1/tests/test_users.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
..................................                                       [100%]
34 passed in 0.01s

[assistant] Added `parse_age(value)` with type checking, whitespace trimming, decimal digit validation, and inclusive 0–150 bounds. Invalid inputs raise `ValidationError`, including booleans.

All 34 tests pass.
