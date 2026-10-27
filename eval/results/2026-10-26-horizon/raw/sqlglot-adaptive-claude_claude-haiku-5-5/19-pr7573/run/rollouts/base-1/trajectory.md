# trajectory base-1

final message:
Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders produce the same alias. The full test suite passes (1096 tests), and ruff is clean on both changed files.

**Cause:** `unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the shared alias node. Every render appended the ordinality column again. I reproduced it with `Postgres().generator().generate(node, copy=False)`: the second render gave `t(col, ord, ord)`. The usual `.sql()` entry point copies the tree first, which hides the bug in the simple case. That is why I reproduced through `copy=False`, which matches your "rendered more than once in one call" case.

**Fix:** the generator now copies the alias and the offset before appending, so the AST is left as it was:

```python
alias = alias.copy()
alias.append("columns", offset.copy())
```

The base generator is where the mutation lives, so the fix covers every dialect that uses `WITH ORDINALITY`, not only Postgres.

**Test:** I added a regression case to `test_unnest` in `tests/dialects/test_postgres.py`. It renders one unnest node twice without copying and checks that both outputs match and the alias still has one column. I did not run the new test against the unfixed code. The reproduction before the fix showed the same duplication.

I have not committed anything.

## events
[tool_use Bash] {"command": "grep -n -i \"ordinality\\|unnest\" sqlglot/dialects/postgres.py | head -60", "description": "Find UNNEST and ordinality handling in Postgres dialect"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn -i \"ordinality\" sqlglot/ | head -40", "description": "Search for ordinality references in sqlglot source"}
[tool_result] sqlglot/tokens.py:345:        "ORDINALITY": TokenType.ORDINALITY,
sqlglot/tokenizer_core.py:362:    ORDINALITY = auto()
sqlglot/parser.py:723:        TokenType.ORDINALITY,
sqlglot/parser.py:4311:        ordinality: bool | None = None
sqlglot/parser.py:4323:            ordinality = self._match_pair(TokenType.WITH, TokenType.ORDINALITY)
sqlglot/parser.py:4333:                ordinality=ordinality,
sqlglot/parser.py:4824:        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
sqlglot/par
…[2373 chars elided]…
,
sqlglot/expressions/query.py:951:        "ordinality": False,
sqlglot/expressions/query.py:1958:        "ordinality": False,
sqlglot/generators/bigquery.py:231:    UNNEST_WITH_ORDINALITY = False
sqlglot/generators/exasol.py:702:        "ordinality",
sqlglot/generators/duckdb.py:2015:                UNNEST(CAST(sig -> 'state' AS UBIGINT[])) WITH ORDINALITY AS t(val, pos)
sqlglot/generators/duckdb.py:2031:                     UNNEST(CAST(sig -> 'state' AS UBIGINT[])) WITH ORDINALITY AS s(h, pos)
[tool_use Bash] {"command": "sed -n 3190,3235p sqlglot/generator.py; echo ----; sed -n 2340,2400p sqlglot/dialects/dialect.py", "description": "Read unnest SQL generation and dialect helper"}
[tool_result]         pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
        return self.prepend_ctes(expression, sql)

    def qualify_sql(self, expression: exp.Qualify) -> str:
        this = self.indent(self.sql(expression, "this"))
        return f"{self.seg('QUALIFY')}{self.sep()}{this}"

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = self.expressions(expression, flat=True
…[3020 chars elided]…
erator, expression: exp.DatetimeDiff | exp.TimestampDiff) -> str:
    return self.func("TIMESTAMPDIFF", expression.unit, expression.expression, expression.this)


def no_make_interval_sql(self: Generator, expression: exp.MakeInterval, sep: str = ", ") -> str:
    args = []
    for unit, value in expression.args.items():
        if isinstance(value, exp.Kwarg):
            value = value.expression

        args.append(f"{value} {unit}")

    return f"INTERVAL '{self.format_args(*args, sep=sep)}'"
[assistant] The mutation is in `unnest_sql`: `alias.append("columns", offset)` writes to the shared alias node on every render. Let me reproduce it before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\nu = e.find(exp.Unnest)\nprint(repr(u.args.get('alias').columns))\nb = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], offset=True, alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\nprint(b.sql('postgres')); print(b.sql('postgres'))\n\"", "description": "Reproduce repeated render alias mutation"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col)
[assistant] The parsed `WITH ORDINALITY` case doesn't reproduce, since the parser stores `offset` as a bool there. The mutation only fires when `offset` is an expression, so I'll test that path directly.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nu = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], offset=exp.to_identifier('ord'), alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\nprint(u.sql('postgres')); print(u.sql('postgres')); print(u.sql('postgres'))\nprint(u.args['alias'].columns)\n\"; grep -n \"class Postgres\" -A3 sqlglot/dialects/postgres.py | head; grep -n \"UNNEST_WITH_ORDINALITY\\|unnest\" sqlglot/generators/postgres.py sqlglot/dialects/postgres.py | head", "description": "Reproduce mutation when offset is an identifier"}
[tool_result] UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
10:class Postgres(Dialect):
11-    INDEX_OFFSET = 1
12-    TYPED_DIVISION = True
13-    CONCAT_COALESCE = True
sqlglot/generators/postgres.py:15:    filter_array_using_unnest,
sqlglot/generators/postgres.py:293:        exp.ArrayFilter: filter_array_using_unnest,
sqlglot/generators/postgres.py:421:    def unnest_sql(self, expression: exp.Unnest) -> str:
sqlglot/generators/postgres.py:430:                        .subquery(expression.args.get("alias") or "_unnested_generate_series")
sqlglot/generators/postgres.py:450:        return super().unnest_sql(expression)
[assistant] A top-level `.sql()` copies the tree first, so the mutation is hidden there. The user's case is a single node rendered several times in one call, which happens when the same instance is shared in two places. Let me test that.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nu = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], offset=exp.to_identifier('ord'), alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\nq = exp.select('*').from_(u).union(exp.select('*').from_(u))\nprint(q.sql('postgres'))\nprint(q.sql('postgres'))\n\"", "description": "Reproduce duplicate ord column with shared unnest node"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord) UNION SELECT * FROM UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord) UNION SELECT * FROM UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
[assistant] Sharing alone doesn't reproduce it, probably because the copy step breaks the shared references. I'll check whether `copy=False` exposes the mutation.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\nu = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], offset=exp.to_identifier('ord'), alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\ng = Postgres().generator()\nprint(g.generate(u, copy=False)); print(g.generate(u, copy=False))\nprint(u.args['alias'].columns)\n\"; grep -n \"def generate\" -A12 sqlglot/generator.py | grep -n \"copy\" ", "description": "Test rendering without copy to expose mutation"}
[tool_result] UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord, ord)
[Identifier(this=col, quoted=False), Identifier(this=ord, quoted=False), Identifier(this=ord, quoted=False)]
1:904:    def generate(self, expression: exp.Expr, copy: bool = True) -> str:
7:910-            copy: Whether to copy the expression. The generator performs mutations so
8:911-                it is safer to copy.
13:916-        if copy:
[assistant] Reproduced with `copy=False`: the second render produces `t(col, ord, ord)`. The `.sql()` entry point copies the tree, which hides this in the common case, but the generator itself still mutates the AST. Let me check the Postgres override and whether `Expression.append` returns anything before I edit.
[tool_use Bash] {"command": "sed -n 418,452p sqlglot/generators/postgres.py; echo ----; grep -n \"    def append\" -A12 sqlglot/expressions/core.py | head -30", "description": "Read Postgres unnest override and Expression.append"}
[tool_result]         return super().columndef_sql(expression, sep)

    def unnest_sql(self, expression: exp.Unnest) -> str:
        if len(expression.expressions) == 1:
            arg = expression.expressions[0]
            if isinstance(arg, exp.GenerateDateArray):
                generate_series: exp.Expr = exp.GenerateSeries(**arg.args)
                if isinstance(expression.parent, (exp.From, exp.Join)):
                    generate_series = (
                        exp.select("value::date")
       
…[1400 chars elided]…
 self,
269-        arg_key: str,
--
1041:    def append(self, arg_key: str, value: t.Any) -> None:
1042-        if type(self.args.get(arg_key)) is not list:
1043-            self.args[arg_key] = []
1044-        self._set_parent(arg_key, value)
1045-        values = self.args[arg_key]
1046-        if isinstance(value, Expr):
1047-            value.index = len(values)
1048-        values.append(value)
1049-
1050-    def set(
1051-        self,
1052-        arg_key: str,
1053-        value: object,
[assistant] `Expression.append` returns `None` and also reparents the value, so the fix is to render from a copied alias instead of mutating the node. I'll make that change in the base generator, where the mutation lives.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset.copy())"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\nu = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], offset=exp.to_identifier('ord'), alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\ng = Postgres().generator()\nprint(g.generate(u, copy=False)); print(g.generate(u, copy=False)); print(g.generate(u, copy=False))\nprint(u.args['alias'].columns, u.args['offset'].parent is u)\n\"; grep -n \"ordinality\\|ORDINALITY\" tests/dialects/test_postgres.py | head", "description": "Verify repeated renders are stable after fix"}
[tool_result] UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)] True
108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"

…[502 chars elided]…
EQUENCE(1, GREATEST(CARDINALITY(ARRAY[1])))) AS _u(pos) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS _u_2(col, pos_2) WHERE _u.pos = _u_2.pos_2 OR (_u.pos > CARDINALITY(ARRAY[1]) AND _u_2.pos_2 = CARDINALITY(ARRAY[1]))",
1554:            """SELECT * FROM ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT), FUNC2(col2) AS alias2("col2" INT)) WITH ORDINALITY"""
1557:            """SELECT * FROM table1, ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT)) WITH ORDINALITY AS alias3("col3" INT, "col4" TEXT)"""
[assistant] Repeated renders are now stable and the original node is untouched. Next I'll add a regression test next to the existing ordinality tests.
[tool_use Bash] {"command": "sed -n 125,150p tests/dialects/test_postgres.py; grep -n \"^from\\|^import\" tests/dialects/test_postgres.py", "description": "Read existing ordinality tests and imports"}
[tool_result]         self.validate_identity(
            """LAST_VALUE("col1") OVER (ORDER BY "col2" RANGE BETWEEN INTERVAL '1 DAY' PRECEDING AND '1 month' FOLLOWING)"""
        )
        self.validate_identity(
            """ALTER TABLE ONLY "Album" ADD CONSTRAINT "FK_AlbumArtistId" FOREIGN KEY ("ArtistId") REFERENCES "Artist" ("ArtistId") ON DELETE CASCADE"""
        )
        self.validate_identity(
            """ALTER TABLE ONLY "Album" ADD CONSTRAINT "FK_AlbumArtistId" FOREIGN KEY ("ArtistId") REFEREN
…[549 chars elided]…
ER b FROM c WINDOW a AS (PARTITION BY d), b AS (PARTITION BY e)"
        )
        self.validate_identity(
            "SELECT CASE WHEN SUBSTRING('abcdefg' FROM 1) IN ('ab') THEN 1 ELSE 0 END"
        )
        self.validate_identity(
            "SELECT CASE WHEN SUBSTRING('abcdefg' FROM 1 FOR 2) IN ('ab') THEN 1 ELSE 0 END"
1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
3:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_postgres.py | head -5; sed -n 1,12p tests/dialects/test_postgres.py", "description": "Locate first test method in Postgres test file"}
[tool_result] 10:    def test_postgres(self):
1073:    def test_ddl(self):
1389:    def test_unnest(self):
1411:    def test_array_offset(self):
1434:    def test_bool_or(self):
from sqlglot import ParseError, UnsupportedError, exp, transpile
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


class TestPostgres(Validator):
    maxDiff = None
    dialect = "postgres"

    def test_postgres(self):
        expr = self.parse_one("SELECT * FROM r CROSS JOIN LATERAL UNNEST(ARRAY[1]) AS s(location)")
        unnest = expr.args["joins"][0].this.this
[tool_use Bash] {"command": "sed -n 1389,1411p tests/dialects/test_postgres.py", "description": "Read the test_unnest method"}
[tool_result]     def test_unnest(self):
        self.validate_identity(
            "SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)"
        )

        self.validate_all(
            "SELECT UNNEST(c) FROM t",
            write={
                "hive": "SELECT EXPLODE(c) FROM t",
                "postgres": "SELECT UNNEST(c) FROM t",
                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS col FROM t CROSS JOIN UNNEST(SEQUENCE(1, GREATEST(CARDINALITY(c)))) AS _u(pos) 
…[233 chars elided]…
)",
            write={
                "hive": "SELECT EXPLODE(ARRAY(1))",
                "postgres": "SELECT UNNEST(ARRAY[1])",
                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS col FROM UNNEST(SEQUENCE(1, GREATEST(CARDINALITY(ARRAY[1])))) AS _u(pos) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS _u_2(col, pos_2) WHERE _u.pos = _u_2.pos_2 OR (_u.pos > CARDINALITY(ARRAY[1]) AND _u_2.pos_2 = CARDINALITY(ARRAY[1]))",
            },
        )

    def test_array_offset(self):
[assistant] I'll add a regression test at the end of `test_unnest` that renders one shared node twice without copying and checks both outputs and the alias.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "                \"presto\": \"SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS col FROM UNNEST(SEQUENCE(1, GREATEST(CARDINALITY(ARRAY[1])))) AS _u(pos) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS _u_2(col, po
…[735 chars elided]…
, columns=[exp.to_identifier(\"col\")]),\n        )\n        generator = Postgres().generator()\n        for _ in range(2):\n            self.assertEqual(\n                generator.generate(unnest, copy=False),\n                \"UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)\",\n            )\n        self.assertEqual(len(unnest.args[\"alias\"].columns), 1)\n\n    def test_array_offset(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\nfrom sqlglot.helper import logger as helper_logger\n", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\nfrom sqlglot.dialects.postgres import Postgres\nfrom sqlglot.helper import logger as helper_logger\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-194545-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll run the project's test command: the new test first, then the full suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k test_unnest 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run Postgres unnest test and full pytest suite"}
[tool_result] ..                                                                [100%]
2 passed, 23 deselected, 7 subtests passed in 0.12s
....................................... [ 66%]
......................................... [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 61.58s (0:01:01)
[assistant] The full suite passes (1096 tests). I'll run the linter on the two changed files, then check the diff.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 14 ++++++++++++++
 2 files changed, 16 insertions(+), 1 deletion(-)
[assistant] Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders produce the same alias. The full test suite passes (1096 tests), and ruff is clean on both changed files.

**Cause:** `unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the shared alias node. Every render appended the ordinality column again. I reproduced it with `Postgres().generator().generate(node, copy=False)`: the second render gave `t(col, ord, ord)`. The usual `.sql()` entry point copies the tree first, which hides the bug in the simple case. That is why
…[168 chars elided]…
pending, so the AST is left as it was:

```python
alias = alias.copy()
alias.append("columns", offset.copy())
```

The base generator is where the mutation lives, so the fix covers every dialect that uses `WITH ORDINALITY`, not only Postgres.

**Test:** I added a regression case to `test_unnest` in `tests/dialects/test_postgres.py`. It renders one unnest node twice without copying and checks that both outputs match and the alias still has one column. I did not run the new test against the unfixed code. The reproduction before the fix showed the same duplication.

I have not committed anything.
