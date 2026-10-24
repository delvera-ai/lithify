# trajectory base-1

final message:
Fixed. `@tenacity.retry` now works after `tenacity.tornado = None`.

**The cause:** `tenacity/__init__.py` decided on tornado at decoration time using `_HAS_TORNADO`, but the coroutine check then read `tornado.gen` from the live module global. Setting the global to `None` made that read raise `AttributeError`.

**The fix** (`tenacity/__init__.py`, in `wrap`): the tornado branch now checks the live global, `tornado is not None`, instead of the import-time `_HAS_TORNADO`. `_HAS_TORNADO` is still used for the import-time `TornadoRetrying` import, which is unchanged.

**Tests and checks:**
- **Regression test first:** I added `TestTornadoUnavailableAtDecoration::test_retry_when_tornado_global_is_none` in `tests/test_tornado.py`. Against the unfixed code it failed with the reported `AttributeError: 'NoneType' object has no attribute 'gen'`. It passes after the fix. I only added lines (a new class and `import tenacity`) and changed no existing test lines.
- **Full suite:** `run_tests.py` exit=0, 179 passed, 1 skipped, 15 subtests passed.
- **`check_changed.py`:** exit=0, PASS: 0 problem(s).
- **Not run:** ruff and mypy (unavailable in this environment). The new test's `# type: ignore[assignment]` on `tenacity.tornado = None` mirrors the existing one on the module's `tornado = None`, but I have not confirmed mypy accepts it.

**Extra:** the tenacity change contract calls for a reno note on bug fixes, so I added `releasenotes/notes/tornado-global-none-decorate-de92354979e52525.yaml` under `fixes:`.

Nothing is committed. The changes are in the working tree: `M tenacity/__init__.py`, `M tests/test_tornado.py`, and the new release note.

## events
[tool_use Bash] {"command": "grep -n 'tornado' tenacity/__init__.py; ls .lithify/harness/scripts/; grep -rn 'tornado' tests/*.py | head -30", "description": "Locate tornado references in tenacity and tests"}
[tool_result] 88:    import tornado
90:    tornado = None  # type: ignore[assignment]
92:# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
95:_HAS_TORNADO = tornado is not None
790:            and hasattr(tornado.gen, "is_coroutine_function")
791:            and tornado.gen.is_coroutine_function(f)
805:    from tenacity.tornadoweb import TornadoRetrying
check_changed.py
list_overrides.py
run_tests.py
tests/test_tornado.py:19:from tornado import gen, testing
tests/test_tornado.py:21:from tenacity import RetryError, retry, stop_after_attempt, tornadoweb
tests/test_tornado.py:60:        repr(tornadoweb.TornadoRetrying())
tests/test_tornado.py:62:    def test_old_tornado(self) -> None:
tests/test_tornado.py:67:            # is_coroutine_function was introduced in tornado 4.5;
[tool_use Bash] {"command": "sed -n 82,100p tenacity/__init__.py; echo ---; sed -n 775,820p tenacity/__init__.py; echo ---; grep -n '_HAS_TORNADO' tenacity/__init__.py; echo ---; sed -n 1,80p tests/test_tornado.py", "description": "Read tornado detection and existing tornado tests"}
[tool_result]     wait_random,
    wait_random_exponential,
)
from .wait import wait_random_exponential as wait_full_jitter

try:
    import tornado
except ImportError:
    tornado = None  # type: ignore[assignment]

# mypy resolves `tornado` to the module (it only ever sees the `try` branch),
# so testing the module object for truthiness reads as an always-true check.
# Keep the availability answer in a plain bool instead.
_HAS_TORNADO = tornado is not None

if t.TYPE_CHECKING:
    if sys.version_info >= (3,
…[3296 chars elided]…
    def test_old_tornado(self) -> None:
        old_attr = gen.is_coroutine_function
        try:
            del gen.is_coroutine_function

            # is_coroutine_function was introduced in tornado 4.5;
            # verify that we don't *completely* fall over on old versions
            @retry
            def retryable(thing: NoIOErrorAfterCount) -> None:
                pass

        finally:
            gen.is_coroutine_function = old_attr


if __name__ == "__main__":
    unittest.main()
[tool_use Bash] {"command": "sed -n 1,60p .lithify/harness/scripts/run_tests.py; ls <work>/env-tenacity/bin/python", "description": "Read test runner script and confirm venv python"}
[tool_result] #!/usr/bin/env python3
"""Run pytest in the foreground with a hard time limit; name the test that hangs.

A retry loop with no `stop=` (tenacity's default is never stop, no wait) spins
forever when the predicate under test is wrong, so a single bad test can hang
the whole suite with no output. This script bounds every run and, on timeout,
prints the node id of the test that was running.

Usage (from the repo root, with the project python from memory.md):
    <project python> .lithify/harness/scr
…[1163 chars elided]…
      return 2
        timeout = float(args[1])
        args = args[2:]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "-rfE",
        "-p",
        "no:cacheprovider",
        "--color=no",
        *args,
    ]
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen(
        cmd,
<work>/env-tenacity/bin/python
[assistant] Step 1: the regression test, written before the fix. I'm adding a new test class and leaving existing lines alone.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n\nif __name__ == \"__main__\":", "new_string": "        finally:\n            gen.is_coroutine_function = old_attr\n\n\nclass TestTornadoUnavaila
…[256 chars elided]…
all time.\n        original = tenacity.tornado\n        tenacity.tornado = None  # type: ignore[assignment]\n        try:\n\n            @tenacity.retry\n            def retryable() -> None:\n                pass\n\n        finally:\n            tenacity.tornado = original\n\n        assert type(retryable.retry) is tenacity.Retrying  # type: ignore[attr-defined]\n\n\nif __name__ == \"__main__\":"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\n\nfrom tornado import gen, testing\n\nfrom tenacity import RetryError, retry, stop_after_attempt, tornadoweb", "new_string": "import unittest\nfrom collections.abc import Generator\nfrom typing import Any\n\nfrom tornado import gen, testing\n\nimport tenacity\nfrom tenacity import RetryError, retry, stop_after_attempt, tornadoweb"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tornado.py::TestTornadoUnavailableAtDecoration::test_retry_when_tornado_global_is_none\" > /tmp/red.txt 2>&1; echo \"exit=$?\"; tail -30 /tmp/red.txt", "description": "Run new regression test against unfixed code"}
[tool_result] exit=1

f = <function TestTornadoUnavailableAtDecoration.test_retry_when_tornado_global_is_none.<locals>.retryable at 0x10b6385e0>

    def wrap(f: t.Callable[P, R]) -> _RetryDecorated[P, R]:
        if isinstance(f, retry_base):
            warnings.warn(
                f"Got retry_base instance ({f.__class__.__name__}) as callable argument, "
                f"this will probably hang indefinitely (did you mean retry={f.__class__.__name__}(...)?)",
                stacklevel=2,
            )
 
…[355 chars elided]…
 ^^^^^^^^^^^
            and tornado.gen.is_coroutine_function(f)
        ):
E       AttributeError: 'NoneType' object has no attribute 'gen'

tenacity/__init__.py:790: AttributeError
=========================== short test summary info ============================
FAILED tests/test_tornado.py::TestTornadoUnavailableAtDecoration::test_retry_when_tornado_global_is_none
============================== 1 failed in 0.06s ===============================
---
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] The test fails with the reported `AttributeError`. Step 2: the fix. The decorator should check the live `tornado` global rather than the import-time `_HAS_TORNADO` snapshot.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tenacity/__init__.py", "old_string": "            _HAS_TORNADO\n            and hasattr(tornado.gen, \"is_coroutine_function\")", "new_string": "            tornado is not None\n            and hasattr(tornado.gen, \"is_coroutine_function\")"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tenacity/__init__.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tornado.py::TestTornadoUnavailableAtDecoration::test_retry_when_tornado_global_is_none\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -20 /tmp/check.txt", "description": "Run regression test, full suite, and stdlib checks"}
[tool_result] exit=0

============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0

============== 179 passed, 1 skipped, 15 subtests passed in 1.82s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
changed: tenacity/__init__.py, tests/test_tornado.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] Regression test passes, full suite is green, and the stdlib check passes. This is a bug fix under `tenacity/`, which the project's contract skill says to read, so I'll check what it requires beyond the code.
[tool_use Bash] {"command": "F=.lithify/harness/skills/tenacity-change-contract/SKILL.md; grep -n '^## ' $F; sed -n 1,60p $F", "description": "Read tenacity change contract skill outline"}
[tool_result] 10:## 1. Code goes in the module that owns the concern
19:## 1a. Retry-loop and `statistics` invariants (`tenacity/__init__.py`)
44:## 1a1. Attributes of a `@retry`-decorated function (`fn.statistics`, `fn.retry`, `fn.retry_with`)
77:## 1a2. Give-up path: `TryAgain`, `reraise`, `RetryError` (`tenacity/__init__.py`)
110:## 1b. Strategy composition (`|`, `&`) and sync/async mixing
150:## 1b2. Object state, pickling and copying (`Retrying`, strategies)
192:## 1b3. Arguments of a wait/stop strategy;
…[5833 chars elided]…
` matches). `copy()` always starts with a fresh `_local`, so
  each call gets a new dict.
- `functools.wraps` (`WRAPPER_UPDATES`) copies the inner function's `__dict__` into an outer
  wrapper ONCE, at decoration. An attribute the inner wrapper later rebinds is stale on the
  outer one. Only objects that stay the same and are mutated in place stay visible there.
  `fn.retry` (the original `Retrying`) and `fn.retry_with` are never rebound, so
  `mock.patch.object(outer.retry, ...)` already works.
[tool_use Bash] {"command": "F=.lithify/harness/skills/tenacity-change-contract/SKILL.md; sed -n 379,460p $F; ls releasenotes/notes | tail -5; cat releasenotes/notes/$(ls releasenotes/notes | tail -1)", "description": "Read release note and test requirements from skill"}
[tool_result] ## 2. A release note in `releasenotes/notes/` (reno)
Maintainer commits that change behaviour ship a reno note alongside the code (e.g. #555, #551,
#552, #540). It is not CI-enforced, so it is easy to omit — do not omit it. "Results are
unchanged" is not an exemption: `tenacity/wait.py` fixes that keep every result ship one
(#646 `ValueError` vs `IndexError`, and the annotation-only #392 `fix-wait-typing-*.yaml`).
A user-reported performance problem (e.g. a strategy that gets slower over a long 
…[2912 chars elided]…
.

## 4. Keep the change surface minimal
Do not edit `AGENTS.md`/`CLAUDE.md` (generated by `lithify sync`).
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-radd-int-6f1a3c9d84b2e057.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[assistant] The contract asks for a reno note on bug fixes (`fixes:`). I'll add one, and drop a `# type: ignore[attr-defined]` I wrote that isn't needed, since `retry` is on the `_RetryDecorated` protocol.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py", "old_string": "        assert type(retryable.retry) is tenacity.Retrying  # type: ignore[attr-defined]", "new_string": "        assert type(retryable.retry) is tenacity.Retrying"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261024-220150-bug-setting-the-module-global-te/base-1/tests/test_tornado.py has been updated successfully.
[tool_use Bash] {"command": "H=$(openssl rand -hex 8); cat > releasenotes/notes/tornado-global-none-decorate-${H}.yaml <<'EOF'\n---\nfixes:\n  - |\n    Decorating a function with ``@retry`` no longer raises ``AttributeError`` when the\n    module global ``tenacity.tornado`` has been set to ``None``. Tornado availability is\n    now read at decoration time.\nEOF\nls releasenotes/notes/tornado-global-none-decorate-
…[288 chars elided]…
_when_tornado_global_is_none\" > /tmp/green.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/green.txt; $PY .lithify/harness/scripts/run_tests.py > /tmp/full.txt 2>&1; echo \"exit=$?\"; tail -3 /tmp/full.txt; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"exit=$?\"; tail -4 /tmp/check.txt; git status --short", "description": "Add reno note, then re-run test, suite and checks"}
[tool_result] releasenotes/notes/tornado-global-none-decorate-de92354979e52525.yaml
exit=0
============================== 1 passed in 0.02s ===============================
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
============== 179 passed, 1 skipped, 15 subtests passed in 1.79s ==============
---
exit=0 (pytest); full log: /tmp/run_tests.log
exit=0
changed: releasenotes/notes/tornado-global-none-decorate-de92354979e52525.yaml, tenacity/__init__.py, tests/test_tornado.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
 M tenacity/__init__.py
 M tests/test_tornado.py
?? releasenotes/notes/tornado-global-none-decorate-de92354979e52525.yaml
[assistant] Fixed. `@tenacity.retry` now works after `tenacity.tornado = None`.

**The cause:** `tenacity/__init__.py` decided on tornado at decoration time using `_HAS_TORNADO`, but the coroutine check then read `tornado.gen` from the live module global. Setting the global to `None` made that read raise `AttributeError`.

**The fix** (`tenacity/__init__.py`, in `wrap`): the tornado branch now checks the live global, `tornado is not None`, instead of the import-time `_HAS_TORNADO`. `_HAS_TORNADO` is still used for the import-time `TornadoRetrying` import, which is unchanged.

**Tests and checks:**
- **Reg
…[454 chars elided]…
heck_changed.py`:** exit=0, PASS: 0 problem(s).
- **Not run:** ruff and mypy (unavailable in this environment). The new test's `# type: ignore[assignment]` on `tenacity.tornado = None` mirrors the existing one on the module's `tornado = None`, but I have not confirmed mypy accepts it.

**Extra:** the tenacity change contract calls for a reno note on bug fixes, so I added `releasenotes/notes/tornado-global-none-decorate-de92354979e52525.yaml` under `fixes:`.

Nothing is committed. The changes are in the working tree: `M tenacity/__init__.py`, `M tests/test_tornado.py`, and the new release note.
