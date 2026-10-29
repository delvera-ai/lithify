# trajectory base-1

final message:
BigQuery `LOAD DATA INTO TEMP TABLE` and `INTO TEMPORARY TABLE` now parse and round-trip, along with the existing `OVERWRITE` and `INTO TABLE` forms. The full suite passes (1112 tests) and ruff is clean.

The cause was in the parser. It only accepted `INTO TABLE` as a pair, so `INTO TEMP TABLE` failed at `INTO`.

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): after `INTO`, an optional `TEMP`/`TEMPORARY` is consumed, then `TABLE`. The keyword is stored as a `Var` so `TEMP` and `TEMPORARY` each come back out unchanged.
- **`sqlglot/expressions/dml.py`**: added a `temporary` arg to `LoadData`.
- **`sqlglot/generator.py`** (`loaddata_sql`): emits `INTO TEMP TABLE` / `INTO TEMPORARY TABLE` on both the `FROM FILES(...)` path and the Hive path.
- **`tests/dialects/test_bigquery.py`**: added the two `INTO TEMP`/`INTO TEMPORARY` cases to the existing `LOAD DATA` loop. No existing test was changed.

Decisions to check:
- I kept `TEMP` vs `TEMPORARY` as written rather than normalizing one to the other, so both spellings are identity round-trips.
- `TEMP` is only accepted after `INTO`, not after `OVERWRITE`, since I didn't find that form in the BigQuery docs. Say if you want it supported.
- `INTO` followed by a bare table name, without `TABLE`, is now accepted. Previously it was a parse error.

## events
[tool_use Bash] {"command": "grep -rn -i \"load\" sqlglot/dialects/bigquery.py | head -50; grep -rn -i \"LOAD DATA\\|LOAD_DATA\\|\\\"LOAD\\\"\" tests/dialects/test_bigquery.py sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/dialect.py | head -30", "description": "Search for LOAD DATA handling in code and tests"}
[tool_result] sqlglot/tokens.py:329:        "LOAD": TokenType.LOAD,
tests/dialects/test_bigquery.py:217:        for load_data_sql in (
tests/dialects/test_bigquery.py:218:            "LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
tests/dialects/test_bigquery.py:219:            "LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
tests/dialects/test_bigquery.py:221:            with self.subTest(load_data_sql=load_data_sql):
tests/dialects/test_bigquery.py:222:                self.validate_identity(load_data_sql).assert_is(exp.LoadData)
[tool_use Bash] {"command": "grep -n \"LoadData\\|LOAD\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/*.py | head -40; sed -n 200,240p tests/dialects/test_bigquery.py", "description": "Find LoadData implementation and existing tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:716:        TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/parser.py:1622:    ISOLATED_LOADING_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {"FOR": ("ALL", "INSERT", "NONE")}
sqlglot/parser.py:3132:        if not self._match_text_seq("ISOLATED", "LOADING"):
sqlglot/parser.py:3136:        target = self._parse_var_from_options(self.ISOLATED_LOADING_OPTIONS, raise_unma
…[2875 chars elided]…
_identity("CAST(x AS NCHAR)", "CAST(x AS STRING)")
        self.validate_identity("CAST(x AS NVARCHAR)", "CAST(x AS STRING)")
        self.validate_identity("CAST(x AS TIMESTAMPTZ)", "CAST(x AS TIMESTAMP)")
        self.validate_identity("CAST(x AS RECORD)", "CAST(x AS STRUCT)")
        self.validate_identity("SELECT * FROM x WHERE x.y >= (SELECT MAX(a) FROM b-c) - 20")
        self.validate_identity(
            """WITH t AS (SELECT '{"x-y": "z"}' AS c) SELECT JSON_EXTRACT(c, '$.x-y') FROM t"""
[tool_use Bash] {"command": "sed -n 3585,3625p sqlglot/parser.py; sed -n 2893,2918p sqlglot/generator.py; grep -n \"class LoadData\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Read LOAD parser and generator code"}
[tool_result ERROR] Exit code 2
            kwargs["null"] = self._parse_string()

        return self.expression(exp.RowFormatDelimitedProperty(**kwargs))  # type: ignore

    def _parse_load(self) -> exp.LoadData | exp.Command:
        if self._match_text_seq("DATA"):
            local = self._match_text_seq("LOCAL")
            self._match_text_seq("INPATH")
            inpath = self._parse_string()
            overwrite = self._match(TokenType.OVERWRITE)
            self._match_pair(TokenType.INTO, TokenType.TA
…[2593 chars elided]…
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
[tool_use Bash] {"command": "grep -n '\"TEMP' sqlglot/tokens.py sqlglot/dialects/bigquery.py; grep -n \"def _match_texts\\|def _match_text_seq\" -A3 sqlglot/parser.py; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMPORARY TABLE a.b FROM FILES(FORMAT=\\'AVRO\\')']:\n  try: print(repr(sqlglot.parse_one(s, read='bigquery')))\n  except Exception as e: print('ERR', type(e), str(e)[:200])\n\"", "description": "Check TEMP token handling and reproduce parse failure"}
[tool_result] sqlglot/tokens.py:392:        "TEMP": TokenType.TEMPORARY,
sqlglot/tokens.py:393:        "TEMPORARY": TokenType.TEMPORARY,
1943:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1944-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1945-            if advance:
1946-                self._advance()
--
1950:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1951-        index = self._index
1952-      
…[46 chars elided]…
for text in texts:
ERR <class 'sqlglot.errors.ParseError'> Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
  LOAD DATA [4mINTO[0m TEMP TABLE mydataset.table1 FR
ERR <class 'sqlglot.errors.ParseError'> Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
  LOAD DATA [4mINTO[0m TEMPORARY TABLE a.b FROM FILES
[assistant] Reproduced: `INTO TEMP TABLE` and `INTO TEMPORARY TABLE` both fail at `INTO`, because the parser only accepts `INTO TABLE` as a pair. Both spellings tokenize as `TokenType.TEMPORARY`. I'll read the exact code before editing.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "offset": 3589, "limit": 18}
[tool_result] 3589	    def _parse_load(self) -> exp.LoadData | exp.Command:
3590	        if self._match_text_seq("DATA"):
3591	            local = self._match_text_seq("LOCAL")
3592	            self._match_text_seq("INPATH")
3593	            inpath = self._parse_string()
3594	            overwrite = self._match(TokenType.OVERWRITE)
3595	            self._match_pair(TokenType.INTO, TokenType.TABLE)
3596	
3597	            return self.expression(
3598	                exp.LoadData(
3599	                    this=self._parse_table(schema=True),
3600	                    local=local,
3601	                    overwrite=overwrite,
3602	                    inpath=inpath,
3603	                    files=self._match_text_seq("FROM", "FILES")
3604	                    and exp.Properties(expressions=self._parse_wrapped_properties()),
3605	                    partition=self._parse_partition(),
3606	                    input_format=self._match_text_seq("INPUTFORMAT") and self._parse_string(),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "offset": 2895, "limit": 24}
[tool_result] 2895	    def loaddata_sql(self, expression: exp.LoadData) -> str:
2896	        is_overwrite = expression.args.get("overwrite")
2897	        overwrite = " OVERWRITE" if is_overwrite else ""
2898	        this = self.sql(expression, "this")
2899	
2900	        files = expression.args.get("files")
2901	        if files:
2902	            files_sql = self.expressions(files, flat=True)
2903	            files_sql = f"FILES{self.wrap(files_sql)}"
2904	            this = f" {this}" if is_overwrite else f" 
…[292 chars elided]…
tion = self.sql(expression, "partition")
2911	        partition = f" {partition}" if partition else ""
2912	        input_format = self.sql(expression, "input_format")
2913	        input_format = f" INPUTFORMAT {input_format}" if input_format else ""
2914	        serde = self.sql(expression, "serde")
2915	        serde = f" SERDE {serde}" if serde else ""
2916	        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
2917	
2918	    def null_sql(self, *_) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "offset": 281, "limit": 13}
[tool_result] 281	class LoadData(Expression):
282	    arg_types = {
283	        "this": True,
284	        "local": False,
285	        "overwrite": False,
286	        "inpath": False,
287	        "files": False,
288	        "partition": False,
289	        "input_format": False,
290	        "serde": False,
291	    }
292	
293	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[238 chars elided]…
okenType.INTO):\n                temporary = self._match(TokenType.TEMPORARY) and exp.var(self._prev.text)\n                self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,\n        \"files\": False,\n        \"partition\": False,\n        \"input_format\": False,\n        \"serde\": False,\n    }\n", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,\n        \"files\": False,\n        \"partition\": False,\n        \"input_format\": False,\n        \"serde\": False,\n    }\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "        this = self.sql(expression, \"this\")\n\n        files = expression.args.get(\"files\")\n        if files:\n            files_sql = self.expressions(files, flat=True)\n            files_sql = f\"FILES{self.wr
…[659 chars elided]…
       files_sql = f\"FILES{self.wrap(files_sql)}\"\n            this = f\" {this}\" if is_overwrite else f\" INTO{temporary} TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"\n\n        local = \" LOCAL\" if expression.args.get(\"local\") else \"\"\n        inpath = f\" INPATH {self.sql(expression, 'inpath')}\"\n        this = f\" INTO{temporary} TABLE {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):", "new_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094012-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[assistant] Edits are in. Now I'll run the project's test command, plus a targeted check of the Hive `LOAD DATA` path since the parser change touches it too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run bigquery, hive, and full test suites"}
[tool_result] ................... [ 26%]
.............................. [ 68%]
............... [ 88%]
........ [100%]
72 passed, 1551 subtests passed in 0.61s
................ [ 53%]
............................................................................... [ 60%]
...................... [ 62%]
........................................................................................................................ [ 73%]
............................................. [ 77%]
............................................................................................................................................................................................... [ 94%]
........................................................                                                [100%]
1112 passed, 18137 subtests passed in 53.29s
[assistant] All 1112 tests pass. I'll run the linter on the changed files too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/dml.py tests/dialects/test_bigquery.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 sqlglot/expressions/dml.py      | 1 +
 sqlglot/generator.py            | 6 ++++--
 sqlglot/parser.py               | 6 +++++-
 tests/dialects/test_bigquery.py | 2 ++
 4 files changed, 12 insertions(+), 3 deletions(-)
[assistant] BigQuery `LOAD DATA INTO TEMP TABLE` and `INTO TEMPORARY TABLE` now parse and round-trip, along with the existing `OVERWRITE` and `INTO TABLE` forms. The full suite passes (1112 tests) and ruff is clean.

The cause was in the parser. It only accepted `INTO TABLE` as a pair, so `INTO TEMP TABLE` failed at `INTO`.

Changes:
- **`sqlglot/parser.py`** (`_parse_load`): after `INTO`, an optional `TEMP`/`TEMPORARY` is consumed, then `TABLE`. The keyword is stored as a `Var` so `TEMP` and `TEMPORARY` each come back out unchanged.
- **`sqlglot/expressions/dml.py`**: added a `temporary` arg to `LoadData
…[107 chars elided]…
the `FROM FILES(...)` path and the Hive path.
- **`tests/dialects/test_bigquery.py`**: added the two `INTO TEMP`/`INTO TEMPORARY` cases to the existing `LOAD DATA` loop. No existing test was changed.

Decisions to check:
- I kept `TEMP` vs `TEMPORARY` as written rather than normalizing one to the other, so both spellings are identity round-trips.
- `TEMP` is only accepted after `INTO`, not after `OVERWRITE`, since I didn't find that form in the BigQuery docs. Say if you want it supported.
- `INTO` followed by a bare table name, without `TABLE`, is now accepted. Previously it was a parse error.
