# trajectory base-1

final message:
Dotted no-paren function names such as `mytable.current_user` now parse as column references and round-trip unchanged. The full suite passed after my last edit:

`SUMMARY: 1106 passed, 18001 subtests passed in 50.54s` / `EXIT: 0`

**The change**

- `sqlglot/parser.py`: `_parse_field` takes an `optional_parens` argument and passes it to `_parse_function`. The dot branch of `_parse_column_ops` passes `optional_parens=False`, so a bare name after a dot is no longer treated as a function. Parenthesized calls such as `x.y.FOO()` are unaffected.
- `tests/test_parser.py`: new `test_dotted_no_paren_function_names_are_identifiers`. It asserts that `mytable.current_user`, `mytable.current_date` and `db.mytable.current_user` give `exp.Column` and round-trip. It also asserts that `mytable.current_user()` stays a `Dot` and bare `current_user` stays `CurrentUser`.

**Probe results after the fix**

- `mytable.current_user`, `mytable.current_date`, `db.mytable.current_user`: `Column`, round-trip unchanged. Before the fix these became `CurrentUser()` or a `Dot` wrapping `CurrentDate`.
- Dotted `current_user` in snowflake and bigquery, `current_timestamp` and `localtime` in postgres, `sysdate` in oracle and snowflake: all `Column`, round-trip unchanged.
- `mytable.current_user()` and `x.y.FOO()` (bigquery): still `Dot`.
- Bare `current_user`: still `CurrentUser`, output `CURRENT_USER()`.

No probe output failed. No transpile target is involved, so the target-validity check didn't apply. I haven't committed anything.

## events
[assistant] I'll start by reproducing the bug and finding where the parser handles dotted column names.
[tool_use Bash] {"command": "ls .lithify/harness 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -30; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT mytable.current_user FROM mytable','SELECT mytable.current_date FROM mytable','SELECT t.sysdate FROM t','SELECT current_user FROM t']:\n    e=sqlglot.parse_one(s, read='oracle' if 'sysdate' in s else None)\n    print(repr(e.selects[0]), '->', e.sql())\n\"", "description": "Reproduce dotted no-paren function names"}
[tool_use Bash] {"command": "grep -n \"NO_PAREN_FUNCTIONS\\|_parse_column_ops\\|def _parse_column\\b\\|def _parse_column(\\|def _parse_field\\|def _parse_primary\\|def _parse_function\" sqlglot/parser.py | head -50", "description": "Locate relevant parser functions"}
[tool_result] guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentUser()) -> SELECT mytable.CURRENT_USER() FROM mytable
Dot(
  this=Identifier(this=mytable, quoted=False),
  expression=CurrentDate()) -> SELECT mytable.CURRENT_DATE FROM mytable
Column(
  this=Identifier(this=sysdate, quoted=False),
  table=Identifier(this=t, quoted=False),
  join_mark=False) -> SELECT t.sysdate FROM t
CurrentUser() -> SELECT CURRENT_USER() FROM t
[tool_result] 432:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
769:        *NO_PAREN_FUNCTIONS,
5824:        return self._parse_column_ops(this)
6059:            return self._parse_column_ops(interval)
6069:            return self._parse_column_ops(data_type)
6077:                this = self._parse_column_ops(this)
6107:                return self._parse_column_ops(data_type)
6472:    def _parse_column(self) -> exp.Expr | None:
6478:            column = self._parse_column_ops(this) if this else this
6659:    
…[371 chars elided]…
      if optional_parens and token_type in self.NO_PAREN_FUNCTIONS:
6854:                return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
6970:    def _parse_function_properties(self) -> exp.Properties | None:
6976:    def _parse_function_parameter(self) -> exp.Expr | None:
7072:    def _parse_field_def(self) -> exp.Expr | None:
7429:    def _parse_primary_key_part(self) -> exp.Expr | None:
7444:    def _parse_primary_key(
8391:    def _parse_primary_or_var(self) -> exp.Expr | None:
[assistant] The bug reproduces: `mytable.current_user` becomes `CurrentUser()` and `mytable.current_date` becomes a `Dot` with `CurrentDate`. Next I'll read the column-ops and field parsing code.
[tool_use Bash] {"command": "sed -n 6472,6500p sqlglot/parser.py; echo ----; sed -n 6659,6830p sqlglot/parser.py; echo ----; sed -n 6829,6870p sqlglot/parser.py", "description": "Read column ops and field parsing code"}
[tool_result]     def _parse_column(self) -> exp.Expr | None:
        column: exp.Expr | None = self._parse_column_parts_fast()
        if column is None:
            this = self._parse_column_reference()
            if not this:
                this = self._parse_bracket(this)
            column = self._parse_column_ops(this) if this else this

        if column:
            if self.dialect.SUPPORTS_COLUMN_JOIN_MARKS:
                column.set("join_mark", self._match(TokenType.JOIN_MARKER))
            if 
…[8081 chars elided]…
   return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())

            return None

        if any_token:
            if token_type in self.RESERVED_TOKENS:
                return None
        elif token_type not in self.FUNC_TOKENS:
            return None

        self._advance(2)

        parser = self.FUNCTION_PARSERS.get(upper)
        if parser and not anonymous:
            result = parser(self)
        else:
            subquery_predicate = self.SUBQUERY_PREDICATES.get(token_type)
[assistant] The cause is in `_parse_column_ops`. For a dot-qualified part it calls `_parse_field(any_token=True, anonymous_func=True)`, which goes through `_parse_function` with `optional_parens=True`. That makes a bare `current_user` match the no-paren function table. I'll check the other callers of `_parse_field` before changing its signature.
[tool_use Bash] {"command": "grep -rn \"_parse_field(\" sqlglot/ | head -40; echo ---; grep -n \"optional_parens\" sqlglot/parser.py sqlglot/parsers/*.py | head -30; echo ---; git status --short; ls tests | head -80 | tr '\\n' ' '", "description": "Find _parse_field callers and optional_parens uses"}
[tool_result] sqlglot/parser.py:2813:        field = self._parse_field()
sqlglot/parser.py:3249:                this=self._parse_schema() or self._parse_bracket(self._parse_field())
sqlglot/parser.py:4513:        on = self._parse_field() if self._match(TokenType.ON) else None
sqlglot/parser.py:5011:            bucket_field = self._parse_field()
sqlglot/parser.py:5524:            count = self._parse_field(tokens=self.FETCH_TOKENS)
sqlglot/parser.py:6562:        this = self._parse_field()
sqlglot/parser.py:6682
…[3389 chars elided]…
a.py:192:            optional_parens=optional_parens,
---
__init__.py dialects fixtures gen_fixtures.py helpers.py leakcheck.py sqlglot test_build.py test_dialect_entry_points.py test_dialect_imports.py test_diff.py test_docs.py test_errors.py test_executor.py test_expressions.py test_generator.py test_helper.py test_integration_loader.py test_jsonpath.py test_lineage.py test_optimizer.py test_parser.py test_schema.py test_serde.py test_time.py test_tokens.py test_transforms.py test_transpile.py
[assistant] The fix is small: the dot branch should not accept optional-paren functions. Parenthesized calls like `x.y.FOO()` still parse because `optional_parens=False` only disables the bare form. I'll add an `optional_parens` pass-through to `_parse_field` and use it at that one call site.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "        anonymous_func: bool = False,\n    ) -> exp.Expr | None:\n        if anonymous_func:\n            field = (\n                self._parse_function(anonymous=anonymous_func, any_token=any_token)\n                o
…[382 chars elided]…
       self._parse_function(\n                    anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n                )\n                or self._parse_primary()\n            )\n        else:\n            field = self._parse_primary() or self._parse_function(\n                anonymous=anonymous_func, optional_parens=optional_parens, any_token=any_token\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py", "old_string": "                field = self._parse_field(any_token=True, anonymous_func=True)\n\n            # Function calls", "new_string": "                field = self._parse_field(\n                    any_token=True, anonymous_func=True, optional_parens=False\n                )\n\n            # Function calls"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll probe the AST shape and round-trip for several positions and dialects, plus the parenthesized forms that must still be function calls.
[tool_use Bash] {"command": "cat > /tmp/probe_dot.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n (\"SELECT mytable.current_user FROM mytable\", None),\n (\"SELECT mytable.current_date FROM mytable\", None),\n (\"SELECT db.mytable.current_user FROM mytable\", None),\n (\"SELECT mytable.current_user() FROM mytable\", None),\n (\"SELECT current_user FROM t\", None),\n (\"SELECT current_date FROM t\
…[453 chars elided]…
parse_one(s, read=d)\n    col = e.selects[0]\n    print(f\"{d or 'base':10} {s!r}\\n   node={type(col).__name__} {col.sql(d)!r}  -> {e.sql(d)!r}\")\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_dot.py", "description": "Probe AST shape and output for dotted names"}
[tool_result] base       'SELECT mytable.current_user FROM mytable'
   node=Column 'mytable.current_user'  -> 'SELECT mytable.current_user FROM mytable'
base       'SELECT mytable.current_date FROM mytable'
   node=Column 'mytable.current_date'  -> 'SELECT mytable.current_date FROM mytable'
base       'SELECT db.mytable.current_user FROM mytable'
   node=Column 'db.mytable.current_user'  -> 'SELECT db.mytable.current_user FROM mytable'
base       'SELECT mytable.current_user() FROM mytable'
   node=Dot 'mytab
…[617 chars elided]…
'SELECT t.current_user FROM t'
   node=Column 't.current_user'  -> 'SELECT t.current_user FROM t'
snowflake  'SELECT t.sysdate FROM t'
   node=Column 't.sysdate'  -> 'SELECT t.sysdate FROM t'
bigquery   'SELECT t.current_user FROM t'
   node=Column 't.current_user'  -> 'SELECT t.current_user FROM t'
bigquery   'SELECT x.y.FOO() FROM t'
   node=Dot 'x.y.FOO()'  -> 'SELECT x.y.FOO() FROM t'
bigquery   'SELECT t.current_date FROM t'
   node=Column 't.current_date'  -> 'SELECT t.current_date FROM t'
[assistant] The AST is now a `Column` for every dotted position, matching the `t.sysdate` sibling. Parenthesized calls are still `Dot`/function nodes. Next I'll find the existing parser tests to put a regression test beside.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/test_parser.py | head -80; grep -n \"CURRENT_USER\\|current_user\" tests/test_parser.py | head", "description": "Find parser test file structure"}
[tool_result] 12:    def test_parse_empty(self):
16:    def test_parse_into(self):
45:    def test_parse_into_error(self):
66:    def test_parse_into_errors(self):
94:    def test_column(self):
100:    def test_tuple(self):
103:    def test_structs(self):
112:    def test_float(self):
115:    def test_unnest(self):
122:    def test_unnest_projection(self):
128:    def test_unary_plus(self):
131:    def test_table(self):
135:    def test_union(self):
160:    def test_select(self):
175:    def test_command(self
…[1481 chars elided]…
 test_parse_prop_eq(self):
958:    def test_collate(self):
973:    def test_drop_column(self):
978:    def test_udf_meta(self):
990:    def test_token_position_meta(self):
1032:    def test_quoted_identifier_meta(self):
1042:    def test_qualified_function(self):
1048:    def test_pivot_missing_agg_func(self):
1054:    def test_multiple_query_modifiers(self):
1067:    def test_parse_into_grant_principal(self):
1082:    def test_parse_into_grant_privilege(self):
1088:    def test_max_nodes(self):
[tool_use Bash] {"command": "sed -n 1040,1048p tests/test_parser.py; sed -n 1,11p tests/test_parser.py", "description": "Read qualified function test for placement"}
[tool_result]         self.assertEqual(sql[table_meta["start"] : table_meta["end"] + 1], '"test_table_a"')

    def test_qualified_function(self):
        sql = "a.b.c.d.e.f.g.foo()"
        ast = parse_one(sql)
        assert not any(isinstance(n, exp.Column) for n in ast.walk())
        assert len(list(ast.find_all(exp.Dot))) == 7

    def test_pivot_missing_agg_func(self):
import time
import unittest
from unittest.mock import patch

from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains


class TestParser(unittest.TestCase):
[assistant] I'll add a regression test next to `test_qualified_function`, covering the AST shape and round-trip.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_pivot_missing_agg_func(self):", "new_string": "        assert len(list(ast.find_all(exp.Dot))) == 7\n\n    def test_dotted_no_paren_function_names_
…[343 chars elided]…
    self.assertIsInstance(column, exp.Column)\n                self.assertEqual(column.sql(), sql.split(\" FROM\")[0][len(\"SELECT \") :])\n\n        self.assertIsInstance(parse_one(\"SELECT mytable.current_user() FROM mytable\").selects[0], exp.Dot)\n        self.assertIsInstance(parse_one(\"SELECT current_user FROM t\").selects[0], exp.CurrentUser)\n\n    def test_pivot_missing_agg_func(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[assistant] The slicing in that test is hard to read, so I'll make the expected column text explicit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py", "old_string": "        for sql in (\n            \"SELECT mytable.current_user FROM mytable\",\n            \"SELECT mytable.current_date FROM mytable\",\n            \"SELECT db.mytable.current_user FROM mytable\",\n        ):\n  
…[726 chars elided]…
LECT {column_sql} FROM mytable\")\n                self.assertIsInstance(ast.selects[0], exp.Column)\n                self.assertEqual(ast.sql(), f\"SELECT {column_sql} FROM mytable\")\n\n        self.assertIsInstance(parse_one(\"SELECT mytable.current_user() FROM mytable\").selects[0], exp.Dot)\n        self.assertIsInstance(parse_one(\"SELECT current_user FROM t\").selects[0], exp.CurrentUser)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-033951-parser-names-that-are-also-no-pa/base-1/tests/test_parser.py has been updated successfully.
[assistant] Next I'll run the parser tests and the lint check, then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py tests/dialects 2>&1 | tail -15; $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py; $PY -m ruff check sqlglot/parser.py tests/test_parser.py", "description": "Run parser and dialect tests plus ruff"}
[tool_result] ........................................ [  8%]
........................................................................................................ [ 21%]
......................................... [ 27%]
............................ [ 30%]
.............................................................................................................................................................. [ 50%]
.............................. [ 54%]
...................................................
…[83 chars elided]…
...... [ 70%]
........... [ 72%]
.............................. [ 76%]
.............. [ 77%]
.............................................................................................................................................. [ 95%]
....................... [ 98%]
..........                                                        [100%]
793 passed, 11104 subtests passed in 11.96s
Would reformat: tests/test_parser.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_parser.py && git diff --stat && $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py", "description": "Apply ruff formatting to test file"}
[tool_result] 1 file reformatted
 sqlglot/parser.py    | 11 ++++++++---
 tests/test_parser.py | 16 ++++++++++++++++
 2 files changed, 24 insertions(+), 3 deletions(-)
2 files already formatted
[This command modified 1 file you've previously read: tests/test_parser.py. Call Read before editing.]
[assistant] The formatter touched only my new test. Now the full suite, through the harness script the project asks for.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py; echo \"exit=$?\"", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-08:24:41 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-c5a
…[132 chars elided]…
n to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261027-033951-parser-names-that-are-also-no-pa-base-1/d8e9600c-3090-494f-8fde-88567a1a6871/tasks/bcbxuyu2e.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. It is running now: do not start a second copy while it runs. If it is no longer needed, stop it with TaskStop. To check interim output, use Read on that file path.
[assistant] The suite is running in the background. I'll check its progress file rather than sleeping.
[tool_use Bash] {"command": "tail -c 1500 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261027-033951-parser-names-that-are-also-no-pa-base-1/d8e9600c-3090-494f-8fde-88567a1a6871/tasks/bcbxuyu2e.output 2>/dev/null || echo \"no output yet\"", "description": "Check interim full-suite output"}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-08:24:41 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-c5a5d43d25.log
[tool_use ScheduleWakeup] {"delaySeconds": 300, "prompt": "Check the background full-suite run for the dotted no-paren function fix in sqlglot (base-1 worktree); read its output file for the SUMMARY/EXIT lines, then report the summary line.", "reason": "Full suite is running in background; checking back for its SUMMARY line"}
[tool_result ERROR] `noop` is required when `stop` is not true.
[assistant] That scheduling tool is meant for `/loop`, so I won't use it. I'll load Monitor and wait for the run's completion marker instead.
[tool_use ToolSearch] {"query": "select:Monitor", "max_results": 1}
[tool_result] 
[tool_use Monitor] {"description": "Full suite completion (SUMMARY/EXIT lines or failures)", "command": "OUT=/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261027-033951-parser-names-that-are-also-no-pa-base-1/d8e9600c-3090-494f-8fde-88567a1a6871/tasks/bcbxuyu2e.output; until grep -qE \"^(SUMMARY|EXIT:)|EXIT: \" \"$OUT\" 2>/dev/null; do sleep 2; done; grep -E \"SUMMARY|EXIT|FAILED|Traceback\" \"$OUT\"", "timeout_ms": 600000}
[tool_result] Monitor started (task btx1dkws3, expires in 10m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[assistant] The full suite is still running in the background, so I haven't got a SUMMARY line yet. A monitor is watching for its completion and will report back when it finishes.

**What's done so far**

- **Root cause:** in `sqlglot/parser.py`, `_parse_column_ops` parsed the part after a dot with `optional_parens=True`. A bare `current_user` or `current_date` then matched the no-paren function table and became a function node.
- **Fix:** `_parse_field` now takes an `optional_parens` pass-through, and the dot branch of `_parse_column_ops` passes `optional_parens=False`. Parenthesized calls such as `x.y.F
…[891 chars elided]…
 (bigquery) | Dot | `x.y.FOO()` |
| `current_user` (bare) | CurrentUser | `CURRENT_USER()` |

Before the fix, `mytable.current_user` produced `CurrentUser()` and `mytable.current_date` produced a `Dot` wrapping `CurrentDate`.

**Checks run**

- `tests/test_parser.py` and `tests/dialects`: 793 passed, 11104 subtests passed.
- `ruff format --check` and `ruff check`: clean on both changed files. The formatter reflowed my new test.
- Full suite: started via `run_suite.py`, still running at the time of this message. I have not yet read its `SUMMARY`/`EXIT` line, so the full-suite result is pending.
[tool_use Bash] {"command": "OUT=/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261027-033951-parser-names-that-are-also-no-pa-base-1/d8e9600c-3090-494f-8fde-88567a1a6871/tasks/bcbxuyu2e.output; grep -E \"SUMMARY|EXIT|FAILED|Traceback|passed|failed\" \"$OUT\" | tail -20; echo ---; tail -n 5 \"$OUT\"", "description": "Read full-suite summary and exit lines"}
[tool_result] SUMMARY: 1106 passed, 18001 subtests passed in 50.54s
EXIT: 0
---
SUMMARY: 1106 passed, 18001 subtests passed in 50.54s
EXIT: 0
exit=0

[exited with code 0]
[assistant] Dotted no-paren function names such as `mytable.current_user` now parse as column references and round-trip unchanged. The full suite passed after my last edit:

`SUMMARY: 1106 passed, 18001 subtests passed in 50.54s` / `EXIT: 0`

**The change**

- `sqlglot/parser.py`: `_parse_field` takes an `optional_parens` argument and passes it to `_parse_function`. The dot branch of `_parse_column_ops` passes `optional_parens=False`, so a bare name after a dot is no longer treated as a function. Parenthesized calls such as `x.y.FOO()` are unaffected.
- `tests/test_parser.py`: new `test_dotted_no_paren_fu
…[323 chars elided]…
`mytable.current_date`, `db.mytable.current_user`: `Column`, round-trip unchanged. Before the fix these became `CurrentUser()` or a `Dot` wrapping `CurrentDate`.
- Dotted `current_user` in snowflake and bigquery, `current_timestamp` and `localtime` in postgres, `sysdate` in oracle and snowflake: all `Column`, round-trip unchanged.
- `mytable.current_user()` and `x.y.FOO()` (bigquery): still `Dot`.
- Bare `current_user`: still `CurrentUser`, output `CURRENT_USER()`.

No probe output failed. No transpile target is involved, so the target-validity check didn't apply. I haven't committed anything.
