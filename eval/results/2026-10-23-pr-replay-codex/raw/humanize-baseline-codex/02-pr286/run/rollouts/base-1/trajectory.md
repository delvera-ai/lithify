# trajectory base-1

final message:
Changed `humanize.i18n` to raise `FileNotFoundError` with the same message. Updated the docstring and strengthened both existing tests to check the specific exception.

Checks passed: 684 passed, 53 skipped.

## events
[assistant] I’ll check the locale-path handling, change the exception type, and run the project checks.
[command exit=0] /bin/zsh -lc 'cat ~/.codex/RTK.md'
# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Always prefix shell commands with `rtk`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```

[command exit=0] /bin/zsh -lc "rg -n 'raise Exception|locale folder|default.*location' src tests; rg --files -g AGENTS.md"
src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:85:            "Humanize cannot determinate the default location of the 'locale' folder. "
src/humanize/i18n.py:88:        raise Exception(msg)
tests/test_i18n.py:227:        "Humanize cannot determinate the default location of the"
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '45,100p' src/humanize/i18n.py"
    import importlib.resources

    with importlib.resources.as_file(importlib.resources.files(package)) as pkg:
        return pkg / "locale"


def get_translation() -> gettext_module.NullTranslations:
    try:
        return _TRANSLATIONS[_CURRENT.locale]
    except (AttributeError, KeyError):
        return _TRANSLATIONS[None]


def activate(
    locale: str | None, path: str | os.PathLike[str] | None = None
) -> gettext_module.NullTranslations:
    """Activate internationalisation.

    Set 
…[628 chars elided]…
(
            "Humanize cannot determinate the default location of the 'locale' folder. "
            "You need to pass the path explicitly."
        )
        raise Exception(msg)
    if locale not in _TRANSLATIONS:
        translation = gettext_module.translation("humanize", path, [locale])
        _TRANSLATIONS[locale] = translation
    _CURRENT.locale = locale
    return _TRANSLATIONS[locale]


def deactivate() -> None:
    """Deactivate internationalisation."""
    _CURRENT.locale = None



[command exit=0] /bin/zsh -lc "rtk proxy sed -n '190,245p' tests/test_i18n.py"
        ("es_ES", 5, "female", "5ª"),
        ("it_IT", 3, "male", "3º"),
        ("it_IT", 8, "female", "8ª"),
    ],
)
def test_ordinal_genders(
    locale: str, number: int, gender: str, expected_result: str
) -> None:
    try:
        humanize.i18n.activate(locale)
    except FileNotFoundError:
        pytest.skip("Generate .mo with scripts/generate-translation-binaries.sh")
    else:
        assert humanize.ordinal(number, gender=gender) == expected_result
    finally:
        humanize.i18n
…[867 chars elided]…
null__spec__(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        i18n = importlib.import_module("humanize.i18n")
        monkeypatch.setattr(i18n, "__spec__", None)

        with pytest.raises(Exception, match=self.expected_msg):
            i18n.activate("ru_RU")

    def test_default_locale_path_undefined__spec__(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        i18n = importlib.import_module("humanize.i18n")
        monkeypatch.delattr(i18n, "__spec__")


[command exit=0] /bin/zsh -lc 'rtk git status --short'
ok
[command exit=0] /bin/zsh -lc "rtk proxy sed -n '240,270p' tests/test_i18n.py"
    def test_default_locale_path_undefined__spec__(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        i18n = importlib.import_module("humanize.i18n")
        monkeypatch.delattr(i18n, "__spec__")

        with pytest.raises(Exception, match=self.expected_msg):
            i18n.activate("ru_RU")

    @freeze_time("2020-02-02")
    def test_en_locale(self) -> None:
        three_seconds = NOW - dt.timedelta(seconds=3)
        test_str = humanize.naturaltime(three_seconds)

     
…[39 chars elided]…
    assert test_str == humanize.naturaltime(three_seconds)

        humanize.i18n.activate("en_GB")
        assert test_str == humanize.naturaltime(three_seconds)

        humanize.i18n.deactivate()

    @freeze_time("2020-02-02")
    def test_none_locale(self) -> None:
        three_seconds = NOW - dt.timedelta(seconds=3)

        try:
            humanize.i18n.activate("fr")
            assert humanize.naturaltime(three_seconds) == "il y a 3 secondes"

            humanize.i18n.activate(None)

[file_change] update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204334-humanize-i18n-raises-a-bare-exce/base-1/src/humanize/i18n.py, update ~/.cache/lithify/work/repo-88f605b6c7e4/20261023-204334-humanize-i18n-raises-a-bare-exce/base-1/tests/test_i18n.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
......................................................................ss [  9%]
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
684 passed, 53 skipped in 0.70s

[assistant] Changed `humanize.i18n` to raise `FileNotFoundError` with the same message. Updated the docstring and strengthened both existing tests to check the specific exception.

Checks passed: 684 passed, 53 skipped.
