# trajectory base-1

final message:
Both dialects now accept the two-argument `DATE_ADD` / `DATE_SUB` form, and your repro parses and round-trips:

```
select date_add('2025-01-01', 1) from a  →  SELECT DATE_ADD('2025-01-01', 1) FROM a
```

The full test suite passes (1086 tests) and `ruff check` and `ruff format --check` are clean.

**What changed**
- **Parsing** (`sqlglot/dialects/dialect.py`, new `build_date_delta_with_days_or_interval`): a two-argument call whose second argument isn't an `INTERVAL` becomes a day-unit `exp.TsOrDsAdd`, the same node Hive and Spark produce. Calls with `INTERVAL` still build `DateAdd` / `DateSub` as before.
- **Wiring** (`sqlglot/parsers/doris.py`, `sqlglot/parsers/starrocks.py`): both parsers register `DATE_ADD` and `DATE_SUB` with this builder. `DATE_SUB` negates the day count.
- **Generation** (`sqlglot/generators/starrocks.py`): StarRocks now emits `TsOrDsAdd` as `DATE_ADD(x, n)`, matching Doris. Before, it emitted the `INTERVAL` form.
- **Tests**: added `test_date_add_sub_days` to `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`.

**Decisions to check**
- `DATE_SUB(x, n)` is written back as `DATE_ADD(x, -n)`, not `DATE_SUB(x, n)`. That's semantically equal and is how Hive's `DATE_SUB` already transpiles. Say if you want the literal `DATE_SUB` form kept on output.
- A compound day count is parenthesized when negated: `DATE_SUB(x, a + 1)` becomes `DATE_ADD(x, -(a + 1))`. My first version dropped the parentheses, which gave `-a + 1`, so I fixed it.
- The MySQL dialect is unchanged, so `DATE_ADD(x, 1)` still fails there. Only Doris and StarRocks were in scope.

I haven't run these against a live Doris or StarRocks instance, so the 2-argument form is confirmed only from the parser and generator outputs, not from the databases. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"DATE_ADD\\|DateAdd\\|DATE_SUB\\|DateSub\\|date_add\\|date_sub\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py; grep -n \"class DateAdd\\|class DateSub\\|class TsOrDsAdd\\|class DateTrunc\" sqlglot/expressions.py", "description": "Find date_add handling in dialect files"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"DateAdd\\|DateSub\\|DATE_SUB\\|DATE_ADD\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py", "description": "Locate date_add handling in Doris, StarRocks, MySQL"}
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
[tool_use Bash] {"command": "grep -rn \"DateAdd\\|DateSub\\|DATE_SUB\\|DATE_ADD\\|date_add\\|date_sub\" sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/parsers/ sqlglot/generators/ sqlglot/dialects/dialect.py | head -60; cat sqlglot/dialects/doris.py; cat sqlglot/dialects/starrocks.py", "description": "Search date_add handling and read Doris/StarRocks dialects"}
[tool_result] sqlglot/parsers/clickhouse.py:271:        "DATE_ADD": build_date_delta(exp.DateAdd, default_unit=None),
sqlglot/parsers/clickhouse.py:272:        "DATEADD": build_date_delta(exp.DateAdd, default_unit=None),
sqlglot/parsers/clickhouse.py:276:        "DATE_SUB": build_date_delta(exp.DateSub, default_unit=None),
sqlglot/parsers/clickhouse.py:277:        "DATESUB": build_date_delta(exp.DateSub, default_unit=None),
sqlglot/parsers/redshift.py:44:        "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
s
…[5466 chars elided]…
ations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.starrocks import StarRocksGenerator
from sqlglot.parsers.starrocks import StarRocksParser
from sqlglot.tokens import TokenType


class StarRocks(MySQL):
    STRICT_JSON_PATH_SYNTAX = False
    INDEX_OFFSET = 1

    class Tokenizer(MySQL.Tokenizer):
        KEYWORDS = {
            **MySQL.Tokenizer.KEYWORDS,
            "LARGEINT": TokenType.INT128,
        }

    Parser = StarRocksParser

    Generator = StarRocksGenerator
[tool_use Bash] {"command": "cat sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py; sed -n 95,130p sqlglot/parsers/mysql.py; grep -n \"def build_date_delta_with_interval\" -A25 sqlglot/parsers/*.py sqlglot/dialects/dialect.py sqlglot/*.py | head -60", "description": "Read Doris/StarRocks parser/generator and MySQL date parsing"}
[tool_result] <persisted-output>
Output too large (37.7KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-d5521a213087-20261028-164006-doris-and-starrocks-dialects-bot-base-1/2201b939-7a05-4dfa-8733-b0b20f8b8030/tool-results/b76masz4c.txt

Preview (first 2KB):
from __future__ import annotations


from sqlglot import exp
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser
from sqlglot.tokens import TokenType


# Accept both DATE_TRUNC
…[1304 chars elided]…
       "UNIQUE": lambda self: self._parse_composite_key_property(exp.UniqueKeyProperty),
        # Plain KEY without UNIQUE/DUPLICATE/AGGREGATE prefixes should be treated as UniqueKeyProperty with unique=False
        "KEY": lambda self: self._parse_composite_key_property(exp.UniqueKeyProperty),
        "BUILD": lambda self: self._parse_build_property(),
        "REFRESH": lambda self: self._parse_refresh_property(),
    }

    def _parse_partition_property(
        self,
...
</persisted-output>
[tool_use Bash] {"command": "cat sqlglot/generators/doris.py | head -150; echo ----; cat sqlglot/generators/starrocks.py | head -80; echo ----; grep -n \"build_date_delta_with_interval\\|def date_add_sql\\|def date_add_interval_sql\" -A22 sqlglot/dialects/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py | head -150", "description": "Read Doris/StarRocks generators and MySQL date helpers"}
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
        
…[14618 chars elided]…
om_arg_list,
sqlglot/parsers/mysql.py-136-        "STR_TO_DATE": _str_to_date,
sqlglot/parsers/mysql.py-137-        "TIMESTAMPDIFF": build_date_delta(exp.TimestampDiff),
sqlglot/parsers/mysql.py-138-        "TO_DAYS": lambda args: exp.paren(
sqlglot/parsers/mysql.py-139-            exp.DateDiff(
sqlglot/parsers/mysql.py-140-                this=exp.TsOrDsToDate(this=seq_get(args, 0)),
sqlglot/parsers/mysql.py-141-                expression=exp.TsOrDsToDate(this=exp.Literal.string("0000-01-01")),
[tool_use Bash] {"command": "grep -rn \"def build_date_delta_with_interval\" -A25 sqlglot/ | head -45; sed -n 28,45p sqlglot/parsers/hive.py; grep -rn \"class TsOrDsAdd\" -A12 sqlglot/expressions/; grep -rn \"TsOrDsAdd\" sqlglot/generators/mysql.py sqlglot/generators/starrocks.py sqlglot/generators/doris.py sqlglot/generator.py; grep -n \"date_add\\|DATE_ADD\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_mysql.py", "description": "Inspect delta helper, TsOrDsAdd, and existing tests"}
[tool_result] sqlglot/dialects/dialect.py:1599:def build_date_delta_with_interval(
sqlglot/dialects/dialect.py-1600-    expression_class: Type[E],
sqlglot/dialects/dialect.py-1601-) -> t.Callable[[BuilderArgs], E | None]:
sqlglot/dialects/dialect.py-1602-    def _builder(args: BuilderArgs) -> E | None:
sqlglot/dialects/dialect.py-1603-        if len(args) < 2:
sqlglot/dialects/dialect.py-1604-            return None
sqlglot/dialects/dialect.py-1605-
sqlglot/dialects/dialect.py-1606-        interval = args[1]

…[3387 chars elided]…
AL (2 * 2) MONTH) FROM foo",
tests/dialects/test_mysql.py:1460:                        f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1465:                            "mysql": f"DATE_ADD('0000-01-01 00:00:00', INTERVAL (TIMESTAMPDIFF({unit}, '0000-01-01 00:00:00', {cast})) {unit})",
tests/dialects/test_mysql.py:1618:                self.validate_identity(f"DATE_ADD(base_date, INTERVAL day_interval {unit})")
[tool_use Bash] {"command": "ls sqlglot/parsers/ | grep -i \"star\\|doris\"; sed -n 1,12p sqlglot/parsers/starrocks.py; grep -n \"FUNCTIONS\" -A12 sqlglot/parsers/starrocks.py | head -30; sed -n 36,60p sqlglot/parsers/spark.py; sed -n 30,42p sqlglot/generators/spark.py; grep -rn \"\\\"doris\\\"\\|\\\"starrocks\\\"\" tests/dialects/*.py | grep -i \"date_add\\|DATE_ADD\\|date_sub\\|DATE_SUB\\|TsOrDs\" | head; grep -rln \"starrocks\\|doris\" tests/ | head -20", "description": "Inspect StarRocks parser, Spark date_add, and tests referencing these dialects"}
[tool_result] doris.py
starrocks.py
from __future__ import annotations


from sqlglot import exp
from sqlglot.dialects.dialect import build_timestamp_trunc
from sqlglot.helper import seq_get
from sqlglot.parsers.mysql import MySQLParser


class StarRocksParser(MySQLParser):
    FUNCTIONS = {
        **MySQLParser.FUNCTIONS,
11:    FUNCTIONS = {
12:        **MySQLParser.FUNCTIONS,
13-        "DATE_TRUNC": build_timestamp_trunc,
14-        "DATEDIFF": lambda args: exp.DateDiff(
15-            this=seq_get(args,
…[2147 chars elided]…
alects/test_doris.py
tests/dialects/test_snowflake.py
tests/dialects/test_oracle.py
tests/dialects/test_redshift.py
tests/dialects/test_bigquery.py
tests/dialects/test_starrocks.py
tests/dialects/test_presto.py
tests/dialects/test_duckdb.py
tests/dialects/test_teradata.py
tests/dialects/test_mysql.py
tests/dialects/test_spark.py
tests/dialects/test_hive.py
tests/dialects/test_postgres.py
tests/dialects/test_dialect.py
tests/dialects/test_clickhouse.py
tests/fixtures/optimizer/qualify_columns.sql
[tool_use Bash] {"command": "sed -n 1055,1095p tests/dialects/test_dialect.py; grep -n \"DATE_ADD\\|DATE_SUB\\|date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py; ls <work>/env-sqlglot/bin/python && git status --short | head", "description": "Check existing date_add tests for both dialects"}
[tool_result]             write={
                "bigquery": "DATE_ADD(x, INTERVAL 1 DAY)",
                "drill": "DATE_ADD(x, INTERVAL 1 DAY)",
                "duckdb": "x + INTERVAL 1 DAY",
                "hive": "DATE_ADD(x, 1)",
                "materialize": "x + INTERVAL '1 DAY'",
                "mysql": "DATE_ADD(x, INTERVAL 1 DAY)",
                "postgres": "x + INTERVAL '1 DAY'",
                "presto": "DATE_ADD('DAY', 1, x)",
                "snowflake": "DATEADD(DAY, 1, x)",
          
…[761 chars elided]…
arrocks": "DATE_ADD(x, INTERVAL 1 DAY)",
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
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['', 'doris','starrocks','mysql','hive']:\n    for s in ['DATE_ADD(x, 1)','DATE_SUB(x, 1)','DATE_ADD(x, INTERVAL 1 DAY)']:\n        try:\n            e = sqlglot.parse_one(s, read=d or None)\n            print(repr(d), s, '->', type(e).__name__, '|
…[51 chars elided]…
sql('hive'))\n        except Exception as ex: print(repr(d), s, 'ERR', ex)\n\" 2>&1 | head -40; sed -n 1,30p sqlglot/parsers/starrocks.py >/dev/null; grep -n \"DATE_ADD\\|DATE_SUB\" sqlglot/parser.py sqlglot/parsers/base*.py 2>/dev/null | head; grep -rn '\"DATE_ADD\"' sqlglot/parsers/parser*.py sqlglot/parser.py 2>/dev/null", "description": "Probe current parse and generate behavior for date_add"}
[tool_result] '' DATE_ADD(x, 1) -> DateAdd | DATE_ADD(x, INTERVAL 1 DAY) | DATE_ADD(x, INTERVAL 1 DAY) | DATE_ADD(x, 1)
'' DATE_SUB(x, 1) -> DateSub | DATE_SUB(x, INTERVAL 1 DAY) | DATE_SUB(x, INTERVAL 1 DAY) | DATE_ADD(x, -1)
'' DATE_ADD(x, INTERVAL 1 DAY) -> DateAdd | DATE_ADD(x, INTERVAL (INTERVAL '1' DAY) DAY) | DATE_ADD(x, INTERVAL (INTERVAL '1' DAY) DAY) | DATE_ADD(x, INTERVAL '1' DAY)
'doris' DATE_ADD(x, 1) ERR INTERVAL expression expected but got '1'
'doris' DATE_SUB(x, 1) ERR INTERVAL expression expe
…[614 chars elided]…
(x, INTERVAL '1' DAY) | DATE_ADD(x, INTERVAL '1' DAY) | DATE_ADD(x, 1)
'hive' DATE_ADD(x, 1) -> TsOrDsAdd | DATE_ADD(x, 1) | DATE_ADD(x, INTERVAL 1 DAY) | DATE_ADD(x, 1)
'hive' DATE_SUB(x, 1) -> TsOrDsAdd | DATE_ADD(x, 1 * -1) | DATE_ADD(x, INTERVAL (1 * -1) DAY) | DATE_ADD(x, 1 * -1)
'hive' DATE_ADD(x, INTERVAL 1 DAY) -> TsOrDsAdd | DATE_ADD(x, INTERVAL '1' DAY) | DATE_ADD(x, INTERVAL (INTERVAL '1' DAY) DAY) | DATE_ADD(x, INTERVAL '1' DAY)
(eval):10: no matches found: sqlglot/parsers/parser*.py
[tool_use Bash] {"command": "grep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/starrocks.py; grep -n \"exp.TimestampTrunc\\|exp.TsOrDs\\|exp.DateTrunc\" sqlglot/generators/starrocks.py; sed -n 1,12p sqlglot/parsers/doris.py >/dev/null; grep -n \"^from\\|^import\\|^BuilderArgs\\|^E = \" sqlglot/dialects/dialect.py | head -30; grep -n \"build_date_delta_with_interval\" sqlglot/parsers/*.py | head -3", "description": "Check StarRocks TRANSFORMS and dialect.py imports"}
[tool_result] 88:    TRANSFORMS = {
89-        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
90-        exp.Array: inline_array_sql,
91-        exp.ArrayAgg: rename_func("ARRAY_AGG"),
89:        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},
107:        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
1:from __future__ import annotations
3:import importlib
4:import logging
5:import typing as t
6:import s
…[629 chars elided]…
port TIMEZONES, format_time, subsecond_precision
30:from sqlglot.tokens import Token, Tokenizer, TokenType
31:from sqlglot.trie import new_trie
32:from sqlglot.typing import EXPRESSION_METADATA
34:from importlib.metadata import entry_points
sqlglot/parsers/bigquery.py:9:    build_date_delta_with_interval,
sqlglot/parsers/bigquery.py:189:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/bigquery.py:191:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164006-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=arg
…[313 chars elided]…
ss)\n\n    def _builder(args: BuilderArgs) -> E | exp.TsOrDsAdd | None:\n        if len(args) == 2 and not isinstance(args[1], exp.Interval):\n            days = exp.Neg(this=args[1]) if negate else args[1]\n            return exp.TsOrDsAdd(this=args[0], expression=days, unit=exp.Literal.string(\"DAY\"))\n\n        return interval_builder(args)\n\n    return _builder\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164006-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now wire it into both parsers and add the StarRocks generator entry to match Doris.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/doris.py'\ns=open(p).read()\ns=s.replace('from sqlglot import exp\\nfrom sqlglot.helper import seq_get\\n','from sqlglot import exp\\nfrom sqlglot.dialects.dialect import build_date_delta_with_days_or_interval\\nfrom sqlglot.helper import seq_get\\n',1)\ns=s.replace('        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\\n','      
…[1453 chars elided]…
sub(x, a + 1)','select date_add(x, INTERVAL 1 DAY)']:\n    e=sqlglot.parse_one(s, read=d)\n    print(d, '|', e.sql(d), '|', e.sql('hive'), '|', e.sql('mysql'))\nprint(sqlglot.transpile(\\\"DATE_ADD(x, 1)\\\", read='hive', write='starrocks'))\nprint(sqlglot.transpile(\\\"DATE_SUB(x, 1)\\\", read='hive', write='doris'))\n\"", "description": "Wire parsers, add StarRocks generator, and probe outputs"}
[tool_result]  sqlglot/dialects/dialect.py     | 15 +++++++++++++++
 sqlglot/generators/starrocks.py |  1 +
 sqlglot/parsers/doris.py        |  3 +++
 sqlglot/parsers/starrocks.py    |  4 +++-
 4 files changed, 22 insertions(+), 1 deletion(-)
doris | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT DATE_ADD('2025-01-01', 1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
doris | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT DATE_ADD('2025-01-01', IN
…[301 chars elided]…
_ADD('2025-01-01', 1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY) FROM a
starrocks | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT DATE_ADD('2025-01-01', -1) FROM a | SELECT DATE_ADD('2025-01-01', INTERVAL -1 DAY) FROM a
starrocks | SELECT DATE_ADD(x, -a + 1) | SELECT DATE_ADD(x, -a + 1) | SELECT DATE_ADD(x, INTERVAL -a + 1 DAY)
starrocks | SELECT DATE_ADD(x, INTERVAL '1' DAY) | SELECT DATE_ADD(x, 1) | SELECT DATE_ADD(x, INTERVAL '1' DAY)
['DATE_ADD(x, 1)']
['DATE_ADD(x, 1 * -1)']
[assistant] Negation drops parentheses on compound arguments (`DATE_SUB(x, a + 1)` became `-a + 1`, which is wrong). Let me check how the generator handles a parenthesized operand.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import exp, parse_one\nfor s in ['a + 1','1','col','f(x)','a * b']:\n    e=parse_one(s)\n    print(s, '|', exp.Neg(this=exp.paren(e.copy())).sql('doris'), '|', exp.Neg(this=e.copy()).sql('doris'), '|', exp.Mul(this=e.copy(), expression=exp.Literal.number(-1)).sql('doris'))\n\"", "description": "Compare negation rendering for compound operands"}
[tool_result] a + 1 | -(a + 1) | -a + 1 | a + 1 * -1
1 | -(1) | -1 | 1 * -1
col | -(col) | -col | col * -1
f(x) | -(F(x)) | -F(x) | F(x) * -1
a * b | -(a * b) | -a * b | a * b * -1
[assistant] Wrapping only binary operands keeps simple cases clean and fixes the precedence bug.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-164006-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py", "old_string": "            days = exp.Neg(this=args[1]) if negate else args[1]", "new_string": "            days = args[1]\n            if negate:\n                days = exp.Neg(this=exp.paren(days) if isinstance(days, exp.Binary) else days)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-164006-doris-and-starrocks-dialects-bot/base-1/sqlglot/dialects/dialect.py has been updated successfully.
[assistant] Now I'll add tests to the Doris and StarRocks test files, then run the probe and the suite.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -30; sed -n 1,25p tests/dialects/test_starrocks.py", "description": "Look at Doris and StarRocks test structure"}
[tool_result] tests/dialects/test_doris.py:7:    def test_doris(self):
tests/dialects/test_doris.py:91:    def test_identity(self):
tests/dialects/test_doris.py:102:    def test_time(self):
tests/dialects/test_doris.py:108:    def test_regex(self):
tests/dialects/test_doris.py:116:    def test_analyze(self):
tests/dialects/test_doris.py:121:    def test_key(self):
tests/dialects/test_doris.py:126:    def test_distributed(self):
tests/dialects/test_doris.py:135:    def test_partition(self):
tests/dialects/test
…[1304 chars elided]…

        self.validate_identity("SELECT ARRAY_AGG(a) FROM x")
        self.validate_identity("SELECT ST_POINT(10, 20)")
        self.validate_identity("SELECT ST_DISTANCE_SPHERE(10.1, 20.2, 30.3, 40.4)")
        self.validate_identity("ARRAY_FLATTEN(arr)").assert_is(exp.Flatten)

        self.validate_all(
            "SELECT * FROM t WHERE cond",
            read={
                "": "SELECT * FROM t WHERE cond IS TRUE",
                "starrocks": "SELECT * FROM t WHERE cond",
            },
[tool_use Bash] {"command": "python3 - <<'EOF'\nfor path, name in [('tests/dialects/test_doris.py','doris'),('tests/dialects/test_starrocks.py','starrocks')]:\n    s=open(path).read()\n    anchor='    def test_time(self):\\n'\n    assert s.count(anchor)==1, path\n    new=f'''    def test_date_add_sub_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(
…[800 chars elided]…
n        )\n\n'''\n    s=s.replace(anchor,new+anchor,1)\n    open(path,'w').write(s)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_dialect.py 2>&1 | tail -30", "description": "Add date_add/date_sub tests and run dialect test files"}
[tool_result] tests/dialects/test_doris.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/dialects/test_dialect.py:63: in validate_identity
    self.assertEqual(
E   AssertionError: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
_____________________ TestStarrocks.test_date_add_sub_days _____________________

sel
…[528 chars elided]…
Error: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
=========================== short test summary info ============================
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days - Asse...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days
2 failed, 118 passed, 2929 subtests passed in 0.60s
[assistant] That failure was my test's mistake (the INTERVAL form normalizes the literal to `'1'`, which existing tests already cover). Removing that line.
[tool_use Bash] {"command": "for f in tests/dialects/test_doris.py tests/dialects/test_starrocks.py; do sed -i '/validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\")/d' $f; done; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py tests/dialects/test_dialect.py 2>&1 | tail -3; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse('select date_add(\\'2025-01-01\\', 1) from a', dialect='doris', error_level=sqlglot.ErrorLevel.IMMEDIATE)[0].sql('doris'))\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Fix test line, run dialect tests, the repro, and full suite"}
[tool_result] sed: 2: "tests/dialects/test_dor ...": undefined label 'ests/dialects/test_doris.py'
sed: 2: "tests/dialects/test_sta ...": undefined label 'ests/dialects/test_starrocks.py'
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days - Asse...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days
2 failed, 118 passed, 2929 subtests passed in 0.49s
SELECT DATE_ADD('2025-01-01', 1) FROM a
        self.validate_identity("SELECT DATE_ADD(x, -1)")
>       self.vali
…[267 chars elided]…
or: 'SELECT DATE_ADD(x, INTERVAL 1 DAY)' != "SELECT DATE_ADD(x, INTERVAL '1' DAY)"
E   - SELECT DATE_ADD(x, INTERVAL 1 DAY)
E   + SELECT DATE_ADD(x, INTERVAL '1' DAY)
E   ?                             + +
=========================== short test summary info ============================
FAILED tests/dialects/test_doris.py::TestDoris::test_date_add_sub_days - Asse...
FAILED tests/dialects/test_starrocks.py::TestStarrocks::test_date_add_sub_days
2 failed, 1084 passed, 17844 subtests passed in 48.69s
[assistant] The `sed -i` call failed on macOS (BSD sed needs an argument after `-i`), so the bad line is still there. I'll remove it with Python instead.
[tool_use Bash] {"command": "python3 - <<'EOF'\nfor p in ['tests/dialects/test_doris.py','tests/dialects/test_starrocks.py']:\n    s=open(p).read()\n    line='        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\")\\n'\n    assert s.count(line)==1, p\n    open(p,'w').write(s.replace(line,''))\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m ruff check sqlglot tests 2>&1 | tail -2; $PY -m ruff format --check sqlglot tests 2>&1 | tail -3; git status --short", "description": "Remove bad test line and run full suite plus lint"}
[tool_result] .......................................................................... [ 99%]
......                                                                   [100%]
1086 passed, 17856 subtests passed in 48.63s
All checks passed!
233 files already formatted
 M sqlglot/dialects/dialect.py
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/doris.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_doris.py
 M tests/dialects/test_starrocks.py
[assistant] Both dialects now accept the two-argument `DATE_ADD` / `DATE_SUB` form, and your repro parses and round-trips:

```
select date_add('2025-01-01', 1) from a  →  SELECT DATE_ADD('2025-01-01', 1) FROM a
```

The full test suite passes (1086 tests) and `ruff check` and `ruff format --check` are clean.

**What changed**
- **Parsing** (`sqlglot/dialects/dialect.py`, new `build_date_delta_with_days_or_interval`): a two-argument call whose second argument isn't an `INTERVAL` becomes a day-unit `exp.TsOrDsAdd`, the same node Hive and Spark produce. Calls with `INTERVAL` still build `DateAdd` / `DateSub
…[597 chars elided]…
l and is how Hive's `DATE_SUB` already transpiles. Say if you want the literal `DATE_SUB` form kept on output.
- A compound day count is parenthesized when negated: `DATE_SUB(x, a + 1)` becomes `DATE_ADD(x, -(a + 1))`. My first version dropped the parentheses, which gave `-a + 1`, so I fixed it.
- The MySQL dialect is unchanged, so `DATE_ADD(x, 1)` still fails there. Only Doris and StarRocks were in scope.

I haven't run these against a live Doris or StarRocks instance, so the 2-argument form is confirmed only from the parser and generator outputs, not from the databases. Nothing is committed.
