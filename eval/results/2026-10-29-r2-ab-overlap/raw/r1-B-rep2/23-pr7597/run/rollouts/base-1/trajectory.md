# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. The example from your report parses and round-trips to `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returned early for a subquery source and skipped the `joins=True` handling that plain tables get. The join was then consumed by the FROM-first fallback, which left the trailing `select` unparsed. Plain tables already worked because their joins are parsed before the `SELECT` is matched.

**Fix:** In the subquery branch of `_parse_table`, when `joins` is set, append the parsed joins to the subquery, the same way the table branch does. This is a single 3-line change.

**Tests:**
- Added a regression case to `tests/dialects/test_duckdb.py` for the query from your report.
- Full suite: 1104 passed, 17947 subtests passed.
- `ruff check` and `ruff format --check` pass on both touched files.
- Probes also cover `FROM (FROM t1) t1 JOIN tbl_2 ... SELECT`, `CROSS JOIN`, the `(select 1)` form, a plain table as the first source, and the `select * from (...) join` form. All parse.

Nothing is committed. The change is in the working tree for you to review.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from (FROM tbl_1) t1 select t1.x','FROM tbl_1 t1 positional join tbl_2 t2 select t1.x','from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1']:\n    try: print(repr(sqlglot.parse_one(q, read='duckdb')))\n    except Exception as e: print('ERR', q, str(e)[:200])\n\"; grep -n \"FROM\\b\" sqlglot/dialects/duckdb.py | head -30; grep -n \"def _parse_select\\|FROM\" sqlglot/parser.py | head -60", "description": "Reproduce the failure and locate FROM-first parsing"}
[tool_result] ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
Select(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False),
      table=Identifier(this=t1, quoted=False))],
  from_=From(
    this=Subquery(
      this=Select(
        expressions=[
          Star()],
        from_=From(
          this=Table(
…[2147 chars elided]…
..b case
sqlglot/parser.py:4758:if self._match_text_seq("ROWS", "FROM")
sqlglot/parser.py:5409:from_=self._match(TokenType.FROM) and self._parse_bitwise(),
sqlglot/parser.py:7613:self.raise_error("Expected FROM or comma after EXTRACT", self._prev)
sqlglot/parser.py:8086:invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_F...
sqlglot/parser.py:9408:kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
sqlglot/parser.py:9576:from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "sed -n 3700,3830p sqlglot/parser.py", "description": "Read FROM-first parsing code in parser"}
[tool_result]         def _parse_value_expression() -> exp.Expr | None:
            if self.dialect.SUPPORTS_VALUES_DEFAULT and self._match(TokenType.DEFAULT):
                return exp.var(self._prev.text.upper())
            return self._parse_expression()

        if self._match(TokenType.L_PAREN):
            expressions = self._parse_csv(_parse_value_expression)
            self._match_r_paren()
            return self.expression(exp.Tuple(expressions=expressions))

        # In some dialects we can hav
…[3813 chars elided]…

            hint = self._parse_hint()

            if self._next and not self._next.token_type == TokenType.DOT:
                all_ = self._match(TokenType.ALL)
                matched_distinct = self._match_set(self.DISTINCT_TOKENS)
            else:
                all_, matched_distinct = None, False

            kind = (
                self._prev.text.upper()
                if self._match(TokenType.ALIAS) and self._match_texts(("STRUCT", "VALUE"))
                else None
            )
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs=['from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x',\n'from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x',\n'from (select 1) t1 positional join (select 2) t2 select t1.x',\n'from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x',\n'from (FROM tbl_1) t1 cross join (FROM
…[53 chars elided]…
_1) t1 positional join (FROM tbl_2) t2',\n'from (FROM tbl_1) t1 positional join (FROM tbl_2) t2',\n]\nfor q in qs:\n    try: sqlglot.parse_one(q, read='duckdb'); print('OK ', q)\n    except Exception as e: print('ERR', q)\n\"; grep -n \"def _parse_table(\" -A60 sqlglot/parser.py | grep -n \"L_PAREN\\|wrapped\\|subquery\\|FROM\" ", "description": "Probe variants to isolate the failing combination"}
[tool_result] OK  from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x
ERR from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x
ERR from (select 1) t1 positional join (select 2) t2 select t1.x
ERR from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x
ERR from (FROM tbl_1) t1 cross join (FROM tbl_2) t2 select t1.x
OK  select t1.x from (FROM tbl_1) t1 positional join (FROM tbl_2) t2
OK  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2
51:4748-        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):
52:4749-            if not subquery.args.get("pivots"):
53:4750-                subquery.set("pivots", self._parse_pivots())
54:4751-            return subquery
60:4757-            self._parse_wrapped_csv(self._parse_table)
61:4758-            if self._match_text_seq("ROWS", "FROM")
[tool_use Bash] {"command": "grep -n \"def _parse_from\\|def _parse_table(\\|def _parse_table_parts\\|def _parse_query_modifiers\\|def _parse_join(\" sqlglot/parser.py; sed -n '/def _parse_from(/,/^    def /p' sqlglot/parser.py | head -40; sed -n '/    def _parse_table(/,/^    def /p' sqlglot/parser.py | head -80", "description": "Read _parse_from and _parse_table"}
[tool_result] rg: regex parse error:
    (?:def _parse_from|def _parse_table(|def _parse_table_parts|def _parse_query_modifiers|def _parse_join()
                                       ^
error: unclosed group
0 matches for 'def _parse_from\|def _parse_table(\|def _parse_table_parts\|def _parse_query_modifiers\|def _parse_join('
    def _parse_from(
        self,
        joins: bool = False,
        skip_from_token: bool = False,
        consume_pipe: bool = False,
    ) -> exp.From | None:
        if not skip
…[2636 chars elided]…
")
            else None
        )
        rows_from = (
            self.expression(exp.Table(rows_from=rows_from_tables)) if rows_from_tables else None
        )

        only = self._match(TokenType.ONLY)

        this = t.cast(
            exp.Expr,
            bracket
            or rows_from
            or self._parse_bracket(
                self._parse_table_parts(schema=schema, is_db_reference=is_db_reference)
            ),
        )

        if only:
            this.set("only", only)
[tool_use Bash] {"command": "sed -n 3830,3960p sqlglot/parser.py", "description": "Read rest of _parse_select_query"}
[tool_result]             distinct: exp.Expr | None = (
                self.expression(
                    exp.Distinct(
                        on=self._parse_value(values=False) if self._match(TokenType.ON) else None
                    )
                )
                if matched_distinct
                else None
            )

            if all_ and distinct:
                self.raise_error("Cannot specify both ALL and DISTINCT after SELECT")

            operation_modifiers = []
            while 
…[3619 chars elided]…
lf.expression(
            exp.With(
                expressions=expressions,
                recursive=recursive or None,
                search=self._parse_recursive_with_search(),
            ),
            comments=comments,
        )

    def _parse_cte(self) -> exp.CTE | None:
        index = self._index

        alias = self._parse_table_alias(self.ID_VAR_TOKENS)
        if not alias or not alias.this:
            self.raise_error("Expected CTE to have alias")

        key_expressions = (
[tool_use Bash] {"command": "sed -n '/    def _parse_table(/,/^    def _parse_table_parts/p' sqlglot/parser.py | sed -n 80,200p", "description": "Read tail of _parse_table for join handling"}
[tool_result]             this.set("only", only)

        # Postgres supports a wildcard (table) suffix operator, which is a no-op in this context
        self._match(TokenType.STAR)

        parse_partition = parse_partition or self.SUPPORTS_PARTITION_SELECTION
        if parse_partition and self._match(TokenType.PARTITION, advance=False):
            this.set("partition", self._parse_partition())

        if schema:
            return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION
…[3445 chars elided]…
es | None:
        if not self._match_text_seq("CHANGES", "(", "INFORMATION", "=>"):
            return None

        information = self._parse_var(any_token=True)
        self._match_r_paren()

        return self.expression(
            exp.Changes(
                information=information,
                at_before=self._parse_historical_data(),
                end=self._parse_historical_data(),
            )
        )

    def _parse_unnest(self, with_alias: bool = True) -> exp.Unnest | None:
[tool_use Bash] {"command": "grep -rn \"joins=True\" sqlglot/ | head; grep -rn \"class Subquery(\" -A12 sqlglot/ | grep -n \"arg_types\\|joins\" ; grep -n \"_parse_joins()\" sqlglot/parser.py | head", "description": "Check joins=True callers and Subquery joins arg"}
[tool_result] sqlglot/parsers/teradata.py:122:                from_=self._parse_from(joins=True),
sqlglot/parser.py:1051:        exp.From: lambda self: self._parse_from(joins=True),
sqlglot/parser.py:3611:                this=self._match(TokenType.FROM) and self._parse_table(joins=True),
sqlglot/parser.py:3613:                and self._parse_csv(lambda: self._parse_table(joins=True)),
sqlglot/parser.py:3626:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
sqlglot/parser.py:3634:                from_ = self._parse_from(joins=True)
sqlglot/parser.py:3809:            self._parse_from(joins=True, consume_pipe=True)
3:sqlglot/expressions/query.py-1664-    arg_types = {
5 matches in 5 files:

4079:0:
4423:0:list | None = list(self._parse_joins())
4821:0:
5017:0:
sqlglot/parser.py:3637:table.set("joins", list(self._parse_joins()) or None)
[tool_use Bash] {"command": "sed -n 1660,1680p sqlglot/expressions/query.py; ls .lithify/harness/scripts/ && head -30 .lithify/harness/scripts/probe_parse.py", "description": "Inspect Subquery args and probe script"}
[tool_result] class Subquery(Expression, DerivedTable, Query):
    is_subquery: t.ClassVar[bool] = True
    arg_types = {
        "this": True,
        "alias": False,
        "with_": False,
        **QUERY_MODIFIERS,
    }

    def unnest(self) -> Expr:
        """Returns the first non subquery."""
        expression: Expr = self
        while isinstance(expression, Subquery):
            expression = expression.this
        return expression

    def unwrap(self) -> Subquery:
        expression = self
    
…[398 chars elided]…
nts, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output changes when transpiled again; the next line shows both

Exits 0 if every statement is OK, 1 if any statement is ERR or UNSTABLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
import argparse
import sys
import sqlglot
def probe(sql, read, write):
def main(argv=None):
[49 more lines]
[assistant] The cause: when the FROM-first source is a subquery, `_parse_table` returns early and skips the `joins=True` handling that plain tables get. The join is then consumed by `_parse_query_modifiers` in the `elif from_:` branch, so the trailing `SELECT` is left unparsed. I'll apply the join handling to the subquery branch too.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150539-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150539-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2\" \"from (select 1) t1 positional join (select 2) t2 select t1.x\" \"from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x\" \"from (FROM tbl_1) t1 cross join (FROM tbl_2) t2 select t1.x\" \"from (FROM tbl_1) t1 positional join (FROM tbl_2) t2\" \"from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x\" \"select * from (select 1) t1 join t2 on true\" | $PY .lithify/harness/scripts/probe_parse.py --read duckdb; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Verify fix with probes and DuckDB dialect tests"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150539-duckdb-dialect-from-first-querie/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
........................ [ 54%]
....................       [100%]
44 passed, 598 subtests passed in 1.27s
[assistant] The probe script couldn't import the local `sqlglot` (it runs from its own directory), so I'll rerun it with `PYTHONPATH` set.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf '%s\\n' \"from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2\" \"from (select 1) t1 positional join (select 2) t2 select t1.x\" \"from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x\" \"from (FROM tbl_1) t1 cross join (FROM tbl_2) t2 select t1.x\" \"from (FROM tbl_1) t1 positional join (FROM tbl_2) t2\" \"from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x\" \"select * from (select 1) t1 join t2 on true\" | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb; echo exit=$?", "description": "Re-run probes with local sqlglot on path"}
[tool_result] OK        from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2
          SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK        from (select 1) t1 positional join (select 2) t2 select t1.x
          SELECT t1.x FROM (SELECT 1) AS t1 POSITIONAL JOIN (SELECT 2) AS t2
OK        from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x
          SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TR
…[94 chars elided]…
 FROM (SELECT * FROM tbl_1) AS t1 CROSS JOIN (SELECT * FROM tbl_2) AS t2
OK        from (FROM tbl_1) t1 positional join (FROM tbl_2) t2
          SELECT * FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK        from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x
          SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK        select * from (select 1) t1 join t2 on true
          SELECT * FROM (SELECT 1) AS t1 JOIN t2 ON TRUE
exit=0
[assistant] All probes pass. Next I'll add a regression test next to the existing FROM-first tests in the DuckDB test file.
[tool_use Bash] {"command": "grep -n \"POSITIONAL\\|positional\\|FROM-first\\|from tbl\\|\\\"FROM \" tests/dialects/test_duckdb.py | head -20", "description": "Find existing FROM-first and positional join tests"}
[tool_result] 9 matches in 1 files:

tests/dialects/test_duckdb.py:469:self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
tests/dialects/test_duckdb.py:485:self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UN...
tests/dialects/test_duckdb.py:486:self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
tests/dialects/test_duckdb.py:487:self.validate_identity("FROM tbl", "SELECT * FROM tbl")
tests/dialects/test_duckdb.py:1453:"FROM (FROM t1 UNION FROM t2)",
tests/dialects/test_duckdb.py:1457:"FROM (FROM (SELECT 1) AS t2(c), (SELECT t2.c AS c0))",
tests/dialects/test_duckdb.py:1461:"FROM (FROM (SELECT 2000 as amount) t GROUP BY amount HAVING SUM(amount) > 10...
tests/dialects/test_duckdb.py:1519:self.validate_identity("FROM t1, t2 SELECT *", "SELECT * FROM t1, t2")
tests/dialects/test_duckdb.py:2357:"FROM (FROM t1 SELECT foo1, foo2)",
[tool_use Bash] {"command": "sed -n 480,492p tests/dialects/test_duckdb.py", "description": "View FROM-first test block for insertion point"}
[tool_result]         self.validate_identity("SELECT {'x': 1, 'y': 2, 'z': 3}")
        self.validate_identity("SELECT {'key1': 'string', 'key2': 1, 'key3': 12.345}")
        self.validate_identity("SELECT ROW(x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT (x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT a.x FROM (SELECT {'x': 1, 'y': 2, 'z': 3} AS a)")
        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
        self.validate_identity(
            "SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)",
            "SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)",
        )
        self.validate_identity("x -> '$.family'")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-150539-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",", "new_string": "        
…[45 chars elided]…
 * FROM tbl\")\n        self.validate_identity(\n            \"from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2\",\n            \"SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\","}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-150539-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the full suite as the final gate, plus a lint check on the touched files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; ($PY -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py) 2>&1 | tail -3", "description": "Run full test suite and lint touched files", "timeout": 300000}
[tool_result] ............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 57.31s
All checks passed!
2 files already formatted
[assistant] FROM-first queries with joined subqueries now parse. The example from your report parses and round-trips to `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returned early for a subquery source and skipped the `joins=True` handling that plain tables get. The join was then consumed by the FROM-first fallback, which left the trailing `select` unparsed. Plain tables already worked because their joins are parsed before the `SELECT` is matched.

**Fix:** In the subquery branch of `_parse_
…[24 chars elided]…
set, append the parsed joins to the subquery, the same way the table branch does. This is a single 3-line change.

**Tests:**
- Added a regression case to `tests/dialects/test_duckdb.py` for the query from your report.
- Full suite: 1104 passed, 17947 subtests passed.
- `ruff check` and `ruff format --check` pass on both touched files.
- Probes also cover `FROM (FROM t1) t1 JOIN tbl_2 ... SELECT`, `CROSS JOIN`, the `(select 1)` form, a plain table as the first source, and the `select * from (...) join` form. All parse.

Nothing is committed. The change is in the working tree for you to review.
