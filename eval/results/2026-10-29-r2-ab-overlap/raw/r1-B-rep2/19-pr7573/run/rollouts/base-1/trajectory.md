# trajectory base-1

final message:
Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders give the same `t(col, ord)`. The full suite passes (1097 tests), and ruff check and format are clean.

**Cause:** `Generator.unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the shared alias node. Each render added the ordinality column again, so a second render of the same node produced `t(col, ord, ord)`.

**Fix:** the generator now copies the alias and offset before appending, so the AST is untouched:

```python
if self.UNNEST_WITH_ORDINALITY:
    if alias and isinstance(offset, exp.Expr):
        alias = alias.copy()
        alias.append("columns", offset.copy())
```

**Test:** `test_unnest_ordinality_is_not_mutated_on_render` in `tests/dialects/test_postgres.py` renders one `Unnest` node twice through the Postgres generator and asserts the output is stable and the alias keeps only `col`. It fails without the fix (`t(col, ord, ord)`) and passes with it.

One thing to know: `sql()` deep-copies the tree before generating, and copying doesn't preserve shared nodes. So a plain `.sql()` call on a tree never renders the same node twice on its own. The bug shows up when a generator renders the same node more than once, which is what the test exercises directly. I didn't find a natural whole-query input that triggers it, so the test calls the generator directly rather than going through `.sql()`.

## events
[tool_use Bash] {"command": "grep -rn -i \"ordinality\" sqlglot/ tests/ | head -50", "description": "Find ordinality handling across sqlglot and tests"}
[tool_result] sqlglot/tokens.py:345:        "ORDINALITY": TokenType.ORDINALITY,
sqlglot/tokenizer_core.py:362:    ORDINALITY = auto()
sqlglot/parser.py:723:        TokenType.ORDINALITY,
sqlglot/parser.py:4311:        ordinality: bool | None = None
sqlglot/parser.py:4323:            ordinality = self._match_pair(TokenType.WITH, TokenType.ORDINALITY)
sqlglot/parser.py:4333:                ordinality=ordinality,
sqlglot/parser.py:4824:        if self._match_pair(TokenType.WITH, TokenType.ORDINALITY):
sqlglot/par
…[6445 chars elided]…
ND _u_3.pos_3 = CARDINALITY(ARRAY[4, 5, 6])))",
tests/dialects/test_spark.py:1200:                "presto": "SELECT col, pos, IF(_u_2.pos_2 = _u_3.pos_3, _u_3.col_2) AS col_2, IF(_u_2.pos_2 = _u_3.pos_3, _u_3.pos_3) AS pos_3 FROM _u CROSS JOIN UNNEST(SEQUENCE(1, GREATEST(CARDINALITY(ARRAY[2, 3])))) AS _u_2(pos_2) CROSS JOIN UNNEST(ARRAY[2, 3]) WITH ORDINALITY AS _u_3(col_2, pos_3) WHERE _u_2.pos_2 = _u_3.pos_3 OR (_u_2.pos_2 > CARDINALITY(ARRAY[2, 3]) AND _u_3.pos_3 = CARDINALITY(ARRAY[2, 3]))",
[tool_use Bash] {"command": "sed -n 2300,2350p sqlglot/generator.py && echo ---- && sed -n 3195,3230p sqlglot/generator.py && echo ---- && grep -n \"def unnest_sql\\|def tablealias_sql\\|def table_sql\" sqlglot/generator.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py", "description": "Read unnest and table generation code"}
[tool_result]         if self.dialect.ALIAS_POST_TABLESAMPLE:
            pre_alias = sample
        else:
            post_alias = sample

        if self.dialect.ALIAS_POST_VERSION:
            pre_alias = f"{pre_alias}{version}"
        else:
            post_alias = f"{post_alias}{version}"

        hints = self.expressions(expression, key="hints", sep=" ")
        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
     
…[2592 chars elided]…
here_sql(self, expression: exp.PreWhere) -> str:
        return ""

    def where_sql(self, expression: exp.Where) -> str:
----
4 matches in 2 files:

sqlglot/generator.py:1524:def tablealias_sql(self, expression: exp.TableAlias) -> str:
sqlglot/generator.py:2287:def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
sqlglot/generator.py:3198:def unnest_sql(self, expression: exp.Unnest) -> str:
sqlglot/generators/postgres.py:421:def unnest_sql(self, expression: exp.Unnest) -> str:
[tool_use Bash] {"command": "sed -n 410,450p sqlglot/generators/postgres.py; grep -n \"UNNEST\" tests/dialects/test_postgres.py | head -30", "description": "Read Postgres unnest generator and related tests"}
[tool_result]         # PostgreSQL places parameter modes BEFORE parameter name
        param_constraint = expression.find(exp.InOutColumnConstraint)

        if param_constraint:
            mode_sql = self.sql(param_constraint)
            param_constraint.pop()  # Remove to prevent double-rendering
            base_sql = super().columndef_sql(expression, sep)
            return f"{mode_sql} {base_sql}"

        return super().columndef_sql(expression, sep)

    def unnest_sql(self, expression: exp.Unnest) 
…[2537 chars elided]…
 LATERAL UNNEST(ARRAY[1]) AS s(location)")
tests/dialects/test_postgres.py:1391:"SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)"
tests/dialects/test_postgres.py:1395:"SELECT UNNEST(c) FROM t",
tests/dialects/test_postgres.py:1403:"SELECT UNNEST(ARRAY[1])",
tests/dialects/test_postgres.py:1533:CROSS JOIN UNNEST(CAST(boxcrate AS array(json))) AS x(tbox)
tests/dialects/test_postgres.py:1534:CROSS JOIN UNNEST(CAST(json_extract(tbox, '$.boxes') AS array(json))) AS y(boxes...
[assistant] The mutation is in `Generator.unnest_sql`: `alias.append("columns", offset)` writes into the shared alias node on every render. Reproducing before fixing.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(exp.Unnest)\nprint(u.args['offset'] is not None, u.args.get('offset'))\nfor _ in range(3):\n    print(e.sql('postgres'))\nprint(e.sql('postgres'))\n\" 2>&1 | head -20", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor _ in range(3):\n    print(e.sql('postgres'))\n\" 2>&1 | head -20", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor _ in range(3):\n    print(e.sql('postgres'))\n\" 2>&1 | head -20", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[assistant] Parsing a Postgres table alias doesn't hit the `Unnest` path, so I'll build the `Unnest` node with an offset directly to exercise the generator branch.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor sql in ['SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', 'SELECT * FROM UNNEST(x) WITH OFFSET AS o']:\n    e = sqlglot.parse_one(sql, read='bigquery')\n    print(repr(e.find(exp.Unnest).args.get('offset')))\n    for _ in range(3):\n        print(e.sql('postgres'))\ne = sqlglot.parse_one('SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', read='bigquery')\nu = e.find(exp.Unnest)\nu.set('alias', exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\nfor _ in range(3):\n    print(e.sql('postgres'))\n\" 2>&1 | head -30", "description": "Try Unnest offset rendering paths for repeated output"}
[tool_result] Identifier(this=o, quoted=False)
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY
Identifier(this=o, quoted=False)
SELECT * FROM UNNEST(x) WITH ORDINALITY
SELECT * FROM UNNEST(x) WITH ORDINALITY
SELECT * FROM UNNEST(x) WITH ORDINALITY
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o)
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o)
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o)
[assistant] The output looks stable in that run, so I'll check whether the alias node itself is growing across renders.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', read='bigquery')\nu = e.find(exp.Unnest)\nu.set('alias', exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\nfor _ in range(3):\n    print(e.sql('postgres'), '|', [c.name for c in u.args['alias'].columns])\nprint(e.sql('duckdb'), '|', [c.name for c in u.args['alias'].columns])\n\" 2>&1 | head -30; grep -n \"UNNEST_WITH_ORDINALITY\\|class Postgres\\|UNNEST_COLUMN_ONLY\" sqlglot/generators/postgres.py sqlglot/dialects/postgres.py sqlglot/generator.py | head", "description": "Check whether alias columns accumulate across renders"}
[tool_result] SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
SELECT * FROM t CROSS JOIN UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
7 matches in 3 files:

sqlglot/dialects/postgres.py:10:class Postgres(Dialect):
sqlglot/generator.py:399:UNNEST_WITH_ORDINALITY = True
sqlglot/generator.py:1533:if not alias and not self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/generator.py:3204:if self.UNNEST_WITH_ORDINALITY:
sqlglot/generator.py:3208:if alias and self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/generator.py:3215:if self.UNNEST_WITH_ORDINALITY:
sqlglot/generators/postgres.py:225:class PostgresGenerator(generator.Generator):
[assistant] The alias node isn't growing here, so the copy-on-render path may be masking it. The report says the same unnest appears in several places within one `.sql()` call, so I'll test a shared node referenced twice.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', read='bigquery')\nu = e.find(exp.Unnest)\nu.set('alias', exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\ne2 = sqlglot.parse_one('SELECT 1')\ne2.set('joins', [exp.Join(this=u.copy()), exp.Join(this=u)])\nprint(e2.sql('postgres'))\nprint([c.name for c in u.args['alias'].columns])\nprint(e2.sql('postgres'))\n\" 2>&1 | head -30; sed -n 1,20p sqlglot/generator.py | head -0; grep -n \"def sql(\" -A30 sqlglot/generator.py | grep -n \"copy\\|preprocess\" ", "description": "Test shared unnest node rendered in multiple places"}
[tool_result] SELECT 1, UNNEST(x) WITH ORDINALITY AS t(col, o), UNNEST(x) WITH ORDINALITY AS t(col, o)
['col']
SELECT 1, UNNEST(x) WITH ORDINALITY AS t(col, o), UNNEST(x) WITH ORDINALITY AS t(col, o)
head: illegal line count -- 0
[assistant] Still no duplication, so the top-level `sql()` likely copies the tree. Checking the generate entry point and whether the offset path mutates anything when the original node is used directly.
[tool_use Bash] {"command": "grep -n \"def generate\" -A40 sqlglot/generator.py | grep -n \"copy\" ; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.generator import Generator\nfrom sqlglot.dialects.postgres import Postgres\ne = sqlglot.parse_one('SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', read='bigquery')\nu = e.find(exp.Unnest)\nu.set('alias', exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]))\ng = Postgres().generator()\nfor _ in range(2):\n    print(g.unnest_sql(u), '|', [c.name for c in u.args['alias'].columns])\n\" 2>&1 | head", "description": "Call unnest_sql directly to observe alias mutation"}
[tool_result] 1:904:    def generate(self, expression: exp.Expr, copy: bool = True) -> str:
7:910-            copy: Whether to copy the expression. The generator performs mutations so
8:911-                it is safer to copy.
13:916-        if copy:
14:917-            expression = expression.copy()
UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col', 'o']
UNNEST(x) WITH ORDINALITY AS t(col, o, o) | ['col', 'o', 'o']
[assistant] Reproduced: calling `unnest_sql` twice on the same node appends `o` to the shared alias each time (`['col','o','o']`). `sql()` copies the tree first, so the bug only shows when the same node is rendered more than once within one generation, which is what the report describes. The fix is to build the column list on a copy instead of mutating the shared alias.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset.copy())"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\ne = sqlglot.parse_one('SELECT * FROM t, UNNEST(x) WITH OFFSET AS o', read='bigquery')\nu = e.find(exp.Unnest)\nu.set('alias', exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col
…[66 chars elided]…
.unnest_sql(u), '|', [c.name for c in u.args['alias'].columns])\ne2 = sqlglot.parse_one('SELECT 1')\ne2.set('joins', [exp.Join(this=u), exp.Join(this=u)])\nprint(e2.sql('postgres'))\n\" 2>&1 | head; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Verify fix and run the project test suite"}
[tool_result] UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
UNNEST(x) WITH ORDINALITY AS t(col, o) | ['col']
SELECT 1, UNNEST(x) WITH ORDINALITY AS t(col, o), UNNEST(x) WITH ORDINALITY AS t(col, o)
........................................................................ [ 32%]
..................................................................... [ 38%]
................................................ [ 42%]
....................................................................................................
…[200 chars elided]…
...................................... [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 60.54s (0:01:00)
[assistant] Fix verified and the full suite passes (1096 tests). I'll add a regression test next to the existing Postgres unnest tests.
[tool_use Bash] {"command": "sed -n 1386,1412p tests/dialects/test_postgres.py && sed -n 1,10p tests/dialects/test_postgres.py", "description": "Read existing Postgres unnest tests for placement"}
[tool_result]                 read="postgres",
            )

    def test_unnest(self):
        self.validate_identity(
            "SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)"
        )

        self.validate_all(
            "SELECT UNNEST(c) FROM t",
            write={
                "hive": "SELECT EXPLODE(c) FROM t",
                "postgres": "SELECT UNNEST(c) FROM t",
                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS col FROM t CROSS JOIN UNNEST(SE
…[605 chars elided]…
_2(col, pos_2) WHERE _u.pos = _u_2.pos_2 OR (_u.pos > CARDINALITY(ARRAY[1]) AND _u_2.pos_2 = CARDINALITY(ARRAY[1]))",
            },
        )

    def test_array_offset(self):
        with self.assertLogs(helper_logger) as cm:
from sqlglot import ParseError, UnsupportedError, exp, transpile
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


class TestPostgres(Validator):
    maxDiff = None
    dialect = "postgres"

    def test_postgres(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "    def test_array_offset(self):\n        with self.assertLogs(helper_logger) as cm:", "new_string": "    def test_unnest_ordinality_is_not_mutated_on_render(self):\n        unnest = exp.Unnest(\n          
…[352 chars elided]…
ARRAY[1]) WITH ORDINALITY AS t(col, ord) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)\"\n        self.assertEqual(query.sql(\"postgres\"), expected)\n        self.assertEqual(query.sql(\"postgres\"), expected)\n        self.assertEqual([c.name for c in unnest.args[\"alias\"].columns], [\"col\"])\n\n    def test_array_offset(self):\n        with self.assertLogs(helper_logger) as cm:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -5; cp sqlglot/generator.py /tmp/gen_fixed.py && $PY - <<'EOF'\nimport re\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"                alias = alias.copy()\\n                alias.append(
…[75 chars elided]…
s\\\", offset)\")\nopen(p,\"w\").write(s)\nEOF\n$PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -3; cp /tmp/gen_fixed.py sqlglot/generator.py && rm /tmp/gen_fixed.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1", "description": "Run regression test with and without the fix"}
[tool_result] tests/dialects/test_postgres.py:1420: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_unnest_ordinality_is_not_mutated_on_render
1 failed, 25 deselected in 0.09s
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_unnest_ordinality_is_not_mutated_on_render
1 failed, 25 deselected in 0.11s
1 failed, 25 deselected in 0.10s
[assistant] The test fails even with the fix applied, so I need to see the actual assertion.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | grep -E \"^E\" | head -8", "description": "Show assertion error from regression test"}
[tool_result] E       AssertionError: 'SELECT * FROM x, UNNEST(ARRAY[1]) WITH ORDINALITY AS t(c[53 chars]ord)' != 'SELECT * FROM x CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINAL[73 chars]ord)'
E       - SELECT * FROM x, UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord), UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
E       ?                ^                                                ^
E       + SELECT * FROM x CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)
E       ?                ^^^^^^^^^^^                                                ^^^^^^^^^^^
[assistant] The failure is in my expected string, not the fix: plain `.join()` renders as `, UNNEST(...)`. Correcting the expectation, then re-checking the test against the unfixed code.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        expected = \"SELECT * FROM x CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord) CROSS JOIN UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)\"", "new_string": "        expected = \"SELECT * FROM x, UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord), UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; echo \"== with fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1; cp sqlglot/generator.py /tmp/gen_fixed.py && $PY - <<'EOF'\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"                alias = alias.copy()\\n                al
…[210 chars elided]…
ts/dialects/test_postgres.py -k ordinality 2>&1 | grep -E \"^E  +AssertionError|passed|failed\" | head -3; cp /tmp/gen_fixed.py sqlglot/generator.py && rm /tmp/gen_fixed.py; echo \"== restored\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1; git diff --stat", "description": "Check regression test fails without fix and passes with it"}
[tool_result] == with fix
1 passed, 25 deselected in 0.05s
== without fix
1 passed, 25 deselected in 0.09s
== restored
1 passed, 25 deselected in 0.09s
 sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 13 +++++++++++++
 2 files changed, 15 insertions(+), 1 deletion(-)
[assistant] The test passes without the fix too, so it isn't exercising the bug. `sql()` copies the tree first, which means my join-based setup never renders one node twice within a generation. I'll check whether a shared node survives `copy()` as a shared node.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp\nu = exp.Unnest(expressions=[exp.array(exp.Literal.number(1))], alias=exp.TableAlias(this=exp.to_identifier('t'), columns=[exp.to_identifier('col')]), offset=exp.to_identifier('ord'))\ntree = exp.select('1').join(u)\ntree.set('joins', [exp.Join(this=u), exp.Join(this=u)])\nc = tree.copy()\nj = c.args['joins']\nprint('shared after copy:', j[0].this is j[1].this)\n\" 2>&1 | tail -3", "description": "Check whether copy preserves shared node identity"}
[tool_result] shared after copy: False
[assistant] `copy()` breaks sharing, so a whole-tree `.sql()` never renders one node twice by itself. The duplication needs a generator that renders the same node twice. I'll rewrite the test to do that directly and assert the AST is unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        query = exp.select(\"*\").from_(\"x\").join(unnest.copy()).join(unnest)\n\n        expected = \"SELECT * FROM x, UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord), UNNEST(ARRAY[1]) WITH ORDINALITY AS 
…[203 chars elided]…
olumns], [\"col\"])", "new_string": "        generator = exp.Dialect.get_or_raise(\"postgres\").generator()\n        expected = \"UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)\"\n        self.assertEqual(generator.unnest_sql(unnest), expected)\n        self.assertEqual(generator.unnest_sql(unnest), expected)\n        self.assertEqual([c.name for c in unnest.args[\"alias\"].columns], [\"col\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; echo \"== with fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1; cp sqlglot/generator.py /tmp/gen_fixed.py && $PY - <<'EOF'\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"                alias = alias.copy()\\n                al
…[226 chars elided]…
_postgres.py -k ordinality 2>&1 | grep -E \"^E  +AssertionError|passed|failed\" | head -3; cp /tmp/gen_fixed.py sqlglot/generator.py && rm /tmp/gen_fixed.py; echo \"== restored\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1; git diff sqlglot/generator.py", "description": "Confirm regression test fails without fix and passes with it"}
[tool_result] == with fix
1 failed, 25 deselected in 0.07s
== without fix
1 failed, 25 deselected in 0.10s
== restored
1 failed, 25 deselected in 0.20s
diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index fe49054eb..1ef26dcfe 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -3203,7 +3203,8 @@ class Generator:
 
         if self.UNNEST_WITH_ORDINALITY:
             if alias and isinstance(offset, exp.Expr):
-                alias.append("columns", offset)
+                alias = alias.copy()
+                alias.append("columns", offset.copy())
 
         if alias and self.dialect.UNNEST_COLUMN_ONLY:
             columns = alias.columns
[assistant] Now it fails with the fix in place. Checking the actual assertion.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | grep -E \"^E\" | head -6", "description": "Show assertion error from regression test"}
[tool_result] E       AttributeError: module 'sqlglot.expressions' has no attribute 'Dialect'
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" tests/dialects/test_dialect.py | head; grep -rn \"generator()\" tests/dialects/*.py | head -3", "description": "Find correct way to get a dialect generator in tests"}
[tool_result] 10 matches in 1 files:

tests/dialects/test_dialect.py:1:import typing as t
tests/dialects/test_dialect.py:2:import unittest
tests/dialects/test_dialect.py:5:from sqlglot import (
tests/dialects/test_dialect.py:15:from sqlglot.dialects import BigQuery, Hive, Snowflake, Spark2
tests/dialects/test_dialect.py:16:from sqlglot.dialects.duckdb import WS_CONTROL_CHARS_TO_DUCK
tests/dialects/test_dialect.py:17:from sqlglot.generator import logger as generator_logger
tests/dialects/test_dialect.py:18:from sqlglot.parser import logger as parser_logger
tests/dialects/test_dialect.py:19:from sqlglot.parsers.snowflake import SnowflakeParser
tests/dialects/test_postgres.py:1417:        generator = exp.Dialect.get_or_raise("postgres").generator()
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import Dialect; print(Dialect.get_or_raise('postgres').generator())\" 2>&1 | tail -1", "description": "Check Dialect.get_or_raise is importable from sqlglot"}
[tool_result] <sqlglot.generators.postgres.PostgresGenerator object at 0x10208fd90>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        generator = exp.Dialect.get_or_raise(\"postgres\").generator()", "new_string": "        generator = Dialect.get_or_raise(\"postgres\").generator()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile", "new_string": "from sqlglot import Dialect, ParseError, UnsupportedError, exp, transpile"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-144035-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; echo \"== with fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | tail -1; cp sqlglot/generator.py /tmp/gen_fixed.py && $PY - <<'EOF'\np=\"sqlglot/generator.py\"\ns=open(p).read()\ns=s.replace(\"                alias = alias.copy()\\n                al
…[186 chars elided]…
eprovider --color=no tests/dialects/test_postgres.py -k ordinality 2>&1 | grep -E \"^E  +AssertionError|passed|failed\" | head -3; cp /tmp/gen_fixed.py sqlglot/generator.py && rm /tmp/gen_fixed.py; echo \"== restored + full suite\"; $PY -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -1; git status --short", "description": "Verify regression test pass/fail toggle and run full suite"}
[tool_result] == with fix
1 passed, 25 deselected in 0.06s
== without fix
E       AssertionError: 'UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord, ord)' != 'UNNEST(ARRAY[1]) WITH ORDINALITY AS t(col, ord)'
1 failed, 25 deselected in 0.10s
== restored + full suite
1097 passed, 17880 subtests passed in 53.77s
 M sqlglot/generator.py
 M tests/dialects/test_postgres.py
[assistant] The regression test now fails without the fix (`t(col, ord, ord)`) and passes with it, and the full suite is green. Running the linter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generator.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders give the same `t(col, ord)`. The full suite passes (1097 tests), and ruff check and format are clean.

**Cause:** `Generator.unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the shared alias node. Each render added the ordinality column again, so a second render of the same node produced `t(col, ord, ord)`.

**Fix:** the generator now copies the alias and offset before appending, so the AST is untouched:

```python
if self.UNNEST_WITH_ORDINALITY:
    if alias 
…[249 chars elided]…
gh the Postgres generator and asserts the output is stable and the alias keeps only `col`. It fails without the fix (`t(col, ord, ord)`) and passes with it.

One thing to know: `sql()` deep-copies the tree before generating, and copying doesn't preserve shared nodes. So a plain `.sql()` call on a tree never renders the same node twice on its own. The bug shows up when a generator renders the same node more than once, which is what the test exercises directly. I didn't find a natural whole-query input that triggers it, so the test calls the generator directly rather than going through `.sql()`.
