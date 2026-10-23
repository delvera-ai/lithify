# trajectory inv-1

final message:
Added `parse_age(value)` with the requested type and range validation. Rejections raise `ValidationError` and record the original input per repository policy.

All 34 tests pass; `git diff --check` passes.

## events
[assistant] I’ll read the validation code and workflow instructions, add `parse_age`, and run the project checks.
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

[command exit=0] /bin/zsh -lc "cat .agents/skills/validation-workflow/SKILL.md; rg --files -g 'AGENTS.md' -g '*.py' -g 'pyproject.toml'"
---
name: validation-workflow
description: Load when adding or changing input validation, parsers, or rejection paths that raise repository-defined exceptions.
---

Before editing, trace the rejection path beyond the target function:

1. Read the exception definition and its imports, then search the repository for its callers and related validation helpers. Read the relevant implementations and tests, including any documented side effects. Reading only the target module and its tests is insuffic
…[528 chars elided]…
rn values and exception types. Do not change existing tests to accommodate the implementation.
4. Run the project checks documented in repository memory and read their output before finishing. Check the rejection side effects against the source contract as well: a passing local suite alone does not establish that those effects were preserved. Report any unverified contract explicitly.
AGENTS.md
tests/test_users.py
app/errors.py
app/orders.py
app/__init__.py
app/users.py
app/audit.py
conftest.py

[command exit=0] /bin/zsh -lc 'rtk proxy cat app/users.py app/errors.py app/orders.py app/audit.py tests/test_users.py conftest.py AGENTS.md'
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
…[1733 chars elided]…
# Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `python -m pytest -q`.

### Skills (load on demand)

- `validation-workflow` — Load when adding or changing input validation, parsers, or rejection paths that raise repository-defined exceptions.
<!-- lithify:end -->

[command exit=0] /bin/zsh -lc "rtk rg -n 'ValidationError|validation|reject' . --glob '"'!*.lock'"'"
./CLAUDE.md:21:- `validation-workflow` — Load when adding or changing input validation, parsers, or rejection paths that raise repository-defined exceptions.
./AGENTS.md:21:- `validation-workflow` — Load when adding or changing input validation, parsers, or rejection paths that raise repository-defined exceptions.
./tests/test_users.py:3:from app.errors import ValidationError
./tests/test_users.py:12:def test_parse_name_rejects(bad):
./tests/test_users.py:13:    with pytest.raises(ValidationErro
…[390 chars elided]…
Policy: every rejected piece of user input must be recorded with
./app/audit.py:4:`record_rejection(field, value, reason)` before the error is raised, so that support can see
./app/audit.py:11:def record_rejection(field: str, value: object, reason: str) -> None:
./app/orders.py:1:from app.errors import ValidationError
./app/orders.py:9:        raise ValidationError("quantity must be a whole number") from None
./app/orders.py:11:        raise ValidationError("quantity must be between 1 and 999")

[assistant] I’m using the `validation-workflow` skill. The audit module requires recording rejected input before raising an error, so `parse_age` will preserve the original value in that record. I’ll test this alongside accepted values and rejection cases.
[file_change] update ~/.cache/lithify/work/repo-d7766e460f47/20261023-125452-add-parse-age-value-to-app-users/inv-1/app/users.py
[file_change] update ~/.cache/lithify/work/repo-d7766e460f47/20261023-125452-add-parse-age-value-to-app-users/inv-1/tests/test_users.py
[command exit=0] /bin/zsh -lc 'rtk proxy python -m pytest -q'
..................................                                       [100%]
34 passed in 0.01s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Added `parse_age(value)` with the requested type and range validation. Rejections raise `ValidationError` and record the original input per repository policy.

All 34 tests pass; `git diff --check` passes.
