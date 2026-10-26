#!/usr/bin/env python3
"""List every method that overrides a base-class method, and whether it has `@override`.

One authoritative, deduplicated list for "mark/annotate every override" work and
for checking that a new subclass method carries `@override`. It imports each
module (run it with the project python, from the repo root), walks the classes
the module itself defines, and for every method defined in the class body looks
the name up along the MRO. "Marked" is read from the source: a decorator named
`override` (`@override`, `@typing.override`, `@_utils.override`, ...).

Usage (from the repo root):
    <project python> .lithify/harness/scripts/list_overrides.py [options] [FILES...]
      FILES             default: tenacity/**/*.py and tests/*.py
      --include-object  also list methods whose only base definition is on
                        `object` (__init__, __repr__, __eq__ ... of plain classes)
      --all             also print MARKED lines, not only problems

Output, one line each (path:line is the `def` line):
    UNMARKED  path:line Class.method (overrides module.Base.method)
    MARKED    path:line ...                       (--all only)
    OBJECT    path:line Class.method (only object.method; marked=yes|no)
                                                  (--include-object only)
    UNMARKED  path:line Class.method (nested) ... a class defined inside a
              function (e.g. a test-local BaseRetrying subclass); its bases
              are resolved from the module's globals
    UNCHECKED path:line Class (nested class whose base can't be resolved:
              check its methods by hand)
    UNAVAILABLE module: <import error>   (that file was not checked)
    SUMMARY: ...

Exit codes:
    0  no UNMARKED method (OBJECT lines never fail the run)
    1  at least one UNMARKED method -- add `@override` at each path:line
    2  no module could be imported -- report the check as not run
The scope rule (object-only overrides excluded by default) is a decision: say in
the final message which rule you used and what --include-object would add.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import os
import sys
from pathlib import Path


def default_files() -> list[str]:
    files = [str(p) for p in sorted(Path("tenacity").rglob("*.py"))]
    files += [str(p) for p in sorted(Path("tests").glob("*.py"))]
    return [f for f in files if not f.endswith(("_version.py", "__main__.py"))]


def module_name(path: str) -> str:
    parts = list(Path(path).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_override_decorator(node: ast.expr) -> bool:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id == "override"
    if isinstance(node, ast.Attribute):
        return node.attr == "override"
    return False


def index_source(path: str) -> tuple[dict[tuple[str, str], tuple[int, bool]], list]:
    """(class qualname, method) -> (def line, marked); plus classes nested in defs.

    A nested entry is (line, class name, base expressions, [(method, line, marked)]).
    """
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    defs: dict[tuple[str, str], tuple[int, bool]] = {}
    nested: list[tuple[int, str, list[ast.expr], list[tuple[str, int, bool]]]] = []
    funcs = (ast.FunctionDef, ast.AsyncFunctionDef)

    def marked_of(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return any(is_override_decorator(d) for d in node.decorator_list)

    def visit(node: ast.AST, qual: str | None, in_func: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                if in_func:
                    methods = [
                        (b.name, b.lineno, marked_of(b))
                        for b in child.body
                        if isinstance(b, funcs)
                    ]
                    if child.bases and methods:
                        nested.append((child.lineno, child.name, child.bases, methods))
                    visit(child, None, True)
                else:
                    name = f"{qual}.{child.name}" if qual else child.name
                    visit(child, name, False)
            elif isinstance(child, funcs):
                if qual is not None and not in_func:
                    # Repeated names (property setter, overloads): keep the first
                    # line; marked if any of the definitions is.
                    line, was = defs.get((qual, child.name), (child.lineno, False))
                    defs[(qual, child.name)] = (line, marked_of(child) or was)
                visit(child, None, True)
            else:
                visit(child, qual, in_func)

    visit(tree, None, False)
    return defs, nested


def resolve(expr: ast.expr, module: object) -> type | None:
    """Resolve a base like `tenacity.BaseRetrying` or `float` in module globals."""
    names: list[str] = []
    while isinstance(expr, ast.Attribute):
        names.append(expr.attr)
        expr = expr.value
    if not isinstance(expr, ast.Name):
        return None
    scope = vars(module)
    obj = scope.get(expr.id, getattr(builtins, expr.id, None))
    for attr in reversed(names):
        obj = getattr(obj, attr, None)
    return obj if isinstance(obj, type) else None


def classes_of(module: object, modname: str) -> list[type]:
    found: list[type] = []
    seen: set[int] = set()

    def add(obj: object) -> None:
        if not isinstance(obj, type) or id(obj) in seen:
            return
        if obj.__module__ != modname:
            return
        seen.add(id(obj))
        found.append(obj)
        for value in vars(obj).values():
            add(value)

    for value in vars(module).values():
        add(value)
    return found


def main() -> int:
    args = sys.argv[1:]
    include_object = "--include-object" in args
    show_all = "--all" in args
    files = [a for a in args if not a.startswith("--")] or default_files()
    sys.path.insert(0, os.getcwd())

    counts = {"marked": 0, "unmarked": 0, "object": 0, "nested": 0, "generated": 0}
    imported = 0

    def report(where: str, name: str, base: type, marked: bool) -> None:
        if base is object:
            counts["object"] += 1
            if include_object:
                print(f"OBJECT {where} (only object.{name};"
                      f" marked={'yes' if marked else 'no'})")
            return
        target = f"{base.__module__}.{base.__qualname__}.{name}"
        if marked:
            counts["marked"] += 1
            if show_all:
                print(f"MARKED {where} (overrides {target})")
        else:
            counts["unmarked"] += 1
            print(f"UNMARKED {where} (overrides {target})")

    for path in files:
        if not path.endswith(".py") or not os.path.exists(path):
            continue
        modname = module_name(path)
        try:
            module = importlib.import_module(modname)
        except Exception as exc:  # report and keep checking other files
            print(f"UNAVAILABLE {modname}: {type(exc).__name__}: {exc}")
            continue
        imported += 1
        defs, nested = index_source(path)
        for cls_line, cls_name, base_exprs, methods in nested:
            bases = [resolve(b, module) for b in base_exprs]
            if any(b is None for b in bases):
                counts["nested"] += 1
                print(f"UNCHECKED {path}:{cls_line} {cls_name} (class inside a function"
                      " with a base this script can't resolve: check it by hand)")
                continue
            mro = [m for b in bases if b for m in b.__mro__]
            for name, line, marked in methods:
                base = next((b for b in mro if name in vars(b)), None)
                if base is not None:
                    report(f"{path}:{line} {cls_name}.{name} (nested)", name, base,
                           marked)
        for cls in classes_of(module, modname):
            for name, value in vars(cls).items():
                func = value
                if isinstance(func, (staticmethod, classmethod)):
                    func = func.__func__
                elif isinstance(func, property):
                    func = func.fget
                if not callable(func) or isinstance(func, type):
                    continue
                key = (cls.__qualname__, name)
                if key not in defs:
                    # Generated (dataclass, functools) or assigned, not a `def` here.
                    if inspect.isfunction(func):
                        counts["generated"] += 1
                    continue
                base = next((b for b in cls.__mro__[1:] if name in vars(b)), None)
                if base is None:
                    continue
                line, marked = defs[key]
                report(f"{path}:{line} {cls.__qualname__}.{name}", name, base, marked)

    total = counts["marked"] + counts["unmarked"]
    print(
        f"SUMMARY: {total} overriding method(s): {counts['marked']} marked,"
        f" {counts['unmarked']} unmarked; {counts['object']} object-only override(s)"
        f" {'listed' if include_object else 'excluded (--include-object)'};"
        f" {counts['nested']} nested class(es) unchecked;"
        f" {counts['generated']} generated method(s) skipped;"
        f" {imported}/{len(files)} file(s) imported"
    )
    if imported == 0:
        return 2
    return 1 if counts["unmarked"] else 0


if __name__ == "__main__":
    sys.exit(main())
