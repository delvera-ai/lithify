# trajectory base-1

final message:
Fixed in `sqlglot/generator.py`. The MySQL null-ordering simulation now checks an unqualified ORDER BY column through the qualified projection it names, so the `CASE` no longer uses an ambiguous bare name. The full suite passes (1110 passed) and ruff is clean.

**What changed**

- **`sqlglot/generator.py`**: new helper `_ordered_null_check_source`. When an unqualified ORDER BY column matches a projection that is a qualified column (`a.x`, or `a.x AS y`), the `CASE WHEN ... IS NULL` check uses that qualified column. The sort key itself stays as written.
- **`tests/dialects/test_duckdb.py`**: new `test_nulls_ordering_ambiguous_columns`, covering the bare-name, aliased-qualified, and alias cases.

**Before and after** (DuckDB → MySQL)

- `SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY x`
  - Before: `ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x`
  - After: `ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x`
- Already-qualified ORDER BY references (`ORDER BY a.x`) and aliases were already unambiguous and are unchanged.

**Limits and open points**

- I couldn't run MySQL here, so the ambiguity fix is verified by the generated SQL, not by executing it against a server. The reasoning is that the sort key `x` resolves to the select-list column, while the `CASE` is resolved against the FROM sources.
- The rewrite only applies when the ORDER BY sits directly on the SELECT. An ORDER BY inside a window (e.g. `SUM(x) OVER (ORDER BY x)`) still emits bare names, which can still be ambiguous. Fixing that would need the real FROM-scope resolution, so I left it alone.
- Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn \"null_ordered\\|NULLS_ARE\\|nulls_first\\|def ordered_sql\" sqlglot/generator.py sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head -50; ls .lithify/harness/scripts/ 2>/dev/null"}
[tool_result] sqlglot/generator.py:2958:    def ordered_sql(self, expression: exp.Ordered) -> str:
sqlglot/generator.py:2962:        nulls_first = expression.args.get("nulls_first")
sqlglot/generator.py:2963:        nulls_last = not nulls_first
sqlglot/generator.py:2972:        if nulls_first and (
probe_parse.py  2.2K
[tool_use Bash] {"command": "sed -n 2950,3010p sqlglot/generator.py; grep -n \"NULL_ORDERING\\|null_ordering\\|nulls_are\\|NULL_ORDER\" sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py | head; cat .lithify/harness/scripts/probe_parse.py | head -60"}
[tool_result]         return self.op_expressions("CLUSTER BY", expression)

    def distribute_sql(self, expression: exp.Distribute) -> str:
        return self.op_expressions("DISTRIBUTE BY", expression)

    def sort_sql(self, expression: exp.Sort) -> str:
        return self.op_expressions("SORT BY", expression)

    def ordered_sql(self, expression: exp.Ordered) -> str:
        desc = expression.args.get("desc")
        asc = not desc

        nulls_first = expression.args.get("nulls_first")
        nulls
…[3940 chars elided]…
d_argument("--write", default=None, help="output dialect; defaults to --read")
    args = parser.parse_args(argv)
    write = args.write or args.read

    count = 0
    failed = False
    for line in sys.stdin:
        sql = line.strip()
        if not sql or sql.startswith("--"):
            continue
        count += 1
        status, detail = probe(sql, args.read, write)
        if status != "OK":
            failed = True
        print(f"{status:9} {sql}")
        print(f"          {detail}")
[tool_use Bash] {"command": "sed -n 3010,3040p sqlglot/generator.py; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT a.x, b.x FROM a JOIN b ON a.id=b.id ORDER BY x', 'SELECT t.x FROM t JOIN u ON t.id=u.id ORDER BY t.x', 'SELECT x AS y FROM t ORDER BY y', 'SELECT a.x AS y FROM a JOIN b ON 1=1 ORDER BY y']:\n    print(sqlglot.transpile(s, read='duckdb', write='mysql')[0])\n\""}
[tool_result]                 ):
                    # BigQuery does not allow these ordering/nulls combinations when used under
                    # an aggregation func or under a window containing one
                    ancestor = expression.find_ancestor(exp.AggFunc, exp.Window, exp.Select)

                    if isinstance(ancestor, exp.Window):
                        ancestor = ancestor.this
                    if isinstance(ancestor, exp.AggFunc):
                        self.unsupported(
          
…[1052 chars elided]…
l}"

    def matchrecognizemeasure_sql(self, expression: exp.MatchRecognizeMeasure) -> str:
        window_frame = self.sql(expression, "window_frame")
SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x
SELECT t.x FROM t JOIN u ON t.id = u.id ORDER BY CASE WHEN t.x IS NULL THEN 1 ELSE 0 END, t.x
SELECT x AS y FROM t ORDER BY CASE WHEN y IS NULL THEN 1 ELSE 0 END, y
SELECT a.x AS y FROM a JOIN b ON 1 = 1 ORDER BY CASE WHEN y IS NULL THEN 1 ELSE 0 END, y
[tool_use Bash] {"command": "grep -rn \"IS NULL THEN 1 ELSE 0\" tests/ | head -20; grep -n \"NULL_ORDERING_SUPPORTED\" sqlglot/dialects/mysql.py sqlglot/generator.py"}
[tool_result] tests/dialects/test_redshift.py:245:                "mysql": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number = 1",
tests/dialects/test_redshift.py:252:                "starrocks": "SELECT a, b FROM (SELECT a AS a, b AS b, ROW_NUMBER() OVER (PARTITION BY a ORDER BY CASE WHEN c IS NULL THEN 1 ELSE 0 END DESC, c DESC) AS _row_number FROM x) AS _t WHERE _row_number 
…[1391 chars elided]…
_sk" IS NULL THEN 1 ELSE 0 END) AS "no_promo",
tests/fixtures/optimizer/tpc-ds/tpc-ds.sql:10068:  SUM(CASE WHEN NOT "promotion"."p_promo_sk" IS NULL THEN 1 ELSE 0 END) AS "promo",
4 matches in 1 files:

sqlglot/generator.py:296:NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generator.py:2984:if nulls_sort_change and not self.NULL_ORDERING_SUPPORTED:
sqlglot/generator.py:3007:elif self.NULL_ORDERING_SUPPORTED is False and (
sqlglot/generator.py:3022:elif self.NULL_ORDERING_SUPPORTED is None:
[tool_use Bash] {"command": "grep -rn \"NULL_ORDERING_SUPPORTED\" sqlglot/ | grep -v \"generator.py:29\\|generator.py:30\"; sed -n 3436,3460p tests/dialects/test_dialect.py; git log --oneline -3 -- sqlglot/generator.py"}
[tool_result] Binary file sqlglot/__pycache__/generator.cpython-312.pyc matches
sqlglot/generators/singlestore.py:29:    NULL_ORDERING_SUPPORTED: bool | None = True
sqlglot/generators/bigquery.py:238:    NULL_ORDERING_SUPPORTED: bool | None = False
Binary file sqlglot/generators/__pycache__/mysql.cpython-312.pyc matches
sqlglot/generators/tsql.py:135:    NULL_ORDERING_SUPPORTED: bool | None = None
sqlglot/generators/mysql.py:134:    NULL_ORDERING_SUPPORTED: bool | None = None
    def test_unsupported_null_ord
…[1036 chars elided]…
,
            (with_small_nulls, False, True, sql),
            (with_small_nulls, True, True, sql_nulls_first),
            (with_small_nulls, False, False, sql_nulls_last),
            (with_small_nulls, True, False, sql),
            (with_large_nulls, False, None, sql_nulls_last),
f00bb4a24 Refactor(postgres)!: rename `Distance3d` to `DistanceNd`
cc448ac48 feat(postgres): add support for PostGIS 3D distance operator <<->> (#7655)
10af77782 feat(tsql): support FOR JSON clause [CLAUDE] (#7649)
[tool_use Bash] {"command": "cat > /tmp/probe_in.sql <<'EOF'\nSELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY a.x\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY a.x\nSELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY x\nSELECT a.x AS y FROM a JOIN b ON a.id = b.id ORDER BY y\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY x\nSELECT a.x FROM a, b ORDER BY x\nSELECT a.x FROM a JOIN b USING (id) ORDER 
…[194 chars elided]…
N b ON a.id = b.id WHERE b.y = 1 ORDER BY a.x LIMIT 1\nSELECT x FROM a JOIN b ON a.id = b.id ORDER BY a.x\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY \"a\".\"x\"\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -I .lithify/harness/scripts/probe_parse.py --read duckdb --write mysql < /tmp/probe_in.sql"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb --write mysql < /tmp/probe_in.sql"}
[tool_result] 'NULLS LAST' translation not supported with positional ordering
OK        SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY a.x
          SELECT a.x, b.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
OK        SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY a.x
          SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
OK        SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY x
          SELECT a.x AS x 
…[1335 chars elided]…
 NULL THEN 1 ELSE 0 END, a.x LIMIT 1
OK        SELECT x FROM a JOIN b ON a.id = b.id ORDER BY a.x
          SELECT x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, a.x
OK        SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1
          SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY 1
OK        SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY "a"."x"
          SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN `a`.`x` IS NULL THEN 1 ELSE 0 END, `a`.`x`
[tool_use Bash] {"command": "grep -n \"def output_name\" sqlglot/expressions.py sqlglot/*/*.py 2>/dev/null | head; grep -rn \"def output_name\" sqlglot/ --include=*.py | head -3"}
[tool_result] 16 matches in 4 files:

sqlglot/expressions/core.py:207:def output_name(self) -> str:
sqlglot/expressions/core.py:951:def output_name(self) -> str:
sqlglot/expressions/core.py:1689:def output_name(self) -> str:
sqlglot/expressions/core.py:1734:def output_name(self) -> str:
sqlglot/expressions/core.py:1776:def output_name(self) -> str:
sqlglot/expressions/core.py:1792:def output_name(self) -> str:
sqlglot/expressions/core.py:1840:def output_name(self) -> str:
sqlglot/expressions/core.py:1876:def output_name(self) -> str:
(eval):1: no matches found: --include=*.py
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        this = (\n         
…[112 chars elided]…
     )", "new_string": "                    elif not isinstance(expression.this, exp.Rand):\n                        null_sort_order = \" DESC\" if nulls_sort_change == \" NULLS FIRST\" else \"\"\n                        null_check = self.sql(self._ordered_null_check_source(expression))\n                        this = f\"CASE WHEN {null_check} IS NULL THEN 1 ELSE 0 END{null_sort_order}, {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py", "old_string": "    def ordered_sql(self, expression: exp.Ordered) -> str:\n        desc = expression.args.get(\"desc\")", "new_string": "    def _ordered_null_check_source(self, expression: exp.Ordered) -> exp.Expression:\n        
…[536 chars elided]…
jection, exp.Alias) else projection\n                if (\n                    isinstance(source, exp.Column)\n                    and source.table\n                    and projection.output_name == column.name\n                ):\n                    return source\n\n        return column\n\n    def ordered_sql(self, expression: exp.Ordered) -> str:\n        desc = expression.args.get(\"desc\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat >> /tmp/probe_in.sql <<'EOF'\nSELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY x\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY x\nSELECT b.z AS x FROM a JOIN b ON a.id = b.id ORDER BY x DESC\nSELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY SUM(x) OVER (ORDER BY x)\nEOF\nPYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read duckdb --write mysql < /tmp/probe_in.sql 2>&1 | tail -32; PYTHONPATH=$PWD $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_dialect.py tests/dialects/test_duckdb.py 2>&1 | tail -3"}
[tool_result] OK        SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY x
          SELECT a.x AS x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, x
OK        SELECT a.x AS y FROM a JOIN b ON a.id = b.id ORDER BY y
          SELECT a.x AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, y
OK        SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY x
          SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 
…[1922 chars elided]…
    SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY SUM(x) OVER (ORDER BY x)
          SELECT a.x FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN SUM(x) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x) IS NULL THEN 1 ELSE 0 END, SUM(x) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x)
..................................................................................... [ 75%]
................................................         [100%]
192 passed, 3904 subtests passed in 0.76s
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_duckdb.py | head -20; sed -n 150,160p tests/dialects/test_duckdb.py"}
[tool_result] 44 matches in 44 files:

13:0:
1615:0:
1655:0:
1696:0:
1721:0:
1786:0:
1956:0:
2004:0:
2008:0:
2184:0:
2216:0:
2223:0:
2241:0:
2249:0:
2256:0:
2263:0:
2270:0:
2277:0:
        self.validate_all(
            "SELECT SUM(X) OVER (ORDER BY x)",
            write={
                "bigquery": "SELECT SUM(X) OVER (ORDER BY x)",
                "duckdb": "SELECT SUM(X) OVER (ORDER BY x)",
                "mysql": "SELECT SUM(X) OVER (ORDER BY CASE WHEN x IS NULL THEN 1 ELSE 0 END, x)",
            },
        )
        self.validate_all(
            "SELECT SUM(X) OVER (ORDER BY x RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
            write={
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_duckdb.py | sed -n 1,12p; sed -n 1,30p tests/dialects/test_duckdb.py | grep -n \"class\\|def \" "}
[tool_result] 44 matches in 44 files:

13:0:
1615:0:
1655:0:
1696:0:
1721:0:
1786:0:
1956:0:
2004:0:
2008:0:
2184:0:
10:class TestDuckDB(Validator):
13:    def test_duckdb(self):
[tool_use Bash] {"command": "awk '/^    def test_/{print NR\": \"$0}' tests/dialects/test_duckdb.py | head -5"}
[tool_result] 13:     def test_duckdb(self):
1615:     def test_array_index(self):
1655:     def test_array_insert(self):
1696:     def test_array_remove(self):
1721:     def test_array_remove_at(self):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "offset": 1610, "limit": 6}
[tool_result] 1610	            read={
1611	                "snowflake": "UNICODE(foo)",
1612	            },
1613	        )
1614	
1615	    def test_array_index(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\n                \"snowflake\": \"UNICODE(foo)\",\n            },\n        )\n\n    def test_array_index(self):", "new_string": "            read={\n                \"snowflake\": \"UNICOD
…[659 chars elided]…
d ORDER BY CASE WHEN b.z IS NULL THEN 1 ELSE 0 END, x\",\n            },\n        )\n        self.validate_all(\n            \"SELECT a.x AS y FROM a JOIN b ON a.id = b.id ORDER BY y\",\n            write={\n                \"mysql\": \"SELECT a.x AS y FROM a JOIN b ON a.id = b.id ORDER BY CASE WHEN a.x IS NULL THEN 1 ELSE 0 END, y\",\n            },\n        )\n\n    def test_array_index(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-155113-duckdb-or-any-source-where-nulls/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k nulls_ordering 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; $PY -m ruff check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/generator.py tests/dialects/test_duckdb.py 2>&1 | tail -2"}
[tool_result] .                                                                    [100%]
1 passed, 44 deselected, 4 subtests passed in 0.07s
..................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [100%]
1110 passed, 18042 subtests passed in 49.46s
All checks passed!
2 files already formatted
[assistant] Fixed in `sqlglot/generator.py`. The MySQL null-ordering simulation now checks an unqualified ORDER BY column through the qualified projection it names, so the `CASE` no longer uses an ambiguous bare name. The full suite passes (1110 passed) and ruff is clean.

**What changed**

- **`sqlglot/generator.py`**: new helper `_ordered_null_check_source`. When an unqualified ORDER BY column matches a projection that is a qualified column (`a.x`, or `a.x AS y`), the `CASE WHEN ... IS NULL` check uses that qualified column. The sort key itself stays as written.
- **`tests/dialects/test_duckdb.py`**: ne
…[414 chars elided]…
unambiguous and are unchanged.

**Limits and open points**

- I couldn't run MySQL here, so the ambiguity fix is verified by the generated SQL, not by executing it against a server. The reasoning is that the sort key `x` resolves to the select-list column, while the `CASE` is resolved against the FROM sources.
- The rewrite only applies when the ORDER BY sits directly on the SELECT. An ORDER BY inside a window (e.g. `SUM(x) OVER (ORDER BY x)`) still emits bare names, which can still be ambiguous. Fixing that would need the real FROM-scope resolution, so I left it alone.
- Nothing is committed.
