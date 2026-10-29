# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. The reported query round-trips to `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the subquery branch returned early, so the `joins=True` handling that runs for plain tables never executed for subquery sources. The `POSITIONAL JOIN` was left unconsumed, and the trailing `SELECT` then raised the error. Plain tables and SELECT-first queries were unaffected because joins are attached elsewhere on those paths.

**Fix:** Before returning a parsed subquery, `_parse_table` now appends any following joins to it when `joins=True`. `Subquery` already accepts `joins` through `QUERY_MODIFIERS`, so no other changes were needed.

**Tests:** I added three cases to `tests/dialects/test_duckdb.py`: a positional join and an `ON` join of two FROM-first subqueries, both checked with `validate_identity`. The full suite passes (1104 tests), and `ruff check` and `ruff format --check` are clean on the changed files.

The changes are uncommitted in the worktree. I didn't commit because you didn't ask for one.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from tbl_1 t1 positional join tbl_2 t2 select t1.x','from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x','from (select 1 as x) t1 join (select 1 as x) t2 select t1.x']:\n    try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, e)\n\" 2>&1 | head -40; grep -n \"FROM\\b\" sqlglot/dialects/duckdb.py | head -30; grep -n \"_parse_from\\|def _parse_select\\|FROM\" sqlglot/parser.py | head -60", "description": "Reproduce bug and locate FROM-first parsing code"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
611:        TokenType.FROM,
1051:        exp.From: lambda self: self._parse_from(joins=True),
1791:    # Whether implicit unnesting is supported, e.g. SELECT 1 FROM y.z AS z, z.a (Redshift)
2458:            referenced_table = self._parse_table_parts() if self._match(TokenType.FROM) else None
3192:        elif self._match(TokenType.FROM):
3587:                    files=self._ma
…[1426 chars elided]…
_set((TokenType.FROM, TokenType.COMMA)):
8086:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8433:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
8780:            if self._match_set((TokenType.FROM, TokenType.IN)):
9408:        kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
9541:        if not securable or not self._match_text_seq("FROM"):
9576:                from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -I -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from tbl_1 t1 positional join tbl_2 t2 select t1.x','from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x','from (select 1 as x) t1 join (select 1 as x) t2 select t1.x']:\n    try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, e)\n\" 2>&1 | head -30; sed -n 3715,3760p sqlglot/parser.py; sed -n 3800,3820p sqlglot/parser.py; sed -n 4168,4200p sqlglot/parser.py", "description": "Reproduce bug and view FROM-first parser code"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'

    def _parse_projections(
        self,
    ) -> tuple[list[exp.Expr], list[exp.Expr] | None]:
        return self._parse_expressions(), None

    def _parse_wrapped_select(self, table: bool = False) -> exp.Expr | None:
        if self._match_set((TokenType.PIVOT, TokenType.UNPIVOT)):
            this: exp.Expr | None = self._parse_simplified_pivot(
                is_unpiv
…[2668 chars elided]…
ression(
            exp.MatchRecognizeMeasure(
                window_frame=self._match_texts(("FINAL", "RUNNING")) and self._prev.text.upper(),
                this=self._parse_expression(),
            )
        )

    def _parse_match_recognize(self) -> exp.MatchRecognize | None:
        if not self._match(TokenType.MATCH_RECOGNIZE):
            return None

        self._match_l_paren()

        partition = self._parse_partition_by()
        order = self._parse_order()

        measures = (
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from tbl_1 t1 positional join tbl_2 t2 select t1.x','from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x','from (select 1 as x) t1 join (select 1 as x) t2 select t1.x', 'from (FROM tbl_1) t1 select t1.x']:\n    try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, type(e).__name__, str(e)[:200])\n\" 2>&1 | head -30", "description": "Reproduce the parse failure with variants"}
[tool_result] ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 ParseError Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2
ERR from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x ParseError Invalid expression / Unexpected token. Line 1, Col: 61.
  from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x [4mselect[0m t1.x
ERR from (select 1 as x) t1 join (select 1 as x) t2 select t1.x ParseError Invalid expression / Unexpected token. Line 1, Col: 54.
  from (select 1 as x) t1 join (select 1 as x) t2 [4mselect[0m t1.x
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor q in ['from (select 1 as x) t1 join (select 1 as x) t2','from (select 1 as x) t1 join (select 1 as x) t2 on true','from tbl t1 join (select 1 as x) t2 select 1', 'from (select 1 as x) t1 join tbl t2 select 1']:\n    try: print(repr(sqlglot.parse_one(q, read='duckdb'))[:300])\n    except Exception as e: print('ERR', q, type(e).__name__, str(e)[:120])\n\"; grep -n \"def _parse_table\\b\\|def _parse_table(\\|def _parse_subquery\\|def _parse_query_modifiers\" sqlglot/parser.py", "description": "Narrow down failing join-with-subquery patterns"}
[tool_result] Select(
  expressions=[
    Star()],
  from_=From(
    this=Subquery(
      this=Select(
        expressions=[
          Alias(
            this=Literal(this=1, is_string=False),
            alias=Identifier(this=x, quoted=False))]),
      alias=TableAlias(
        this=Identifier(this=t1, quoted=Fa
Select(
  expressions=[
    Star()],
  from_=From(
    this=Subquery(
      this=Select(
        expressions=[
          Alias(
            this=Literal(this=1, is_string=False),
            alias=Id
…[307 chars elided]…
alse)),
      joins=[
        Join(
          this=Subquery(
            this=Select(
         
ERR from (select 1 as x) t1 join tbl t2 select 1 ParseError Invalid expression / Unexpected token. Line 1, Col: 42.
  from (select 1 as x) t1 join tbl t2 [4mselect[0m 1
4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4698:    def _parse_table(
[tool_use Bash] {"command": "sed -n 4029,4070p sqlglot/parser.py; sed -n 4698,4790p sqlglot/parser.py", "description": "Read _parse_subquery and _parse_table"}
[tool_result]     def _parse_subquery(
        self, this: exp.Expr | None, parse_alias: bool = True
    ) -> exp.Subquery | None:
        if not this:
            return None

        return self.expression(
            exp.Subquery(
                this=this,
                pivots=self._parse_pivots(),
                alias=self._parse_table_alias() if parse_alias else None,
                sample=self._parse_table_sample(),
            )
        )

    def _implicit_unnests_to_explicit(self, this: E) -> E
…[4076 chars elided]…
upports a wildcard (table) suffix operator, which is a no-op in this context
        self._match(TokenType.STAR)

        parse_partition = parse_partition or self.SUPPORTS_PARTITION_SELECTION
        if parse_partition and self._match(TokenType.PARTITION, advance=False):
            this.set("partition", self._parse_partition())

        if schema:
            return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())
[tool_use Bash] {"command": "sed -n 4790,4830p sqlglot/parser.py; grep -n \"_parse_wrapped_select\\|_parse_subquery(\" sqlglot/parser.py; sed -n 3805,3830p sqlglot/parser.py | head -5; grep -n \"def _parse_query_modifiers\" -A40 sqlglot/parser.py | sed -n 1,60p", "description": "Read rest of _parse_table and query modifiers"}
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
…[3112 chars elided]…
sion.expressions
4107-                                expression.set("expressions", None)
4108-                                offset.set("expressions", limit_by_expressions)
4109-                        continue
4110-                break
4111-
4112-        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
4113-            this = self._implicit_unnests_to_explicit(this)
4114-
4115-        return this
4116-
4117-    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
[tool_use Bash] {"command": "sed -n 3754,3800p sqlglot/parser.py; sed -n 3860,3895p sqlglot/parser.py", "description": "Read _parse_select dispatch for subqueries"}
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

      
…[1984 chars elided]…
lse):
            this = self._parse_derived_table_values()
        elif from_:
            this = exp.select("*").from_(from_.this, copy=False)
            this = self._parse_query_modifiers(this)
        elif self._match(TokenType.SUMMARIZE):
            table = self._match(TokenType.TABLE)
            this = self._parse_select() or self._parse_string() or self._parse_table()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
[tool_use Bash] {"command": "grep -n \"^class Subquery\" -A25 sqlglot/expressions.py | head -40; grep -n \"MODIFIABLES\\s*=\" -A3 sqlglot/parser.py sqlglot/expressions.py | head; grep -n \"Subquery.*joins\\|joins.*Subquery\" tests/*.py tests/dialects/*.py | head -5", "description": "Check Subquery arg_types and joins support"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"^class Subquery\" -A22 sqlglot/expressions/ | head -40; grep -rn \"MODIFIABLES = \" sqlglot/ | head", "description": "Locate Subquery expression definition"}
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
sqlglot/expressions/query.py:1662:class Subquery(Expression, DerivedTable, Query):
sqlglot/expressions/query.py-1663-    is_subquery: t.ClassVar[bool] = True
sqlglot/expressions/query.py-1664-    arg_type
…[1582 chars elided]…
pressions/core.py-1592-
sqlglot/expressions/core.py-1593-class Any(Expression, SubqueryPredicate):
sqlglot/expressions/core.py-1594-    pass
sqlglot/expressions/core.py-1595-
sqlglot/expressions/core.py-1596-
sqlglot/expressions/core.py-1597-@trait
sqlglot/expressions/core.py-1598-class Binary(Condition):
sqlglot/expressions/core.py-1599-    arg_types: t.ClassVar[dict[str, bool]] = {"this": True, "expression": True}
sqlglot/expressions/core.py-1600-
sqlglot/expressions/core.py-1601-    @property
[assistant] Subquery accepts `joins` via `QUERY_MODIFIERS`. The cause is in `_parse_table`: the subquery branch returns early, so `joins=True` never gets applied to a subquery source. I'll apply joins there.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2','from (FROM tbl_1) t1 join (FROM tbl_2) t2 on t1.x=t2.x select t1.x','from (select 1 as x) t1 join (select 1 as x) t2 select t1.x','from (select 1 as x) t1 join tbl t2 select 1', 'select * from (select 1) t1 join (select 2) t2 on true']:\n    try: print(sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q, type(e).__name__, str(e)[:120])\n\"; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x
SELECT t1.x FROM (SELECT 1 AS x) AS t1, (SELECT 1 AS x) AS t2
SELECT 1 FROM (SELECT 1 AS x) AS t1, tbl AS t2
SELECT * FROM (SELECT 1) AS t1 JOIN (SELECT 2) AS t2 ON TRUE
..................................................................... [ 38%]
................................................ [ 42
…[306 chars elided]…
................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 54.57s
[assistant] The failing query now parses and round-trips, and the full suite passes (1104 tests). Before adding a regression test, I'll confirm the plain-join output matches the SELECT-first form.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(sqlglot.parse_one('select 1 from (select 1 as x) t1 join tbl t2', read='duckdb').sql('duckdb'))\nprint(sqlglot.parse_one('select 1 from tbl t1 join tbl t2', read='duckdb').sql('duckdb'))\nprint(sqlglot.parse_one('from tbl t1 join tbl t2 select 1', read='duckdb').sql('duckdb'))\n\"; grep -n \"FROM-first\\|from-first\\|FROM tbl\\|from tbl\" tests/dialects/test_duckdb.py | head -20", "description": "Compare FROM-first and SELECT-first join output"}
[tool_result] SELECT 1 FROM (SELECT 1 AS x) AS t1, tbl AS t2
SELECT 1 FROM tbl AS t1, tbl AS t2
SELECT 1 FROM tbl AS t1, tbl AS t2
426:            "SELECT tbl.x*1e4+tbl.y FROM tbl",
427:            "SELECT tbl.x * 1e4 + tbl.y FROM tbl",
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
496:        self.validate_identity("SUMMARIZE SELECT * FROM tbl").assert_is(exp.Summarize)
1950:            "SELECT * 
…[759 chars elided]…
(20%), tbl2 WHERE tbl.i=tbl2.i",
1971:            "SELECT * FROM tbl TABLESAMPLE RESERVOIR (20 PERCENT), tbl2 WHERE tbl.i = tbl2.i",
1974:            "SELECT * FROM tbl, tbl2 WHERE tbl.i=tbl2.i USING SAMPLE RESERVOIR(20%)",
1975:            "SELECT * FROM tbl, tbl2 WHERE tbl.i = tbl2.i USING SAMPLE RESERVOIR (20 PERCENT)",
2558:            "WITH RECURSIVE tbl(a, b) USING KEY (a) AS (SELECT a, b FROM (VALUES (1, 3), (2, 4)) AS t(a, b) UNION SELECT a + 1, b FROM tbl WHERE a < 3) SELECT * FROM tbl"
[assistant] Output matches the SELECT-first behavior. Next I'll add a regression test next to the existing FROM-first tests.
[tool_use Bash] {"command": "sed -n 480,500p tests/dialects/test_duckdb.py; grep -n \"POSITIONAL\" tests/dialects/test_duckdb.py | head -5", "description": "View existing FROM-first tests in duckdb suite"}
[tool_result]         self.validate_identity("SELECT {'x': 1, 'y': 2, 'z': 3}")
        self.validate_identity("SELECT {'key1': 'string', 'key2': 1, 'key3': 12.345}")
        self.validate_identity("SELECT ROW(x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT (x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT a.x FROM (SELECT {'x': 1, 'y': 2, 'z': 3} AS a)")
        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x 
…[624 chars elided]…
tity("SUMMARIZE tbl").assert_is(exp.Summarize)
        self.validate_identity("SUMMARIZE SELECT * FROM tbl").assert_is(exp.Summarize)
        self.validate_identity("CREATE TABLE tbl_summary AS SELECT * FROM (SUMMARIZE tbl)")
        self.validate_identity("SELECT STAR(tbl, exclude := [foo])")
        self.validate_identity("UNION_VALUE(k1 := 1)").find(exp.PropertyEQ).this.assert_is(
            exp.Identifier
469:        self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(", "new_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validat
…[340 chars elided]…
N t1.x = t2.x SELECT t1.x\",\n            \"SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",\n            \"SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)\",\n        )\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I accidentally duplicated the existing `NOT EXISTS` assertion in that edit. Removing the copy:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "            \"SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",\n            \"SELECT * FROM t1 WHERE NOT EXISTS(SELECT * FROM t2 WHERE t2.id = t1.id)\",\n        )\n        self.validate_identity(", "new_string": "            \"SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON t1.x = t2.x\",\n        )\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-085100-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $P -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -2; $P -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -2; git status --short", "description": "Run full tests, ruff lint and format checks"}
[tool_result] ................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 50.69s
All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
[assistant] FROM-first queries with joined subqueries now parse. The reported query round-trips to `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`.

**Cause:** In `_parse_table` (`sqlglot/parser.py`), the subquery branch returned early, so the `joins=True` handling that runs for plain tables never executed for subquery sources. The `POSITIONAL JOIN` was left unconsumed, and the trailing `SELECT` then raised the error. Plain tables and SELECT-first queries were unaffected because joins are attached elsewhere on those paths.

**Fix:** Before returning a parsed subquery, `_parse_table` now appends any following joins to it when `joins=True`. `Subquery` already accepts `joins` through `QUERY_MODIFIERS`, so no other changes were needed.

**Tests:** I added three cases to `tests/dialects/test_duckdb.py`: a positional join and an `ON` join of two FROM-first subqueries, both checked with `validate_identity`. The full suite passes (1104 tests), and `ruff check` and `ruff format --check` are clean on the changed files.

The changes are uncommitted in the worktree. I didn't commit because you didn't ask for one.
