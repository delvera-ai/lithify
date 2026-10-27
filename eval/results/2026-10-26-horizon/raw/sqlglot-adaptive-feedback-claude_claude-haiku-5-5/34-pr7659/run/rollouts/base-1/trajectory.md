# trajectory base-1

final message:
Fixed. Leading CTEs and the pipe's generated `__tmp` CTEs are now both kept, and the output matches your expected SQL:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the rest of the statement. By that point the pipe has already built `WITH __tmp1 AS (...)`, and `this.set("with_", cte)` replaced that whole `WITH` with the leading one, dropping `__tmp1`.

**Fix:** When the statement already has a `WITH`, the leading CTEs are prepended to its CTE list, so the leading ones come first and the pipe's CTEs can reference them. This is a 3-line change in `sqlglot/parser.py`.

**Test:** Added `test_with` to `tests/dialects/test_pipe_syntax.py`, covering the leading-CTE form and the `WITH ... SELECT ... |>` form. I did not edit or weaken any existing test.

**Verification:**
- Full suite via `run_suite.py` after the last edit: `SUMMARY: 1109 passed, 18038 subtests passed in 51.00s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.
- Probes: a multi-stage pipe with a leading CTE (`... |> SELECT ... |> SELECT ... AS y`) keeps every generated CTE. A leading `WITH` with two CTEs keeps both.

**Still open, not caused by this change:** `FROM x |> SELECT x1 |> UNION ALL (SELECT 5)` produces a `__tmp` CTE chain that I did not check against BigQuery semantics. It does not involve leading CTEs, so I left it alone.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn \"__tmp\\|tmp_cte\\|PIPE\" sqlglot/ --include=*.py | grep -v \"^sqlglot/tokens\" | head -60", "description": "Locate pipe syntax and temp CTE code"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git status --short | head; grep -rln \"__tmp\" sqlglot/ ; grep -rn \"pipe\" sqlglot/parsers/bigquery.py sqlglot/generators/bigquery.py sqlglot/dialects/bigquery.py | head -60", "description": "Check git status and find pipe code in BigQuery"}
[tool_result] sqlglot/parser.py
[tool_use Bash] {"command": "grep -n \"__tmp\\|PIPE_CTE\\|pipe\" sqlglot/parser.py | head -80", "description": "Find pipe-related code in parser.py"}
[tool_result] 321:        "_pipe_cte_counter",
1209:        "AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
1210:        "AS": lambda self, query: self._build_pipe_cte(
1214:        "EXTEND": lambda self, query: self._parse_pipe_syntax_extend(query),
1215:        "LIMIT": lambda self, query: self._parse_pipe_syntax_limit(query),
1219:        "PIVOT": lambda self, query: self._parse_pipe_syntax_pivot(query),
1220:        "SELECT": lambda self, query: self._parse_pipe_syntax_select(qu
…[2769 chars elided]…
   return self._build_pipe_cte(query=query, expressions=[exp.Star()])
9841:    def _parse_pipe_syntax_tablesample(self, query: exp.Select) -> exp.Select:
9852:    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
9868:                parsed_query = self._parse_pipe_syntax_set_operator(query)
9869:                parsed_query = parsed_query or self._parse_pipe_syntax_join(query)
9872:                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
[tool_use Bash] {"command": "sed -n 9680,9720p sqlglot/parser.py; echo ----; sed -n 9845,9885p sqlglot/parser.py; echo ----; sed -n 2275,2300p sqlglot/parser.py", "description": "Read pipe CTE builder and query parsing"}
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
 
…[3240 chars elided]…
eturn self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._match(TokenType.TEMPORARY)
        materialized = self._match_text_seq("MATERIALIZED")
        iceberg = self._match_text_seq("ICEBERG")

        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
        if not kind or (iceberg and kind and kind != "TABLE"):
            return self._parse_as_command(start)
[tool_use Bash] {"command": "cat > /tmp/probe_pipe.py <<'EOF'\nimport sqlglot\nfor sql in [\n    \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n    \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2 |> WHERE x1 = 1\",\n    \"WITH x AS (SELECT 1 AS x1) SELECT * FROM x |> SELECT x1\",\n    \"FROM x |> SELECT x1, 2 AS x2\",\n]:\n    e = sqlglot.parse_one(sql, read=\"bigquery\")\n    print(e.sql(\"bigquery\"))\n    print(repr(e.args.get(\"with_\"))[:0], [c.alias for c in e.args[\"with_\"].expressions] if e.args.get(\"with_\") else None)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pipe.py", "description": "Probe pipe syntax with leading CTEs"}
[tool_result] WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
 ['x']
WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1 WHERE x1 = 1
 ['x']
WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
 ['x']
WITH __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
 ['__tmp1']
[tool_use Bash] {"command": "grep -n \"def _apply_cte_builder\" -A 30 sqlglot/expressions/*.py", "description": "Read CTE builder helper"}
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
[tool_use Bash] {"command": "grep -n \"def _apply_child_list_builder\" -A 40 sqlglot/expressions/*.py | head -60; grep -n \"def pop\" -A 12 sqlglot/expressions/core.py | head -30", "description": "Read child list builder and pop implementation"}
[tool_result] sqlglot/expressions/core.py:2599:def _apply_child_list_builder(
sqlglot/expressions/core.py-2600-    *expressions: ExpOrStr | None,
sqlglot/expressions/core.py-2601-    instance: E,
sqlglot/expressions/core.py-2602-    arg: str,
sqlglot/expressions/core.py-2603-    append: bool = True,
sqlglot/expressions/core.py-2604-    copy: bool = True,
sqlglot/expressions/core.py-2605-    prefix: str | None = None,
sqlglot/expressions/core.py-2606-    into: Type[Expr] | None = None,
sqlglot/expressions/core
…[2595 chars elided]…
    """
265-        raise NotImplementedError
266-
--
484:    def pop(self: E) -> E:
485-        """
486-        Remove this expression from its AST.
487-
488-        Returns:
489-            The popped expression.
490-        """
491-        raise NotImplementedError
492-
493-    def assert_is(self, type_: Type[E]) -> E:
494-        """
495-        Assert that this `Expr` is an instance of `type_`.
496-
--
1036:    def pop_comments(self) -> list[str]:
1037-        comments = self.comments or []
[tool_use Bash] {"command": "cat > /tmp/probe_dbg.py <<'EOF'\nimport sqlglot\ne = sqlglot.parse_one(\"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\", read=\"bigquery\")\nprint(repr(e))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_dbg.py; grep -n \"def _parse_with\\b\\|def _parse_with(\" -A 25 sqlglot/parser.py | head -40", "description": "Dump AST for pipe query with leading CTE"}
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
3951:    def _parse_with(self, skip_with_token: bool = False) -> exp.With | None:
39
…[400 chars elided]…
           expressions.append(cte)
3964-                if last_comments:
3965-                    cte.add_comments(last_comments)
3966-
3967-            if not self._match(TokenType.COMMA) and not self._match(TokenType.WITH):
3968-                break
3969-            else:
3970-                self._match(TokenType.WITH)
3971-
3972-            last_comments = self._prev_comments
3973-
3974-        return self.expression(
3975-            exp.With(
3976-                expressions=expressions,
[tool_use Bash] {"command": "cat > /tmp/probe_dbg2.py <<'EOF'\nfrom sqlglot import exp\nq = exp.select(\"x1\").from_(\"x\").with_(\"x\", as_=\"SELECT 1 AS x1\")\nw = q.args.get(\"with_\")\nprint(\"popped\", repr(w.pop())[:40], q.args.get(\"with_\"))\nns = exp.select(\"*\").from_(\"__tmp1\").set(\"with_\", w)\nprint(ns.sql())\nr = ns.with_(\"__tmp1\", as_=q, copy=False)\nprint(r.sql())\nprint(r is ns)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_dbg2.py", "description": "Reproduce CTE pop and append logic"}
[tool_result ERROR] Exit code 1
popped With(
  expressions=[
    CTE(
      thi None
Traceback (most recent call last):
  File "/tmp/probe_dbg2.py", line 6, in <module>
    print(ns.sql())
          ^^^^^^
AttributeError: 'NoneType' object has no attribute 'sql'
[tool_use Bash] {"command": "cat > /tmp/probe_dbg2.py <<'EOF'\nfrom sqlglot import exp\nq = exp.select(\"x1\").from_(\"x\").with_(\"x\", as_=\"SELECT 1 AS x1\")\nw = q.args.get(\"with_\")\nw.pop()\nns = exp.select(\"*\").from_(\"__tmp1\")\nns.set(\"with_\", w)\nprint(ns.sql())\nr = ns.with_(\"__tmp1\", as_=q, copy=False)\nprint(r.sql())\nprint(r is ns, ns.sql())\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_dbg2.py", "description": "Reproduce CTE pop and append logic"}
[tool_result] WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
True WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
[tool_use Bash] {"command": "cat > /tmp/probe_dbg3.py <<'EOF'\nimport sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._build_pipe_cte\ndef wrapped(self, query, expressions, alias_cte=None):\n    print(\"IN \", query.sql(\"bigquery\"))\n    r = orig(self, query, expressions, alias_cte)\n    print(\"OUT\", r.sql(\"bigquery\"))\n    return r\nParser._build_pipe_cte = wrapped\nprint(sqlglot.transpile(\"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\", read=\"bigquery\", write=\"bigquery\"))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_dbg3.py", "description": "Trace _build_pipe_cte inputs and outputs"}
[tool_result] IN  SELECT x1, 2 AS x2 FROM x
OUT WITH __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
['WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1']
[tool_use Bash] {"command": "sed -n 3730,3800p sqlglot/parser.py", "description": "Read FROM-first select parsing with pipes"}
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
…[1724 chars elided]…
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
[tool_use Bash] {"command": "sed -n 3800,3830p sqlglot/parser.py", "description": "Read select query parsing with leading WITH"}
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
[assistant] The leading `WITH` is attached in `_parse_select_query` (`sqlglot/parser.py:~3803`). It parses the rest of the statement first, and that already contains the pipe-generated `__tmp1` CTE in its own `WITH`. Then `this.set("with_", cte)` overwrites that `WITH` with the leading one. I'll merge the two lists, leading CTEs first so `__tmp1` can reference `x`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-095523-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)", "new_string": "            if \"with_\" in this.arg_types:\n                if existing := this.args.get(\"with_\"):\n                    # e.g. pipe syntax generates CTEs that must follow the leading ones\n                    cte.set(\"expressions\", cte.expressions + existing.expressions)\n                this.set(\"with_\", cte)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-095523-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pipe.py; cat > /tmp/probe_pipe2.py <<'EOF'\nimport sqlglot\nfor sql in [\n    \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1 |> SELECT x1 AS y\",\n    \"WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1) FROM x
…[105 chars elided]…
ELECT 1 AS x1) FROM x |> SELECT x1 |> UNION ALL (SELECT 5)\",\n]:\n    print(sqlglot.transpile(sql, read=\"bigquery\", write=\"bigquery\", pretty=False)[0])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_pipe2.py", "description": "Re-run pipe probes after the fix"}
[tool_result] WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
 ['x', '__tmp1']
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1 WHERE x1 = 1
 ['x', '__tmp1']
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
 ['x', '__tmp1']
WITH __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
 ['__tmp1']
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x), __tmp2 AS (SELECT x1 AS y FROM __tmp1) SELECT * FROM __tmp2
WITH x AS (SELECT 1 AS x1), y AS (SELECT 2 AS y1) SELECT * FROM x WHERE x1 = 1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x), __tmp2 AS (SELECT * FROM __tmp1), __tmp3 AS (SELECT * FROM __tmp2 UNION ALL SELECT 5) SELECT * FROM __tmp3
[assistant] Output now matches the expected SQL, and the nested and set-operation cases keep their CTEs. Next I'll add a regression test next to the existing BigQuery pipe tests.
[tool_use Bash] {"command": "grep -n \"|>\" tests/dialects/test_bigquery.py | head -30; grep -n \"WITH\" tests/dialects/test_bigquery.py | grep \"|>\" | head", "description": "Find existing BigQuery pipe syntax tests"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rln \"|>\" tests/ | head; grep -rn \"__tmp1\" tests/ | head -5", "description": "Locate pipe syntax test files"}
[tool_result] tests/dialects/test_pipe_syntax.py
tests/dialects/test_pipe_syntax.py:8:            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
tests/dialects/test_pipe_syntax.py:12:            "WITH __tmp1 AS (SELECT x.x1, x.x2 FROM x) SELECT * FROM __tmp1",
tests/dialects/test_pipe_syntax.py:16:            "WITH __tmp1 AS (SELECT x1 AS c1, x2 AS c2 FROM x) SELECT * FROM __tmp1",
tests/dialects/test_pipe_syntax.py:20:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x) SELECT * FROM __tmp1 WHERE x1_a > 1",
tests/dialects/test_pipe_syntax.py:24:            "WITH __tmp1 AS (SELECT x1 + 1 AS x1_a, x2 - 1 AS x2_a FROM x), __tmp2 AS (SELECT x2_a FROM __tmp1 WHERE x1_a > 1) SELECT * FROM __tmp2",
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_pipe_syntax.py; tail -30 tests/dialects/test_pipe_syntax.py", "description": "Read pipe syntax test file structure"}
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
            "WITH __tmp1 AS (SELE
…[1183 chars elided]…
 SYSTEM (1 PERCENT)",
        )
        self.validate_identity(
            "FROM x |> SELECT x.x1 |> TABLESAMPLE SYSTEM (1 PERCENT)",
            "WITH __tmp1 AS (SELECT x.x1 FROM x TABLESAMPLE SYSTEM (1 PERCENT)) SELECT * FROM __tmp1",
        )
        self.validate_identity(
            "FROM x |> TABLESAMPLE SYSTEM (1 PERCENT) |> WHERE x.x1 > 0 |> SELECT x1, x2",
            "WITH __tmp1 AS (SELECT x1, x2 FROM x WHERE x.x1 > 0 TABLESAMPLE SYSTEM (1 PERCENT)) SELECT * FROM __tmp1",
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_pipe_syntax.py <<'EOF'\n\n    def test_with(self):\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) SELECT * FR
…[97 chars elided]…
CT * FROM __tmp1\",\n        )\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_pipe_syntax.py tests/dialects/test_bigquery.py 2>&1 | tail -15", "description": "Add pipe WITH regression test and run dialect tests"}
[tool_result] ......................................................................                          [100%]
70 passed, 1129 subtests passed in 0.45s
[assistant] The new test and the existing BigQuery tests pass. The harness requires a full-suite run after the last edit, so I'll run that now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py 2>&1 | tail -30", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-14:25:33 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-d16d40a64a.log
ELAPSED: 51s
SUMMARY: 1109 passed, 18038 subtests passed in 51.00s
EXIT: 0
[tool_use Bash] {"command": "(ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format check changed files"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py                  |  3 +++
 tests/dialects/test_pipe_syntax.py | 10 ++++++++++
 2 files changed, 13 insertions(+)
[assistant] Fixed. Leading CTEs and the pipe's generated `__tmp` CTEs are now both kept, and the output matches your expected SQL:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed first, then the rest of the statement. By that point the pipe has already built `WITH __tmp1 AS (...)`, and `this.set("with_", cte)` replaced that whole `WITH` with the leading one, dropping `__tmp1`.

**Fix:** When the statement already has a `WITH`, the leading CTEs are prepended to its CTE
…[298 chars elided]…
ting test.

**Verification:**
- Full suite via `run_suite.py` after the last edit: `SUMMARY: 1109 passed, 18038 subtests passed in 51.00s`, `EXIT: 0`.
- `ruff check` and `ruff format --check` pass on both changed files.
- Probes: a multi-stage pipe with a leading CTE (`... |> SELECT ... |> SELECT ... AS y`) keeps every generated CTE. A leading `WITH` with two CTEs keeps both.

**Still open, not caused by this change:** `FROM x |> SELECT x1 |> UNION ALL (SELECT 5)` produces a `__tmp` CTE chain that I did not check against BigQuery semantics. It does not involve leading CTEs, so I left it alone.
