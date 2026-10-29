# trajectory base-1

final message:
DuckDB → Snowflake now transpiles `list(x)` to `ARRAY_AGG(x)` and `list_distinct(x)` to `ARRAY_DISTINCT(ARRAY_COMPACT(x))`, so the NULL-dropping semantics carry over. The full suite passes (1092 tests), and ruff check and format are clean. I haven't run the output against a live DuckDB or Snowflake.

```
SELECT list(x) FROM t           -> SELECT ARRAY_AGG(x) FROM t
SELECT list_distinct(x) FROM t  -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
```

**What changed**
- `sqlglot/parsers/duckdb.py`: `LIST` now parses to `exp.ArrayAgg`. Previously it fell through to the generic `exp.List`, which Snowflake emitted as an invalid `LIST(...)`. `LIST_DISTINCT` parses to `ArrayDistinct(ArrayCompact(x))`, which encodes "drops NULLs" in the AST.
- `sqlglot/generators/duckdb.py`: `arraydistinct_sql` drops a redundant inner `ArrayCompact` when emitting `LIST_DISTINCT`, since DuckDB's `LIST_DISTINCT` already removes NULLs. Without this, DuckDB → DuckDB round-trips of `list_distinct` would gain a `LIST_FILTER` wrapper.
- `tests/dialects/test_duckdb.py`: two `validate_all` cases next to the existing `LIST(DISTINCT ...)` test. I did not modify any existing test.

**Side effect to be aware of:** DuckDB → DuckDB output for `LIST(x)` is now `ARRAY_AGG(x)`. It's equivalent, and the existing tests still pass, but it's a visible text change.

**Pre-existing issue, not fixed here:** `list(x) FILTER(WHERE cond)` → Snowflake gives `ARRAY_AGG(IFF(cond, x, NULL))`. Snowflake's `ARRAY_AGG` keeps NULLs, so rows failing the filter appear as NULL elements instead of being excluded. The same happens for `ARRAY_AGG(x) FILTER(...)` on the untouched base commit. It's in the generic `filter_sql` path, so it needs its own change, probably `ARRAY_COMPACT(ARRAY_AGG(IFF(...)))`. I can take that on as a follow-up if you want.

I didn't commit anything.

## events
[tool_use Bash] {"command": "git status --short && grep -n -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayAgg\\|\\\"LIST\\\"\\|ArrayUniq\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py | head -80", "description": "Check status and grep for relevant expressions"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "pwd && ls && git status --short | head; ls sqlglot 2>/dev/null | head -3; ls -la | head -30", "description": "Inspect worktree layout"}
[tool_result] ~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1
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
__main__.py
_typing.py
total 3808
drwxr-xr-x@ 30 user  staff      960 Oct 28 11:40 .
drwxr-xr-x@  4 user  staff      128 Oct 28 11:40 ..
drwxr-xr-x@  3 user  staff  
…[1181 chars elided]…
@  9 user  staff      288 Oct 28 11:40 posts
-rw-r--r--@  1 user  staff     1328 Oct 28 11:40 pyproject.toml
-rw-r--r--@  1 user  staff      241 Oct 28 11:40 setup.cfg
-rw-r--r--@  1 user  staff      794 Oct 28 11:40 setup.py
drwxr-xr-x@ 29 user  staff      928 Oct 28 11:40 sqlglot
drwxr-xr-x@  2 user  staff       64 Oct 28 11:40 sqlglot-integration-tests
-rw-r--r--@  1 user  staff     7358 Oct 28 11:40 sqlglot.png
drwxr-xr-x@  5 user  staff      160 Oct 28 11:40 sqlglotc
[tool_use Bash] {"command": "grep -rn -i \"list_distinct\\|ListDistinct\\|ArrayUniqueAgg\\|ArrayAgg\\b\" sqlglot/ | grep -v \"\\.pyc\" | head -60", "description": "Search sqlglot for list/array aggregate expressions"}
[tool_result] sqlglot/generator.py:3583:    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
sqlglot/generator.py:3592:            "JSON_ARRAYAGG",
sqlglot/generator.py:5333:        array_agg_expr: exp.ArrayAgg,
sqlglot/generator.py:5341:            array_agg_expr: The ArrayAgg expression node
sqlglot/generator.py:5370:    def arrayagg_sql(self, expression: exp.ArrayAgg) -> str:
sqlglot/parser.py:323:        "ARRAYAGG": lambda args, dialect: exp.ArrayAgg(
sqlglot/parser.py:326:        "ARRAY_A
…[4106 chars elided]…
er.expressions)
sqlglot/generators/duckdb.py:3299:    def arrayuniqueagg_sql(self, expression: exp.ArrayUniqueAgg) -> str:
sqlglot/generators/duckdb.py:3313:        func = self.func("LIST_DISTINCT", arr)
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/generators/starrocks.py:91:        exp.ArrayAgg: rename_func("ARRAY_AGG"),
sqlglot/generators/mysql.py:140:        exp.ArrayAgg: rename_func("GROUP_CONCAT"),
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT array_agg(x) FROM t','SELECT array_distinct(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT list(x ORDER BY y) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:300])\n    print(' ->', e.sql('snowflake'))\n\"; grep -n \"ListDistinct\\|\\\"LIST\\\"\\|ARRAY_DISTINCT\\|ArrayDistinct\\|ArrayCompact\" sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/generators/duckdb.py sqlglot/parsers/snowflake.py sqlglot/dialects/*.py sqlglot/parser.py | head -30", "description": "Test current DuckDB to Snowflake behavior"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/generators/duckdb.py:1503:        exp.ArrayCompact: array_compact_sql,
sqlglot/generators/duckdb.py:1505:            exp.ArrayCompact(this=exp.Array(expressions=e.expressions))
sqlglot/generators/duckdb.py:3302:                this=exp.func("LIST", exp.Distinct(expressions=[expression.this])),
sqlglot/generators/duckdb.py:3311:    def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
sqlglot/generators/duckdb.py:3317:                "LIST_APPEND", exp.func("LIST_DISTINCT", exp.ArrayCompact(this=arr)), exp.Null()
sqlglot/dialects/dialect.py:2176:def array_compact_sql(self: Generator, expression: exp.ArrayCompact) -> str:
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parser.py:1720:        "LIST": lambda self: self._parse_analyze_list(),
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor q in ['SELECT list(x) FROM t','SELECT list_distinct(x) FROM t','SELECT array_agg(x) FROM t','SELECT array_distinct(x) FROM t', 'SELECT list(DISTINCT x) FROM t', 'SELECT list(x ORDER BY y) FROM t', 'SELECT list(x) FILTER(WHERE x IS NOT NULL) FROM t']:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.selects[0])[:300])\n    print(' ->', e.sql('snowflake'))\n\"", "description": "Test current DuckDB to Snowflake behavior"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/expressions/core.py", line 1097, in sql
    return Dialect.get_or_raise(dialect).generate(self, copy=copy, **opts)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckd
…[2854 chars elided]…
     this=Column(
        this=Identifier(this=x, quoted=False)),
      expressions=[
        Ordered(
          this=Column(
            this=Identifier(this=y, quoted=False)),
          nulls_first=False)])])
 -> SELECT LIST(x ORDER BY y) FROM t
Filter(
  this=List(
    expressions=[
      Column(
        this=Identifier(this=x, quoted=False))]),
  expression=Where(
    this=Not(
      this=Is(
        this=Column(
          this=Identifier(this=x, quoted=False)),
        expression=Null()))))
[tool_use Bash] {"command": "grep -rn \"class List\\b\\|class List(\\|exp\\.List\\b\" sqlglot/ | head; sed -n 765,780p sqlglot/parser.py; grep -n \"LIST\\|ArrayCompact\\|ARRAY_COMPACT\" sqlglot/parsers/duckdb.py sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py | head -30; sed -n 3295,3330p sqlglot/generators/duckdb.py; sed -n 60,100p sqlglot/expressions/aggregate.py", "description": "Inspect List expr and DuckDB/Snowflake array funcs"}
[tool_result] sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/expressions/array.py:34:class List(Expression, Func):
sqlglot/generators/materialize.py:47:    def list_sql(self, expression: exp.List) -> str:
        TokenType.SEMI,
        TokenType.WINDOW,
    }

    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS

    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS

    ARRAY_CONSTRUCTORS: t.ClassVar = {
        "ARRAY": exp.Array,
        "LIST": exp.List,
    }

    COMMENT_TABLE_ALIAS_TOKENS: t.Class
…[3597 chars elided]…
ggFunc, Binary):
    # Correlation divides by variance(column). If a column has 0 variance, the denominator
    # is 0 - some dialects return NaN (DuckDB) while others return NULL (Snowflake).
    # `null_on_zero_variance` is set to True at parse time for dialects that return NULL.
    arg_types = {"this": True, "expression": True, "null_on_zero_variance": False}


class Count(Expression, AggFunc):
    arg_types = {"this": False, "expressions": False, "big_int": False}
    is_var_len_args = True
[tool_use Bash] {"command": "grep -rn \"ARRAY_CONSTRUCTORS\\|exp.List\\b\\|List)\" sqlglot/ | grep -v \"^sqlglot/expressions/array.py:3[4]\" | head -30; sed -n 30,45p sqlglot/expressions/array.py; grep -n \"def list_sql\\|exp.List:\" sqlglot/generators/*.py | head; grep -n \"ARRAY_AGG\\|ArrayAgg\\|ARRAY_DISTINCT\\|ARRAY_COMPACT\" sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py | head -20", "description": "Trace ARRAY_CONSTRUCTORS and List handling"}
[tool_result] sqlglot/parser.py:147:    if exp_class == exp.Array and dialect.HAS_DISTINCT_ARRAY_CONSTRUCTORS:
sqlglot/parser.py:773:    ARRAY_CONSTRUCTORS: t.ClassVar = {
sqlglot/parser.py:775:        "LIST": exp.List,
sqlglot/parser.py:7476:            constructor_type = self.ARRAY_CONSTRUCTORS.get(this.name.upper())
sqlglot/dialects/dialect.py:625:    HAS_DISTINCT_ARRAY_CONSTRUCTORS = False
sqlglot/dialects/redshift.py:20:    HAS_DISTINCT_ARRAY_CONSTRUCTORS = True
sqlglot/generators/materialize.py:47:    d
…[670 chars elided]…
HIN GROUP (ORDER BY y) -> ARRAY_AGG(x ORDER BY y)
sqlglot/generators/duckdb.py:3001:        if isinstance(func, exp.ArrayAgg):
sqlglot/generators/duckdb.py:3008:            # Move ORDER BY inside ARRAY_AGG by wrapping its argument with Order
sqlglot/generators/duckdb.py:3009:            # ArrayAgg.this should become Order(this=ArrayAgg.this, expressions=order.expressions)
sqlglot/generators/duckdb.py:3018:            # Generate the ARRAY_AGG function with ORDER BY and add FILTER clause if needed
[tool_use Bash] {"command": "sed -n 7465,7495p sqlglot/parser.py; grep -n \"\\\"LIST\\\"\\|'LIST'\\|List\\b\" sqlglot/parsers/duckdb.py | head; sed -n 1,80p sqlglot/generators/duckdb.py | grep -n \"List\\|LIST\" ; grep -n \"Array.*Agg\\|ARRAY_AGG\" sqlglot/parsers/duckdb.py | head; sed -n 315,335p sqlglot/parser.py", "description": "Read array constructor parsing and ArrayAgg parser entries"}
[tool_result]         if bracket_kind == TokenType.L_BRACE:
            this = self.expression(
                exp.Struct(
                    expressions=self._kv_to_prop_eq(expressions=expressions, parse_map=parse_map)
                )
            )
        elif not this:
            this = build_array_constructor(
                exp.Array, args=expressions, bracket_kind=bracket_kind, dialect=self.dialect
            )
        else:
            constructor_type = self.ARRAY_CONSTRUCTORS.get(this.name.upp
…[1247 chars elided]…
xp.ArrayAgg(
            this=seq_get(args, 0), nulls_excluded=dialect.ARRAY_AGG_INCLUDES_NULLS is None or None
        ),
        "ARRAY_APPEND": build_array_append,
        "ARRAY_CAT": build_array_concat,
        "ARRAY_CONCAT": build_array_concat,
        "ARRAY_INTERSECT": lambda args: exp.ArrayIntersect(expressions=args),
        "ARRAY_INTERSECTION": lambda args: exp.ArrayIntersect(expressions=args),
        "ARRAY_PREPEND": build_array_prepend,
        "ARRAY_REMOVE": build_array_remove,
[tool_use Bash] {"command": "grep -rn \"class ArrayDistinct\\|class ArrayCompact\" -A4 sqlglot/expressions/; sed -n 410,420p sqlglot/parsers/snowflake.py; grep -rn \"check_null\" sqlglot/ | head -20; grep -n \"ArrayCompact\\|array_compact_sql\" -A12 sqlglot/dialects/dialect.py | sed -n 1,30p; grep -n \"ARRAY_AGG_INCLUDES_NULLS\\|ARRAY_DISTINCT\\|ARRAY_COMPACT\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/dialect.py", "description": "Examine ArrayDistinct, ArrayCompact and null handling flags"}
[tool_result] sqlglot/expressions/array.py:50:class ArrayCompact(Expression, Func):
sqlglot/expressions/array.py-51-    pass
sqlglot/expressions/array.py-52-
sqlglot/expressions/array.py-53-
sqlglot/expressions/array.py-54-class ArrayConcat(Expression, Func):
--
sqlglot/expressions/array.py:138:class ArrayDistinct(Expression, Func):
sqlglot/expressions/array.py-139-    arg_types = {"this": True, "check_null": False}
sqlglot/expressions/array.py-140-
sqlglot/expressions/array.py-141-
sqlglot/expressions/array.
…[2202 chars elided]…
()
2179-    return self.sql(
2180-        exp.ArrayFilter(
2181-            this=expression.this,
2182-            expression=exp.Lambda(this=cond, expressions=[lambda_id]),
2183-        )
2184-    )
2185-
2186-
2187-def remove_from_array_using_filter(self: Generator, expression: exp.ArrayRemove) -> str:
2188-    lambda_id = exp.to_identifier("_u")
sqlglot/dialects/snowflake.py:25:    ARRAY_AGG_INCLUDES_NULLS = None
sqlglot/dialects/dialect.py:647:    ARRAY_AGG_INCLUDES_NULLS: bool | None = True
[tool_use Bash] {"command": "grep -rn -i \"list_distinct\\|LIST(\\|list(\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | grep -iv \"list_\\|_list(\\|tolist\" | head -40; grep -rn -i \"list_distinct\" tests/ | wc -l; grep -n \"def arrayagg_sql\" -A12 sqlglot/generators/snowflake.py | head -30; grep -n \"def arraydistinct\\|ArrayDistinct\\|ArrayCompact\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py", "description": "Find existing tests and Snowflake array generators"}
[tool_result] tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
tests/dialects/test_snowflake.py:670:            write={"duckdb": "SELECT LIST(DISTINCT col) FILTER(WHERE NOT col IS NULL) FROM t"},
tests/dialects/test_snowflake.py:675:                "duckdb": "SELECT LIST(DISTINCT col) FILTER(WHERE NOT col IS NULL) OVER (PARTITION BY grp) FROM t"
tests/dialects/test_snowflake.py:2271:                "duckdb": "(SELECT JSON_
…[1171 chars elided]…
 from ARRAY_AGG
1039-        # and add it later as part of the WITHIN GROUP clause
1040-        order = this if isinstance(this, exp.Order) else None
1041-        if order:
1042-            expression.set("this", order.this.pop())
1043-
1044-        expr_sql = super().arrayagg_sql(expression)
1045-
1046-        if order:
1047-            expr_sql = self.sql(exp.WithinGroup(this=expr_sql, expression=order))
sqlglot/parsers/snowflake.py:414:        "ARRAY_DISTINCT": lambda args: exp.ArrayDistinct(
[tool_use Bash] {"command": "sed -n 684,696p tests/dialects/test_duckdb.py; grep -rn -i \"list_distinct\" tests/ ; grep -rn \"LIST\\[\\|LIST(\" tests/dialects/test_duckdb.py | head -20", "description": "View DuckDB LIST test context and list_distinct tests"}
[tool_result]         self.validate_all("0x1010", write={"": "0 AS x1010"})
        self.validate_identity("x ~ y", "REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("x !~ y", "NOT REGEXP_FULL_MATCH(x, y)")
        self.validate_identity("REGEXP_FULL_MATCH(x, y, 'i')")
        self.validate_all("SELECT * FROM 'x.y'", write={"duckdb": 'SELECT * FROM "x.y"'})
        self.validate_all(
            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
            read
…[2365 chars elided]…
IST_APPEND(LIST_DISTINCT(LIST_FILTER([1, 2, 2, 3, 1], _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT([1, 2, 2, 3, 1]) END",
tests/dialects/test_dialect.py:1770:                "duckdb": "SELECT CASE WHEN [1, 2, 3] IS NULL OR [2] IS NULL THEN NULL ELSE LIST_FILTER(LIST_DISTINCT([1, 2, 3]), e -> LENGTH(LIST_FILTER([2], x -> x IS NOT DISTINCT FROM e)) = 0) END",
tests/dialects/test_duckdb.py:690:            "SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table",
[tool_use Bash] {"command": "sed -n 120,152p sqlglot/parsers/duckdb.py; grep -n \"ArrayCompact\\|ARRAY_COMPACT\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT LIST(DISTINCT x) FROM t','SELECT ARRAY_COMPACT(x)']:\n  print(sqlglot.transpile(q, read='duckdb', write='snowflake'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))', read='snowflake', write='duckdb'))\nprint(sqlglot.transpile('SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))', read='snowflake', write='snowflake'))\n\"", "description": "View DuckDB function map and check Snowflake array compact"}
[tool_result]         "EDITDIST3": exp.Levenshtein.from_arg_list,
        "ENCODE": lambda args: exp.Encode(
            this=seq_get(args, 0), charset=exp.Literal.string("utf-8")
        ),
        "EPOCH": exp.TimeToUnix.from_arg_list,
        "EPOCH_MS": lambda args: exp.UnixToTime(this=seq_get(args, 0), scale=exp.UnixToTime.MILLIS),
        "GENERATE_SERIES": _build_generate_series(),
        "GET_CURRENT_TIME": exp.CurrentTime.from_arg_list,
        "GET_BIT": lambda args: exp.Getbit(
            this=se
…[1264 chars elided]…
AKE_DATE": exp.DateFromParts.from_arg_list,
        "MAKE_TIME": exp.TimeFromParts.from_arg_list,
['SELECT LIST(DISTINCT x) FROM t']
['SELECT ARRAY_COMPACT(x)']
['SELECT CASE WHEN ARRAY_LENGTH(LIST_FILTER(x, _u -> NOT _u IS NULL)) <> LIST_COUNT(LIST_FILTER(x, _u -> NOT _u IS NULL)) THEN LIST_APPEND(LIST_DISTINCT(LIST_FILTER(LIST_FILTER(x, _u -> NOT _u IS NULL), _u -> NOT _u IS NULL)), NULL) ELSE LIST_DISTINCT(LIST_FILTER(x, _u -> NOT _u IS NULL)) END']
['SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))']
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"LIST_APPEND\": exp.ArrayAppend.from_arg_list,\n        \"LIST_CONCAT\": parser.build_array_concat,\n        \"LIST_CONTAINS\": exp.ArrayContains.from_arg_list,\n        \"LIST_COSINE_DISTANCE\": exp.Co
…[382 chars elided]…
,\n        \"LIST_COSINE_DISTANCE\": exp.CosineDistance.from_arg_list,\n        \"LIST_DISTANCE\": exp.EuclideanDistance.from_arg_list,\n        # LIST_DISTINCT drops NULLs, unlike ArrayDistinct which keeps them\n        \"LIST_DISTINCT\": lambda args: exp.ArrayDistinct(\n            this=exp.ArrayCompact(this=seq_get(args, 0))\n        ),\n        \"LIST_FILTER\": exp.ArrayFilter.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now the DuckDB generator: avoid a redundant `LIST_FILTER` wrapper when round-tripping `LIST_DISTINCT`, since DuckDB's `LIST_DISTINCT` already drops NULLs.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py", "old_string": "        arr = expression.this\n        func = self.func(\"LIST_DISTINCT\", arr)\n\n        if expression.args.get(\"check_null\"):", "new_string": "        arr = expression.this\n        # LIST_DISTINCT already drops NULLs, so an inner ArrayCompact is redundant\n        func = self.func(\n            \"LIST_DISTINCT\", arr.this if isinstance(arr, exp.ArrayCompact) else arr\n        )\n\n        if expression.args.get(\"check_null\"):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = ['SELECT list(x) FROM t','SELECT list(DISTINCT x) FROM t','SELECT list(x ORDER BY y) FROM t','SELECT list_distinct(x) FROM t','SELECT list(x) FILTER(WHERE x IS NOT NULL) FROM t','SELECT list_distinct(list(x)) FROM t']\nfor q in cases:\n  for w in ['snowflake','duckdb','spark']:\n    try: print(w, '|', sqlglot.transpile(q, read='duckdb', write=w)[0])\n    except Exception as e: print(w, 'ERR', type(e).__name__, e)\n\"", "description": "Verify DuckDB list and list_distinct transpilation"}
[tool_result] snowflake | SELECT ARRAY_AGG(x) FROM t
duckdb | SELECT ARRAY_AGG(x) FROM t
spark | SELECT COLLECT_LIST(x) FROM t
snowflake | SELECT ARRAY_AGG(DISTINCT x) FROM t
duckdb | SELECT ARRAY_AGG(DISTINCT x) FROM t
spark | SELECT COLLECT_LIST(DISTINCT x) FROM t
snowflake | SELECT ARRAY_AGG(x) WITHIN GROUP (ORDER BY y) FROM t
duckdb | SELECT ARRAY_AGG(x ORDER BY y) FROM t
spark | SELECT COLLECT_LIST(x) FROM t
snowflake | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
duckdb | SELECT LIST_DISTINCT(x) FROM t
spark | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
snowflake | SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t
duckdb | SELECT ARRAY_AGG(x) FILTER(WHERE NOT x IS NULL) FROM t
spark | SELECT COLLECT_LIST(x) FILTER(WHERE NOT x IS NULL) FROM t
snowflake | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(ARRAY_AGG(x))) FROM t
duckdb | SELECT LIST_DISTINCT(ARRAY_AGG(x)) FROM t
spark | SELECT ARRAY_DISTINCT(ARRAY_COMPACT(COLLECT_LIST(x))) FROM t
[tool_use Bash] {"command": "sed -n 1800,1835p sqlglot/generator.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FILTER(WHERE x IS NOT NULL) FROM t', read='duckdb', write='snowflake')[0])\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FILTER(WHERE x > 1) FROM t', read='duckdb', write='snowflake')[0])\nprint(sqlglot.transpile('SELECT ARRAY_AGG(x) FILTER(WHERE x > 1) FROM t', read='duckdb', write='snowflake')[0])\n\"; git stash list | head -2; git diff --stat", "description": "Inspect filter_sql handling and pre-existing behavior"}
[tool_result]     def fetch_sql(self, expression: exp.Fetch) -> str:
        direction = expression.args.get("direction")
        direction = f" {direction}" if direction else ""
        count = self.sql(expression, "count")
        count = f" {count}" if count else ""
        limit_options = self.sql(expression, "limit_options")
        limit_options = f"{limit_options}" if limit_options else " ROWS ONLY"
        return f"{self.seg('FETCH')}{direction}{count}{limit_options}"

    def limitoptions_sql(self, e
…[844 chars elided]…
ression: exp.Hint) -> str:
        if not self.QUERY_HINTS:
            self.unsupported("Hints are not supported")
            return ""

        return f" /*+ {self.expressions(expression, sep=self.QUERY_HINT_SEP).strip()} */"
SELECT ARRAY_AGG(IFF(NOT x IS NULL, x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(x > 1, x, NULL)) FROM t
SELECT ARRAY_AGG(IFF(x > 1, x, NULL)) FROM t
 sqlglot/generators/duckdb.py | 5 ++++-
 sqlglot/parsers/duckdb.py    | 5 +++++
 2 files changed, 9 insertions(+), 1 deletion(-)
[assistant] Core transpilation works. The `FILTER(WHERE …)` output is a pre-existing issue in ArrayAgg→Snowflake (not caused by this change), which I'll report rather than widen scope. Now I'll add tests next to the existing DuckDB `LIST` test.
[tool_use Bash] {"command": "awk 'NR<=690 && /    def test_/ {l=NR\": \"$0} END{}; NR==690{print l}' tests/dialects/test_duckdb.py", "description": "Locate enclosing DuckDB test method"}
[tool_result] 13:     def test_duckdb(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT LIST(DISTINCT sample_col) FILTER(WHERE NOT sample_col IS NULL) FROM sample_table\",\n            read={\"spark\": \"SELECT COLLECT_SET(sample_col) FROM sample
…[430 chars elided]…
RRAY_AGG(x)\", \"snowflake\": \"SELECT ARRAY_AGG(x)\"},\n        )\n        self.validate_all(\n            \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            read={\"duckdb\": \"SELECT LIST_DISTINCT(x)\"},\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x)\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            },\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] I wrote those validate_all calls with the wrong parse direction (the `sql` argument is parsed as DuckDB). Let me restructure them so the DuckDB input is the primary SQL.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT ARRAY_AGG(x)\",\n            read={\"duckdb\": \"SELECT LIST(x)\"},\n            write={\"duckdb\": \"SELECT ARRAY_AGG(x)\", \"snowflake\": \"SELECT ARRAY_AGG
…[389 chars elided]…
ll(\n            \"SELECT LIST(x)\",\n            write={\"duckdb\": \"SELECT ARRAY_AGG(x)\", \"snowflake\": \"SELECT ARRAY_AGG(x)\"},\n        )\n        self.validate_all(\n            \"SELECT LIST_DISTINCT(x)\",\n            write={\n                \"duckdb\": \"SELECT LIST_DISTINCT(x)\",\n                \"snowflake\": \"SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-114049-duckdb-snowflake-duckdb-s-list-c/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the full project check, using the command from the project's harness config.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
............................................. [ 11%]
........................................................................................................................................... [ 24%]
....................................................................................................................... [ 35%]
............................. [ 37%]
.............................. [ 40%]
.........
…[319 chars elided]…
................................................................................................... [ 76%]
............................................. [ 80%]
................................ [ 83%]
................ [ 85%]
....................................... [ 88%]
..........................................................................................................................                                                        [100%]
1092 passed, 17861 subtests passed in 53.01s
[assistant] All 1092 tests pass. Let me run the project's style checks on the changed files too.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff --version && $P/ruff check sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py && $P/ruff format --check sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -15; git diff", "description": "Run ruff lint/format checks and show diff"}
[tool_result] ruff 0.15.6
All checks passed!
Would reformat: sqlglot/generators/duckdb.py
1 file would be reformatted, 2 files already formatted
diff --git a/sqlglot/generators/duckdb.py b/sqlglot/generators/duckdb.py
index 2c8f9dfef..87f68c320 100644
--- a/sqlglot/generators/duckdb.py
+++ b/sqlglot/generators/duckdb.py
@@ -3310,7 +3310,10 @@ class DuckDBGenerator(generator.Generator):
 
     def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
         arr = expression.this
-        func = self
…[1971 chars elided]…
  "SELECT LIST(x)",
+            write={"duckdb": "SELECT ARRAY_AGG(x)", "snowflake": "SELECT ARRAY_AGG(x)"},
+        )
+        self.validate_all(
+            "SELECT LIST_DISTINCT(x)",
+            write={
+                "duckdb": "SELECT LIST_DISTINCT(x)",
+                "snowflake": "SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x))",
+            },
+        )
         self.validate_all(
             "SELECT LIST_TRANSFORM(STR_SPLIT_REGEX('abc , dfg ', ','), x -> TRIM(x))",
             write={
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/ruff format --diff sqlglot/generators/duckdb.py 2>&1 | head -20", "description": "Preview ruff format change for generator"}
[tool_result] --- sqlglot/generators/duckdb.py
+++ sqlglot/generators/duckdb.py
@@ -3311,9 +3311,7 @@
     def arraydistinct_sql(self, expression: exp.ArrayDistinct) -> str:
         arr = expression.this
         # LIST_DISTINCT already drops NULLs, so an inner ArrayCompact is redundant
-        func = self.func(
-            "LIST_DISTINCT", arr.this if isinstance(arr, exp.ArrayCompact) else arr
-        )
+        func = self.func("LIST_DISTINCT", arr.this if isinstance(arr, exp.ArrayCompact) else arr)
 
         if expression.args.get("check_null"):
             add_null_to_array = exp.func(

1 file would be reformatted
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; $P/ruff format sqlglot/generators/duckdb.py && $P/ruff format --check sqlglot/ tests/dialects/test_duckdb.py | tail -1 && $P/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_dialect.py 2>&1 | tail -2", "description": "Apply formatting and rerun related dialect tests", "timeout": 600000}
[tool_result] 1 file reformatted
175 files already formatted
......                                            [100%]
237 passed, 4976 subtests passed in 1.02s
[This command modified 1 file you've previously read: sqlglot/generators/duckdb.py. Call Read before editing.]
[assistant] DuckDB → Snowflake now transpiles `list(x)` to `ARRAY_AGG(x)` and `list_distinct(x)` to `ARRAY_DISTINCT(ARRAY_COMPACT(x))`, so the NULL-dropping semantics carry over. The full suite passes (1092 tests), and ruff check and format are clean. I haven't run the output against a live DuckDB or Snowflake.

```
SELECT list(x) FROM t           -> SELECT ARRAY_AGG(x) FROM t
SELECT list_distinct(x) FROM t  -> SELECT ARRAY_DISTINCT(ARRAY_COMPACT(x)) FROM t
```

**What changed**
- `sqlglot/parsers/duckdb.py`: `LIST` now parses to `exp.ArrayAgg`. Previously it fell through to the generic `exp.List`, which 
…[642 chars elided]…
ARRAY_AGG(x)`. It's equivalent, and the existing tests still pass, but it's a visible text change.

**Pre-existing issue, not fixed here:** `list(x) FILTER(WHERE cond)` → Snowflake gives `ARRAY_AGG(IFF(cond, x, NULL))`. Snowflake's `ARRAY_AGG` keeps NULLs, so rows failing the filter appear as NULL elements instead of being excluded. The same happens for `ARRAY_AGG(x) FILTER(...)` on the untouched base commit. It's in the generic `filter_sql` path, so it needs its own change, probably `ARRAY_COMPACT(ARRAY_AGG(IFF(...)))`. I can take that on as a follow-up if you want.

I didn't commit anything.
