# trajectory base-1

final message:
The `PATTERN` clause is now preserved on a staged-file query when there is no `FILE_FORMAT`. Your example outputs `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`, and the full suite passes (1126 tests).

The cause was in the generator (`sqlglot/generator.py`). It only wrote the parenthesized options block when `FILE_FORMAT` was set, so a lone `PATTERN` was dropped. It now builds the option list from whichever of the two is present, so `FILE_FORMAT` and `PATTERN` each survive alone or together.

I added two round-trip checks to `test_staged_files` in `tests/dialects/test_snowflake.py`: one for `PATTERN` alone and one for `FILE_FORMAT` alone. The existing combined case still passes unchanged. I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"PATTERN\\|FILE_FORMAT\\|FileFormat\\|def _parse_table_parts\\|StageFile\\|stage\" sqlglot/dialects/snowflake.py | head -80", "description": "Find staged-file handling in Snowflake dialect"}
[tool_result] 1 matches in 1 files:

144:0:TokenType.FILE_FORMAT,
[tool_use Bash] {"command": "grep -rn \"PATTERN\\|FILE_FORMAT\\|FileFormat\\|file_format\" sqlglot/ | grep -v \"^sqlglot/dialects/dialect\" | head -50; grep -rn \"@mystage\\|stage\" tests/dialects/test_snowflake.py | head -30", "description": "Search for PATTERN and FILE_FORMAT handling"}
[tool_result] sqlglot/parsers/spark2.py:21:    TRIM_PATTERN_FIRST = True
sqlglot/parsers/hive.py:266:        return self._parse_property_assignment(exp.FileFormatProperty)
sqlglot/parsers/snowflake.py:770:        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
sqlglot/parsers/snowflake.py:1092:            file_format = None
sqlglot/parsers/snowflake.py:1097:                if self._match_text_seq("FILE_FORMAT", "=>"):
sqlglot/parsers/snowflake.py:1098:                    file_format = self._pa
…[6854 chars elided]…
3:            "CREATE STAGE stage1 FILE_FORMAT=schema1.format1",
tests/dialects/test_snowflake.py:4284:            "CREATE STAGE stage1 FILE_FORMAT=(FORMAT_NAME=schema1.format1)",
tests/dialects/test_snowflake.py:4287:            self.parse_one("CREATE STAGE stage1 FILE_FORMAT=123", dialect="snowflake")
tests/dialects/test_snowflake.py:5245:    def test_show_stages(self):
tests/dialects/test_snowflake.py:5525:        self.validate_identity("COPY INTO test (c1) FROM (SELECT $1.c1 FROM @mystage)")
[tool_use Bash] {"command": "sed -n 1080,1115p sqlglot/parsers/snowflake.py; echo ----; sed -n 2400,2420p sqlglot/generator.py; echo ----; sed -n 3436,3446p tests/dialects/test_snowflake.py", "description": "View staged-file parse and generate code and test"}
[tool_result]         wildcard: bool = False,
        fast: bool = False,
    ) -> exp.Table | exp.Dot | None:
        # https://docs.snowflake.com/en/user-guide/querying-stage
        if self._match(TokenType.STRING, advance=False):
            table = self._parse_string()
        elif self._match_text_seq("@", advance=False):
            table = self._parse_location_path()
        else:
            table = None

        if table:
            file_format = None
            pattern = None

            wrapped
…[1865 chars elided]…
        )
        self.validate_identity(
            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
        )
        self.validate_identity(
            "SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t"
        )
        self.validate_identity(
            "SELECT parse_json($1):a.b FROM @mystage2/data1.json.gz",
            "SELECT GET_PATH(PARSE_JSON($1), 'a.b') FROM @mystage2/data1.json.gz",
[assistant] The generator only emits the parenthesized options block when `format` is set, so a lone `pattern` is dropped. I'll make it emit whichever of the two options is present.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203914-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[90 chars elided]…
 file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        if file_format or pattern:\n            options = []\n            if file_format:\n                options.append(f\"FILE_FORMAT => {file_format}\")\n            if pattern:\n                options.append(f\"PATTERN => {pattern}\")\n            file_format = f\" ({', '.join(options)})\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203914-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add regression tests for the PATTERN-only case and the FILE_FORMAT-only case next to the existing staged-file tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203914-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )", "new_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (FILE_FORMAT => 'myformat')\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203914-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", dialect='snowflake').sql(dialect='snowflake'))\"", "description": "Run Snowflake tests and check the reported example"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.63s
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
[assistant] The Snowflake tests pass and the reported example now round-trips. I'll run the full project suite to check the generator change doesn't affect other dialects.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; git diff --stat", "description": "Run full test suite and show diff stats"}
[tool_result] .......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 46.94s
sqlglot/generator.py             | 12 ++++++++----
 tests/dialects/test_snowflake.py |  6 ++++++
 2 files changed, 14 insertions(+), 4 deletions(-)
[assistant] The `PATTERN` clause is now preserved on a staged-file query when there is no `FILE_FORMAT`. Your example outputs `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`, and the full suite passes (1126 tests).

The cause was in the generator (`sqlglot/generator.py`). It only wrote the parenthesized options block when `FILE_FORMAT` was set, so a lone `PATTERN` was dropped. It now builds the option list from whichever of the two is present, so `FILE_FORMAT` and `PATTERN` each survive alone or together.

I added two round-trip checks to `test_staged_files` in `tests/dialects/test_snowflake.py`: one for `PATTERN` alone and one for `FILE_FORMAT` alone. The existing combined case still passes unchanged. I haven't committed anything.
