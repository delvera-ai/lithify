# trajectory base-1

final message:
Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders produce the same output. The full suite passes (1097 tests), and ruff is clean on the changed files.

**Root cause:** `unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the live AST node. Each render added another copy of the ordinality column. The top-level `.sql()` deep-copies the tree, which hides this in normal use, so it only shows when the generator is run with `copy=False` on the same node. Repeated renders then gave `(x, pos)`, then `(x, pos, pos)`.

**Change:**
- `sqlglot/generator.py`: `unnest_sql` now copies the alias and the offset before appending, so the AST is left untouched.
- `tests/dialects/test_postgres.py`: added `test_unnest_ordinality_render_is_idempotent`. It renders a BigQuery `WITH OFFSET AS pos` node twice with `copy=False` and checks the alias has one column afterwards. It fails without the fix and passes with it.

Choices I made:
- I used a copy at render time rather than changing the parser to store the offset in the alias. That keeps the change to the generator and leaves existing output unchanged.
- I didn't touch the anonymous `_tN` alias counter. It is generator-level state, so with `copy=False` on one generator the name increments (`_t0`, then `_t1`). That is separate from the duplicate-column bug. Say if you want that stabilised too.

## events
[tool_use Bash] {"command": "grep -n -i \"ordinality\\|_unnest\\|unnest\" sqlglot/dialects/postgres.py | head -60", "description": "Find unnest/ordinality handling in postgres dialect"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "pwd; ls; ls sqlglot/dialects | head -50; grep -rn -i \"ordinality\" sqlglot/ | head -40", "description": "List repo layout and search for ordinality"}
[tool_result] ~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1
AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.
…[3050 chars elided]…
,
sqlglot/expressions/query.py:951:        "ordinality": False,
sqlglot/expressions/query.py:1958:        "ordinality": False,
sqlglot/generators/bigquery.py:231:    UNNEST_WITH_ORDINALITY = False
sqlglot/generators/duckdb.py:2015:                UNNEST(CAST(sig -> 'state' AS UBIGINT[])) WITH ORDINALITY AS t(val, pos)
sqlglot/generators/duckdb.py:2031:                     UNNEST(CAST(sig -> 'state' AS UBIGINT[])) WITH ORDINALITY AS s(h, pos)
sqlglot/generators/exasol.py:702:        "ordinality",
[tool_use Bash] {"command": "sed -n 3190,3235p sqlglot/generator.py; echo ----; grep -n \"unnest\" sqlglot/generators/postgres.py sqlglot/dialects/postgres.py", "description": "Read unnest_sql in generator and postgres unnest handling"}
[tool_result]         pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
        return self.prepend_ctes(expression, sql)

    def qualify_sql(self, expression: exp.Qualify) -> str:
        this = self.indent(self.sql(expression, "this"))
        return f"{self.seg('QUALIFY')}{self.sep()}{this}"

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = self.expressions(expression, flat=True
…[1204 chars elided]…
     this = self.sql(expression, "this")
----
sqlglot/generators/postgres.py:15:    filter_array_using_unnest,
sqlglot/generators/postgres.py:293:        exp.ArrayFilter: filter_array_using_unnest,
sqlglot/generators/postgres.py:421:    def unnest_sql(self, expression: exp.Unnest) -> str:
sqlglot/generators/postgres.py:430:                        .subquery(expression.args.get("alias") or "_unnested_generate_series")
sqlglot/generators/postgres.py:450:        return super().unnest_sql(expression)
[tool_use Bash] {"command": "sed -n 415,452p sqlglot/generators/postgres.py", "description": "Read postgres unnest_sql override"}
[tool_result]             param_constraint.pop()  # Remove to prevent double-rendering
            base_sql = super().columndef_sql(expression, sep)
            return f"{mode_sql} {base_sql}"

        return super().columndef_sql(expression, sep)

    def unnest_sql(self, expression: exp.Unnest) -> str:
        if len(expression.expressions) == 1:
            arg = expression.expressions[0]
            if isinstance(arg, exp.GenerateDateArray):
                generate_series: exp.Expr = exp.GenerateSeries(*
…[688 chars elided]…
is.this

                arg_as_json = self.sql(exp.cast(this, exp.DType.JSON))
                alias = self.sql(expression, "alias")
                alias = f" AS {alias}" if alias else ""

                if expression.args.get("offset"):
                    self.unsupported("Unsupported JSON_ARRAY_ELEMENTS with offset")

                return f"JSON_ARRAY_ELEMENTS({arg_as_json}){alias}"

        return super().unnest_sql(expression)

    def bracket_sql(self, expression: exp.Bracket) -> str:
[assistant] Found the root cause: `unnest_sql` in `sqlglot/generator.py` calls `alias.append("columns", offset)` on the live AST node, so every render adds another copy of the ordinality column. I'll reproduce it first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(sqlglot.exp.Unnest)\nprint(u.sql('postgres')); print(u.sql('postgres')); print(u.sql('postgres'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\n\" 2>&1 | tail -20", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(sqlglot.exp.Unnest)\nprint(u.sql('postgres')); print(u.sql('postgres')); print(u.sql('postgres'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\n\" 2>&1 | tail -20", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[assistant] The Postgres-to-Postgres round trip doesn't trigger it, because the parser keeps `ord` in the alias and leaves `offset` as a bool. The mutation only fires when `offset` is an expression, e.g. BigQuery `WITH OFFSET AS pos` transpiled to Postgres. Let me check that path.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS x WITH OFFSET AS pos', read='bigquery')\nu = e.find(sqlglot.exp.Unnest)\nprint(repr(u.args.get('offset')))\nprint(u.sql('postgres')); print(u.sql('postgres')); print(u.sql('postgres'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\n\" 2>&1 | tail -20", "description": "Reproduce with BigQuery offset transpiled to Postgres"}
[tool_result] Identifier(this=pos, quoted=False)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS x WITH OFFSET AS pos', read='bigquery')\nu = e.find(sqlglot.exp.Unnest)\nprint(repr(u.args.get('alias')))\nprint(u.sql('postgres')); print(repr(u.args.get('alias')))\nprint(u.sql('postgres')); print(repr(u.args.get('alias')))\n\" 2>&1 | tail -20; grep -n \"UNNEST_WITH_ORDINALITY\\|UNNEST_COLUMN_ONLY\" -r sqlglot | head", "description": "Inspect alias columns across repeated renders"}
[tool_result] TableAlias(
  columns=[
    Identifier(this=x, quoted=False)])
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
TableAlias(
  columns=[
    Identifier(this=x, quoted=False)])
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
TableAlias(
  columns=[
    Identifier(this=x, quoted=False)])
sqlglot/parser.py:4909:            if self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/generator.py:399:    UNNEST_WITH_ORDINALITY = True
sqlglot/generator.py:1533:        if not alias and not self.dialect.UNNEST_COLU
…[107 chars elided]…
  if alias and self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/generator.py:3215:        if self.UNNEST_WITH_ORDINALITY:
sqlglot/optimizer/resolver.py:163:                if self.dialect.UNNEST_COLUMN_ONLY and isinstance(source_expr, exp.Unnest):
sqlglot/optimizer/resolver.py:319:        # For BigQuery UNNEST_COLUMN_ONLY, build a mapping of original UNNEST aliases
sqlglot/optimizer/resolver.py:323:        if self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/dialects/dialect.py:331:    UNNEST_COLUMN_ONLY = False
[assistant] The top-level `.sql()` deep-copies the tree, so the mutation is hidden on a single render. It should leak when one `Unnest` node object is rendered twice within a single generate call. I'll build that case directly.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS x WITH OFFSET AS pos', read='bigquery')\nu = e.find(exp.Unnest)\ns = exp.select('*').from_(u.copy())\nq = exp.Union(this=s, expression=s.copy())\n# same node object shared in two places\ns2 = exp.select('*').from_(u)\nq2 = exp.Union(this=s2, expression=exp.select('*').from_(u))\nprint(q2.sql('postgres'))\nprint(q2.sql('postgres'))\n\" 2>&1 | tail -20", "description": "Render a shared Unnest node twice in one tree"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos) UNION SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t1(x, pos)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos) UNION SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t1(x, pos)
[assistant] Still no duplicate, which suggests the copy step is breaking the sharing. I'll check whether the mutation is visible when the generator is run with `copy=False` on the same node.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.dialect import Dialect\ne = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS x WITH OFFSET AS pos', read='bigquery')\nu = e.find(exp.Unnest)\ng = Dialect.get_or_raise('postgres').generator()\nprint(g.generate(u, copy=False)); print(repr(u.args['alias'].args.get('columns')))\nprint(g.generate(u, copy=False)); print(repr(u.args['alias'].args.get('columns')))\n\" 2>&1 | tail -20; grep -n \"def generate\" -A30 sqlglot/generator.py | grep -n \"copy\" ", "description": "Render Unnest with copy=False to observe AST mutation"}
[tool_result] UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
[Identifier(this=x, quoted=False), Identifier(this=pos, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t1(x, pos, pos)
[Identifier(this=x, quoted=False), Identifier(this=pos, quoted=False), Identifier(this=pos, quoted=False)]
1:904:    def generate(self, expression: exp.Expr, copy: bool = True) -> str:
7:910-            copy: Whether to copy the expression. The generator performs mutations so
8:911-                it is safer to copy.
13:916-        if copy:
14:917-            expression = expression.copy()
[assistant] Confirmed: the second render produces `(x, pos, pos)`, and the alias name also changed from `_t0` to `_t1`. Let me find where that `_t` counter comes from before editing.
[tool_use Bash] {"command": "grep -n '\"_t\"\\|f\"_t\\|_t{' sqlglot/generator.py sqlglot/generators/postgres.py sqlglot/dialects/dialect.py | head; sed -n 1525,1545p sqlglot/generator.py", "description": "Locate generated _t alias naming logic"}
[tool_result] sqlglot/generator.py:890:        self._next_name = name_sequence("_t")
sqlglot/generators/postgres.py:429:                        .from_(exp.Table(this=generate_series).as_("_t", table=["value"]))
        alias = self.sql(expression, "this")
        columns = self.expressions(expression, key="columns", flat=True)
        columns = f"({columns})" if columns else ""

        if columns and not self.SUPPORTS_TABLE_ALIAS_COLUMNS:
            columns = ""
            self.unsupported("Named columns a
…[27 chars elided]…
lias.")

        if not alias and not self.dialect.UNNEST_COLUMN_ONLY:
            alias = self._next_name()

        return f"{alias}{columns}"

    def bitstring_sql(self, expression: exp.BitString) -> str:
        this = self.sql(expression, "this")
        if self.dialect.BIT_START:
            return f"{self.dialect.BIT_START}{this}{self.dialect.BIT_END}"
        return f"{int(this, 2)}"

    def hexstring_sql(
        self, expression: exp.HexString, binary_function_repr: str | None = None
[assistant] The `_t` counter is generator-level naming for anonymous aliases and is not part of this bug, so I'll leave it alone. The fix is to stop mutating the shared alias and append the offset to a copy at render time. I'll make the edit.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset.copy())"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.dialect import Dialect\ne = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS x WITH OFFSET AS pos', read='bigquery')\nu = e.find(exp.Unnest)\ng = Dialect.get_or_raise('postgres').generator()\nprint(g.generate(u, copy=False)); print(repr(u.args['alias'].args.get('columns')))\nprint(g.generate(u, copy=False)); print(repr(u.args['alias'].args.get('columns')))\nprint(u.sql('postgres'), u.sql('postgres'))\n\" 2>&1 | tail -20", "description": "Verify repeated renders no longer mutate the alias"}
[tool_result] UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
[Identifier(this=x, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t1(x, pos)
[Identifier(this=x, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos) UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(x, pos)
[assistant] The alias is no longer mutated, and repeated renders now give `(x, pos)`. Next I'll add a regression test next to the existing Postgres UNNEST tests.
[tool_use Bash] {"command": "grep -n \"WITH ORDINALITY\\|def test_\" tests/dialects/test_postgres.py | grep -n -B1 \"ORDINALITY\" | head -30; grep -n \"^from\\|^import\" tests/dialects/test_postgres.py", "description": "Find existing ordinality tests in postgres test file"}
[tool_result] 1-10:    def test_postgres(self):
2:108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
3:135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
4:138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
5:141:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
--
7-1389:    def test_unnest(self):
…[618 chars elided]…
)",
--
17-1551:    def test_rows_from(self):
18:1554:            """SELECT * FROM ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT), FUNC2(col2) AS alias2("col2" INT)) WITH ORDINALITY"""
19:1557:            """SELECT * FROM table1, ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT)) WITH ORDINALITY AS alias3("col3" INT, "col4" TEXT)"""
1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
3:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "sed -n 1389,1392p tests/dialects/test_postgres.py; sed -n 1412,1425p tests/dialects/test_postgres.py", "description": "Read the test_unnest method boundaries"}
[tool_result]     def test_unnest(self):
        self.validate_identity(
            "SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)"
        )
        with self.assertLogs(helper_logger) as cm:
            self.validate_all(
                "SELECT col[1]",
                write={
                    "bigquery": "SELECT col[0]",
                    "duckdb": "SELECT col[1]",
                    "hive": "SELECT col[0]",
                    "postgres": "SELECT col[1]",
                    "presto": "SELECT col[1]",
                },
            )

            self.assertEqual(
                cm.output,
[assistant] I'll add a regression test that renders the same node twice with `copy=False`, so the in-place mutation would show up.
[tool_use Bash] {"command": "grep -n \"^from sqlglot\" tests/dialects/test_postgres.py && grep -rn \"get_or_raise(\\\"postgres\\\")\\|Dialect.get_or_raise\" tests/dialects/*.py | head -3", "description": "Check imports and existing generator usage in tests"}
[tool_result] 1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
tests/dialects/test_dialect.py:120:            self.assertIsNotNone(Dialect.get_or_raise(dialect))
tests/dialects/test_dialect.py:132:        self.assertIsInstance(Dialect.get_or_raise(Hive), Hive)
tests/dialects/test_dialect.py:133:        self.assertIsInstance(Dialect.get_or_raise(Hive()), Hive)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "    def test_rows_from(self):", "new_string": "    def test_unnest_ordinality_render_is_idempotent(self):\n        unnest = parse_one(\n            \"SELECT * FROM UNNEST([1, 2]) AS x WITH OFFSET AS pos\", read=\"bigquery\"\n        ).find(exp.Unnest)\n        generator = Dialect.get_or_raise(\"postgres\").generator()\n\n        self.assertIn(\"(x, pos)\", generator.generate(unnest, copy=False))\n        self.assertIn(\"(x, pos)\", generator.generate(unnest, copy=False))\n        self.assertEqual(len(unnest.args[\"alias\"].columns), 1)\n\n    def test_rows_from(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\nfrom sqlglot.helper import logger as helper_logger", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile\nfrom sqlglot.dialects.dialect import Dialect\nfrom sqlglot.helper import logger as helper_logger"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-173806-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll confirm the new test fails without the fix, then run the full suite with the fix in place.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git stash list >/dev/null; git diff -- sqlglot/generator.py > /tmp/unnest_fix.patch; git checkout -- sqlglot/generator.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k idempotent 2>&1 | tail -4; git apply /tmp/unnest_fix.patch && git diff --stat", "description": "Confirm new test fails without fix, then restore fix"}
[tool_result] tests/dialects/test_postgres.py:1559: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_unnest_ordinality_render_is_idempotent
1 failed, 25 deselected in 0.14s
 sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 13 ++++++++++++-
 2 files changed, 14 insertions(+), 2 deletions(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full project test suite with the fix"}
[tool_result] .............................. [ 59%]
................................................................................................................ [ 70%]
.... [ 70%]
.................................................. [ 74%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
.........................................................................................                                [100%]
1097 passed, 17880 subtests passed in 50.81s
[assistant] The full suite passes. I'll run the project's formatter/linter on the two changed files, since `make check` includes style.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git status --short", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generator.py
 M tests/dialects/test_postgres.py
[assistant] Fixed: rendering an `UNNEST ... WITH ORDINALITY` node no longer mutates its alias, so repeated renders produce the same output. The full suite passes (1097 tests), and ruff is clean on the changed files.

**Root cause:** `unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the live AST node. Each render added another copy of the ordinality column. The top-level `.sql()` deep-copies the tree, which hides this in normal use, so it only shows when the generator is run with `copy=False` on the same node. Repeated renders then gave `(x, pos)`, then `(x, pos, pos)`.

**
…[223 chars elided]…
It renders a BigQuery `WITH OFFSET AS pos` node twice with `copy=False` and checks the alias has one column afterwards. It fails without the fix and passes with it.

Choices I made:
- I used a copy at render time rather than changing the parser to store the offset in the alias. That keeps the change to the generator and leaves existing output unchanged.
- I didn't touch the anonymous `_tN` alias counter. It is generator-level state, so with `copy=False` on one generator the name increments (`_t0`, then `_t1`). That is separate from the duplicate-column bug. Say if you want that stabilised too.
