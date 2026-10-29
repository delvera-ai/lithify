# trajectory base-1

final message:
Leading CTEs are now kept alongside the pipe's generated `__tmp` CTEs. `WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2` now produces the expected output:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the statement after it. The pipe parser had already attached a `With` node holding `__tmp1` to that statement. The code then did `this.set("with_", cte)`, which replaced that node and dropped `__tmp1`.

**Fix:** In `sqlglot/parser.py`, when the statement already has a `With`, the leading CTEs are prepended to its expressions before it is set. Leading CTEs come first, so the `__tmp` CTEs can reference them.

**Test:** I added `test_leading_ctes` to `tests/dialects/test_pipe_syntax.py`. It covers the example above and a chained `|> WHERE` variant.

**Verification:**
- Full suite with the project's pytest command: 1109 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I checked that a leading `WITH` inside a subquery, `SELECT * FROM (WITH x ... FROM x |> SELECT ...)`, also keeps both CTEs.

I did not run `make check` or the BigQuery integration tests against a live BigQuery instance. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"__tmp\\|pipe\\|PIPE\" sqlglot/dialects/bigquery.py | head -80", "description": "Find pipe syntax handling in BigQuery dialect"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "pwd; ls; git rev-parse --show-toplevel; grep -rn \"__tmp\\|PIPE_SYNTAX\\|pipe\" sqlglot/dialects/bigquery.py | head -40", "description": "Check working dir and grep pipe handling"}
[tool_result] ~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1
[tool_use Bash] {"command": "grep -rn \"__tmp\\|PIPE_SYNTAX\\|pipe\" sqlglot/ --include=*.py | grep -v \"^sqlglot/.*#\" | head -60", "description": "Search sqlglot source for pipe and tmp CTE handling"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"__tmp\" sqlglot/ | head -40; echo ---; grep -rln \"pipe\" sqlglot/ | head -40", "description": "Search sqlglot for tmp CTE names and pipe files"}
[tool_result] sqlglot/parser.py:9699:            new_cte = f"__tmp{self._pipe_cte_counter}"
---
sqlglot/parser.py
sqlglot/generator.py
sqlglot/parsers/redshift.py
sqlglot/parsers/clickhouse.py
sqlglot/parsers/snowflake.py
sqlglot/parsers/prql.py
sqlglot/parsers/duckdb.py
sqlglot/dialects/dialect.py
sqlglot/expressions/core.py
sqlglot/generators/redshift.py
sqlglot/generators/singlestore.py
sqlglot/generators/sqlite.py
sqlglot/generators/tsql.py
sqlglot/generators/mysql.py
[tool_use Bash] {"command": "grep -n \"_pipe_cte_counter\\|_parse_pipe_syntax\\|def _parse_pipe\\|_pipe_cte\\|with_\\b\" sqlglot/parser.py | head -60; echo ---; sed -n 9660,9760p sqlglot/parser.py", "description": "Inspect pipe CTE generation in parser"}
[tool_result] 321:        "_pipe_cte_counter",
1209:        "AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
1210:        "AS": lambda self, query: self._build_pipe_cte(
1214:        "EXTEND": lambda self, query: self._parse_pipe_syntax_extend(query),
1215:        "LIMIT": lambda self, query: self._parse_pipe_syntax_limit(query),
1219:        "PIVOT": lambda self, query: self._parse_pipe_syntax_pivot(query),
1220:        "SELECT": lambda self, query: self._parse_pipe_syntax_select(qu
…[6680 chars elided]…
     expr = self._parse_csv(self._parse_pipe_syntax_aggregate_fields)
        aggregates_or_groups, orders = [], []
        for element in expr:
            if isinstance(element, exp.Ordered):
                this = element.this
                if isinstance(this, exp.Alias):
                    element.set("this", this.args["alias"])
                orders.append(element)
            else:
                this = element
            aggregates_or_groups.append(this)

        if group_by_exists:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery')\nprint(repr(e))\nprint(e.sql('bigquery'))\n\" ; echo; sed -n 9796,9815p sqlglot/parser.py; grep -n \"def with_\\b\" -A60 sqlglot/expressions/core.py | grep -n \"\" | head -5", "description": "Reproduce bug and view related helper code"}
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

            first_setop.expression.
…[292 chars elided]…
irst_setop, exp.Union):
            query = query.union(*setops, copy=False, **first_setop.args)
        elif isinstance(first_setop, exp.Except):
            query = query.except_(*setops, copy=False, **first_setop.args)
        else:
            query = query.intersect(*setops, copy=False, **first_setop.args)

        query.set("with_", ctes)

        return self._build_pipe_cte(query=query, expressions=[exp.Star()])

    def _parse_pipe_syntax_join(self, query: exp.Query) -> exp.Query | None:
[tool_use Bash] {"command": "grep -n \"def with_\\|def _apply_cte_builder\" -A40 sqlglot/expressions/core.py | head -120", "description": "View with_ builder implementation"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"def with_(\\|def _apply_cte_builder\" sqlglot/ ", "description": "Locate with_ builder definition"}
[tool_result] sqlglot/expressions/query.py:50:def _apply_cte_builder(
sqlglot/expressions/query.py:304:    def with_(
sqlglot/expressions/dml.py:217:    def with_(
sqlglot/expressions/dml.py:460:    def with_(
[tool_use Bash] {"command": "sed -n 50,90p sqlglot/expressions/query.py; sed -n 304,340p sqlglot/expressions/query.py", "description": "Read CTE builder helper and Query.with_"}
[tool_result] def _apply_cte_builder(
    instance: E,
    alias: ExpOrStr,
    as_: ExpOrStr,
    recursive: bool | None = None,
    materialized: bool | None = None,
    append: bool = True,
    dialect: DialectType = None,
    copy: bool = True,
    scalar: bool | None = None,
    **opts: Unpack[ParserNoDialectArgs],
) -> E:
    alias_expression = maybe_parse(alias, dialect=dialect, into=TableAlias, **opts)
    as_expression = maybe_parse(as_, dialect=dialect, copy=copy, **opts)
    if scalar and not isins
…[1814 chars elided]…
      append: if `True`, add to any existing expressions.
                Otherwise, this resets the expressions.
            dialect: the dialect used to parse the input expression.
            copy: if `False`, modify this expression instance in-place.
            scalar: if `True`, this is a scalar common table expression.
            opts: other options to use to parse the input expressions.

        Returns:
            The modified expression.
        """
        return _apply_cte_builder(
[tool_use Bash] {"command": "sed -n 2270,2300p sqlglot/parser.py; echo ----; sed -n 3770,3830p sqlglot/parser.py; echo ----; sed -n 9852,9885p sqlglot/parser.py", "description": "View pipe query entry points and WITH handling"}
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
…[3855 chars elided]…
sed_query:
                    self._retreat(start_index)
                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
                    break
                query = parsed_query
            else:
                query = parser(self, query)

        return query

    def _parse_declareitem(self) -> exp.DeclareItem | None:
        self._match_texts(("VAR", "VARIABLE"))

        vars = self._parse_csv(self._parse_id_var)
        if not vars:
            return None
[assistant] The cause is in `_parse_select_query`: after the leading `WITH` is parsed, `this.set("with_", cte)` overwrites the `With` node that the pipe parser already attached (holding `__tmp1`). Let me check existing tests before editing.
[tool_use Bash] {"command": "grep -rn \"|>\" tests/dialects/test_bigquery.py | grep -i \"with\" | head; grep -n \"def test_pipe_syntax\\|def test_.*pipe\" tests/dialects/test_bigquery.py tests/*.py | head", "description": "Find existing BigQuery pipe syntax tests"}
[tool_result] tests/test_expressions.py:1344:    def test_pipe_and_apply(self) -> None:
[tool_use Bash] {"command": "grep -rln \"|>\" tests/ | head; grep -n \"|>\" tests/dialects/test_bigquery.py | head -5", "description": "Locate pipe syntax tests across test suite"}
[tool_result] tests/dialects/test_pipe_syntax.py
[tool_use Bash] {"command": "grep -n \"WITH\" tests/dialects/test_pipe_syntax.py | head -20; echo; sed -n 1,30p tests/dialects/test_pipe_syntax.py", "description": "Inspect existing pipe syntax tests for WITH cases"}
[tool_result] 8:            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
12:            "WITH __tmp1 AS (SELECT x.x1, x.x2 FROM x) SELECT * FROM __tmp1",
16:            "WITH __tmp1 AS (SELECT x1 AS c1, x2 AS c2 FROM x) SELECT * FROM __tmp1",
20:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x) SELECT * FROM __tmp1 WHERE x1_a > 1",
24:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tmp2 AS (SELECT x2_a FROM __tmp
…[3110 chars elided]…
, x2 - 1 as x2_a |> WHERE x1_a > 1 |> SELECT x2_a",
            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tmp2 AS (SELECT x2_a FROM __tmp1 WHERE x1_a > 1) SELECT * FROM __tmp2",
        )
        self.validate_identity(
            "FROM x |> WHERE x1 > 0 OR x2 > 0 |> WHERE x3 > 1 AND x4 > 1 |> SELECT x1, x4",
            "WITH __tmp1 AS (SELECT x1, x4 FROM x WHERE (x1 > 0 OR x2 > 0) AND (x3 > 1 AND x4 > 1)) SELECT * FROM __tmp1",
        )
        self.validate_identity(
[assistant] Now the fix: merge the leading CTEs into any `With` the pipe already attached, instead of replacing it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                if existing := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", [*cte.expressions, *existing.expressions])\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2',\n          'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x2 > 1',\n          'SELECT * FROM (WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1)',\n          'WITH x AS (SELECT 1 AS x1) SELECT * FROM x']:\n    print(sqlglot.transpile(s, read='bigquery', write='bigquery')[0])\n\"", "description": "Verify fix on several leading-CTE pipe queries"}
[tool_result] WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1 WHERE x2 > 1
SELECT * FROM (WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1)
WITH x AS (SELECT 1 AS x1) SELECT * FROM x
[assistant] The output matches the expected SQL. Now I'll add a regression test next to the existing pipe tests.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_pipe_syntax.py; sed -n 84,100p tests/dialects/test_pipe_syntax.py", "description": "List test methods and view section near insertion point"}
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
        self.validate_identity(
            "FROM x |> ORDER BY x1 |> WHERE x1 > 0 OR x1 != 1 |> ORDER BY x2 |> WHERE x2 > 0 AND x2 != 1 |> SEL
…[335 chars elided]…
T * FROM __tmp1",
        )
        self.validate_identity(
            "FROM x |> WHERE x1 > 0 |> SELECT x1 |> ORDER BY x1",
            "WITH __tmp1 AS (SELECT x1 FROM x WHERE x1 > 0) SELECT * FROM __tmp1 ORDER BY x1",
        )
        self.validate_identity(
            "FROM x |> SELECT x1, x2, x3 |> ORDER BY x1 DESC NULLS FIRST, x2 ASC NULLS LAST, x3",
            "WITH __tmp1 AS (SELECT x1, x2, x3 FROM x) SELECT * FROM __tmp1 ORDER BY x1 DESC NULLS FIRST, x2 ASC NULLS LAST, x3",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py", "old_string": "    def test_order_by(self):\n        self.validate_identity(", "new_string": "    def test_leading_ctes(self):\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELEC
…[51 chars elided]…
 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x2 > 1\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1 WHERE x2 > 1\",\n        )\n\n    def test_order_by(self):\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130234-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py has been updated successfully.
[assistant] Now the project's check command, per the harness instructions.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................ [  5%]
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 29%]
.......................... [ 32%]
.......................................... [ 36%]
............................................
…[294 chars elided]…
................................. [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1109 passed, 18038 subtests passed in 51.87s
[assistant] All 1109 tests pass. I'll run the linter on the two changed files too.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -5; git status --short", "description": "Lint changed files and show git status"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_pipe_syntax.py
[assistant] Leading CTEs are now kept alongside the pipe's generated `__tmp` CTEs. `WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2` now produces the expected output:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the statement after it. The pipe parser had already attached a `With` node holding `__tmp1` to that statement. The code then did `this.set("with_", cte)`, which replaced that node and dropped `__tmp1`.

**Fix:** In `sqlglot/parser.py`, w
…[130 chars elided]…
t, so the `__tmp` CTEs can reference them.

**Test:** I added `test_leading_ctes` to `tests/dialects/test_pipe_syntax.py`. It covers the example above and a chained `|> WHERE` variant.

**Verification:**
- Full suite with the project's pytest command: 1109 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I checked that a leading `WITH` inside a subquery, `SELECT * FROM (WITH x ... FROM x |> SELECT ...)`, also keeps both CTEs.

I did not run `make check` or the BigQuery integration tests against a live BigQuery instance. Nothing is committed.
