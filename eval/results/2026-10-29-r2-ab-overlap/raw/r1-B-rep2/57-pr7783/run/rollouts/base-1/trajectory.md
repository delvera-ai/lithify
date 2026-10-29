# trajectory base-1

final message:
The `PATTERN` clause is now kept on staged-file queries when there is no `FILE_FORMAT`. Your example round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`.

**Cause:** The parser already stored `pattern` on the `Table` node. The generator emitted `PATTERN` only inside the `if file_format:` branch, so it was dropped when no format was given.

**Fix** (`sqlglot/generator.py`): `FILE_FORMAT` and `PATTERN` are now collected independently and joined into one parenthesised clause. Output for each case:
- `FILE_FORMAT` only: `(FILE_FORMAT => 'ff')`, unchanged.
- `PATTERN` only: `(PATTERN => '...')`, previously dropped.
- Both: `(FILE_FORMAT => 'ff', PATTERN => '...')`, unchanged.

**Tests** (`tests/dialects/test_snowflake.py`): I added round-trip cases for `PATTERN` alone, with and without an alias. The existing cases already cover `FILE_FORMAT` alone and both together.

**Verification:** The full suite passes (1126 tests, 18224 subtests). `ruff format --check` and `ruff check` are clean on both edited files. I did not run `make check`, which also runs mypy.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/generator.py sqlglot/tokens.py | head -60; grep -rn \"class Table\\b\\|class Table(\" sqlglot/expressions.py sqlglot/expressions/*.py 2>/dev/null | head", "description": "Search for PATTERN and FILE_FORMAT handling"}
[tool_result] sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/parser.py:32:    from re import Pattern
sqlglot/parser.py:42:TIME_ZONE_RE: Pattern[str] = re.compile(r":.*?[a-zA-Z\+\-]")
sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:622:        TokenType.FILE_FORMAT,
sqlglot/parser.py:1701:        "FILE_FORMAT",
sqlglot/parser.py:1777:    TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:4320:        if self._match_text_seq("PATT
…[2254 chars elided]…
:5341:            sep = " " if upper == "FILE_FORMAT" else ", "
sqlglot/generator.py:5480:        fill_pattern = self.sql(expression, "fill_pattern") or None
sqlglot/generator.py:5481:        if not fill_pattern and self.PAD_FILL_PATTERN_IS_REQUIRED:
sqlglot/generator.py:5482:            fill_pattern = "' '"
sqlglot/generator.py:5484:        return self.func(f"{prefix}PAD", expression.this, expression.expression, fill_pattern)
sqlglot/expressions/query.py:943:class Table(Expression, Selectable):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => '.*x.*')\\\"]:\n    e = sqlglot.parse_one(s, dialect='snowflake')\n    print(repr(e.args['from'].this))\n    print(e.sql(dialect='snowflake'))\n\"", "description": "Reproduce the PATTERN drop and inspect the AST"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'from'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => '.*x.*')\\\"]:\n    e = sqlglot.parse_one(s, dialect='snowflake')\n    t = e.find(sqlglot.exp.Table)\n    print(repr(t))\n    print(e.sql(dialect='snowflake'))\n\" ; sed -n 4300,4370p sqlglot/parser.py; sed -n 2400,2420p sqlglot/generator.py; sed -n 9540,9560p sqlglot/parser.py; sed -n 9780,9800p sqlglot/parser.py", "description": "Dump Table AST and relevant parser/generator code"}
[tool_result] Table(
  this=Var(this=@mystage),
  pattern=Literal(this='.*data-100.*', is_string=True))
SELECT * FROM @mystage
Table(
  this=Var(this=@mystage),
  format=Literal(this='ff', is_string=True))
SELECT * FROM @mystage (FILE_FORMAT => 'ff')
Table(
  this=Var(this=@mystage),
  format=Literal(this='ff', is_string=True),
  pattern=Literal(this='.*x.*', is_string=True))
SELECT * FROM @mystage (FILE_FORMAT => 'ff', PATTERN => '.*x.*')
            elif self._match_text_seq("WITH", "UNMATCHED", "ROWS"):
  
…[4449 chars elided]…
FILE_FORMAT = <format_name>
        return self.expression(
            exp.Property(
                this=exp.var("FORMAT_NAME"), value=self._parse_string() or self._parse_table_parts()
            )
        )

    def _parse_max_min_by(self, expr_type: type[exp.AggFunc]) -> exp.AggFunc:
        args: list[exp.Expr] = []

        if self._match(TokenType.DISTINCT):
            args.append(self.expression(exp.Distinct(expressions=[self._parse_lambda()])))
            self._match(TokenType.COMMA)
[assistant] The parser already stores `pattern` on the `Table` node. The bug is in the generator: the `PATTERN` branch is nested under `if file_format:`, so it's skipped when there's no format. I'll restructure so each parameter is emitted on its own.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-170610-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[70 chars elided]…
ew_string": "        file_format_params = []\n        if file_format := self.sql(expression, \"format\"):\n            file_format_params.append(f\"FILE_FORMAT => {file_format}\")\n        if pattern := self.sql(expression, \"pattern\"):\n            file_format_params.append(f\"PATTERN => {pattern}\")\n        file_format = f\" ({', '.join(file_format_params)})\" if file_format_params else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-170610-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Next I'll find the existing staged-file tests so I can add a regression case next to them.
[tool_use Bash] {"command": "grep -rn \"PATTERN =>\\|FILE_FORMAT =>\" tests/ | head -20", "description": "Find existing tests for staged-file FILE_FORMAT/PATTERN"}
[tool_result] tests/dialects/test_snowflake.py:3432:        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
tests/dialects/test_snowflake.py:3436:            "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
tests/dialects/test_snowflake.py:3439:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
tests/dialects/test_snowflake.py:3442:            "SELECT t.$1, t.$2 FROM @mysta
…[130 chars elided]…
FROM @foo/bar (PATTERN => 'test', FILE_FORMAT => ds_sandbox.test.my_csv_format) AS bla",
tests/dialects/test_snowflake.py:3454:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla",
tests/dialects/test_snowflake.py:3458:            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
tests/dialects/test_snowflake.py:3459:            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
[tool_use Bash] {"command": "sed -n 3428,3465p tests/dialects/test_snowflake.py", "description": "View existing staged-file tests"}
[tool_result]         self.validate_identity("SELECT * FROM @mystage")
        self.validate_identity("SELECT * FROM '@mystage'")
        self.validate_identity("SELECT * FROM @namespace.mystage/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM @namespace.%table_name/path/to/file.json.gz")
        self.validate_identity("SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv')")
        self.validate_identity("PUT file:///dir/tmp.csv @%table", check_command_warning=True)
        se
…[1063 chars elided]…
RN => 'test') AS bla",
        )

        self.validate_identity(
            "SELECT * FROM @test.public.thing/location/somefile.csv( FILE_FORMAT => 'fmt' )",
            "SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')",
        )

    def test_sample(self):
        self.validate_identity("SELECT * FROM testtable TABLESAMPLE BERNOULLI (20.3)")
        self.validate_identity("SELECT * FROM testtable TABLESAMPLE SYSTEM (3) SEED (82)")
        self.validate_identity(
[assistant] I'll add round-trip tests for the `PATTERN`-only case and for the issue's exact query.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-170610-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')\",\n        )\n\n    def test_sample(self):", "new_string": "            \"SELECT * FROM @test.public.thing/location/somefile.csv (FILE_FORMAT => 'fmt')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*') AS t\",\n        )\n\n    def test_sample(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-170610-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", dialect='snowflake').sql(dialect='snowflake'))\"", "description": "Run Snowflake dialect tests and verify the issue query"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.58s
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
[assistant] The Snowflake tests pass and the issue query now round-trips. Running the full suite as the final gate, plus a lint check on the two edited files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; (command -v ruff >/dev/null && ruff format --check sqlglot/generator.py tests/dialects/test_snowflake.py && ruff check sqlglot/generator.py tests/dialects/test_snowflake.py) 2>&1 | tail -5; git diff --stat", "description": "Run full test suite, lint edited files, show diff stat"}
[tool_result] ............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 46.37s
2 files already formatted
Ruff: No issues found
sqlglot/generator.py             | 11 ++++++-----
 tests/dialects/test_snowflake.py |  6 ++++++
 2 files changed, 12 insertions(+), 5 deletions(-)
[assistant] The `PATTERN` clause is now kept on staged-file queries when there is no `FILE_FORMAT`. Your example round-trips as `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`.

**Cause:** The parser already stored `pattern` on the `Table` node. The generator emitted `PATTERN` only inside the `if file_format:` branch, so it was dropped when no format was given.

**Fix** (`sqlglot/generator.py`): `FILE_FORMAT` and `PATTERN` are now collected independently and joined into one parenthesised clause. Output for each case:
- `FILE_FORMAT` only: `(FILE_FORMAT => 'ff')`, unchanged.
- `PATTERN` only: `(PATTERN => '...')`, previously dropped.
- Both: `(FILE_FORMAT => 'ff', PATTERN => '...')`, unchanged.

**Tests** (`tests/dialects/test_snowflake.py`): I added round-trip cases for `PATTERN` alone, with and without an alias. The existing cases already cover `FILE_FORMAT` alone and both together.

**Verification:** The full suite passes (1126 tests, 18224 subtests). `ruff format --check` and `ruff check` are clean on both edited files. I did not run `make check`, which also runs mypy.

I did not commit anything.
