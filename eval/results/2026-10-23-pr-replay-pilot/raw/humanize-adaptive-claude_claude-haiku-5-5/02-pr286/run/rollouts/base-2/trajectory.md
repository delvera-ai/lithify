# trajectory base-2

final message:
`humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it can't find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`. I also updated the docstring's `Raises:` entry to name `FileNotFoundError`, so it matches the code. The project test suite passes: 684 passed, 53 skipped. I didn't add a test for the new exception type, and I didn't commit.

## events
[tool_use Bash] {"command": "grep -rn \"Exception\" src/humanize/i18n.py; sed -n 1,80p src/humanize/i18n.py | grep -n \"raise\\|def \\|import\" ", "description": "Find bare Exception raise in i18n module"}
[tool_result] src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:88:        raise Exception(msg)
3:from __future__ import annotations
5:import gettext as gettext_module
6:from threading import local
10:    import os
11:    import pathlib
40:def _get_default_locale_path() -> pathlib.Path | None:
45:    import importlib.resources
47:    with importlib.resources.as_file(importlib.resources.files(package)) as pkg:
51:def get_translation() -> gettext_module.NullTranslations:
58:def activate(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-2/src/humanize/i18n.py", "offset": 60, "limit": 35}
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
…[218 chars elided]…
et_default_locale_path()
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
[assistant] Two edits: the raise itself and the docstring's `Raises:` entry, which should match the new exception type.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-2/src/humanize/i18n.py", "old_string": "        raise Exception(msg)", "new_string": "        raise FileNotFoundError(msg)"}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-2/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-2/src/humanize/i18n.py", "old_string": "        Exception: If humanize cannot find the locale folder.", "new_string": "        FileNotFoundError: If humanize cannot find the locale folder."}
[tool_result] The file ~/.cache/lithify/work/repo-439cf9294399/20261023-142146-humanize-i18n-raises-a-bare-exce/base-2/src/humanize/i18n.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -n 15", "description": "Run project test suite"}
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
684 passed, 53 skipped in 0.55s
[assistant] `humanize.i18n.activate` now raises `FileNotFoundError` instead of a bare `Exception` when it can't find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`. I also updated the docstring's `Raises:` entry to name `FileNotFoundError`, so it matches the code. The project test suite passes: 684 passed, 53 skipped. I didn't add a test for the new exception type, and I didn't commit.
