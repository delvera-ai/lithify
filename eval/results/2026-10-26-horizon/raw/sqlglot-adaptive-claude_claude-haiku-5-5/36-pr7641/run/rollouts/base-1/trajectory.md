# trajectory base-1

final message:
The MySQL emulation now keeps the `ORDER BY` column reference unambiguous when it names a projection alias. The full suite passes: 1109 tests, exit code 0.

**The cause:** the `CASE WHEN <col> IS NULL` copy was built from the raw sort key. For `SELECT a.x AS x, b.y ... FROM a JOIN b ... ORDER BY x`, that produced `CASE WHEN x IS NULL ...`. MySQL re-resolves the bare `x` against the FROM tables there, and it's ambiguous between `a.x` and `b.x`.

**The fix** (`sqlglot/generator.py`):
- A new helper `_unambiguous_order_key` returns the aliased column when the sort key is a bare name that matches a projection alias in the same SELECT's ORDER BY, and that projection is a column. Only the `CASE` copy changes; the trailing sort key stays as written.
- Window-level `ORDER BY` clauses are excluded, because aliases aren't visible there and substituting would change which column is read.

**Output now:**
- `ORDER BY x` (alias for `a.x`) → `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`
- `ORDER BY a.x` → unchanged, already qualified.

**Test:** added a DuckDB→MySQL case to `tests/dialects/test_duckdb.py` for the alias shape. I didn't edit or weaken any existing test.

**Not verified:** no MySQL server is installed here, so I checked the generated SQL and the test suite, not MySQL's actual resolution. Bare columns that aren't aliases are unchanged, since an ambiguous bare name there is already invalid in the source dialect.

Nothing is committed. Say if you want a commit with the model attribution line.

## events
[assistant] I'll start by finding where the MySQL generator emulates `NULLS FIRST/LAST`.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -rn \"IS NULL THEN\\|null_ordering\\|nulls_first\\|NULLS_ORDER\\|def ordered_sql\" sqlglot/generator.py sqlglot/generators/mysql.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head -50", "description": "Locate NULL ordering emulation code"}
[tool_result] d0290be9d lithify: probe base
sqlglot/generator.py:2958:    def ordered_sql(self, expression: exp.Ordered) -> str:
sqlglot/generator.py:2962:        nulls_first = expression.args.get("nulls_first")
sqlglot/generator.py:2963:        nulls_last = not nulls_first
sqlglot/generator.py:2972:        if nulls_first and (
sqlglot/generator.py:3030:                            f"CASE WHEN {this} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "offset": 2955, "limit": 90}
[tool_result] 2955	    def sort_sql(self, expression: exp.Sort) -> str:
2956	        return self.op_expressions("SORT BY", expression)
2957	
2958	    def ordered_sql(self, expression: exp.Ordered) -> str:
2959	        desc = expression.args.get("desc")
2960	        asc = not desc
2961	
2962	        nulls_first = expression.args.get("nulls_first")
2963	        nulls_last = not nulls_first
2964	        nulls_are_large = self.dialect.NULL_ORDERING == "nulls_are_large"
2965	        nulls_are_small = self.dialect.
…[3741 chars elided]…

3033	
3034	        with_fill = self.sql(expression, "with_fill")
3035	        with_fill = f" {with_fill}" if with_fill else ""
3036	
3037	        return f"{this}{sort_order}{nulls_sort_change}{with_fill}"
3038	
3039	    def matchrecognizemeasure_sql(self, expression: exp.MatchRecognizeMeasure) -> str:
3040	        window_frame = self.sql(expression, "window_frame")
3041	        window_frame = f"{window_frame} " if window_frame else ""
3042	
3043	        this = self.sql(expression, "this")
3044	
[assistant] The emulation copies `this` verbatim, so a bare column is repeated as-is. Next I'll reproduce the failure and check the existing tests.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\ntests = [\n 'SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x AS x, b.y AS y FROM a JOIN b ON a.id = b.i
…[23 chars elided]…
T a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY z',\n]\nfor q in tests:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; grep -rn \"NULL_ORDERING_SUPPORTED = False\\|NULL_ORDERING_SUPPORTED = None\\|NULL_ORDERING_SUPPORTED\" sqlglot/ | head; grep -rn \"CASE WHEN .* IS NULL THEN 1 ELSE 0 END\" tests/ | head -5", "description": "Reproduce MySQL NULL ordering emulation output"}
[tool_result] <work>/env-sqlglot/bin/python
SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.x AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x AS x, b.y AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS z FROM a JOIN b ON a.id = b.id
…[1288 chars elided]…
SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/dialects/test_duckdb.py:84:                "mysql": "SELECT FIRST_VALUE(c) RESPECT NULLS OVER (PARTITION BY gb ORDER BY CASE WHEN ob IS NULL THEN 1 ELSE 0 END, ob) FROM t",
tests/dialects/test_duckdb.py:155:                "mysql": "SELECT SUM(X) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x)",
[assistant] Reproduced. The failing shape is an `ORDER BY` on a projection alias (`a.x AS x`) when the same bare name also exists in another FROM table: the emulated `CASE` re-resolves `x` against the FROM tables, not the alias. The bare-column case that the instructions describe also needs care. I'll check the existing tests that cover this emulation before editing.
[tool_use Bash] {"command": "grep -rn \"IS NULL THEN 1 ELSE 0 END\" tests/ | wc -l; grep -rln \"IS NULL THEN 1 ELSE 0 END\" tests/; which mysql mysqld 2>&1 | head -2", "description": "Count existing tests covering null ordering emulation"}
[tool_result]       12
tests/dialects/test_redshift.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_mysql.py
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql
mysql not found
mysqld not found
[assistant] No MySQL server is available, so I'll verify by the generated SQL and the test suite. Applying the fix: when the sort key is a bare column that names a projection alias of the same SELECT's ORDER BY, the emulated `CASE` uses the aliased column reference (qualified), while the sort key itself stays as written.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[108 chars elided]…
         )", "new_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        null_check = self.sql(self._unambiguous_order_key(expression))\n                        this = f\"CASE WHEN {null_check} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the helper, placed just above `ordered_sql`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "    def ordered_sql(self, expression: exp.Ordered) -> str:\n        desc = expression.args.get(\"desc\")", "new_string": "    def _unambiguous_order_key(self, expression: exp.Ordered) -> exp.Expression:\n        # A 
…[487 chars elided]…
pressions:\n                if (\n                    isinstance(projection, exp.Alias)\n                    and projection.alias == key.name\n                    and isinstance(projection.this, exp.Column)\n                ):\n                    return projection.this\n        return key\n\n    def ordered_sql(self, expression: exp.Ordered) -> str:\n        desc = expression.args.get(\"desc\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-run the repro cases and the full suite with the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ntests = [\n 'SELECT a.x AS x, b.y AS y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY z',\n 'SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT b.y AS x, a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY x DESC',\n 'SELECT ROW_NUMBER() OVER (ORDER BY x) AS r, a.x AS x FROM a JOIN b ON a.id = b.id',\n]\nfor q in tests:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify repro output and run full test suite"}
[tool_result] SELECT a.x AS x, b.y AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, z
SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT b.y AS x, a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY x DESC
SELECT ROW_NUMBER() OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) AS r, a.x AS x FROM a JOIN b ON a.id = b.id
Comma
…[115 chars elided]…
n to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-045334-duckdb-or-any-source-where-nulls-base-1/0ceeef00-f59b-4584-af88-8ff640f2126e/tasks/bu15qcoku.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. It is running now: do not start a second copy while it runs. If it is no longer needed, stop it with TaskStop. To check interim output, use Read on that file path.
[assistant] The repro output is correct: the emulated `CASE` now uses `a.x` for the alias `x` (and `ROW_NUMBER` windows keep the bare column, as before). The full suite is still running in the background. Meanwhile I'll look at the DuckDB test file so I can add a regression test beside the existing MySQL expectations.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "offset": 145, "limit": 25}
[tool_result] 145	            "SELECT CASE WHEN delim IS NULL THEN NULL ELSE ARRAY_TO_STRING(LIST_TRANSFORM(arr, x -> COALESCE(CAST(x AS TEXT), '')), delim) END",
146	            read={
147	                "snowflake": "SELECT ARRAY_TO_STRING(arr, delim)",
148	            },
149	        )
150	        self.validate_all(
151	            "SELECT SUM(X) OVER (ORDER BY x)",
152	            write={
153	                "bigquery": "SELECT SUM(X) OVER (ORDER BY x)",
154	                "duckdb": "SELECT SUM(X) OVER (
…[324 chars elided]…
ery": "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
162	                "duckdb": "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
163	                "mysql": "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
164	            },
165	        )
166	        self.validate_all(
167	            "SELECT * FROM x ORDER BY 1 NULLS LAST",
168	            write={
169	                "duckdb": "SELECT * FROM x ORDER BY 1",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)\",", "new_string": "        self.validate_all(\n            \"SELECT a.x AS x, b.y FROM a J
…[34 chars elided]…
\n            write={\n                \"duckdb\": \"SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x\",\n                \"mysql\": \"SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x\",\n            },\n        )\n        self.validate_all(\n            \"SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll check the background suite run and the new test together.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 110 $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Run DuckDB dialect tests"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Run DuckDB dialect tests"}
[tool_result] ............................................     [100%]
44 passed, 600 subtests passed in 0.22s
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-045334-duckdb-or-any-source-where-nulls-base-1/0ceeef00-f59b-4584-af88-8ff640f2126e/tasks/bu15qcoku.output"}
[tool_result] 1	SELECT a.x AS x, b.y AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
2	SELECT a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, z
3	SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
4	SELECT b.y AS x, a.x AS z FROM a JOIN b ON a.id = b.id ORDER BY x DESC
5	SELECT ROW_NUMBER() OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) AS r, a.x AS x FROM a JOIN b ON a.id = b.id
6	
[assistant] That file only has my probe output; the background pytest hasn't written its summary yet. I'll run the full suite again in the foreground with a longer timeout, since the first run was still going past the 120s default.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
[tool_result] Command did not complete within its 600s timeout and was moved to the background (ID: b32iok1q8). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-045334-duckdb-or-any-source-where-nulls-base-1/0ceeef00-f59b-4584-af88-8ff640f2126e/tasks/b32iok1q8.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. It is running now: do not start a second copy while it runs. If it is no longer needed, stop it with TaskStop. No output had been read from it when it was moved. A program that buffers its output, or a pipe into one such as tail, can keep the output file empty until the command finishes. To check interim output, use Read on that file path.
[assistant] The earlier background run was stopped by the time limit, so the new run (`b32iok1q8`) is the one that counts. I'll wait for its summary line.
[tool_use ToolSearch] {"query": "select:Monitor", "max_results": 1}
[tool_result] 
[tool_use Monitor] {"description": "Wait for full test suite summary", "command": "F=/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-045334-duckdb-or-any-source-where-nulls-base-1/0ceeef00-f59b-4584-af88-8ff640f2126e/tasks/b32iok1q8.output; until grep -qE \"passed|failed|error\" \"$F\" 2>/dev/null; do sleep 15; done; tail -15 \"$F\"", "timeout_ms": 900000}
[tool_result] Monitor started (task ba7uahh6h, expires in 10m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[assistant] The full test suite is still running in the background. I've armed a monitor that will report the summary when it finishes, so I'll wait for that before reporting.
[tool_use Bash] {"command": "tail -8 \"/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-045334-duckdb-or-any-source-where-nulls-base-1/0ceeef00-f59b-4584-af88-8ff640f2126e/tasks/b32iok1q8.output\"; cd ~/.cache/lithify/work/repo-161bf5b46800/20261027-045334-duckdb-or-any-source-where-nulls/base-1 && git status --short && git diff --stat", "description": "Show test summary and changed files"}
[tool_result] ............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................    [100%]
1109 passed, 18040 subtests passed in 68.03s (0:01:08)

[exited with code 0]
 M sqlglot/generator.py
 M tests/dialects/test_duckdb.py
 sqlglot/generator.py          | 25 ++++++++++++++++++++++---
 tests/dialects/test_duckdb.py |  7 +++++++
 2 files changed, 29 insertions(+), 3 deletions(-)
[assistant] The MySQL emulation now keeps the `ORDER BY` column reference unambiguous when it names a projection alias. The full suite passes: 1109 tests, exit code 0.

**The cause:** the `CASE WHEN <col> IS NULL` copy was built from the raw sort key. For `SELECT a.x AS x, b.y ... FROM a JOIN b ... ORDER BY x`, that produced `CASE WHEN x IS NULL ...`. MySQL re-resolves the bare `x` against the FROM tables there, and it's ambiguous between `a.x` and `b.x`.

**The fix** (`sqlglot/generator.py`):
- A new helper `_unambiguous_order_key` returns the aliased column when the sort key is a bare name that matches 
…[322 chars elided]…
(alias for `a.x`) → `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`
- `ORDER BY a.x` → unchanged, already qualified.

**Test:** added a DuckDB→MySQL case to `tests/dialects/test_duckdb.py` for the alias shape. I didn't edit or weaken any existing test.

**Not verified:** no MySQL server is installed here, so I checked the generated SQL and the test suite, not MySQL's actual resolution. Bare columns that aren't aliases are unchanged, since an ambiguous bare name there is already invalid in the source dialect.

Nothing is committed. Say if you want a commit with the model attribution line.
