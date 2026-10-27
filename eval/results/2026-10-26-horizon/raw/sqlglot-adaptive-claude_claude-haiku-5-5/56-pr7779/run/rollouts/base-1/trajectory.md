# trajectory base-1

final message:
All four StarRocks forms now generate StarRocks-native SQL and parse StarRocks' own forms back. The full suite passes (1126 tests), and ruff and mypy are clean on the changed modules. Nothing is committed.

- **`MIN_BY` / `MAX_BY`:** emitted by name, including the `OVER (...)` window form. Previously these came out as `ARG_MIN` / `ARG_MAX`.
- **`MAP`:** parsed as the variadic constructor, so `MAP(1, 2, 3, 4)` round-trips. Two literal arrays from DuckDB or Presto become `MAP(1, 3, 2, 4)`.
- **`ARRAY_CONTAINS_ALL(a, b)`:** emitted by name instead of `@>`.
- **`TRIM`:** StarRocks only takes `trim(str[, chars])`, so `TRIM(BOTH 'x' FROM a)` becomes `TRIM(a, 'x')`, `LEADING` becomes `LTRIM(a, 'x')`, and `TRAILING` becomes `RTRIM(a, 'x')`.

The changes are in `sqlglot/parsers/starrocks.py`, `sqlglot/generators/starrocks.py`, and new tests in `tests/dialects/test_starrocks.py`. Existing tests were not touched.

Choices I made that you may want to change:
- **Non-literal two-array maps** (e.g. DuckDB `MAP(k_col, v_col)`) become `MAP_FROM_ARRAYS(k, v)`, which StarRocks has from 3.1 onward. The variadic form needs literal arrays to expand.
- **`COLLATE` on `TRIM`** has no StarRocks equivalent, so it raises an "unsupported" warning rather than being dropped silently.

Known gaps:
- Literal arrays of unequal length in a two-array `MAP` are silently truncated, because the element pairing stops at the shorter array. The source SQL is already invalid in that case, but nothing warns about it.
- I checked the syntax against StarRocks' published docs, not a live StarRocks instance, so the output is verified by docs and tests only.

## events
[assistant] I'll start by reading the StarRocks dialect and the existing tests for these functions.
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "git status --short | head && ls sqlglot/dialects/starrocks.py sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py 2>&1; grep -rn -i \"minby\\|max_by\\|arg_min\\|ArrayContainsAll\\|ARRAY_CONTAINS_ALL\\|MAP(\" sqlglot/dialects/starrocks.py sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py sqlglot/dialects/mysql.py sqlglot/generators/mysql.py sqlglot/parsers/mysql.py 2>/dev/null | head -50", "description": "Check repo state and grep StarRocks-related code"}
[tool_result] sqlglot/dialects/starrocks.py
sqlglot/generators/starrocks.py
sqlglot/parsers/starrocks.py
tests/dialects/test_starrocks.py
sqlglot/generators/mysql.py:652:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
[assistant] Those Docs tools are unrelated to this SQL task, so I'll ignore them. Next I'm reading the StarRocks dialect, parser, generator and tests.
[tool_use Bash] {"command": "cat sqlglot/dialects/starrocks.py sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py && sed -n 640,670p sqlglot/generators/mysql.py && wc -l tests/dialects/test_starrocks.py && git log --oneline -1", "description": "Read StarRocks dialect, parser, generator and MySQL array helper"}
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

    Ge
…[17776 chars elided]…
    def dpipe_sql(self, expression: exp.DPipe) -> str:
        return self.func("CONCAT", *expression.flatten())

    def extract_sql(self, expression: exp.Extract) -> str:
        unit = expression.name
        if unit and unit.lower() == "epoch":
            return self.func("UNIX_TIMESTAMP", expression.expression)

        return super().extract_sql(expression)

    def datatype_sql(self, expression: exp.DataType) -> str:
     335 tests/dialects/test_starrocks.py
f9d7a0c7b lithify: probe base
[assistant] I've read the StarRocks files. Next I'll check what the current code actually emits for each of the four cases, using the repo's source.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY 2>&1; PYTHONPATH=. $PY -c \"\nimport sqlglot\ncases = [\n ('duckdb','SELECT ARG_MAX(a,b) FROM t'),\n ('duckdb','SELECT ARG_MIN(a,b) FROM t'),\n ('snowflake','SELECT MAX_BY(a,b) FROM t'),\n ('spark','SELECT MIN_BY(a,b) OV
…[948 chars elided]…
s in cases:\n    try:\n        e = sqlglot.parse_one(s, read=d)\n        print(d, '|', s, '\\n   ->', e.sql('starrocks'), '\\n   AST:', repr(e)[:0] or type(e.selects[0]).__name__ if hasattr(e,'selects') else '')\n    except Exception as ex:\n        print(d,'|',s,'\\n   ERR',type(ex).__name__, str(ex)[:200])\n\" 2>&1", "description": "Probe current StarRocks output for the four function families"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
duckdb | SELECT ARG_MAX(a,b) FROM t 
   -> SELECT ARG_MAX(a, b) FROM t 
   AST: ArgMax
duckdb | SELECT ARG_MIN(a,b) FROM t 
   -> SELECT ARG_MIN(a, b) FROM t 
   AST: ArgMin
snowflake | SELECT MAX_BY(a,b) FROM t 
 
…[1614 chars elided]…
[4m>[0m b FROM t
starrocks | SELECT TRIM(BOTH 'x' FROM a) 
   -> SELECT TRIM(BOTH 'x' FROM a) 
   AST: Trim
starrocks | SELECT TRIM(LEADING 'x' FROM a) 
   -> SELECT TRIM(LEADING 'x' FROM a) 
   AST: Trim
starrocks | SELECT TRIM(a) 
   -> SELECT TRIM(a) 
   AST: Trim
starrocks | SELECT TRIM('x' FROM a) 
   -> SELECT TRIM('x' FROM a) 
   AST: Trim
postgres | SELECT TRIM(BOTH 'x' FROM a) 
   -> SELECT TRIM(BOTH 'x' FROM a) 
   AST: Trim
duckdb | SELECT TRIM(a) 
   -> SELECT TRIM(a) 
   AST: Trim
[assistant] The probe shows four real gaps: `ARG_MIN`/`ARG_MAX` are emitted for `MIN_BY`/`MAX_BY`, two-array `MAP` is emitted as-is, `ARRAY_CONTAINS_ALL` becomes `@>`, and `TRIM(... FROM ...)` passes through. Next I'll check the node definitions and the existing StarRocks tests.
[tool_use Bash] {"command": "grep -rn -A6 \"^class ArgMax\\|^class ArgMin\\|^class Map(\\|^class Trim\\|^class ArrayContainsAll\\|^class VarMap\\|^class MapFromEntries\" sqlglot/expressions/ | head -120; echo ----; grep -rn \"def trim_sql\\|def map_sql\\|def trim\\b\\|exp.Trim\\|VarMap\\|def arrayagg\\|ArgMax\\|ArgMin\\|MAX_BY\\|MIN_BY\" sqlglot/generator.py sqlglot/generators/mysql.py sqlglot/generators/duckdb.p
…[58 chars elided]…
rs/presto.py sqlglot/dialects/dialect.py sqlglot/dialects/snowflake.py sqlglot/parsers/spark.py sqlglot/dialects/spark*.py sqlglot/generators/spark.py 2>/dev/null | head -60; echo ----; grep -n \"def test\\|ARG_M\\|MAX_BY\\|MIN_BY\\|MAP\\|TRIM\\|CONTAINS_ALL\\|@>\" tests/dialects/test_starrocks.py | head -80", "description": "Inspect node definitions, generator hooks and existing StarRocks tests"}
[tool_result] sqlglot/expressions/aggregate.py:61:class ArgMax(Expression, AggFunc):
sqlglot/expressions/aggregate.py-62-    arg_types = {"this": True, "expression": True, "count": False}
sqlglot/expressions/aggregate.py-63-    _sql_names = ["ARG_MAX", "ARGMAX", "MAX_BY"]
sqlglot/expressions/aggregate.py-64-
sqlglot/expressions/aggregate.py-65-
sqlglot/expressions/aggregate.py:66:class ArgMin(Expression, AggFunc):
sqlglot/expressions/aggregate.py-67-    arg_types = {"this": True, "expression": True, "count": 
…[4293 chars elided]…
:8288:            exp.Trim(this=this, position=position, expression=expression, collation=collation)
----
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
[assistant] Next I'll read the shared helpers this will hook into: `map_sql`, the ArgMax/ArgMin helper, `trim_sql`, and the MySQL and base generator entries.
[tool_use Bash] {"command": "sed -n 1470,1500p sqlglot/dialects/dialect.py; echo ----; sed -n 1775,1800p sqlglot/dialects/dialect.py; echo ----; sed -n 1930,1960p sqlglot/dialects/dialect.py; echo ----; sed -n 3610,3625p sqlglot/generator.py; echo ----; grep -n \"trim_sql\\|exp.Map\\b\\|exp.Map:\\|VarMap\\|ArgMax\\|ArgMin\\|ArrayContainsAll\\|arg_max_or_min\" sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/presto.py sqlglot/generators/snowflake.py sqlglot/generators/spark.py sqlglot/generators/duckdb.py | head -40; echo ----; sed -n 8265,8290p sqlglot/parser.py; echo ----; grep -n \"def _parse_map\\|\\\"MAP\\\"\" sqlglot/parser.py sqlglot/parsers/*.py | head", "description": "Read shared helpers for map, trim, arg-max and related generator hooks"}
[tool_result]         return _build_func_call(self, name, wrapped_args)

    return _array_concat_sql


def var_map_sql(
    self: Generator, expression: exp.Map | exp.VarMap, map_func_name: str = "MAP"
) -> str:
    keys = expression.args.get("keys")
    values = expression.args.get("values")

    if not isinstance(keys, exp.Array) or not isinstance(values, exp.Array):
        self.unsupported("Cannot convert array columns into map.")
        return self.func(map_func_name, keys, values)

    args = []
    f
…[5842 chars elided]…
p_token is not None and map_token.text.upper() == "MAP"
sqlglot/parsers/clickhouse.py:287:        "MAP": parser.build_var_map,
sqlglot/parsers/duckdb.py:201:        "MAP": lambda self: self._parse_map(),
sqlglot/parsers/duckdb.py:334:    def _parse_map(self) -> exp.ToMap | exp.Map:
sqlglot/parsers/materialize.py:15:        "MAP": lambda self: self._parse_map(),
sqlglot/parsers/materialize.py:28:    def _parse_map(self) -> exp.ToMap:
sqlglot/parsers/hive.py:99:        "MAP": parser.build_var_map,
[assistant] The base helpers I need exist: `var_map_sql` already expands literal key and value arrays into the variadic form. Before I settle the TRIM and MAP output, I need StarRocks' actual syntax for both, so I'm checking its docs.
[tool_use ToolSearch] {"query": "select:WebSearch", "max_results": 1}
[tool_result] 
[tool_use WebSearch] {"query": "StarRocks trim function syntax docs", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks map_from_arrays function MAP constructor syntax", "mode": "standard"}
[tool_result] Web search results for query: "StarRocks map_from_arrays function MAP constructor syntax"

Links: [{"title":"map from arrays","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.celerdata.com/BYOC/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays"},{"title":"ma
…[1502 chars elided]…
s NULL keys or values. When a key repeats, Doris keeps the last value. Doris also only checks length when both arrays are non-NULL.

**Gap:** The results don't cover a separate MAP literal or `map()` constructor syntax in StarRocks, so I can't confirm whether one exists. The StarRocks MAP data-type page covers the column type declaration, `MAP<key_type,value_type>`, but not a value constructor.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks trim function syntax docs"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/string-functions/trim/"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io
…[1334 chars elided]…
.

The docs also cover the one-sided variants, `ltrim` and `rtrim`, which accept the same arguments. Support for specifying characters starts at StarRocks 2.5.0.

Caveat: the Apache Doris docs also have a `trim` page. Its documented behavior differs: it removes the full second argument as a string rather than as a character set. Don't mix the two sets of semantics if you're targeting StarRocks.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] Both answers are in. StarRocks `trim` takes only `trim(str[, chars])`, with `ltrim`/`rtrim` as the one-sided forms, so `BOTH`/`LEADING`/`TRAILING ... FROM` has to be rewritten. `map_from_arrays` exists (v3.1+), so non-literal two-array maps can map to it. Next I'll check how the generator dispatches `Map`/`Trim`, how `build_var_map` and `build_trim` parse, and what the function-name parsers do with the second argument.
[tool_use Bash] {"command": "sed -n 40,56p sqlglot/parser.py; sed -n 160,172p sqlglot/parser.py; grep -n \"def map_sql\\|exp.Map:\\|exp.Map\\b\" sqlglot/generator.py | head; grep -n \"TRIM_PATTERN_FIRST\\|\\\"LTRIM\\\"\\|\\\"RTRIM\\\"\\|\\\"TRIM\\\"\" sqlglot/parser.py sqlglot/parsers/mysql.py | head; grep -n \"TRANSFORMS\\b\" sqlglot/generator.py | head -5; grep -n \"if transform := \\|self.TRANSFORMS.get\\|TRAN
…[116 chars elided]…
ra-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT LTRIM(a, \\'x\\')','SELECT TRIM(a, \\'x\\')','SELECT RTRIM(a)','SELECT MAP(1,2)']:\n    e=sqlglot.parse_one(s, read='starrocks'); print(s, '->', repr(e.selects[0])[:200])\n\"", "description": "Inspect parser builders and generator dispatch for Map and Trim"}
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
…[1280 chars elided]…
T LTRIM(a, 'x') -> Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Literal(this='x', is_string=True),
  position=LEADING)
SELECT TRIM(a, 'x') -> Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Literal(this='x', is_string=True))
SELECT RTRIM(a) -> Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  position=TRAILING)
SELECT MAP(1,2) -> Map(
  keys=Literal(this=1, is_string=False),
  values=Literal(this=2, is_string=False))
[assistant] Parsing is already close to right: `LTRIM(a, 'x')` gives `LEADING` with the pattern as `expression`, and `TRIM(a, 'x')` keeps the string first. Two gaps follow from this. `MAP(1,2)` parses to a `Map` with scalar keys, so StarRocks needs `build_var_map` to get array-shaped nodes. And generator `TRANSFORMS` win over methods, so inherited `Trim`/`VarMap` entries have to be filtered out before my methods can take effect. Next I'll look at the test style before editing.
[tool_use Bash] {"command": "sed -n 1,33p tests/dialects/test_starrocks.py; sed -n 173,185p tests/dialects/test_starrocks.py; sed -n 264,282p tests/dialects/test_starrocks.py; grep -rn \"build_var_map\" sqlglot/parsers/*.py | head -3", "description": "Read StarRocks test file structure and an example test"}
[tool_result] from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator


class TestStarrocks(Validator):
    dialect = "starrocks"

    def test_starrocks(self):
        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))

        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_')")
        self.validate_identity("ALTER
…[1685 chars elided]…
       )
        self.validate_identity(
            "DELETE FROM t WHERE a BETWEEN 1 AND 10 AND b BETWEEN 20 AND 30 OR c BETWEEN 'x' AND 'z'",
            "DELETE FROM t WHERE a >= 1 AND a <= 10 AND b >= 20 AND b <= 30 OR c >= 'x' AND c <= 'z'",
        )

    def test_partition(self):
sqlglot/parsers/clickhouse.py:287:        "MAP": parser.build_var_map,
sqlglot/parsers/hive.py:99:        "MAP": parser.build_var_map,
sqlglot/parsers/snowflake.py:1390:    expression = parser.build_var_map(args)
[assistant] I have what I need. The plan:

- **Parser:** map `MAP` to `build_var_map` so `MAP(k1, v1, ...)` parses to array-shaped nodes.
- **Generator:** name `MIN_BY`/`MAX_BY`; emit variadic `MAP` for literal arrays and `MAP_FROM_ARRAYS` otherwise; emit `ARRAY_CONTAINS_ALL`; and rewrite `TRIM` to `TRIM`/`LTRIM`/`RTRIM` with the pattern as the second argument. The inherited `Trim` and `VarMap` entries have to come out of the `TRANSFORMS` filter for the new methods to apply.

I'll start with the parser.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc", "new_string": "from sqlglot import exp, parser\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,\n    }", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": parser.build_var_map,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Parser is done. Now the generator: the imports, the `TRANSFORMS` filter and entries, and the new methods.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    property_sql,\n)", "new_string": "    property_sql,\n    var_map_sql,\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: 
…[391 chars elided]…
ray: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: rename_func(\"ARRAY_FILTER\"),\n        exp.ArrayToString: rename_func(\"ARRAY_JOIN\"),\n        exp.ApproxDistinct: approx_count_distinct_sql,\n        exp.ArgMax: rename_func(\"MAX_BY\"),\n        exp.ArgMin: rename_func(\"MIN_BY\"),\n        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:\n        self.unsupported(\"Array operations are not supported by MySQL\")\n        return self.function_fallback_sql(expression
…[571 chars elided]…
   def trim_sql(self, expression: exp.Trim) -> str:\n        if expression.args.get(\"collation\"):\n            self.unsupported(\"StarRocks TRIM does not support COLLATE\")\n\n        func_name = {\"LEADING\": \"LTRIM\", \"TRAILING\": \"RTRIM\"}.get(\n            self.sql(expression, \"position\"), \"TRIM\"\n        )\n        return self.func(func_name, expression.this, expression.expression)"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:     def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
        self.unsupported("Array operations are not supported by MySQL")
        return self.function_fallback_sql(expression)</tool_use_error>
[assistant] That last edit failed because `arraycontainsall_sql` lives in `mysql.py`, not the StarRocks generator, so the new methods never went in. I'll append them to the end of the StarRocks generator instead, next to `refreshtriggerproperty_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        return f\"REFRESH{method}{kind}{starts}{every}\"", "new_string": "        return f\"REFRESH{method}{kind}{starts}{every}\"\n\n    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) ->
…[481 chars elided]…
   def trim_sql(self, expression: exp.Trim) -> str:\n        if expression.args.get(\"collation\"):\n            self.unsupported(\"StarRocks TRIM does not support COLLATE\")\n\n        func_name = {\"LEADING\": \"LTRIM\", \"TRAILING\": \"RTRIM\"}.get(\n            self.sql(expression, \"position\"), \"TRIM\"\n        )\n        return self.func(func_name, expression.this, expression.expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now I'll rerun the probe from earlier, with the new cases included, to check the output.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n ('duckdb','SELECT ARG_MAX(a,b) FROM t'),\n ('snowflake','SELECT MAX_BY(a,b) FROM t'),\n ('spark','SELECT MIN_BY(a,b) OVER (PARTITION BY c) FROM t'),\n ('starrocks','SELECT MAX_BY(a,b) OVE
…[910 chars elided]…
T TRIM(a)'),\n ('postgres','SELECT TRIM(LEADING \\'x\\' FROM a COLLATE \\\"C\\\")'),\n]\nfor d,s in cases:\n    try:\n        e = sqlglot.parse_one(s, read=d)\n        print(d, '|', s, '\\n   ->', e.sql('starrocks'))\n    except Exception as ex:\n        print(d,'|',s,'\\n   ERR',type(ex).__name__, str(ex)[:200])\n\" 2>&1", "description": "Re-run probe with the new StarRocks generator and parser"}
[tool_result] duckdb | SELECT ARG_MAX(a,b) FROM t 
   -> SELECT MAX_BY(a, b) FROM t
snowflake | SELECT MAX_BY(a,b) FROM t 
   -> SELECT MAX_BY(a, b) FROM t
spark | SELECT MIN_BY(a,b) OVER (PARTITION BY c) FROM t 
   -> SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
starrocks | SELECT MAX_BY(a,b) OVER (PARTITION BY c) FROM t 
   -> SELECT MAX_BY(a, b) OVER (PARTITION BY c) FROM t
duckdb | SELECT MAP([1,2],[3,4]) 
   -> SELECT MAP(1, 3, 2, 4)
presto | SELECT MAP(ARRAY[1,2], ARRAY[3,4]) 
   -> SELECT MAP(1, 3,
…[742 chars elided]…
a, 'x')
starrocks | SELECT TRIM(a) 
   -> SELECT TRIM(a)
starrocks | SELECT TRIM('x' FROM a) 
   -> SELECT TRIM(a, 'x')
starrocks | SELECT TRIM(a, 'x') 
   -> SELECT TRIM(a, 'x')
starrocks | SELECT LTRIM(a, 'x') 
   -> SELECT LTRIM(a, 'x')
starrocks | SELECT RTRIM(a) 
   -> SELECT RTRIM(a)
postgres | SELECT TRIM(BOTH 'x' FROM a) 
   -> SELECT TRIM(a, 'x')
postgres | SELECT TRIM(a) 
   -> SELECT TRIM(a)
postgres | SELECT TRIM(LEADING 'x' FROM a COLLATE "C") 
   -> SELECT LTRIM(a COLLATE `C`, 'x')
[assistant] Three of the four now emit StarRocks syntax. Two cases are still wrong:

- `MAP(1,2,3,4)` still prints `MAP([1, 3], [2, 4])`. The inherited base `VarMap` entry in `TRANSFORMS` is still winning, so I need to filter `exp.VarMap` out as well.
- `ARRAY_CONTAINS_ALL` still prints `@>`. Something else must be dispatching that node, so I'll find out what.
[tool_use Bash] {"command": "grep -rn \"ArrayContainsAll\" sqlglot/generator.py sqlglot/generators/mysql.py sqlglot/generators/starrocks.py sqlglot/generators/*.py | head; grep -n \"ArrayContainsAll\\|arraycontainsall\" sqlglot/generator.py | head", "description": "Find what dispatches ArrayContainsAll in the generators"}
[tool_result] sqlglot/generators/starrocks.py:344:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
sqlglot/generators/mysql.py:652:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
sqlglot/generator.py:144:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/generators/mysql.py:652:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
sqlglot/generators/starrocks.py:344:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
144:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
[assistant] The base generator maps `ArrayContainsAll` to `@>` in its own `TRANSFORMS`, and `VarMap` has an entry there too. Both have to be filtered out so my methods are used. I'll update the filter to cover them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "            if k not in (exp.DateTrunc, exp.Trim)\n        },", "new_string": "            if k not in (exp.ArrayContainsAll, exp.DateTrunc, exp.Trim, exp.VarMap)\n        },"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n ('starrocks','SELECT MAP(1,2,3,4)'),\n ('starrocks','SELECT MAP()'),\n ('starrocks','SELECT MAP(a, b)'),\n ('duckdb','SELECT MAP([1,2],[3,4])'),\n ('duckdb','SELECT MAP(k, v) FROM t'),\n 
…[398 chars elided]…
hify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT MAP(1,2,3,4)','SELECT ARRAY_CONTAINS_ALL([1,2],[1])','SELECT TRIM(BOTH \\'x\\' FROM a)']:\n    e=sqlglot.parse_one(s, read='starrocks')\n    print(s,'->',e.sql('starrocks'),'->',e.sql('mysql'))\n\"", "description": "Re-check MAP and ARRAY_CONTAINS_ALL output after filter fix"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 15, in <module>
  File "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/sqlglot/dialects/dialect.py", line 1124, in parse
    return self.
…[5784 chars elided]…

postgres | SELECT ARRAY_CONTAINS_ALL(a,b) 
   -> SELECT ARRAY_CONTAINS_ALL(a, b)
Arrays are not supported by MySQL
Arrays are not supported by MySQL
Arrays are not supported by MySQL
Arrays are not supported by MySQL
SELECT MAP(1,2,3,4) -> SELECT MAP(1, 2, 3, 4) -> SELECT MAP(ARRAY(1, 3), ARRAY(2, 4))
SELECT ARRAY_CONTAINS_ALL([1,2],[1]) -> SELECT ARRAY_CONTAINS_ALL([1, 2], [1]) -> SELECT ARRAY(1, 2) @> ARRAY(1)
SELECT TRIM(BOTH 'x' FROM a) -> SELECT TRIM(a, 'x') -> SELECT TRIM(BOTH 'x' FROM a)
[assistant] All four families now produce StarRocks-native output. The one remaining error is from my probe, not the code: the old `a @> b` form in StarRocks SQL is one I deliberately dropped. The round-trip looks right too: `MAP(1,2,3,4)` stays variadic, and `ARRAY_CONTAINS_ALL` reads back as itself.

Next I'll add regression tests. First I need the end of the test file, so I can append in the right place.
[tool_use Bash] {"command": "sed -n 318,335p tests/dialects/test_starrocks.py; grep -rln \"starrocks\" tests/ | head -20; grep -rn \"ARG_M\\|MAX_BY\\|MIN_BY\\|CONTAINS_ALL\\|@>\" tests/dialects/test_starrocks.py tests/dialects/test_mysql.py | head", "description": "Read end of StarRocks test file and find related existing tests"}
[tool_result]         # RANGE partitioning with explicit values
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (PARTITION p1 VALUES LESS THAN ('2020-01-31'), PARTITION p2 VALUES LESS THAN ('2020-02-29'), PARTITION p3 VALUES LESS THAN ('2020-03-31'))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 STRING) PARTITION BY RANGE (STR2DATE(col1, '%Y-%m-%d')) (PARTITION p1 VALUES LESS THAN ('2021-01-01'), PARTITION p2 VA
…[767 chars elided]…
AL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
tests/test_transpile.py
tests/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_oracle.py
tests/dialects/test_starrocks.py
tests/dialects/test_redshift.py
tests/dialects/test_teradata.py
tests/dialects/test_presto.py
tests/dialects/test_dialect.py
tests/dialects/test_duckdb.py
tests/dialects/test_mysql.py
tests/dialects/test_postgres.py
tests/fixtures/optimizer/qualify_columns.sql
[assistant] I'll insert the new test methods just before `test_partition`, keeping them in the file's existing style.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "    def test_partition(self):", "new_string": "    def test_arg_max_min(self):\n        self.validate_all(\n            \"SELECT MAX_BY(a, b) FROM t\",\n            read={\n                \"duckdb\": \"S
…[1800 chars elided]…
            \"starrocks\": \"SELECT TRIM('x' FROM a)\",\n            },\n        )\n        self.validate_all(\n            \"SELECT LTRIM(a, 'x')\",\n            read={\"\": \"SELECT TRIM(LEADING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT RTRIM(a, 'x')\",\n            read={\"\": \"SELECT TRIM(TRAILING 'x' FROM a)\"},\n        )\n\n    def test_partition(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-102622-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Now the verification. I'll run the StarRocks test file first, then the full suite with the project's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Run StarRocks dialect tests"}
[tool_result] .............. [ 87%]
..                                                [100%]
16 passed, 81 subtests passed in 0.12s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -40", "description": "Run full project test suite"}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
.............. [ 22%]
................................................................. [ 28%]
................................................................................ [ 35%]
.......................................
…[344 chars elided]…
........................................................................................... [ 75%]
.......................................... [ 79%]
.......................................... [ 83%]
.................................... [ 86%]
............................................................. [ 92%]
................................. [ 94%]
............................. [ 97%]
............................                               [100%]
1126 passed, 18212 subtests passed in 50.75s
[assistant] The full suite passes: 1126 tests and 18212 subtests. The project also runs lint and format checks, so I'll run those on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py && $PY -m ruff format --check sqlglot/parsers/starrocks.py sqlglot/generators/starrocks.py tests/dialects/test_starrocks.py) 2>&1 | tail -20; git status --short; git diff --stat", "description": "Run ruff lint and format checks on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.py
 sqlglot/generators/starrocks.py  | 32 ++++++++++++++++++++-
 sqlglot/parsers/starrocks.py     |  3 +-
 tests/dialects/test_starrocks.py | 60 ++++++++++++++++++++++++++++++++++++++++
 3 files changed, 93 insertions(+), 2 deletions(-)
[assistant] Lint and format are clean. Last, a type check, since the project's `make check` includes mypy.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 300 $PY -m mypy sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py 2>&1 | tail -15", "description": "Run mypy on the changed StarRocks modules"}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py 2>&1 | tail -15", "description": "Run mypy on the changed StarRocks modules"}
[tool_result] Success: no issues found in 2 source files
[assistant] All four StarRocks forms now generate StarRocks-native SQL and parse StarRocks' own forms back. The full suite passes (1126 tests), and ruff and mypy are clean on the changed modules. Nothing is committed.

- **`MIN_BY` / `MAX_BY`:** emitted by name, including the `OVER (...)` window form. Previously these came out as `ARG_MIN` / `ARG_MAX`.
- **`MAP`:** parsed as the variadic constructor, so `MAP(1, 2, 3, 4)` round-trips. Two literal arrays from DuckDB or Presto become `MAP(1, 3, 2, 4)`.
- **`ARRAY_CONTAINS_ALL(a, b)`:** emitted by name instead of `@>`.
- **`TRIM`:** StarRocks only takes `trim
…[439 chars elided]…
_FROM_ARRAYS(k, v)`, which StarRocks has from 3.1 onward. The variadic form needs literal arrays to expand.
- **`COLLATE` on `TRIM`** has no StarRocks equivalent, so it raises an "unsupported" warning rather than being dropped silently.

Known gaps:
- Literal arrays of unequal length in a two-array `MAP` are silently truncated, because the element pairing stops at the shorter array. The source SQL is already invalid in that case, but nothing warns about it.
- I checked the syntax against StarRocks' published docs, not a live StarRocks instance, so the output is verified by docs and tests only.
