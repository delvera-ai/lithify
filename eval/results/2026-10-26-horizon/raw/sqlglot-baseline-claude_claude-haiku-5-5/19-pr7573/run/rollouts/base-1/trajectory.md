# trajectory base-1

final message:
Fixed: rendering a Postgres `UNNEST ... WITH ORDINALITY AS t(col, ord)` node more than once now gives the same alias every time.

**Cause:** `unnest_sql` in `sqlglot/generator.py` appended the ordinality column to the node's own alias (`alias.append("columns", offset)`), so each render added another `ord`. The default `.sql()` path copies the tree first, which hides this. It shows up when the same node is rendered with `copy=False`, or appears in several places of one output.

**Change:**
- `sqlglot/generator.py`: the alias is copied before the ordinality column is appended, so the AST is no longer modified.
- `tests/dialects/test_postgres.py`: added a regression check in `test_unnest` that renders the same node twice with `copy=False` and expects the same output both times.

**Verification:**
- Before the fix, the shared node rendered as `t(x, ord, ord)`, then `t(x, ord, ord, ord)`, and grew on each render. After the fix, a `UNION ALL` of the same node renders identically on repeated calls.
- Full suite: 1096 passed. Ruff check and format check are clean on both files.

I did not confirm that the new test fails on the unfixed code. The repro above showed the growth before the fix, so the test targets that case.

## events
[tool_use Bash] {"command": "grep -n \"ORDINALITY\\|ordinality\" sqlglot/dialects/postgres.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -50", "description": "Find ordinality handling in dialect and generator"}
[tool_result] sqlglot/dialects/dialect.py:2357:        # - The position is 0-based whereas WITH ORDINALITY is 1-based
sqlglot/dialects/dialect.py:2358:        # For that matter, we must (1) subtract 1 from the ORDINALITY position and (2) rearrange the columns accordingly, returning:
sqlglot/dialects/dialect.py:2359:        # `FROM x CROSS JOIN LATERAL (SELECT pos - 1 AS pos, col FROM UNNEST(y) WITH ORDINALITY AS t(col, pos))
sqlglot/generator.py:398:    # UNNEST WITH ORDINALITY (presto) instead of UNNEST WITH
…[691 chars elided]…
erator.py:2713:        return f"{self.lateral_op(expression)} {this}{alias}{ordinality}"
sqlglot/generator.py:3204:        if self.UNNEST_WITH_ORDINALITY:
sqlglot/generator.py:3215:        if self.UNNEST_WITH_ORDINALITY:
sqlglot/generator.py:3216:            suffix = f" WITH ORDINALITY{alias}" if offset else alias
sqlglot/generator.py:3612:        ordinality = " FOR ORDINALITY" if expression.args.get("ordinality") else ""
sqlglot/generator.py:3613:        return f"{this}{kind}{path}{ordinality}"
[tool_use Bash] {"command": "sed -n 2300,2340p sqlglot/generator.py && echo ---- && sed -n 3195,3230p sqlglot/generator.py && echo ---- && sed -n 2340,2400p sqlglot/dialects/dialect.py && echo ---- && grep -n \"UNNEST\\|Unnest\\|unnest\" sqlglot/dialects/postgres.py", "description": "Read unnest generation code"}
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
     
…[4015 chars elided]…
, expression: exp.DatetimeDiff | exp.TimestampDiff) -> str:
    return self.func("TIMESTAMPDIFF", expression.unit, expression.expression, expression.this)


def no_make_interval_sql(self: Generator, expression: exp.MakeInterval, sep: str = ", ") -> str:
    args = []
    for unit, value in expression.args.items():
        if isinstance(value, exp.Kwarg):
            value = value.expression

        args.append(f"{value} {unit}")

    return f"INTERVAL '{self.format_args(*args, sep=sep)}'"

----
[assistant] The mutation is visible at `generator.py:3204-3205`: `alias.append("columns", offset)` writes into the shared AST on every render. Let me reproduce it before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres')\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\nu = e.find(exp.Unnest)\nprint(u.args['alias'].columns, u.args.get('offset'))\ne2 = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres')\nprint(e2.sql('postgres'), e2.sql('postgres'))\nprint(e2.sql('postgres', pretty=True) == e2.sql('postgres', pretty=True))\n\" 2>&1", "description": "Reproduce repeated-render alias duplication"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
[Identifier(this=x, quoted=False)] ord
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord) SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
True
[assistant] No mutation shows up on the plain path, which suggests `generate()` copies the tree by default. I'll check that and try the case from the report: the same Unnest node used in more than one place with `copy=False`.
[tool_use Bash] {"command": "grep -n \"copy\" sqlglot/generator.py | head -20 && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\nu = sqlglot.parse_one('UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres
…[253 chars elided]…
n(exp.select('*').from_(u))\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres')\nf = e.find(exp.Unnest)\ns = exp.select('*').from_(f).union(exp.select('*').from_(f))\nprint(s.sql('postgres'))\nprint(s.sql('postgres'))\nprint(s.sql('postgres', copy=False) if False else '')\n\" 2>&1", "description": "Check copy behavior and shared-node rendering"}
[tool_result ERROR] Exit code 1
487:    SUPPORTED_JSON_PATH_PARTS: t.ClassVar = ALL_JSON_PATH_PARTS.copy()
904:    def generate(self, expression: exp.Expr, copy: bool = True) -> str:
910:            copy: Whether to copy the expression. The generator performs mutations so
911:                it is safer to copy.
916:        if copy:
917:            expression = expression.copy()
1470:        keyword = "COPY" if expression.args.get("copy") and self.SUPPORTS_TABLE_COPY else "CLONE"
1774:                    exp.subque
…[2261 chars elided]…
b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/sqlglot/parser.py", line 2124, in _parse_batch_statements
    self.raise_error("Invalid expression / Unexpected token")
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/sqlglot/parser.py", line 1991, in raise_error
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 1, Col: 23.
  UNNEST(ARRAY[1,2]) [4mWITH[0m ORDINALITY AS t(x, ord)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres')\nf = e.find(exp.Unnest)\nprint('off
…[50 chars elided]…
].columns)\ngen = Postgres().generator()\nprint(gen.generate(f, copy=False)); print(gen.generate(f, copy=False))\nprint('after', f.args['alias'].columns)\ns = exp.select('*').from_(f).union(exp.select('*').from_(f), distinct=False, copy=False)\nprint(s.sql('postgres', copy=False))\nprint(s.sql('postgres', copy=False))\n\" 2>&1", "description": "Test repeated render with copy=False on shared node"}
[tool_result] offset ord cols [Identifier(this=x, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord, ord)
after [Identifier(this=x, quoted=False), Identifier(this=ord, quoted=False), Identifier(this=ord, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord, ord, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord, ord, ord, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord, ord, ord, ord, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord, ord, ord, ord, ord, ord)
[assistant] Reproduced with `copy=False`: each render appends another `ord` to the shared alias, so the AST changes between renders. The default `generate()` copies the tree, which is why the plain call hid it. The fix is to append to a copy of the alias instead of the original.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll add a regression test next to the existing Postgres UNNEST tests.
[tool_use Bash] {"command": "grep -n \"ORDINALITY\" tests/dialects/test_postgres.py | head; grep -n \"def test_\" tests/dialects/test_postgres.py | head -5; sed -n 1,12p tests/dialects/test_postgres.py", "description": "Locate existing ordinality tests in postgres suite"}
[tool_result] 108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
141:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
1399:                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS co
…[902 chars elided]…
(self):
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
[tool_use Bash] {"command": "sed -n 1389,1411p tests/dialects/test_postgres.py", "description": "Read existing test_unnest in postgres tests"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "            },\n        )\n\n    def test_array_offset(self):", "new_string": "            },\n        )\n\n        # Rendering the same UNNEST node repeatedly must not mutate its alias\n        unnest = se
…[30 chars elided]…
ELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)\"\n        ).find(exp.Unnest)\n        generator = self.dialect.generator()\n        expected = \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)\"\n        self.assertEqual(generator.generate(unnest, copy=False), expected)\n        self.assertEqual(generator.generate(unnest, copy=False), expected)\n\n    def test_array_offset(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] The test uses `self.dialect`, which is a string in `Validator`, so calling `.generator()` on it won't work. I'll switch to `.sql(..., copy=False)` and run the test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        unnest = self.parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)\"\n        ).find(exp.Unnest)\n        generator = self.dialect.generator()\n        expected =
…[186 chars elided]…
y=False), expected)", "new_string": "        unnest = self.parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)\"\n        ).find(exp.Unnest)\n        expected = \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)\"\n        self.assertEqual(unnest.sql(self.dialect, copy=False), expected)\n        self.assertEqual(unnest.sql(self.dialect, copy=False), expected)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-143615-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k unnest 2>&1 | tail -5; git stash list >/dev/null; git diff --stat; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k unnest 2>&1 | tail -1 >/dev/null; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run postgres unnest tests and full suite"}
[tool_result] ..                                                                [100%]
2 passed, 23 deselected, 7 subtests passed in 0.16s
 sqlglot/generator.py            | 1 +
 tests/dialects/test_postgres.py | 8 ++++++++
 2 files changed, 9 insertions(+)
........................................................................ [ 32%]
..................................................................... [ 38%]
................................................ [ 42%]
...........................................
…[247 chars elided]…
[ 66%]
......................................... [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 54.06s
[assistant] The full suite passes (1096 tests). Last, I'll run the linter and formatter on the two changed files, then confirm the fix with the repro from before.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/generator.py tests/dialects/test_postgres.py && $PY -m ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(x, ord)', read='postgres')\nf = e.find(exp.Unnest)\ns = exp.select('*').from_(f).union(exp.select('*').from_(f), distinct=False, copy=False)\nprint(s.sql('postgres', copy=False)); print(s.sql('postgres', copy=False))\n\"", "description": "Lint, format-check, and re-run repro"}
[tool_result] All checks passed!
2 files already formatted
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(x, ord)
[assistant] Fixed: rendering a Postgres `UNNEST ... WITH ORDINALITY AS t(col, ord)` node more than once now gives the same alias every time.

**Cause:** `unnest_sql` in `sqlglot/generator.py` appended the ordinality column to the node's own alias (`alias.append("columns", offset)`), so each render added another `ord`. The default `.sql()` path copies the tree first, which hides this. It shows up when the same node is rendered with `copy=False`, or appears in several places of one output.

**Change:**
- `sqlglot/generator.py`: the alias is copied before the ordinality column is appended, so the AST is no l
…[31 chars elided]…
ts/test_postgres.py`: added a regression check in `test_unnest` that renders the same node twice with `copy=False` and expects the same output both times.

**Verification:**
- Before the fix, the shared node rendered as `t(x, ord, ord)`, then `t(x, ord, ord, ord)`, and grew on each render. After the fix, a `UNION ALL` of the same node renders identically on repeated calls.
- Full suite: 1096 passed. Ruff check and format check are clean on both files.

I did not confirm that the new test fails on the unfixed code. The repro above showed the growth before the fix, so the test targets that case.
