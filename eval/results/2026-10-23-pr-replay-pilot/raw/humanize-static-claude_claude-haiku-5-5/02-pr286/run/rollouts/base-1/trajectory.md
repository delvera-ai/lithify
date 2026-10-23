# trajectory base-1

final message:
`humanize.i18n` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`:
- The raise on line 88 is now `raise FileNotFoundError(msg)`.
- The docstring's `Raises:` entry now says `FileNotFoundError`, so it matches the code.

I left the tests alone. They use `pytest.raises(Exception, ...)`, which still matches the subclass. The project's test command passes: 684 passed, 53 skipped. I haven't committed the change.

## events
[tool_use Bash] {"command": "grep -rn \"Exception\" src/humanize/i18n.py; grep -rn \"raise Exception\\|except Exception\" src/ | head; ls tests 2>/dev/null | head -30", "description": "Locate bare Exception in humanize i18n"}
[tool_result] src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:88:        raise Exception(msg)
src/humanize/i18n.py:88:        raise Exception(msg)
__init__.py
test_filesize.py
test_i18n.py
test_lists.py
test_number.py
test_time.py
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "offset": 60, "limit": 40}
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
[tool_use Bash] {"command": "grep -n \"Exception\\|raises\" tests/test_i18n.py", "description": "Check tests referencing Exception in i18n tests"}
[tool_result] 237:        with pytest.raises(Exception, match=self.expected_msg):
246:        with pytest.raises(Exception, match=self.expected_msg):
[assistant] The tests use `pytest.raises(Exception, ...)`, which still matches a `FileNotFoundError`, so they need no changes. I'll update the raise and the docstring that documents it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "old_string": "        Exception: If humanize cannot find the locale folder.", "new_string": "        FileNotFoundError: If humanize cannot find the locale folder."}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py", "old_string": "        raise Exception(msg)", "new_string": "        raise FileNotFoundError(msg)"}
[tool_result] The file ~/.cache/lithify/work/repo-591a89d5b953/20261023-142559-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py has been updated successfully.
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
684 passed, 53 skipped in 0.58s
[assistant] `humanize.i18n` now raises `FileNotFoundError` instead of a bare `Exception` when it cannot find the default locale folder. The message is unchanged.

The change is in `src/humanize/i18n.py`:
- The raise on line 88 is now `raise FileNotFoundError(msg)`.
- The docstring's `Raises:` entry now says `FileNotFoundError`, so it matches the code.

I left the tests alone. They use `pytest.raises(Exception, ...)`, which still matches the subclass. The project's test command passes: 684 passed, 53 skipped. I haven't committed the change.
