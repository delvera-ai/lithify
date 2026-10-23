# trajectory dom-1

final message:
`humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it can't find the locale folder. The message is unchanged. The full test suite passes (684 passed, 53 skipped).

Changes:
- **`src/humanize/i18n.py`**: the `raise` now uses `FileNotFoundError(msg)`, and the docstring `Raises:` entry names `FileNotFoundError`.
- **`tests/test_i18n.py`**: both `TestActivate` cases now use `pytest.raises(FileNotFoundError, ...)`. The old `Exception` assertions would also have passed without the change, so these tests are what verify the new type. This narrows the tests rather than weakening them.

Ruff isn't installed in the project's test environment, so I couldn't run the lint check (`EM` rules). The change keeps the existing `msg = ...` then `raise X(msg)` pattern, so it should pass. I haven't committed anything.

## events
[tool_use Skill] {"skill": "humanize-error-contract"}
[tool_result] Launching skill: humanize-error-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/.claude/skills/humanize-error-contract

# Changing what a humanize function raises

An exception type in this library is public API. Three places must agree; check each.

1. **The raise site** (`src/humanize/*.py`). Ruff selects `EM` (flake8-errmsg), so every raise
   builds its message in a local first and passes the variable:
   `msg = "..."` then `raise ValueError(msg)` (see `time.py`, `number.py`, `i18n.py`).
   Never write `raise X("literal")` or `rais
…[521 chars elided]…
 the type.** Error tests use `pytest.raises(<Type>, match=<message>)`
   (`tests/test_time.py`, `tests/test_i18n.py::TestActivate`). A `pytest.raises(Exception, ...)`
   assertion still passes after you narrow the type to a subclass — and also passes if you never
   made the change. When the task is to change the type, make sure some test asserts the NEW
   specific type with the same `match`; otherwise the change is unverified. Passing the suite is
   not evidence the new type is raised.

Release notes are drafted on GitHub Releases (`RELEASING.md`); the repo has no CHANGELOG file to
update.

[tool_use Bash] {"command": "grep -rn \"Exception\" src/humanize/i18n.py; grep -rn \"raise Exception\\|except Exception\" src/humanize/ | head -50", "description": "Find bare Exception raises in humanize source"}
[tool_result] src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:88:        raise Exception(msg)
src/humanize/i18n.py:88:        raise Exception(msg)
[assistant] The skill's checklist covers three places: the raise, the docstring `Raises:` section, and a test that pins the new type. Next I'll read the raise site and the existing tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/src/humanize/i18n.py", "offset": 60, "limit": 40}
[tool_result] 60	) -> gettext_module.NullTranslations:
61	    """Activate internationalisation.
62	
63	    Set `locale` as current locale. Search for locale in directory `path`.
64	
65	    Args:
66	        locale (str | None): Language name, e.g. `en_GB`. If `None`, defaults to no
67	            transaltion. Similar to calling ``deactivate()``.
68	        path (str | pathlib.Path): Path to search for locales.
69	
70	    Returns:
71	        dict: Translations.
72	
73	    Raises:
74	        Exception: If humani
…[331 chars elided]…
te the default location of the 'locale' folder. "
86	            "You need to pass the path explicitly."
87	        )
88	        raise Exception(msg)
89	    if locale not in _TRANSLATIONS:
90	        translation = gettext_module.translation("humanize", path, [locale])
91	        _TRANSLATIONS[locale] = translation
92	    _CURRENT.locale = locale
93	    return _TRANSLATIONS[locale]
94	
95	
96	def deactivate() -> None:
97	    """Deactivate internationalisation."""
98	    _CURRENT.locale = None
99	
[tool_use Bash] {"command": "grep -n \"raises\" tests/test_i18n.py; grep -rn \"Exception\" tests/test_i18n.py", "description": "Find error-related tests in i18n test file"}
[tool_result] 237:        with pytest.raises(Exception, match=self.expected_msg):
246:        with pytest.raises(Exception, match=self.expected_msg):
tests/test_i18n.py:237:        with pytest.raises(Exception, match=self.expected_msg):
tests/test_i18n.py:246:        with pytest.raises(Exception, match=self.expected_msg):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/tests/test_i18n.py", "offset": 220, "limit": 40}
[tool_result] 220	    i18n = importlib.import_module("humanize.i18n")
221	    monkeypatch.delattr(i18n, "__spec__")
222	    assert i18n._get_default_locale_path() is None
223	
224	
225	class TestActivate:
226	    expected_msg = (
227	        "Humanize cannot determinate the default location of the"
228	        " 'locale' folder. You need to pass the path explicitly."
229	    )
230	
231	    def test_default_locale_path_null__spec__(
232	        self, monkeypatch: pytest.MonkeyPatch
233	    ) -> None:
234	     
…[506 chars elided]…
match=self.expected_msg):
247	            i18n.activate("ru_RU")
248	
249	    @freeze_time("2020-02-02")
250	    def test_en_locale(self) -> None:
251	        three_seconds = NOW - dt.timedelta(seconds=3)
252	        test_str = humanize.naturaltime(three_seconds)
253	
254	        humanize.i18n.activate("en_US")
255	        assert test_str == humanize.naturaltime(three_seconds)
256	
257	        humanize.i18n.activate("en_GB")
258	        assert test_str == humanize.naturaltime(three_seconds)
259	
[assistant] The raise, the docstring, and both tests all need the same type change. Narrowing `pytest.raises(Exception)` to `FileNotFoundError` makes the tests stricter, not weaker. I'll keep the message text unchanged, since the tests match on it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/src/humanize/i18n.py", "old_string": "        Exception: If humanize cannot find the locale folder.", "new_string": "        FileNotFoundError: If humanize cannot find the locale folder."}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/src/humanize/i18n.py", "old_string": "        raise Exception(msg)", "new_string": "        raise FileNotFoundError(msg)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/tests/test_i18n.py", "old_string": "        monkeypatch.setattr(i18n, \"__spec__\", None)\n\n        with pytest.raises(Exception, match=self.expected_msg):", "new_string": "        monkeypatch.setattr(i18n, \"__spec__\", None)\n\n        with pytest.raises(FileNotFoundError, match=self.expected_msg):"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/tests/test_i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/tests/test_i18n.py", "old_string": "        monkeypatch.delattr(i18n, \"__spec__\")\n\n        with pytest.raises(Exception, match=self.expected_msg):", "new_string": "        monkeypatch.delattr(i18n, \"__spec__\")\n\n        with pytest.raises(FileNotFoundError, match=self.expected_msg):"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/dom-1/tests/test_i18n.py has been updated successfully.
[assistant] Now I'll run the project's test command, plus ruff if it's available, to check the change.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -20; echo \"---ruff---\"; (ruff check src/humanize/i18n.py tests/test_i18n.py 2>&1 || <work>/env-humanize/bin/ruff check src/humanize/i18n.py tests/test_i18n.py 2>&1) | tail -5", "description": "Run project test suite and ruff lint"}
[tool_result] ......................................................................ss [  9%]
ssssssssssssssssssssssssssssssssssssssssssssssssss......s............... [ 19%]
........................................................................ [ 29%]
........................................................................ [ 39%]
........................................................................ [ 48%]
........................................................................ [ 58%]
....................
…[146 chars elided]…
.................................................................. [ 87%]
........................................................................ [ 97%]
.................                                                        [100%]
684 passed, 53 skipped in 0.59s
---ruff---
(eval):1: command not found: ruff
(eval):1: no such file or directory: <work>/env-humanize/bin/ruff
[tool_use Bash] {"command": "git diff --stat; git diff", "description": "Show the diff of the changes"}
[tool_result]  src/humanize/i18n.py | 4 ++--
 tests/test_i18n.py   | 4 ++--
 2 files changed, 4 insertions(+), 4 deletions(-)
diff --git a/src/humanize/i18n.py b/src/humanize/i18n.py
index 1d30d50..5308a13 100644
--- a/src/humanize/i18n.py
+++ b/src/humanize/i18n.py
@@ -71,7 +71,7 @@ def activate(
         dict: Translations.
 
     Raises:
-        Exception: If humanize cannot find the locale folder.
+        FileNotFoundError: If humanize cannot find the locale folder.
     """
     if locale is None or lo
…[835 chars elided]…
est.raises(FileNotFoundError, match=self.expected_msg):
             i18n.activate("ru_RU")
 
     def test_default_locale_path_undefined__spec__(
@@ -243,7 +243,7 @@ class TestActivate:
         i18n = importlib.import_module("humanize.i18n")
         monkeypatch.delattr(i18n, "__spec__")
 
-        with pytest.raises(Exception, match=self.expected_msg):
+        with pytest.raises(FileNotFoundError, match=self.expected_msg):
             i18n.activate("ru_RU")
 
     @freeze_time("2020-02-02")
[assistant] `humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it can't find the locale folder. The message is unchanged. The full test suite passes (684 passed, 53 skipped).

Changes:
- **`src/humanize/i18n.py`**: the `raise` now uses `FileNotFoundError(msg)`, and the docstring `Raises:` entry names `FileNotFoundError`.
- **`tests/test_i18n.py`**: both `TestActivate` cases now use `pytest.raises(FileNotFoundError, ...)`. The old `Exception` assertions would also have passed without the change, so these tests are what verify the new type. This narrows the tests rather than weakening them.

Ruff isn't installed in the project's test environment, so I couldn't run the lint check (`EM` rules). The change keeps the existing `msg = ...` then `raise X(msg)` pattern, so it should pass. I haven't committed anything.
