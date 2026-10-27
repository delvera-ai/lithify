# trajectory base-1

final message:
Druid now parses and round-trips `JSON_VALUE(x, '$.a' RETURNING BIGINT)` unchanged. The full suite passes (1121 passed) with the project's interpreter.

**Cause:** `JSON_VALUE` was only wired to `_parse_json_value` in the MySQL, Trino and Exasol parsers. Druid's parser inherited the base function parsing, which doesn't handle `RETURNING`.

**Change:**
- `sqlglot/parsers/druid.py`: `DruidParser` now registers `"JSON_VALUE": lambda self: self._parse_json_value()` in `FUNCTION_PARSERS`, the same way MySQL, Trino and Exasol do. The generator needed no change, since the shared `jsonvalue_sql` already emits `RETURNING`.
- `tests/dialects/test_druid.py`: added `validate_identity` cases for `JSON_VALUE(x, '$.a')` and the `RETURNING BIGINT` form from the report.

I kept this in the Druid parser rather than the base parser. Base-level registration would change `JSON_VALUE` for every dialect, including ones like BigQuery that define their own `JSON_VALUE` handling.

Not committed. The change is in the working tree for you to review.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-101900-druid-dialect-the-returning-type/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn \"RETURNING\" sqlglot/parsers/mysql.py sqlglot/parsers/trino.py sqlglot/parsers/exasol.py sqlglot/parsers/druid.py sqlglot/generators/mysql.py sqlglot/generators/trino.py sqlglot/generators/exasol.py sqlglot/generators/druid.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/json.py 2>/dev/null; ls sqlglot/parsers/ | head -50; ls sqlglot/dialects | grep -i druid", "description": "Load skill and search RETURNING handling across dialects"}
[tool_result] sqlglot/parser.py:3497:        returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:        if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:            elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:        by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8088:        return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10036:  
…[895 chars elided]…
se ""
sqlglot/generator.py:5953:        by_ref = f"{self.sep()}RETURNING SEQUENCE BY REF" if expression.args.get("by_ref") else ""
__init__.py
athena.py
base.py
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
druid.py
[tool_use Bash] {"command": "sed -n 8070,8110p sqlglot/parser.py; grep -n \"JSONValue\\|JSON_VALUE\" sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generator.py sqlglot/generators/*.py sqlglot/dialects/druid.py sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py | head -40; grep -n \"class JSONValue\" -A 12 sqlglot/expressions/json.py; python3 -c \"\nimport sqlglot\nfor d in ['mysql','trino','exasol','druid']:\n    try: print(d, sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read=d, write=d))\n    except Exception as e: print(d, 'ERR', e)\n\"", "description": "Inspect JSON_VALUE parsing and test dialects"}
[tool_result]     def _parse_json_object(self, agg=False):
        star = self._parse_star()
        expressions = (
            [star]
            if star
            else self._parse_csv(lambda: self._parse_format_json(self._parse_json_key_value()))
        )
        null_handling = self._parse_on_handling("NULL", "NULL", "ABSENT")

        unique_keys = None
        if self._match_text_seq("WITH", "UNIQUE"):
            unique_keys = True
        elif self._match_text_seq("WITHOUT", "UNIQUE"):
            
…[3299 chars elided]…
db.py:4634:                this=rename_func("JSON_VALUE")(self, expression), expression="'$'"
sqlglot/generators/tsql.py:104:    json_value = self.func("JSON_VALUE", expression.this, expression.expression)
mysql ["SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`) FROM t"]
trino ["SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t"]
exasol ['SELECT JSON_VALUE(x, \'$.a\' RETURNING "BIGINT") FROM t']
druid ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT) FROM t
[tool_use Bash] {"command": "cat sqlglot/parsers/druid.py 2>/dev/null; cat sqlglot/dialects/druid.py; sed -n 10025,10050p sqlglot/parser.py; sed -n 5528,5542p sqlglot/generator.py; sed -n 1,40p sqlglot/parsers/trino.py | grep -n \"class\\|JSON\"; grep -n \"JSON\" tests/dialects/test_druid.py | head; grep -n \"json_value\\|JSON_VALUE\" tests/dialects/test_mysql.py tests/dialects/test_trino.py | head", "description": "Read Druid dialect and JSON_VALUE tests"}
[tool_result] from __future__ import annotations

from sqlglot.parser import Parser


class DruidParser(Parser):
    pass
from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator

        if exp_class == exp.TryCast:
            kwargs["requires_string"] = self.dialect.TRY_CAST_REQUIRES_STRING

        return self.expression(exp_class(**kwargs))
…[2175 chars elided]…
_option} ON ERROR) AS price"""
tests/dialects/test_mysql.py:1557:    def test_json_value(self):
tests/dialects/test_mysql.py:1559:        self.validate_identity(f"""SELECT JSON_VALUE({json_doc}, '$.price')""")
tests/dialects/test_mysql.py:1561:            f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_mysql.py:1566:                f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
[tool_use Bash] {"command": "cat sqlglot/generators/druid.py; sed -n 1,25p sqlglot/parsers/trino.py; ls tests/dialects | grep -i druid; cat tests/dialects/test_druid.py 2>/dev/null | head -60; sed -n 1,20p sqlglot/parsers/exasol.py | grep -n import", "description": "Read Druid generator and Trino parser pattern"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # https://druid.apache.org/docs/latest/querying/sql-data-types/
    TYPE_MAPPING = {
        **generator.Generator.TYPE
…[1805 chars elided]…
entity("SELECT CURRENT_TIMESTAMP")
        self.validate_identity("SELECT ARRAY[1, 2, 3]")

        # validate across all dialects
        write = {dialect.value: "FLOOR(__time TO WEEK)" for dialect in Dialects}
        self.validate_all(
            "FLOOR(__time TO WEEK)",
            write=write,
        )
1:from __future__ import annotations
4:from sqlglot import exp, parser
5:from sqlglot.dialects.dialect import (
12:from sqlglot.helper import seq_get
13:from sqlglot.tokens import TokenType
[tool_use Bash] {"command": "cat > sqlglot/parsers/druid.py <<'EOF'\nfrom __future__ import annotations\n\nfrom sqlglot.parser import Parser\n\n\nclass DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }\nEOF\npython3 - <<'EOF'\nimport sqlglot\nq=\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\"\nprint(sqlg
…[117 chars elided]…
GINT DEFAULT 1 ON EMPTY) FROM t\", read=\"druid\", write=\"druid\"))\nprint(sqlglot.transpile(\"SELECT JSON_VALUE(x, '$.a') FROM t\", read=\"druid\", write=\"druid\"))\nEOF\nls <work>/env-sqlglot/bin/python", "description": "Add JSON_VALUE parser to Druid and check round-trip"}
[tool_result] ["SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t"]
["SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT DEFAULT 1 ON EMPTY) FROM t"]
["SELECT JSON_VALUE(x, '$.a') FROM t"]
<work>/env-sqlglot/bin/python
[assistant] Round-trip works. Now I'll add a test next to the existing Druid identities and run the suite with the project's interpreter.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101900-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a')\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101900-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Druid and related dialect tests"}
[tool_result] .......................................................... [ 73%]
.... [ 78%]
.................                                            [100%]
79 passed, 1102 subtests passed in 0.42s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 58.59s
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses and round-trips `JSON_VALUE(x, '$.a' RETURNING BIGINT)` unchanged. The full suite passes (1121 passed) with the project's interpreter.

**Cause:** `JSON_VALUE` was only wired to `_parse_json_value` in the MySQL, Trino and Exasol parsers. Druid's parser inherited the base function parsing, which doesn't handle `RETURNING`.

**Change:**
- `sqlglot/parsers/druid.py`: `DruidParser` now registers `"JSON_VALUE": lambda self: self._parse_json_value()` in `FUNCTION_PARSERS`, the same way MySQL, Trino and Exasol do. The generator needed no change, since the shared `jsonvalue_sql` already emits `RETURNING`.
- `tests/dialects/test_druid.py`: added `validate_identity` cases for `JSON_VALUE(x, '$.a')` and the `RETURNING BIGINT` form from the report.

I kept this in the Druid parser rather than the base parser. Base-level registration would change `JSON_VALUE` for every dialect, including ones like BigQuery that define their own `JSON_VALUE` handling.

Not committed. The change is in the working tree for you to review.
