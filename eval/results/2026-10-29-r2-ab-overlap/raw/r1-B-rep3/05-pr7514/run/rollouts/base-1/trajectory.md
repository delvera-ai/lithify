# trajectory base-1

final message:
Doris and StarRocks now parse the two-argument `DATE_ADD` / `DATE_SUB` form. The repro from the report returns `SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a`. The full suite passes (1086 tests), and ruff format and lint are clean.

**Generation does not emit the two-argument form.** I wrote the generator side first, but four existing tests in `tests/dialects/test_dialect.py::test_time` pin DAY-unit `DateAdd` output for Doris and StarRocks to `DATE_ADD(x, INTERVAL 1 DAY)`. I can't edit those tests, so I reverted it. Both `INTERVAL` forms are valid in both dialects, so the output is correct, just not byte-identical to the input. If you want the literal two-argument spelling on output, that will need a change to those expectations or a marker on the AST node so the source form is remembered. Tell me if you want either.

**What changed:**
- `sqlglot/dialects/dialect.py`: new `build_date_delta_with_interval_or_days`. A two-argument call whose second argument is not an `INTERVAL` becomes `DateAdd`/`DateSub` with unit `DAY`. Everything else goes through the existing interval builder.
- `sqlglot/parsers/doris.py` and `sqlglot/parsers/starrocks.py`: `DATE_ADD` and `DATE_SUB` use that builder. MySQL is unchanged.
- `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`: a `test_date_add_sub_days` method in each, checking that the two-argument form reads correctly and produces the `INTERVAL` output.

I could only run these against sqlglot's own parser and generator. I haven't checked against a live Doris or StarRocks instance, and I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"DATE_ADD\\|DATE_SUB\\|DateAdd\\|DateSub\\|_build_date_add\\|build_date_delta\" dialects/doris.py dialects/starrocks.py dialects/mysql.py | head -80", "description": "Find date_add handling in dialects"}
[tool_result] rg: dialects/doris.py: No such file or directory (os error 2)
rg: dialects/starrocks.py: No such file or directory (os error 2)
rg: dialects/mysql.py: No such file or directory (os error 2)
0 matches for 'DATE_ADD\|DATE_SUB\|DateAdd\|DateSub\|_build_date_add\|build_date_delta'
[assistant] The working directory is a worktree, so my first grep ran from the wrong root. I'll search from the worktree's `sqlglot/` package instead.
[tool_use Bash] {"command": "ls && rg -n \"DATE_ADD|DATE_SUB|DateAdd|DateSub|build_date_delta|DateAddInterval\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head -80", "description": "Locate date_add handling in Doris/StarRocks/MySQL"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.7M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  2.5K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  794B
sqlglot.png  7.2K
11 matches in 1 files:

sqlglot/dialects/dialect.py:36:DATE_ADD_OR_DIFF = t.Union[
s
…[225 chars elided]…
dd,
sqlglot/dialects/dialect.py:49:exp.DateSub,
sqlglot/dialects/dialect.py:58:DATETIME_ADD = (exp.DateAdd, exp.TimeAdd, exp.DatetimeAdd, exp.TsOrDsAdd, exp...
sqlglot/dialects/dialect.py:1577:def build_date_delta(
sqlglot/dialects/dialect.py:1599:def build_date_delta_with_interval(
sqlglot/dialects/dialect.py:1934:def date_delta_sql(name: str, cast: bool = False) -> t.Callable[[Generator, D...
sqlglot/dialects/dialect.py:1935:def _delta_sql(self: Generator, expression: DATE_ADD_OR_DIFF) -> str:
[tool_use Bash] {"command": "cat sqlglot/dialects/doris.py && echo ---- && cat sqlglot/dialects/starrocks.py && echo ---- && sed -n 1570,1630p sqlglot/dialects/dialect.py && echo ---- && sed -n 1930,1960p sqlglot/dialects/dialect.py", "description": "Read Doris, StarRocks and date helper sources"}
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
…[3154 chars elided]…
lta_to_binary_interval_op(
    cast: bool = True,
) -> t.Callable[[Generator, DATETIME_DELTA], str]:
    def date_delta_to_binary_interval_op_sql(self: Generator, expression: DATETIME_DELTA) -> str:
        this = expression.this
        unit = unit_to_var(expression)
        op = "+" if isinstance(expression, DATETIME_ADD) else "-"

        to_type: exp.DATA_TYPE | None = None
        if cast:
            if isinstance(expression, exp.TsOrDsAdd):
                to_type = expression.return_type
[assistant] The dialect files are thin; the real logic lives under `sqlglot/parsers/` and `sqlglot/generators/`. Let me read those for Doris, StarRocks, and MySQL.
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators | head -100 && echo ---- && cat sqlglot/parsers/doris.py && echo ---- && cat sqlglot/parsers/starrocks.py && echo ---- && cat sqlglot/generators/doris.py && echo ---- && cat sqlglot/generators/starrocks.py && echo ---- && rg -n \"DATE_ADD|DATE_SUB|DateAdd|DateSub|build_date_delta|date_add|date_sub\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/dialects/mysql.py sqlglot/parsers/*.py sqlglot/generators/*.py | head -80", "description": "Read Doris/StarRocks parser and generator modules"}
[tool_result] <persisted-output>
Output too large (41.5KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-6e430de19896-20261029-173416-doris-and-starrocks-dialects-bot-base-1/017698cf-0c93-4efb-8dad-728bbe23053d/tool-results/bxjx1n2f7.txt

Preview (first 2KB):
__init__.py  0B
athena.py  5.8K
bigquery.py  24.3K
clickhouse.py  26.6K
databricks.py  3.8K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  172.4K
dune.py  323B
exasol.py  28.0K
fa
…[1272 chars elided]…
 0), seq_get(args, 1)

    def _is_unit_like(e: exp.Expr | None) -> bool:
        if not (isinstance(e, exp.Literal) and e.is_string):
            return False
        text = e.this
        return not any(ch.isdigit() for ch in text)

    # Determine which argument is the unit
    unit, this = (a0, a1) if _is_unit_like(a0) else (a1, a0)

    return exp.TimestampTrunc(this=this, unit=unit)


class DorisParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
...
</persisted-output>
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py | sed -n 20,200p; echo ----; cat sqlglot/parsers/starrocks.py | head -150; echo ----; rg -n \"DATE_ADD|DATE_SUB|DateAdd|DateSub|build_date_delta|date_add|date_sub|DATE_ADD|DATE_SUB\" sqlglot/parsers/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py", "description": "Read Doris/StarRocks parser details and grep date functions"}
[tool_result]     # Determine which argument is the unit
    unit, this = (a0, a1) if _is_unit_like(a0) else (a1, a0)

    return exp.TimestampTrunc(this=this, unit=unit)


class DorisParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
        "COLLECT_SET": exp.ArrayUniqueAgg.from_arg_list,
        "DATE_TRUNC": _build_date_trunc,
        "L2_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "MONTHS_ADD": exp.AddMonths.from_arg_list,
        "REGEXP": exp.RegexpLike.from_arg_list,
 
…[10380 chars elided]…
iff)([unit, start_ts, express...
sqlglot/generators/mysql.py:742:dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
sqlglot/parsers/mysql.py:9:build_date_delta,
sqlglot/parsers/mysql.py:10:build_date_delta_with_interval,
sqlglot/parsers/mysql.py:114:"DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:"DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/parsers/mysql.py:137:"TIMESTAMPDIFF": build_date_delta(exp.TimestampDiff),
[assistant] MySQL's `DATE_ADD` uses `build_date_delta_with_interval`, which Doris and StarRocks inherit. Next I'll read the MySQL generator's `date_add_sql` and the Doris and StarRocks generators.
[tool_use Bash] {"command": "sed -n 70,95p sqlglot/generators/mysql.py; echo ----; sed -n 1,20p sqlglot/generators/doris.py; echo ...; sed -n 60,90p sqlglot/generators/doris.py; sed -n 175,200p sqlglot/generators/doris.py; echo ----; cat sqlglot/generators/starrocks.py | head -80; echo ----; sed -n 105,125p sqlglot/parsers/mysql.py; sed -n 730,750p sqlglot/generators/mysql.py", "description": "Read MySQL/Doris/StarRocks date_add generator code"}
[tool_result]         self.format_time(expression),
    )


def date_add_sql(
    kind: str,
) -> t.Callable[[generator.Generator, exp.Expr], str]:
    def func(self: generator.Generator, expression: exp.Expr) -> str:
        return self.func(
            f"DATE_{kind}",
            expression.this,
            exp.Interval(this=expression.expression, unit=unit_to_var(expression)),
        )

    return func


def _ts_or_ds_to_date_sql(self: MySQLGenerator, expression: exp.TsOrDsToDate) -> str:
    time_forma
…[7297 chars elided]…

        timestamp_diff = build_date_delta(exp.TimestampDiff)([unit, start_ts, expression.this])
        interval = exp.Interval(this=timestamp_diff, unit=unit)
        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])

        return self.sql(dateadd)

    def converttimezone_sql(self, expression: exp.ConvertTimezone) -> str:
        from_tz = expression.args.get("source_tz")
        to_tz = expression.args.get("target_tz")
        dt = expression.args.get("timestamp")
[assistant] Doris and StarRocks inherit the MySQL `DATE_ADD` parser and generator. Before choosing a representation, I'll check what the existing tests pin down for these functions.
[tool_use Bash] {"command": "rg -n -i \"date_add|date_sub|days_add|DATE_ADD\\(|DATE_SUB\\(\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -80; echo ----; rg -n \"DATE_ADD|date_add\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/generators/doris.py; ls tests/dialects | grep -i \"doris\\|starrocks\"; git log --oneline -3 -- sqlglot/parsers/doris.py", "description": "Check existing date_add tests for Doris/StarRocks/MySQL"}
[tool_result] grep: parentheses not balanced
----
2 matches in 1 files:

sqlglot/generators/doris.py:75:exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:"date_add",
test_doris.py  11.5K
test_starrocks.py  15.3K
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
6c26467d5 Refactor(parser)!!: Fully compile the parsers  (#7265)
b155a2957 refactor!: expression to not use **kwargs because it allocates multiple dicts (#7256)
[tool_use Bash] {"command": "rg -n -i -F -e \"date_add\" -e \"date_sub\" -e \"days_add\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -80", "description": "Search tests for date_add references"}
[tool_result] tests/dialects/test_mysql.py:353:        self.validate_identity("DATE_ADD(x, INTERVAL '1' YEAR)")
tests/dialects/test_mysql.py:876:            "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:878:                "mysql": "WITH t AS (SELECT CAST('2020-01-10' AS DATE) AS col, 5 AS num_days) SELECT DATE_ADD(col, INTERVAL num_days DAY) FROM t",
tests/dialects/test_mysql.py:1004:            "SELECT D
…[462 chars elided]…
AS __timestamp FROM tableT",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[assistant] No existing Doris or StarRocks tests cover `date_add`. Next I'll reproduce the failure with the project's interpreter and check which existing tests write `DATE_ADD` or `DATE_SUB` for these dialects.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['doris','starrocks']:\n    try:\n        print(d, sqlglot.parse_one(\\\"select date_add('2025-01-01', 1)\\\", read=d).sql(d))\n    except Exception as e: print(d, 'ERR', e)\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\", read='mysql', write='doris'))\n\"; rg -n -F -e \"DATE_ADD\" -e \"DATE_SUB\" -e \"date_add\" -e \"DATE_DIFF\" tests/ | rg -i \"doris|starrocks\" | head -30; rg -n \"doris|starrocks\" tests/dialects/test_mysql.py | head -5", "description": "Reproduce the bug and check related test expectations"}
[tool_result] doris ERR INTERVAL expression expected but got '1'
starrocks ERR INTERVAL expression expected but got '1'
["SELECT DATE_ADD(x, INTERVAL '1' DAY)"]
grep: tests/: Is a directory
4 matches in 4 files:

1432:0:"a / b",
538:0:"SELECT x'CC'",
559:0:"SELECT x'0000CC'",
[assistant] Both dialects fail with the same error as the report. Next I'll look at how the Doris and StarRocks test files are structured so the new tests match them.
[tool_use Bash] {"command": "sed -n 1,40p tests/dialects/test_doris.py; echo ----; sed -n 1,30p tests/dialects/test_starrocks.py; echo ----; tail -30 tests/dialects/test_starrocks.py", "description": "Read Doris and StarRocks test file structure"}
[tool_result] from tests.dialects.test_dialect import Validator


class TestDoris(Validator):
    dialect = "doris"

    def test_doris(self):
        self.validate_all(
            "SELECT TO_DATE('2020-02-02 00:00:00')",
            write={
                "doris": "SELECT TO_DATE('2020-02-02 00:00:00')",
                "oracle": "SELECT CAST('2020-02-02 00:00:00' AS DATE)",
            },
        )
        self.validate_all(
            "SELECT MAX_BY(a, b), MIN_BY(c, d)",
            read={
             
…[3210 chars elided]…
   self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] The existing tests give me no conflicting expectations for these dialects. Before I pick a design, I need to confirm two things: how the generator prioritises `TRANSFORMS` against auto-discovered `*_sql` methods, and what the `unit_to_str` and `unit_to_var` helpers return.
[tool_use Bash] {"command": "rg -n \"TRANSFORMS\" sqlglot/generator.py | head; rg -n -A12 \"^def unit_to_str|^def unit_to_var\" sqlglot/dialects/dialect.py; rg -n -B2 -A12 \"transform = self.TRANSFORMS|self.TRANSFORMS.get\" sqlglot/generator.py | head -50", "description": "Check generator dispatch order and unit helpers"}
[tool_result] 9 matches in 5 files:

134:0:t.ClassVar[dict[type[exp.Expr], t.Callable[..., str]]] = {
632:0:t.ClassVar = {
64:0:dict[str, t.Any] = {
80:0:dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
sqlglot/generator.py:13:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSON_PATH_PART_TRANSFORMS
sqlglot/generator.py:135:**JSON_PATH_PART_TRANSFORMS,
sqlglot/generator.py:636:**AFTER_HAVING_MODIFIER_TRANSFORMS,
sqlglot/generator.py:3024:...en(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.values()],
[tool_use Bash] {"command": "rg -n \"_sql_transforms|self\\._transforms|def sql\\(\" sqlglot/generator.py | head; rg -n \"def unit_to_str|def unit_to_var\" -A10 sqlglot/dialects/dialect.py sqlglot/*.py | head -40", "description": "Locate generator sql dispatch and unit helpers"}
[tool_result] 1 matches in 1 files:

sqlglot/generator.py:1062:def sql(
[tool_use Bash] {"command": "sed -n 1062,1110p sqlglot/generator.py; rg -n \"def unit_to_str|def unit_to_var\" sqlglot/ | head", "description": "Read generator sql dispatch and locate unit helpers"}
[tool_result]     def sql(
        self,
        expression: str | exp.Expr | None,
        key: str | None = None,
        comment: bool = True,
    ) -> str:
        if not expression:
            return ""

        if isinstance(expression, str):
            return expression

        if key:
            value = expression.args.get(key)
            if value:
                return self.sql(value)
            return ""

        handler = self._dispatch.get(expression.__class__)

        if handler:
        
…[1148 chars elided]…
urn self.prepend_ctes(expression, sql)

    def characterset_sql(self, expression: exp.CharacterSet) -> str:
        default = "DEFAULT " if expression.args.get("default") else ""
        return f"{default}CHARACTER SET={self.sql(expression, 'this')}"
2 matches in 1 files:

sqlglot/dialects/dialect.py:1979:def unit_to_str(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
sqlglot/dialects/dialect.py:1990:def unit_to_var(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 76,100p sqlglot/generator.py; rg -n \"_dispatch\" sqlglot/generator.py | head; sed -n 1979,2000p sqlglot/dialects/dialect.py", "description": "Read generator dispatch construction and unit helper bodies"}
[tool_result] def _build_dispatch(
    cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and expr_cls not in dispatch:
            dispatch[expr_cls] = getattr(cls, attr_name)

    r
…[657 chars elided]…
 if default else None

    if isinstance(unit, exp.Placeholder) or type(unit) not in (exp.Var, exp.Literal):
        return unit

    return exp.Literal.string(unit.name)


def unit_to_var(expression: exp.Expr, default: str = "DAY") -> exp.Expr | None:
    unit = expression.args.get("unit")

    if isinstance(unit, (exp.Var, exp.Placeholder, exp.WeekStart, exp.Column)):
        return unit

    value = unit.name if unit else default
    return exp.Var(this=value) if value else None


@t.overload
[assistant] Subclass `TRANSFORMS` entries override auto-discovered `*_sql` methods, and MySQL's `DateAdd`/`DateSub` entries are inherited. So the Doris and StarRocks overrides need to go in their own `TRANSFORMS`. Next I'll check what those dicts already contain, and whether the MySQL base test suite passes before I change anything.
[tool_use Bash] {"command": "rg -n \"TRANSFORMS|DateAdd|DateSub|TsOrDsAdd|TimestampTrunc\" sqlglot/generators/doris.py sqlglot/generators/starrocks.py; rg -n \"build_date_delta_with_interval|^from sqlglot.dialects.dialect import\" -A3 sqlglot/parsers/mysql.py | head -20; PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -5", "description": "Inspect generator TRANSFORMS and run baseline dialect tests"}
[tool_result] 7 matches in 2 files:

sqlglot/generators/doris.py:47:TRANSFORMS = {
sqlglot/generators/doris.py:48:**MySQLGenerator.TRANSFORMS,
sqlglot/generators/doris.py:75:exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:78:exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", e.this, unit_to_s...
sqlglot/generators/starrocks.py:88:TRANSFORMS = {
sqlglot/generators/starrocks.py:89:**{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTru...
sqlglot/generators/starrocks.py:107:exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e...
........................................................... [ 85%]
..........                                                         [100%]
69 passed, 595 subtests passed in 0.33s
[assistant] Baseline is green (69 passed, 595 subtests). I'll check the top of each generator's `TRANSFORMS` so the new entries go in the right place.
[tool_use Bash] {"command": "sed -n 45,52p sqlglot/generators/doris.py; echo ----; sed -n 86,110p sqlglot/generators/starrocks.py; echo ----; rg -n \"^from|^import\" -A6 sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py | head -5; sed -n 1,30p sqlglot/parsers/mysql.py | rg -n \"dialect import\" -A8", "description": "View TRANSFORMS blocks and import lines"}
[tool_result]     TIMESTAMP_FUNC_TYPES = set()

    TRANSFORMS = {
        **MySQLGenerator.TRANSFORMS,
        exp.AddMonths: rename_func("MONTHS_ADD"),
        exp.ApproxDistinct: approx_count_distinct_sql,
        exp.ArgMax: rename_func("MAX_BY"),
        exp.ArgMin: rename_func("MIN_BY"),
----
    }

    TRANSFORMS = {
        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
        exp.Array: inline_array_sql,
        exp.ArrayAgg: rename_func("ARRAY_AGG"),
        exp.A
…[975 chars elided]…
DATE_TRUNC", unit_to_str(e), e.this),
        exp.TimeStrToDate: rename_func("TO_DATE"),
        exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
        exp.UnixToTime: rename_func("FROM_UNIXTIME"),
----
7:from sqlglot.dialects.dialect import (
8-    Dialect,
9-    build_date_delta,
10-    build_date_delta_with_interval,
11-    build_formatted_time,
12-    isnull_to_is_null,
13-)
14-from sqlglot.helper import seq_get
15-from sqlglot.tokens import TokenType
[assistant] I have what I need. The plan:

- **Parse:** a shared builder in `dialect.py` accepts the two-argument form when the second argument is not an `INTERVAL`, and produces `DateAdd`/`DateSub` with unit `DAY`. Doris and StarRocks use it for `DATE_ADD`/`DATE_SUB`. MySQL is untouched.
- **Generate:** for `DAY` units, Doris and StarRocks emit the two-argument form. Other units fall back to MySQL's `INTERVAL` output.

I'll start with the shared helpers in `dialect.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n", "new_string": "        return expression_class(this=args[0], expression=interval
…[140 chars elided]…
) -> t.Callable[[BuilderArgs], E | None]:\n    interval_builder = build_date_delta_with_interval(expression_class)\n\n    def _builder(args: BuilderArgs) -> E | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            return expression_class(this=args[0], expression=args[1], unit=exp.var(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return self.func(\n            name,\n            unit_to_var(expression),\n            expression.expression,\n            expression.this,\n        )\n\n    return _delta_sql\n\n", "new_string": "   
…[294 chars elided]…
 str]\n) -> t.Callable[[Generator, DATE_ADD_OR_SUB], str]:\n    def _delta_sql(self: Generator, expression: DATE_ADD_OR_SUB) -> str:\n        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            return self.func(name, expression.this, expression.expression)\n\n        return interval_sql(self, expression)\n\n    return _delta_sql\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Next, the parsers and generators for both dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py", "old_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n     
…[170 chars elided]…
build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Now the generators. I'll register the day-aware helper in each `TRANSFORMS`, with MySQL's existing entries as the fallback.
[tool_use Bash] {"command": "sed -n 1,16p sqlglot/generators/doris.py && sed -n 1,12p sqlglot/generators/starrocks.py", "description": "View generator import blocks"}
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
from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_array_sql,
    property_sql,
)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    property_sql,\n    rename_func,\n    time_format,\n    unit_to_str,\n)\nfrom sqlglot.generators.mysql import MySQLGenerator", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    date_delta_days_or_interval_sql,\n    property_sql,\n    rename_func,\n    time_format,\n    unit_to_str,\n)\nfrom sqlglot.generators.mysql import MySQLGenerator"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "        **MySQLGenerator.TRANSFORMS,\n        exp.AddMonths: rename_func(\"MONTHS_ADD\"),", "new_string": "        **MySQLGenerator.TRANSFORMS,\n        exp.AddMonths: rename_func(\"MONTHS_ADD\"),\n        exp.DateAdd: date_delta_days_or_interval_sql(\"DATE_ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_delta_days_or_interval_sql(\"DATE_SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    date_delta_days_or_interval_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\",\n        exp.DateDiff: lambda self, e: self.func(\"DATE_DIFF\", unit_to_str(e), e.this, e.expression),", "new_string": "        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\",\n        exp.DateAdd: date_delta_days_or_interval_sql(\"DATE_ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateDiff: lambda self, e: self.func(\"DATE_DIFF\", unit_to_str(e), e.this, e.expression),\n        exp.DateSub: date_delta_days_or_interval_sql(\"DATE_SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now I'll check the repro and the generated output for both dialects, including the MySQL-to-Doris and StarRocks paths.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for q in [\\\"select date_add('2025-01-01', 1)\\\", \\\"select date_sub('2025-01-01', 1)\\\", \\\"select date_add('2025-01-01', interval 2 day)\\\", \\\"select date_add('2025-01-01', interval 2 hour)\\\", \
…[162 chars elided]…
Y), DATE_SUB(x, INTERVAL n DAY)\\\", read='mysql', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='doris', write='mysql'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='starrocks', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, 1)\\\", read='doris', write='starrocks'))\n\"", "description": "Verify parse and generate for both dialects"}
[tool_result] doris SELECT DATE_ADD('2025-01-01', 1)
doris SELECT DATE_SUB('2025-01-01', 1)
doris SELECT DATE_ADD('2025-01-01', '2')
doris SELECT DATE_ADD('2025-01-01', INTERVAL '2' HOUR)
doris SELECT DATE_ADD('2025-01-01', 1 + n)
starrocks SELECT DATE_ADD('2025-01-01', 1)
starrocks SELECT DATE_SUB('2025-01-01', 1)
starrocks SELECT DATE_ADD('2025-01-01', '2')
starrocks SELECT DATE_ADD('2025-01-01', INTERVAL '2' HOUR)
starrocks SELECT DATE_ADD('2025-01-01', 1 + n)
["SELECT DATE_ADD(x, '1'), DATE_SUB(x, n)"]
['SELECT DATE_ADD(x, INTERVAL 1 DAY)']
['SELECT DATE_ADD(x, 1)']
['SELECT DATE_ADD(x, 1)']
[assistant] Parsing and generating both work now. Two outputs need fixing, though:

- `INTERVAL 2 DAY` in Doris and StarRocks now emits `DATE_ADD(x, '2')`. The MySQL parser stores the interval count as a string literal, so the day-form output has to be a number. Before my change this input produced `INTERVAL '2' DAY`.
- The same quoting shows up on MySQL→Doris transpiles.

I'll normalise integer string literals to numbers in the day-form helper.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            return self.func(name, expression.this, expression.expression)", "new_string": "        unit = unit_to_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            days = expression.expression\n            if days.is_string and days.name.isdigit():\n                days = exp.Literal.number(days.name)\n            return self.func(name, expression.this, days)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['doris','starrocks']:\n    for q in [\\\"select date_add('2025-01-01', 1)\\\", \\\"select date_sub('2025-01-01', 1)\\\", \\\"select date_add('2025-01-01', interval 2 day)\\\", \\\"select date_add('2025-01-01', interval 2 hour)\\\"]:\
…[54 chars elided]…
\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY), DATE_SUB(x, INTERVAL n DAY)\\\", read='mysql', write='doris'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\", read='mysql', write='starrocks'))\nprint(sqlglot.transpile(\\\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\\\", read='mysql', write='mysql'))\n\"", "description": "Re-verify outputs after literal normalisation"}
[tool_result] doris SELECT DATE_ADD('2025-01-01', 1)
doris SELECT DATE_SUB('2025-01-01', 1)
doris SELECT DATE_ADD('2025-01-01', 2)
doris SELECT DATE_ADD('2025-01-01', INTERVAL '2' HOUR)
starrocks SELECT DATE_ADD('2025-01-01', 1)
starrocks SELECT DATE_SUB('2025-01-01', 1)
starrocks SELECT DATE_ADD('2025-01-01', 2)
starrocks SELECT DATE_ADD('2025-01-01', INTERVAL '2' HOUR)
['SELECT DATE_ADD(x, 1), DATE_SUB(x, n)']
['SELECT DATE_ADD(x, 1)']
["SELECT DATE_ADD(x, INTERVAL '1' DAY)"]
[assistant] Both directions now produce clean output. Next I'll add tests to the existing Doris and StarRocks test files. I'll check the end of each file first so the new methods fit.
[tool_use Bash] {"command": "tail -12 tests/dialects/test_doris.py; echo ----; rg -n \"def test_\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py", "description": "Inspect end of Doris test file and test method names"}
[tool_result]         # REFRESH methods with triggers
        self.validate_identity("CREATE MATERIALIZED VIEW mv REFRESH COMPLETE ON MANUAL AS SELECT 1")
        self.validate_identity("CREATE MATERIALIZED VIEW mv REFRESH AUTO ON COMMIT AS SELECT 1")
        self.validate_identity(
            "CREATE MATERIALIZED VIEW mv REFRESH AUTO ON SCHEDULE EVERY 5 MINUTE STARTS '2025-01-01 00:00:00' AS SELECT 1"
        )

        # Combined BUILD and REFRESH
        self.validate_identity(
            "CREATE MATERIA
…[823 chars elided]…
est_starrocks(self):
tests/dialects/test_starrocks.py:30:def test_ddl(self):
tests/dialects/test_starrocks.py:125:def test_identity(self):
tests/dialects/test_starrocks.py:136:def test_time(self):
tests/dialects/test_starrocks.py:145:def test_regex(self):
tests/dialects/test_starrocks.py:157:def test_unnest(self):
tests/dialects/test_starrocks.py:215:def test_analyze(self):
tests/dialects/test_starrocks.py:236:def test_between(self):
tests/dialects/test_starrocks.py:254:def test_partition(self):
[tool_use Bash] {"command": "cat >> tests/dialects/test_doris.py <<'EOF'\n\n    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB('2025-01-01', 1)\")\n        self.validate_all(\n            \"DATE_ADD(x, 1)\",\n            read={\"mysql\": \"DATE_ADD(x, INTERVAL 1 DAY)\"},\n            write={\n               
…[1506 chars elided]…
\",\n            \"SELECT DATE_ADD('2025-01-01 00:00:00', INTERVAL '2' HOUR)\",\n        )\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py 2>&1 | tail -30", "description": "Add Doris/StarRocks tests and run dialect tests"}
[tool_result] ............................................. [ 63%]
..........................                                           [100%]
71 passed, 607 subtests passed in 0.20s
[assistant] The dialect tests pass: 71 now, up from 69, which matches the two new test methods. Next I'll run the full suite with the project's harness command, plus ruff on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"---- ruff\"; $PY -I -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5; $PY -I -m ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py 2>&1 | tail -5", "description": "Run full test suite and ruff format/lint checks"}
[tool_result]                             identify=identify,
                        ),
                        write_sql,
                    )
E                   AssertionError: 'DATE_ADD(x, 1)' != 'DATE_ADD(x, INTERVAL 1 DAY)'
E                   - DATE_ADD(x, 1)
E                   + DATE_ADD(x, INTERVAL 1 DAY)

tests/dialects/test_dialect.py:101: AssertionError
=========================== short test summary info ============================
SUBFAILED[DATE_ADD(x, 1, 'DAY') -> starrocks] tests/dialects/te
…[50 chars elided]…
TE_ADD(x, 1, 'DAY') -> doris] tests/dialects/test_dialect.py::TestDialect::test_time
SUBFAILED[DATE_ADD(x, 1) -> starrocks] tests/dialects/test_dialect.py::TestDialect::test_time
SUBFAILED[DATE_ADD(x, 1) -> doris] tests/dialects/test_dialect.py::TestDialect::test_time
4 failed, 1086 passed, 17852 subtests passed in 47.42s
---- ruff
Would reformat: sqlglot/generators/doris.py
Would reformat: sqlglot/generators/starrocks.py
2 files would be reformatted, 5 files already formatted
All checks passed!
[assistant] Four existing tests in `test_dialect.py::test_time` fail. They pin Doris and StarRocks output to `DATE_ADD(x, INTERVAL 1 DAY)` for DAY-unit dates. My generator change breaks that expectation. Let me read the test before deciding how to resolve it.
[tool_use Bash] {"command": "rg -n \"DATE_ADD\\(x, 1\" -B12 -A8 tests/dialects/test_dialect.py | head -80", "description": "Read the failing test_time expectations"}
[tool_result] grep: parentheses not balanced
[tool_use Bash] {"command": "rg -n -F \"DATE_ADD(x, 1\" tests/dialects/test_dialect.py; rg -n -F \"DATE_ADD(x, 1, 'DAY')\" -B3 -A3 tests/dialects/test_dialect.py | head -40", "description": "Locate DATE_ADD expectations in test_dialect"}
[tool_result] 1050:            "DATE_ADD(x, 1, 'DAY')",
1053:                "dremio": "DATE_ADD(x, 1)",
1059:                "hive": "DATE_ADD(x, 1)",
1065:                "spark": "DATE_ADD(x, 1)",
1070:                "dremio": "DATE_ADD(x, 1)",
1074:            "DATE_ADD(x, 1)",
1079:                "hive": "DATE_ADD(x, 1)",
1082:                "spark": "DATE_ADD(x, 1)",
1085:                "dremio": "DATE_ADD(x, 1)",
1265:                "hive": "DATE_ADD(x, 1)",
1047-            },
1048-        )
1049-        self.validate_all(
1050:            "DATE_ADD(x, 1, 'DAY')",
1051-            read={
1052-                "snowflake": "DATEADD('DAY', 1, x)",
1053-                "dremio": "DATE_ADD(x, 1)",
[tool_use Bash] {"command": "sed -n 1049,1095p tests/dialects/test_dialect.py", "description": "Read full DATE_ADD expectations block in test_dialect"}
[tool_result]         self.validate_all(
            "DATE_ADD(x, 1, 'DAY')",
            read={
                "snowflake": "DATEADD('DAY', 1, x)",
                "dremio": "DATE_ADD(x, 1)",
            },
            write={
                "bigquery": "DATE_ADD(x, INTERVAL 1 DAY)",
                "drill": "DATE_ADD(x, INTERVAL 1 DAY)",
                "duckdb": "x + INTERVAL 1 DAY",
                "hive": "DATE_ADD(x, 1)",
                "materialize": "x + INTERVAL '1 DAY'",
                "mysql": 
…[882 chars elided]…
Y', 1, x)",
                "spark": "DATE_ADD(x, 1)",
                "starrocks": "DATE_ADD(x, INTERVAL 1 DAY)",
                "doris": "DATE_ADD(x, INTERVAL 1 DAY)",
                "dremio": "DATE_ADD(x, 1)",
            },
        )
        self.validate_all(
            "DATE_TRUNC('DAY', x)",
            read={
                "bigquery": "DATE_TRUNC(x, day)",
                "spark": "TRUNC(x, 'day')",
            },
            write={
                "bigquery": "DATE_TRUNC(x, DAY)",
[assistant] The existing `test_dialect.py` expectations are explicit: DAY-unit `DateAdd` writes to Doris and StarRocks as `DATE_ADD(x, INTERVAL 1 DAY)`. I can't edit those tests, so the generator change has to go. Parsing the two-argument form already produces a `DateAdd` with unit `DAY`, and the existing generator emits valid `INTERVAL` SQL for both dialects. I'll revert the generator side and the now-unused helper, then fix my tests to match.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "        exp.AddMonths: rename_func(\"MONTHS_ADD\"),\n        exp.DateAdd: date_delta_days_or_interval_sql(\"DATE_ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateSub: date_delta_days_or_interval_sql(\"DATE_SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),", "new_string": "        exp.AddMonths: rename_func(\"MONTHS_ADD\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py", "old_string": "    approx_count_distinct_sql,\n    date_delta_days_or_interval_sql,\n    property_sql,", "new_string": "    approx_count_distinct_sql,\n    property_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.DateAdd: date_delta_days_or_interval_sql(\"DATE_ADD\", MySQLGenerator.TRANSFORMS[exp.DateAdd]),\n        exp.DateDiff: lambda self, e: self.func(\"DATE_DIFF\", unit_to_str(e), e.this, e.expression),\n        exp.DateSub: date_delta_days_or_interval_sql(\"DATE_SUB\", MySQLGenerator.TRANSFORMS[exp.DateSub]),", "new_string": "        exp.DateDiff: lambda self, e: self.func(\"DATE_DIFF\", unit_to_str(e), e.this, e.expression),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py", "old_string": "    arrow_json_extract_sql,\n    date_delta_days_or_interval_sql,\n    rename_func,", "new_string": "    arrow_json_extract_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Next I'll remove the unused generator helper from `dialect.py`, keeping the parser builder.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "def date_delta_days_or_interval_sql(\n    name: str, interval_sql: t.Callable[[Generator, DATE_ADD_OR_SUB], str]\n) -> t.Callable[[Generator, DATE_ADD_OR_SUB], str]:\n    def _delta_sql(self: Generator, expres
…[53 chars elided]…
o_var(expression)\n        if isinstance(unit, exp.Var) and unit.name.upper() == \"DAY\":\n            days = expression.expression\n            if days.is_string and days.name.isdigit():\n                days = exp.Literal.number(days.name)\n            return self.func(name, expression.this, days)\n\n        return interval_sql(self, expression)\n\n    return _delta_sql\n\n\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Next I'll rewrite the two test methods so they check what the change actually guarantees: the two-argument form parses and emits valid `INTERVAL` SQL in each dialect.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py", "old_string": "    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB('2025-01-01', 1)\")\n        self.validate_all(\n 
…[732 chars elided]…
"new_string": "    def test_date_add_sub_days(self):\n        self.validate_all(\n            \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n            read={\"doris\": \"SELECT DATE_ADD('2025-01-01', 1)\"},\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB('2025-01-01', INTERVAL n DAY)\",\n            read={\"doris\": \"SELECT DATE_SUB('2025-01-01', n)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB('2025-01-01', 1)\")\n        self.validate_all
…[752 chars elided]…
ing": "    def test_date_add_sub_days(self):\n        self.validate_all(\n            \"SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY)\",\n            read={\"starrocks\": \"SELECT DATE_ADD('2025-01-01', 1)\"},\n        )\n        self.validate_all(\n            \"SELECT DATE_SUB('2025-01-01', INTERVAL n DAY)\",\n            read={\"starrocks\": \"SELECT DATE_SUB('2025-01-01', n)\"},\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173416-doris-and-starrocks-dialects-bot/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Now the full suite again, plus ruff format and lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; echo \"---- ruff\"; $PY -I -m ruff format --check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -3; $PY -I -m ruff check sqlglot/dialects/dialect.py sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py 2>&1 | tail -2; git status --short", "description": "Rerun full suite and lint after revert"}
[tool_result] ....................................................................................................................................... [ 90%]
............................... [ 93%]
........................................................................   [100%]
1086 passed, 17848 subtests passed in 45.59s
---- ruff
7 files already formatted
All checks passed!
 M sqlglot/dialects/dialect.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[assistant] All 1086 tests pass and ruff is clean. Last, I'll re-run the exact repro from the report and review the final diff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['doris','starrocks']:\n    print(sqlglot.parse(\\\"select date_add('2025-01-01', 1) from a\\\", dialect=d, error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql(d))\n    print(sqlglot.transpile(\\\"select date_sub('2025-01-01', 1)\\\", read=d, write='mysql'))\n\"; git diff -- sqlglot/", "description": "Run the reported repro and show source diff"}
[tool_result] SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
["SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY)"]
SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
["SELECT DATE_SUB('2025-01-01', INTERVAL 1 DAY)"]
sqlglot/dialects/dialect.py  | 14 ++++++++++++++
 sqlglot/parsers/doris.py     |  3 +++
 sqlglot/parsers/starrocks.py |  4 +++-
 3 files changed, 20 insertions(+), 1 deletion(-)

--- Changes ---

sqlglot/dialects/dialect.py
  @@ -1613,6 +1613,20 @@ def build_date_delta_with_interval(
  +def bu
…[1566 chars elided]…
lot.helper import seq_get
   from sqlglot.parsers.mysql import MySQLParser
   
  @@ -10,6 +10,8 @@ from sqlglot.parsers.mysql import MySQLParser
  +        "DATE_ADD": build_date_delta_with_interval_or_days(exp.DateAdd),
  +        "DATE_SUB": build_date_delta_with_interval_or_days(exp.DateSub),
           "DATE_TRUNC": build_timestamp_trunc,
           "DATEDIFF": lambda args: exp.DateDiff(
               this=seq_get(args, 0), expression=seq_get(args, 1), unit=exp.Literal.string("DAY")
  +3 -1
[assistant] Doris and StarRocks now parse the two-argument `DATE_ADD` / `DATE_SUB` form. The repro from the report returns `SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a`. The full suite passes (1086 tests), and ruff format and lint are clean.

**Generation does not emit the two-argument form.** I wrote the generator side first, but four existing tests in `tests/dialects/test_dialect.py::test_time` pin DAY-unit `DateAdd` output for Doris and StarRocks to `DATE_ADD(x, INTERVAL 1 DAY)`. I can't edit those tests, so I reverted it. Both `INTERVAL` forms are valid in both dialects, so the output is corr
…[398 chars elided]…
ecomes `DateAdd`/`DateSub` with unit `DAY`. Everything else goes through the existing interval builder.
- `sqlglot/parsers/doris.py` and `sqlglot/parsers/starrocks.py`: `DATE_ADD` and `DATE_SUB` use that builder. MySQL is unchanged.
- `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`: a `test_date_add_sub_days` method in each, checking that the two-argument form reads correctly and produces the `INTERVAL` output.

I could only run these against sqlglot's own parser and generator. I haven't checked against a live Doris or StarRocks instance, and I haven't committed anything.
