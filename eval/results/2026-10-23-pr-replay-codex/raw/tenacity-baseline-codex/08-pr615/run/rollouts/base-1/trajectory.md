# trajectory base-1

final message:
Implemented standard `pickle` support for `Retrying` and built-in retry strategies.

Restored controllers preserve configuration and statistics and rebuild transient thread state. Regression tests cover fresh and used controllers, strategy behavior, and decorated functions with multiprocessing `Pool.map`.

Checks passed: 186 tests, 1 skipped, 12 subtests.

Custom callbacks must themselves be picklable.

## events
[assistant] I’ll inspect how retry state and strategies are stored, add pickle support and regression tests, then run the project checks.
[command exit=0] /bin/zsh -lc "cat ~/.codex/RTK.md; pwd; rg --files -g 'AGENTS.md' -g '*retry*' -g '*test*' -g 'pyproject.toml' -g 'setup.cfg'"
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
…[447 chars elided]…
ry_if_exception_cause_type-d16b918ace4ae0ad.yaml
releasenotes/notes/do_not_package_tests-fe5ac61940b0a5ed.yaml
releasenotes/notes/add-retry_except_exception_type-31b31da1924d55f4.yaml
releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml
releasenotes/notes/add-test-extra-55e869261b03e56d.yaml
AGENTS.md
tenacity/asyncio/retry.py
tenacity/retry.py
tests/test_after.py
tests/test_tornado.py
tests/test_issue_478.py
tests/test_tenacity.py
tests/test_asyncio.py
tests/test_utils.py
pyproject.toml

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'cat tenacity/retry.py; sed -n \"210,420p\" tenacity/__init__.py; cat pyproject.toml; head -70 tests/test_tenacity.py; cat tenacity/asyncio/retry.py; git status --short'"
# Copyright 2016–2021 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS O
…[27576 chars elided]…
type: ignore[override]
        result = True
        for r in self.retries:
            result = result and await _utils.wrap_to_async_func(r)(retry_state)
            if not result:
                break
        return result

    def __rand__(  # type: ignore[misc,override]
        self, other: "retry_base | async_retry_base"
    ) -> "retry_all":
        if isinstance(other, retry_all):
            return retry_all(*other.retries, *self.retries)
        return retry_all(other, *self.retries)

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tenacity/retry.py'); s=p.read_text(); s=s.replace('super().__init__(lambda e: isinstance(e, exception_types))','super().__init_
…[1884 chars elided]…
       statistics = state.pop(\"_statistics\")
        self.__dict__.update(state)
        self._local = threading.local()
        self._local.statistics = statistics

'''+s[pos:]; p.write_text(s)
PY"

[assistant] Two things block pickling: `Retrying` stores a `threading.local`, and several strategies create local predicate functions. I’ve replaced those predicates with bound methods and added serialization that preserves configuration and statistics while rebuilding transient iteration state.
[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'cat > tests/test_pickle.py <<'\"'\"'PY'\"'\"'
import multiprocessing
import pickle
import re
import sys
import typing

import pytest

import tenacity


@tenacity.retry(s
…[3489 chars elided]…
<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no'"
............s........................................................... [ 39%]
............................................................ [ 71%]
....................................................                     [100%]
183 passed, 1 skipped, 12 subtests passed in 1.87s

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'command -v ruff; git diff --stat; git diff --check; git diff -- tenacity/retry.py tenacity/__init__.py'"
 tenacity/__init__.py | 14 ++++++++++++++
 tenacity/retry.py    | 52 ++++++++++++++++++++++++----------------------------
 2 files changed, 38 insertions(+), 28 deletions(-)
diff --git a/tenacity/__init__.py b/tenacity/__init__.py
index 591f970..a157555 100644
--- a/tenacity/__init__.py
+++ b/tenacity/__init__.py
@@ -256,6 +256,20 @@ class BaseRetrying(ABC):
         self._name = name
         self.enabled = enabled
 
+    def __getstate__(self) -> dict[str, t.Any]:
+        state = self.__dict_
…[3666 chars elided]…
 | None = None,
-        match: None | str | re.Pattern[str] = None,
-    ) -> None:
-        super().__init__(message, match)
-        # invert predicate
-        if_predicate = self.predicate
-        self.predicate = lambda *args_, **kwargs_: not if_predicate(*args_, **kwargs_)
+    def _predicate(self, exception: BaseException) -> bool:
+        return not super()._predicate(exception)
 
     def __call__(self, retry_state: "RetryCallState") -> bool:
         if retry_state.outcome is None:

[command exit=0] /bin/zsh -lc "rtk proxy sh -c 'git status --short --untracked-files=all; ls tests/test_pickle.py; cat .gitignore; ls <work>/env-tenacity/bin'"
 M tenacity/__init__.py
 M tenacity/retry.py
?? tests/test_pickle.py
tests/test_pickle.py
.idea
dist
*.pyc
*.egg-info
build
.venv/
uv.lock
AUTHORS
ChangeLog
doc/_build

tenacity/_version.py
/.pytest_cache
.lithify/runs/
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
py.test
pydoc.bat
pygmentize
pytest
python
python3
python3.12

[command exit=0] /bin/zsh -lc "rtk proxy python - <<'PY'
from pathlib import Path
p=Path('tests/test_pickle.py'); s=p.read_text().replace('import typing\\n',''); s=s.replace('@pytest.mark.parametrize(\"used\", [False,
…[623 chars elided]…
 <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no"
............s........................................................... [ 38%]
............................................................ [ 70%]
.......................................................                  [100%]
186 passed, 1 skipped, 12 subtests passed in 1.92s

[command exit=0] /bin/zsh -lc 'rtk git diff --check'


[assistant] Implemented standard `pickle` support for `Retrying` and built-in retry strategies.

Restored controllers preserve configuration and statistics and rebuild transient thread state. Regression tests cover fresh and used controllers, strategy behavior, and decorated functions with multiprocessing `Pool.map`.

Checks passed: 186 tests, 1 skipped, 12 subtests.

Custom callbacks must themselves be picklable.
