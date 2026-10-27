# trajectory base-1

final message:
DuckDB `list(col)` and `list_distinct(col)` now transpile to Snowflake. The full suite passed after my last edit: `SUMMARY: 1092 passed, 17861 subtests passed in 47.97s`, `EXIT: 0`. Ruff check and format are clean on the four changed files.

**What changed**

- **`list(col)` → `ARRAY_AGG`.** DuckDB's `LIST` parses to `exp.List`. I added `list_sql` in `sqlglot/generators/snowflake.py` that emits `ARRAY_AGG`. Keeping `exp.List` on the DuckDB side preserves DuckDB identity (`LIST(DISTINCT ...) FILTER(...)` still round-trips, as an existing test requires).
- **`list_distinct` → `ARRAY_DISTINCT(ARRAY_COMPACT(x))`.** DuckDB's `LIST_DISTINCT` was previously an untyped `Anonymous`. The DuckDB parser now builds `exp.ArrayDistinct(check_null=False)`. The Snowflake generator wraps the argument in `ARRAY_COMPACT` when `check_null is False`, which drops the NULLs that Snowflake's `ARRAY_DISTINCT` would keep. DuckDB round-trip is unchanged.
- **`LIST(x) FILTER (WHERE ...)` crash fixed.** Transpiling to Snowflake crashed with `AttributeError` because the generic `filter_sql` expects `.this`, which `exp.List` doesn't have. `filter_sql` in `sqlglot/generator.py` now rewrites a `List` to an `ArrayAgg` first. This is a generic change, so it also affects other dialects without FILTER support. Those cases crashed before.
- **Tests** added to `tests/dialects/test_duckdb.py`: the Snowflake output for both functions, the FILTER case, the DuckDB round-trip for `LIST_DISTINCT`, and an AST check that it parses to `exp.ArrayDistinct`.

**Decisions to review**

- I read `check_null is False` as the signal for "DuckDB null-dropping semantics". Only DuckDB's parser sets it, so ClickHouse `arrayDistinct` (which leaves it unset) keeps its current Snowflake output. A truthiness check would also change ClickHouse → Snowflake, and I believe ClickHouse keeps NULLs, so I avoided that.
- `LIST` maps to `ARRAY_AGG` for any source that produces `exp.List`, not only DuckDB. Only DuckDB produces it in this repo, as far as I can see.

**Not fixed (pre-existing)**

`LIST(DISTINCT x) FILTER (WHERE ...)` still produces invalid Snowflake SQL, `ARRAY_AGG(IFF(cond, DISTINCT x, NULL))`. The generic FILTER rewrite has the same bug for `COUNT(DISTINCT x) FILTER (...)`. The fix belongs in the generic `filter_sql`, so I left it alone.

## events
[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null | head -20; grep -n -i \"list_distinct\\|\\\"LIST\\\"\\|ListDistinct\\|ARRAY_DISTINCT\\|ArrayUniqueAgg\\|ArrayAgg\\b\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/parsers/duckdb.py sqlglot/parsers/snowflake.py sqlglot/generators/duckdb.py sqlglot/generators/snowflake.py sqlglot/expressions/*.py | head -60", "description": "Check memory file and find relevant list/array references"}
[tool_use Bash] {"command": "ls sqlglot/parsers sqlglot/generators 2>&1 | head -5; ls sqlglot | head -50; git log --oneline -1", "description": "List parser/generator layout and current commit"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[1800 chars elided]…
s=exp.func("LIST", exp.Distinct(expressions=[expression.this])),
sqlglot/generators/duckdb.py:3313:        func = self.func("LIST_DISTINCT", arr)
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/expressions/aggregate.py:71:class ArrayAgg(Expression, AggFunc):
sqlglot/expressions/aggregate.py:83:class ArrayUniqueAgg(Expression, AggFunc):
sqlglot/expressions/json.py:21:class JSONArrayAgg(Expression, AggFunc):
[tool_result] sqlglot/generators:
__init__.py
athena.py
bigquery.py
clickhouse.py
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
01a31e74e lithify: probe base
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['SELECT LIST(x) FROM t', 'SELECT LIST_DISTINCT(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT LIST(x) FILTER (WHERE x IS NOT NULL) FROM t']:\n    e = sqlglot.parse_one(s, read='duckdb')\n    print(repr(e.selects[0]))\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'))\n\"; grep -n \"class ArrayAgg\\|class ArrayUniqueAgg\\|class ArrayDistinct\\|class ArrayCompact\" -A8 sqlglot/expressions/*.py | head -60", "description": "Probe current DuckDB to Snowflake output for list functions"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/__init__.py", l
…[4634 chars elided]…
sions/array.py:138:class ArrayDistinct(Expression, Func):
sqlglot/expressions/array.py-139-    arg_types = {"this": True, "check_null": False}
sqlglot/expressions/array.py-140-
sqlglot/expressions/array.py-141-
sqlglot/expressions/array.py-142-class ArrayFirst(Expression, Func):
sqlglot/expressions/array.py-143-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/array.py-144-
sqlglot/expressions/array.py-145-
sqlglot/expressions/array.py-146-class ArrayLast(Expression, Func):
[tool_use Bash] {"command": "grep -rn \"exp\\.List\\b\\|class List\\b\\|\\\"LIST\\\"\\|LIST_DISTINCT\\|\\\"LIST_DISTINCT\\\"\\|ArrayUniqueAgg\\|ArrayDistinct\" sqlglot/ | grep -v \"^sqlglot/executor\" | head -60; echo ---; sed -n 3290,3325p sqlglot/generators/duckdb.py", "description": "Find list and distinct mappings across dialects"}
[tool_result] sqlglot/tokens.py:450:        "LIST": TokenType.LIST,
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parser.py:1720:        "LIST": lambda self: self._parse_analyze_list(),
sqlglot/parsers/clickhouse.py:258:        "ARRAYDISTINCT": exp.ArrayDistinct.from_arg_list,
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
sqlglot/parsers/doris.py:31:        "COLLECT_SET": exp.ArrayUniqueAgg.from_arg_list,
sqlglot/parsers/hive.py:63:        "COLLECT_SET": 
…[3448 chars elided]…
"LIST_DISTINCT", arr)

        if expression.args.get("check_null"):
            add_null_to_array = exp.func(
                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
            )
            return self.sql(
                exp.If(
                    this=exp.NEQ(
                        this=exp.ArraySize(this=arr), expression=exp.func("LIST_COUNT", arr)
                    ),
                    true=add_null_to_array,
                    false=func,
[tool_use Bash] {"command": "sed -n 30,45p sqlglot/expressions/array.py; sed -n 405,420p sqlglot/parsers/snowflake.py; echo ---SF gen; grep -n \"ArrayDistinct\\|ArrayCompact\\|ArrayAgg\\|check_null\\|def list_sql\\|exp.List\" sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py; echo ---DDB; sed -n 3311,3330p sqlglot/generators/duckdb.py; sed -n 2995,3015p sqlglot/generators/duckdb.py", "description": "Read list/array expression and dialect code paths"}
[tool_result]     arg_types = {"expressions": False}
    is_var_len_args = True


class List(Expression, Func):
    arg_types = {"expressions": False}
    is_var_len_args = True


class ToArray(Expression, Func):
    pass


# Array manipulation


        "CURRENT_TIME": lambda args: exp.Localtime(this=seq_get(args, 0)),
        "APPROX_TOP_K": _build_approx_top_k,
        "ARRAY_CONSTRUCT": lambda args: exp.Array(expressions=args),
        "ARRAY_CONTAINS": lambda args: exp.ArrayContains(
            this=seq
…[3265 chars elided]…
ql(func)

            # Save the original column for FILTER clause (before wrapping with Order)
            original_this = func.this

            # Move ORDER BY inside ARRAY_AGG by wrapping its argument with Order
            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
            func.set(
                "this",
                exp.Order(
                    this=func.this.copy(),
                    expressions=order.expressions,
                ),
[tool_use Bash] {"command": "grep -rn -i \"array_distinct\\|arraydistinct\\|list_distinct\\|ArrayCompact\\|array_compact\" tests/ | head -60; echo ---; grep -rn \"ArrayCompact\\|array_compact\" sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py sqlglot/parsers/*.py | head; echo ---; grep -n \"def array_compact_sql\" -A12 sqlglot/generators/duckdb.py", "description": "Find existing tests and mappings for distinct and compact arrays"}
[tool_result] tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNHEX('08000000000000000000' || h) END FROM (SELECT l, COALESCE(LIST_REDUCE(LIST_TRANSFORM(l, __x -> PRINTF('%02X%02X', CAST(__x AS INT) & 255, (CAST(__x AS INT) >> 8) & 255)),
…[4827 chars elided]…
03:ARRAY_COMPACT([1, null, 2]);
---
sqlglot/generators/duckdb.py:15:    array_compact_sql,
sqlglot/generators/duckdb.py:1503:        exp.ArrayCompact: array_compact_sql,
sqlglot/generators/duckdb.py:1505:            exp.ArrayCompact(this=exp.Array(expressions=e.expressions))
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/parsers/clickhouse.py:256:        "ARRAYCOMPACT": exp.ArrayCompact.from_arg_list,
---
[tool_use Bash] {"command": "grep -n \"ArrayAgg\\|\\\"LIST\\\"\\|LIST\\b\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head -30; grep -n \"def arrayagg_sql\" -A25 sqlglot/generators/duckdb.py | head -40; echo ---SF; sed -n 1035,1050p sqlglot/generators/snowflake.py; sed -n 300,312p tests/dialects/test_dialect.py", "description": "Inspect DuckDB ArrayAgg and LIST handling"}
[tool_result] ---SF
    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
        this = expression.this

        # If an ORDER BY clause is present, we need to remove it from ARRAY_AGG
        # and add it later as part of the WITHIN GROUP clause
        order = this if isinstance(this, exp.Order) else None
        if order:
            expression.set("this", order.this.pop())

        expr_sql = super().arrayagg_sql(expression)

        if order:
            expr_sql = self.sql(exp.WithinGroup(this=e
…[53 chars elided]…

            "CAST((1, 2, 3, 4) AS STRUCT<a: TINYINT, b: SMALLINT, c: INT, d: BIGINT>)",
            write={
                "clickhouse": "CAST((1, 2, 3, 4) AS Tuple(a Nullable(Int8), b Nullable(Int16), c Nullable(Int32), d Nullable(Int64)))",
            },
        )
        self.validate_all(
            "SELECT ARRAY_DISTINCT(x)",
            write={
                "clickhouse": "SELECT arrayDistinct(x)",
            },
        )
        self.validate_all(
            "CAST(a AS DATETIME)",
[tool_use Bash] {"command": "grep -rn \"[^_A-Z]LIST(\" tests/dialects/test_duckdb.py | head -30; echo; grep -rn \"LIST(\" tests/dialects/test_snowflake.py tests/test_transpile.py tests/dialects/test_dialect.py | grep -i duckdb | head; echo ---; grep -n \"ArrayAgg\\|ARRAY_AGG\" sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py | head; grep -n \"\\\"ARRAY_AGG\\\"\\|ArrayAgg\" sqlglot/parser.py | head -5", "description": "Check DuckDB test expectations for LIST and ARRAY_AGG"}
[tool_result] tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",

tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNHEX('08000000000000000000' || h) END
…[1930 chars elided]…
Agg):
sqlglot/generators/duckdb.py:3008:            # Move ORDER BY inside ARRAY_AGG by wrapping its argument with Order
sqlglot/generators/duckdb.py:3009:            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
sqlglot/generators/duckdb.py:3018:            # Generate the ARRAY_AGG function with ORDER BY and add FILTER clause if needed
323:        "ARRAYAGG": lambda args, dialect: exp.ArrayAgg(
326:        "ARRAY_AGG": lambda args, dialect: exp.ArrayAgg(
[tool_use Bash] {"command": "grep -n \"def filter_sql\" -A40 sqlglot/generator.py; grep -n \"def filter_sql\" -A5 sqlglot/generators/snowflake.py; grep -n \"\\\"FILTER\\\"\\|exp.Filter\" sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py", "description": "Read generic filter_sql used for aggregate FILTER clauses"}
[tool_result] 1818:    def filter_sql(self, expression: exp.Filter) -> str:
1819-        if self.AGGREGATE_FILTER_SUPPORTED:
1820-            this = self.sql(expression, "this")
1821-            where = self.sql(expression, "expression").strip()
1822-            return f"{this} FILTER({where})"
1823-
1824-        agg = expression.this
1825-        agg_arg = agg.this
1826-        cond = expression.expression.this
1827-        agg_arg.replace(exp.If(this=cond.copy(), true=agg_arg.copy()))
1828-        return se
…[1156 chars elided]…
h_storage else ""
1850-        tablespace = self.sql(expression, "tablespace")
1851-        tablespace = f" USING INDEX TABLESPACE {tablespace}" if tablespace else ""
1852-        on = self.sql(expression, "on")
1853-        on = f" ON {on}" if on else ""
1854-
1855-        return f"{using}{columns}{include}{with_storage}{tablespace}{partition_by}{where}{on}"
1856-
1857-    def index_sql(self, expression: exp.Index) -> str:
1858-        unique = "UNIQUE " if expression.args.get("unique") else ""
[tool_use Bash] {"command": "grep -n \"FUNCTIONS = {\" -A6 sqlglot/parsers/duckdb.py | head -12; grep -n \"    def \\w*_sql\" sqlglot/generators/snowflake.py | head -80 | tail -50; grep -n \"^from\\|^import\\|seq_get\" sqlglot/parsers/duckdb.py | head", "description": "Locate parser and generator insertion points"}
[tool_result] 72:    NO_PAREN_FUNCTIONS = {
73-        **parser.Parser.NO_PAREN_FUNCTIONS,
74-        TokenType.LOCALTIME: exp.Localtime,
75-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
76-        TokenType.CURRENT_CATALOG: exp.CurrentCatalog,
77-        TokenType.SESSION_USER: exp.SessionUser,
78-    }
--
102:    FUNCTIONS = {
103-        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
104-        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from
…[2532 chars elided]…
xpression: exp.Uniform) -> str:
1136:    def window_sql(self, expression: exp.Window) -> str:
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
22:    return exp.SortArray(this=seq_get(args, 0), asc=exp.false())
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"ANY_VALUE\": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),\n        \"ARRAY_PREPEND\": _build_array_prepend,", "new_string": "        \"ANY_VALUE\": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),\n        \"ARRAY_PREPEND\": _build_array_prepend,\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(this=seq_get(args, 0), check_null=False),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py", "old_string": "    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:", "new_string": "    def list_sql(self, expression: exp.List) -> str:\n        return self.sql(exp.ArrayAgg(this=expression.expression
…[39 chars elided]…
f, expression: exp.ArrayDistinct) -> str:\n        arr = expression.this\n\n        # DuckDB's LIST_DISTINCT drops NULLs, whereas Snowflake's ARRAY_DISTINCT keeps them\n        if expression.args.get(\"check_null\") is False:\n            arr = exp.ArrayCompact(this=arr)\n\n        return self.func(\"ARRAY_DISTINCT\", arr)\n\n    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT LIST(x) FROM t', 'SELECT LIST(DISTINCT x) FROM t', 'SELECT LIST_DISTINCT(x) FROM t', 'SELECT LIST_DISTINCT(LIST(x)) FROM t', 'SELECT LIST(x) FILTER (WHERE x IS NOT NULL) FROM t', 'SELECT
…[12 chars elided]…
CT x) FILTER (WHERE x IS NOT NULL) FROM t']:\n    for w in ['snowflake','duckdb']:\n        try: print(w, '|', sqlglot.transpile(s, read='duckdb', write=w)[0])\n        except Exception as e: print(w, 'ERR', type(e).__name__, e)\nprint(repr(sqlglot.parse_one('SELECT LIST_DISTINCT(x) FROM t', read='duckdb').selects[0]))\n\"", "description": "Check new DuckDB to Snowflake output for list functions"}
[tool_result] snowflake | SELECT ARRAY_AGG(x) FROM t
duckdb | SELECT LIST(x) FROM t
snowflake | SELECT ARRAY_AGG(DISTINCT x) FROM t
duckdb | SELECT LIST(DISTINCT x) FROM t
snowflake | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
duckdb | SELECT LIST_DISTINCT(x) FROM t
snowflake | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY_AGG(x))) FROM t
duckdb | SELECT LIST_DISTINCT(LIST(x)) FROM t
snowflake ERR AttributeError 'NoneType' object has no attribute 'replace'
duckdb | SELECT LIST(x) FILTER(WHERE NOT x IS NULL) FROM t
snowflake ERR AttributeError 'NoneType' object has no attribute 'replace'
duckdb | SELECT LIST(DISTINCT x) FILTER(WHERE NOT x IS NULL) FROM t
ArrayDistinct(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  check_null=False)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT COUNT(DISTINCT x) FILTER (WHERE x IS NOT NULL) FROM t', 'SELECT ARRAY_AGG(x) FILTER (WHERE x IS NOT NULL) FROM t','SELECT ARRAY_AGG(DISTINCT x) FILTER (WHERE x IS NOT NULL) FROM t']:\n    try: print(sqlglot.transpile(s, read='duckdb', write='snowflake')[0])\n    except Exception as e: print('ERR', e)\n\"; grep -rn \"FILTER\" tests/dialects/test_snowflake.py | head -5; sed -n 1,30p sqlglot/generators/snowflake.py | grep -n \"AGGREGATE_FILTER\"; grep -rn \"AGGREGATE_FILTER_SUPPORTED\" sqlglot | head -3", "description": "Compare FILTER behavior for other aggregates in Snowflake"}
[tool_result] SELECT COUNT(IFF(NOT x IS NULL, DISTINCT x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(NOT x IS NULL, DISTINCT x, NULL)) FROM t
tests/dialects/test_snowflake.py:111:                "duckdb": "SELECT (SELECT CASE WHEN l IS NULL OR LENGTH(l) = 0 THEN NULL WHEN LENGTH(l) <> LENGTH(LIST_FILTER(l, __v -> __v BETWEEN 0 AND 32767)) THEN NULL WHEN LENGTH(l) < 5 THEN UNHEX(PRINTF('%04X', LENGTH(l)) || h || REPEAT('00', GREATEST(0, 4 - LENGTH(l)) * 2)) ELSE UNH
…[1269 chars elided]…
) END",
tests/dialects/test_snowflake.py:670:            write={"duckdb": "SELECT LIST(DISTINCT col) FILTER(WHERE NOT col IS NULL) FROM t"},
tests/dialects/test_snowflake.py:675:                "duckdb": "SELECT LIST(DISTINCT col) FILTER(WHERE NOT col IS NULL) OVER (PARTITION BY grp) FROM t"
sqlglot/generator.py:402:    AGGREGATE_FILTER_SUPPORTED = True
sqlglot/generator.py:1819:        if self.AGGREGATE_FILTER_SUPPORTED:
sqlglot/generators/snowflake.py:383:    AGGREGATE_FILTER_SUPPORTED = False
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py", "old_string": "        agg = expression.this\n        agg_arg = agg.this\n        cond = expression.expression.this", "new_string": "        agg = expression.this\n        if isinstance(agg, exp.List):\n            agg = exp.ArrayAgg(this=agg.expressions[0])\n        agg_arg = agg.this\n        cond = expression.expression.this"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 686,700p tests/dialects/test_duckdb.py; sed -n 704,722p tests/dialects/test_duckdb.py", "description": "View DuckDB test style near list tests"}
[tool_result]         self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
        self.validate_all("SELECT * FROM 'x.y'", write={"duckdb": 'SELECT * FROM "x.y"'})
        self.validate_all(
            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
            read={"spark": "SELECT COLLECT_SET(sample_col) FROM sample_table"},
        )
        self.validate_all(
            "SELECT LIST_TRA
…[478 chars elided]…
 NULL, 3])",
            write={
                "duckdb": "LIST_FILTER([1, NULL, 2, NULL, 3], _u -> NOT _u IS NULL)",
                "snowflake": "ARRAY_COMPACT([1, NULL, 2, NULL, 3])",
            },
        )
        self.validate_all(
            "ARRAY_COMPACT(NULL)",
            write={
                "duckdb": "LIST_FILTER(NULL, _u -> NOT _u IS NULL)",
                "snowflake": "ARRAY_COMPACT(NULL)",
            },
        )
        self.validate_all(
            "ARRAY_COMPACT([])",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample_table\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x
…[517 chars elided]…
TINCT(x)\",\n            write={\n                \"duckdb\": \"LIST_DISTINCT(x)\",\n                \"snowflake\": \"ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            },\n        )\n        self.assertIsInstance(parse_one(\"LIST_DISTINCT(x)\", read=\"duckdb\"), exp.ArrayDistinct)\n        self.validate_all(\n            \"SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_duckdb.py | grep -n import", "description": "Check imports in DuckDB test file"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.assertIsInstance(parse_one(\"LIST_DISTINCT(x)\", read=\"duckdb\"), exp.ArrayDistinct)", "new_string": "        parse_one(\"LIST_DISTINCT(x)\", read=\"duckdb\").assert_is(exp.ArrayDistinct)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-195405-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Run DuckDB, Snowflake and dialect test files", "timeout": 300000}
[tool_result] ....................................................................................................................................................................................................................................... [ 97%]
......                                            [100%]
237 passed, 4976 subtests passed in 1.18s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py; echo \"exit=$?\"", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-00:25:09 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  53838       00:47 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-368d295949.log
ELAPSED: 48s
SUMMARY: 1092 passed, 17861 subtests passed in 47.97s
EXIT: 0
exit=0
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/generator.py tests/dialects/test_duckdb.py; $PY -m ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/generator.py tests/dialects/test_duckdb.py; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
4 files already formatted
 M sqlglot/generator.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] DuckDB `list(col)` and `list_distinct(col)` now transpile to Snowflake. The full suite passed after my last edit: `SUMMARY: 1092 passed, 17861 subtests passed in 47.97s`, `EXIT: 0`. Ruff check and format are clean on the four changed files.

**What changed**

- **`list(col)` → `ARRAY_AGG`.** DuckDB's `LIST` parses to `exp.List`. I added `list_sql` in `sqlglot/generators/snowflake.py` that emits `ARRAY_AGG`. Keeping `exp.List` on the DuckDB side preserves DuckDB identity (`LIST(DISTINCT ...) FILTER(...)` still round-trips, as an existing test requires).
- **`list_distinct` → `ARRAY_DISTINCT(ARR
…[1121 chars elided]…
set) keeps its current Snowflake output. A truthiness check would also change ClickHouse → Snowflake, and I believe ClickHouse keeps NULLs, so I avoided that.
- `LIST` maps to `ARRAY_AGG` for any source that produces `exp.List`, not only DuckDB. Only DuckDB produces it in this repo, as far as I can see.

**Not fixed (pre-existing)**

`LIST(DISTINCT x) FILTER (WHERE ...)` still produces invalid Snowflake SQL, `ARRAY_AGG(IFF(cond, DISTINCT x, NULL))`. The generic FILTER rewrite has the same bug for `COUNT(DISTINCT x) FILTER (...)`. The fix belongs in the generic `filter_sql`, so I left it alone.
