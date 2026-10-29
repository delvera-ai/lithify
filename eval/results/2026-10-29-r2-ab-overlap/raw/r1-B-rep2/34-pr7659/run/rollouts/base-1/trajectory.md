# trajectory base-1

final message:
Fixed. A BigQuery pipe query with leading CTEs now keeps both the leading CTEs and the pipe's generated `__tmp` CTEs:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed after the pipe chain has already been built. The code then did `this.set("with_", cte)`, which overwrote the `WITH` node that held the `__tmp` CTEs.

**Change:** When the statement already has a `with_`, the leading CTEs are now prepended to its list instead of replacing it. The leading `WITH` node is kept, so `RECURSIVE` still applies.

**Tests:** I added `test_leading_with` to `tests/dialects/test_pipe_syntax.py` with the example from your report and a `WHERE` variant. `test_pipe_syntax.py` and `test_bigquery.py` pass (70 tests). The full suite passes (1109 tests). `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -rn \"__tmp\\|PIPE_CTE\\|pipe\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/transforms.py 2>/dev/null | head -60; ls .lithify/harness/scripts/", "description": "Locate pipe syntax code and harness scripts"}
[tool_result] sqlglot/parser.py:321:        "_pipe_cte_counter",
sqlglot/parser.py:1209:        "AGGREGATE": lambda self, query: self._parse_pipe_syntax_aggregate(query),
sqlglot/parser.py:1210:        "AS": lambda self, query: self._build_pipe_cte(
sqlglot/parser.py:1214:        "EXTEND": lambda self, query: self._parse_pipe_syntax_extend(query),
sqlglot/parser.py:1215:        "LIMIT": lambda self, query: self._parse_pipe_syntax_limit(query),
sqlglot/parser.py:1219:        "PIVOT": lambda self, query: self._
…[3726 chars elided]…
e_syntax_tablesample(self, query: exp.Select) -> exp.Select:
sqlglot/parser.py:9852:    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
sqlglot/parser.py:9868:                parsed_query = self._parse_pipe_syntax_set_operator(query)
sqlglot/parser.py:9869:                parsed_query = parsed_query or self._parse_pipe_syntax_join(query)
sqlglot/parser.py:9872:                    self.raise_error(f"Unsupported pipe syntax operator: '{start_text}'.")
probe_parse.py  2.2K
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "offset": 9680, "limit": 40}
[tool_result] 9680	        )
9681	
9682	    def _identifier_expression(
9683	        self, token: Token | None = None, quoted: bool | None = None
9684	    ) -> exp.Identifier:
9685	        token = token or self._prev
9686	        return self.expression(exp.Identifier(this=token.text, quoted=quoted), token)
9687	
9688	    def _build_pipe_cte(
9689	        self,
9690	        query: exp.Query,
9691	        expressions: list[exp.Expr],
9692	        alias_cte: exp.TableAlias | None = None,
9693	    ) -> exp.Select
…[529 chars elided]…
urn new_select.with_(new_cte, as_=query, copy=False)
9709	
9710	    def _parse_pipe_syntax_select(self, query: exp.Select) -> exp.Select:
9711	        select = self._parse_select(consume_pipe=False)
9712	        if not select:
9713	            return query
9714	
9715	        return self._build_pipe_cte(
9716	            query=query.select(*select.expressions, append=False), expressions=[exp.Star()]
9717	        )
9718	
9719	    def _parse_pipe_syntax_limit(self, query: exp.Select) -> exp.Select:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "offset": 9850, "limit": 50}
[tool_result] 9850	        return query
9851	
9852	    def _parse_pipe_syntax_query(self, query: exp.Query) -> exp.Query | None:
9853	        if isinstance(query, exp.Subquery):
9854	            query = exp.select("*").from_(query, copy=False)
9855	
9856	        if not query.args.get("from_"):
9857	            query = exp.select("*").from_(query.subquery(copy=False), copy=False)
9858	
9859	        while self._match(TokenType.PIPE_GT):
9860	            start_index = self._index
9861	            start_text = se
…[1460 chars elided]…
89	        default = (
9890	            self._match(TokenType.DEFAULT) or self._match(TokenType.EQ)
9891	        ) and self._parse_bitwise()
9892	
9893	        return self.expression(exp.DeclareItem(this=vars, kind=kind, default=default))
9894	
9895	    def _parse_declare(self) -> exp.Declare | exp.Command:
9896	        start = self._prev
9897	        replace = self._match_text_seq("OR", "REPLACE")
9898	        expressions = self._try_parse(lambda: self._parse_csv(self._parse_declareitem))
9899	
[tool_use Bash] {"command": "cat .lithify/harness/scripts/probe_parse.py | head -30; printf 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\\nWITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --help 2>&1 | head -5", "description": "Inspect probe script usage"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[323 chars elided]…
s

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "printf 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\\nWITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\\n' | PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"exit $?\"", "description": "Reproduce the BigQuery pipe CTE bug"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
[tool_use Bash] {"command": "printf 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\\nWITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"exit $?\"", "description": "Reproduce the BigQuery pipe CTE bug"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
[tool_use Bash] {"command": "printf 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\\nWITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\\n' | PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read bigquery; echo \"exit $?\"", "description": "Reproduce the BigQuery pipe CTE bug with PYTHONPATH"}
[tool_result] OK        WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2
          WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
OK        WITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1
          WITH x AS (SELECT 1 AS x1) SELECT * FROM __tmp1
exit 0
[tool_use Bash] {"command": "grep -n \"def _apply_cte_builder\" -A 30 sqlglot/expressions.py sqlglot/*.py | head -50; grep -n \"pipe\" tests/dialects/test_bigquery.py | head -40", "description": "Inspect CTE builder and existing pipe tests"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
0 matches for 'pipe'
[tool_use Bash] {"command": "grep -rn \"def _apply_cte_builder\" -A 25 sqlglot/ | head -40; grep -rln \"|>\" tests/ | head", "description": "Find CTE builder and pipe syntax tests"}
[tool_result] sqlglot/expressions/query.py:50:def _apply_cte_builder(
sqlglot/expressions/query.py-51-    instance: E,
sqlglot/expressions/query.py-52-    alias: ExpOrStr,
sqlglot/expressions/query.py-53-    as_: ExpOrStr,
sqlglot/expressions/query.py-54-    recursive: bool | None = None,
sqlglot/expressions/query.py-55-    materialized: bool | None = None,
sqlglot/expressions/query.py-56-    append: bool = True,
sqlglot/expressions/query.py-57-    dialect: DialectType = None,
sqlglot/expressions/query.py-58-
…[1254 chars elided]…
sive": recursive} if recursive else {},
tests/dialects/test_pipe_syntax.py
tests/fixtures/optimizer/tpc-h/customer.csv.gz
tests/fixtures/optimizer/tpc-h/supplier.csv.gz
tests/fixtures/optimizer/tpc-h/lineitem.csv.gz
tests/fixtures/optimizer/tpc-h/part.csv.gz
tests/fixtures/optimizer/tpc-h/partsupp.csv.gz
tests/fixtures/optimizer/tpc-h/orders.csv.gz
tests/fixtures/optimizer/tpc-ds/store_returns.csv.gz
tests/fixtures/optimizer/tpc-ds/customer.csv.gz
tests/fixtures/optimizer/tpc-ds/web_sales.csv.gz
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery')\nprint(repr(e))\n\" ; grep -n \"def _apply_child_list_builder\" -A 30 sqlglot/expressions/*.py | head -45", "description": "Dump AST for the failing query"}
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
sqlglot/expressions/core.py:2599:def _apply_child_list_builder(
sqlglot/expressions/
…[1435 chars elided]…
ns/core.py-2622-                into=into,
sqlglot/expressions/core.py-2623-                dialect=dialect,
sqlglot/expressions/core.py-2624-                prefix=prefix,
sqlglot/expressions/core.py-2625-                **opts,
sqlglot/expressions/core.py-2626-            )
sqlglot/expressions/core.py-2627-            for k, v in expression.args.items():
sqlglot/expressions/core.py-2628-                if k == "expressions":
sqlglot/expressions/core.py-2629-                    parsed.extend(v)
[tool_use Bash] {"command": "sed -n 2629,2650p sqlglot/expressions/core.py; sed -n 9719,9735p sqlglot/parser.py", "description": "Read rest of child list builder and limit parser"}
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
    *express
…[365 chars elided]…
to_py():
                query.limit(limit, copy=False)
        if offset:
            curr_offset = query.args.get("offset")
            curr_offset = curr_offset.expression.to_py() if curr_offset else 0
            query.offset(exp.Literal.number(curr_offset + offset.expression.to_py()), copy=False)

        return query

    def _parse_pipe_syntax_aggregate_fields(self) -> exp.Expr | None:
        this = self._parse_disjunction()
        if self._match_text_seq("GROUP", "AND", advance=False):
[tool_use Bash] {"command": "sed -n 2270,2300p sqlglot/parser.py; sed -n 3770,3830p sqlglot/parser.py", "description": "Read where pipe query is invoked"}
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
…[2235 chars elided]…
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
[assistant] The leading-WITH branch in `_parse_select_query` replaces the `with_` node wholesale, which drops the pipe-generated `__tmp` CTEs. Let me read that exact region before editing.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "offset": 5636, "limit": 30}
[tool_result] 5636	        elif token_type == TokenType.EXCEPT:
5637	            operation = exp.Except
5638	        else:
5639	            operation = exp.Intersect
5640	
5641	        comments = self._prev.comments
5642	
5643	        if self._match(TokenType.DISTINCT):
5644	            distinct: bool | None = True
5645	        elif self._match(TokenType.ALL):
5646	            distinct = False
5647	        else:
5648	            distinct = self.dialect.SET_OP_DISTINCT_BY_DEFAULT[operation]
5649	            if
…[153 chars elided]…
      self._match_text_seq("BY", "NAME")
5654	            or self._match_text_seq("STRICT", "CORRESPONDING")
5655	            or None
5656	        )
5657	        if self._match_text_seq("CORRESPONDING"):
5658	            by_name = True
5659	            if not side and not kind:
5660	                kind = "INNER"
5661	
5662	        on_column_list = None
5663	        if by_name and self._match_texts(("ON", "BY")):
5664	            on_column_list = self._parse_wrapped_csv(self._parse_column)
5665	
[tool_use Bash] {"command": "grep -n 'if \"with_\" in this.arg_types' sqlglot/parser.py", "description": "Locate leading CTE attach line"}
[tool_result] 1 matches in 1 files:

3814:0:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "offset": 3800, "limit": 25}
[tool_result] 3800	    ) -> exp.Expr | None:
3801	        cte = self._parse_with()
3802	
3803	        if cte:
3804	            this = self._parse_statement()
3805	
3806	            if not this:
3807	                self.raise_error("Failed to parse any statement following CTE")
3808	                return cte
3809	
3810	            while isinstance(this, exp.Subquery) and this.is_wrapper:
3811	                this = this.this
3812	
3813	            assert this is not None
3814	            if "with_" in this.arg_types:
3815	                this.set("with_", cte)
3816	            else:
3817	                self.raise_error(f"{this.key} does not support CTE")
3818	                this = cte
3819	
3820	            return this
3821	
3822	        # duckdb supports leading with FROM x
3823	        from_ = (
3824	            self._parse_from(joins=True, consume_pipe=True)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py", "old_string": "            if \"with_\" in this.arg_types:\n                this.set(\"with_\", cte)\n            else:\n                self.raise_error(f\"{this.key} does not support CTE\")\n                this = cte\n\n           
…[207 chars elided]…
by pipe syntax\n                if existing := this.args.get(\"with_\"):\n                    cte.set(\"expressions\", [*cte.expressions, *existing.expressions])\n                this.set(\"with_\", cte)\n            else:\n                self.raise_error(f\"{this.key} does not support CTE\")\n                this = cte\n\n            return this\n\n        # duckdb supports leading with FROM x"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "printf 'WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2\\nWITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\\nWITH RECURSIVE x AS (SELECT 1 AS x1) FROM x |> SELECT x1\\n' | PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read bigquery; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2', read='bigquery', write='bigquery', pretty=True)[0])\"", "description": "Re-run probes and show pretty output"}
[tool_result] OK        WITH x AS (SELECT 1 AS x1) FROM x |> SELECT x1, 2 AS x2
          WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
OK        WITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1
          WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x WHERE x1 > 0) SELECT * FROM __tmp1
OK        WITH RECURSIVE x AS (SELECT 1 AS x1) FROM x |> SELECT x1
          WITH RECURSIVE x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x) SELECT * FROM __tmp1
WITH x AS (
  SELECT
    1 AS x1
), __tmp1 AS (
  SELECT
    x1,
    2 AS x2
  FROM x
)
SELECT
  *
FROM __tmp1
[assistant] Output now matches the expected form. Next I'll add a regression test next to the existing pipe-syntax tests.
[tool_use Bash] {"command": "grep -n \"WITH\\|def test\" tests/dialects/test_pipe_syntax.py | head -60; wc -l tests/dialects/test_pipe_syntax.py", "description": "Survey existing pipe syntax tests"}
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
…[2221 chars elided]…
_tmp1 ORDER BY...
tests/dialects/test_pipe_syntax.py:98:"WITH __tmp1 AS (SELECT x1, x2, x3 FROM x) SELECT * FROM __tmp1 ORDER BY x1 D...
tests/dialects/test_pipe_syntax.py:108:f"WITH __tmp1 AS (SELECT x1, x2 FROM x {option}) SELECT * FROM __tmp1 WHERE x...
tests/dialects/test_pipe_syntax.py:112:f"WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1 WHERE x1 > 0 AND...
tests/dialects/test_pipe_syntax.py:116:"WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1 LIMIT 2",
[+30 more]
465
[tool_use Bash] {"command": "sed -n 1,8p tests/dialects/test_pipe_syntax.py; sed -n 56,70p tests/dialects/test_pipe_syntax.py; sed -n 440,465p tests/dialects/test_pipe_syntax.py", "description": "Read test structure of pipe syntax tests"}
[tool_result] from tests.dialects.test_dialect import Validator


class TestPipeSyntax(Validator):
    def test_select(self):
        self.validate_identity("FROM x", "SELECT * FROM x")
        self.validate_identity(
            "FROM x |> SELECT x1, x2", "WITH __tmp1 AS (SELECT x1, x2 FROM x) SELECT * FROM __tmp1"
            "WITH __tmp2 AS (SELECT x FROM (SELECT * FROM (WITH __tmp1 AS (SELECT SUM(x1) AS xx, x, x1 FROM (SELECT 1 AS x, 2 AS x1) GROUP BY x, x1) SELECT * FROM __tmp1))) SELECT * FROM __tmp2",

…[2063 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py", "old_string": "    def test_tablesample(self):\n        self.validate_identity(", "new_string": "    def test_leading_with(self):\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> SE
…[39 chars elided]…
 x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1\",\n        )\n        self.validate_identity(\n            \"WITH x AS (SELECT 1 AS x1) FROM x |> WHERE x1 > 0 |> SELECT x1\",\n            \"WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1 FROM x WHERE x1 > 0) SELECT * FROM __tmp1\",\n        )\n\n    def test_tablesample(self):\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154447-bigquery-pipe-syntax-when-a-pipe/base-1/tests/dialects/test_pipe_syntax.py has been updated successfully.
[assistant] Now the targeted test file, then the full suite as the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_pipe_syntax.py tests/dialects/test_bigquery.py 2>&1 | tail -15", "description": "Run pipe syntax and BigQuery dialect tests"}
[tool_result] ......................................................................                          [100%]
70 passed, 1129 subtests passed in 0.46s
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 590000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 590000}
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
1109 passed, 18038 subtests passed in 48.27s
[assistant] The full suite passes. I'll run the linter on the two changed files as well.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_pipe_syntax.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_pipe_syntax.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_pipe_syntax.py
[assistant] Fixed. A BigQuery pipe query with leading CTEs now keeps both the leading CTEs and the pipe's generated `__tmp` CTEs:

```sql
WITH x AS (SELECT 1 AS x1), __tmp1 AS (SELECT x1, 2 AS x2 FROM x) SELECT * FROM __tmp1
```

**Cause:** In `_parse_select_query` (`sqlglot/parser.py`), the leading `WITH` is parsed after the pipe chain has already been built. The code then did `this.set("with_", cte)`, which overwrote the `WITH` node that held the `__tmp` CTEs.

**Change:** When the statement already has a `with_`, the leading CTEs are now prepended to its list instead of replacing it. The leading `WITH` node is kept, so `RECURSIVE` still applies.

**Tests:** I added `test_leading_with` to `tests/dialects/test_pipe_syntax.py` with the example from your report and a `WHERE` variant. `test_pipe_syntax.py` and `test_bigquery.py` pass (70 tests). The full suite passes (1109 tests). `ruff check` and `ruff format --check` are clean on both files.

I did not commit anything.
