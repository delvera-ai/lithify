# trajectory base-1

final message:
`APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 tests), and ruff check and format are clean. Nothing is committed.

**What changed**

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` also accepts a `PERCENTILE_DISC ... WITHIN GROUP` after `APPROXIMATE` and builds an `exp.ApproxQuantile`. It reuses the existing `APPROXIMATE` hook, so `APPROXIMATE COUNT(DISTINCT ...)` is unchanged.
- **Generator** (`sqlglot/generators/redshift.py`): a new `approxquantile_sql` method emits `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)`. It is auto-discovered, so `APPROX_PERCENTILE` (Snowflake), `PERCENTILE_APPROX` (Spark) and `APPROX_QUANTILE` (DuckDB) now transpile into Redshift. The `accuracy`, `weight` and `error_tolerance` arguments are marked unsupported, since Redshift has no equivalent.
- **Tests** (`tests/dialects/test_redshift.py`): an identity round-trip plus cross-dialect `validate_all` cases next to the existing `APPROXIMATE COUNT` test.

**Choices I made**

- `ORDER BY x DESC` is still a parse error. `PERCENTILE_DISC` with `DESC` is a different percentile, so mapping it to the ascending form would silently change results. Say if you want it accepted anyway.
- Multi-column `ORDER BY` is also still a parse error, since the approximate form takes one ordering expression.

## events
[tool_use Bash] {"command": "grep -rn -i \"approximate\" sqlglot/dialects/redshift.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/dialect.py | head -50; grep -rn -i \"approximate\" tests/dialects/test_redshift.py | head", "description": "Search for APPROXIMATE handling across sqlglot"}
[tool_use Bash] {"command": "grep -rn \"PERCENTILE_DISC\\|PercentileDisc\\|PERCENTILE_CONT\\|PercentileCont\\|ApproxQuantile\\|ApproxDistinct\" sqlglot/ | head -60", "description": "Find percentile and approx quantile expression definitions"}
[tool_result] sqlglot/transforms.py:568:        return expression.replace(exp.ApproxQuantile(this=input_value, quantile=quantile))
sqlglot/parsers/redshift.py:99:    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:
sqlglot/parsers/redshift.py:104:            return self.expression(exp.ApproxDistinct(this=seq_get(func.this.expressions, 0)))
sqlglot/parsers/singlestore.py:120:        "APPROX_PERCENTILE": lambda args, dialect: exp.ApproxQuantile(
sqlglot/parsers/spark2.py:82:        "APPROX_PERCE
…[4712 chars elided]…
add_within_group_for_percentiles]),
sqlglot/generators/snowflake.py:540:        exp.PercentileDisc: transforms.preprocess([transforms.add_within_group_for_percentiles]),
sqlglot/generators/snowflake.py:931:    def approxquantile_sql(self, expression: exp.ApproxQuantile) -> str:
sqlglot/generators/presto.py:261:        exp.ApproxQuantile: lambda self, e: self.func(
sqlglot/generators/exasol.py:363:        exp.ApproxDistinct: unsupported_args("accuracy")(rename_func("APPROXIMATE_COUNT_DISTINCT")),
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
[tool_use Bash] {"command": "cat sqlglot/parsers/redshift.py | sed -n 1,140p; echo ----; sed -n 60,90p sqlglot/generators/redshift.py; echo ----; sed -n 200,240p sqlglot/expressions/aggregate.py; sed -n 1970,1990p sqlglot/expressions/core.py", "description": "Read Redshift parser, generator, and aggregate expression definitions"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.postgres import PostgresParser
from sqlglot.parser import build_convert_timezone
from sqlglot.tokens import TokenType
from sqlglot.dialects.dialect import map_date_part
from builtins import type as Type

if t.TYPE_CHECKING:
    from sqlglot._typing import E
    from collections.abc import Collection


def _build_date_delta(expr_type: Type[E]) -> t.Callable[[list
…[6626 chars elided]…
this": True, "expressions": False}
    is_var_len_args = True


class ApproxDistinct(Expression, AggFunc):
    arg_types = {"this": True, "accuracy": False}
    _sql_names = ["APPROX_DISTINCT", "APPROX_COUNT_DISTINCT"]


class Slice(Expression):
    arg_types = {"this": False, "expression": False, "step": False}


@trait
class TimeUnit(Expr):
    """Automatically converts unit arg into a var."""

    UNABBREVIATED_UNIT_NAME: t.ClassVar[dict[str, str]] = {
        "D": "DAY",
        "H": "HOUR",
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', 'SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try:\n        e=sqlglot.parse_one(s, read='redshift'); print(repr(e.selects[0])); print(e.sql('red
…[237 chars elided]…
\n    e=sqlglot.parse_one(s, read='snowflake'); print(e.sql('postgres'))\n\"; grep -n \"_parse_quantile_function\\|def add_within_group_for_percentiles\" -A12 sqlglot/parser.py sqlglot/transforms.py | head -80; grep -rn \"PercentileDisc\\|APPROXIMATE\" tests/dialects/test_redshift.py tests/dialects/test_postgres.py | head", "description": "Reproduce the parse error and inspect percentile helpers"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/transforms.py:544:def add_within_group_for_percentiles(expression: exp.Expr) -> exp.Expr:
sqlglot/transforms.py-545-    """Transforms percentiles by adding a WITHIN GROUP clause to them."""
sqlglot/transforms.py-546-    if (
sqlglot/transforms.py-547-        isinstance(expression, exp.PERCENTILES)
sqlglot/transforms.py-548-        and not isinstance(expression.parent, 
…[309 chars elided]…
der(expressions=[exp.Ordered(this=column)])
sqlglot/transforms.py-554-        expression = exp.WithinGroup(this=expression, expression=order)
sqlglot/transforms.py-555-
sqlglot/transforms.py-556-    return expression
tests/dialects/test_redshift.py:61:            "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:66:                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
tests/dialects/test_redshift.py:364:        self.validate_identity("SELECT APPROXIMATE AS y")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', 'SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t']:\n    try:\n        e=sqlglot.parse_one(s, read='redshift'); print(repr(e.selects[0])); print(e.sql('redshift'))\n    except Excepti
…[73 chars elided]…
X_PERCENTILE(x, 0.5) FROM t'\ne=sqlglot.parse_one(s, read='snowflake'); print(repr(e.selects[0]));print(e.sql('redshift'))\nprint(e.sql('postgres'))\n\"; grep -n \"PERCENTILE\\|_parse_quantile_function\" -B2 -A10 sqlglot/parser.py | sed -n 1,80p; grep -rn \"def _parse_quantile_function\" -A15 sqlglot/parsers/ | head -30", "description": "Reproduce parse error and inspect quantile parsing helpers"}
[tool_result] ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
WithinGroup(
  this=PercentileDisc(
    this=Literal(this=0.5, is_string=False)),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=x, quoted=False),
          join_mark=False),
        nulls_first=False)]),
  join_mark=False)
SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
App
…[667 chars elided]…
ch(TokenType.ALL)
sqlglot/parsers/hive.py-186-            first_arg = self._parse_lambda()
sqlglot/parsers/hive.py-187-
sqlglot/parsers/hive.py-188-        args = [first_arg]
sqlglot/parsers/hive.py-189-        if self._match(TokenType.COMMA):
sqlglot/parsers/hive.py-190-            args.extend(self._parse_function_args())
sqlglot/parsers/hive.py-191-
sqlglot/parsers/hive.py-192-        return func.from_arg_list(args)
sqlglot/parsers/hive.py-193-
sqlglot/parsers/hive.py-194-    def _parse_types(
[tool_use Bash] {"command": "grep -rn \"WithinGroup\" sqlglot/parser.py sqlglot/parsers/*.py | head; grep -n \"def _parse_window\\b\" -A6 sqlglot/parser.py; grep -n \"ApproxQuantile\\|approxquantile\" -A8 sqlglot/generators/snowflake.py | sed -n 1,20p", "description": "Locate WITHIN GROUP parsing and approx quantile generators"}
[tool_result] sqlglot/parser.py:7739:        # This is done "manually", instead of letting _parse_window parse it into an exp.WithinGroup node, so that
sqlglot/parser.py:8131:            this = self.expression(exp.WithinGroup(this=this, expression=order))
8123:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
8124-        func = this
8125-        comments = func.comments if isinstance(func, exp.Expr) else None
8126-
8127-        # T-SQL allows the OVER (...) syntax af
…[329 chars elided]…
ion.this, expression.args.get("quantile"))
933-
934-    def alterset_sql(self, expression: exp.AlterSet) -> str:
935-        exprs = self.expressions(expression, flat=True)
936-        exprs = f" {exprs}" if exprs else ""
937-        file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
938-        file_format = f" STAGE_FILE_FORMAT = ({file_format})" if file_format else ""
939-        copy_options = self.expressions(expression, key="copy_options", flat=True, sep=" ")
[tool_use Bash] {"command": "sed -n 8123,8145p sqlglot/parser.py", "description": "Read the _parse_window WITHIN GROUP handling"}
[tool_result]     def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
        func = this
        comments = func.comments if isinstance(func, exp.Expr) else None

        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
        # https://learn.microsoft.com/en-us/sql/t-sql/functions/percentile-disc-transact-sql?view=sql-server-ver16
        if self._match_text_seq("WITHIN", "GROUP"):
            order = self._parse_wrapped(self._parse_order)
            this = self
…[202 chars elided]…
                exp.Filter(this=this, expression=self._parse_where(skip_where_token=True))
            )
            self._match_r_paren()

        # SQL spec defines an optional [ { IGNORE | RESPECT } NULLS ] OVER
        # Some dialects choose to implement and some do not.
        # https://dev.mysql.com/doc/refman/8.0/en/window-function-descriptions.html

        # There is some code above in _parse_lambda that handles
        #   SELECT FIRST_VALUE(TABLE.COLUMN IGNORE|RESPECT NULLS) OVER ...
[tool_use Bash] {"command": "grep -rn \"@unsupported_args\" -A2 sqlglot/generators/*.py | head -12; grep -n \"^from\\|^import\" sqlglot/generators/redshift.py; grep -n \"def \\w*_sql\" sqlglot/generators/redshift.py | head -5", "description": "Check unsupported_args decorator usage and redshift generator imports"}
[tool_result] sqlglot/generators/bigquery.py:194:@unsupported_args("ins_cost", "del_cost", "sub_cost")
sqlglot/generators/bigquery.py-195-def _levenshtein_sql(self: BigQueryGenerator, expression: exp.Levenshtein) -> str:
sqlglot/generators/bigquery.py-196-    max_dist = expression.args.get("max_dist")
sqlglot/generators/duckdb.py:548:@unsupported_args(("expression", "DuckDB's ARRAY_SORT does not support a comparator."))
sqlglot/generators/duckdb.py-549-def _array_sort_sql(self: DuckDBGenerator, expression: ex
…[499 chars elided]…
ts.dialect import (
15:from sqlglot.generator import Generator
16:from sqlglot.generators.postgres import PostgresGenerator
17:from sqlglot.helper import seq_get
273:    def unnest_sql(self, expression: exp.Unnest) -> str:
290:    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:
297:    def datatype_sql(self, expression: exp.DataType) -> str:
313:    def alterset_sql(self, expression: exp.AlterSet) -> str:
323:    def array_sql(self, expression: exp.Array) -> str:
[assistant] Parser first: extend `_parse_approximate_count` to accept `PERCENTILE_DISC ... WITHIN GROUP`, retreating on anything else.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "    def _parse_approximate_count(self) -> exp.ApproxDistinct | None:\n        index = self._index - 1\n        func = self._parse_function()\n\n        if isinstance(func, exp.Count) and isinstance(func.this, 
…[666 chars elided]…
exp.WithinGroup):\n                ordered = seq_get(within_group.expression.expressions, 0)\n                if len(within_group.expression.expressions) == 1 and not ordered.args.get(\"desc\"):\n                    return self.expression(\n                        exp.ApproxQuantile(this=ordered.this, quantile=func.this)\n                    )\n\n        self._retreat(index)\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[assistant] Now the generator, using an auto-discovered `approxquantile_sql` method so other dialects' `APPROX_PERCENTILE` transpiles into Redshift's form.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/generators/redshift.py; sed -n 270,300p sqlglot/generators/redshift.py", "description": "View redshift generator imports and method area"}
[tool_result] from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    array_concat_sql,
    concat_to_dpipe_sql,
    concat_ws_to_dpipe_sql,
    date_delta_sql,
    generatedasidentitycolumnconstraint_sql,
    json_extract_segments,
    no_tablesample_sql,
    rename_func,
)
from sqlglot.generator import Generator
from sqlglot.generators.postgres import PostgresGenerator
from sqlglot.helper import seq_get


class RedshiftGenerator(PostgresGenerator):
…[802 chars elided]…
ON):
            # Redshift doesn't support a JSON type, so casting to it is treated as a noop
            return self.sql(expression, "this")

        return super().cast_sql(expression, safe_prefix=safe_prefix)

    def datatype_sql(self, expression: exp.DataType) -> str:
        """
        Redshift converts the `TEXT` data type to `VARCHAR(255)` by default when people more generally mean
        VARCHAR of max length which is `VARCHAR(max)` in Redshift. Therefore if we get a `TEXT` data type
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:\n        if expression.is_type(exp.DType.JSON):", "new_string": "    @unsupported_args(\"accuracy\", \"weight\", \"error_
…[96 chars elided]…
within_group = exp.WithinGroup(\n            this=exp.PercentileDisc(this=expression.args.get(\"quantile\")),\n            expression=exp.Order(expressions=[exp.Ordered(this=expression.this)]),\n        )\n        return f\"APPROXIMATE {self.sql(within_group)}\"\n\n    def cast_sql(self, expression: exp.Cast, safe_prefix: str | None = None) -> str:\n        if expression.is_type(exp.DType.JSON):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/^    rename_func,\\n)/X/' sqlglot/generators/redshift.py && python3 - <<'EOF'\nimport re\np='sqlglot/generators/redshift.py'\ns=open(p).read()\ns=s.replace(\"    rename_func,\\n)\\nfrom sqlglot.generator import Generator\",\"    rename_func,\\n    unsupported_args,\\n)\\nfrom sqlglot.generator import Generator\",1)\nopen(p,'w').write(s)\nEOF\ngrep -n \"def unsupported_args\"
…[1155 chars elided]…
qlglot.transpile('SELECT PERCENTILE_APPROX(x, 0.5) FROM t', read='spark', write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_QUANTILE(x, 0.5) FROM t', read='duckdb', write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5, 100) FROM t', read='snowflake', write='redshift')[0])\n\"\n", "description": "Wire unsupported_args import and exercise parse/generate cases"}
[tool_result ERROR] Exit code 1
sed: 1: "sqlglot/generators/reds ...": unterminated substitute pattern
sqlglot/generator.py:30:def unsupported_args(
Traceback (most recent call last):
  File "<string>", line 8, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/__init__.py", line 155, in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/l
…[1685 chars elided]…
ify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", line 20, in <module>
    class RedshiftGenerator(PostgresGenerator):
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", line 290, in RedshiftGenerator
    @unsupported_args("accuracy", "weight", "error_tolerance")
     ^^^^^^^^^^^^^^^^
NameError: name 'unsupported_args' is not defined
[assistant] The import went to the wrong module (`unsupported_args` lives in `sqlglot/generator.py`). Fixing that and re-running the checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py", "old_string": "from sqlglot.generator import Generator\n", "new_string": "from sqlglot.generator import Generator, unsupported_args\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/generators/redshift.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t',\n          'SELECT APPROXIMATE PERCENTILE_DISC(0.9) WITHIN GROUP (ORDER BY x DESC) FROM t',\n          'SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t',\n          'SELECT APPROXIMAT
…[568 chars elided]…
rint(sqlglot.transpile('SELECT APPROX_QUANTILE(x, 0.5) FROM t', read='duckdb', write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5, 100) FROM t', read='snowflake', write='redshift')[0])\nprint(sqlglot.transpile('SELECT APPROX_PERCENTILE(x, 0.5) FROM t', read='snowflake', write='snowflake')[0])\n\"", "description": "Exercise parse and generate cases after fixing import"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 9, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/dialects/dialect.py", line 1119, in parse
    r
…[1147 chars elided]…
ken. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
ERR Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.5) WITHIN GROUP (ORDER BY x) FROM t
ERR Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.9) WITHIN GROUP (ORDER BY x DESC) FROM t
SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE COUNT(DISTINCT y) FROM t
[assistant] Still failing, so `_parse_function` isn't returning a `PercentileDisc` here. Checking what it does return.
[tool_use Bash] {"command": "grep -rn \"PERCENTILE_DISC\\|PercentileDisc\" sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/parsers/redshift.py sqlglot/parsers/base*.py 2>/dev/null; grep -n \"def _parse_function\\b\" -A3 sqlglot/parser.py | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read='postgres'); print(repr(e.selects[0])[:300])\ne=sqlglot.parse_one('SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read='redshift'); print(type(e.selects[0]).__name__, type(e.selects[0].this).__name__)\n\"", "description": "Check how PERCENTILE_DISC is parsed in general"}
[tool_result] sqlglot/parsers/redshift.py:106:        if isinstance(func, exp.PercentileDisc):
6758:    def _parse_function(
6759-        self,
6760-        functions: dict[str, t.Callable] | None = None,
6761-        anonymous: bool = False,
WithinGroup(
  this=PercentileDisc(
    this=Literal(this=0.5, is_string=False)),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=x, quoted=False)),
        nulls_first=False)]))
WithinGroup PercentileDisc
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parsers import redshift as r\norig=r.RedshiftParser._parse_approximate_count\ndef dbg(self):\n    i=self._index\n    f=self._parse_function()\n    print('func', type(f).__name__, 'curr', self._curr.text if self._curr else None)\n    self._retreat(i)\n    return orig(self)\nr.RedshiftParser._parse_approximate_count=dbg\ntry: sqlglot.parse_one('SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t', read='redshift')\nexcept Exception as e: print('ERR')\n\" 2>&1 | head; grep -n \"NO_PAREN_FUNCTION_PARSERS\" -B3 -A12 sqlglot/parser.py | sed -n 1,60p", "description": "Trace what _parse_function returns for the approximate branch"}
[tool_result] func WithinGroup curr FROM
ERR
1464-        "TRUNCATE",
1465-    }
1466-
1467:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
1468-        "ANY": lambda self: self.expression(exp.Any(this=self._parse_bitwise())),
1469-        "CASE": lambda self: self._parse_case(),
1470-        "CONNECT_BY_ROOT": lambda self: self.expression(
1471-            exp.ConnectByRoot(this=self._parse_column())
1472-        ),
1473-        "IF": lambda self: self._parse_if(),
1474-    }
1475-
1476-    INVALID_FUNC_NAME_T
…[1420 chars elided]…
RATORS or curr_tt in self.COLUMN_POSTFIX_TOKENS:
6474-                    self._retreat(index)
6475-                    return None
6476-            elif curr_tt not in self.IDENTIFIER_TOKENS:
6477-                self._retreat(index)
--
6805-        this: str | exp.Expr = self._curr.text
6806-        upper = self._curr.text.upper()
6807-
6808:        parser = self.NO_PAREN_FUNCTION_PARSERS.get(upper)
6809-        if optional_parens and parser and token_type not in self.INVALID_FUNC_NAME_TOKENS:
[assistant] `_parse_function` already applies the window step, so it returns the `WithinGroup` itself. Adjusting the parser to match on that shape instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py", "old_string": "        if isinstance(func, exp.PercentileDisc):\n            within_group = self._parse_window(func)\n            if isinstance(within_group, exp.WithinGroup):\n                ordered = seq_get(within_group.
…[351 chars elided]…
func, exp.WithinGroup) and isinstance(func.this, exp.PercentileDisc):\n            ordered = seq_get(func.expression.expressions, 0)\n            if len(func.expression.expressions) == 1 and not ordered.args.get(\"desc\"):\n                return self.expression(\n                    exp.ApproxQuantile(this=ordered.this, quantile=func.this.this)\n                )\n\n        self._retreat(index)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/sqlglot/parsers/redshift.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t',\n          'SELECT APPROXIMATE PERCENTILE_DISC(0.9) WITHIN GROUP (ORDER BY x DESC) FROM t',\n          'SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t',\n   
…[410 chars elided]…
RCENTILE(x, 0.5) FROM t','snowflake'),('SELECT PERCENTILE_APPROX(x, 0.5) FROM t','spark'),('SELECT APPROX_QUANTILE(x, 0.5) FROM t','duckdb'),('SELECT APPROX_PERCENTILE(x, 0.5, 100) FROM t','snowflake'),('SELECT APPROX_PERCENTILE(x, 0.5) FROM t','snowflake')]:\n    print(sqlglot.transpile(s, read=d, write='redshift')[0])\n\"", "description": "Re-run parse and transpile cases with corrected parser"}
[tool_result] Argument 'accuracy' is not supported for expression 'ApproxQuantile' when targeting Redshift.
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
ERR Invalid expression / Unexpected token. Line 1, Col: 35.
  SELECT APPROXIMATE PERCENTILE_DISC[4m([0m0.9) WITHIN GROUP (ORDER BY x DESC) FROM t
SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE COUNT(DISTINCT y) FROM t
ApproxQuantile(
  this=Column(
    this=Identifier(this=x, quoted=False),
    jo
…[94 chars elided]…
XIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t | SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t
[assistant] Parse and round-trip work, and the transpile cases all land in Redshift's form. `DESC` still raises a parse error, which is deliberate (see the summary). Next I'll add regression tests next to the existing `APPROXIMATE COUNT` test.
[tool_use Bash] {"command": "sed -n 55,72p tests/dialects/test_redshift.py", "description": "View existing APPROXIMATE COUNT test"}
[tool_result]                 "spark, version=4.0.0": "LISTAGG(sellerid, ', ')",
                "spark": "LISTAGG(sellerid, ', ')",
                "databricks": "LISTAGG(sellerid, ', ')",
            },
        )
        self.validate_all(
            "SELECT APPROXIMATE COUNT(DISTINCT y)",
            read={
                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
            },
            write={
                "redshift": "SELECT APPROXIMATE COUNT(DISTINCT y)",
                "spark": "SELECT APPROX_COUNT_DISTINCT(y)",
            },
        )
        self.validate_all(
            "x ~* 'pat'",
            write={
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py", "old_string": "                \"spark\": \"SELECT APPROX_COUNT_DISTINCT(y)\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\",", "new_string": "                \"spark\": \"SELECT APPR
…[454 chars elided]…
(x, 0.5) FROM t\",\n                \"spark\": \"SELECT PERCENTILE_APPROX(x, 0.5) FROM t\",\n            },\n            write={\n                \"redshift\": \"SELECT APPROXIMATE PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY x) FROM t\",\n                \"snowflake\": \"SELECT APPROX_PERCENTILE(x, 0.5) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"x ~* 'pat'\","}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174731-redshift-dialect-approximate-per/base-1/tests/dialects/test_redshift.py has been updated successfully.
[assistant] Running the Redshift tests first, then the full suite with the project's configured pytest command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_redshift.py 2>&1 | tail -15", "description": "Run Redshift dialect tests"}
[tool_result] .................                     [100%]
17 passed, 179 subtests passed in 0.33s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -m ruff check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/redshift.py sqlglot/generators/redshift.py tests/dialects/test_redshift.py 2>&1 | tail -3", "description": "Run full test suite and lint/format checks"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
........................................................................ [ 32%]
..................................................................... [ 38%]
......................................
…[307 chars elided]…
.................................................................................. [ 74%]
............................................. [ 78%]
................................................................................................................................................................................................... [ 95%]
..............................................            [100%]
1103 passed, 17894 subtests passed in 50.90s
All checks passed!
3 files already formatted
[assistant] Full suite passes (1103 tests), and ruff check and format are clean. A quick look at the final diff before reporting:
[tool_use Bash] {"command": "git status --short && git diff -- sqlglot/", "description": "Show working tree status and source diff"}
[tool_result]  M sqlglot/generators/redshift.py
 M sqlglot/parsers/redshift.py
 M tests/dialects/test_redshift.py
diff --git a/sqlglot/generators/redshift.py b/sqlglot/generators/redshift.py
index bfe0d74f4..dbbeaaa23 100644
--- a/sqlglot/generators/redshift.py
+++ b/sqlglot/generators/redshift.py
@@ -12,7 +12,7 @@ from sqlglot.dialects.dialect import (
     no_tablesample_sql,
     rename_func,
 )
-from sqlglot.generator import Generator
+from sqlglot.generator import Generator, unsupported_args
 from sqlglo
…[1628 chars elided]…
p.ApproxDistinct(this=seq_get(func.this.expressions, 0)))
+
+        if isinstance(func, exp.WithinGroup) and isinstance(func.this, exp.PercentileDisc):
+            ordered = seq_get(func.expression.expressions, 0)
+            if len(func.expression.expressions) == 1 and not ordered.args.get("desc"):
+                return self.expression(
+                    exp.ApproxQuantile(this=ordered.this, quantile=func.this.this)
+                )
+
         self._retreat(index)
         return None
[assistant] `APPROXIMATE PERCENTILE_DISC(p) WITHIN GROUP (ORDER BY x)` now parses in the Redshift dialect, round-trips, and transpiles. The full suite passes (1103 tests), and ruff check and format are clean. Nothing is committed.

**What changed**

- **Parser** (`sqlglot/parsers/redshift.py`): `_parse_approximate_count` also accepts a `PERCENTILE_DISC ... WITHIN GROUP` after `APPROXIMATE` and builds an `exp.ApproxQuantile`. It reuses the existing `APPROXIMATE` hook, so `APPROXIMATE COUNT(DISTINCT ...)` is unchanged.
- **Generator** (`sqlglot/generators/redshift.py`): a new `approxquantile_sql` method emi
…[221 chars elided]…
cy`, `weight` and `error_tolerance` arguments are marked unsupported, since Redshift has no equivalent.
- **Tests** (`tests/dialects/test_redshift.py`): an identity round-trip plus cross-dialect `validate_all` cases next to the existing `APPROXIMATE COUNT` test.

**Choices I made**

- `ORDER BY x DESC` is still a parse error. `PERCENTILE_DISC` with `DESC` is a different percentile, so mapping it to the ascending form would silently change results. Say if you want it accepted anyway.
- Multi-column `ORDER BY` is also still a parse error, since the approximate form takes one ordering expression.
