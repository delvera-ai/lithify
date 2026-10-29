# trajectory base-1

final message:
Fixed: rendering an `UNNEST ... WITH ORDINALITY AS t(col, ord)` node repeatedly no longer adds another `ord` column to the alias. The full suite passes (1096 tests), and ruff is clean.

**Cause:** `Generator.unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the AST's own alias node. Each render appended the ordinality column again. The default `copy=True` hid this, but `copy=False`, or any path that renders the same node more than once, exposed it. Before the fix, three renders with `copy=False` gave `t(col, ord, ord, ord)`.

**Change:** the generator now appends to a copy of the alias and a copy of the offset, so the AST is never mutated.

**Test:** I added a regression check to `test_postgres` in `tests/dialects/test_postgres.py`. It renders the same parsed node twice with `copy=False` and expects the same output each time. I also added the `parse_one` import that the test needs. I did not weaken any existing assertion.

**Stash mishap:** I ran `git stash push -u` by mistake, which set my edits aside. I restored them with `git stash apply <sha>`, then dropped only my own entry. The tree shows only the two intended files changed.

I did not commit anything. The fix is in the shared generator, so it also applies to every dialect that uses `UNNEST_WITH_ORDINALITY`, not just Postgres.

## events
[tool_use Bash] {"command": "grep -n -i \"ordinality\\|unnest\" sqlglot/dialects/postgres.py | head -50", "description": "Find UNNEST/ordinality references in postgres dialect"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "ls && git status --short | head && grep -rn -i \"ordinality\" sqlglot/ | head -40", "description": "Locate ordinality references in source"}
[tool_result] AGENTS.md
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
sqlglot/tokenizer_core.py:362:    ORDINALITY = auto()
sqlglot/tokens.py:345:        "ORDINALITY": TokenType.ORDINALITY,
sqlglot/generator.py:398:    # UNNEST WITH ORDINALITY (presto) instead of UNNEST WITH OFFSET (bigquery)
sqlglot/generator.py:399:    UNNEST_WITH_ORDINALITY = True
sqlglot/gene
…[2578 chars elided]…
) WITH ORDINALITY AS s(h, pos)
sqlglot/dialects/dialect.py:2357:        # - The position is 0-based whereas WITH ORDINALITY is 1-based
sqlglot/dialects/dialect.py:2358:        # For that matter, we must (1) subtract 1 from the ORDINALITY position and (2) rearrange the columns accordingly, returning:
sqlglot/dialects/dialect.py:2359:        # `FROM x CROSS JOIN LATERAL (SELECT pos - 1 AS pos, col FROM UNNEST(y) WITH ORDINALITY AS t(col, pos))
sqlglot/generators/exasol.py:702:        "ordinality",
[tool_use Bash] {"command": "sed -n 3190,3240p sqlglot/generator.py && echo ---- && grep -n -i \"unnest\" sqlglot/generators/postgres.py sqlglot/dialects/postgres.py", "description": "Read unnest_sql generator and postgres unnest refs"}
[tool_result]         pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        sql = self.query_modifiers(expression, self.wrap(expression), alias, pivots)
        return self.prepend_ctes(expression, sql)

    def qualify_sql(self, expression: exp.Qualify) -> str:
        this = self.indent(self.sql(expression, "this"))
        return f"{self.seg('QUALIFY')}{self.sep()}{this}"

    def unnest_sql(self, expression: exp.Unnest) -> str:
        args = self.expressions(expression, flat=True
…[1538 chars elided]…
:    filter_array_using_unnest,
sqlglot/generators/postgres.py:293:        exp.ArrayFilter: filter_array_using_unnest,
sqlglot/generators/postgres.py:309:        exp.Explode: rename_func("UNNEST"),
sqlglot/generators/postgres.py:421:    def unnest_sql(self, expression: exp.Unnest) -> str:
sqlglot/generators/postgres.py:430:                        .subquery(expression.args.get("alias") or "_unnested_generate_series")
sqlglot/generators/postgres.py:450:        return super().unnest_sql(expression)
[tool_use Bash] {"command": "sed -n 415,452p sqlglot/generators/postgres.py && echo ---- && grep -n \"def append\" -A12 sqlglot/expressions/core.py | head -30 && echo ---- && grep -rn \"UNNEST_COLUMN_ONLY\" sqlglot | head", "description": "Read postgres unnest_sql and Expression.append"}
[tool_result]             param_constraint.pop()  # Remove to prevent double-rendering
            base_sql = super().columndef_sql(expression, sep)
            return f"{mode_sql} {base_sql}"

        return super().columndef_sql(expression, sep)

    def unnest_sql(self, expression: exp.Unnest) -> str:
        if len(expression.expressions) == 1:
            arg = expression.expressions[0]
            if isinstance(arg, exp.GenerateDateArray):
                generate_series: exp.Expr = exp.GenerateSeries(*
…[2552 chars elided]…
nal UNNEST aliases
sqlglot/optimizer/resolver.py:323:        if self.dialect.UNNEST_COLUMN_ONLY:
sqlglot/dialects/dialect.py:331:    UNNEST_COLUMN_ONLY = False
sqlglot/dialects/bigquery.py:25:    UNNEST_COLUMN_ONLY = True
sqlglot/generators/snowflake.py:348:        # `TableAlias` node that only fills `columns` and not `this`, due to `UNNEST_COLUMN_ONLY`.
sqlglot/generators/bigquery.py:57:    # Due to `UNNEST_COLUMN_ONLY`, it is expected that the table alias be contained in the columns expression
[assistant] Let me reproduce the bug before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(sqlglot.exp.Unnest)\nprint(u.args.get('offset'))\nfor _ in range(3): print(e.sql(dialect='postgres'))\nprint(u.args['alias'].sql())\n\" ; echo; ~/.cache/lithif
…[56 chars elided]…
ort sqlglot\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nprint(repr(e.find(sqlglot.exp.Unnest).args.get('offset')))\nprint(sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres').find(sqlglot.exp.Unnest).args.get('offset'))\n\"", "description": "Reproduce duplicate ordinality alias column"}
[tool_result] ord
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
t(col)

Identifier(this=ord, quoted=False)
ord
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nsel = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = sel.find(exp.Unnest)\nq = exp.union(sel, sel, distinct=False)\nprint(q.sql(dialect='postgres'))\nprint(q.sql(dialect='postgres'))\nprint(u.args['alias'].sql())\nprint(q.sql(dialect='postgres', copy=False))\nprint(u.args['alias'].sql())\n\"; grep -n \"def sql\\b\" -A3 sqlglot/expressions/core.py | head; grep -n \"copy\" sqlglot/generator.py | head -20", "description": "Reproduce with shared node and check copy behaviour"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
t(col)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION ALL SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
t(col)
428:    def sql(
429-        self, dialect: DialectType = None, co
…[1334 chars elided]…
gs.get("count")))
3017:            limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))
3132:            subquery = expression.subquery(copy=False)
3134:            sql = self.sql(exp.select(star).from_(subquery, copy=False))
4114:            r.replace(exp.Nullif(this=r.copy(), expression=exp.Literal.number(0)))
4118:                l.replace(exp.cast(l.copy(), to=exp.DType.DOUBLE))
4205:                    like = exp.Escape(this=like, expression=escape.expression.copy())
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.generator import Generator\nsel = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor _ in range(3): print(sel.sql(dialect='postgres', copy=False))\nprint(sel.find(exp.Unnest).args['alias'].sql())\n\"", "description": "Confirm duplication with copy=False rendering"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord)
t(col, ord, ord, ord)
[assistant] Reproduced: with `copy=False` (or any path that re-renders the same node), each render appends another `ord` to the alias. The cause is `unnest_sql` in `generator.py` calling `alias.append(...)` on the AST node. I'll change it to append to a copy.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset.copy())"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nsel = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor _ in range(3): print(sel.sql(dialect='postgres', copy=False))\nprint(sel.find(exp.Unnest).args['alias'].sql())\nprint(sel.sql(dialect='duckdb'), '|', sel.sql(dialect='bigquery'))\n\"", "description": "Verify repeated rendering is stable"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
t(col)
SELECT * FROM UNNEST([1, 2]) WITH ORDINALITY AS t(col, ord) | SELECT * FROM UNNEST([1, 2]) AS col WITH OFFSET AS ord
[assistant] Rendering is now stable and the AST is untouched. Next I'll add a regression test to the Postgres dialect tests and run the suite.
[tool_use Bash] {"command": "grep -n -i \"ordinality\" tests/dialects/test_postgres.py | head; grep -n \"def test_\" tests/dialects/test_postgres.py | tail -3; tail -5 tests/dialects/test_postgres.py", "description": "Find existing ordinality tests in postgres tests"}
[tool_result] 108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
141:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
1399:                "presto": "SELECT IF(_u.pos = _u_2.pos_2, _u_2.col) AS co
…[720 chars elided]…
 FROM (FUNC1(col1) AS alias1("col1" TEXT)) WITH ORDINALITY AS alias3("col3" INT, "col4" TEXT)"""
1771:    def test_begin_transaction(self):
1794:    def test_interval_span(self):
1816:    def test_postgres_create_trigger(self):
            "CREATE TRIGGER proc_trigger BEFORE INSERT ON users FOR EACH ROW EXECUTE FUNCTION LOG_CHANGES()",
        )
        self.validate_identity(
            'CREATE TRIGGER "MyTrigger" BEFORE INSERT ON "MyTable" FOR EACH ROW EXECUTE FUNCTION MYFUNCTION()'
        )
[tool_use Bash] {"command": "sed -n 130,145p tests/dialects/test_postgres.py", "description": "Read tests near existing ordinality identities"}
[tool_result]         )
        self.validate_identity(
            """ALTER TABLE ONLY "Album" ADD CONSTRAINT "FK_AlbumArtistId" FOREIGN KEY ("ArtistId") REFERENCES "Artist" ("ArtistId") ON DELETE RESTRICT"""
        )
        self.validate_identity(
            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
        )
        self.validate_identity(
            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
        )
        self.validate_identity(
            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
        )
        self.validate_identity(
            "SELECT SUM(x) OVER a, SUM(y) OVER b FROM c WINDOW a AS (PARTITION BY d), b AS (PARTITION BY e)"
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)\"\n        )\n        self.validate_identity(\n            \"SELECT S
…[207 chars elided]…
(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\"\n        )\n        for _ in range(2):\n            self.assertEqual(\n                unnest.sql(\"postgres\", copy=False),\n                \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\",\n            )\n        self.validate_identity(\n            \"SELECT SUM(x) OVER a"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_postgres.py | grep -n import; git stash list | head -0; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Run postgres dialect tests"}
[tool_result] 1:from sqlglot import ParseError, UnsupportedError, exp, transpile
2:from sqlglot.helper import logger as helper_logger
3:from tests.dialects.test_dialect import Validator
head: illegal line count -- 0
            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json"
        )
        self.validate_identity(
            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)"
        )
>       unnest = parse_one(
                 ^^^^^^^^^
            "SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)", read="postgres"
        )
E       NameError: name 'parse_one' is not defined

tests/dialects/test_postgres.py:143: NameError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_postgres - NameErr...
1 failed, 24 passed, 187 subtests passed in 0.18s
[assistant] The test file doesn't import `parse_one`; I'll use `exp.maybe_parse`-free code by calling the module's own `parse_one` import, which is missing, so I'll add it to the existing sqlglot import line.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, parse_one, transpile"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121241-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -3; git stash push -u -m \"verify-fix-check\" >/dev/null 2>&1; echo; git diff --stat HEAD -- sqlglot | tail -1", "description": "Run postgres tests after adding import"}
[tool_result] .........................                              [100%]
25 passed, 378 subtests passed in 0.19s
[assistant] I made a mistake just now: I ran `git stash push` without a real reason, which set my working-tree edits aside. I'll restore them by SHA rather than pop, following the shared-stash rules.
[tool_use Bash] {"command": "git stash list --format='%H %gs' | grep \"verify-fix-check\"; git status --short", "description": "Find my stash entry by tag"}
[tool_result] 98cf47e5a4b070cc8c01e0beb066b80e1cb53b20 On (no branch): verify-fix-check
[tool_use Bash] {"command": "git stash apply 98cf47e5a4b070cc8c01e0beb066b80e1cb53b20 && git status --short && git diff --stat && ref=$(git stash list --format='%H %gs' | grep \"98cf47e5a4b070cc8c01e0beb066b80e1cb53b20\" | head -1 | cut -d' ' -f1); echo \"$ref\"; n=$(git stash list | grep -n \"verify-fix-check\" | cut -d: -f1 | head -1); echo \"index $n\"", "description": "Restore my changes from stash by SHA"}
[tool_result] Not currently on any branch.
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   sqlglot/generator.py
	modified:   tests/dialects/test_postgres.py

no changes added to commit (use "git add" and/or "git commit -a")
 M sqlglot/generator.py
 M tests/dialects/test_postgres.py
 sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 10 +++++++++-
 2 files changed, 11 insertions(+), 2 deletions(-)
98cf47e5a4b070cc8c01e0beb066b80e1cb53b20
index 1
[assistant] Changes are restored. Now I'll drop only my own stash entry (re-found by its SHA) and run the full test suite.
[tool_use Bash] {"command": "cur=$(git stash list --format='%gd %H' | grep \" 98cf47e5a4b070cc8c01e0beb066b80e1cb53b20$\" | cut -d' ' -f1); echo \"dropping $cur\"; [ -n \"$cur\" ] && git stash drop \"$cur\"; git stash list --format='%H %gs' | grep -c 98cf47e5; git diff --stat; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Drop my stash entry and run full test suite"}
[tool_result] dropping stash@{0}
Dropped stash@{0} (98cf47e5a4b070cc8c01e0beb066b80e1cb53b20)
0
 sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 10 +++++++++-
 2 files changed, 11 insertions(+), 2 deletions(-)
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 48.87s
[assistant] Full suite passes. A quick lint check on the two changed files:
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/generator.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git diff", "description": "Lint changed files and show final diff"}
[tool_result] All checks passed!
2 files already formatted
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
 
         if alias and self.
…[721 chars elided]…
       unnest = parse_one(
+            "SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)", read="postgres"
+        )
+        for _ in range(2):
+            self.assertEqual(
+                unnest.sql("postgres", copy=False),
+                "SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)",
+            )
         self.validate_identity(
             "SELECT SUM(x) OVER a, SUM(y) OVER b FROM c WINDOW a AS (PARTITION BY d), b AS (PARTITION BY e)"
         )
[assistant] Fixed: rendering an `UNNEST ... WITH ORDINALITY AS t(col, ord)` node repeatedly no longer adds another `ord` column to the alias. The full suite passes (1096 tests), and ruff is clean.

**Cause:** `Generator.unnest_sql` in `sqlglot/generator.py` called `alias.append("columns", offset)` on the AST's own alias node. Each render appended the ordinality column again. The default `copy=True` hid this, but `copy=False`, or any path that renders the same node more than once, exposed it. Before the fix, three renders with `copy=False` gave `t(col, ord, ord, ord)`.

**Change:** the generator now append
…[135 chars elided]…
` in `tests/dialects/test_postgres.py`. It renders the same parsed node twice with `copy=False` and expects the same output each time. I also added the `parse_one` import that the test needs. I did not weaken any existing assertion.

**Stash mishap:** I ran `git stash push -u` by mistake, which set my edits aside. I restored them with `git stash apply <sha>`, then dropped only my own entry. The tree shows only the two intended files changed.

I did not commit anything. The fix is in the shared generator, so it also applies to every dialect that uses `UNNEST_WITH_ORDINALITY`, not just Postgres.
