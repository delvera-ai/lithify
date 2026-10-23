"""List `raise ValidationError` statements not immediately preceded by `record_rejection(...)`.

Usage: check_audit.py FILE [FILE ...] [--only FUNC [FUNC ...]]
Exit status 1 if any unaudited raise is found in the selected functions.
"""
import argparse
import ast
import sys


def _call_name(node):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def _is_validation_raise(stmt):
    return isinstance(stmt, ast.Raise) and stmt.exc is not None and (
        _call_name(stmt.exc) == "ValidationError"
        or (isinstance(stmt.exc, ast.Name) and stmt.exc.id == "ValidationError")
    )


def _is_record(stmt):
    return isinstance(stmt, ast.Expr) and _call_name(stmt.value) == "record_rejection"


def _bodies(node):
    for name in ("body", "orelse", "finalbody"):
        block = getattr(node, name, None)
        if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
            yield block
    for h in getattr(node, "handlers", []) or []:
        yield h.body
    for c in getattr(node, "cases", []) or []:
        yield c.body


def _scan(func):
    problems = []
    stack = [func]
    while stack:
        node = stack.pop()
        for block in _bodies(node):
            for i, stmt in enumerate(block):
                if _is_validation_raise(stmt) and not (i > 0 and _is_record(block[i - 1])):
                    problems.append(stmt.lineno)
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    stack.append(stmt)
    return sorted(problems)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--only", nargs="+", default=None, help="function names to check")
    args = ap.parse_args(argv)
    bad = 0
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if args.only and node.name not in args.only:
                continue
            for line in _scan(node):
                print(f"{path}:{line}: {node.name}: ValidationError raised without a preceding record_rejection(...)")
                bad += 1
    if bad == 0:
        print("ok: every checked ValidationError raise is preceded by record_rejection(...)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
