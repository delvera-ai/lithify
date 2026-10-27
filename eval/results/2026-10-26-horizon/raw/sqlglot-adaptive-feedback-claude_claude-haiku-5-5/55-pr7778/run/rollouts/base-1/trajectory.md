# trajectory base-1

final message:
Trino's `FROM_ISO8601_DATE` now parses to a typed node and transpiles to `CAST(... AS DATE)` in other dialects. Week and ordinal date inputs still don't match Trino, and I left that open on purpose.

**What changed** (4 files, uncommitted):
- `sqlglot/expressions/temporal.py`: new `exp.FromISO8601Date` class, mirroring `FromISO8601Timestamp`.
- `sqlglot/generator.py`: base `fromiso8601date_sql` emits `CAST(x AS DATE)`. This is the same pattern the recent `FROM_ISO8601_TIMESTAMP` commit used.
- `sqlglot/generators/presto.py`: `rename_func("FROM_ISO8601_DATE")`, so Presto and Trino round-trip.
- `tests/dialects/test_presto.py`: asserts the node class, the Trino/Presto round-trip, and the DuckDB, Snowflake, Spark and BigQuery outputs.

**Results:**
- Node: `Anonymous` before, `FromISO8601Date` now.
- Trino → Trino and Trino → Presto: `SELECT FROM_ISO8601_DATE('2020-05-11')`.
- Trino → DuckDB, Snowflake, Spark, BigQuery: `SELECT CAST('2020-05-11' AS DATE)`.
- DuckDB executes the cast output for `2020-05-11`, `2020-02-29` and `2020-05-11 ` and returns the correct dates.
- `tests/dialects/test_presto.py` and `test_trino.py`: 27 passed.
- Full suite: `SUMMARY: 1122 passed, 18190 subtests passed in 54.00s` and `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on the changed files.

**Remaining gap:** Trino's ISO 8601 parser also accepts week dates (`2020-W19-1`) and ordinal dates (`2020-132`). DuckDB's `CAST ... AS DATE` rejects both, so those inputs would return a different result or an error after transpiling. I did not handle this because doing it correctly needs per-engine logic beyond the plain cast you asked for. Tell me if you want that covered. I have not checked the Trino side against a live server; the week/ordinal behavior comes from Trino's documented ISO 8601 support.

I did not commit, since you didn't ask for one.

## events
[assistant] I'll start by reading the skill that matches this task, then the existing Trino code.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md; echo ----; grep -rn \"ISO8601\\|iso8601\" sqlglot/ | head -50; echo ----; cat .lithify/harness/memory.md 2>/dev/null | head -20; ls .lithify/harness/", "description": "Read dialect-functions skill and find ISO8601 references"}
[tool_result] ---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — any change to a
…[13743 chars elided]…
ion classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[assistant] The skill calls for inspecting the AST before editing. I'll check how Presto/Trino handles the sibling `FROM_ISO8601_TIMESTAMP` and run the AST probe on the current behavior.
[tool_use Bash] {"command": "grep -rn \"ISO8601\\|FROM_ISO\" sqlglot/parsers/presto.py sqlglot/generators/presto.py sqlglot/parsers/trino.py sqlglot/generators/trino.py sqlglot/dialects/presto.py sqlglot/dialects/trino.py 2>/dev/null; sed -n 430,445p sqlglot/expressions/temporal.py; ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/; git log --oneline -3 -- sqlglot/parsers/presto.py | cat; git show 7db4d2515 --stat | cat", "description": "Find Presto/Trino ISO8601 handling and the latest sibling commit"}
[tool_result] sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),


class DiToDate(Expression, Func):
    pass


class FromISO8601Timestamp(Expression, Func):
    _sql_names = ["FROM_ISO8601_TIMESTAMP"]


class ParseDatetime(Expression, Func):
    arg_types = {"this": True, "format": False, "zone": False, "default_year": False}


class ParseTime(Expression, Func):
    arg_types = {"this": True, "format": True}
ast_check.py
value_check.py
7e7cf8b06 Refactor
…[497 chars elided]…
   timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
    
    Co-authored-by: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

 sqlglot/generator.py          | 3 +++
 sqlglot/generators/duckdb.py  | 3 ---
 sqlglot/generators/presto.py  | 1 +
 tests/dialects/test_presto.py | 5 +++++
 4 files changed, 9 insertions(+), 3 deletions(-)
[tool_use Bash] {"command": "git show 7db4d2515 -- sqlglot/generator.py sqlglot/generators/duckdb.py tests/dialects/test_presto.py | cat; sed -n 3990,4000p sqlglot/generator.py; grep -n \"FROM_ISO8601_DATE\\|from_iso8601\" -ri tests sqlglot | head", "description": "Show sibling commit diff and any existing FROM_ISO8601_DATE refs"}
[tool_result] commit 7db4d2515435ba3d0651f2bd467fca1a747be265
Author: Baruch Oxman <baruch@honeydew.ai>
Date:   Mon Jun 22 12:54:22 2026 +0300

    fix(snowflake): transpile FROM_ISO8601_TIMESTAMP to cast [CLAUDE] (#7776)
    
    FROM_ISO8601_TIMESTAMP is a Presto/Trino function that returns a
    timestamp with timezone. Move DuckDB's cast-to-TIMESTAMPTZ logic into
    the base Generator so it transpiles correctly for all dialects (e.g.
    Snowflake, Spark), and keep the native function for Presto/Trino.
 
…[2648 chars elided]…
test_presto.py:37:            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:40:                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
tests/dialects/test_presto.py:41:                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
sqlglot/expressions/temporal.py:437:    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
sqlglot/generators/presto.py:307:        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
[assistant] There's a direct precedent: `FROM_ISO8601_TIMESTAMP` got a shared base-generator cast after the sibling commit. I'll follow that pattern. First, the current AST for the reported case, using the project's python.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read trino --write duckdb,snowflake,spark,bigquery,presto --repr \"SELECT FROM_ISO8601_DATE('2020-05-11')\"; echo EXIT $?", "description": "Probe current AST for FROM_ISO8601_DATE in Trino"}
[tool_result] == SELECT FROM_ISO8601_DATE('2020-05-11')
  node: Anonymous  <-- GENERIC node: is there a typed exp class for this function?
  Anonymous(
    this=FROM_ISO8601_DATE,
    expressions=[
      Literal(this='2020-05-11', is_string=True)])
  trino (round-trip): SELECT FROM_ISO8601_DATE('2020-05-11')
  duckdb: SELECT FROM_ISO8601_DATE('2020-05-11')
  snowflake: SELECT FROM_ISO8601_DATE('2020-05-11')
  spark: SELECT FROM_ISO8601_DATE('2020-05-11')
  bigquery: SELECT FROM_ISO8601_DATE('2020-05-11')
  presto: SELECT FROM_ISO8601_DATE('2020-05-11')
EXIT 0
[assistant] Confirmed: it parses to a generic `Anonymous` node. I'll add a typed `FromISO8601Date` class next to its timestamp sibling, mirror the generator wiring, and read the lines I'm about to change.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "offset": 434, "limit": 6}
[tool_result] 434	
435	
436	class FromISO8601Timestamp(Expression, Func):
437	    _sql_names = ["FROM_ISO8601_TIMESTAMP"]
438	
439	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "offset": 304, "limit": 6}
[tool_result] 304	        exp.Encode: lambda self, e: encode_decode_sql(self, e, "TO_UTF8"),
305	        exp.FileFormatProperty: lambda self, e: f"format={self.sql(exp.Literal.string(e.name))}",
306	        exp.First: _first_last_sql,
307	        exp.FromISO8601Timestamp: rename_func("FROM_ISO8601_TIMESTAMP"),
308	        exp.FromTimeZone: lambda self, e: (
309	            f"WITH_TIMEZONE({self.sql(e, 'this')}, {self.sql(e, 'zone')}) AT TIME ZONE 'UTC'"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py", "old_string": "class FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n", "new_string": "class FromISO8601Date(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_DATE\"]\n\n\nclass FromISO8601Timestamp(Expression, Func):\n    _sql_names = [\"FROM_ISO8601_TIMESTAMP\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/expressions/temporal.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py", "old_string": "        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n", "new_string": "        exp.FromISO8601Date: rename_func(\"FROM_ISO8601_DATE\"),\n        exp.FromISO8601Timestamp: rename_func(\"FROM_ISO8601_TIMESTAMP\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/generators/presto.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py", "old_string": "    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:", "new_string": "    def fromiso8601date_sql(self, expression: exp.FromISO8601Date) -> str:\n        return self.sql(exp.cast(expression.this, exp.DType.DATE))\n\n    def fromiso8601timestamp_sql(self, expression: exp.FromISO8601Timestamp) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-probe the node and the transpiles, including the Trino round-trip and the Presto target.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read trino --write duckdb,snowflake,spark,bigquery,presto,postgres,tsql --repr \"SELECT FROM_ISO8601_DATE('2020-05-11')\"; echo EXIT $?; $PY -c \"\nimport
…[100 chars elided]…
'2020-05-11')\\\", read=s, write=s)[0])\nfor d in ['snowflake','duckdb','spark','bigquery','postgres','tsql']:\n    print(d, sqlglot.transpile(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", read='trino', write=d)[0])\nprint(repr(sqlglot.parse_one(\\\"SELECT FROM_ISO8601_DATE('2020-05-11')\\\", read='trino').selects[0]))\n\"", "description": "Re-probe FROM_ISO8601_DATE node and transpile outputs"}
[tool_result] == SELECT FROM_ISO8601_DATE('2020-05-11')
  node: FromISO8601Date
  FromISO8601Date(
    this=Literal(this='2020-05-11', is_string=True))
  trino (round-trip): SELECT FROM_ISO8601_DATE('2020-05-11')
  duckdb: SELECT CAST('2020-05-11' AS DATE)
  snowflake: SELECT CAST('2020-05-11' AS DATE)
  spark: SELECT CAST('2020-05-11' AS DATE)
  bigquery: SELECT CAST('2020-05-11' AS DATE)
  presto: SELECT FROM_ISO8601_DATE('2020-05-11')
  postgres: SELECT CAST('2020-05-11' AS DATE)
  tsql: SELECT CAST('2020-05-11' AS DATE)
EXIT 0
trino SELECT FROM_ISO8601_DATE('2020-05-11')
presto SELECT FROM_ISO8601_DATE('2020-05-11')
snowflake SELECT CAST('2020-05-11' AS DATE)
duckdb SELECT CAST('2020-05-11' AS DATE)
spark SELECT CAST('2020-05-11' AS DATE)
bigquery SELECT CAST('2020-05-11' AS DATE)
postgres SELECT CAST('2020-05-11' AS DATE)
tsql SELECT CAST('2020-05-11' AS DATE)
FromISO8601Date(
  this=Literal(this='2020-05-11', is_string=True))
[assistant] The node is now typed as `FromISO8601Date`, the Trino/Presto round-trip is preserved, and other targets get `CAST(... AS DATE)`. Next I'll check value semantics with DuckDB if it's available, and look at the existing test block to add a matching test.
[tool_use Bash] {"command": "sed -n 30,52p tests/dialects/test_presto.py; PY=<work>/env-sqlglot/bin/python; $PY -c \"import duckdb\" 2>&1 | tail -1; grep -n \"FROM_ISO\\|class Test\\|def test_\" tests/dialects/test_trino.py | head", "description": "View existing Presto test block and check duckdb availability"}
[tool_result]             },
            write={
                "presto": "CAST(x AS BOOLEAN)",
                "tsql": "CAST(x AS BIT)",
            },
        )
        self.validate_all(
            "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
            write={
                "duckdb": "SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMPTZ)",
                "presto": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:05')",
                "trino": "SELECT FROM_ISO8601_TIMESTAMP('2020-05-11T11:15:
…[318 chars elided]…
AMP)",
            },
        )
        self.validate_all(
            "CAST(x AS INTERVAL YEAR TO MONTH)",
            write={
                "oracle": "CAST(x AS INTERVAL YEAR TO MONTH)",
                "presto": "CAST(x AS INTERVAL YEAR TO MONTH)",
4:class TestTrino(Validator):
7:    def test_trino(self):
54:    def test_listagg(self):
78:    def test_trim(self):
91:    def test_ddl(self):
145:    def test_analyze(self):
149:    def test_json_value(self):
165:    def test_array_first(self):
[assistant] DuckDB imports cleanly here, so I can check values directly. I'll run the value probe on the example and a couple of inputs, then add the tests next to the timestamp sibling.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot, duckdb\ncon = duckdb.connect()\nfor s in ['2020-05-11', '2020-02-29', '2020-05-11 ']:\n    sql = sqlglot.transpile(f\\\"SELECT FROM_ISO8601_DATE('{s}')\\\", read='trino', write='duckdb')[0]\n    try: print(repr(s), sql, '->', con.sql(sql).fetchall())\n    except Exception as e: print(repr(s), sql, 'ERR', type(e).__name__, str(e)[:80])\n\"", "description": "Execute transpiled DuckDB output for sample dates"}
[tool_result] '2020-05-11' SELECT CAST('2020-05-11' AS DATE) -> [(datetime.date(2020, 5, 11),)]
'2020-02-29' SELECT CAST('2020-02-29' AS DATE) -> [(datetime.date(2020, 2, 29),)]
'2020-05-11 ' SELECT CAST('2020-05-11 ' AS DATE) -> [(datetime.date(2020, 5, 11),)]
[assistant] The DuckDB results match Trino's `DATE` values for those inputs. Now the tests, placed beside the timestamp sibling in `test_presto.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py", "old_string": "                \"bigquery\": \"SELECT CAST('2020-05-11T11:15:05' AS TIMESTAMP)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\",", "new_string": "
…[497 chars elided]…
-05-11')\",\n                \"trino\": \"SELECT FROM_ISO8601_DATE('2020-05-11')\",\n                \"snowflake\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"spark\": \"SELECT CAST('2020-05-11' AS DATE)\",\n                \"bigquery\": \"SELECT CAST('2020-05-11' AS DATE)\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS INTERVAL YEAR TO MONTH)\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-113715-trino-other-dialects-from-iso860/base-1/tests/dialects/test_presto.py has been updated successfully.
[tool_use Bash] {"command": "head -5 tests/dialects/test_presto.py; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_presto.py tests/dialects/test_trino.py 2>&1 | tail -15", "description": "Run Presto and Trino dialect test files"}
[tool_result] from sqlglot import UnsupportedError, exp, parse_one
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


...........................                          [100%]
27 passed, 524 subtests passed in 0.21s
[assistant] Dialect tests pass. Now the full suite, run in the foreground as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-16:06:48 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-fa5c3a7fc2.log
ELAPSED: 54s
SUMMARY: 1122 passed, 18190 subtests passed in 54.00s
EXIT: 0
[assistant] The full suite finished with `SUMMARY: 1122 passed` and `EXIT: 0`. I'll run the linter and formatter on the changed files, then review the diff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/expressions/temporal.py sqlglot/generator.py sqlglot/generators/presto.py tests/dialects/test_presto.py 2>&1 | tail -3; git status --short; git diff --stat | cat", "description": "Lint, format-check, and show changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/temporal.py
 M sqlglot/generator.py
 M sqlglot/generators/presto.py
 M tests/dialects/test_presto.py
 sqlglot/expressions/temporal.py |  4 ++++
 sqlglot/generator.py            |  3 +++
 sqlglot/generators/presto.py    |  1 +
 tests/dialects/test_presto.py   | 13 +++++++++++++
 4 files changed, 21 insertions(+)
[assistant] Lint and format are clean. One value edge is still open: Trino's ISO 8601 parser also accepts week and ordinal dates, which a plain `CAST` may not handle. I'll check that against DuckDB before reporting.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb\ncon = duckdb.connect()\nfor s in ['2020-W19-1', '2020-132']:\n    try: print(s, con.sql(f\\\"SELECT CAST('{s}' AS DATE)\\\").fetchall())\n    except Exception as e: print(s, 'ERR', str(e)[:100])\n\"", "description": "Check DuckDB cast on ISO week and ordinal dates"}
[tool_result] 2020-W19-1 ERR Conversion Error: invalid date field format: "2020-W19-1", expected format is (YYYY-MM-DD)

LINE 1: 
2020-132 ERR Conversion Error: invalid date field format: "2020-132", expected format is (YYYY-MM-DD)

LINE 1: SE
[assistant] Trino's `FROM_ISO8601_DATE` now parses to a typed node and transpiles to `CAST(... AS DATE)` in other dialects. Week and ordinal date inputs still don't match Trino, and I left that open on purpose.

**What changed** (4 files, uncommitted):
- `sqlglot/expressions/temporal.py`: new `exp.FromISO8601Date` class, mirroring `FromISO8601Timestamp`.
- `sqlglot/generator.py`: base `fromiso8601date_sql` emits `CAST(x AS DATE)`. This is the same pattern the recent `FROM_ISO8601_TIMESTAMP` commit used.
- `sqlglot/generators/presto.py`: `rename_func("FROM_ISO8601_DATE")`, so Presto and Trino round-trip.
-
…[659 chars elided]…
ormat --check` pass on the changed files.

**Remaining gap:** Trino's ISO 8601 parser also accepts week dates (`2020-W19-1`) and ordinal dates (`2020-132`). DuckDB's `CAST ... AS DATE` rejects both, so those inputs would return a different result or an error after transpiling. I did not handle this because doing it correctly needs per-engine logic beyond the plain cast you asked for. Tell me if you want that covered. I have not checked the Trino side against a live server; the week/ordinal behavior comes from Trino's documented ISO 8601 support.

I did not commit, since you didn't ask for one.
