# trajectory base-1

final message:
Exasol `LISTAGG` now parses its second argument as the separator, the same as Oracle, Snowflake, Trino and DuckDB. The SQL from your report round-trips unchanged: `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`. The full suite passes (1126 tests) and ruff is clean.

**Cause:** `sqlglot/parsers/exasol.py` mapped both `LISTAGG` and `GROUP_CONCAT` to `_parse_group_concat`. That parser is MySQL-style: it concatenates comma-separated arguments and only reads a separator after a `SEPARATOR` keyword.

**Fix:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now uses `_parse_string_agg()`, the same parser Oracle and Snowflake use. `GROUP_CONCAT` keeps `_parse_group_concat()`, since Exasol's `GROUP_CONCAT` is MySQL-style.
- `tests/dialects/test_exasol.py`: added a round-trip check for the `LISTAGG` form and read checks from Oracle, Snowflake and Trino.

The existing `GROUP_CONCAT ... SEPARATOR ','` tests still pass unchanged.

One behaviour to be aware of: a `LISTAGG` with no separator still gets `','` written in on output, because the Exasol generator defaults to a comma. That was already the case, and I left it alone.

## events
[tool_use Bash] {"command": "rtk grep -n -i \"listagg\\|group_concat\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Find LISTAGG handling across dialects"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n -i \"listagg\\|group_concat\" sqlglot/dialects/exasol.py sqlglot/dialects/oracle.py sqlglot/dialects/snowflake.py sqlglot/dialects/trino.py sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py", "description": "Find LISTAGG handling across dialects"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/dialect.py:2426:    func_name: str = "LISTAGG",
sqlglot/dialects/dialect.py:2454:    listagg: exp.Expr = exp.Anonymous(this=func_name, expressions=[args])
sqlglot/dialects/dialect.py:2460:            listagg = exp.WithinGroup(this=listagg, expression=order)
sqlglot/dialects/dialect.py:2465:        listagg.set("expressions", [f"{args}{modifiers}"])
sqlglot/dialects/dialect.py:2467:    return self.sql(listagg)
sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:10057:    def _parse_group_concat(self) -> exp.Expr | None:
[tool_use Bash] {"command": "grep -rn -i \"listagg\\|GroupConcat\" sqlglot/ | grep -v \"\\.pyc\" | head -60; echo ---; sed -n 2415,2470p sqlglot/dialects/dialect.py; echo ---; sed -n 7895,7925p sqlglot/parser.py", "description": "Search LISTAGG and GroupConcat references in sqlglot"}
[tool_result] sqlglot/parser.py:7894:    def _parse_string_agg(self) -> exp.GroupConcat:
sqlglot/parser.py:7905:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7928:            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))
sqlglot/parser.py:7935:            return self.validate_expression(exp.GroupConcat.from_arg_list(args), args)
sqlglot/parser.py:7941:            exp.GroupConcat(
sqlglot/parser.py:10094:        retu
…[7148 chars elided]…
                      or not self._match_text_seq("WITHOUT", "COUNT")
                        ),
                    )
                )
        else:
            on_overflow = None

        index = self._index
        if not self._match(TokenType.R_PAREN) and args:
            # postgres: STRING_AGG([DISTINCT] expression, separator [ORDER BY expression1 {ASC | DESC} [, ...]])
            # bigquery: STRING_AGG([DISTINCT] expression [, separator] [ORDER BY key [{ASC | DESC}] [, ... ]] [LIMIT n])
[tool_use Bash] {"command": "sed -n 7925,7950p sqlglot/parser.py; echo ---; sed -n 10057,10100p sqlglot/parser.py; echo ---; sed -n 110,130p sqlglot/parsers/exasol.py; echo ---; sed -n 345,356p sqlglot/generators/exasol.py; echo ---; sed -n 640,660p sqlglot/generators/exasol.py; echo; git log --oneline -3 -- sqlglot/parsers/exasol.py", "description": "Inspect parser and generator code paths for LISTAGG"}
[tool_result]             # bigquery: STRING_AGG([DISTINCT] expression [, separator] [ORDER BY key [{ASC | DESC}] [, ... ]] [LIMIT n])
            # The order is parsed through `this` as a canonicalization for WITHIN GROUPs
            args[0] = self._parse_limit(this=self._parse_order(this=args[0]))
            return self.expression(exp.GroupConcat(this=args[0], separator=seq_get(args, 1)))

        # Checks if we can parse an order clause: WITHIN GROUP (ORDER BY <order_by_expression_list> [ASC | DESC]).
  
…[4567 chars elided]…
       "like",
        "limit",
        "listagg",
        "localtime",
        "localtimestamp",
        "locator",
        "log",
        "longvarchar",
        "loop",
        "low",
        "map",
        "match",
        "matched",

7e7cf8b06 Refactor: make dialect in build_formatted_time optional, fetch it from parser (#7639)
234198a31 feat(exasol): transpile USE/OPEN SCHEMA and SHOW TABLES to system-table query (#7538)
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
[assistant] The cause is in the Exasol parser: `LISTAGG` is routed to `_parse_group_concat`, which is MySQL-style `GROUP_CONCAT` (comma-separated args are concatenated, separator only after a `SEPARATOR` keyword). Oracle, Snowflake and Trino use `_parse_string_agg`, which is the right fit. Let me check existing Exasol tests before changing it.
[tool_use Bash] {"command": "grep -n -i -B2 -A6 \"listagg\\|group_concat\" tests/dialects/test_exasol.py", "description": "Find existing Exasol LISTAGG tests"}
[tool_result] 323-
324-        self.validate_identity(
325:            "SELECT id, department, hire_date, GROUP_CONCAT(id ORDER BY hire_date SEPARATOR ',') OVER (PARTITION BY department rows between 1 preceding and 1 following) GROUP_CONCAT_RESULT from employee_table ORDER BY department, hire_date",
326:            "SELECT id, department, hire_date, LISTAGG(id, ',') WITHIN GROUP (ORDER BY hire_date) OVER (PARTITION BY department rows BETWEEN 1 preceding AND 1 following) AS GROUP_CONCAT_RESULT FROM employee_ta
…[206 chars elided]…
ISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
332:                "mysql": "GROUP_CONCAT(DISTINCT x ORDER BY y DESC SEPARATOR ',')",
333-                "tsql": "STRING_AGG(x, ',') WITHIN GROUP (ORDER BY y DESC)",
334:                "databricks": "LISTAGG(DISTINCT x, ',') WITHIN GROUP (ORDER BY y DESC)",
335-            },
336-        )
337-        self.validate_all(
338-            "EDIT_DISTANCE(col1, col2)",
339-            read={
340-                "exasol": "EDIT_DISTANCE(col1, col2)",
[assistant] Existing tests only cover `GROUP_CONCAT` (MySQL-style), so splitting `LISTAGG` off is safe. Making the change:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132639-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py", "old_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_co
…[76 chars elided]…
lf: self._parse_group_concat()),", "new_string": "        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/listagg.htm\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/group_concat.htm\n        \"GROUP_CONCAT\": lambda self: self._parse_group_concat(),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132639-exasol-dialect-the-second-argume/base-1/sqlglot/parsers/exasol.py has been updated successfully.
[assistant] Now I'll check the behaviour against the cross-dialect examples from the report, and add a test next to the existing Exasol one.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['exasol','oracle','snowflake','trino','duckdb']:\n    e = sqlglot.parse_one(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read=d)\n    g = e.find(sqlglot.exp.GroupConcat)\n    print(d, '| this:', g.this.sql(), '| sep:', g.args.get('separator').sql() if g.args.get('separator') else None)\nprint(sqlglot.parse_one(\\\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\\\", read='exasol').sql('exasol'))\nprint(sqlglot.parse_one(\\\"SELECT GROUP_CONCAT(x ORDER BY y SEPARATOR ',') FROM t\\\", read='exasol').sql('exasol'))\n\"", "description": "Verify Exasol LISTAGG parse and round-trip"}
[tool_result] exasol | this: x ORDER BY y NULLS LAST | sep: ','
oracle | this: x ORDER BY y NULLS LAST | sep: ','
snowflake | this: x ORDER BY y NULLS LAST | sep: ','
trino | this: x ORDER BY y NULLS LAST | sep: ','
duckdb | this: x ORDER BY y NULLS LAST | sep: ','
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t
[assistant] Exasol now matches the other dialects, and the SQL round-trips. Adding a regression test beside the existing `GROUP_CONCAT` test:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132639-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py", "old_string": "        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\",", "new_string": "        self.validate_identity(\"SELECT LISTAGG(x, ',') WITHIN GROUP (ORDER BY y) FROM t\")\n        sel
…[41 chars elided]…
 ',') WITHIN GROUP (ORDER BY y)\",\n            read={\n                \"oracle\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"snowflake\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n                \"trino\": \"LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)\",\n            },\n        )\n        self.validate_all(\n            \"GROUP_CONCAT(DISTINCT x ORDER BY y DESC)\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-132639-exasol-dialect-the-second-argume/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] .................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
........................................................................................................................................................................................ [ 38%]
..................................... [ 42%]
........................................................... [ 47%]
.....................................................................
…[148 chars elided]…
............................................................... [ 70%]
............................................. [ 74%]
.......................................... [ 78%]
......................................................................................................................................................................................................... [ 96%]
.......................... [ 98%]
................                [100%]
1126 passed, 18227 subtests passed in 56.22s
[assistant] All 1126 tests pass. I'll run the linter on the two edited files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git diff --stat", "description": "Lint edited files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parsers/exasol.py     | 3 ++-
 tests/dialects/test_exasol.py | 9 +++++++++
 2 files changed, 11 insertions(+), 1 deletion(-)
[assistant] Exasol `LISTAGG` now parses its second argument as the separator, the same as Oracle, Snowflake, Trino and DuckDB. The SQL from your report round-trips unchanged: `LISTAGG(x, ',') WITHIN GROUP (ORDER BY y)`. The full suite passes (1126 tests) and ruff is clean.

**Cause:** `sqlglot/parsers/exasol.py` mapped both `LISTAGG` and `GROUP_CONCAT` to `_parse_group_concat`. That parser is MySQL-style: it concatenates comma-separated arguments and only reads a separator after a `SEPARATOR` keyword.

**Fix:**
- `sqlglot/parsers/exasol.py`: `LISTAGG` now uses `_parse_string_agg()`, the same parser Oracle and Snowflake use. `GROUP_CONCAT` keeps `_parse_group_concat()`, since Exasol's `GROUP_CONCAT` is MySQL-style.
- `tests/dialects/test_exasol.py`: added a round-trip check for the `LISTAGG` form and read checks from Oracle, Snowflake and Trino.

The existing `GROUP_CONCAT ... SEPARATOR ','` tests still pass unchanged.

One behaviour to be aware of: a `LISTAGG` with no separator still gets `','` written in on output, because the Exasol generator defaults to a comma. That was already the case, and I left it alone.
