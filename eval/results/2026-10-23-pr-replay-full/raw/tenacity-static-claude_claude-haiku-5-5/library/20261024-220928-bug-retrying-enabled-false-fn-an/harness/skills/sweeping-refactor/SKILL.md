---
name: sweeping-refactor
description: Load when a task applies the same mechanical edit to every member of a set across the codebase, such as "mark every method that overrides a base method with @override", adding a decorator, annotation, import or rename to every subclass, strategy or test helper. Covers building the authoritative target list (scripts/list_overrides.py for overrides), applying the edit by script, proving nothing was missed, and what still has to ship with a refactor.
---

# Applying one edit to every member of a set

The edit is easy. The risk is the set: a member left out passes every gate and nobody
notices. A runtime walker over `cls.__subclasses__()` or module globals cannot see classes
defined inside a function. One run marked 66 methods, called that list complete, and missed
the `tenacity.BaseRetrying` subclass defined inside a test method in `tests/test_tenacity.py`.

## 1. Build the list with a script, before editing
- Overrides: `<project python> .lithify/harness/scripts/list_overrides.py > /tmp/targets.txt;
  echo "exit=$?"; tail -1 /tmp/targets.txt`. Run it from the repo root. It imports
  `tenacity/**` and `tests/*.py`, resolves classes nested in functions from module globals,
  prints `UNMARKED path:line Class.method (overrides Base.method)` and a SUMMARY line. A
  `(nested)` tag means a class defined inside a function. Before the `@override` refactor it
  found 68 overriding methods (2 nested) and 43 object-only ones.
- Object-only overrides (a plain class's `__init__`/`__repr__`, whose only base definition is
  on `object`) are left out by default. `--include-object` lists them. Choose a scope rule,
  apply it to everything, and state it in the final message along with the count it leaves
  out. Don't apply it to some classes and not others.
- Other kinds of sets: write the same kind of list with `ast` and save it to /tmp. Don't use
  grep for this.
- If two counts of the same set disagree (an early estimate vs the script, or the walker vs
  the edit count), diff the two lists before going on. Don't declare either one
  authoritative until you can explain the gap.

## 2. Apply the edit by script, bottom-up
- Put the helper script in the scratchpad, outside the repo. Run it from the repo root with
  `PYTHONPATH=$PWD <project python> <script>`. Without that, `import tenacity` fails with
  `ModuleNotFoundError`, because the script's own directory goes on `sys.path`, not the cwd.
- Insert at AST-located `def` lines in descending line order, so earlier inserts don't shift
  later targets. Copy the def's own indentation. Put a new decorator directly above the `def`,
  below any existing decorators (`@abc.abstractmethod`, `@gen.coroutine`, `@property`).
- To add an import to many files with anchor replacement: assert that each anchor occurs once
  and that `old != new`. Afterwards, `grep -L '<new import>'` the touched files. One run's
  batch edit printed "ok" for a file it hadn't changed.

## 3. Done means
1. Re-run `list_overrides.py`. It must show `0 unmarked` and `0 nested class(es) unchecked`,
   and its total must equal the number of decorators you added (`git diff -U0 | grep -c
   '^+ *@override'`). Read the counts. Don't just check that the exit code is 0.
2. If you add a guard test, a runtime walker won't see nested classes. Say so in the final
   message, or cover those classes another way.
3. Version-gated code: the project venv is Python 3.12, and no 3.10/3.11 interpreter is on
   this host (`python3.10`/`python3.11` not found; only newer ones). Don't go looking for
   one. Define the fallback at module level, unconditionally, so a test can call it
   directly. Then report the version-switch line itself as checked by reading only.
4. Run system.md steps 2–3 (full suite, `check_changed.py`). After `tenacity/_utils.py`
   provides `override`, `check_changed.py` also fails on any added overriding method that
   doesn't carry `@override`.

## 4. A refactor still ships its companion files
"No behaviour change" is not a reason to skip `tenacity-change-contract`. Read its §2:
changes to internal structure and typing that keep behaviour still get an `other:` reno note.
Decide based on that section, and give the decision in the final message.
