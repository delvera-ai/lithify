# trajectory base-1

final message:
Fixed: `PATTERN` is now kept on a staged-file table when there is no `FILE_FORMAT`. Your repro now round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The full test suite passes (1126 tests), and ruff format and lint are clean on the changed files.

**Cause:** the table generator in `sqlglot/generator.py` only emitted the parenthesized clause inside `if file_format:`, so `PATTERN` was dropped whenever `FILE_FORMAT` was absent. The parser already captured `PATTERN` correctly.

**Change:** the generator now builds the parameter list from each optional argument independently, so `FILE_FORMAT` and `PATTERN` each appear on their own or together, in the same order as before.

**Tests:** I added two round-trip cases to `tests/dialects/test_snowflake.py`, next to the existing `FILE_FORMAT` + `PATTERN` test:
- `PATTERN` only
- `FILE_FORMAT` only

The `FILE_FORMAT` + `PATTERN` case already covered the combined form.

This is a shared generator path, so other dialects that render `exp.Table` with `pattern` set will now also emit the clause. I didn't find any other dialect producing that arg, and the full suite passes.

I haven't committed anything.

## events
[assistant] I'll start by finding where Snowflake handles staged-file tables and the `PATTERN` parameter.
[tool_use Bash] {"command": "grep -rn -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/*.py | grep -v \"re.compile\\|regexp\\|REGEXP\" | head -80", "description": "Search for PATTERN and FILE_FORMAT handling"}
[tool_use Bash] {"command": "grep -rn -i \"stage\" tests/dialects/test_snowflake.py | head -40", "description": "Find existing Snowflake stage tests"}
[tool_result] tests/dialects/test_snowflake.py:643:        self.validate_identity("RM @parquet_stage", check_command_warning=True)
tests/dialects/test_snowflake.py:644:        self.validate_identity("REMOVE @parquet_stage", check_command_warning=True)
tests/dialects/test_snowflake.py:848:        self.validate_identity("SELECT FILE_URL FROM DIRECTORY(@mystage) WHERE SIZE > 100000").args[
tests/dialects/test_snowflake.py:850:        ].this.this.assert_is(exp.DirectoryStage).this.assert_is(exp.Var)
tests/dialect
…[3695 chars elided]…

tests/dialects/test_snowflake.py:5527:            """COPY INTO temp FROM @random_stage/path/ FILE_FORMAT = (TYPE=CSV FIELD_DELIMITER='|' NULL_IF=('str1', 'str2') FIELD_OPTIONALLY_ENCLOSED_BY='"' TIMESTAMP_FORMAT='TZHTZM YYYY-MM-DD HH24:MI:SS.FF9' DATE_FORMAT='TZHTZM YYYY-MM-DD HH24:MI:SS.FF9' BINARY_FORMAT=BASE64) VALIDATION_MODE = 'RETURN_3_ROWS'"""
tests/dialects/test_snowflake.py:5539:            """COPY INTO @my_stage/result/data FROM (SELECT * FROM orderstiny) FILE_FORMAT = (TYPE='csv')"""
[tool_result] sqlglot/parsers/snowflake.py:770:        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
sqlglot/parsers/snowflake.py:1092:            file_format = None
sqlglot/parsers/snowflake.py:1093:            pattern = None
sqlglot/parsers/snowflake.py:1097:                if self._match_text_seq("FILE_FORMAT", "=>"):
sqlglot/parsers/snowflake.py:1098:                    file_format = self._parse_string() or super()._parse_table_parts(
sqlglot/parsers/snowflake.py:1101:                eli
…[3479 chars elided]…
   elif self._match_text_seq("STAGE_FILE_FORMAT"):
sqlglot/parser.py:8880:            alter_set.set("file_format", self._parse_wrapped_options())
sqlglot/parser.py:9551:                # Snowflake FILE_FORMAT case, Databricks COPY & FORMAT options
sqlglot/parser.py:9553:            elif prev == "FILE_FORMAT":
sqlglot/parser.py:9788:        # for FILE_FORMAT = <format_name>
sqlglot/expressions/string.py:106:    arg_types = {"this": True, "expression": True, "fill_pattern": False, "is_left": True}
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "offset": 2400, "limit": 45}
[tool_result] 2400	            pre_alias = f"{pre_alias}{version}"
2401	        else:
2402	            post_alias = f"{post_alias}{version}"
2403	
2404	        hints = self.expressions(expression, key="hints", sep=" ")
2405	        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
2406	        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
2407	        joins = self.indent(
2408	            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
2409	      
…[1054 chars elided]…
not None:
2436	            indexed = f" INDEXED BY {self.sql(indexed)}" if indexed else " NOT INDEXED"
2437	        else:
2438	            indexed = ""
2439	
2440	        return f"{only}{table}{changes}{partition}{file_format}{pre_alias}{alias}{indexed}{hints}{pivots}{post_alias}{joins}{laterals}{ordinality}"
2441	
2442	    def tablefromrows_sql(self, expression: exp.TableFromRows) -> str:
2443	        table = self.func("TABLE", expression.this)
2444	        alias = self.sql(expression, "alias")
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/sqlglot/parsers/snowflake.py", "offset": 1080, "limit": 40}
[tool_result] 1080	        wildcard: bool = False,
1081	        fast: bool = False,
1082	    ) -> exp.Table | exp.Dot | None:
1083	        # https://docs.snowflake.com/en/user-guide/querying-stage
1084	        if self._match(TokenType.STRING, advance=False):
1085	            table = self._parse_string()
1086	        elif self._match_text_seq("@", advance=False):
1087	            table = self._parse_location_path()
1088	        else:
1089	            table = None
1090	
1091	        if table:
1092	            f
…[584 chars elided]…
    else:
1104	                    break
1105	
1106	                self._match(TokenType.COMMA)
1107	
1108	            table = self.expression(exp.Table(this=table, format=file_format, pattern=pattern))
1109	        else:
1110	            table = super()._parse_table_parts(
1111	                schema=schema,
1112	                is_db_reference=is_db_reference,
1113	                fast=fast,
1114	            )
1115	
1116	        return table
1117	
1118	    def _parse_table(
1119	        self,
[assistant] The bug is in the base generator: `pattern` is only emitted inside the `if file_format:` branch, so a `PATTERN`-only table loses it. I'll emit each parameter independently and add a test next to the existing `FILE_FORMAT` + `PATTERN` case.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[52 chars elided]…
}{pattern})\"", "new_string": "        file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        stage_params = [\n            *([f\"FILE_FORMAT => {file_format}\"] if file_format else []),\n            *([f\"PATTERN => {pattern}\"] if pattern else []),\n        ]\n        file_format = f\" ({', '.join(stage_params)})\" if stage_params else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "offset": 3436, "limit": 12}
[tool_result] 3436	            "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
3437	        )
3438	        self.validate_identity(
3439	            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
3440	        )
3441	        self.validate_identity(
3442	            "SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t"
3443	        )
3444	        self.validate_identity(
3445	            "SELECT parse_json($1):a.b FROM @mystage2/data1.json.gz",
3446	            "SELECT GET_PATH(PARSE_JSON($1), 'a.b') FROM @mystage2/data1.json.gz",
3447	        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n        self.validate_identity(\n            
…[173 chars elided]…
'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (FILE_FORMAT => 'myformat') AS t\",\n        )\n        self.validate_identity(\n            \"SELECT parse_json($1):a.b FROM @mystage2/data1.json.gz\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103050-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now I'll run the Snowflake tests and the full suite using the project's test command from its memory notes.
[tool_use Bash] {"command": "(ls <work>/env-sqlglot/bin/python >/dev/null 2>&1 && PY=<work>/env-sqlglot/bin/python || PY=python3; $PY -m pytest -q -p no:cacheprovider --col
…[111 chars elided]…
tail -8; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", dialect='snowflake').sql(dialect='snowflake'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')\\\", dialect='snowflake').sql(dialect='snowflake'))\n\")", "description": "Run Snowflake tests, full suite, and repro check", "timeout": 600000}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.67s
.......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 51.57s
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'p')
[assistant] Tests pass and the repro is fixed. I'll run the linter on the two changed files as well.
[tool_use Bash] {"command": "(ruff format --check sqlglot/generator.py tests/dialects/test_snowflake.py && ruff check sqlglot/generator.py tests/dialects/test_snowflake.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] 2 files already formatted
All checks passed!
 sqlglot/generator.py             | 10 ++++++----
 tests/dialects/test_snowflake.py |  6 ++++++
 2 files changed, 12 insertions(+), 4 deletions(-)
[assistant] Fixed: `PATTERN` is now kept on a staged-file table when there is no `FILE_FORMAT`. Your repro now round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The full test suite passes (1126 tests), and ruff format and lint are clean on the changed files.

**Cause:** the table generator in `sqlglot/generator.py` only emitted the parenthesized clause inside `if file_format:`, so `PATTERN` was dropped whenever `FILE_FORMAT` was absent. The parser already captured `PATTERN` correctly.

**Change:** the generator now builds the parameter list from each optional argument independently, so `FILE_FORMAT` and `PATTERN` each appear on their own or together, in the same order as before.

**Tests:** I added two round-trip cases to `tests/dialects/test_snowflake.py`, next to the existing `FILE_FORMAT` + `PATTERN` test:
- `PATTERN` only
- `FILE_FORMAT` only

The `FILE_FORMAT` + `PATTERN` case already covered the combined form.

This is a shared generator path, so other dialects that render `exp.Table` with `pattern` set will now also emit the clause. I didn't find any other dialect producing that arg, and the full suite passes.

I haven't committed anything.
