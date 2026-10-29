# trajectory base-1

final message:
`LOAD DATA INTO TEMP TABLE` now parses and round-trips in the BigQuery dialect, along with the two forms that already worked. The full test suite passes (1112 passed).

The three statements from your request round-trip unchanged:
- `LOAD DATA OVERWRITE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TABLE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(...)`

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): the `INTO TABLE` pair is now matched as separate optional tokens, with `TEMP`/`TEMPORARY` accepted between them. `TEMP` and `TEMPORARY` both tokenize to `TokenType.TEMPORARY`, so `INTO TEMPORARY TABLE` parses too.
- **`sqlglot/expressions/dml.py`**: `LoadData` gets a `temporary` arg.
- **`sqlglot/generator.py`** (`loaddata_sql`): emits `INTO TEMP TABLE` when `temporary` is set.
- **`tests/dialects/test_bigquery.py`**: added the `INTO TEMP TABLE` case to the existing LOAD DATA round-trip loop.

Choices to review:
- **`TEMPORARY` normalizes to `TEMP` on output.** `INTO TEMPORARY TABLE ...` parses but prints as `INTO TEMP TABLE`. I did this because `TEMP` is the form in your request. Keeping the original spelling would need a separate flag.
- **`OVERWRITE TEMP TABLE` is accepted and round-trips.** I'm not certain BigQuery allows `TEMP` with `OVERWRITE`, so I kept it parseable rather than rejecting it.
- **The parser is shared, not BigQuery-only.** `LOAD DATA` parsing lives in the base parser, so Hive-style input now also accepts `TEMP`. I left it there because `FILES` handling is already in the base parser. Moving the `TEMP` handling into the BigQuery dialect would need a dialect-level `_parse_load` override.
- **`INTO` without `TABLE` is now accepted.** The old code required `INTO TABLE` as a pair. The new code treats each keyword as optional, which is a small loosening.

## events
[tool_use Bash] {"command": "grep -rn \"LOAD\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | grep -i \"load\" | head -50; grep -rn \"LOAD DATA\" tests/ | head", "description": "Find LOAD references in source and tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:2169:        return f"WITH{no}{concurrent} ISOLATED LOADING{target}"
sqlglot/generator.py:2905:            return f"LOAD DATA{overwrite}{this} FROM {files_sql}"
sqlglot/generator.py:2916:        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
sqlglot/parser.py:716:        TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/
…[717 chars elided]…
es/identity.sql:710:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy')
tests/fixtures/identity.sql:711:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y'
tests/fixtures/identity.sql:712:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:713:LOAD DATA INPATH 'x' INTO TABLE y INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:714:LOAD DATA INPATH 'x' INTO TABLE y.b INPUTFORMAT 'y' SERDE 'z'
[tool_use Bash] {"command": "sed -n 2890,2920p sqlglot/generator.py; grep -n \"_parse_load\" -A40 sqlglot/parser.py | sed -n 1,60p; sed -n 205,230p tests/dialects/test_bigquery.py; grep -n \"class LoadData\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Inspect load generator, parser, and tests"}
[tool_result ERROR] Exit code 2
        delimiter = delimiter or self.dialect.QUOTE_END
        escaped_delimiter = escaped_delimiter or self._escaped_quote_end

        return self._replace_line_breaks(text).replace(delimiter, escaped_delimiter)

    def loaddata_sql(self, expression: exp.LoadData) -> str:
        is_overwrite = expression.args.get("overwrite")
        overwrite = " OVERWRITE" if is_overwrite else ""
        this = self.sql(expression, "this")

        files = expression.args.get("files")
        
…[5993 chars elided]…
qlglot/expressions/dml.py-284-        "local": False,
sqlglot/expressions/dml.py-285-        "overwrite": False,
sqlglot/expressions/dml.py-286-        "inpath": False,
sqlglot/expressions/dml.py-287-        "files": False,
sqlglot/expressions/dml.py-288-        "partition": False,
sqlglot/expressions/dml.py-289-        "input_format": False,
sqlglot/expressions/dml.py-290-        "serde": False,
sqlglot/expressions/dml.py-291-    }
sqlglot/expressions/dml.py-292-
sqlglot/expressions/dml.py-293-
[tool_use Bash] {"command": "grep -n \"def _match_texts\" -A8 sqlglot/parser.py; grep -n '\"TEMP' sqlglot/tokens.py sqlglot/dialects/bigquery.py | head; sed -n 3606,3612p sqlglot/parser.py", "description": "Check _match_texts helper and TEMP keywords"}
[tool_result] 1943:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1944-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1945-            if advance:
1946-                self._advance()
1947-            return True
1948-        return False
1949-
1950-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1951-        index = self._index
sqlglot/tokens.py:392:        "TEMP": TokenType.TEMPORARY,
sqlglot/tokens.py:393:        "TEMPORARY": TokenType.TEMPORARY,
                    input_format=self._match_text_seq("INPUTFORMAT") and self._parse_string(),
                    serde=self._match_text_seq("SERDE") and self._parse_string(),
                )
            )
        return self._parse_as_command(self._prev)

    def _parse_delete(self) -> exp.Delete:
[assistant] Both `TEMP` and `TEMPORARY` tokenize to `TokenType.TEMPORARY`, so the parser can match that token directly. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[167 chars elided]…
.OVERWRITE)\n            self._match(TokenType.INTO)\n            temporary = self._match(TokenType.TEMPORARY)\n            self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,\n        \"files\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,\n        \"files\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "        is_overwrite = expression.args.get(\"overwrite\")\n        overwrite = \" OVERWRITE\" if is_overwrite else \"\"\n        this = self.sql(expression, \"this\")\n\n        files = expression.args.get(\"files\")
…[588 chars elided]…
lat=True)\n            files_sql = f\"FILES{self.wrap(files_sql)}\"\n            temp = \" TEMP TABLE\" if expression.args.get(\"temporary\") else \"\"\n            if is_overwrite:\n                this = f\"{temp} {this}\" if temp else f\" {this}\"\n            else:\n                this = f\" INTO{temp or ' TABLE'} {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):", "new_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-121014-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\')','LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\')','LOAD DATA INTO TEMPORARY TABLE mydata
…[125 chars elided]…
    e = sqlglot.parse_one(s, read='bigquery'); print(type(e).__name__, e.sql('bigquery'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py tests/test_parser.py tests/test_transpile.py 2>&1 | tail -5", "description": "Verify round-trips and run related test files"}
[tool_result] LoadData LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
LoadData LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LoadData LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LoadData LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LoadData LOAD DATA OVERWRITE TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
.................................................................... [ 40%]
.............. [ 49%]
................................................................................... [ 99%]
.                                                                        [100%]
166 passed, 2643 subtests passed in 11.50s
[assistant] The targeted tests pass. Running the full suite, since the project's check covers all of it.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Run full test suite and show diff stat"}
[tool_result] ............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 59.35s
 sqlglot/expressions/dml.py      | 1 +
 sqlglot/generator.py            | 6 +++++-
 sqlglot/parser.py               | 5 ++++-
 tests/dialects/test_bigquery.py | 1 +
 4 files changed, 11 insertions(+), 2 deletions(-)
[assistant] `LOAD DATA INTO TEMP TABLE` now parses and round-trips in the BigQuery dialect, along with the two forms that already worked. The full test suite passes (1112 passed).

The three statements from your request round-trip unchanged:
- `LOAD DATA OVERWRITE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TABLE mydataset.table1 FROM FILES(...)`
- `LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(...)`

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): the `INTO TABLE` pair is now matched as separate optional tokens, with `TEMP`/`TEMPORARY` accepted between them. `TEMP` and `TEMPORARY` bot
…[652 chars elided]…
round-trips.** I'm not certain BigQuery allows `TEMP` with `OVERWRITE`, so I kept it parseable rather than rejecting it.
- **The parser is shared, not BigQuery-only.** `LOAD DATA` parsing lives in the base parser, so Hive-style input now also accepts `TEMP`. I left it there because `FILES` handling is already in the base parser. Moving the `TEMP` handling into the BigQuery dialect would need a dialect-level `_parse_load` override.
- **`INTO` without `TABLE` is now accepted.** The old code required `INTO TABLE` as a pair. The new code treats each keyword as optional, which is a small loosening.
