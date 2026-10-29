# trajectory base-1

final message:
Fixed. The query now produces the expected SQL:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `sqlglot/parser.py`, `_parse_select_query` parses the leading `WITH` and then parses the rest of the statement, which includes the whole pipe chain. The pipe chain already returns a query with its own `WITH __tmp1 ...`. The leading CTEs were then attached with `this.set("with_", cte)`, which replaced the pipe's CTE list and dropped `__tmp1`.

**Fix:** When the result already has a `WITH`, the leading CTEs are prepended to its list instead of replacing it. Ordering puts the user's CTEs first, then the generated ones. This is two added lines in `sqlglot/parser.py`.

**Test:** I added the reported query to `test_select` in `tests/dialects/test_pipe_syntax.py`, placed next to the other pipe cases. I did not change any existing test.

**Verification:**
- Full suite with the project's command: 1108 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I also checked a chained case, `WITH x AS (...) FROM x |> AS y |> SELECT x1`, which now keeps `x`, `y`, and `__tmp1`.

I did not run the test against the unfixed code to confirm it fails there. The trace of `_build_pipe_cte` showed the input already lacked the leading `WITH`, which is the same mechanism.

Nothing has been committed.

## events
[tool_use Bash] {"command": "grep -rn \"__tmp\\|pipe\\|Pipe\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/generator.py | head -80", "description": "Find pipe syntax handling in BigQuery and parser code"}
[tool_result] sqlglot/generator.py:3505:            # Transpile to double pipe operators, which typically returns NULL if any args are NULL
sqlglot/generator.py:3509:            return sqlglot.dialects.dialect.concat_to_dpipe_sql(self, expression)
sqlglot/generator.py:4188:    def dpipe_sql(self, expression: exp.DPipe) -> str:
sqlglot/parser.py:321:        "_pipe_cte_counter",
sqlglot/parser.py:1209:        "AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
sqlglot/parser.py:1210:     
…[4074 chars elided]…
41:    def _parse_pipe_syntax_tablesample(self, query: exp.Select) -> exp.Select:
sqlglot/parser.py:9852:    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
sqlglot/parser.py:9868:                parsed_query = self._parse_pipe_syntax_set_operator(query)
sqlglot/parser.py:9869:                parsed_query = parsed_query or self._parse_pipe_syntax_join(query)
sqlglot/parser.py:9872:                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
[tool_use Bash] {"command": "sed -n 2270,2300p sqlglot/parser.py && echo ---- && sed -n 9685,9720p sqlglot/parser.py && echo ---- && sed -n 9850,9900p sqlglot/parser.py", "description": "Read pipe CTE builder and query parsing code"}
[tool_result]             return None

        if self._match_set(self.STATEMENT_PARSERS):
            comments = self._prev_comments
            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
            stmt.add_comments(comments, prepend=True)
            return stmt

        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
            return self._parse_command()

        if self._match_text_seq("WHILE"):
            return self._parse_whileblock()

        expression = self._parse_e
…[3781 chars elided]…
se_types()
        default = (
            self._match(TokenType.DEFAULT) or self._match(TokenType.EQ)
        ) and self._parse_bitwise()

        return self.expression(exp.DeclareItem(this=vars, kind=kind, default=default))

    def _parse_declare(self) -> exp.Declare | exp.Command:
        start = self._prev
        replace = self._match_text_seq("OR", "REPLACE")
        expressions = self._try_parse(lambda: self._parse_csv(self._parse_declareitem))

        if not expressions or self._curr:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery')\nprint(repr(e))\nprint(e.sql('bigquery'))\n\" ; grep -n \"def with_\" -A30 sqlglot/expressions.py | head -60", "description": "Reproduce the bug and inspect the with_ builder"}
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
WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"def _apply_cte_builder\" -A30 sqlglot/ | head -45", "description": "Locate CTE builder implementation"}
[tool_result] sqlglot/expressions/query.py:50:def _apply_cte_builder(
sqlglot/expressions/query.py-51-    instance: E,
sqlglot/expressions/query.py-52-    alias: ExpOrStr,
sqlglot/expressions/query.py-53-    as_: ExpOrStr,
sqlglot/expressions/query.py-54-    recursive: bool | None = None,
sqlglot/expressions/query.py-55-    materialized: bool | None = None,
sqlglot/expressions/query.py-56-    append: bool = True,
sqlglot/expressions/query.py-57-    dialect: DialectType = None,
sqlglot/expressions/query.py-58-
…[992 chars elided]…
t/expressions/query.py-71-        arg="with_",
sqlglot/expressions/query.py-72-        append=append,
sqlglot/expressions/query.py-73-        copy=copy,
sqlglot/expressions/query.py-74-        into=With,
sqlglot/expressions/query.py-75-        properties={"recursive": recursive} if recursive else {},
sqlglot/expressions/query.py-76-    )
sqlglot/expressions/query.py-77-
sqlglot/expressions/query.py-78-
sqlglot/expressions/query.py-79-@trait
sqlglot/expressions/query.py-80-class Selectable(Expr):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nq = exp.select('x1').from_('x').with_('x', as_='SELECT 1 AS x1')\nctes = q.args['with_'].pop()\nprint('after pop, q with:', q.args.get('with_'))\nn = exp.select('*').from_('__tmp1').set('with_', ctes)\nprint(n.sql())\nn.with_('__tmp1', as_=q, copy=False)\nprint(n.sql())\n\"", "description": "Debug CTE pop and append behavior in isolation"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 7, in <module>
AttributeError: 'NoneType' object has no attribute 'sql'
after pop, q with: None
[tool_use Bash] {"command": "grep -rn \"    def pop(\" -A12 sqlglot/expressions/core.py | head -30; grep -rn \"def set(\" -A3 sqlglot/expressions/core.py | head", "description": "Check Expr.pop semantics"}
[tool_result] sqlglot/expressions/core.py:484:    def pop(self: E) -> E:
sqlglot/expressions/core.py-485-        """
sqlglot/expressions/core.py-486-        Remove this expression from its AST.
sqlglot/expressions/core.py-487-
sqlglot/expressions/core.py-488-        Returns:
sqlglot/expressions/core.py-489-            The popped expression.
sqlglot/expressions/core.py-490-        """
sqlglot/expressions/core.py-491-        raise NotImplementedError
sqlglot/expressions/core.py-492-
sqlglot/expressions/core.py-
…[976 chars elided]…
 k in self.args:
sqlglot/expressions/core.py-1283-                if k not in self.arg_types:
sqlglot/expressions/core.py:267:    def set(
sqlglot/expressions/core.py-268-        self,
sqlglot/expressions/core.py-269-        arg_key: str,
sqlglot/expressions/core.py-270-        value: object,
--
sqlglot/expressions/core.py:1050:    def set(
sqlglot/expressions/core.py-1051-        self,
sqlglot/expressions/core.py-1052-        arg_key: str,
sqlglot/expressions/core.py-1053-        value: object,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nq = exp.select('x1').from_('x').with_('x', as_='SELECT 1 AS x1')\nctes = q.args['with_'].pop()\nn = exp.select('*').from_('__tmp1')\nn.set('with_', ctes)\nprint('A', n.sql())\nn.with_('__tmp1', as_=q, copy=False)\nprint('B', n.sql())\n\"", "description": "Retry CTE pop/append debug with correct API usage"}
[tool_result] A WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
B WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp, parser\norig = parser.Parser._build_pipe_cte\ndef wrap(self, query, expressions, alias_cte=None):\n    print('IN', query.sql('bigquery'), '| with=', query.args.get('with_') is not None)\n    r = orig(self, query, expressions, alias_cte)\n    print('OUT', r.sql('bigquery'))\n    return r\nparser.Parser._build_pipe_cte = wrap\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery'))\n\"", "description": "Trace _build_pipe_cte inputs and outputs"}
[tool_result] IN SELECT x1, 2 AS x2 FROM x | with= False
OUT WITH __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
['WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1']
[tool_use Bash] {"command": "sed -n 3728,3830p sqlglot/parser.py", "description": "Read _parse_select FROM-first and pipe handling"}
[tool_result]             return self.expression(exp.Tuple(expressions=[expression]))
        return None

    def _parse_projections(
        self,
    ) -> tuple[list[exp.Expr], list[exp.Expr] | None]:
        return self._parse_expressions(), None

    def _parse_wrapped_select(self, table: bool = False) -> exp.Expr | None:
        if self._match_set((TokenType.PIVOT, TokenType.UNPIVOT)):
            this: exp.Expr | None = self._parse_simplified_pivot(
                is_unpivot=self._prev.token_type == T
…[2705 chars elided]…
_" in this.arg_types:
                this.set("with_", cte)
            else:
                self.raise_error(f"{this.key} does not support CTE")
                this = cte

            return this

        # duckdb supports leading with FROM x
        from_ = (
            self._parse_from(joins=True, consume_pipe=True)
            if self._match(TokenType.FROM, advance=False)
            else None
        )

        if self._match(TokenType.SELECT):
            comments = self._prev_comments
[assistant] The leading `WITH` is attached in `_parse_select_query` after the whole pipe statement has already been parsed. `this.set("with_", cte)` then overwrites the `__tmp1` CTE list. I'll merge the two lists instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-110355-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                if with_ := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", [*cte.expressions, *with_.expressions])\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-110355-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery'))\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery', pretty=False))\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> AS y |> SELECT x1', read='bigquery', write='bigquery'))\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) SELECT * FROM x', read='bigquery', write='bigquery'))\n\"", "description": "Verify the fix on the reported and related queries"}
[tool_result] ['WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1']
['WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1']
['WITH x AS (SELECT 1 AS x1), y AS (SELECT * FROM x), __tmp1 AS (SELECT x1 FROM y) SELECT * FROM __tmp1']
['WITH x AS (SELECT 1 AS x1) SELECT * FROM x']
[assistant] The output now matches the expected SQL. Next I'll add a regression test next to the existing BigQuery pipe tests and run the suite.
[tool_use Bash] {"command": "grep -n \"|>\" tests/dialects/test_bigquery.py | head -20; grep -n \"def test_.*pipe\" tests/dialects/test_bigquery.py", "description": "Find existing BigQuery pipe syntax tests"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln \"|>\" tests/ | head; grep -rn \"|> SELECT\" tests/dialects/*.py | head -5", "description": "Locate pipe syntax tests across the test suite"}
[tool_result] tests/dialects/test_pipe_syntax.py
tests/dialects/test_pipe_syntax.py:8:            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
tests/dialects/test_pipe_syntax.py:11:            "FROM x |> SELECT x.x1, x.x2",
tests/dialects/test_pipe_syntax.py:15:            "FROM x |> SELECT x1 as c1, x2 as c2",
tests/dialects/test_pipe_syntax.py:19:            "FROM x |> SELECT x1 + 1 as x1_a, x2 - 1 as x2_a |> WHERE x1_a > 1",
tests/dialects/test_pipe_syntax.py:23:            "FROM x |> SELECT x1 + 1 as x1_a, x2 - 1 as x2_a |> WHERE x1_a > 1 |> SELECT x2_a",
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_pipe_syntax.py; grep -n \"WITH\" tests/dialects/test_pipe_syntax.py | head", "description": "View pipe syntax test file header and CTE tests"}
[tool_result] from tests.dialects.test_dialect import Validator


class TestPipeSyntax(Validator):
    def test_select(self):
        self.validate_identity("FROM x", "SELECT * FROM x")
        self.validate_identity(
            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
        )
        self.validate_identity(
            "FROM x |> SELECT x.x1, x.x2",
            "WITH __tmp1 AS (SELECT x.x1, x.x2 FROM x) SELECT * FROM __tmp1",
8:            "FROM x |> SELECT x
…[611 chars elided]…
SELECT * FROM __tmp1",
32:            "WITH __tmp1 AS (SELECT x1 AS gt1, x2 AS gt2 FROM x WHERE x1 > 1 AND x2 > 2) SELECT * FROM __tmp1",
36:            "WITH __tmp1 AS (SELECT x1 AS gt1, x2 AS gt2 FROM x WHERE x1 > 1 AND x2 > 2), __tmp2 AS (SELECT gt1 * 2 + gt2 * 2 AS gt2_2 FROM __tmp1) SELECT * FROM __tmp2",
40:            "WITH __tmp1 AS (SELECT x, y FROM (SELECT 1 AS y, 2 AS x)) SELECT * FROM __tmp1",
44:            "WITH a_x AS (SELECT x1, x2, x3 FROM x) SELECT * FROM a_x WHERE a_x.x1 > 0",
[tool_use Bash] {"command": "grep -n \"def test_\\|^    def \" tests/dialects/test_pipe_syntax.py | head -30; sed -n 40,60p tests/dialects/test_pipe_syntax.py", "description": "List test methods and view a middle section"}
[tool_result] 5:    def test_select(self):
79:    def test_order_by(self):
101:    def test_limit(self):
123:    def test_aggregate(self):
176:    def test_set_operators(self):
335:    def test_join(self):
388:    def test_pivot_unpivot(self):
407:    def test_as(self):
421:    def test_distinct(self):
439:    def test_extend(self):
453:    def test_tablesample(self):
            "WITH __tmp1 AS (SELECT x, y FROM (SELECT 1 AS y, 2 AS x)) SELECT * FROM __tmp1",
        )
        self.validate_identity(
       
…[1038 chars elided]…
OM __tmp1))) SELECT * FROM __tmp2",
        )
        self.validate_identity(
            "FROM (SELECT 1 as x1) AS x |> SELECT x.x1 |> UNION ALL (FROM (SELECT 1 AS c) |> SELECT c) |> SELECT x1",
            "SELECT * FROM (WITH __tmp1 AS (SELECT x.x1 FROM (SELECT 1 AS x1) AS x), __tmp3 AS (SELECT * FROM __tmp1), __tmp4 AS (SELECT * FROM __tmp3 UNION ALL SELECT * FROM (WITH __tmp2 AS (SELECT c FROM (SELECT 1 AS c)) SELECT * FROM __tmp2)), __tmp5 AS (SELECT x1 FROM __tmp4) SELECT * FROM __tmp5)",
[tool_use Bash] {"command": "sed -n 60,78p tests/dialects/test_pipe_syntax.py", "description": "View end of test_select to place new test"}
[tool_result]             "SELECT * FROM (WITH __tmp1 AS (SELECT x.x1 FROM (SELECT 1 AS x1) AS x), __tmp3 AS (SELECT * FROM __tmp1), __tmp4 AS (SELECT * FROM __tmp3 UNION ALL SELECT * FROM (WITH __tmp2 AS (SELECT c FROM (SELECT 1 AS c)) SELECT * FROM __tmp2)), __tmp5 AS (SELECT x1 FROM __tmp4) SELECT * FROM __tmp5)",
        )
        self.validate_identity(
            "FROM (SELECT x1 FROM (SELECT 1 as x1) |> SELECT x1) |> SELECT x1",
            "SELECT * FROM (WITH __tmp2 AS (SELECT x1 FROM ((WITH __tmp1 
…[205 chars elided]…
 (WITH __tmp1 AS (SELECT id FROM t2) SELECT * FROM __tmp1)",
        )
        self.validate_identity(
            "SELECT * FROM t1 LEFT JOIN (FROM t2 |> SELECT id) ON TRUE",
            "SELECT * FROM t1 LEFT JOIN (WITH __tmp1 AS (SELECT id FROM t2) SELECT * FROM __tmp1) ON TRUE",
        )
        self.validate_identity(
            "(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2",
            "WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-110355-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py", "old_string": "            \"(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2\",\n            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )", "new_string": "    
…[1 chars elided]…
       \"(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2\",\n            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-110355-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py has been updated successfully.
[assistant] Now the full test suite, using the project's check command.
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
1108 passed, 18038 subtests passed in 63.08s (0:01:03)
[tool_use Bash] {"command": "git diff --stat && (<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py 2>&1 || true) | tail -3; (<work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py 2>&1 || true) | tail -2", "description": "Show diff stats and run ruff lint and format checks"}
[tool_result]  sqlglot/parser.py                  | 2 ++
 tests/dialects/test_pipe_syntax.py | 4 ++++
 2 files changed, 6 insertions(+)
All checks passed!
2 files already formatted
[assistant] Fixed. The query now produces the expected SQL:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `sqlglot/parser.py`, `_parse_select_query` parses the leading `WITH` and then parses the rest of the statement, which includes the whole pipe chain. The pipe chain already returns a query with its own `WITH __tmp1 ...`. The leading CTEs were then attached with `this.set("with_", cte)`, which replaced the pipe's CTE list and dropped `__tmp1`.

**Fix:** When the result already has a `WITH`, the leading CTEs are prepended to its list ins
…[202 chars elided]…
cts/test_pipe_syntax.py`, placed next to the other pipe cases. I did not change any existing test.

**Verification:**
- Full suite with the project's command: 1108 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I also checked a chained case, `WITH x AS (...) FROM x |> AS y |> SELECT x1`, which now keeps `x`, `y`, and `__tmp1`.

I did not run the test against the unfixed code to confirm it fails there. The trace of `_build_pipe_cte` showed the input already lacked the leading `WITH`, which is the same mechanism.

Nothing has been committed.
