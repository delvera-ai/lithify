# trajectory base-1

final message:
Overloaded DuckDB macros now parse and round-trip. The issue's example outputs `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`, and DuckDB 1.5.6 accepts that output and resolves the overloads correctly: `add_x(1, 2)` returns 3 and `add_x(1, 2, 3)` returns 6. The full suite passes (1114 tests), and ruff and mypy are clean. I haven't committed anything.

**Representation.** An overloaded macro becomes `Create(this=<name only>, kind=MACRO, expression=MacroOverloads(...))`. `MacroOverloads` holds one `MacroOverload` per overload, each with its parameters, its body, and a `table` flag. Single-overload macros keep their existing representation, so existing output doesn't change.

**Changes:**
- `sqlglot/expressions/ddl.py`: the two new node classes.
- `sqlglot/parser.py`: after a `CREATE MACRO` body, a comma starts further overloads. This is gated by a new `SUPPORTS_MACRO_OVERLOADS` flag, which only the DuckDB parser enables.
- `sqlglot/parsers/duckdb.py`: overrides the macro body parser. Without this, a subquery body swallows `, (a, b)` as an implicit join, so `AS (SELECT a), (a, b) AS …` fails to parse. This override applies to all DuckDB `CREATE FUNCTION`/`CREATE MACRO` bodies, not only overloads. The existing tests pass, but it's a real behavior change.
- `sqlglot/generator.py`: emits the overloads without the extra `AS` and separator that `create_sql` would add. Overloads are written flat, so pretty output stays on one line.
- `tests/dialects/test_duckdb.py`: a new `test_macro_overloads` covering scalar and table overloads, round-trips, and the node structure.

**Limits.** DuckDB only accepts a parenthesized body for a table overload, as in `AS TABLE (SELECT …)`. An unparenthesized `AS TABLE SELECT …` followed by another overload is a syntax error in DuckDB too, so sqlglot doesn't accept it either. DuckDB also doesn't allow mixing scalar and table overloads in one macro. The parser accepts a mix and doesn't reject it, since the representation keeps the flag per overload.

## events
[assistant] I'll start by finding how the DuckDB dialect currently parses `CREATE MACRO`.
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60; echo ---; grep -rn -i \"macro\" tests/dialects/test_duckdb.py | head -30", "description": "Search macro handling across sqlglot and tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
---
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
[tool_use Bash] {"command": "ls; grep -rn -i \"macro\" sqlglot/expressions/*.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/duckdb.py 2>/dev/null | head -60; echo ---; sed -n 2570,2620p tests/dialects/test_duckdb.py", "description": "Locate macro references in source and tests"}
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
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
---
        ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM
…[1779 chars elided]…
RNS TABLE RETURN SELECT a",
                "duckdb": "CREATE OR REPLACE FUNCTION func(a INT, b REAL) AS TABLE SELECT a",
            },
        )

    def test_bitwise_agg(self):
        self.validate_all(
            "SELECT BIT_OR(int_value) FROM t",
            read={
                "snowflake": "SELECT BITOR_AGG(int_value) FROM t",
                "duckdb": "SELECT BIT_OR(int_value) FROM t",
            },
        )
        self.validate_all(
            "SELECT BIT_AND(int_value) FROM t",
[assistant] Macros go through the generic `CREATE ... FUNCTION` path. Next I'll check how the parser and generator handle that path, and reproduce the failure.
[tool_use Bash] {"command": "grep -n \"_parse_create\\|def _parse_user_defined_function\\|_parse_user_defined_function_expression\\|TABLE\\b\" sqlglot/parser.py | head -40; echo ---; grep -n \"def create_sql\\|def _parse_create\" sqlglot/generator.py sqlglot/parser.py sqlglot/dialects/duckdb.py; ls .venv 2>/dev/null; which python; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__, sys.version)\"", "description": "Find create parsing code and check Python env"}
[tool_result] 633:        TokenType.TABLE,
660:        TokenType.TABLE,
865:        TokenType.TABLE,
1090:        TokenType.CREATE: lambda self: self._parse_create(),
1253:            exp.StabilityProperty(this=exp.Literal.string("IMMUTABLE"))
1274:        "IMMUTABLE": lambda self: self.expression(
1275:            exp.StabilityProperty(this=exp.Literal.string("IMMUTABLE"))
1285:        "LIKE": lambda self: self._parse_create_like(),
1322:        "STABLE": lambda self: self.expression(
1323:            exp.St
…[1988 chars elided]…
r:
sqlglot/parser.py:2346:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parser.py:3296:    def _parse_create_like(self) -> exp.LikeProperty | None:
<work>/env-sqlglot/bin/python
~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
[tool_use Bash] {"command": "sed -n 2346,2470p sqlglot/parser.py; echo ---; grep -n \"_parse_user_defined_function_expression\" -A30 sqlglot/parser.py | sed -n 1,50p", "description": "Read _parse_create and UDF expression parsing"}
[tool_result]     def _parse_create(self) -> exp.Create | exp.Command:
        # Note: this can't be None because we've matched a statement parser
        start = self._prev

        replace = (
            start.token_type == TokenType.REPLACE
            or self._match_pair(TokenType.OR, TokenType.REPLACE)
            or self._match_pair(TokenType.OR, TokenType.ALTER)
        )
        refresh = self._match_pair(TokenType.OR, TokenType.REFRESH)

        unique = self._match(TokenType.UNIQUE)

        if sel
…[6712 chars elided]…
  def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032-        this = self._parse_table_parts(schema=True)
7033-
7034-        if not self._match(TokenType.L_PAREN):
7035-            return this
7036-
7037-        expressions = self._parse_csv(self._parse_function_parameter)
7038-        self._match_r_paren()
7039-        return self.expression(
7040-            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
7041-        )
7042-
[assistant] The failure is in the `AS <body>` step: it parses one expression and then hits the comma. Next I'll look at the `Create` and `UserDefinedFunction` expression definitions and the generator's `create_sql`.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; ls sqlglot/expressions* -d; grep -rn \"class Create(\\|class UserDefinedFunction\\|class Return(\" sqlglot/ ; echo ---; sed -n 1287,1340p sqlglot/generator.py; echo ---; grep -n \"def userdefinedfunction_sql\" -A12 sqlglot/generator
…[60 chars elided]…
R REPLACE MACRO add_2(a, b) AS a + b;', 'CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c']:\n  try:\n    e=sqlglot.parse_one(s, read='duckdb'); print(repr(e)[:600]); print(e.sql('duckdb'))\n  except Exception as ex: print('ERR', type(ex).__name__, str(ex)[:300])\n\"", "description": "Inspect Create/UDF classes, generator, and current parse output"}
[tool_result] ls: -d: No such file or directory
sqlglot/expressions:
__init__.py
__pycache__
aggregate.py
array.py
builders.py
constraints.py
core.py
datatypes.py
ddl.py
dml.py
functions.py
json.py
math.py
properties.py
query.py
string.py
temporal.py
sqlglot/expressions/ddl.py:39:class Create(Expression, DDL):
sqlglot/expressions/ddl.py:225:class UserDefinedFunction(Expression):
sqlglot/expressions/query.py:882:class Return(Expression):
---
    def create_sql(self, expression: exp.Create) -> str:
        kind
…[3709 chars elided]…
False,
  unique=False,
  expression=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]),
  exists=False,
  properties=Properties(
    expressions=[
      ReturnsProperty(
        this=Schema(
          this=Var(this=TABLE)),
        is_table=True)]),
  begin=False,
  concurrently=False)
CREATE MACRO t(a) AS TABLE SELECT a
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  CREATE MACRO add_x (a, b) AS a + b[4m,[0m (a, b, c) AS a + b + c
[assistant] The single-overload case parses; the comma-separated overload list does not. Next I'll read the `Create`/`UserDefinedFunction` definitions, the rest of `create_sql`, and how DuckDB emits the table-macro `AS TABLE` form.
[tool_use Bash] {"command": "sed -n 39,60p sqlglot/expressions/ddl.py; echo ...; sed -n 220,240p sqlglot/expressions/ddl.py; echo ---; sed -n 1340,1360p sqlglot/generator.py; echo ---; grep -n \"ReturnsProperty\\|is_table\\|TABLE\" sqlglot/dialects/duckdb.py | head; grep -n \"def returnsproperty_sql\" -A25 sqlglot/generator.py | head -40; echo ---; grep -n \"MACRO\\|macro\" sqlglot/dialects/duckdb.py sqlglot/tokens.py | head", "description": "Read Create and UDF classes and related generator code"}
[tool_result] class Create(Expression, DDL):
    arg_types = {
        "with_": False,
        "this": True,
        "kind": True,
        "expression": False,
        "exists": False,
        "properties": False,
        "replace": False,
        "refresh": False,
        "unique": False,
        "indexes": False,
        "no_schema_binding": False,
        "begin": False,
        "clone": False,
        "concurrently": False,
        "clustered": False,
    }

    @property
    def kind(self) -> str | None:
…[1053 chars elided]…
ent=False, sep=" ")
        indexes = f" {indexes}" if indexes else ""
        index_sql = indexes + postindex_props_sql

        replace = " OR REPLACE" if expression.args.get("replace") else ""
        refresh = " OR REFRESH" if expression.args.get("refresh") else ""
        unique = " UNIQUE" if expression.args.get("unique") else ""

        clustered = expression.args.get("clustered")
        if clustered is None:
---
---
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
[tool_use Bash] {"command": "grep -rn \"is_table\" sqlglot/ | head; echo ---; grep -n \"ReturnsProperty\" sqlglot/*.py sqlglot/dialects/duckdb.py sqlglot/expressions/*.py | head -20; echo ---; sed -n 1360,1400p sqlglot/generator.py; echo ---; sed -n 880,900p sqlglot/expressions/query.py; grep -n \"class Return\\b\" -A5 sqlglot/expressions/*.py; grep -n \"def return_sql\" -A6 sqlglot/generator.py", "description": "Trace table-macro RETURNS handling and remaining create_sql"}
[tool_result] sqlglot/parser.py:3333:        is_table = self._match(TokenType.TABLE)
sqlglot/parser.py:3335:        if is_table:
sqlglot/parser.py:3350:        return self.expression(exp.ReturnsProperty(this=value, is_table=is_table, null=null))
sqlglot/schema.py:540:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:564:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:601:            parts = [sel
…[3242 chars elided]…
ressions/query.py-886-class Tuple(Expression):
sqlglot/expressions/query.py-887-    arg_types = {"expressions": False}
3814:    def return_sql(self, expression: exp.Return) -> str:
3815-        return f"RETURN {self.sql(expression, 'this')}"
3816-
3817-    def reference_sql(self, expression: exp.Reference) -> str:
3818-        this = self.sql(expression, "this")
3819-        expressions = self.expressions(expression, flat=True)
3820-        expressions = f"({expressions})" if expressions else ""
[assistant] Table macros (`AS TABLE SELECT`) already round-trip through a `ReturnsProperty`. I'll check where that is produced and how it's generated, since the overload node has to carry the same thing.
[tool_use Bash] {"command": "sed -n 240,256p sqlglot/generator.py; echo ---; grep -n \"def _parse_function_properties\\|def _parse_heredoc\" -A12 sqlglot/parser.py | head -50; echo ---; sed -n 3328,3352p sqlglot/parser.py; echo ---; sed -n 380,400p sqlglot/expressions/properties.py", "description": "Read returns generation and function-property parsing"}
[tool_result]         exp.RemoteWithConnectionModelProperty: lambda self, e: (
            f"REMOTE WITH CONNECTION {self.sql(e, 'this')}"
        ),
        exp.ReturnsProperty: lambda self, e: (
            "RETURNS NULL ON NULL INPUT" if e.args.get("null") else self.naked_property(e)
        ),
        exp.RowAccessProperty: lambda *_: "ROW ACCESS",
        exp.SafeFunc: lambda self, e: f"SAFE.{self.sql(e, 'this')}",
        exp.SampleProperty: lambda self, e: f"SAMPLE BY {self.sql(e, 'this')}",
        ex
…[2543 chars elided]…
xp.Describe:
---

class RemoteWithConnectionModelProperty(Property):
    arg_types = {"this": True}


class ReturnsProperty(Property):
    arg_types = {"this": False, "is_table": False, "table": False, "null": False}


class StrictProperty(Property):
    arg_types = {}


class RowFormatProperty(Property):
    arg_types = {"this": True}


class RowFormatDelimitedProperty(Property):
    # https://cwiki.apache.org/confluence/display/hive/languagemanual+dml
    arg_types = {
        "fields": False,
[tool_use Bash] {"command": "grep -rn \"_parse_returns\\|\\\"RETURNS\\\"\" sqlglot/ | head; echo ---; grep -n \"class Parser\" -A5 sqlglot/dialects/duckdb.py | head; grep -n \"_parse_user_defined_function\\|_parse_create\\|FUNCTION\" sqlglot/dialects/duckdb.py | head -20", "description": "Find where RETURNS/table-macro parsing is wired"}
[tool_result] sqlglot/parser.py:1306:        "RETURNS": lambda self: self._parse_returns(),
sqlglot/parser.py:3330:    def _parse_returns(self) -> exp.ReturnsProperty:
sqlglot/parsers/tsql.py:621:    def _parse_returns(self) -> exp.ReturnsProperty:
sqlglot/parsers/tsql.py:623:        returns = super()._parse_returns()
sqlglot/expressions/properties.py:604:        "RETURNS": ReturnsProperty,
---
95:            "MACRO": TokenType.FUNCTION,
[tool_use Bash] {"command": "grep -rn \"is_table=True\\|ReturnsProperty\" sqlglot/ | grep -v \"^sqlglot/schema\" | head; echo ---; grep -n \"def _parse_statement\" -A25 sqlglot/parser.py | head -40", "description": "Find where ReturnsProperty with is_table is created"}
[tool_result] sqlglot/generator.py:243:        exp.ReturnsProperty: lambda self, e: (
sqlglot/generator.py:732:        exp.ReturnsProperty: exp.Properties.Location.POST_SCHEMA,
sqlglot/parser.py:3330:    def _parse_returns(self) -> exp.ReturnsProperty:
sqlglot/parser.py:3350:        return self.expression(exp.ReturnsProperty(this=value, is_table=is_table, null=null))
sqlglot/parsers/duckdb.py:241:                    exp.ReturnsProperty(
sqlglot/parsers/duckdb.py:243:                        is_table=True,
sqlg
…[985 chars elided]…
on = self._parse_expression()
2286-        expression = self._parse_set_operations(expression) if expression else self._parse_select()
2287-
2288-        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
2289-            expression = self._parse_pipe_syntax_query(expression)
2290-
2291-        return self._parse_query_modifiers(expression)
2292-
2293-    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2294-        start = self._prev
[assistant] The table-macro handling lives in the DuckDB parser. Let me read that section.
[tool_use Bash] {"command": "sed -n 200,275p sqlglot/parsers/duckdb.py; echo ---; ls sqlglot/parsers/ | head -50; echo; grep -n \"^from\\|^import\" sqlglot/parsers/duckdb.py", "description": "Read DuckDB parser table-macro logic"}
[tool_result]         "MAP": lambda self: self._parse_map(),
        "@": lambda self: exp.Abs(this=self._parse_bitwise()),
    }

    PLACEHOLDER_PARSERS = {
        **parser.Parser.PLACEHOLDER_PARSERS,
        TokenType.PARAMETER: lambda self: (
            self.expression(exp.Placeholder(this=self._prev.text))
            if self._match(TokenType.NUMBER) or self._match_set(self.ID_VAR_TOKENS)
            else None
        ),
    }

    TYPE_CONVERTERS = {
        # https://duckdb.org/docs/sql/data_types/nu
…[2664 chars elided]…
resto.py
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

1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
[assistant] I now have the full picture of the existing path. Before designing the change, I'll check the generator helpers I plan to use, whether DuckDB is importable here for verifying the output, and the baseline test state.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; grep -n \"    def wrap\\|    def expressions\\|    def no_identify\\|CREATE_FUNCTION_RETURN_AS\" sqlglot/generator.py | head; grep -n \"from .ddl\\|import \\*\" sqlglot/expressions/__init__.py | head -5; $P -c \"import duckdb; print('duckdb', duckdb.__version__)\"; echo ---; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3; git status --short | head", "description": "Check generator helpers, duckdb availability, baseline tests"}
[tool_result] 319:    CREATE_FUNCTION_RETURN_AS = True
1027:    def wrap(self, expression: exp.Expr | str) -> str:
1039:    def no_identify(self, func: t.Callable[..., str], *args, **kwargs) -> str:
1331:            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):
4510:    def expressions(
14:from sqlglot.expressions.core import *  # noqa: F401,F403
15:from sqlglot.expressions.datatypes import *  # noqa: F401,F403
16:from sqlglot.expressions.constraints import *  # noqa: F401,F403
17:from sqlglot.expressions.properties import *  # noqa: F401,F403
18:from sqlglot.expressions.query import *  # noqa: F401,F403
duckdb 1.5.6
---
........................ [ 54%]
....................     [100%]
44 passed, 600 subtests passed in 0.34s
[assistant] DuckDB 1.5.6 is installed, so I can check round-trips against the real engine. Baseline DuckDB tests pass (44). Let me confirm that DuckDB accepts the overload syntax and see the `expressions()` signature.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; sed -n 4510,4520p sqlglot/generator.py; grep -n \"ddl\" sqlglot/expressions/__init__.py; $P -I -c \"\nimport duckdb\nc=duckdb.connect()\nfor s in ['CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO add_x(a
…[413 chars elided]…
\nc.execute('CREATE MACRO m(a) AS a + 1, (a, b) AS TABLE SELECT a, b')\nprint(c.execute(\\\"select function_name, function_type, parameters, macro_definition, has_side_effects from duckdb_functions() where function_name='m'\\\").fetchall())\nprint(c.execute('select m(1)').fetchall(), c.execute('select * from m(1, 2)').fetchall())\n\"", "description": "Check DuckDB accepts overloaded macro syntax"}
[tool_result ERROR] Exit code 1
    def expressions(
        self,
        expression: exp.Expr | None = None,
        key: str | None = None,
        sqls: t.Collection[str | exp.Expr] | None = None,
        flat: bool = False,
        indent: bool = True,
        skip_first: bool = False,
        skip_last: bool = False,
        sep: str = ", ",
        prefix: str = "",
19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
Traceback (most recent call last):
  File "<string>", line 11, in <module>
_duckdb.P
…[211 chars elided]…
b, (a, b, c) AS a + b + c
ERR CREATE MACRO add_x(a) AS a + 1, (a, b) AS TABLE SELECT a, b -> Parser Error: syntax error at or near "TABLE"

LINE 1: CREATE MACRO add_x(a) AS a + 1, (a, b) AS TABLE SELECT a, b
                                   
ERR CREATE MACRO t(a) AS TABLE SELECT a, (b, c) AS a + b -> Parser Error: syntax error at or near "+"

LINE 1: CREATE MACRO t(a) AS TABLE SELECT a, (b, c) AS a + b
                                              
OK CREATE OR REPLACE MACRO f() AS 1, (a) AS a
[assistant] DuckDB rejects `AS TABLE` on a non-first overload, so table overloads need a different shape. I'll probe which table-overload forms DuckDB actually accepts before designing the parser.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport duckdb\ncases = [\n 'CREATE MACRO t1(a) AS TABLE SELECT a, (b) AS TABLE SELECT b',\n 'CREATE MACRO t2(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a+b',\n 'CREATE MACRO t3(a) AS TABLE SELECT a',\n 'CREATE MACRO t
…[183 chars elided]…
MACRO t7(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a+b',\n 'CREATE MACRO t8(a) AS a + 1, (a, b) AS (SELECT a + b)',\n 'CREATE MACRO t9(a) AS a + 1, (a, b) AS a * b',\n]\nfor s in cases:\n  c=duckdb.connect()\n  try: c.execute(s); print('OK ', s)\n  except Exception as e: print('ERR', s, '->', str(e).splitlines()[0][:120])\n\"", "description": "Probe DuckDB table-macro overload syntax variants"}
[tool_result] ERR CREATE MACRO t1(a) AS TABLE SELECT a, (b) AS TABLE SELECT b -> Parser Error: syntax error at or near "SELECT"
ERR CREATE MACRO t2(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a+b -> Parser Error: syntax error at or near "SELECT"
OK  CREATE MACRO t3(a) AS TABLE SELECT a
ERR CREATE MACRO t4(a) AS TABLE SELECT a, (a, b) AS a + b -> Parser Error: syntax error at or near "+"
ERR CREATE MACRO t5(a) AS a + 1, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "TABLE"
ERR CREATE MACRO t6(a) AS (SELECT a), (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "TABLE"
ERR CREATE MACRO t7(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a+b -> Parser Error: syntax error at or near "SELECT"
OK  CREATE MACRO t8(a) AS a + 1, (a, b) AS (SELECT a + b)
OK  CREATE MACRO t9(a) AS a + 1, (a, b) AS a * b
[assistant] DuckDB seems to reject `TABLE` on any overload after the first, and the first table body's select list swallows the comma. I'll test a few more shapes, including parenthesized table bodies.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport duckdb\ncases = [\n 'CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a+b)',\n 'CREATE MACRO u2(a) AS a + 1, (a, b) AS TABLE (SELECT a+b)',\n 'CREATE MACRO u3(a) AS TABLE SELECT a FROM range(3) t(a
…[175 chars elided]…
a) AS TABLE SELECT a FROM range(3) t(a)',\n 'CREATE MACRO u7(a) AS TABLE SELECT a FROM range(3) t(a) LIMIT 1, (a, b) AS a + b',\n 'CREATE MACRO u8(a) AS TABLE (SELECT a) ',\n]\nfor s in cases:\n  c=duckdb.connect()\n  try: c.execute(s); print('OK ', s)\n  except Exception as e: print('ERR', s, '->', str(e).splitlines()[0][:120])\n\"", "description": "Probe more DuckDB table macro overload shapes"}
[tool_result] OK  CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a+b)
ERR CREATE MACRO u2(a) AS a + 1, (a, b) AS TABLE (SELECT a+b) -> Parser Error: syntax error at or near "TABLE"
ERR CREATE MACRO u3(a) AS TABLE SELECT a FROM range(3) t(a), (a, b) AS TABLE SELECT a -> Parser Error: syntax error at or near ","
ERR CREATE MACRO u4(a) AS TABLE SELECT a, (a, b) AS (SELECT 1) -> Parser Error: syntax error at or near "("
OK  CREATE MACRO u5(a) AS (SELECT a), (a, b) AS (SELECT a+b)
OK  CREATE MACRO u6(a) AS TABLE SELECT a FROM range(3) t(a)
ERR CREATE MACRO u7(a) AS TABLE SELECT a FROM range(3) t(a) LIMIT 1, (a, b) AS a + b -> Parser Error: errhint NOT IMPLEMENTED
OK  CREATE MACRO u8(a) AS TABLE (SELECT a)
[assistant] Findings so far:
- DuckDB accepts `AS TABLE (SELECT …)` in overloads (`u1`), but not an unparenthesized `TABLE SELECT …` followed by a comma. The parser needs to handle the parenthesized form.
- Scalar and table overloads can't be mixed. Table-ness is per macro, so a per-overload flag is still the right representation.

Next I need to see how `_parse_create` builds the final `Create`, and check the existing parser feature flags, so the DuckDB-only grammar can be gated.
[tool_use Bash] {"command": "grep -n \"return self.expression(\" sqlglot/parser.py | awk -F: '$1>2470 && $1<2700' | head -3; sed -n 2640,2680p sqlglot/parser.py | grep -n \"exp.Create\\|properties\" ; grep -n \"exp.Create(\" -A20 sqlglot/parser.py | sed -n 1,30p; echo ---; grep -n \"^    [A-Z_]* = \\(True\\|False\\)$\" sqlglot/parser.py | head -20; grep -n \"SUPPORTS_IMPLICIT_UNNEST\\|_OVERLOAD\" sqlglot/parser.py sqlglot/dialects/duckdb.py | head", "description": "Inspect Create construction and parser feature flags"}
[tool_result] 2584:        return self.expression(
2585:            exp.Create(
2586-                this=this,
2587-                kind=self.dialect.CREATABLE_KIND_MAPPING.get(create_kind_text) or create_kind_text,
2588-                replace=replace,
2589-                refresh=refresh,
2590-                unique=unique,
2591-                expression=expression,
2592-                exists=exists,
2593-                properties=properties,
2594-                indexes=indexes,
2595-                no
…[39 chars elided]…
-                begin=begin,
2597-                clone=clone,
2598-                concurrently=concurrently,
2599-                clustered=clustered,
2600-            )
2601-        )
2602-
2603-    def _parse_sequence_properties(self) -> exp.SequenceProperties | None:
2604-        seq = exp.SequenceProperties()
2605-
---
sqlglot/parser.py:1794:    SUPPORTS_IMPLICIT_UNNEST: t.ClassVar = False
sqlglot/parser.py:4151:        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
[assistant] `_parse_create` passes `properties` straight into `Create`, so I can take the table marker out of it safely. Let me confirm three helper details before editing: `Expression.pop`, the `expressions()` separator behavior, and where the parser flag block is.
[tool_use Bash] {"command": "grep -n \"    def pop(\" -A3 sqlglot/expressions/core.py | head -6; sed -n 4520,4545p sqlglot/generator.py; sed -n 1788,1797p sqlglot/parser.py; grep -n \"SUPPORTS_IMPLICIT_UNNEST\\|class Parser\" sqlglot/parsers/duckdb.py sqlglot/dialects/duckdb.py | head -4", "description": "Confirm pop, expressions() separator, parser flag location"}
[tool_result] 484:    def pop(self: E) -> E:
485-        """
486-        Remove this expression from its AST.
487-
--
1276:    def pop(self: E) -> E:
        prefix: str = "",
        dynamic: bool = False,
        new_line: bool = False,
    ) -> str:
        expressions = expression.args.get(key or "expressions") if expression else sqls

        if not expressions:
            return ""

        if flat:
            return sep.join(sql for sql in (self.sql(e) for e in expressions) if sql)

        num_sqls 
…[432 chars elided]…
         else:

    # Whether or not a VALUES keyword needs to be followed by '(' to form a VALUES clause.
    # If this is True and '(' is not found, the keyword will be treated as an identifier
    VALUES_FOLLOWED_BY_PAREN: t.ClassVar = True

    # Whether implicit unnesting is supported, e.g. SELECT 1 FROM y.z AS z, z.a (Redshift)
    SUPPORTS_IMPLICIT_UNNEST: t.ClassVar = False

    # Whether or not interval spans are supported, INTERVAL 1 YEAR TO MONTHS
    INTERVAL_SPANS: t.ClassVar = True
[assistant] I have what I need. Here's the plan:

- **Expressions** (`ddl.py`): `MacroOverload` (one per overload: params, body, table flag) and `MacroOverloads` (the list).
- **Parser**: when a `CREATE MACRO` has a comma after its first body, collect the remaining overloads into `MacroOverloads`. Gate this behind a parser flag that only DuckDB enables, since the comma grammar is DuckDB-specific.
- **Generator**: emit overloads without the extra `AS` that `create_sql` would otherwise add.

Starting with the expression classes:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True, \"table\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Next, the parser flag and the overload-parsing logic in `_parse_create`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    SUPPORTS_IMPLICIT_UNNEST: t.ClassVar = False\n", "new_string": "    SUPPORTS_IMPLICIT_UNNEST: t.ClassVar = False\n\n    # Whether overloaded macros are supported, e.g. CREATE MACRO m(a) AS a, (a, b) AS a + b (DuckDB)\n    SUPPORTS_MACRO_OVERLOADS: t.ClassVar = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                        expression = (\n                            self._parse_user_defined_function_expression()\n                            if create_token_type == TokenType.FUNCTION\n                            else
…[592 chars elided]…
e.FUNCTION\n                        and isinstance(this, exp.UserDefinedFunction)\n                        and self._match(TokenType.COMMA, advance=False)\n                    ):\n                        this, expression = self._parse_macro_overloads(this, expression, properties)\n\n                    if return_:\n                        expression = self.expression(exp.Return(this=expression))"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the helper that collects the overloads. It goes next to `_parse_user_defined_function`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:", "new_string": "    def _parse_macro_overloads(\n        self,\n        this: exp.UserDefinedFunction,\n        expression: e
…[1199 chars elided]…
d(\n                self.expression(\n                    exp.MacroOverload(expressions=params, expression=body, table=table)\n                )\n            )\n\n        return exp.UserDefinedFunction(this=this.this), self.expression(\n            exp.MacroOverloads(expressions=overloads)\n        )\n\n    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] One mypy concern: `returns.pop()` is reached with `returns` typed as Optional. I'll narrow it explicitly:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        table = bool(returns and returns.args.get(\"is_table\"))\n        if table:\n            returns.pop()", "new_string": "        table = bool(returns and returns.args.get(\"is_table\"))\n        if returns and table:\n            returns.pop()"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the DuckDB parser enables the flag. Let me find its class header:
[tool_use Bash] {"command": "grep -n \"^class \\|    [A-Z_]*: t.ClassVar\\|    [A-Z_]* = \" sqlglot/parsers/duckdb.py | head -20", "description": "Find DuckDB parser class and flag definitions"}
[tool_result] 74:class DuckDBParser(parser.Parser):
75:    MAP_KEYS_ARE_ARBITRARY_EXPRESSIONS = True
77:    NO_PAREN_FUNCTIONS = {
85:    BITWISE = {k: v for k, v in parser.Parser.BITWISE.items() if k != TokenType.CARET}
87:    RANGE_PARSERS = {
94:    EXPONENT = {
100:    FUNCTIONS_WITH_ALIASED_ARGS = {*parser.Parser.FUNCTIONS_WITH_ALIASED_ARGS, "STRUCT_PACK"}
102:    SHOW_PARSERS = {
107:    FUNCTIONS = {
191:    FUNCTION_PARSERS = {
198:    NO_PAREN_FUNCTION_PARSERS = {
204:    PLACEHOLDER_PARSERS = {
213:    TYPE_CONVERTERS = {
220:    STATEMENT_PARSERS = {
229:    SET_PARSERS = {
234:    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
235:    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "class DuckDBParser(parser.Parser):\n    MAP_KEYS_ARE_ARBITRARY_EXPRESSIONS = True\n", "new_string": "class DuckDBParser(parser.Parser):\n    MAP_KEYS_ARE_ARBITRARY_EXPRESSIONS = True\n    SUPPORTS_MACRO_OVERLOADS = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now the generator. First the `create_sql` branch that would otherwise add a second `AS`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):", "new_string": "            if not isinstance(expression.expression, exp.MacroOverloads) and (\n                self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def joinhint_sql(", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def ma
…[44 chars elided]…
verload) -> str:\n        params = self.wrap(self.no_identify(self.expressions, expression))\n        table = \"TABLE \" if expression.args.get(\"table\") else \"\"\n        return f\"{params} AS {table}{self.sql(expression, 'expression')}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, sep=\",\")\n\n    def joinhint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll check the output against the issue's examples and the table and scalar variants, plus the existing single-overload cases:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\ncases = [\n 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''',\n 'CREATE MACRO add_x(a) AS a + 1, (a, b) AS a * b',\n 'CREATE MACRO
…[299 chars elided]…
'OK ', out)\n  except Exception as e: print('ERR', str(e)[:200])\nprint(sqlglot.parse_one('CREATE MACRO add_x(a) AS a + 1, (a, b) AS TABLE (SELECT a + b)', read='duckdb').sql('duckdb', pretty=True))\nprint(repr(sqlglot.parse_one('CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb'))[:900])\n\"", "description": "Run round-trip checks on overloaded macro examples"}
[tool_result] 'CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u5(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
OK  CREATE OR REPLACE MACRO add_2(a, b) AS a + b
OK  CREATE MACRO add_x (a, b) AS a + b,(a, b, c) AS a + b + c
OK  CREATE MACRO add_x (a) AS a + 1,(a, b) AS a * b
OK  CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
OK  CREATE MACRO u5(a) AS (SELECT a), (a, b) AS (SELECT a + b)
OK  CREATE MACRO t(a) AS TABLE SELECT a
OK  CREATE MACRO f () AS 1,(a) AS a
CREATE MACRO add_x
  (
      a
  ) AS a + 1,
  (
      a,
      b
  ) AS TABLE (
    SELECT
      a + b
  )
Command(this=CREATE, expression=MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b))
[assistant] Two problems:

1. The separator is `,(` with no space. The `sep=","` I passed is wrong; the default `", "` is right.
2. Parenthesized table and subquery bodies fall back to `Command`, so the parser stops early there. I'll find out why.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\np = DuckDB().parser()\nfor s in ['CREATE MACRO u8(a) AS TABLE (SELECT a)', 'CREATE MACRO u5(a) AS (SELECT a), (a, b) AS (SELECT a + b)', 'CREATE MACRO u5(a) AS (SELECT a)', 'SELECT (SELECT a), 1']:\n  try:\n    print(s, '=>', repr(sqlglot.parse_one(s, read='duckdb'))[:300].replace(chr(10),' '))\n  except Exception as e: print('ERR', s, str(e)[:200])\n\"", "description": "Narrow down subquery body parse failure"}
[tool_result] 'CREATE MACRO u5(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO u8(a) AS TABLE (SELECT a) => Create(   this=UserDefinedFunction(     this=Table(       this=Identifier(this=u8, quoted=False)),     expressions=[       Identifier(this=a, quoted=False)],     wrapped=True),   kind=MACRO,   replace=False,   refresh=False,   unique=False,   expression=Subquery(     this=Select(       expressions=[
CREATE MACRO u5(a) AS (SELE
…[171 chars elided]…
UserDefinedFunction(     this=Table(       this=Identifier(this=u5, quoted=False)),     expressions=[       Identifier(this=a, quoted=False)],     wrapped=True),   kind=MACRO,   replace=False,   refresh=False,   unique=False,   expression=Subquery(     this=Select(       expressions=[
SELECT (SELECT a), 1 => Select(   expressions=[     Subquery(       this=Select(         expressions=[           Column(             this=Identifier(this=a, quoted=False))])),     Literal(this=1, is_string=False)])
[assistant] The single parenthesized body parses. The failure appears only when the body starts with `(` and a comma follows, so the body expression parser may be swallowing the comma. Let me check what the body parse returns in that case:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.dialects.duckdb import DuckDB\np = DuckDB().parser()\nfor toks in ['(a) , (b)', '(SELECT a), (a, b)']:\n  sql = toks\n  ast = p.parse(sqlglot.tokenize(sql, read='duckdb
…[276 chars elided]…
function_expression()\n  print('  body =>', repr(node)[:200].replace(chr(10),' '), '| next token:', pp._curr)\nfor s in ['CREATE MACRO f(a) AS (a), (a, b) AS (a + b)', 'CREATE MACRO f(a) AS (a) , (a, b) AS a + b']:\n  print(s, '=>', repr(sqlglot.parse_one(s, read='duckdb'))[:120].replace(chr(10),' '))\n\" 2>&1 | head -40", "description": "Inspect what body parse consumes for parenthesized bodies"}
[tool_result] (a) , (b)
  body => None | next token: <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
(SELECT a), (a, b)
  body => None | next token: <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
CREATE MACRO f(a) AS (a), (a, b) AS (a + b) => Create(   this=UserDefinedFunction(     this=Table(       this=Identifier(this=f, quoted=False))),   kind=MACRO,   repla
CREATE MACRO f(a) AS (a) , (a, b) AS a + b => Create(   this=UserDefinedFunction(     this=Table(       this=Identifier(this=f, quoted=False))),   kind=MACRO,   repla
[assistant] My debug harness was wrong (the body came back `None`), but it shows that parenthesized scalar bodies work. The failing case is specifically a subquery body. I'll test the two halves separately:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['CREATE MACRO u5(a) AS (SELECT a), (a, b) AS a + b', 'CREATE MACRO u5(a) AS a + 1, (a, b) AS (SELECT a + b)', 'CREATE MACRO u5(a) AS (SELECT a) , 1', 'SELECT (SELECT a), (b)']:\n  try:\n    print(s, '=>', sqlglot.parse_one(s, read='duckdb').sql('duckdb'))\n  except Exception as e: print('ERR', s, str(e)[:120])\n\" 2>&1 | head -20", "description": "Isolate which subquery-body combination fails"}
[tool_result] 'CREATE MACRO u5(a) AS (SELECT a), (a, b) AS a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u5(a) AS (SELECT a) , 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO u5(a) AS (SELECT a), (a, b) AS a + b => CREATE MACRO u5(a) AS (SELECT a), (a, b) AS a + b
CREATE MACRO u5(a) AS a + 1, (a, b) AS (SELECT a + b) => CREATE MACRO u5 (a) AS a + 1,(a, b) AS (SELECT a + b)
CREATE MACRO u5(a) AS (SELECT a) , 1 => CREATE MACRO u5(a) AS (SELECT a) , 1
SELECT (SELECT a), (b) => SELECT (SELECT a), (b)
[assistant] A parenthesized subquery body followed by a comma fails, but a scalar body followed by a subquery overload works. I'll find where the "unsupported syntax" fallback is triggered and trace the real exception:
[tool_use Bash] {"command": "grep -rn \"contains unsupported syntax\" sqlglot/*.py | head -3; P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfrom sqlglot.dialects.duckdb import DuckDB\nd = DuckDB()\nfor s in ['CREATE MACRO u5(a) AS (SELECT a) 
…[47 chars elided]…
 AS a + b']:\n  try:\n    print(repr(d.parse(s)[0])[:150].replace(chr(10),' '))\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n  p = d.parser(error_level=ErrorLevel.IMMEDIATE)\n  try: print(p.parse(d.tokenize(s))[0].sql('duckdb'))\n  except Exception as e: print('ERR2', type(e).__name__, str(e)[:300])\n\"", "description": "Trace parse errors for failing macro body inputs"}
[tool_result] sqlglot/parser.py:2170:            f"'{sql}' contains unsupported syntax. Falling back to parsing as a 'Command'."
'CREATE MACRO u5(a) AS (SELECT a) , 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u5(a) AS (SELECT a), (a, b) AS a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=CREATE, expression=MACRO u5(a) AS (SELECT a) , 1)
ERR2 TypeError Parser.parse() missing 1 required positional argument: 'sql'
Command(this=CREATE, expression=MACRO u5(a) AS (SELECT a), (a, b) AS a + b)
ERR2 TypeError Parser.parse() missing 1 required positional argument: 'sql'
[tool_use Bash] {"command": "sed -n 2150,2175p sqlglot/parser.py", "description": "Read the parse fallback that triggers the Command result"}
[tool_result]                     chunks.append([token])

                if i < total - 1:
                    chunks.append([])
            else:
                chunks[-1].append(token)

        self._chunks = chunks

        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)

    def _warn_unsupported(self) -> None:
        if self._tokens_size <= 1:
            return

        # We use _find_sql because self.sql may comprise multiple chunks, and we're only
        # interested in emitting a warning for the one being currently processed.
        sql = self._find_sql(self._tokens[0], self._tokens[-1])[: self.error_message_context]

        logger.warning(
            f"'{sql}' contains unsupported syntax. Falling back to parsing as a 'Command'."
        )

    def _parse_command(self) -> exp.Command:
        self._warn_unsupported()
        comments = self._prev_comments
[assistant] The fallback is `_parse_command` → `_warn_unsupported`. I'll print a stack trace from that point to see which branch triggers it:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport traceback, sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._warn_unsupported\ndef spy(self):\n    traceback.print_stack(limit=7)\n    orig(self)\nParser._warn_unsupported = spy\nsqlglot.parse_one('CREATE MACRO u5(a) AS (SELECT a) , 1', read='duckdb')\n\" 2>&1 | grep -v \"^    \" | head -30", "description": "Print stack trace for the command fallback"}
[tool_result]   File "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2159, in _parse
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2126, in _parse_batch_statements
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2278, in _parse_statement
  
…[130 chars elided]…
y", line 1090, in <lambda>
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2592, in _parse_create
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 9246, in _parse_as_command
  File "<string>", line 6, in spy
'CREATE MACRO u5(a) AS (SELECT a) , 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
[tool_use Bash] {"command": "sed -n 2578,2595p sqlglot/parser.py", "description": "Read the code that falls back to command in _parse_create"}
[tool_result]                 if self._match_text_seq("WITH", "NO", "SCHEMA", "BINDING"):
                    no_schema_binding = True
            elif create_token_type in (TokenType.SINK, TokenType.SOURCE):
                extend_props(self._parse_properties())

            shallow = self._match_text_seq("SHALLOW")

            if self._match_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = create_token.text.upper()
        return self.expression(
[assistant] The trailing-token check runs after the body parse, so the body parser must be consuming the comma when the body is a subquery. I'll confirm by inspecting the token position right after the body parse:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._parse_user_defined_function_expression\ndef spy(self):\n    r = orig(self)\n    print('body:', repr(r)[:160].replace(chr(10),' '), '| curr:', self._curr.text if self._curr else None)\n    return r\nParser._parse_user_defined_function_expression = spy\nsqlglot.parse_one('CREATE MACRO u5(a) AS (SELECT a) , 1', read='duckdb')\n\" 2>&1 | head -12", "description": "Spy on macro body parse to see consumed tokens"}
[tool_result] 'CREATE MACRO u5(a) AS (SELECT a) , 1' contains unsupported syntax. Falling back to parsing as a 'Command'.
body: Subquery(   this=Select(     expressions=[       Column(         this=Identifier(this=a, quoted=False))])) | curr: 1
[assistant] Confirmed: after the subquery body is parsed, the current token is `1`, so `_parse_statement` consumed the `, 1` as an implicit comma join on the subquery. Let me see where that happens in the query-modifier code:
[tool_use Bash] {"command": "grep -n \"def _parse_query_modifiers\" -A30 sqlglot/parser.py | head -50; grep -n \"def _parse_join(\" -A30 sqlglot/parser.py | grep -n \"COMMA\" ", "description": "Read query modifier and comma-join parsing"}
[tool_result] 4122:    def _parse_query_modifiers(self, this: E) -> E: ...
4123-
4124-    @t.overload
4125:    def _parse_query_modifiers(self, this: None) -> None: ...
4126-
4127:    def _parse_query_modifiers(self, this):
4128-        if isinstance(this, self.MODIFIABLES):
4129-            for join in self._parse_joins():
4130-                this.append("joins", join)
4131-            for lateral in iter(self._parse_lateral, None):
4132-                this.append("laterals", lateral)
4133-
4134-          
…[780 chars elided]…
fset = expression.args.get("offset")
4150-                            expression.set("offset", None)
4151-
4152-                            if offset:
4153-                                offset = exp.Offset(expression=offset)
4154-                                this.set("offset", offset)
4155-
4156-                                limit_by_expressions = expression.expressions
4157-                                expression.set("expressions", None)
7:4419-        if self._match(TokenType.COMMA):
[assistant] The comma join comes from `_parse_statement`, which ends by applying query modifiers (including comma joins) to whatever it parsed. A macro body can't legitimately end in a comma join, so the cleanest fix is for the DuckDB body parser to skip the statement-level modifiers. I'll test that idea with a monkeypatch before committing to it:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.parser import Parser\ndef body(self):\n    expression = self._parse_expression()\n    return self._parse_set_operations(expression) if expression else self._parse_selec
…[278 chars elided]…
BLE SELECT a FROM x WHERE a > 1 ORDER BY a LIMIT 2',\n 'CREATE MACRO add_x(a) AS a + 1, (a, b) AS a * b',\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n]\nfor s in cases:\n  try: print('OK ', sqlglot.parse_one(s, read='duckdb').sql('duckdb'))\n  except Exception as e: print('ERR', str(e)[:150])\n\" 2>&1", "description": "Test expression-based macro body parsing via monkeypatch"}
[tool_result] OK  CREATE MACRO u5 (a) AS (SELECT a),(a, b) AS (SELECT a + b)
ERR Expected ( to start a macro overload. Line 1, Col: 36.
  CREATE MACRO u5(a) AS (SELECT a) , [4m1[0m
OK  CREATE MACRO u1 (a) AS TABLE (SELECT a),(a, b) AS TABLE (SELECT a + b)
OK  CREATE MACRO t(a) AS TABLE SELECT a FROM x WHERE a > 1 ORDER BY a LIMIT 2
OK  CREATE MACRO add_x (a) AS a + 1,(a, b) AS a * b
OK  CREATE MACRO add_x (a, b) AS a + b,(a, b, c) AS a + b + c
[assistant] That works: the subquery cases and the table-overload cases now parse, and the `, 1` case still errors, which is correct for invalid input. The change is limited to DuckDB's body parser, so I'll put it in `parsers/duckdb.py` next to the existing `_parse_function_properties` override.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "        return super()._parse_function_properties()\n\n    def _parse_lambda(", "new_string": "        return super()._parse_function_properties()\n\n    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        # Parse without statement-level query modifiers, so a comma after a subquery body\n        # separates macro overloads instead of being consumed as an implicit join\n        expression = self._parse_expression()\n        return self._parse_set_operations(expression) if expression else self._parse_select()\n\n    def _parse_lambda("}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now the separator fix in the generator (default `", "` instead of `","`):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return self.expressions(expression, sep=\",\")", "new_string": "        return self.expressions(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-run the round trips and check that DuckDB accepts the generated SQL and that the overloads resolve correctly at runtime:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot, duckdb\ncases = [\n 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''',\n 'CREATE MACRO add_x(a) AS a + 1, (a, b) AS a * b',\n 'C
…[731 chars elided]…
 read='duckdb').sql('duckdb'))\nprint(c.execute('select add_x(1,2), add_x(1,2,3)').fetchall())\nc.execute(sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb').sql('duckdb'))\nprint(c.execute('select * from t(5)').fetchall(), c.execute('select * from t(5, 6)').fetchall())\n\" 2>&1", "description": "Re-run round trips and verify in DuckDB engine"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` drops the working directory from the import path, so sqlglot isn't found. That's fine to drop here, since this is the repo's own code and not an untrusted download.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot, duckdb\ncases = [\n 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''',\n 'CREATE MACRO add_x(a) AS a + 1, (a, b) AS a * b',\n 'CREA
…[710 chars elided]…
 read='duckdb').sql('duckdb'))\nprint(c.execute('select add_x(1,2), add_x(1,2,3)').fetchall())\nc.execute(sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb').sql('duckdb'))\nprint(c.execute('select * from t(5)').fetchall(), c.execute('select * from t(5, 6)').fetchall())\n\" 2>&1", "description": "Re-run round trips and verify in DuckDB engine"}
[tool_result] CREATE OR REPLACE MACRO add_2(a, b) AS a + b | duckdb-src OK | duckdb-out OK
CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c | duckdb-src OK | duckdb-out OK
CREATE MACRO add_x (a) AS a + 1, (a, b) AS a * b | duckdb-src OK | duckdb-out OK
CREATE MACRO u1 (a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b) | duckdb-src OK | duckdb-out OK
CREATE MACRO u5 (a) AS (SELECT a), (a, b) AS (SELECT a + b) | duckdb-src OK | duckdb-out OK
CREATE MACRO t(a) AS TABLE SELECT a | duckdb-src OK | duckdb-out OK
CREATE MACRO f () AS 1, (a) AS a | duckdb-src OK | duckdb-out OK
[(3, 6)]
[(5,)] [(11,)]
[assistant] Everything round-trips, and DuckDB executes the overloads correctly: `add_x(1,2)=3` and `add_x(1,2,3)=6`, and the table overloads return the right rows.

One cosmetic problem remains. `create_sql` always inserts a separator after the name, so overloaded output becomes `add_x (a, b)` and `f () AS 1`, while single-overload output is `add_2(a, b)`. I'll check how the single form renders in pretty mode, then decide whether to drop that separator for overloads.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE MACRO f(a, b) AS a + b', read='duckdb').sql('duckdb', pretty=True)))\nprint(repr(sqlglot.parse_one('CREATE MACRO f(a, b) AS a + b', read='duckdb').sql('duckdb')))\nprint(repr(sqlglot.parse_one('CREATE MACRO f() AS 1', read='duckdb').sql('duckdb')))\nprint(repr(sqlglot.parse_one('CREATE MACRO f(a) AS a + 1, (a, b) AS a * b', read='duckdb').sql('duckdb', pretty=True)))\n\"", "description": "Compare single-overload and pretty output formats"}
[tool_result] 'CREATE MACRO f(\n    a,\n    b\n) AS\na + b'
'CREATE MACRO f(a, b) AS a + b'
'CREATE MACRO f() AS 1'
'CREATE MACRO f\n  (\n      a\n  ) AS a + 1,\n  (\n      a,\n      b\n  ) AS a * b'
[assistant] Single-overload pretty output uses the same wrapped parameter style as my per-overload output, so that part is consistent. The only real mismatch is the space after the name. I'll drop the separator in `create_sql` for overloaded macros so the first overload attaches directly to the name:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        if expression_sql:\n            expression_sql = f\"{begin}{self.sep()}{expression_sql}\"\n\n            if not isinstance(expression.expression, exp.MacroOverloads) and (\n                self.CREATE_FUNCTION
…[178 chars elided]…
er lists, so they attach directly to the name\n            is_macro_overloads = isinstance(expression.expression, exp.MacroOverloads)\n            expression_sql = f\"{begin}{'' if is_macro_overloads else self.sep()}{expression_sql}\"\n\n            if not is_macro_overloads and (\n                self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['CREATE OR REPLACE MACRO add_2(a, b) AS a + b', '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''', 'CREATE MACRO f() AS 1, (a) AS a', 'CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)']:\n  e = sqlglot.parse_one(s, read='duckdb')\n  print(e.sql('duckdb')); print(e.sql('duckdb', pretty=True)); print('--')\n\"", "description": "Check overloaded macro output in plain and pretty mode"}
[tool_result] CREATE OR REPLACE MACRO add_2(a, b) AS a + b
CREATE OR REPLACE MACRO add_2(
    a,
    b
) AS
a + b
--
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE MACRO add_x  (
      a,
      b
  ) AS a + b,
  (
      a,
      b,
      c
  ) AS a + b + c
--
CREATE MACRO f() AS 1, (a) AS a
CREATE MACRO f  () AS 1,
  (
      a
  ) AS a
--
CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
CREATE MACRO u1  (
      a
  ) AS TABLE (
    SELECT
      a
  ),
  (
      a,
      b
  ) AS TABLE (
    SELECT
      a + b
  )
--
[assistant] Plain output is clean now. Pretty output is noisy because the parameter lists are wrapped and indented per overload. Let me look at `wrap` before choosing a fix:
[tool_use Bash] {"command": "sed -n 1027,1040p sqlglot/generator.py", "description": "Read the generator wrap helper"}
[tool_result]     def wrap(self, expression: exp.Expr | str) -> str:
        this_sql = (
            self.sql(expression)
            if isinstance(expression, exp.UNWRAPPED_QUERIES)
            else self.sql(expression, "this")
        )
        if not this_sql:
            return "()"

        this_sql = self.indent(this_sql, level=1, pad=0)
        return f"({self.sep('')}{this_sql}{self.seg(')', sep='')}"

    def no_identify(self, func: t.Callable[..., str], *args, **kwargs) -> str:
        original = self.identify
[assistant] `wrap` is pretty-aware, which is what makes each overload break across lines. Flat parameter lists read better for overload headers, so I'll render them flat in both modes:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        params = self.wrap(self.no_identify(self.expressions, expression))\n        table = \"TABLE \" if expression.args.get(\"table\") else \"\
…[248 chars elided]…
 expression: exp.MacroOverload) -> str:\n        params = self.no_identify(self.expressions, expression, flat=True)\n        table = \"TABLE \" if expression.args.get(\"table\") else \"\"\n        return f\"({params}) AS {table}{self.sql(expression, 'expression')}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['CREATE OR REPLACE MACRO add_2(a, b) AS a + b', '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''', 'CREATE MACRO f() AS 1, (a) AS a', 'CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)']:\n  e = sqlglot.parse_one(s, read='duckdb')\n  print(e.sql('duckdb')); print(e.sql('duckdb', pretty=True)); print('--')\n\"", "description": "Verify flat overload output in both modes"}
[tool_result] CREATE OR REPLACE MACRO add_2(a, b) AS a + b
CREATE OR REPLACE MACRO add_2(
    a,
    b
) AS
a + b
--
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
--
CREATE MACRO f() AS 1, (a) AS a
CREATE MACRO f() AS 1, (a) AS a
--
CREATE MACRO u1(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
CREATE MACRO u1(a) AS TABLE (
  SELECT
    a
), (a, b) AS TABLE (
  SELECT
    a + b
)
--
[assistant] The output now matches single-overload style. Next, tests. I'll check whether the existing suite runs DuckDB itself anywhere, since the project asks that dialect tests be verified in the target database:
[tool_use Bash] {"command": "grep -rln \"import duckdb\" tests/ | head; grep -n \"^import\\|^from\" tests/dialects/test_duckdb.py | head", "description": "Check whether tests execute against duckdb"}
[tool_result] tests/test_optimizer.py
tests/test_executor.py
1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
[assistant] The dialect tests don't import DuckDB, so I'll follow the existing pattern (identity round-trips in `test_udf`) and verify against DuckDB manually, as I did above.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "                self.validate_identity(\n                    f\"CREATE {keyword} my_table_function(a, b) AS TABLE SELECT x, y FROM (VALUES (a, b)) AS tbl(x, y)\"\n                ).assert_is(exp.Create)\n\n        self.validate_all(", "new_string": "                self.validate_identity(\n                    f\"CREATE {keyword} my_table_function(a, b) AS TABLE SELECT x, y FROM (VALUES (a, b)) AS tbl(x, y)\"\n                ).assert_is(exp.Create)\n\n        self.validate_all("}
[tool_result ERROR] <tool_use_error>No changes to make: old_string and new_string are exactly the same.</tool_use_error>
[assistant] That edit was a no-op by mistake. I'll add a dedicated test method just before `test_bitwise_agg`, instead of growing `test_udf`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):\n        self.validate_all(", "new_string": "    def test_macro_overloads(self):\n        self.validate_identity(\"CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c\")\
…[563 chars elided]…
tEqual(len(overloads), 2)\n        self.assertEqual(len(overloads[1].expressions), 3)\n\n        macro = parse_one(\n            \"CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)\", read=\"duckdb\"\n        )\n        self.assertTrue(all(overload.args.get(\"table\") for overload in macro.expression.expressions))\n\n    def test_bitwise_agg(self):\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now I'll run the DuckDB dialect tests, then the full suite using the project's test command from the harness notes:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -30", "description": "Run DuckDB dialect tests"}
[tool_result] ........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.24s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; timeout 550 $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run the full project test suite", "timeout": 570000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run the full project test suite", "timeout": 600000}
[tool_result] .................................................................................................................................................................................................................................................................................. [ 24%]
.................................... [ 27%]
............................................................................................................................................ [ 40%]
..........................
…[266 chars elided]…
......................................................... [ 69%]
....................................................................................................................................................................................... [ 85%]
................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 56.98s
[assistant] The full suite passes: 1114 tests, 0 failures. Next, the project's style checks, since the repo runs ruff and mypy in pre-commit:
[tool_use Bash] {"command": "grep -n \"^style\" -A8 Makefile; P=<work>/env-sqlglot/bin/python; $P -m ruff --version 2>&1; $P -m mypy --version 2>&1 | head -1", "description": "Check style target and available linters"}
[tool_result] 96:style:
97-	pre-commit run --all-files
98-	@if [ -f sqlglot-integration-tests/Makefile ]; then \
99-		MYPYPATH=$(abspath .) $(MAKE) -C sqlglot-integration-tests style && \
100-		$(MAKE) -C sqlglot-integration-tests check-submodule; \
101-	fi
102-
103-check: style test testc
104-
ruff 0.15.6
mypy 2.4.0 (compiled: yes)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; FILES=\"sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py\"; $P -m ruff format --check $FILES; $P -m ruff check $FILES; git stash list >/dev/null; $P -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -15", "description": "Run ruff format, ruff check, and mypy on changed files"}
[tool_result] error: Failed to format sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
E902 No such file or directory (os error 2)
--> sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
Success: no issues found in 4 source files
[assistant] The shell is zsh, which doesn't word-split the unquoted `$FILES`, so ruff got one bogus path. mypy passed. I'll rerun ruff with explicit arguments:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format --check sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py; $P -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py", "description": "Run ruff format and lint checks on changed files"}
[tool_result] Would reformat: sqlglot/parser.py
Would reformat: tests/dialects/test_duckdb.py
2 files would be reformatted, 3 files already formatted
All checks passed!
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format --diff sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | head -60", "description": "Preview the formatting changes ruff wants"}
[tool_result] --- sqlglot/parser.py
+++ sqlglot/parser.py
@@ -7053,9 +7053,7 @@
 
         overloads = [
             self.expression(
-                exp.MacroOverload(
-                    expressions=this.expressions, expression=expression, table=table
-                )
+                exp.MacroOverload(expressions=this.expressions, expression=expression, table=table)
             )
         ]
 
@@ -7072,9 +7070,7 @@
             table = bool(self._match(TokenType.TABLE))
             body = self._parse
…[964 chars elided]…
n(overloads), 2)
@@ -2627,7 +2625,9 @@
         macro = parse_one(
             "CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)", read="duckdb"
         )
-        self.assertTrue(all(overload.args.get("table") for overload in macro.expression.expressions))
+        self.assertTrue(
+            all(overload.args.get("table") for overload in macro.expression.expressions)
+        )
 
     def test_bitwise_agg(self):
         self.validate_all(

2 files would be reformatted
[assistant] Those are only line-wrapping changes in my own code. I'll apply the formatter to the two files, then re-run the affected tests and the full diff review:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m ruff format sqlglot/parser.py tests/dialects/test_duckdb.py && $P -m ruff format --check sqlglot/ tests/dialects/test_duckdb.py | tail -1; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -1; git status --short; git diff", "description": "Apply formatting, re-test DuckDB dialect, show diff"}
[tool_result] 2 files reformatted
177 files already formatted
45 passed, 600 subtests passed in 0.29s
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
diff --git a/sqlglot/expressions/ddl.py b/sqlglot/expressions/ddl.py
index 829c917ac..226c379f4 100644
--- a/sqlglot/expressions/ddl.py
+++ b/sqlglot/expressions/ddl.py
@@ -226,6 +226,14 @@ class UserDefinedFunction(Expression):
     arg_types = {"this": True, "expressions":
…[7409 chars elided]…
 macro = parse_one(
+            "CREATE MACRO t(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)", read="duckdb"
+        )
+        self.assertTrue(
+            all(overload.args.get("table") for overload in macro.expression.expressions)
+        )
+
     def test_bitwise_agg(self):
         self.validate_all(
             "SELECT BIT_OR(int_value) FROM t",
[This command modified 2 files you've previously read: tests/dialects/test_duckdb.py, sqlglot/parser.py. Call Read before editing.]
[assistant] The diff is what I intended. One cleanup: a comment in `_parse_macro_overloads` runs past the project's line length, so I'll wrap it. Then I'll run the final checks: the full suite, ruff, mypy, and the DuckDB engine check once more.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        # The first overload's TABLE marker is parsed as a RETURNS property, so move it onto its overload\n        returns", "new_string": "        # The first overload's TABLE marker is parsed as a RETURNS property,\n        # so move it onto that overload\n        returns"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-155045-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[assistant] The harness says `parser.py` changed on disk since my last read. My own `ruff format` run would explain that, but I'll check the diff for anything unexpected before going further:
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff sqlglot/parser.py | grep \"^[-+]\" | grep -v \"^+++\\|^---\" | head -80", "description": "Check parser.py diff for unexpected changes"}
[tool_result]  M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
 sqlglot/expressions/ddl.py    |  8 +++++++
 sqlglot/generator.py          | 16 ++++++++++++--
 sqlglot/parser.py             | 50 +++++++++++++++++++++++++++++++++++++++++++
 sqlglot/parsers/duckdb.py     |  7 ++++++
 tests/dialects/test_duckdb.py | 21 ++++++++++++++++++
 5 files changed, 100 insertions(+), 2 deletions(-)
+    # Whether overloaded macros are s
…[1588 chars elided]…
okenType.ALIAS):
+                self.raise_error("Expected AS in macro overload")
+
+            table = bool(self._match(TokenType.TABLE))
+            body = self._parse_user_defined_function_expression()
+            overloads.append(
+                self.expression(exp.MacroOverload(expressions=params, expression=body, table=table))
+            )
+
+        return exp.UserDefinedFunction(this=this.this), self.expression(
+            exp.MacroOverloads(expressions=overloads)
+        )
+
[assistant] The parser diff contains only my changes, so the notice came from my own formatter run. Final verification: full suite, ruff, mypy, and the issue's exact example against DuckDB.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; $P -m ruff format --check sqlglot tests/dialects/test_duckdb.py | tail -1; $P -m ruff check sqlglot tests/dialects/test_duckdb.py | tail -1; $P -m mypy sqlglot/parser.py
…[192 chars elided]…
) AS a + b + c;'''\nout = sqlglot.parse_one(issue, read='duckdb').sql('duckdb')\nprint(out)\nc = duckdb.connect(); c.execute(out)\nprint(c.execute('select add_x(1, 2), add_x(1, 2, 3)').fetchall())\nprint(sqlglot.parse_one('CREATE OR REPLACE MACRO add_2(a, b) AS a + b;', dialect='duckdb').sql('duckdb'))\n\"", "description": "Run full suite, linters, and issue example end to end", "timeout": 600000}
[tool_result] 1114 passed, 18162 subtests passed in 59.70s
177 files already formatted
All checks passed!
Success: no issues found in 4 source files
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
[(3, 6)]
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
[assistant] Overloaded DuckDB macros now parse and round-trip. The issue's example outputs `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`, and DuckDB 1.5.6 accepts that output and resolves the overloads correctly: `add_x(1, 2)` returns 3 and `add_x(1, 2, 3)` returns 6. The full suite passes (1114 tests), and ruff and mypy are clean. I haven't committed anything.

**Representation.** An overloaded macro becomes `Create(this=<name only>, kind=MACRO, expression=MacroOverloads(...))`. `MacroOverloads` holds one `MacroOverload` per overload, each with its parameters, its body, and a `table` flag. 
…[816 chars elided]…
n flat, so pretty output stays on one line.
- `tests/dialects/test_duckdb.py`: a new `test_macro_overloads` covering scalar and table overloads, round-trips, and the node structure.

**Limits.** DuckDB only accepts a parenthesized body for a table overload, as in `AS TABLE (SELECT …)`. An unparenthesized `AS TABLE SELECT …` followed by another overload is a syntax error in DuckDB too, so sqlglot doesn't accept it either. DuckDB also doesn't allow mixing scalar and table overloads in one macro. The parser accepts a mix and doesn't reject it, since the representation keeps the flag per overload.
