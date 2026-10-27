# trajectory base-1

final message:
Fixed. Rendering an `UNNEST ... WITH ORDINALITY` no longer mutates the AST, so repeated renders give the same alias.

**Root cause:** `Generator.unnest_sql` in `sqlglot/generator.py` did `alias.append("columns", offset)` on the shared `TableAlias`. Each render added another `ord` column. Output looked right the first time and got worse on every later render.

**Fix:** one line. The alias is copied before the ordinality column is appended:

```python
if alias and isinstance(offset, exp.Expr):
    alias = alias.copy()
    alias.append("columns", offset)
```

**Test:** I added a regression check to `test_unnest` in `tests/dialects/test_postgres.py`. It renders the same unnest twice with `copy=False` and checks that the output and `alias.sql()` (`t(col)`) stay unchanged. Without the fix it fails with `t(col, ord, ord)`. With the fix it passes.

**Verification:**
- Ruff format and check pass on both files.
- `tests/dialects/test_postgres.py`: 25 passed.
- Full suite, run after the final edit: `SUMMARY: 1096 passed, 17880 subtests passed in 66.61s (0:01:06)`, `EXIT: 0`.

**Scope note:** the duplication only appears when the same unnest node is rendered without copying, such as `copy=False` or the second render of an already-mutated tree. The default `.sql()` path copies the tree first, so a plain `.sql()` call on a fresh parse didn't reproduce it in my probes. The fix covers both cases.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"ordinality\" sqlglot/generators/postgres.py sqlglot/parsers/postgres.py sqlglot/generator.py sqlglot/dialects/postgres.py sqlglot/generators/*.py | head -50; cat .lithify/harness/memory.md 2>/dev/null | head -20", "description": "Search ordinality handling in postgres and generator code"}
[tool_result] sqlglot/generator.py:398:    # UNNEST WITH ORDINALITY (presto) instead of UNNEST WITH OFFSET (bigquery)
sqlglot/generator.py:399:    UNNEST_WITH_ORDINALITY = True
sqlglot/generator.py:2325:        ordinality = expression.args.get("ordinality") or ""
sqlglot/generator.py:2326:        if ordinality:
sqlglot/generator.py:2327:            ordinality = f" WITH ORDINALITY{alias}"
sqlglot/generator.py:2347:        return f"{only}{table}{changes}{partition}{file_format}{pre_alias}{alias}{indexed}{hints}
…[1470 chars elided]…
s.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 tests) takes 60–80 s when it runs alone. The slowest test is
  `tests/test_executor.py::TestExecutor::test_execute_tpcds`; with several pytest runs competing
  for CPU it sits there for minutes and looks hung, but it is only slow. Run the dialect's own
  test file first (well under a second), then the full suite once.
[tool_use Bash] {"command": "sed -n 3190,3235p sqlglot/generator.py; echo ----; grep -n -i \"unnest\" sqlglot/generators/postgres.py sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py | head -40", "description": "Read unnest generation code and postgres unnest references"}
[tool_result]         pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
        return self.prepend_ctes(expression, sql)

    def qualify_sql(self, expression: exp.Qualify) -> str:
        this = self.indent(self.sql(expression, "this"))
        return f"{self.seg('QUALIFY')}{self.sep()}{this}"

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = self.expressions(expression, flat=True
…[1360 chars elided]…
:    filter_array_using_unnest,
sqlglot/generators/postgres.py:293:        exp.ArrayFilter: filter_array_using_unnest,
sqlglot/generators/postgres.py:309:        exp.Explode: rename_func("UNNEST"),
sqlglot/generators/postgres.py:421:    def unnest_sql(self, expression: exp.Unnest) -> str:
sqlglot/generators/postgres.py:430:                        .subquery(expression.args.get("alias") or "_unnested_generate_series")
sqlglot/generators/postgres.py:450:        return super().unnest_sql(expression)
[tool_use Bash] {"command": "sed -n 415,452p sqlglot/generators/postgres.py; echo ----; cat > /tmp/repro_unnest.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nsql = \"SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)\"\ntree = sqlglot.parse_one(sql, read=\"postgres\")\nu = tree.find(exp.Unnest)\nprint(repr(u.args.get(\"offset\")))\nprint(tree.sql(\"postgres\"))\nprint(tree.sql(\"postgres\"))\n
…[3 chars elided]…
nt(tree.sql(\"postgres\"))\nprint(u.args[\"alias\"].sql(\"postgres\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro_unnest.py').read())\"", "description": "Read postgres unnest override and reproduce the duplicate alias"}
[tool_result]             param_constraint.pop()  # Remove to prevent double-rendering
            base_sql = super().columndef_sql(expression, sep)
            return f"{mode_sql} {base_sql}"

        return super().columndef_sql(expression, sep)

    def unnest_sql(self, expression: exp.Unnest) -> str:
        if len(expression.expressions) == 1:
            arg = expression.expressions[0]
            if isinstance(arg, exp.GenerateDateArray):
                generate_series: exp.Expr = exp.GenerateSeries(*
…[930 chars elided]…
                   self.unsupported("Unsupported JSON_ARRAY_ELEMENTS with offset")

                return f"JSON_ARRAY_ELEMENTS({arg_as_json}){alias}"

        return super().unnest_sql(expression)

    def bracket_sql(self, expression: exp.Bracket) -> str:
----
Identifier(this=ord, quoted=False)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
t(col)
[tool_use Bash] {"command": "cat > /tmp/repro2.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nsql = \"SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)\"\ntree = sqlglot.parse_one(sql, read=\"postgres\")\nu = tree.find(exp.Unnest)\nprint(repr(u.args[\"alias\"]))\nprint(tree.sql(\"postgres\"))\nprint(repr(u.args[\"alias\"]))\n# same node placed in two spots\nu2 = u.copy()\nboth = exp.union(exp.
…[68 chars elided]…
nprint(both.sql(\"postgres\"))\nprint(both.sql(\"postgres\"))\nprint(repr(u.args[\"alias\"]))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro2.py').read())\"", "description": "Probe alias mutation with a shared unnest node"}
[tool_result] TableAlias(
  this=Identifier(this=t, quoted=False),
  columns=[
    Identifier(this=col, quoted=False)])
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
TableAlias(
  this=Identifier(this=t, quoted=False),
  columns=[
    Identifier(this=col, quoted=False)])
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
TableAlias(
  this=Identifier(this=t, quoted=False),
  columns=[
    Identifier(this=col, quoted=False)])
[tool_use Bash] {"command": "cat > /tmp/repro3.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\ntree = sqlglot.parse_one(\"SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\")\nu = tree.find(exp.Unnest)\nprint(\"offset:\", repr(u.args.get(\"offset\")))\nfor i in range(3):\n    print(Postgres().generate(u, copy=False))\n    print(
…[219 chars elided]…
"*\").from_(shared), distinct=False)\nprint(both.sql(\"postgres\"))\nprint(both.sql(\"postgres\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro3.py').read())\"", "description": "Probe mutation with copy=False generation"}
[tool_result] offset: Identifier(this=ord, quoted=False)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
alias after: t(col, ord) 2
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord)
alias after: t(col, ord, ord) 3
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord)
alias after: t(col, ord, ord, ord) 4
--- copy=True path, shared node in two spots
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord, ord)
[assistant] Reproduced: with `copy=False`, each render appends another `ord` to the shared `TableAlias`. The cause is `alias.append("columns", offset)` in `Generator.unnest_sql`, which mutates the AST. I'll make that path work on a copy, then look for an existing test to extend.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "grep -n -i \"ordinality\" tests/dialects/test_postgres.py | head; grep -n \"def test_\" tests/dialects/test_postgres.py | head -3; <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/repro3.py').read())\"", "description": "Check existing postgres ordinality tests and rerun repro"}
[tool_result] 108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
141:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
1399:                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS co
…[996 chars elided]…
l, ord)
alias after: t(col) 1
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
alias after: t(col) 1
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
alias after: t(col) 1
--- copy=True path, shared node in two spots
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[assistant] The fix holds: repeated renders are stable and the AST alias is untouched. Next I'll add a regression test to the Postgres dialect tests, next to the existing unnest test.
[tool_use Bash] {"command": "sed -n 1385,1392p tests/dialects/test_postgres.py; sed -n 1,9p tests/dialects/test_postgres.py", "description": "Read unnest test header in postgres tests"}
[tool_result]                 "CREATE TABLE products (price DECIMAL, CHECK price > 1)",
                read="postgres",
            )

    def test_unnest(self):
        self.validate_identity(
            "SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)"
        )
from sqlglot import ParseError, UnsupportedError, exp, transpile
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


class TestPostgres(Validator):
    maxDiff = None
    dialect = "postgres"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "    def test_unnest(self):\n        self.validate_identity(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2], ARRAY['foo', 'bar', 'baz']) AS x(a, b)\"\n        )", "new_string": "    def test_unnest(self):\n
…[164 chars elided]…
n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\"\n        ).find(exp.Unnest)\n        for _ in range(2):\n            self.assertEqual(\n                unnest.sql(\"postgres\"),\n                \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\",\n            )\n        self.assertEqual(unnest.args[\"alias\"].sql(\"postgres\"), \"t(col)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] The `parse_one` import is missing. Also, `unnest.sql()` deep-copies the tree by default, so this test would pass even without the fix. The regression case needs a shared node in two places, which is what the union reproduction showed. I'll rewrite the test around that.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        unnest = parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\"\n        ).find(exp.Unnest)\n        for _ in range(2):\n            self.ass
…[605 chars elided]…
t(\"*\").from_(unnest), distinct=False)\n        for _ in range(2):\n            self.assertEqual(\n                shared.sql(\"postgres\"),\n                \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\",\n            )\n        self.assertEqual(unnest.args[\"alias\"].sql(\"postgres\"), \"t(col)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] I left an unused `union` variable in there. Removing it and adding the import:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        union = exp.union(\n            exp.select(\"*\").from_(unnest), exp.select(\"*\").from_(unnest.copy()), distinct=False\n        )\n        shared = exp.union(exp.select(\"*\").from_(unnest), exp.se
…[284 chars elided]…
LITY AS t(col, ord)\",\n            )", "new_string": "        shared = exp.union(\n            exp.select(\"*\").from_(unnest), exp.select(\"*\").from_(unnest), distinct=False\n        )\n        expected = \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\"\n        for _ in range(2):\n            self.assertEqual(shared.sql(\"postgres\"), f\"{expected} UNION ALL {expected}\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll confirm the new test actually fails without the fix. I'll drop the copy line temporarily, run the test, and restore it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; sed -i '' '/^                alias = alias.copy()$/d' sqlglot/generator.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py::TestPostgres::test_unnest 2>&1 | tail -4; sed -i '' 's/^                alias.append(\"columns\", offset)$/                alias = alias.copy()\\n                alias.append(\"columns\", offset)/' sqlglot/generator.py && grep -n -A1 \"if alias and isinstance(offset, exp.Expr)\" sqlglot/generator.py && git diff --stat", "description": "Confirm new test fails without fix, then restore fix"}
[tool_result] .                                                                  [100%]
1 passed, 6 subtests passed in 0.16s
3205:            if alias and isinstance(offset, exp.Expr):
3206-                alias = alias.copy()
 sqlglot/generator.py            |  1 +
 tests/dialects/test_postgres.py | 13 ++++++++++++-
 2 files changed, 13 insertions(+), 1 deletion(-)
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The test passes even without the fix, so it doesn't yet guard against the bug. In `repro2` a fresh tree rendered with `copy=True` came out correct, and only the `copy=False` path or an already-mutated node duplicated. I need a `.sql()`-level trigger. I'll monkeypatch the old behaviour into a script rather than editing the file, and compare several shapes.
[tool_use Bash] {"command": "cat > /tmp/repro4.py <<'EOF'\nimport sys\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.generator import Generator\n\ndef old_unnest_sql(self, expression):\n    args = self.expressions(expression, flat=True)\n    alias = expression.args.get(\"alias\")\n    offset = expression.args.get(\"offset\")\n    if self.UNNEST_WITH_ORDINALITY:\n        if alias and isinstance(offset, exp
…[1737 chars elided]…
9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python\necho \"== OLD\"; $PY -I -c \"import sys; sys.argv=['x','old']; sys.path.insert(0,'.'); exec(open('/tmp/repro4.py').read())\"\necho \"== NEW\"; $PY -I -c \"import sys; sys.argv=['x','new']; sys.path.insert(0,'.'); exec(open('/tmp/repro4.py').read())\"", "description": "Compare old vs fixed unnest rendering across shared-node shapes"}
[tool_result] == OLD
A SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
B SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) JOIN UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) ON TRUE
C [1, 1, 1]
D [2, 2, 2]
E SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) JOIN (SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)) AS x ON TRUE
== NEW
A SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
B SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) JOIN UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) ON TRUE
C [1, 1, 1]
D [2, 2, 2]
E SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) JOIN (SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)) AS x ON TRUE
[assistant] Under the old code, `.sql()` with the default `copy=True` never duplicates. The builders (`from_`, `union`) copy their inputs, and the top-level generate copies the tree, so the shared node doesn't survive into the render. The bug is real but needs a render that doesn't copy, and the core requirement is that rendering must not mutate the AST. I'll check whether `Expression.sql` takes `copy` so the test can exercise that path.
[tool_use Bash] {"command": "grep -n \"def sql(\" -A3 sqlglot/expressions/core.py sqlglot/expressions/*.py 2>/dev/null | head -12; grep -n \"def generate\" -A8 sqlglot/dialects/dialect.py | head -20; grep -n \"^from\\|^import\" tests/dialects/test_postgres.py tests/dialects/test_dialect.py | head", "description": "Check Expression.sql and Dialect.generate copy parameters"}
[tool_result] sqlglot/expressions/core.py:428:    def sql(
sqlglot/expressions/core.py-429-        self, dialect: DialectType = None, copy: bool = True, **opts: Unpack[GeneratorNoDialectArgs]
sqlglot/expressions/core.py-430-    ) -> str:
sqlglot/expressions/core.py-431-        """
--
sqlglot/expressions/core.py:1220:    def sql(
sqlglot/expressions/core.py-1221-        self, dialect: DialectType = None, copy: bool = True, **opts: Unpack[GeneratorNoDialectArgs]
sqlglot/expressions/core.py-1222-    ) -> str:
sq
…[1406 chars elided]…
lect.py:1:import typing as t
tests/dialects/test_dialect.py:2:import unittest
tests/dialects/test_dialect.py:5:from sqlglot import (
tests/dialects/test_dialect.py:15:from sqlglot.dialects import BigQuery, Hive, Snowflake, Spark2
tests/dialects/test_dialect.py:16:from sqlglot.dialects.duckdb import WS_CONTROL_CHARS_TO_DUCK
tests/dialects/test_dialect.py:17:from sqlglot.generator import logger as generator_logger
tests/dialects/test_dialect.py:18:from sqlglot.parser import logger as parser_logger
[assistant] `Expression.sql` accepts `copy`, and `transpile` itself renders with `copy=False`, so that is the production path that matters. I'll rewrite the test to render without copying twice and assert the alias stays unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        shared = exp.union(\n            exp.select(\"*\").from_(unnest), exp.select(\"*\").from_(unnest), distinct=False\n        )\n        expected = \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY A
…[117 chars elided]…
ON ALL {expected}\")\n        self.assertEqual(unnest.args[\"alias\"].sql(\"postgres\"), \"t(col)\")", "new_string": "        for _ in range(2):\n            self.assertEqual(\n                unnest.sql(\"postgres\", copy=False),\n                \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\",\n            )\n        self.assertEqual(unnest.args[\"alias\"].sql(\"postgres\"), \"t(col)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-202726-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python\necho \"== with fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py::TestPostgres::test_unnest 2>&1 | tail -2\ncp sqlglot/generator.py /tmp/generator_fixed.py\nsed -i '' '/^                alias = 
…[51 chars elided]…
thout fix\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py::TestPostgres::test_unnest 2>&1 | grep -E \"AssertionError|passed|failed\" | head -4\ncp /tmp/generator_fixed.py sqlglot/generator.py\necho \"== restored\"; grep -c \"alias = alias.copy()\" sqlglot/generator.py; git diff --stat", "description": "Verify regression test fails without fix and passes with it"}
[tool_result] == with fix
.                                                                  [100%]
1 passed, 6 subtests passed in 0.07s
== without fix
E           AssertionError: 'UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord)' != 'UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)'
tests/dialects/test_postgres.py:1398: AssertionError
1 failed in 0.11s
== restored
1
 sqlglot/generator.py            |  1 +
 tests/dialects/test_postgres.py | 12 +++++++++++-
 2 files changed, 12 insertions(+), 1 deletion(-)
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The regression test now fails without the fix (`t(col, ord, ord)`) and passes with it. Next, lint/format the two changed files, then run the dialect file and the full suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py && $PY -m ruff check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -8; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Run ruff checks and the postgres dialect test file"}
[tool_result] ruff 0.15.6
2 files already formatted
All checks passed!
.........................                              [100%]
25 passed, 378 subtests passed in 0.27s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
   3144       00:44 <work>/env-sqlglot/b
  34207 03-00:57:37 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-484d239f44.log
ELAPSED: 243s
SUMMARY: 1096 passed, 17880 subtests passed in 66.61s (0:01:06)
EXIT: 0
[assistant] Fixed. Rendering an `UNNEST ... WITH ORDINALITY` no longer mutates the AST, so repeated renders give the same alias.

**Root cause:** `Generator.unnest_sql` in `sqlglot/generator.py` did `alias.append("columns", offset)` on the shared `TableAlias`. Each render added another `ord` column. Output looked right the first time and got worse on every later render.

**Fix:** one line. The alias is copied before the ordinality column is appended:

```python
if alias and isinstance(offset, exp.Expr):
    alias = alias.copy()
    alias.append("columns", offset)
```

**Test:** I added a regression check 
…[234 chars elided]…
he fix it passes.

**Verification:**
- Ruff format and check pass on both files.
- `tests/dialects/test_postgres.py`: 25 passed.
- Full suite, run after the final edit: `SUMMARY: 1096 passed, 17880 subtests passed in 66.61s (0:01:06)`, `EXIT: 0`.

**Scope note:** the duplication only appears when the same unnest node is rendered without copying, such as `copy=False` or the second render of an already-mutated tree. The default `.sql()` path copies the tree first, so a plain `.sql()` call on a fresh parse didn't reproduce it in my probes. The fix covers both cases.

I haven't committed anything.
