# trajectory base-1

final message:
`wait_exponential_jitter` now takes a `min` floor and accepts `datetime.timedelta` or numeric seconds for `max`, `jitter` and `min`. The full test suite passes (154 passed, 1 skipped) using the project's test command.

Changes:
- **`tenacity/wait.py`**: `min` is a new last parameter, so existing positional calls keep their meaning. `max`, `jitter` and `min` go through `_utils.to_seconds`, as in `wait_exponential`. The result is clamped with the same expression `wait_exponential` uses: `max(max(0, min), min(result, max))`. The docstring describes the new behaviour.
- **`tests/test_tenacity.py`**: two new tests, one for `min` and one for timedelta inputs. Existing tests are unchanged.
- **`releasenotes/notes/wait-exponential-jitter-min-timedelta-01852c02ef239a52.yaml`**: a feature note, following the repo's reno format.

Choices I made:
- **`min` wins over `max`.** If `min > max`, the wait is `min`. This matches `wait_exponential`.
- **`initial` stays numeric.** You listed `max`, `jitter` and `min`, so I left `initial` alone. It would be a small follow-up if you want it too.
- **Nothing is committed.** The changes are in the working tree for you to review.

I couldn't run `ruff` or `mypy`, because they aren't in the project's test environment. The new code follows the existing style, but those checks haven't run.

## events
[tool_use Bash] {"command": "git status --short && grep -rn \"wait_exponential\" --include=*.py --include=*.md --include=*.rst . | grep -v \"^./.git/\" | head -50", "description": "Locate wait_exponential references"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short; grep -rn \"wait_exponential\" . --exclude-dir=.git | head -50", "description": "Search repo for wait_exponential references"}
[tool_result] tenacity/wait.py:175:class wait_exponential(wait_base):
tenacity/wait.py:209:class wait_random_exponential(wait_exponential):
tenacity/wait.py:231:    wait_exponential strategy (which uses a fixed interval) may be preferable.
tenacity/wait.py:240:class wait_exponential_jitter(wait_base):
tenacity/__init__.py:76:    wait_exponential,
tenacity/__init__.py:77:    wait_exponential_jitter,
tenacity/__init__.py:798:    "wait_exponential",
tenacity/__init__.py:799:    "wait_exponential_jitter",
tests/t
…[894 chars elided]…
.rst:176:    @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
doc/source/index.rst:177:    def wait_exponential_1():
doc/source/index.rst:199:    def wait_exponential_jitter():
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml:4:    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
[tool_use Bash] {"command": "sed -n 1,40p tenacity/wait.py && echo ---- && sed -n 170,290p tenacity/wait.py && echo ---- && sed -n 590,625p tests/test_tenacity.py && echo ---- && sed -n 185,215p doc/source/index.rst && ls releasenotes/notes | tail -5 && cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml", "description": "Read wait strategies, tests, docs, release notes"}
[tool_result] # Copyright 2016–2021 Julien Danjou
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
…[7277 chars elided]…
, 7s for the next 2 attempts and 9s for all attempts thereafter")
        raise Exception

Whether to retry
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
[tool_use Bash] {"command": "cat tenacity/_utils.py | sed -n 1,80p && echo ---- && cat releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml releasenotes/notes/support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml && echo ---- && grep -n \"time_unit_type\\|to_seconds\" -r tenacity | head -30 && echo ---- && sed -n 330,410p tests/test_tenacity.py && git log --oneline -3 -- tenacity/wait.py", "description": "Read utils, release notes, and wait tests"}
[tool_result] # Copyright 2016 Julien Danjou
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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY
…[7514 chars elided]…
              self.assertEqual(r.wait(make_retry_state(3, 0)), 10)
                self.assertEqual(r.wait(make_retry_state(4, 0)), 10)
                self.assertEqual(r.wait(make_retry_state(5, 0)), 16)
                self.assertEqual(r.wait(make_retry_state(6, 0)), 32)
ae2d75e refactor: enable PGH, PYI ruff rules and rename TCH to TC (#619)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
9686ed7 refactor: enable additional ruff rules and fix violations (#584)
[tool_use Bash] {"command": "sed -n 80,95p tenacity/_utils.py; ls <work>/env-tenacity/bin/python 2>&1; sed -n 60,80p tenacity/__init__.py | head -5; grep -n \"wait_exponential_jitter\\|timedelta\" doc/source/*.rst | head", "description": "Check to_seconds and test env python availability"}
[tool_result] time_unit_type = int | float | timedelta


def to_seconds(time_unit: time_unit_type) -> float:
    return float(
        time_unit.total_seconds() if isinstance(time_unit, timedelta) else time_unit
    )


def is_coroutine_callable(call: typing.Callable[..., typing.Any]) -> bool:
    if inspect.isclass(call):
        return False
    if inspect.iscoroutinefunction(call):
        return True
    partial_call = isinstance(call, functools.partial) and call.func
<work>/env-tenacity/bin/python
# Import all built-in stop strategies for easier usage.
from .stop import (
    stop_after_attempt,
    stop_after_delay,
    stop_all,
doc/source/index.rst:199:    def wait_exponential_jitter():
[assistant] Current `wait_exponential_jitter` takes only numbers, and has no floor. I'll mirror `wait_exponential`: add `min`, convert `max`/`jitter`/`min` with `_utils.to_seconds`, and keep the existing positional order.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is min(initial * 2**
…[1630 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tenacity/wait.py", "old_string": "    The wait time is max(min, min(initial * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count.", "new_string": "    The wait time is min(initial * 2**n + random.uniform(0, jitter), maximum),\n    raised to at least minimum, where n is the retry count."}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now the tests (adding new ones; the existing test stays as it is) and a release note in the repo's reno format.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n", "new_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jit
…[1047 chars elided]…
, min=10)\n\n        self.assertEqual(fn.max, expected.max)\n        self.assertEqual(fn.jitter, expected.jitter)\n        self.assertEqual(fn.min, expected.min)\n\n        for _ in range(1000):\n            self.assertEqual(fn(make_retry_state(1, 0)), 10)\n            self._assert_inclusive_range(fn(make_retry_state(5, 0)), 16, 17)\n            self.assertEqual(fn(make_retry_state(7, 0)), 60)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fd67065479be/20261023-161410-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py has been updated successfully.
[tool_use Bash] {"command": "H=$(python3 -c \"import secrets;print(secrets.token_hex(8))\") && printf -- '---\\nfeatures:\\n  - |\\n    Add a ``min`` argument to ``wait_exponential_jitter``, and accept\\n    ``datetime.timedelta`` values for its ``max``, ``jitter`` and ``min``\\n    arguments, as ``wait_exponential`` does.\\n' > releasenotes/notes/wait-exponential-jitter-min-timedelta-$H.yaml && cat releasenotes/notes/wait-exponential-jitter-min-timedelta-$H.yaml && <work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Add release note and run the project test suite"}
[tool_result] ---
features:
  - |
    Add a ``min`` argument to ``wait_exponential_jitter``, and accept
    ``datetime.timedelta`` values for its ``max``, ``jitter`` and ``min``
    arguments, as ``wait_exponential`` does.
............s............................................... [ 38%]
........................................................................ [ 85%]
.......................                                                  [100%]
154 passed, 1 skipped, 12 subtests passed in 1.95s
[assistant] Tests pass. Let me also run the linters the project uses, if they're available in the environment.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; for t in ruff mypy; do if [ -x $PY/$t ]; then echo \"== $t\"; $PY/$t check tenacity tests 2>&1 | tail -5 || true; fi; done; $PY/ruff format --check tenacity tests 2>&1 | tail -3; $PY/mypy tenacity 2>&1 | tail -3; git status --short", "description": "Run ruff and mypy if installed"}
[tool_result] (eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/mypy
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-jitter-min-timedelta-01852c02ef239a52.yaml
[assistant] `wait_exponential_jitter` now takes a `min` floor and accepts `datetime.timedelta` or numeric seconds for `max`, `jitter` and `min`. The full test suite passes (154 passed, 1 skipped) using the project's test command.

Changes:
- **`tenacity/wait.py`**: `min` is a new last parameter, so existing positional calls keep their meaning. `max`, `jitter` and `min` go through `_utils.to_seconds`, as in `wait_exponential`. The result is clamped with the same expression `wait_exponential` uses: `max(max(0, min), min(result, max))`. The docstring describes the new behaviour.
- **`tests/test_tenacity.py`*
…[132 chars elided]…
-jitter-min-timedelta-01852c02ef239a52.yaml`**: a feature note, following the repo's reno format.

Choices I made:
- **`min` wins over `max`.** If `min > max`, the wait is `min`. This matches `wait_exponential`.
- **`initial` stays numeric.** You listed `max`, `jitter` and `min`, so I left `initial` alone. It would be a small follow-up if you want it too.
- **Nothing is committed.** The changes are in the working tree for you to review.

I couldn't run `ruff` or `mypy`, because they aren't in the project's test environment. The new code follows the existing style, but those checks haven't run.
