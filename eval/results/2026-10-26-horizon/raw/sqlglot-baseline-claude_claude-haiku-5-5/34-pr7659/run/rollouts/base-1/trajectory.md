# trajectory base-1

final message:
Fixed. `WITH x AS (...) FROM x |> SELECT x1, 2 AS x2` now produces `WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1`, keeping both the leading CTEs and the pipe's intermediate CTEs.

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the rest of the statement, including the pipe chain, is parsed. The pipe chain already carries its own `WITH` holding `__tmp1`. The code then did `this.set("with_", cte)`, which replaced that whole `WITH` with just the leading CTEs.

**Fix:** In `sqlglot/parser.py`, if the parsed statement already has a `WITH`, the leading CTEs are prepended to its expressions before it is set. Leading CTEs come first, so the generated CTEs can reference them. The `RECURSIVE` property on the leading `WITH` is kept, since the pipe-generated `WITH` never sets it.

**Test:** I added `test_leading_with` to `tests/dialects/test_pipe_syntax.py`. It covers the reported query and a two-CTE variant with a further `|> WHERE` stage.

**Verification:**
- Full suite: 1109 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on the two changed files.
- I did not run `make check` itself, which also runs mypy. That is the remaining gap.

I have not committed anything.

## events
[tool_use Bash] {"command": "rtk grep -n \"__tmp\\|pipe\\|PIPE\" sqlglot/dialects/bigquery.py sqlglot/transforms.py sqlglot/parser.py | head -80", "description": "Find pipe syntax handling code"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"__tmp\\|pipe\" sqlglot/dialects/bigquery.py sqlglot/transforms.py | head -80", "description": "Search for pipe and tmp CTE handling"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln \"PIPE_CTE\\|__tmp\\|pipe_cte\\|PipeCte\\|pipe_syntax\\|FROM_PIPE\\|PIPE\" sqlglot | head; git log --oneline -3", "description": "Locate pipe-syntax implementation files"}
[tool_result] sqlglot/tokenizer_core.py
sqlglot/parser.py
sqlglot/tokens.py
sqlglot/parsers/solr.py
sqlglot/parsers/singlestore.py
sqlglot/parsers/prql.py
sqlglot/parsers/mysql.py
sqlglot/dialects/dialect.py
sqlglot/dialects/prql.py
sqlglot/dialects/solr.py
5499576a3 lithify: probe base
d2991178a eval setup at 8e34388be82d
8e34388be Sync w/ integration tests
[tool_use Bash] {"command": "grep -rn \"__tmp\\|PIPE_OPERATORS\\|_parse_pipe\\|pipe\" sqlglot/parser.py sqlglot/dialects/bigquery.py sqlglot/parsers/bigquery.py sqlglot/generator.py sqlglot/generators/bigquery.py sqlglot/transforms.py 2>/dev/null | head -80; ls sqlglot | head -50", "description": "Search pipe handling in parser and generator"}
[tool_result] sqlglot/generator.py:3505:            # Transpile to double pipe operators, which typically returns NULL if any args are NULL
sqlglot/generator.py:3509:            return sqlglot.dialects.dialect.concat_to_dpipe_sql(self, expression)
sqlglot/generator.py:4188:    def dpipe_sql(self, expression: exp.DPipe) -> str:
sqlglot/parser.py:321:        "_pipe_cte_counter",
sqlglot/parser.py:1209:        "AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
sqlglot/parser.py:1210:     
…[4304 chars elided]…
glot/parser.py:9869:                parsed_query = parsed_query or self._parse_pipe_syntax_join(query)
sqlglot/parser.py:9872:                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
__init__.py
__main__.py
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
[tool_use Bash] {"command": "sed -n 9680,9720p sqlglot/parser.py; echo ----; sed -n 9850,9900p sqlglot/parser.py; echo ----; sed -n 2270,2300p sqlglot/parser.py; echo ---; sed -n 1870,1885p sqlglot/parser.py", "description": "Read pipe CTE builder and query parser"}
[tool_result]         )

    def _identifier_expression(
        self, token: Token | None = None, quoted: bool | None = None
    ) -> exp.Identifier:
        token = token or self._prev
        return self.expression(exp.Identifier(this=token.text, quoted=quoted), token)

    def _build_pipe_cte(
        self,
        query: exp.Query,
        expressions: list[exp.Expr],
        alias_cte: exp.TableAlias | None = None,
    ) -> exp.Select:
        new_cte: str | exp.TableAlias | None
        if alias_cte:
 
…[4392 chars elided]…
f._parse_as_command(start)
---
        self.sql = ""
        self.errors = []
        self._tokens = []
        self._tokens_size = 0
        self._index = 0
        self._curr = SENTINEL_NONE
        self._next = SENTINEL_NONE
        self._prev = SENTINEL_NONE
        self._prev_comments = []
        self._pipe_cte_counter = 0
        self._chunks = []
        self._chunk_index = 0
        self._node_count = 0

    def _advance(self, times: i64 = 1) -> None:
        index = self._index + times
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python && PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', 'WITH x AS (SELECT 1 AS x1) SELECT * FROM x |> SELECT x1, 2 AS x2']:\n    e = sqlglot.parse_one(q, read='bigquery')\n    print(repr(e.sql('bigquery')))\n    print(e.sql('bigquery', pretty=True))\n    print(repr(e)[:1500]); print('====')\n\"", "description": "Reproduce the pipe CTE bug"}
[tool_result] <work>/env-sqlglot/bin/python
'WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1'
WITH x AS (
  SELECT
    1 AS x1
)
SELECT
  *
FROM __tmp1
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
              
…[209 chars elided]…
SELECT * FROM __tmp1'
WITH x AS (
  SELECT
    1 AS x1
)
SELECT
  *
FROM __tmp1
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
====
[assistant] The leading `WITH` is replaced rather than extended. Let me check how the builder's `with_` merges into an existing `With`.
[tool_use Bash] {"command": "grep -rn \"def _apply_cte_builder\" -A 40 sqlglot/expressions/*.py | head -60", "description": "Read CTE builder helper implementation"}
[tool_result] sqlglot/expressions/query.py:50:def _apply_cte_builder(
sqlglot/expressions/query.py-51-    instance: E,
sqlglot/expressions/query.py-52-    alias: ExpOrStr,
sqlglot/expressions/query.py-53-    as_: ExpOrStr,
sqlglot/expressions/query.py-54-    recursive: bool | None = None,
sqlglot/expressions/query.py-55-    materialized: bool | None = None,
sqlglot/expressions/query.py-56-    append: bool = True,
sqlglot/expressions/query.py-57-    dialect: DialectType = None,
sqlglot/expressions/query.py-58-
…[1574 chars elided]…
 def selects(self) -> list[Expr]:
sqlglot/expressions/query.py-83-        raise NotImplementedError("Subclasses must implement selects")
sqlglot/expressions/query.py-84-
sqlglot/expressions/query.py-85-    @property
sqlglot/expressions/query.py-86-    def named_selects(self) -> list[str]:
sqlglot/expressions/query.py-87-        return _named_selects(self)
sqlglot/expressions/query.py-88-
sqlglot/expressions/query.py-89-
sqlglot/expressions/query.py-90-def _named_selects(self: Expr) -> list[str]:
[tool_use Bash] {"command": "grep -n \"def _apply_child_list_builder\" -A 30 sqlglot/expressions/*.py | head -45", "description": "Read child list builder implementation"}
[tool_result] sqlglot/expressions/core.py:2599:def _apply_child_list_builder(
sqlglot/expressions/core.py-2600-    *expressions: ExpOrStr | None,
sqlglot/expressions/core.py-2601-    instance: E,
sqlglot/expressions/core.py-2602-    arg: str,
sqlglot/expressions/core.py-2603-    append: bool = True,
sqlglot/expressions/core.py-2604-    copy: bool = True,
sqlglot/expressions/core.py-2605-    prefix: str | None = None,
sqlglot/expressions/core.py-2606-    into: Type[Expr] | None = None,
sqlglot/expressions/core
…[1019 chars elided]…
ns/core.py-2622-                into=into,
sqlglot/expressions/core.py-2623-                dialect=dialect,
sqlglot/expressions/core.py-2624-                prefix=prefix,
sqlglot/expressions/core.py-2625-                **opts,
sqlglot/expressions/core.py-2626-            )
sqlglot/expressions/core.py-2627-            for k, v in expression.args.items():
sqlglot/expressions/core.py-2628-                if k == "expressions":
sqlglot/expressions/core.py-2629-                    parsed.extend(v)
[tool_use Bash] {"command": "sed -n 2629,2650p sqlglot/expressions/core.py", "description": "Read rest of child list builder"}
[tool_result]                     parsed.extend(v)
                else:
                    properties[k] = v

    existing = instance.args.get(arg)
    if append and existing:
        parsed = existing.expressions + parsed
    if into is None:
        raise ValueError("`into` is required to use `_apply_child_list_builder`")
    child = into(expressions=parsed)
    for k, v in properties.items():
        child.set(k, v)
    instance.set(arg, child)

    return instance


def _apply_list_builder(
    *expressions: ExpOrStr | None,
    instance: E,
    arg: str,
    append: bool = True,
[assistant] The builder does append, so something else is dropping the CTE. Let me trace `_build_pipe_cte` directly.
[tool_use Bash] {"command": "PYTHON=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PYTHON -c \"\nfrom sqlglot import exp\nimport sqlglot\nq = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x', read='bigquery')\nprint(type(q), q.args.keys())\nw = q.args.get('with_')\nprint('with', type(w), w is not None)\np = w.pop()\nprint('popped', type(p), p is w, p.sql('bigquery'))\nprint('q after pop', q.sql('bigquery'))\n\"", "description": "Trace WITH pop behavior on parsed query"}
[tool_result] <class 'sqlglot.expressions.query.Select'> dict_keys(['expressions', 'from_', 'with_'])
with <class 'sqlglot.expressions.query.With'> True
popped <class 'sqlglot.expressions.query.With'> True WITH x AS (SELECT 1 AS x1)
q after pop SELECT * FROM x
[assistant] The pop itself is fine. The likely culprit is where the leading `WITH` gets attached after the pipe query is built. Let me check `_parse_select`.
[tool_use Bash] {"command": "grep -n \"def _parse_select\\b\" sqlglot/parser.py; grep -n \"cte = self._parse_with\\|_parse_with()\" sqlglot/parser.py | head", "description": "Locate WITH parsing in select parser"}
[tool_result] 3769:    def _parse_select(
1078:        exp.With: lambda self: self._parse_with(),
3801:        cte = self._parse_with()
[tool_use Bash] {"command": "sed -n 3769,3900p sqlglot/parser.py", "description": "Read _parse_select implementation"}
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

      
…[3428 chars elided]…
nd=kind,
                    hint=hint,
                    distinct=distinct,
                    expressions=projections,
                    limit=limit,
                    exclude=exclude,
                    operation_modifiers=operation_modifiers or None,
                )
            )
            this.comments = comments

            into = self._parse_into()
            if into:
                this.set("into", into)

            if not from_:
                from_ = self._parse_from()
[assistant] Found it. In `_parse_select_query`, the leading `WITH` is parsed first, then `_parse_statement()` parses the pipe query (which already holds its own `With` containing `x` and `__tmp1`). Line 3813's `this.set("with_", cte)` then overwrites that whole `With`, dropping `__tmp1`. Let me look at existing pipe tests before making the fix.
[tool_use Bash] {"command": "grep -rn \"|>\" tests/dialects/*.py | grep -i \"with \" | head; grep -rln \"|>\" tests | head", "description": "Find existing pipe syntax tests"}
[tool_result] tests/dialects/test_pipe_syntax.py:8:            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
tests/dialects/test_pipe_syntax.py
[tool_use Bash] {"command": "sed -n 1,40p tests/dialects/test_pipe_syntax.py; grep -n \"WITH\" tests/dialects/test_pipe_syntax.py | head", "description": "Read pipe syntax test file"}
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
        )
        self.validate_i
…[2328 chars elided]…
SELECT * FROM __tmp1",
32:            "WITH __tmp1 AS (SELECT x1 AS gt1, x2 AS gt2 FROM x WHERE x1 > 1 AND x2 > 2) SELECT * FROM __tmp1",
36:            "WITH __tmp1 AS (SELECT x1 AS gt1, x2 AS gt2 FROM x WHERE x1 > 1 AND x2 > 2), __tmp2 AS (SELECT gt1 * 2 + gt2 * 2 AS gt2_2 FROM __tmp1) SELECT * FROM __tmp2",
40:            "WITH __tmp1 AS (SELECT x, y FROM (SELECT 1 AS y, 2 AS x)) SELECT * FROM __tmp1",
44:            "WITH a_x AS (SELECT x1, x2, x3 FROM x) SELECT * FROM a_x WHERE a_x.x1 > 0",
[assistant] Now the fix: when the statement already carries its own `With` (from the pipe), prepend the leading CTEs to it instead of overwriting it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-152511-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                if inner_with := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", cte.expressions + inner_with.expressions)\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-152511-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', 'WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1) FROM x |> SELECT x1 |> WHERE x1 > 0', 'WITH x AS (SELECT 1 AS x1) SELECT * FROM x']:\n    print(sqlglot.transpile(q, read='bigquery', write='bigquery')[0])\n\"", "description": "Verify fix on reproduction queries"}
[tool_result] WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1 WHERE x1 > 0
WITH x AS (SELECT 1 AS x1) SELECT * FROM x
[assistant] Output now matches the expected result. Next I'll add a regression test to the pipe-syntax test file.
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_pipe_syntax.py; tail -5 tests/dialects/test_pipe_syntax.py", "description": "List test methods and file tail"}
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
        )
        self.validate_identity(
            "FROM x |> TABLESAMPLE SYSTEM (1 PERCENT) |> WHERE x.x1 > 0 |> SELECT x1, x2",
            "WITH __tmp1 AS (SELECT x1, x2 FROM x WHERE x.x1 > 0 TABLESAMPLE SYSTEM (1 PERCENT)) SELECT * FROM __tmp1",
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_pipe_syntax.py <<'EOF'\n\n    def test_leading_with(self):\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1), y 
…[167 chars elided]…
 __tmp1 WHERE x1 > 0\",\n        )\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_pipe_syntax.py tests/dialects/test_bigquery.py 2>&1 | tail -15", "description": "Add regression test and run pipe/BigQuery tests"}
[tool_result] ......................................................................                          [100%]
70 passed, 1129 subtests passed in 0.48s
[assistant] Targeted tests pass. Now the project's full check command.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite"}
[tool_result] ........................................................................................................................................ [ 21%]
............................................................................................ [ 29%]
.......................... [ 32%]
.......................................... [ 36%]
....................................................................................... [ 43%]
.................................................. [ 48%]
...................
…[166 chars elided]…
................................. [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1109 passed, 18038 subtests passed in 50.91s
[assistant] All 1109 tests pass. I'll run the linter on the changed files too, since the repo's CLAUDE.md asks for `make check`.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff --version && $P/ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && $P/ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -8; git status --short", "description": "Lint changed files and show git status"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_pipe_syntax.py
[assistant] Fixed. `WITH x AS (...) FROM x |> SELECT x1, 2 AS x2` now produces `WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1`, keeping both the leading CTEs and the pipe's intermediate CTEs.

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the rest of the statement, including the pipe chain, is parsed. The pipe chain already carries its own `WITH` holding `__tmp1`. The code then did `this.set("with_", cte)`, which replaced that whole `WITH` with just the leading CTEs.

**Fix:** In `sqlglot/parser.py`, if the pars
…[95 chars elided]…
is set. Leading CTEs come first, so the generated CTEs can reference them. The `RECURSIVE` property on the leading `WITH` is kept, since the pipe-generated `WITH` never sets it.

**Test:** I added `test_leading_with` to `tests/dialects/test_pipe_syntax.py`. It covers the reported query and a two-CTE variant with a further `|> WHERE` stage.

**Verification:**
- Full suite: 1109 passed, 18038 subtests passed.
- `ruff check` and `ruff format --check` pass on the two changed files.
- I did not run `make check` itself, which also runs mypy. That is the remaining gap.

I have not committed anything.
