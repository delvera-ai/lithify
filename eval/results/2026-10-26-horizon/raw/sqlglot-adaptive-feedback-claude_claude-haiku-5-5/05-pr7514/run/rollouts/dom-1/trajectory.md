# trajectory dom-1

final message:
Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full test suite passes (1086 passed), and ruff lint and format are clean. I haven't committed anything.

Your example now parses as `exp.TsOrDsAdd(this='2025-01-01', expression=1, unit='DAY')` in both dialects, and round-trips as `DATE_ADD('2025-01-01', 1)`.

**Changes**
- `sqlglot/dialects/dialect.py`: new shared builder `build_date_delta_with_interval_or_days`. A two-argument call with a non-interval second argument builds `TsOrDsAdd` with a DAY unit. `DATE_SUB` negates the day count, as Hive does. Otherwise it defers to the existing interval builder. Also a shared generator `date_add_days_or_interval_sql`.
- `sqlglot/parsers/doris.py`, `sqlglot/parsers/starrocks.py`: `DATE_ADD` / `DATE_SUB` use the new builder.
- `sqlglot/generators/doris.py`, `sqlglot/generators/starrocks.py`: `TsOrDsAdd` emits the short `DATE_ADD(x, n)` only when the unit is DAY or absent. Other units fall back to `DATE_ADD(x, INTERVAL n UNIT)`.
- Tests in `tests/dialects/test_doris.py` and `tests/dialects/test_starrocks.py`: a new `test_date_add_days` per file. It asserts node classes and the Redshift `DATEADD(month, ...)` / `ADD_MONTHS` transpile.

**A bug I fixed along the way:** Doris's `TsOrDsAdd` transform was unguarded. Redshift `DATEADD(month, 1, x)` and `ADD_MONTHS(x, 2)` were both turning into `DATE_ADD(x, 1)` and `DATE_ADD(x, 2)`, which adds days instead of months. They now emit `INTERVAL 1 MONTH` / `INTERVAL 2 MONTH`.

**Choices to review**
- The new node uses the default `return_type` (DATE), following the Spark precedent. I did not verify whether Doris's `DATE_ADD` returns DATETIME for datetime input. If it does, `return_type` should be set on the node.
- `DATE_SUB(x, n)` comes back as `DATE_ADD(x, -n)`, not `DATE_SUB`. The short form has no subtract spelling, so this is the same result, but the output text differs.

## events
[tool_use Skill] {"skill": "sqlglot-date-arithmetic"}
[tool_result] Launching skill: sqlglot-date-arithmetic
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/.claude/skills/sqlglot-date-arithmetic

# Date arithmetic in sqlglot: which node, and transforms that keep the unit

Use together with `sqlglot-dialect-functions` (canonical-node and parser/generator contract).

## Which node a form parses into (verified in source)
- `DATE_ADD(x, INTERVAL n UNIT)` in the MySQL family → `exp.DateAdd` / `exp.DateSub` via
  `build_date_delta_with_interval` in `sqlglot/dialects/dialect.py`. That builder is what raises
  `ParseE
…[2260 chars elided]…
e new form parses into the node above in every dialect the task names, and the INTERVAL form
  still parses into `DateAdd` / `DateSub`.
- A transpile of Redshift `SELECT DATEADD(month, 1, x), ADD_MONTHS(x, 2)` into each dialect whose
  generator you touched still contains `MONTH`. Compare with the output before your edit; it must
  not lose a unit it used to keep.
- The short-form round-trip and a transpile to one interval-style target (e.g. MySQL or DuckDB)
  appear in the tests, with the node class asserted. If `DATE_SUB(x, n)` comes back as
  `DATE_ADD(x, -n)`, say so in the final message.

[tool_use Bash] {"command": "grep -n -i \"date_add\\|dateadd\\|date_sub\\|DateSub\\|DateAdd\\|TsOrDsAdd\" sqlglot/parsers/doris.py sqlglot/generators/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/dialects/doris.py sqlglot/dialects/starrocks.py sqlglot/dialects/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/mysql.py; ls <work>/env-sqlglot/bin/python", "description": "Locate date_add handling in Doris/StarRocks/MySQL"}
[tool_result] sqlglot/generators/doris.py:75:        exp.TsOrDsAdd: lambda self, e: self.func("DATE_ADD", e.this, e.expression),
sqlglot/generators/doris.py:184:        "date_add",
sqlglot/generators/doris.py:188:        "date_sub",
sqlglot/generators/doris.py:189:        "dateadd",
sqlglot/parsers/mysql.py:114:        "DATE_ADD": build_date_delta_with_interval(exp.DateAdd),
sqlglot/parsers/mysql.py:119:        "DATE_SUB": build_date_delta_with_interval(exp.DateSub),
sqlglot/generators/mysql.py:10:    date_ad
…[365 chars elided]…
lot/generators/mysql.py:196:        exp.TimestampSub: date_add_interval_sql("DATE", "SUB"),
sqlglot/generators/mysql.py:209:        exp.TsOrDsAdd: date_add_sql("ADD"),
sqlglot/generators/mysql.py:742:        dateadd = build_date_delta_with_interval(exp.DateAdd)([start_ts, interval])
sqlglot/generators/mysql.py:744:        return self.sql(dateadd)
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "grep -n \"def build_date_delta_with_interval\" -A 30 sqlglot/dialects/dialect.py; grep -n \"_build_date_add\\|_add_date_sql\\|def _build_dateadd\\|_dateadd_sql\" -A 14 sqlglot/parsers/hive.py sqlglot/generators/hive.py sqlglot/parsers/spark.py sqlglot/generators/spark.py | head -150; echo ---; cat sqlglot/parsers/doris.py | head -80; echo ---; grep -n \"DATE\\|date\" sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py sqlglot/dialects/starrocks.py sqlglot/dialects/doris.py | head -40", "description": "Read date builders and Hive/Spark/Doris/StarRocks code"}
[tool_result] 1599:def build_date_delta_with_interval(
1600-    expression_class: Type[E],
1601-) -> t.Callable[[BuilderArgs], E | None]:
1602-    def _builder(args: BuilderArgs) -> E | None:
1603-        if len(args) < 2:
1604-            return None
1605-
1606-        interval = args[1]
1607-
1608-        if not isinstance(interval, exp.Interval):
1609-            raise ParseError(f"INTERVAL expression expected but got '{interval}'")
1610-
1611-        return expression_class(this=args[0], expression=interv
…[12943 chars elided]…
_DIFF", unit_to_str(e), e.this, e.expression),
sqlglot/generators/starrocks.py:107:        exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
sqlglot/generators/starrocks.py:108:        exp.TimeStrToDate: rename_func("TO_DATE"),
sqlglot/generators/starrocks.py:139:        "current_date",
sqlglot/generators/starrocks.py:258:        "update",
sqlglot/dialects/doris.py:9:    DATE_FORMAT = "'yyyy-MM-dd'"
sqlglot/dialects/doris.py:10:    DATEINT_FORMAT = "'yyyyMMdd'"
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/starrocks.py; echo ---; sed -n 1,20p sqlglot/generators/starrocks.py; sed -n 85,110p sqlglot/generators/starrocks.py; echo ---; sed -n 1,30p sqlglot/generators/doris.py; sed -n 60,80p sqlglot/generators/doris.py; echo ---; sed -n 70,95p sqlglot/generators/mysql.py; sed -n 1,30p sqlglot/dialects/dialect.py | grep -n import; echo ---; grep -rn \"DATE_ADD\\|DATE_SUB\\|date_add\\|date_sub\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py", "description": "Read StarRocks/Doris generator and existing tests"}
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
        "DAT
…[5832 chars elided]…
:from sqlglot.errors import ParseError
15:from sqlglot.generator import Generator, unsupported_args
16:from sqlglot.expressions import apply_index_offset
17:from sqlglot.helper import (
26:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSONPathTokenizer, parse as parse_json_path
27:from sqlglot.parser import Parser
28:from sqlglot.parsers.base import BaseParser
29:from sqlglot.time import TIMEZONES, format_time, subsecond_precision
30:from sqlglot.tokens import Token, Tokenizer, TokenType
---
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(exp.Literal.number(1) * -1), (exp.column('n')*-1).sql())\nfor d in ['doris','starrocks']:\n  for s in [\\\"SELECT DATEADD(month, 1, x)\\\", \\\"SELECT ADD_MONTHS(x, 2)\
…[36 chars elided]…
 1 DAY)\\\"]:\n    try: print(d, sqlglot.transpile(s, read='redshift' if 'DATEADD' in s or 'ADD_MONTHS' in s else d, write=d)[0])\n    except Exception as e: print(d, 'ERR', e)\n\" ; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT DATEADD(month, 1, x)\\\", read='redshift', write='doris'))\" ; git status --short | head", "description": "Probe baseline Doris and StarRocks date output"}
[tool_result] Mul(
  this=Literal(this=1, is_string=False),
  expression=Neg(
    this=Literal(this=1, is_string=False))) n * -1
doris SELECT DATE_ADD(x, 1)
doris SELECT DATE_ADD(x, 2)
doris SELECT DATE_ADD(x, INTERVAL '1' DAY)
starrocks SELECT DATE_ADD(x, INTERVAL 1 MONTH)
starrocks SELECT DATE_ADD(x, INTERVAL 2 MONTH)
starrocks SELECT DATE_ADD(x, INTERVAL '1' DAY)
['SELECT DATE_ADD(x, 1)']
[assistant] Baseline confirms the unguarded Doris transform bug: Redshift `DATEADD(month, 1, x)` and `ADD_MONTHS(x, 2)` both become `DATE_ADD(x, 1)` / `DATE_ADD(x, 2)` in Doris. I'll fix that as part of the generator change. Now the edits.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/dialects/dialect.py", "old_string": "        return expression_class(this=args[0], expression=interval.this, unit=unit_to_str(interval))\n\n    return _builder\n\n\ndef date_trunc_to_time(", "new_string": "        return expression_class(this=args
…[693 chars elided]…
l(expression_class)(args)\n\n    return _builder\n\n\ndef date_add_days_or_interval_sql(self: Generator, expression: exp.TsOrDsAdd) -> str:\n    if not expression.unit or expression.text(\"unit\").upper() == \"DAY\":\n        return self.func(\"DATE_ADD\", expression.this, expression.expression)\n\n    return date_add_interval_sql(\"DATE\", \"ADD\")(self, expression)\n\n\ndef date_trunc_to_time("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/dialects/dialect.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|    date_add_interval_sql\\|    rename_func,\\|^class\\|DATE_ADD\\|DATE_SUB\" sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py | head -40; grep -n \"^from sqlglot.dialects.dialect import\" -A3 sqlglot/parsers/doris.py sqlglot/parsers/starrocks.py", "description": "Check imports in the four dialect files"}
[tool_result] sqlglot/parsers/doris.py:1:from __future__ import annotations
sqlglot/parsers/doris.py:4:from sqlglot import exp
sqlglot/parsers/doris.py:5:from sqlglot.helper import seq_get
sqlglot/parsers/doris.py:6:from sqlglot.parsers.mysql import MySQLParser
sqlglot/parsers/doris.py:7:from sqlglot.tokens import TokenType
sqlglot/parsers/doris.py:26:class DorisParser(MySQLParser):
sqlglot/parsers/starrocks.py:1:from __future__ import annotations
sqlglot/parsers/starrocks.py:4:from sqlglot import exp
sqlglot
…[987 chars elided]…
cts.dialect import (
sqlglot/generators/starrocks.py:8:    rename_func,
sqlglot/generators/starrocks.py:13:from sqlglot.generators.mysql import MySQLGenerator
sqlglot/generators/starrocks.py:54:class StarRocksGenerator(MySQLGenerator):
sqlglot/parsers/starrocks.py:5:from sqlglot.dialects.dialect import build_timestamp_trunc
sqlglot/parsers/starrocks.py-6-from sqlglot.helper import seq_get
sqlglot/parsers/starrocks.py-7-from sqlglot.parsers.mysql import MySQLParser
sqlglot/parsers/starrocks.py-8-
[assistant] Now wiring the parsers and generators for both dialects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/doris.py", "old_string": "from sqlglot import exp\nfrom sqlglot.helper import seq_get", "new_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval_or_days\nfrom sqlglot.helper import seq_get"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/doris.py", "old_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_TRUNC\": _build_date_trunc,", "new_string": "        \"COLLECT_SET\": exp.ArrayUniqueAgg.from_arg_list,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": _build_date_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.dialects.dialect import build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n      
…[169 chars elided]…
build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\n\n\nclass StarRocksParser(MySQLParser):\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"DATE_ADD\": build_date_delta_with_interval_or_days(exp.DateAdd),\n        \"DATE_SUB\": build_date_delta_with_interval_or_days(exp.DateSub),\n        \"DATE_TRUNC\": build_timestamp_trunc,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/doris.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    property_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    date_add_days_or_interval_sql,\n    property_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/doris.py", "old_string": "        exp.TsOrDsAdd: lambda self, e: self.func(\"DATE_ADD\", e.this, e.expression),", "new_string": "        exp.TsOrDsAdd: date_add_days_or_interval_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/starrocks.py", "old_string": "    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,", "new_string": "    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    date_add_days_or_interval_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/starrocks.py", "old_string": "        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),\n        exp.SchemaCommentProperty: lambda self, e: self.naked_property(e),\n        exp.SqlSecurityProperty", "new_string": "        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),\n        exp.SchemaCommentProperty: lambda self, e: self.naked_property(e),\n        exp.SqlSecurityProperty"}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] I need to add the StarRocks `TsOrDsAdd` transform entry (the last edit was a no-op). Adding it after `TimeStrToDate`, then testing.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/starrocks.py", "old_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr", "new_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.TsOrDsAdd: date_add_days_or_interval_sql,\n        exp.UnixToStr"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp, ErrorLevel\nfor d in ['doris','starrocks']:\n  e = sqlglot.parse_one(\\\"select date_add('2025-01-01', 1), date_sub('2025-01-01', 1), date_add('2025-01-01', interval 1 day), da
…[121 chars elided]…
\n  print(' ', e.sql(d))\n  print(' ', e.sql('mysql'))\n  for s in ['SELECT DATEADD(month, 1, x), ADD_MONTHS(x, 2)']:\n    print(' ', sqlglot.transpile(s, read='redshift', write=d)[0])\n\"; $PY -I -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT DATEADD(month, 1, x), ADD_MONTHS(x, 2)', read='redshift', write='mysql'))\"", "description": "Verify parse and generate behavior for both dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores the working directory, so the local package didn't import. Rerunning with `PYTHONPATH` set to the repo.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfrom sqlglot import exp, ErrorLevel\nfor d in ['doris','starrocks']:\n  e = sqlglot.parse_one(\\\"select date_add('2025-01-01', 1), date_sub('2025-01-01', 1), date_add('2025-01-01', interv
…[148 chars elided]…
 e.sql(d))\n  print(' ', e.sql('mysql'))\n  print(' ', sqlglot.transpile('SELECT DATEADD(month, 1, x), ADD_MONTHS(x, 2), DATEADD(day, 3, x)', read='redshift', write=d)[0])\n\"; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT DATEADD(month, 1, x), ADD_MONTHS(x, 2)', read='redshift', write='mysql'))\"", "description": "Verify parse and generate behavior for both dialects"}
[tool_result] doris ['TsOrDsAdd', 'TsOrDsAdd', 'DateAdd', 'TsOrDsAdd']
  SELECT DATE_ADD('2025-01-01', 1), DATE_ADD('2025-01-01', -1), DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_ADD(x, -n) FROM a
  SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_ADD('2025-01-01', INTERVAL -1 DAY), DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_ADD(x, INTERVAL -n DAY) FROM a
  SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH), DATE_ADD(x, 3)
starrocks ['TsOrDsAdd', 'TsOrDsAdd', 'DateAdd', 'TsOrDsAdd']
  SELECT DATE_ADD('2025-01-01', 1), DATE_ADD('2025-01-01', -1), DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_ADD(x, -n) FROM a
  SELECT DATE_ADD('2025-01-01', INTERVAL 1 DAY), DATE_ADD('2025-01-01', INTERVAL -1 DAY), DATE_ADD('2025-01-01', INTERVAL '1' DAY), DATE_ADD(x, INTERVAL -n DAY) FROM a
  SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH), DATE_ADD(x, 3)
['SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)']
[assistant] Parsing and generation behave as intended in both dialects, and the Redshift month/ADD_MONTHS units are now preserved. Next, tests: I'll check the existing structure of the two test files.
[tool_use Bash] {"command": "grep -n \"def test_\\|^class\\|^from\\|^import\" tests/dialects/test_doris.py tests/dialects/test_starrocks.py | head -30; tail -5 tests/dialects/test_doris.py; tail -5 tests/dialects/test_starrocks.py", "description": "Inspect Doris and StarRocks test file structure"}
[tool_result] tests/dialects/test_doris.py:1:from tests.dialects.test_dialect import Validator
tests/dialects/test_doris.py:4:class TestDoris(Validator):
tests/dialects/test_doris.py:7:    def test_doris(self):
tests/dialects/test_doris.py:91:    def test_identity(self):
tests/dialects/test_doris.py:102:    def test_time(self):
tests/dialects/test_doris.py:108:    def test_regex(self):
tests/dialects/test_doris.py:116:    def test_analyze(self):
tests/dialects/test_doris.py:121:    def test_key(self):
tests/d
…[1375 chars elided]…
UTE AS SELECT 1"
        )
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_doris.py <<'EOF'\n\n    def test_date_add_days(self):\n        self.validate_identity(\"SELECT DATE_ADD('2025-01-01', 1)\")\n        self.validate_identity(\"SELECT DATE_SUB(x, n)\", \"SELECT DATE_ADD(x, -n)\")\n        self.validate_identity(\"SELECT DATE_ADD(x, INTERVAL 1 DAY)\", \"SELECT DATE_ADD(x, INTERVAL '1' DAY)\")\n        self.assertIsInstance(pars
…[1440 chars elided]…
THS(x, 2)\", read=\"redshift\", write=\"starrocks\"),\n            [\"SELECT DATE_ADD(x, INTERVAL 1 MONTH), DATE_ADD(x, INTERVAL 2 MONTH)\"],\n        )\nEOF\nsed -i '1s/.*/from sqlglot import exp, parse_one, transpile/' tests/dialects/test_starrocks.py\nhead -3 tests/dialects/test_starrocks.py tests/dialects/test_doris.py", "description": "Append date-add tests to Doris and StarRocks test files"}
[tool_result] sed: 2: "tests/dialects/test_dor ...": undefined label 'ests/dialects/test_doris.py'
sed: 2: "tests/dialects/test_sta ...": undefined label 'ests/dialects/test_starrocks.py'
==> tests/dialects/test_starrocks.py <==
from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator

==> tests/dialects/test_doris.py <==
from tests.dialects.test_dialect import Validator
[assistant] The `sed -i` calls failed on macOS (BSD sed needs `-i ''`), so no files were changed by them. Fixing the imports with the edit tool.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/tests/dialects/test_doris.py", "old_string": "from tests.dialects.test_dialect import Validator", "new_string": "from sqlglot import exp, parse_one, transpile\nfrom tests.dialects.test_dialect import Validator"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/tests/dialects/test_doris.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/tests/dialects/test_starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.errors import UnsupportedError", "new_string": "from sqlglot import exp, parse_one, transpile\nfrom sqlglot.errors import UnsupportedError"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-160938-doris-and-starrocks-dialects-bot/dom-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run Doris/StarRocks tests then full suite"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bhdihx1dp). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "sleep 100; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output | tail -30", "description": "Wait for background test run and read output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output tail -30. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -30", "description": "Run Doris and StarRocks dialect tests", "timeout": 600000}
[tool_result] ......................         [100%]
22 passed, 114 subtests passed in 0.35s
[assistant] Doris and StarRocks tests pass (22 passed). The full suite is still running in the background; I'll wait for it.
[tool_use Monitor] {"command": "until grep -q -E \"passed|failed|error\" /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output 2>/dev/null; do sleep 5; done; tail -15 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output", "description": "Wait for full test suite result", "timeout_ms": 900000}
[tool_result] Monitor started (task bkrq8oppj, expires in 10m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5; $PY -m ruff format --check sqlglot tests/dialects/test_doris.py tests/dialects/test_starrocks.py 2>&1 | tail -5; git diff --stat", "description": "Run ruff lint and format checks on changed files", "timeout": 300000}
[tool_result] All checks passed!
Would reformat: tests/dialects/test_doris.py
Would reformat: tests/dialects/test_starrocks.py
2 files would be reformatted, 173 files already formatted
 sqlglot/dialects/dialect.py      | 23 +++++++++++++++++++++++
 sqlglot/generators/doris.py      |  3 ++-
 sqlglot/generators/starrocks.py  |  2 ++
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 13 +++++++++++++
 tests/dialects/test_starrocks.py | 14 +++++++++++++-
 7 files changed, 59 insertions(+), 3 deletions(-)
[assistant] The monitor's output is the Doris/StarRocks run, not the full suite. I'll check the full-suite background task directly and fix the two formatting issues in the test files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_doris.py tests/dialects/test_starrocks.py && git diff --stat && tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-160938-doris-and-starrocks-dialects-bot-dom-1/2c6e99b0-6856-4847-8af2-21b42e2fef2e/tasks/bhdihx1dp.output", "description": "Format test files and check full-suite output", "timeout": 300000}
[tool_result] 2 files reformatted
 sqlglot/dialects/dialect.py      | 23 +++++++++++++++++++++++
 sqlglot/generators/doris.py      |  3 ++-
 sqlglot/generators/starrocks.py  |  2 ++
 sqlglot/parsers/doris.py         |  3 +++
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_doris.py     | 23 +++++++++++++++++++++++
 tests/dialects/test_starrocks.py | 25 ++++++++++++++++++++++++-
 7 files changed, 80 insertions(+), 3 deletions(-)
......................         [100%]
22 passed, 114 subtests passed in 0.23s
[This command modified 2 files you've previously read: tests/dialects/test_starrocks.py, tests/dialects/test_doris.py. Call Read before editing.]
[assistant] That "changed on disk" notice is just my `ruff format` run, and the diff is limited to the new tests and the import line. Running the full suite in the foreground with a longer timeout.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full sqlglot test suite", "timeout": 600000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
...............................................................................................................................................................................................................................................
…[251 chars elided]…
........................................................... [ 68%]
............................................... [ 73%]
.................................................................................................................................................................................................. [ 90%]
............................... [ 93%]
....................................................................       [100%]
1086 passed, 17844 subtests passed in 101.50s (0:01:41)
[assistant] Doris and StarRocks now parse and generate the two-argument `DATE_ADD` / `DATE_SUB` form. The full test suite passes (1086 passed), and ruff lint and format are clean. I haven't committed anything.

Your example now parses as `exp.TsOrDsAdd(this='2025-01-01', expression=1, unit='DAY')` in both dialects, and round-trips as `DATE_ADD('2025-01-01', 1)`.

**Changes**
- `sqlglot/dialects/dialect.py`: new shared builder `build_date_delta_with_interval_or_days`. A two-argument call with a non-interval second argument builds `TsOrDsAdd` with a DAY unit. `DATE_SUB` negates the day count, as Hive does. 
…[726 chars elided]…
ADD(month, 1, x)` and `ADD_MONTHS(x, 2)` were both turning into `DATE_ADD(x, 1)` and `DATE_ADD(x, 2)`, which adds days instead of months. They now emit `INTERVAL 1 MONTH` / `INTERVAL 2 MONTH`.

**Choices to review**
- The new node uses the default `return_type` (DATE), following the Spark precedent. I did not verify whether Doris's `DATE_ADD` returns DATETIME for datetime input. If it does, `return_type` should be set on the node.
- `DATE_SUB(x, n)` comes back as `DATE_ADD(x, -n)`, not `DATE_SUB`. The short form has no subtract spelling, so this is the same result, but the output text differs.
