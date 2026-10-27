# trajectory base-1

final message:
The ClickHouse `groupConcat` parametric form now parses and round-trips. The Superset query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` returns the same SQL, and the full suite passes (1081 tests, run with the project's pytest command).

**What changed**
- **Parser** (`sqlglot/parsers/clickhouse.py`): `groupConcat` now has a function parser. The first parenthesised argument is the separator and the second is the column, so it becomes `exp.GroupConcat(this=column, separator=sep)`. This mirrors how `quantile(0.5)(a)` is already parsed.
- **Generator** (`sqlglot/generators/clickhouse.py`): a `groupconcat_sql` method emits `groupConcat(sep)(col)` when a separator is present, and `groupConcat(col)` otherwise.
- **Tests** (`tests/dialects/test_clickhouse.py`): round-trip tests for the Superset query and the plain form, plus a MySQL → ClickHouse translation check. `GROUP_CONCAT(x SEPARATOR ',')` now becomes `groupConcat(',')(x)`, which is the correct ClickHouse equivalent.

**Choices I made that you may want to change**
- **Plain multi-argument calls** such as `groupConcat(x, 10)` still parse as an anonymous function, so their output is unchanged.
- **Parametric calls with a max-size argument**, such as `groupConcat(', ', 10)(x)`, now raise a `ParseError`. `GroupConcat` has no slot for that second argument, and silently dropping it would produce wrong SQL. This shape errored before too, so it is not a regression. Supporting it would need a new argument on the expression.
- **Other dialects' output** for `GroupConcat` is unaffected. Only ClickHouse generation changed. Going from ClickHouse to another dialect works as before (for example, to DuckDB it gives `LISTAGG(part_name, ', ')`).

## events
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|PARAMETRIC\\|quantile\\|_parse_quantile\\|params\" sqlglot/dialects/clickhouse.py | head -80", "description": "Search ClickHouse dialect for parametric aggregate handling"}
[tool_use Bash] {"command": "grep -n -i \"groupconcat\\|GroupConcat\" sqlglot/*.py sqlglot/dialects/*.py tests/dialects/test_clickhouse.py | head -40", "description": "Search codebase for GroupConcat references"}
[tool_result] (Bash completed with no output)
[tool_result] sqlglot/dialects/dialect.py:2397:def groupconcat_sql(
sqlglot/dialects/dialect.py:2399:    expression: exp.GroupConcat,
sqlglot/parser.py:7645:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7679:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7686:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7692:            exp.GroupConcat(
sqlglot/parser.py:9835:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "sed -n 9800,9840p sqlglot/parser.py && grep -n \"class GroupConcat\" -A 12 sqlglot/expressions.py && grep -n \"def _parse_function_call\\|PARAMETRIC\\|def _parse_params\\|params\" sqlglot/parser.py | head -30 && grep -n \"PARAMETRIC\\|parametric\\|_parse_params\\|quantile\" sqlglot/dialects/clickhouse.py | head", "description": "Inspect group_concat parser and GroupConcat expression"}
[tool_result ERROR] Exit code 2
            if isinstance(node, exp.Distinct) and len(node.expressions) > 1:
                concat_exprs = [
                    self.expression(
                        exp.Concat(
                            expressions=node.expressions,
                            safe=True,
                            coalesce=self.dialect.CONCAT_COALESCE,
                        )
                    )
                ]
                node.set("expressions", concat_exprs)
                retur
…[660 chars elided]…
, args))

            this = order or concat_exprs(args[0], args)
        else:
            this = None

        separator = self._parse_field() if self._match(TokenType.SEPARATOR) else None

        return self.expression(exp.GroupConcat(this=this, separator=separator))

    def _parse_initcap(self) -> exp.Initcap:
        expr = exp.Initcap.from_arg_list(self._parse_function_args())

        # attach dialect's default delimiters
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot/ | head -50; grep -rn \"class GroupConcat\" -A 10 sqlglot/ | head -20; grep -n \"def _parse_function\\|_parse_function_call\\|PARAMETERIZED\\|parameter\" sqlglot/dialects/clickhouse.py | head -30; grep -n \"def _parse_function_call\" -A 5 sqlglot/parser.py | head", "description": "Locate expression definitions and ClickHouse function parsing hooks"}
[tool_result] __init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
sqlglot/expressions/aggregate.py:133:class GroupConcat(Expression, AggFunc):
sqlglot/expressions/aggregate.py-134-    arg_types = {"this": True, "separator": False, "on_overflow": False}
sqlglot/expressions/aggregate
…[221 chars elided]…
gate.py-139-    is_var_len_args = True
sqlglot/expressions/aggregate.py-140-
sqlglot/expressions/aggregate.py-141-
sqlglot/expressions/aggregate.py-142-class GroupingId(Expression, AggFunc):
sqlglot/expressions/aggregate.py-143-    arg_types = {"expressions": False}
6754:    def _parse_function_call(
6755-        self,
6756-        functions: dict[str, t.Callable] | None = None,
6757-        anonymous: bool = False,
6758-        optional_parens: bool = True,
6759-        any_token: bool = False,
[tool_use Bash] {"command": "ls sqlglot/dialects/ | grep -i click; grep -n -i \"param\\|quantile\\|FUNCTION_PARSERS\\|_parse_function_call\\|LPAREN\" sqlglot/dialects/clickhouse.py | head -60; grep -rn \"PARAMETRIC\\|parametric\" sqlglot/parser.py sqlglot/parsers/ sqlglot/generator.py sqlglot/generators/ | head -20", "description": "Search ClickHouse dialect and parser for parametric aggregate support"}
[tool_result] clickhouse.py
[tool_use Bash] {"command": "wc -l sqlglot/dialects/clickhouse.py && grep -n \"class \\|def \" sqlglot/dialects/clickhouse.py | head -120", "description": "List classes and methods in ClickHouse dialect"}
[tool_result]      131 sqlglot/dialects/clickhouse.py
15:class ClickHouse(Dialect):
45:    def generate_values_aliases(self, expression: exp.Values) -> list[exp.Identifier]:
59:            structure_coldefs = [coldef.strip() for coldef in structure.name.split(",")]
61:                exp.to_identifier(coldef.split(" ")[0]) for coldef in structure_coldefs
71:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "cat sqlglot/dialects/clickhouse.py; ls sqlglot/parsers sqlglot/generators sqlglot/expressions; grep -rln -i \"clickhouse\" sqlglot/ | head -30", "description": "Read full ClickHouse dialect and list related files"}
[tool_result] from __future__ import annotations


from sqlglot import exp, tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.clickhouse import ClickHouseGenerator
from sqlglot.parsers.clickhouse import ClickHouseParser
from sqlglot.tokens import TokenType
from sqlglot.typing.clickhouse import EXPRESSION_METADATA


class ClickHouse(Dialect):
    INDEX_OFFSET = 1
    NORMALIZE_FUNCTIONS: bool | str = False
    NULL_ORDERING = "nulls_are_last"
    SU
…[4912 chars elided]…
ialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
sqlglot/parser.py
sqlglot/parsers/clickhouse.py
sqlglot/optimizer/resolver.py
sqlglot/dialects/__init__.py
sqlglot/optimizer/qualify_columns.py
sqlglot/dialects/clickhouse.py
sqlglot/generators/clickhouse.py
sqlglot/dialects/dialect.py
sqlglot/expressions/constraints.py
sqlglot/expressions/dml.py
[tool_use Bash] {"command": "cat sqlglot/parsers/clickhouse.py | head -400", "description": "Read ClickHouse parser"}
[tool_result] from __future__ import annotations

import typing as t

from collections import deque

from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    build_date_delta,
    build_formatted_time,
    build_json_extract_path,
    build_like,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import Token, TokenType
from builtins import type as Type

if t.TYPE_CHECKING:
    from sqlglot._typing import E
    from collections.abc import Mapping, Sequence, Collection


def _build_date
…[12186 chars elided]…
Parser.NO_PAREN_FUNCTIONS.items()
        if k != TokenType.CURRENT_TIMESTAMP
    }

    RANGE_PARSERS = {
        **parser.Parser.RANGE_PARSERS,
        TokenType.GLOBAL: lambda self, this: self._parse_global_in(this),
    }

    COLUMN_OPERATORS = {
        **{k: v for k, v in parser.Parser.COLUMN_OPERATORS.items() if k != TokenType.PLACEHOLDER},
        TokenType.DOTCARET: lambda self, this, field: self.expression(
            exp.NestedJSONSelect(this=this, expression=field)
        ),
    }
[tool_use Bash] {"command": "grep -n \"_parse_quantile\" -A 25 sqlglot/parsers/clickhouse.py | sed -n 1,200p | grep -v \"^--$\" | tail -40; grep -n \"Quantile\" -A 6 sqlglot/expressions/aggregate.py | head -30; grep -n \"def quantile_sql\\|Quantile\\|def _parse_quantile\" -A 12 sqlglot/generators/clickhouse.py | head -60", "description": "Read quantile parsing and generation logic"}
[tool_result] 378-
379-    NO_PAREN_FUNCTION_PARSERS = {
380-        k: v for k, v in parser.Parser.NO_PAREN_FUNCTION_PARSERS.items() if k != "ANY"
381-    }
382-
383-    NO_PAREN_FUNCTIONS = {
384-        k: v
385-        for k, v in parser.Parser.NO_PAREN_FUNCTIONS.items()
386-        if k != TokenType.CURRENT_TIMESTAMP
387-    }
388-
389-    RANGE_PARSERS = {
390-        **parser.Parser.RANGE_PARSERS,
391-        TokenType.GLOBAL: lambda self, this: self._parse_global_in(this),
732:    def _parse_quantile(
…[2305 chars elided]…
ession),
328-        exp.Rand: rename_func("randCanonical"),
329-        exp.StartsWith: rename_func("startsWith"),
330-        exp.Struct: rename_func("tuple"),
331-        exp.Trunc: rename_func("trunc"),
332-        exp.EndsWith: rename_func("endsWith"),
333-        exp.EuclideanDistance: rename_func("L2Distance"),
334-        exp.StrPosition: lambda self, e: strposition_sql(
335-            self,
336-            e,
337-            func_name="POSITION",
338-            supports_position=True,
[tool_use Bash] {"command": "sed -n 2390,2420p sqlglot/dialects/dialect.py; grep -n \"GroupConcat\" sqlglot/generators/*.py sqlglot/generator.py | head; grep -n \"def _parse_func_params\" -A 22 sqlglot/parser.py; grep -n \"def _parse_function_call\" -A 50 sqlglot/parser.py | grep -n \"FUNCTION_PARSERS\\|upper\\|parser\" ", "description": "Read groupconcat generator, GroupConcat handling, and func params parser"}
[tool_result] def length_or_char_length_sql(self: Generator, expression: exp.Length) -> str:
    length_func = "LENGTH" if expression.args.get("binary") else "CHAR_LENGTH"
    return self.func(length_func, expression.this)


def groupconcat_sql(
    self: Generator,
    expression: exp.GroupConcat,
    func_name: str = "LISTAGG",
    sep: str | None = ",",
    within_group: bool = True,
    on_overflow: bool = False,
) -> str:
    this = expression.this
    separator = self.sql(
        expression.args.get("s
…[1229 chars elided]…
r:
sqlglot/generators/spark.py:115:            exp.GroupConcat: _groupconcat_sql,
16:6769-        upper = self._curr.text.upper()
18:6771-        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
19:6772-        if optional_parens and parser and token_type not in self.INVALID_FUNC_NAME_TOKENS:
21:6774-            return self._parse_window(parser(self))
38:6791-        parser = self.FUNCTION_PARSERS.get(upper)
39:6792-        if parser and not anonymous:
40:6793-            result = parser(self)
[tool_use Bash] {"command": "grep -rn \"def _parse_func_params\" -A 20 sqlglot/parsers/base.py | head -30; ls <work>/env-sqlglot/bin/python && PY=<work>/env-sqlglot/bin/pyt
…[186 chars elided]…
 print(sqlglot.transpile(s, read='clickhouse', write='clickhouse'))\n    except Exception as e: print('ERR', e)\nprint(repr(sqlglot.parse_one('SELECT GROUP_CONCAT(x SEPARATOR \\',\\') FROM t', read='mysql')))\nprint(sqlglot.transpile('SELECT GROUP_CONCAT(x SEPARATOR \\',\\') FROM t', read='mysql', write='clickhouse'))\n\"", "description": "Locate func params parser and reproduce current behavior"}
[tool_result] <work>/env-sqlglot/bin/python
ERR Invalid expression / Unexpected token. Line 1, Col: 38.
  SELECT groupConcat(', ')(part_name) [4mAS[0m concatenated FROM system.parts
['SELECT groupConcat(part_name) FROM t']
Select(
  expressions=[
    GroupConcat(
      this=Column(
        this=Identifier(this=x, quoted=False)),
      separator=Literal(this=',', is_string=True))],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))))
["SELECT GROUP_CONCAT(x, ',') FROM t"]
[tool_use Bash] {"command": "grep -rn \"def _parse_func_params\" -A 22 sqlglot/ | head -30; sed -n 6760,6800p sqlglot/parser.py; grep -n \"quantile\\|groupConcat\\|groupconcat\" -i tests/dialects/test_clickhouse.py | head -20", "description": "Read func params parser, function call dispatch, existing tests"}
[tool_result] sqlglot/parsers/clickhouse.py:721:    def _parse_func_params(self, this: exp.Func | None = None) -> list[exp.Expr] | None:
sqlglot/parsers/clickhouse.py-722-        if self._match_pair(TokenType.R_PAREN, TokenType.L_PAREN):
sqlglot/parsers/clickhouse.py-723-            return self._parse_csv(self._parse_lambda)
sqlglot/parsers/clickhouse.py-724-
sqlglot/parsers/clickhouse.py-725-        if self._match(TokenType.L_PAREN):
sqlglot/parsers/clickhouse.py-726-            params = self._parse_csv(self
…[3545 chars elided]…
 0.4)(a)",
572:            read={"duckdb": "SELECT quantile(a, [0.5, 0.4])"},
573:            write={"clickhouse": "SELECT quantiles(0.5, 0.4)(a)"},
576:            "SELECT quantiles(0.5)(a)",
577:            read={"duckdb": "SELECT quantile(a, [0.5])"},
578:            write={"clickhouse": "SELECT quantiles(0.5)(a)"},
713:            "SELECT quantilesExactExclusive(0.25, 0.5, 0.75)(x) AS y FROM (SELECT number AS x FROM num)"
1374:                a AggregateFunction(quantiles(0.5, 0.9), UInt64),
[tool_use Bash] {"command": "grep -rn -i \"group_concat\\|groupconcat\" tests/ | grep -i \"clickhouse\" ; grep -rn -i \"group_concat\\|groupconcat\" tests/dialects/test_dialect.py | head -5; sed -n 1,30p sqlglot/generators/clickhouse.py | grep -n \"import\\|from\"; grep -n \"_quantile_sql\\|def _\\w*_sql\" sqlglot/generators/clickhouse.py | head; grep -n \"    def \\w*_sql\" sqlglot/generators/clickhouse.py | head -30; grep -n \"GroupConcat\\|def func\" -B2 -A2 sqlglot/generator.py | head -20", "description": "Check existing ClickHouse groupconcat tests and generator conventions"}
[tool_result] 1:from __future__ import annotations
3:import datetime
4:import typing as t
6:from sqlglot import exp, generator
7:from sqlglot.dialects.dialect import (
16:    remove_from_array_using_filter,
25:from sqlglot.generator import unsupported_args
26:from sqlglot.helper import is_int
27:from collections import defaultdict
32:def _unix_to_time_sql(self: ClickHouseGenerator, expression: exp.UnixToTime) -> str:
56:def _quantile_sql(self: ClickHouseGenerator, expression: exp.Quantile) -> str:
68:def _dat
…[2298 chars elided]…
35:    def not_sql(self, expression: exp.Not) -> str:
645:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
658:    def timestamptrunc_sql(self, expression: exp.TimestampTrunc) -> str:
4298-        return self.function_fallback_sql(expression)
4299-
4300:    def function_fallback_sql(self, expression: exp.Func) -> str:
4301-        args = []
4302-
--
4317-        return self.func(name, *args)
4318-
4319:    def func(
4320-        self,
4321-        name: str,
[assistant] Reproduced: `groupConcat(', ')(part_name)` fails, while `groupConcat(part_name)` parses as an anonymous function. The ClickHouse parser already handles `quantile(0.5)(a)` with `_parse_func_params`, so I'll follow that pattern.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        \"QUANTILE\": lambda self: self._parse_quantile(),\n        \"MEDIAN\": lambda self: self._parse_quantile(),", "new_string": "        \"QUANTILE\": lambda self: self._parse_quantile(),\n        \"MEDIAN\": lambda self: self._parse_quantile(),\n        \"GROUPCONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))\n\n", "new_string": "        return self.expression(exp.Quantile(this=this, quantile=exp.Literal.number(0.5)))\n\n   
…[59 chars elided]…
nymous:\n        args = self._parse_csv(self._parse_lambda)\n        params = self._parse_func_params()\n        if params:\n            return self.expression(exp.GroupConcat(this=seq_get(params, 0), separator=seq_get(args, 0)))\n        if len(args) == 1:\n            return self.expression(exp.GroupConcat(this=args[0]))\n        return exp.Anonymous(this=\"groupConcat\", expressions=args)\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/generators/clickhouse.py", "old_string": "    def in_sql(self, expression: exp.In) -> str:", "new_string": "    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:\n        separator = expression.args.get(\"separator\")\n        if separator:\n            return self.func(\"groupConcat\", separator) + f\"({self.sql(expression, 'this')})\"\n        return self.func(\"groupConcat\", expression.this)\n\n    def in_sql(self, expression: exp.In) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/generators/clickhouse.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = [\n \\\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\\\",\n \\\"SELECT groupConcat(part_name) FROM t\\\",\n \\\"SELECT groupConcat(', ', 10)(part_name) FROM t\\\",\n \\\"S
…[258 chars elided]…
lglot.transpile('SELECT GROUP_CONCAT(x SEPARATOR \\',\\') FROM t', read='mysql', write='clickhouse'))\nprint(sqlglot.transpile(\\\"SELECT groupConcat(', ')(part_name) AS c FROM t\\\", read='clickhouse', write='duckdb'))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_clickhouse.py 2>&1 | tail -5", "description": "Verify fix on repro and edge cases, run ClickHouse tests"}
[tool_result] ["SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts"]
['SELECT groupConcat(part_name) FROM t']
["SELECT groupConcat(', ')(part_name) FROM t"]
['SELECT groupConcat(x, 10) FROM t']
["SELECT groupConcat(', ')(a) OVER (PARTITION BY b) FROM t"]
["SELECT groupConcat(',')(x) FROM t"]
["SELECT LISTAGG(part_name, ', ') AS c FROM t"]
.............................                                                              [100%]
29 passed, 270 subtests passed in 0.26s
[assistant] The parametric form works and the existing ClickHouse tests pass. One problem: `groupConcat(', ', 10)(part_name)` silently drops the `10` (the max-size argument). I'll make that shape raise a parse error instead of producing wrong SQL. First I'll confirm `raise_error` exists in the base parser.
[tool_use Bash] {"command": "grep -n \"def raise_error\" -A 3 sqlglot/parser.py sqlglot/parsers/base.py | head; grep -n \"self.raise_error(\" sqlglot/parsers/clickhouse.py | head -3", "description": "Confirm raise_error signature in parser"}
[tool_result] sqlglot/parser.py:1949:    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
sqlglot/parser.py-1950-        token = token or self._curr or self._prev or Token.string("")
sqlglot/parser.py-1951-        formatted_sql, start_context, highlight, end_context = highlight_sql(
sqlglot/parser.py-1952-            sql=self.sql,
552:            self.raise_error("Expecting }")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py", "old_string": "        params = self._parse_func_params()\n        if params:\n            return self.expression(exp.GroupConcat(this=seq_get(params, 0), separator=seq_get(args, 0)))\n        if len(args) == 1:", "new_string": "        params = self._parse_func_params()\n        if params:\n            if len(args) != 1 or len(params) != 1:\n                self.raise_error(\"groupConcat(separator)(expr) takes one separator and one expression\")\n            return self.expression(exp.GroupConcat(this=params[0], separator=args[0]))\n        if len(args) == 1:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/sqlglot/parsers/clickhouse.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing `quantile` tests.
[tool_use Bash] {"command": "sed -n 96,106p tests/dialects/test_clickhouse.py; grep -n \"def test_\" tests/dialects/test_clickhouse.py | awk -F: '$1<100' ", "description": "View quantile test lines for placement"}
[tool_result]         self.validate_identity("SELECT * FROM foo GLOBAL ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo GLOBAL LEFT ANY JOIN bla")
        self.validate_identity("SELECT quantile(0.5)(a)")
        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT quantilesIf(0.5)(a, a > 1) AS x FROM t")
        self.validate_identity("SELECT quantileState(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT deltaSumMerge(a) AS x FROM t")
        self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
        self.validate_identity("SELECT quantileTiming(0.5)(RANGE(100))")
        self.validate_identity("SELECT histogram(5)(a)")
        self.validate_identity("SELECT groupUniqArray(2)(a)")
15:    def test_clickhouse(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py", "old_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n", "new_string": "        self.validate_identity(\"SELECT groupUniqArray(2)(a)\")\n        self.validate_identity(\"SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts\")\n        self.validate_identity(\"SELECT groupConcat(part_name) FROM t\")\n        self.validate_identity(\"SELECT groupConcat(x, 10) FROM t\")\n        self.validate_all(\n            \"SELECT groupConcat(',')(x) FROM t\",\n            read={\"mysql\": \"SELECT GROUP_CONCAT(x SEPARATOR ',') FROM t\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-154230-clickhouse-dialect-the-parametri/base-1/tests/dialects/test_clickhouse.py has been updated successfully.
[assistant] Next I'll run the formatter and the full test suite with the project's command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff format sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py && $PY -m ruff check sqlglot/parsers/clickhouse.py sqlglot/generators/clickhouse.py tests/dialects/test_clickhouse.py) 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git status --short", "description": "Format, lint, and run full test suite"}
[tool_result] 2 files reformatted, 1 file left unchanged
All checks passed!
.......... [ 65%]
................................................................................................. [ 74%]
............................................................................................................................ [ 85%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1081 passed, 17837 subtests passed in 61.49s (0:01:01)
 M sqlglot/generators/clickhouse.py
 M sqlglot/parsers/clickhouse.py
 M tests/dialects/test_clickhouse.py
[This command modified 2 files you've previously read: sqlglot/parsers/clickhouse.py, tests/dialects/test_clickhouse.py. Call Read before editing.]
[assistant] The formatter touched two files I'd edited, so I'll check the final diff to confirm it contains only my intended change.
[tool_use Bash] {"command": "git diff", "description": "Show full diff of changes"}
[tool_result] diff --git a/sqlglot/generators/clickhouse.py b/sqlglot/generators/clickhouse.py
index eef1a97ad..9f0fdf868 100644
--- a/sqlglot/generators/clickhouse.py
+++ b/sqlglot/generators/clickhouse.py
@@ -624,6 +624,12 @@ class ClickHouseGenerator(generator.Generator):
 
         return is_sql
 
+    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
+        separator = expression.args.get("separator")
+        if separator:
+            return self.func("groupConcat", separator) + f"({self
…[2575 chars elided]…
part_name) FROM t")
+        self.validate_identity("SELECT groupConcat(x, 10) FROM t")
+        self.validate_all(
+            "SELECT groupConcat(',')(x) FROM t",
+            read={"mysql": "SELECT GROUP_CONCAT(x SEPARATOR ',') FROM t"},
+        )
         self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
         self.validate_identity("levenshteinDistance(col1, col2)", "editDistance(col1, col2)")
         self.validate_identity("jaroWinklerSimilarity('hello', 'world')")
[assistant] The diff is clean. Last, I'll confirm the unsupported `max_size` shape now raises instead of dropping the argument.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ntry: print(sqlglot.transpile(\\\"SELECT groupConcat(', ', 10)(part_name) FROM t\\\", read='clickhouse', write='clickhouse'))\nexcept sqlglot.ParseError as e: print('ParseError:', str(e).splitlines()[0])\n\"", "description": "Confirm unsupported max-size form raises a parse error"}
[tool_result] ParseError: groupConcat(separator)(expr) takes one separator and one expression. Line 1, Col: 39.
[assistant] The ClickHouse `groupConcat` parametric form now parses and round-trips. The Superset query `SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts` returns the same SQL, and the full suite passes (1081 tests, run with the project's pytest command).

**What changed**
- **Parser** (`sqlglot/parsers/clickhouse.py`): `groupConcat` now has a function parser. The first parenthesised argument is the separator and the second is the column, so it becomes `exp.GroupConcat(this=column, separator=sep)`. This mirrors how `quantile(0.5)(a)` is already parsed.
- **Generator** (`sqlglot/genera
…[533 chars elided]…
 an anonymous function, so their output is unchanged.
- **Parametric calls with a max-size argument**, such as `groupConcat(', ', 10)(x)`, now raise a `ParseError`. `GroupConcat` has no slot for that second argument, and silently dropping it would produce wrong SQL. This shape errored before too, so it is not a regression. Supporting it would need a new argument on the expression.
- **Other dialects' output** for `GroupConcat` is unaffected. Only ClickHouse generation changed. Going from ClickHouse to another dialect works as before (for example, to DuckDB it gives `LISTAGG(part_name, ', ')`).
