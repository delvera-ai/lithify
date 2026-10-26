# trajectory comp-1

final message:
Changed `humanize.i18n` to raise `FileNotFoundError` with the same message, updated the docstring, and added a regression test. Existing tests remain unchanged.

Checks passed: 685 passed, 53 skipped.

## events
[assistant] I’ll update the exception type, add a regression test, and run the project checks.
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
tests/test_i18n.py:227:        "Humanize cannot determinate the default location of the"
src/humanize/i18n.py:74:        Exception: If humanize cannot find the locale folder.
src/humanize/i18n.py:85:            "Humanize cannot determinate the default location of the 'locale' folder. "
src/humanize/i18n.py:88:        raise Exception(msg)
AGENTS.md

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,140p' src/humanize/i18n.py"
"""Activate, get and deactivate translations."""

from __future__ import annotations

import gettext as gettext_module
from threading import local

TYPE_CHECKING = False
if TYPE_CHECKING:
    import os
    import pathlib

__all__ = ["activate", "deactivate", "decimal_separator", "thousands_separator"]

_TRANSLATIONS: dict[str | None, gettext_module.NullTranslations] = {
    None: gettext_module.NullTranslations()
}
_CURRENT = local()


# Mapping of locale to thousands separator
_THOUSANDS_SEPARA
…[2525 chars elided]…
ranslate.

    Returns:
        str: Translated text.
    """
    return get_translation().pgettext(msgctxt, message)


def _ngettext(message: str, plural: str, num: int) -> str:
    """Plural version of _gettext.

    Args:
        message (str): Singular text to translate.
        plural (str): Plural text to translate.
        num (int): The number (e.g. item count) to determine translation for the
            respective grammatical number.

    Returns:
        str: Translated text.
    """

[command exit=0] /bin/zsh -lc "rtk proxy sed -n '1,270p' tests/test_i18n.py"
"""Internationalisation tests."""

from __future__ import annotations

import datetime as dt
import importlib

import pytest
from freezegun import freeze_time

import humanize

with freeze_time("2020-02-02"):
    NOW = dt.datetime.now(tz=dt.timezone.utc)


@freeze_time("2020-02-02")
def test_i18n() -> None:
    three_seconds = NOW - dt.timedelta(seconds=3)
    one_min_three_seconds = dt.timedelta(milliseconds=67_000)

    assert humanize.naturaltime(three_seconds) == "3 seconds ago"
    assert h
…[8136 chars elided]…
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

[file_change] update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-204358-humanize-i18n-raises-a-bare-exce/comp-1/src/humanize/i18n.py, update ~/.cache/lithify/work/repo-f19ff99309c1/20261023-204358-humanize-i18n-raises-a-bare-exce/comp-1/tests/test_i18n.py
[command exit=0] /bin/zsh -lc 'rtk proxy env PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no'
......................................................................ss [  9%]
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
685 passed, 53 skipped in 0.67s

[assistant] Changed `humanize.i18n` to raise `FileNotFoundError` with the same message, updated the docstring, and added a regression test. Existing tests remain unchanged.

Checks passed: 685 passed, 53 skipped.
