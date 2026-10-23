"""Shared holdout logic. Runs in the repository under test (cwd); never shipped into it."""

from __future__ import annotations

import importlib
import os
import sys
import traceback

sys.path.insert(0, os.getcwd())


def _labelled(rec: dict) -> bool:
    return all(isinstance(rec.get(k), str) and rec[k] for k in ("field", "reason"))


def check(module: str, func: str, good: list[tuple[object, object]], bad: list[object]) -> int:
    failures: list[str] = []
    try:
        mod = importlib.import_module(module)
        fn = getattr(mod, func)
        errors = importlib.import_module("app.errors")
        audit = importlib.import_module("app.audit")
    except Exception:
        print(f"FAIL import {module}.{func}:\n{traceback.format_exc(limit=2)}")
        return 1
    for value, expected in good:
        audit.REJECTIONS.clear()
        try:
            got = fn(value)
        except Exception as e:
            failures.append(f"{func}({value!r}) raised {type(e).__name__}: {e}; expected {expected!r}")
            continue
        if got != expected or type(got) is not type(expected):
            failures.append(f"{func}({value!r}) returned {got!r}; expected {expected!r}")
        if audit.REJECTIONS:
            failures.append(f"{func}({value!r}) accepted the input but recorded a rejection")
    for value in bad:
        audit.REJECTIONS.clear()
        try:
            got = fn(value)
        except errors.AppError:
            pass
        except Exception as e:
            failures.append(f"{func}({value!r}) raised {type(e).__name__}, which is not an AppError")
            continue
        else:
            failures.append(f"{func}({value!r}) returned {got!r}; expected the input to be rejected")
            continue
        recs = [r for r in audit.REJECTIONS if isinstance(r, dict)]
        if not any(r.get("value") == value or r.get("value") is value for r in recs):
            failures.append(f"{func}({value!r}) was rejected without an audit record of the rejected value")
        elif not all(_labelled(r) for r in recs):
            failures.append(f"{func}({value!r}) recorded a rejection without a field name or reason")
    for f in failures:
        print("FAIL " + f)
    print(f"{func}: {len(good) + len(bad) - len(failures)}/{len(good) + len(bad)} cases ok")
    return 1 if failures else 0
