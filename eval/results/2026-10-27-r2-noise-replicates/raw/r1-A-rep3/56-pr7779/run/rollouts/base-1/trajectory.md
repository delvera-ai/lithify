# trajectory base-1

final message:
The StarRocks dialect now generates its own forms for all four functions and parses them back. The full suite passes (1126 tests), and ruff and mypy are clean on the changed modules. I did not commit.

**What changed**

- **`MIN_BY` / `MAX_BY`**: generated as `MIN_BY` / `MAX_BY`, including the window form. `ARG_MIN` / `ARG_MAX` from other dialects are rewritten to these.
- **`MAP`**: the parser reads `MAP(k1, v1, k2, v2, ...)` as a variadic map. The generator expands literal arrays from DuckDB, Presto and Snowflake into `MAP('a', 1, 'b', 2)`. An odd argument count is a `ParseError`.
- **`ARRAY_CONTAINS_ALL(a, b)`**: generated instead of `@>`, and parsed back.
- **`TRIM`**: generated as `TRIM(str, chars)`, `LTRIM(str, chars)` or `RTRIM(str, chars)`. `TRIM(a, 'x')` now round-trips, and the Postgres `TRIM('x' FROM a)` form is rewritten to it. Without a character set, the output is still `TRIM(a)` / `LTRIM(a)` / `RTRIM(a)`.

The changes are in `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py` and `tests/dialects/test_starrocks.py`.

**Decisions to review**

- **Column-valued arrays in `MAP`.** A variadic `MAP(...)` can only be built when the arrays are literals, so a column-valued two-array map becomes `MAP_FROM_ARRAYS(keys, values)`. That is a native StarRocks function, and the parser reads it back. The StarRocks docs disagree on whether it arrived in 3.0 or 3.1.
- **COLLATE on TRIM.** A collation on a TRIM with a character set is dropped silently in the StarRocks output, since StarRocks has no equivalent. The no-character path already did this.

**Verification limits**

I checked the StarRocks docs through search snippets, not the full pages. Confirmed: `ltrim` / `rtrim` take a character set from 2.5, and `array_contains_all` exists from 2.4. The `trim(str, chars)` signature is inferred from a doc example, not read from the page. `min_by` / `max_by` are in the function list, but I found no syntax reference for them. Neither has been run against a live StarRocks instance.

## events
[tool_use Bash] {"command": "git status --short | head && cat sqlglot/dialects/starrocks.py && grep -n \"MIN_BY\\|MAX_BY\\|ArgMin\\|ArgMax\\|class Map\\b\\|class VarMap\\|ArrayContainsAll\\|class Trim\\|class Map(\" sqlglot/expressions.py | head -40", "description": "Inspect StarRocks dialect and related expressions"}
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
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "git status --short | head; ls sqlglot | head -80; cat sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py; ls sqlglot/dialects | head -50", "description": "List repo layout and StarRocks modules"}
[tool_result] __init__.py
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
from __future__ import annotations


from sqlglot import exp, transforms
from sqlglot.dialects.dialect import (
    approx_count_distinct_sql,
    arrow_json_extract_sql,
    rename_func,
    unit_to_str,
    inline_
…[16498 chars elided]…
      exp.RefreshTriggerProperty(
                method=method, kind=kind, starts=start, every=every, unit=unit
            )
        )
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
postgres.py
presto.py
prql.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/sr_probe.py <<'EOF'\nimport sqlglot\ncases = [\n (\"ARG_MAX(a, b)\", \"duckdb\", \"starrocks\"),\n (\"SELECT MIN_BY(a, b) FROM t\", \"duckdb\", \"starrocks\"),\n (\"SELECT ARG_MIN(a, b) FROM t\", \"duckdb\", \"starrocks\"),\n (\"SELECT MAX_BY(a, b) FROM t\", \"starrocks\", \"starrocks\"),\n (\"SEL
…[1114 chars elided]…
),\n (\"SELECT TRIM(a, 'x')\", \"starrocks\", \"starrocks\"),\n]\nfor sql, r, w in cases:\n    try:\n        print(f\"{r}->{w}: {sql!r}\\n    {sqlglot.transpile(sql, read=r, write=w)[0]}\")\n    except Exception as e:\n        print(f\"{r}->{w}: {sql!r}\\n    ERR {type(e).__name__}: {e}\")\nEOF\nPYTHONPATH=. $PY -I /tmp/sr_probe.py", "description": "Probe current StarRocks transpilation behavior"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/sr_probe.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/sr_probe.py", "description": "Run probe script against the repo sources"}
[tool_result] duckdb->starrocks: 'ARG_MAX(a, b)'
    ARG_MAX(a, b)
duckdb->starrocks: 'SELECT MIN_BY(a, b) FROM t'
    SELECT ARG_MIN(a, b) FROM t
duckdb->starrocks: 'SELECT ARG_MIN(a, b) FROM t'
    SELECT ARG_MIN(a, b) FROM t
starrocks->starrocks: 'SELECT MAX_BY(a, b) FROM t'
    SELECT ARG_MAX(a, b) FROM t
starrocks->starrocks: 'SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t'
    SELECT ARG_MIN(a, b) OVER (PARTITION BY c) FROM t
duckdb->starrocks: 'SELECT ARG_MAX(a, b) OVER (PARTITION BY c) FROM t'
    S
…[855 chars elided]…
 'SELECT ARRAY_CONTAINS_ALL(a, b)'
    SELECT a @> b
postgres->starrocks: "SELECT TRIM(BOTH 'x' FROM a)"
    SELECT TRIM(BOTH 'x' FROM a)
postgres->starrocks: "SELECT TRIM(LEADING 'x' FROM a)"
    SELECT TRIM(LEADING 'x' FROM a)
postgres->starrocks: "SELECT TRIM('x' FROM a)"
    SELECT TRIM('x' FROM a)
postgres->starrocks: 'SELECT TRIM(a)'
    SELECT TRIM(a)
starrocks->starrocks: 'SELECT TRIM(BOTH FROM a)'
    SELECT TRIM(a)
starrocks->starrocks: "SELECT TRIM(a, 'x')"
    SELECT TRIM('x' FROM a)
[tool_use Bash] {"command": "grep -rn \"class ArgMax\\|class ArgMin\\|class Map(\\|class VarMap\\|class ArrayContainsAll\\|class Trim\\|class MapFromArrays\\|class ArrayOverlaps\" sqlglot/expressions/ | head; grep -rn \"ArgMax\\|ArgMin\\|VarMap\\|ArrayContainsAll\\|exp.Trim\\|MapFromArrays\" sqlglot/generators/*.py sqlglot/parsers/*.py sqlglot/dialects/*.py sqlglot/generator.py sqlglot/parser.py | head -80", "description": "Find relevant expression classes and usages"}
[tool_result] sqlglot/expressions/aggregate.py:61:class ArgMax(Expression, AggFunc):
sqlglot/expressions/aggregate.py:66:class ArgMin(Expression, AggFunc):
sqlglot/expressions/array.py:113:class ArrayContainsAll(Expression, Binary, Func):
sqlglot/expressions/array.py:131:class ArrayOverlaps(Expression, Binary, Func):
sqlglot/expressions/array.py:283:class Map(Expression, Func):
sqlglot/expressions/array.py:339:class VarMap(Expression, Func):
sqlglot/expressions/string.py:241:class Trim(Expression, Func):
sqlg
…[3970 chars elided]…
1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1490:            name: lambda self: self._parse_max_min_by(exp.ArgMax) for name in exp.ArgMax.sql_names()
sqlglot/parser.py:1493:            name: lambda self: self._parse_max_min_by(exp.ArgMin) for name in exp.ArgMin.sql_names()
sqlglot/parser.py:8265:    def _parse_trim(self) -> exp.Trim:
sqlglot/parser.py:8288:            exp.Trim(this=this, position=position, expression=expression, collation=collation)
[tool_use Bash] {"command": "sed -n 40,80p sqlglot/expressions/aggregate.py; sed -n 105,135p sqlglot/expressions/array.py; sed -n 280,360p sqlglot/expressions/array.py; sed -n 236,260p sqlglot/expressions/string.py; sed -n 1470,1500p sqlglot/dialects/dialect.py; sed -n 1775,1800p sqlglot/dialects/dialect.py; sed -n 1930,1960p sqlglot/dialects/dialect.py; sed -n 640,670p sqlglot/generators/mysql.py; grep -n \"_parse_max_min_by\" -A25 sqlglot/parser.py | head -45; sed -n 8265,8295p sqlglot/parser.py; sed -n 3610,3630p sqlglot/generator.py", "description": "Read relevant expression and generator helper code"}
[tool_result] class ApproxTopK(Expression, AggFunc):
    arg_types = {"this": True, "expression": False, "counters": False}


class ApproxTopKAccumulate(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class ApproxTopKCombine(Expression, AggFunc):
    arg_types = {"this": True, "expression": False}


class ApproxTopKEstimate(Expression, Func):
    arg_types = {"this": True, "expression": False}


class ApproxTopSum(Expression, AggFunc):
    arg_types = {"this": True, "expression": T
…[12039 chars elided]…
c_name = "LTRIM"
        elif trim_type == "TRAILING":
            func_name = "RTRIM"
        else:
            func_name = "TRIM"

        return self.func(func_name, expression.this, expression.expression)

    def convert_concat_args(self, expression: exp.Func) -> list[exp.Expr]:
        args = expression.expressions
        if isinstance(expression, exp.ConcatWs):
            args = args[1:]  # Skip the delimiter

        if self.dialect.STRICT_STRING_CONCAT and expression.args.get("safe"):
[tool_use Bash] {"command": "echo placeholder", "description": "No-op placeholder"}
[tool_result] placeholder
[tool_use WebSearch] {"query": "StarRocks trim function syntax docs sql-functions string-functions trim ltrim rtrim", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks map constructor MAP(k1, v1, k2, v2) map_from_arrays docs", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks min_by max_by array_contains_all function docs", "mode": "standard"}
[tool_result] Web search results for query: "StarRocks min_by max_by array_contains_all function docs"

Links: [{"title":"Function list","url":"https://docs.starrocks.io/docs/3.1/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/function-list/"},{"title":"Function list","url":"https://docs.starrocks.io/docs/3.0/sql-reference/sql-functions/function-list/"},{"title":"array contains all","url":"https://docs.starrocks.io/zh/docs
…[2318 chars elided]…
e 0. It is documented as supported starting from version 2.4. The signature is `BOOLEAN array_contains_all(arr1, arr2)`, as shown in the CelerData mirror of the same docs (Checks whether arr1 contains all the elements of arr2).

Version note: the StarRocks 3.0 and 3.1 function lists both include `array_contains_all` in their array-function sections, so it is available in those releases as well.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks trim function syntax docs sql-functions string-functions trim ltrim rtrim"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/zh/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title
…[2802 chars elided]…
 mirror of the StarRocks rtrim page (Japanese) says that if the characters argument is an empty string, an error is returned.

The `trim` signature itself wasn't in the results. The likely form is `trim(str[, characters])`, but that is inferred from the examples, not confirmed. The official `trim` page at docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim would confirm it.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks map constructor MAP(k1, v1, k2, v2) map_from_arrays docs"

Links: [{"title":"map from arrays","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.celerdata.com/BYOC/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays"},{"t
…[2195 chars elided]…
, value_expr ...) form, where keys and values must come in pairs, with the example `map(a,1,b,2,c,3)`. The same page also lists a brace form, `map{a:1, b:2, c:3}`, and notes that key and value types are inferred from the inputs.

For the English constructor reference, check docs.starrocks.io under the map functions or data type section. I couldn't confirm the English wording from these results.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_use Bash] {"command": "sed -n 40,60p sqlglot/parser.py; grep -rn \"TRIM_PATTERN_FIRST\\|\\\"MAP\\\"\\|exp.Map\\b\\|exp.Map:\" sqlglot/ | grep -v \"^sqlglot/expressions/\" | head -30; grep -n \"TRANSFORMS\" sqlglot/generator.py | head; grep -n \"def sql(\" -A60 sqlglot/generator.py | grep -n \"TRANSFORMS\\|_sql\\\"\\|getattr\\|handler\" ", "description": "Check dispatch order and MAP/TRIM parser hooks"}
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
…[3063 chars elided]…
p.Expr], t.Callable[..., str]]] = {
136:        **JSON_PATH_PART_TRANSFORMS,
655:    AFTER_HAVING_MODIFIER_TRANSFORMS: t.ClassVar = {
659:        **AFTER_HAVING_MODIFIER_TRANSFORMS,
3249:            *[gen(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.values()],
3748:            transform = self.TRANSFORMS.get(expression.__class__)
19:1105-        handler = self._dispatch.get(expression.__class__)
21:1107-        if handler:
22:1108-            sql = handler(self, expression)
[tool_use Bash] {"command": "sed -n 78,100p sqlglot/generator.py; sed -n 1100,1125p sqlglot/generator.py; grep -n \"exp.Map\\|MAP\\|VarMap\\|map_\" sqlglot/generators/mysql.py | head; sed -n 1,30p sqlglot/generators/mysql.py | grep -n import -A12 | head -30; grep -n \"\\\"MAP\\|MAP_\" sqlglot/parsers/mysql.py sqlglot/parser.py | head; sed -n 1,30p sqlglot/parsers/doris.py 2>/dev/null | head -5; ls tests/dialects | grep -i starrocks; grep -n \"TRIM\\|MIN_BY\\|MAX_BY\\|ARG_M\\|MAP(\\|@>\" tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head -40", "description": "Check dispatch precedence and existing StarRocks tests"}
[tool_result] def _build_dispatch(
    cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and expr_cls not in dispatch:
            dispatch[expr_cls] = getattr(cls, attr_name)

    r
…[2622 chars elided]…
m sqlglot.dialects.dialect import build_date_delta_with_interval
test_starrocks.py
tests/dialects/test_mysql.py:308:        self.validate_identity("SELECT TRIM(LEADING 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:309:        self.validate_identity("SELECT TRIM(TRAILING 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:310:        self.validate_identity("SELECT TRIM(BOTH 'bla' FROM ' XXX ')")
tests/dialects/test_mysql.py:311:        self.validate_identity("SELECT TRIM('bla' FROM ' XXX ')")
[assistant] The StarRocks dialect lives in `sqlglot/generators/starrocks.py` and `sqlglot/parsers/starrocks.py`. Generator dispatch checks `TRANSFORMS` before `*_sql` methods, so I'll override the inherited entries directly. Let me check the existing tests and the LTRIM/MAP parse paths before editing.
[tool_use Bash] {"command": "grep -n \"build_trim\\|\\\"LTRIM\\\"\\|\\\"RTRIM\\\"\" sqlglot/parser.py | head; grep -n \"TRANSFORMS = {\" -A3 sqlglot/generators/mysql.py | head -8; wc -l tests/dialects/test_starrocks.py; sed -n 1,40p tests/dialects/test_starrocks.py; grep -n \"def test_\" tests/dialects/test_starrocks.py | tail -5; tail -30 tests/dialects/test_starrocks.py", "description": "Check LTRIM parsing, MySQL TRANSFORMS base, and existing StarRocks tests"}
[tool_result] 165:def build_trim(args: BuilderArgs, is_left: bool = True, reverse_args: bool = False) -> exp.Trim:
394:        "LTRIM": lambda args: build_trim(args),
398:        "RTRIM": lambda args: build_trim(args, is_left=False),
153:    TRANSFORMS = {
154-        **generator.Generator.TRANSFORMS,
155-        exp.ArrayAgg: rename_func("GROUP_CONCAT"),
156-        exp.BitwiseAndAgg: rename_func("BIT_AND"),
     335 tests/dialects/test_starrocks.py
from sqlglot import exp
from sqlglot.errors import Unsuppor
…[3105 chars elided]…
   self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] Now the generator edits: native `MAX_BY`/`MIN_BY`, `ARRAY_CONTAINS_ALL`, a MAP writer, and a TRIM writer.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    return self.func(\"ST_Distance_Sphere\", point1_x, point1_y, point2_x, point2_y)\n\n\nclass StarRocksGenerator(MySQLGenerator):", "new_string": "    return self.func(\"ST_Distance_Sphere\", point1_x, p
…[909 chars elided]…
:\n        return self.trim_sql(expression)\n\n    # StarRocks takes the characters to strip as a second argument, e.g. TRIM(str, chars)\n    position = self.sql(expression, \"position\")\n    func_name = {\"LEADING\": \"LTRIM\", \"TRAILING\": \"RTRIM\"}.get(position, \"TRIM\")\n    return self.func(func_name, expression.this, expression.expression)\n\n\nclass StarRocksGenerator(MySQLGenerator):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: rename_func(\"ARRAY_FILTER\"),\n        exp.ArrayToString: rename_func(\"ARRAY_JOIN\"),\n        exp.ApproxDistinct: approx_count
…[1043 chars elided]…
_DIFF\", unit_to_str(e), e.this, e.expression),\n        exp.Delete: transforms.preprocess([_eliminate_between_in_delete]),\n        exp.Flatten: rename_func(\"ARRAY_FLATTEN\"),\n        exp.JSONExtractScalar: arrow_json_extract_sql,\n        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Map: _map_sql,\n        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.UnixToStr: lambda self, e: self.func(\"FROM_UNIXTIME\", e.this, self.format_time(e)),\n        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n    }", "new_string": "        exp.TimeStrToDate: rename_func(\"TO_DATE\"),\n        exp.Trim: _trim_sql,\n        exp.UnixToStr: lambda self, e: self.func(\"FROM_UNIXTIME\", e.this, self.format_time(e)),\n        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n        exp.VarMap: _map_sql,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arg_max_or_min_no_count,\n    arrow_json_extract_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now the parser: variadic `MAP(...)` and StarRocks' `MAP_FROM_ARRAYS`, so its own forms parse back.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser\nfrom sqlglot.tokens import TokenType", "new_string": "from sqlglot.helper import seq_get\nfrom sqlglot.parser import build_var_map\nfrom sqlglot.parsers.mysql import MySQLParser\nfrom sqlglot.tokens import TokenType"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/sr_probe2.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n (\"SELECT MIN_BY(a, b) FROM t\", \"starrocks\", \"starrocks\"),\n (\"SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t\", \"starrocks\", \"starrocks\"),\n (\"SELECT MIN_BY(a, b) FROM t\", \"duckdb\", \"starrocks\"),\n (\"SELECT ARG_MAX(a, b) FROM t\", \"duckdb\", \"starrocks\"),\n (\"SELECT ARG_MIN(a,
…[1944 chars elided]…
, write=w)[0]}\")\n    except Exception as e:\n        print(f\"{r}->{w}: {sql!r}\\n    ERR {type(e).__name__}: {e}\")\nprint(repr(sqlglot.parse_one(\"SELECT MAP('a', 1, 'b', 2)\", read=\"starrocks\").selects[0]))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/sr_probe2.py 2>&1", "description": "Re-run probes against the edited StarRocks dialect"}
[tool_result] starrocks->starrocks: 'SELECT MIN_BY(a, b) FROM t'
    SELECT MIN_BY(a, b) FROM t
starrocks->starrocks: 'SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t'
    SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t
duckdb->starrocks: 'SELECT MIN_BY(a, b) FROM t'
    SELECT MIN_BY(a, b) FROM t
duckdb->starrocks: 'SELECT ARG_MAX(a, b) FROM t'
    SELECT MAX_BY(a, b) FROM t
duckdb->starrocks: 'SELECT ARG_MIN(a, b) OVER (PARTITION BY c) FROM t'
    SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
starrocks
…[1846 chars elided]…
' FROM a)
starrocks->duckdb: "SELECT TRIM(a, 'x')"
    SELECT TRIM(a, 'x')
starrocks->mysql: "SELECT TRIM(a, 'x')"
    SELECT TRIM('x' FROM a)
starrocks->starrocks: 'SELECT TRIM(a)'
    SELECT TRIM(a)
starrocks->starrocks: 'SELECT LTRIM(a)'
    SELECT LTRIM(a)
VarMap(
  keys=Array(
    expressions=[
      Literal(this='a', is_string=True),
      Literal(this='b', is_string=True)]),
  values=Array(
    expressions=[
      Literal(this=1, is_string=False),
      Literal(this=2, is_string=False)]))
[assistant] Output matches the StarRocks forms I targeted. One thing to check: an odd-argument `MAP(...)` goes through the shared `build_var_map`, which may raise a raw `IndexError` instead of a parse error. Then I'll run the suite.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ntry:\n    print(sqlglot.transpile(\\\"SELECT MAP('a', 1, 'b')\\\", read='starrocks', write='starrocks'))\nexcept Exception as e: print(type(e).__name__, e)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_dialect.py 2>&1 | tail -30", "description": "Check odd-arg MAP handling and run dialect tests"}
[tool_result] IndexError list index out of range
................................................................................................................................................................. [100%]
161 passed, 3385 subtests passed in 0.61s
[assistant] The suite passes. The odd-argument case now raises a raw `IndexError`, though, which is worse than a `ParseError`. Let me see how the DuckDB parser handles its own `MAP` so I can match it.
[tool_use Bash] {"command": "sed -n 196,203p sqlglot/parsers/duckdb.py; sed -n 330,342p sqlglot/parsers/duckdb.py; grep -n \"FUNCTION_PARSERS = {\" sqlglot/parsers/starrocks.py sqlglot/parsers/mysql.py sqlglot/parser.py | head -3", "description": "Inspect DuckDB MAP parser for pattern reuse"}
[tool_result]         ),
    }

    NO_PAREN_FUNCTION_PARSERS = {
        **parser.Parser.NO_PAREN_FUNCTION_PARSERS,
        "MAP": lambda self: self._parse_map(),
        "@": lambda self: exp.Abs(this=self._parse_bitwise()),
    }
            bracket.set("returns_list_for_maps", True)

        return bracket

    def _parse_map(self) -> exp.ToMap | exp.Map:
        if self._match(TokenType.L_BRACE, advance=False):
            return self.expression(exp.ToMap(this=self._parse_bracket()))

        args = self._parse_wrapped_csv(self._parse_assignment)
        return self.expression(exp.Map(keys=seq_get(args, 0), values=seq_get(args, 1)))

    def _parse_struct_types(self, type_required: bool = False) -> exp.Expr | None:
        return self._parse_field_def()
sqlglot/parsers/mysql.py:154:    FUNCTION_PARSERS = {
[assistant] I'll add a small `_parse_var_map` that reports an odd argument count as a proper parse error, and test it.
[tool_use Bash] {"command": "grep -n \"def _parse_char\\b\" -A12 sqlglot/parser.py | head -20; grep -n \"def raise_error\" sqlglot/parser.py", "description": "Look at a FUNCTION_PARSERS example and raise_error"}
[tool_result] 7819:    def _parse_char(self) -> exp.Chr:
7820-        return self.expression(
7821-            exp.Chr(
7822-                expressions=self._parse_csv(self._parse_assignment),
7823-                charset=self._match(TokenType.USING) and self._parse_charset_name(),
7824-            )
7825-        )
7826-
7827-    def _parse_charset_name(self) -> exp.Expr | None:
7828-        """
7829-        Parse a charset name after USING or CHARACTER SET. Dialects that need to preserve quoting
7830-        for specific name shapes override this.
7831-        """
1987:    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.helper import seq_get\nfrom sqlglot.parser import build_var_map\nfrom sqlglot.parsers.mysql import MySQLParser", "new_string": "from sqlglot.helper import seq_get\nfrom sqlglot.parsers.mysql import MySQLParser"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,\n    }\n", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,\n    }\n\n    FUNCTION_PARSERS = {\n        **MySQLParser.FUNCTION_PARSERS,\n        \"MAP\": lambda self: self._parse_var_map(),\n    }\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "    def _parse_rollup_property(self) -> exp.RollupProperty:", "new_string": "    def _parse_var_map(self) -> exp.VarMap:\n        # MAP(k1, v1, k2, v2, ...)\n        args = self._parse_csv(self._parse_assignment)\n        if len(args) % 2:\n            self.raise_error(\"MAP expects an even number of key and value arguments\")\n\n        return self.expression(\n            exp.VarMap(keys=exp.array(*args[::2], copy=False), values=exp.array(*args[1::2], copy=False))\n        )\n\n    def _parse_rollup_property(self) -> exp.RollupProperty:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/sr_probe2.py 2>&1 | grep -A1 \"MAP\" | head -30; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT MAP('a', 1, 'b')\\\", 'SELECT MAP()']:\n    try: print(sqlglot.transpile(s, read='starrocks', write='starrocks'))\n    except Exception as e: print(type(e).__name__, e)\n\"", "description": "Re-run MAP probes and odd-arg error check"}
[tool_result] starrocks->starrocks: "SELECT MAP('a', 1, 'b', 2)"
    SELECT MAP('a', 1, 'b', 2)
starrocks->duckdb: "SELECT MAP('a', 1)"
    SELECT MAP(['a'], [1])
starrocks->starrocks: 'SELECT MAP()'
    SELECT MAP()
duckdb->starrocks: "SELECT MAP(['a'], [1])"
    SELECT MAP('a', 1)
presto->starrocks: "SELECT MAP(ARRAY['a'], ARRAY[1])"
    SELECT MAP('a', 1)
presto->starrocks: "SELECT MAP(ARRAY['a', 'b'], ARRAY[1])"
    SELECT MAP_FROM_ARRAYS(['a', 'b'], [1])
snowflake->starrocks: "SELECT MAP(ARRAY['a'], ARRA
…[201 chars elided]…
sto: 'SELECT MAP_FROM_ARRAYS(k, v)'
    SELECT MAP(k, v)
starrocks->presto: "SELECT MAP('a', 1, 'b', 2)"
    SELECT MAP(ARRAY['a', 'b'], ARRAY[1, 2])
starrocks->duckdb: "SELECT MAP('a', 1, 'b', 2)"
    SELECT MAP(['a', 'b'], [1, 2])
starrocks->spark: "SELECT MAP('a', 1, 'b', 2)"
    SELECT MAP('a', 1, 'b', 2)
starrocks->starrocks: 'SELECT ARRAY_CONTAINS_ALL(a, b)'
ParseError MAP expects an even number of key and value arguments. Line 1, Col: 23.
  SELECT MAP('a', 1, 'b'[4m)[0m
['SELECT MAP()']
[assistant] Odd-argument `MAP` now gives a clean `ParseError`. Next I'll add tests covering each form, then run the whole suite to catch any other test that expected the old output.
[tool_use Bash] {"command": "grep -rn \"starrocks\" tests/ --include=*.py -l; grep -rn \"\\\"starrocks\\\"\" tests/dialects/*.py | grep -i \"ARG_\\|MAX_BY\\|MIN_BY\\|TRIM\\|MAP(\\|@>\" | head; sed -n 173,185p tests/dialects/test_starrocks.py", "description": "Find other tests that reference StarRocks output"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rln \"starrocks\" tests/ ; grep -rn \"starrocks\" tests/dialects/*.py | grep -i \"ARG_\\|MAX_BY\\|MIN_BY\\|TRIM\\|MAP(\\|@>\" | head", "description": "Find tests referencing StarRocks"}
[tool_result] tests/test_transpile.py
tests/dialects/test_bigquery.py
tests/dialects/test_snowflake.py
tests/dialects/test_oracle.py
tests/dialects/test_presto.py
tests/dialects/test_starrocks.py
tests/dialects/test_redshift.py
tests/dialects/test_teradata.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_mysql.py
tests/dialects/test_postgres.py
tests/fixtures/optimizer/qualify_columns.sql
[assistant] Now I'll add the StarRocks tests, placing them in the existing `test_starrocks.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_distinct_on(self):", "new_string": "    def test_min_max_by(self):\n        self.validate_identity(\"SELECT MIN_BY(a, b) FROM t\")\n        self.validate_identity(\"SELECT MAX_BY(a, b) OVER (
…[2001 chars elided]…
    read={\"postgres\": \"SELECT TRIM(LEADING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT RTRIM(a, 'x')\",\n            read={\"postgres\": \"SELECT TRIM(TRAILING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT TRIM(a, 'x')\",\n            write={\"postgres\": \"SELECT TRIM('x' FROM a)\"},\n        )\n\n    def test_distinct_on(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] I put a duplicate `postgres` key in `test_trim`, and I haven't verified the Snowflake `OBJECT_CONSTRUCT` read. Fixing both and adding the imports.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "            read={\n                \"postgres\": \"SELECT TRIM('x' FROM a)\",\n                \"postgres\": \"SELECT TRIM(BOTH 'x' FROM a)\",\n            },\n        )", "new_string": "            read={\"postgres\": \"SELECT TRIM(BOTH 'x' FROM a)\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "                \"presto\": \"SELECT MAP(ARRAY['a', 'b'], ARRAY[1, 2])\",\n                \"snowflake\": \"SELECT OBJECT_CONSTRUCT('a', 1, 'b', 2)\",\n            },", "new_string": "                \"presto\": \"SELECT MAP(ARRAY['a', 'b'], ARRAY[1, 2])\",\n            },"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.errors import UnsupportedError\nfrom tests.dialects.test_dialect import Validator", "new_string": "from sqlglot import exp, parse_one\nfrom sqlglot.errors import ParseError, UnsupportedError\nfrom tests.dialects.test_dialect import Validator"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Run StarRocks dialect tests"}
[tool_result] ................                                                 [100%]
16 passed, 80 subtests passed in 0.09s
[assistant] StarRocks tests pass. Now the full suite using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite", "timeout": 600000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
.......................................
…[321 chars elided]…
[ 66%]
............................................................................................................ [ 76%]
.......................................... [ 79%]
.............................................................................. [ 86%]
............................................................. [ 92%]
.........................................................................................                                [100%]
1126 passed, 18211 subtests passed in 53.22s
[assistant] Full suite is green: 1126 passed. Next, the style checks the repo uses.
[tool_use Bash] {"command": "grep -n \"^style\" -A6 Makefile; ls <work>/env-sqlglot/bin | grep -i \"ruff\\|mypy\"; <work>/env-sqlglot/bin/ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py 2>&1; <work>/env-sqlglot/bin/ruff check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py 2>&1 | tail -20", "description": "Check repo style target and ruff on changed files"}
[tool_result] 119:style:
120-	pre-commit run --all-files
121-	@if [ -f sqlglot-integration-tests/Makefile ]; then \
122-		MYPYPATH=$(abspath .) $(MAKE) -C sqlglot-integration-tests style && \
123-		$(MAKE) -C sqlglot-integration-tests check-submodule; \
124-	fi
125-
dmypy
mypy
mypyc
ruff
Would reformat: sqlglot/parsers/starrocks.py
1 file would be reformatted, 2 files already formatted
All checks passed!
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/ruff format sqlglot/parsers/starrocks.py && git diff sqlglot/parsers/starrocks.py | head -80; $R/mypy sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py 2>&1 | tail -5", "description": "Apply ruff formatting and type-check StarRocks modules", "timeout": 300000}
[tool_result] 1 file reformatted
diff --git a/sqlglot/parsers/starrocks.py b/sqlglot/parsers/starrocks.py
index eb5387154..90b918ef4 100644
--- a/sqlglot/parsers/starrocks.py
+++ b/sqlglot/parsers/starrocks.py
@@ -27,9 +27,15 @@ class StarRocksParser(MySQLParser):
             this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
         ),
         "ARRAY_FLATTEN": exp.Flatten.from_arg_list,
+        "MAP_FROM_ARRAYS": exp.Map.from_arg_list,
         "REGEXP": exp.RegexpLike.from_arg_lis
…[699 chars elided]…
      exp.VarMap(
+                keys=exp.array(*args[::2], copy=False), values=exp.array(*args[1::2], copy=False)
+            )
+        )
+
     def _parse_rollup_property(self) -> exp.RollupProperty:
         # ROLLUP (rollup_name (col1, col2) [FROM from_index] [PROPERTIES (...)], ...)
         def parse_rollup_index() -> exp.RollupIndex:
Success: no issues found in 2 source files
[This command modified 1 file you've previously read: sqlglot/parsers/starrocks.py. Call Read before editing.]
[assistant] The only change in that output is ruff's formatting of the parser, which I made deliberately. mypy is clean. I'll re-run the StarRocks tests and review the final generator diff.
[tool_use Bash] {"command": "R=<work>/env-sqlglot/bin; $R/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/ 2>&1 | tail -2; git diff --stat; git diff sqlglot/generators/starrocks.py | head -120", "description": "Re-run dialect tests and review generator diff", "timeout": 300000}
[tool_result] .................................................................................................................................................................................................................................................................................................                     [100%]
740 passed, 11120 subtests passed in 2.46s
 sqlglot/generators/starrocks.py  | 36 ++++++++++++++++++++++
 sqlglot/parsers/starrocks.py     | 18 +++++++++++
 tests/dialects/test_starro
…[3207 chars elided]…
STAMP", e.this, self.format_time(e)),
         exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", unit_to_str(e), e.this),
         exp.TimeStrToDate: rename_func("TO_DATE"),
+        exp.Trim: _trim_sql,
         exp.UnixToStr: lambda self, e: self.func("FROM_UNIXTIME", e.this, self.format_time(e)),
         exp.UnixToTime: rename_func("FROM_UNIXTIME"),
+        exp.VarMap: _map_sql,
     }
 
     # https://docs.starrocks.io/docs/sql-reference/sql-statements/keywords/#reserved-keywords
[tool_use Bash] {"command": "rm -f /tmp/sr_probe.py /tmp/sr_probe2.py; cd ~/.cache/lithify/work/repo-90e86f132b84/20261028-142458-starrocks-dialect-several-functi/base-1 && git status --short", "description": "Remove probe scripts and confirm changed files"}
[tool_result]  M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.py
[assistant] The StarRocks dialect now generates its own forms for all four functions and parses them back. The full suite passes (1126 tests), and ruff and mypy are clean on the changed modules. I did not commit.

**What changed**

- **`MIN_BY` / `MAX_BY`**: generated as `MIN_BY` / `MAX_BY`, including the window form. `ARG_MIN` / `ARG_MAX` from other dialects are rewritten to these.
- **`MAP`**: the parser reads `MAP(k1, v1, k2, v2, ...)` as a variadic map. The generator expands literal arrays from DuckDB, Presto and Snowflake into `MAP('a', 1, 'b', 2)`. An odd argument count is a `ParseError`.
- **`ARRAY
…[819 chars elided]…
** A collation on a TRIM with a character set is dropped silently in the StarRocks output, since StarRocks has no equivalent. The no-character path already did this.

**Verification limits**

I checked the StarRocks docs through search snippets, not the full pages. Confirmed: `ltrim` / `rtrim` take a character set from 2.5, and `array_contains_all` exists from 2.4. The `trim(str, chars)` signature is inferred from a doc example, not read from the page. `min_by` / `max_by` are in the function list, but I found no syntax reference for them. Neither has been run against a live StarRocks instance.
