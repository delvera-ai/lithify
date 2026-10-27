# trajectory base-1

final message:
`LOAD DATA INTO TEMP TABLE` now parses and round-trips in BigQuery, and all three forms from your list round-trip. Full suite: `SUMMARY: 1112 passed, 18136 subtests passed in 59.52s` / `EXIT: 0`.

**Changes**
- `sqlglot/expressions/dml.py`: `LoadData` gets a `temporary` arg.
- `sqlglot/parser.py` (`_parse_load`): after `INTO`, accepts `TEMP` or `TEMPORARY`, sets `temporary`, then the `TABLE` keyword. The parser is shared, so this applies to all dialects.
- `sqlglot/generator.py` (`loaddata_sql`): the `FILES` branch emits `INTO TEMP TABLE` when `temporary` is set.
- `tests/dialects/test_bigquery.py`: added the `INTO TEMP TABLE` form to the existing round-trip loop.

**Checks**
- AST: `INTO TEMP TABLE` and `INTO TEMPORARY TABLE` both produce `LoadData` with `temporary=True`. `OVERWRITE` and `INTO TABLE` leave `temporary` unset.
- Cross-dialect: `TEMP` survives generation in all 31 dialects with no dropped output.
- Ruff check and format pass on the changed files.

**Decisions to confirm**
- `TEMPORARY` is normalised to `TEMP` on output, so that spelling is accepted but doesn't round-trip verbatim. Say if you want it preserved.
- The `TABLE` keyword is now optional, so `LOAD DATA TABLE x ...` (without `INTO`) and `LOAD DATA OVERWRITE TABLE x` now parse. Previously `INTO TABLE` had to appear as a pair. This is lenient but harmless for valid BigQuery input; tighten it if you prefer.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn -i \"LOAD DATA\\|LoadData\\|\\\"LOAD\\\"\\|LOAD_DATA\" sqlglot/ tests/ | head -50; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Find LOAD DATA handling in code and tests"}
[tool_result] sqlglot/tokens.py:329:        "LOAD": TokenType.LOAD,
sqlglot/generator.py:2895:    def loaddata_sql(self, expression: exp.LoadData) -> str:
sqlglot/generator.py:2905:            return f"LOAD DATA{overwrite}{this} FROM {files_sql}"
sqlglot/generator.py:2916:        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
sqlglot/parser.py:3589:    def _parse_load(self) -> exp.LoadData | exp.Command:
sqlglot/parser.py:3598:                exp.LoadData(
sqlglot/expressi
…[1673 chars elided]…
on -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1100 tests) takes 60–80 s alone; `tests/test_executor.py::TestExecutor::test_execute_tpcds`
  is slowest and looks hung under CPU contention. Run the dialect's own test file first (<1 s).
[tool_use Bash] {"command": "sed -n 3585,3625p sqlglot/parser.py; sed -n 2890,2920p sqlglot/generator.py; sed -n 275,300p sqlglot/expressions/dml.py; sed -n 205,230p tests/dialects/test_bigquery.py; grep -n \"LoadData\\|_parse_load\" sqlglot/parsers/*.py sqlglot/dialects/bigquery.py | head", "description": "Read LOAD DATA parser, generator, and tests"}
[tool_result]             kwargs["null"] = self._parse_string()

        return self.expression(exp.RowFormatDelimitedProperty(**kwargs))  # type: ignore

    def _parse_load(self) -> exp.LoadData | exp.Command:
        if self._match_text_seq("DATA"):
            local = self._match_text_seq("LOCAL")
            self._match_text_seq("INPATH")
            inpath = self._parse_string()
            overwrite = self._match(TokenType.OVERWRITE)
            self._match_pair(TokenType.INTO, TokenType.TABLE)

      
…[4053 chars elided]…
.validate_identity("CAST(x AS BIGNUMERIC)")
        self.validate_identity("SELECT y + 1 FROM x GROUP BY y + 1 ORDER BY 1")
        self.validate_identity("SELECT TIMESTAMP_SECONDS(2) AS t")
        self.validate_identity("SELECT TIMESTAMP_MILLIS(2) AS t")
        self.validate_identity("UPDATE x SET y = NULL")
        self.validate_identity("LOG(n, b)")
        self.validate_identity("SELECT COUNT(x RESPECT NULLS)")
        self.validate_identity("SELECT LAST_VALUE(x IGNORE NULLS) OVER y AS x")
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-data-types/SKILL.md | head -150; grep -n \"def _match_texts\\|def _match_text_seq\" sqlglot/parser.py; grep -n '\"TEMP' sqlglot/tokens.py | head; git status --short | head", "description": "Read data-types skill and check token helpers"}
[tool_result] ---
name: sqlglot-data-types
description: Load when a task changes how sqlglot parses or generates a data type (exp.DataType) — CAST / TRY_CAST / `::` target types, nested types (ARRAY<…>, STRUCT<…>, MAP, Nullable(…)), type modifiers or trailing clauses such as COLLATE, CHARACTER SET, WITH TIME ZONE — or when a fix adds a new arg to any existing expression class (DataType, Cast, Column, …) that must survive generation in every dialect.
---

# Data types and new node args in sqlglot

## Who owns 
…[3391 chars elided]…
 the method (e.g. `tests/dialects/test_spark.py`), with the expected
   string written from that engine's syntax, not copied from the script output.
4. Then the normal done-check: dialect test files, then `run_suite.py` (see `tool_guidance.md`).
1943:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1950:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
392:        "TEMP": TokenType.TEMPORARY,
393:        "TEMPORARY": TokenType.TEMPORARY,
[assistant] Adding a `temporary` arg to `LoadData` and parsing it in `_parse_load`, then the generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[170 chars elided]…
ERWRITE)\n            temporary = self._match(TokenType.INTO) and self._match_texts((\"TEMP\", \"TEMPORARY\"))\n            self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: emit `TEMP` in the `FILES` branch when set.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "            this = f\" {this}\" if is_overwrite else f\" INTO TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"", "new_string": "            temporary = \" TEMP\" if expression.args.get(\"temporary\") else \"\"\n            this = f\" {this}\" if is_overwrite else f\" INTO{temporary} TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[assistant] Now the test: add the TEMP form to the BigQuery round-trip loop, then probe the AST node and every dialect's output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):", "new_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-101316-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_load.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfor sql in [\n \"LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n \"LOAD DATA INTO TABLE mydataset.t
…[325 chars elided]…
arse_one(sql, read=\"bigquery\")\n    print(type(e).__name__, e.args.get(\"temporary\"), e.args.get(\"overwrite\"), \"|\", e.sql(\"bigquery\"))\nEOF\nPYTHONPATH=. $PY /tmp/probe_load.py; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py tests/dialects/test_mysql.py 2>&1 | tail -5", "description": "Probe LOAD DATA AST and run dialect tests"}
[tool_result] LoadData False True | LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
LoadData False False | LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
LoadData True False | LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
LoadData True False | LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
.................................................................... [ 55%]
.......................................................  [100%]
123 passed, 2036 subtests passed in 0.58s
[assistant] The AST nodes look right: `temporary` is set only for the `INTO TEMP`/`TEMPORARY` forms, and `overwrite` is unchanged. Next, the cross-dialect check from the data-types skill, and then the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-data-types/scripts/all_dialects.py --read bigquery --keep TEMP \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\" \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\"; echo \"EXIT: $?\"", "description": "Run cross-dialect generation check for LOAD DATA"}
[tool_result] == LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
  bigquery (round-trip): LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
  athena: LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(format='AVRO', uris=ARRAY['gs://bucket/path/file.avro'])
  bigquery: LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])
  clickhouse: LOAD DA
…[11112 chars elided]…
TO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=ARRAY('gs://bucket/path/file.avro'))
  teradata: LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=ARRAY('gs://bucket/path/file.avro'))
  trino: LOAD DATA INTO TABLE mydataset.table1 FROM FILES(format='AVRO', uris=ARRAY['gs://bucket/path/file.avro'])
  tsql: LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=ARRAY('gs://bucket/path/file.avro'))
  -- 0 silent drop/error line(s) across 31 dialects
EXIT: 0
[assistant] The `TEMP` keyword survives generation in every dialect. The array and `FILES` differences in other dialects also show up for the existing `OVERWRITE` and `INTO TABLE` forms, so they predate this change. Now the full suite, run on its own as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:42:55 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  77564       00:34 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-25b490cc43.log
ELAPSED: 60s
SUMMARY: 1112 passed, 18136 subtests passed in 59.52s
EXIT: 0
[assistant] The full suite passes. Last, a lint/format check on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff --version >/dev/null 2>&1 && $PY/ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py && $PY/ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py) || (ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py && ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py); git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/expressions/dml.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_bigquery.py
[assistant] `LOAD DATA INTO TEMP TABLE` now parses and round-trips in BigQuery, and all three forms from your list round-trip. Full suite: `SUMMARY: 1112 passed, 18136 subtests passed in 59.52s` / `EXIT: 0`.

**Changes**
- `sqlglot/expressions/dml.py`: `LoadData` gets a `temporary` arg.
- `sqlglot/parser.py` (`_parse_load`): after `INTO`, accepts `TEMP` or `TEMPORARY`, sets `temporary`, then the `TABLE` keyword. The parser is shared, so this applies to all dialects.
- `sqlglot/generator.py` (`loaddata_sql`): the `FILES` branch emits `INTO TEMP TABLE` when `temporary` is set.
- `tests/dialects/test_bigquer
…[223 chars elided]…
porary` unset.
- Cross-dialect: `TEMP` survives generation in all 31 dialects with no dropped output.
- Ruff check and format pass on the changed files.

**Decisions to confirm**
- `TEMPORARY` is normalised to `TEMP` on output, so that spelling is accepted but doesn't round-trip verbatim. Say if you want it preserved.
- The `TABLE` keyword is now optional, so `LOAD DATA TABLE x ...` (without `INTO`) and `LOAD DATA OVERWRITE TABLE x` now parse. Previously `INTO TABLE` had to appear as a pair. This is lenient but harmless for valid BigQuery input; tighten it if you prefer.

Nothing is committed.
