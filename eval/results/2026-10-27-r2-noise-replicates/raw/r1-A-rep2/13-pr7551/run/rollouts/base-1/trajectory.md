# trajectory base-1

final message:
DuckDB → Snowflake now transpiles `list(x)` and `list_distinct(x)`. The full suite passes (1093 tests), and ruff is clean on the changed files.

**What changed**

- **`list(x)` → `ARRAY_AGG(x)`**: `sqlglot/generators/snowflake.py` gets a `list_sql` that emits `ARRAY_AGG` for a single-argument `List`. `DISTINCT` and `ORDER BY` carry through, e.g. `ARRAY_AGG(x) WITHIN GROUP (ORDER BY y)`. Both keep NULLs, so semantics match.
- **`list_distinct(x)` → `ARRAY_COMPACT(ARRAY_DISTINCT(x))`**: `sqlglot/parsers/duckdb.py` parses `LIST_DISTINCT` into the existing `ArrayDistinct` node with `check_null=False`. The Snowflake generator emits `ARRAY_COMPACT(ARRAY_DISTINCT(...))` only for that flag, so NULLs are dropped as DuckDB does. Snowflake's own `ARRAY_DISTINCT` and ClickHouse's `arrayDistinct` (flag unset) still come out as plain `ARRAY_DISTINCT`.
- **Tests**: `tests/dialects/test_duckdb.py` gets a `test_list_aggregates` covering the three cases above.

**Choices to review**

- I left the DuckDB parse of `list()` as `exp.List`, so DuckDB round-trips are unchanged. The Snowflake side does the mapping.
- `LIST_DISTINCT` now parses to `ArrayDistinct` for every target, not just Snowflake. Presto, Spark and BigQuery now get `ARRAY_DISTINCT(x)`, which keeps NULLs, so those outputs can differ from DuckDB's NULL-dropping behavior. Previously they got an unknown `LIST_DISTINCT` call, so this is no regression, but it isn't correct either. Say if you want those targets handled too.
- Materialize's `LIST[x]` literal also parses to `exp.List`, so a single-element literal would now become `ARRAY_AGG` when written to Snowflake. Previously it produced an invalid `LIST(...)`. Multi-element literals still fall back to the old output.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayAgg\\|\\\"LIST\\\"\\|ARRAY_DISTINCT\\|ArrayDistinct\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Search for relevant list/array expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "cat > /tmp/probe_list.py <<'EOF'\nimport sqlglot\nfor sql in [\"SELECT list(x) FROM t\", \"SELECT list_distinct(x) FROM t\", \"SELECT list(DISTINCT x) FROM t\"]:\n    e = sqlglot.parse_one(sql, read=\"duckdb\")\n    print(repr(e.selects[0]))\n    print(e.sql(\"snowflake\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_list.py').read())\"", "description": "Search sources and probe current DuckDB\u2192Snowflake output"}
[tool_result] List(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))])
SELECT LIST(x) FROM t
Anonymous(
  this=list_distinct,
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))])
SELECT LIST_DISTINCT(x) FROM t
List(
  expressions=[
    Distinct(
      expressions=[
        Column(
          this=Identifier(this=x, quoted=False))])])
SELECT LIST(DISTINCT x) FROM t
[tool_use Bash] {"command": "ls; grep -rn \"class List\\b\\|class List(\\|class ArrayUniqueAgg\\|class ArrayAgg\\|class ArrayDistinct\\|class ArrayUnique\" sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null; grep -rn \"exp.List\\b\\|ArrayUniqueAgg\\|ArrayDistinct\\|ARRAY_DISTINCT\\|list_distinct\" sqlglot/dialects/*.py | head -60", "description": "Locate expression classes and related dialect usages"}
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
sqlglot/expressions/array.py:34:class List(Expression, Func):
sqlglot/expressions/array.py:138:class ArrayDistinct(Expression, Func):
sqlglot/expressions/aggregate.py:71:class ArrayAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py:83:class ArrayUniqueAgg(Expression, AggFunc):
[tool_use Bash] {"command": "sed -n 25,45p sqlglot/expressions/array.py; sed -n 135,145p sqlglot/expressions/array.py; sed -n 65,95p sqlglot/expressions/aggregate.py; grep -rn \"ArrayUniqueAgg\\|ArrayDistinct\\|ArrayAgg\\|exp.List\\b\\|\\\"LIST\\\"\\|LIST_DISTINCT\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/dialects/dialect.py sqlglot/generator.py sqlglot/parser.py | head -60", "description": "Inspect List/ArrayDistinct/ArrayAgg definitions and usages"}
[tool_result]     }
    is_var_len_args = True


class ArrayConstructCompact(Expression, Func):
    arg_types = {"expressions": False}
    is_var_len_args = True


class List(Expression, Func):
    arg_types = {"expressions": False}
    is_var_len_args = True


class ToArray(Expression, Func):
    pass


# Array manipulation


# Array properties


class ArrayDistinct(Expression, Func):
    arg_types = {"this": True, "check_null": False}


class ArrayFirst(Expression, Func):
    arg_types = {"this": True, "exp
…[1063 chars elided]…
Y_AGG": lambda args, dialect: exp.ArrayAgg(
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parser.py:1720:        "LIST": lambda self: self._parse_analyze_list(),
sqlglot/generator.py:3583:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:5333:        array_agg_expr: exp.ArrayAgg,
sqlglot/generator.py:5341:            array_agg_expr: The ArrayAgg expression node
sqlglot/generator.py:5370:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
[tool_use Bash] {"command": "grep -rn \"ArrayDistinct\\|ArrayCompact\\|check_null\\|exp.List\\b\\|ArrayUniqueAgg\" sqlglot/ --include=*.py | grep -v \"^sqlglot/expressions/array.py:138\" | head -60; echo ---; grep -n \"list_distinct\\|LIST_DISTINCT\\|list(\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head -30", "description": "Find ArrayDistinct, ArrayCompact, List usages and existing tests"}
[tool_result] (eval):1: no matches found: --include=*.py
---
tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNHEX('08000000000000000000' || h) END FROM (SELECT l, COALESCE(LIST_REDUCE(LIST_TRANSFORM(l, __x -> PRINTF('%02X%02X', CAST(__x 
…[1578 chars elided]…
T([1, 2, 2, 3, 1]) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
tests/dialects/test_snowflake.py:4925:        self.assertEqual(list(search_ast.args), ["this", "expression"])
tests/dialects/test_snowflake.py:4945:        self.assertEqual(list(search_ast.args), ["this", "expression", "search_mode", "analyzer"])
tests/dialects/test_snowflake.py:5848:        self.assertEqual(len(list(ast.find_all(exp.Column))), 1)
[tool_use Bash] {"command": "grep -rn \"ArrayDistinct\\|ArrayCompact\\|check_null\\|exp\\.List\\b\\|ArrayUniqueAgg\" sqlglot/ | head -60", "description": "Find ArrayDistinct, ArrayCompact, List usages in sqlglot"}
[tool_result] sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parsers/clickhouse.py:256:        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/parsers/doris.py:31:        "COLLECT_SET": exp.ArrayUniqueAgg.from_arg_list,
sqlglot/parsers/snowflake.py:412:            check_null=True,
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
sqlglot/parsers/snowflake.py:416
…[2800 chars elided]…
:1505:            exp.ArrayCompact(this=exp.Array(expressions=e.expressions))
sqlglot/generators/duckdb.py:3299:    def arrayuniqueagg_sql(self, expression: exp.ArrayUniqueAgg) -> str:
sqlglot/generators/duckdb.py:3311:    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
sqlglot/generators/duckdb.py:3315:        if expression.args.get("check_null"):
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
[tool_use Bash] {"command": "sed -n 405,420p sqlglot/parsers/snowflake.py; echo ---; sed -n 3295,3325p sqlglot/generators/duckdb.py; echo ---; sed -n 550,566p sqlglot/generators/duckdb.py; echo ---; sed -n 2170,2190p sqlglot/dialects/dialect.py; echo ---; sed -n 1498,1510p sqlglot/generators/duckdb.py; echo ---; sed -n 40,60p sqlglot/generators/materialize.py; echo; grep -n \"ArrayCompact\\|ArrayDistinct\\|ArrayAgg\\|ArrayUniqueAgg\\|List\\b\" sqlglot/generators/snowflake.py | head", "description": "Read relevant parser and generator code sections"}
[tool_result]         "CURRENT_TIME": lambda args: exp.Localtime(this=seq_get(args, 0)),
        "APPROX_TOP_K": _build_approx_top_k,
        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
        "ARRAY_CONTAINS": lambda args: exp.ArrayContains(
            this=seq_get(args, 1),
            expression=seq_get(args, 0),
            ensure_variant=False,
            check_null=True,
        ),
        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
            this=seq_get(args, 0),
          
…[4189 chars elided]…
self.normalize_func('MAP')}[{self.expressions(expression.this)}]"

189:                    exp.select(exp.ArrayAgg(this=exp.Star())).from_(unnest).subquery()
611:        exp.ArrayConcatAgg: lambda self, e: self.func("ARRAY_FLATTEN", exp.ArrayAgg(this=e.this)),
673:    RESPECT_IGNORE_NULLS_UNSUPPORTED_EXPRESSIONS = (exp.ArrayAgg,)
1035:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
1069:                array_agg = exp.ArrayAgg(this=build_object_construct(args=object_construct_args))
[tool_use Bash] {"command": "sed -n 3,80p sqlglot/parsers/duckdb.py | grep -n \"LIST\\|Array\" ; grep -n \"ArrayAgg\\|arrayagg\\|\\\"LIST\\\"\\|List\" sqlglot/generators/duckdb.py | head -30; echo ---; sed -n 5370,5400p sqlglot/generator.py; echo ---; grep -n \"ArrayAgg\\|ArrayUniqueAgg\\|ARRAY_AGG\" sqlglot/generators/snowflake.py; sed -n 1035,1050p sqlglot/generators/snowflake.py", "description": "Check DuckDB parser/generator handling of list aggregates"}
[tool_result] 20:    return exp.SortArray(this=seq_get(args, 0), asc=exp.false())
24:    return exp.ArrayPrepend(this=seq_get(args, 1), expression=seq_get(args, 0))
3001:        if isinstance(func, exp.ArrayAgg):
3009:            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
3021:            return self._add_arrayagg_null_filter(array_agg_sql, func, original_this)
3302:                this=exp.func("LIST", exp.Distinct(expressions=[expression.this])),
---
    def array
…[1876 chars elided]…
ayAgg) -> str:
        this = expression.this

        # If an ORDER BY clause is present, we need to remove it from ARRAY_AGG
        # and add it later as part of the WITHIN GROUP clause
        order = this if isinstance(this, exp.Order) else None
        if order:
            expression.set("this", order.this.pop())

        expr_sql = super().arrayagg_sql(expression)

        if order:
            expr_sql = self.sql(exp.WithinGroup(this=expr_sql, expression=order))

        return expr_sql
[tool_use Bash] {"command": "grep -n \"FUNCTIONS = {\" -A3 sqlglot/parsers/duckdb.py | head; grep -n \"\\\"LIST_\\|\\\"LIST\\\"\\|\\\"LIST_VALUE\\|\\\"ARRAY_UNIQUE\\|\\\"LIST_HAS\" sqlglot/parsers/duckdb.py | head; grep -n \"def list_sql\\|def arraydistinct_sql\\|ArrayDistinct\\|ArrayCompact\" sqlglot/generator.py sqlglot/generators/snowflake.py; echo ---; grep -n \"list_distinct\\|LIST_DISTINCT\\|list(\\|LIST(\" tests/dialects/test_duckdb.py | head -40", "description": "Check parser function map and existing DuckDB list tests"}
[tool_result] 72:    NO_PAREN_FUNCTIONS = {
73-        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: exp.Localtime,
75-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
--
102:    FUNCTIONS = {
103-        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
104-        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
105-        "ARRAY_PREPEND": _build_array_prepend,
136:        "LIST_APPEND": exp.ArrayAppend.from_ar
…[150 chars elided]…
ISTANCE": exp.CosineDistance.from_arg_list,
140:        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
141:        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
142:        "LIST_HAS": exp.ArrayContains.from_arg_list,
143:        "LIST_HAS_ANY": exp.ArrayOverlaps.from_arg_list,
144:        "LIST_MAX": exp.ArrayMax.from_arg_list,
145:        "LIST_MIN": exp.ArrayMin.from_arg_list,
---
690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
[tool_use Bash] {"command": "sed -n 136,150p sqlglot/parsers/duckdb.py; echo ---; sed -n 1073,1085p sqlglot/generators/snowflake.py; echo ---; grep -n \"^from\\|^import\" sqlglot/generators/snowflake.py; echo ---; <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nprint(sqlglot.parse_one('SELECT list(x ORDER BY y) FROM t', read='duckdb').sql('duckdb'))\nprint(repr(sqlglot.parse_one('SELECT list(x ORDER BY y) FROM t', read='duckdb').selects[0]))\nprint(sqlglot.parse_one('SELECT ARRAY_DISTINCT(x)', read='snowflake').sql('duckdb'))\"", "description": "Read parser map and snowflake generator context"}
[tool_result]         "LIST_APPEND": exp.ArrayAppend.from_arg_list,
        "LIST_CONCAT": parser.build_array_concat,
        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
        "LIST_HAS": exp.ArrayContains.from_arg_list,
        "LIST_HAS_ANY": exp.ArrayOverlaps.from_arg_list,
        "LIST_MAX": exp.ArrayMax.from_arg_list
…[1170 chars elided]…
lot.tokens import TokenType
37:from collections import defaultdict
---
SELECT LIST(x ORDER BY y) FROM t
List(
  expressions=[
    Order(
      this=Column(
        this=Identifier(this=x, quoted=False)),
      expressions=[
        Ordered(
          this=Column(
            this=Identifier(this=y, quoted=False)),
          nulls_first=False)])])
SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END
[assistant] Current output confirms the gap: `list(x)` and `list_distinct(x)` pass through as `LIST(...)` and `LIST_DISTINCT(...)`, which Snowflake doesn't have. I'll parse `list_distinct` into the existing `ArrayDistinct` node with `check_null=False` (DuckDB's NULL-dropping semantics), then have Snowflake emit `ARRAY_COMPACT(ARRAY_DISTINCT(x))` for that case. `list(x)` becomes `ARRAY_AGG` in the Snowflake generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,", "new_string": "        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(this=seq_get(args, 0), check_null=False),\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"seq_get\" sqlglot/parsers/duckdb.py | head -3", "description": "Check seq_get import in DuckDB parser"}
[tool_result] 15:from sqlglot.helper import seq_get
22:    return exp.SortArray(this=seq_get(args, 0), asc=exp.false())
26:    return exp.ArrayPrepend(this=seq_get(args, 1), expression=seq_get(args, 0))
[assistant] Now the Snowflake generator: `list` → `ARRAY_AGG`, and `ArrayDistinct` with `check_null=False` → `ARRAY_COMPACT(ARRAY_DISTINCT(...))`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "        if order:\n            expr_sql = self.sql(exp.WithinGroup(this=expr_sql, expression=order))\n\n        return expr_sql\n", "new_string": "        if order:\n            expr_sql = self.sql(exp.Wit
…[338 chars elided]…
xpression: exp.ArrayDistinct) -> str:\n        # DuckDB's LIST_DISTINCT drops NULLs (check_null=False), Snowflake's ARRAY_DISTINCT keeps them\n        if expression.args.get(\"check_null\") is False:\n            return self.sql(\n                exp.ArrayCompact(this=exp.ArrayDistinct(this=expression.this, check_null=True))\n            )\n        return self.function_fallback_sql(expression)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/probe_list2.py <<'EOF'\nimport sqlglot\ncases = [\n (\"SELECT list(x) FROM t\", \"duckdb\"),\n (\"SELECT list(DISTINCT x) FROM t\", \"duckdb\"),\n (\"SELECT list(x ORDER BY y) FROM t\", \"duckdb\"),\n (\"SELECT list_distinct(x) FROM t\", \"duckdb\"),\n (\"SELECT list_distinct(LIST(x)) FROM t\", \"duckdb\"),\n (\"SELECT ARRAY_DISTINCT(x)\", \"snowflake\"),\n (\"SELECT ARRAY_
…[97 chars elided]…
n    print(sql, \"->\", e.sql(\"snowflake\"), \"| duckdb:\", e.sql(\"duckdb\"))\nprint(sqlglot.parse_one(\"SELECT ARRAY_DISTINCT(x)\", read=\"clickhouse\").sql(\"snowflake\"))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/probe_list2.py').read())\"", "description": "Probe new DuckDB to Snowflake outputs"}
[tool_result] SELECT list(x) FROM t -> SELECT ARRAY_AGG(x) FROM t | duckdb: SELECT LIST(x) FROM t
SELECT list(DISTINCT x) FROM t -> SELECT ARRAY_AGG(DISTINCT x) FROM t | duckdb: SELECT LIST(DISTINCT x) FROM t
SELECT list(x ORDER BY y) FROM t -> SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t | duckdb: SELECT LIST(x ORDER BY y) FROM t
SELECT list_distinct(x) FROM t -> SELECT ARRAY_COMPACT(ARRAY_DISTINCT(x)) FROM t | duckdb: SELECT LIST_DISTINCT(x) FROM t
SELECT list_distinct(LIST(x)) FROM t -> SELECT ARRAY_COMPACT(ARRAY_DISTINCT(ARRAY_AGG(x))) FROM t | duckdb: SELECT LIST_DISTINCT(LIST(x)) FROM t
SELECT ARRAY_DISTINCT(x) -> SELECT ARRAY_DISTINCT(x) | duckdb: SELECT CASE WHEN ARRAY_LENGTH(x) <> LIST_COUNT(x) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(x) END
SELECT ARRAY_DISTINCT(x) -> SELECT ARRAY_DISTINCT(x) | duckdb: SELECT LIST_DISTINCT(x)
SELECT ARRAY_DISTINCT(x)
[assistant] The conversions look right. Now I'll add tests to the DuckDB dialect test file and run the project's checks.
[tool_use Bash] {"command": "grep -n \"def test_\\|\\\"snowflake\\\": \\\"SELECT ARRAY_AGG\\|\\\"snowflake\\\": \\\"ARRAY\" tests/dialects/test_duckdb.py | head -80", "description": "Locate test methods in DuckDB test file"}
[tool_result] 13:    def test_duckdb(self):
139:                "snowflake": "ARRAY_TO_STRING(arr, delim)",
711:                "snowflake": "ARRAY_COMPACT([1, NULL, 2, NULL, 3])",
718:                "snowflake": "ARRAY_COMPACT(NULL)",
725:                "snowflake": "ARRAY_COMPACT([])",
732:                "snowflake": "ARRAY_COMPACT(['a', NULL, 'b', NULL, 'c'])",
739:                "snowflake": "ARRAY_COMPACT([[1, 2], NULL, [3, 4]])",
746:                "snowflake": "ARRAY_CONSTRUCT_COMPACT(1, 2, 3, 4, 
…[2419 chars elided]…
create_sequence(self):
2526:    def test_install(self):
2538:    def test_cte_using_key(self):
2546:    def test_udf(self):
2569:    def test_bitwise_agg(self):
2620:    def test_approx_percentile(self):
2639:    def test_current_database(self):
2651:    def test_current_schema(self):
2663:    def test_current_schemas(self):
2675:    def test_map_delete(self):
2695:    def test_map_size(self):
2715:    def test_map_pick(self):
2750:    def test_to_array(self):
2779:    def test_map_insert(self):
[tool_use Bash] {"command": "sed -n 2569,2575p tests/dialects/test_duckdb.py; sed -n 2612,2620p tests/dialects/test_duckdb.py", "description": "Read surrounding test method for insertion point"}
[tool_result]     def test_bitwise_agg(self):
        self.validate_all(
            "SELECT BIT_OR(int_value) FROM t",
            read={
                "snowflake": "SELECT BITOR_AGG(int_value) FROM t",
                "duckdb": "SELECT BIT_OR(int_value) FROM t",
            },
        self.validate_all(
            "SELECT BIT_XOR(CAST(val AS DECIMAL)) FROM t",
            write={
                "duckdb": "SELECT BIT_XOR(CAST(CAST(val AS DECIMAL(18, 3)) AS INT)) FROM t",
                "snowflake": "SELECT BITXORAGG(CAST(val AS DECIMAL(18, 3))) FROM t",
            },
        )

    def test_approx_percentile(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "                \"snowflake\": \"SELECT BITXORAGG(CAST(val AS DECIMAL(18, 3))) FROM t\",\n            },\n        )\n\n    def test_approx_percentile(self):", "new_string": "                \"snowflake\": \"
…[1124 chars elided]…
        \"SELECT ARRAY_COMPACT(ARRAY_DISTINCT(x)) FROM t\",\n            read={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\",\n            },\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\",\n                \"snowflake\": \"SELECT ARRAY_COMPACT(ARRAY_DISTINCT(x)) FROM t\",\n            },\n        )\n\n    def test_approx_percentile(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] My first draft mixed up the `validate_all` direction (the main SQL is parsed in the test's dialect, DuckDB here). I'll rewrite it with DuckDB as the source and Snowflake as the target.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_list_aggregates(self):\n        self.validate_all(\n            \"SELECT ARRAY_AGG(x) FROM t\",\n            read={\n                \"duckdb\": \"SELECT LIST(x) FROM t\",\n                \"sno
…[1900 chars elided]…
OM t\",\n                \"snowflake\": \"SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x) FROM t\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x) FROM t\",\n                \"snowflake\": \"SELECT ARRAY_COMPACT(ARRAY_DISTINCT(x)) FROM t\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-162852-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py 2>&1 | tail -30", "description": "Run DuckDB and Snowflake dialect tests"}
[tool_result] ............................................................................................................................................                                                                       [100%]
140 passed, 2166 subtests passed in 0.68s
[assistant] Both dialect files pass. Now the full suite, which is the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite"}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
............................................................................... [ 31%]
............................................................................................................................
…[275 chars elided]…
...................................................................... [ 72%]
............................................. [ 76%]
............................................. [ 80%]
......................................................................................................................................................................................................................                                                   [100%]
1093 passed, 17865 subtests passed in 48.38s
[assistant] All 1093 tests pass. I'll also run the linter and formatter on the changed files.
[tool_use Bash] {"command": "F=\"sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py\"; (<work>/env-sqlglot/bin/python -I -m ruff check $F && <work>/env-sqlglot/bin/python -I -m ruff format --check $F) 2>&1 | tail -15; git status --short; git diff --stat", "description": "Lint, format-check, and show changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/generators/snowflake.py | 13 +++++++++++++
 sqlglot/parsers/duckdb.py       |  1 +
 tests/dialects/test_duckdb.py   | 30 ++++++++++++++++++++++++++++++
 3 files changed, 44 insertions(+)
[tool_use Bash] {"command": "(which ruff && ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py && ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py tests/dialects/test_duckdb.py) 2>&1 | tail -8", "description": "Run system ruff on changed files if available"}
[tool_result] <work>/env-sqlglot/bin/ruff
All checks passed!
3 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor d in ['presto','spark','clickhouse','bigquery']:\n    print(d, sqlglot.transpile('SELECT LIST_DISTINCT(x)', read='duckdb', write=d))\"", "description": "Check list_distinct output for other target dialects"}
[tool_result] presto ['SELECT ARRAY_DISTINCT(x)']
spark ['SELECT ARRAY_DISTINCT(x)']
clickhouse ['SELECT arrayDistinct(x)']
bigquery ['SELECT ARRAY_DISTINCT(x)']
[assistant] DuckDB → Snowflake now transpiles `list(x)` and `list_distinct(x)`. The full suite passes (1093 tests), and ruff is clean on the changed files.

**What changed**

- **`list(x)` → `ARRAY_AGG(x)`**: `sqlglot/generators/snowflake.py` gets a `list_sql` that emits `ARRAY_AGG` for a single-argument `List`. `DISTINCT` and `ORDER BY` carry through, e.g. `ARRAY_AGG(x) WITHIN GROUP (ORDER BY y)`. Both keep NULLs, so semantics match.
- **`list_distinct(x)` → `ARRAY_COMPACT(ARRAY_DISTINCT(x))`**: `sqlglot/parsers/duckdb.py` parses `LIST_DISTINCT` into the existing `ArrayDistinct` node with `check_null=Fal
…[558 chars elided]…
r every target, not just Snowflake. Presto, Spark and BigQuery now get `ARRAY_DISTINCT(x)`, which keeps NULLs, so those outputs can differ from DuckDB's NULL-dropping behavior. Previously they got an unknown `LIST_DISTINCT` call, so this is no regression, but it isn't correct either. Say if you want those targets handled too.
- Materialize's `LIST[x]` literal also parses to `exp.List`, so a single-element literal would now become `ARRAY_AGG` when written to Snowflake. Previously it produced an invalid `LIST(...)`. Multi-element literals still fall back to the old output.

Nothing is committed.
