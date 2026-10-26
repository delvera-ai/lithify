# trajectory dom-1

final message:
Ruff and mypy aren't installed anywhere I can reach, so I haven't run them. Both changed files are short and fully annotated, but that's a read, not a check.

Fixed: `find_ordinal` now returns "th" for numbers whose last two digits are 11, 12 or 13, so 111, 112 and 113 give "111th", "112th" and "113th". Every other suffix is unchanged.

**Changes**
- `tenacity/_utils.py`: added an `elif 11 <= pos_num % 100 <= 13: return "th"` branch before the recursive fallback. The bug was that 111 recursed to `find_ordinal(1)` and got "st". The fix goes in the helper, so `before.py`, `after.py` and their tests all benefit.
- `tests/test_utils.py`: added `test_to_ordinal`, which covers 0–4, 11–13, 21–23, 101–103, 111–113, 121, 1011 and 1012. The 111–113 cases fail without the fix.
- `releasenotes/notes/fix-find-ordinal-teens-3c9a1d7e5b2f40a8.yaml`: a `fixes` note describing the change. The hex suffix is random, as the skill allows.

**Verification**
- Full test suite with the project's Python: 126 passed, 1 skipped, 12 subtests passed.
- Reproduction: `to_ordinal` gives 111th, 112th, 113th, 121st and 21st.
- Not run: `ruff check`, `ruff format --check` and `mypy --strict`. I couldn't find either tool on this machine; CI will run them.

I didn't commit anything. The working tree now has the three changes above.

## events
[assistant] I'll load the project's tenacity change-conventions skill first, since this is a bug fix under `tenacity/`.
[tool_use Skill] {"skill": "tenacity-change-conventions"}
[tool_result] Launching skill: tenacity-change-conventions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/.claude/skills/tenacity-change-conventions

# What a tenacity maintainer expects a behaviour change to include

## 1. A reno release note (the rollout-visible omission)
User-visible fixes and features in this repo ship a release note; recent fix PRs
(#555, #551, #497, #484, #479, #425) each added one alongside the code change.

- Location: `releasenotes/notes/<kebab-slug>-<16 hex chars>.yaml` (e.g.
  `fix-async-retry-type-overloads-27f3e0c239ed6b.yaml`). Pic
…[1345 chars elided]…
l` / `_utils.find_ordinal` build the "Nth time calling it" text in both
  `tenacity/before.py` and `tenacity/after.py`, and `tests/test_after.py` builds its expected
  messages through `_utils.to_ordinal`. Fix the helper, not the call sites.
- `_utils.get_callback_name` and the `LoggerProtocol` in `_utils.py` are likewise shared by
  `before.py`, `after.py` and `before_sleep.py`.

## 4. New public names are exported
New strategies/classes meant for users are imported in `tenacity/__init__.py` and listed in
its `__all__` (see PR #393, "Add ... to __all__"). Private helpers stay in `_utils.py`.

[tool_use Bash] {"command": "grep -rn \"find_ordinal\" . --include=*.py --include=*.md --include=*.rst --include=*.txt | grep -v \"/env\" ; git status --short", "description": "Locate find_ordinal usages and check worktree state"}
[tool_result] (eval):1: no matches found: --include=*.py
[assistant] The skill's checklist for this change is: fix the helper in `tenacity/_utils.py` (not the callers), add tests in `tests/test_utils.py`, add a reno note, and keep mypy strict and ruff clean. My previous grep failed because zsh didn't expand the `--include` globs, so I'll rerun it with quoting.
[tool_use Bash] {"command": "grep -rn \"find_ordinal\\|to_ordinal\" tenacity tests releasenotes; echo ---; git status --short; echo ---; ls releasenotes/notes | tail -5", "description": "Find ordinal helper usages and check worktree state"}
[tool_result] tenacity/before.py:43:            f"this is the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tenacity/after.py:46:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tenacity/_utils.py:40:def find_ordinal(pos_num: int) -> str:
tenacity/_utils.py:53:        return find_ordinal(pos_num % 10)
tenacity/_utils.py:56:def to_ordinal(pos_num: int) -> str:
tenacity/_utils.py:57:    return f"{pos_num}{find_ordinal(pos_num)}"
tests/test_after.py:49:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
tests/test_after.py:74:            f"this was the {_utils.to_ordinal(retry_state.attempt_number)} time calling it.",
---
---
support-timedelta-wait-unit-type-5ba1e9fc0fe45523.yaml
timedelta-for-stop-ef6bf71b88ce9988.yaml
trio-support-retry-22bd544800cd1f36.yaml
wait-random-exponential-min-2a4b7eed9f002436.yaml
wait_exponential_jitter-6ffc81dddcbaa6d3.yaml
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tenacity/_utils.py", "offset": 30, "limit": 35}
[tool_result] 30	    Protocol used by utils expecting a logger (eg: before_log).
31	
32	    Compatible with logging, structlog, loguru, etc...
33	    """
34	
35	    def log(
36	        self, level: int, msg: str, /, *args: typing.Any, **kwargs: typing.Any
37	    ) -> typing.Any: ...
38	
39	
40	def find_ordinal(pos_num: int) -> str:
41	    # See: https://en.wikipedia.org/wiki/English_numerals#Ordinal_numbers
42	    if pos_num == 0:
43	        return "th"
44	    elif pos_num == 1:
45	        return "st"
46	    
…[13 chars elided]…
== 2:
47	        return "nd"
48	    elif pos_num == 3:
49	        return "rd"
50	    elif 4 <= pos_num <= 20:
51	        return "th"
52	    else:
53	        return find_ordinal(pos_num % 10)
54	
55	
56	def to_ordinal(pos_num: int) -> str:
57	    return f"{pos_num}{find_ordinal(pos_num)}"
58	
59	
60	def get_callback_name(cb: typing.Callable[..., typing.Any]) -> str:
61	    """Get a callback fully-qualified name.
62	
63	    If no name can be produced ``repr(cb)`` is called and returned.
64	    """
[tool_use Bash] {"command": "grep -n \"ordinal\\|^def \\|^import\\|^from\" tests/test_utils.py | head -40; echo ---; cat releasenotes/notes/async-sleep-retrying-32de5866f5d041.yaml", "description": "Inspect existing ordinal tests and a sample release note"}
[tool_result] 1:import functools
3:from tenacity import _utils
6:def test_is_coroutine_callable() -> None:
---
---
fixes:
  - |
    Passing an async ``sleep`` callable (e.g. ``trio.sleep``) to ``@retry``
    now correctly uses ``AsyncRetrying``, even when the decorated function is
    synchronous. Previously, the async sleep would silently not be awaited,
    resulting in no delay between retries.
[assistant] The bug is in the `else` branch: 111 falls through to `find_ordinal(111 % 10)`, which is `find_ordinal(1)` and returns "st". The fix is to check the last two digits for 11–13 before that recursion, so every number ending in 11, 12 or 13 gets "th". I'll make that change in the helper and add tests next to the existing `_utils` test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tenacity/_utils.py", "old_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    else:", "new_string": "    elif 4 <= pos_num <= 20:\n        return \"th\"\n    elif 11 <= pos_num % 100 <= 13:\n        return \"th\"\n    else:"}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tenacity/_utils.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tests/test_utils.py"}
[tool_result] 1	import functools
2	
3	from tenacity import _utils
4	
5	
6	def test_is_coroutine_callable() -> None:
7	    async def async_func() -> None:
8	        pass
9	
10	    def sync_func() -> None:
11	        pass
12	
13	    class AsyncClass:
14	        async def __call__(self) -> None:
15	            pass
16	
17	    class SyncClass:
18	        def __call__(self) -> None:
19	            pass
20	
21	    lambda_fn = lambda: None  # noqa: E731
22	
23	    partial_async_func = functools.partial(async_func)
2
…[563 chars elided]…
s False
34	    assert _utils.is_coroutine_callable(SyncClass()) is False
35	    assert _utils.is_coroutine_callable(lambda_fn) is False
36	
37	    assert _utils.is_coroutine_callable(partial_async_func) is True
38	    assert _utils.is_coroutine_callable(partial_sync_func) is False
39	    assert _utils.is_coroutine_callable(partial_async_class) is True
40	    assert _utils.is_coroutine_callable(partial_sync_class) is False
41	    assert _utils.is_coroutine_callable(partial_lambda_fn) is False
42	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tests/test_utils.py", "old_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n", "new_string": "    assert _utils.is_coroutine_callable(partial_lambda_fn) is False\n\n\ndef test_to_ordinal() -> None:\n    expected = {\n        0
…[171 chars elided]…
  21: \"21st\",\n        22: \"22nd\",\n        23: \"23rd\",\n        101: \"101st\",\n        102: \"102nd\",\n        103: \"103rd\",\n        111: \"111th\",\n        112: \"112th\",\n        113: \"113th\",\n        121: \"121st\",\n        1011: \"1011th\",\n        1012: \"1012th\",\n    }\n    for number, ordinal in expected.items():\n        assert _utils.to_ordinal(number) == ordinal\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/tests/test_utils.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next, the release note, following the shape of the existing `fixes` notes.
[tool_use Write] {"file_path": "~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/releasenotes/notes/fix-find-ordinal-teens-3c9a1d7e5b2f40a8.yaml", "content": "---\nfixes:\n  - |\n    Log messages such as \"this is the N-th time calling it\" now use the\n    correct ordinal suffix for numbers greater than 20 that end in 11, 12 or\n    13. For example, 111 is now written as ``111th`` instead of ``111st``,\n    ``112th`` instead of ``112nd``, and ``113th`` instead of ``113rd``.\n"}
[tool_result] File created successfully at: ~/.cache/lithify/work/repo-d71b8290d947/20261023-154952-bug-tenacity-utils-find-ordinal/dom-1/releasenotes/notes/fix-find-ordinal-teens-3c9a1d7e5b2f40a8.yaml (file state is current in your context — no need to Read it back)
[tool_use Bash] {"command": "<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_utils.py tests/test_after.py tests/test_tenacity.py 2>&1 | tail -15", "description": "Run targeted test files with the project's Python"}
[tool_result] ............................................................ [ 60%]
.......................................                                  [100%]
99 passed, 12 subtests passed in 1.83s
[assistant] The targeted tests pass. Next I'll run the full suite, plus the lint and type checks the skill mentions, using the project's environment.
[tool_use Bash] {"command": "PY=<work>/env-tenacity/bin; $PY/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"--- ruff\"; ($PY/ruff check tenacity tests && $PY/ruff format --check tenacity tests) 2>&1 | tail -3; echo \"--- mypy\"; $PY/python -m mypy tenacity tests 2>&1 | tail -3; echo \"--- reproduce\"; $PY/python -c \"from tenacity import _utils as u; print([u.to_ordinal(n) for n in (111,112,113,121,21)])\"", "description": "Run full test suite, ruff, mypy, and a quick reproduction"}
[tool_result] ..........s................................................. [ 47%]
...................................................................      [100%]
126 passed, 1 skipped, 12 subtests passed in 1.78s
--- ruff
(eval):1: no such file or directory: <work>/env-tenacity/bin/ruff
--- mypy
<work>/env-tenacity/bin/python: No module named mypy
--- reproduce
['111th', '112th', '113th', '121st', '21st']
[assistant] The full suite passes (126 passed, 1 skipped). Ruff and mypy aren't installed in the project env, so I'll check whether they're available elsewhere on the machine.
[tool_use Bash] {"command": "which ruff mypy uvx 2>/dev/null; ruff --version 2>/dev/null; mypy --version 2>/dev/null; echo \"exit=$?\"", "description": "Check whether ruff or mypy is available on PATH"}
[tool_result] ruff not found
mypy not found
uvx not found
exit=127
[assistant] Ruff and mypy aren't installed anywhere I can reach, so I haven't run them. Both changed files are short and fully annotated, but that's a read, not a check.

Fixed: `find_ordinal` now returns "th" for numbers whose last two digits are 11, 12 or 13, so 111, 112 and 113 give "111th", "112th" and "113th". Every other suffix is unchanged.

**Changes**
- `tenacity/_utils.py`: added an `elif 11 <= pos_num % 100 <= 13: return "th"` branch before the recursive fallback. The bug was that 111 recursed to `find_ordinal(1)` and got "st". The fix goes in the helper, so `before.py`, `after.py` and their te
…[116 chars elided]…
 121, 1011 and 1012. The 111–113 cases fail without the fix.
- `releasenotes/notes/fix-find-ordinal-teens-3c9a1d7e5b2f40a8.yaml`: a `fixes` note describing the change. The hex suffix is random, as the skill allows.

**Verification**
- Full test suite with the project's Python: 126 passed, 1 skipped, 12 subtests passed.
- Reproduction: `to_ordinal` gives 111th, 112th, 113th, 121st and 21st.
- Not run: `ruff check`, `ruff format --check` and `mypy --strict`. I couldn't find either tool on this machine; CI will run them.

I didn't commit anything. The working tree now has the three changes above.
