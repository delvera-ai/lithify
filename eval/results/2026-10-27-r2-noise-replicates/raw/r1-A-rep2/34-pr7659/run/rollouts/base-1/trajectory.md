# trajectory base-1

final message:
Fixed. A pipe query with leading CTEs now keeps both its `WITH` CTEs and the generated `__tmp` CTEs.

```sql
WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2
-- now: WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the statement after it. The pipe builder had already put `__tmp1` into that statement's `with_`. The leading-`WITH` code then called `this.set("with_", cte)`, which replaced the whole `with_` and dropped `__tmp1`.

**Fix:** Before replacing, the code now moves any existing pipe-generated CTEs onto the leading `WITH` node, after the leading CTEs. That ordering matches the expected output, and chained pipe stages keep their order too. The change is two lines in `sqlglot/parser.py`.

**Test:** I added the repro case to `test_select` in `tests/dialects/test_pipe_syntax.py`. I did not touch any existing test.

**Verification:**
- Full suite with the project's pytest command: 1108 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I did not run the BigQuery-specific pytest path separately; the new case is in the base-dialect pipe test file, which the full run covers.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"__tmp\" sqlglot/ | head -50; git status --short | head", "description": "Locate generated intermediate CTE names in source"}
[tool_result] sqlglot/parser.py:9699:            new_cte = f"__tmp{self._pipe_cte_counter}"
[tool_use Bash] {"command": "grep -n \"_pipe_cte_counter\\|def _parse_pipe_syntax_query\\|def _build_pipe_cte\\|def _parse_pipe\" sqlglot/parser.py; sed -n 9670,9740p sqlglot/parser.py", "description": "Show pipe CTE generation code in parser"}
[tool_result] 321:        "_pipe_cte_counter",
1864:        self._pipe_cte_counter: int = 0
1879:        self._pipe_cte_counter = 0
9688:    def _build_pipe_cte(
9698:            self._pipe_cte_counter += 1
9699:            new_cte = f"__tmp{self._pipe_cte_counter}"
9710:    def _parse_pipe_syntax_select(self, query: exp.Select) -> exp.Select:
9719:    def _parse_pipe_syntax_limit(self, query: exp.Select) -> exp.Select:
9733:    def _parse_pipe_syntax_aggregate_fields(self) -> exp.Expr | None:
9745:    def _p
…[2697 chars elided]…
r_offset = curr_offset.expression.to_py() if curr_offset else 0
            query.offset(exp.Literal.number(curr_offset + offset.expression.to_py()), copy=False)

        return query

    def _parse_pipe_syntax_aggregate_fields(self) -> exp.Expr | None:
        this = self._parse_disjunction()
        if self._match_text_seq("GROUP", "AND", advance=False):
            return this

        this = self._parse_alias(this)

        if self._match_set((TokenType.ASC, TokenType.DESC), advance=False):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery')[0])\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x1 = 1', read='bigquery', write='bigquery')[0])\n\"; grep -n \"def with_\\|def _apply_cte_modifiers\" -A30 sqlglot/expressions.py | grep -n \"\" | sed -n 1,80p", "description": "Reproduce bug and inspect CTE builder helpers"}
[tool_result] WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1 WHERE x1 = 1
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -n \"def _apply_cte_modifiers\\|def with_(\" sqlglot/expressions.py sqlglot/*.py | head; ", "description": "Find CTE modifier helper definitions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"def _apply_cte_modifiers\" -A30 sqlglot/ | head -60", "description": "List package layout and find CTE modifier helper"}
[tool_result] __init__.py
__main__.py
__pycache__
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
[tool_use Bash] {"command": "grep -rn \"def _apply_cte_modifiers\\|def with_(\" -A28 sqlglot/expressions/ | head -90", "description": "Show with_ builder and CTE modifier implementation"}
[tool_result] sqlglot/expressions/query.py:304:    def with_(
sqlglot/expressions/query.py-305-        self: Q,
sqlglot/expressions/query.py-306-        alias: ExpOrStr,
sqlglot/expressions/query.py-307-        as_: ExpOrStr,
sqlglot/expressions/query.py-308-        recursive: bool | None = None,
sqlglot/expressions/query.py-309-        materialized: bool | None = None,
sqlglot/expressions/query.py-310-        append: bool = True,
sqlglot/expressions/query.py-311-        dialect: DialectType = None,
sqlglot/e
…[5554 chars elided]…
s to `False`.
sqlglot/expressions/dml.py-484-            materialized: set the MATERIALIZED part of the expression.
sqlglot/expressions/dml.py-485-            append: if `True`, add to any existing expressions.
sqlglot/expressions/dml.py-486-                Otherwise, this resets the expressions.
sqlglot/expressions/dml.py-487-            dialect: the dialect used to parse the input expression.
sqlglot/expressions/dml.py-488-            copy: if `False`, modify this expression instance in-place.
[tool_use Bash] {"command": "sed -n 333,360p sqlglot/expressions/query.py; grep -n \"def _apply_cte_modifiers\\|def _apply_child_list_builder\" -A25 sqlglot/expressions/core.py | head -60", "description": "Read with_ body and child-list builder helper"}
[tool_result]             copy: if `False`, modify this expression instance in-place.
            scalar: if `True`, this is a scalar common table expression.
            opts: other options to use to parse the input expressions.

        Returns:
            The modified expression.
        """
        return _apply_cte_builder(
            self,
            alias,
            as_,
            recursive=recursive,
            materialized=materialized,
            append=append,
            dialect=dialect,

…[761 chars elided]…
2-    parsed = []
2613-    properties = {} if properties is None else properties
2614-
2615-    for expression in expressions:
2616-        if expression is not None:
2617-            if _is_wrong_expression(expression, into) and into is not None:
2618-                expression = into(expressions=[expression])
2619-
2620-            expression = maybe_parse(
2621-                expression,
2622-                into=into,
2623-                dialect=dialect,
2624-                prefix=prefix,
[tool_use Bash] {"command": "grep -n \"def _apply_cte_builder\" -A40 sqlglot/expressions/query.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery')\nprint(repr(e))\n\"", "description": "Read CTE builder and dump parsed AST"}
[tool_result] 50:def _apply_cte_builder(
51-    instance: E,
52-    alias: ExpOrStr,
53-    as_: ExpOrStr,
54-    recursive: bool | None = None,
55-    materialized: bool | None = None,
56-    append: bool = True,
57-    dialect: DialectType = None,
58-    copy: bool = True,
59-    scalar: bool | None = None,
60-    **opts: Unpack[ParserNoDialectArgs],
61-) -> E:
62-    alias_expression = maybe_parse(alias, dialect=dialect, into=TableAlias, **opts)
63-    as_expression = maybe_parse(as_, dialect=dialect, copy
…[801 chars elided]…
 return _named_selects(self)
88-
89-
90-def _named_selects(self: Expr) -> list[str]:
Select(
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
[tool_use Bash] {"command": "sed -n 9852,9900p sqlglot/parser.py; grep -n \"_parse_pipe_syntax_query\\|consume_pipe\" sqlglot/parser.py | head -30", "description": "Read pipe query parse loop and callers"}
[tool_result]     def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
        if isinstance(query, exp.Subquery):
            query = exp.select("*").from_(query, copy=False)

        if not query.args.get("from_"):
            query = exp.select("*").from_(query.subquery(copy=False), copy=False)

        while self._match(TokenType.PIPE_GT):
            start_index = self._index
            start_text = self._curr.text.upper()
            parser = self.PIPE_SYNTAX_TRANSFORM_PARSERS.get(
…[2349 chars elided]…
   consume_pipe: bool = False,
4738:        if not schema and not is_db_reference and not consume_pipe and not joins:
4778:        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):
5620:        self, this: exp.Expr | None, consume_pipe: bool = False
5667:            nested=True, parse_set_operation=False, consume_pipe=consume_pipe
9711:        select = self._parse_select(consume_pipe=False)
9852:    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
[tool_use Bash] {"command": "sed -n 3770,3800p sqlglot/parser.py; sed -n 2275,2295p sqlglot/parser.py", "description": "Read select parsing around pipe consumption"}
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
…[917 chars elided]…
perations(expression) if expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
[tool_use Bash] {"command": "grep -n \"def _parse_select(\" sqlglot/parser.py; grep -n \"_parse_with(\" sqlglot/parser.py | head; grep -n \"with_ = self._parse_with\\|cte = self._parse_with\\|with_=\" sqlglot/parser.py | head -20", "description": "Locate where leading WITH is parsed"}
[tool_result] 3769:    def _parse_select(
1078:        exp.With: lambda self: self._parse_with(),
3801:        cte = self._parse_with()
3951:    def _parse_with(self, skip_with_token: bool = False) -> exp.With | None:
2881:        prop = self.expression(exp.WithSystemVersioningProperty(on=True, with_=with_))
2943:            prop = self._parse_system_versioning_property(with_=True)
2965:            return self._parse_serde_properties(with_=True)
3551:            exp.SerdeProperties(expressions=self._parse_wrapped_properties(), with_=with_)
3801:        cte = self._parse_with()
5831:                exp.JSON(this=kind, with_=_with, unique=unique)
[tool_use Bash] {"command": "sed -n 3800,3830p sqlglot/parser.py", "description": "Read _parse_select_query leading WITH handling"}
[tool_result]     ) -> exp.Expr | None:
        cte = self._parse_with()

        if cte:
            this = self._parse_statement()

            if not this:
                self.raise_error("Failed to parse any statement following CTE")
                return cte

            while isinstance(this, exp.Subquery) and this.is_wrapper:
                this = this.this

            assert this is not None
            if "with_" in this.arg_types:
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
[assistant] The leading-`WITH` handler in `_parse_select_query` (`sqlglot/parser.py:3801-3816`) calls `this.set("with_", cte)`, which overwrites the `with_` that the pipe builder already put on the statement, so the `__tmp1` CTE is dropped. The fix is to keep the pipe-generated CTEs and append them after the leading ones.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092924-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                if pipe_with := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", [*cte.expressions, *pipe_with.expressions])\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092924-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x1 = 1', 'WITH x AS (SELECT 1 AS x1) FROM x']:\n    print(sqlglot.transpile(q, read='bigquery', write='bigquery')[0])\n\"; grep -rn \"WITH .* |>\\|WITH.*FROM.*|>\" tests/dialects/test_bigquery.py | head", "description": "Verify fix on repro and related queries"}
[tool_result] WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1 WHERE x1 = 1
WITH x AS (SELECT 1 AS x1) SELECT * FROM x
[assistant] The output now matches the expected result. Next I'll add a regression test next to the existing pipe-syntax tests.
[tool_use Bash] {"command": "grep -n \"|>\" tests/dialects/test_bigquery.py | head -5; grep -n \"def test_.*pipe\" tests/dialects/test_bigquery.py", "description": "Find existing pipe syntax tests in BigQuery tests"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln \"|>\" tests/ | head; grep -rn \"def test_.*pipe\" tests/ | head", "description": "Search tests for pipe syntax coverage"}
[tool_result] tests/dialects/test_pipe_syntax.py
tests/test_expressions.py:1344:    def test_pipe_and_apply(self) -> None:
[tool_use Bash] {"command": "grep -n \"WITH\\|def test_\" tests/dialects/test_pipe_syntax.py | head -40; sed -n 1,30p tests/dialects/test_pipe_syntax.py", "description": "Inspect pipe syntax test file structure"}
[tool_result] 5:    def test_select(self):
8:            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
12:            "WITH __tmp1 AS (SELECT x.x1, x.x2 FROM x) SELECT * FROM __tmp1",
16:            "WITH __tmp1 AS (SELECT x1 AS c1, x2 AS c2 FROM x) SELECT * FROM __tmp1",
20:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x) SELECT * FROM __tmp1 WHERE x1_a > 1",
24:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tm
…[5234 chars elided]…
, x2 - 1 as x2_a |> WHERE x1_a > 1 |> SELECT x2_a",
            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tmp2 AS (SELECT x2_a FROM __tmp1 WHERE x1_a > 1) SELECT * FROM __tmp2",
        )
        self.validate_identity(
            "FROM x |> WHERE x1 > 0 OR x2 > 0 |> WHERE x3 > 1 AND x4 > 1 |> SELECT x1, x4",
            "WITH __tmp1 AS (SELECT x1, x4 FROM x WHERE (x1 > 0 OR x2 > 0) AND (x3 > 1 AND x4 > 1)) SELECT * FROM __tmp1",
        )
        self.validate_identity(
[tool_use Bash] {"command": "sed -n 74,79p tests/dialects/test_pipe_syntax.py", "description": "View end of test_select to place new test"}
[tool_result]         self.validate_identity(
            "(SELECT 1 AS col1) |> EXTEND col1 + 1 AS col2",
            "WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1",
        )

    def test_order_by(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-092924-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py", "old_string": "            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )\n\n    def test_order_by(self):", "new_string": "            \"WITH __tmp1 AS (SELECT *, col1 + 1 AS col2 FROM (SELECT 1 AS col1)) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n\n    def test_order_by(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-092924-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py has been updated successfully.
[assistant] Now the project's test command, the full suite included:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
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
1108 passed, 18038 subtests passed in 50.92s
[assistant] All 1108 tests pass. I'll also run the linter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files; show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py                  | 2 ++
 tests/dialects/test_pipe_syntax.py | 4 ++++
 2 files changed, 6 insertions(+)
[assistant] Fixed. A pipe query with leading CTEs now keeps both its `WITH` CTEs and the generated `__tmp` CTEs.

```sql
WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2
-- now: WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the statement after it. The pipe builder had already put `__tmp1` into that statement's `with_`. The leading-`WITH` code then called `this.set("with_", cte)`, which replaced the whole `with_` and dropped `__tmp1`.

**Fix:** Before repl
…[117 chars elided]…
 ordering matches the expected output, and chained pipe stages keep their order too. The change is two lines in `sqlglot/parser.py`.

**Test:** I added the repro case to `test_select` in `tests/dialects/test_pipe_syntax.py`. I did not touch any existing test.

**Verification:**
- Full suite with the project's pytest command: 1108 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.
- I did not run the BigQuery-specific pytest path separately; the new case is in the base-dialect pipe test file, which the full run covers.

I did not commit anything.
