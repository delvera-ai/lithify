# trajectory base-1

final message:
BigQuery `LOAD DATA INTO TEMP TABLE` now parses and round-trips. All three forms from your request produce the same SQL back, and the full suite passes (1112 passed).

**What changed**
- **`sqlglot/expressions/dml.py`**: `LoadData` gets a `temporary` arg.
- **`sqlglot/parser.py`** (`_parse_load`): after an optional `OVERWRITE`, it accepts `INTO TEMP TABLE` or `INTO TEMPORARY TABLE`, and sets `temporary`. Otherwise it keeps the existing `INTO TABLE` handling.
- **`sqlglot/generator.py`** (`loaddata_sql`, FILES branch): emits `INTO TEMP TABLE` when `temporary` is set.
- **`tests/dialects/test_bigquery.py`**: added the `INTO TEMP TABLE` identity case, plus a `TEMPORARY` input that is checked to generate `TEMP`.

**Choices I made**
- `TEMPORARY` is normalised to `TEMP` on output, since that is BigQuery's short form. If you need `TEMPORARY` to survive a round-trip exactly, the flag would have to store the original keyword instead.
- The change lives in the base parser and generator, next to the existing `LOAD DATA ... FROM FILES` support, rather than in the BigQuery dialect class.
- The Hive-style branch (`INPATH ...`) does not handle `temporary`. A statement like `LOAD DATA INTO TEMP TABLE x INPATH ...` would drop the `TEMP`. I left it alone because that form isn't valid BigQuery.

I haven't committed anything, since you didn't ask for a commit.

## events
[tool_use Bash] {"command": "grep -n \"LOAD\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -rn \"LOAD DATA\" tests/ | head -20", "description": "Find LOAD DATA handling in code and tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:716:        TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/parser.py:1622:    ISOLATED_LOADING_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {"FOR": ("ALL", "INSERT", "NONE")}
sqlglot/parser.py:3132:        if not self._match_text_seq("ISOLATED", "LOADING"):
sqlglot/parser.py:3136:        target = self._parse_var_from_options(self.ISOLATED_LOADING_OPTIONS, raise_unma
…[717 chars elided]…
es/identity.sql:710:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy')
tests/fixtures/identity.sql:711:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y'
tests/fixtures/identity.sql:712:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:713:LOAD DATA INPATH 'x' INTO TABLE y INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:714:LOAD DATA INPATH 'x' INTO TABLE y.b INPUTFORMAT 'y' SERDE 'z'
[assistant] Existing `LOAD DATA` handling is in the base parser and generator. Next I'll read those and the BigQuery parse path.
[tool_use Bash] {"command": "grep -n \"_parse_load\" -A60 sqlglot/parser.py | sed -n '1,80p'; echo ----; sed -n 2885,2920p sqlglot/generator.py; echo ----; grep -n \"class Load\\b\" -A12 sqlglot/expressions.py; echo ----; grep -n \"LOAD\\|load\" sqlglot/dialects/bigquery.py; echo ----; sed -n 205,230p tests/dialects/test_bigquery.py", "description": "Read LOAD parsing, generation, and BigQuery tests"}
[tool_result] 1099:        TokenType.LOAD: lambda self: self._parse_load(),
1100-        TokenType.MERGE: lambda self: self._parse_merge(),
1101-        TokenType.PIVOT: lambda self: self._parse_simplified_pivot(),
1102-        TokenType.PRAGMA: lambda self: self.expression(exp.Pragma(this=self._parse_expression())),
1103-        TokenType.REFRESH: lambda self: self._parse_refresh(),
1104-        TokenType.ROLLBACK: lambda self: self._parse_commit_or_rollback(),
1105-        TokenType.SET: lambda self: self._
…[6341 chars elided]…
.validate_identity("CAST(x AS BIGNUMERIC)")
        self.validate_identity("SELECT y + 1 FROM x GROUP BY y + 1 ORDER BY 1")
        self.validate_identity("SELECT TIMESTAMP_SECONDS(2) AS t")
        self.validate_identity("SELECT TIMESTAMP_MILLIS(2) AS t")
        self.validate_identity("UPDATE x SET y = NULL")
        self.validate_identity("LOG(n, b)")
        self.validate_identity("SELECT COUNT(x RESPECT NULLS)")
        self.validate_identity("SELECT LAST_VALUE(x IGNORE NULLS) OVER y AS x")
[tool_use Bash] {"command": "sed -n 3606,3615p sqlglot/parser.py; echo ----; grep -rn \"class LoadData\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -20; echo ----; grep -n \"TEMPORARY\\|\\\"TEMP\\\"\" sqlglot/dialects/bigquery.py | head; echo ----; grep -n \"TEMPORARY\" sqlglot/parser.py | head -5; echo ---; .venv/bin/python -c \"print(1)\" 2>/dev/null; ls <work>/env-sqlglot/bin/python", "description": "Inspect LoadData class, TEMP handling, and test env"}
[tool_result]                     input_format=self._match_text_seq("INPUTFORMAT") and self._parse_string(),
                    serde=self._match_text_seq("SERDE") and self._parse_string(),
                )
            )
        return self._parse_as_command(self._prev)

    def _parse_delete(self) -> exp.Delete:
        hint = self._parse_hint()

        # This handles MySQL's "Multiple-Table Syntax"
----
sqlglot/expressions/dml.py:281:class LoadData(Expression):
sqlglot/expressions/dml.py-282-    arg_type
…[451 chars elided]…
: False,
sqlglot/expressions/dml.py-291-    }
sqlglot/expressions/dml.py-292-
sqlglot/expressions/dml.py-293-
----
----
749:        TokenType.TEMPORARY,
1329:        "TEMPORARY": lambda self: self.expression(exp.TemporaryProperty()),
2295:        temporary = self._match(TokenType.TEMPORARY)
4195:        temp = self._match(TokenType.TEMPORARY)
---
<work>/env-sqlglot/bin/python
[assistant] I have what I need. The plan: add a `temporary` flag to `exp.LoadData`, parse `INTO [TEMP|TEMPORARY] TABLE` in `_parse_load`, and emit `INTO TEMP TABLE` in the FILES branch of `loaddata_sql`. I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,\n        \"files\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,\n        \"files\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[332 chars elided]…
       if temporary:\n                self._match(TokenType.TABLE)\n            else:\n                self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "            this = f\" {this}\" if is_overwrite else f\" INTO TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"", "new_string": "            into = \" INTO TEMP TABLE\" if expression.args.get(\"temporary\") else \" INTO TABLE\"\n            this = f\" {this}\" if is_overwrite else f\"{into} {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):\n            with self.subTest(load_data_sql=load_data_sql):\n             
…[374 chars elided]…
ta_sql=load_data_sql):\n                self.validate_identity(load_data_sql).assert_is(exp.LoadData)\n        self.validate_identity(\n            \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-153957-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/test_transpile.py tests/test_parser.py tests/test_generator.py 2>&1 | tail -15", "description": "Run BigQuery and core parser/generator tests"}
[tool_result] ................................................................. [ 41%]
...................................................................................... [ 95%]
.......                                                                [100%]
158 passed, 2155 subtests passed in 28.85s
[assistant] The targeted tests pass. Next I'll run the full suite with the project's check command, since the Hive `LOAD DATA` fixtures also go through this code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\n
…[11 chars elided]…
LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f\\'])','LOAD DATA INTO TEMPORARY TABLE t FROM FILES(uris=[\\'gs://b/f\\'])','LOAD DATA INTO TABLE t FROM FILES(uris=[\\'gs://b/f\\'])']:\n    e=sqlglot.parse_one(s, read='bigquery'); print(type(e).__name__, e.sql('bigquery'))\n\"; git status --short", "description": "Run full test suite and spot-check round-trips"}
[tool_result] ................ [ 53%]
............................................................................................................................................................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 58.10s
LoadData LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f'])
LoadData LOAD DATA INTO TEMP TABLE t FROM FILES(uris=['gs://b/f'])
LoadData LOAD DATA INTO TABLE t FROM FILES(uris=['gs://b/f'])
 M sqlglot/expressions/dml.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_bigquery.py
[assistant] BigQuery `LOAD DATA INTO TEMP TABLE` now parses and round-trips. All three forms from your request produce the same SQL back, and the full suite passes (1112 passed).

**What changed**
- **`sqlglot/expressions/dml.py`**: `LoadData` gets a `temporary` arg.
- **`sqlglot/parser.py`** (`_parse_load`): after an optional `OVERWRITE`, it accepts `INTO TEMP TABLE` or `INTO TEMPORARY TABLE`, and sets `temporary`. Otherwise it keeps the existing `INTO TABLE` handling.
- **`sqlglot/generator.py`** (`loaddata_sql`, FILES branch): emits `INTO TEMP TABLE` when `temporary` is set.
- **`tests/dialects/test_bi
…[163 chars elided]…
ed to `TEMP` on output, since that is BigQuery's short form. If you need `TEMPORARY` to survive a round-trip exactly, the flag would have to store the original keyword instead.
- The change lives in the base parser and generator, next to the existing `LOAD DATA ... FROM FILES` support, rather than in the BigQuery dialect class.
- The Hive-style branch (`INPATH ...`) does not handle `temporary`. A statement like `LOAD DATA INTO TEMP TABLE x INPATH ...` would drop the `TEMP`. I left it alone because that form isn't valid BigQuery.

I haven't committed anything, since you didn't ask for a commit.
