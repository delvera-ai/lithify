# trajectory comp-1

final message:
`humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged. The project test suite passes: 685 passed, 53 skipped (the skips were already there, from the translation-binary tests).

Changes:
- **`src/humanize/i18n.py`**: the raise is now `FileNotFoundError(msg)`, and the `Raises:` docstring names `FileNotFoundError`.
- **`tests/test_i18n.py`**: I added `test_default_locale_path_not_found_raises_file_not_found` in `TestActivate`. It uses the same setup and `match` as the existing tests and pins the new type. The existing `pytest.raises(Exception, ...)` lines are untouched, as the project's contract asks.

I did not run `ruff`, since it is not installed here. The `msg` variable pattern already matches the EM rule, so the raise site should be fine. I did not commit anything.

## events
[tool_use Skill] {"skill": "humanize-error-contract"}
[tool_result] Launching skill: humanize-error-contract
[user] Base directory for this skill: ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/.claude/skills/humanize-error-contract

# Changing what a humanize function raises

An exception type in this library is public API. Check each of these places.

1. **The raise site** (`src/humanize/*.py`). Ruff selects `EM` (flake8-errmsg), so every raise
   builds its message in a local first and passes the variable:
   `msg = "..."` then `raise ValueError(msg)` (see `time.py`, `number.py`, `i18n.py`).
   Never write `raise X("literal")` or `raise X(f"..
…[645 chars elided]…
Type>, match=<message>)`
   (`tests/test_time.py`, `tests/test_i18n.py::TestActivate`). If an existing assertion uses a
   base class (e.g. `pytest.raises(Exception, ...)`), it still passes after you narrow to a
   subclass. Do NOT rewrite those lines, because changing a pre-existing test line counts as
   editing an existing test even when it makes the test stricter. To pin the new type, add a
   NEW test function next to the existing ones. Base it on the same setup and the same `match`.

Release notes are drafted on GitHub Releases (`RELEASING.md`); the repo has no CHANGELOG file to
update.

[tool_use Bash] {"command": "grep -rn \"raise Exception\\|except Exception\" src/humanize/ ; grep -n \"locale\" src/humanize/i18n.py | head -50", "description": "Find bare Exception raises and locale code in i18n"}
[tool_result] src/humanize/i18n.py:88:        raise Exception(msg)
21:# Mapping of locale to thousands separator
30:# Mapping of locale to decimal separator
40:def _get_default_locale_path() -> pathlib.Path | None:
48:        return pkg / "locale"
53:        return _TRANSLATIONS[_CURRENT.locale]
59:    locale: str | None, path: str | os.PathLike[str] | None = None
63:    Set `locale` as current locale. Search for locale in directory `path`.
66:        locale (str | None): Language name, e.g. `en_GB`. If `None
…[389 chars elided]…
not in _TRANSLATIONS:
90:        translation = gettext_module.translation("humanize", path, [locale])
91:        _TRANSLATIONS[locale] = translation
92:    _CURRENT.locale = locale
93:    return _TRANSLATIONS[locale]
98:    _CURRENT.locale = None
184:    """Return the thousands separator for a locale, default to comma.
190:        sep = _THOUSANDS_SEPARATOR[_CURRENT.locale]
197:    """Return the decimal separator for a locale, default to dot.
203:        sep = _DECIMAL_SEPARATOR[_CURRENT.locale]
[assistant] The skill's checklist applies here: the raise site, the docstring `Raises:` section, and the tests. The docs MCP tools are not needed, since this is a code change and no doc was requested. Next I'll read the function and its tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py", "offset": 56, "limit": 40}
[tool_result] 56	
57	
58	def activate(
59	    locale: str | None, path: str | os.PathLike[str] | None = None
60	) -> gettext_module.NullTranslations:
61	    """Activate internationalisation.
62	
63	    Set `locale` as current locale. Search for locale in directory `path`.
64	
65	    Args:
66	        locale (str | None): Language name, e.g. `en_GB`. If `None`, defaults to no
67	            transaltion. Similar to calling ``deactivate()``.
68	        path (str | pathlib.Path): Path to search for locales.
69	
70
…[317 chars elided]…
efault_locale_path()
82	
83	    if path is None:
84	        msg = (
85	            "Humanize cannot determinate the default location of the 'locale' folder. "
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
[tool_use Bash] {"command": "grep -n \"raises\\|class \\|def test\" tests/test_i18n.py", "description": "List error tests in i18n test file"}
[tool_result] 18:def test_i18n() -> None:
42:def test_intcomma() -> None:
72:def test_naturaldelta() -> None:
149:def test_intword_i18n(locale: str, number: int, expected_result: str) -> None:
172:def test_langauge_codes(locale: str, expected_result: str) -> None:
195:def test_ordinal_genders(
208:def test_default_locale_path_defined__spec__() -> None:
213:def test_default_locale_path_none__spec__(monkeypatch: pytest.MonkeyPatch) -> None:
219:def test_default_locale_path_undefined__file__(monkeypatch: pytest.MonkeyPatch) -> None:
225:class TestActivate:
231:    def test_default_locale_path_null__spec__(
237:        with pytest.raises(Exception, match=self.expected_msg):
240:    def test_default_locale_path_undefined__spec__(
246:        with pytest.raises(Exception, match=self.expected_msg):
250:    def test_en_locale(self) -> None:
263:    def test_none_locale(self) -> None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/tests/test_i18n.py", "offset": 205, "limit": 70}
[tool_result] 205	        humanize.i18n.deactivate()
206	
207	
208	def test_default_locale_path_defined__spec__() -> None:
209	    i18n = importlib.import_module("humanize.i18n")
210	    assert i18n._get_default_locale_path() is not None
211	
212	
213	def test_default_locale_path_none__spec__(monkeypatch: pytest.MonkeyPatch) -> None:
214	    i18n = importlib.import_module("humanize.i18n")
215	    monkeypatch.setattr(i18n, "__spec__", None)
216	    assert i18n._get_default_locale_path() is None
217	
218	
219	d
…[1716 chars elided]…
:
264	        three_seconds = NOW - dt.timedelta(seconds=3)
265	
266	        try:
267	            humanize.i18n.activate("fr")
268	            assert humanize.naturaltime(three_seconds) == "il y a 3 secondes"
269	
270	            humanize.i18n.activate(None)
271	            test_str = humanize.naturaltime(three_seconds)
272	            assert test_str == "3 seconds ago"
273	        except FileNotFoundError:
274	            pytest.skip("Generate .mo with scripts/generate-translation-binaries.sh")
[assistant] The raise, the docstring, and the existing tests are all clear. I'll make the three edits: narrow the raise, update the docstring, and add a new test that pins the type without touching the existing assertions.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py", "old_string": "        raise Exception(msg)", "new_string": "        raise FileNotFoundError(msg)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py", "old_string": "        Exception: If humanize cannot find the locale folder.", "new_string": "        FileNotFoundError: If humanize cannot find the locale folder."}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/tests/test_i18n.py", "old_string": "        with pytest.raises(Exception, match=self.expected_msg):\n            i18n.activate(\"ru_RU\")\n\n    @freeze_time(\"2020-02-02\")\n    def test_en_locale(self) -> None:", "new_string": "        with pytest.rais
…[113 chars elided]…
_not_found_raises_file_not_found(\n        self, monkeypatch: pytest.MonkeyPatch\n    ) -> None:\n        i18n = importlib.import_module(\"humanize.i18n\")\n        monkeypatch.setattr(i18n, \"__spec__\", None)\n\n        with pytest.raises(FileNotFoundError, match=self.expected_msg):\n            i18n.activate(\"ru_RU\")\n\n    @freeze_time(\"2020-02-02\")\n    def test_en_locale(self) -> None:"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/comp-1/tests/test_i18n.py has been updated successfully.
[assistant] Edits are in. Now I'll run the project's test command.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run project test suite"}
[tool_result] ......................................................................ss [  9%]
ssssssssssssssssssssssssssssssssssssssssssssssssss.......s.............. [ 19%]
........................................................................ [ 29%]
........................................................................ [ 39%]
........................................................................ [ 48%]
........................................................................ [ 58%]
........................................................................ [ 68%]
........................................................................ [ 78%]
........................................................................ [ 87%]
........................................................................ [ 97%]
..................                                                       [100%]
685 passed, 53 skipped in 0.56s
[assistant] `humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged. The project test suite passes: 685 passed, 53 skipped (the skips were already there, from the translation-binary tests).

Changes:
- **`src/humanize/i18n.py`**: the raise is now `FileNotFoundError(msg)`, and the `Raises:` docstring names `FileNotFoundError`.
- **`tests/test_i18n.py`**: I added `test_default_locale_path_not_found_raises_file_not_found` in `TestActivate`. It uses the same setup and `match` as the existing tests and pins the new type. The existing `pytest.raises(Exception, ...)` lines are untouched, as the project's contract asks.

I did not run `ruff`, since it is not installed here. The `msg` variable pattern already matches the EM rule, so the raise site should be fine. I did not commit anything.
