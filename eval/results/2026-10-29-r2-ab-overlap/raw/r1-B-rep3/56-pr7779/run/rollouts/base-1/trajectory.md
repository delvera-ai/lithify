# trajectory base-1

final message:
StarRocks now gets its own syntax for all four families, and StarRocks' own forms parse back. The full suite passes (1123 tests, 18208 subtests), and ruff and mypy are clean on the changed files. I haven't committed.

What changed, per family:

- **`MIN_BY` / `MAX_BY`**: generated as `MIN_BY` / `MAX_BY`, using the existing `arg_max_or_min_no_count` helper as Hive and BigQuery do. The window form works too (`MAX_BY(a, b) OVER (PARTITION BY c ORDER BY d)`). The docs say window support arrived in StarRocks 3.2. A third `count` argument warns as unsupported, since StarRocks takes two.
- **`MAP`**: array-pair inputs from DuckDB, Presto and Snowflake expand to interleaved `MAP(k1, v1, k2, v2, ...)`. Non-literal inputs, such as a Presto `MAP(col_a, col_b)`, become `MAP_FROM_ARRAYS(keys, values)`, which StarRocks documents. The parser reads `MAP(...)` back as the variadic form and `MAP_FROM_ARRAYS` as the two-array form.
- **`ARRAY_CONTAINS_ALL`**: emitted by name instead of `@>`. Parsing `ARRAY_CONTAINS_ALL(a, b)` already worked.
- **`TRIM`**: StarRocks documents `trim(str[, chars])` plus separate `ltrim`/`rtrim`. So `TRIM(BOTH 'x' FROM a)` becomes `TRIM(a, 'x')`, `LEADING` becomes `LTRIM(a, 'x')`, and `TRAILING` becomes `RTRIM(a, 'x')`. The `TRIM(a, 'x')` form parses back as well.

Files: `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py`, and new `test_native_functions` in `tests/dialects/test_starrocks.py`. No existing test asserted the old output, so none were edited.

Not covered:
- StarRocks' brace map literal (`map{k:v}`) isn't parsed. It wasn't in your list.
- The `TRIM` collation argument is dropped, as the base generator already does.

## events
[assistant] I'll start by reading the StarRocks dialect and the MySQL/base code it inherits from.
[tool_use Bash] {"command": "cat sqlglot/dialects/starrocks.py && git status --short | head && grep -n \"ArgMin\\|ArgMax\\|ARG_MIN\\|ARG_MAX\\|MIN_BY\\|MAX_BY\\|ArrayContainsAll\\|ARRAY_CONTAINS_ALL\" -r sqlglot/ | head -60", "description": "Read StarRocks dialect and search for relevant expressions"}
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
…[2580 chars elided]…

sqlglot/generators/duckdb.py:1123:    # Transform ANY_VALUE(expr HAVING MAX/MIN having_expr) to ARG_MAX_NULL/ARG_MIN_NULL
sqlglot/generators/duckdb.py:1126:        func_name = "ARG_MAX_NULL" if having.args.get("max") else "ARG_MIN_NULL"
sqlglot/generators/teradata.py:73:        exp.ArgMax: rename_func("MAX_BY"),
sqlglot/generators/teradata.py:74:        exp.ArgMin: rename_func("MIN_BY"),
sqlglot/generators/mysql.py:652:    def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
[assistant] The StarRocks dialect is split into `generators/starrocks.py` and `parsers/starrocks.py`. Next I'll read those, plus the MySQL pieces that StarRocks inherits.
[tool_use Bash] {"command": "cat sqlglot/generators/starrocks.py; echo ----PARSER; cat sqlglot/parsers/starrocks.py; echo ----MYSQL-GEN; sed -n 630,670p sqlglot/generators/mysql.py; grep -n \"trim\\|Trim\\|TRIM\\|_sql\\b\\|def map\\|Map\\b\\|MAP\" sqlglot/generators/mysql.py | head -60; echo ----MYSQL-PARSER; grep -n \"TRIM\\|Trim\\|MAP\\|Map\\|_parse_map\\|ARRAY_CONTAINS\\|ArrayContains\" sqlglot/parsers/mysql.py | head -40", "description": "Read StarRocks generator/parser and MySQL trim/map/array handling"}
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

…[20057 chars elided]…
:0:exp.IgnoreNulls) -> str:
809:0:exp.CurrentSchema) -> str:
812:0:exp.Partition) -> str:
825:0:exp.PartitionByRangeProperty) -> str:
828:0:exp.PartitionByListProperty) -> str:
831:0:exp.PartitionList) -> str:
836:0:exp.PartitionRange) -> str:
sqlglot/generators/mysql.py:7:arrow_json_extract_sql,
sqlglot/generators/mysql.py:10:date_add_interval_sql,
----MYSQL-PARSER
1 matches in 1 files:

sqlglot/parsers/mysql.py:98:exp.JSONArrayContains(this=this, expression=self._parse_wrapped(self._parse_e...
[assistant] Next I'll check what the current code actually produces for each of the four cases, so I fix what is really broken rather than what looks wrong.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n ('SELECT MIN_BY(a, b) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) FROM t','starrocks'),\n ('SELECT ARG_MIN(a, b) FROM t','duckdb'),\n ('SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) OVER (PARTITION 
…[960 chars elided]…
ut = 'ERR ' + repr(e)\n    print(f'{d:9} {sql!r:55} -> {out}')\nprint()\nfor sql in ['SELECT MIN_BY(a, b) FROM t','SELECT MAP(\\'a\\', 1, \\'b\\', 2)','SELECT ARRAY_CONTAINS_ALL(a, b)','SELECT TRIM(BOTH \\'x\\' FROM a)','SELECT TRIM(a)']:\n    print(repr(sqlglot.parse_one(sql, read='starrocks')))\n\" 2>&1 | head -120", "description": "Probe current StarRocks output for the four function families"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The `-I` flag ignores the working directory, so the local `sqlglot` package didn't load. This is the user's own repo, so I'll drop `-I` and rerun.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n ('SELECT MIN_BY(a, b) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) FROM t','starrocks'),\n ('SELECT ARG_MIN(a, b) FROM t','duckdb'),\n ('SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) OVER (PARTITION BY 
…[957 chars elided]…
ut = 'ERR ' + repr(e)\n    print(f'{d:9} {sql!r:55} -> {out}')\nprint()\nfor sql in ['SELECT MIN_BY(a, b) FROM t','SELECT MAP(\\'a\\', 1, \\'b\\', 2)','SELECT ARRAY_CONTAINS_ALL(a, b)','SELECT TRIM(BOTH \\'x\\' FROM a)','SELECT TRIM(a)']:\n    print(repr(sqlglot.parse_one(sql, read='starrocks')))\n\" 2>&1 | head -120", "description": "Probe current StarRocks output for the four function families"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 35, in <module>
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/dialects/dialect.py", line 1124, in parse
    return self.
…[9240 chars elided]…
ocks "SELECT TRIM(BOTH 'x' FROM a)"                          -> SELECT TRIM(BOTH 'x' FROM a)
starrocks "SELECT TRIM(LEADING 'x' FROM a)"                       -> SELECT TRIM(LEADING 'x' FROM a)
duckdb    'SELECT TRIM(a)'                                        -> SELECT TRIM(a)
duckdb    "SELECT TRIM('x' FROM a)"                               -> SELECT TRIM('x' FROM a)
duckdb    "SELECT TRIM(a, 'x')"                                   -> SELECT TRIM('x' FROM a)

Select(
  expressions=[
    ArgMin(
[assistant] Four problems are confirmed: `MIN_BY`/`MAX_BY` come out as `ARG_MIN`/`ARG_MAX`, the variadic `MAP(k, v, ...)` fails to parse, `ARRAY_CONTAINS_ALL` is emitted as `@>`, and `TRIM` passes through unchanged. Next I'll look at the MAP and TRIM code paths and check StarRocks' documented TRIM syntax.
[tool_use Bash] {"command": "grep -n \"def trim_sql\" -A 12 sqlglot/dialects/dialect.py; grep -n \"class Trim\\b\" -A 8 sqlglot/expressions/*.py; grep -n \"class Map\\b\\|class VarMap\\|class ToMap\" -A 6 sqlglot/expressions/*.py; grep -n '\"MAP\"\\|exp.Map\\b\\|exp.VarMap\\|_parse_map\\|def build_var_map\\|def build_map\\|Map.from_arg_list' sqlglot/parser.py sqlglot/parsers/*.py sqlglot/dialects/dialect.py | head -40; grep -n \"exp.Map\\b\\|exp.Map:\\|def map_sql\\|exp.VarMap\" sqlglot/generator.py sqlglot/generators/*.py | head -30; grep -n \"_parse_trim\" -A 25 sqlglot/parser.py | head -60", "description": "Inspect trim, map, and parser trim code paths"}
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
…[6290 chars elided]…
 invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8279-            expression = self._parse_bitwise()
8280-
8281-            if invert_order:
8282-                this, expression = expression, this
8283-
8284-        if self._match(TokenType.COLLATE):
8285-            collation = self._parse_bitwise()
8286-
8287-        return self.expression(
8288-            exp.Trim(this=this, position=position, expression=expression, collation=collation)
8289-        )
8290-
[assistant] Before deciding the TRIM rewrite, I need StarRocks' own documented TRIM signature. I'll check that and the MAP and MIN_BY docs in parallel.
[tool_use Bash] {"command": "echo \"checking docs via WebSearch next\"", "description": "Placeholder step before documentation search"}
[tool_result] checking docs via WebSearch next
[tool_use WebSearch] {"query": "StarRocks trim function syntax ltrim rtrim docs.starrocks.io"}
[tool_use WebSearch] {"query": "StarRocks MAP constructor syntax map(key1, value1, key2, value2) docs"}
[tool_use WebSearch] {"query": "StarRocks min_by max_by window function syntax"}
[tool_result] Web search results for query: "StarRocks trim function syntax ltrim rtrim docs.starrocks.io"

Links: [{"title":"ltrim","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/ltrim/"},{"title":"trim","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim/"},{"title":"rtrim","url":"https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/rtrim/"},{"title":"TRIM Functions in sql. hey , this is article about my small…","
…[1617 chars elided]…
ARCHAR characters])`. It removes consecutive spaces or specified characters from both the beginning and end of the str argument. (https://docs.starrocks.io/docs/sql-reference/sql-functions/string-functions/trim/)

Specified-character trimming has been available since StarRocks 2.5.0, per all three pages. The other results were from Oracle, SQL Server, and generic references, so I left them out.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks MAP constructor syntax map(key1, value1, key2, value2) docs"

Links: [{"title":"MAP @ Map @ StarRocks Docs","url":"https://docs.starrocks.io/en-us/3.1/sql-reference/sql-statements/data-types/Map"},{"title":"MAP","url":"https://docs.starrocks.io/docs/sql-reference/data-types/semi_structured/Map/"},{"title":"starrocks/contrib/starrocks-python-client/docs/usage_guide/tables.md at main · StarRocks/starrocks · GitHub","url":"https://github.com/StarRocks/starro
…[1567 chars elided]…
P data type is supported from v3.1 onwards.
- A related function, `map_from_arrays`, builds a map from two arrays, and its docs state that keys and values must have the same length, otherwise it will return an error.

Sources: https://docs.starrocks.io/docs/sql-reference/data-types/semi_structured/Map/ and https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[tool_result] Web search results for query: "StarRocks min_by max_by window function syntax"

Links: [{"title":"Window function @ Window_function @ StarRocks Docs","url":"https://docs.starrocks.io/en-us/latest/using_starrocks/Window_function"},{"title":"[Feature]support max_by/min_by in window op by before-Sunrise · Pull Request #54961 · StarRocks/starrocks · GitHub","url":"https://github.com/StarRocks/starrocks/pull/54961"},{"title":"starrocks/docs/en/release_notes/release-3.2.md at main · StarRocks/starrock
…[1856 chars elided]…
null value, the row that corresponds to the null value is ignored. For ties, the function returns the first value of x encountered.

The window-specific syntax and any frame-clause restrictions for `max_by`/`min_by` are still unverified. The official docs for the window functions page don't list these two functions. Checking the PR #54961 diff or the 3.2.15 release notes would be the next step.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] The docs confirm the target syntax: StarRocks `TRIM(str[, chars])` with separate `LTRIM`/`RTRIM`, the variadic `MAP(k1, v1, ...)`, `MAP_FROM_ARRAYS(keys, values)` for the two-array form, and `MIN_BY`/`MAX_BY` (2 args, window form supported since 3.2). Next I'll check the generator dispatch order, the existing helpers, and whether the current tests assert the old output.
[tool_use Bash] {"command": "sed -n 40,60p sqlglot/parser.py; grep -n \"def arg_max_or_min_no_count\" -A 12 sqlglot/dialects/dialect.py; grep -n \"class ArgMin\\|class ArgMax\" -B0 -A4 sqlglot/expressions/aggregate.py; grep -n \"def trim_sql\" -A 25 sqlglot/generator.py; grep -n \"exp.Trim\\|trim_sql\" sqlglot/generators/mysql.py sqlglot/generator.py sqlglot/dialects/dialect.py | head; grep -n \"class Ltrim\\|class Rtrim\\|class LTrim\\|class RTrim\" -A3 sqlglot/expressions/*.py; grep -n \"def _generate_method\\|TRANSFORMS.get\\|getattr(self, f\\\"{\\|_sql\\\"\" sqlglot/generator.py | head", "description": "Inspect helpers, arg definitions, and generator dispatch"}
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
…[2554 chars elided]…
l.py:221:exp.Trim: trim_sql,
sqlglot/expressions/string.py:125:class RtrimmedLength(Expression, Func):
sqlglot/expressions/string.py-126-    pass
sqlglot/expressions/string.py-127-
sqlglot/expressions/string.py-128-
rg: regex parse error:
    (?:def _generate_method|TRANSFORMS.get|getattr(self, f"{|_sql")
                                                            ^
error: repetition quantifier expects a valid decimal
0 matches for 'def _generate_method\|TRANSFORMS.get\|getattr(self, f"{\|_sql"'
[tool_use Bash] {"command": "ls tests/dialects | grep -i star; grep -n -i \"arg_min\\|arg_max\\|min_by\\|max_by\\|@>\\|contains_all\\|trim\\|map(\" tests/dialects/test_starrocks.py | head -60; grep -rn \"starrocks\" tests/*.py tests/dialects/test_mysql.py tests/dialects/test_dialect.py 2>/dev/null | head -20", "description": "Check helper definitions and existing StarRocks test assertions"}
[tool_result] test_starrocks.py  17.0K
tests/test_transpile.py:1073:            ("starrocks", "CREATE VIEW v SECURITY INVOKER AS SELECT 1"),
tests/dialects/test_mysql.py:585:            "starrocks": "SELECT x'CC'",
tests/dialects/test_mysql.py:606:            "starrocks": "SELECT x'0000CC'",
tests/dialects/test_mysql.py:1059:                "starrocks": "CAST(x AS STRING)",
tests/dialects/test_mysql.py:1511:                "starrocks": "a / b",
tests/dialects/test_dialect.py:243:                "starrocks": "
…[728 chars elided]…
ialects/test_dialect.py:459:                "starrocks": "CAST(a AS DOUBLE)",
tests/dialects/test_dialect.py:472:                "starrocks": "CAST(a AS DATETIME)",
tests/dialects/test_dialect.py:481:                "starrocks": "TIMESTAMP(a)",
tests/dialects/test_dialect.py:639:                "starrocks": "TO_BINARY('1C')",
tests/dialects/test_dialect.py:646:                "starrocks": "TO_BINARY('1C')",
tests/dialects/test_dialect.py:657:                "starrocks": "TO_BINARY('1C', 'HEX')",
[assistant] The StarRocks test file doesn't cover these four families. The shared dialect tests might, so I'll grep those for StarRocks expectations that my change would alter.
[tool_use Bash] {"command": "grep -rn '\"starrocks\": .*\\(ARG_\\|MIN_BY\\|MAX_BY\\|MAP(\\|TRIM\\|@>\\|CONTAINS_ALL\\|LTRIM\\|RTRIM\\)' tests/ | head -40; echo ---; grep -rn 'ARG_MIN\\|ARG_MAX\\|ArgMin\\|ArgMax' tests/ | grep -i \"starrocks\\|mysql\\|doris\" | head; echo ---; grep -n \"ArrayContainsAll\\|ARRAY_CONTAINS_ALL\" -r tests/dialects/*.py | head -20", "description": "Find existing StarRocks test expectations for affected functions"}
[tool_result] ---
---
tests/dialects/test_duckdb.py:1353:        self.validate_identity("a @> b").assert_is(exp.ArrayContainsAll)
[assistant] No existing test pins the old output, so nothing has to be weakened. Next I'll confirm how the generator resolves `TRANSFORMS` against `<name>_sql` methods, since that decides where the `ARRAY_CONTAINS_ALL` fix goes.
[tool_use Bash] {"command": "grep -n \"    def sql(\" -A 40 sqlglot/generator.py | grep -n \"TRANSFORMS\\|sql_handler\\|_sql\\|getattr\\|transform\" | head -20; grep -n \"ArrayContainsAll\" sqlglot/generators/*.py sqlglot/generator.py | head; grep -n \"exp.VarMap\\|exp.Map\\b\" sqlglot/generators/duckdb.py sqlglot/generators/mysql.py | head", "description": "Check generator dispatch precedence and related generator entries"}
[tool_result] 24:1110-            sql = self.function_fallback_sql(expression)
26:1112-            sql = self.property_sql(expression)
32:1118-    def uncache_sql(self, expression: exp.Uncache) -> str:
34:1120-        exists_sql = " IF EXISTS" if expression.args.get("exists") else ""
35:1121-        return f"UNCACHE TABLE{exists_sql} {table}"
37:1123-    def cache_sql(self, expression: exp.Cache) -> str:
2 matches in 2 files:

sqlglot/generator.py:144:exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/generators/mysql.py:652:def arraycontainsall_sql(self, expression: exp.ArrayContainsAll) -> str:
1 matches in 1 files:

sqlglot/generators/duckdb.py:3548:return self.sql(exp.array(exp.Map(keys=exp.array(), values=exp.array())))
[tool_use Bash] {"command": "grep -n \"    def sql(\" -A 45 sqlglot/generator.py | sed -n 1,60p; grep -n \"def __init_subclass__\\|_sql_handler\\|TRANSFORMS\" sqlglot/generator.py | head -20", "description": "Read generator sql() dispatch logic"}
[tool_result] 1087:    def sql(
1088-        self,
1089-        expression: str | exp.Expr | None,
1090-        key: str | None = None,
1091-        comment: bool = True,
1092-    ) -> str:
1093-        if not expression:
1094-            return ""
1095-
1096-        if isinstance(expression, str):
1097-            return expression
1098-
1099-        if key:
1100-            value = expression.args.get(key)
1101-            if value:
1102-                return self.sql(value)
1103-            return ""
1104
…[1525 chars elided]…
y] = {
655:0:t.ClassVar = {
81:0:dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)
sqlglot/generator.py:14:from sqlglot.jsonpath import ALL_JSON_PATH_PARTS, JSON_PATH_PART_TRANSFORMS
sqlglot/generator.py:136:**JSON_PATH_PART_TRANSFORMS,
sqlglot/generator.py:659:**AFTER_HAVING_MODIFIER_TRANSFORMS,
sqlglot/generator.py:3249:*[gen(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.valu...
sqlglot/generator.py:3748:transform = self.TRANSFORMS.get(expression.__class__)
[assistant] Two things remain to verify before editing: how the base class picks up a `<name>_sql` method when no `TRANSFORMS` entry exists, and how other parsers import `build_var_map`. I'll check both, plus how StarRocks currently parses `LTRIM`/`RTRIM` with a second argument.
[tool_use Bash] {"command": "sed -n 75,100p sqlglot/generator.py; grep -n \"build_var_map\\|^from\\|^import\" sqlglot/parsers/hive.py | head; grep -n \"^from\\|^import\" sqlglot/parsers/mysql.py | head; grep -n \"def var_map_sql\" -A 12 sqlglot/dialects/dialect.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['SELECT LTRIM(a, \\'x\\')','SELECT RTRIM(a)','SELECT MAP_FROM_ARRAYS(a, b)', 'SELECT TRIM(a, \\'x\\')']:\n    print(repr(sqlglot.parse_one(s, read='starrocks').selects[0]))\n\"", "description": "Check generator method discovery and parser import conventions"}
[tool_result] _DISPATCH_CACHE: dict[type[Generator], dict[type[exp.Expr], t.Callable[..., str]]] = {}


def _build_dispatch(
    cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and
…[1677 chars elided]…

Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Literal(this='x', is_string=True),
  position=LEADING)
Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  position=TRAILING)
Anonymous(
  this=MAP_FROM_ARRAYS,
  expressions=[
    Column(
      this=Identifier(this=a, quoted=False)),
    Column(
      this=Identifier(this=b, quoted=False))])
Trim(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Literal(this='x', is_string=True))
[assistant] Two useful findings: `LTRIM(a, 'x')` already parses to `Trim(position=LEADING)`, and the shared `var_map_sql` helper already interleaves keys and values into `MAP(k1, v1, ...)`. I'll read the rest of that helper before deciding whether to reuse it.
[tool_use Bash] {"command": "sed -n 1476,1496p sqlglot/dialects/dialect.py; grep -n \"var_map_sql\\|arg_max_or_min_no_count\\|rename_func\" sqlglot/generators/hive.py | head -5; grep -n \"ArrayContainsAll\\|Trim\" sqlglot/generators/doris.py sqlglot/generators/clickhouse.py | head", "description": "Read full var_map_sql helper and precedent usages"}
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
…[13 chars elided]…
args.append(self.sql(value))

    return self.func(map_func_name, *args)


def months_between_sql(self: Generator, expression: exp.MonthsBetween) -> str:
    """
    Transpile MONTHS_BETWEEN to dialects that don't have native support.
30 matches in 25 files:

239:0:rename_func("FIRST"),
241:0:arg_max_or_min_no_count("MAX_BY"),
242:0:arg_max_or_min_no_count("MIN_BY"),
1 matches in 1 files:

sqlglot/generators/clickhouse.py:366:exp.Trim: lambda self, e: trim_sql(self, e, default_trim_type="BOTH"),
[assistant] I have what I need. The plan:

- **MIN_BY / MAX_BY**: reuse the existing `arg_max_or_min_no_count` helper, as Hive and BigQuery do. It covers the window form too.
- **MAP**: reuse `var_map_sql` (it emits interleaved `MAP(k1, v1, ...)`) for array-pair inputs. Non-array inputs go to `MAP_FROM_ARRAYS`, which StarRocks documents, rather than the helper's `MAP(keys, values)` fallback, which StarRocks would reject. On the parse side, `MAP` maps to `build_var_map`.
- **ARRAY_CONTAINS_ALL**: a `rename_func` entry in `TRANSFORMS`. The base `TRANSFORMS` entry for `@>` wins over the MySQL `_sql` method, so a method alone would not change the output.
- **TRIM**: drop MySQL's `Trim` transform so the base `trim_sql` method applies. That method emits `TRIM(x, chars)`, and `LTRIM`/`RTRIM` for LEADING/TRAILING, which is what StarRocks accepts.

I'll make the generator edits first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arrow_json_extract_sql,\n    rename_func,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n)", "new_string": "from sqlglot.dialects.dialect import (\n    approx_count_distinct_sql,\n    arg_max_or_min_no_count,\n    arrow_json_extract_sql,\n    rename_func,\n    unit_to_str,\n    inline_array_sql,\n    property_sql,\n    var_map_sql,\n)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "    point2_y = self.func(\"ST_Y\", point2)\n\n    return self.func(\"ST_Distance_Sphere\", point1_x, point1_y, point2_x, point2_y)\n", "new_string": "    point2_y = self.func(\"ST_Y\", point2)\n\n    retur
…[266 chars elided]…
else goes through map_from_arrays\n    # https://docs.starrocks.io/docs/sql-reference/sql-functions/map-functions/map_from_arrays/\n    keys = expression.args.get(\"keys\")\n    values = expression.args.get(\"values\")\n\n    if isinstance(keys, exp.Array) and isinstance(values, exp.Array):\n        return var_map_sql(self, expression)\n\n    return self.func(\"MAP_FROM_ARRAYS\", keys, values)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        **{k: v for k, v in MySQLGenerator.TRANSFORMS.items() if k is not exp.DateTrunc},\n        exp.Array: inline_array_sql,\n        exp.ArrayAgg: rename_func(\"ARRAY_AGG\"),\n        exp.ArrayFilter: 
…[584 chars elided]…
ContainsAll: rename_func(\"ARRAY_CONTAINS_ALL\"),\n        exp.ArrayFilter: rename_func(\"ARRAY_FILTER\"),\n        exp.ArrayToString: rename_func(\"ARRAY_JOIN\"),\n        exp.ApproxDistinct: approx_count_distinct_sql,\n        exp.ArgMax: arg_max_or_min_no_count(\"MAX_BY\"),\n        exp.ArgMin: arg_max_or_min_no_count(\"MIN_BY\"),\n        exp.CurrentVersion: lambda *_: \"CURRENT_VERSION()\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Property: property_sql,", "new_string": "        exp.JSONExtract: arrow_json_extract_sql,\n        exp.Map: _map_sql,\n        exp.Property: property_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py", "old_string": "        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n    }", "new_string": "        exp.UnixToTime: rename_func(\"FROM_UNIXTIME\"),\n        exp.VarMap: _map_sql,\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/generators/starrocks.py has been updated successfully.
[assistant] Next, the parser side: the variadic `MAP` and the `MAP_FROM_ARRAYS` form, so StarRocks' own output reads back.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "from sqlglot import exp\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc", "new_string": "from sqlglot import exp, parser\nfrom sqlglot.dialects.dialect import build_date_delta_with_interval, build_timestamp_trunc"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py", "old_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,", "new_string": "        \"ARRAY_FLATTEN\": exp.Flatten.from_arg_list,\n        \"MAP\": parser.build_var_map,\n        \"MAP_FROM_ARRAYS\": exp.Map.from_arg_list,\n        \"REGEXP\": exp.RegexpLike.from_arg_list,"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/sqlglot/parsers/starrocks.py has been updated successfully.
[assistant] Now I'll re-run the same probe to confirm the new output for every case, including the parse-back forms.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = [\n ('SELECT MIN_BY(a, b) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) FROM t','starrocks'),\n ('SELECT ARG_MIN(a, b) FROM t','duckdb'),\n ('SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t','starrocks'),\n ('SELECT MAX_BY(a, b) OVER (PARTITION BY c ORDER BY d) FROM t','st
…[1099 chars elided]…
s e:\n        out = 'ERR ' + repr(e)[:200]\n    print(f'{d:9} {sql!r:50} -> {out}')\nprint()\nfor sql in ['SELECT MAP(\\'a\\', 1, \\'b\\', 2)','SELECT MAP_FROM_ARRAYS(a, b)','SELECT ARRAY_CONTAINS_ALL(a, b)','SELECT TRIM(BOTH \\'x\\' FROM a)']:\n    print(sqlglot.transpile(sql, read='starrocks', write='duckdb')[0])\n\" 2>&1 | head -80", "description": "Re-run StarRocks probe to verify new output"}
[tool_result] starrocks 'SELECT MIN_BY(a, b) FROM t'                       -> SELECT MIN_BY(a, b) FROM t
starrocks 'SELECT MAX_BY(a, b) FROM t'                       -> SELECT MAX_BY(a, b) FROM t
duckdb    'SELECT ARG_MIN(a, b) FROM t'                      -> SELECT MIN_BY(a, b) FROM t
starrocks 'SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t' -> SELECT MIN_BY(a, b) OVER (PARTITION BY c) FROM t
starrocks 'SELECT MAX_BY(a, b) OVER (PARTITION BY c ORDER BY d) FROM t' -> SELECT MAX_BY(a, b) OVER (PARTITION BY 
…[1439 chars elided]…
'x')
starrocks "SELECT LTRIM(a, 'x')"                             -> SELECT LTRIM(a, 'x')
starrocks 'SELECT RTRIM(a)'                                  -> SELECT RTRIM(a)
duckdb    'SELECT TRIM(a)'                                   -> SELECT TRIM(a)
duckdb    "SELECT TRIM('x' FROM a)"                          -> SELECT TRIM(a, 'x')
duckdb    "SELECT TRIM(LEADING 'x' FROM a)"                  -> SELECT LTRIM(a, 'x')

SELECT MAP(['a', 'b'], [1, 2])
SELECT MAP(a, b)
SELECT a @> b
SELECT TRIM(a, 'x')
[assistant] All the cases produce StarRocks-native output now. The parse-back forms (`MAP`, `MAP_FROM_ARRAYS`, `ARRAY_CONTAINS_ALL`, `TRIM` with a character set) also round-trip. Next I'll add tests in the existing StarRocks test file, so I'm checking its style first.
[tool_use Bash] {"command": "sed -n 1,40p tests/dialects/test_starrocks.py; echo ...; tail -30 tests/dialects/test_starrocks.py", "description": "Read StarRocks test file style and structure"}
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
…[2509 chars elided]…
   self.validate_identity(
            "CREATE TABLE test_table (col1 BIGINT) PARTITION BY RANGE (col1) (START ('1') END ('10') EVERY (1), START ('10') END ('100') EVERY (10))"
        )
        self.validate_identity(
            "CREATE TABLE test_table (col1 DATE) PARTITION BY RANGE (col1) (START ('2019-01-01') END ('2021-01-01') EVERY (INTERVAL 1 YEAR), START ('2021-01-01') END ('2021-05-01') EVERY (INTERVAL 1 MONTH), START ('2021-05-01') END ('2021-05-04') EVERY (INTERVAL 1 DAY))"
        )
[assistant] I'll add a `test_native_functions` method next to the existing `test_starrocks`, using the file's `validate_identity` and `validate_all` helpers. The `read` entries cover the cross-dialect cases.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py", "old_string": "        self.validate_identity(\"SELECT t1.id FROM t1 LEFT SEMI JOIN t2 ON t1.id = t2.id\")\n\n    def test_distinct_on(self):", "new_string": "        self.validate_identity(\"SELECT t1.id FROM t1 LEFT S
…[1468 chars elided]…
          read={\"duckdb\": \"SELECT TRIM('x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT LTRIM(a, 'x')\",\n            read={\"duckdb\": \"SELECT TRIM(LEADING 'x' FROM a)\"},\n        )\n        self.validate_all(\n            \"SELECT RTRIM(a, 'x')\",\n            read={\"duckdb\": \"SELECT TRIM(TRAILING 'x' FROM a)\"},\n        )\n\n    def test_distinct_on(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-203438-starrocks-dialect-several-functi/base-1/tests/dialects/test_starrocks.py has been updated successfully.
[assistant] Now I'll run the StarRocks test module, then the project's full check command from the harness.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_starrocks.py 2>&1 | tail -40", "description": "Run StarRocks dialect tests"}
[tool_result] ............. [100%]
13 passed, 77 subtests passed in 0.13s
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
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
....... [ 66%]
............................................................................................................ [ 76%]
.......................................... [ 80%]
.............................................. [ 84%]
................................................................................................................................................................................                                      [100%]
1123 passed, 18208 subtests passed in 47.14s
[assistant] The full suite passes: 1123 tests and 18208 subtests. Last, I'll run the repo's lint and format checks on the changed files.
[tool_use Bash] {"command": "ENVBIN=<work>/env-sqlglot/bin; ls $ENVBIN | grep -i \"ruff\\|mypy\" ; ($ENVBIN/ruff check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py && $ENVBIN/ruff format --check sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py tests/dialects/test_starrocks.py) 2>&1 | tail -15; git status --short; git diff --stat", "description": "Run ruff lint and format check on changed files"}
[tool_result] dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
All checks passed!
3 files already formatted
 M sqlglot/generators/starrocks.py
 M sqlglot/parsers/starrocks.py
 M tests/dialects/test_starrocks.pysqlglot/generators/starrocks.py  | 27 ++++++++++++++++++++++-
 sqlglot/parsers/starrocks.py     |  4 +++-
 tests/dialects/test_starrocks.py | 46 ++++++++++++++++++++++++++++++++++++++++
 3 files changed, 75 insertions(+), 2 deletions(-)
[assistant] Lint and format pass. The repo's pre-commit config also runs mypy, so I'll type-check the two source files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/mypy sqlglot/generators/starrocks.py sqlglot/parsers/starrocks.py 2>&1 | tail -8", "description": "Type-check changed StarRocks source files", "timeout": 600000}
[tool_result] Success: no issues found in 2 source files
[assistant] StarRocks now gets its own syntax for all four families, and StarRocks' own forms parse back. The full suite passes (1123 tests, 18208 subtests), and ruff and mypy are clean on the changed files. I haven't committed.

What changed, per family:

- **`MIN_BY` / `MAX_BY`**: generated as `MIN_BY` / `MAX_BY`, using the existing `arg_max_or_min_no_count` helper as Hive and BigQuery do. The window form works too (`MAX_BY(a, b) OVER (PARTITION BY c ORDER BY d)`). The docs say window support arrived in StarRocks 3.2. A third `count` argument warns as unsupported, since StarRocks takes two.
- **`MAP`**:
…[480 chars elided]…
tr[, chars])` plus separate `ltrim`/`rtrim`. So `TRIM(BOTH 'x' FROM a)` becomes `TRIM(a, 'x')`, `LEADING` becomes `LTRIM(a, 'x')`, and `TRAILING` becomes `RTRIM(a, 'x')`. The `TRIM(a, 'x')` form parses back as well.

Files: `sqlglot/generators/starrocks.py`, `sqlglot/parsers/starrocks.py`, and new `test_native_functions` in `tests/dialects/test_starrocks.py`. No existing test asserted the old output, so none were edited.

Not covered:
- StarRocks' brace map literal (`map{k:v}`) isn't parsed. It wasn't in your list.
- The `TRIM` collation argument is dropped, as the base generator already does.
