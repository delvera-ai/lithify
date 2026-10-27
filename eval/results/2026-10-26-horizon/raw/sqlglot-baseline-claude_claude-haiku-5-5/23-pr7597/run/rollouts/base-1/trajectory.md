# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. The example from the report returns `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`, and DuckDB runs the output and returns `(1, 2)`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the table-with-joins path returned early for subqueries, so the `JOIN` clauses after a subquery were never consumed. Plain tables were fine because their joins were parsed before the `SELECT` keyword was checked. The parser then hit `select` with a join still pending.

**Fix:** When `joins=True` and the source is a subquery, the parser now attaches the joins to the subquery node, the same way it already does for tables. This is a 3-line change in `sqlglot/parser.py`.

**Test:** I added a `validate_identity` case to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests, using the query from the report.

**Verification:**
- Full test suite: 1104 passed, 17947 subtests passed (run before I added the new test case).
- `tests/dialects/test_duckdb.py` after adding the case: 44 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not commit. I also did not run `make check`, which the project guidance asks for before submitting. The `rtk` wrapper wasn't on the shell path, so I ran the commands directly.

## events
[tool_use Bash] {"command": "rtk grep -n \"FROM\\|from_first\\|_parse_from\" sqlglot/dialects/duckdb.py | head -50; rtk grep -n \"def _parse_from\\|def _parse_select\\|FROM-first\\|from_first\" sqlglot/parser.py | head", "description": "Find FROM-first handling in DuckDB dialect and parser"}
[tool_result] (eval):1: command not found: rtk
(eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"FROM\\b\" sqlglot/dialects/duckdb.py | head -30; grep -n \"from_first\\|FROM_FIRST\\|def _parse_from\\|def _parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head -30", "description": "Search for FROM-first handling in DuckDB dialect and parser"}
[tool_result] 3754:    def _parse_select(
3779:    def _parse_select_query(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4168:    def _parse_from(
8433:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 3754,3830p sqlglot/parser.py; sed -n 4168,4190p sqlglot/parser.py; grep -n \"FROM\" sqlglot/dialects/duckdb.py | head; grep -rn \"from_first\\|FROM-first\\|FROM first\" sqlglot/ tests/ | head", "description": "Read select parsing and from parsing code"}
[tool_result]     def _parse_select(
        self,
        nested: bool = False,
        table: bool = False,
        parse_subquery_alias: bool = True,
        parse_set_operation: bool = True,
        consume_pipe: bool = True,
        from_: exp.From | None = None,
    ) -> exp.Expr | None:
        query = self._parse_select_query(
            nested=nested,
            table=table,
            parse_subquery_alias=parse_subquery_alias,
            parse_set_operation=parse_set_operation,
        )

      
…[3106 chars elided]…
from_first": False}
sqlglot/generators/snowflake.py:628:        from_first = expression.args.get("from_first")
sqlglot/generators/snowflake.py:630:        if from_first is not None:
sqlglot/generators/snowflake.py:631:            if from_first:
sqlglot/generators/duckdb.py:2335:        from_first = expression.args.get("from_first", True)
sqlglot/generators/duckdb.py:2336:        if not from_first:
tests/test_expressions.py:209:            SELECT * FROM first, second, (SELECT * FROM baz) AS third
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls $P 2>/dev/null; $P -I -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2','from (select 1) t1 positional join tbl_2 t2 select t1.x']:\n  try: print(repr(sqlglot.parse_one(q, read='duckdb'))[:300])\n  except Exception as e: print('ERR', e)\n\" 2>&1 | tail -20; sed -n 3715,3745p sqlglot/parser.py", "description": "Reproduce the parse failure and view nearby parser code"}
[tool_result] <work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'

    def _parse_projections(
        self,
    ) -> tuple[list[exp.Expr], list[exp.Expr] | None]:
        return self._parse_expressions(), None

    def _parse_wrapped_select(self, table: bool = False) -> exp.Expr | None:
    
…[625 chars elided]…
      this = exp.select("*").from_(t.cast(exp.From, from_))
                this = self._parse_query_modifiers(self._parse_set_operations(this))
        else:
            this = (
                self._parse_table(consume_pipe=True)
                if table
                else self._parse_select(nested=True, parse_set_operation=False)
            )

            # Transform exp.Values into a exp.Table to pass through parse_query_modifiers
            # in case a modifier (e.g. join) is following
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2','from (select 1) t1 positional join tbl_2 t2 select t1.x', 'from (select 1 as x) t1 join (select 2 as x) t2 on true select *', 'from (FROM tbl_1) t1 select *']:\n  try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n  except Exception as e: print('ERR', str(e)[:200])\n\" 2>&1 | tail -20", "description": "Reproduce with repo sqlglot on path"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2
ERR Invalid expression / Unexpected token. Line 1, Col: 50.
  from (select 1) t1 positional join tbl_2 t2 [4mselect[0m t1.x
ERR Invalid expression / Unexpected token. Line 1, Col: 62.
  from (select 1 as x) t1 join (select 2 as x) t2 on true [4mselect[0m *
SELECT * FROM (SELECT * FROM tbl_1) AS t1
[tool_use Bash] {"command": "grep -n \"def _parse_table(\\|def _parse_table_parts\\|def _parse_join(\\|def _parse_subquery\\|def _parse_derived_table\" sqlglot/parser.py", "description": "Locate table parsing functions"}
[tool_result] 4029:    def _parse_subquery(
4363:    def _parse_join(
4564:    def _parse_table_parts_fast(self) -> exp.Table | None:
4627:    def _parse_table_parts(
4698:    def _parse_table(
4928:    def _parse_derived_table_values(self) -> exp.Values | None:
[tool_use Bash] {"command": "sed -n 4698,4790p sqlglot/parser.py; echo ----; sed -n 4029,4076p sqlglot/parser.py", "description": "Read _parse_table and _parse_subquery"}
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
…[4232 chars elided]…
          if isinstance(table.args.get("alias"), exp.TableAlias):
                        table_as_column.replace(table_as_column.this)
                        exp.alias_(unnest, None, table=[table.args["alias"].this], copy=False)

                    table.replace(unnest)

            refs.add(normalized_table.alias_or_name)

        return this

    @t.overload
    def _parse_query_modifiers(self, this: E) -> E: ...

    @t.overload
    def _parse_query_modifiers(self, this: None) -> None: ...
[tool_use Bash] {"command": "sed -n 3830,3850p sqlglot/parser.py; echo ...; awk 'NR>=3850 && NR<=4028 && /from_|joins|_parse_query_modifiers|wrapped|table|consume_pipe|this = |return/' sqlglot/parser.py | head -80; grep -n \"_parse_query_modifiers(\" sqlglot/parser.py | head -30", "description": "Trace the rest of the select query parser"}
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
…[2369 chars elided]…
query_modifiers(this)
3890:            this = self._parse_query_modifiers(this)
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
5798:                    exp.In(this=this, query=self._parse_query_modifiers(query).subquery(copy=False))
6701:                this=self._parse_query_modifiers(self._parse_set_operations(this)),
8444:        return self._parse_query_modifiers(
[tool_use Bash] {"command": "sed -n 4790,4830p sqlglot/parser.py; echo ...; sed -n 3866,3895p sqlglot/parser.py; echo ...; sed -n 3725,3752p sqlglot/parser.py", "description": "Read rest of _parse_table and surrounding select branches"}
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
…[2979 chars elided]…
self._parse_select(nested=True, parse_set_operation=False)
            )

            # Transform exp.Values into a exp.Table to pass through parse_query_modifiers
            # in case a modifier (e.g. join) is following
            if table and isinstance(this, exp.Values) and this.alias:
                alias = this.args["alias"].pop()
                this = exp.Table(this=this, alias=alias)

            this = self._parse_query_modifiers(self._parse_set_operations(this))

        return this
[tool_use Bash] {"command": "sed -n 4077,4110p sqlglot/parser.py; P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q in ['from (select 1) t1 join tbl_2 t2 select *','from (select 1) t1 join tbl_2 t2 on true select *','from (select 1) t1 join tb
…[74 chars elided]…
ct 1) t1 join (select 2) t2 on true','from (select 1) t1 join tbl_2 t2 on true','from (select 1) t1, tbl_2 t2 select *', 'from tbl_1 t1 join (select 2) t2 on true select *']:\n  try: print('OK ', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n  except Exception as e: print('ERR', q, str(e)[:80].replace(chr(10),' '))\n\" 2>&1", "description": "Read query modifiers and bisect failing variants"}
[tool_result]     def _parse_query_modifiers(self, this):
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for lateral in iter(self._parse_lateral, None):
                this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
                    parser = self.QUERY_MODIFIER_PARSERS[mo
…[1307 chars elided]…
t1 joi
ERR from (select 1) t1 join tbl_2 t2 select * Invalid expression / Unexpected token. Line 1, Col: 39.   from (select 1) t1 joi
OK  SELECT * FROM (SELECT 1) AS t1, tbl_2 AS t2 WHERE TRUE
OK  SELECT * FROM (SELECT 1) AS t1 JOIN (SELECT 2) AS t2 ON TRUE
OK  SELECT * FROM (SELECT 1) AS t1 JOIN tbl_2 AS t2 ON TRUE
ERR from (select 1) t1, tbl_2 t2 select * Invalid expression / Unexpected token. Line 1, Col: 35.   from (select 1) t1, tb
OK  SELECT * FROM tbl_1 AS t1 JOIN (SELECT 2) AS t2 ON TRUE
[tool_use Bash] {"command": "grep -rn \"class Subquery\\b\\|class Subquery(\" -A 12 sqlglot/expressions/*.py | head -30; grep -n \"def subquery_sql\" -A 25 sqlglot/generator.py | head -40; grep -n \"def table_sql\" -A 5 sqlglot/generator.py | head", "description": "Inspect Subquery expression and generator"}
[tool_result] sqlglot/expressions/query.py:1662:class Subquery(Expression, DerivedTable, Query):
sqlglot/expressions/query.py-1663-    is_subquery: t.ClassVar[bool] = True
sqlglot/expressions/query.py-1664-    arg_types = {
sqlglot/expressions/query.py-1665-        "this": True,
sqlglot/expressions/query.py-1666-        "alias": False,
sqlglot/expressions/query.py-1667-        "with_": False,
sqlglot/expressions/query.py-1668-        **QUERY_MODIFIERS,
sqlglot/expressions/query.py-1669-    }
sqlglot/expressio
…[1448 chars elided]…
rgs.get("offset")
3205-
3206-        if self.UNNEST_WITH_ORDINALITY:
3207-            if alias and isinstance(offset, exp.Expr):
2289:    def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
2290-        table = self.table_parts(expression)
2291-        only = "ONLY " if expression.args.get("only") else ""
2292-        partition = self.sql(expression, "partition")
2293-        partition = f" {partition}" if partition else ""
2294-        version = self.sql(expression, "version")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144804-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144804-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nqs=['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from (select 1) t1 join tbl_2 t2 select *','from (select 1) t1 join tbl_2 t2 on 
…[160 chars elided]…
x','from (select 1) t1, tbl_2 t2 select *']\nfor q in qs:\n  try:\n    e=sqlglot.parse_one(q, read='duckdb'); print('OK ', e.sql('duckdb'), '|', e.sql('duckdb', pretty=False))\n  except Exception as ex: print('ERR', q, str(ex)[:80].replace(chr(10),' '))\n\" 2>&1; $P -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Verify fix on variants and run full test suite"}
[tool_result] OK  SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2 | SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK  SELECT * FROM (SELECT 1) AS t1, tbl_2 AS t2 | SELECT * FROM (SELECT 1) AS t1, tbl_2 AS t2
OK  SELECT * FROM (SELECT 1) AS t1 JOIN tbl_2 AS t2 ON TRUE WHERE TRUE | SELECT * FROM (SELECT 1) AS t1 JOIN tbl_2 AS t2 ON TRUE WHERE TRUE
OK  SELECT * FROM (SELECT 1) AS t1 JOIN (SELEC
…[822 chars elided]…
................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 54.87s
[tool_use Bash] {"command": "grep -n \"POSITIONAL\\|FROM tbl\\|from tbl\\|\\\"FROM \" tests/dialects/test_duckdb.py | head -20; P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\ntry: sqlglot.parse_one('from tbl_1 t1 join tbl_2 t2 on true select * from x', read='duckdb'); print('ok')\nexcept Exception as ex: print('ERR plain-table too')\n\"; $P -c \"import duckdb; print(duckdb.__version__)\"", "description": "Find existing FROM-first tests and check duckdb availability"}
[tool_result] 426:            "SELECT tbl.x*1e4+tbl.y FROM tbl",
427:            "SELECT tbl.x * 1e4 + tbl.y FROM tbl",
469:        self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
485:        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
496:        self.validate_identity("SUMMARIZ
…[519 chars elided]…
AMPLE 10%",
1955:            "SELECT * FROM tbl USING SAMPLE SYSTEM (10 PERCENT)",
1958:            "SELECT * FROM tbl USING SAMPLE 10 PERCENT (bernoulli)",
1959:            "SELECT * FROM tbl USING SAMPLE BERNOULLI (10 PERCENT)",
1962:            "SELECT * FROM tbl USING SAMPLE reservoir(50 ROWS) REPEATABLE (100)",
1963:            "SELECT * FROM tbl USING SAMPLE RESERVOIR (50 ROWS) REPEATABLE (100)",
1966:            "SELECT * FROM tbl USING SAMPLE 10% (system, 377)",
ERR plain-table too
1.5.6
[tool_use Bash] {"command": "sed -n 480,492p tests/dialects/test_duckdb.py; sed -n 1515,1522p tests/dialects/test_duckdb.py", "description": "View FROM-first test block context"}
[tool_result]         self.validate_identity("SELECT {'x': 1, 'y': 2, 'z': 3}")
        self.validate_identity("SELECT {'key1': 'string', 'key2': 1, 'key3': 12.345}")
        self.validate_identity("SELECT ROW(x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT (x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT a.x FROM (SELECT {'x': 1, 'y': 2, 'z': 3} AS a)")
        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x 
…[399 chars elided]…
entity("x -> '$.family'")
        self.validate_identity(
            "SELECT CAST(TRIM(CAST(CAST('***apple***' AS BLOB) AS TEXT), CAST(CAST('*' AS BLOB) AS TEXT)) AS BLOB) AS result"
        )
        self.validate_identity("SELECT GREATEST(1.0, 2.5, NULL, 3.7)")
        self.validate_identity("FROM t1, t2 SELECT *", "SELECT * FROM t1, t2")
        self.validate_identity("ROUND(2.256, 1)")

        # TODO: This is incorrect AST, DATE_PART creates a STRUCT of values but it's stored in 'year' arg
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144804-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM t1, t2 SELECT *\", \"SELECT * FROM t1, t2\")\n        self.validate_identity(\"ROUND(2.256, 1)\")", "new_string": "        self.validate_identity(\"FROM t1, t2 SELECT *\", \"SELECT * FROM t1, t2\")\n        self.validate_identity(\n            \"FROM (FROM tbl_1) t1 POSITIONAL JOIN (FROM tbl_2) t2 SELECT t1.x AS x1, t2.x AS x2\",\n            \"SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )\n        self.validate_identity(\"ROUND(2.256, 1)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144804-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3; $P -c \"\nimport sys; sys.path.insert(0,'.')\nimport duckdb, sqlglot\nc=duckdb.connect()\nc.sql('create table tbl_1 as select 1 as x'); c.s
…[52 chars elided]…
ql(sqlglot.transpile('FROM (FROM tbl_1) t1 POSITIONAL JOIN (FROM tbl_2) t2 SELECT t1.x AS x1, t2.x AS x2', read='duckdb', write='duckdb')[0]).fetchall())\n\"; $P -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -2; $P -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -2", "description": "Run duckdb tests, execute query in DuckDB, and lint"}
[tool_result] ........................ [ 54%]
....................       [100%]
44 passed, 598 subtests passed in 0.25s
[(1, 2)]
All checks passed!
2 files already formatted
[assistant] FROM-first queries with joined subqueries now parse. The example from the report returns `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`, and DuckDB runs the output and returns `(1, 2)`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the table-with-joins path returned early for subqueries, so the `JOIN` clauses after a subquery were never consumed. Plain tables were fine because their joins were parsed before the `SELECT` keyword was checked. The parser then hit `select` with a join still pending.

**Fix:** When `joins=True` an
…[158 chars elided]…
ot/parser.py`.

**Test:** I added a `validate_identity` case to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests, using the query from the report.

**Verification:**
- Full test suite: 1104 passed, 17947 subtests passed (run before I added the new test case).
- `tests/dialects/test_duckdb.py` after adding the case: 44 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not commit. I also did not run `make check`, which the project guidance asks for before submitting. The `rtk` wrapper wasn't on the shell path, so I ran the commands directly.
