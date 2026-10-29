# trajectory base-1

final message:
FROM-first DuckDB queries with joined subqueries now parse, and the full suite passes (1104 tests).

**Cause:** `_parse_table` returns early when the table is a parenthesized subquery, so the `joins` requested by `joins=True` were never consumed. The joins then fell through to the `elif from_:` branch in `_parse_select_query`, which can't be followed by `SELECT`. That is why the error pointed at `select`. Plain-table first sources worked because their joins are parsed in the table branch.

**Fix** (`sqlglot/parser.py`, in `_parse_table`): when `joins` is set, attach the joins to the subquery node, as the UPDATE path already does for subquery sources.

**Tests** (`tests/dialects/test_duckdb.py`): added two round-trip cases next to the existing FROM-first tests:
- The reported `FROM (FROM tbl_1) t1 POSITIONAL JOIN (FROM tbl_2) t2 SELECT ...` query.
- A subquery-first `JOIN tbl_2` variant.

The new tests were not run against the unpatched code. The failing shapes were confirmed by hand before the fix. `ruff check` and `ruff format --check` pass on both files.

I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n -i \"from\" sqlglot/dialects/duckdb.py | grep -i -E \"first|_parse_from|FROM\" | head -40; grep -n \"_parse_from\\|def _parse_select\\|FROM_FIRST\\|from_first\" sqlglot/parser.py | head -40", "description": "Locate FROM-first parsing code"}
[tool_result] 1:from __future__ import annotations
4:from sqlglot import exp, tokens
6:from sqlglot.dialects.dialect import (
10:from sqlglot.generators.duckdb import DuckDBGenerator, WS_CONTROL_CHARS_TO_DUCK  # noqa: F401
11:from sqlglot.parsers.duckdb import DuckDBParser
12:from sqlglot.tokens import TokenType
13:from sqlglot.typing.duckdb import EXPRESSION_METADATA
1051:        exp.From: lambda self: self._parse_from(joins=True),
3634:                from_ = self._parse_from(joins=True)
3727:            from_ = self._parse_from(skip_from_token=True, consume_pipe=True)
3754:    def _parse_select(
3779:    def _parse_select_query(
3809:            self._parse_from(joins=True, consume_pipe=True)
3869:                from_ = self._parse_from()
4168:    def _parse_from(
8433:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 3754,3830p sqlglot/parser.py; echo ----; sed -n 4168,4200p sqlglot/parser.py; echo ----; grep -n \"FROM\" sqlglot/parsers/duckdb.py | head -30", "description": "Read select and from parsing code"}
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

      
…[2789 chars elided]…
exp.MatchRecognize | None:
        if not self._match(TokenType.MATCH_RECOGNIZE):
            return None

        self._match_l_paren()

        partition = self._parse_partition_by()
        order = self._parse_order()

        measures = (
----
283:        # DuckDB supports prefix aliases, e.g. FROM foo: bar
368:        from_ = self._parse_table(schema=True) if self._match(TokenType.FROM) else None
383:                from_=self._parse_var_or_string() if self._match(TokenType.FROM) else None,
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\ntests = {\n'a': '''from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'b': '''from (SELECT * FROM tbl_1) t1 positional join (SELECT * FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'c': '''from tbl_1 t1 positional join tbl_2 t2 select t1.x a
…[37 chars elided]…
ROM tbl_1) t1 join (FROM tbl_2) t2 on true select t1.x''',\n'e': '''from (FROM tbl_1) t1 select t1.x''',\n'f': '''select t1.x from (FROM tbl_1) t1 positional join (FROM tbl_2) t2''',\n}\nfor k,v in tests.items():\n    try: print(k, sqlglot.parse_one(v, read='duckdb').sql('duckdb'))\n    except Exception as e: print(k, 'ERR', str(e)[:200])\n\"", "description": "Reproduce FROM-first parse failures"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ntests = {\n'a': '''from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'b': '''from (SELECT * FROM tbl_1) t1 positional join (SELECT * FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'c': '''from tbl_1 t1 positional join tbl_2 t2 
…[68 chars elided]…
 (FROM tbl_2) t2 on true select t1.x''',\n'e': '''from (FROM tbl_1) t1 select t1.x''',\n'f': '''select t1.x from (FROM tbl_1) t1 positional join (FROM tbl_2) t2''',\n}\nfor k,v in tests.items():\n    try: print(k, sqlglot.parse_one(v, read='duckdb').sql('duckdb'))\n    except Exception as e: print(k, 'ERR', str(e)[:200])\n\"", "description": "Reproduce FROM-first parse failures with repo on path"}
[tool_result] a ERR Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
b ERR Invalid expression / Unexpected token. Line 1, Col: 77.
  from (SELECT * FROM tbl_1) t1 positional join (SELECT * FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
c SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2
d ERR Invalid expression / Unexpected token. Line 1, Col: 56.
  from (FROM tbl_1) t1 join (FROM tbl_2) t2 on true [4mselect[0m t1.x
e SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
f SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ntests = {\n'g': 'from tbl_1 t1 join (SELECT * FROM tbl_2) t2 on true select t1.x',\n'h': 'from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true select t1.x',\n'i': 'from (SELECT * FROM tbl_1) t1 select t1.x',\n'j': 'from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true',\
…[43 chars elided]…
bl_2 t2 on true where t1.x = 1',\n'l': 'from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true select t1.x as x1',\n'm': 'from (SELECT * FROM tbl_1) t1, (SELECT 1) t2 select t1.x',\n}\nfor k,v in tests.items():\n    try: print(k, sqlglot.parse_one(v, read='duckdb').sql('duckdb'))\n    except Exception as e: print(k, 'ERR', str(e)[:200])\n\"", "description": "Narrow down which FROM-first shape fails"}
[tool_result] g SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON TRUE
h ERR Invalid expression / Unexpected token. Line 1, Col: 58.
  from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true [4mselect[0m t1.x
i SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
j SELECT * FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE
k SELECT * FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE WHERE t1.x = 1
l ERR Invalid expression / Unexpected token. Line 1, Col: 58.
  from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true [4mselect[0m t1.x as x1
m ERR Invalid expression / Unexpected token. Line 1, Col: 51.
  from (SELECT * FROM tbl_1) t1, (SELECT 1) t2 [4mselect[0m t1.x
[tool_use Bash] {"command": "grep -n \"def _parse_table\\b\\|def _parse_table(\\|def _parse_query_modifiers\\|def _parse_subquery\\|def _parse_table_parts\" sqlglot/parser.py", "description": "Find table and subquery parsing functions"}
[tool_result] 4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4564:    def _parse_table_parts_fast(self) -> exp.Table | None:
4627:    def _parse_table_parts(
4698:    def _parse_table(
[tool_use Bash] {"command": "sed -n 4029,4070p sqlglot/parser.py; echo ----; sed -n 4077,4100p sqlglot/parser.py; echo ----; sed -n 4698,4800p sqlglot/parser.py", "description": "Read subquery, modifiers, and table parsing"}
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
…[5550 chars elided]…
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
[tool_use Bash] {"command": "sed -n 4800,4830p sqlglot/parser.py; echo ----; sed -n 3830,3900p sqlglot/parser.py", "description": "Read rest of table parsing and select query"}
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
…[2798 chars elided]…
= self._parse_query_modifiers(this)
        elif self._match(TokenType.SUMMARIZE):
            table = self._match(TokenType.TABLE)
            this = self._parse_select() or self._parse_string() or self._parse_table()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
            this = self._parse_describe()
        else:
            this = None

        return self._parse_set_operations(this) if parse_set_operation else this
[tool_use Bash] {"command": "grep -n '\"joins\"' sqlglot/parser.py | head -30; grep -n \"class Subquery\" -A12 sqlglot/expressions/*.py | grep -n \"arg_types\\|joins\" ; grep -rn \"class Subquery\" sqlglot/ | head", "description": "Find where joins from FROM-first are moved"}
[tool_result] 3637:                    table.set("joins", list(self._parse_joins()) or None)
4048:        for i, join in enumerate(this.args.get("joins") or []):
4080:                this.append("joins", join)
4433:            kwargs["this"].set("joins", joins if joins else None)
4822:                this.append("joins", join)
16:sqlglot/expressions/query.py-1664-    arg_types = {
sqlglot/expressions/core.py:1585:class SubqueryPredicate(Predicate):
sqlglot/expressions/query.py:1662:class Subquery(Expression, DerivedTable, Query):
[tool_use Bash] {"command": "sed -n 3620,3645p sqlglot/parser.py; echo ----; sed -n 4420,4440p sqlglot/parser.py; echo ----; sed -n 1662,1672p sqlglot/expressions/query.py", "description": "Inspect join attachment code paths"}
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
…[1334 chars elided]…
)

        kwargs["pivots"] = self._parse_pivots()

        comments = [c for token in (method, side, kind) if token for c in token.comments]
        comments = (join_comments or []) + comments

        if (
----
class Subquery(Expression, DerivedTable, Query):
    is_subquery: t.ClassVar[bool] = True
    arg_types = {
        "this": True,
        "alias": False,
        "with_": False,
        **QUERY_MODIFIERS,
    }

    def unnest(self) -> Expr:
        """Returns the first non subquery."""
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('from tbl_1 t1 join tbl_2 t2 on true select t1.x', read='duckdb')))\nprint(repr(sqlglot.parse_one('from tbl_1 t1 join (select 1) t2 on true select t1.x', read='duckdb')))\n\" | head -c 3000; echo; grep -n \"from_.*joins\\|joins.*from_\" sqlglot/*.py sqlglot/*/*.py | head", "description": "Inspect AST for working FROM-first join case"}
[tool_result] Select(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False),
      table=Identifier(this=t1, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=tbl_1, quoted=False),
      alias=TableAlias(
        this=Identifier(this=t1, quoted=False)),
      joins=[
        Join(
          this=Table(
            this=Identifier(this=tbl_2, quoted=False),
            alias=TableAlias(
              this=Identifier(this=t2, quoted=False))),
          on=Boolean(this=T
…[1041 chars elided]…
ql(expression)
sqlglot/planner.py:118:            join = Join.from_joins(joins, ctes)
sqlglot/planner.py:334:    def from_joins(cls, joins: Iterable[exp.Join], ctes: dict[str, Step] | None = None) -> Join:
sqlglot/parser.py:3634:                from_ = self._parse_from(joins=True)
sqlglot/optimizer/optimize_joins.py:81:                if name != from_.alias_or_name and name in joins_by_name
sqlglot/optimizer/merge_subqueries.py:100:            _merge_joins(outer_scope, inner_scope, from_or_join)
[tool_use Bash] {"command": "grep -rn \"joins=True\" sqlglot/ | head -20; git status --short | head", "description": "Find callers that pass joins=True"}
[tool_result] sqlglot/parser.py:1051:        exp.From: lambda self: self._parse_from(joins=True),
sqlglot/parser.py:3611:                this=self._match(TokenType.FROM) and self._parse_table(joins=True),
sqlglot/parser.py:3613:                and self._parse_csv(lambda: self._parse_table(joins=True)),
sqlglot/parser.py:3626:            "this": self._parse_table(joins=True, alias_tokens=self.UPDATE_ALIAS_TOKENS),
sqlglot/parser.py:3634:                from_ = self._parse_from(joins=True)
sqlglot/parser.py:3809:            self._parse_from(joins=True, consume_pipe=True)
sqlglot/parsers/teradata.py:122:                from_=self._parse_from(joins=True),
[assistant] The cause is in `_parse_table`: when the table is a parenthesized subquery, it returns early and never parses the `joins` that `joins=True` asks for. The joins then fall through to `_parse_select_query`'s `elif from_:` branch, which can't be followed by `SELECT`. I'll attach joins to the subquery in that branch, matching how the table branch and the UPDATE path already attach them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102140-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102140-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ntests = [\n'''from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'''from (SELECT * FROM tbl_1) t1 positional join (SELECT * FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'from (SELECT * FROM tbl_1) t1 join tbl_2 t2 on true sele
…[298 chars elided]…
       e = sqlglot.parse_one(v, read='duckdb'); print(e.sql('duckdb'))\n    except Exception as ex: print('ERR', str(ex)[:150])\n\"; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(sqlglot.transpile('from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2', read='duckdb', write='duckdb', pretty=True)[0])\"", "description": "Verify fix on the failing and related queries"}
[tool_result] SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE
SELECT * FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1, (SELECT 1) AS t2
SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
SELECT
  t1.x AS x1,
  t2.x AS x2
FROM (
  SELECT
    *
  FROM tbl_1
) AS t1
POSITIONAL JOIN (
  SELECT
    *
  FROM tbl_2
) AS t2
[assistant] The reported query now parses and round-trips. Next I'll add a regression test next to the existing FROM-first tests and run the project suite.
[tool_use Bash] {"command": "grep -n -i \"from-first\\|FROM tbl\\|leading with\\|FROM x\\|\\\"FROM \" tests/dialects/test_duckdb.py | head -20", "description": "Find existing FROM-first tests in DuckDB suite"}
[tool_result] 167:            "SELECT * FROM x ORDER BY 1 NULLS LAST",
169:                "duckdb": "SELECT * FROM x ORDER BY 1",
170:                "mysql": "SELECT * FROM x ORDER BY 1",
378:            "SELECT UNNEST(ARRAY[1, 2, 3]), UNNEST(ARRAY[4, 5]), UNNEST(ARRAY[6]) FROM x",
380:                "bigquery": "SELECT IF(pos = pos_2, col, NULL) AS col, IF(pos = pos_3, col_2, NULL) AS col_2, IF(pos = pos_4, col_3, NULL) AS col_3 FROM x CROSS JOIN UNNEST(GENERATE_ARRAY(0, GREATEST(ARRAY_LENGTH([1, 2, 3]), 
…[1920 chars elided]…
igquery": f"SELECT * FROM x {join_type} JOIN UNNEST(y)",
532:                        "bigquery": f"SELECT * FROM x {join_type} JOIN UNNEST(y) ON TRUE",
533:                        "duckdb": f"SELECT * FROM x {join_type} JOIN UNNEST(y) ON TRUE",
922:            "WITH 'x' AS (SELECT 1) SELECT * FROM x",
923:            write={"duckdb": 'WITH "x" AS (SELECT 1) SELECT * FROM x'},
1453:            "FROM (FROM t1 UNION FROM t2)",
1457:            "FROM (FROM (SELECT 1) AS t2(c), (SELECT t2.c AS c0))",
[tool_use Bash] {"command": "sed -n 480,500p tests/dialects/test_duckdb.py", "description": "View context around FROM-first tests"}
[tool_result]         self.validate_identity("SELECT {'x': 1, 'y': 2, 'z': 3}")
        self.validate_identity("SELECT {'key1': 'string', 'key2': 1, 'key3': 12.345}")
        self.validate_identity("SELECT ROW(x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT (x, x + 1, y) FROM (SELECT 1 AS x, 'a' AS y)")
        self.validate_identity("SELECT a.x FROM (SELECT {'x': 1, 'y': 2, 'z': 3} AS a)")
        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x 
…[537 chars elided]…
dentity("SELECT * FROM foo WHERE bar > $baz AND bla = $bob")
        self.validate_identity("SUMMARIZE tbl").assert_is(exp.Summarize)
        self.validate_identity("SUMMARIZE SELECT * FROM tbl").assert_is(exp.Summarize)
        self.validate_identity("CREATE TABLE tbl_summary AS SELECT * FROM (SUMMARIZE tbl)")
        self.validate_identity("SELECT STAR(tbl, exclude := [foo])")
        self.validate_identity("UNION_VALUE(k1 := 1)").find(exp.PropertyEQ).this.assert_is(
            exp.Identifier
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102140-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM tbl\", \"SELECT * FROM tbl\")\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\",", "new_string": "        
…[259 chars elided]…
tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )\n        self.validate_identity(\n            \"FROM (SELECT * FROM tbl_1) t1 JOIN tbl_2 t2 ON TRUE SELECT t1.x\",\n            \"SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE\",\n        )\n        self.validate_identity(\n            \"SELECT * FROM t1 WHERE NOT EXISTS(FROM t2 WHERE t2.id = t1.id)\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102140-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the project test suite"}
[tool_result] ..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 54%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
....................................... [ 65%]
......................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 49.34s
[assistant] All 1104 tests pass. I'll also run the linter on the two changed files, since the new test line is long.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ($P -m ruff --version && $P -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py && $P -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py) 2>&1 | tail -8; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
 sqlglot/parser.py             | 3 +++
 tests/dialects/test_duckdb.py | 8 ++++++++
 2 files changed, 11 insertions(+)
[assistant] FROM-first DuckDB queries with joined subqueries now parse, and the full suite passes (1104 tests).

**Cause:** `_parse_table` returns early when the table is a parenthesized subquery, so the `joins` requested by `joins=True` were never consumed. The joins then fell through to the `elif from_:` branch in `_parse_select_query`, which can't be followed by `SELECT`. That is why the error pointed at `select`. Plain-table first sources worked because their joins are parsed in the table branch.

**Fix** (`sqlglot/parser.py`, in `_parse_table`): when `joins` is set, attach the joins to the subquery node, as the UPDATE path already does for subquery sources.

**Tests** (`tests/dialects/test_duckdb.py`): added two round-trip cases next to the existing FROM-first tests:
- The reported `FROM (FROM tbl_1) t1 POSITIONAL JOIN (FROM tbl_2) t2 SELECT ...` query.
- A subquery-first `JOIN tbl_2` variant.

The new tests were not run against the unpatched code. The failing shapes were confirmed by hand before the fix. `ruff check` and `ruff format --check` pass on both files.

I did not commit anything.
