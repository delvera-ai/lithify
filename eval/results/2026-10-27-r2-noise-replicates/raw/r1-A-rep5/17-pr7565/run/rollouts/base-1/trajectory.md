# trajectory base-1

final message:
Oracle now parses and round-trips `LISTAGG` with `ON OVERFLOW`. The full suite passes (1094 tests) and ruff is clean. I did not commit.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` now goes through the shared `_parse_string_agg`, the same path Snowflake and Trino use. Before this, Oracle `LISTAGG(... ON OVERFLOW ...)` raised a `ParseError`.
- `sqlglot/generators/oracle.py`: added an `exp.GroupConcat` mapping that emits `ON OVERFLOW` and adds no default separator (`sep=None`), since Oracle's separator defaults to NULL. Without this, Oracle output would have added a `','` that the input didn't have.
- `tests/dialects/test_oracle.py`: added `test_listagg` covering `ON OVERFLOW ERROR`, `TRUNCATE '...' WITH COUNT`, `TRUNCATE '...' WITHOUT COUNT`, and a plain separator/no-overflow case. All are identity round-trips.

**Something you should know about Snowflake:** the parser accepts `ON OVERFLOW` for Snowflake, but the Snowflake generator drops it on output. `LISTAGG(x, ';' ON OVERFLOW TRUNCATE '...')` in Snowflake becomes `LISTAGG(x, ';')`. So the clause parses there but doesn't round-trip. I left that alone because it's outside this task. If you want Snowflake to round-trip it too, that's a one-line change to its generator.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\\|ListAgg\" sqlglot/ | grep -v \"^Binary\" | head -60", "description": "Search for overflow and ListAgg references"}
[tool_use Bash] {"command": "grep -rn -i \"listagg\\|overflow\" tests/dialects/ | head -40", "description": "Search tests for listagg and overflow"}
[tool_result] tests/dialects/test_snowflake.py:382:                "duckdb": "SELECT (SELECT LISTAGG(SUBSTRING('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 1 + CAST(FLOOR(random_value * 62) AS INT), 1), '') FROM (SELECT (ABS(HASH(i + 123)) % 1000) / 1000.0 AS random_value FROM RANGE(10) AS t(i)))",
tests/dialects/test_snowflake.py:389:                "duckdb": "SELECT (SELECT LISTAGG(SUBSTRING('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 1 + CAST(FLOOR(random_value * 
…[4323 chars elided]…
y:68:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:71:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:74:            "SELECT LISTAGG(col) WITHIN GROUP (ORDER BY col DESC) FROM tbl",
tests/dialects/test_trino.py:75:            "SELECT LISTAGG(col, ',') WITHIN GROUP (ORDER BY col DESC) FROM tbl",
[tool_result] sqlglot/parser.py:7705:        if self._match_text_seq("ON", "OVERFLOW"):
sqlglot/parser.py:7706:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7708:                on_overflow: exp.Expr | None = exp.var("ERROR")
sqlglot/parser.py:7711:                on_overflow = self.expression(
sqlglot/parser.py:7712:                    exp.OverflowTruncateBehavior(
sqlglot/parser.py:7721:            on_overflow = None
sqlglot/parser.py:7745:         
…[4209 chars elided]…
/duckdb.py:2795:        # Snowflake's TIME_FROM_PARTS supports overflow
sqlglot/generators/duckdb.py:2796:        if overflow:
sqlglot/generators/duckdb.py:2812:            # Overflow or nanoseconds detected - use INTERVAL arithmetic
sqlglot/generators/duckdb.py:3944:        null_if_pos_overflow = expression.args.get("null_if_pos_overflow")
sqlglot/generators/duckdb.py:3967:            if null_if_pos_overflow:
sqlglot/generators/mysql.py:739:        # Source: https://stackoverflow.com/a/32955740
[tool_use Bash] {"command": "sed -n 7690,7760p sqlglot/parser.py && echo ---- && sed -n 5485,5500p sqlglot/generator.py && echo ---- && sed -n 1878,1895p sqlglot/expressions/query.py && echo ---- && sed -n 130,140p sqlglot/expressions/aggregate.py && echo ---- && grep -n \"string_agg\\|STRING_AGG\\|LISTAGG\\|GroupConcat\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/parser.py | head -30", "description": "Read LISTAGG parsing, generator, and Oracle references"}
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
…[4677 chars elided]…
py:7729:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7733:        # the STRING_AGG call is parsed like in MySQL / SQLite and can thus be transpiled more easily to them.
sqlglot/parser.py:7736:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7742:            exp.GroupConcat(
sqlglot/parser.py:9886:        return self.expression(exp.GroupConcat(this=this, separator=separator))
[tool_use Bash] {"command": "grep -n \"_parse_string_agg\" -A3 sqlglot/parser.py | head; grep -n \"def _parse_string_agg\" -A60 sqlglot/parser.py | head -80; echo ----; grep -n \"def groupconcat_sql\\|def _groupconcat\" -A30 sqlglot/dialects/dialect.py | head -5; sed -n 2405,2452p sqlglot/dialects/dialect.py; echo ----; grep -n \"ON OVERFLOW\\|on_overflow\" tests/dialects/test_trino.py tests/dialects/test_snowflake.py tests/dialects/test_oracle.py; grep -n \"class Oracle\\|Generator\\|class Parser\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py | head", "description": "Read string_agg parser and related Oracle files"}
[tool_result] 1511:        "STRING_AGG": lambda self: self._parse_string_agg(),
1512-        "SUBSTRING": lambda self: self._parse_substring(),
1513-        "TRIM": lambda self: self._parse_trim(),
1514-        "TRY_CAST": lambda self: self._parse_cast(False, safe=True),
--
7695:    def _parse_string_agg(self) -> exp.GroupConcat:
7696-        if self._match(TokenType.DISTINCT):
7697-            args: list[exp.Expr | None] = [
7698-                self.expression(exp.Distinct(expressions=[self._parse_disjuncti
…[5447 chars elided]…
ORDER BY col ASC) FROM tbl"
sqlglot/parsers/oracle.py:22:class OracleParser(parser.Parser):
sqlglot/generators/oracle.py:14:def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
sqlglot/generators/oracle.py:23:class OracleGenerator(generator.Generator):
sqlglot/generators/oracle.py:45:        **generator.Generator.TYPE_MAPPING,
sqlglot/generators/oracle.py:66:        **generator.Generator.TRANSFORMS,
sqlglot/generators/oracle.py:107:        **generator.Generator.PROPERTIES_LOCATION,
[tool_use Bash] {"command": "sed -n 1,60p sqlglot/parsers/oracle.py; echo ----; grep -n \"GroupConcat\\|groupconcat\" sqlglot/generators/oracle.py sqlglot/generators/snowflake.py sqlglot/generators/trino.py sqlglot/generator.py sqlglot/parsers/snowflake.py; echo ----; grep -n \"LISTAGG\\|GROUP_CONCAT\\|STRING_AGG\" sqlglot/parser.py sqlglot/parsers/*.py | head -30; echo ----; grep -n \"def test_listagg\" -A25 tests/dialects/test_trino.py", "description": "Inspect Oracle parser and generator and LISTAGG handling"}
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
…[4371 chars elided]…
l"
69-        )
70-        self.validate_identity(
71-            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
72-        )
73-        self.validate_identity(
74-            "SELECT LISTAGG(col) WITHIN GROUP (ORDER BY col DESC) FROM tbl",
75-            "SELECT LISTAGG(col, ',') WITHIN GROUP (ORDER BY col DESC) FROM tbl",
76-        )
77-
78-    def test_trim(self):
79-        self.validate_identity("SELECT TRIM('!' FROM '!foo!')")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d,q in [('oracle','SELECT LISTAGG(last_name, \\'; \\' ON OVERFLOW TRUNCATE \\'...\\') WITHIN GROUP (ORDER BY last_name) FROM t'),\n ('oracle','SELECT LISTAGG(last_name, \\'; \\') WITHIN GROUP (ORDER BY last_name) FROM t'),\n ('oracle','SELECT LISTAGG(last_name, \\'; \\' ON OVER
…[391 chars elided]…
except Exception as e: print(d,'ERR',type(e).__name__, str(e)[:200])\nprint(repr(sqlglot.parse_one(\\\"SELECT LISTAGG(a, ';' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY a) FROM t\\\", read='snowflake').find(sqlglot.exp.GroupConcat).args))\n\"; grep -n \"GroupConcat\" sqlglot/generator.py sqlglot/generators/*.py | head -30", "description": "Check current round-trip behavior across dialects"}
[tool_result] oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
oracle -> SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM t
snowflake -> SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
trino -> SELECT 
…[1694 chars elided]…
erflow=True),
sqlglot/generators/spark.py:57:def _groupconcat_sql(self: SparkGenerator, expression: exp.GroupConcat) -> str:
sqlglot/generators/spark.py:115:            exp.GroupConcat: _groupconcat_sql,
sqlglot/generators/tsql.py:49:def _string_agg_sql(self: TSQLGenerator, expression: exp.GroupConcat) -> str:
sqlglot/generators/tsql.py:53:        # exp.Distinct can appear below an exp.Order or an exp.GroupConcat expression
sqlglot/generators/tsql.py:204:        exp.GroupConcat: _string_agg_sql,
[tool_use Bash] {"command": "sed -n 1,14p sqlglot/generators/oracle.py; echo ----; sed -n 60,100p sqlglot/generators/oracle.py; echo ----; grep -n \"def test_\\|^class\" tests/dialects/test_oracle.py | head -20; sed -n 1,12p tests/dialects/test_oracle.py", "description": "Inspect Oracle generator and test file layout"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
----
        exp.DType.BINARY: "BLOB",
        exp.DType.VARBINARY: "BLOB",
        exp.DType.ROWVERSION: "BLOB",
    }

    TRANSFORMS = {
        **generator.Generator.TRANSFORMS,
        exp.DateStrToDat
…[2312 chars elided]…
:    def test_analyze(self):
870:    def test_prior(self):
878:    def test_utc_time(self):
884:    def test_merge(self):
from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
[assistant] I have what I need. Oracle has no `LISTAGG` parser, so it falls through to a generic function call. I'll route it through the shared `_parse_string_agg` (the same path Snowflake and Trino use) and add a generator mapping that emits `ON OVERFLOW` without a default separator, since Oracle's separator defaults to NULL.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_ARRAYAGG\": lambda self: self._parse_oracle_json_arrayagg(),\n        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_ARRAYAGG\": lambda self: self._parse_oracle_json_arrayagg(),\n        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None, on_overflow=True),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now I'll add a test next to the existing Oracle tests, then check the round-trips.
[tool_use Bash] {"command": "sed -n 868,884p tests/dialects/test_oracle.py", "description": "View test file section around test_prior"}
[tool_result]         )

    def test_prior(self):
        self.validate_identity(
            "SELECT id, PRIOR name AS parent_name, name FROM tree CONNECT BY NOCYCLE PRIOR id = parent_id"
        )

        with self.assertRaises(ParseError):
            parse_one("PRIOR as foo", read="oracle")

    def test_utc_time(self):
        self.validate_identity("UTC_TIME()").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIME(6)").assert_is(exp.UtcTime)
        self.validate_identity("UTC_TIMESTAMP()").assert_is(exp.UtcTimestamp)
        self.validate_identity("UTC_TIMESTAMP(6)").assert_is(exp.UtcTimestamp)

    def test_merge(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_utc_time(self):\n        self.validate_identity(\"UTC_TIME()\").assert_is(exp.UtcTime)", "new_string": "    def test_listagg(self):\n        self.validate_identity(\n            \"SELECT LISTAGG
…[443 chars elided]…
identity(\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\"\n        )\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name) WITHIN GROUP (ORDER BY last_name) FROM employees\"\n        )\n\n    def test_utc_time(self):\n        self.validate_identity(\"UTC_TIME()\").assert_is(exp.UtcTime)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-100248-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m unittest tests.dialects.test_oracle 2>&1 | tail -30; $PY -m unittest tests.dialects.test_trino tests.dialects.test_snowflake 2>&1 | tail -3", "description": "Run Oracle, Trino, and Snowflake dialect tests"}
[tool_result] .........................
----------------------------------------------------------------------
Ran 25 tests in 0.084s

OK
Ran 102 tests in 0.333s

OK
[assistant] Targeted tests pass. Now the full project check command from the harness, plus lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; $PY -m ruff check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Run full pytest suite and ruff checks"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[329 chars elided]…
.................... [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 52.26s
All checks passed!
3 files already formatted
[assistant] Oracle now parses and round-trips `LISTAGG` with `ON OVERFLOW`. The full suite passes (1094 tests) and ruff is clean. I did not commit.

**Changes**
- `sqlglot/parsers/oracle.py`: `LISTAGG` now goes through the shared `_parse_string_agg`, the same path Snowflake and Trino use. Before this, Oracle `LISTAGG(... ON OVERFLOW ...)` raised a `ParseError`.
- `sqlglot/generators/oracle.py`: added an `exp.GroupConcat` mapping that emits `ON OVERFLOW` and adds no default separator (`sep=None`), since Oracle's separator defaults to NULL. Without this, Oracle output would have added a `','` that the input
…[47 chars elided]…
: added `test_listagg` covering `ON OVERFLOW ERROR`, `TRUNCATE '...' WITH COUNT`, `TRUNCATE '...' WITHOUT COUNT`, and a plain separator/no-overflow case. All are identity round-trips.

**Something you should know about Snowflake:** the parser accepts `ON OVERFLOW` for Snowflake, but the Snowflake generator drops it on output. `LISTAGG(x, ';' ON OVERFLOW TRUNCATE '...')` in Snowflake becomes `LISTAGG(x, ';')`. So the clause parses there but doesn't round-trip. I left that alone because it's outside this task. If you want Snowflake to round-trip it too, that's a one-line change to its generator.
