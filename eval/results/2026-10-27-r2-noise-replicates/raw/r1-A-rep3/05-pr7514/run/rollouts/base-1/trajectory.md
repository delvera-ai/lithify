# trajectory base-1

final message:
Doris and StarRocks now parse the two-argument `DATE_ADD` / `DATE_SUB` form, but I did not add the two-argument output. The existing test suite expects the `INTERVAL` form, so I couldn't add it without changing those expectations.

The example from the report now parses and round-trips as:

```
SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
```

**What changed**
- `sqlglot/dialects/dialect.py`: new `build_date_delta_with_interval_or_days`. It builds a `DateAdd`/`DateSub` with a DAY unit when the second argument is not an `INTERVAL`, and otherwise falls through to the existing interval builder.
- `sqlglot/parsers/doris.py` and `sqlglot/parsers/starrocks.py`: `DATE_ADD` and `DATE_SUB` use that builder. MySQL is unchanged.
- `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`: a new `test_date_add_sub_days` for each dialect covering the two-argument parse.

**Why generation isn't changed**
I first made Doris and StarRocks emit `DATE_ADD(x, 1)` for DAY-unit `DateAdd`/`DateSub`. That broke four existing subtests in `tests/dialects/test_dialect.py::test_time` (around lines 1050–1085). Those tests expect `DATE_ADD(x, 1)` to write as `DATE_ADD(x, INTERVAL 1 DAY)` for both dialects. The harness says not to edit tests to pass, so I reverted that change.

Decision for you: should Doris and StarRocks write the two-argument form? If yes, I'll update those four expectations in `test_dialect.py` and make the generator change. Doris already emits the two-argument form for `TS_OR_DS_ADD`, so this would make the two paths consistent. Both `INTERVAL` and two-argument forms are valid Doris and StarRocks SQL, so the current output is correct, just not the form you asked for.

**Verification**
- Full suite: `1086 passed, 17850 subtests passed`.
- `ruff check` and `ruff format --check`: clean.
- Not committed.

## events
[tool_use Bash] {"command": "grep -n -i \"date_add\\|DateAdd\\|date_sub\\|DateSub\\|DATE_ADD\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/generator.py | head -80; grep -n \"def _build_date_add\\|def build_date_delta\\|def _build_date_delta\" -A30 sqlglot/dialects/dialect.py | head -80", "description": "Locate date_add handling across dialects"}
[tool_result] sqlglot/generator.py:4864:    def dateadd_sql(self, expression: exp.DateAdd) -> str:
sqlglot/generator.py:4868:            "DATE_ADD",
sqlglot/generator.py:5811:            exp.DateAdd(
1577:def build_date_delta(
1578-    exp_class: Type[E],
1579-    unit_mapping: dict[str, str] | None = None,
1580-    default_unit: str | None = "DAY",
1581-    supports_timezone: bool = False,
1582-) -> t.Callable[[BuilderArgs], E]:
1583-    def _builder(args: BuilderArgs) -> E:
1584-        unit_based = len(arg
…[1446 chars elided]…
       return exp.DateTrunc(unit=unit, this=this)
1622-    return exp.TimestampTrunc(this=this, unit=unit)
1623-
1624-
1625-def date_add_interval_sql(data_type: str, kind: str) -> t.Callable[[Generator, exp.Expr], str]:
1626-    def func(self: Generator, expression: exp.Expr) -> str:
1627-        this = self.sql(expression, "this")
1628-        interval = exp.Interval(this=expression.expression, unit=unit_to_var(expression))
1629-        return f"{data_type}_{kind}({this}, {self.sql(interval)})"
[tool_use Bash] {"command": "cat sqlglot/dialects/doris.py; echo ----; cat sqlglot/dialects/starrocks.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\" sqlglot/dialects/mysql.py sqlglot/parser.py sqlglot/dialects/dialect.py | head -40; sed -n 4855,4885p sqlglot/generator.py", "description": "Read doris and starrocks dialect files and related code"}
[tool_result] from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.doris import DorisGenerator
from sqlglot.parsers.doris import DorisParser


class Doris(MySQL):
    DATE_FORMAT = "'yyyy-MM-dd'"
    DATEINT_FORMAT = "'yyyyMMdd'"
    TIME_FORMAT = "'yyyy-MM-dd HH:mm:ss'"

    Parser = DorisParser

    Generator = DorisGenerator
----
from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.starrocks import StarRocksGene
…[1969 chars elided]…
pression)
            filtered_not_empty = exp.ArraySize(this=filtered).neq(0)
            original_is_empty = exp.ArraySize(this=expression.this).eq(0)
            return self.sql(exp.paren(original_is_empty.or_(filtered_not_empty)))

        import sqlglot.dialects.dialect

        # SQLGlot's executor supports ARRAY_ANY, so we don't wanna warn for the SQLGlot dialect
        if self.dialect.__class__ != sqlglot.dialects.dialect.Dialect:
            self.unsupported("ARRAY_ANY is unsupported")
[assistant] The parsers and generators live in separate packages. Let me look at those and the MySQL DATE_ADD handling.
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators | head -100; echo ----; cat sqlglot/parsers/doris.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/doris.py; echo ----; cat sqlglot/generators/starrocks.py; echo ----; grep -rn \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parser.py | head", "description": "Read doris/starrocks parser and generator modules"}
[tool_result] <persisted-output>
Output too large (35.6KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-90e86f132b84-20261028-111420-doris-and-starrocks-dialects-bot-base-1/526b33eb-6e7d-4a0e-b220-c923785d3b09/tool-results/bksng3ed1.txt

Preview (first 2KB):
sqlglot/generators:
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgr
…[1313 chars elided]…

    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
        "COLLECT_SET": exp.ArrayUniqueAgg.from_arg_list,
        "DATE_TRUNC": _build_date_trunc,
        "L2_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "MONTHS_ADD": exp.AddMonths.from_arg_list,
        "REGEXP": exp.RegexpLike.from_arg_list,
        "TO_DATE": exp.TsOrDsToDate.from_arg_list,
    }

    FUNCTION_PARSERS = {
        k: v for k, v in MySQLParser.FUNCTION_PARSERS.items() if k != "GROUP_CONCAT"
...
</persisted-output>
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py | sed -n 30,200p; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; cat sqlglot/generators/doris.py; echo ----; cat sqlglot/generators/starrocks.py; echo ----; grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|build_date_delta_with_interval\\|date_add\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/base.py sqlglot/dialects/mysql.py", "description": "Read rest of doris/starrocks parser and generator modules"}
[tool_result] <persisted-output>
Output too large (34.4KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-90e86f132b84-20261028-111420-doris-and-starrocks-dialects-bot-base-1/526b33eb-6e7d-4a0e-b220-c923785d3b09/tool-results/bwsiq75pc.txt

Preview (first 2KB):
        "DATE_TRUNC": _build_date_trunc,
        "L2_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "MONTHS_ADD": exp.AddMonths.from_arg_list,
        "REGEXP": exp.RegexpLike.from_arg_list,
     
…[1301 chars elided]…
ing_granularity_dynamic)
        else:
            create_expressions = None

        self._match_r_paren()

        return self.expression(
            exp.PartitionByRangeProperty(
                partition_expressions=expr, create_expressions=create_expressions
            )
        )

    def _parse_partitioning_granularity_dynamic(self) -> exp.PartitionByRangePropertyDynamic:
        self._match_text_seq("FROM")
        start = self._parse_wrapped(self._parse_string)
...
</persisted-output>
[tool_use Bash] {"command": "grep -n -i \"date_add\\|date_sub\\|DateAdd\\|DateSub\\|DATE_DELTA\\|interval\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/dialects/mysql.py | cut -c1-220", "description": "Grep date add/sub handling in mysql-family files"}
[tool_result] sqlglot/parsers/starrocks.py:126:        every = self._parse_wrapped(lambda: self._parse_interval() or self._parse_number())
sqlglot/parsers/starrocks.py:134:                [ASYNC | ASYNC [START (<start_time>)] EVERY (INTERVAL <refresh_interval>) | MANUAL]
sqlglot/parsers/starrocks.py:142:            self._match_text_seq("INTERVAL")
sqlglot/generators/starrocks.py:322:        every = f" EVERY (INTERVAL {every} {unit})" if every and unit else ""
sqlglot/generators/mysql.py:8:    build_date_delta
…[2459 chars elided]…
"DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/parsers/mysql.py:137:        "TIMESTAMPDIFF": build_date_delta(exp.TimestampDiff),
sqlglot/parsers/mysql.py:498:        self, parse_interval: bool = True, fallback_to_identifier: bool = False
sqlglot/parsers/mysql.py:509:            parse_interval=parse_interval, fallback_to_identifier=fallback_to_identifier
sqlglot/dialects/mysql.py:51:    VALID_INTERVAL_UNITS = {
sqlglot/dialects/mysql.py:52:        *Dialect.VALID_INTERVAL_UNITS,
[tool_use Bash] {"command": "sed -n 60,110p sqlglot/generators/mysql.py; echo ----; sed -n 60,80p sqlglot/generators/doris.py; sed -n 175,195p sqlglot/generators/doris.py; echo ----; grep -rn -i \"date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | cut -c1-250", "description": "Inspect MySQL date_add_sql and existing doris/starrocks tests"}
[tool_result] def _unix_to_time_sql(self: MySQLGenerator, expression: exp.UnixToTime) -> str:
    scale = expression.args.get("scale")
    timestamp = expression.this

    if scale in (None, exp.UnixToTime.SECONDS):
        return self.func("FROM_UNIXTIME", timestamp, self.format_time(expression))

    return self.func(
        "FROM_UNIXTIME",
        exp.Div(this=timestamp, expression=exp.func("POW", 10, scale)),
        self.format_time(expression),
    )


def date_add_sql(
    kind: str,
) -> t.Callable[
…[3919 chars elided]…
AS __timestamp FROM tableT",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[tool_use Bash] {"command": "grep -n \"^class\\|^from\\|^import\" sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py sqlglot/parsers/doris.py; grep -n \"def unit_to_str\\|def unit_to_var\" -A12 sqlglot/dialects/dialect.py; sed -n 105,125p sqlglot/parsers/mysql.py; grep -n \"DATE_ADD\\|DateAdd\\|DateSub\" sqlglot/generators/starrocks.py sqlglot/generators/doris.py; grep -rln -i \"doris\\|starrocks\" tests | head -20", "description": "Inspect class hierarchy, unit helpers, and test files"}
[tool_result] sqlglot/generators/doris.py:1:from __future__ import annotations
sqlglot/generators/doris.py:3:from sqlglot import exp
sqlglot/generators/doris.py:4:from sqlglot.dialects.dialect import (
sqlglot/generators/doris.py:11:from sqlglot.generators.mysql import MySQLGenerator
sqlglot/generators/doris.py:23:class DorisGenerator(MySQLGenerator):
sqlglot/parsers/starrocks.py:1:from __future__ import annotations
sqlglot/parsers/starrocks.py:4:from sqlglot import exp
sqlglot/parsers/starrocks.py:5:from sql
…[3344 chars elided]…
alects/test_doris.py
tests/dialects/test_bigquery.py
tests/dialects/test_snowflake.py
tests/dialects/test_spark.py
tests/dialects/test_oracle.py
tests/dialects/test_presto.py
tests/dialects/test_starrocks.py
tests/dialects/test_redshift.py
tests/dialects/test_teradata.py
tests/dialects/test_dialect.py
tests/dialects/test_duckdb.py
tests/dialects/test_mysql.py
tests/dialects/test_hive.py
tests/dialects/test_postgres.py
tests/dialects/test_clickhouse.py
tests/fixtures/optimizer/qualify_columns.sql
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/generators/doris.py; sed -n 23,35p sqlglot/generators/doris.py; echo ----; sed -n 1,70p sqlglot/generators/starrocks.py; echo ----; sed -n 1,12p sqlglot/parsers/starrocks.py; grep -n \"TRANSFORMS\" sqlglot/generator.py | head -5", "description": "Read generator headers and TRANSFORMS setup"}
[tool_result] from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    property_sql,
    rename_func,
    time_format,
    unit_to_str,
)
from sqlglot.generators.mysql import MySQLGenerator


def _lag_lead_sql(self, expression: exp.Lag | exp.Lead) -> str:
    return self.func(
        "LAG" if isinstance(expression, exp.Lag) else "LEAD",
        expression.this,
        expression.args.get("offset") or exp.Literal.number(1),
        
…[3188 chars elided]…
lot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser


class StarRocksParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
13:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSON_PATH_PART_TRANSFORMS
64:AFTER_HAVING_MODIFIER_TRANSFORMS: dict[str, t.Any] = {
80:    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
134:    TRANSFORMS: t.ClassVar[dict[type[exp.Expr], t.Callable[..., str]]] = {
135:        **JSON_PATH_PART_TRANSFORMS,
[assistant] Both dialects inherit MySQL's `DATE_ADD` parser and generator, and the only thing rejecting the two-argument form is the `INTERVAL` check in `build_date_delta_with_interval`. I'll add a shared parse builder and a generator helper in `dialect.py`, then wire them into the Doris and StarRocks parsers and generators.
[tool_use Bash] {"command": "sed -n 1625,1640p sqlglot/dialects/dialect.py; grep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/starrocks.py | head; grep -n \"^from\\|^import\\|    build_\\|^)\" sqlglot/parsers/doris.py | head -20", "description": "View insertion point and imports"}
[tool_result] def date_add_interval_sql(data_type: str, kind: str) -> t.Callable[[Generator, exp.Expr], str]:
    def func(self: Generator, expression: exp.Expr) -> str:
        this = self.sql(expression, "this")
        interval = exp.Interval(this=expression.expression, unit=unit_to_var(expression))
        return f"{data_type}_{kind}({this}, {self.sql(interval)})"

    return func


def timestamptrunc_sql(
    func: str = "DATE_TRUNC", zone: bool = False
) -> t.Callable[[Generator, exp.TimestampTrunc], st
…[109 chars elided]…
_to_str(expression), expression.this]
        if zone:
            args.append(expression.args.get("zone"))
88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
1:from __future__ import annotations
4:from sqlglot import exp
5:from sqlglot.helper import seq_get
6:from sqlglot.parsers.mysql import MySQLParser
7:from sqlglot.tokens import TokenType
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "    return _builder\n\n\ndef date_trunc_to_time(args: BuilderArgs) -> exp.DateTrunc | exp.TimestampTrunc:", "new_string": "    return _builder\n\n\ndef build_date_delta_with_interval_or_days(\n    expression_c
…[98 chars elided]…
_with_interval(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            return expression_class(this=args[0], expression=args[1], unit=exp.var(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time(args: BuilderArgs) -> exp.DateTrunc | exp.TimestampTrunc:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return f\"{data_type}_{kind}({this}, {self.sql(interval)})\"\n\n    return func\n\n\ndef timestamptrunc_sql(", "new_string": "        return f\"{data_type}_{kind}({this}, {self.sql(interval)})\"\n\n   
…[115 chars elided]…
 t.Callable[[Generator, exp.Expr], str]:\n    def func(self: Generator, expression: exp.Expr) -> str:\n        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            return self.func(f\"DATE_{kind}\", expression.this, expression.expression)\n\n        return interval_sql(self, expression)\n\n    return func\n\n\ndef timestamptrunc_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now the parsers.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/parsers/starrocks.py", "description": "View StarRocks parser header and FUNCTIONS"}
[tool_result] from __future__ import annotations


from sqlglot import exp
from sqlglot.dialects.dialect import build_timestamp_trunc
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser


class StarRocksParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
        "DATE_TRUNC": build_timestamp_trunc,
        "DATEDIFF": lambda args: exp.DateDiff(
            this=seq_get(args, 0), expression=seq_get(args, 1), unit=exp.Literal.string("DAY")
        ),
        "DATE_DIFF": lambda args: exp.DateDiff(
            this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
        ),
        "ARRAY_FLATTEN": exp.Flatten.from_arg_list,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n     
…[170 chars elided]…
build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Now the generators. Doris already emits `DATE_ADD(x, n)` for `TsOrDsAdd`, so I'll route `DateAdd`/`DateSub` with a DAY unit through the same two-argument form and fall back to MySQL's `INTERVAL` output otherwise.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    property_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    date_add_days_sql,\n    property_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "        exp.Lead: _lag_lead_sql,\n        exp.Map: rename_func(\"ARRAY_MAP\"),", "new_string": "        exp.DateAdd: date_add_days_sql(\"ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_add_days_sql(\"SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),\n        exp.Lag: _lag_lead_sql,\n        exp.Lead: _lag_lead_sql,\n        exp.Map: rename_func(\"ARRAY_MAP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"TRANSFORMS = {\" -A8 sqlglot/generators/doris.py; grep -n \"TRANSFORMS = {\" -A6 sqlglot/generators/starrocks.py | tail -8; grep -n \"exp.Lag\\|exp.Date\\|exp.Cast\\|exp.Array\\b\" sqlglot/generators/starrocks.py | head", "description": "Check TRANSFORMS blocks in doris/starrocks generators"}
[tool_result] 48:    TRANSFORMS = {
49-        **MySQLGenerator.TRANSFORMS,
50-        exp.AddMonths: rename_func("MONTHS_ADD"),
51-        exp.ApproxDistinct: approx_count_distinct_sql,
52-        exp.ArgMax: rename_func("MAX_BY"),
53-        exp.ArgMin: rename_func("MIN_BY"),
54-        exp.ArrayAgg: rename_func("COLLECT_LIST"),
55-        exp.ArrayToString: rename_func("ARRAY_JOIN"),
56-        exp.ArrayUniqueAgg: rename_func("COLLECT_SET"),
88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerat
…[48 chars elided]…
,
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
92-        exp.ArrayFilter: rename_func("ARRAY_FILTER"),
93-        exp.ArrayToString: rename_func("ARRAY_JOIN"),
94-        exp.ApproxDistinct: approx_count_distinct_sql,
89:        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90:        exp.Array: inline_array_sql,
96:        exp.DateDiff: lambda self, e: self.func("DATE_DIFF", unit_to_str(e), e.this, e.expression),
[tool_use Bash] {"command": "sed -n 56,64p sqlglot/generators/doris.py; sed -n 94,110p sqlglot/generators/starrocks.py", "description": "View TRANSFORMS neighborhoods for insertion"}
[tool_result]         exp.ArrayUniqueAgg: rename_func("COLLECT_SET"),
        exp.CurrentDate: lambda self, _: self.func("CURRENT_DATE"),
        exp.CurrentTimestamp: lambda self, _: self.func("NOW"),
        exp.DateTrunc: lambda self, e: self.func("DATE_TRUNC", e.this, unit_to_str(e)),
        exp.EuclideanDistance: rename_func("L2_DISTANCE"),
        exp.GroupConcat: lambda self, e: self.func(
            "GROUP_CONCAT", e.this, e.args.get("separator") or exp.Literal.string(",")
        ),
        exp.JSO
…[699 chars elided]…
SecurityProperty: lambda self, e: f"SECURITY {self.sql(e.this)}",
        exp.StDistance: st_distance_sphere,
        exp.StrToUnix: lambda self, e: self.func("UNIX_TIMESTAMP", e.this, self.format_time(e)),
        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
        exp.TimeStrToDate: rename_func("TO_DATE"),
        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
[assistant] I'll move those entries to their alphabetical spots in each TRANSFORMS block.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "        exp.DateAdd: date_add_days_sql(\"ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_add_days_sql(\"SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),\n        exp.Lag: _lag_lead_sql,", "new_string": "        exp.Lag: _lag_lead_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "        exp.CurrentTimestamp: lambda self, _: self.func(\"NOW\"),\n        exp.DateTrunc:", "new_string": "        exp.CurrentTimestamp: lambda self, _: self.func(\"NOW\"),\n        exp.DateAdd: date_add_days_sql(\"ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_add_days_sql(\"SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),\n        exp.DateTrunc:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\",\n        exp.DateDiff:", "new_string": "        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\",\n        exp.DateAdd: date_add_days_sql(\"ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_add_days_sql(\"SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),\n        exp.DateDiff:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    date_add_days_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now let me check the behaviour directly, including the interval forms that must stay unchanged.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for s in [\\\"select date_add('2025-01-01', 1) from a\\\", \\\"select date_sub('2025-01-01', 1) from a\\\", \\\"select date_add('2025-01-01', INTERVAL 2 MONTH) from a\\\", \\\"select date_sub(x, INTERVAL 1 DAY) from a\\\"]:\n        e = sqlglot.
…[78 chars elided]…
'|', e.sql('duckdb'))\nprint(sqlglot.transpile(\\\"select date_add(x, interval 3 day) from t\\\", read='duckdb', write='doris'))\nprint(sqlglot.transpile(\\\"select date_add(x, 3) from t\\\", read='doris', write='starrocks'))\nprint(sqlglot.transpile(\\\"select date_add(x, 3) from t\\\", read='doris', write='mysql'))\n\"", "description": "Check parse and generate behavior for doris and starrocks"}
[tool_result] doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL 1 DAY FROM a
doris | SELECT DATE_SUB('2025-01-01', 1) FROM a | SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY) FROM a | SELECT CAST('2025-01-01' AS DATE) - INTERVAL 1 DAY FROM a
doris | SELECT DATE_ADD('2025-01-01', INTERVAL '2' MONTH) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL '2' MONTH) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL '2'
…[414 chars elided]…
LECT CAST('2025-01-01' AS DATE) - INTERVAL 1 DAY FROM a
starrocks | SELECT DATE_ADD('2025-01-01', INTERVAL '2' MONTH) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL '2' MONTH) FROM a | SELECT CAST('2025-01-01' AS DATE) + INTERVAL '2' MONTH FROM a
starrocks | SELECT DATE_SUB(x, '1') FROM a | SELECT DATE_SUB(x, INTERVAL '1' DAY) FROM a | SELECT x - INTERVAL '1' DAY FROM a
["SELECT DATE_ADD(x, INTERVAL '3' DAY) FROM t"]
['SELECT DATE_ADD(x, 3) FROM t']
['SELECT DATE_ADD(x, INTERVAL 3 DAY) FROM t']
[assistant] Parsing works for both dialects, and the `INTERVAL` forms are unchanged. One problem: `DATE_SUB(x, INTERVAL 1 DAY)` now renders as `DATE_SUB(x, '1')`, because sqlglot stores interval counts as string literals. That's valid but looks wrong, so I'll emit numeric literals on the two-argument path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            return self.func(f\"DATE_{kind}\", expression.this, expression.expression)", "new_string": "        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            days = expression.expression\n            if days.is_string and days.name.isdigit():\n                days = exp.Literal.number(days.name)\n            return self.func(f\"DATE_{kind}\", expression.this, days)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now tests. I'll look at how the existing Doris and StarRocks test files are structured.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_doris.py; echo ...; grep -n \"def test_\" tests/dialects/test_doris.py | tail -3; tail -5 tests/dialects/test_doris.py; echo ----; sed -n 1,12p tests/dialects/test_starrocks.py; grep -n \"def test_\" tests/dialects/test_starrocks.py | tail -3; tail -5 tests/dialects/test_starrocks.py", "description": "Inspect structure of doris and starrocks test files"}
[tool_result] from tests.dialects.test_dialect import Validator


class TestDoris(Validator):
    dialect = "doris"

    def test_doris(self):
        self.validate_all(
            "SELECT TO_DATE('2020-02-02 00:00:00')",
            write={
                "doris": "SELECT TO_DATE('2020-02-02 00:00:00')",
                "oracle": "SELECT CAST('2020-02-02 00:00:00' AS DATE)",
...
154:    def test_table_alias_conversion(self):
229:    def test_rename_table(self):
239:    def test_materialized_view_properties
…[663 chars elided]…
 def test_partition(self):
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] I'll add a focused test to each dialect's test file.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py", "old_string": "            \"CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH AUTO ON SCHEDULE EVERY 10 MINUTE AS SELECT 1\"\n        )\n", "new_string": "            \"CREATE MATERIALIZED VIEW mv BUILD DEFERRED REFRESH A
…[231 chars elided]…
 1)\")\n        self.validate_all(\n            \"SELECT DATE_ADD(x, 1)\",\n            write={\n                \"doris\": \"SELECT DATE_ADD(x, 1)\",\n                \"mysql\": \"SELECT DATE_ADD(x, INTERVAL 1 DAY)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB(x, INTERVAL 1 DAY)\",\n            write={\"doris\": \"SELECT DATE_SUB(x, 1)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py", "old_string": "START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))\"\n        )\n", "new_string": "START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))\"\n        )\n\n    def test_date_add_sub_da
…[151 chars elided]…
        self.validate_all(\n            \"SELECT DATE_ADD(x, 1)\",\n            write={\n                \"starrocks\": \"SELECT DATE_ADD(x, 1)\",\n                \"mysql\": \"SELECT DATE_ADD(x, INTERVAL 1 DAY)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB(x, INTERVAL 1 DAY)\",\n            write={\"starrocks\": \"SELECT DATE_SUB(x, 1)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Now the project's check command from the harness notes, run on the full suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full pytest suite", "timeout": 600000}
[tool_result]                     ),
                    sql,
                )
    
        for write_dialect, write_sql in (write or {}).items():
            with self.subTest(f"{sql} -> {write_dialect}"):
                if write_sql is UnsupportedError:
                    with self.assertRaises(UnsupportedError):
                        expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
                else:
>                   self.assertEqual(
                        expression.sql(
    
…[520 chars elided]…
========== short test summary info ============================
SUBFAILED[DATE_ADD(x, 1, 'DAY') -> starrocks] tests/dialects/test_dialect.py::TestDialect::test_time
SUBFAILED[DATE_ADD(x, 1, 'DAY') -> doris] tests/dialects/test_dialect.py::TestDialect::test_time
SUBFAILED[DATE_ADD(x, 1) -> starrocks] tests/dialects/test_dialect.py::TestDialect::test_time
SUBFAILED[DATE_ADD(x, 1) -> doris] tests/dialects/test_dialect.py::TestDialect::test_time
4 failed, 1086 passed, 17846 subtests passed in 52.61s
[assistant] Four existing subtests in `test_dialect.py::test_time` fail. Those expectations pin the current Doris/StarRocks output for `DATE_ADD(x, 1)`, so let me read them before deciding anything.
[tool_use Bash] {"command": "grep -n \"DATE_ADD(x, 1\" -B3 -A12 tests/dialects/test_dialect.py | head -60", "description": "Show the existing test_time expectations for DATE_ADD"}
[tool_result] 1047-            },
1048-        )
1049-        self.validate_all(
1050:            "DATE_ADD(x, 1, 'DAY')",
1051-            read={
1052-                "snowflake": "DATEADD('DAY', 1, x)",
1053:                "dremio": "DATE_ADD(x, 1)",
1054-            },
1055-            write={
1056-                "bigquery": "DATE_ADD(x, INTERVAL 1 DAY)",
1057-                "drill": "DATE_ADD(x, INTERVAL 1 DAY)",
1058-                "duckdb": "x + INTERVAL 1 DAY",
1059:                "hive": "DATE_AD
…[1582 chars elided]…
        write={
1095-                "bigquery": "DATE_TRUNC(x, DAY)",
1096-                "duckdb": "DATE_TRUNC('DAY', x)",
1097-                "mysql": "DATE(x)",
--
1262-            "TS_OR_DS_ADD(x, 1, 'DAY')",
1263-            write={
1264-                "presto": "DATE_ADD('DAY', 1, CAST(CAST(x AS TIMESTAMP) AS DATE))",
1265:                "hive": "DATE_ADD(x, 1)",
1266-            },
1267-        )
1268-        self.validate_all(
1269-            "TS_OR_DS_ADD(CURRENT_DATE, 1, 'DAY')",
[assistant] The existing `test_time` expectations pin `DATE_ADD(x, 1)` → `DATE_ADD(x, INTERVAL 1 DAY)` for both Doris and StarRocks. Those are deliberate, shared expectations, and the guardrails say to fix code rather than edit tests. So the generator change I made can't stand as written. I'll revert it and keep the parser change, which is what fixes the reported error. Then I'll check whether the two-argument form can still be emitted anywhere without breaking those tests.
[tool_use Bash] {"command": "git checkout -- sqlglot/generators/doris.py sqlglot/generators/starrocks.py && git status --short && git diff --stat", "description": "Revert generator edits and show remaining changes"}
[tool_result]  M sqlglot/dialects/dialect.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
 sqlglot/dialects/dialect.py      | 30 ++++++++++++++++++++++++++++++
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 15 +++++++++++++++
 tests/dialects/test_starrocks.py | 15 +++++++++++++++
 5 files changed, 66 insertions(+), 1 deletion(-)
[assistant] The generator files now match HEAD (the notice is just my revert showing up). Next I'll drop the now-unused `date_add_days_sql` helper and rewrite the new tests so they check parsing, with generation left at the existing `INTERVAL` output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "def date_add_days_sql(\n    kind: str, interval_sql: t.Callable[[Generator, exp.Expr], str]\n) -> t.Callable[[Generator, exp.Expr], str]:\n    def func(self: Generator, expression: exp.Expr) -> str:\n        u
…[18 chars elided]…
expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            days = expression.expression\n            if days.is_string and days.name.isdigit():\n                days = exp.Literal.number(days.name)\n            return self.func(f\"DATE_{kind}\", expression.this, days)\n\n        return interval_sql(self, expression)\n\n    return func\n\n\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py", "old_string": "    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB('2025-01-01', 1)\")\n        self.validate_all(\n 
…[478 chars elided]…
025-01-01', 1)\",\n            write={\n                \"doris\": \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n                \"mysql\": \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB('2025-01-01', 1)\",\n            write={\"doris\": \"SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB('2025-01-01', 1)\")\n        self.validate_all
…[498 chars elided]…
1', 1)\",\n            write={\n                \"starrocks\": \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n                \"mysql\": \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB('2025-01-01', 1)\",\n            write={\"starrocks\": \"SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-111420-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse(\\\"select date_add('2025-01-01', 1) from a\\\", dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql('doris'))\nprint(sqlglot.parse(\\\"select date_sub('2025-01-01', 1) from a\\\", dia
…[38 chars elided]…
ErrorLevel.IMMEDIATE)[0].sql('starrocks'))\n\"; git diff --stat; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests 2>&1 | tail -2", "description": "Run full suite, repro example, and lint/format check", "timeout": 600000}
[tool_result] .............................................................................. [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1086 passed, 17850 subtests passed in 52.60s
SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY) FROM a
 sqlglot/dialects/dialect.py      | 14 ++++++++++++++
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 13 +++++++++++++
 tests/dialects/test_starrocks.py | 13 +++++++++++++
 5 files changed, 46 insertions(+), 1 deletion(-)
All checks passed!
233 files already formatted
[assistant] Doris and StarRocks now parse the two-argument `DATE_ADD` / `DATE_SUB` form, but I did not add the two-argument output. The existing test suite expects the `INTERVAL` form, so I couldn't add it without changing those expectations.

The example from the report now parses and round-trips as:

```
SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
```

**What changed**
- `sqlglot/dialects/dialect.py`: new `build_date_delta_with_interval_or_days`. It builds a `DateAdd`/`DateSub` with a DAY unit when the second argument is not an `INTERVAL`, and otherwise falls through to the existing interval bu
…[642 chars elided]…
dit tests to pass, so I reverted that change.

Decision for you: should Doris and StarRocks write the two-argument form? If yes, I'll update those four expectations in `test_dialect.py` and make the generator change. Doris already emits the two-argument form for `TS_OR_DS_ADD`, so this would make the two paths consistent. Both `INTERVAL` and two-argument forms are valid Doris and StarRocks SQL, so the current output is correct, just not the form you asked for.

**Verification**
- Full suite: `1086 passed, 17850 subtests passed`.
- `ruff check` and `ruff format --check`: clean.
- Not committed.
