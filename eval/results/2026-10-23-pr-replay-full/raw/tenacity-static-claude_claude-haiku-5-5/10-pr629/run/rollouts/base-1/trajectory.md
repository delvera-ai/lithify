# trajectory base-1

final message:
`wait_exponential_jitter` now takes `multiplier` (default 1). Passing `initial` by keyword or position still works but emits a `DeprecationWarning`, and passing both raises `ValueError`. The full suite passes (158 passed, 1 skipped) and `check_changed.py` passes; ruff and mypy were not run here.

**Changes**
- `tenacity/wait.py`: `initial` and `multiplier` both default to `None`, so an explicit `multiplier=1` alongside `initial` is detected and raises. The formula, docstring and `__call__` now use `multiplier`.
- `tests/test_tenacity.py`: four new tests in `TestWaitConditions`, one per gap (multiplier, keyword `initial` warns, positional `initial` warns, both raises). I ran each against the unfixed code first and each failed for its own reason, then they went green.
- `releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml`: a `features:` entry for `multiplier` and a `deprecations:` entry for `initial`.

**Choices you may want to change**
- `multiplier` is appended as the last parameter. `initial` stays in position 0 so existing positional calls keep their meaning and can warn.
- The signature shows `multiplier=None` rather than `multiplier=1`; the docstring says it defaults to 1. A sentinel would have the same signature problem, and `None` keeps the type checker simple.
- The `self.initial` attribute is no longer set. Nothing in the repo reads it, but external code reading `.initial` would break. Say if you want it kept as an alias.
- I did not edit `doc/source/index.rst`. The docs have no existing example of `wait_exponential_jitter`, so there was no documented usage to update. I also did not edit the two existing tests that pass `initial=`; they now emit the expected `DeprecationWarning` (the 2 suite warnings).

## events
[tool_use Bash] {"command": "cat .lithify/memory.md 2>/dev/null | head -20; grep -n \"class wait_exponential\\|class wait_exponential_jitter\" -A60 tenacity/wait.py | head -200", "description": "Read memory notes and wait class definitions"}
[tool_result] 175:class wait_exponential(wait_base):
176-    """Wait strategy that applies exponential backoff.
177-
178-    It allows for a customized multiplier and an ability to restrict the
179-    upper and lower limits to some maximum and minimum value.
180-
181-    The intervals are fixed (i.e. there is no jitter), so this strategy is
182-    suitable for balancing retries against latency when a required resource is
183-    unavailable for an unknown duration, but *not* suitable for resolving
184-    c
…[3030 chars elided]…
ase
263-        self.jitter = _utils.to_seconds(jitter)
264-        self.min = _utils.to_seconds(min)
265-
266-    def __call__(self, retry_state: "RetryCallState") -> float:
267-        jitter = random.uniform(0, self.jitter)
268-        try:
269-            exp = self.exp_base ** (retry_state.attempt_number - 1)
270-            result = self.initial * exp + jitter
271-        except OverflowError:
272-            result = self.max
273-        return max(max(0, self.min), min(result, self.max))
[tool_use Bash] {"command": "cat .lithify/harness/skills/tenacity-change-contract/SKILL.md; echo ---; ls <work>/env-tenacity/bin/python 2>&1; echo ---; grep -rn \"wait_exponential_jitter\\|initial=\" --include='*.py' --include='*.rst' --include='*.yaml' . | grep -v \"^./.git/\" | head -40; ls releasenotes/notes | tail -5; grep -n \"DeprecationWarning\\|deprecat\" -ri tenacity | head", "description": "Read tenacity change contract and find usages"}
[tool_result] ---
name: tenacity-change-contract
description: Load when a task changes user-visible behaviour of the tenacity package (a bug fix, new feature, a new keyword/option on `Retrying`/`AsyncRetrying`/`@retry`, changed log/message text, retry-loop or `statistics` behaviour, retry/stop/wait strategy composition with `|`/`&`/`+` or sync/async strategy mixing, typing change, dropped Python version, pickling/copying/`multiprocessing` support or `threading.local`/statistics state on `Retrying`, adding or 
…[15767 chars elided]…
dcbaa6d3.yaml:4:    Implement a wait.wait_exponential_jitter per Google's storage retry guide.
releasenotes/notes/add_omitted_modules_to_import_all-2ab282f20a2c22f7.yaml:3:  - Add `retry_if_exception_cause_type`and `wait_exponential_jitter` to __all__ of init.py
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Bash] {"command": "sed -n 590,650p tests/test_tenacity.py; echo ---; sed -n 185,215p doc/source/index.rst; echo ---; cat releasenotes/notes/wait-exponential-jitter-min-timedelta-a8e3c1f4b7d29e50.yaml; echo ---; sed -n 1,20p tenacity/wait.py; echo ---; grep -rn \"warnings\" tenacity/*.py | head; echo ---; grep -n \"filterwarnings\\|DeprecationWarning\" -r tests pyproject.toml | head", "description": "Read existing tests, docs, release note, imports"}
[tool_result]         self._assert_inclusive_epsilon(mean(attempt[3]), 1, 0.08)
        self._assert_inclusive_epsilon(mean(attempt[4]), 2, 0.16)
        self._assert_inclusive_epsilon(mean(attempt[5]), 4, 0.32)
        self._assert_inclusive_epsilon(mean(attempt[6]), 8, 0.64)
        self._assert_inclusive_epsilon(mean(attempt[7]), 16, 1.28)
        self._assert_inclusive_epsilon(mean(attempt[8]), 30, 2.56)
        self._assert_inclusive_epsilon(mean(attempt[9]), 30, 2.56)

    def test_wait_exponential_jitt
…[4178 chars elided]…
ed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import abc
import random
import typing

---
tenacity/__init__.py:24:import warnings
tenacity/__init__.py:719:            warnings.warn(
---
pyproject.toml:95:filterwarnings = [
pyproject.toml:96:    "once::DeprecationWarning",
[tool_use Bash] {"command": "sed -n 88,102p pyproject.toml; echo ---; grep -n \"_unset\" tenacity/*.py | head -5; echo ---; grep -n \"^class \\|^import\\|^from\" tests/test_tenacity.py | head -40; echo ---; grep -ln \"deprecations:\" releasenotes/notes/*.yaml | head -3; grep -n \"sections\" -A10 releasenotes/config.yaml 2>/dev/null; echo ---; head -30 doc/source/index.rst | grep -n \"testsetup\\|import\" ; grep -n \"testsetup\" -A6 doc/source/index.rst | head -12; git status --short; sed -n 1,12p tenacity/__init__.py | head -3; sed -n 20,40p tenacity/__init__.py", "description": "Inspect pyproject warnings config, sentinels, test classes, reno config"}
[tool_result] sequence = [
    { ref = "lint" },
    { ref = "mypy" },
    { ref = "check" },
]

[tool.pytest.ini_options]
filterwarnings = [
    "once::DeprecationWarning",
]

[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py310"
---
tenacity/__init__.py:172:_unset = object()
tenacity/__init__.py:176:    return second if first is _unset else first
tenacity/__init__.py:261:        sleep: t.Callable[[int | float], None] | object = _unset,
tenacity/__init__.py:262:        stop: "StopBaseT | obj
…[1905 chars elided]…
 ABC, abstractmethod
from concurrent import futures

from . import _utils

# Import all built-in after strategies for easier usage.
from .after import after_log, after_nothing

# Import all built-in before strategies for easier usage.
from .before import before_log, before_nothing

# Import all built-in before sleep strategies for easier usage.
from .before_sleep import before_sleep_log, before_sleep_nothing

# Import all nap strategies for easier usage.
from .nap import sleep, sleep_using_event
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py", "offset": 636, "limit": 6}
[tool_result] 636	            min=timedelta(seconds=5),
637	        )
638	        for _ in range(1000):
639	            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 5, 5)
640	            self._assert_inclusive_range(fn(make_retry_state(5, 0)), 16, 17)
641	            self.assertEqual(fn(make_retry_state(7, 0)), 60)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py", "old_string": "            self._assert_inclusive_range(fn(make_retry_state(5, 0)), 16, 17)\n            self.assertEqual(fn(make_retry_state(7, 0)), 60)\n\n    def test_wait_retry_state_attributes(self) -> None:", "new_string": 
…[1001 chars elided]…
y.wait_exponential_jitter(10, 60)\n        for _ in range(1000):\n            self._assert_inclusive_range(fn(make_retry_state(1, 0)), 10, 11)\n\n    def test_wait_exponential_jitter_initial_and_multiplier_raises(self) -> None:\n        with pytest.raises(ValueError):\n            tenacity.wait_exponential_jitter(initial=1, multiplier=1)\n\n    def test_wait_retry_state_attributes(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py has been updated successfully.
[assistant] Tests are written. Now I'll run them against the unfixed code, which must fail for the right reasons.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; for t in multiplier initial_keyword_deprecated initial_positional_deprecated initial_and_multiplier_raises; do $PY .lithify/harness/scripts/run_tests.py --timeout 60 \"tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_$t\" > /tmp/red_$t.txt 2>&1; echo \"== $t exit=$?\"; grep -E \"Error|assert|passed|failed|exit=\" /tmp/red_$t.txt | tail -4; done", "description": "Run new regression tests against unfixed code"}
[tool_result] == multiplier exit=1
E       TypeError: wait_exponential_jitter.__init__() got an unexpected keyword argument 'multiplier'
tests/test_tenacity.py:644: TypeError
============================== 1 failed in 0.08s ===============================
exit=1 (pytest); full log: /tmp/run_tests.log
== initial_keyword_deprecated exit=1
E       AssertionError: DeprecationWarning not triggered
tests/test_tenacity.py:651: AssertionError
============================== 1 failed in 0.03s ==========================
…[129 chars elided]…
rning not triggered
tests/test_tenacity.py:657: AssertionError
============================== 1 failed in 0.03s ===============================
exit=1 (pytest); full log: /tmp/run_tests.log
== initial_and_multiplier_raises exit=1
E           TypeError: wait_exponential_jitter.__init__() got an unexpected keyword argument 'multiplier'
tests/test_tenacity.py:664: TypeError
============================== 1 failed in 0.03s ===============================
exit=1 (pytest); full log: /tmp/run_tests.log
[assistant] All four fail for their own gap (TypeError on the missing kwarg, or no `DeprecationWarning`). Now the implementation. Positional slot 0 stays `initial` so existing positional calls keep their meaning and can warn; `multiplier` goes last. I'm using `None` defaults, since a sentinel can't distinguish an explicit `multiplier=1` from the default and the spec requires that case to raise.
[tool_use Bash] {"command": "sed -n 20,30p tenacity/wait.py", "description": "Show wait.py imports"}
[tool_result] from tenacity import _utils

if typing.TYPE_CHECKING:
    from tenacity import RetryCallState


class wait_base(abc.ABC):
    """Abstract base class for wait strategies."""

    @abc.abstractmethod
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "offset": 17, "limit": 5}
[tool_result] 17	import abc
18	import random
19	import typing
20	
21	from tenacity import _utils
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "import abc\nimport random\nimport typing\n\nfrom tenacity import _utils", "new_string": "import abc\nimport random\nimport typing\nimport warnings\n\nfrom tenacity import _utils"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "    It allows for a customized initial wait, maximum wait, jitter and minimum.\n\n    This implements the strategy described here:\n    https://cloud.google.com/storage/docs/retry-strategy\n\n    The wait time is max(min
…[2104 chars elided]…
ls.to_seconds(max)\n        self.exp_base = exp_base\n        self.jitter = _utils.to_seconds(jitter)\n        self.min = _utils.to_seconds(min)\n\n    def __call__(self, retry_state: \"RetryCallState\") -> float:\n        jitter = random.uniform(0, self.jitter)\n        try:\n            exp = self.exp_base ** (retry_state.attempt_number - 1)\n            result = self.multiplier * exp + jitter"}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[assistant] Now the four new tests should go green. I'll also run the existing `wait_exponential_jitter` tests, which use `initial=` and must still pass.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py --timeout 60 tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_multiplier tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_initial_keyword_
…[199 chars elided]…
multiplier_raises tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_timedelta > /tmp/green_targeted.txt 2>&1; echo \"run exit=$?\"; tail -5 /tmp/green_targeted.txt", "description": "Run new and existing jitter tests after fix"}
[tool_result] run exit=0

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 7 passed, 2 warnings in 0.08s =========================
---
exit=0 (pytest); full log: /tmp/run_tests.log
[assistant] Targeted tests are green. Next is the release note the change contract requires. Creating it with a fresh 16-hex suffix:
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml", "content": "---\nfeatures:\n  - |\n    Add ``multiplier`` parameter to ``wait_exponential_jitter``, with the same\n    meaning as in ``wait_exponential``. It defaults to 1.\ndeprecations:\n  - |\n    The ``initial`` parameter of ``wait_exponential_jitter`` is deprecated in\n    favour of ``multiplier``. Passing ``initial`` (by keyword or positionally)\n    still works but emits a ``DeprecationWarning``. Passing both ``initial`` and\n    ``multiplier`` raises ``ValueError``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml (file state is current in your context — no need to Read it back)
[assistant] Now the full suite and the lint substitute, run in the foreground as the project requires.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/run_tests.py > /tmp/full_run.txt 2>&1; echo \"run_tests exit=$?\"; grep -E \"passed|failed|exit=\" /tmp/full_run.txt | tail -4; echo ---; $PY .lithify/harness/scripts/check_changed.py > /tmp/check.txt 2>&1; echo \"check exit=$?\"; tail -15 /tmp/check.txt", "description": "Run full test suite and changed-file checks"}
[tool_result] run_tests exit=0
======== 158 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.85s ========
exit=0 (pytest); full log: /tmp/run_tests.log
---
check exit=1
changed: releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml, tenacity/wait.py, tests/test_tenacity.py
FAIL tenacity/wait.py:249: line is 90 columns (max 88)
FAIL: 1 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
[assistant] The suite passes (158 passed), but the checker flags one line at 90 columns. That's the docstring formula line I rewrote. Fixing it:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py", "old_string": "    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter), maximum))\n    where n is the retry count. ``multiplier`` defaults to 1.", "new_string": "    The wait time is max(min, min(multiplier * 2**n + random.uniform(0, jitter),\n    maximum)) where n is the retry count. ``multiplier`` defaults to 1."}
[tool_result] The file ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tenacity/wait.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin/python; $PY .lithify/harness/scripts/check_changed.py > /tmp/check2.txt 2>&1; echo \"check exit=$?\"; tail -6 /tmp/check2.txt; echo ---; $PY .lithify/harness/scripts/run_tests.py > /tmp/full_run2.txt 2>&1; echo \"run_tests exit=$?\"; gr
…[235 chars elided]…
tch_warnings(record=True) as r:\n    warnings.simplefilter('always')\n    w(initial=2, max=9); print('initial kw warns:', [str(x.category.__name__)+' '+x.filename for x in r])\nprint('multiplier explicit 1 + initial raises:', end=' ')\ntry: w(initial=2, multiplier=1)\nexcept ValueError as e: print('ValueError', e)\n\"", "description": "Re-run checks, full suite, and manual deprecation spot-check"}
[tool_result] check exit=0
changed: releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml, tenacity/wait.py, tests/test_tenacity.py
PASS: 0 problem(s)
NOT RUN: ruff, mypy, PyYAML (unavailable here) -- report them as not run
---
run_tests exit=0
======== 158 passed, 1 skipped, 2 warnings, 12 subtests passed in 1.82s ========
exit=0 (pytest); full log: /tmp/run_tests.log
---
ok
initial kw warns: ['DeprecationWarning <string>']
multiplier explicit 1 + initial raises: ValueError pass either 'multiplier' or 'initial', not both
[assistant] Checks pass. The suite now reports 2 warnings, which I want to attribute correctly before I report it.
[tool_use Bash] {"command": "grep -n \"DeprecationWarning\" -B3 /tmp/full_run2.txt | head -20; git status --short", "description": "Identify source of the two suite warnings"}
[tool_result] 29-
30-=============================== warnings summary ===============================
31-tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter
32:  ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:612: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
33-    fn = tenacity.wait_exponential_jitter(10, 5)
34-
35-tests/test_tenacity.py::TestWaitConditions::test_wait_exponential_jitter_min
36:  ~/.cache/lithify/work/repo-8ffc43e3927e/20261023-204745-api-cleanup-every-other-exponent/base-1/tests/test_tenacity.py:621: DeprecationWarning: 'initial' is deprecated, use 'multiplier' instead
 M tenacity/wait.py
 M tests/test_tenacity.py
?? releasenotes/notes/wait-exponential-jitter-multiplier-4d7e2a9c1b06f583.yaml
[assistant] `wait_exponential_jitter` now takes `multiplier` (default 1). Passing `initial` by keyword or position still works but emits a `DeprecationWarning`, and passing both raises `ValueError`. The full suite passes (158 passed, 1 skipped) and `check_changed.py` passes; ruff and mypy were not run here.

**Changes**
- `tenacity/wait.py`: `initial` and `multiplier` both default to `None`, so an explicit `multiplier=1` alongside `initial` is detected and raises. The formula, docstring and `__call__` now use `multiplier`.
- `tests/test_tenacity.py`: four new tests in `TestWaitConditions`, one per gap (mu
…[564 chars elided]…
han `multiplier=1`; the docstring says it defaults to 1. A sentinel would have the same signature problem, and `None` keeps the type checker simple.
- The `self.initial` attribute is no longer set. Nothing in the repo reads it, but external code reading `.initial` would break. Say if you want it kept as an alias.
- I did not edit `doc/source/index.rst`. The docs have no existing example of `wait_exponential_jitter`, so there was no documented usage to update. I also did not edit the two existing tests that pass `initial=`; they now emit the expected `DeprecationWarning` (the 2 suite warnings).
