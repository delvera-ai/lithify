# trajectory base-1

final message:
Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff check and format are clean. I haven't committed.

Changes:
- **`sqlglot/parsers/oracle.py`**: Oracle's `FUNCTION_PARSERS` now maps `LISTAGG` to the shared `_parse_string_agg`, which already handles the overflow clause. Before this, Oracle parsed `LISTAGG` as a generic function and the clause was a syntax error.
- **`sqlglot/generators/oracle.py`**: added `exp.GroupConcat` → `groupconcat_sql(self, e, sep=None, on_overflow=True)`, the same approach Trino uses. `sep=None` means a missing delimiter isn't invented, since Oracle's delimiter is optional. Without this mapping, Oracle output would have fallen back to `GROUP_CONCAT`.
- **`tests/dialects/test_oracle.py`**: new `test_listagg` covering the ERROR, TRUNCATE with and without COUNT, and no-separator forms.

Behavior change to be aware of: Oracle now emits `LISTAGG` for any `GroupConcat` from another dialect, where it previously emitted `GROUP_CONCAT`. That's an improvement, since `GROUP_CONCAT` isn't valid Oracle, and no existing test depended on the old output.

Things I found but did not change:
- **Snowflake drops the clause on output.** It parses `ON OVERFLOW`, but its generator calls `groupconcat_sql` without `on_overflow=True`, so `read='snowflake'` → `write='snowflake'` loses it. You described Snowflake as already supporting the clause; it's only half-supported. Fixing it means deciding whether Snowflake really accepts the clause, so I left it alone.
- **Overflow is dropped without `WITHIN GROUP`.** In `_parse_string_agg`, the no-`WITHIN GROUP` branch discards `on_overflow`. This is shared with Trino and Snowflake. Oracle always requires `WITHIN GROUP`, so the Oracle path isn't affected, but Trino's `LISTAGG(x, ',' ON OVERFLOW ERROR)` silently loses the clause. It's a small fix, but it touches shared code, so I left it for a separate change.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\" sqlglot/ | head -50; echo ---; grep -rn -i \"listagg\" sqlglot/ tests/ | head -60", "description": "Search for overflow and listagg references"}
[tool_result] sqlglot/parsers/clickhouse.py:142:    "sumWithOverflow",
sqlglot/parsers/bigquery.py:114:                {"null_if_pos_overflow": dialect.REGEXP_EXTRACT_POSITION_OVERFLOW_RETURNS_NULL}
sqlglot/parsers/snowflake.py:67:        allow_overflow=True,
sqlglot/parsers/snowflake.py:237:                {"null_if_pos_overflow": dialect.REGEXP_EXTRACT_POSITION_OVERFLOW_RETURNS_NULL}
sqlglot/parsers/snowflake.py:567:            lower=exp.Literal.number(-9223372036854775808.0),  # -2^63 as float to avoid ove
…[9890 chars elided]…
"SELECT LISTAGG(DISTINCT col, ',') WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:59:            "SELECT LISTAGG(col, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:62:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:65:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
[tool_use Bash] {"command": "sed -n 7695,7750p sqlglot/parser.py; echo ---; sed -n 5485,5500p sqlglot/generator.py; echo ---; sed -n 1880,1890p sqlglot/expressions/query.py; echo ---; sed -n 2405,2452p sqlglot/dialects/dialect.py; echo ---; sed -n 50,70p tests/dialects/test_trino.py; echo ---; grep -n -i \"listagg\\|group_concat\\|GroupConcat\\|string_agg\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py; echo ---; grep -n \"_parse_string_agg\\|_parse_group_concat\" -A3 sqlglot/parser.py | head -30; echo; sed -n 120,140p sqlglot/expressions/aggregate.py", "description": "Read listagg parser, generator, and related code"}
[tool_result]     def _parse_string_agg(self) -> exp.GroupConcat:
        if self._match(TokenType.DISTINCT):
            args: list[exp.Expr | None] = [
                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
            ]
            if self._match(TokenType.COMMA):
                args.extend(self._parse_csv(self._parse_disjunction))
        else:
            args = self._parse_csv(self._parse_disjunction)  # type: ignore

        if self._match_text_seq("ON", "OVERFLOW"):
  
…[6101 chars elided]…

9852-                concat_exprs = [

class DenseRank(Expression, AggFunc):
    arg_types = {"expressions": False}
    is_var_len_args = True


class First(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class FirstValue(Expression, AggFunc):
    pass


class GroupConcat(Expression, AggFunc):
    arg_types = {"this": True, "separator": False, "on_overflow": False}


class Grouping(Expression, AggFunc):
    arg_types = {"expressions": True}
    is_var_len_args = True
[assistant] Snowflake's `LISTAGG` already goes through the shared `_parse_string_agg`. Let me check what Oracle does with the clause today.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\"
…[180 chars elided]…
) FROM employees\\\"]\nfor q in qs:\n  for d in ['oracle','snowflake']:\n    try: print(d, '|', sqlglot.transpile(q, read='oracle', write=d)[0])\n    except Exception as e: print(d,'ERR',type(e).__name__, str(e)[:200])\n  try: print(repr(sqlglot.parse_one(q, read='oracle'))[:600])\n  except Exception as e: print('parse ERR', e)\n\"", "description": "Check current Oracle LISTAGG overflow behavior"}
[tool_result] oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
snowflake ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
parse ERR Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees
…[1289 chars elided]…
     expressions=[
          Column(
            this=Identifier(this=last_name, quoted=False),
            join_mark=False),
          Literal(this='; ', is_string=True)]),
      expression=Order(
        expressions=[
          Ordered(
            this=Column(
              this=Identifier(this=last_name, quoted=False),
              join_mark=False),
            nulls_first=False)]),
      join_mark=False)],
  from_=From(
    this=Table(
      this=Identifier(this=employees, quoted=False))))
[assistant] Oracle currently parses `LISTAGG` as a generic `Anonymous` call, so the overflow clause is a syntax error. Let me look at the Oracle parser/generator and how Snowflake wires it up.
[tool_use Bash] {"command": "grep -n \"FUNCTION_PARSERS\" -A12 sqlglot/parsers/oracle.py | head -40; echo ---; grep -n \"GroupConcat\\|groupconcat\" sqlglot/generators/oracle.py sqlglot/generators/snowflake.py; echo ---; grep -n \"FUNCTION_PARSERS\" -A3 sqlglot/parsers/snowflake.py | head; echo ---; grep -n \"def test_\\|listagg\\|LISTAGG\" tests/dialects/test_oracle.py | head -80; echo ---; ~/.cache
…[177 chars elided]…
OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\", read='snowflake', write='snowflake')[0])\nprint(sqlglot.transpile(\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\", read='snowflake', write='oracle')[0])\n\"", "description": "Inspect Oracle parser/generator and Snowflake handling"}
[tool_result] 40:    NO_PAREN_FUNCTION_PARSERS = {
41:        **parser.Parser.NO_PAREN_FUNCTION_PARSERS,
42-        "NEXT": lambda self: self._parse_next_value_for(),
43-        "PRIOR": lambda self: self.expression(exp.Prior(this=self._parse_bitwise())),
44-        "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp(sysdate=True)),
45-        "DBMS_RANDOM": lambda self: self._parse_dbms_random(),
46-    }
47-
48-    NO_PAREN_FUNCTIONS = {
49-        **parser.Parser.NO_PAREN_FUNCTIONS,
50-        Tok
…[1246 chars elided]…
, v in FUNCTION_PARSERS.items() if k != "TRIM"}
737-
738-    TIMESTAMPS = parser.Parser.TIMESTAMPS - {TokenType.TIME}
739-
---
24 matches in 24 files:

378:0:
393:0:
468:0:
532:0:
557:0:
586:0:
608:0:
617:0:
693:0:
707:0:
725:0:
743:0:
760:0:
780:0:
846:0:
870:0:
878:0:
884:0:
899:0:
9:0:
913:0:
927:0:
931:0:
973:0:
---
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT GROUP_CONCAT(last_name ORDER BY last_name, '; ', TRUNCATE '...' WITH COUNT) FROM employees
[assistant] Two findings so far. Oracle has no `LISTAGG` parser entry (it falls through to `Anonymous`). And Snowflake's round-trip drops the overflow clause, because its generator calls `groupconcat_sql` without `on_overflow=True`. Trino is the only dialect that passes it. Before changing Oracle, I'll check what Oracle currently emits for `GroupConcat` so I don't break existing expectations.
[tool_use Bash] {"command": "grep -rn '\"oracle\": \".*\\(GROUP_CONCAT\\|LISTAGG\\|STRING_AGG\\)' tests/ | head -20; echo ---; grep -n \"GROUP_CONCAT\\|STRING_AGG\" tests/dialects/test_oracle.py | head; echo ---; grep -n \"def test_\\|class Test\" tests/dialects/test_oracle.py | head -60; echo ---; grep -n \"^from\\|^import\" sqlglot/generators/oracle.py sqlglot/parsers/oracle.py; echo ---; grep -n \"^class \\|TRANSFORMS = {\" sqlglot/generators/oracle.py | head", "description": "Check existing Oracle GroupConcat expectations and imports"}
[tool_result] ---
0 matches for 'GROUP_CONCAT\|STRING_AGG'
---
25 matches in 25 files:

378:0:
393:0:
468:0:
532:0:
557:0:
586:0:
6:0:
608:0:
617:0:
693:0:
707:0:
725:0:
743:0:
760:0:
780:0:
846:0:
870:0:
878:0:
884:0:
899:0:
9:0:
913:0:
927:0:
931:0:
973:0:
---
10 matches in 2 files:

sqlglot/generators/oracle.py:1:from __future__ import annotations
sqlglot/generators/oracle.py:4:from sqlglot import exp, generator, transforms
sqlglot/generators/oracle.py:5:from sqlglot.dialects.dialect import (
sqlglot/parse
…[159 chars elided]…
lglot/parsers/oracle.py:6:from sqlglot.dialects.dialect import build_formatted_time, build_timetostr_or...
sqlglot/parsers/oracle.py:7:from sqlglot.helper import seq_get
sqlglot/parsers/oracle.py:8:from sqlglot.parser import OPTIONS_TYPE, build_coalesce
sqlglot/parsers/oracle.py:9:from sqlglot.tokens import TokenType
---
rg: regex parse error:
    (?:^class |TRANSFORMS = {)
                             ^
error: repetition quantifier expects a valid decimal
0 matches for '^class \|TRANSFORMS = {'
[tool_use Bash] {"command": "sed -n 1,20p sqlglot/generators/oracle.py; grep -n \"TRANSFORMS\" -A6 sqlglot/generators/oracle.py | head -30; echo ---; grep -rn \"GROUP_CONCAT\" tests/dialects/*.py | grep -i \"oracle\" | head; echo ---; sed -n 1,30p tests/dialects/test_oracle.py | head -30; echo; grep -n \"def test_\" tests/dialects/test_oracle.py | tail -5; wc -l tests/dialects/test_oracle.py", "description": "View Oracle generator header, transforms, and test file layout"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)
42:    AFTER_
…[1619 chars elided]…
(exp.Rand)
        self.validate_identity("DBMS_RANDOM.VALUE()").assert_is(exp.Rand)
        self.validate_identity("CAST(value AS NUMBER DEFAULT 0 ON CONVERSION ERROR)")
        self.validate_identity("SYSDATE")
        self.validate_identity("CREATE GLOBAL TEMPORARY TABLE t AS SELECT * FROM orders")
        self.validate_identity("CREATE PRIVATE TEMPORARY TABLE t AS SELECT * FROM orders")
        self.validate_identity("REGEXP_REPLACE('source', 'search')")

9:0:
913:0:
927:0:
931:0:
973:0:
988
[assistant] Plan: Oracle gets the shared `_parse_string_agg` for `LISTAGG`, which already handles `ON OVERFLOW`. Oracle also needs a `GroupConcat` generator that passes `on_overflow=True`, the way Trino does. Without one, the default generic output would turn `LISTAGG` into `GROUP_CONCAT`. I'll use `sep=None` so a missing delimiter isn't invented, since Oracle's delimiter is optional.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_ARRAY\": lambda self: self._parse_oracle_json_array(),\n        \"JSON_ARRAYAGG\": lambda self: self._parse_oracle_json_arrayagg(),\n        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_ARRAY\": lambda self: self._parse_oracle_json_array(),\n        \"JSON_ARRAYAGG\": lambda self: self._parse_oracle_json_arrayagg(),\n        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.DateTrunc: lambda self, e: self.func(\"TRUNC\", e.this, e.unit),\n        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),", "new_string": "        exp.DateTrunc: lambda self, e: self.func(\"TRUNC\", e.this, e.unit),\n        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, sep=None, on_overflow=True),"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-181913-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now I'll check the behavior and add a test to the Oracle test file.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nqs=[\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM employees\\\",\n\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees\\\"
…[311 chars elided]…
qlglot.transpile(q, read='oracle', write='oracle')[0])\nprint(sqlglot.transpile(\\\"SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY col) FROM t\\\", read='oracle', write='trino')[0])\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(x SEPARATOR ';') FROM t\\\", read='mysql', write='oracle')[0])\n\"", "description": "Verify Oracle LISTAGG overflow round-trips"}
[tool_result] SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT LISTAGG(last_name) WITHIN GROUP (ORDER BY last_name) FROM employees
SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY col) FROM t
SELECT LISTAGG(x, ';') FROM t
[assistant] The round-trips work. The default-count form normalizes to an explicit `WITH COUNT`, which matches the Trino tests. Next I'll add a test at the end of the Oracle test class.
[tool_use Bash] {"command": "tail -15 tests/dialects/test_oracle.py; grep -n \"    def test_\" tests/dialects/test_oracle.py | tail -3", "description": "View end of Oracle test file"}
[tool_result]         """Test that Oracle CREATE TRIGGER statements fall back to Command parsing."""
        self.validate_identity(
            "CREATE TRIGGER check_salary BEFORE INSERT ON employees FOR EACH ROW BEGIN :NEW.status := 'PENDING' END",
            check_command_warning=True,
        )

        self.validate_identity(
            "CREATE TRIGGER audit_trigger AFTER UPDATE ON accounts FOR EACH ROW BEGIN INSERT INTO audit_log (user_id, old_balance, new_balance, changed_at) VALUES (:OLD.id, :OLD.balance, :NEW.balance, SYSDATE) END",
            check_command_warning=True,
        )

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view FOR EACH ROW BEGIN INSERT INTO employees (id, name, dept_id) VALUES (:NEW.id, :NEW.name, :NEW.dept_id) END",
            check_command_warning=True,
        )
927:0:
931:0:
973:0:
[tool_use Bash] {"command": "cat >> tests/dialects/test_oracle.py <<'EOF'\n\n    def test_listagg(self):\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM employees\"\n        )\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY last_name) FROM employees\"\n        )\n        
…[768 chars elided]…
 FROM employees\",\n        )\nEOF\n<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_trino.py tests/dialects/test_snowflake.py tests/dialects/test_redshift.py tests/dialects/test_exasol.py 2>&1 | tail -30", "description": "Add Oracle LISTAGG test and run related dialect tests"}
[tool_result] ......................................... [ 25%]
.............................................. [ 53%]
...........................................................................                                               [100%]
162 passed, 2528 subtests passed in 0.88s
[assistant] The focused tests pass. Now the full suite, plus a lint/format check on the changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -I -m ruff check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -I -m ruff format --check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -3", "description": "Run full test suite and ruff checks"}
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[329 chars elided]…
.................... [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 56.43s
All checks passed!
3 files already formatted
[assistant] Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff check and format are clean. I haven't committed.

Changes:
- **`sqlglot/parsers/oracle.py`**: Oracle's `FUNCTION_PARSERS` now maps `LISTAGG` to the shared `_parse_string_agg`, which already handles the overflow clause. Before this, Oracle parsed `LISTAGG` as a generic function and the clause was a syntax error.
- **`sqlglot/generators/oracle.py`**: added `exp.GroupConcat` → `groupconcat_sql(self, e, sep=None, on_overflow=True)`, 
…[796 chars elided]…
rite='snowflake'` loses it. You described Snowflake as already supporting the clause; it's only half-supported. Fixing it means deciding whether Snowflake really accepts the clause, so I left it alone.
- **Overflow is dropped without `WITHIN GROUP`.** In `_parse_string_agg`, the no-`WITHIN GROUP` branch discards `on_overflow`. This is shared with Trino and Snowflake. Oracle always requires `WITHIN GROUP`, so the Oracle path isn't affected, but Trino's `LISTAGG(x, ',' ON OVERFLOW ERROR)` silently loses the clause. It's a small fix, but it touches shared code, so I left it for a separate change.
