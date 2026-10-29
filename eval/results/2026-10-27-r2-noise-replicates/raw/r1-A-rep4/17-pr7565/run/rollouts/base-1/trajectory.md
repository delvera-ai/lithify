# trajectory base-1

final message:
Oracle now parses `LISTAGG` with the `ON OVERFLOW` clause and round-trips it. The full test suite passes (1094 tests) and `ruff` is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/oracle.py`**: Added `"LISTAGG": lambda self: self._parse_string_agg()` to Oracle's `FUNCTION_PARSERS`. This is the same path Snowflake and Trino use, which already handles `ON OVERFLOW ERROR` and `TRUNCATE '...' [WITH|WITHOUT COUNT]`.
- **`sqlglot/generators/oracle.py`**: Added a `GroupConcat` transform using `groupconcat_sql(self, e, sep=None, on_overflow=True)`. Without this, the parsed node would have generated `GROUP_CONCAT` in Oracle output.
- **`tests/dialects/test_oracle.py`**: Added `test_listagg` covering the separator and no-separator forms, `ON OVERFLOW ERROR`, and each `TRUNCATE` variant.

**Choices to be aware of**

- `ON OVERFLOW TRUNCATE '...'` with no count comes back as `WITH COUNT`. The generator always writes an explicit count, and `WITH COUNT` is Oracle's default, so the output is equivalent. The test expects that canonical form.
- Oracle `LISTAGG` is now parsed into the shared `GroupConcat` node rather than kept as an anonymous function. This also changes cross-dialect output. For example, MySQL `GROUP_CONCAT(a SEPARATOR '; ')` written to Oracle now gives `LISTAGG(a, '; ')`, where it used to give `GROUP_CONCAT`. Dialect-to-dialect output from `LISTAGG` now goes through the shared node, and the existing suite still passes.
- Transpiling to other dialects drops the overflow clause (for example, Oracle to DuckDB). That matches how other dialects already handle it and is not something I changed.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\" sqlglot/ tests/ | head -50; grep -rn -i \"listagg\" sqlglot/ | head -40", "description": "Find existing LISTAGG and overflow handling"}
[tool_result] sqlglot/generator.py:5489:    def overflowtruncatebehavior_sql(self, expression: exp.OverflowTruncateBehavior) -> str:
sqlglot/parser.py:7705:        if self._match_text_seq("ON", "OVERFLOW"):
sqlglot/parser.py:7706:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7708:                on_overflow: exp.Expr | None = exp.var("ERROR")
sqlglot/parser.py:7711:                on_overflow = self.expression(
sqlglot/parser.py:7712:                 
…[5610 chars elided]…
   listagg = exp.WithinGroup(this=listagg, expression=order)
sqlglot/dialects/dialect.py:2449:        listagg.set("expressions", [f"{args}{modifiers}"])
sqlglot/dialects/dialect.py:2451:    return self.sql(listagg)
sqlglot/generators/redshift.py:87:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/exasol.py:342:            self, e, func_name="LISTAGG", within_group=True
sqlglot/generators/exasol.py:647:        "listagg",
sqlglot/generators/duckdb.py:1976:        SELECT LISTAGG(
[tool_use Bash] {"command": "sed -n 7695,7760p sqlglot/parser.py; echo ----; sed -n 2405,2455p sqlglot/dialects/dialect.py; echo ----; sed -n 5485,5500p sqlglot/generator.py; echo ----; grep -n \"GroupConcat\\|OverflowTruncate\\|def _parse_string_agg\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py sqlglot/parsers/snowflake.py sqlglot/parser.py | head -30; echo ----; sed -n 125,145p sqlglot/expressions/aggregate.py; echo; sed -n 1880,1890p sqlglot/expressions/query.py; echo ----; sed -n 50,80p tests/dialects/test_trino.py", "description": "Read LISTAGG parser, generator helpers, and tests"}
[tool_result]     def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disjunction))
        else:
            args = self._parse_csv(self._parse_disjunction)  # type: ignore

        if self._match_text_seq("ON", "OVERFLOW"):
  
…[6759 chars elided]…
dentity(
            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
        )
        self.validate_identity(
            "SELECT LISTAGG(col) WITHIN GROUP (ORDER BY col DESC) FROM tbl",
            "SELECT LISTAGG(col, ',') WITHIN GROUP (ORDER BY col DESC) FROM tbl",
        )

    def test_trim(self):
        self.validate_identity("SELECT TRIM('!' FROM '!foo!')")
        self.validate_identity("SELECT TRIM(BOTH '$' FROM '$var$')")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' O
…[32 chars elided]…
ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees\\\"]\nfor q in qs:\n  try:\n    e=sqlglot.parse_one(q, read='oracle'); print(repr(e.selects[0])[:400]); print(e.sql('oracle'))\n  except Exception as ex: print('ERR', type(ex).__name__, ex)\n  print('--')\n\"", "description": "Check current Oracle LISTAGG parsing behavior"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON O
…[29 chars elided]…
ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees\\\"]\nfor q in qs:\n  try:\n    e=sqlglot.parse_one(q, read='oracle'); print(repr(e.selects[0])[:400]); print(e.sql('oracle'))\n  except Exception as ex: print('ERR', type(ex).__name__, ex)\n  print('--')\n\"", "description": "Check current Oracle LISTAGG parsing behavior"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
--
ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
--
ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees
--
WithinGroup(
  this=Anonymous(
    this=LISTAGG,
    expressions=[
      Column(
        this=Identifier(this=last_name, quoted=False),
        join_mark=False),
      Literal(this='; ', is_string=True)]),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=last_name, quoted=False),
          join_mark=False),
        nulls_first=False)]),
  joi
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
--
[tool_use Bash] {"command": "cat sqlglot/parsers/oracle.py | head -80; echo ----; grep -n \"GroupConcat\\|groupconcat\\|TRANSFORMS\\|WithinGroup\" sqlglot/generators/oracle.py; echo ----; sed -n 20,30p sqlglot/parsers/trino.py; sed -n 725,735p sqlglot/parsers/snowflake.py; grep -n \"GroupConcat\" sqlglot/generators/snowflake.py sqlglot/generators/trino.py sqlglot/generators/base*.py sqlglot/generator.py 2>/dev/null; ls sqlglot/generators | head -50", "description": "Inspect Oracle parser and generator"}
[tool_result ERROR] Exit code 1
from __future__ import annotations

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
        return exp.Anony
…[3224 chars elided]…
UNCTION_PARSERS = {
        **parser.Parser.FUNCTION_PARSERS,
        "DATE_PART": lambda self: self._parse_date_part(),
        "DIRECTORY": lambda self: self._parse_directory(),
        "OBJECT_CONSTRUCT_KEEP_NULL": lambda self: self._parse_json_object(),
        "LISTAGG": lambda self: self._parse_string_agg(),
        "SEMANTIC_VIEW": lambda self: self._parse_semantic_view(),
        "SUBSTR": lambda self: self._parse_substring(),
    }
(eval):1: no matches found: sqlglot/generators/base*.py
[tool_use Bash] {"command": "grep -rn \"GroupConcat\" sqlglot/generators/*.py sqlglot/generator.py | head -20; grep -n \"FUNCTION_PARSERS\" sqlglot/parsers/oracle.py", "description": "Locate GroupConcat generator handling and Oracle FUNCTION_PARSERS"}
[tool_result] sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/databricks.py:47:            exp.GroupConcat: groupconcat_sql,
sqlglot/generators/doris.py:60:        exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/clickhouse.py:419:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/duckdb.py:1596:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, within_group=False),
sqlglot/generator
…[947 chars elided]…
ators/tsql.py:53:        # exp.Distinct can appear below an exp.Order or an exp.GroupConcat expression
sqlglot/generators/tsql.py:204:        exp.GroupConcat: _string_agg_sql,
sqlglot/generators/trino.py:28:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, on_overflow=True),
40:    NO_PAREN_FUNCTION_PARSERS = {
41:        **parser.Parser.NO_PAREN_FUNCTION_PARSERS,
54:    FUNCTION_PARSERS = {
55:        **{k: v for k, v in parser.Parser.FUNCTION_PARSERS.items() if k != "CONVERT"},
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/generators/oracle.py; sed -n 60,110p sqlglot/generators/oracle.py; sed -n 338,345p sqlglot/generators/exasol.py; grep -n \"LISTAGG\\|listagg\" tests/dialects/test_oracle.py tests/dialects/test_snowflake.py | head", "description": "View Oracle generator header and TRANSFORMS"}
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
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


class Oracl
…[4458 chars elided]…
, '|SEPARATOR|') WITHIN GROUP (ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5882:                    "duckdb": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|' ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5885:                    "snowflake": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|') WITHIN GROUP (ORDER BY col2) FROM t",
tests/dialects/test_snowflake.py:5886:                    "trino": f"SELECT LISTAGG({distinct}col, '|SEPARATOR|') WITHIN GROUP (ORDER BY col2) FROM t",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON O
…[458 chars elided]…
 duckdb:', e.sql('duckdb'))\n  assert e.sql('oracle')==q, 'roundtrip'\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(a, ',') FROM t\\\", read='mysql', write='oracle'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects 2>&1 | tail -30", "description": "Verify Oracle LISTAGG round-trip and run dialect tests"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 11, in <module>
AssertionError: roundtrip
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
 duckdb: SELECT LISTAGG(last_name, '; ' ORDER BY last_name) FROM employees
[assistant] The `ON OVERFLOW` clause is dropped on output because `groupconcat_sql` only emits it when `on_overflow=True` (only Trino passes that today). Passing it for Oracle:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None),", "new_string": "        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None, on_overflow=True),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON O
…[593 chars elided]…
ckdb:', e.sql('duckdb'))\n  assert e.sql('oracle')==q, 'roundtrip'\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(a, ',') FROM t\\\", read='mysql', write='oracle'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects 2>&1 | tail -30", "description": "Re-verify Oracle LISTAGG round-trip and run dialect tests"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 12, in <module>
AssertionError: roundtrip
SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
 duckdb: SELECT LISTAGG(last_name, '; ' ORDER BY last_name) FROM employees
[assistant] The first input has no explicit count, so the output adds `WITH COUNT` (Oracle's default). That's the expected canonical form, not a bug, so I'll drop that input from the strict round-trip check and run the suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects 2>&1 | tail -30; grep -n \"def test_\\|GROUP_CONCAT\\|LISTAGG\" tests/dialects/test_oracle.py | head -60", "description": "Run dialect tests and list Oracle test names"}
[tool_result] ................................................................................. [ 11%]
............................................................................................................................................ [ 30%]
............................................................ [ 38%]
...................................... [ 43%]
.....................................................................................................................................................
…[679 chars elided]…
_functions(self):
707:    def test_grant(self):
725:    def test_revoke(self):
743:    def test_datetrunc(self):
760:    def test_trunc_type_inference(self):
780:    def test_trunc(self):
846:    def test_analyze(self):
870:    def test_prior(self):
878:    def test_utc_time(self):
884:    def test_merge(self):
899:    def test_merge_builder_alias(self):
913:    def test_pseudocolumns(self):
927:    def test_chr(self):
931:    def test_full_procedure(self):
973:    def test_create_trigger(self):
[assistant] Dialect suite passes (726). Now adding a regression test to the Oracle test file:
[tool_use Bash] {"command": "sed -n 925,932p tests/dialects/test_oracle.py", "description": "View context around test_chr in Oracle tests"}
[tool_result]         )

    def test_chr(self):
        self.validate_identity("SELECT CHR(187 USING NCHAR_CS)")
        self.validate_identity("SELECT CHR(187)")

    def test_full_procedure(self):
        sql = """
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\"SELECT CHR(187)\")\n\n    def test_full_procedure(self):", "new_string": "        self.validate_identity(\"SELECT CHR(187)\")\n\n    def test_listagg(self):\n        self.val
…[1110 chars elided]…
loyees\",\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\",\n        )\n        self.validate_all(\n            \"SELECT GROUP_CONCAT(last_name SEPARATOR '; ') FROM employees\",\n            write={\"oracle\": \"SELECT LISTAGG(last_name, '; ') FROM employees\"},\n        )\n\n    def test_full_procedure(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] The `validate_all` I just added parses its input as Oracle, so a MySQL `GROUP_CONCAT` input would be wrong there. Removing it and verifying that cross-dialect case directly instead:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_all(\n            \"SELECT GROUP_CONCAT(last_name SEPARATOR '; ') FROM employees\",\n            write={\"oracle\": \"SELECT LISTAGG(last_name, '; ') FROM employees\"},\n        )\n\n    def test_full_procedure(self):", "new_string": "\n    def test_full_procedure(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173140-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(a SEPARATOR '; ') FROM t\\\", read='mysql', write='oracle'))\nprint(sqlglot.transpile(\\\"SELECT LISTAGG(a, ';') WITHIN GROUP (ORDER BY a) FROM t\\\", read='oracle', write='snowflake'))\n\" && ~/.cache/lithify-dev/r2-noise-scratc
…[33 chars elided]…
t -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_oracle.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Run full test suite and lint checks"}
[tool_result] ["SELECT LISTAGG(a, '; ') FROM t"]
["SELECT LISTAGG(a, ';') WITHIN GROUP (ORDER BY a) FROM t"]
................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
......................................................
…[426 chars elided]…
.................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 52.25s
All checks passed!
175 files already formatted
[assistant] Oracle now parses `LISTAGG` with the `ON OVERFLOW` clause and round-trips it. The full test suite passes (1094 tests) and `ruff` is clean. I did not commit.

**What changed**

- **`sqlglot/parsers/oracle.py`**: Added `"LISTAGG": lambda self: self._parse_string_agg()` to Oracle's `FUNCTION_PARSERS`. This is the same path Snowflake and Trino use, which already handles `ON OVERFLOW ERROR` and `TRUNCATE '...' [WITH|WITHOUT COUNT]`.
- **`sqlglot/generators/oracle.py`**: Added a `GroupConcat` transform using `groupconcat_sql(self, e, sep=None, on_overflow=True)`. Without this, the parsed node would 
…[432 chars elided]…
pects that canonical form.
- Oracle `LISTAGG` is now parsed into the shared `GroupConcat` node rather than kept as an anonymous function. This also changes cross-dialect output. For example, MySQL `GROUP_CONCAT(a SEPARATOR '; ')` written to Oracle now gives `LISTAGG(a, '; ')`, where it used to give `GROUP_CONCAT`. Dialect-to-dialect output from `LISTAGG` now goes through the shared node, and the existing suite still passes.
- Transpiling to other dialects drops the overflow clause (for example, Oracle to DuckDB). That matches how other dialects already handle it and is not something I changed.
