# trajectory base-1

final message:
`wait_exponential_jitter` now takes a `min` floor and accepts `timedelta` for `max`, `jitter` and `min`, alongside plain seconds. The full suite passes (154 passed, 1 skipped), and the project's test command was used for that run.

Changes:

- **`tenacity/wait.py`**: `min` is the last parameter, so existing positional calls such as `wait_exponential_jitter(10, 5)` still work. `max`, `jitter` and `min` go through `_utils.to_seconds`, as `wait_exponential` and `wait_fixed` do. The result is `max(min, min(result, max))`, the same clamp order `wait_exponential` uses, so the floor always holds. The docstring describes the new formula.
- **`tests/test_tenacity.py`**: two new tests, one for `min` and one that runs seconds and `timedelta` inputs through the same assertions. No existing test was edited.
- **`releasenotes/notes/wait_exponential_jitter-min-8b3b51ca1054a6af.yaml`**: a reno note for the two features, following the repo's existing notes.

Decisions to check:

- **`initial` is still seconds only.** It wasn't in your request, and it's the one value that isn't consistent with `wait_exponential`'s `multiplier`, which does take timedeltas. Passing a timedelta as `initial` will fail. I can add conversion for it if you want the same treatment.
- **`min` is applied after jitter.** Attempts whose computed wait falls below `min` all wait exactly `min`, so jitter disappears in those early attempts. This matches the "floor" you described. It differs from `wait_random_exponential`, where `min` is the lower bound of the random range.

Ruff and mypy aren't installed in the project's test environment or on the PATH here, so I didn't run them. I checked the line lengths in the edited files against the 88-column limit by hand, and the only over-length lines are pre-existing.

## events
[assistant] I'll start by reading the current `wait_exponential_jitter` and `wait_exponential` implementations and their tests.
[tool_use Bash] {"command": "git status --short && ls && grep -rn \"wait_exponential\" --include=*.py --include=*.md --include=*.rst . | grep -v \"^./.git/\" | head -50", "description": "Check repo state and find wait_exponential references"}
[tool_result] AGENTS.md
CLAUDE.md
LICENSE
README.rst
doc
pyproject.toml
releasenotes
reno.yaml
tenacity
tests
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short && grep -rn \"exponential\" tenacity doc tests README.rst releasenotes | head -80 && cat AGENTS.md | head -80", "description": "Check git status, grep exponential references, read AGENTS.md"}
[tool_result] tenacity/wait.py:175:class wait_exponential(wait_base):
tenacity/wait.py:176:    """Wait strategy that applies exponential backoff.
tenacity/wait.py:185:    wait_random_exponential for the latter case.
tenacity/wait.py:209:class wait_random_exponential(wait_exponential):
tenacity/wait.py:210:    """Random wait with exponentially widening window.
tenacity/wait.py:212:    An exponential backoff strategy used to mediate contention between multiple
tenacity/wait.py:214:    is the sense in which "exp
…[5003 chars elided]…
it, and finish only after the project's checks pass.

### Guardrails

- Never edit, skip or weaken an existing test to make it pass; fix the code instead.
- Never add credentials, tokens or secrets to the repository.

### Durable project memory

- The project's checks run with `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no`.
<!-- lithify:end -->
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tenacity/wait.py"}
[tool_result] 1	# Copyright 2016–2021 Julien Danjou
2	# Copyright 2016 Joshua Harlow
3	# Copyright 2013-2014 Ray Holder
4	#
5	# Licensed under the Apache License, Version 2.0 (the "License");
6	# you may not use this file except in compliance with the License.
7	# You may obtain a copy of the License at
8	#
9	# http://www.apache.org/licenses/LICENSE-2.0
10	#
11	# Unless required by applicable law or agreed to in writing, software
12	# distributed under the License is distributed on an "AS IS" BASIS,
13	# WITH
…[9266 chars elided]…
tial = initial
260	        self.max = max
261	        self.exp_base = exp_base
262	        self.jitter = jitter
263	
264	    def __call__(self, retry_state: "RetryCallState") -> float:
265	        jitter = random.uniform(0, self.jitter)
266	        try:
267	            exp = self.exp_base ** (retry_state.attempt_number - 1)
268	            result = self.initial * exp + jitter
269	        except OverflowError:
270	            result = self.max
271	        return max(0, min(result, self.max))
272	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py", "offset": 330, "limit": 300}
[tool_result] 330	        times.add(r.wait(make_retry_state(1, 6546)))
331	        times.add(r.wait(make_retry_state(1, 6546)))
332	
333	        # this is kind of non-deterministic...
334	        self.assertTrue(len(times) > 1)
335	        for t in times:
336	            self.assertTrue(t >= 0)
337	            self.assertTrue(t <= 2)
338	
339	    def test_exponential(self) -> None:
340	        r = Retrying(wait=tenacity.wait_exponential())
341	        self.assertEqual(r.wait(make_retry_state(1, 0)), 1)
342	  
…[13581 chars elided]…
ter()
618	        fn(make_retry_state(0, 0))
619	
620	    def test_wait_retry_state_attributes(self) -> None:
621	        class ExtractCallState(Exception):
622	            pass
623	
624	        # retry_state is mutable, so return it as an exception to extract the
625	        # exact values it has when wait is called and bypass any other logic.
626	        def waitfunc(retry_state: RetryCallState) -> float:
627	            raise ExtractCallState(retry_state)
628	
629	        retrying = Retrying(
[tool_use Bash] {"command": "cat releasenotes/notes/wait_exponential_jitter-6ffc81dddcbaa6d3.yaml releasenotes/notes/wait-random-exponential-min-2a4b7eed9f002436.yaml && ls releasenotes/notes | tail -5 && sed -n 1,20p tenacity/wait.py", "description": "Read release notes and wait.py header"}
[tool_result] ---
features:
  - |
    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
    See https://cloud.google.com/storage/docs/retry-strategy
---
fixes:
  - |
    Respects `min` arg for `wait_random_exponential`
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
# Copyright 2016–2021 Julien Danjou
#
…[144 chars elided]…
 use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import random
import typing
[assistant] The request is specific: add `min`, and accept `timedelta` for `max`, `jitter` and `min`. I'll check the existing timedelta helper and its release note so I follow the same pattern.
[tool_use Bash] {"command": "cat tenacity/_utils.py | head -60 && cat releasenotes/notes/support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml && grep -n \"to_seconds\\|time_unit\" tenacity/*.py | head -30 && sed -n 600,640p tenacity/wait.py 2>/dev/null; sed -n 1,40p tests/test_tenacity.py | grep -n import; sed -n 40,60p README.rst >/dev/null; git log --oneline -3 -- tenacity/wait.py", "description": "Inspect _utils time helpers and timedelta release note"}
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
…[2960 chars elided]…

23:import unittest
24:from fractions import Fraction
25:from unittest import mock
27:import pytest
28:from typeguard import check_type
30:import tenacity
31:from tenacity import RetryCallState, RetryError, Retrying, retry
32:from tenacity.retry import retry_all, retry_any
ae2d75e refactor: enable PGH, PYI ruff rules and rename TCH to TC (#619)
ac9c21f refactor: replace deprecated typing constructs with modern syntax (#616)
9686ed7 refactor: enable additional ruff rules and fix violations (#584)
[assistant] I have what I need. Plan:

- Keep `initial` as-is (not in the request; renaming or converting it would be a bigger change).
- Append `min` as the last parameter so existing positional calls keep working.
- Convert `max`, `jitter` and `min` with `_utils.to_seconds`, matching `wait_exponential` and `wait_fixed`.
- Apply `min` as a floor after the `max` clamp, the same order `wait_exponential` uses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tenacity/wait.py", "old_string": "    \"\"\"Wait strategy that applies exponential backoff and jitter.\n\n    It allows for a customized initial wait, maximum wait and jitter.\n\n    This implements the strategy described here:\n    https://cloud.google.c
…[1779 chars elided]…
= _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.initial * exp + jitter\n        except OverflowError:\n            result = self.max\n        return max(max(0, self.min), min(result, self.max))"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tenacity/wait.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll add tests. Existing tests stay untouched, per the project guardrails. I'm also checking the project's line-length setting, since I just wrote a long docstring line.
[tool_use Bash] {"command": "grep -n \"line-length\\|line_length\\|\\[tool\" pyproject.toml; ls <work>/env-tenacity/bin/python && echo PY_OK", "description": "Check ruff line length and project python exists"}
[tool_result] 5:[tool.hatch.version]
8:[tool.hatch.build.hooks.vcs]
66:[tool.poe.tasks]
75:[tool.poe.tasks.fmt]
81:[tool.poe.tasks.lint]
87:[tool.poe.tasks.all]
94:[tool.pytest.ini_options]
99:[tool.ruff]
100:line-length = 88
105:[tool.ruff.lint]
118:[tool.mypy]
124:[[tool.mypy.overrides]]
<work>/env-tenacity/bin/python
PY_OK
[assistant] Line length is 88, so my docstring line is too long. I'll wrap it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tenacity/wait.py", "old_string": "    The wait time is max(minimum, min(initial * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count.", "new_string": "    The wait time is max(minimum, min(initial * 2**n + random.uniform(0, jitter),\n    maximum)) where n is the retry count."}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tenacity/wait.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py", "old_string": "        # Default arguments exist\n        fn = tenacity.wait_exponential_jitter()\n        fn(make_retry_state(0, 0))\n\n    def test_wait_retry_state_attributes(self) -> None:", "new_string": "        # Default ar
…[1554 chars elided]…
al(fn(make_retry_state(7, 0)), 60)\n\n        # Zero jitter yields a deterministic value.\n        fn = tenacity.wait_exponential_jitter(\n            jitter=datetime.timedelta(0), min=datetime.timedelta(seconds=3)\n        )\n        self.assertEqual(fn(make_retry_state(1, 0)), 3)\n        self.assertEqual(fn(make_retry_state(3, 0)), 4)\n\n    def test_wait_retry_state_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Now I'll run the project's test command, plus ruff and mypy if they're available in that environment.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"--- ruff\"; $PY -m ruff check tenacity tests 2>&1 | tail -5; $PY -m ruff format --check tenacity tests 2>&1 | tail -5; echo \"--- mypy\"; $PY -m mypy tenacity 2>&1 | tail -3", "description": "Run test suite, ruff and mypy in project env"}
[tool_result] ............s............................................... [ 38%]
...................................................................... [ 83%]
.........................                                                [100%]
154 passed, 1 skipped, 14 subtests passed in 1.87s
--- ruff
<work>/env-tenacity/bin/python: No module named ruff
<work>/env-tenacity/bin/python: No module named ruff
--- mypy
<work>/env-tenacity/bin/python: No module named mypy
[assistant] All 154 tests pass. Ruff and mypy aren't installed in the project env, so I'll check whether they're on the PATH, and add a release note in the repo's reno format while I'm at it.
[tool_use Bash] {"command": "(which ruff mypy || echo \"no global ruff/mypy\"); python3 -c \"import secrets;print(secrets.token_hex(8))\"; awk 'length > 88 {print FILENAME\": \"FNR\": \"length}' tenacity/wait.py tests/test_tenacity.py", "description": "Check for ruff/mypy, generate note id, check line lengths"}
[tool_result] ruff not found
mypy not found
no global ruff/mypy
8b3b51ca1054a6af
tests/test_tenacity.py: 49: 89
tests/test_tenacity.py: 133: 89
tests/test_tenacity.py: 421: 105
tests/test_tenacity.py: 942: 99
tests/test_tenacity.py: 967: 99
tests/test_tenacity.py: 1411: 89
tests/test_tenacity.py: 1541: 106
tests/test_tenacity.py: 1552: 148
tests/test_tenacity.py: 1604: 92
tests/test_tenacity.py: 1605: 99
tests/test_tenacity.py: 1864: 92
tests/test_tenacity.py: 2051: 92
[assistant] None of the over-length lines are mine; they're pre-existing. Now the release note:
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/releasenotes/notes/wait_exponential_jitter-min-8b3b51ca1054a6af.yaml", "content": "---\nfeatures:\n  - |\n    ``wait_exponential_jitter`` now accepts a ``min`` argument that sets a floor\n    on the wait time, consistent with ``wait_exponential``.\n  - |\n    ``wait_exponential_jitter`` now accepts ``datetime.timedelta`` values for\n    ``max``, ``jitter`` and ``min``, as well as numbers of seconds.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1/releasenotes/notes/wait_exponential_jitter-min-8b3b51ca1054a6af.yaml (file state is current in your context — no need to Read it back)
[assistant] Last step: run the new tests by name and review the diff.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no -k \"wait_exponential_jitter\" -v 2>&1 | tail -8; git status --short; git diff --stat", "description": "Run targeted jitter tests and show changed files"}
[tool_result] rootdir: ~/.cache/lithify/work/repo-b58808c83cd1/20261023-163916-feature-wait-exponential-jitter/base-1
configfile: pyproject.toml
plugins: typeguard-4.6.0
collected 155 items / 152 deselected / 3 selected

tests/test_tenacity.py ...                                               [100%]

====================== 3 passed, 152 deselected in 0.11s =======================
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait_exponential_jitter-min-8b3b51ca1054a6af.yaml
 tenacity/wait.py       | 20 ++++++++++++--------
 tests/test_tenacity.py | 37 +++++++++++++++++++++++++++++++++++++
 2 files changed, 49 insertions(+), 8 deletions(-)
[assistant] `wait_exponential_jitter` now takes a `min` floor and accepts `timedelta` for `max`, `jitter` and `min`, alongside plain seconds. The full suite passes (154 passed, 1 skipped), and the project's test command was used for that run.

Changes:

- **`tenacity/wait.py`**: `min` is the last parameter, so existing positional calls such as `wait_exponential_jitter(10, 5)` still work. `max`, `jitter` and `min` go through `_utils.to_seconds`, as `wait_exponential` and `wait_fixed` do. The result is `max(min, min(result, max))`, the same clamp order `wait_exponential` uses, so the floor always holds. The
…[590 chars elided]…
ill fail. I can add conversion for it if you want the same treatment.
- **`min` is applied after jitter.** Attempts whose computed wait falls below `min` all wait exactly `min`, so jitter disappears in those early attempts. This matches the "floor" you described. It differs from `wait_random_exponential`, where `min` is the lower bound of the random range.

Ruff and mypy aren't installed in the project's test environment or on the PATH here, so I didn't run them. I checked the line lengths in the edited files against the 88-column limit by hand, and the only over-length lines are pre-existing.
