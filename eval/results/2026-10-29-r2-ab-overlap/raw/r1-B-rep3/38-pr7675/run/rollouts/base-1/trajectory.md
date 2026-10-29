# trajectory base-1

final message:
`LOAD DATA INTO TEMP TABLE` and `LOAD DATA INTO TEMPORARY TABLE` now parse in the BigQuery dialect. All three forms from your list round-trip, and the full suite passes (1112 passed). I did not commit anything.

The fix adds a `temporary` flag to `exp.LoadData`, set by the parser when it sees `TEMP` or `TEMPORARY` (both tokenize to the same token). The generator writes `TEMP`, so `TEMPORARY` input comes back out as `TEMP`.

Changes:
- `sqlglot/expressions/dml.py`: new `temporary` arg on `LoadData`.
- `sqlglot/parser.py` (`_parse_load`): `INTO` and `TABLE` are now each optional, with `TEMPORARY` matched between them. This is in the shared base parser, so it also affects the Hive `LOAD DATA ... INTO TABLE` path, which still passes its existing tests.
- `sqlglot/generator.py` (`loaddata_sql`): emits `INTO TEMP TABLE` when the flag is set, in both the `FILES(...)` and Hive branches.
- `tests/dialects/test_bigquery.py`: added the `TEMP` round-trip to the existing LOAD DATA list, plus a `TEMPORARY` → `TEMP` normalization check.

One edge case: `LOAD DATA OVERWRITE TEMP TABLE x ...` parses, but the generator drops `TEMP` in the overwrite form. I did not verify that BigQuery accepts that combination, so I left it alone.

## events
[tool_use Bash] {"command": "grep -rn \"LOAD\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | grep -i \"load\" | head -50; grep -rn \"LOAD DATA\" tests/ | head", "description": "Find LOAD-related code and tests"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:716:        TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/parser.py:1622:    ISOLATED_LOADING_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {"FOR": ("ALL", "INSERT", "NONE")}
sqlglot/parser.py:3132:        if not self._match_text_seq("ISOLATED", "LOADING"):
sqlglot/parser.py:3136:        target = self._parse_var_from_options(self.ISOLATED_LOADING_OPTIONS, raise_unmatched=Fals
…[707 chars elided]…
es/identity.sql:710:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy')
tests/fixtures/identity.sql:711:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y'
tests/fixtures/identity.sql:712:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:713:LOAD DATA INPATH 'x' INTO TABLE y INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:714:LOAD DATA INPATH 'x' INTO TABLE y.b INPUTFORMAT 'y' SERDE 'z'
[tool_use Bash] {"command": "grep -n \"def _parse_load\" -A 40 sqlglot/parser.py; sed -n 2890,2920p sqlglot/generator.py; sed -n 205,230p tests/dialects/test_bigquery.py; grep -n \"class LoadData\" -A 12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Read LOAD parsing and generation code"}
[tool_result ERROR] Exit code 2
3589:    def _parse_load(self) -> exp.LoadData | exp.Command:
3590-        if self._match_text_seq("DATA"):
3591-            local = self._match_text_seq("LOCAL")
3592-            self._match_text_seq("INPATH")
3593-            inpath = self._parse_string()
3594-            overwrite = self._match(TokenType.OVERWRITE)
3595-            self._match_pair(TokenType.INTO, TokenType.TABLE)
3596-
3597-            return self.expression(
3598-                exp.LoadData(
3599-              
…[4514 chars elided]…
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
[tool_use Bash] {"command": "grep -n '\"TEMP' sqlglot/tokens.py sqlglot/dialects/bigquery.py | head; grep -n \"def _match_pair\" -A 8 sqlglot/parser.py; grep -rn \"LoadData\\|loaddata\" sqlglot/ | grep -v \"^sqlglot/expressions/dml.py:281\"", "description": "Check TEMP token mapping and LoadData usages"}
[tool_result] 2 matches in 1 files:

sqlglot/tokens.py:392:"TEMP": TokenType.TEMPORARY,
sqlglot/tokens.py:393:"TEMPORARY": TokenType.TEMPORARY,
1934:    def _match_pair(
1935-        self, token_type_a: TokenType, token_type_b: TokenType, advance: bool = True
1936-    ) -> bool:
1937-        if self._curr.token_type == token_type_a and self._next.token_type == token_type_b:
1938-            if advance:
1939-                self._advance(2)
1940-            return True
1941-        return False
1942-
sqlglot/parser.py:3589:    def _parse_load(self) -> exp.LoadData | exp.Command:
sqlglot/parser.py:3598:                exp.LoadData(
sqlglot/generator.py:2895:    def loaddata_sql(self, expression: exp.LoadData) -> str:
sqlglot/generators/singlestore.py:897:        "loaddata_where",
[assistant] Both `TEMP` and `TEMPORARY` tokenize to `TokenType.TEMPORARY`, so the parser can match either with one call. Making the edits now: a `temporary` arg on `LoadData`, parser handling, generator output, and tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,\n        \"files\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,\n        \"files\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[167 chars elided]…
.OVERWRITE)\n            self._match(TokenType.INTO)\n            temporary = self._match(TokenType.TEMPORARY)\n            self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "        is_overwrite = expression.args.get(\"overwrite\")\n        overwrite = \" OVERWRITE\" if is_overwrite else \"\"\n        this = self.sql(expression, \"this\")\n\n        files = expression.args.get(\"files\")
…[861 chars elided]…
       files_sql = f\"FILES{self.wrap(files_sql)}\"\n            this = f\" {this}\" if is_overwrite else f\" INTO{temporary} TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"\n\n        local = \" LOCAL\" if expression.args.get(\"local\") else \"\"\n        inpath = f\" INPATH {self.sql(expression, 'inpath')}\"\n        this = f\" INTO{temporary} TABLE {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):\n            with self.subTest(load_data_sql=load_data_sql):\n             
…[374 chars elided]…
ta_sql=load_data_sql):\n                self.validate_identity(load_data_sql).assert_is(exp.LoadData)\n        self.validate_identity(\n            \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-193410-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py tests/dialects/test_dialect.py tests/test_transpile.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['LOAD DATA OVERWRITE mydataset
…[87 chars elided]…
E a.b FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMP TABLE a.b FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMPORARY TABLE a.b FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])']:\n    print(sqlglot.transpile(s, read='bigquery', write='bigquery')[0])\n\"", "description": "Run BigQuery/Hive/dialect tests and round-trip checks"}
[tool_result] .................................................................... [ 34%]
..................................................................................................................................                      [100%]
198 passed, 5397 subtests passed in 1.06s
LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
LOAD DATA INTO TABLE a.b FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
LOAD DATA INTO TEMP TABLE a.b FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
LOAD DATA INTO TEMP TABLE a.b FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
[assistant] Targeted tests pass. Running the full project suite, since `LoadData` and the base parser are shared by every dialect.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ................ [ 53%]
............................................................................................................................................................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 46.51s
 M sqlglot/expressions/dml.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_bigquery.py
[assistant] `LOAD DATA INTO TEMP TABLE` and `LOAD DATA INTO TEMPORARY TABLE` now parse in the BigQuery dialect. All three forms from your list round-trip, and the full suite passes (1112 passed). I did not commit anything.

The fix adds a `temporary` flag to `exp.LoadData`, set by the parser when it sees `TEMP` or `TEMPORARY` (both tokenize to the same token). The generator writes `TEMP`, so `TEMPORARY` input comes back out as `TEMP`.

Changes:
- `sqlglot/expressions/dml.py`: new `temporary` arg on `LoadData`.
- `sqlglot/parser.py` (`_parse_load`): `INTO` and `TABLE` are now each optional, with `TEMPORARY
…[31 chars elided]…
 in the shared base parser, so it also affects the Hive `LOAD DATA ... INTO TABLE` path, which still passes its existing tests.
- `sqlglot/generator.py` (`loaddata_sql`): emits `INTO TEMP TABLE` when the flag is set, in both the `FILES(...)` and Hive branches.
- `tests/dialects/test_bigquery.py`: added the `TEMP` round-trip to the existing LOAD DATA list, plus a `TEMPORARY` → `TEMP` normalization check.

One edge case: `LOAD DATA OVERWRITE TEMP TABLE x ...` parses, but the generator drops `TEMP` in the overwrite form. I did not verify that BigQuery accepts that combination, so I left it alone.
