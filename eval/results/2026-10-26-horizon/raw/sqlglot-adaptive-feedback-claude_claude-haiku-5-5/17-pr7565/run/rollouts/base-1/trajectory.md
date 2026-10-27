# trajectory base-1

final message:
Oracle now parses `LISTAGG(expr, sep ON OVERFLOW ...)` and round-trips it. The full suite passes: `SUMMARY: 1094 passed, 17874 subtests passed in 52.75s` and `EXIT: 0`.

The Oracle `LISTAGG` now parses into `exp.GroupConcat`, the same node Snowflake and Trino use, with `on_overflow` set to an `exp.OverflowTruncateBehavior` (for `TRUNCATE`) or an `exp.Var` (for `ERROR`).

Changes:
- **`sqlglot/parsers/oracle.py`**: `LISTAGG` is mapped to the shared `_parse_string_agg()` in `FUNCTION_PARSERS`.
- **`sqlglot/generators/oracle.py`**: `exp.GroupConcat` is generated with `groupconcat_sql(self, e, sep=None, on_overflow=True)`. Oracle's delimiter is optional with no default separator, so I passed `sep=None`, unlike Trino's `,` default.
- **`tests/dialects/test_oracle.py`**: new `test_listagg` covering `ON OVERFLOW ERROR`, `TRUNCATE '...' WITH COUNT`, `WITHOUT COUNT`, a plain `LISTAGG(x)`, and a `validate_all` to Oracle and Trino. It also asserts the node class.

Things to know:
- **`ON OVERFLOW TRUNCATE '...'` without a count comes back as `WITH COUNT`.** That's Oracle's default, so it's semantically the same, but the text isn't identical. The test records this as an explicit normalization.
- **Snowflake drops `ON OVERFLOW` when transpiling**, since its generator doesn't pass `on_overflow`. That's existing Snowflake behavior and I left it alone, because Snowflake has no such clause.
- **Oracle `LISTAGG` now transpiles to other dialects as `GroupConcat`.** Previously it was an anonymous function with `WITHIN GROUP`. The suite passes, so no existing test depends on the old passthrough.
- I checked the node types with a Python probe, not the harness's `ast_check.py`, which I didn't run.
- I didn't commit anything.

## events
[assistant] I'll start by finding how the Snowflake `ON OVERFLOW` clause is already handled.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Bash] {"command": "grep -rn \"OVERFLOW\\|overflow\" sqlglot/ --include=*.py | head -50 && echo --- && grep -rn \"ListAgg\\|LISTAGG\" sqlglot/ --include=*.py | head -50", "description": "Find overflow and ListAgg handling in sqlglot"}
[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness 2>/dev/null; git status --short | head", "description": "Locate harness memory and check git status"}
[tool_result] (eval):1: no matches found: --include=*.py
---
(eval):1: no matches found: --include=*.py
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 tests) takes 60–80 s when it runs alone. The slowest test is
  `tests/test_executor.py::TestExecutor::test_execute_tpcds`; with several pytest runs competing
  for CPU it sits there for minutes and looks hung, but it is only slow. Run the dialect's own
  test file first (well under a second), then the full suite once.
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The first grep failed on zsh globbing, so I'm rerunning it with the glob quoted.
[tool_use Bash] {"command": "grep -rn 'OVERFLOW\\|overflow' sqlglot/ --include='*.py' | head -50; echo ---; grep -rn 'ListAgg\\|LISTAGG' sqlglot/ --include='*.py' | head -50", "description": "Search for overflow and ListAgg handling"}
[tool_result] sqlglot/generator.py:5489:    def overflowtruncatebehavior_sql(self, expression: exp.OverflowTruncateBehavior) -> str:
sqlglot/parser.py:7705:        if self._match_text_seq("ON", "OVERFLOW"):
sqlglot/parser.py:7706:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7708:                on_overflow: exp.Expr | None = exp.var("ERROR")
sqlglot/parser.py:7711:                on_overflow = self.expression(
sqlglot/parser.py:7721:            on_ov
…[3455 chars elided]…
ROUP_CONCAT", "LISTAGG", "STRINGAGG"), lambda self: self._parse_string_agg()
sqlglot/parsers/exasol.py:123:        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
sqlglot/dialects/dialect.py:2410:    func_name: str = "LISTAGG",
sqlglot/generators/redshift.py:87:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/exasol.py:342:            self, e, func_name="LISTAGG", within_group=True
sqlglot/generators/duckdb.py:1976:        SELECT LISTAGG(
[tool_use Bash] {"command": "sed -n 7690,7760p sqlglot/parser.py; echo ---; sed -n 5480,5500p sqlglot/generator.py; echo ---; sed -n 125,140p sqlglot/expressions/aggregate.py; echo ---; grep -n 'OverflowTruncate' -r sqlglot tests | head; echo ---; grep -n 'LISTAGG\\|GroupConcat\\|WITHIN\\|_parse_string_agg\\|def _parse_string_agg' sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/parser.py | head -30", "description": "Read Snowflake string_agg parser and related code"}
[tool_result]             safe=safe,
            action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
            default=default,
        )

    def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disj
…[4930 chars elided]…
t/parser.py:7734:        if not self._match_text_seq("WITHIN", "GROUP"):
sqlglot/parser.py:7736:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7742:            exp.GroupConcat(
sqlglot/parser.py:8114:        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
sqlglot/parser.py:8116:        if self._match_text_seq("WITHIN", "GROUP"):
sqlglot/parser.py:9886:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[assistant] The shared `_parse_string_agg` already handles `ON OVERFLOW`, and Snowflake and Trino route `LISTAGG` through it. Next I'll check how Oracle currently parses `LISTAGG` and what the existing tests expect.
[tool_use Bash] {"command": "sed -n 1,80p sqlglot/parsers/oracle.py; echo ---; grep -n 'LISTAGG\\|GroupConcat\\|group_concat' sqlglot/generators/oracle.py; echo ---; grep -rn 'OVERFLOW' tests | head -30; echo ---; grep -rn 'LISTAGG' tests/dialects/test_oracle.py | head", "description": "Inspect Oracle parser, generator, and tests for LISTAGG"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.dialects.dialect import build_formatted_time, build_timetostr_or_tochar, build_trunc
from sqlglot.helper import seq_get
from sqlglot.parser import OPTIONS_TYPE, build_coalesce
from sqlglot.tokens import TokenType

if t.TYPE_CHECKING:
    from sqlglot._typing import E


def _build_to_timestamp(args: list) -> exp.StrToTime | exp.Anonymous:
    if len(args) == 1:
        return exp.Anonymous(this="T
…[2805 chars elided]…
) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:65:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:68:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:71:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
---
[assistant] Oracle has no `LISTAGG` mapping, so it's probably parsed as an anonymous function today. I'll check the current behavior and the Trino/Snowflake round-trips before changing anything.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GRO
…[213 chars elided]…
selects[0])[:400]); print(e.sql('oracle'))\n  except Exception as ex: print('ERR',type(ex).__name__, ex)\n  print('--snow'); \n  try: print(sqlglot.transpile(q,read='oracle',write='snowflake')[0])\n  except Exception as ex: print('ERR',ex)\n\"; git log --oneline -3 -- sqlglot/parsers/oracle.py; ls tests/dialects | grep -i oracle", "description": "Probe current Oracle LISTAGG parse and round-trip"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
--snow
ERR Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees
--snow
ERR Expecting ). 
…[736 chars elided]…
       this=Column(
          this=Identifier(this=last_name, quoted=False),
          join_mark=False),
        nulls_first=False)]),
  joi
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
--snow
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
ea76ca554 Chore: unpin ruff (#7287)
a13995e7c Chore(parser)!: Move `ParserCore` back to `Parser` (#7268)
test_oracle.py
[assistant] Oracle parses `LISTAGG ... WITHIN GROUP` today only as an anonymous function, so the `ON OVERFLOW` clause fails. Before wiring in the shared parser, I need to see how `GroupConcat` is generated for Oracle and how Snowflake's tests cover this.
[tool_use Bash] {"command": "sed -n 2405,2440p sqlglot/dialects/dialect.py; echo ---; grep -n 'GroupConcat\\|def groupconcat' sqlglot/generator.py sqlglot/generators/oracle.py sqlglot/generators/snowflake.py | head; echo ---; grep -rn 'ON OVERFLOW' tests/dialects/test_snowflake.py | head -5; echo ---; sed -n 50,75p tests/dialects/test_trino.py; echo ---; grep -n 'WITHIN GROUP' tests/dialects/test_oracle.py | head -5", "description": "Read group_concat generation and related tests"}
[tool_result] def groupconcat_sql(
    self: Generator,
    expression: exp.GroupConcat,
    func_name: str = "LISTAGG",
    sep: str | None = ",",
    within_group: bool = True,
    on_overflow: bool = False,
) -> str:
    this = expression.this
    separator = self.sql(
        expression.args.get("separator") or (exp.Literal.string(sep) if sep else None)
    )

    on_overflow_sql = self.sql(expression, "on_overflow")
    on_overflow_sql = f" ON OVERFLOW {on_overflow_sql}" if (on_overflow and on_overflow_s
…[1660 chars elided]…
ol) WITHIN GROUP (ORDER BY col DESC) FROM tbl",
            "SELECT LISTAGG(col, ',') WITHIN GROUP (ORDER BY col DESC) FROM tbl",
---
366:            "SELECT CUME_DIST(15, 0.05) WITHIN GROUP (ORDER BY col1, col2) FROM t"
369:            "SELECT DENSE_RANK(15, 0.05) WITHIN GROUP (ORDER BY col1, col2) FROM t"
371:        self.validate_identity("SELECT RANK(15, 0.05) WITHIN GROUP (ORDER BY col1, col2) FROM t")
373:            "SELECT PERCENT_RANK(15, 0.05) WITHIN GROUP (ORDER BY col1, col2) FROM t"
[assistant] Trino already has the exact pattern I need: parse via `_parse_string_agg`, generate via `groupconcat_sql(..., on_overflow=True)`. The harness says to load the dialect-functions skill for FUNCTION_PARSERS / TRANSFORMS changes, so I'll load it and read the Oracle generator's transforms.
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot
…[9631 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "grep -n 'TRANSFORMS\\|import\\|groupconcat' sqlglot/generators/oracle.py | head -30; echo ---; sed -n 20,35p sqlglot/generators/trino.py; echo ---; grep -n 'def test_' tests/dialects/test_oracle.py | tail -5; tail -5 tests/dialects/test_oracle.py", "description": "Read Oracle generator imports and transforms"}
[tool_result] 1:from __future__ import annotations
4:from sqlglot import exp, generator, transforms
5:from sqlglot.dialects.dialect import (
42:    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
65:    TRANSFORMS = {
66:        **generator.Generator.TRANSFORMS,
---

    TRANSFORMS = {
        **PrestoGenerator.TRANSFORMS,
        exp.ArraySum: lambda self, e: (
            f"REDUCE({self.sql(e, 'this')}, 0, (acc, x) -> acc + x, acc -> acc)"
        ),
        exp.ArrayUniqueAgg:
…[484 chars elided]…
ansforms.explode_projection_to_unnest(1),
---
899:    def test_merge_builder_alias(self):
913:    def test_pseudocolumns(self):
927:    def test_chr(self):
931:    def test_full_procedure(self):
973:    def test_create_trigger(self):

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view FOR EACH ROW BEGIN INSERT INTO employees (id, name, dept_id) VALUES (:NEW.id, :NEW.name, :NEW.dept_id) END",
            check_command_warning=True,
        )
[assistant] The skill is loaded. Next I'll read the rest of `groupconcat_sql` and the Oracle generator's import block before editing.
[tool_use Bash] {"command": "sed -n 2440,2452p sqlglot/dialects/dialect.py; echo ---; sed -n 1,20p sqlglot/generators/oracle.py; echo ---; sed -n 62,75p sqlglot/generators/oracle.py; echo ---; sed -n 120,130p sqlglot/parsers/oracle.py", "description": "Read rest of groupconcat_sql and Oracle generator header"}
[tool_result]     modifiers = self.sql(limit)

    if order:
        if within_group:
            listagg = exp.WithinGroup(this=listagg, expression=order)
        else:
            modifiers = f"{self.sql(order)}{modifiers}"

    if modifiers:
        listagg.set("expressions", [f"{args}{modifiers}"])

    return self.sql(listagg)

---
from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_s
…[835 chars elided]…
MOD"),
---
            exp.JSONArrayAgg,
            this=self._parse_format_json(self._parse_bitwise()),
            order=self._parse_order(),
        )

    def _parse_json_array(self, expr_type: type[E], **kwargs) -> E:
        return self.expression(
            expr_type(
                null_handling=self._parse_on_handling("NULL", "NULL", "ABSENT"),
                return_type=self._match_text_seq("RETURNING") and self._parse_type(),
                strict=self._match_text_seq("STRICT"),
[assistant] Plan: route Oracle's `LISTAGG` through the shared `_parse_string_agg` (as Trino and Snowflake do), and generate `GroupConcat` back as `LISTAGG(... ON OVERFLOW ...) WITHIN GROUP (...)`. Oracle's delimiter is optional with no default separator, so the generator passes `sep=None` rather than Trino's `,`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None, on_overflow=True),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now I'll check the parse node and round-trips for each form the task names, plus transpiles to Snowflake and Trino.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GRO
…[215 chars elided]…
\\"]\nfor q in qs:\n  e=sqlglot.parse_one(q,read='oracle'); g=e.selects[0].find(exp.GroupConcat); print(type(e.selects[0]).__name__, type(g).__name__, g.args.get('on_overflow') and type(g.args['on_overflow']).__name__)\n  print(' oracle:', e.sql('oracle'))\n  print(' snow  :', e.sql('snowflake'))\n  print(' trino :', e.sql('trino'))\n\"", "description": "Verify Oracle LISTAGG AST and round-trips"}
[tool_result] GroupConcat GroupConcat OverflowTruncateBehavior
 oracle: SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
 snow  : SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
 trino : SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
GroupConcat GroupConcat Var
 oracle: SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDE
…[714 chars elided]…
ORDER BY last_name) FROM employees
 snow  : SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
 trino : SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
GroupConcat GroupConcat None
 oracle: SELECT LISTAGG(last_name) WITHIN GROUP (ORDER BY last_name) FROM employees
 snow  : SELECT LISTAGG(last_name) WITHIN GROUP (ORDER BY last_name) FROM employees
 trino : SELECT LISTAGG(last_name, ',') WITHIN GROUP (ORDER BY last_name) FROM employees
[assistant] The AST is `GroupConcat` with an `OverflowTruncateBehavior` or `Var` for `on_overflow`, and each form round-trips. Two things to note: Oracle's `TRUNCATE '...'` without a count normalizes to `WITH COUNT` (Oracle's default, so it's semantically equal), and the Snowflake output drops `ON OVERFLOW`, which is existing Snowflake behavior since Snowflake has no such clause. I'll add the test to the Oracle test file and check the file's imports first.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_oracle.py; grep -n 'def test_chr' -A4 tests/dialects/test_oracle.py", "description": "Check Oracle test imports and a sample test"}
[tool_result] from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
927:    def test_chr(self):
928-        self.validate_identity("SELECT CHR(187 USING NCHAR_CS)")
929-        self.validate_identity("SELECT CHR(187)")
930-
931-    def test_full_procedure(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_chr(self):\n        self.validate_identity(\"SELECT CHR(187 USING NCHAR_CS)\")\n        self.validate_identity(\"SELECT CHR(187)\")\n", "new_string": "    def test_chr(self):\n        self.valid
…[1649 chars elided]…
t_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\",\n            write={\n                \"oracle\": \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\",\n                \"trino\": \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-201710-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now I'll run the Oracle test file, using the project Python from `memory.md` if it exists.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; [ -x \"$P\" ] || P=python3; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Run Oracle dialect test file"}
[tool_result] .........................                                                 [100%]
25 passed, 215 subtests passed in 0.33s
[assistant] The Oracle file passes (25 tests). Next is the full suite through the harness runner, in the foreground.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; [ -x \"$P\" ] || P=python3; $P .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-00:49:56 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  90728       00:37 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-4d0cedb1f4.log
ELAPSED: 53s
SUMMARY: 1094 passed, 17874 subtests passed in 52.75s
EXIT: 0
[assistant] Oracle now parses `LISTAGG(expr, sep ON OVERFLOW ...)` and round-trips it. The full suite passes: `SUMMARY: 1094 passed, 17874 subtests passed in 52.75s` and `EXIT: 0`.

The Oracle `LISTAGG` now parses into `exp.GroupConcat`, the same node Snowflake and Trino use, with `on_overflow` set to an `exp.OverflowTruncateBehavior` (for `TRUNCATE`) or an `exp.Var` (for `ERROR`).

Changes:
- **`sqlglot/parsers/oracle.py`**: `LISTAGG` is mapped to the shared `_parse_string_agg()` in `FUNCTION_PARSERS`.
- **`sqlglot/generators/oracle.py`**: `exp.GroupConcat` is generated with `groupconcat_sql(self, e, sep
…[531 chars elided]…
 isn't identical. The test records this as an explicit normalization.
- **Snowflake drops `ON OVERFLOW` when transpiling**, since its generator doesn't pass `on_overflow`. That's existing Snowflake behavior and I left it alone, because Snowflake has no such clause.
- **Oracle `LISTAGG` now transpiles to other dialects as `GroupConcat`.** Previously it was an anonymous function with `WITHIN GROUP`. The suite passes, so no existing test depends on the old passthrough.
- I checked the node types with a Python probe, not the harness's `ast_check.py`, which I didn't run.
- I didn't commit anything.
