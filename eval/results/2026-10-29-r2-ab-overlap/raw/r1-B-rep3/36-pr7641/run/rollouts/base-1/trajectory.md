# trajectory base-1

final message:
The MySQL `ORDER BY` simulation for NULLS-last sources no longer produces an ambiguous column reference. The full suite passes (1109 tests), and I confirmed the rewritten queries run on MySQL 8.0.

**Cause:** the `CASE WHEN <col> IS NULL` check reused the raw ORDER BY text. MySQL resolves a bare name at the top level of `ORDER BY` to the select-list column, but inside the `CASE` it resolves against the FROM tables. When the name exists in both tables, that fails. I reproduced this on MySQL 8.0 with `SELECT b.id AS id FROM a JOIN b ... ORDER BY id`, which errored with `Column 'id' in order clause is ambiguous`.

**Fix** (`sqlglot/generator.py`): a new helper, `_ordered_null_check`, is used by `ordered_sql`. When the ORDER BY key is an unqualified column that matches a projection in the same SELECT's ORDER BY, the `CASE` check uses that projection's underlying column, qualified. The second sort key stays as the original reference.

- `SELECT b.id AS id ... ORDER BY id` → `ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id`
- `SELECT a.id, b.y ... ORDER BY id` → `ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, id`

Qualified ORDER BY references (`ORDER BY a.x`) were already emitted qualified, so they needed no change. Window-function ORDER BY clauses are excluded, since they cannot see projection aliases.

**Test:** one `validate_all` case added to `tests/dialects/test_duckdb.py`.

**Not covered:** an ambiguous bare name that is a projection alias of a non-column expression (e.g. `SELECT a.id * 1 AS id ... ORDER BY id`) still emits the bare alias in the `CASE`. I left that out to keep the change small.

I did not commit. I also started a temporary `mysql:8.0` container for the check and removed it afterwards.

## events
[tool_use Bash] {"command": "grep -rn \"null_ordering\\|NULL_ORDERING\\|nulls_first\\|NULLS_FIRST\" sqlglot/generator.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head -50", "description": "Locate NULL ordering handling code"}
[tool_result] sqlglot/generator.py:296:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generator.py:299:    WINDOW_FUNCS_WITH_NULL_ORDERING: t.ClassVar[tuple[type[exp.Expression], ...]] = ()
sqlglot/generator.py:2962:        nulls_first = expression.args.get("nulls_first")
sqlglot/generator.py:2963:        nulls_last = not nulls_first
sqlglot/generator.py:2964:        nulls_are_large = self.dialect.NULL_ORDERING == "nulls_are_large"
sqlglot/generator.py:2965:        nulls_are_small = self.dialect.NULL
…[126 chars elided]…
t"
sqlglot/generator.py:2972:        if nulls_first and (
sqlglot/generator.py:2984:        if nulls_sort_change and not self.NULL_ORDERING_SUPPORTED:
sqlglot/generator.py:2999:                isinstance(window_this, self.WINDOW_FUNCS_WITH_NULL_ORDERING)
sqlglot/generator.py:3007:                elif self.NULL_ORDERING_SUPPORTED is False and (
sqlglot/generator.py:3022:                elif self.NULL_ORDERING_SUPPORTED is None:
sqlglot/dialects/dialect.py:383:    NULL_ORDERING = "nulls_are_small"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "offset": 2950, "limit": 110}
[tool_result] 2950	        return self.op_expressions("CLUSTER BY", expression)
2951	
2952	    def distribute_sql(self, expression: exp.Distribute) -> str:
2953	        return self.op_expressions("DISTRIBUTE BY", expression)
2954	
2955	    def sort_sql(self, expression: exp.Sort) -> str:
2956	        return self.op_expressions("SORT BY", expression)
2957	
2958	    def ordered_sql(self, expression: exp.Ordered) -> str:
2959	        desc = expression.args.get("desc")
2960	        asc = not desc
2961	
2962	     
…[4805 chars elided]…
URES{self.seg(measures)}") if measures else ""
3052	        rows = self.sql(expression, "rows")
3053	        rows = self.seg(rows) if rows else ""
3054	        after = self.sql(expression, "after")
3055	        after = self.seg(after) if after else ""
3056	        pattern = self.sql(expression, "pattern")
3057	        pattern = self.seg(f"PATTERN ({pattern})") if pattern else ""
3058	        definition_sqls = [
3059	            f"{self.sql(definition, 'alias')} AS {self.sql(definition, 'this')}"
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nqs = [\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x, b.y',\n 'SELECT x FROM a JOIN b ON a.id = b.id ORDER BY x DESC',\n 'SELECT * FROM a JOIN b ON a.id = b.id ORDER BY b.y',\n 'SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY a.x + 1',\n]\nfor q in qs:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; ls; git log --oneline -1 -- sqlglot/generator.py", "description": "Reproduce DuckDB to MySQL NULL ordering cases"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
.agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  3.1K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  1.2K
sqlglot.png  7.2K
f00bb4a24 Refactor(postgres)!: rename `Distance3d` to `DistanceNd`
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nqs = [\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x, b.y',\n 'SELECT x FROM a JOIN b ON a.id = b.id ORDER BY x DESC',\n 'SELECT * FROM a JOIN b ON a.id = b.id ORDER BY b.y',\n 'SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY a.x + 1',\n]\nfor q in qs:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"; git status --short", "description": "Reproduce DuckDB to MySQL NULL ordering cases"}
[tool_result] SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT a.x AS x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x, CASE WHEN b.y IS NULL THEN 1 ELSE 0 END, b.y
SELECT x FROM a JOIN b ON a.id = b.id ORDER BY x DESC
SELECT * FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN b.y IS NULL THEN 1 ELSE 0 END, b.y
SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x + 1 IS NULL THEN 1 ELSE 0 END, a.x + 1
ok
[tool_use Bash] {"command": "grep -rn \"IS NULL THEN 1 ELSE 0 END\" tests | head -40; which mysql mysqld docker 2>/dev/null; echo ---; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nfor q in ['SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY id', 'SELECT b.id AS s FROM a JOIN b ON a.k = b.k ORDER BY s DESC', 'SELECT a.x FROM a ORDER BY x']:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"", "description": "Find existing tests and check for MySQL binary"}
[tool_result] tests/dialects/test_redshift.py:245:                "mysql": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/dialects/test_redshift.py:252:                "starrocks": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number 
…[1354 chars elided]…
:  SUM(CASE WHEN "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "no_promo",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10068:  SUM(CASE WHEN NOT "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "promo",
mysql not found
mysqld not found
/usr/local/bin/docker
---
SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN id IS NULL THEN 1 ELSE 0 END, id
SELECT b.id AS s FROM a JOIN b ON a.k = b.k ORDER BY s DESC
SELECT a.x FROM a ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
[tool_use Bash] {"command": "timeout 20 docker info --format '{{.ServerVersion}}' 2>&1 | head -3; timeout 10 docker images --format '{{.Repository}}:{{.Tag}}' 2>&1 | grep -i mysql | head", "description": "Check Docker daemon and cached MySQL images"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "docker info --format '{{.ServerVersion}}' 2>&1 | head -3; docker images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -20", "description": "Check Docker daemon and local images"}
[tool_result] 29.8.2
rrvv-tools:local
python:3.13-slim
postgres:16
terrane-p7-runner:local
vsc-terrane-81e5ce9a4aa9add5e1df98d63d8410a4afe41b590252e57ca108baa7a35a2441:latest
terrane-p7-devbase:local
terrane-devcontainer-codex-verify:local
node:22-bookworm
frt/migrate:offline-o006-r3-20261006
frt/oms:offline-o006-r3-20261006
frt/trading:offline-o006-r3-20261006
frt/migrate:offline-o006-r2-20261006
frt/oms:offline-o006-r2-20261006
frt/trading-api:offline-o006-r2-20261006
frt/cp-readonly-proxy:closeout-20261005-v5
frt/cp-readonly-proxy:closeout-20261005-v4
frt/cp-readonly-proxy:closeout-20261005-v3
frt/cp-readonly-proxy:closeout-20261005-v2
frt/cp-readonly-proxy:closeout-20261005
frt/trading-api:observer-d7017eb-offline-20261003
[tool_use Bash] {"command": "docker pull mysql:8.0 2>&1 | tail -3", "description": "Pull MySQL 8.0 image for behavior verification", "timeout": 600000}
[tool_result] Digest: sha256:7dcddc01f13bab2f15cde676d44d01f61fc9f99fe7785e86196dfc07d358ae2b
Status: Image is up to date for mysql:8.0
docker.io/library/mysql:8.0
[tool_use Bash] {"command": "docker rm -f sqlglot-mysql-probe >/dev/null 2>&1; docker run -d --name sqlglot-mysql-probe -e MYSQL_ROOT_PASSWORD=probe -e MYSQL_DATABASE=probe mysql:8.0 >/dev/null && for i in $(seq 1 60); do docker exec sqlglot-mysql-probe mysqladmin ping -uroot -pprobe --silent 2>/dev/null && break; sleep 2; done; docker exec -i sqlglot-mysql-probe mysql -uroot -pprobe probe 2>/dev/null <<'EOF'\nCR
…[576 chars elided]…
L THEN 1 ELSE 0 END, x;\nSELECT a.x, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x;\nSELECT a.x, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x;\nSELECT b.y AS x FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x;\nEOF", "description": "Start MySQL container and probe ORDER BY behavior", "timeout": 300000}
[tool_result ERROR] Exit code 1
mysqld is alive
id	y
1	7
2	NULL
[tool_use Bash] {"command": "q(){ echo \"== $1\"; docker exec sqlglot-mysql-probe mysql -uroot -pprobe probe -N -e \"$1\" 2>&1 | grep -v \"Using a password\"; }\nq \"SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN id IS NULL THEN 1 ELSE 0 END, id\"\nq \"SELECT b.id AS id FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN id IS NULL THEN 1 ELSE 0 END, id\"\nq \"SELECT b.id AS id FROM a JOIN b ON a.k=b.k ORDE
…[175 chars elided]…
 a JOIN b ON a.k=b.k ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x\"\nq \"SELECT b.y AS x FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x\"\nq \"SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY id\"\nq \"SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, a.id\"", "description": "Run ORDER BY variants against MySQL 8.0"}
[tool_result] == SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN id IS NULL THEN 1 ELSE 0 END, id
ERROR 1052 (23000) at line 1: Column 'id' in order clause is ambiguous
== SELECT b.id AS id FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN id IS NULL THEN 1 ELSE 0 END, id
ERROR 1052 (23000) at line 1: Column 'id' in order clause is ambiguous
== SELECT b.id AS id FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id
3
NULL
== SELECT a.x, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
5	NULL
NULL	7
== SELECT a.x, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
5	NULL
NULL	7
== SELECT b.y AS x FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
NULL
7
== SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY id
1	7
2	NULL
== SELECT a.id, b.y FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, a.id
1	7
2	NULL
[assistant] Reproduced on MySQL 8.0: the simulated `CASE WHEN id IS NULL` fails with `ERROR 1052 ... ambiguous`, while the plain `ORDER BY id` resolves to the select-list column. The fix is to use the projection's qualified column in the `CASE` check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n                            f\"CASE WHEN {this} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\"\n                        )", "new_string": "                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        null_check = self._ordered_null_check(expression, this)\n                        this = f\"CASE WHEN {null_check} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "        with_fill = self.sql(expression, \"with_fill\")\n        with_fill = f\" {with_fill}\" if with_fill else \"\"\n\n        return f\"{this}{sort_order}{nulls_sort_change}{with_fill}\"\n", "new_string": "       
…[567 chars elided]…
stance(order, exp.Order) else None\n\n        if isinstance(column, exp.Column) and not column.table and isinstance(select, exp.Select):\n            for projection in select.expressions:\n                source = projection.unalias()\n                if projection.output_name == column.name and isinstance(source, exp.Column):\n                    return self.sql(source)\n\n        return this\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -c \"\nimport sqlglot\nqs = [\n 'SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY id',\n 'SELECT a.id, b.y FROM a JOIN b ON a.k = b.k ORDER BY id',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY x',\n 'SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY a.x',\n 'SELECT b.y AS x FROM a JOIN b ON a.k = b.k ORDER BY x',\n 'SELECT a.x + 1 AS s FROM a JOIN b ON a.k = b.k ORDER BY s',\n 'SELECT x, ROW_NUMBER() OVER (ORDER BY x) AS r FROM a',\n 'SELECT * FROM t ORDER BY c',\n]\nfor q in qs:\n    print(sqlglot.transpile(q, read='duckdb', write='mysql')[0])\n\"", "description": "Verify transpilation output after the fix"}
[tool_result] SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id
SELECT a.id, b.y FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, id
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
SELECT a.x, b.y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
SELECT b.y AS x FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN b.y IS NULL THEN 1 ELSE 0 END, x
SELECT a.x + 1 AS s FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN s IS NULL THEN 1 ELSE 0 END, s
SELECT x, ROW_NUMBER() OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) AS r FROM a
SELECT * FROM t ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END, c
[assistant] Outputs look right. Now I'll confirm MySQL accepts the rewritten queries, then add a regression test.
[tool_use Bash] {"command": "q(){ echo \"== $1\"; docker exec sqlglot-mysql-probe mysql -uroot -pprobe probe -N -e \"$1\" 2>&1 | grep -v \"Using a password\"; }\nq \"SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id\"\nq \"SELECT a.id, b.y FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, id\"\nq \"SELECT a.x, b.y FROM a JOIN b ON a.k = 
…[102 chars elided]…
k ORDER BY CASE WHEN b.y IS NULL THEN 1 ELSE 0 END, x\"\ndocker rm -f sqlglot-mysql-probe >/dev/null; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1 && sed -n 75,90p tests/dialects/test_duckdb.py && grep -n \"def test_\" tests/dialects/test_duckdb.py | head -5", "description": "Run rewritten queries on MySQL, remove probe container"}
[tool_result] == SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id
3
NULL
== SELECT a.id, b.y FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN a.id IS NULL THEN 1 ELSE 0 END, id
1	7
2	NULL
== SELECT a.x, b.y FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
5	NULL
NULL	7
== SELECT b.y AS x FROM a JOIN b ON a.k=b.k ORDER BY CASE WHEN b.y IS NULL THEN 1 ELSE 0 END, x
7
NULL
                "mysql": UnsupportedError,
                "post
…[242 chars elided]…
ECT NULLS) OVER (PARTITION BY gb ORDER BY ob) FROM t",
                "sqlite": "SELECT FIRST_VALUE(c) OVER (PARTITION BY gb ORDER BY ob NULLS LAST) FROM t",
                "mysql": "SELECT FIRST_VALUE(c) RESPECT NULLS OVER (PARTITION BY gb ORDER BY CASE WHEN ob IS NULL THEN 1 ELSE 0 END, ob) FROM t",
                "postgres": UnsupportedError,
            },
        )
        self.validate_all(
            "CAST(x AS UUID)",
            write={
44 matches in 44 files:

13:0:
1615:0:
1655:0:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "                \"postgres\": UnsupportedError,\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS UUID)\",", "new_string": "                \"postgres\": UnsupportedError,\n    
…[59 chars elided]…
    \"SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY id\",\n            write={\n                \"duckdb\": \"SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY id\",\n                \"mysql\": \"SELECT b.id AS id FROM a JOIN b ON a.k = b.k ORDER BY CASE WHEN b.id IS NULL THEN 1 ELSE 0 END, id\",\n            },\n        )\n        self.validate_all(\n            \"CAST(x AS UUID)\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192832-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full project test suite", "timeout": 600000}
[tool_result] ........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................................................................. [ 34%]
................. [ 35%]
..............................................................................................................................
…[204 chars elided]…
................................. [ 66%]
............................................................................................................ [ 76%]
............................................. [ 80%]
..................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................    [100%]
1109 passed, 18040 subtests passed in 46.50s
[assistant] All 1109 tests pass. Quick lint/format check on the changed files:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -3; git status --short; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generator.py
 M tests/dialects/test_duckdb.pysqlglot/generator.py          | 20 +++++++++++++++++---
 tests/dialects/test_duckdb.py |  7 +++++++
 2 files changed, 24 insertions(+), 3 deletions(-)
[assistant] The MySQL `ORDER BY` simulation for NULLS-last sources no longer produces an ambiguous column reference. The full suite passes (1109 tests), and I confirmed the rewritten queries run on MySQL 8.0.

**Cause:** the `CASE WHEN <col> IS NULL` check reused the raw ORDER BY text. MySQL resolves a bare name at the top level of `ORDER BY` to the select-list column, but inside the `CASE` it resolves against the FROM tables. When the name exists in both tables, that fails. I reproduced this on MySQL 8.0 with `SELECT b.id AS id FROM a JOIN b ... ORDER BY id`, which errored with `Column 'id' in order clau
…[541 chars elided]…
fied ORDER BY references (`ORDER BY a.x`) were already emitted qualified, so they needed no change. Window-function ORDER BY clauses are excluded, since they cannot see projection aliases.

**Test:** one `validate_all` case added to `tests/dialects/test_duckdb.py`.

**Not covered:** an ambiguous bare name that is a projection alias of a non-column expression (e.g. `SELECT a.id * 1 AS id ... ORDER BY id`) still emits the bare alias in the `CASE`. I left that out to keep the change small.

I did not commit. I also started a temporary `mysql:8.0` container for the check and removed it afterwards.
