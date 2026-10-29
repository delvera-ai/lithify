# trajectory base-1

final message:
Fixed. `WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2` now produces:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** the pipe parser builds `__tmpN` CTEs into a `WITH` on the query. Then the leading-`WITH` handler in `_parse_select` (`sqlglot/parser.py`, around line 3814) called `this.set("with_", cte)`, which replaced that generated `WITH` with the leading one. The `__tmp1` CTE was dropped, so the outer `FROM __tmp1` pointed at nothing.

**Change:** in `sqlglot/parser.py`, the leading CTEs are now prepended to any `WITH` already on the query, rather than overwriting it. Leading CTEs come first, then the pipe's intermediate CTEs.

**Test:** I added the reported query to `tests/dialects/test_pipe_syntax.py`, as a `validate_identity` case. I did not touch any existing test.

**Verification:** the full pytest suite passes (1108 passed, 18038 subtests), and ruff check and format are clean on both files.

One side effect to be aware of: the merge applies to any query that has a leading `WITH` and a pre-existing `WITH`, not only pipe queries. In the suite I saw no change in behavior, but the scope is wider than the pipe case.

## events
[tool_use Bash] {"command": "grep -n \"__tmp\\|pipe\\|PIPE\" sqlglot/dialects/bigquery.py | head -80; grep -rn \"__tmp\" sqlglot/*.py | head -30", "description": "Find pipe-syntax CTE generation code"}
[tool_result] 0 matches for '__tmp\|pipe\|PIPE'
sqlglot/parser.py:9699:            new_cte = f"__tmp{self._pipe_cte_counter}"
[tool_use Bash] {"command": "grep -n \"_pipe_cte_counter\\|_parse_pipe_syntax\\|def _parse_pipe\" sqlglot/parser.py; sed -n 9670,9730p sqlglot/parser.py", "description": "Inspect pipe CTE generation in parser"}
[tool_result] 30 matches in 19 files:

1209:0:lambda self, query: self._parse_pipe_syntax_aggregate(query),
1214:0:lambda self, query: self._parse_pipe_syntax_extend(query),
1215:0:lambda self, query: self._parse_pipe_syntax_limit(query),
1219:0:lambda self, query: self._parse_pipe_syntax_pivot(query),
1220:0:lambda self, query: self._parse_pipe_syntax_select(query),
1221:0:lambda self, query: self._parse_pipe_syntax_tablesample(query),
1222:0:lambda self, query: self._parse_pipe_syntax_pivot(query),
1864:0:i
…[2952 chars elided]…
 self._parse_limit()
        offset = self._parse_offset()
        if limit:
            curr_limit = query.args.get("limit", limit)
            if curr_limit.expression.to_py() >= limit.expression.to_py():
                query.limit(limit, copy=False)
        if offset:
            curr_offset = query.args.get("offset")
            curr_offset = curr_offset.expression.to_py() if curr_offset else 0
            query.offset(exp.Literal.number(curr_offset + offset.expression.to_py()), copy=False)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery')[0])\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x1 = 1', read='bigquery', write='bigquery')[0])\nprint(sqlglot.transpile('FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery')[0])\n\"; grep -n \"pipe\" tests/dialects/test_bigquery.py | head -20", "description": "Reproduce the leading-CTE pipe bug"}
[tool_result] WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1 WHERE x1 = 1
WITH __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
0 matches for 'pipe'
[tool_use Bash] {"command": "grep -n \"def _apply_cte_builder\" -A 25 sqlglot/expressions.py; grep -n \"def pop\" -A 12 sqlglot/expressions.py | head -30", "description": "Read CTE builder and pop helpers"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"def _apply_cte_builder\" -A 25 sqlglot/ | head -40; grep -rn \"    def pop(self\" -A 12 sqlglot/expressions/ | head -20", "description": "Read CTE builder and pop helpers"}
[tool_result] sqlglot/expressions/query.py:50:def _apply_cte_builder(
sqlglot/expressions/query.py-51-    instance: E,
sqlglot/expressions/query.py-52-    alias: ExpOrStr,
sqlglot/expressions/query.py-53-    as_: ExpOrStr,
sqlglot/expressions/query.py-54-    recursive: bool | None = None,
sqlglot/expressions/query.py-55-    materialized: bool | None = None,
sqlglot/expressions/query.py-56-    append: bool = True,
sqlglot/expressions/query.py-57-    dialect: DialectType = None,
sqlglot/expressions/query.py-58-
…[1873 chars elided]…
94-        """
sqlglot/expressions/core.py-495-        Assert that this `Expr` is an instance of `type_`.
sqlglot/expressions/core.py-496-
--
sqlglot/expressions/core.py:1271:    def pop(self: E) -> E:
sqlglot/expressions/core.py-1272-        self.replace(None)
sqlglot/expressions/core.py-1273-        return self
sqlglot/expressions/core.py-1274-
sqlglot/expressions/core.py-1275-    def assert_is(self, type_: Type[E]) -> E:
sqlglot/expressions/core.py-1276-        if not isinstance(self, type_):
[tool_use Bash] {"command": "grep -n \"def _apply_child_list_builder\" -A 30 sqlglot/expressions/query.py | head -45; grep -n \"_pipe_cte_counter\\|pipe\" sqlglot/dialects/bigquery.py sqlglot/parser.py | sed -n 1,5p; sed -n 2275,2295p sqlglot/parser.py", "description": "Read child list builder and parse site"}
[tool_result] 52 matches in 1 files:

sqlglot/parser.py:321:"_pipe_cte_counter",
sqlglot/parser.py:1209:"AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
sqlglot/parser.py:1210:"AS": lambda self, query: self._build_pipe_cte(
            stmt.add_comments(comments, prepend=True)
            return stmt

        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
            return self._parse_command()

        if self._match_text_seq("WHILE"):
            return self._parse_whi
…[95 chars elided]…
perations(expression) if expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery')\nprint(repr(e))\n\" | head -30; grep -n \"def _parse_pipe_syntax_query\" -A 25 sqlglot/parser.py", "description": "Dump AST for the failing query"}
[tool_result] Select(
  expressions=[
    Star()],
  from_=From(
    this=Table(
      this=Identifier(this=__tmp1, quoted=False))),
  with_=With(
    expressions=[
      CTE(
        this=Select(
          expressions=[
            Alias(
              this=Literal(this=1, is_string=False),
              alias=Identifier(this=x1, quoted=False))]),
        alias=TableAlias(
          this=Identifier(this=x, quoted=False)))]))
9852:    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
9
…[929 chars elided]…
             parsed_query = self._parse_pipe_syntax_set_operator(query)
9869-                parsed_query = parsed_query or self._parse_pipe_syntax_join(query)
9870-                if not parsed_query:
9871-                    self._retreat(start_index)
9872-                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
9873-                    break
9874-                query = parsed_query
9875-            else:
9876-                query = parser(self, query)
9877-
[tool_use Bash] {"command": "sed -n 3770,3800p sqlglot/parser.py", "description": "Read the WITH-prefixed pipe parse site"}
[tool_result]         self,
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

        if consume_pipe and s
…[57 chars elided]…
 if not query and from_:
                query = exp.select("*").from_(from_)
            if isinstance(query, exp.Query):
                query = self._parse_pipe_syntax_query(query)
                query = query.subquery(copy=False) if query and table else query

        return query

    def _parse_select_query(
        self,
        nested: bool = False,
        table: bool = False,
        parse_subquery_alias: bool = True,
        parse_set_operation: bool = True,
    ) -> exp.Expr | None:
[tool_use Bash] {"command": "grep -n \"_parse_with(\" sqlglot/parser.py | head; grep -n \"if with_ := \\|with_ = self._parse_with\\|cte = self._parse_with\" -A 25 sqlglot/parser.py | sed -n 1,80p", "description": "Locate where leading WITH is attached to query"}
[tool_result] rg: regex parse error:
    (?:_parse_with()
    ^
error: unclosed group
0 matches for '_parse_with('
3801:        cte = self._parse_with()
3802-
3803-        if cte:
3804-            this = self._parse_statement()
3805-
3806-            if not this:
3807-                self.raise_error("Failed to parse any statement following CTE")
3808-                return cte
3809-
3810-            while isinstance(this, exp.Subquery) and this.is_wrapper:
3811-                this = this.this
3812-
3813-   
…[22 chars elided]…
s not None
3814-            if "with_" in this.arg_types:
3815-                this.set("with_", cte)
3816-            else:
3817-                self.raise_error(f"{this.key} does not support CTE")
3818-                this = cte
3819-
3820-            return this
3821-
3822-        # duckdb supports leading with FROM x
3823-        from_ = (
3824-            self._parse_from(joins=True, consume_pipe=True)
3825-            if self._match(TokenType.FROM, advance=False)
3826-            else None
[assistant] The leading `WITH` is attached in `_parse_select` via `this.set("with_", cte)`, which overwrites the `With` the pipe parser just generated (`__tmp1`). I'll merge the leading CTEs in front of the existing ones instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192317-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                # Keep any CTEs already attached by a pipe query, e.g. its intermediate __tmpN CTEs\n                if existing := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", cte.expressions + existing.expressions)\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192317-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2',\n          'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x1 = 1',\n          'WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1) FROM x |> JOIN y ON TRUE |> SELECT x1']:\n    print(sqlglot.transpile(q, read='bigquery', write='bigquery')[0])\n\"", "description": "Verify the fix on the reported queries"}
[tool_result] WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1 WHERE x1 = 1
WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1), __tmp1 AS (SELECT x1 FROM x JOIN y ON TRUE) SELECT * FROM __tmp1
[assistant] The output now matches the expected form. Next I'll add a regression test and run the project's checks.
[tool_use Bash] {"command": "grep -rn \"|> \" tests/dialects/test_bigquery.py | head -5; grep -rln \"|>\" tests/ | head", "description": "Find existing pipe syntax tests"}
[tool_result] tests/dialects/test_pipe_syntax.py
tests/fixtures/optimizer/tpc-h/customer.csv.gz
tests/fixtures/optimizer/tpc-h/supplier.csv.gz
tests/fixtures/optimizer/tpc-h/lineitem.csv.gz
tests/fixtures/optimizer/tpc-h/part.csv.gz
tests/fixtures/optimizer/tpc-h/partsupp.csv.gz
tests/fixtures/optimizer/tpc-h/orders.csv.gz
tests/fixtures/optimizer/tpc-ds/store_returns.csv.gz
tests/fixtures/optimizer/tpc-ds/customer.csv.gz
tests/fixtures/optimizer/tpc-ds/web_sales.csv.gz
[tool_use Bash] {"command": "grep -n \"WITH\\|def test\" tests/dialects/test_pipe_syntax.py | head -30; sed -n 1,30p tests/dialects/test_pipe_syntax.py", "description": "Read the pipe syntax test file"}
[tool_result] 68 matches in 14 files:

101:0:
123:0:
176:0:
192:0:f"WITH __tmp1 AS (SELECT * FROM x), __tmp2 AS (SELECT * FROM __tmp1 {op_opera...
207:0:f"WITH __tmp1 AS (SELECT x1, x2 FROM x), __tmp2 AS (SELECT * FROM __tmp1), __...
335:0:
388:0:
407:0:
421:0:
439:0:
453:0:
5:0:
79:0:
tests/dialects/test_pipe_syntax.py:8:"FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FR...
tests/dialects/test_pipe_syntax.py:12:"WITH __tmp1 AS (SELECT x.x1, x.x2 FROM x) SELECT * FROM __tmp1",
tests
…[2499 chars elided]…
, x2 - 1 as x2_a |> WHERE x1_a > 1 |> SELECT x2_a",
            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tmp2 AS (SELECT x2_a FROM __tmp1 WHERE x1_a > 1) SELECT * FROM __tmp2",
        )
        self.validate_identity(
            "FROM x |> WHERE x1 > 0 OR x2 > 0 |> WHERE x3 > 1 AND x4 > 1 |> SELECT x1, x4",
            "WITH __tmp1 AS (SELECT x1, x4 FROM x WHERE (x1 > 0 OR x2 > 0) AND (x3 > 1 AND x4 > 1)) SELECT * FROM __tmp1",
        )
        self.validate_identity(
[tool_use Bash] {"command": "sed -n 60,80p tests/dialects/test_pipe_syntax.py", "description": "Read end of pipe syntax test file"}
[tool_result]             "SELECT * FROM (WITH __tmp1 AS (SELECT x.x1 FROM (SELECT 1 AS x1) AS x), __tmp3 AS (SELECT * FROM __tmp1), __tmp4 AS (SELECT * FROM __tmp3 UNION ALL SELECT * FROM (WITH __tmp2 AS (SELECT c FROM (SELECT 1 AS c)) SELECT * FROM __tmp2)), __tmp5 AS (SELECT x1 FROM __tmp4) SELECT * FROM __tmp5)",
        )
        self.validate_identity(
            "FROM (SELECT x1 FROM (SELECT 1 as x1) |> SELECT x1) |> SELECT x1",
            "SELECT * FROM (WITH __tmp2 AS (SELECT x1 FROM ((WITH __tmp1 
…[322 chars elided]…
ELECT * FROM t1 LEFT JOIN (FROM t2 |> SELECT id) ON TRUE",
            "SELECT * FROM t1 LEFT JOIN (WITH __tmp1 AS (SELECT id FROM t2) SELECT * FROM __tmp1) ON TRUE",
        )
        self.validate_identity(
            "(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2",
            "WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1",
        )

    def test_order_by(self):
        self.validate_identity("FROM x |> ORDER BY x1", "SELECT * FROM x ORDER BY x1")
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2'))\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery'))\n\"", "description": "Check default dialect parses the query"}
[tool_result] ['WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1']
['WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1']
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192317-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py", "old_string": "            \"(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2\",\n            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )\n", "new_string": "  
…[5 chars elided]…
     \"(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2\",\n            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192317-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py has been updated successfully.
[assistant] Now the project's test command (from the harness instructions), run in full:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the full pytest suite", "timeout": 600000}
[tool_result] .......................... [ 32%]
.......................................... [ 36%]
....................................................................................... [ 43%]
.................................................. [ 48%]
............. [ 49%]
.......... [ 50%]
....... [ 51%]
........................... [ 53%]
................................................................................................................................................. [ 66%]
.................................... [ 69%]
........................................................................ [ 76%]
............................................. [ 80%]
.................................................................................................................................................... [ 93%]
....................................................................       [100%]
1108 passed, 18038 subtests passed in 45.94s
[assistant] All 1108 tests pass. I'll run a quick lint on the changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stats"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/parser.py                  | 3 +++
 tests/dialects/test_pipe_syntax.py | 4 ++++
 2 files changed, 7 insertions(+)
[assistant] Fixed. `WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2` now produces:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** the pipe parser builds `__tmpN` CTEs into a `WITH` on the query. Then the leading-`WITH` handler in `_parse_select` (`sqlglot/parser.py`, around line 3814) called `this.set("with_", cte)`, which replaced that generated `WITH` with the leading one. The `__tmp1` CTE was dropped, so the outer `FROM __tmp1` pointed at nothing.

**Change:** in `sqlglot/parser.py`, the leading CTEs are now prepended to any `WITH`
…[10 chars elided]…
n the query, rather than overwriting it. Leading CTEs come first, then the pipe's intermediate CTEs.

**Test:** I added the reported query to `tests/dialects/test_pipe_syntax.py`, as a `validate_identity` case. I did not touch any existing test.

**Verification:** the full pytest suite passes (1108 passed, 18038 subtests), and ruff check and format are clean on both files.

One side effect to be aware of: the merge applies to any query that has a leading `WITH` and a pre-existing `WITH`, not only pipe queries. In the suite I saw no change in behavior, but the scope is wider than the pipe case.
