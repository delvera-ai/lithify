# trajectory base-1

final message:
All four StarRocks gaps are fixed. The full suite passes (1123 tests, 18213 subtests), and ruff check and format are clean on the changed files. Nothing is committed.

**What changed**
- **`MIN_BY` / `MAX_BY`:** `ArgMin`/`ArgMax` now emit `MIN_BY`/`MAX_BY`, including the `OVER (...)` window form. A `count` argument is flagged as unsupported rather than silently dropped.
- **`MAP`:** Generated as `MAP(k1, v1, k2, v2, …)`. Two-array forms from DuckDB and Presto are unpacked when their arrays are literal, so `MAP([1,2],[3,4])` becomes `MAP(1, 3, 2, 4)`. StarRocks' `MAP(...)` and `MAP_FROM_ARRAYS(...)` parse back to the shared AST.
- **`ARRAY_CONTAINS_ALL`:** Emitted as the function call rather than `@>`.
- **`TRIM`:** The MySQL `BOTH`/`LEADING`/`TRAILING … FROM` form is dropped. Output is `TRIM(str, chars)`, `LTRIM(str, chars)` or `RTRIM(str, chars)`, and StarRocks' own `TRIM(a, 'x')` round-trips.

Changes are in `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py`, and a new `test_native_functions` in `tests/dialects/test_starrocks.py`.

**Choices I made**
- A two-array `MAP` whose arrays are columns can't be unpacked into the variadic form, so it emits `MAP_FROM_ARRAYS(keys, values)`. I used that StarRocks function because the docs list it (v3.0/3.1+).
- An odd-argument `MAP(1, 2, 3)` still raises `ParseError`. Routing `MAP` through the shared builder would have turned that into a raw `IndexError`, so I kept the old error path.

**Caveats**
- **TRIM semantics:** MySQL's `TRIM('ab' FROM s)` removes the substring `ab`. StarRocks' `trim(s, chars)` removes any of the characters `a` or `b` from the ends. The two agree only when the trim string is one character. I did not add a fallback for multi-character trim strings.
- **Window `MAX_BY`:** The StarRocks docs search didn't confirm window support for `max_by`. I implemented it as you specified, but I have not checked it against a live StarRocks. There's no StarRocks instance here, so every check is a string-level test, and nothing has been run against a real server.

## events
[assistant] I'll start by reading the StarRocks dialect and the MySQL/base code it inherits from.
[tool_use Bash] {"command": "cat sqlglot/dialects/starrocks.py && git log --oneline -3 -- sqlglot/dialects/starrocks.py && ls tests/dialects | grep -i star", "description": "Show StarRocks dialect source and test file"}
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
1b14a7971 refactor(mysql)!: Extract and compile generator (#7381)
ea035e157 refactor!: Rename Parser to <Dialect>Parser and auto-discover parsers in setup.py (#7252)
5c8b0037e refactor!: Extract StarRocks parser for mypyc compilation (#7248)
test_starrocks.py
[tool_use Bash] {"command": "cat tests/dialects/test_starrocks.py && grep -n \"ArgMax\\|ArgMin\\|MAX_BY\\|MIN_BY\\|ARRAY_CONTAINS_ALL\\|ArrayContainsAll\\|class Map(\\|class VarMap\\|class Trim\\|class ArrayContains\" sqlglot/expressions.py", "description": "Show StarRocks tests and relevant expression classes"}
[tool_result ERROR] Exit code 2
from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator


class TestStarrocks(Validator):
    dialect = "starrocks"

    def test_starrocks(self):
        self.assertEqual(self.validate_identity("arr[1]").expressions[0], exp.Literal.number(0))

        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_', 'NULL')")
        self.validate_identity("SELECT ARRAY_JOIN([1, 3, 5, NULL], '_')")
        self.validate_ide
…[9039 chars elided]…
ol1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
ugrep: warning: sqlglot/expressions.py: No such file or directory
[assistant] The dialect has been split into `sqlglot/parsers/` and `sqlglot/generators/`, so I'll locate the generic expression and MySQL code before changing anything.
[tool_use Bash] {"command": "ls sqlglot sqlglot/generators sqlglot/parsers | head -100; wc -l sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py sqlglot/generators/mysql.py sqlglot/dialects/mysql.py; cat sqlglot/generators/starrocks.py; cat sqlglot/parsers/starrocks.py", "description": "List package layout and StarRocks generator and parser"}
[tool_result] sqlglot:
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
postgre
…[17072 chars elided]…
parse_string)

        if self._match_text_seq("EVERY"):
            self._match_l_paren()
            self._match_text_seq("INTERVAL")
            every = self._parse_number()
            unit = self._parse_var(any_token=True)
            self._match_r_paren()
        else:
            every = None
            unit = None

        return self.expression(
            exp.RefreshTriggerProperty(
                method=method, kind=kind, starts=start, every=every, unit=unit
            )
        )
[assistant] Next I'll check what the StarRocks generator currently emits for each of the four cases, so I know the real gaps.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ntests = [\n ('starrocks','SELECT MIN_BY(a, b) FROM t'),\n ('starrocks','SELECT MAX_BY(a, b) FROM t'),\n ('duckdb','SELECT ARG_MIN(a, b) FROM t'),\n ('duckdb','SELECT ARG_MAX(a, b) FROM t'),\n ('spark','SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t'),\n ('starrocks','SELECT MIN_B
…[960 chars elided]…
s:\n    try:\n        ast = sqlglot.parse_one(s, read=d)\n        out = ast.sql('starrocks')\n        print(f'{d:9} | {s}\\n          -> {out}\\n          AST: {repr(ast)[:0]}{type(ast.selects[0]).__name__}')\n    except Exception as e:\n        print(f'{d:9} | {s}\\n          ERR {type(e).__name__}: {e}')\n\" 2>&1 | head -150", "description": "Probe current StarRocks output for target functions"}
[tool_result] starrocks | SELECT MIN_BY(a, b) FROM t
          -> SELECT ARG_MIN(a, b) FROM t
          AST: ArgMin
starrocks | SELECT MAX_BY(a, b) FROM t
          -> SELECT ARG_MAX(a, b) FROM t
          AST: ArgMax
duckdb    | SELECT ARG_MIN(a, b) FROM t
          -> SELECT ARG_MIN(a, b) FROM t
          AST: ArgMin
duckdb    | SELECT ARG_MAX(a, b) FROM t
          -> SELECT ARG_MAX(a, b) FROM t
          AST: ArgMax
spark     | SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
          -> SELECT ARG_MIN(a
…[1752 chars elided]…

          AST: Trim
starrocks | SELECT TRIM(TRAILING 'x' FROM a)
          -> SELECT TRIM(TRAILING 'x' FROM a)
          AST: Trim
starrocks | SELECT LTRIM(a), RTRIM(a)
          -> SELECT LTRIM(a), RTRIM(a)
          AST: Trim
starrocks | SELECT TRIM(FROM a)
          -> SELECT TRIM(a)
          AST: Trim
postgres  | SELECT TRIM(BOTH 'x' FROM a)
          -> SELECT TRIM(BOTH 'x' FROM a)
          AST: Trim
duckdb    | SELECT TRIM(a, 'x')
          -> SELECT TRIM('x' FROM a)
          AST: Trim
[assistant] The probe shows four concrete gaps: `ARG_MIN`/`ARG_MAX` are emitted for `MIN_BY`/`MAX_BY`, the two-array `MAP` is emitted as `MAP([..],[..])` and the variadic `MAP(1,2,3,4)` fails to parse, `@>` is emitted for `ArrayContainsAll`, and the MySQL-style `TRIM(BOTH ... FROM ...)` is emitted. Before changing anything I need to confirm StarRocks' exact TRIM and MAP syntax, and check how the existing tests cover these.
[tool_use Bash] {"command": "grep -rn \"ARG_M\\|MIN_BY\\|MAX_BY\\|ArgMax\\|ArgMin\" sqlglot/generators/ sqlglot/parsers/ sqlglot/dialects/ sqlglot/generator.py sqlglot/parser.py | head -40; echo ---; grep -rn \"def build_var_map\\|class VarMap\\|class Map(\\|def _build_map\\|\\\"MAP\\\":\" sqlglot/ | head; echo ---; grep -n \"ArrayContainsAll\\|class Trim\\|class ArgMax\\|class ArgMin\\|class Map\\|class VarMap\" -A6 sqlglot/expressions/*.py | head -120; echo ---; grep -rn \"starrocks\" tests/dialects/*.py | grep -i \"trim\\|map(\\|min_by\\|max_by\\|arg_m\\|contains_all\\|@>\" | head -30", "description": "Locate relevant generator, parser and expression definitions"}
[tool_result] sqlglot/generators/clickhouse.py:289:        exp.ArgMax: arg_max_or_min_no_count("argMax"),
sqlglot/generators/clickhouse.py:290:        exp.ArgMin: arg_max_or_min_no_count("argMin"),
sqlglot/generators/bigquery.py:281:        exp.ArgMax: arg_max_or_min_no_count("MAX_BY"),
sqlglot/generators/bigquery.py:282:        exp.ArgMin: arg_max_or_min_no_count("MIN_BY"),
sqlglot/generators/doris.py:51:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/doris.py:52:        exp.ArgMin: rename_func
…[6415 chars elided]…
self) -> list[Expr]:
sqlglot/expressions/array.py-345-        return self.args["keys"].expressions
sqlglot/expressions/string.py:241:class Trim(Expression, Func):
sqlglot/expressions/string.py-242-    arg_types = {
sqlglot/expressions/string.py-243-        "this": True,
sqlglot/expressions/string.py-244-        "expression": False,
sqlglot/expressions/string.py-245-        "position": False,
sqlglot/expressions/string.py-246-        "collation": False,
sqlglot/expressions/string.py-247-    }
---
[assistant] Key details: `ArgMax`/`ArgMin` carry an optional `count` argument, and `VarMap` already exists as the variadic form. Next I'll read the helpers that handle those, plus the MySQL and base TRIM and MAP code.
[tool_use Bash] {"command": "sed -n 1930,1950p sqlglot/dialects/dialect.py; echo ----PARSER_build_var_map; sed -n 40,75p sqlglot/parser.py; echo ----MAP_expr; sed -n 283,300p sqlglot/expressions/array.py; sed -n 339,360p sqlglot/expressions/array.py; echo ----TRIM_mysql; grep -n -i \"trim\" sqlglot/generators/mysql.py sqlglot/parsers/mysql.py sqlglot/generators/starrocks.py sqlglot/generators/doris.py sqlglot/parsers/doris.py sqlglot/generator.py sqlglot/parser.py | head -40; echo ----map_gen; grep -n \"def map_sql\\|def varmap_sql\\|exp.VarMap\\|exp.Map\\b\\|exp.Map:\" -A12 sqlglot/generator.py | head -60", "description": "Inspect helper, map and trim generation/parsing code"}
[tool_result]     start = self.sql(expression, "start") or "1"
    increment = self.sql(expression, "increment") or "1"
    return f"IDENTITY({start}, {increment})"


def arg_max_or_min_no_count(name: str) -> t.Callable[[Generator, exp.ArgMax | exp.ArgMin], str]:
    @unsupported_args("count")
    def _arg_max_or_min_sql(self: Generator, expression: exp.ArgMax | exp.ArgMin) -> str:
        return self.func(name, expression.this, expression.expression)

    return _arg_max_or_min_sql


def ts_or_ds_add_cast(ex
…[4948 chars elided]…
{self.expressions(e, flat=True)}",
291-        exp.WithSchemaBindingProperty: lambda self, e: f"WITH SCHEMA {self.sql(e, 'this')}",
292-        exp.WithOperator: lambda self, e: f"{self.sql(e, 'this')} WITH {self.sql(e, 'op')}",
293-        exp.ForceProperty: lambda *_: "FORCE",
294-    }
295-
296-    # Whether null ordering is supported in order by
297-    # True: Full Support, None: No support, False: No support for certain cases
298-    # such as window specifications, aggregate functions etc
[assistant] The code side is clear now. Before I write StarRocks-specific output, I need to confirm the exact native syntax for TRIM and MAP in the StarRocks docs.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT MAP(1, 2, 3, 4)', 'SELECT MAP()', 'SELECT ARRAY_CONTAINS_ALL(a, b)']:\n    try: print(sqlglot.parse_one(s, read='mysql').sql('mysql'))\n    except Exception as e: print('ERR', e)\n\" 2>&1 | head; grep -n \"def _parse_map\\|def build_map\" -A3 sqlglot/parser.py | head -20; grep -n \"def _parse_trim\" -A30 sqlglot/parser.py | head -40", "description": "Check MAP parser and TRIM parser code"}
[tool_result] ERR The number of provided arguments (4) is greater than the maximum number of supported arguments (2). Line 1, Col: 22.
  SELECT MAP(1, 2, 3, 4[4m)[0m
SELECT MAP()
SELECT a @> b
8265:    def _parse_trim(self) -> exp.Trim:
8266-        # https://www.w3resource.com/sql/character-functions/trim.php
8267-        # https://docs.oracle.com/javadb/10.8.3.0/ref/rreftrimfunc.html
8268-
8269-        position = None
8270-        collation = None
8271-        expression = None
8272-
8273-        if self.
…[524 chars elided]…
ion = self._parse_bitwise()
8286-
8287-        return self.expression(
8288-            exp.Trim(this=this, position=position, expression=expression, collation=collation)
8289-        )
8290-
8291-    def _parse_window_clause(self) -> list[exp.Expr] | None:
8292-        return self._parse_csv(self._parse_named_window) if self._match(TokenType.WINDOW) else None
8293-
8294-    def _parse_named_window(self) -> exp.Expr | None:
8295-        return self._parse_window(self._parse_id_var(), alias=True)
[tool_use Bash] {"command": "grep -n \"_parse_map\\b\\|def _parse_map\" sqlglot/parser.py sqlglot/parsers/*.py | head; grep -n '\"MAP\"' sqlglot/parsers/mysql.py sqlglot/parsers/doris.py sqlglot/parsers/singlestore.py sqlglot/parser.py; grep -n \"class Trim\\|trim_sql\" -A22 sqlglot/generator.py | sed -n 1,30p; grep -n \"def trim_sql\" -A25 sqlglot/dialects/dialect.py | head -5", "description": "Find MAP parser registration and TRIM generation helper"}
[tool_result] sqlglot/parsers/duckdb.py:201:        "MAP": lambda self: self._parse_map(),
sqlglot/parsers/duckdb.py:334:    def _parse_map(self) -> exp.ToMap | exp.Map:
sqlglot/parsers/materialize.py:15:        "MAP": lambda self: self._parse_map(),
sqlglot/parsers/materialize.py:28:    def _parse_map(self) -> exp.ToMap:
sqlglot/parser.py:3627:        if self._match_text_seq("MAP", "KEYS", "TERMINATED", "BY"):
sqlglot/parser.py:7663:            parse_map = map_token is not None and map_token.text.upper() == 
…[736 chars elided]…
args.get("safe"):
3631-            args = [exp.cast(e, exp.DType.TEXT) for e in args]
3632-
3633-        concat_coalesce = (
3634-            self.dialect.CONCAT_WS_COALESCE
3635-            if isinstance(expression, exp.ConcatWs)
1777:def trim_sql(self: Generator, expression: exp.Trim, default_trim_type: str = "") -> str:
1778-    remove_chars = self.sql(expression, "expression")
1779-
1780-    # Use TRIM/LTRIM/RTRIM syntax if the expression isn't database-specific
1781-    if not remove_chars:
[assistant] I've confirmed the code paths. Now the external facts: I'll check StarRocks' own docs for TRIM, MAP, MIN_BY/MAX_BY, and ARRAY_CONTAINS_ALL in parallel.
[tool_use Bash] {"command": "echo \"placeholder: searches are issued via WebSearch tool, not bash\"", "description": "No-op placeholder for search planning"}
[tool_result] placeholder: searches are issued via WebSearch tool, not bash
[tool_use WebSearch] {"query": "StarRocks trim function syntax ltrim rtrim docs", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks map() function variadic key value syntax map_from_arrays", "mode": "standard"}
[tool_use WebSearch] {"query": "StarRocks max_by min_by window function syntax docs", "mode": "standard"}
[tool_result] Web search results for query: "StarRocks trim function syntax ltrim rtrim docs"

Links: [{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.starrocks.io","url":"https://docs.starrocks.io/zh/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"docs.celerdata.com","url":"https:
…[2835 chars elided]…
("abcd", "ad")` returning `bc`, so `trim` removes the listed characters from both ends.

Only the English ltrim page's syntax section was cut off in the results, so I could not confirm its exact signature from the English source. The Japanese mirror is the only source I have for that line. I did not open the full pages, so check the official English docs for the complete parameter descriptions.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks map() function variadic key value syntax map_from_arrays"

Links: [{"title":"map from arrays","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.starrocks.io/ja/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title":"map from arrays","url":"https://docs.starrocks.io/zh/docs/sql-reference/sql-functions/map-functions/map_from_arrays/"},{"title"
…[2452 chars elided]…
le `map(a,1,b,2,c,3)`. The page also notes that StarRocks infers the key and value types from the inputs, and that Key 和 Value 取值都可以为 NULL (keys and values can both be NULL).

The results did not include the official map() function reference page itself, so the variadic details come from the MAP type documentation. For the exact current behavior, check the StarRocks map-functions docs directly.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks max_by min_by window function syntax docs"

Links: [{"title":"how to use window functions in starrocks","url":"https://gurubase.io/g/starrocks/how-to-use-window-functions-in-starrocks"},{"title":"Window function","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/Window_function/"},{"title":"Aggregate function calls","url":"https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/aggregate-function-calls"},{"title":"0% found this 
…[2397 chars elided]…
dow functions or what their exact signature is. The most useful next step is to check the StarRocks aggregate function index at docs.starrocks.io for `max_by`/`min_by`, or to test the query on a StarRocks instance.
- **Other results:** Databricks, Snowflake, and Doris pages document `max_by`/`min_by` with `OVER` support. These are not StarRocks docs, so they only indicate what other engines do.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] Search results confirm the native forms for TRIM (`trim(str[, chars])`, with `ltrim`/`rtrim` taking the same optional characters argument) and for the variadic `map(k, v, ...)`. They did not confirm `max_by` for StarRocks, so I'll treat the window form as the user specified. Next I'll check existing tests and any mapping that would conflict with the planned changes.
[tool_use Bash] {"command": "grep -rn \"MAP_FROM_ARRAYS\\|class MapFromArrays\" sqlglot/ | head -5; echo ---; grep -n \"exp.Map\\b\\|exp.Map:\\|exp.VarMap\\|exp.Trim\\|exp.ArrayContainsAll\\|exp.ArgMax\\|def map_sql\\|def trim_sql\" sqlglot/generator.py sqlglot/generators/mysql.py sqlglot/generators/doris.py sqlglot/generators/singlestore.py | head -20; echo ---; grep -rn -i \"trim(\\|MAP(\\|ARG_M\\|MIN_BY\\|MAX_BY\\|@>\\|CONTAINS_ALL\" tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_doris.py 2>/dev/null | head -40; echo ---; grep -rln \"starrocks\" tests/ | head -20", "description": "Check existing mappings and tests touching these functions"}
[tool_result] sqlglot/parsers/spark2.py:55:        "MAP_FROM_ARRAYS": exp.Map.from_arg_list,
sqlglot/generators/spark2.py:27:    return self.func("MAP_FROM_ARRAYS", keys, values)
---
sqlglot/generators/doris.py:51:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/doris.py:66:        exp.Map: rename_func("ARRAY_MAP"),
sqlglot/generators/mysql.py:221:        exp.Trim: trim_sql,
sqlglot/generators/mysql.py:652:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
sqlglot/genera
…[690 chars elided]…
test_mysql.py:311:        self.validate_identity("SELECT TRIM('bla' FROM ' XXX ')")
---
tests/test_transpile.py
tests/dialects/test_snowflake.py
tests/dialects/test_oracle.py
tests/dialects/test_starrocks.py
tests/dialects/test_teradata.py
tests/dialects/test_redshift.py
tests/dialects/test_bigquery.py
tests/dialects/test_duckdb.py
tests/dialects/test_mysql.py
tests/dialects/test_presto.py
tests/dialects/test_dialect.py
tests/dialects/test_postgres.py
tests/fixtures/optimizer/qualify_columns.sql
[assistant] `spark2` already maps `MAP_FROM_ARRAYS` to `exp.Map`, so I'll mirror that. Other dialect test files also contain StarRocks write expectations that my change could affect, so I'll look for them.
[tool_use Bash] {"command": "sed -n 15,35p sqlglot/generators/spark2.py; echo ---; grep -rn \"starrocks\" tests/dialects/test_dialect.py tests/dialects/test_duckdb.py tests/dialects/test_presto.py tests/dialects/test_snowflake.py tests/dialects/test_postgres.py tests/dialects/test_mysql.py tests/dialects/test_bigquery.py tests/dialects/test_oracle.py tests/dialects/test_teradata.py tests/dialects/test_redshift.py tests/test_transpile.py | grep -i \"trim\\|map\\|arg_\\|min_by\\|max_by\\|@>\\|contains\" ", "description": "Inspect spark2 map generator and cross-dialect starrocks expectations"}
[tool_result]     ctas_with_tmp_tables_to_create_tmp_view,
    move_schema_columns_to_partitioned_by,
)


def _map_sql(self: Spark2Generator, expression: exp.Map) -> str:
    keys = expression.args.get("keys")
    values = expression.args.get("values")

    if not keys or not values:
        return self.func("MAP")

    return self.func("MAP_FROM_ARRAYS", keys, values)


def _str_to_date(self: Spark2Generator, expression: exp.StrToDate) -> str:
    time_format = self.format_time(expression)
    if time_format == HIVE_DATE_FORMAT:
        return self.func("TO_DATE", expression.this)
    return self.func("TO_DATE", expression.this, time_format)

---
[assistant] No existing StarRocks test covers these outputs, so the change won't silently conflict with a passing expectation. I'll check how other parsers import `build_var_map` and what the MySQL parser's function table looks like, then make the edits.
[tool_use Bash] {"command": "grep -n \"build_var_map\\|^from sqlglot.parser\\|^from sqlglot import parser\" sqlglot/parsers/hive.py sqlglot/parsers/clickhouse.py | head; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py | head; grep -n \"FUNCTIONS\" -A4 sqlglot/parsers/mysql.py | head -12", "description": "Check build_var_map import style in parsers"}
[tool_result] sqlglot/parsers/hive.py:99:        "MAP": parser.build_var_map,
sqlglot/parsers/clickhouse.py:287:        "MAP": parser.build_var_map,
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
14:from sqlglot.helper import seq_get
15:from sqlglot.tokens import TokenType
55:    NO_PAREN_FUNCTIONS = {
56:        **parser.Parser.NO_PAREN_FUNCTIONS,
57-        TokenType.LOCALTIME: exp.Localtime,
58-        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
59-    }
60-
--
102:    FUNCTIONS = {
103:        **parser.Parser.FUNCTIONS,
104-        "BIT_AND": exp.BitwiseAndAgg.from_arg_list,
105-        "BIT_OR": exp.BitwiseOrAgg.from_arg_list,
106-        "BIT_XOR": exp.BitwiseXorAgg.from_arg_list,
[assistant] I have what I need. The plan, following the repo's rules (auto-discovered `*_sql` methods for single-entry cases, `TRANSFORMS` only where a function has several entry points):

- **Generator:** `ArgMax`/`ArgMin` → `MAX_BY`/`MIN_BY` (via the existing `arg_max_or_min_no_count` helper so `count` is flagged, not silently dropped); `ArrayContainsAll` → `ARRAY_CONTAINS_ALL`; `Map`/`VarMap` → one shared function that emits `MAP(k1, v1, …)` for literal arrays and `MAP_FROM_ARRAYS` otherwise; and drop the MySQL `exp.Trim` transform so the base `trim_sql` emits `TRIM(str, chars)` / `LTRIM` / `RTRIM`.
- **Parser:** `MAP` → `build_var_map` (variadic), and `MAP_FROM_ARRAYS` → `exp.Map`.

I'll start with the generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arg_max_or_min_no_count,\n    arrow_json_extract_sql,\n    rename_func,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "# https://docs.starrocks.io/docs/sql-reference/sql-functions/spatial-functions/st_distance_sphere/\ndef st_distance_sphere(", "new_string": "def _map_sql(self: StarRocksGenerator, expression: exp.Map | exp
…[456 chars elided]…
p.Array)\n        and len(keys.expressions) == len(values.expressions)\n    ):\n        pairs = [arg for kv in zip(keys.expressions, values.expressions) for arg in kv]\n        return self.func(\"MAP\", *pairs)\n\n    return self.func(\"MAP_FROM_ARRAYS\", keys, values)\n\n\n# https://docs.starrocks.io/docs/sql-reference/sql-functions/spatial-functions/st_distance_sphere/\ndef st_distance_sphere("}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: 
…[131 chars elided]…
ems()\n            if k not in (exp.DateTrunc, exp.Trim)\n        },\n        exp.ArgMax: arg_max_or_min_no_count(\"MAX_BY\"),\n        exp.ArgMin: arg_max_or_min_no_count(\"MIN_BY\"),\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayContainsAll: rename_func(\"ARRAY_CONTAINS_ALL\"),\n        exp.ArrayFilter: rename_func(\"ARRAY_FILTER\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),", "new_string": "        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Map: _map_sql,\n        exp.Property: property_sql,\n        exp.RegexpLike: rename_func(\"REGEXP\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n    }", "new_string": "        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n        exp.VarMap: _map_sql,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Now the parser side: variadic `MAP` and `MAP_FROM_ARRAYS` parse back to the shared AST.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc", "new_string": "from sqlglot import exp, parser\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": parser.build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Next I'll re-run the same probe to see the new output, plus the StarRocks round-trips and the edge cases (empty MAP, odd argument count, non-literal arrays).
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ntests = [\n ('starrocks','SELECT MIN_BY(a, b) FROM t'),\n ('starrocks','SELECT MAX_BY(a, b) FROM t'),\n ('duckdb','SELECT ARG_MIN(a, b) FROM t'),\n ('spark','SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t'),\n ('starrocks','SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t'),\n ('
…[1083 chars elided]…
t.transpile(s, read=d, write=\\\"starrocks\\\")[0]}')\n    except Exception as e:\n        print(f'{d:9} | {s}\\n          ERR {type(e).__name__}: {e}')\nprint('odd:')\ntry: print(sqlglot.transpile('SELECT MAP(1, 2, 3)', read='starrocks', write='starrocks'))\nexcept Exception as e: print('ERR', type(e).__name__, e)\n\" 2>&1", "description": "Re-run probe on updated StarRocks generator and parser"}
[tool_result] starrocks | SELECT MIN_BY(a, b) FROM t
          -> SELECT MIN_BY(a, b) FROM t
starrocks | SELECT MAX_BY(a, b) FROM t
          -> SELECT MAX_BY(a, b) FROM t
duckdb    | SELECT ARG_MIN(a, b) FROM t
          -> SELECT MIN_BY(a, b) FROM t
spark     | SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
          -> SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
starrocks | SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
          -> SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
starrocks | SELE
…[1183 chars elided]…
FROM a)
          -> SELECT RTRIM(a, 'x')
starrocks | SELECT TRIM(a)
          -> SELECT TRIM(a)
starrocks | SELECT TRIM(a, 'x')
          -> SELECT TRIM(a, 'x')
starrocks | SELECT TRIM('x' FROM a)
          -> SELECT TRIM(a, 'x')
starrocks | SELECT LTRIM(a, 'x'), RTRIM(a)
          -> SELECT LTRIM(a, 'x'), RTRIM(a)
duckdb    | SELECT TRIM(a, 'x')
          -> SELECT TRIM(a, 'x')
mysql     | SELECT TRIM(BOTH 'x' FROM a)
          -> SELECT TRIM(a, 'x')
odd:
ERR IndexError list index out of range
[assistant] Nearly all the forms now come out StarRocks-native, and StarRocks' own forms round-trip. One regression to handle: `MAP(1, 2, 3)` now raises a raw `IndexError` from the shared `build_var_map`, where it previously raised a `ParseError`. I'll check how the parser handles builder errors before deciding on a fix.
[tool_use Bash] {"command": "grep -n \"def _parse_function_call\" -A60 sqlglot/parser.py | grep -n \"function(\\|except\\|validate\\|raise\" | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d in ['starrocks','hive','duckdb']:\n  for s in ['SELECT MAP(1, 2, 3)','SELECT MAP(1, 2, 3, 4)']:\n    try: print(d, s, '->', sqlglot.transpile(s, read=d, write='starrocks'))\n    except Exception as e: print(d, s, 'ERR', type(e).__name__, str(e)[:80])\n\"", "description": "Check parser error handling for odd-arity MAP calls"}
[tool_result] starrocks SELECT MAP(1, 2, 3) ERR IndexError list index out of range
starrocks SELECT MAP(1, 2, 3, 4) -> ['SELECT MAP(1, 2, 3, 4)']
hive SELECT MAP(1, 2, 3) ERR IndexError list index out of range
hive SELECT MAP(1, 2, 3, 4) -> ['SELECT MAP(1, 2, 3, 4)']
duckdb SELECT MAP(1, 2, 3) -> ['SELECT MAP_FROM_ARRAYS(1, 2)']
duckdb SELECT MAP(1, 2, 3, 4) -> ['SELECT MAP_FROM_ARRAYS(1, 2)']
[assistant] Hive already has this `IndexError` on odd arity, so it's a shared pre-existing gap. But StarRocks is the one dialect where I've routed `MAP` through it, so my change is what turned a `ParseError` into an `IndexError` there. I'll keep StarRocks' error behavior by sending odd arity through the old generic path, which validates the argument count.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"MAP\": parser.build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,", "new_string": "        \"MAP\": lambda args: _build_map(args),\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot.tokens import TokenType\n\n\nclass StarRocksParser(MySQLParser):", "new_string": "from sqlglot.tokens import TokenType\n\n\ndef _build_map(args: list[exp.Expr]) -> exp.Expr:\n    # MAP takes alternating keys and values, so an odd argument count is left to the generic\n    # Map builder, which rejects it, rather than failing on a missing value\n    if len(args) % 2:\n        return exp.Map.from_arg_list(args)\n    return parser.build_var_map(args)\n\n\nclass StarRocksParser(MySQLParser):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] The lambda wrapper isn't needed; a plain function reference is clearer. I'll fix that and check the `BuilderArgs` type so the helper's annotation matches the builder it wraps.
[tool_use Bash] {"command": "sed -i 's/\"MAP\": lambda args: _build_map(args),/\"MAP\": _build_map,/' sqlglot/parsers/starrocks.py && grep -n '\"MAP\"' sqlglot/parsers/starrocks.py; grep -rn \"^BuilderArgs\\|BuilderArgs =\" sqlglot/*.py sqlglot/*/*.py | head -3; grep -n \"^from\\|^import\" sqlglot/parsers/hive.py | head", "description": "Simplify MAP builder registration and find BuilderArgs type"}
[tool_result] sed: 1: "sqlglot/parsers/starroc ...": unterminated substitute pattern
sqlglot/_typing.py:20:BuilderArgs = Sequence[t.Any]
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import build_formatted_time, build_regexp_extract
7:from sqlglot.helper import seq_get
8:from sqlglot.tokens import TokenType
[assistant] The `sed` failed on the quoting, so I'll make that edit with the editor instead. `BuilderArgs` lives in `sqlglot/_typing.py`, which I'll use for the annotation.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"MAP\": lambda args: _build_map(args),", "new_string": "        \"MAP\": _build_map,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Bash] {"command": "grep -rn \"BuilderArgs\" sqlglot/parsers/*.py | head -3", "description": "Check how parsers import BuilderArgs"}
[tool_result] (Bash completed with no output)
[assistant] Parsers don't use `BuilderArgs`, so the `list[exp.Expr]` annotation matches the local style. Next I'll add StarRocks tests covering both directions: StarRocks-native output from other dialects, and round-trip of StarRocks' own forms. First I'll confirm which error the odd-arity case raises so the test asserts the right class.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT MAP(1, 2, 3)', 'SELECT MAP(1, 2, 3, 4, 5)']:\n  try: print(sqlglot.parse_one(s, read='starrocks').sql('starrocks'))\n  except Exception as e: print(type(e).__mro__[:2], str(e).splitlines()[0])\n\"", "description": "Confirm error class for odd-arity MAP parse"}
[tool_result] (<class 'sqlglot.errors.ParseError'>, <class 'sqlglot.errors.SqlglotError'>) The number of provided arguments (3) is greater than the maximum number of supported arguments (2). Line 1, Col: 19.
(<class 'sqlglot.errors.ParseError'>, <class 'sqlglot.errors.SqlglotError'>) The number of provided arguments (5) is greater than the maximum number of supported arguments (2). Line 1, Col: 25.
[assistant] It raises `ParseError`, the same as before my change. Now I'll add the tests, placed after the main `test_starrocks` method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\"SELECT t1.id FROM t1 LEFT SEMI JOIN t2 ON t1.id = t2.id\")\n\n    def test_distinct_on(self):", "new_string": "        self.validate_identity(\"SELECT t1.id FROM t1 LEFT S
…[2175 chars elided]…
M(BOTH 'x' FROM a)\", \"duckdb\": \"SELECT TRIM(a, 'x')\"},\n        )\n        self.validate_all(\n            \"SELECT LTRIM(a, 'x')\",\n            read={\"mysql\": \"SELECT TRIM(LEADING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT RTRIM(a, 'x')\",\n            read={\"mysql\": \"SELECT TRIM(TRAILING 'x' FROM a)\"},\n        )\n\n    def test_distinct_on(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "sed -n 1,5p tests/dialects/test_starrocks.py", "description": "Check test file imports before adding ParseError"}
[tool_result] from sqlglot import exp
from sqlglot.errors import UnsupportedError
from tests.dialects.test_dialect import Validator
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.errors import UnsupportedError\nfrom tests.dialects.test_dialect import Validator", "new_string": "from sqlglot import exp, parse_one\nfrom sqlglot.errors import ParseError, UnsupportedError\nfrom tests.dialects.test_dialect import Validator"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-083736-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Run StarRocks dialect tests"}
[tool_result] .............                                                  [100%]
13 passed, 82 subtests passed in 0.14s
[assistant] The StarRocks tests pass. The project's check command is the full pytest run, so I'll run that next to catch any cross-dialect expectations I didn't touch directly.
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
…[329 chars elided]…
......................................................................................................... [ 76%]
.......................................... [ 79%]
.............................................................................. [ 86%]
............................................................. [ 92%]
........................................................................................                                 [100%]
1123 passed, 18213 subtests passed in 60.44s (0:01:00)
[assistant] The full suite passes: 1123 tests, 18213 subtests. Last is the style gate, so I'll run ruff on the changed files only, without modifying anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; F=\"sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py\"; $PY -m ruff --version && $PY -m ruff check $F; $PY -m ruff format --check $F; git status --short", "description": "Lint and format-check changed files"}
[tool_result] ruff 0.15.6
E902 No such file or directory (os error 2)
--> sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py:1:1

Found 1 error.
error: Failed to format sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py: No such file or directory (os error 2)
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.py
[assistant] The shell didn't word-split the unquoted variable, so ruff received the three paths as one argument. I'll re-run with the paths passed separately.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py && $PY -m ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py", "description": "Run ruff check and format check on changed files"}
[tool_result ERROR] Exit code 1
All checks passed!
Would reformat: sqlglot/generators/starrocks.py
1 file would be reformatted, 2 files already formatted
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff sqlglot/generators/starrocks.py 2>&1 | head -30", "description": "Show the formatting diff for generator file"}
[tool_result] --- sqlglot/generators/starrocks.py
+++ sqlglot/generators/starrocks.py
@@ -108,9 +108,7 @@
 
     TRANSFORMS = {
         **{
-            k: v
-            for k, v in MySQLGenerator.TRANSFORMS.items()
-            if k not in (exp.DateTrunc, exp.Trim)
+            k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k not in (exp.DateTrunc, exp.Trim)
         },
         exp.ArgMax: arg_max_or_min_no_count("MAX_BY"),
         exp.ArgMin: arg_max_or_min_no_count("MIN_BY"),

1 file would be reformatted
[assistant] The only formatting issue is in my comprehension edit, and the diff touches nothing else, so I'll apply the formatter to that file and re-check everything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/generators/starrocks.py && $PY -m ruff check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py && $PY -m ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py tests/dialects/test_mysql.py tests/dialects/test_doris.py 2>&1 | tail -3; git diff --stat", "description": "Apply formatting, re-lint and run related dialect tests"}
[tool_result] 1 file reformatted
All checks passed!
3 files already formatted
............................................................................                                [100%]
76 passed, 613 subtests passed in 0.23s
 sqlglot/generators/starrocks.py  | 30 ++++++++++++++++++-
 sqlglot/parsers/starrocks.py     | 12 +++++++-
 tests/dialects/test_starrocks.py | 64 ++++++++++++++++++++++++++++++++++++++--
 3 files changed, 102 insertions(+), 4 deletions(-)
[This command modified 1 file you've previously read: sqlglot/generators/starrocks.py. Call Read before editing.]
[assistant] That notice is just my own `ruff format` run rewriting the file. I'll review the final diff of the source files and re-run the full suite once more after the formatting change.
[tool_use Bash] {"command": "git diff -- sqlglot/ && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Review source diff and run full suite again"}
[tool_result] diff --git a/sqlglot/generators/starrocks.py b/sqlglot/generators/starrocks.py
index e71176c1f..0b2c0ef29 100644
--- a/sqlglot/generators/starrocks.py
+++ b/sqlglot/generators/starrocks.py
@@ -4,6 +4,7 @@ from __future__ import annotations
 from sqlglot import exp, transforms
 from sqlglot.dialects.dialect import (
     approx_count_distinct_sql,
+    arg_max_or_min_no_count,
     arrow_json_extract_sql,
     rename_func,
     unit_to_str,
@@ -38,6 +39,26 @@ def _eliminate_between_in_delete(expr
…[3664 chars elided]…
@@ class StarRocksParser(MySQLParser):
             this=seq_get(args, 1), expression=seq_get(args, 2), unit=seq_get(args, 0)
         ),
         "ARRAY_FLATTEN": exp.Flatten.from_arg_list,
+        "MAP": _build_map,
+        "MAP_FROM_ARRAYS": exp.Map.from_arg_list,
         "REGEXP": exp.RegexpLike.from_arg_list,
     }
 
........................................................................................                                 [100%]
1123 passed, 18213 subtests passed in 52.79s
[assistant] All four StarRocks gaps are fixed. The full suite passes (1123 tests, 18213 subtests), and ruff check and format are clean on the changed files. Nothing is committed.

**What changed**
- **`MIN_BY` / `MAX_BY`:** `ArgMin`/`ArgMax` now emit `MIN_BY`/`MAX_BY`, including the `OVER (...)` window form. A `count` argument is flagged as unsupported rather than silently dropped.
- **`MAP`:** Generated as `MAP(k1, v1, k2, v2, …)`. Two-array forms from DuckDB and Presto are unpacked when their arrays are literal, so `MAP([1,2],[3,4])` becomes `MAP(1, 3, 2, 4)`. StarRocks' `MAP(...)` and `MAP_FROM_ARRAYS(
…[858 chars elided]…
path.

**Caveats**
- **TRIM semantics:** MySQL's `TRIM('ab' FROM s)` removes the substring `ab`. StarRocks' `trim(s, chars)` removes any of the characters `a` or `b` from the ends. The two agree only when the trim string is one character. I did not add a fallback for multi-character trim strings.
- **Window `MAX_BY`:** The StarRocks docs search didn't confirm window support for `max_by`. I implemented it as you specified, but I have not checked it against a live StarRocks. There's no StarRocks instance here, so every check is a string-level test, and nothing has been run against a real server.
