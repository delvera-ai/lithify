# trajectory base-1

final message:
Fixed: rendering an `UNNEST ... WITH ORDINALITY AS t(col, ord)` node repeatedly no longer adds a duplicate `ord` column, and the AST is left unchanged.

**Root cause:** `unnest_sql` in `sqlglot/generator.py` (around line 3204) called `alias.append("columns", offset)` on the shared alias node. Every call appended the offset column again. Calling the generator on the same node three times gave `t(col, ord)`, then `t(col, ord, ord)`, then `t(col, ord, ord, ord)`. `Expr.sql()` deep-copies the tree first, so the bug only shows up when the same node is rendered again without that copy, which is what the issue describes.

**Fix:** the offset is now appended to a copy of the alias (and a copy of the offset), so the original node is never modified:

```python
if self.UNNEST_WITH_ORDINALITY:
    if alias and isinstance(offset, exp.Expr):
        alias = alias.copy()
        alias.append("columns", offset.copy())
```

The change is in the base generator, so it applies to every dialect that uses `unnest_sql`, not only Postgres.

**Test:** I added a regression case to `tests/dialects/test_postgres.py` (in `test_postgres`). It renders one parsed `Unnest` node twice through `generate(copy=False)` and expects the same output both times. It fails on the original code (`t(col, ord, ord)`) and passes with the fix. No existing tests were changed.

**Checks:** the full suite passes (1096 passed, 17880 subtests), and `ruff check` and `ruff format --check` are clean on both files. I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn -i \"ordinality\" sqlglot/dialects/postgres.py sqlglot/generator.py sqlglot/expressions.py sqlglot/parser.py | head -50", "description": "Find ordinality handling in source"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:398:    # UNNEST WITH ORDINALITY (presto) instead of UNNEST WITH OFFSET (bigquery)
sqlglot/generator.py:399:    UNNEST_WITH_ORDINALITY = True
sqlglot/generator.py:2325:        ordinality = expression.args.get("ordinality") or ""
sqlglot/generator.py:2326:        if ordinality:
sqlglot/generator.py:2327:            ordinality = f" WITH ORDINALITY{alias}"
sqlglot/generator.py:2347:        return f"{only}{table}{changes}{p
…[1333 chars elided]…
h_pair(TokenType.WITH, TokenType.ORDINALITY)
sqlglot/parser.py:7048:        if self._match_text_seq("FOR", "ORDINALITY"):
sqlglot/parser.py:7049:            return self.expression(exp.ColumnDef(this=this, ordinality=True))
sqlglot/parser.py:7925:            ordinality = self._match_pair(TokenType.FOR, TokenType.ORDINALITY)
sqlglot/parser.py:7930:            ordinality = None
sqlglot/parser.py:7939:                this=this, kind=kind, path=path, nested_schema=nested_schema, ordinality=ordinality
[tool_use Bash] {"command": "sed -n 2310,2330p sqlglot/generator.py && echo ---- && sed -n 2700,2715p sqlglot/generator.py && echo ---- && sed -n 3195,3225p sqlglot/generator.py && echo ---- && grep -n -i \"unnest\" sqlglot/dialects/postgres.py", "description": "Inspect generator unnest and table code"}
[tool_result ERROR] Exit code 1

        hints = self.expressions(expression, key="hints", sep=" ")
        hints = f" {hints}" if hints and self.TABLE_HINTS else ""
        pivots = self.expressions(expression, key="pivots", sep="", flat=True)
        joins = self.indent(
            self.expressions(expression, key="joins", sep="", flat=True), skip_first=True
        )
        laterals = self.expressions(expression, key="laterals", sep="")

        file_format = self.sql(expression, "format")
        if file_form
…[1718 chars elided]…
else:
            alias = self.sql(alias)

        alias = f" AS {alias}" if alias else alias
        if self.UNNEST_WITH_ORDINALITY:
            suffix = f" WITH ORDINALITY{alias}" if offset else alias
        else:
            if isinstance(offset, exp.Expr):
                suffix = f"{alias} WITH OFFSET AS {self.sql(offset)}"
            elif offset:
                suffix = f"{alias} WITH OFFSET"
            else:
                suffix = alias

        return f"UNNEST({args}){suffix}"
----
[assistant] The `alias.append("columns", offset)` call in `unnest_sql` mutates the shared alias node on every render. Let me confirm with a reproduction before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(exp.Unnest)\nprint(repr(u.args.get('alias')) [:0])\nfor i in range(3):\n    print(e.sql('postgres'))\nprint(e.sql('presto'))\n\" ; grep -n -i \"unnest\" sqlglot/dialects/postgres.py | head; grep -rn \"WITH ORDINALITY\" tests/dialects/test_postgres.py | head", "description": "Reproduce repeated render mutation of unnest alias"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
tests/dialects/test_postgres.py:108:            "SELECT * FROM test_data, LATERAL JSONB_ARRAY_ELEMENTS(data) WITH ORDINALITY AS elem(value, ordinality)"
tests/dialects/test_postgres.py:135:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY"
tests/dialects/test_postgres.py:138:            "SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]
…[693 chars elided]…
IN UNNEST(ARRAY[1]) WITH ORDINALITY AS _u_2(col, pos_2) WHERE _u.pos = _u_2.pos_2 OR (_u.pos > CARDINALITY(ARRAY[1]) AND _u_2.pos_2 = CARDINALITY(ARRAY[1]))",
tests/dialects/test_postgres.py:1554:            """SELECT * FROM ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT), FUNC2(col2) AS alias2("col2" INT)) WITH ORDINALITY"""
tests/dialects/test_postgres.py:1557:            """SELECT * FROM table1, ROWS FROM (FUNC1(col1) AS alias1("col1" TEXT)) WITH ORDINALITY AS alias3("col3" INT, "col4" TEXT)"""
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor i in range(3):\n    print(e.sql('presto'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\n\"", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` also ignores `PYTHONPATH`, so I'll run without it from the repo root, which is trusted source.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.__file__)\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor i in range(3):\n    print(e.sql('presto'))\nprint(e.sql('postgres'))\nprint(e.sql('postgres'))\n\"", "description": "Reproduce duplicate ordinality column on repeated render"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/sqlglot/__init__.py
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[assistant] No duplication on this path, so the trigger must be a different AST shape. Let me inspect the parsed tree and try an offset-bearing source (BigQuery `WITH OFFSET`).
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(exp.Unnest); print(repr(u.args.get('offset')), u.args.get('alias').columns)\ne2 = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS col WITH OFFSET
…[63 chars elided]…
r(u2.args.get('offset')), u2.args.get('alias').columns if u2.args.get('alias') else None)\nfor i in range(3):\n    print(e2.sql('postgres'))\nprint(e2.sql('postgres'))\ne3 = sqlglot.parse_one('SELECT * FROM x CROSS JOIN UNNEST(c) WITH ORDINALITY AS t(col, ord)', read='postgres')\nfor i in range(3): print(e3.sql('postgres'))\n\"", "description": "Inspect unnest AST and test BigQuery offset source"}
[tool_result] Identifier(this=ord, quoted=False) [Identifier(this=col, quoted=False)]
Identifier(this=ord, quoted=False) [Identifier(this=col, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
SELECT * FROM x CROSS JOIN UNNEST(c) WITH ORDINALITY AS t(col, ord)
SELECT * FROM x CROSS JOIN UNNEST(c) WITH ORDINALITY AS t(col, ord)
SELECT * FROM x CROSS JOIN UNNEST(c) WITH ORDINALITY AS t(col, ord)
[assistant] Repeated renders look stable here, so I need to check whether the mutation actually persists on the AST.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(exp.Unnest)\nprint(e.sql('postgres')); print(u.args['alias'].columns, u.args.get('offset'))\nprint(e.sql('postgres')); print(u.args['alias'].columns)\nprint(e.sql('presto')); print(u.args['alias'].columns)\n\"; grep -n \"def append\" -A12 sqlglot/expressions/core.py 2>/dev/null | head -30; ls sqlglot | head -50", "description": "Check whether alias columns mutate across renders"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)] ord
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
257:    def append(self, arg_key: str, value: t.Any) -> None:
258-        """
259-        Appends value to arg_key if it's a list or sets it as a new list.
260-
261-        Args:
262-       
…[617 chars elided]…
 set(
1051-        self,
1052-        arg_key: str,
1053-        value: object,
dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__.py  6.4K
__main__.py  2.1K
_typing.py  1.5K
_version.py  91B
diff.py  16.3K
errors.py  4.7K
generator.py  245.6K
helper.py  11.7K
jsonpath.py  7.8K
lineage.py  17.0K
parser.py  367.1K
planner.py  14.2K
py.typed  0B
schema.py  27.4K
serde.py  3.0K
time.py  18.0K
tokenizer_core.py  34.4K
tokens.py  22.8K
transforms.py  41.0K
trie.py  2.2K
[assistant] The alias isn't growing in this case, so I need to see which generator path actually handles the node. Checking the flag and the BigQuery-sourced tree's alias state after repeated renders.
[tool_use Bash] {"command": "grep -rn \"UNNEST_WITH_ORDINALITY\" sqlglot/ | head; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne2 = sqlglot.parse_one('SELECT * FROM UNNEST([1,2]) AS col WITH OFFSET AS ord', read='bigquery')\nu2 = e2.find(exp.Unnest)\nprint(u2.args['alias'].columns)\nfor i in range(3): print(e2.sql('postgres')); print(u2.args['alias'].columns)\n\"", "description": "Check ordinality flag and BigQuery alias mutation"}
[tool_result] Binary file sqlglot/__pycache__/generator.cpython-312.pyc matches
sqlglot/generator.py:399:    UNNEST_WITH_ORDINALITY = True
sqlglot/generator.py:3204:        if self.UNNEST_WITH_ORDINALITY:
sqlglot/generator.py:3215:        if self.UNNEST_WITH_ORDINALITY:
sqlglot/generators/bigquery.py:231:    UNNEST_WITH_ORDINALITY = False
Binary file sqlglot/generators/__pycache__/bigquery.cpython-312.pyc matches
[Identifier(this=col, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
[Identifier(this=col, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
[Identifier(this=col, quoted=False)]
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS _t0(col, ord)
[Identifier(this=col, quoted=False)]
[assistant] The alias list isn't visibly growing, so I'll inspect the raw `args` and the `columns` property directly.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = e.find(exp.Unnest)\nprint(u.args['alias'].args)\ne.sql('postgres')\nprint(u.args['alias'].args)\nprint(u.args['alias'] is e.find(exp.Unnest).args['alias'])\n\"; grep -n \"class TableAlias\" -A25 sqlglot/expressions/*.py | grep -n \"columns\" ", "description": "Inspect raw alias args before and after render"}
[tool_result] {'this': Identifier(this=t, quoted=False), 'columns': [Identifier(this=col, quoted=False)]}
{'this': Identifier(this=t, quoted=False), 'columns': [Identifier(this=col, quoted=False)]}
True
2:sqlglot/expressions/query.py-468-    arg_types = {"this": False, "columns": False}
5:sqlglot/expressions/query.py-471-    def columns(self) -> list[t.Any]:
6:sqlglot/expressions/query.py-472-        return self.args.get("columns") or []
[assistant] The raw args are unchanged after rendering, so something copies the tree before generating. Checking `generate()` to see whether the mutation is actually reachable, and where the postgres path diverges.
[tool_use Bash] {"command": "grep -n \"copy()\" sqlglot/generator.py | head -20; grep -n \"def generate\" -A30 sqlglot/generator.py | grep -n \"copy\\|preprocess\" ", "description": "Find where generator copies the tree"}
[tool_result] 32 matches in 8 files:

2528:0:exp.union(x, y, distinct=False, copy=False), selects)
487:0:t.ClassVar = ALL_JSON_PATH_PARTS.copy()
5060:0:exp.CopyParameter) -> str:
5108:0:exp.Copy) -> str:
904:0:exp.Expr, copy: bool = True) -> str:
910:0:Whether to copy the expression. The generator performs mutations so
916:0:
sqlglot/generator.py:911:it is safer to copy.
sqlglot/generator.py:917:expression = expression.copy()
sqlglot/generator.py:1470:keyword = "COPY" if expression.args.get("copy") and self.S
…[573 chars elided]…
tor.py:3017:limit = exp.Fetch(direction="FIRST", count=exp.maybe_copy(limit.expression))
sqlglot/generator.py:3132:subquery = expression.subquery(copy=False)
1:904:    def generate(self, expression: exp.Expr, copy: bool = True) -> str:
7:910-            copy: Whether to copy the expression. The generator performs mutations so
8:911-                it is safer to copy.
13:916-        if copy:
14:917-            expression = expression.copy()
16:919-        expression = self.preprocess(expression)
[assistant] `generate()` copies by default, but deep-copy keeps shared nodes shared. So duplication should appear when one `Unnest` object is referenced in two places within a single tree. Let me build that shape.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nq = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = q.find(exp.Unnest)\ns = exp.select('*').from_(u, copy=False).join(u, copy=False)\nfor i in range(2): print(s.sql('postgres'))\nprint(u.args['alias'].columns)\nu.args['alias'].columns\n\" ", "description": "Reproduce duplicate ord with shared unnest node"}
[tool_result] SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord), UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord), UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
[assistant] Join-based sharing didn't reproduce it (the join copies its argument). Let me try a shared subtree under a set operation, and check whether `copy()` preserves sharing at all.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nq = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = q.find(exp.Unnest)\nsel = exp.select('*').from_(u, copy=False)\nun = exp.union(sel, sel, copy=False)\nprint(un.sql('postgres'))\nprint(un.sql('postgres'))\nc = un.copy(); us = list(c.find_all(exp.Unnest)); print(len(us), us[0] is us[1])\nprint(sel.args['from'].this.args['alias'].columns)\n\"", "description": "Test shared subtree under UNION and copy sharing"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 11, in <module>
KeyError: 'from'
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord) UNION SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
2 False
[assistant] `copy()` breaks sharing, so a single `.sql()` pass renders separate copies. The mutation still happens on every `unnest_sql` call, though. Let me demonstrate it directly by calling the generator method repeatedly on one node, which is the "repeated rendering" the issue describes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\nq = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = q.find(exp.Unnest)\ng = Postgres().generator()\nfor i in range(3):\n    print(g.unnest_sql(u)); print(u.args['alias'].columns)\n\"", "description": "Call unnest_sql repeatedly on same node to show mutation"}
[tool_result] UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False), Identifier(this=ord, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord)
[Identifier(this=col, quoted=False), Identifier(this=ord, quoted=False), Identifier(this=ord, quoted=False)]
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord, ord)
[Identifier(this=col, quoted=False), Identifier(this=ord, quoted=False), Identifier(this=ord, quoted=False), Identifier(this=ord, quoted=False)]
[assistant] Confirmed: each `unnest_sql` call appends another `ord` to the shared alias node, so the output grows (`t(col, ord)` → `t(col, ord, ord)` → …). The root cause is `alias.append("columns", offset)` in `unnest_sql` (`sqlglot/generator.py:3204`), which mutates the node in place. The fix is to append to a copy. Let me look at the existing tests for this area before editing.
[tool_use Bash] {"command": "sed -n 130,145p tests/dialects/test_postgres.py && grep -n \"def test_\" tests/dialects/test_postgres.py | head -5 && git status --short", "description": "View existing ordinality tests and git status"}
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
25 matches in 25 files:

10:0:
1073:0:
1389:0:
ok
[assistant] Applying the fix in the base generator, since `unnest_sql` is shared by every dialect. The offset column gets appended to a copy of the alias, so the AST is left untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py", "old_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias.append(\"columns\", offset)", "new_string": "        if self.UNNEST_WITH_ORDINALITY:\n            if alias and isinstance(offset, exp.Expr):\n                alias = alias.copy()\n                alias.append(\"columns\", offset.copy())"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a regression test in the Postgres test file, next to the existing ordinality identities. It renders the same node repeatedly and checks the output stays stable.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM JSON_ARRAY_ELEMENTS('[1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)\"\n        )\n", "new_string": "        self.validate_identity(\n    
…[46 chars elided]…
1,true, [2,false]]') WITH ORDINALITY AS kv_json(a, b)\"\n        )\n        unnest = parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\"\n        ).find(exp.Unnest)\n        for _ in range(2):\n            self.assertEqual(\n                unnest.sql(\"postgres\"), \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\"\n            )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Before running it, one concern: `Expr.sql()` deep-copies the tree by default, so this test could pass on the old code too. I need to check that the test actually fails without the fix. Checking the imports and trying `generate(copy=False)` on the original code.
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_postgres.py && git stash list | head -0; git show HEAD:sqlglot/generator.py > /tmp/gen_orig_check.txt; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.postgres import Postgres\nq = sqlglot.parse_one('SELECT * FROM UNNEST(ARRAY[1,2]) WITH ORDINALITY AS t(col, ord)', read='postgres')\nu = q.find(exp.Unnest)\ng = Postgres().generator()\nfor i in range(3): print(g.generate(u, copy=False))\nprint(u.sql('postgres')); print(u.args['alias'].columns)\n\"", "description": "Check test imports and generate(copy=False) behavior"}
[tool_result] from sqlglot import ParseError, UnsupportedError, exp, transpile
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


class TestPostgres(Validator):
    maxDiff = None
    dialect = "postgres"

    def test_postgres(self):
        expr = self.parse_one("SELECT * FROM r CROSS JOIN LATERAL UNNEST(ARRAY[1]) AS s(location)")
        unnest = expr.args["joins"][0].this.this
head: illegal line count -- 0

thread 'main' (44029662) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)
[Identifier(this=col, quoted=False)]
[assistant] The fix works: three renders now produce identical output and the alias keeps a single `ord`. Now I'll make the test a real regression test by calling the generator with `copy=False`, which is the path that exposes the mutation. First, checking how existing tests build a generator.
[tool_use Bash] {"command": "grep -rn \"generator(\" tests/dialects/*.py | head -5; grep -rn \"copy=False)\" tests/dialects/test_dialect.py | head -3", "description": "Find how tests build generators"}
[tool_result] tests/dialects/test_snowflake.py:6513:    def test_generator(self):
[tool_use Bash] {"command": "sed -n 6513,6525p tests/dialects/test_snowflake.py; grep -n \"def parse_one\\|def validate_identity\" -A6 tests/dialects/test_dialect.py | head -30", "description": "Read existing generator test and Validator helpers"}
[tool_result]     def test_generator(self):
        self.validate_identity("SELECT 1 FROM TABLE(GENERATOR(ROWCOUNT => 10))")
        self.validate_identity("SELECT 1 FROM TABLE(GENERATOR(TIMELIMIT => 5))")
        self.validate_identity("SELECT 1 FROM TABLE(GENERATOR(ROWCOUNT => 10, TIMELIMIT => 5))")

        # Positional args are mapped to ROWCOUNT, TIMELIMIT in order
        self.validate_identity(
            "SELECT 1 FROM TABLE(GENERATOR(10))",
            "SELECT 1 FROM TABLE(GENERATOR(ROWCOUNT => 10))
…[251 chars elided]…
 read=self.dialect, **kwargs)
31-
32-    def assert_duckdb_sql(
33-        self,
34-        expression: exp.Expr,
35-        *,
--
53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
[assistant] I'll write the test with `Dialect.get_or_raise("postgres").generator()` and `generate(copy=False)`, then run it against both the original and the fixed generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "        unnest = parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\", read=\"postgres\"\n        ).find(exp.Unnest)\n        for _ in range(2):\n            self.ass
…[160 chars elided]…
elf.parse_one(\n            \"SELECT * FROM UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\"\n        ).find(exp.Unnest)\n        generator = Dialect.get_or_raise(\"postgres\").generator()\n        for _ in range(2):\n            self.assertEqual(\n                generator.generate(unnest, copy=False),\n                \"UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)\",\n            )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py", "old_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\nfrom sqlglot.helper import logger as helper_logger", "new_string": "from sqlglot import ParseError, UnsupportedError, exp, transpile\nfrom sqlglot.dialects.dialect import Dialect\nfrom sqlglot.helper import logger as helper_logger"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-182546-postgres-dialect-when-an-unnest/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll verify the test fails on the original generator and passes with the fix. I'm swapping the original `generator.py` in temporarily, then restoring it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cp sqlglot/generator.py /tmp/generator_fixed.py && git show HEAD:sqlglot/generator.py > sqlglot/generator.py && echo \"== ORIGINAL ==\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k test_postgres 2>&1 | tail -8; cp /tmp/generator_fixed.py sqlglot/generator.py && echo \"== FIXED ==\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py -k test_postgres 2>&1 | tail -3; git diff --stat", "description": "Verify test fails on original and passes with fix"}
[tool_result] == ORIGINAL ==
E           - UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord, ord)
E           ?                                               -----
E           + UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)

tests/dialects/test_postgres.py:149: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_postgres - Asserti...
1 failed, 24 passed, 187 subtests passed in 0.28s
== FIXED ==
.........................                              [100%]
25 passed, 378 subtests passed in 0.24s
sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 10 ++++++++++
 2 files changed, 12 insertions(+), 1 deletion(-)
[assistant] The regression test fails on the original code (`t(col, ord, ord)`) and passes with the fix. Now the project's full check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full project test suite"}
[tool_result] ....................................... [ 66%]
......................................... [ 70%]
.... [ 70%]
.................................................. [ 75%]
............................................. [ 79%]
............................................................................................................................................. [ 91%]
........................................................................................                                 [100%]
1096 passed, 17880 subtests passed in 51.90s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generator.py tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generator.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git diff", "description": "Run ruff lint/format check and show diff"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/generator.py            |  3 ++-
 tests/dialects/test_postgres.py | 10 ++++++++++
 2 files changed, 12 insertions(+), 1 deletion(-)

--- Changes ---

sqlglot/generator.py
  @@ -3203,7 +3203,8 @@ class Generator:
  -                alias.append("columns", offset)
  +                alias = alias.copy()
  +                alias.append("columns", offset.copy())
   
           if alias and self.dialect.UNNEST_COLUMN_ONLY:
               columns = 
…[382 chars elided]…
ALITY AS t(col, ord)"
  +        ).find(exp.Unnest)
  +        generator = Dialect.get_or_raise("postgres").generator()
  +        for _ in range(2):
  +            self.assertEqual(
  +                generator.generate(unnest, copy=False),
  +                "UNNEST(ARRAY[1, 2]) WITH ORDINALITY AS t(col, ord)",
  +            )
           self.validate_identity(
               "SELECT SUM(x) OVER a, SUM(y) OVER b FROM c WINDOW a AS (PARTITION BY d), b AS (PARTITION BY e)"
           )
  +10 -0
[assistant] Fixed: rendering an `UNNEST ... WITH ORDINALITY AS t(col, ord)` node repeatedly no longer adds a duplicate `ord` column, and the AST is left unchanged.

**Root cause:** `unnest_sql` in `sqlglot/generator.py` (around line 3204) called `alias.append("columns", offset)` on the shared alias node. Every call appended the offset column again. Calling the generator on the same node three times gave `t(col, ord)`, then `t(col, ord, ord)`, then `t(col, ord, ord, ord)`. `Expr.sql()` deep-copies the tree first, so the bug only shows up when the same node is rendered again without that copy, which is what
…[312 chars elided]…
())
```

The change is in the base generator, so it applies to every dialect that uses `unnest_sql`, not only Postgres.

**Test:** I added a regression case to `tests/dialects/test_postgres.py` (in `test_postgres`). It renders one parsed `Unnest` node twice through `generate(copy=False)` and expects the same output both times. It fails on the original code (`t(col, ord, ord)`) and passes with the fix. No existing tests were changed.

**Checks:** the full suite passes (1096 passed, 17880 subtests), and `ruff check` and `ruff format --check` are clean on both files. I haven't committed anything.
