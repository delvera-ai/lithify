# trajectory base-1

final message:
`PATTERN` is now kept when `FILE_FORMAT` is absent, and both parameters survive alone and together.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')   -> unchanged
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')   -> unchanged
SELECT * FROM @mystage (FILE_FORMAT => 'f')   -> unchanged
```

**Cause:** the parser already built the right node (`format=None`, `pattern=Literal`). The bug was in `table_sql` in `sqlglot/generator.py`, which only emitted the parenthesised block when `format` was set, so a `PATTERN`-only table lost it. I rewrote that block to collect `FILE_FORMAT => ...` and `PATTERN => ...` and emit the parentheses when either is present.

I put the fix in the base generator rather than the Snowflake generator because the `format`/`pattern` args live on the generic `exp.Table` node. The change is therefore not Snowflake-only in effect, but it only changes output when `pattern` is set without `format`, which only Snowflake's parser produces today.

**Tests:** I added two round-trip checks to `tests/dialects/test_snowflake.py`, one for `PATTERN` alone and one for `FILE_FORMAT` alone. The combined form was already covered.

**Verification:**
- `tests/dialects/test_snowflake.py`: 96 passed.
- Full suite via `run_suite.py`: `SUMMARY: 1126 passed, 18224 subtests passed in 56.86s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not check the other dialects' output for this node, and I did not commit.

## events
[tool_use Bash] {"command": "grep -rn -i \"pattern\\|file_format\\|FILE_FORMAT\" sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py | head -60; cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md | head -80", "description": "Locate PATTERN and FILE_FORMAT handling in Snowflake code"}
[tool_result] sqlglot/dialects/snowflake.py:144:            "FILE FORMAT": TokenType.FILE_FORMAT,
sqlglot/parsers/snowflake.py:770:        "FILE_FORMAT": lambda self: self._parse_file_format_property(),
sqlglot/parsers/snowflake.py:1092:            file_format = None
sqlglot/parsers/snowflake.py:1093:            pattern = None
sqlglot/parsers/snowflake.py:1097:                if self._match_text_seq("FILE_FORMAT", "=>"):
sqlglot/parsers/snowflake.py:1098:                    file_format = self._parse_string() 
…[7074 chars elided]…
 or is rewritten,
you are not done: that is the failure, not a footnote.

In the final message, name the expression class the new syntax parses into and the result type
on each side of the translation. "Round-trips" alone is not enough.

## INVARIANT: shorthand forms reuse the node the full form already builds
When a dialect accepts a second spelling of a function it already parses (an omitted keyword or
a defaulted argument), the new spelling must build the SAME expression class as the existing
[tool_use Bash] {"command": "sed -n 1075,1125p sqlglot/parsers/snowflake.py; grep -n \"exp.Table\\b\\|def table_sql\\|pattern\\|format\" sqlglot/generators/snowflake.py | head -40; grep -rn \"pattern\" sqlglot/expressions/*.py | grep -i \"table\\|class\\|arg_types\" | head; grep -n \"pattern\\|FILE_FORMAT\\|@\" tests/dialects/test_snowflake.py | head -30", "description": "Inspect Snowflake stage table parsing, generator, and tests"}
[tool_result]     def _parse_table_parts(
        self,
        schema: bool = False,
        is_db_reference: bool = False,
        wildcard: bool = False,
        fast: bool = False,
    ) -> exp.Table | exp.Dot | None:
        # https://docs.snowflake.com/en/user-guide/querying-stage
        if self._match(TokenType.STRING, advance=False):
            table = self._parse_string()
        elif self._match_text_seq("@", advance=False):
            table = self._parse_location_path()
        else:
           
…[4496 chars elided]…
o)")
3436:            "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
3439:            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
3442:            "SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t"
3445:            "SELECT parse_json($1):a.b FROM @mystage2/data1.json.gz",
3446:            "SELECT GET_PATH(PARSE_JSON($1), 'a.b') FROM @mystage2/data1.json.gz",
[tool_use Bash] {"command": "grep -n \"\\\"pattern\\\"\\|'pattern'\\|\\\"format\\\"\\|table_sql\" sqlglot/generators/snowflake.py sqlglot/generator.py sqlglot/generators/*.py | head -20; grep -n \"pattern\\|format\" sqlglot/expressions/query.py | head -20", "description": "Find where Table format and pattern args are generated"}
[tool_result] sqlglot/generators/snowflake.py:527:            f"{'TRY_' if e.args.get('safe') else ''}TO_BINARY", e.this, e.args.get("format")
sqlglot/generators/snowflake.py:533:            f"{'TRY_' if e.args.get('safe') else ''}TO_DOUBLE", e.this, e.args.get("format")
sqlglot/generators/snowflake.py:736:            expression.args.get("format"),
sqlglot/generators/doris.py:261:        "format",
sqlglot/generators/doris.py:607:    def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
sqlglot
…[989 chars elided]…
ot/generator.py:3774:        fmt = self.sql(expression, "format")
sqlglot/generator.py:3846:    def jsontable_sql(self, expression: exp.JSONTable) -> str:
sqlglot/generator.py:4065:        format_sql = self.sql(expression, "format")
523:    arg_types = {"information": True, "at_before": False, "end": False}
831:        "pattern": False,
879:    arg_types = {"input_format": False, "output_format": False}
955:        "format": False,
956:        "pattern": False,
2037:        "format_json": False,
[tool_use Bash] {"command": "sed -n 2380,2440p sqlglot/generator.py; sed -n 950,960p sqlglot/expressions/query.py; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f')\\\"]:\n    e=sqlglot.parse_one(s,dialect='snowflake'); print(repr(e.find(sqlglot.exp.Table).args)); print(e.sql(dialect='snowflake'))\n\"", "description": "Read Table generation and reproduce the bug"}
[tool_result]     def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
        table = self.table_parts(expression)
        only = "ONLY " if expression.args.get("only") else ""
        partition = self.sql(expression, "partition")
        partition = f" {partition}" if partition else ""
        version = self.sql(expression, "version")
        version = f" {version}" if version else ""
        alias = self.sql(expression, "alias")
        alias = f"{sep}{alias}" if alias else ""

        sam
…[2137 chars elided]…
": False,
        "only": False,
        "partition": False,
{'this': Var(this=@mystage), 'format': None, 'pattern': Literal(this='.*data-100.*', is_string=True)}
SELECT * FROM @mystage
{'this': Var(this=@mystage), 'format': Literal(this='f', is_string=True), 'pattern': Literal(this='x', is_string=True)}
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')
{'this': Var(this=@mystage), 'format': Literal(this='f', is_string=True), 'pattern': None}
SELECT * FROM @mystage (FILE_FORMAT => 'f')
[assistant] The bug is in the base generator: `table_sql` only emits the parenthesised `FILE_FORMAT`/`PATTERN` block when `format` is set, so a `PATTERN`-only table loses it. The parser already builds the right node (`format=None`, `pattern=Literal`), so the fix belongs in generation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py", "old_string": "        file_format = self.sql(expression, \"format\")\n        if file_format:\n            pattern = self.sql(expression, \"pattern\")\n            pattern = f\", PATTERN => {pattern}\" if pattern else \"\"\n      
…[71 chars elided]…
w_string": "        file_format = self.sql(expression, \"format\")\n        pattern = self.sql(expression, \"pattern\")\n        staged_args = []\n        if file_format:\n            staged_args.append(f\"FILE_FORMAT => {file_format}\")\n        if pattern:\n            staged_args.append(f\"PATTERN => {pattern}\")\n        file_format = f\" ({', '.join(staged_args)})\" if staged_args else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add tests next to the existing staged-file tests, covering each parameter alone and together.
[tool_use Bash] {"command": "sed -n 3436,3444p tests/dialects/test_snowflake.py", "description": "View existing staged-file test lines"}
[tool_result]             "SELECT * FROM (SELECT * FROM '@external/location' (FILE_FORMAT => 'path.to.csv'))"
        )
        self.validate_identity(
            "SELECT * FROM @foo/bar (FILE_FORMAT => ds_sandbox.test.my_csv_format, PATTERN => 'test') AS bla"
        )
        self.validate_identity(
            "SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t"
        )
        self.validate_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )", "new_string": "        self.validate_identity(\n            \"SELECT t.$1, t.$2 FROM @mystage1 (FILE_FORMAT => 'myformat', PATTERN => '.*data.*[.]csv.gz') AS t\"\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (FILE_FORMAT => 'myformat')\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM @mystage (FILE_FORMAT => 'myformat')\",\n        )", "new_string": "        self.validate_identity(\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\")\n        self.validate_identity(\"SELECT * FROM @mystage (FILE_FORMAT => 'myformat')\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-115018-snowflake-dialect-the-pattern-cl/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Next I'll run the Snowflake test file and check the parsed node and the output in other dialects.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -5; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM @mystage (PATTERN => '.*data-100.*')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')\\\", \\\"SELECT * FROM @mystage (FILE_FORMAT => 'f')\\\"]:\n    e=sqlglot.parse_one(s,dialect='snowflake'); t=e.find(sqlglot.exp.Table); print({k:type(v).__name__ for k,v in t.args.items() if k in ('format','pattern')}); print(e.sql(dialect='snowflake'))\n\"", "description": "Run Snowflake tests and verify node and output"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.69s
{'format': 'NoneType', 'pattern': 'Literal'}
SELECT * FROM @mystage (PATTERN => '.*data-100.*')
{'format': 'Literal', 'pattern': 'Literal'}
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')
{'format': 'Literal', 'pattern': 'NoneType'}
SELECT * FROM @mystage (FILE_FORMAT => 'f')
[assistant] The Snowflake file passes (96 tests) and each case now round-trips. Next is the full-suite run that the harness requires before I report done.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-16:19:36 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-725d95b165.log
ELAPSED: 57s
SUMMARY: 1126 passed, 18224 subtests passed in 56.86s
EXIT: 0
[assistant] The full suite passed. I'll also run the repo's linter on the two changed files.
[tool_use Bash] {"command": "(ruff --version && ruff check sqlglot/generator.py tests/dialects/test_snowflake.py && ruff format --check sqlglot/generator.py tests/dialects/test_snowflake.py) 2>&1 | tail -5; git status --short; git diff --stat", "description": "Lint and format-check changed files; show diff stat"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 M sqlglot/generator.py
 M tests/dialects/test_snowflake.py
 sqlglot/generator.py             | 9 ++++++---
 tests/dialects/test_snowflake.py | 2 ++
 2 files changed, 8 insertions(+), 3 deletions(-)
[assistant] `PATTERN` is now kept when `FILE_FORMAT` is absent, and both parameters survive alone and together.

```
SELECT * FROM @mystage (PATTERN => '.*data-100.*')   -> unchanged
SELECT * FROM @mystage (FILE_FORMAT => 'f', PATTERN => 'x')   -> unchanged
SELECT * FROM @mystage (FILE_FORMAT => 'f')   -> unchanged
```

**Cause:** the parser already built the right node (`format=None`, `pattern=Literal`). The bug was in `table_sql` in `sqlglot/generator.py`, which only emitted the parenthesised block when `format` was set, so a `PATTERN`-only table lost it. I rewrote that block to collect `FILE_FORMAT => 
…[284 chars elided]…
nly changes output when `pattern` is set without `format`, which only Snowflake's parser produces today.

**Tests:** I added two round-trip checks to `tests/dialects/test_snowflake.py`, one for `PATTERN` alone and one for `FILE_FORMAT` alone. The combined form was already covered.

**Verification:**
- `tests/dialects/test_snowflake.py`: 96 passed.
- Full suite via `run_suite.py`: `SUMMARY: 1126 passed, 18224 subtests passed in 56.86s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not check the other dialects' output for this node, and I did not commit.
