# trajectory base-1

final message:
`wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated. The test suite passes: 154 passed, 1 skipped. Ruff and mypy aren't installed in the project's check environment, so I didn't run them.

Changes in `tenacity/wait.py`:
- **`multiplier`**: same meaning as in `wait_exponential`. The wait is `multiplier * 2**n + jitter`, clamped to `[min, max]`.
- **`initial`**: still accepted by keyword or position and warns with `DeprecationWarning`, pointing at the caller. Its value is used as the multiplier.
- **Both passed**: `ValueError` is raised.

I also added `releasenotes/notes/wait-exponential-jitter-multiplier-5c2d9e7a1f3b8d40.yaml` with a features entry and a deprecations entry.

Decisions to check:
- **Parameter placement**: `multiplier` is the last parameter, not the first as in `wait_exponential`. Putting it first would shift the meaning of existing positional calls like `wait_exponential_jitter(10, 5)`, so I kept `initial` first and added `multiplier` at the end.
- **Sentinel defaults**: both parameters default to `None` so that "passed both" can be detected. The effective default is still 1. The signature shows `None`, not `1`.
- **`.initial` attribute**: it's no longer set, so code that reads `.initial` on an instance would break. I didn't add a compatibility property. Say if you want one.

The existing tests that pass `initial` now emit the new warning. I left them alone, as the project guardrails require, and the warning doesn't fail the run.

I checked the behaviour directly: keyword and positional `initial` both warn and compute the same wait as before, `multiplier=2` gives 8.0 on attempt 3 with no jitter, and both `initial` and `multiplier` raise `ValueError`.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"exponential_jitter\\|class wait_exponential\\|multiplier\\|initial\" tenacity/wait.py | head -80; git status --short | head", "description": "Locate wait_exponential_jitter in source"}
[tool_result] 175:class wait_exponential(wait_base):
178:    It allows for a customized multiplier and an ability to restrict the
190:        multiplier: float = 1,
195:        self.multiplier = multiplier
203:            result = self.multiplier * exp
221:    It allows for a custom multiplier and an ability to restrict the upper
226:        wait_random_exponential(multiplier=0.5,  # initial window 0.5s
240:class wait_exponential_jitter(wait_base):
243:    It allows for a customized initial wait, maximum wait, jitter and minimum.
248:    The wait time is max(min, min(initial * 2**n + random.uniform(0, jitter), maximum))
254:        initial: float = 1,
260:        self.initial = initial
270:            result = self.initial * exp + jitter
[tool_use Bash] {"command": "sed -n 1,30p tenacity/wait.py; sed -n 170,290p tenacity/wait.py; grep -rn \"exponential_jitter\\|DeprecationWarning\\|warnings\" --include=*.py --include=*.md --include=*.rst . | grep -v \"^./.venv\" | head -40", "description": "Read wait.py exponential classes and find references"}
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
…[3869 chars elided]…
base
        self.jitter = _utils.to_seconds(jitter)
        self.min = _utils.to_seconds(min)

    def __call__(self, retry_state: "RetryCallState") -> float:
        jitter = random.uniform(0, self.jitter)
        try:
            exp = self.exp_base ** (retry_state.attempt_number - 1)
            result = self.initial * exp + jitter
        except OverflowError:
            result = self.max
        return max(max(0, self.min), min(result, self.max))
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rln \"exponential_jitter\" . --exclude-dir=.git | head; grep -n \"filterwarnings\\|\\[tool.pytest\" -A5 pyproject.toml setup.cfg 2>/dev/null | head -20; grep -n \"initial\" -B3 -A3 tests/test_tenacity.py | head -60; ls <work>/env-tenacity/bin/python 2>&1", "description": "Find tests, docs, config for jitter wait"}
[tool_result] tests/test_tenacity.py
tenacity/__init__.py
tenacity/wait.py
doc/source/index.rst
releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml
releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
94:[tool.pytest.ini_options]
95:filterwarnings = [
96-    "once::DeprecationWarning",
97-]
98-
99-[tool.ruff]
100-line-length = 88
618-        fn(make_retry_state(0, 0))
619-
620-    def test_wait_exponential_jitter_min(self) -> None:
621:        fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)
622-        for _ in range(1000):
623-            # Even for attempt 1 (base wait=1 + jitter 0..1 = 1..2), min=5 applies
624-            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 5, 5)
<work>/env-tenacity/bin/python
[tool_use Bash] {"command": "cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml; cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml; grep -n \"exponential_jitter\" -A12 doc/source/index.rst | head -50; grep -n \"exponential_jitter\" -B2 -A6 tests/test_tenacity.py | head -80; grep -rn \"DeprecationWarning\" tenacity | head", "description": "Read release notes, docs and existing tests"}
[tool_result] ---
features:
  - |
    Add ``min`` parameter to ``wait_exponential_jitter`` to set a minimum wait
    time floor, consistent with ``wait_exponential``. Also accept ``timedelta``
    for ``max``, ``jitter``, and ``min`` parameters.
---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
199:    def wait_exponential_jitter():
200-        print("Randomly wait up to 2^x * 1 seconds between each r
…[1926 chars elided]…
           self._assert_inclusive_range(fn(make_retry_state(4, 0)), 8, 9)
629-
630:    def test_wait_exponential_jitter_timedelta(self) -> None:
631-        from datetime import timedelta
632-
633:        fn = tenacity.wait_exponential_jitter(
634-            max=timedelta(seconds=60),
635-            jitter=timedelta(seconds=1),
636-            min=timedelta(seconds=5),
637-        )
638-        for _ in range(1000):
639-            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 5, 5)
[tool_use Bash] {"command": "grep -n \"requires-python\" pyproject.toml; ls releasenotes/notes | tail -5; grep -rn \"deprecat\" -i releasenotes/notes | head -3", "description": "Check Python version floor and release note conventions"}
[tool_result] 17:requires-python = ">=3.10"
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
releasenotes/notes/drop_deprecated-7ea90b212509b082.yaml:3:  - "Removed `BaseRetrying.call`: was long time deprecated and produced `DeprecationWarning`"
releasenotes/notes/drop_deprecated-7ea90b212509b082.yaml:4:  - "Removed `BaseRetrying.fn`: was noted as deprecated"
releasenotes/notes/drop-deprecated-python-versions-69a05cb2e0f1034c.yaml:4:    Drop support for deprecated Python versions (2.7 and 3.5)
[assistant] Now the implementation. I'm keeping `initial` as the first positional parameter so existing positional calls keep their meaning, and putting `multiplier` last so no existing positional argument shifts.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait, jitter and minimum.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is max(min
…[2012 chars elided]…
ls.to_seconds(max)\n        self.exp_base = exp_base\n        self.jitter = _utils.to_seconds(jitter)\n        self.min = _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp + jitter"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "import abc\nimport random\nimport typing", "new_string": "import abc\nimport random\nimport typing\nimport warnings"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[assistant] Next, a release note, then I'll run the project checks and a few behavioural checks.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-5c2d9e7a1f3b8d40.yaml", "content": "---\nfeatures:\n  - |\n    Add ``multiplier`` parameter to ``wait_exponential_jitter``, consistent with\n    the other exponential wait classes. It defaults to 1.\ndeprecations:\n  - |\n    The ``initial`` parameter of ``wait_exponential_jitter`` is deprecated in\n    favor of ``multiplier``. Passing ``initial`` still works but emits a\n    ``DeprecationWarning``. Passing both ``initial`` and ``multiplier`` raises\n    ``ValueError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-5c2d9e7a1f3b8d40.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -W error::DeprecationWarning -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport warnings\nfrom tenacity import wait_exponential_jitter as W\nfrom tenacity im
…[357 chars elided]…
 w])\n    print('pos initial', W(3, 60, 2, 0)(st(1)), [x.category.__name__ for x in w][-1:])\n    print('multiplier', W(multiplier=2, jitter=0)(st(3)), W(jitter=0)(st(1)))\ntry: W(initial=1, multiplier=2)\nexcept ValueError as e: print('VE', e)\ntry: W(1, 60, 2, 1, 0, 2)\nexcept ValueError as e: print('VE pos', e)\n\" 2>&1", "description": "Run test suite and behavioural checks for new parameter"}
[tool_result] ............s............................................... [ 38%]
........................................................................ [ 85%]
.......................                                                  [100%]
=============================== warnings summary ===============================
tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
  ~/.cache/lithify/work/repo-b58808c83cd1/20261023-164015-api-cleanup-every-other-exponent/base-1/tests/t
…[334 chars elided]…
/test_tenacity.py:621: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
    fn = tenacity.wait_exponential_jitter(initial=1, max=60, jitter=1, min=5)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
154 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.84s
kw initial 4.0 ['DeprecationWarning']
pos initial 3.0 ['DeprecationWarning']
multiplier 8.0 1.0
VE Cannot pass both 'initial' and 'multiplier'
VE pos Cannot pass both 'initial' and 'multiplier'
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; ($PY -m ruff check tenacity/wait.py && $PY -m ruff format --check tenacity/wait.py) 2>&1 | tail -4; $PY -m mypy tenacity/wait.py 2>&1 | tail -2; git status --short", "description": "Run lint, format and type checks on changed file"}
[tool_result] <work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named mypy
 M tenacity/wait.py
?? releasenotes/notes/wait-exponential-jitter-multiplier-5c2d9e7a1f3b8d40.yaml
[assistant] `wait_exponential_jitter` now takes `multiplier` (default 1), and `initial` is deprecated. The test suite passes: 154 passed, 1 skipped. Ruff and mypy aren't installed in the project's check environment, so I didn't run them.

Changes in `tenacity/wait.py`:
- **`multiplier`**: same meaning as in `wait_exponential`. The wait is `multiplier * 2**n + jitter`, clamped to `[min, max]`.
- **`initial`**: still accepted by keyword or position and warns with `DeprecationWarning`, pointing at the caller. Its value is used as the multiplier.
- **Both passed**: `ValueError` is raised.

I also added `relea
…[554 chars elided]…
ature shows `None`, not `1`.
- **`.initial` attribute**: it's no longer set, so code that reads `.initial` on an instance would break. I didn't add a compatibility property. Say if you want one.

The existing tests that pass `initial` now emit the new warning. I left them alone, as the project guardrails require, and the warning doesn't fail the run.

I checked the behaviour directly: keyword and positional `initial` both warn and compute the same wait as before, `multiplier=2` gives 8.0 on attempt 3 with no jitter, and both `initial` and `multiplier` raise `ValueError`.

Nothing is committed.
