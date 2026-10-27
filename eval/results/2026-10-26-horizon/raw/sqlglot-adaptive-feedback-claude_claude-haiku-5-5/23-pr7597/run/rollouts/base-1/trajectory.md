# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. The full suite passed after my last edit: `SUMMARY: 1104 passed, 17947 subtests passed in 70.32s`, `EXIT: 0`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the parenthesised-subquery branch returned before the `if joins:` block. A leading `FROM` calls `_parse_table(joins=True)`, so a join after a parenthesised source was never consumed and the trailing `select` failed. This also broke `from (select 1 x) t1 join tbl_2 ...`, so it isn't specific to `FROM`-first.

**Fix:** When `joins` is set, the subquery branch now attaches the following joins to the `Subquery` node. `Subquery` already has a `joins` arg and its generator emits it.

**Probes that now parse:** `positional join` and `join` with subqueries on either or both sides, `left join`, chained joins, comma joins, a join with no alias, `WHERE`/`LIMIT` after the `SELECT`, `SELECT`-first, and the `UPDATE ... FROM` and `DELETE ... USING` paths, which also use `joins=True`.

**Tests:** I added three cases to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests. They cover the positional-join example from the report, a subquery with an inner join, and an AST assertion that the join sits on the `Subquery`. No existing test was changed.

**Not done:** I did not run `ast_check.py`, and I did not check transpile output to other dialects. This is a parser-structure fix, not a function mapping, so there was no target-function type equivalence to check.

## events
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-214401-duckdb-dialect-from-first-querie/base-1/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

If the failing syntax is SQL/JSON (JSON_TABLE, FORMAT JSON, JSON_OBJECT RETURNING), also load
the `sqlglot-json-table` skill: that syntax is parsed in the base `sqlglot/parser.py`, not in
the dialect's parser.

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the fu
…[9842 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; ls .lithify/harness/ 2>/dev/null; grep -n -i \"from\\b\" sqlglot/parsers/duckdb.py | head -50; grep -rn \"POSITIONAL\\|positional\" sqlglot/parser.py sqlglot/parsers/duckdb.py | head -30", "description": "Check harness memory and find FROM/positional handling"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[508 chars elided]…
dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
283:        # DuckDB supports prefix aliases, e.g. FROM foo: bar
368:        from_ = self._parse_table(schema=True) if self._match(TokenType.FROM) else None
383:                from_=self._parse_var_or_string() if self._match(TokenType.FROM) else None,
sqlglot/parser.py:946:        TokenType.POSITIONAL,
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && $PY -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2',\n          'fro
…[45 chars elided]…
) t2 select t1.x as x1, t2.x as x2',\n          'from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x',\n          'from (FROM tbl_1) t1 select t1.x']:\n    try:\n        print('OK', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e:\n        print('ERR', q, '->', str(e).splitlines()[0])\n\"", "description": "Reproduce FROM-first parse failures in duckdb"}
[tool_result] <work>/env-sqlglot/bin/python
ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 -> Invalid expression / Unexpected token. Line 1, Col: 59.
OK SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2
ERR from (select 1 x) t1 positional join (select 2 x) t2 select t1.x as x1, t2.x as x2 -> Invalid expression / Unexpected token. Line 1, Col: 59.
ERR from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 61.
OK SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
[assistant] The failure is at column 59, the `select` that follows the joined subquery, and it also happens with a plain `(select ...)` subquery. So the bug is in how the FROM-first path ends a join. Let me look at that code.
[tool_use Bash] {"command": "grep -n \"_parse_from\\|FROM\\b\" sqlglot/parsers/duckdb.py | head; sed -n 355,400p sqlglot/parsers/duckdb.py; grep -n \"def _parse_query_modifiers\\|def _parse_join\\b\\|def _parse_join(\\|QUERY_MODIFIER_PARSERS\\|_parse_from(\" sqlglot/parser.py | head -20", "description": "Read DuckDB FROM-first parsing code"}
[tool_result] 283:        # DuckDB supports prefix aliases, e.g. FROM foo: bar
368:        from_ = self._parse_table(schema=True) if self._match(TokenType.FROM) else None
383:                from_=self._parse_var_or_string() if self._match(TokenType.FROM) else None,

        if self._match(TokenType.L_PAREN, advance=False):
            expressions = self._parse_wrapped_csv(_parse_attach_option)
        else:
            expressions = None

        return (
            self.expression(exp.Attach(this=this, exi
…[1564 chars elided]…
  self._parse_from(joins=True, consume_pipe=True)
3869:                from_ = self._parse_from()
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4085:                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4087:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
4168:    def _parse_from(
4363:    def _parse_join(
[tool_use Bash] {"command": "sed -n 4077,4110p sqlglot/parser.py; sed -n 4168,4200p sqlglot/parser.py; sed -n 4363,4380p sqlglot/parser.py; grep -n \"POSITIONAL\" sqlglot/parser.py sqlglot/parsers/duckdb.py | head", "description": "Read query modifier and from parsing core"}
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
…[2459 chars elided]…
PRECEDENCE:
                cross_join.set("kind", "CROSS")

            return cross_join

        index = self._index
        method, side, kind = self._parse_join_parts()
        directed = self._match_text_seq("DIRECTED")
        hint = self._prev.text if self._match_texts(self.JOIN_HINTS) else None
        join = self._match(TokenType.JOIN) or (kind and kind.token_type == TokenType.STRAIGHT_JOIN)
        join_comments = self._prev_comments
sqlglot/parser.py:946:        TokenType.POSITIONAL,
[tool_use Bash] {"command": "sed -n 3620,3650p sqlglot/parser.py; echo ----; sed -n 3860,3885p sqlglot/parser.py; echo ----; grep -n \"def _parse_table(\\|def _parse_table_parts\\|def _parse_subquery\" sqlglot/parser.py", "description": "Read FROM-first select parsing branches"}
[tool_result]         )

    def _parse_update(self) -> exp.Update:
        hint = self._parse_hint()
        kwargs: dict[str, object] = {
            "hint": hint,
            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
        }
        while self._curr:
            if self._match(TokenType.SET):
                kwargs["expressions"] = self._parse_csv(self._parse_equality)
            elif self._match(TokenType.RETURNING, advance=False):
                kwargs["returning"]
…[1420 chars elided]…
   this.add_comments(comments, prepend=True)

            # We return early here so that the UNION isn't attached to the subquery by the
            # following call to _parse_set_operations, but instead becomes the parent node
            self._match_r_paren()
            return self._parse_subquery(this, parse_alias=parse_subquery_alias)
----
4029:    def _parse_subquery(
4564:    def _parse_table_parts_fast(self) -> exp.Table | None:
4627:    def _parse_table_parts(
4698:    def _parse_table(
[tool_use Bash] {"command": "grep -n \"TokenType.FROM\" sqlglot/parser.py | head -40; grep -n \"FROM\" sqlglot/parsers/duckdb.py | head", "description": "Find FROM-first handling in base parser"}
[tool_result] 611:        TokenType.FROM,
2458:            referenced_table = self._parse_table_parts() if self._match(TokenType.FROM) else None
3192:        elif self._match(TokenType.FROM):
3602:        if not self._match(TokenType.FROM, advance=False):
3611:                this=self._match(TokenType.FROM) and self._parse_table(joins=True),
3633:            elif self._match(TokenType.FROM, advance=False):
3726:        elif self._match(TokenType.FROM):
3810:            if self._match(TokenType.FROM, advance=
…[400 chars elided]…
86:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8780:            if self._match_set((TokenType.FROM, TokenType.IN)):
9408:        kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
283:        # DuckDB supports prefix aliases, e.g. FROM foo: bar
368:        from_ = self._parse_table(schema=True) if self._match(TokenType.FROM) else None
383:                from_=self._parse_var_or_string() if self._match(TokenType.FROM) else None,
[tool_use Bash] {"command": "sed -n 3600,3619p sqlglot/parser.py", "description": "Read leading-FROM query parse function"}
[tool_result]         # https://dev.mysql.com/doc/refman/8.0/en/delete.html
        tables = None
        if not self._match(TokenType.FROM, advance=False):
            tables = self._parse_csv(self._parse_table) or None

        returning = self._parse_returning()

        return self.expression(
            exp.Delete(
                hint=hint,
                tables=tables,
                this=self._match(TokenType.FROM) and self._parse_table(joins=True),
                using=self._match(TokenType.USING)
                and self._parse_csv(lambda: self._parse_table(joins=True)),
                cluster=self._match(TokenType.ON) and self._parse_on_property(),
                where=self._parse_where(),
                returning=returning or self._parse_returning(),
                order=self._parse_order(),
                limit=self._parse_limit(),
            )
[tool_use Bash] {"command": "sed -n 3715,3745p sqlglot/parser.py; echo ----; sed -n 3800,3830p sqlglot/parser.py", "description": "Read FROM-first select branch in parser"}
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
…[1336 chars elided]…

            hint = self._parse_hint()

            if self._next and not self._next.token_type == TokenType.DOT:
                all_ = self._match(TokenType.ALL)
                matched_distinct = self._match_set(self.DISTINCT_TOKENS)
            else:
                all_, matched_distinct = None, False

            kind = (
                self._prev.text.upper()
                if self._match(TokenType.ALIAS) and self._match_texts(("STRUCT", "VALUE"))
                else None
            )
[assistant] Leading-FROM goes through `_parse_from(joins=True)` → `_parse_table(joins=True)`. Let me narrow which side of the join triggers it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nqs = [\n 'from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x',\n 'from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x',\n 'from (FROM tbl_1) t1 join tbl_2 t2 on t1.x=t2.x select t1.x',\n 'fro
…[426 chars elided]…
2 on t1.x=t2.x select t1.x',\n 'from tbl_1 t1 join (select 1 x) t2 on t1.x=t2.x select *',\n 'select t1.x from tbl_1 t1 join (select 1 x) t2 on t1.x=t2.x',\n]\nfor q in qs:\n    try: print('OK ', q, '=>', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0])\n\"", "description": "Probe join/subquery combinations in FROM-first"}
[tool_result] ERR from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 52.
OK  from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x => SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
ERR from (FROM tbl_1) t1 join tbl_2 t2 on t1.x=t2.x select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 54.
OK  from tbl_1 t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x => SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT * FROM tb
…[638 chars elided]…
= 1 => SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT 1 AS x) AS t2 ON t1.x = t2.x WHERE t1.x = 1
OK  from tbl_1 t1 join (select 1 x) t2 on t1.x=t2.x select t1.x => SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT 1 AS x) AS t2 ON t1.x = t2.x
OK  from tbl_1 t1 join (select 1 x) t2 on t1.x=t2.x select * => SELECT * FROM tbl_1 AS t1 JOIN (SELECT 1 AS x) AS t2 ON t1.x = t2.x
OK  select t1.x from tbl_1 t1 join (select 1 x) t2 on t1.x=t2.x => SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT 1 AS x) AS t2 ON t1.x = t2.x
[assistant] The bug is narrower than I thought: it's any leading parenthesised subquery in FROM-first form followed by a join, including `from (select 1 x) t1 join tbl_2`. The `from tbl_1 ... join (subquery)` form works. Next I'll read `_parse_table`.
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
[tool_use Bash] {"command": "sed -n 4790,4830p sqlglot/parser.py; echo ----; sed -n 4029,4070p sqlglot/parser.py", "description": "Read rest of _parse_table and _parse_subquery"}
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
…[2207 chars elided]…
a parent Alias node that we want to convert to
                    # a TableAlias and attach to the Unnest, so it matches the parser's output
                    if isinstance(table.args.get("alias"), exp.TableAlias):
                        table_as_column.replace(table_as_column.this)
                        exp.alias_(unnest, None, table=[table.args["alias"].this], copy=False)

                    table.replace(unnest)

            refs.add(normalized_table.alias_or_name)

        return this
[assistant] Found it. In `_parse_table`, the subquery branch does `return subquery` before the `if joins:` block at the end, so a `joins=True` caller (the leading FROM) never picks up the join that follows a parenthesised source. Before I change it, I'll check that `Subquery` accepts a `joins` arg and how its generator emits one.
[tool_use Bash] {"command": "grep -n \"class Subquery\" -A 25 sqlglot/expressions/query.py | grep -n \"arg_types\\|joins\" ; grep -rn \"def subquery_sql\" -A 15 sqlglot/generator.py | head -30; grep -rn \"joins\" sqlglot/generator.py | grep -i subquer | head", "description": "Check Subquery joins arg and generator support"}
[tool_result] 3:1664-    arg_types = {
sqlglot/generator.py:3182:    def subquery_sql(self, expression: exp.Subquery, sep: str = " AS ") -> str:
sqlglot/generator.py-3183-        alias = self.sql(expression, "alias")
sqlglot/generator.py-3184-        alias = f"{sep}{alias}" if alias else ""
sqlglot/generator.py-3185-        sample = self.sql(expression, "sample")
sqlglot/generator.py-3186-        if self.dialect.ALIAS_POST_TABLESAMPLE and sample:
sqlglot/generator.py-3187-            alias = f"{sample}{alias}
…[217 chars elided]…
ator.py-3191-
sqlglot/generator.py-3192-        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
sqlglot/generator.py-3193-        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
sqlglot/generator.py-3194-        return self.prepend_ctes(expression, sql)
sqlglot/generator.py-3195-
sqlglot/generator.py-3196-    def qualify_sql(self, expression: exp.Qualify) -> str:
sqlglot/generator.py-3197-        this = self.indent(self.sql(expression, "this"))
[assistant] `Subquery` has a `joins` arg and its generator emits joins through `query_modifiers`, so attaching joins to the subquery node is the right shape. The change is in `_parse_table`, the subquery branch:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-214401-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-214401-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll re-run the reproduction, plus the other positions the task implies: different join kinds, multiple joins, an alias-less subquery, the `SELECT`-first form, and the same-shape `UPDATE ... FROM` path that also passes `joins=True`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nqs = [\n 'from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n 'from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x',\n 'from (FROM tbl_1) t1 join tbl_2 t2 on t1.x=
…[705 chars elided]…
ROM tbl_1) t1 join tbl_2 t2 on t1.x=t2.x where tbl_0.x=t1.x',\n 'delete from tbl_0 using (select 1 x) t1 join tbl_2 t2 on t1.x=t2.x where tbl_0.x=t1.x',\n]\nfor q in qs:\n    try: print('OK ', q, '\\n   =>', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0])\n\"", "description": "Re-run FROM-first join probes after the fix"}
[tool_result] OK  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 
   => SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK  from (FROM tbl_1) t1 positional join tbl_2 t2 select t1.x 
   => SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN tbl_2 AS t2
OK  from (FROM tbl_1) t1 join tbl_2 t2 on t1.x=t2.x select t1.x 
   => SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON t1.x = t2.x
OK  from 
…[1368 chars elided]…
 t1.x=t2.x 
   => SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON t1.x = t2.x
OK  update tbl_0 set x = 1 from (FROM tbl_1) t1 join tbl_2 t2 on t1.x=t2.x where tbl_0.x=t1.x 
   => UPDATE tbl_0 SET x = 1 FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON t1.x = t2.x WHERE tbl_0.x = t1.x
OK  delete from tbl_0 using (select 1 x) t1 join tbl_2 t2 on t1.x=t2.x where tbl_0.x=t1.x 
   => DELETE FROM tbl_0 USING (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON t1.x = t2.x WHERE tbl_0.x = t1.x
[assistant] Every probe parses now, and the output shape is right. The joins hang off the `Subquery` node, which is where a `FROM (subquery) JOIN ...` belongs. Next I'll find the existing FROM-first tests so I can add a regression test beside them.
[tool_use Bash] {"command": "grep -n -i \"positional\\|FROM-first\\|from tbl\\|\\\"from \\|'from \" tests/dialects/test_duckdb.py | head -30", "description": "Find existing DuckDB FROM-first tests"}
[tool_result] 426:            "SELECT tbl.x*1e4+tbl.y FROM tbl",
427:            "SELECT tbl.x * 1e4 + tbl.y FROM tbl",
469:        self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
485:        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
496:        self.validate_identity("SUMMARIZ
…[1371 chars elided]…
         "SELECT * FROM tbl, tbl2 WHERE tbl.i = tbl2.i USING SAMPLE RESERVOIR (20 PERCENT)",
2357:            "FROM (FROM t1 SELECT foo1, foo2)",
2558:            "WITH RECURSIVE tbl(a, b) USING KEY (a) AS (SELECT a, b FROM (VALUES (1, 3), (2, 4)) AS t(a, b) UNION SELECT a + 1, b FROM tbl WHERE a < 3) SELECT * FROM tbl"
2561:            "WITH RECURSIVE tbl(a, b) USING KEY (a, b) AS (SELECT a, b FROM (VALUES (1, 3), (2, 4)) AS t(a, b) UNION SELECT a + 1, b FROM tbl WHERE a < 3) SELECT * FROM tbl"
[tool_use Bash] {"command": "sed -n 480,492p tests/dialects/test_duckdb.py", "description": "Read FROM-first test block"}
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
[assistant] I'll add the regression tests beside the existing FROM-first block. They check the round-trip and also assert that the join is attached to the subquery, which is the AST node the fix is supposed to produce.
[user] Your response above was cut off mid-stream. Resume directly from where it stops — no apology, no recap. If none of it survived, answer the request from the start.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-214401-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",", "new_string": "        
…[631 chars elided]…
 \"FROM (FROM tbl_1) t1 JOIN tbl_2 t2 ON t1.x = t2.x SELECT t1.x\",\n                \"SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON t1.x = t2.x\",\n            )\n            .args[\"from_\"]\n            .this.args[\"joins\"][0],\n            exp.Join,\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-214401-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the DuckDB test file, then the full suite once after the last edit.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Run DuckDB dialect test file"}
[tool_result] ........................ [ 54%]
....................       [100%]
44 passed, 598 subtests passed in 0.34s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] Command did not complete within its 600s timeout and was moved to the background (ID: bktwnz5tq). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-214401-duckdb-dialect-from-first-querie-base-1/a6a46cd5-8d74-4d9f-86f3-03ff4df968fb/tasks/bktwnz5tq.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. To check interim output, use Read on that file path.
[assistant] The full suite is still running in the background. I'll read its output file to see where it is.
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-214401-duckdb-dialect-from-first-querie-base-1/a6a46cd5-8d74-4d9f-86f3-03ff4df968fb/tasks/bktwnz5tq.output"}
[tool_result] 1	WARNING: 2 other pytest process(es) running; expect slower runs:
2	  34207 03-02:28:53 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
3	  36233       00:01 <work>/env-sqlglot/b
4	RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
5	LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0eb2d5946e.log
6	
[assistant] The DuckDB dialect file passes (44 tests). The full suite is still running in the background, and the harness will notify me when it finishes. I'll give the final summary once it reports the `SUMMARY`/`EXIT` lines, since I can't mark this done before then.

**Status so far**

- **Cause:** In `sqlglot/parser.py`, `_parse_table` returns early for a parenthesised source (`(FROM t) alias` or `(SELECT ...) alias`) before its `if joins:` block. A leading FROM calls `_parse_table(joins=True)`, so any join after a parenthesised source was left unparsed and the following `select` raised "Invalid expres
…[778 chars elided]…
ner join, and an AST assertion that the join is on the `Subquery` node. I did not change any existing test.
- **Verification so far:** `tests/dialects/test_duckdb.py` passes: 44 passed, 598 subtests.
- **Pending:** the full suite via `run_suite.py` is running in the background (task `bktwnz5tq`). I have not yet seen its `SUMMARY`/`EXIT` lines.
- **Not done:** I did not run `ast_check.py` (the skill's step 4), and the change is a parser-structure fix rather than a function mapping, so there is no new type-equivalence check. I also have not checked the transpile output for other target dialects.
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-55c905b0df68-20261026-214401-duckdb-dialect-from-first-querie-base-1/a6a46cd5-8d74-4d9f-86f3-03ff4df968fb/tasks/bktwnz5tq.output"}
[tool_result] 1	WARNING: 2 other pytest process(es) running; expect slower runs:
2	  34207 03-02:28:53 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
3	  36233       00:01 <work>/env-sqlglot/b
4	RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
5	LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-0eb2d5946e.log
6	ELAPSED: 971s
7	SUMMARY: 1104 passed, 17947 subtests passed in 70.32s (0:01:10)
8	EXIT: 0
9	
10	[exited with code 0]
11	
[assistant] FROM-first queries with joined subqueries now parse. The full suite passed after my last edit: `SUMMARY: 1104 passed, 17947 subtests passed in 70.32s`, `EXIT: 0`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the parenthesised-subquery branch returned before the `if joins:` block. A leading `FROM` calls `_parse_table(joins=True)`, so a join after a parenthesised source was never consumed and the trailing `select` failed. This also broke `from (select 1 x) t1 join tbl_2 ...`, so it isn't specific to `FROM`-first.

**Fix:** When `joins` is set, the subquery branch now attaches the followi
…[293 chars elided]…
, `SELECT`-first, and the `UPDATE ... FROM` and `DELETE ... USING` paths, which also use `joins=True`.

**Tests:** I added three cases to `tests/dialects/test_duckdb.py` next to the existing FROM-first tests. They cover the positional-join example from the report, a subquery with an inner join, and an AST assertion that the join sits on the `Subquery`. No existing test was changed.

**Not done:** I did not run `ast_check.py`, and I did not check transpile output to other dialects. This is a parser-structure fix, not a function mapping, so there was no target-function type equivalence to check.
