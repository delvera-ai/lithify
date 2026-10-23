# trajectory base-1

final message:
`humanize.i18n` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`:
- The `raise Exception(msg)` at line 88 is now `raise FileNotFoundError(msg)`.
- The docstring's `Raises:` entry is updated to match.

The project test suite passes: 684 passed, 53 skipped. I did not add a test for the new exception type, and I did not touch any existing tests. I also did not commit, since you didn't ask for one.

## events
[tool_use Bash] {"command": "grep -rn \"Exception\" src/humanize/i18n.py; grep -rn \"locale\" src/humanize/i18n.py | head -30", "description": "Find Exception raises in i18n module"}
[tool_result] src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:88:        raise Exception(msg)
src/humanize/i18n.py:21:# Mapping of locale to thousands separator
src/humanize/i18n.py:30:# Mapping of locale to decimal separator
src/humanize/i18n.py:40:def _get_default_locale_path() -> pathlib.Path | None:
src/humanize/i18n.py:48:        return pkg / "locale"
src/humanize/i18n.py:53:        return _TRANSLATIONS[_CURRENT.locale]
src/humanize/i18n.py:59:  
…[979 chars elided]…
n
src/humanize/i18n.py:92:    _CURRENT.locale = locale
src/humanize/i18n.py:93:    return _TRANSLATIONS[locale]
src/humanize/i18n.py:98:    _CURRENT.locale = None
src/humanize/i18n.py:184:    """Return the thousands separator for a locale, default to comma.
src/humanize/i18n.py:190:        sep = _THOUSANDS_SEPARATOR[_CURRENT.locale]
src/humanize/i18n.py:197:    """Return the decimal separator for a locale, default to dot.
src/humanize/i18n.py:203:        sep = _DECIMAL_SEPARATOR[_CURRENT.locale]
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "offset": 68, "limit": 25}
[tool_result] 68	        path (str | pathlib.Path): Path to search for locales.
69	
70	    Returns:
71	        dict: Translations.
72	
73	    Raises:
74	        Exception: If humanize cannot find the locale folder.
75	    """
76	    if locale is None or locale.startswith("en"):
77	        _CURRENT.locale = None
78	        return _TRANSLATIONS[None]
79	
80	    if path is None:
81	        path = _get_default_locale_path()
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "old_string": "        Exception: If humanize cannot find the locale folder.", "new_string": "        FileNotFoundError: If humanize cannot find the locale folder."}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "old_string": "        raise Exception(msg)", "new_string": "        raise FileNotFoundError(msg)"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run project test suite"}
[tool_result] ......................................................................ss [  9%]
ssssssssssssssssssssssssssssssssssssssssssssssssss......s............... [ 19%]
........................................................................ [ 29%]
........................................................................ [ 39%]
........................................................................ [ 48%]
........................................................................ [ 58%]
........................................................................ [ 68%]
........................................................................ [ 78%]
........................................................................ [ 87%]
........................................................................ [ 97%]
.................                                                        [100%]
684 passed, 53 skipped in 0.61s
[assistant] `humanize.i18n` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`:
- The `raise Exception(msg)` at line 88 is now `raise FileNotFoundError(msg)`.
- The docstring's `Raises:` entry is updated to match.

The project test suite passes: 684 passed, 53 skipped. I did not add a test for the new exception type, and I did not touch any existing tests. I also did not commit, since you didn't ask for one.
