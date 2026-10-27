# trajectory base-1

final message:
Fixed. `PATTERN` is now emitted on its own, whether or not `FILE_FORMAT` is present.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')    # was: SELECT * FROM @mystage
SELECT * FROM @s (FILE_FORMAT => f, PATTERN => 'p')   # unchanged
SELECT * FROM @s (FILE_FORMAT => f)                   # unchanged
```

**Cause:** the parser already stored `pattern` correctly. In `sqlglot/generator.py` (`table_sql`), the `PATTERN` emission sat inside the `if file_format:` block, so a pattern without a format was never written out.

**Change:**
- `sqlglot/generator.py`: `pattern` is read independently. If either option is set, the generator builds the parenthesised list from whichever of `FILE_FORMAT` and `PATTERN` are present.
- `tests/dialects/test_snowflake.py`: added a round-trip `validate_identity` for `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The existing `FILE_FORMAT` + `PATTERN` cases still pass unchanged.

**Verification:** the full suite passes with the project's test command (1126 passed, 18224 subtests). I did not run the linter or commit anything.

## events
[tool_use Bash] {"command": "grep -n -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/dialects/snowflake.py | head -80", "description": "Find PATTERN and FILE_FORMAT handling in snowflake dialect"}
[tool_result] 144:            "FILE FORMAT": TokenType.FILE_FORMAT,
[tool_use Bash] {"command": "grep -rn -i \"pattern\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/snowflake.py | grep -i \"stage\\|pattern\\|FileFormat\\|file_format\" | head -40; grep -rn -i \"FILE_FORMAT\\|FileFormat\\|file_format\" sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/snowflake.py | head -40", "description": "Search parser, generator, expressions for file format and pattern"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/parser.py:32:    from re import Pattern
sqlglot/parser.py:42:TIME_ZONE_RE: Pattern[str] = re.compile(r":.*?[a-zA-Z\+\-]")
sqlglot/parser.py:137:        fill_pattern=seq_get(args, 2),
sqlglot/parser.py:1777:    TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:4320:        if self._match_text_seq("PATTERN"):
sqlglot/parser.py:4341:            pattern = exp.var(self._find_sql(start, end))
sqlglot/parser.py:4343:      
…[3005 chars elided]…
qlglot/generator.py:2413:        if file_format:
sqlglot/generator.py:2416:            file_format = f" (FILE_FORMAT => {file_format}{pattern})"
sqlglot/generator.py:2440:        return f"{only}{table}{changes}{partition}{file_format}{pre_alias}{alias}{indexed}{hints}{pivots}{post_alias}{joins}{laterals}{ordinality}"
sqlglot/generator.py:5340:            # Snowflake FILE_FORMAT options are separated by whitespace
sqlglot/generator.py:5341:            sep = " " if upper == "FILE_FORMAT" else ", "
[tool_use Bash] {"command": "sed -n 2400,2425p sqlglot/generator.py; grep -n \"PATTERN\\|FILE_FORMAT\" tests/dialects/test_snowflake.py | head -30; sed -n 9775,9800p sqlglot/parser.py", "description": "Inspect generator table sql and related tests"}
[tool_result]             pre_alias = f"{pre_alias}{version}"
        else:
            post_alias = f"{post_alias}{version}"

        hints = self.expressions(expression, key="hints", sep=" ")
        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        joins = self.indent(
            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
        )
        laterals = self.expressions(expression
…[4890 chars elided]…
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
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\ne=sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", dialect='snowflake')\nprint(repr(e.find(sqlglot.exp.Table).args))\nprint(e.sql(dialect='snowflake'))\" 2>&1 | tail -5", "description": "Reproduce the bug and inspect parsed table args"}
[tool_result] <work>/env-sqlglot/bin/python
{'this': Var(this=@mystage), 'format': None, 'pattern': Literal(this='.*data-100.*', is_string=True)}
SELECT * FROM @mystage
[assistant] The parser captures `pattern` correctly; the generator drops it because the `PATTERN` emission sits inside the `if file_format:` block. I'll fix the generator so each option is emitted on its own.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195026-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[90 chars elided]…
 file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        if file_format or pattern:\n            options = []\n            if file_format:\n                options.append(f\"FILE_FORMAT => {file_format}\")\n            if pattern:\n                options.append(f\"PATTERN => {pattern}\")\n            file_format = f\" ({', '.join(options)})\""}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195026-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Next I'll add tests for the standalone PATTERN case, then run the repro and the test suite.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195026-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "offset": 3436, "limit": 12}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-195026-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n", "new_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-195026-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.parse_one(\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", dialect='snowflake').sql(dialect='snowflake'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM @s (PATTERN => 'p', FILE_FORMA
…[24 chars elided]…
owflake').sql(dialect='snowflake'))\nprint(sqlglot.parse_one(\\\"SELECT * FROM @s (FILE_FORMAT => f)\\\", dialect='snowflake').sql(dialect='snowflake'))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -3 && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify repro output and run snowflake and full test suites"}
[tool_result] SELECT * FROM @mystage (PATTERN => '.*data-100.*')
SELECT * FROM @s (FILE_FORMAT => f, PATTERN => 'p')
SELECT * FROM @s (FILE_FORMAT => f)
............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.63s
............................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
.............                   [100%]
1126 passed, 18224 subtests passed in 59.34s
[assistant] Fixed. `PATTERN` is now emitted on its own, whether or not `FILE_FORMAT` is present.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')    # was: SELECT * FROM @mystage
SELECT * FROM @s (FILE_FORMAT => f, PATTERN => 'p')   # unchanged
SELECT * FROM @s (FILE_FORMAT => f)                   # unchanged
```

**Cause:** the parser already stored `pattern` correctly. In `sqlglot/generator.py` (`table_sql`), the `PATTERN` emission sat inside the `if file_format:` block, so a pattern without a format was never written out.

**Change:**
- `sqlglot/generator.py`: `pattern` is read independently. If either option is set, the generator builds the parenthesised list from whichever of `FILE_FORMAT` and `PATTERN` are present.
- `tests/dialects/test_snowflake.py`: added a round-trip `validate_identity` for `SELECT * FROM @mystage (PATTERN => '.*data-100.*')`. The existing `FILE_FORMAT` + `PATTERN` cases still pass unchanged.

**Verification:** the full suite passes with the project's test command (1126 passed, 18224 subtests). I did not run the linter or commit anything.
