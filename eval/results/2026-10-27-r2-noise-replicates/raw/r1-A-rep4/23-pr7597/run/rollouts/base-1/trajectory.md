# trajectory base-1

final message:
FROM-first queries whose joined sources are subqueries now parse. Your repro transpiles to DuckDB as `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1104 passed), and ruff lint and format are clean.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returned a parenthesized subquery early, before it consumed trailing joins. The FROM-first branch then handed the join to query modifiers, which never reach the `SELECT` after it. Plain tables already consumed joins at the end of `_parse_table`, which is why they worked.

**Fix:** The subquery branch of `_parse_table` now attaches joins when `joins=True`, the same way the table branch does (`sqlglot/parser.py`, around line 4775). `Subquery` already accepts query modifiers, so no expression changes were needed.

**Tests:** I added three identity checks to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests. They cover your positional-join repro and a subquery joined to a table. The third is a plain `JOIN` between two subqueries; all three fail before the fix.

I did not add an explicit test for the same query with `SELECT` first, since that path was already working.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2',\n          'from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x',\n          'from (FROM tbl_1) t1 select t1.x']:\n    try: print(repr(sqlglot.parse_one(q, read='duckdb')))\n    except Exception as e: print('ERR', q, str(e)[:200])\n\"; grep -n \"FROM\\b\" sqlglot/dialects/duckdb.py | head -40; grep -n \"def _parse_select\\|FROM\" sqlglot/parser.py | head -60", "description": "Reproduce the failing parse and locate FROM handling"}
[tool_result] ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
Select(
  expressions=[
    Alias(
      this=Column(
        this=Identifier(this=x, quoted=False),
        table=Identifier(this=t1, quoted=False)),
      alias=Identifier(this=x1, quoted=False)),
    Alias(
      this=Column(
        this=Identifier(this=x, quo
…[2550 chars elided]…
_set((TokenType.FROM, TokenType.COMMA)):
8086:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8433:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
8780:            if self._match_set((TokenType.FROM, TokenType.IN)):
9408:        kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
9541:        if not securable or not self._match_text_seq("FROM"):
9576:                from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "sed -n 3715,3830p sqlglot/parser.py; grep -n \"_parse_table\\b\\|def _parse_table(\" sqlglot/parser.py | head; grep -n \"from_first\\|FROM-first\\|leading\" sqlglot/dialects/duckdb.py sqlglot/parser.py | head", "description": "Read FROM-first select parsing code"}
[tool_result]     def _parse_projections(
        self,
    ) -> tuple[list[exp.Expr], list[exp.Expr] | None]:
        return self._parse_expressions(), None

    def _parse_wrapped_select(self, table: bool = False) -> exp.Expr | None:
        if self._match_set((TokenType.PIVOT, TokenType.UNPIVOT)):
            this: exp.Expr | None = self._parse_simplified_pivot(
                is_unpivot=self._prev.token_type == TokenType.UNPIVOT
            )
        elif self._match(TokenType.FROM):
            from_ = 
…[4167 chars elided]…
         this=self._parse_table(schema=True),
3402:            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
3459:                source=self._match(TokenType.TABLE) and self._parse_table(),
sqlglot/parser.py:3728:            # Support parentheses for duckdb FROM-first syntax
sqlglot/parser.py:3807:        # duckdb supports leading with FROM x
sqlglot/parser.py:6647:            # This converts the final AST to a series of Dots leading to the function call
[tool_use Bash] {"command": "grep -n \"def _parse_from\\|def _parse_table(\\|def _parse_subquery\\|def _parse_query_modifiers\" sqlglot/parser.py; sed -n \"$(grep -n 'def _parse_from' sqlglot/parser.py | cut -d: -f1),+25p\" sqlglot/parser.py; sed -n 3830,3900p sqlglot/parser.py", "description": "Inspect _parse_from and the SELECT-less branch"}
[tool_result] 4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4168:    def _parse_from(
4698:    def _parse_table(
    def _parse_from(
        self,
        joins: bool = False,
        skip_from_token: bool = False,
        consume_pipe: bool = False,
    ) -> exp.From | None:
        if not skip_from_token and not self._match(TokenType.FROM):
       
…[2894 chars elided]…
= self._parse_query_modifiers(this)
        elif self._match(TokenType.SUMMARIZE):
            table = self._match(TokenType.TABLE)
            this = self._parse_select() or self._parse_string() or self._parse_table()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
            this = self._parse_describe()
        else:
            this = None

        return self._parse_set_operations(this) if parse_set_operation else this
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['from tbl_1 join (FROM tbl_2) t2 on true select t2.x',\n          'from tbl_1 join (select 2 as x) t2 on true select t2.x',\n          'from tbl_1 join (select 2 as x) t2 on true',\n          'from (select 1 as x) t1 select t1.x',\n          'from (select 1 as x) t1 join tbl_2 t2
…[340 chars elided]…
true select t1.x; ',\n          'from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x order by 1',\n          'from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x order by 1',\n          ]:\n    try: sqlglot.parse_one(q, read='duckdb'); print('OK ', q)\n    except Exception as e: print('ERR', q)\n\"", "description": "Probe variants of FROM-first with subquery joins"}
[tool_result] OK  from tbl_1 join (FROM tbl_2) t2 on true select t2.x
OK  from tbl_1 join (select 2 as x) t2 on true select t2.x
OK  from tbl_1 join (select 2 as x) t2 on true
OK  from (select 1 as x) t1 select t1.x
ERR from (select 1 as x) t1 join tbl_2 t2 on true select t1.x
OK  select 1 from (select 1 as x) t1 join (select 2 as x) t2 on true
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x where true
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x; 
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x order by 1
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x order by 1
[tool_use Bash] {"command": "sed -n 4698,4790p sqlglot/parser.py", "description": "Read _parse_table implementation"}
[tool_result]     def _parse_table(
        self,
        schema: bool = False,
        joins: bool = False,
        alias_tokens: t.Collection[TokenType] | None = None,
        parse_bracket: bool = False,
        is_db_reference: bool = False,
        parse_partition: bool = False,
        consume_pipe: bool = False,
    ) -> exp.Expr | None:
        if not schema and not is_db_reference and not consume_pipe and not joins:
            index = self._index
            table = self._parse_table_parts(fast=True
…[2310 chars elided]…
upports a wildcard (table) suffix operator, which is a no-op in this context
        self._match(TokenType.STAR)

        parse_partition = parse_partition or self.SUPPORTS_PARTITION_SELECTION
        if parse_partition and self._match(TokenType.PARTITION, advance=False):
            this.set("partition", self._parse_partition())

        if schema:
            return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())
[tool_use Bash] {"command": "sed -n 4790,4815p sqlglot/parser.py; sed -n 4029,4070p sqlglot/parser.py; grep -n \"joins\" sqlglot/parser.py | sed -n 1,60p", "description": "Read rest of _parse_table and join handling"}
[tool_result]             this.set("version", self._parse_version())

        if self.dialect.ALIAS_POST_TABLESAMPLE:
            this.set("sample", self._parse_table_sample())

        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
        if alias:
            this.set("alias", alias)

        if self._match(TokenType.INDEXED_BY):
            this.set("indexed", self._parse_table_parts())
        elif self._match_text_seq("NOT", "INDEXED"):
            this.set("indexe
…[3339 chars elided]…
ins and self._match(TokenType.ON):
4427:            elif joins and self._match(TokenType.USING):
4430:                joins = None
4433:            kwargs["this"].set("joins", joins if joins else None)
4701:        joins: bool = False,
4708:        if not schema and not is_db_reference and not consume_pipe and not joins:
4820:        if joins:
4821:            for join in self._parse_joins():
4822:                this.append("joins", join)
5017:    def _parse_joins(self) -> t.Iterator[exp.Join]:
[tool_use Bash] {"command": "grep -n \"class Subquery(\" -A 12 sqlglot/expressions.py | head -30; grep -n \"def subquery_sql\" -A 12 sqlglot/generator.py", "description": "Check Subquery joins arg and generator"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
3182:    def subquery_sql(self, expression: exp.Subquery, sep: str = " AS ") -> str:
3183-        alias = self.sql(expression, "alias")
3184-        alias = f"{sep}{alias}" if alias else ""
3185-        sample = self.sql(expression, "sample")
3186-        if self.dialect.ALIAS_POST_TABLESAMPLE and sample:
3187-            alias = f"{sample}{alias}"
3188-
3189-            # Set to None so it's not generated again by self.query_modifiers()
3190-            expression.set("sample", None)
3191-
3192-        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
3193-        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
3194-        return self.prepend_ctes(expression, sql)
[tool_use Bash] {"command": "grep -rn \"class Subquery(\" -A 12 sqlglot/expressions/ | grep -n \"arg_types\\|joins\\|class\" | head; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('(select 1 as x) t1 join tbl_2 t2 on true', read='duckdb'))\nprint(repr(sqlglot.parse_one('select * from (select 1) t1 join tbl_2 t2 on true')))\" | head -30", "description": "Locate Subquery class and joins arg"}
[tool_result] 1:sqlglot/expressions/query.py:1662:class Subquery(Expression, DerivedTable, Query):
3:sqlglot/expressions/query.py-1664-    arg_types = {
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/sqlglot/__init__.py", line 196, in transpile
    for expression in parse(sql, read, error_level=error_level)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
…[1188 chars elided]…
5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", line 2124, in _parse_batch_statements
    self.raise_error("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", line 1991, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 23.
  (select 1 as x) t1 [4mjoin[0m tbl_2 t2 on true
[tool_use Bash] {"command": "sed -n 1662,1672p sqlglot/expressions/query.py", "description": "View Subquery arg_types"}
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
[assistant] Root cause: when a FROM-first query's first source is a parenthesized subquery, `_parse_table(joins=True)` returns the subquery early (`parser.py` ~L4775) without consuming the trailing joins. The FROM-first branch then only runs query modifiers, which can't reach the `SELECT` that follows. Plain tables handle joins at the end of `_parse_table` (L4820), so the fix is to do the same on the subquery branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from (select 1 as x) t1 join tbl_2 t2 on true select t1.x',\n          'from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x order by 1 limit 2']:\n    print(sqlglot.transpile(q, read='duckdb', write='duckdb')[0])\n    print(sqlglot.transpile(q, read='duckdb', write='duckdb', pretty=True)[0]); print()\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix on repro queries and run test suite"}
[tool_result] SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
SELECT
  t1.x AS x1,
  t2.x AS x2
FROM (
  SELECT
    *
  FROM tbl_1
) AS t1
POSITIONAL JOIN (
  SELECT
    *
  FROM tbl_2
) AS t2

SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE
SELECT
  t1.x
FROM (
  SELECT
    1 AS x
) AS t1
JOIN tbl_2 AS t2
  ON TRUE

SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN (SELECT 2 AS x) AS t2 ON TRUE ORDER BY 1 LIMIT 2
SELECT
  t1.x
FROM (
  SELECT
    1 AS x
) AS t1
JOIN (
  SELECT
    2 AS x
) AS t2
  ON TRUE
ORDER BY
  1
LIMIT 2

............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 52.81s
[assistant] The repro now parses and the full suite passes (1104 passed). Next I'll add a regression test next to the existing FROM-first tests.
[tool_use Bash] {"command": "grep -n \"FROM-first\\|from tbl\\|\\\"FROM \\|'FROM \\|from x\\b\" tests/dialects/test_duckdb.py | head -20", "description": "Find existing FROM-first tests in DuckDB suite"}
[tool_result] 485:        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
1453:            "FROM (FROM t1 UNION FROM t2)",
1457:            "FROM (FROM (SELECT 1) AS t2(c), (SELECT t2.c AS c0))",
1461:            "FROM (FROM (SELECT 2000 as amount) t GROUP BY amount HAVING SUM(amount) > 1000)",
1519:        self.validate_identity("FROM t1, t2 SELECT *", "SELECT * FROM t1, t2")
2357:            "FROM (FROM t1 SELECT foo1, foo2)",
[tool_use Bash] {"command": "sed -n 480,492p tests/dialects/test_duckdb.py", "description": "View context around FROM-first identity tests"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(", "new_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validat
…[300 chars elided]…
M (SELECT 1 AS x) t1 JOIN tbl_2 t2 ON TRUE SELECT t1.x\",\n            \"SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",\n            \"SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)\",\n        )\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I accidentally duplicated the `NOT EXISTS` assertion in that edit. Removing the copy.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "            \"SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",\n            \"SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)\",\n        )\n        self.validate_identity(", "new_string": "            \"SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE\",\n        )\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-175101-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list >/dev/null; git diff --stat", "description": "Run DuckDB tests and full suite, show diff stat"}
[tool_result] ........................ [ 54%]
....................       [100%]
44 passed, 598 subtests passed in 0.24s
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 50.64s
 sqlglot/parser.py             | 3 +++
 tests/dialects/test_duckdb.py | 8 ++++++++
 2 files changed, 11 insertions(+)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] FROM-first queries whose joined sources are subqueries now parse. Your repro transpiles to DuckDB as `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1104 passed), and ruff lint and format are clean.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returned a parenthesized subquery early, before it consumed trailing joins. The FROM-first branch then handed the join to query modifiers, which never reach the `SELECT` after it. Plain tables already consumed joins at the end of `_parse_table`, which is why they w
…[30 chars elided]…
branch of `_parse_table` now attaches joins when `joins=True`, the same way the table branch does (`sqlglot/parser.py`, around line 4775). `Subquery` already accepts query modifiers, so no expression changes were needed.

**Tests:** I added three identity checks to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests. They cover your positional-join repro and a subquery joined to a table. The third is a plain `JOIN` between two subqueries; all three fail before the fix.

I did not add an explicit test for the same query with `SELECT` first, since that path was already working.
