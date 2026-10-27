# trajectory base-1

final message:
DuckDB → MySQL `ORDER BY` now qualifies the simulated `CASE` operand when a bare sort key names a single projection of its SELECT. The full suite passes (`SUMMARY: 1110 passed, 18041 subtests passed`, `EXIT: 0`), run after the last edit. Ruff lint and format are clean. Nothing is committed.

**The change**
- `sqlglot/generator.py`: `ordered_sql` now builds the `CASE WHEN … IS NULL` operand with a new helper, `_null_check_operand`. For a bare column in a SELECT's own `ORDER BY`, the helper finds the projection with that output name. If exactly one matches, it uses that projection's underlying expression (alias stripped). Otherwise it keeps the original column. The sort key itself is unchanged.
- `tests/dialects/test_duckdb.py`: new `test_null_ordering_mysql_ambiguous_columns` with three cases: a bare name that is also a column of the second table, a projection alias, and a qualified reference that was already correct.

Example: `SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x` now emits `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x` instead of `CASE WHEN x IS NULL …`.

**Choices I made**
- I used the projection's expression rather than the alias, so `a.x AS v ORDER BY v` gives `CASE WHEN a.x …, v`. For a non-column alias such as `x + 1 AS v`, the CASE copies `x + 1`. That is the same meaning, but the bare `x` inside it can still be ambiguous in the same way.
- If two projections share the name, I leave the bare column alone. The source query is already ambiguous in that case.

**Still not handled**
- Window `ORDER BY` (`SUM(y) OVER (ORDER BY x)` over a join) still emits a bare `CASE WHEN x IS NULL`. It is ambiguous in MySQL if `b` also has `x`. There is no projection to map to here, so the fix would need table resolution (for example the optimizer's qualify pass).
- `UNION … ORDER BY x` also still emits a bare CASE operand. I did not check MySQL's behaviour for that form.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"NULL_ORDERING\\|null_ordered\\|nulls_first\\|NULLS_FIRST\\|def ordered_sql\" -r sqlglot/generator.py sqlglot/generators/mysql.py sqlglot/dialects/dialect.py | head -50; cat memory.md 2>/dev/null; ls .lithify/harness 2>/dev/null; cat ~/.claude/projects/-private-tmp-claude-501--Users-user-Coding-delvera-foundational-lithify-f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a-scratchpad-hwork-replay-horizon-sqlglot-adaptive-feedback-claude-claude-haiku-5-5-repo/memory/MEMORY.md 2>/dev/null | head -30", "description": "Check repo state and find null ordering code"}
[tool_result] sqlglot/generators/mysql.py:134:    NULL_ORDERING_SUPPORTED: bool | None = None
sqlglot/dialects/dialect.py:383:    NULL_ORDERING = "nulls_are_small"
sqlglot/generator.py:296:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generator.py:299:    WINDOW_FUNCS_WITH_NULL_ORDERING: t.ClassVar[tuple[type[exp.Expression], ...]] = ()
sqlglot/generator.py:2958:    def ordered_sql(self, expression: exp.Ordered) -> str:
sqlglot/generator.py:2962:        nulls_first = expression.args.get("nulls_first
…[357 chars elided]…
_last"
sqlglot/generator.py:2972:        if nulls_first and (
sqlglot/generator.py:2984:        if nulls_sort_change and not self.NULL_ORDERING_SUPPORTED:
sqlglot/generator.py:2999:                isinstance(window_this, self.WINDOW_FUNCS_WITH_NULL_ORDERING)
sqlglot/generator.py:3007:                elif self.NULL_ORDERING_SUPPORTED is False and (
sqlglot/generator.py:3022:                elif self.NULL_ORDERING_SUPPORTED is None:
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "sed -n 2950,3050p sqlglot/generator.py && cat .lithify/harness/memory.md && sed -n 120,140p sqlglot/generators/mysql.py && grep -n \"NULL_ORDERING\\|nulls_first\\|null_ordered\" sqlglot/dialects/duckdb.py sqlglot/parsers/*.py sqlglot/dialects/mysql.py | head", "description": "Read ordered_sql and MySQL generator flags"}
[tool_result]         return self.op_expressions("CLUSTER BY", expression)

    def distribute_sql(self, expression: exp.Distribute) -> str:
        return self.op_expressions("DISTRIBUTE BY", expression)

    def sort_sql(self, expression: exp.Sort) -> str:
        return self.op_expressions("SORT BY", expression)

    def ordered_sql(self, expression: exp.Ordered) -> str:
        desc = expression.args.get("desc")
        asc = not desc

        nulls_first = expression.args.get("nulls_first")
        nulls
…[5559 chars elided]…
sqlglot/dialects/duckdb.py:17:    NULL_ORDERING = "nulls_are_last"
sqlglot/parsers/prql.py:134:            term.set("nulls_first", False)
sqlglot/parsers/snowflake.py:290:    nulls_first = seq_get(args, 2)
sqlglot/parsers/snowflake.py:291:    if nulls_first is None and isinstance(asc, exp.Boolean):
sqlglot/parsers/snowflake.py:292:        nulls_first = exp.Boolean(this=not asc.this)
sqlglot/parsers/snowflake.py:293:    return exp.SortArray(this=seq_get(args, 0), asc=asc, nulls_first=nulls_first)
[tool_use Bash] {"command": "cat > /tmp/probe_null.py <<'EOF'\nimport sqlglot\ncases = [\n \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x\",\n \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x\",\n \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v\",\n \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v DESC\",\n \"SELECT x FROM a ORDER BY x DESC\",\n \"SELECT x FROM a
…[53 chars elided]…
T x FROM a ORDER BY x + 1\",\n]\nfor c in cases:\n    print(c)\n    print(\"  ->\", sqlglot.transpile(c, read=\"duckdb\", write=\"mysql\")[0])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_null.py", "description": "Probe DuckDB to MySQL ORDER BY null translation"}
[tool_result] SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x
  -> SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x
  -> SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v
  -> SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN v IS NULL THEN 1 ELSE 0 END, v
SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v DESC
  -> SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v DESC
SELECT x FROM a ORDER BY x DESC
  -> SELECT x FROM a ORDER BY x DESC
SELECT x FROM a JOIN b ON a.id = b.id ORDER BY b.x DESC
  -> SELECT x FROM a JOIN b ON a.id = b.id ORDER BY b.x DESC
SELECT x FROM a ORDER BY x + 1
  -> SELECT x FROM a ORDER BY CASE WHEN x + 1 IS NULL THEN 1 ELSE 0 END, x + 1
[tool_use Bash] {"command": "grep -rn \"IS NULL THEN 1 ELSE 0 END\" tests/ | head -30; grep -rn \"nulls_first\\|NULLS FIRST\" tests/dialects/test_mysql.py | head", "description": "Find existing tests for null-ordering simulation"}
[tool_result] tests/dialects/test_redshift.py:245:                "mysql": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/dialects/test_redshift.py:252:                "starrocks": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number 
…[2616 chars elided]…
               "snowflake": "SELECT FIRST_VALUE(col1) RESPECT NULLS OVER (ORDER BY col2 NULLS FIRST) FROM table1",
tests/dialects/test_mysql.py:1739:                "oracle": "SELECT LAST_VALUE(col1) OVER (PARTITION BY col3 ORDER BY col2 NULLS FIRST ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM table1",
tests/dialects/test_mysql.py:1750:                "oracle": "SELECT LAG(col1) OVER (ORDER BY CASE WHEN col2 IS NULL THEN 1 ELSE 0 END NULLS FIRST, col2 NULLS FIRST) FROM table1",
[tool_use Bash] {"command": "grep -rn \"def unalias\\|def alias_or_name\" -A6 sqlglot/expressions/core.py | head -30; sed -n 3436,3450p tests/dialects/test_dialect.py", "description": "Check unalias helper and existing null-ordering test"}
[tool_result] sqlglot/expressions/core.py:203:    def alias_or_name(self) -> str:
sqlglot/expressions/core.py-204-        raise NotImplementedError
sqlglot/expressions/core.py-205-
sqlglot/expressions/core.py-206-    @property
sqlglot/expressions/core.py-207-    def output_name(self) -> str:
sqlglot/expressions/core.py-208-        """
sqlglot/expressions/core.py-209-        Name of the output column if this expression is a selection.
--
sqlglot/expressions/core.py:401:    def unalias(self) -> Expr:
sqlglot/ex
…[1390 chars elided]…
park"
        with_large_nulls = "postgres"

        sql = "SELECT * FROM t ORDER BY c"
        sql_nulls_last = "SELECT * FROM t ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END, c"
        sql_nulls_first = "SELECT * FROM t ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c"

        for read_dialect, desc, nulls_first, expected_sql in (
            (with_last_nulls, False, None, sql_nulls_last),
            (with_last_nulls, True, None, sql),
            (with_last_nulls, False, True, sql),
[assistant] Confirmed the failure shape: `SELECT a.x, b.y FROM a JOIN b ... ORDER BY x` emits a bare `CASE WHEN x IS NULL`, which MySQL resolves against both FROM tables. I'll make the simulated `CASE` use the projection's column when the bare `ORDER BY` name matches exactly one projection.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[105 chars elided]…
            )", "new_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        null_check = self.sql(self._null_check_operand(expression))\n                        this = f\"CASE WHEN {null_check} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{sort_order}{nulls_sort_change}{with_fill}\"\n\n    def matchrecognizemeasure_sql(", "new_string": "        return f\"{this}{sort_order}{nulls_sort_change}{with_fill}\"\n\n    def _null_check_
…[340 chars elided]…
der.parent if isinstance(order, exp.Order) else None\n\n        if isinstance(column, exp.Column) and not column.table and isinstance(select, exp.Select):\n            projections = [p for p in select.expressions if p.alias_or_name == column.name]\n            if len(projections) == 1:\n                return projections[0].unalias()\n\n        return column\n\n    def matchrecognizemeasure_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "cat >> /tmp/probe_null.py <<'EOF'\nfor c in [\n \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x\",\n \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v\",\n \"SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v DESC\",\n \"SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY x\",\n \"SELECT x FROM a UNION SELECT y FROM b ORDER BY x\",\n \"SELECT * FROM 
…[93 chars elided]…
ER BY x) FROM a JOIN b ON a.id = b.id\",\n]:\n    print(\"ALT\", c); print(\"  ->\", sqlglot.transpile(c, read=\"duckdb\", write=\"mysql\")[0])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_null.py", "description": "Re-run DuckDB to MySQL probes after the change"}
[tool_result] SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x
  -> SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x
  -> SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY v
  -> SELECT a.x AS v, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, v
SELECT a.x A
…[1075 chars elided]…
 UNION SELECT y FROM b ORDER BY x
  -> SELECT x FROM a UNION SELECT y FROM b ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
ALT SELECT * FROM (SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x) AS t
  -> SELECT * FROM (SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x) AS t
ALT SELECT SUM(y) OVER (ORDER BY x) FROM a JOIN b ON a.id = b.id
  -> SELECT SUM(y) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) FROM a JOIN b ON a.id = b.id
[assistant] The probes now show the qualified `CASE` operand with the bare sort key unchanged. Next I'll add a regression test next to the existing DuckDB→MySQL null-ordering coverage.
[tool_use Bash] {"command": "grep -n \"    def test_\\|^class\\|^from\\|^import\" tests/dialects/test_duckdb.py | head -20; grep -n \"def test_\" tests/dialects/test_duckdb.py | tail -3; tail -5 tests/dialects/test_duckdb.py", "description": "Locate test structure in DuckDB test file"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
10:class TestDuckDB(Validator):
13:    def test_duckdb(self):
1615:    def test_array_index(self):
1655:    def test_array_insert(self):
1696:    def test_array_remove(self):
1721
…[73 chars elided]…
   def test_sample(self):
2004:    def test_array(self):
2008:    def test_cast(self):
2184:    def test_encode_decode(self):
2216:    def test_sha(self):
2223:    def test_rename_table(self):
2241:    def test_timestamps_with_units(self):
2749:    def test_map_pick(self):
2784:    def test_to_array(self):
2813:    def test_map_insert(self):
            write={
                "duckdb": "SELECT CAST('1' AS VARIANT)",
                "snowflake": "SELECT TO_VARIANT('1')",
            },
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_duckdb.py <<'EOF'\n\n    def test_null_ordering_mysql_ambiguous_columns(self):\n        self.validate_all(\n            \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x\",\n            write={\n                \"duckdb\": \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x NULLS LAST\",\n                \"mysql\": \"SELECT a.x, b.y FROM a JOIN
…[645 chars elided]…
,\n            },\n        )\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k null_ordering tests/dialects/test_dialect.py 2>&1 | tail -30", "description": "Add regression test and run targeted tests"}
[tool_result] ..                                                 [100%]
=================================== FAILURES ===================================
_ TestDuckDB.test_null_ordering_mysql_ambiguous_columns [SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x -> duckdb] _
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x' != 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x NULLS LAST'
E   - SELEC
…[4 chars elided]…
x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x
E   + SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x NULLS LAST
E   ?                                                        +++++++++++
=========================== short test summary info ============================
SUBFAILED[SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x -> duckdb] tests/dialects/test_duckdb.py::TestDuckDB::test_null_ordering_mysql_ambiguous_columns
1 failed, 2 passed, 141 deselected, 21 subtests passed in 0.20s
[assistant] The failure is in my test expectation, not the code: DuckDB's own output omits `NULLS LAST`. I'll drop that line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "            write={\n                \"duckdb\": \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x NULLS LAST\",\n                \"mysql\": \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x\",\n            },", "new_string": "            write={\n                \"mysql\": \"SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-100136-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_mysql.py tests/dialects/test_dialect.py 2>&1 | tail -5; ls .lithify/harness/scripts", "description": "Run DuckDB, MySQL, and dialect test files"}
[tool_result] ........................ [ 12%]
....................... [ 24%]
.............................. [ 39%]
....................................................................................................................     [100%]
193 passed, 3907 subtests passed in 0.81s
run_suite.py
[assistant] Dialect files pass. Now the full suite, run in the foreground as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite in foreground", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:31:51 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  58760       00:01 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-9b9c0c8b91.log
ELAPSED: 61s
SUMMARY: 1110 passed, 18041 subtests passed in 60.90s (0:01:00)
EXIT: 0
[assistant] Full suite passed. I'll run the linter/formatter on the two changed files to match the project's pre-commit checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff check sqlglot/generator.py tests/dialects/test_duckdb.py && $PY/ruff format --check sqlglot/generator.py tests/dialects/test_duckdb.py) 2>&1 | tail -5; git status --short; rm -f /tmp/probe_null.py", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generator.py
 M tests/dialects/test_duckdb.py
[assistant] DuckDB → MySQL `ORDER BY` now qualifies the simulated `CASE` operand when a bare sort key names a single projection of its SELECT. The full suite passes (`SUMMARY: 1110 passed, 18041 subtests passed`, `EXIT: 0`), run after the last edit. Ruff lint and format are clean. Nothing is committed.

**The change**
- `sqlglot/generator.py`: `ordered_sql` now builds the `CASE WHEN … IS NULL` operand with a new helper, `_null_check_operand`. For a bare column in a SELECT's own `ORDER BY`, the helper finds the projection with that output name. If exactly one matches, it uses that projection's underlying e
…[718 chars elided]…
 meaning, but the bare `x` inside it can still be ambiguous in the same way.
- If two projections share the name, I leave the bare column alone. The source query is already ambiguous in that case.

**Still not handled**
- Window `ORDER BY` (`SUM(y) OVER (ORDER BY x)` over a join) still emits a bare `CASE WHEN x IS NULL`. It is ambiguous in MySQL if `b` also has `x`. There is no projection to map to here, so the fix would need table resolution (for example the optimizer's qualify pass).
- `UNION … ORDER BY x` also still emits a bare CASE operand. I did not check MySQL's behaviour for that form.
