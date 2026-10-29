# trajectory base-1

final message:
The Snowflake `PATTERN` clause now survives round-tripping when there is no `FILE_FORMAT`. Your example gives `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`, and the full suite passes (1126 tests plus 18224 subtests).

The cause was in the generator, not the parser. `Generator.table_sql` in `sqlglot/generator.py` only wrote the parenthesised block when `format` was set, so a `pattern`-only table lost its `PATTERN`. The block is now emitted when either parameter is present, and each one is included independently:

- `(PATTERN => ...)` alone
- `(FILE_FORMAT => ...)` alone
- `(FILE_FORMAT => ..., PATTERN => ...)` together, with the same ordering as before

I also added a one-line `validate_identity` case for the `PATTERN`-only form in `tests/dialects/test_snowflake.py`. The existing both-present cases already cover the combined form. I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/dialects/snowflake.py | head -80", "description": "Find PATTERN and FILE_FORMAT handling in Snowflake dialect"}
[tool_result] 144:            "FILE FORMAT": TokenType.FILE_FORMAT,
[tool_use Bash] {"command": "grep -rn -i \"pattern\" sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/snowflake.py | grep -i \"pattern\\b\\|PATTERN\\|pattern=\" | head -30; grep -rn \"FILE_FORMAT\\|file_format\" sqlglot/ | head -30; grep -n \"class Table(\" -A 30 sqlglot/expressions.py | head -50", "description": "Search for PATTERN and FILE_FORMAT references in sqlglot source"}
[tool_result] sqlglot/parser.py:32:    from re import Pattern
sqlglot/parser.py:42:TIME_ZONE_RE: Pattern[str] = re.compile(r":.*?[a-zA-Z\+\-]")
sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:1777:    TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:4320:        if self._match_text_seq("PATTERN"):
sqlglot/parser.py:4341:            pattern = exp.var(self._find_sql(start, end))
sqlglot/parser.py:4343:            pattern = None
sqlglot/parser.py:4360:                patter
…[3836 chars elided]…
"
sqlglot/generators/hive.py:506:        file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
sqlglot/generators/hive.py:507:        file_format = f" FILEFORMAT {file_format}" if file_format else ""
sqlglot/generators/hive.py:513:        return f"SET{serde}{exprs}{location}{file_format}{tags}"
sqlglot/generators/snowflake.py:487:            f"FILE_FORMAT=({self.expressions(e, 'expressions', sep=' ')})"
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 1085,1112p sqlglot/parsers/snowflake.py; echo ----; sed -n 2405,2420p sqlglot/generator.py; echo ----; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => 'x')\\\"]:\n    e = sqlglot.parse_one(s, dialect='snowflake'); print(repr(e.args.get('from_').this.args) if False else e.sql(dialect='snowflake'))\n    print(e.find(sqlglot.exp.Table).args)\n\"", "description": "Inspect Snowflake stage table parsing and generator"}
[tool_result]             table = self._parse_string()
        elif self._match_text_seq("@", advance=False):
            table = self._parse_location_path()
        else:
            table = None

        if table:
            file_format = None
            pattern = None

            wrapped = self._match(TokenType.L_PAREN)
            while self._curr and wrapped and not self._match(TokenType.R_PAREN):
                if self._match_text_seq("FILE_FORMAT", "=>"):
                    file_format = self._par
…[1270 chars elided]…
            ordinality = f" WITH ORDINALITY{alias}"
----
SELECT * FROM @mystage
{'this': Var(this=@mystage), 'format': None, 'pattern': Literal(this='.*data-100.*', is_string=True)}
SELECT * FROM @mystage (FILE_FORMAT => 'ff')
{'this': Var(this=@mystage), 'format': Literal(this='ff', is_string=True), 'pattern': None}
SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => 'x')
{'this': Var(this=@mystage), 'format': Literal(this='ff', is_string=True), 'pattern': Literal(this='x', is_string=True)}
[assistant] The parser keeps `pattern`, but the generator only emits the parenthesised block when `format` is set. I'll make it emit when either is set.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-143037-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[50 chars elided]…
at}{pattern})\"", "new_string": "        file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        if file_format or pattern:\n            options = [f\"FILE_FORMAT => {file_format}\"] if file_format else []\n            if pattern:\n                options.append(f\"PATTERN => {pattern}\")\n            file_format = f\" ({', '.join(options)})\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-143037-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => 'x')\\\", 'SELECT * FROM @mystage']:\n    print(sqlglot.parse_one(s, dialect='snowflake').sql(dialect='snowflake'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Verify fix on examples and run the full test suite"}
[tool_result] SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @mystage (FILE_FORMAT => 'ff')
SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => 'x')
SELECT * FROM @mystage
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
...................................................... [ 40%]
...........................................................................
…[242 chars elided]…
....................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
............................................... [ 82%]
.................................... [ 86%]
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 51.88s
[assistant] All four cases round-trip correctly and the suite passes. Next I'll add a regression test next to the existing stage-file tests.
[tool_use Bash] {"command": "grep -n \"FILE_FORMAT =>\" tests/dialects/test_snowflake.py | head", "description": "Find existing stage FILE_FORMAT tests"}
[tool_result] 3432:        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
3436:            "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
3439:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
3442:            "SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t"
3453:            "SELECT * FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla",
3454:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla",
3458:            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
3459:            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
[tool_use Bash] {"command": "sed -n 3428,3446p tests/dialects/test_snowflake.py", "description": "Read stage tests around the FILE_FORMAT cases"}
[tool_result]         self.validate_identity("SELECT * FROM @mystage")
        self.validate_identity("SELECT * FROM '@mystage'")
        self.validate_identity("SELECT * FROM @namespace.mystage/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM @namespace.%table_name/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
        self.validate_identity("PUT file:///dir/tmp.csv @%table", check_command_warning=True)
        se
…[187 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-143037-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')\")\n        self.validate_identity(\"PUT", "new_string": "        self.validate_identity(\"SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')\")\n        self.validate_identity(\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\")\n        self.validate_identity(\"PUT"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-143037-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -3; git diff --stat", "description": "Rerun full test suite and show diff stat"}
[tool_result] .......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 58.55s
 sqlglot/generator.py             | 10 ++++++----
 tests/dialects/test_snowflake.py |  1 +
 2 files changed, 7 insertions(+), 4 deletions(-)
[assistant] The Snowflake `PATTERN` clause now survives round-tripping when there is no `FILE_FORMAT`. Your example gives `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`, and the full suite passes (1126 tests plus 18224 subtests).

The cause was in the generator, not the parser. `Generator.table_sql` in `sqlglot/generator.py` only wrote the parenthesised block when `format` was set, so a `pattern`-only table lost its `PATTERN`. The block is now emitted when either parameter is present, and each one is included independently:

- `(PATTERN => ...)` alone
- `(FILE_FORMAT => ...)` alone
- `(FILE_FORMAT => ..., PATTERN => ...)` together, with the same ordering as before

I also added a one-line `validate_identity` case for the `PATTERN`-only form in `tests/dialects/test_snowflake.py`. The existing both-present cases already cover the combined form. I didn't commit anything.
