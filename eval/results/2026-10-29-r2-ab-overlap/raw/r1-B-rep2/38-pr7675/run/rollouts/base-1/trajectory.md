# trajectory base-1

final message:
BigQuery now parses and round-trips `LOAD DATA INTO TEMP TABLE`, and the full suite passes (1112 tests, 53s), along with ruff lint and format.

All three forms from your list round-trip unchanged:
- `LOAD DATA OVERWRITE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TABLE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(...)`

`INTO TEMPORARY TABLE` is also accepted, and it generates `INTO TEMP TABLE`. It parses to the same AST, so the output is the same statement; the spelling is normalized.

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): after `INTO`, it now accepts an optional `TEMP`/`TEMPORARY`, then an optional `TABLE`. This replaces the old `_match_pair(INTO, TABLE)`, so `INTO` without `TABLE` is now accepted as well. That is a small loosening of the shared Hive path.
- **`sqlglot/expressions/dml.py`**: `LoadData` gets a `temporary` arg.
- **`sqlglot/generator.py`** (`loaddata_sql`): emits `TEMP` in the `FROM FILES` branch.
- **`tests/dialects/test_bigquery.py`**: added the `TEMP` form to the round-trip list and a `TEMPORARY` → `TEMP` normalization check.

The changes are not committed.

## events
[tool_use Bash] {"command": "grep -rn \"LOAD DATA\\|LoadData\\|_parse_load\\|\\\"LOAD\\\"\" sqlglot/ tests/dialects/test_bigquery.py | head -40; ls .lithify/harness/scripts/", "description": "Locate LOAD DATA handling in sqlglot"}
[tool_result] sqlglot/tokens.py:329:        "LOAD": TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/parser.py:3589:    def _parse_load(self) -> exp.LoadData | exp.Command:
sqlglot/parser.py:3598:                exp.LoadData(
sqlglot/generator.py:2895:    def loaddata_sql(self, expression: exp.LoadData) -> str:
sqlglot/generator.py:2905:            return f"LOAD DATA{overwrite}{this} FROM {files_sql}"
sqlglot/generator.py:2916:        return f"LOAD DATA{l
…[60 chars elided]…
e}"
sqlglot/expressions/dml.py:281:class LoadData(Expression):
tests/dialects/test_bigquery.py:218:            "LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
tests/dialects/test_bigquery.py:219:            "LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
tests/dialects/test_bigquery.py:222:                self.validate_identity(load_data_sql).assert_is(exp.LoadData)
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 3585,3625p sqlglot/parser.py; echo ----; sed -n 2893,2920p sqlglot/generator.py; echo ----; sed -n 278,300p sqlglot/expressions/dml.py; echo ----; sed -n 205,230p tests/dialects/test_bigquery.py", "description": "Read LOAD DATA parser, generator, expression, tests"}
[tool_result]             kwargs["null"] = self._parse_string()

        return self.expression(exp.RowFormatDelimitedProperty(**kwargs))  # type: ignore

    def _parse_load(self) -> exp.LoadData | exp.Command:
        if self._match_text_seq("DATA"):
            local = self._match_text_seq("LOCAL")
            self._match_text_seq("INPATH")
            inpath = self._parse_string()
            overwrite = self._match(TokenType.OVERWRITE)
            self._match_pair(TokenType.INTO, TokenType.TABLE)

      
…[3907 chars elided]…
.validate_identity("CAST(x AS BIGNUMERIC)")
        self.validate_identity("SELECT y + 1 FROM x GROUP BY y + 1 ORDER BY 1")
        self.validate_identity("SELECT TIMESTAMP_SECONDS(2) AS t")
        self.validate_identity("SELECT TIMESTAMP_MILLIS(2) AS t")
        self.validate_identity("UPDATE x SET y = NULL")
        self.validate_identity("LOG(n, b)")
        self.validate_identity("SELECT COUNT(x RESPECT NULLS)")
        self.validate_identity("SELECT LAST_VALUE(x IGNORE NULLS) OVER y AS x")
[tool_use Bash] {"command": "grep -n \"def _match_texts\" -A8 sqlglot/parser.py; grep -n '\"TEMP' sqlglot/tokens.py; cat .lithify/harness/scripts/probe_parse.py | head -30", "description": "Check _match_texts helper and TEMP keyword tokens"}
[tool_result] 1943:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1944-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1945-            if advance:
1946-                self._advance()
1947-            return True
1948-        return False
1949-
1950-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1951-        index = self._index
2 matches in 2 files:

392:0:TokenType.TEMPORARY,
393:0:TokenType.TEMPORARY,
…[542 chars elided]…
hows both

Exits 0 if every statement is OK, 1 if any statement is ERR or UNSTABLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
  <python> -I .lithify/harness/scripts/probe_parse.py --read oracle < variants.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"
[tool_use Bash] {"command": "printf '%s\\n' \"LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" | <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"exit $?\"", "description": "Probe baseline BigQuery LOAD DATA variants"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
[tool_use Bash] {"command": "printf '%s\\n' \"LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" | PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"exit $?\"", "description": "Probe baseline BigQuery LOAD DATA variants"}
[tool_result] OK        LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
OK        LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
ERR       LOAD DATA INTO TEMP TABLE mydataset.table1 FROM 
…[19 chars elided]…
, uris=['gs://bucket/path/file.avro'])
          ParseError: Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
ERR       LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          ParseError: Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
exit 1
[assistant] Reproduced: `INTO TEMP TABLE` and `INTO TEMPORARY TABLE` both fail. Now the change: a `temporary` flag on `LoadData`, parsed after `INTO`, and emitted in the `FROM FILES` branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[222 chars elided]…
 if self._match(TokenType.INTO):\n                temporary = self._match_texts((\"TEMP\", \"TEMPORARY\"))\n                self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "            files_sql = f\"FILES{self.wrap(files_sql)}\"\n            this = f\" {this}\" if is_overwrite else f\" INTO TABLE {this}\"", "new_string": "            files_sql = f\"FILES{self.wrap(files_sql)}\"\n            temporary = \" TEMP\" if expression.args.get(\"temporary\") else \"\"\n            this = f\" {this}\" if is_overwrite else f\" INTO{temporary} TABLE {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests. I'll add the `TEMP` form to the existing round-trip list and a `TEMPORARY` → `TEMP` normalization check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):\n            with self.subTest(load_data_sql=load_data_sql):\n             
…[374 chars elided]…
ta_sql=load_data_sql):\n                self.validate_identity(load_data_sql).assert_is(exp.LoadData)\n        self.validate_identity(\n            \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155652-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py tests/dialects/test_spark.py 2>&1 | tail -15; printf '%s\\n' \"LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TABLE mydataset.tab
…[68 chars elided]…
 \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"probe exit $?\"", "description": "Run BigQuery/Hive/Spark tests and re-probe LOAD DATA"}
[tool_result] .................................................................... [ 72%]
..........................                   [100%]
94 passed, 1976 subtests passed in 0.65s
OK        LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
OK        LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])

…[92 chars elided]…
/path/file.avro'])
OK        LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
OK        LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
          LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
probe exit 0
[assistant] Targeted tests pass and all four variants probe clean. Running the full suite as the final gate, plus lint.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py && $PY -m ruff format --check sqlglot tests/dialects/test_bigquery.py) 2>&1 | tail -4; git status --short", "description": "Run full test suite, ruff lint and format check"}
[tool_result] ................ [ 53%]
............................................................................................................................................................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 53.55s
All checks passed!
177 files already formatted
 M sqlglot/expressions/dml.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_bigquery.py
[assistant] BigQuery now parses and round-trips `LOAD DATA INTO TEMP TABLE`, and the full suite passes (1112 tests, 53s), along with ruff lint and format.

All three forms from your list round-trip unchanged:
- `LOAD DATA OVERWRITE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TABLE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(...)`

`INTO TEMPORARY TABLE` is also accepted, and it generates `INTO TEMP TABLE`. It parses to the same AST, so the output is the same statement; the spelling is normalized.

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): after `INTO`, it now accepts an optional `TEMP`/`TEMPORARY`, then an optional `TABLE`. This replaces the old `_match_pair(INTO, TABLE)`, so `INTO` without `TABLE` is now accepted as well. That is a small loosening of the shared Hive path.
- **`sqlglot/expressions/dml.py`**: `LoadData` gets a `temporary` arg.
- **`sqlglot/generator.py`** (`loaddata_sql`): emits `TEMP` in the `FROM FILES` branch.
- **`tests/dialects/test_bigquery.py`**: added the `TEMP` form to the round-trip list and a `TEMPORARY` → `TEMP` normalization check.

The changes are not committed.
