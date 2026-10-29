# trajectory base-1

final message:
DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake's `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full suite passes (1084 tests) and ruff check and format are clean on the changed files.

**Cause:** `JSON_ARRAY` isn't in the parser's function registry. `exp.JSONArray` has no `_sql_names`, so its auto-derived name is `J_S_O_N_ARRAY`. DuckDB parsed the call as an opaque `Anonymous` function and passed it through unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: maps `JSON_ARRAY` to `exp.JSONArray(expressions=args)`, the same pattern SingleStore uses for `JSON_BUILD_ARRAY`.
- `sqlglot/generators/snowflake.py`: adds a `jsonarray_sql` method that emits `ARRAY_CONSTRUCT`. It uses `@unsupported_args` for `null_handling`, `return_type` and `strict`, which Snowflake can't express, so those emit a warning rather than being dropped silently.
- `tests/dialects/test_duckdb.py`: a `validate_all` case covering the DuckDB round-trip and the Snowflake output.

**Side effects:** any dialect that parses into `exp.JSONArray` now gets `ARRAY_CONSTRUCT` when writing Snowflake. BigQuery's `JSON_ARRAY` is the main case, so BigQuery → Snowflake also changes. No existing test broke, and I didn't add a test for it.

I haven't committed anything. Let me know if you want a commit, and with what message.

## events
[tool_use Bash] {"command": "grep -rn -i \"JSONArray\\|JSON_ARRAY\\b\" sqlglot/dialects/duckdb.py sqlglot/dialects/snowflake.py sqlglot/expressions.py sqlglot/dialects/dialect.py | head -50; grep -rn -i \"json_array\" tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py | head", "description": "Search JSON_ARRAY references in dialects and expressions"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn -i \"JSON_ARRAY\\b\\|JSONArray\\b\" sqlglot/ | head -40; echo ---; grep -rn -i \"json_array\" tests/ | head -30", "description": "Search JSON_ARRAY references across sqlglot and tests"}
[tool_result] sqlglot/parsers/singlestore.py:107:        "JSON_BUILD_ARRAY": lambda args: exp.JSONArray(expressions=args),
sqlglot/parsers/bigquery.py:279:        "JSON_ARRAY": lambda self: self.expression(
sqlglot/parsers/bigquery.py:280:            exp.JSONArray(expressions=self._parse_csv(self._parse_bitwise))
sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:112:    def _parse_oracle_json_array(self) -> exp.JSONArray:
sqlglot/parsers
…[3834 chars elided]…
py:4853:                "": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4854:                "bigquery": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4857:                "bigquery": """JSON_ARRAY_INSERT(PARSE_JSON('["a", ["b", "c"], "d"]'), '$[1]', 1)""",
tests/dialects/test_dialect.py:4858:                "mysql": """JSON_ARRAY_INSERT('["a", ["b", "c"], "d"]', '$[1]', 1)""",
[tool_use Bash] {"command": "ls sqlglot/generators | head -50; grep -rn \"ARRAY_CONSTRUCT\\|ArrayConstruct\\|class Array\\b\" sqlglot/generators/snowflake.py sqlglot/parsers/snowflake.py sqlglot/generators/duckdb.py | head; grep -n \"class JSONArray\" -A 12 sqlglot/expressions/json.py; sed -n 3560,3580p sqlglot/generator.py; grep -n \"ArrayConstruct\\|class Array(\" sqlglot/expressions/*.py | head", "description": "Inspect generator layout and array-related code"}
[tool_result] __init__.py  0B
athena.py  5.8K
bigquery.py  24.3K
clickhouse.py  26.6K
databricks.py  3.8K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  172.4K
dune.py  323B
exasol.py  28.0K
fabric.py  6.5K
hive.py  21.0K
materialize.py  2.0K
mysql.py  25.3K
oracle.py  6.3K
postgres.py  21.5K
presto.py  25.1K
prql.py  192B
redshift.py  10.1K
risingwave.py  1.1K
singlestore.py  42.1K
snowflake.py  46.1K
solr.py  192B
spark.py  7.7K
spark2.py  9.6K
sqlite.py  11.9K
starrocks.py  9.6K
t
…[2066 chars elided]…
{strict})"
        )

    def jsonarrayagg_sql(self, expression: exp.JSONArrayAgg) -> str:
        this = self.sql(expression, "this")
        order = self.sql(expression, "order")
        null_handling = expression.args.get("null_handling")
        null_handling = f" {null_handling}" if null_handling else ""
        return_type = self.sql(expression, "return_type")
rg: regex parse error:
    (?:ArrayConstruct|class Array()
    ^
error: unclosed group
0 matches for 'ArrayConstruct\|class Array('
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb')\nprint(repr(e.selects[0]))\nprint(e.sql('snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", read='duckdb', write='snowflake'))\nprint(sqlglot.transpile(\\\"S
…[99 chars elided]…
ARRAY_CONSTRUCT('a', 'b')\\\", read='snowflake', write='snowflake'))\nprint(sqlglot.transpile(\\\"SELECT JSON_ARRAY(1, 2)\\\", read='snowflake', write='duckdb'))\n\"; grep -n \"exp.Array:\\|def array_sql\\|ARRAY_CONSTRUCT\" sqlglot/generators/snowflake.py | head; grep -n \"exp.Array:\" -A3 sqlglot/generators/duckdb.py | head", "description": "Check current DuckDB\u2192Snowflake JSON_ARRAY output"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this='a', is_string=True),
    Literal(this='b', is_string=True),
    Literal(this='c', is_string=True)])
SELECT JSON_ARRAY('a', 'b', 'c')
["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT JSON_ARRAY(1, NULL)']
["SELECT ['a', 'b']"]
['SELECT JSON_ARRAY(1, 2)']
2 matches in 2 files:

1051:0:exp.Array) -> str:
413:0:transforms.preprocess([transforms.inherit_struct_field_names]),
1498:        exp.Array: transforms.preprocess(
1499-            [transforms.inherit_struct_field_names],
1500-            generator=inline_array_unless_query,
1501-        ),
[tool_use Bash] {"command": "sed -n 1040,1065p sqlglot/generators/snowflake.py; grep -n \"ARRAY_CONSTRUCT\\|JSONArray\\|unsupported_args\" sqlglot/generators/snowflake.py | head; grep -n \"JSON_ARRAY\\|JSONArray\" -B2 -A8 sqlglot/generators/singlestore.py | sed -n 1,30p; grep -n \"JSON_ARRAY\\|\\\"JSON_\" sqlglot/parsers/duckdb.py | head", "description": "Inspect Snowflake array generation and DuckDB JSON parsing"}
[tool_result]         expr_sql = super().arrayagg_sql(expression)

        if order:
            expr_sql = self.sql(exp.WithinGroup(this=expr_sql, expression=order))

        return expr_sql

    def arraytostring_sql(self, expression: exp.ArrayToString) -> str:
        return self.func("ARRAY_TO_STRING", expression.this, expression.expression)

    def array_sql(self, expression: exp.Array) -> str:
        expressions = expression.expressions

        first_expr = seq_get(expressions, 0)
        if isinstan
…[1918 chars elided]…
on_type:
1458-            return self.func(
1459:                f"JSON_ARRAY_CONTAINS_{json_type}", expression.expression, expression.this
1460-            )
1461-
1462-        return self.func(
1463:            "JSON_ARRAY_CONTAINS_JSON",
1464-            expression.expression,
1465-            self.func("TO_JSON", expression.this),
1466-        )
2 matches in 2 files:

133:0:parser.build_extract_json_with_path(exp.JSONExtract),
134:0:parser.build_extract_json_with_path(exp.JSONExtractScalar),
[tool_use Bash] {"command": "sed -n 1065,1080p sqlglot/generators/snowflake.py; grep -n \"ARRAY_CONSTRUCT\\|JSON_ARRAY\" tests/dialects/test_snowflake.py | head -5; grep -n \"def func\\b\" -A3 sqlglot/generator.py | head -5", "description": "Read rest of Snowflake array_sql and related tests"}
[tool_result]                 array_agg = exp.ArrayAgg(this=build_object_construct(args=object_construct_args))

                first_expr.set("kind", None)
                first_expr.set("expressions", [array_agg])

                return self.sql(first_expr.subquery())

        return inline_array_sql(self, expression)

    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
        zone = self.sql(expression, "this")
        if not zone:
            return super().currentdate_sql(expression)

        expr = exp.Cast(
6 matches in 3 files:

1237:0:"ARRAY_CONSTRUCT_COMPACT(1, NULL, 2)",
2169:0::VARIANT[0]""",
tests/dialects/test_snowflake.py:115:"SELECT BITMAP_COUNT(BITMAP_CONSTRUCT_AGG(value)) FROM TABLE(FLATTEN(INPUT =>...
4320:    def func(
4321-        self,
4322-        name: str,
4323-        *args: t.Any,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one(\\\"JSON_ARRAY(1)\\\")))\nprint(repr(sqlglot.parse_one(\\\"JSON_ARRAY(1)\\\", read='duckdb')))\nprint(repr(sqlglot.parse_one(\\\"JSON_ARRAY(1)\\\", read='bigquery')))\n\"; grep -n \"JSON\\|FUNCTIONS = {\" sqlglot/parsers/duckdb.py | head -20; sed -n 920,930p sqlglot/generators/snowflake.py; grep -n \"_sql_names\\|def sql_names\" -A6 sqlglot/expressions/core.py | head -40", "description": "Test JSON_ARRAY parsing across dialects"}
[tool_result] Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False)])
Anonymous(
  this=JSON_ARRAY,
  expressions=[
    Literal(this=1, is_string=False)])
JSONArray(
  expressions=[
    Literal(this=1, is_string=False)])
rg: regex parse error:
    (?:JSON|FUNCTIONS = {)
                         ^
error: repetition quantifier expects a valid decimal
0 matches for 'JSON\|FUNCTIONS = {'
            else:
                keys.append(exp.Literal.string(f"_{i}"))
                values.
…[1497 chars elided]…
      return cls._sql_names
1656-
1657-    @classmethod
1658-    def sql_name(cls) -> str:
1659-        sql_names = cls.sql_names()
1660-        assert sql_names, f"Expected non-empty 'sql_names' for Func: {cls.__name__}."
1661-        return sql_names[0]
--
1977:    _sql_names = ["APPROX_DISTINCT", "APPROX_COUNT_DISTINCT"]
1978-
1979-
1980-class Slice(Expression):
1981-    arg_types = {"this": False, "expression": False, "step": False}
1982-
1983-
--
2277:    _sql_names = ["POWER", "POW"]
2278-
[tool_use Bash] {"command": "grep -rnF \"JSON\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py 2>/dev/null | head -20; grep -rnF \"JSON_ARRAY\" sqlglot/ | head; grep -rnF \"JSONArray\" sqlglot/parsers/duckdb.py sqlglot/parser.py | head; grep -rnF \"class DuckDB\" -l sqlglot | head -3", "description": "Locate DuckDB parser JSON handling"}
[tool_result] sqlglot/parsers/duckdb.py:132:        "JSON": exp.ParseJSON.from_arg_list,
sqlglot/parsers/duckdb.py:133:        "JSON_EXTRACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
sqlglot/parsers/duckdb.py:134:        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
sqlglot/dialects/duckdb.py:24:    STRICT_JSON_PATH_SYNTAX = False
sqlglot/dialects/duckdb.py:56:            # DuckDB also supports the JSON pointer syntax, where every path starts with a `/`.
…[657 chars elided]…
mbda self: self.expression(
sqlglot/parsers/oracle.py:56:        "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
sqlglot/parsers/oracle.py:57:        "JSON_ARRAYAGG": lambda self: self._parse_oracle_json_arrayagg(),
Binary file sqlglot/__pycache__/generator.cpython-312.pyc matches
sqlglot/generator.py:3572:            "JSON_ARRAY", *expression.expressions, suffix=f"{null_handling}{return_type}{strict})"
sqlglot/parsers/duckdb.py
sqlglot/dialects/duckdb.py
sqlglot/generators/duckdb.py
[tool_use Bash] {"command": "grep -n \"FUNCTIONS\" sqlglot/parsers/duckdb.py | head; grep -n \"FUNCTIONS = \\|FUNCTIONS:\" sqlglot/parser.py | head; grep -rn \"ALL_FUNCTIONS\\b\" sqlglot/parser.py | head -5; grep -n \"class ParserMeta\\|def __new__\\|FUNCTIONS\" sqlglot/parser.py | head", "description": "Trace how parser FUNCTIONS map is built"}
[tool_result] 5 matches in 2 files:

103:0:v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
sqlglot/parsers/duckdb.py:72:NO_PAREN_FUNCTIONS = {
sqlglot/parsers/duckdb.py:73:**parser.Parser.NO_PAREN_FUNCTIONS,
sqlglot/parsers/duckdb.py:95:FUNCTIONS_WITH_ALIASED_ARGS = {*parser.Parser.FUNCTIONS_WITH_ALIASED_ARGS, "STRU...
sqlglot/parsers/duckdb.py:102:FUNCTIONS = {
3 matches in 3 files:

319:0:t.ClassVar[dict[str, t.Callable]] = {
418:0:t.ClassVar[dict] = {
6789:0:
8 matches in 5 files:

1467:0:t.ClassVar = {"STRUCT"}
319:0:t.ClassVar[dict[str, t.Callable]] = {
418:0:t.ClassVar[dict] = {
6789:0:
sqlglot/parser.py:754:*NO_PAREN_FUNCTIONS,
sqlglot/parser.py:6791:return self.expression(self.NO_PAREN_FUNCTIONS[token_type]())
sqlglot/parser.py:6824:functions = self.FUNCTIONS
sqlglot/parser.py:6829:alias = not known_function or upper in self.FUNCTIONS_WITH_ALIASED_ARGS
[tool_use Bash] {"command": "sed -n 98,110p sqlglot/parsers/duckdb.py; sed -n 125,140p sqlglot/parsers/duckdb.py", "description": "Read DuckDB FUNCTIONS dict definition"}
[tool_result]         "TABLES": _show_parser("TABLES"),
        "ALL TABLES": _show_parser("ALL TABLES"),
    }

    FUNCTIONS = {
        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k not in ("DATE_SUB", "GLOB")},
        "ANY_VALUE": lambda args: exp.IgnoreNulls(this=exp.AnyValue.from_arg_list(args)),
        "ARRAY_PREPEND": _build_array_prepend,
        "ARRAY_REVERSE_SORT": _build_sort_array_desc,
        "ARRAY_INTERSECT": lambda args: exp.ArrayIntersect(expressions=args),
        "ARRAY_SORT
…[621 chars elided]…
RACT_PATH": parser.build_extract_json_with_path(exp.JSONExtract),
        "JSON_EXTRACT_STRING": parser.build_extract_json_with_path(exp.JSONExtractScalar),
        "LIST_APPEND": exp.ArrayAppend.from_arg_list,
        "LIST_CONCAT": parser.build_array_concat,
        "LIST_CONTAINS": exp.ArrayContains.from_arg_list,
        "LIST_COSINE_DISTANCE": exp.CosineDistance.from_arg_list,
        "LIST_DISTANCE": exp.EuclideanDistance.from_arg_list,
        "LIST_FILTER": exp.ArrayFilter.from_arg_list,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot.parsers.duckdb import DuckDB\nfrom sqlglot.parser import Parser\nprint('JSON_ARRAY' in Parser.FUNCTIONS, 'JSON_ARRAY' in DuckDB.Parser.FUNCTIONS, DuckDB.Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint(Parser.FUNCTIONS.get('JSON_ARRAY'))\nimport sqlglot; print(sqlglot.__file__)\n\"", "description": "Check JSON_ARRAY in parser FUNCTIONS maps"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 3, in <module>
ImportError: cannot import name 'DuckDB' from 'sqlglot.parsers.duckdb' (~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\nprint('base', Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint('duck', DuckDB.Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint(sqlglot.__file__)\n\"; grep -n \"class.*Parser\\|FUNCTIONS\" sqlglot/dialects/duckdb.py | head", "description": "Check JSON_ARRAY entries in base and DuckDB parser"}
[tool_result] base None
duck None
~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/__init__.py
0 matches for 'class.*Parser\|FUNCTIONS'
[tool_use Bash] {"command": "sed -n 6818,6850p sqlglot/parser.py; grep -n \"ALL_FUNCTIONS\" sqlglot/*.py sqlglot/*/*.py | head", "description": "Read function-call resolution logic in parser"}
[tool_result]                     expr = self._parse_bitwise()

                if expr:
                    return self.expression(subquery_predicate(this=expr), comments=comments)

            if functions is None:
                functions = self.FUNCTIONS

            function = functions.get(upper)
            known_function = function and not anonymous

            alias = not known_function or upper in self.FUNCTIONS_WITH_ALIASED_ARGS
            args = self._parse_function_args(alias)

            pos
…[688 chars elided]…
)

                # mypyc compiled functions don't have __code__, so we use
                # try/except to check if func_builder accepts 'dialect'.
                try:
3 matches in 2 files:

sqlglot/executor/python.py:399:**{klass: _rename for klass in exp.ALL_FUNCTIONS},
sqlglot/expressions/__init__.py:49:ALL_FUNCTIONS = subclasses(__name__, Func, {AggFunc, Anonymous, Func})
sqlglot/expressions/__init__.py:50:...ON_BY_NAME = {name: func for func in ALL_FUNCTIONS for name in func.sql_names()}
[tool_use Bash] {"command": "sed -n 40,60p sqlglot/expressions/__init__.py; grep -n \"FUNCTIONS: \\|FUNCTIONS = \" -A3 sqlglot/parser.py | head -20; grep -n \"FUNCTIONS.*ALL_FUNCTIONS\\|FUNCTION_BY_NAME\" sqlglot/parser.py sqlglot/dialect.py sqlglot/dialects/dialect.py | head", "description": "Find how FUNCTION_BY_NAME feeds parser FUNCTIONS"}
[tool_result]     _is_wrong_expression,
    _to_s,
)
from sqlglot.expressions.query import _apply_cte_builder  # noqa: F401,E402
from sqlglot.expressions.dml import DML  # noqa: F401,E402
from sqlglot.expressions.array import _ExplodeOuter  # noqa: F401,E402

from sqlglot.helper import subclasses

ALL_FUNCTIONS = subclasses(__name__, Func, {AggFunc, Anonymous, Func})
FUNCTION_BY_NAME = {name: func for func in ALL_FUNCTIONS for name in func.sql_names()}
EXPR_CLASSES: dict[str, type[Expr]] = {cls.key: cls for c
…[164 chars elided]…
_NAME.items()},
321-        **dict.fromkeys(("COALESCE", "IFNULL", "NVL"), build_coalesce),
322-        "ARRAY": lambda args, dialect: exp.Array(expressions=args),
--
418:    NO_PAREN_FUNCTIONS: t.ClassVar[dict] = {
419-        TokenType.CURRENT_DATE: exp.CurrentDate,
420-        TokenType.CURRENT_DATETIME: exp.CurrentDate,
421-        TokenType.CURRENT_TIME: exp.CurrentTime,
1 matches in 1 files:

sqlglot/parser.py:320:**{name: func.from_arg_list for name, func in exp.FUNCTION_BY_NAME.items()},
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.parser import Parser\nprint(exp.FUNCTION_BY_NAME.get('JSON_ARRAY'))\nprint(exp.JSONArray.sql_names())\nprint(Parser.FUNCTIONS.get('JSON_ARRAY'))\nprint(type(sqlglot.parse_one('JSON_ARRAY(1)')))\n\"", "description": "Debug JSON_ARRAY function registry lookup"}
[tool_result] None
['J_S_O_N_ARRAY']
None
<class 'sqlglot.expressions.core.Anonymous'>
[assistant] Found the cause: `JSON_ARRAY` isn't in the function registry (`JSONArray` has no `_sql_names`, so its auto-derived name is `J_S_O_N_ARRAY`), so DuckDB parses it as `Anonymous`. The fix is to map it to `exp.JSONArray` in the DuckDB parser, then generate `ARRAY_CONSTRUCT` for Snowflake. Let me look at the existing test layout first.
[tool_use Bash] {"command": "grep -n \"JSON\" tests/dialects/test_duckdb.py | head -20; grep -n \"def test_\" tests/dialects/test_duckdb.py | head -80 | tail -30; grep -n \"def test_json\\|JSON\" tests/dialects/test_snowflake.py | head -5", "description": "Inspect DuckDB and Snowflake JSON test locations"}
[tool_result] 31 matches in 22 files:

105:0:1}') THEN CAST('{"x: 1}' AS JSON) ELSE NULL END""",
107:0:"""SELECT CASE WHEN JSON_VALID('{"x: 1}') THEN CAST('{"x: 1}' AS JSON) ELSE NULL...
108:0:"""SELECT TRY_PARSE_JSON('{"x: 1}')""",
2006:0:'b'} AS JSON)",
313:0:[1, 2, 3]}', '/duck/0')""",
315:0:"""SELECT JSON_EXTRACT('{"duck": [1, 2, 3]}', '/duck/0')""",
320:0:"banana"}') -> 'fruit'""",
322:0:"""SELECT JSON('{"fruit":"banana"}') -> '$.fruit'""",
323:0:"""SELECT GET_PATH(PARSE_JSON('{"fruit":"banana"}'), 'frui
…[457 chars elided]…
 ] }', ['$.family', '$....
569:0:2]",
573:0:2]",
759:0:1}' AS JSON)""",
2202:0:
2209:0:
2216:0:
2223:0:
2233:0:
2256:0:
2277:0:
2305:0:
2319:0:
2322:0:
2405:0:
2431:0:
2438:0:
2455:0:
2473:0:
2484:0:
2489:0:
2498:0:
2510:0:
2518:0:
2541:0:
2592:0:
2611:0:
2623:0:
2635:0:
2647:0:
2667:0:
2687:0:
2722:0:
2751:0:
102 matches in 88 files:

1255:0:"JSON_OBJECT(['key_1', 'key_2'], ['one', NULL])",
1256:0:"JSON_OBJECT('key_1', 'one', 'key_2', NULL)",
1259:0:"JSON_OBJECT('key_1', 'one', 'key_2', NULL)",
[tool_use Bash] {"command": "/usr/bin/grep -n \"    def test_\" tests/dialects/test_duckdb.py | awk -F: '$1<340' | tail -3; /usr/bin/sed -n 100,112p tests/dialects/test_duckdb.py", "description": "Locate JSON-related DuckDB test function"}
[tool_result] 13:    def test_duckdb(self):
                "duckdb": UnsupportedError,
            },
        )

        self.validate_all(
            """SELECT CASE WHEN JSON_VALID('{"x: 1}') THEN CAST('{"x: 1}' AS JSON) ELSE NULL END""",
            read={
                "duckdb": """SELECT CASE WHEN JSON_VALID('{"x: 1}') THEN CAST('{"x: 1}' AS JSON) ELSE NULL END""",
                "snowflake": """SELECT TRY_PARSE_JSON('{"x: 1}')""",
            },
        )
        self.validate_all(
            "SELECT straight_join",
[assistant] Now the edits: the DuckDB parser mapping, and a Snowflake generator method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py", "old_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_EXTRACT_PATH\"", "new_string": "        \"JSON\": exp.ParseJSON.from_arg_list,\n        \"JSON_ARRAY\": lambda args: exp.JSONArray(expressions=args),\n        \"JSON_EXTRACT_PATH\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py", "old_string": "        return inline_array_sql(self, expression)\n\n    def currentdate_sql(", "new_string": "        return inline_array_sql(self, expression)\n\n    @unsupported_args(\"null_handling\", \"return_type\", \"strict\")\n    def jsonarray_sql(self, expression: exp.JSONArray) -> str:\n        return self.func(\"ARRAY_CONSTRUCT\", *expression.expressions)\n\n    def currentdate_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_all(\n            \"SELECT straight_join\",", "new_string": "        self.validate_all(\n            \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n            write={\n                \"duckdb\": \"SELECT JSON_ARRAY('a', 'b', 'c')\",\n                \"snowflake\": \"SELECT ARRAY_CONSTRUCT('a', 'b', 'c')\",\n            },\n        )\n        self.validate_all(\n            \"SELECT straight_join\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-173037-transpiling-duckdb-s-json-array/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in [\\\"SELECT JSON_ARRAY('a', 'b', 'c')\\\", 'SELECT JSON_ARRAY()', 'SELECT JSON_ARRAY(1, NULL)']:\n    print(sqlglot.transpile(s, read='duckdb', write='snowflake'), sqlglot.transpile(s, read='duckdb', write='duckdb'))\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py tests/dialects/test_snowflake.py tests/dialects/test_bigquery.py tests/dialects/test_singlestore.py tests/dialects/test_oracle.py tests/dialects/test_dialect.py 2>&1 | tail -15", "description": "Verify transpilation and run related dialect tests"}
[tool_result] ["SELECT ARRAY_CONSTRUCT('a', 'b', 'c')"] ["SELECT JSON_ARRAY('a', 'b', 'c')"]
['SELECT ARRAY_CONSTRUCT()'] ['SELECT JSON_ARRAY()']
['SELECT ARRAY_CONSTRUCT(1, NULL)'] ['SELECT JSON_ARRAY(1, NULL)']
.........................................................................................................................................................................................................................................................................................................................................................                                                [100%]
345 passed, 6448 subtests passed in 1.84s
[assistant] The transpilation is correct and the related dialect tests pass. Now the full suite, using the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
............................................................................ [ 24%]
................................. [ 27%]
................................................................................................................................................................................................. [ 45%]
...........................................
…[280 chars elided]…
.......... [ 73%]
.................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1084 passed, 17838 subtests passed in 61.14s (0:01:01)
 M sqlglot/generators/snowflake.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/snowflake.py sqlglot/parsers/duckdb.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
3 files already formatted
[assistant] DuckDB `JSON_ARRAY(...)` now transpiles to Snowflake's `ARRAY_CONSTRUCT(...)`:

```sql
-- DuckDB input
SELECT JSON_ARRAY('a', 'b', 'c')
-- Snowflake output
SELECT ARRAY_CONSTRUCT('a', 'b', 'c')
```

The full suite passes (1084 tests) and ruff check and format are clean on the changed files.

**Cause:** `JSON_ARRAY` isn't in the parser's function registry. `exp.JSONArray` has no `_sql_names`, so its auto-derived name is `J_S_O_N_ARRAY`. DuckDB parsed the call as an opaque `Anonymous` function and passed it through unchanged.

**Changes:**
- `sqlglot/parsers/duckdb.py`: maps `JSON_ARRAY` to `exp
…[206 chars elided]…
d_args` for `null_handling`, `return_type` and `strict`, which Snowflake can't express, so those emit a warning rather than being dropped silently.
- `tests/dialects/test_duckdb.py`: a `validate_all` case covering the DuckDB round-trip and the Snowflake output.

**Side effects:** any dialect that parses into `exp.JSONArray` now gets `ARRAY_CONSTRUCT` when writing Snowflake. BigQuery's `JSON_ARRAY` is the main case, so BigQuery → Snowflake also changes. No existing test broke, and I didn't add a test for it.

I haven't committed anything. Let me know if you want a commit, and with what message.
