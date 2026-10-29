# trajectory base-1

final message:
StarRocks now gets its own forms for all four cases, in both directions, and the full suite passes (1126 tests, 18210 subtests). The changes are uncommitted in the worktree.

**What changed**

- **`MIN_BY` / `MAX_BY`:** emitted as `MIN_BY` / `MAX_BY` instead of `ARG_MIN` / `ARG_MAX`. The window form (`... OVER (...)`) follows the same path. `MIN_BY` and `MAX_BY` already parsed to the right expressions.
- **`MAP`:** StarRocks now parses its variadic `MAP(k1, v1, ...)` (before, `MAP(1, 'a', 2, 'b')` raised a parse error). Maps from other dialects are emitted in variadic form. DuckDB, Presto and Snowflake two-array forms with literal arrays become `MAP(1, 3, 2, 4)`.
- **`ARRAY_CONTAINS_ALL`:** emitted as the function, not `@>`. Parsing `ARRAY_CONTAINS_ALL` and `ARRAY_HAS_ALL` already worked.
- **`TRIM`:** MySQL's `TRIM(BOTH 'x' FROM a)` form is no longer inherited. StarRocks now gets `TRIM(a, 'x')`, and LEADING/TRAILING become `LTRIM(a, 'x')` / `RTRIM(a, 'x')`. The StarRocks docs confirm `trim(str[, characters])`, and `ltrim`/`rtrim` take the same optional second argument.

**Files**
- `sqlglot/generators/starrocks.py`: the TRANSFORMS entries above, and `exp.Trim` excluded from the inherited MySQL entries.
- `sqlglot/parsers/starrocks.py`: `"MAP": parser.build_var_map`.
- `tests/dialects/test_starrocks.py`: four new test methods (`test_min_max_by`, `test_map`, `test_array_contains_all`, `test_trim`). No existing tests were changed.

**Choices and limits**
- For `Map`/`VarMap` I reused the shared `var_map_sql` helper, the same one Hive uses. It only unpacks literal arrays. Non-literal arrays such as `MAP(x, y)` still emit `MAP(x, y)` with the existing "Cannot convert array columns into map" warning. StarRocks would reject that output. Generating it properly would need a StarRocks function for building a map from two arrays, which I did not verify exists, so I left it.
- The TRIM output drops the collation argument, since StarRocks has no equivalent.
- I did not verify a StarRocks `MIN_BY` aggregate with a `count` argument; the current generator ignores it.

Ruff check and format pass on the changed files.

## events
[assistant] I'll start by reading the StarRocks dialect and the MySQL/base code it inherits from.
[tool_use Bash] {"command": "git status --short | head && cat sqlglot/dialects/starrocks.py && wc -l sqlglot/dialects/starrocks.py && ls tests/dialects | grep -i star"}
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
      21 sqlglot/dialects/starrocks.py
test_starrocks.py
[tool_use Bash] {"command": "grep -n \"MIN_BY\\|MAX_BY\\|ArgMin\\|ArgMax\\|ARRAY_CONTAINS_ALL\\|ArrayContainsAll\\|class Map\\b\\|VarMap\\|ToMap\\|StarMap\\|Trim\\|TRIM\" sqlglot/expressions.py | head -50; grep -n \"MIN_BY\\|MAX_BY\\|ARRAY_CONTAINS_ALL\\|ArrayContainsAll\\|VarMap\\|_trim_sql\\|TRIM\" sqlglot/dialects/mysql.py sqlglot/dialects/dialect.py sqlglot/generator.py sqlglot/parser.py | head -60"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/dialect.py:1477:    self: Generator, expression: exp.Map | exp.VarMap, map_func_name: str = "MAP"
sqlglot/dialects/dialect.py:1780:    # Use TRIM/LTRIM/RTRIM syntax if the expression isn't database-specific
sqlglot/dialects/dialect.py:1792:    return f"TRIM({trim_type}{remove_chars}{from_part}{target}{collation})"
sqlglot/generator.py:144:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/
…[743 chars elided]…
        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1516:        "TRIM": lambda self: self._parse_trim(),
sqlglot/parser.py:1776:    # Whether the TRIM function expects the characters to trim as its first argument
sqlglot/parser.py:1777:    TRIM_PATTERN_FIRST: t.ClassVar = False
sqlglot/parser.py:8273:        if self._match_texts(self.TRIM_TYPES):
sqlglot/parser.py:8278:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
[assistant] The StarRocks dialect delegates to `sqlglot/generators/starrocks.py` and `sqlglot/parsers/starrocks.py`. I'll read those, plus the existing StarRocks tests.
[tool_use Bash] {"command": "ls sqlglot/generators sqlglot/parsers | head -80; cat sqlglot/generators/starrocks.py; cat sqlglot/parsers/starrocks.py; cat tests/dialects/test_starrocks.py"}
[tool_result] <persisted-output>
Output too large (34.2KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-e2b5bc4f1eee-20261029-131913-starrocks-dialect-several-functi-base-1/6e265eee-db1a-415a-b135-162a61717a0f/tool-results/b4fb6n3qr.txt

Preview (first 2KB):
sqlglot/generators:
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgr
…[1309 chars elided]…
(_eliminate_between_in_delete(expr).sql(dialect="starrocks"))
        DELETE FROM t WHERE x >= 1 AND x <= 10
    """
    if where := expression.args.get("where"):
        for between in where.find_all(exp.Between):
            between.replace(
                exp.and_(
                    exp.GTE(this=between.this.copy(), expression=between.args["low"]),
                    exp.LTE(this=between.this.copy(), expression=between.args["high"]),
                    copy=False,
...
</persisted-output>
[tool_use Bash] {"command": "cat sqlglot/generators/starrocks.py | sed -n 30,200p; echo ----PARSER; cat sqlglot/parsers/starrocks.py; echo ----TESTS; cat tests/dialects/test_starrocks.py"}
[tool_result]         for between in where.find_all(exp.Between):
            between.replace(
                exp.and_(
                    exp.GTE(this=between.this.copy(), expression=between.args["low"]),
                    exp.LTE(this=between.this.copy(), expression=between.args["high"]),
                    copy=False,
                )
            )
    return expression


# https://docs.starrocks.io/docs/sql-reference/sql-functions/spatial-functions/st_distance_sphere/
def st_distance_sphere(self, ex
…[28341 chars elided]…
   self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] Before changing anything, I'll check what the StarRocks dialect currently emits and parses for each of the four cases.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c '\nimport sqlglot\nfrom sqlglot import parse_one\ncases = [\n (\"SELECT MIN_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT MAX_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT ARG_MIN(a, b) FROM t\", \"duckdb\"),\n (\"SELECT ARG_MAX(a, b) FROM t\", \"duckdb\"),\n (\"SELECT MAX_BY(a, b) OVER (PARTITION BY c) 
…[470 chars elided]…
LECT TRIM(a)\", \"starrocks\"),\n (\"SELECT TRIM(LEADING \\\"x\\\" FROM a)\", \"mysql\"),\n (\"SELECT TRIM(\\\"x\\\" FROM a)\", \"mysql\"),\n]\nfor sql, d in cases:\n    try:\n        e = parse_one(sql, read=d)\n        print(repr(sql), d, \"->\", e.sql(\"starrocks\"), \"|\", type(e.selects[0]).__name__)\n    except Exception as ex:\n        print(repr(sql), d, \"ERR\", type(ex).__name__, ex)\n'"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` drops the working directory from the import path, so I'll point `PYTHONPATH` at the worktree.
[tool_use Bash] {"command": "cat > /tmp/sr_probe.py <<'EOF'\nfrom sqlglot import parse_one\ncases = [\n (\"SELECT MIN_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT MAX_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT ARG_MIN(a, b) FROM t\", \"duckdb\"),\n (\"SELECT ARG_MAX(a, b) FROM t\", \"duckdb\"),\n (\"SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t\", \"starrocks\"),\n (\"SELECT ARG_MAX(a, b) OVER (PARTITION
…[526 chars elided]…
]\nfor sql, d in cases:\n    try:\n        e = parse_one(sql, read=d)\n        print(repr(sql), d, \"->\", e.sql(\"starrocks\"), \"|\", type(e.selects[0]).__name__, \"|\", repr(e.selects[0])[:0])\n    except Exception as ex:\n        print(repr(sql), d, \"ERR\", type(ex).__name__, ex)\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python -I /tmp/sr_probe.py"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/sr_probe.py", line 1, in <module>
    from sqlglot import parse_one
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` also ignores `PYTHONPATH`. The `-I` guidance is for untrusted files, and this is the user's own repo, so I'll run without it. The probe script stays in `/tmp`.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/sr_probe.py"}
[tool_result] 'SELECT MIN_BY(a, b) FROM t' starrocks -> SELECT ARG_MIN(a, b) FROM t | ArgMin | 
'SELECT MAX_BY(a, b) FROM t' starrocks -> SELECT ARG_MAX(a, b) FROM t | ArgMax | 
'SELECT ARG_MIN(a, b) FROM t' duckdb -> SELECT ARG_MIN(a, b) FROM t | ArgMin | 
'SELECT ARG_MAX(a, b) FROM t' duckdb -> SELECT ARG_MAX(a, b) FROM t | ArgMax | 
'SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t' starrocks -> SELECT ARG_MAX(a, b) OVER (PARTITION BY c) FROM t | Window | 
'SELECT ARG_MAX(a, b) OVER (PARTITION BY c) FROM t
…[459 chars elided]…
ARRAY[3, 4])' snowflake -> SELECT MAP([1, 2], [3, 4]) | Map | 
'SELECT ARRAY_CONTAINS_ALL(a, b)' starrocks -> SELECT a @> b | ArrayContainsAll | 
'SELECT a @> b' postgres -> SELECT a @> b | ArrayContainsAll | 
"SELECT TRIM(BOTH 'x' FROM a)" starrocks -> SELECT TRIM(BOTH 'x' FROM a) | Trim | 
'SELECT TRIM(a)' starrocks -> SELECT TRIM(a) | Trim | 
"SELECT TRIM(LEADING 'x' FROM a)" mysql -> SELECT TRIM(LEADING 'x' FROM a) | Trim | 
"SELECT TRIM('x' FROM a)" mysql -> SELECT TRIM('x' FROM a) | Trim |
[assistant] The probe confirms four problems: MIN_BY/MAX_BY come out as ARG_MIN/ARG_MAX, StarRocks rejects the variadic `MAP(1,2,3,4)`, `ARRAY_CONTAINS_ALL` comes out as `@>`, and TRIM passes through unchanged. Next I'll look at the inherited MAP and TRIM handling and at how other dialects handle these.
[tool_use Bash] {"command": "grep -rn '\"MAP\"' sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/parsers/doris.py sqlglot/parsers/presto.py sqlglot/parsers/base.py sqlglot/dialects/dialect.py | head -20; sed -n 40,60p sqlglot/parser.py; grep -n \"def trim_sql\\|def _parse_trim\" -A28 sqlglot/generator.py sqlglot/parser.py | head -90; sed -n 1765,1795p sqlglot/dialects/dialect.py; grep -n \"VarMap\\|Map\\b\" sqlglot/generators/doris.py sqlglot/generators/mysql.py sqlglot/generators/presto.py sqlglot/generator.py | head -30"}
[tool_result] sqlglot/parser.py:3627:        if self._match_text_seq("MAP", "KEYS", "TERMINATED", "BY"):
sqlglot/parser.py:7663:            parse_map = map_token is not None and map_token.text.upper() == "MAP"
sqlglot/dialects/dialect.py:1477:    self: Generator, expression: exp.Map | exp.VarMap, map_func_name: str = "MAP"

# Used to detect alphabetical characters and +/- in timestamp literals
TIME_ZONE_RE: Pattern[str] = re.compile(r":.*?[a-zA-Z\+\-]")


def build_var_map(args: BuilderArgs) -> exp.StarMap | 
…[5135 chars elided]…
eturn f"TRIM({trim_type}{remove_chars}{from_part}{target}{collation})"


def str_to_time_sql(self: Generator, expression: exp.Expr) -> str:
sqlglot/generators/doris.py:66:        exp.Map: rename_func("ARRAY_MAP"),
sqlglot/generator.py:269:        exp.ToMap: lambda self, e: f"MAP {self.sql(e, 'this')}",
sqlglot/generator.py:286:        exp.VarMap: lambda self, e: self.func("MAP", e.args["keys"], e.args["values"]),
sqlglot/generators/presto.py:347:        exp.StrToMap: rename_func("SPLIT_TO_MAP"),
[assistant] The MAP failure comes from the default `exp.Map` builder, which caps arguments at two. StarRocks' own form needs a variadic builder. Before I decide on the TRIM and MAP output forms, I'll check StarRocks' documented syntax.
[tool_use Bash] {"command": "grep -n \"^class Map(\\|^class VarMap\\|^class ArgMin\\|^class ArgMax\\|^class ArrayContainsAll\\|^class Trim\\|^class ToMap\\|^class StarMap\" -A6 sqlglot/expressions.py | head -80; grep -rn \"MIN_BY\\|MAX_BY\\|ARG_MIN\" sqlglot/dialects/*.py sqlglot/generators/*.py sqlglot/parsers/*.py | head -20"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generators/doris.py:51:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/doris.py:52:        exp.ArgMin: rename_func("MIN_BY"),
sqlglot/generators/bigquery.py:281:        exp.ArgMax: arg_max_or_min_no_count("MAX_BY"),
sqlglot/generators/bigquery.py:282:        exp.ArgMin: arg_max_or_min_no_count("MIN_BY"),
sqlglot/generators/duckdb.py:1123:    # Transform ANY_VALUE(expr HAVING MAX/MIN having_expr) to ARG_MAX_NU
…[266 chars elided]…
_func("MIN_BY"),
sqlglot/generators/hive.py:241:        exp.ArgMax: arg_max_or_min_no_count("MAX_BY"),
sqlglot/generators/hive.py:242:        exp.ArgMin: arg_max_or_min_no_count("MIN_BY"),
sqlglot/generators/snowflake.py:411:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/snowflake.py:412:        exp.ArgMin: rename_func("MIN_BY"),
sqlglot/generators/teradata.py:73:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/teradata.py:74:        exp.ArgMin: rename_func("MIN_BY"),
[tool_use Bash] {"command": "ls sqlglot/ | head -80; grep -rln \"class VarMap\" sqlglot/ ; grep -rn \"class VarMap\\|class Map(\\|class ArrayContainsAll\\|class ArgMin\" -A5 sqlglot/expressions/ 2>/dev/null | head -60"}
[tool_result] __init__.py
__main__.py
__pycache__
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
sqlglot/expressions/array.py
sqlglot/expressions/aggregate.py:66:class ArgMin(Expression, AggFunc):
sqlglot/expressions/aggregate.py-67-    arg_types = {"this": True, "expression": True, "count": False}
s
…[817 chars elided]…
roperty
sqlglot/expressions/array.py-287-    def keys(self) -> list[Expr]:
sqlglot/expressions/array.py-288-        keys = self.args.get("keys")
--
sqlglot/expressions/array.py:339:class VarMap(Expression, Func):
sqlglot/expressions/array.py-340-    arg_types = {"keys": True, "values": True}
sqlglot/expressions/array.py-341-    is_var_len_args = True
sqlglot/expressions/array.py-342-
sqlglot/expressions/array.py-343-    @property
sqlglot/expressions/array.py-344-    def keys(self) -> list[Expr]:
[tool_use Bash] {"command": "sed -n 283,360p sqlglot/expressions/array.py; grep -n \"class Trim\" -A8 sqlglot/expressions/*.py; grep -n \"VarMap\\|exp.Map\\b\\|Map:\" sqlglot/generators/*.py sqlglot/dialects/dialect.py | head -30"}
[tool_result] class Map(Expression, Func):
    arg_types = {"keys": False, "values": False}

    @property
    def keys(self) -> list[Expr]:
        keys = self.args.get("keys")
        return keys.expressions if keys else []

    @property
    def values(self) -> list[Expr]:
        values = self.args.get("values")
        return values.expressions if values else []


class MapCat(Expression, Func):
    arg_types = {"this": True, "expression": True}


class MapContainsKey(Expression, Func):
    arg_types = {
…[2445 chars elided]…
        exp.VarMap: var_map_sql,
sqlglot/generators/hive.py:312:        exp.StarMap: rename_func("MAP"),
sqlglot/generators/duckdb.py:3548:            return self.sql(exp.array(exp.Map(keys=exp.array(), values=exp.array())))
sqlglot/generators/spark2.py:20:def _map_sql(self: Spark2Generator, expression: exp.Map) -> str:
sqlglot/generators/spark2.py:166:            exp.Map: _map_sql,
sqlglot/dialects/dialect.py:1477:    self: Generator, expression: exp.Map | exp.VarMap, map_func_name: str = "MAP"
[assistant] The existing `var_map_sql` helper and ClickHouse's `_map_sql` already handle the Map-to-variadic conversion, so I'll check how they deal with non-literal arrays.
[tool_use Bash] {"command": "sed -n 1475,1500p sqlglot/dialects/dialect.py; sed -n 135,150p sqlglot/generators/clickhouse.py"}
[tool_result] def var_map_sql(
    self: Generator, expression: exp.Map | exp.VarMap, map_func_name: str = "MAP"
) -> str:
    keys = expression.args.get("keys")
    values = expression.args.get("values")

    if not isinstance(keys, exp.Array) or not isinstance(values, exp.Array):
        self.unsupported("Cannot convert array columns into map.")
        return self.func(map_func_name, keys, values)

    args = []
    for key, value in zip(keys.expressions, values.expressions):
        args.append(self.sql(k
…[590 chars elided]…
t.arg_key == "settings"):
        return _lower_func(var_map_sql(self, expression))

    keys = expression.args.get("keys")
    values = expression.args.get("values")

    if not isinstance(keys, exp.Array) or not isinstance(values, exp.Array):
        self.unsupported("Cannot convert array columns into map.")
        return ""

    args = []
    for key, value in zip(keys.expressions, values.expressions):
        args.append(f"{self.sql(key)}: {self.sql(value)}")

    csv_args = ", ".join(args)
[assistant] `var_map_sql` is the shared helper for this conversion. It emits variadic `MAP(k1, v1, ...)` for literal arrays and flags a warning otherwise. Before reusing it, I'll confirm StarRocks' documented forms for MAP, TRIM, MIN_BY, and ARRAY_CONTAINS_ALL.
[tool_use Bash] {"command": "echo \"placeholder to keep turn ordered\""}
[tool_result] placeholder to keep turn ordered
[tool_use WebSearch] {"query": "StarRocks map() function syntax MAP(key, value, ...) docs", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks trim function syntax ltrim rtrim trim(str) documentation", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks min_by max_by array_contains_all functions documentation", "mode": "standard"}
[tool_result] Web search results for query: "StarRocks trim function syntax ltrim rtrim trim(str) documentation"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/zh/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.starrocks
…[2666 chars elided]…
str[, VARCHAR characters]) and documents str as the VARCHAR input to trim (index 4-1).
- **trim:** The English page's only result is an example, where trimming "x" from "xxabcdxx" returns "abcd" (index 5-1). I did not find a formal syntax block for `trim` in these results, so check https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim directly for the exact signature.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks min_by max_by array_contains_all functions documentation"

Links: [{"title":"Function list","url":"https://docs.starrocks.io/docs/3.1/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/3.0/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/function-list/"},{"title":"min n max n","url":"https://docs.starrocks.io/docs
…[2363 chars elided]…
alue paired with an extreme key.

The function list is at https://docs.starrocks.io/docs/sql-reference/sql-functions/function-list/. The `array_contains_all` page is under the array-functions section of the Chinese docs, and the English page should be at the same path. I did not find an English `min_by`/`max_by` page, so check the aggregate-functions section of the docs for the current version.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks map() function syntax MAP(key, value, ...) docs"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/data-types/semi_structured/Map/"},{"title":"map values","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_values/"},{"title":"map keys","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_keys"},{"title":"map keys","url":"https://docs.starrocks.io/ja/doc
…[2520 chars elided]…
ithin each map (the English MAP page).

I didn't find a result that confirms the exact English `map()` function signature, so the Japanese page is the only source for the call form. The English MAP data type page at docs.starrocks.io/docs/sql-reference/data-types/semi_structured/Map/ is the place to check it. A follow-up search for the English `map` function reference could confirm the wording.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] The MAP function-call form `map(a,1,b,2,...)` is confirmed. The TRIM and MIN_BY results are not precise enough yet, so I'll fetch the official trim page directly.
[tool_use ToolSearch] {"query": "select:WebFetch", "max_results": 1}
[tool_result] 
[tool_use WebFetch] {"url": "https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim", "prompt": "Give the exact syntax block(s) for trim, ltrim and rtrim, the description of each argument, the supported version notes, and the examples verbatim. Say whether trim accepts a second argument of characters to remove, and whether any FROM/LEADING/TRAILING/BOTH syntax is supported."}
[tool_result] **trim**

- **Syntax:**
  ```
  VARCHAR trim(VARCHAR str[, VARCHAR characters])
  ```
- **Arguments:**
  - `str`: Required. The string to trim. It must evaluate to a VARCHAR.
  - `characters`: Optional. The set of characters to remove, as a VARCHAR. If omitted, spaces are removed. An empty string produces an error.
- **Return value:** A VARCHAR.
- **Version note:** Per the page, removing specified characters is supported starting in StarRocks 2.5.0.
- **Examples:**
  ```sql
  SELECT trim("   ab 
…[199 chars elided]…
s. `trim` accepts an optional second `characters` argument.

**FROM/LEADING/TRAILING/BOTH:** The page does not document this syntax, and the syntax block shows only the `str[, characters]` form. It should not be assumed to be supported.

**ltrim and rtrim:** The page only links to them under References. Their syntax, argument descriptions, version notes, and examples are not in the content provided, so I can't give those details from this page. Their own reference pages would need to be checked.
[assistant] The official TRIM syntax is `trim(str[, characters])`, and `ltrim`/`rtrim` take the same optional second argument. So a TRIM with a character set can be emitted as the comma form, and LEADING/TRAILING map to LTRIM/RTRIM. I'll check how MySQL currently routes Trim and whether the base generator's `trim_sql` can be reused.
[tool_use Bash] {"command": "grep -n \"Trim\\|trim\" sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/singlestore.py | head; grep -n \"def func\\b\" -A12 sqlglot/generator.py | head -30; grep -n \"exp.Trim\" sqlglot/generator.py"}
[tool_result] sqlglot/generators/doris.py:520:        "trim",
sqlglot/generators/mysql.py:23:    trim_sql,
sqlglot/generators/mysql.py:221:        exp.Trim: trim_sql,
sqlglot/generators/singlestore.py:916:        "ltrim",
sqlglot/generators/singlestore.py:1165:        "rtrim",
sqlglot/generators/singlestore.py:1333:        "trim",
4593:    def func(
4594-        self,
4595-        name: str,
4596-        *args: t.Any,
4597-        prefix: str = "(",
4598-        suffix: str = ")",
4599-        normalize: bool = True,
4600-    ) -> str:
4601-        name = self.normalize_func(name) if normalize else name
4602-        return f"{name}{prefix}{self.format_args(*args)}{suffix}"
4603-
4604-    def format_args(self, *args: t.Any, sep: str = ", ") -> str:
4605-        arg_sqls = tuple(
3613:    def trim_sql(self, expression: exp.Trim) -> str:
[assistant] MySQL routes `exp.Trim` through the dialect-level `trim_sql` in TRANSFORMS, which always emits the FROM form. StarRocks inherits that entry, so I need to drop it so the base generator's comma-form `trim_sql` takes over. Next I'll check where `build_var_map` is imported from in other parsers, and whether any existing tests depend on the current output.
[tool_use Bash] {"command": "grep -rn \"build_var_map\" sqlglot/ | head -5; grep -rn \"starrocks\" tests/ --include=*.py -l; grep -rn -i \"ARG_M\\|MIN_BY\\|MAX_BY\\|ARRAY_CONTAINS_ALL\\|@>\\|TRIM\" tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head; grep -n \"def format_args\" -A8 sqlglot/generator.py | head -12"}
[tool_result ERROR] Exit code 1
sqlglot/parser.py:45:def build_var_map(args: BuilderArgs) -> exp.StarMap | exp.VarMap:
sqlglot/parser.py:429:        "VAR_MAP": build_var_map,
sqlglot/parsers/clickhouse.py:287:        "MAP": parser.build_var_map,
sqlglot/parsers/hive.py:99:        "MAP": parser.build_var_map,
sqlglot/parsers/snowflake.py:1390:    expression = parser.build_var_map(args)
(eval):1: no matches found: --include=*.py
[assistant] Hive and ClickHouse both use `parser.build_var_map` for `MAP`, so I'll follow that pattern. The last command failed on a zsh glob in my grep flags, so I'll re-run the remaining checks.
[tool_use Bash] {"command": "grep -rln \"starrocks\" tests/ ; grep -n -i \"ARG_M\\|MIN_BY\\|MAX_BY\\|ARRAY_CONTAINS_ALL\\|@>\\|TRIM\\|MAP(\" tests/dialects/test_starrocks.py | head -20; grep -n \"def format_args\" -A6 sqlglot/generator.py | head -10"}
[tool_result] tests/test_transpile.py
tests/dialects/test_snowflake.py
tests/dialects/test_oracle.py
tests/dialects/test_bigquery.py
tests/dialects/test_starrocks.py
tests/dialects/test_redshift.py
tests/dialects/test_teradata.py
tests/dialects/test_presto.py
tests/dialects/test_duckdb.py
tests/dialects/test_mysql.py
tests/dialects/test_postgres.py
tests/dialects/test_dialect.py
tests/fixtures/optimizer/qualify_columns.sql
4604:    def format_args(self, *args: t.Any, sep: str = ", ") -> str:
4605-        arg_sqls = tuple(
4606-            self.sql(arg) for arg in args if arg is not None and not isinstance(arg, bool)
4607-        )
4608-        if self.pretty and self.too_wide(arg_sqls):
4609-            return self.indent(
4610-                "\n" + f"{sep.strip()}\n".join(arg_sqls) + "\n", skip_first=True, skip_last=True
[assistant] `format_args` already drops `None` arguments, so the base `trim_sql` will emit a bare `TRIM(a)` when no characters are given. I'll check how the Hive parser imports `build_var_map`, then make the edits.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\" sqlglot/parsers/hive.py sqlglot/parsers/clickhouse.py | head; grep -n \"dialect import\" -A3 sqlglot/generators/hive.py | head -8"}
[tool_result] sqlglot/parsers/hive.py:1:from __future__ import annotations
sqlglot/parsers/hive.py:3:import typing as t
sqlglot/parsers/hive.py:5:from sqlglot import exp, parser
sqlglot/parsers/hive.py:6:from sqlglot.dialects.dialect import build_formatted_time, build_regexp_extract
sqlglot/parsers/hive.py:7:from sqlglot.helper import seq_get
sqlglot/parsers/hive.py:8:from sqlglot.tokens import TokenType
sqlglot/parsers/clickhouse.py:1:from __future__ import annotations
sqlglot/parsers/clickhouse.py:3:import typing as t
sqlglot/parsers/clickhouse.py:5:from collections import deque
sqlglot/parsers/clickhouse.py:7:from sqlglot import exp, parser
7:from sqlglot.dialects.dialect import (
8-    DATE_ADD_OR_SUB,
9-    approx_count_distinct_sql,
10-    arg_max_or_min_no_count,
[assistant] Now the edits. Parser first: a variadic `MAP` builder so StarRocks' own `MAP(k1, v1, ...)` parses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc\nfrom sqlglot.helper import seq_get", "new_string": "from sqlglot import exp, parser\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc\nfrom sqlglot.helper import seq_get"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": parser.build_var_map,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Now the generator: exclude MySQL's FROM-style Trim so the base comma-form is used, and add MIN_BY/MAX_BY, `ARRAY_CONTAINS_ALL`, and the MAP mappings.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n)", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n    var_map_sql,\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: 
…[524 chars elided]…
Agg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayContainsAll: rename_func(\"ARRAY_CONTAINS_ALL\"),\n        exp.ArrayFilter: rename_func(\"ARRAY_FILTER\"),\n        exp.ArrayToString: rename_func(\"ARRAY_JOIN\"),\n        exp.ApproxDistinct: approx_count_distinct_sql,\n        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\",\n        exp.Map: var_map_sql,\n        exp.VarMap: var_map_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now I'll re-run the probe with the StarRocks cases added, including round-trips and the window forms.
[tool_use Bash] {"command": "cat > /tmp/sr_probe2.py <<'EOF'\nfrom sqlglot import parse_one\ncases = [\n (\"SELECT MIN_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT MAX_BY(a, b) FROM t\", \"starrocks\"),\n (\"SELECT ARG_MAX(a, b) FROM t\", \"duckdb\"),\n (\"SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t\", \"starrocks\"),\n (\"SELECT ARG_MIN(a, b) OVER (PARTITION BY c) FROM t\", \"duckdb\"),\n (\"SELECT MAP(1,
…[731 chars elided]…
"),\n]\nfor sql, d in cases:\n    try:\n        e = parse_one(sql, read=d)\n        print(f\"{sql!r:55} {d:9} -> {e.sql('starrocks')!r}  [{type(e.selects[0]).__name__}]\")\n    except Exception as ex:\n        print(f\"{sql!r} {d} ERR {type(ex).__name__}: {str(ex).splitlines()[0]}\")\nEOF\nPYTHONPATH=$PWD <work>/env-sqlglot/bin/python /tmp/sr_probe2.py"}
[tool_result] Cannot convert array columns into map.
'SELECT MIN_BY(a, b) FROM t'                            starrocks -> 'SELECT MIN_BY(a, b) FROM t'  [ArgMin]
'SELECT MAX_BY(a, b) FROM t'                            starrocks -> 'SELECT MAX_BY(a, b) FROM t'  [ArgMax]
'SELECT ARG_MAX(a, b) FROM t'                           duckdb    -> 'SELECT MAX_BY(a, b) FROM t'  [ArgMax]
'SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t'      starrocks -> 'SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t'  [Window]
'SELECT
…[1276 chars elided]…
  [Trim]
"SELECT TRIM(BOTH 'x' FROM a)"                          mysql     -> "SELECT TRIM(a, 'x')"  [Trim]
"SELECT TRIM(LEADING 'x' FROM a)"                       mysql     -> "SELECT LTRIM(a, 'x')"  [Trim]
"SELECT TRIM(TRAILING 'x' FROM a)"                      mysql     -> "SELECT RTRIM(a, 'x')"  [Trim]
"SELECT TRIM('x' FROM a)"                               mysql     -> "SELECT TRIM(a, 'x')"  [Trim]
'SELECT TRIM(a)'                                        mysql     -> 'SELECT TRIM(a)'  [Trim]
[assistant] The generator now emits StarRocks-native forms:
- `MIN_BY`/`MAX_BY`, including the window form.
- Variadic `MAP(k, v, ...)`, converted from the two-array forms of DuckDB, Presto and Snowflake.
- `ARRAY_CONTAINS_ALL`.
- Comma-form `TRIM`, `LTRIM` and `RTRIM`.

One caveat: `MAP(x, y)` over non-literal arrays still can't be unpacked. It emits the existing "Cannot convert array columns into map" warning, which is the same behaviour Hive has. Next I'll add tests to the existing StarRocks test file, inserting new methods without touching the existing ones.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_regex(self):", "new_string": "    def test_min_max_by(self):\n        self.validate_identity(\"SELECT MIN_BY(a, b) FROM t\")\n        self.validate_identity(\"SELECT MAX_BY(a, b) FROM t\")\n 
…[1410 chars elided]…
\n            read={\"mysql\": \"SELECT TRIM(BOTH 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT LTRIM(a, 'x')\",\n            read={\"mysql\": \"SELECT TRIM(LEADING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT RTRIM(a, 'x')\",\n            read={\"mysql\": \"SELECT TRIM(TRAILING 'x' FROM a)\"},\n        )\n\n    def test_regex(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-131913-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Next I'll run the StarRocks test file, then the full suite using the project's configured check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -40"}
[tool_result] ................                                                  [100%]
16 passed, 79 subtests passed in 0.16s
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "timeout": 900000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
.......................................
…[322 chars elided]…
[ 66%]
............................................................................................................ [ 76%]
.......................................... [ 79%]
.............................................................................. [ 86%]
............................................................. [ 92%]
........................................................................................                                 [100%]
1126 passed, 18210 subtests passed in 56.19s
[assistant] The full suite passes: 1126 tests, 18210 subtests. CLAUDE.md also asks for style checks, so I'll run ruff on the three changed files.
[tool_use Bash] {"command": "F=\"sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py\"; <work>/env-sqlglot/bin/python -m ruff check $F 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check $F 2>&1 | tail -5; git status --short; rm -f /tmp/sr_probe.py /tmp/sr_probe2.py"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py:1:1

Found 1 error.
error: Failed to format sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py: No such file or directory (os error 2)
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.py
[assistant] The ruff error comes from zsh not splitting my unquoted file list into separate arguments. I'll re-run with the paths passed explicitly.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py"}
[tool_result ERROR] Exit code 1
All checks passed!
Would reformat: sqlglot/generators/starrocks.py
1 file would be reformatted, 2 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff sqlglot/generators/starrocks.py 2>&1 | head -30"}
[tool_result] --- sqlglot/generators/starrocks.py
+++ sqlglot/generators/starrocks.py
@@ -88,9 +88,7 @@
 
     TRANSFORMS = {
         **{
-            k: v
-            for k, v in MySQLGenerator.TRANSFORMS.items()
-            if k not in (exp.DateTrunc, exp.Trim)
+            k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k not in (exp.DateTrunc, exp.Trim)
         },
         exp.Array: inline_array_sql,
         exp.ArgMax: rename_func("MAX_BY"),

1 file would be reformatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/generators/starrocks.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/starrocks.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -2 && git diff --stat"}
[tool_result] 1 file reformatted
1 file already formatted
................                                                  [100%]
16 passed, 79 subtests passed in 0.10s
 sqlglot/generators/starrocks.py  | 10 +++++++-
 sqlglot/parsers/starrocks.py     |  3 ++-
 tests/dialects/test_starrocks.py | 49 ++++++++++++++++++++++++++++++++++++++++
 3 files changed, 60 insertions(+), 2 deletions(-)
[This command modified 1 file you've previously read: sqlglot/generators/starrocks.py. Call Read before editing.]
[assistant] The "changed on disk" note is from my own `ruff format` run, which only reflowed the TRANSFORMS comprehension. I'll review the final source diff before reporting.
[tool_use Bash] {"command": "git diff -- sqlglot/"}
[tool_result] diff --git a/sqlglot/generators/starrocks.py b/sqlglot/generators/starrocks.py
index e71176c1f..17adced51 100644
--- a/sqlglot/generators/starrocks.py
+++ b/sqlglot/generators/starrocks.py
@@ -9,6 +9,7 @@ from sqlglot.dialects.dialect import (
     unit_to_str,
     inline_array_sql,
     property_sql,
+    var_map_sql,
 )
 from sqlglot.generators.mysql import MySQLGenerator
 
@@ -86,13 +87,20 @@ class StarRocksGenerator(MySQLGenerator):
     }
 
     TRANSFORMS = {
-        **{k: v for k, v in 
…[1216 chars elided]…
qlglot import exp, parser
 from sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc
 from sqlglot.helper import seq_get
 from sqlglot.parsers.mysql import MySQLParser
@@ -27,6 +27,7 @@ class StarRocksParser(MySQLParser):
             this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
         ),
         "ARRAY_FLATTEN": exp.Flatten.from_arg_list,
+        "MAP": parser.build_var_map,
         "REGEXP": exp.RegexpLike.from_arg_list,
     }
[assistant] StarRocks now gets its own forms for all four cases, in both directions, and the full suite passes (1126 tests, 18210 subtests). The changes are uncommitted in the worktree.

**What changed**

- **`MIN_BY` / `MAX_BY`:** emitted as `MIN_BY` / `MAX_BY` instead of `ARG_MIN` / `ARG_MAX`. The window form (`... OVER (...)`) follows the same path. `MIN_BY` and `MAX_BY` already parsed to the right expressions.
- **`MAP`:** StarRocks now parses its variadic `MAP(k1, v1, ...)` (before, `MAP(1, 'a', 2, 'b')` raised a parse error). Maps from other dialects are emitted in variadic form. DuckDB, Presto and 
…[938 chars elided]…
, the same one Hive uses. It only unpacks literal arrays. Non-literal arrays such as `MAP(x, y)` still emit `MAP(x, y)` with the existing "Cannot convert array columns into map" warning. StarRocks would reject that output. Generating it properly would need a StarRocks function for building a map from two arrays, which I did not verify exists, so I left it.
- The TRIM output drops the collation argument, since StarRocks has no equivalent.
- I did not verify a StarRocks `MIN_BY` aggregate with a `count` argument; the current generator ignores it.

Ruff check and format pass on the changed files.
