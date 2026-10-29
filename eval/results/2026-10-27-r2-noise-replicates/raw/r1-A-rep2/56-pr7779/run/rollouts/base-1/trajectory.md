# trajectory base-1

final message:
The four StarRocks forms now generate StarRocks-native SQL, and StarRocks' own forms parse back. The full suite passes (1126 tests) and ruff and mypy are clean. I haven't committed.

- **`MIN_BY` / `MAX_BY`:** generated as `MIN_BY`/`MAX_BY` instead of `ARG_MIN`/`ARG_MAX`, including `OVER (...)`. The StarRocks docs I fetched don't mention window support, so the window form is unverified against a live server.
- **`MAP`:** `MAP(k1, v1, ...)` now parses, and literal two-array forms from DuckDB, Presto and Spark are interleaved into it. Two-array maps built from columns can't be interleaved, so they emit `MAP_FROM_ARRAYS(k, v)`, which StarRocks documents as 3.1+. That's a choice I made; say if you'd rather they error.
- **`ARRAY_CONTAINS_ALL`:** generated as `ARRAY_CONTAINS_ALL(a, b)` rather than `@>`. `ARRAY_HAS_ALL` also maps to it.
- **`TRIM`:** the StarRocks docs give only `trim(str[, characters])`, with no `FROM` form. So `TRIM(BOTH 'x' FROM s)` becomes `TRIM(s, 'x')`, LEADING becomes `LTRIM(s, 'x')`, and TRAILING becomes `RTRIM(s, 'x')`.

Changes are in `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py` and `tests/dialects/test_starrocks.py`.

Two things to know:
- `MAP(1)` (odd arity) now reaches `IndexError` from the shared `build_var_map`. Hive hits the same path. The input is invalid in StarRocks, so I left it alone.
- Nothing was run against a live StarRocks. The tests only check sqlglot's own output.

## events
[assistant] I'll start by reading the StarRocks dialect and how it inherits from MySQL and the base generator.
[tool_use Bash] {"command": "cat sqlglot/dialects/starrocks.py && git log --oneline -1 && grep -n \"MIN_BY\\|MAX_BY\\|ArgMin\\|ArgMax\\|ARRAY_CONTAINS_ALL\\|ArrayContainsAll\\|class Map\\b\\|class Map(\\|VarMap\\|MAP_FROM_ENTRIES\\|class Trim\" sqlglot/expressions.py | head -50", "description": "Read StarRocks dialect and find related expression classes"}
[tool_result] from __future__ import annotations

from sqlglot.dialects.mysql import MySQL
from sqlglot.generators.starrocks import StarRocksGenerator
from sqlglot.parsers.starrocks import StarRocksParser
from sqlglot.tokens import TokenType


class StarRocks(MySQL):
    STRICT_JSON_PATH_SYNTAX = False
    INDEX_OFFSET = 1

    class Tokenizer(MySQL.Tokenizer):
        KEYWORDS = {
            **MySQL.Tokenizer.KEYWORDS,
            "LARGEINT": TokenType.INT128,
        }

    Parser = StarRocksParser

    Generator = StarRocksGenerator
1171ba900 lithify: probe base
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"starrocks\\|StarRocks\" tests/ --include=*.py -l; ls tests/dialects | head -50; grep -rn \"ARRAY_CONTAINS_ALL\\|MIN_BY\\|MAX_BY\\|ArrayContainsAll\\|class ArgMax\\|class ArgMin\" sqlglot/ | head -30", "description": "Find StarRocks tests and related function mappings"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[assistant] The repo has `sqlglot/generators/` and `sqlglot/parsers/` packages, so the StarRocks logic lives there rather than in the dialect file. I'll read those and locate the expression classes.
[tool_use Bash] {"command": "cat sqlglot/generators/starrocks.py; echo ----; cat sqlglot/parsers/starrocks.py; echo ----; ls tests/dialects | grep -i \"star\\|mysql\"; echo ----; grep -rn \"ArgMax\\|ArgMin\\|ARG_MAX\\|ARG_MIN\\|ArrayContainsAll\\|ARRAY_CONTAINS_ALL\" sqlglot/ | head -40", "description": "Read StarRocks generator and parser, find related classes"}
[tool_result] from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_array_sql,
    property_sql,
)
from sqlglot.generators.mysql import MySQLGenerator


def _eliminate_between_in_delete(expression: exp.Expr) -> exp.Expr:
    """
    StarRocks doesn't support BETWEEN in DELETE statements, so we convert
    BETWEEN expressions to explicit comparisons.

…[18947 chars elided]…
ssion: exp.ArrayContainsAll) -> str:
sqlglot/generators/presto.py:268:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/presto.py:269:        exp.ArgMin: rename_func("MIN_BY"),
sqlglot/generators/snowflake.py:411:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/snowflake.py:412:        exp.ArgMin: rename_func("MIN_BY"),
sqlglot/generators/teradata.py:73:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/teradata.py:74:        exp.ArgMin: rename_func("MIN_BY"),
[assistant] Doris already emits `MIN_BY`/`MAX_BY`, and MySQL has an `arraycontainsall_sql`. I'll read those, plus the MySQL trim/map handling and the existing StarRocks tests.
[tool_use Bash] {"command": "sed -n 640,670p sqlglot/generators/mysql.py; echo ----MYSQL TRIM/MAP; grep -n \"Trim\\|trim\\|VarMap\\|\\\"MAP\\\"\\|Map\\b\\|def _parse_max_min_by\\|ArgMax\\|ArgMin\" sqlglot/generators/mysql.py sqlglot/parsers/mysql.py sqlglot/parser.py sqlglot/generators/doris.py sqlglot/generators/starrocks.py sqlglot/generator.py | head -60; echo ----DORIS; sed -n 1,80p sqlglot/generators/doris.py | grep -n \"Trim\\|MAP\\|Map\\|ArgM\" ; echo ----TESTS; cat tests/dialects/test_starrocks.py | head -150; wc -l tests/dialects/test_starrocks.py", "description": "Inspect MySQL/parser/generator internals and StarRocks tests"}
[tool_result]                     break

        return locations

    def computedcolumnconstraint_sql(self, expression: exp.ComputedColumnConstraint) -> str:
        persisted = "STORED" if expression.args.get("persisted") else "VIRTUAL"
        return f"GENERATED ALWAYS AS ({self.sql(expression.this.unnest())}) {persisted}"

    def array_sql(self, expression: exp.Array) -> str:
        self.unsupported("Arrays are not supported by MySQL")
        return self.function_fallback_sql(expression)

    def arra
…[10879 chars elided]…
ELECT APPROX_COUNT_DISTINCT(a) FROM x")
        self.validate_identity("SELECT [1, 2, 3]")
        self.validate_identity(
            """SELECT CAST(PARSE_JSON(fieldvalue) -> '00000000-0000-0000-0000-00000000' AS VARCHAR) AS `code` FROM (SELECT '{"00000000-0000-0000-0000-00000000":"code01"}') AS t(fieldvalue)"""
        )
        self.validate_identity(
            "SELECT text FROM example_table", write_sql="SELECT `text` FROM example_table"
        )

     335 tests/dialects/test_starrocks.py
[assistant] Next I'll probe the current output for each of the four requested behaviours to see what's actually broken before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_sr.py <<'EOF'\nimport sqlglot\ncases = [\n (\"spark\", \"SELECT MIN_BY(x, y) FROM t\"),\n (\"spark\", \"SELECT MAX_BY(x, y) FROM t\"),\n (\"snowflake\", \"SELECT MIN_BY(x, y) FROM t\"),\n (\"starrocks\", \"SELECT MIN_BY(x, y) FROM t\"),\n (\"starrocks\", \"SELECT MAX_BY(x, y) FROM t\"),\n (\
…[1544 chars elided]…
d, sql in cases:\n    try:\n        out = sqlglot.transpile(sql, read=read, write=\"starrocks\")[0]\n    except Exception as e:\n        out = f\"ERR {type(e).__name__}: {e}\"\n    print(f\"[{read}] {sql}\\n    -> {out}\")\nfor sql in [\"SELECT MAP(1,2)\", \"SELECT MAP('a', 1)\"]:\n    pass\nEOF\n$PY -I /tmp/probe_sr.py", "description": "Probe current StarRocks output for the requested functions"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/probe_sr.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The env python isn't seeing this worktree's `sqlglot`. I'll check which copy it imports, since an editable install could point at a different checkout.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sys;print(sqlglot.__file__)\"; $PY -c \"import sqlglot\" 2>&1; cd /tmp && $PY -c \"import sqlglot;print(sqlglot.__file__)\" 2>&1 | tail -1", "description": "Check which sqlglot the env imports"}
[tool_result] ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/__init__.py
ModuleNotFoundError: No module named 'sqlglot'
Shell cwd was reset to ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1
[assistant] Running from the worktree root picks up the local `sqlglot`. I'll run the probe from there.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"$(cat /tmp/probe_sr.py)\"", "description": "Run probe of current StarRocks transpilation output"}
[tool_result] [spark] SELECT MIN_BY(x, y) FROM t
    -> SELECT ARG_MIN(x, y) FROM t
[spark] SELECT MAX_BY(x, y) FROM t
    -> SELECT ARG_MAX(x, y) FROM t
[snowflake] SELECT MIN_BY(x, y) FROM t
    -> SELECT ARG_MIN(x, y) FROM t
[starrocks] SELECT MIN_BY(x, y) FROM t
    -> SELECT ARG_MIN(x, y) FROM t
[starrocks] SELECT MAX_BY(x, y) FROM t
    -> SELECT ARG_MAX(x, y) FROM t
[starrocks] SELECT ARG_MIN(x, y) FROM t
    -> SELECT ARG_MIN(x, y) FROM t
[starrocks] SELECT MAX_BY(x, y) OVER (PARTITION BY g) FROM t
  
…[1847 chars elided]…
  -> SELECT RTRIM('a  ')
[mysql] SELECT TRIM(LEADING 'x' FROM 'xax')
    -> SELECT TRIM(LEADING 'x' FROM 'xax')
[mysql] SELECT TRIM(BOTH 'x' FROM 'xax')
    -> SELECT TRIM(BOTH 'x' FROM 'xax')
[duckdb] SELECT TRIM('x' FROM 'xax')
    -> SELECT TRIM('x' FROM 'xax')
[snowflake] SELECT TRIM('xax', 'x')
    -> SELECT TRIM('x' FROM 'xax')
[spark] SELECT TRIM(BOTH 'x' FROM 'xax')
    -> SELECT TRIM(BOTH 'x' FROM 'xax')
[postgres] SELECT TRIM(BOTH 'x' FROM 'xax')
    -> SELECT TRIM(BOTH 'x' FROM 'xax')
[assistant] The probe confirms four separate gaps:

- `MIN_BY`/`MAX_BY` come out as `ARG_MIN`/`ARG_MAX`.
- Multi-argument `MAP(k, v, ...)` is rejected when parsed, and the two-array form is emitted as-is.
- `ARRAY_CONTAINS_ALL` comes out as `@>`.
- `TRIM` with a character set is emitted in the `FROM` form.

Before I pick a TRIM replacement I need to know what StarRocks actually accepts, and I need the MAP parsing path. I'll look at the parser and generator internals while checking the StarRocks docs.
[tool_use Bash] {"command": "sed -n 40,60p sqlglot/parser.py; grep -n '\"MAP\"\\|\"MAP_FROM\\|StarMap\\|MapFromEntries' sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generator.py sqlglot/generators/*.py | head -30; sed -n 3605,3640p sqlglot/generator.py; grep -n \"class VarMap\\|class Map(\\|class StarMap\\|class ToMap\" -A6 sqlglot/expressions/*.py", "description": "Inspect MAP builders, trim generator, and map expression classes"}
[tool_result] # Used to detect alphabetical characters and +/- in timestamp literals
TIME_ZONE_RE: Pattern[str] = re.compile(r":.*?[a-zA-Z\+\-]")


def build_var_map(args: BuilderArgs) -> exp.StarMap | exp.VarMap:
    if len(args) == 1 and args[0].is_star:
        return exp.StarMap(this=args[0])

    keys: list[ExpOrStr] = []
    values: list[ExpOrStr] = []
    for i in range(0, len(args), 2):
        keys.append(args[i])
        values.append(args[i + 1])

    return exp.VarMap(keys=exp.array(*keys, copy=Fa
…[3948 chars elided]…
s
sqlglot/expressions/array.py-337-
sqlglot/expressions/array.py-338-
sqlglot/expressions/array.py:339:class VarMap(Expression, Func):
sqlglot/expressions/array.py-340-    arg_types = {"keys": True, "values": True}
sqlglot/expressions/array.py-341-    is_var_len_args = True
sqlglot/expressions/array.py-342-
sqlglot/expressions/array.py-343-    @property
sqlglot/expressions/array.py-344-    def keys(self) -> list[Expr]:
sqlglot/expressions/array.py-345-        return self.args["keys"].expressions
[assistant] Both `Map` and `VarMap` need handling. Before writing the generator I need to confirm the StarRocks-side facts: which `TRIM` forms it accepts, the `MAP` constructor and whether a two-array form exists, and `MIN_BY`/`ARRAY_CONTAINS_ALL`. I'll check the official docs in parallel.
[tool_use Bash] {"command": "grep -rn \"starrocks\" tests/dialects/test_dialect.py tests/test_transpile.py 2>/dev/null | grep -i \"trim\\|map(\" | head; grep -rln \"MAP_FROM_ARRAYS\\|map_from_arrays\" sqlglot tests | head; grep -rn \"TRIM\" tests/dialects/test_mysql.py | head -5", "description": "Search repo for existing StarRocks trim/map test expectations"}
[tool_result] sqlglot/parsers/spark2.py
sqlglot/generators/spark2.py
tests/test_expressions.py
tests/dialects/test_presto.py
tests/dialects/test_spark.py
tests/dialects/test_mysql.py:308:        self.validate_identity("SELECT TRIM(LEADING 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:309:        self.validate_identity("SELECT TRIM(TRAILING 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:310:        self.validate_identity("SELECT TRIM(BOTH 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:311:        self.validate_identity("SELECT TRIM('bla' FROM ' XXX ')")
[tool_use Bash] {"command": "echo placeholder", "description": "No-op placeholder before web research"}
[tool_result] placeholder
[tool_use WebSearch] {"query": "StarRocks trim function syntax str ltrim rtrim documentation", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks map() function syntax map(key, value, ...) map_from_arrays", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks max_by min_by array_contains_all function documentation", "mode": "standard"}
[tool_result] Web search results for query: "StarRocks trim function syntax str ltrim rtrim documentation"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/zh/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.celerdata.com",
…[2634 chars elided]…
 examples rather than a clear signature in these results. `trim("xxabcdxx", "x")` returns `abcd`, and `trim("abcd", "ad")` returns `bc`. (Sources: index 5-1 and index 9-1.)

I did not find the exact `trim` signature in these results, so check the official trim page for the full parameter list. The search also returned unrelated vendor docs (Palo Alto Cortex, AtScale, Vertica), which I excluded.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks max_by min_by array_contains_all function documentation"

Links: [{"title":"Function list","url":"https://docs.starrocks.io/docs/3.1/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/3.0/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/function-list/"},{"title":"array contains all","url":"https://docs.starrocks.i
…[1997 chars elided]…
er aggregate functions, but the snippets had no syntax or behavior details. You can find a built-in function based on the following categories: followed by a list that includes max_by and min_by.

I didn't find a dedicated StarRocks page for `max_by` or `min_by`, so their semantics are unverified here. The next step would be to search for the StarRocks `max_by` aggregate-function page directly.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks map() function syntax map(key, value, ...) map_from_arrays"

Links: [{"title":"map from arrays","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.celerdata.com/BYOC/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays"},{
…[2838 chars elided]…
emoved when MAP data is loaded, and that mixed key or value types are coerced to a common supertype. (Source: 14-10 to 14-12, 14-14.)

Gap: I didn't find an official `map()` function reference page, so the variadic syntax above comes from the data-type documentation rather than a dedicated function page. Checking the StarRocks `map` function docs directly would confirm the exact argument rules.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] The search results settle most of the design:

- `array_contains_all(arr1, arr2)` is StarRocks-native.
- `map_from_arrays(keys, values)` is StarRocks' two-array form (3.1+), and `map(k1, v1, ...)` is the variadic constructor.
- `ltrim`/`rtrim`/`trim` take an optional `characters` argument, so there's no `FROM` syntax.

I want the exact `trim` and `max_by` signatures from the official pages rather than from search snippets, so I'll fetch them.
[tool_use ToolSearch] {"query": "select:WebFetch", "max_results": 1}
[tool_result] 
[tool_use WebFetch] {"url": "https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim", "prompt": "Give the exact function signature(s) for trim, including whether it accepts a second 'characters' argument, whether it supports any 'BOTH/LEADING/TRAILING ... FROM' syntax, and 2-3 examples with outputs. Quote the syntax block verbatim."}
[tool_use WebFetch] {"url": "https://docs.starrocks.io/docs/sql-reference/sql-functions/aggregate-functions/max_by/", "prompt": "Give the exact syntax block verbatim, the argument count, and whether it supports a window/OVER clause. Include the version it was introduced in if stated."}
[tool_result] **Syntax:** `max_by(x,y)`

**Argument count:** 2 (`x`, an expression of any type, and `y`, an orderable expression).

**Window/OVER clause:** The page doesn't say whether `max_by` supports a window or `OVER` clause.

**Introduced:** The page says it is "supported from v2.5."
[tool_result] **Syntax**

The page gives this syntax block:

```
VARCHAR trim(VARCHAR str[, VARCHAR characters])
```

- **Two-argument form:** Yes. The optional second argument, `characters`, is a VARCHAR listing which characters to remove. If omitted, spaces are removed. An empty string here returns an error.
- **`BOTH/LEADING/TRAILING ... FROM` syntax:** Not documented on this page. The only supported forms are `trim(str)` and `trim(str, characters)`.

**Examples**

1. Remove spaces from both ends:
   `trim("   ab c  ")` → `ab c`
2. Remove the characters `a` and `d` from both ends:
   `trim("abcd", "ad")` → `bc`
3. Remove the character `x` from both ends:
   `trim("xxabcdxx", "x")` → `abcd`
[assistant] Both pages are confirmed. `trim(str[, characters])` has no `FROM` form, so I'll map BOTH to `TRIM(str, chars)`, LEADING to `LTRIM`, and TRAILING to `RTRIM`. `max_by` takes two arguments and the page doesn't mention `OVER`, so I'll keep the window form as you asked and say so in the summary.

Next I need the existing MySQL `trim_sql`, the arg shapes of `ArgMax`/`ArgMin`, and the AST each source dialect produces for `MAP`.
[tool_use Bash] {"command": "grep -n \"def trim_sql\" -A22 sqlglot/dialects/dialect.py; sed -n 55,70p sqlglot/expressions/aggregate.py; sed -n 9795,9815p sqlglot/parser.py; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d,s in [('duckdb',\\\"SELECT MAP(['a'],[1])\\\"),('presto','SELECT MAP(ARRAY[\\'a\\'],ARRAY[1])'),('spark',\\\"SELECT MAP('a',1,'b',2)
…[3 chars elided]…
"),('starrocks',\\\"SELECT MAP('a',1,'b',2)\\\"),('starrocks','SELECT MAP_FROM_ARRAYS([1],[2])'),('duckdb','SELECT MAP(col_k, col_v)'),('spark','SELECT MAP_FROM_ARRAYS(a,b)')]:\n    try: print(d, s, '->', repr(sqlglot.parse_one(s,read=d).selects[0])[:300])\n    except Exception as e: print(d,s,'ERR',str(e)[:120])\n\"", "description": "Read trim_sql, ArgMax defs, and MAP ASTs from source dialects"}
[tool_result] 1777:def trim_sql(self: Generator, expression: exp.Trim, default_trim_type: str = "") -> str:
1778-    remove_chars = self.sql(expression, "expression")
1779-
1780-    # Use TRIM/LTRIM/RTRIM syntax if the expression isn't database-specific
1781-    if not remove_chars:
1782-        return self.trim_sql(expression)
1783-
1784-    target = self.sql(expression, "this")
1785-    trim_type = self.sql(expression, "position") or default_trim_type
1786-    collation = self.sql(expression, "collation")
1
…[2682 chars elided]…
YS,
  expressions=[
    Array(
      expressions=[
        Literal(this=1, is_string=False)]),
    Array(
      expressions=[
        Literal(this=2, is_string=False)])])
duckdb SELECT MAP(col_k, col_v) -> Map(
  keys=Column(
    this=Identifier(this=col_k, quoted=False)),
  values=Column(
    this=Identifier(this=col_v, quoted=False)))
spark SELECT MAP_FROM_ARRAYS(a,b) -> Map(
  keys=Column(
    this=Identifier(this=a, quoted=False)),
  values=Column(
    this=Identifier(this=b, quoted=False)))
[assistant] The AST shapes settle the MAP design. DuckDB and Presto produce `Map(keys=Array, values=Array)`, Spark produces `VarMap`, and a column-based two-array map arrives as `Map` with non-literal keys. So the generator will:

- interleave literal arrays into the variadic `MAP(k1, v1, ...)`;
- fall back to StarRocks' native `MAP_FROM_ARRAYS` when the arrays aren't literals.

For `TRIM`, the base `Generator.trim_sql` already emits `TRIM`/`LTRIM`/`RTRIM(str, chars)`, so the fix is to stop MySQL's `FROM`-style transform from being inherited.

I'll check two things before editing: how Hive imports `build_var_map`, and what the MySQL parser does with `MAP` and `TRIM(a, b)` today.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|build_var_map\" sqlglot/parsers/hive.py | head; grep -n '\"MAP\"' sqlglot/parsers/mysql.py sqlglot/parser.py | head -3; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT TRIM('xax', 'x')\\\", \\\"SELECT LTRIM('xax', 'x')\\\", \\\"SELECT RTRIM('xax', 'x')\\\", 'SELECT MAP()']:\n    try: print(s, '->', sqlglot.transpile(s, read='mysql', write='mysql')[0], '|', repr(sqlglot.parse_one(s,read='mysql').selects[0].__class__.__name__))\n    except Exception as e: print(s,'ERR',str(e)[:150])\n\"", "description": "Check Hive import pattern and MySQL trim/map parsing"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import build_formatted_time, build_regexp_extract
7:from sqlglot.helper import seq_get
8:from sqlglot.tokens import TokenType
99:        "MAP": parser.build_var_map,
sqlglot/parser.py:3627:        if self._match_text_seq("MAP", "KEYS", "TERMINATED", "BY"):
sqlglot/parser.py:7663:            parse_map = map_token is not None and map_token.text.upper() == "MAP"
SELECT TRIM('xax', 'x') -> SELECT TRIM('x' FROM 'xax') | 'Trim'
SELECT LTRIM('xax', 'x') -> SELECT TRIM(LEADING 'x' FROM 'xax') | 'Trim'
SELECT RTRIM('xax', 'x') -> SELECT TRIM(TRAILING 'x' FROM 'xax') | 'Trim'
SELECT MAP() -> SELECT MAP() | 'Map'
[assistant] `TRIM(str, chars)`, `LTRIM` and `RTRIM` all parse back to the same `Trim` node, so the round trip works once generation is fixed. I have what I need, so I'll make the generator changes first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    return self.func(\"ST_Distance_Sphere\", point1_x, point1_y, point2_x, point2_y)\n\n\nclass StarRocksGenerator(MySQLGenerator):", "new_string": "    return self.func(\"ST_Distance_Sphere\", point1_x, p
…[563 chars elided]…
  if (\n        isinstance(keys, exp.Array)\n        and isinstance(values, exp.Array)\n        and len(keys.expressions) == len(values.expressions)\n    ):\n        pairs = [arg for pair in zip(keys.expressions, values.expressions) for arg in pair]\n        return self.func(\"MAP\", *pairs)\n\n    return self.func(\"MAP_FROM_ARRAYS\", keys, values)\n\n\nclass StarRocksGenerator(MySQLGenerator):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    TRANSFORMS = {\n        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n     
…[1509 chars elided]…
is, e.expression),\n        exp.Delete: transforms.preprocess([_eliminate_between_in_delete]),\n        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.JSONExtractScalar: arrow_json_extract_sql,\n        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Map: map_sql,\n        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),\n        exp.VarMap: map_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now the parser side: StarRocks needs the variadic `MAP` builder and its own `MAP_FROM_ARRAYS` name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc\nfrom sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\nfrom sql
…[806 chars elided]…
supports LEFT SEMI JOIN and LEFT ANTI JOIN natively\n    # https://docs.starrocks.io/docs/sql-reference/sql-statements/table_bucket_part_index/SELECT/SELECT_JOIN/\n    TABLE_ALIAS_TOKENS = MySQLParser.TABLE_ALIAS_TOKENS - {TokenType.ANTI, TokenType.SEMI}\n\n    FUNCTIONS = {\n        **MySQLParser.FUNCTIONS,\n        \"ADDDATE\": build_date_delta_with_interval(exp.DateAdd, default_unit=\"DAY\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": parser.build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Now I'll re-run the probe, with a few round-trip and edge cases added: odd-arity `MAP`, column arrays, and `TRIM` with characters.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe2.py <<'EOF'\nimport sqlglot\ncases = [\n (\"spark\", \"SELECT MIN_BY(x, y) FROM t\"),\n (\"starrocks\", \"SELECT MIN_BY(x, y) FROM t\"),\n (\"starrocks\", \"SELECT MAX_BY(x, y) OVER (PARTITION BY g) FROM t\"),\n (\"starrocks\", \"SELECT MIN_BY(x, y) OVER (PARTITION BY g ORDER BY z) FROM t\")
…[1351 chars elided]…
\"ERR {type(e).__name__}: {str(e)[:120]}\"\n    print(f\"[{read}] {sql}\\n    -> {out}\")\nfor s in [\"SELECT MAP(1)\"]:\n    try: print(s, '->', sqlglot.transpile(s, read='starrocks', write='starrocks')[0])\n    except Exception as e: print(s, 'ERR', type(e).__name__, str(e)[:120])\nEOF\n$PY -c \"$(cat /tmp/probe2.py)\"", "description": "Re-run probe after StarRocks generator and parser changes"}
[tool_result] [spark] SELECT MIN_BY(x, y) FROM t
    -> SELECT MIN_BY(x, y) FROM t
[starrocks] SELECT MIN_BY(x, y) FROM t
    -> SELECT MIN_BY(x, y) FROM t
[starrocks] SELECT MAX_BY(x, y) OVER (PARTITION BY g) FROM t
    -> SELECT MAX_BY(x, y) OVER (PARTITION BY g) FROM t
[starrocks] SELECT MIN_BY(x, y) OVER (PARTITION BY g ORDER BY z) FROM t
    -> SELECT MIN_BY(x, y) OVER (PARTITION BY g ORDER BY z) FROM t
[starrocks] SELECT ARG_MIN(x, y) FROM t
    -> SELECT MIN_BY(x, y) FROM t
[duckdb] SELECT MAP(['a'], [
…[1153 chars elided]…
 SELECT TRIM('  a  ')
[starrocks] SELECT LTRIM('  a  ')
    -> SELECT LTRIM('  a  ')
[starrocks] SELECT TRIM(BOTH 'x' FROM 'xax')
    -> SELECT TRIM('xax', 'x')
[starrocks] SELECT TRIM(LEADING 'x' FROM 'xax')
    -> SELECT LTRIM('xax', 'x')
[duckdb] SELECT TRIM('x' FROM 'xax')
    -> SELECT TRIM('xax', 'x')
[mysql] SELECT TRIM(BOTH 'x' FROM 'xax')
    -> SELECT TRIM('xax', 'x')
[snowflake] SELECT TRIM('xax', 'x')
    -> SELECT TRIM('xax', 'x')
SELECT MAP(1) ERR IndexError list index out of range
[assistant] Most cases now produce the StarRocks-native forms, and the round trips hold. One thing to note: `MAP(1)` (odd arity) raises `IndexError` in the shared `build_var_map`, which Hive also uses. That input is invalid in StarRocks anyway, so I'll mention it rather than widen the change. Next I'll run the existing test suites to catch any expectations the change breaks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_doris.py tests/test_transpile.py 2>&1 | tail -40", "description": "Run StarRocks, MySQL, Doris and transpile tests"}
[tool_result] ...................................................................... [ 67%]
.................................    [100%]
103 passed, 1622 subtests passed in 0.45s
[assistant] Those pass. Other dialect suites also have cross-dialect `starrocks` expectations, so I'll run the full project suite with the configured command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 900 $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite"}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
.......................................
…[332 chars elided]…
[ 67%]
............................................... [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
............................................ [ 84%]
.........................................................................................................................................................................                                               [100%]
1122 passed, 18200 subtests passed in 49.43s
[assistant] The full suite passes (1122 tests, 18200 subtests). Now I'll add regression tests in the StarRocks test file. First I need the exact `validate_all` and `validate_identity` signatures in the test helper.
[tool_use Bash] {"command": "grep -n \"def validate_all\\|def validate_identity\" -A12 tests/dialects/test_dialect.py | head -60; sed -n 150,175p tests/dialects/test_starrocks.py; grep -n \"    def test_\" tests/dialects/test_starrocks.py", "description": "Read validate helper signatures and test method layout"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
60-        else:
61-            expression = self.parse_one(sql)
62-
63-        self.assertEqual(
64-            write_sql or sql,
…[1660 chars elided]…
7 DAY)")

    def test_regex(self):
        self.validate_all(
            "SELECT REGEXP(abc, '%foo%')",
9:    def test_starrocks(self):
33:    def test_distinct_on(self):
39:    def test_generate_date_array(self):
45:    def test_ddl(self):
140:    def test_identity(self):
151:    def test_time(self):
160:    def test_date_add_sub(self):
173:    def test_regex(self):
185:    def test_unnest(self):
243:    def test_analyze(self):
264:    def test_between(self):
282:    def test_partition(self):
[assistant] I'll add the new tests as one method per function group, placed before `test_regex`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_regex(self):\n        self.validate_all(", "new_string": "    def test_min_max_by(self):\n        self.validate_identity(\"SELECT MIN_BY(x, y) FROM t\")\n        self.validate_identity(\"SELE
…[2211 chars elided]…
"duckdb\": \"SELECT TRIM('x' FROM 'xax')\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LTRIM('xax', 'x')\", read={\"\": \"SELECT TRIM(LEADING 'x' FROM 'xax')\"}\n        )\n        self.validate_all(\n            \"SELECT RTRIM('xax', 'x')\", read={\"\": \"SELECT TRIM(TRAILING 'x' FROM 'xax')\"}\n        )\n\n    def test_regex(self):\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] I duplicated one `validate_identity` line and left a redundant `write=` in the `MAP_FROM_ARRAYS` case. I'll tidy both before running.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\"SELECT MAP_FROM_ARRAYS(k, v) FROM t\")\n        self.validate_identity(\"SELECT MAP_FROM_ARRAYS(k, v) FROM t\")\n        self.validate_all(\n            \"SELECT MAP('a', 
…[810 chars elided]…
presto\": \"SELECT MAP(ARRAY['a', 'b'], ARRAY[1, 2])\",\n                \"spark\": \"SELECT MAP('a', 1, 'b', 2)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT MAP_FROM_ARRAYS(k, v) FROM t\",\n            read={\n                \"duckdb\": \"SELECT MAP(k, v) FROM t\",\n                \"spark\": \"SELECT MAP_FROM_ARRAYS(k, v) FROM t\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-104151-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -30; ls $(dirname $PY) | grep -i \"ruff\\|mypy\" ; git status --short", "description": "Run StarRocks tests and check tool availability and changed files"}
[tool_result] ................                                              [100%]
16 passed, 83 subtests passed in 0.09s
dmypy
mypy
mypyc
ruff
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.py
[assistant] All 16 StarRocks tests pass. Next I'll run the repo's lint and format checks on the three changed files, since the pre-commit hooks use ruff and mypy.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py; $R/ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py; $R/ruff format --diff tests/dialects/test_starrocks.py sqlglot/generators/starrocks.py 2>&1 | head -40", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
Would reformat: sqlglot/generators/starrocks.py
1 file would be reformatted, 2 files already formatted
--- sqlglot/generators/starrocks.py
+++ sqlglot/generators/starrocks.py
@@ -109,9 +109,7 @@
     TRANSFORMS = {
         # TRIM/LTRIM/RTRIM take the characters as a second argument, not MySQL's TRIM(... FROM ...)
         **{
-            k: v
-            for k, v in MySQLGenerator.TRANSFORMS.items()
-            if k not in (exp.DateTrunc, exp.Trim)
+            k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k not in (exp.DateTrunc, exp.Trim)
         },
         exp.Array: inline_array_sql,
         exp.ArrayAgg: rename_func("ARRAY_AGG"),

1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format sqlglot/generators/starrocks.py && $R/ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py && $R/mypy sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py 2>&1 | tail -5", "description": "Apply ruff formatting and run mypy on changed modules"}
[tool_result] 1 file reformatted
3 files already formatted
Success: no issues found in 2 source files
[This command modified 1 file you've previously read: sqlglot/generators/starrocks.py. Call Read before editing.]
[assistant] The file-changed notice is from my own `ruff format` run, so the content is what I expect. I'll re-run the full suite and the lint check on the final state.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/ruff check sqlglot tests/dialects/test_starrocks.py | tail -1; git diff --stat", "description": "Final full test run, lint, and diff stat"}
[tool_result] ............................................................... [ 97%]
.............................                             [100%]
1126 passed, 18214 subtests passed in 49.22s
All checks passed!
 sqlglot/generators/starrocks.py  | 31 +++++++++++++++++++-
 sqlglot/parsers/starrocks.py     |  4 ++-
 tests/dialects/test_starrocks.py | 62 ++++++++++++++++++++++++++++++++++++++++
 3 files changed, 95 insertions(+), 2 deletions(-)
[assistant] The four StarRocks forms now generate StarRocks-native SQL, and StarRocks' own forms parse back. The full suite passes (1126 tests) and ruff and mypy are clean. I haven't committed.

- **`MIN_BY` / `MAX_BY`:** generated as `MIN_BY`/`MAX_BY` instead of `ARG_MIN`/`ARG_MAX`, including `OVER (...)`. The StarRocks docs I fetched don't mention window support, so the window form is unverified against a live server.
- **`MAP`:** `MAP(k1, v1, ...)` now parses, and literal two-array forms from DuckDB, Presto and Spark are interleaved into it. Two-array maps built from columns can't be interleaved, so th
…[246 chars elided]…
*`TRIM`:** the StarRocks docs give only `trim(str[, characters])`, with no `FROM` form. So `TRIM(BOTH 'x' FROM s)` becomes `TRIM(s, 'x')`, LEADING becomes `LTRIM(s, 'x')`, and TRAILING becomes `RTRIM(s, 'x')`.

Changes are in `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py` and `tests/dialects/test_starrocks.py`.

Two things to know:
- `MAP(1)` (odd arity) now reaches `IndexError` from the shared `build_var_map`. Hive hits the same path. The input is invalid in StarRocks, so I left it alone.
- Nothing was run against a live StarRocks. The tests only check sqlglot's own output.
