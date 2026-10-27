# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** `_parse_table` in `sqlglot/parser.py` returns early when the table is a subquery, so the `joins=True` handling at the end of the function never ran. The FROM-first path calls it with `joins=True`, which left the `positional join` unconsumed and broke the trailing `select`. Plain tables went through the non-early path, which is why they worked.

**Fix:** in the subquery branch of `_parse_table`, when `joins` is set, parse the joins and attach them to the subquery. `Subquery` already accepts `joins` and the generator already prints them, so no node or generator change was needed.

**Test:** I added a `validate_identity` case next to the existing FROM-first tests in `tests/dialects/test_duckdb.py`.

**Verification:** `tests/dialects/test_duckdb.py` passes (44 tests), and the full suite passes (1104 tests). I ran both with the system `python3`, because the project's pinned venv path from the repo notes doesn't exist in this environment. I did not run `make check` (ruff/mypy), and I did not commit.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nprint(sqlglot.__file__)\ntry:\n    print(repr(sqlglot.parse_one('''from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2''', read='duckdb')))\nexcept Exception as e: print('ERR', e)\n\"", "description": "Reproduce the FROM-first parse failure"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The skill is loaded. The project's env python path doesn't exist here, so I'll run the repo's own sqlglot directly.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/ 2>&1 | head -3; python3 -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nprint(sqlglot.__file__)\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2', 'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2', 'select t1.x as x1, t2.x as x2 from (select * from tbl_1) t1 positional join (select * from tbl_2) t2']:\n    try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Reproduce the FROM-first parse failure"}
[tool_result] activate
activate.bat
activate.csh
~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/sqlglot/__init__.py
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2
SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
[assistant] Reproduced: the failure is at the `select` after `(FROM tbl_2) t2`. Next I'll look at how the parser handles a bare `FROM` subquery and where the join is consumed.
[tool_use Bash] {"command": "grep -n \"FROM\" sqlglot/parsers/duckdb.py | head -30; echo ---; grep -n \"def _parse_select\\b\\|def _parse_query_modifiers\\|def _parse_table_alias\\|def _parse_subquery\\|def _parse_derived_table\\|from_first\\|FROM-first\\|def _parse_from\\b\" sqlglot/parser.py | head -30; echo ---; grep -rn \"POSITIONAL\" sqlglot/parser.py sqlglot/parsers/duckdb.py sqlglot/tokens.py | head", "description": "Locate FROM-first and subquery parsing code"}
[tool_result] 283:        # DuckDB supports prefix aliases, e.g. FROM foo: bar
368:        from_ = self._parse_table(schema=True) if self._match(TokenType.FROM) else None
383:                from_=self._parse_var_or_string() if self._match(TokenType.FROM) else None,
---
3728:            # Support parentheses for duckdb FROM-first syntax
3754:    def _parse_select(
3996:    def _parse_table_alias(
4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4168:    def _parse_from(
4928:    def _parse_derived_table_values(self) -> exp.Values | None:
---
sqlglot/parser.py:946:        TokenType.POSITIONAL,
[tool_use Bash] {"command": "sed -n 3715,3760p sqlglot/parser.py; echo ----; sed -n 3996,4070p sqlglot/parser.py; echo ----; sed -n 4168,4190p sqlglot/parser.py", "description": "Read FROM-first and subquery parsing sections"}
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
…[4653 chars elided]…
nts = self._prev_comments
        return self.expression(
            exp.From(this=self._parse_table(joins=joins, consume_pipe=consume_pipe)),
            comments=comments,
        )

    def _parse_match_recognize_measure(self) -> exp.MatchRecognizeMeasure:
        return self.expression(
            exp.MatchRecognizeMeasure(
                window_frame=self._match_texts(("FINAL", "RUNNING")) and self._prev.text.upper(),
                this=self._parse_expression(),
            )
        )
[tool_use Bash] {"command": "sed -n 3760,3800p sqlglot/parser.py; echo ----; grep -n \"from_=\\|from_ is not None\\|from_:\" sqlglot/parser.py | head -30; echo ----; grep -n \"def _parse_table\\b\" -A40 sqlglot/parser.py | grep -n \"L_PAREN\\|subquery\\|wrapped\\|FROM\" ", "description": "Read rest of _parse_select and table parsing hooks"}
[tool_result]         consume_pipe: bool = True,
        from_: exp.From | None = None,
    ) -> exp.Expr | None:
        query = self._parse_select_query(
            nested=nested,
            table=table,
            parse_subquery_alias=parse_subquery_alias,
            parse_set_operation=parse_set_operation,
        )

        if consume_pipe and self._match(TokenType.PIPE_GT, advance=False):
            if not query and from_:
                query = exp.select("*").from_(from_)
            if isinstan
…[747 chars elided]…
rt this is not None
            if "with_" in this.arg_types:
                this.set("with_", cte)
----
3729:            select = self._parse_select(from_=from_)
3761:        from_: exp.From | None = None,
3771:            if not query and from_:
3868:            if not from_:
3871:            if from_:
3888:        elif from_:
5409:                    from_=self._match(TokenType.FROM) and self._parse_bitwise(),
9576:                from_=_parse_overlay_arg("FROM"),
9752:        if from_:
----
[tool_use Bash] {"command": "sed -n 3840,3900p sqlglot/parser.py; echo ----; grep -n \"_parse_table(\" sqlglot/parser.py | head -5; grep -n \"    def _parse_table(\" -A60 sqlglot/parser.py | head -80", "description": "Read select-from handling and _parse_table"}
[tool_result]             if all_ and distinct:
                self.raise_error("Cannot specify both ALL and DISTINCT after SELECT")

            operation_modifiers = []
            while self._curr and self._match_texts(self.OPERATION_MODIFIERS):
                operation_modifiers.append(exp.var(self._prev.text.upper()))

            limit = self._parse_limit(top=True)
            projections, exclude = self._parse_projections()

            this = self.expression(
                exp.Select(
            
…[4382 chars elided]…
True, consume_pipe=consume_pipe):
4749-            if not subquery.args.get("pivots"):
4750-                subquery.set("pivots", self._parse_pivots())
4751-            return subquery
4752-
4753-        bracket = parse_bracket and self._parse_bracket(None)
4754-        bracket = self.expression(exp.Table(this=bracket)) if bracket else None
4755-
4756-        rows_from_tables = (
4757-            self._parse_wrapped_csv(self._parse_table)
4758-            if self._match_text_seq("ROWS", "FROM")
[tool_use Bash] {"command": "sed -n 3800,3840p sqlglot/parser.py; echo ----; grep -n \"TABLE_TERMINATORS\\|TABLE_POSTFIX_TOKENS\" sqlglot/parser.py | head -4; grep -n \"def _parse_query_modifiers\" -A30 sqlglot/parser.py | sed -n 1,40p", "description": "Read select-branch start and query modifier parsing"}
[tool_result]                 this.set("with_", cte)
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

            hint = s
…[2294 chars elided]…
 == "limit":
4099-                            offset = expression.args.get("offset")
4100-                            expression.set("offset", None)
4101-
4102-                            if offset:
4103-                                offset = exp.Offset(expression=offset)
4104-                                this.set("offset", offset)
4105-
4106-                                limit_by_expressions = expression.expressions
4107-                                expression.set("expressions", None)
[assistant] The top-level FROM is parsed with `joins=True`, so the join's subquery goes through `_parse_wrapped_select`'s FROM branch. I'll isolate which combination breaks.
[tool_use Bash] {"command": "python3 -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nqs = [\n 'from (FROM tbl_1) t1 select t1.x',\n 'from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x = t2.x select t1.x',\n 'from tbl_1 t1 join (FROM tbl_2) t2 on t1.x = t2.x select t1.x',\n 'from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x',\n 'from (select * from tbl_1) t1 positional join (FROM tbl_2) t2 selec
…[240 chars elided]…
nal join (FROM tbl_2) t2 select *',\n 'select t1.x from (FROM tbl_1) t1 positional join (FROM tbl_2) t2',\n 'from (FROM tbl_1) t1 cross join (FROM tbl_2) t2 select t1.x',\n]\nfor q in qs:\n    try: print('OK ', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0])\n\"", "description": "Isolate which FROM-first join forms fail"}
[tool_result] OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
ERR from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x = t2.x select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 63.
OK  SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x
OK  SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
ERR from (select * from tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 68.
ERR from (FROM tbl_1) t1
…[164 chars elided]…
elect t1.x -> Invalid expression / Unexpected token. Line 1, Col: 68.
OK  SELECT * FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select * -> Invalid expression / Unexpected token. Line 1, Col: 59.
OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
ERR from (FROM tbl_1) t1 cross join (FROM tbl_2) t2 select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 54.
[assistant] Pattern so far: failures only occur when the first FROM item is a subquery *and* a join follows. Let me check whether `_parse_table` skips joins on its subquery return path.
[tool_use Bash] {"command": "sed -n 4758,4800p sqlglot/parser.py", "description": "Read the rest of _parse_table to check join handling"}
[tool_result]             if self._match_text_seq("ROWS", "FROM")
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

  
…[435 chars elided]…
return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())

        if self.dialect.ALIAS_POST_TABLESAMPLE:
            this.set("sample", self._parse_table_sample())

        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
        if alias:
            this.set("alias", alias)

        if self._match(TokenType.INDEXED_BY):
            this.set("indexed", self._parse_table_parts())
[tool_use Bash] {"command": "sed -n 4800,4830p sqlglot/parser.py; echo ----; grep -n \"def _parse_joins\" -A12 sqlglot/parser.py; echo; git log --oneline -3 -- sqlglot/parser.py", "description": "Read tail of _parse_table and _parse_joins"}
[tool_result]             this.set("indexed", self._parse_table_parts())
        elif self._match_text_seq("NOT", "INDEXED"):
            this.set("indexed", False)

        if isinstance(this, exp.Table) and self._match_text_seq("AT"):
            return self.expression(
                exp.AtIndex(this=this.to_column(copy=False), expression=self._parse_id_var())
            )

        this.set("hints", self._parse_table_hints())

        if not this.args.get("pivots"):
            this.set("pivots", self._p
…[835 chars elided]…
turn None
5023-
5024-        return self.expression(
5025-            exp.UnpivotColumns(
5026-                this=self._match_text_seq("NAME") and self._parse_column(),
5027-                expressions=self._match_text_seq("VALUE") and self._parse_csv(self._parse_column),
5028-            )
5029-        )

717a50d81 Support FORMAT JSON for JSON_TABLE in Oracle (#7578)
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
[assistant] Found the cause. In `_parse_table`, the subquery branch returns early (`return subquery`), so the `if joins:` block at the end never runs for `(subquery) alias`. The FROM-first path calls `_parse_table(joins=True)`, so the join is left unconsumed. Before choosing a fix, I need to know whether `Subquery` can hold `joins` and how the generator prints them.
[tool_use Bash] {"command": "grep -rn \"class Subquery\\|class DerivedTable\\|class Query(\" -A12 sqlglot/expressions/query.py | grep -n \"class\\|arg_types\\|joins\" ; echo ----; grep -n \"def subquery_sql\" -A25 sqlglot/generator.py; echo ----; grep -n \"def table_sql\" -A30 sqlglot/generator.py | grep -n \"joins\"", "description": "Check Subquery arg_types and generator join handling"}
[tool_result] 1:sqlglot/expressions/query.py:96:class DerivedTable(Selectable):
9:sqlglot/expressions/query.py-104-class UDTF(DerivedTable):
15:sqlglot/expressions/query.py:112:class Query(Selectable):
29:sqlglot/expressions/query.py:1662:class Subquery(Expression, DerivedTable, Query):
31:sqlglot/expressions/query.py-1664-    arg_types = {
----
3182:    def subquery_sql(self, expression: exp.Subquery, sep: str = " AS ") -> str:
3183-        alias = self.sql(expression, "alias")
3184-        alias = f"{sep}{a
…[740 chars elided]…
sep()}{this}"
3199-
3200-    def unnest_sql(self, expression: exp.Unnest) -> str:
3201-        args = self.expressions(expression, flat=True)
3202-
3203-        alias = expression.args.get("alias")
3204-        offset = expression.args.get("offset")
3205-
3206-        if self.UNNEST_WITH_ORDINALITY:
3207-            if alias and isinstance(offset, exp.Expr):
----
28:2316-        joins = self.indent(
29:2317-            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
[tool_use Bash] {"command": "sed -n 1662,1672p sqlglot/expressions/query.py; grep -n \"def query_modifiers\" -A12 sqlglot/generator.py | head -20", "description": "Check Subquery arg_types and query_modifiers"}
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
3013:    def query_modifiers(self, expression: exp.Expr, *sqls: str) -> str:
3014-        limit = expression.args.get("limit")
3015-
3016-        if self.LIMIT_FETCH == "LIMIT" and isinstance(limit, exp.Fetch):
3
…[37 chars elided]…
ression=exp.maybe_copy(limit.args.get("count")))
3018-        elif self.LIMIT_FETCH == "FETCH" and isinstance(limit, exp.Limit):
3019-            limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))
3020-
3021-        return csv(
3022-            *sqls,
3023-            *[self.sql(join) for join in expression.args.get("joins") or []],
3024-            self.sql(expression, "match"),
3025-            *[self.sql(lateral) for lateral in expression.args.get("laterals") or []],
[assistant] `Subquery` accepts `joins` through `QUERY_MODIFIERS` and the generator already prints them, so the fix is local to the subquery branch of `_parse_table`. I'll apply it so the subquery path honours `joins=True` the same way the table path does.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nqs = [\n 'from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n 'from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x = t2.x select t1.x',\n 'from (select * from tbl_1) t1 positional join tbl_2 t2 select t1.x',\n 'from (FROM tbl_1) t1 positional join (FROM tbl_2) t2',\n 'from (FROM tbl_1) t1 select t1.x',\n]\nfor q in qs:\n    try: print('OK ', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0])\n\"", "description": "Verify the fix on the failing and related forms"}
[tool_result] OK  SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x
OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN tbl_2 AS t2
OK  SELECT * FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
[assistant] The reported query now parses and produces the same SQL as the `SELECT`-first form. Next I'll add a regression test next to the existing FROM-first tests in the DuckDB suite.
[tool_use Bash] {"command": "grep -n -i \"from-first\\|from first\\|FROM tbl\\|POSITIONAL JOIN\\|positional\" tests/dialects/test_duckdb.py | head -30", "description": "Find existing FROM-first and positional join tests"}
[tool_result] 426:            "SELECT tbl.x*1e4+tbl.y FROM tbl",
427:            "SELECT tbl.x * 1e4 + tbl.y FROM tbl",
469:        self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
496:        self.validate_identity("SUMMARIZE SELECT * FROM tbl").assert_is(exp.Summarize)
1950:            "SELECT * FROM tbl USING SAMPLE 5",
1951
…[908 chars elided]…
E tbl.i=tbl2.i USING SAMPLE RESERVOIR(20%)",
1975:            "SELECT * FROM tbl, tbl2 WHERE tbl.i = tbl2.i USING SAMPLE RESERVOIR (20 PERCENT)",
2558:            "WITH RECURSIVE tbl(a, b) USING KEY (a) AS (SELECT a, b FROM (VALUES (1, 3), (2, 4)) AS t(a, b) UNION SELECT a + 1, b FROM tbl WHERE a < 3) SELECT * FROM tbl"
2561:            "WITH RECURSIVE tbl(a, b) USING KEY (a, b) AS (SELECT a, b FROM (VALUES (1, 3), (2, 4)) AS t(a, b) UNION SELECT a + 1, b FROM tbl WHERE a < 3) SELECT * FROM tbl"
[tool_use Bash] {"command": "sed -n 466,492p tests/dialects/test_duckdb.py", "description": "Read the test block near the FROM-first tests"}
[tool_result]         self.validate_identity("SELECT MAP(['key1', 'key2', 'key3'], [10, 20, 30])")
        self.validate_identity("SELECT MAP {'x': 1}")
        self.validate_identity("SELECT (MAP {'x': 1})['x']")
        self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
        self.validate_identity("MAKE_TIMESTAMP(1992, 9, 20, 13, 34, 27.123456)")
        self.validate_identity("MAKE_TIMESTAMP(1667810584123456)")
        self.validate_identity("SELECT EPOCH_MS(10) AS t")
        se
…[885 chars elided]…
 self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
        self.validate_identity(
            "SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)",
            "SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)",
        )
        self.validate_identity("x -> '$.family'")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM (FROM tbl)\", \"SELECT * FROM (SELECT * FROM tbl)\")\n        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")", "new_string": "        self.validate_identity
…[1 chars elided]…
\"FROM (FROM tbl)\", \"SELECT * FROM (SELECT * FROM tbl)\")\n        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(\n            \"FROM (FROM tbl_1) t1 POSITIONAL JOIN (FROM tbl_2) t2 SELECT t1.x AS x1, t2.x AS x2\",\n            \"SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-201302-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll run the DuckDB tests and then the full suite. The project's pinned venv isn't present here, so I'll use the system Python.
[tool_use Bash] {"command": "python3 -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run DuckDB dialect tests"}
[tool_result] ........................ [ 54%]
....................       [100%]
44 passed, 598 subtests passed in 0.38s
[tool_use Bash] {"command": "python3 -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15; git stash list | head -0; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 54%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
....................................... [ 65%]
......................................... [ 69%]
.... [ 69%]
.........
…[30 chars elided]…
........... [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 60.28s (0:01:00)
head: illegal line count -- 0
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
[assistant] FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** `_parse_table` in `sqlglot/parser.py` returns early when the table is a subquery, so the `joins=True` handling at the end of the function never ran. The FROM-first path calls it with `joins=True`, which left the `positional join` unconsumed and broke the trailing `select`. Plain tables went through the non-early path, which is why they worked.

**Fix:** in the subquery branch of `_parse_table`, when 
…[5 chars elided]…
s` is set, parse the joins and attach them to the subquery. `Subquery` already accepts `joins` and the generator already prints them, so no node or generator change was needed.

**Test:** I added a `validate_identity` case next to the existing FROM-first tests in `tests/dialects/test_duckdb.py`.

**Verification:** `tests/dialects/test_duckdb.py` passes (44 tests), and the full suite passes (1104 tests). I ran both with the system `python3`, because the project's pinned venv path from the repo notes doesn't exist in this environment. I did not run `make check` (ruff/mypy), and I did not commit.
