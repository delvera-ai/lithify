# trajectory base-1

final message:
Fixed `retry` to check the live `tenacity.tornado` global at decoration time.

Added regression coverage for both `@retry` and `@retry()` with `tornado` set to `None`.

Validation: 180 passed, 1 skipped, 15 subtests passed.

## events
[assistant] I’ll inspect how `retry` checks for Tornado, fix the availability check, and run the project tests.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*tornado*' -g '*test*' -g '__init__.py' | head -60"
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
~/.ca
…[10 chars elided]…
y/work/repo-553f5f2e6879/20261023-202510-bug-setting-the-module-global-te/base-1
releasenotes/notes/Fix-tests-for-typeguard-3.x-6eebfea546b6207e.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
AGENTS.md
tenacity/asyncio/__init__.py
tenacity/tornadoweb.py
tenacity/__init__.py
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/__init__.py
tests/test_utils.py

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git status --short; rg -n \"tornado|def retry\" tenacity/__init__.py tests/test_tornado.py tests/test_tenacity.py; cat AGENTS.md'"
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
tests/test_tornado.py:70:            def retryable(thing: NoIOErrorAfterCount) -> None:
tests/test_tenacity.py:2065:     
…[1389 chars elided]…
t, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->

[command exit=2] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"75,105p\" tenacity/__init__.py; sed -n \"765,815p\" tenacity/__init__.py; cat tests/test_tornado.py; head -85 tests/test_tenacity.py; rg -n \"_HAS_TORNADO|warn_unreachable|mypy|python\" pyproject.toml setup.cfg tox.ini'"
    wait_combine,
    wait_exception,
    wait_exponential,
    wait_exponential_jitter,
    wait_fixed,
    wait_incrementing,
    wait_none,
    wait_random,
    wait_random_exponential,
)
from .wait import wait_random_exponential as wait_full_jitter

try:
    import tornado
except ImportError:
    tornado = None  # type: ignore[assignment]

# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
# so testing the module object for truthiness reads as an always-true check.
…[7141 chars elided]…
ni: No such file or directory (os error 2)
pyproject.toml:17:requires-python = ">=3.10"
pyproject.toml:57:    "mypy==2.3.0",
pyproject.toml:69:mypy = "mypy"
pyproject.toml:87:    { ref = "mypy" },
pyproject.toml:115:[tool.mypy]
pyproject.toml:117:# Match `requires-python`, so results do not depend on which interpreter
pyproject.toml:118:# happens to run mypy. Without this it defaults to the running version and
pyproject.toml:120:python_version = "3.10"
pyproject.toml:125:warn_unreachable = true

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'sed -n \"110,145p\" pyproject.toml; rg -n \""'^class Test|''^def test_" tests/test_tenacity.py | head -20'"'"
    "RUF005",  # iterable unpacking vs concatenation (less readable for tuple +)
    "RUF012",  # mutable class default (test constant, never mutated)
    "SIM108",  # ternary instead of if-else (less readable in context)
]

[tool.mypy]
strict = true
# Match `requires-python`, so results do not depend on which interpreter
# happens to run mypy. Without this it defaults to the running version and
# silently skips checking that the code is valid on the oldest one we support.
python_version = "3.10
…[816 chars elided]…
s TestEnabled:
1740:class TestRetryWith:
1778:class TestBeforeAfterAttempts(unittest.TestCase):
1931:class TestReraiseExceptions(unittest.TestCase):
2000:class TestStatistics(unittest.TestCase):
2052:class TestRetryErrorCallback(unittest.TestCase):
2086:class TestContextManager(unittest.TestCase):
2141:class TestInvokeAsCallable:
2211:class TestRetryException(unittest.TestCase):
2221:class TestRetryTyping(unittest.TestCase):
2275:class TestMockingSleep:
2316:class TestPickle(unittest.TestCase):

[file_change] update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-202510-bug-setting-the-module-global-te/base-1/tenacity/__init__.py, update ~/.cache/lithify/work/repo-553f5f2e6879/20261023-202510-bug-setting-the-module-global-te/base-1/tests/test_tenacity.py
[command exit=0] /bin/zsh -lc 'rtk proxy <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'
................s................................................................................................................ [ 71%]
....................................................                     [100%]
180 passed, 1 skipped, 15 subtests passed in 1.84s

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'ls <work>/env-tenacity/bin/{mypy,ruff}; git diff --check; git diff --stat'"
ls: <work>/env-tenacity/bin/mypy: No such file or directory
ls: <work>/env-tenacity/bin/ruff: No such file or directory
 tenacity/__init__.py   |  2 +-
 tests/test_tenacity.py | 13 +++++++++++++
 2 files changed, 14 insertions(+), 1 deletion(-)

[assistant] Fixed `retry` to check the live `tenacity.tornado` global at decoration time.

Added regression coverage for both `@retry` and `@retry()` with `tornado` set to `None`.

Validation: 180 passed, 1 skipped, 15 subtests passed.
