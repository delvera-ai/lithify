# trajectory base-1

final message:
Qualifying an unqualified column inside a lateral now terminates. On a missing table or a column not in the schema it raises `OptimizeError: Column 'arr' could not be resolved`, the same error a plain `SELECT a FROM t` gives. It no longer raises `RecursionError`.

**Cause:** `Resolver.get_source_columns` types a lateral's input column by building a fresh `Resolver` on the parent scope. That resolver's `get_table` asks for the columns of every source, including the same lateral, which starts the loop again. Each fresh resolver has an empty cache, so nothing stopped it.

**Fix** (`sqlglot/optimizer/resolver.py`):
- A shared `_resolving` set of lateral sources is passed to nested resolvers.
- The lateral branch skips the input-type lookup when its source is already in that set, so the cycle stops.

**Tests:** I added `test_qualify_unnest_unqualified_column_terminates` to `tests/test_optimizer.py`. It covers the Spark `LATERAL VIEW EXPLODE` and Snowflake `LATERAL FLATTEN` cases with the table missing, and checks that a schema-present query still qualifies correctly.
- Full suite: 1121 passed, using the project's `env-sqlglot` interpreter.
- `ruff check` and `ruff format` are clean on both files; `mypy` passes on `resolver.py`.

**Not verified:**
- I did not build or run the mypyc-compiled `sqlglot[c]` path. `resolver.py` is in the compiled module list, so that path still needs a check.
- I did not change the BigQuery `UNNEST` branch. Every `UNNEST` shape I tried terminated without recursion, so I did not add a guard there without evidence.

I have not committed anything.

## events
[assistant] I'll reproduce the recursion first, then trace it through the qualify column resolver.
[tool_use Bash] {"command": "git status --short && ls .lithify/harness/scripts/ && cat .lithify/harness/scripts/probe_parse.py | head -50 && grep -rn \"def _expand_\\|def _get_unambiguous\\|def _unnest\\|Unnest\\|Explode\" sqlglot/optimizer/qualify_columns.py | head -60", "description": "Check repo state and locate qualify column code"}
[tool_result] okprobe_parse.py  2.2K
"""Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UN
…[1601 chars elided]…
_by_and_distinct_on(scope: Scope, resolver: Resolver) -> None:
sqlglot/optimizer/qualify_columns.py:477:def _expand_positional_references(
sqlglot/optimizer/qualify_columns.py:518:                    or select_expr.find(exp.Explode, exp.Unnest)
sqlglot/optimizer/qualify_columns.py:648:def _expand_struct_stars_no_parens(
sqlglot/optimizer/qualify_columns.py:702:def _expand_struct_stars_with_parens(expression: exp.Dot) -> list[exp.Alias]:
sqlglot/optimizer/qualify_columns.py:764:def _expand_stars(
[assistant] The Docs tools aren't relevant to this task. Next I'll reproduce the recursion.
[tool_use Bash] {"command": "cat > /tmp/repro_qual.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => col) f\", {\"other\": {\"x\": \"INT\"}}),\n (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(input => col) f\", {\"t\": {\"y\": \"INT\"}}),\n (\"bigquery\", \"
…[250 chars elided]…
    try:\n        print(d, qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema=schema).sql(d))\n    except BaseException as e:\n        print(d, \"EXC\", type(e).__name__, str(e)[:120])\nEOF\nls; <work>/env-sqlglot/bin/python -I /tmp/repro_qual.py \"$PWD\" 2>&1 | tail -30", "description": "Reproduce qualify recursion on unqualified UNNEST/FLATTEN"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
snowflake EXC OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 51
snowflake EXC OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 51
bigquery EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
[assistant] No recursion yet: both cases raise `OptimizeError`. I'll confirm which sqlglot is imported, then read the resolver code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'$PWD'); import sqlglot; print(sqlglot.__file__)\"; grep -n \"class Resolver\" -A 120 sqlglot/optimizer/scope.py sqlglot/optimizer/qualify_columns.py | head -5; grep -n \"def \\|Unnest\\|Lateral\\|Flatten\\|_get_source_columns\\|recurs\" sqlglot/optimizer/qualify_columns.py | sed -n '1,200p' | grep -in \"resol\\|unnest\\|lateral\\|flatten\\|source_col\\|recurs\\|def _qualify_columns\\|def _get_unambig\\|def _expand_stars\\|def _qualify_outputs\"", "description": "Confirm imported sqlglot path and map resolver functions"}
[tool_result] ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/__init__.py
7:198:0:Scope, resolver: Resolver) -> dict[str, t.Any]:
12:432:0:Scope, resolver: Resolver) -> None:
14:537:0:Scope, resolver: Resolver) -> None:
25:sqlglot/optimizer/qualify_columns.py:400:# We shouldn't expand aliases if they match the recursive CTE's columns
26:sqlglot/optimizer/qualify_columns.py:401:# and we are in the recursive part (right sub tree) of the CTE
27
…[60 chars elided]…
n.pop(recursive_cte_column.output_name, None)
29:sqlglot/optimizer/qualify_columns.py:518:or select_expr.find(exp.Explode, exp.Unnest)
30:sqlglot/optimizer/qualify_columns.py:587:def _qualify_columns(
32:sqlglot/optimizer/qualify_columns.py:651:"""[BigQuery] Expand/Flatten foo.bar.* where bar is a struct column"""
33:sqlglot/optimizer/qualify_columns.py:703:"""[RisingWave] Expand/Flatten (<exp>.bar).*, where bar is a struct column"""
34:sqlglot/optimizer/qualify_columns.py:764:def _expand_stars(
[tool_use Bash] {"command": "grep -n \"class Resolver\" -r sqlglot/ ; grep -n \"def \\|Unnest\\|Lateral\\|recurs\\|Explode\" sqlglot/optimizer/scope.py | head -80", "description": "Locate Resolver class and scope helpers"}
[tool_result] sqlglot/optimizer/resolver.py:17:class Resolver:
62 matches in 55 files:

1043:0:exp.Expr) -> str:
130:0:
173:0:
228:0:
232:0:t.Callable[[exp.Expr], bool] | None = None) -> Iterator[exp.Expr]:
235:0:Type[E]) -> E | None:
238:0:Type[E]) -> Iterator[E]:
241:0:exp.Expr, new: exp.Expr) -> None:
255:0:
266:0:
277:0:
291:0:
302:0:
316:0:
321:0:
329:0:
337:0:
394:0:
399:0:
427:0:
448:0:
471:0:
487:0:
497:0:
508:0:
517:0:
521:0:str) -> list[exp.Column]:
533:0:
538:0:
543:0:
548:0:
553:0:
558:0:
563:0:
5
…[511 chars elided]…
er/scope.py:101:def __init__(
sqlglot/optimizer/scope.py:151:def branch(
sqlglot/optimizer/scope.py:209:elif type(node) is exp.Lateral or (
sqlglot/optimizer/scope.py:764:# if the scope is a recursive cte, it must be in the form of base_case UNION ...
sqlglot/optimizer/scope.py:765:# thus the recursive scope is the first section of the union.
sqlglot/optimizer/scope.py:947:def walk_in_scope(
sqlglot/optimizer/scope.py:1001:def find_all_in_scope(
sqlglot/optimizer/scope.py:1023:def find_in_scope(
[tool_use Bash] {"command": "cat -n sqlglot/optimizer/resolver.py", "description": "Read the Resolver class"}
[tool_result]   1 │ from __future__ import annotations
  2 │ 
  3 │ import itertools
  4 │ import typing as t
  5 │ 
  6 │ from sqlglot import exp
  7 │ from sqlglot.dialects.dialect import Dialect
  8 │ from sqlglot.errors import OptimizeError
  9 │ from sqlglot.helper import seq_get, SingleValuedMapping
 10 │ from sqlglot.optimizer.scope import Scope
 11 │ 
 12 │ if t.TYPE_CHECKING:
 13 │     from sqlglot.schema import Schema
 14 │     from collections.abc import Sequence, Mapping
 15 │ 
 16 │ 
 17 │ class 
…[19562 chars elided]…
ot col_type.is_type(exp.DType.UNKNOWN):
405 │                 return col_type
406 │         elif isinstance(source, Scope):
407 │             # iterate over all sources in the scope
408 │             for source_name, nested_source in source.sources.items():
409 │                 col_type = self._get_column_type_from_scope(nested_source, column)
410 │                 if col_type and not col_type.is_type(exp.DType.UNKNOWN):
411 │                     return col_type
412 │ 
413 │         return None
[assistant] The likely loop is `get_source_columns` → `_get_unnest_column_type` → a new `Resolver` on the parent scope → `get_table` → `get_source_columns` again. Each new `Resolver` has its own cache, so nothing stops it. My repro didn't hit it, so I'll check the AST shapes and try more query variants.
[tool_use Bash] {"command": "cat > /tmp/ast_qual.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ne = sqlglot.parse_one(\"SELECT f.value FROM t, LATERAL FLATTEN(input => col) f\", read=\"snowflake\")\nprint(repr(e.args[\"laterals\"]))\ne = sqlglot.parse_one(\"SELECT x FROM t CROSS JOIN UNNEST(arr) AS x\", read=\"bigquery\")\nprint(repr(e.args.
…[688 chars elided]…
ne(sql, read=d), dialect=d, schema=schema).sql(d))\n    except RecursionError:\n        print(\"RECURSION\", sql)\n    except Exception as ex:\n        print(\"EXC\", type(ex).__name__, str(ex)[:100])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/ast_qual.py \"$PWD\" 2>&1 | tail -30", "description": "Probe AST shapes and more query variants for recursion"}
[tool_result] Traceback (most recent call last):
  File "/tmp/ast_qual.py", line 6, in <module>
    print(repr(e.args["laterals"]))
               ~~~~~~^^^^^^^^^^^^
KeyError: 'laterals'
[tool_use Bash] {"command": "sed -i 's/print(repr(e.args\\[\"laterals\"\\]))/print(repr(e.args.get(\"laterals\")))/' /tmp/ast_qual.py && <work>/env-sqlglot/bin/python -I /tmp/ast_qual.py \"$PWD\" 2>&1 | tail -30", "description": "Rerun AST and variant probe with safe dict access"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/ast_qual.py
": command a expects \ followed by text
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'$PWD')\nimport sqlglot\ne = sqlglot.parse_one('SELECT f.value FROM t, LATERAL FLATTEN(input => col) f', read='snowflake')\nprint(repr(e.args.get('laterals'))); print(repr(e.args.get('joins')))\ne = sqlglot.parse_one('SELECT x FROM t, UNNEST(arr) AS x', read='bigquery')\nprint(repr(e.args.get('joins')))\n\" 2>&1 | cut -c1-600", "description": "Print AST shapes for FLATTEN and UNNEST"}
[tool_result] None
[Join(
  this=Lateral(
    this=Explode(
      this=Kwarg(
        this=Var(this=input),
        expression=Column(
          this=Identifier(this=col, quoted=False)))),
    view=False,
    outer=False,
    alias=TableAlias(
      this=Identifier(this=f, quoted=False),
      columns=[
        Identifier(this=SEQ, quoted=False),
        Identifier(this=KEY, quoted=False),
        Identifier(this=PATH, quoted=False),
        Identifier(this=INDEX, quoted=False),
        Identifier(this=VALUE, quoted=False),
        Identifier(this=THIS, quoted=False)]),
    ordinality=False))]
[Join(
  this=Unnest(
    expressions=[
      Column(
        this=Identifier(this=arr, quoted=False, _type=DataType(this=DType.UNKNOWN)),
        _type=DataType(this=DType.UNKNOWN))],
    alias=TableAlias(
      columns=[
        Identifier(this=x, quoted=False)]),
    offset=False),
  kind=CROSS)]
[assistant] Snowflake's `FLATTEN(input => col)` produces `Explode(Kwarg(...))`, so the `isinstance(explode_col, exp.Column)` guard skips the lookup. I'll try variants where the argument is a bare column.
[tool_use Bash] {"command": "cat > /tmp/variants.py <<'EOF'\nimport sys\nsys.path.insert(0, sys.argv[1])\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ncases = [\n (\"snowflake\", \"SELECT value FROM t, LATERAL FLATTEN(col)\", {\"other\": {\"a\": \"INT\"}}),\n (\"snowflake\", \"SELECT f.value FROM t, LATERAL FLATTEN(col) f\", {\"other\": {\"a\": \"INT\"}}),\n (\"snowflake\", \"SELECT f.value FROM
…[1048 chars elided]…
ct=d, schema=schema).sql(d))\n    except RecursionError:\n        print(\"RECURSION\", d, sql, schema)\n    except Exception as ex:\n        print(\"EXC\", d, type(ex).__name__, str(ex).splitlines()[0][:100])\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/variants.py \"$PWD\" 2>&1 | tail -30", "description": "Run qualify on FLATTEN/EXPLODE/UNNEST variants"}
[tool_result] RECURSION snowflake SELECT value FROM t, LATERAL FLATTEN(col) {'other': {'a': 'INT'}}
RECURSION snowflake SELECT f.value FROM t, LATERAL FLATTEN(col) f {'other': {'a': 'INT'}}
RECURSION snowflake SELECT f.value FROM t, LATERAL FLATTEN(col) f {'t': {'a': 'INT'}}
RECURSION spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x {'other': {'a': 'INT'}}
RECURSION spark SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x {'t': {'a': 'INT'}}
RECURSION hive SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x 
…[7 chars elided]…
': {'a': 'INT'}}
EXC bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
EXC bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
OK bigquery SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
EXC bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
OK bigquery SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
EXC bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
[assistant] Reproduced: `LATERAL VIEW EXPLODE(arr)` / `LATERAL FLATTEN(col)` with an unqualified column recurses. Next I'll confirm the cycle from the stack trace.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys, traceback; sys.path.insert(0,'$PWD')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\ntry:\n    qualify(sqlglot.parse_one('SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x', read='spark'), dialect='spark', schema={'other': {'a': 'INT'}})\nexcept RecursionError:\n    tb = traceback.extract_tb(sys.exc_info()[2])\n    for f in tb[:40]: print(f.filename.split('/')[-1], f.lineno, f.name)\n\" 2>&1 | head -60", "description": "Capture recursion stack to confirm cycle"}
[tool_result] <string> 6 <module>
qualify.py 98 qualify
qualify_columns.py 85 qualify_columns
qualify_columns.py 621 _qualify_columns
resolver.py 45 get_table
resolver.py 234 _get_table_name_from_sources
resolver.py 220 _get_all_source_columns
resolver.py 182 get_source_columns
resolver.py 380 _get_unnest_column_type
resolver.py 45 get_table
resolver.py 234 _get_table_name_from_sources
resolver.py 220 _get_all_source_columns
resolver.py 182 get_source_columns
resolver.py 380 _get_unnest_column_type
resolver.p
…[439 chars elided]…
py 220 _get_all_source_columns
resolver.py 182 get_source_columns
resolver.py 380 _get_unnest_column_type
resolver.py 45 get_table
resolver.py 234 _get_table_name_from_sources
resolver.py 220 _get_all_source_columns
resolver.py 182 get_source_columns
resolver.py 380 _get_unnest_column_type
resolver.py 45 get_table
resolver.py 234 _get_table_name_from_sources
resolver.py 220 _get_all_source_columns
resolver.py 182 get_source_columns
resolver.py 380 _get_unnest_column_type
resolver.py 45 get_table
[assistant] The cycle is confirmed: `get_source_columns` (lateral branch) → `_get_unnest_column_type` → a fresh `Resolver` on the parent scope → `get_table` → `_get_all_source_columns` → `get_source_columns` on the same lateral. Each fresh resolver has an empty cache, so nothing stops it. Before choosing a fix, I'll check how `Resolver` is constructed elsewhere and whether `Scope` is hashable.
[tool_use Bash] {"command": "grep -rn \"Resolver(\" sqlglot/ | grep -v \"class Resolver\"; grep -n \"__eq__\\|__hash__\" sqlglot/optimizer/scope.py; grep -rn \"UNNEST_COLUMN_ONLY = True\" sqlglot/dialects | head; git log --oneline -3 -- sqlglot/optimizer/resolver.py", "description": "Check Resolver call sites, Scope hashability, dialects"}
[tool_result] sqlglot/optimizer/qualify_columns.py:71:        resolver = Resolver(scope, schema, infer_schema=infer_schema)
sqlglot/optimizer/resolver.py:379:            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
sqlglot/optimizer/pushdown_projections.py:174:        resolver = Resolver(scope, schema)
0 matches for '__eq__\|__hash__'
sqlglot/dialects/bigquery.py:25:    UNNEST_COLUMN_ONLY = True
b3fa15979 refactor(optimizer): continuation on typing coverage improvements (#7572)
8f572f865 fix(optimizer)!: qualify UNPIVOT on CTE sources (#7550)
5351ca128 fix(optimizer): EXPLODE qualify and annotate (#7549)
[assistant] `Scope` has no custom `__eq__`/`__hash__`, so it can be used as an identity-keyed set member. My plan is a shared in-progress set of lateral sources. The lateral branch skips type inference when its source is already being resolved, and nested resolvers receive the same set. Then the parent-scope lookup can no longer re-enter the same source. I'll implement that now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:\n        self.scope: Scope = scope\n        self.schema: Schema = schema\n        self.dialect: Dialect = schema.diale
…[779 chars elided]…
ng[str, str] | None = None\n        self._all_columns: set[str] | None = None\n        self._infer_schema: bool = infer_schema\n        self._get_source_columns_cache: dict[tuple[str, bool], Sequence[str]] = {}\n        # Lateral sources whose input column is being typed, shared with nested resolvers to break cycles\n        self._resolving: set[Scope] = set() if resolving is None else resolving"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "                    if isinstance(explode_col, exp.Column) and source.parent:\n                        col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        columns.ext
…[221 chars elided]…
 not in self._resolving\n                    ):\n                        self._resolving.add(source)\n                        try:\n                            col_type = self._get_unnest_column_type(explode_col, source.parent)\n                        finally:\n                            self._resolving.discard(source)\n                        columns.extend(self._struct_field_names(col_type))"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py", "old_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema)", "new_string": "            parent_resolver = Resolver(scope, self.schema, self._infer_schema, self._resolving)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/sqlglot/optimizer/resolver.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I /tmp/variants.py \"$PWD\" 2>&1 | tail -30; <work>/env-sqlglot/bin/python -I /tmp/repro_qual.py \"$PWD\" 2>&1 | tail", "description": "Apply resolver cycle guard and rerun variant probes"}
[tool_result] EXC snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 40
EXC snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 42
EXC snowflake OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 42
EXC spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
EXC spark OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
EXC hive OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 40
EXC bigquery OptimizeError 
…[357 chars elided]…
T(`t`.`arr`) AS `x`
EXC bigquery OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
snowflake EXC OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 51
snowflake EXC OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 51
bigquery EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
bigquery SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`arr`) AS `x`
[assistant] Both recursion paths now terminate. Every case ends in a clean `OptimizeError` instead of recursion. The Spark case with `t` missing from the schema is the one I need to check against baseline: `arr` could reasonably be inferred to `t`, so I'll confirm the error matches how plain unqualified columns behave when `t` is missing.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'$PWD')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor sql,d,s in [('SELECT a FROM t', 'spark', {'other': {'a': 'INT'}}), ('SELECT a FROM t, u', 'spark', {'other': {'a': 'INT'}}), ('SELECT x, arr FROM t LATERAL VIEW EXPLODE(arr) v AS x', 'spark', {'other': {'a': 'INT'}})]:\n    try: print(qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema=s).sql(d))\n    except Exception as e: print('EXC', type(e).__name__, str(e).splitlines()[0])\n\"; git stash list | head -0", "description": "Compare unqualified column behavior with missing table"}
[tool_result ERROR] Exit code 1
EXC OptimizeError Column 'a' could not be resolved. Line: 1, Col: 8
EXC OptimizeError Column 'a' could not be resolved. Line: 1, Col: 8
EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 13
head: illegal line count -- 0

thread 'main' (43234868) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
[assistant] Baseline behaves the same: a plain `SELECT a FROM t` with `t` missing from the schema also raises `OptimizeError`, so the new result is consistent. Next I'll find existing tests for lateral explode qualification so I can add a regression test next to them.
[tool_use Bash] {"command": "grep -rn \"EXPLODE\\|LATERAL VIEW\\|FLATTEN\" tests/test_optimizer.py tests/fixtures/optimizer/qualify_columns.sql | head -30; grep -n \"def test_qualify_columns\\|assertRaises(OptimizeError)\" tests/test_optimizer.py | head", "description": "Find existing qualify tests for lateral explode"}
[tool_result] tests/test_optimizer.py:718:                    "SELECT ci.name, ci.age FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci",
tests/test_optimizer.py:729:            "SELECT `ci`.`name` AS `name`, `ci`.`age` AS `age` FROM `my_table` AS `my_table` LATERAL VIEW EXPLODE(`my_table`.`items`) ci AS `ci`",
tests/test_optimizer.py:738:                    "SELECT (SELECT SUM(ci.amount) FROM my_table LATERAL VIEW EXPLODE(items) ci AS ci WHERE ci.type = 'promotion') AS total FROM my_table",
tests/test_optim
…[757 chars elided]…
 _0 AS c;
tests/fixtures/optimizer/qualify_columns.sql:814:SELECT c FROM x LATERAL VIEW EXPLODE (a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:815:SELECT t.c AS c FROM x AS x LATERAL VIEW EXPLODE(x.a) t AS c;
tests/fixtures/optimizer/qualify_columns.sql:851:SELECT c FROM (SELECT 1 a) AS x LATERAL VIEW EXPLODE(a) AS c;
tests/fixtures/optimizer/qualify_columns.sql:852:SELECT _0.c AS c FROM (SELECT 1 AS a) AS x LATERAL VIEW EXPLODE(x.a) _0 AS c;
3 matches in 3 files:

357:0:
753:0:
763:0:
[tool_use Bash] {"command": "sed -n 700,760p tests/test_optimizer.py; sed -n 1680,1700p tests/test_optimizer.py", "description": "Read existing lateral explode qualify tests"}
[tool_result]                 parse_one("select foo from x"),
                schema={"foo": {"y": "int"}},
            )

        # Test ambiguous columns error with PIVOT (which skips "could not be resolved" check)
        with self.assertRaisesRegex(OptimizeError, "Ambiguous column 'a'"):
            expression = parse_one(
                "SELECT * FROM (SELECT a, b, c FROM x) PIVOT (SUM(b) FOR c IN ('x', 'y'))"
            )
            qualified = optimizer.qualify_columns.qualify_columns(
             
…[2725 chars elided]…
.type.this)
                self.assertEqual(sql, expression.sql())

    def test_lateral_annotation(self):
        expression = optimizer.optimize(
            parse_one("SELECT c FROM (select 1 a) as x LATERAL VIEW EXPLODE (a) AS c")
        ).expressions[0]
        self.assertEqual(expression.type.this, exp.DataType.Type.INT)

    def test_derived_tables_column_annotation(self):
        schema = {"x": {"cola": "INT"}, "y": {"cola": "FLOAT"}}
        sql = """
            SELECT a.cola AS cola
[assistant] I'll add a regression test beside the existing lateral-explode checks. Before writing expected values, I'll check what the schema-present success path produces.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'$PWD')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor sql,d,s in [('SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x', 'spark', {'t': {'arr': 'ARRAY<INT>'}}), ('SELECT f.value FROM t, LATERAL FLATTEN(col) f', 'snowflake', {'t': {'col': 'VARIANT'}}), ('SELECT f.value FROM t, LATERAL FLATTEN(col) f', 'snowflake', {'other': {'a': 'INT'}})]:\n    try: print(qualify(sqlglot.parse_one(sql, read=d), dialect=d, schema=s).sql(d))\n    except Exception as e: print('EXC', type(e).__name__, str(e).splitlines()[0])\n\"", "description": "Check schema-present success outputs for regression test"}
[tool_result] SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`
SELECT "F"."VALUE" AS "VALUE" FROM "T" AS "T", LATERAL FLATTEN("T"."COL") AS "F"("SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS")
EXC OptimizeError Column 'COL' could not be resolved. Line: 1, Col: 42
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "        self.assertEqual(expression.selects[0].type, exp.DataType.build(\"DOUBLE\", dialect=\"spark\"))\n\n    def test_qualify_columns__with_invisible(self):", "new_string": "        self.assertEqual(expression.s
…[812 chars elided]…
x FROM t LATERAL VIEW EXPLODE(arr) v AS x\", read=\"spark\"),\n            schema={\"t\": {\"arr\": \"ARRAY<INT>\"}},\n            dialect=\"spark\",\n        )\n        self.assertEqual(\n            expression.sql(dialect=\"spark\"),\n            \"SELECT `v`.`x` AS `x` FROM `t` AS `t` LATERAL VIEW EXPLODE(`t`.`arr`) v AS `x`\",\n        )\n\n    def test_qualify_columns__with_invisible(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[assistant] Now I'll run the new test and the optimizer test module, then the full suite as the final gate.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py -k \"unnest_unqualified or lateral or qualify\" 2>&1 | tail -5; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py tests/dialects 2>&1 | tail -5", "description": "Run new regression test and optimizer/dialect tests"}
[tool_result] ........                           [100%]
8 passed, 72 deselected, 470 subtests passed in 2.38s
........................................................................................................................................... [ 62%]
.............................. [ 65%]
................................................ [ 71%]
.......................................................................................................................................................................................................................................                        [100%]
814 passed, 15003 subtests passed in 16.48s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; time $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite as final gate"}
[tool_result] ........................................ [ 30%]
........................................................................................ [ 38%]
...................................................................................................................... [ 48%]
............................ [ 51%]
................................................................................................................................................... [ 64%]
.......................................
…[85 chars elided]…
............................................................................................................................................................................................................... [ 94%]
...................................................................        [100%]
1121 passed, 18168 subtests passed in 47.75s
$PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1  115.92s user 12.65s system 267% cpu 47.996 total
tail -8  0.00s user 0.00s system 0% cpu 47.996 total
[assistant] The full suite passes (1121 passed). The issue also mentions the compiled `sqlglot[c]` build, so I'll check whether `resolver.py` is in the mypyc module list and whether the BigQuery `UNNEST` branch can still recurse.
[tool_use Bash] {"command": "grep -rn \"resolver\\|optimizer\" setup.py sqlglotc/*.py 2>/dev/null | head -5; PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'$PWD')\nimport sqlglot\nfrom sqlglot.optimizer.qualify import qualify\nfor sql,s in [('SELECT x FROM t, UNNEST(arr) AS x', {'o': {'a': 'INT'}}), ('SELECT x FROM t CROSS JOIN UNNEST(arr
…[181 chars elided]…
}}), ('SELECT x FROM t, UNNEST(y) AS x, UNNEST(x) AS y', None)]:\n    try: print('OK', qualify(sqlglot.parse_one(sql, read='bigquery'), dialect='bigquery', schema=s).sql('bigquery'))\n    except RecursionError: print('RECURSION', sql)\n    except Exception as e: print('EXC', type(e).__name__, str(e).splitlines()[0][:90])\n\"", "description": "Check compiled module list and BigQuery UNNEST shapes"}
[tool_result] sqlglotc/setup.py:60:            "optimizer",
sqlglotc/setup.py:63:                "resolver.py",
sqlglotc/setup.py:132:    """Pin sqlglot to the matching version so resolvers keep the two packages in lockstep."""
EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 37
EXC OptimizeError Column 'arr' could not be resolved. Line: 1, Col: 27
OK SELECT `x` AS `x` FROM `t` AS `t` CROSS JOIN UNNEST(`t`.`y`) AS `x` CROSS JOIN UNNEST(`x`) AS `y`
[assistant] `resolver.py` is in the mypyc-compiled list, and the BigQuery `UNNEST` shapes I tried terminate without recursion, so I left that branch alone. Last, I'll run the lint and type checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PY -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py) 2>&1 | tail -5; ($PY -m mypy --version && $PY -m mypy sqlglot/optimizer/resolver.py) 2>&1 | tail -3; git diff --stat", "description": "Run ruff and mypy on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
Would reformat: tests/test_optimizer.py
1 file would be reformatted, 1 file already formatted
mypy 2.3.0.post2 (compiled: yes)
Success: no issues found in 1 source file
sqlglot/optimizer/resolver.py | 24 ++++++++++++++++++++----
 tests/test_optimizer.py       | 20 ++++++++++++++++++++
 2 files changed, 40 insertions(+), 4 deletions(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff tests/test_optimizer.py 2>&1 | head -30; git stash list --format='%H %gs' | head -0; git show HEAD:tests/test_optimizer.py > /tmp/orig_test_optimizer.py && $PY -m ruff format --check /tmp/orig_test_optimizer.py", "description": "Inspect formatting diff and check if baseline was formatted"}
[tool_result] --- tests/test_optimizer.py
+++ tests/test_optimizer.py
@@ -758,7 +758,9 @@
         ):
             with self.subTest(sql):
                 with self.assertRaisesRegex(OptimizeError, "could not be resolved"):
-                    optimizer.qualify.qualify(parse_one(sql, read=read), schema=schema, dialect=read)
+                    optimizer.qualify.qualify(
+                        parse_one(sql, read=read), schema=schema, dialect=read
+                    )
 
         expression = optimizer.qualify.qualify(
             parse_one("SELECT x FROM t LATERAL VIEW EXPLODE(arr) v AS x", read="spark"),

1 file would be reformatted
head: illegal line count -- 0

thread 'main' (43247845) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
1 file already formatted
[assistant] The only formatting issue is in my new test, so I'll apply the formatter's suggestion and re-run the targeted tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py", "old_string": "                    optimizer.qualify.qualify(parse_one(sql, read=read), schema=schema, dialect=read)", "new_string": "                    optimizer.qualify.qualify(\n                        parse_one(sql, read=read), schema=schema, dialect=read\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-163304-optimizer-sqlglot-optimizer-qual/base-1/tests/test_optimizer.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/optimizer/resolver.py tests/test_optimizer.py && $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_optimizer.py 2>&1 | tail -2; git diff sqlglot/", "description": "Recheck formatting, rerun optimizer tests, show source diff"}
[tool_result] 2 files already formatted
................................................................................                                          [100%]
80 passed, 3911 subtests passed in 13.38s
sqlglot/optimizer/resolver.py | 24 ++++++++++++++++++++----
 1 file changed, 20 insertions(+), 4 deletions(-)

--- Changes ---

sqlglot/optimizer/resolver.py
  @@ -21,7 +21,13 @@ class Resolver:
  -    def __init__(self, scope: Scope, schema: Schema, infer_schema: bool = True) -> None:
  +    def __ini
…[1494 chars elided]…
 isinstance(source.expression, exp.SetOperation):
                   columns = self.get_source_columns_from_set_op(source.expression)
  @@ -376,7 +392,7 @@ class Resolver:
  -            parent_resolver = Resolver(scope, self.schema, self._infer_schema)
  +            parent_resolver = Resolver(scope, self.schema, self._infer_schema, self._resolving)
               table_identifier = parent_resolver.get_table(column)
               if not table_identifier:
                   return None
  +20 -4
[assistant] Qualifying an unqualified column inside a lateral now terminates. On a missing table or a column not in the schema it raises `OptimizeError: Column 'arr' could not be resolved`, the same error a plain `SELECT a FROM t` gives. It no longer raises `RecursionError`.

**Cause:** `Resolver.get_source_columns` types a lateral's input column by building a fresh `Resolver` on the parent scope. That resolver's `get_table` asks for the columns of every source, including the same lateral, which starts the loop again. Each fresh resolver has an empty cache, so nothing stopped it.

**Fix** (`sqlglot/optimi
…[393 chars elided]…
 the table missing, and checks that a schema-present query still qualifies correctly.
- Full suite: 1121 passed, using the project's `env-sqlglot` interpreter.
- `ruff check` and `ruff format` are clean on both files; `mypy` passes on `resolver.py`.

**Not verified:**
- I did not build or run the mypyc-compiled `sqlglot[c]` path. `resolver.py` is in the compiled module list, so that path still needs a check.
- I did not change the BigQuery `UNNEST` branch. Every `UNNEST` shape I tried terminated without recursion, so I did not add a guard there without evidence.

I have not committed anything.
