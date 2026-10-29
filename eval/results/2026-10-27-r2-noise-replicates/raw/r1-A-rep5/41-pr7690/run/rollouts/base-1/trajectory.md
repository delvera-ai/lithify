# trajectory base-1

final message:
Overloaded `CREATE MACRO` now parses and round-trips in the DuckDB dialect. The spec example produces `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`, and the full suite passes (1114 tests, including a new `test_macro_overloads`). The changes are uncommitted.

**Representation:** the macro name goes in `Create.this`. Each overload is an `exp.MacroOverload` (`expressions` = parameter list, `expression` = body, `is_table` flag), and `Create.expression` is an `exp.MacroOverloads` holding one entry per overload.

**Changes:**
- `sqlglot/expressions/ddl.py`: adds `MacroOverload` and `MacroOverloads`.
- `sqlglot/parser.py`: in the function branch of `_parse_create`, a trailing `, (` triggers overload parsing. The first overload's `AS TABLE` is moved from the properties onto its entry.
- `sqlglot/parsers/duckdb.py`: a DuckDB-only body-parse override. Without it, `AS (SELECT a), (b) AS ...` swallows the separator as a comma join on the subquery.
- `sqlglot/generator.py`: renderers for both nodes, and a guard so overloads attach directly to the name.
- `tests/dialects/test_duckdb.py`: a new test. No existing tests were changed.

**Verified against real DuckDB 1.5.6:** the generated SQL runs, and the overloads resolve correctly (`add_x(1,2)` gives 3, `add_x(1,2,3)` gives 6, and a table overload returns rows).

**Decisions for you to review:**
- **Single-overload macros keep the old AST shape**: `Create(this=UDF(name, params), expression=body)`, with no `MacroOverloads`. The spec could be read as wanting every macro wrapped. I didn't, to avoid changing existing AST output. Wrapping them would be a small follow-up.
- **The parser change is in the shared base parser, not gated to DuckDB.** The `MACRO` keyword maps to `FUNCTION` only in DuckDB, and the new branch only fires when a function body is followed by `, (`, which was a parse error before.

**Limits, which match DuckDB:**
- A bare `SELECT` table body followed by another overload (`AS TABLE SELECT a, (a, b) AS ...`) is rejected by DuckDB too. Sqlglot falls back to `Command` with the text preserved. Parenthesized bodies (`AS TABLE (SELECT ...)`) work.
- Mixing scalar and table overloads in one macro is rejected by DuckDB, so I didn't add support for it.

## events
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py | head -80; git log --oneline -1", "description": "Find MACRO references in source"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
622ad32d7 lithify: probe base
[tool_use Bash] {"command": "ls sqlglot | head -80; grep -rn -i \"macro\" sqlglot/ --include=*.py | grep -v \"^sqlglot/dialects/[a-z]*\\.py:.*MACRO\\b\" | head -60; grep -rn -i \"macro\" tests/dialects/test_duckdb.py | head -40", "description": "Search for macro references across sqlglot and tests"}
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
(eval):1: no matches found: --include=*.py
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ | grep -v \"\\.pyc\" | head -60; sed -n 2570,2640p tests/dialects/test_duckdb.py", "description": "Search macro references and existing macro tests"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
        ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
  
…[2389 chars elided]…
ROM t",
            read={
                "snowflake": "SELECT BITXOR_AGG(int_value) FROM t",
                "duckdb": "SELECT BIT_XOR(int_value) FROM t",
            },
        )
        self.validate_all(
            "SELECT BIT_OR(CAST(val AS FLOAT)) FROM t",
            write={
                "duckdb": "SELECT BIT_OR(CAST(ROUND(CAST(val AS REAL)) AS INT)) FROM t",
                "snowflake": "SELECT BITORAGG(CAST(val AS FLOAT)) FROM t",
            },
        )
        self.validate_all(
[tool_use Bash] {"command": "grep -n \"FUNCTION\\|_parse_user_defined_function\\|def _parse_create\\|UserDefinedFunction\\|def _parse_udf\" sqlglot/parser.py sqlglot/parsers/*.py | head -60; grep -n \"class UserDefinedFunction\" -A 12 sqlglot/expressions/*.py; grep -n \"def userdefinedfunction_sql\\|def create_sql\" -A 40 sqlglot/generator.py sqlglot/generators/*.py | head -120", "description": "Locate UDF parsing and generation code"}
[tool_result] sqlglot/parsers/clickhouse.py:90:AGG_FUNCTIONS = {
sqlglot/parsers/clickhouse.py:211:AGG_FUNCTIONS_SUFFIXES: list[str] = sorted(
sqlglot/parsers/clickhouse.py:235:    f"{f}{sfx}": (f, sfx) for sfx in AGG_FUNCTIONS_SUFFIXES for f in AGG_FUNCTIONS
sqlglot/parsers/clickhouse.py:236:} | {f: (f, None) for f in AGG_FUNCTIONS}
sqlglot/parsers/clickhouse.py:248:    FUNCTIONS = {
sqlglot/parsers/clickhouse.py:251:            for k, v in parser.Parser.FUNCTIONS.items()
sqlglot/parsers/clickhouse.py:314:  
…[13501 chars elided]…
lglot/generator.py-4615-                then = f"UPDATE {self.sql(then_expression, 'expressions')}"
sqlglot/generator.py-4616-            else:
sqlglot/generator.py-4617-                expressions_sql = self.expressions(then_expression)
sqlglot/generator.py-4618-                then = f"UPDATE SET{self.sep()}{expressions_sql}" if expressions_sql else "UPDATE"
sqlglot/generator.py-4619-        else:
sqlglot/generator.py-4620-            then = self.sql(then_expression)
sqlglot/generator.py-4621-
[tool_use Bash] {"command": "sed -n 2346,2480p sqlglot/parser.py; sed -n 7020,7045p sqlglot/parser.py; sed -n 1325,1400p sqlglot/generator.py", "description": "Read CREATE parsing and generation of function bodies"}
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
…[8973 chars elided]…
f expression.args.get("concurrently") else ""
        exists_sql = " IF NOT EXISTS" if expression.args.get("exists") else ""
        no_schema_binding = (
            " WITH NO SCHEMA BINDING" if expression.args.get("no_schema_binding") else ""
        )

        clone = self.sql(expression, "clone")
        clone = f" {clone}" if clone else ""

        if kind in self.EXPRESSION_PRECEDES_PROPERTIES_CREATABLES:
            properties_expression = f"{expression_sql}{properties_sql}"
        else:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['CREATE OR REPLACE MACRO add_2(a, b) AS a + b', 'CREATE MACRO t(a, b) AS TABLE SELECT a, b', 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c']:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n    except Exception as ex: print('ERR', type(ex).__name__, ex)\n\"; grep -rn \"_try_parse\\b\" sqlglot/parser.py | head -3; grep -n \"TABLE\" sqlglot/generators/duckdb.py | head; grep -n \"class Parser\" -A3 sqlglot/dialects/duckdb.py", "description": "Probe current DuckDB macro parse behavior"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/parser.py:2007:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
sqlglot/parser.py:2549:                    expression = self._try_parse(self._parse_table_parts)
sqlglot/parser.py:4379:            if this := self._try_parse(self._parse_table):
1459:    TABLE_HINTS = False
1463:    RENAME_TABLE_WITH_DB = False
1466:    TABLESAMPLE_KEYWORDS = "USING SAMPLE"
1467:    TABLESAMPLE_SEED_KEYWORD = "REPEATABLE"
1473:    SUPPORTS_CREATE_TABLE_LIKE = False
1647:        exp.ReturnsProperty: lambda self, e: "TABLE" if isinstance(e.this, exp.Schema) else "",
1837:    # DuckDB doesn't generally support CREATE TABLE .. properties
2983:            tablesample_keyword = "TABLESAMPLE"
3776:        # For GENERATOR, unwrap TABLE() - just emit the Generator (becomes RANGE)
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/ | head; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\"; PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE OR REPLACE MACRO add_2(a, b) AS a + b', 'CREATE MACRO t(a, b) AS TABLE SELECT a, b', 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c']:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n    except Exception as ex: print('ERR', type(ex).__name__, ex)\n\"", "description": "Run probe with repo sqlglot on path"}
[tool_result] activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
dmypy
f2py
~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py
Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=add_2, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False),
      Identifier(this=b, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=True,
  ref
…[602 chars elided]…
Column(
        this=Identifier(this=a, quoted=False)),
      Column(
        this=Identifier(this=b, quoted=False))]),
  exists=False,
  properties=Properties(
    expressions=[
      ReturnsProperty(
        this=Schema(
          this=Var(this=TABLE)),
        is_table=True)]),
  begin=False,
  concurrently=False)
CREATE MACRO t(a, b) AS TABLE SELECT a, b
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 35.
  CREATE MACRO add_x (a, b) AS a + b[4m,[0m (a, b, c) AS a + b + c
[tool_use Bash] {"command": "grep -rn \"is_table\\|ReturnsProperty\" sqlglot/ | head -20; grep -n \"def _parse_heredoc\\|def _parse_returns\" -A12 sqlglot/parser.py | head -60; grep -n \"class Parser\\|FUNCTION\\|def _parse\" sqlglot/dialects/duckdb.py | head -60", "description": "Inspect table-macro returns parsing"}
[tool_result] sqlglot/generator.py:243:        exp.ReturnsProperty: lambda self, e: (
sqlglot/generator.py:732:        exp.ReturnsProperty: exp.Properties.Location.POST_SCHEMA,
sqlglot/schema.py:540:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:564:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:601:            parts = [self._normalize_name(part, dialect=dialect, is_table=True) for part in p
…[1680 chars elided]…
:    def _parse_heredoc(self) -> exp.Heredoc | None:
9251-        if self._match(TokenType.HEREDOC_STRING):
9252-            return self.expression(exp.Heredoc(this=self._prev.text))
9253-
9254-        if not self._match_text_seq("$"):
9255-            return None
9256-
9257-        tags = ["$"]
9258-        tag_text = None
9259-
9260-        if self._is_connected():
9261-            self._advance()
9262-            tags.append(self._prev.text.upper())
95:            "MACRO": TokenType.FUNCTION,
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/duckdb.py; sed -n 215,275p sqlglot/parsers/duckdb.py; sed -n 235,255p sqlglot/generator.py; grep -n \"class DuckDB\\|Generator\\|def create_sql\" sqlglot/generators/duckdb.py | head; ls sqlglot/parsers/ | head -50; grep -n \"^from\\|^import\" sqlglot/parsers/duckdb.py", "description": "Read DuckDB parser macro table handling"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.trie import new_trie
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_default_decimal_type,
    build_formatted_time,
    build_regexp_extract,
    date_trunc_to_time,
    pivot_column_names,
)
from sqlglot.helper import seq_get
from sqlglot.parser import binary_range_parser
from sqlglot.tokens import TokenType
from collections.abc import Collection


def _build_sort_arr
…[5041 chars elided]…
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
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
[tool_use Bash] {"command": "sed -n 2007,2025p sqlglot/parser.py; grep -n \"def _parse_wrapped_csv\\|def _parse_function_parameter\\|def _parse_csv\" -A3 sqlglot/parser.py | head -20; sed -n 215,228p sqlglot/expressions/ddl.py; grep -n \"def no_identify\\|def wrap\\b\\|def wrap(\" -A3 sqlglot/generator.py | head; grep -rn \"AS '\" tests/dialects/test_postgres.py | grep -i \"create\" | head -3; grep -n \"CREATE\\|sep()\" sqlglot/generator.py | sed -n 1,3p", "description": "Read try_parse helper and related utilities"}
[tool_result]     def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
        index = self._index
        error_level = self.error_level
        this: T | None = None

        self.error_level = ErrorLevel.IMMEDIATE
        try:
            this = parse_method()
        except ParseError:
            this = None
        finally:
            if not this or retreat:
                self._retreat(index)
            self.error_level = error_level

        return this

    def
…[1607 chars elided]…
         "CREATE FUNCTION add(integer, integer) RETURNS INT LANGUAGE SQL IMMUTABLE STRICT AS 'select $1 + $2;'"
tests/dialects/test_postgres.py:1282:            "CREATE FUNCTION add(INT, INT) RETURNS INT SET search_path TO 'public' AS 'select $1 + $2;' LANGUAGE SQL IMMUTABLE",
319:    CREATE_FUNCTION_RETURN_AS = True
407:    # Whether to include the type of a computed column in the CREATE DDL
410:    # Whether CREATE TABLE .. COPY .. is supported. False means we'll generate CLONE instead of COPY
[tool_use Bash] {"command": "sed -n 1400,1420p sqlglot/generator.py; grep -n \"    def expressions\" -A12 sqlglot/generator.py | head -20; grep -n \"    def wrap\" -A10 sqlglot/generator.py", "description": "Read rest of create_sql and helpers"}
[tool_result]         else:
            properties_expression = f"{properties_sql}{expression_sql}"

        expression_sql = f"CREATE{modifiers} {kind}{concurrently}{exists_sql} {this}{properties_expression}{postexpression_props_sql}{index_sql}{no_schema_binding}{clone}"
        return self.prepend_ctes(expression, expression_sql)

    def sequenceproperties_sql(self, expression: exp.SequenceProperties) -> str:
        start = self.sql(expression, "start")
        start = f"START WITH {start}" if start else 
…[982 chars elided]…
= False,
4522-        new_line: bool = False,
1027:    def wrap(self, expression: exp.Expr | str) -> str:
1028-        this_sql = (
1029-            self.sql(expression)
1030-            if isinstance(expression, exp.UNWRAPPED_QUERIES)
1031-            else self.sql(expression, "this")
1032-        )
1033-        if not this_sql:
1034-            return "()"
1035-
1036-        this_sql = self.indent(this_sql, level=1, pad=0)
1037-        return f"({self.sep('')}{this_sql}{self.seg(')', sep='')}"
[assistant] Current behavior: `MACRO` is tokenized as `FUNCTION`, the first overload parses through `_parse_create`'s function branch, and the trailing `, (...) AS ...` is left unconsumed. I'll add the overload parse in that branch, a `MacroOverload`/`MacroOverloads` pair in `ddl.py`, and the matching generators.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": True, \"expression\": True, \"is_table\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Now the parser: the function branch, plus the helpers next to `_parse_user_defined_function`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n   
…[99 chars elided]…
n                create_token_type == TokenType.FUNCTION\n                and isinstance(this, exp.UserDefinedFunction)\n                and self._match_pair(TokenType.COMMA, TokenType.L_PAREN, advance=False)\n            ):\n                expression = self._parse_macro_overloads(this, expression, properties)\n                this = this.this\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        expressions = self._parse_csv(self._parse_function_parameter)\n        self._match_r_paren()\n        return self.expression(\n            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
…[1304 chars elided]…
self._match(TokenType.ALIAS):\n            self.raise_error(\"Expected AS after macro parameters\")\n\n        is_table = bool(self._match(TokenType.TABLE))\n        return self.expression(\n            exp.MacroOverload(\n                expressions=params,\n                expression=self._parse_user_defined_function_expression(),\n                is_table=is_table,\n            )\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: the entry and list renderers, and the `create_sql` guard so overloads attach directly to the name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        expression_sql = self.sql(expression, \"expression\")\n        if expression_sql:\n            expression_sql = f\"{begin}{self.sep()}{expression_sql}\"", "new_string": "        expression_sql = self.sql(expression, \"expression\")\n        # Macro overloads carry their own parameter lists, so they attach directly to the name\n        if expression_sql and not isinstance(expression.expression, exp.MacroOverloads):\n            expression_sql = f\"{begin}{self.sep()}{expression_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def joinhint_sql(", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def ma
…[47 chars elided]…
load) -> str:\n        params = self.wrap(self.no_identify(self.expressions, expression))\n        table = \"TABLE \" if expression.args.get(\"is_table\") else \"\"\n        return f\"{params} AS {table}{self.sql(expression, 'expression')}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)\n\n    def joinhint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a probe covering the spec example, table overloads, a mixed scalar/table case, the single-overload form, and the Postgres `'lib', 'sym'` form that also has a comma after a function body.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c''',\n 'CREATE MACRO t(a) AS TABLE SELECT a, 1 AS b, (a, b) AS TABLE SELECT a + b',\n 'CREATE MACRO m(a) AS (a + 1), (a, b) AS a * b',\n 'CREATE
…[158 chars elided]…
one(s, read='duckdb'); out = e.sql('duckdb'); print(out)\n    except Exception as ex: print('ERR', type(ex).__name__, ex)\nprint(repr(sqlglot.parse_one(cases[1], read='duckdb').args['expression']))\nprint(sqlglot.parse_one(\\\"CREATE FUNCTION add(integer, integer) RETURNS INT AS 'lib', 'sym'\\\", read='postgres').sql('postgres'))\n\"", "description": "Probe overload parsing and round-trip output"}
[tool_result] 'CREATE MACRO t(a) AS TABLE SELECT a, 1 AS b, (a, b) AS TABLE SELECT a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE FUNCTION f(a, b) AS TABLE SELECT a, (b, c) AS TABLE SELECT b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE FUNCTION add(integer, integer) RETURNS INT AS 'lib', 'sym'' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
CREATE MACRO add_x(a, b) AS a + b,
…[759 chars elided]…
ssions=[
        Identifier(this=a, quoted=False),
        Identifier(this=b, quoted=False),
        Identifier(this=c, quoted=False)],
      expression=Add(
        this=Add(
          this=Column(
            this=Identifier(this=a, quoted=False)),
          expression=Column(
            this=Identifier(this=b, quoted=False))),
        expression=Column(
          this=Identifier(this=c, quoted=False))),
      is_table=False)])
CREATE FUNCTION add(integer, integer) RETURNS INT AS 'lib', 'sym'
[assistant] The spec example now round-trips. Three things to address: the zero-parameter overload fails because `expressions` is required on `MacroOverload`, and the two table cases fall back to `Command`. The table cases may be a genuine SQL ambiguity (`SELECT a, (a, b) AS ...` reads as a select list), so I want to check against real DuckDB before deciding.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"import duckdb; print(duckdb.__version__)\" 2>&1 | tail -1; which duckdb; <work>/env-sqlglot/bin/python -c \"import sqlglot\" 2>&1 | tail -1", "description": "Check whether duckdb is available for validation"}
[tool_result] 1.5.6
duckdb not found
[tool_use Bash] {"command": "cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\ncon = duckdb.connect()\nstmts = [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO z() AS 1, (a) AS a',\n 'CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b',\n 'CREATE MACRO t2(a) AS TABLE SELECT a, 1 AS b',\n 'CREATE MACRO t3(a)
…[304 chars elided]…
(e).splitlines()[0])\nprint(con.execute(\\\"select * from duckdb_functions() where function_name in ('add_x','t','sc') \\\").fetchall()[:0])\nprint(con.execute('select add_x(1,2), add_x(1,2,3)').fetchall())\nprint(con.execute('select * from z()').fetchall() if False else con.execute('select z(), z(5)').fetchall())\n\" 2>&1 | tail -30", "description": "Validate overload syntax against real DuckDB"}
[tool_result] OK   CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK   CREATE MACRO z() AS 1, (a) AS a
FAIL CREATE MACRO t(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
OK   CREATE MACRO t2(a) AS TABLE SELECT a, 1 AS b
FAIL CREATE MACRO t3(a) AS TABLE SELECT a, (a, b) AS TABLE (SELECT a + b) -> Parser Error: syntax error at or near "("
FAIL CREATE MACRO mix(a) AS TABLE SELECT a, (a, b) AS a + b -> Parser Error: syntax error at or near "+"
FAIL CREATE MACRO sc(a) AS (a + 1), (a, b) AS TABLE SELECT a * b -> Parser Error: syntax error at or near "TABLE"
[]
[(3, 6)]
[(1, 5)]
Shell cwd was reset to ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1
[assistant] Real DuckDB 1.5.6 accepts `CREATE MACRO z() AS 1, (a) AS a` (so the zero-parameter entry must be allowed), and it accepts the spec example. It rejects my table cases as written, so those were invalid inputs. Let me find which table-overload forms DuckDB does accept.
[tool_use Bash] {"command": "cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\ncon = duckdb.connect()\nstmts = [\n 'CREATE MACRO t1(a) AS TABLE SELECT a WHERE a > 0, (a, b) AS TABLE SELECT a + b',\n 'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t3(a) AS TABLE SELECT a ORDER BY a, (a, b) AS TABLE SELECT a + b',\
…[173 chars elided]…
 a, (a, b) AS a + b',\n 'CREATE MACRO t7(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b',\n 'CREATE MACRO t8(a) AS TABLE SELECT a LIMIT 1, (a, b) AS TABLE SELECT a + b',\n]\nfor s in stmts:\n    try:\n        con.execute(s); print('OK  ', s)\n    except Exception as e: print('FAIL', s, '->', str(e).splitlines()[0])\n\" 2>&1 | tail -20", "description": "Probe valid DuckDB table-overload forms"}
[tool_result] FAIL CREATE MACRO t1(a) AS TABLE SELECT a WHERE a > 0, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near ","
OK   CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
FAIL CREATE MACRO t3(a) AS TABLE SELECT a ORDER BY a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "AS"
FAIL CREATE MACRO t4(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
OK   CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)
FAIL CREATE MACRO t6(a) AS TABLE SELECT a, (a, b) AS a + b -> Parser Error: syntax error at or near "+"
FAIL CREATE MACRO t7(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b -> Parser Error: syntax error at or near "SELECT"
FAIL CREATE MACRO t8(a) AS TABLE SELECT a LIMIT 1, (a, b) AS TABLE SELECT a + b -> Parser Error: errhint NOT IMPLEMENTED
Shell cwd was reset to ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1
[assistant] Valid multi-overload table forms are the parenthesized bodies (`AS TABLE (SELECT ...)` and `AS (SELECT ...)`); a bare `SELECT` body followed by a comma is rejected by DuckDB itself. So the `Command` fallback for bare-select table overloads matches DuckDB. Now I'll make the parameter list optional for zero-argument overloads and re-probe with the valid forms.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class MacroOverload(Expression):\n    arg_types = {\"expressions\": True, \"expression\": True, \"is_table\": False}", "new_string": "class MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True, \"is_table\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n 'CREATE MACRO z() AS 1, (a) AS a',\n 'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)',\n 'CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)',\n 'CREATE MACRO sc(a) AS (a + 1), (a, b) AS a * b',\n 'CREATE OR REPLACE MACRO add_x(a, b)
…[261 chars elided]…
 + b)', read='duckdb').expression.expressions[1].args)\nprint(sqlglot.parse_one('CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb').expression.expressions[0].args.get('is_table'))\nprint(sqlglot.parse_one('CREATE MACRO z() AS 1, (a) AS a', read='duckdb').sql('duckdb', pretty=True))\n\" 2>&1 | tail -30", "description": "Re-probe overloads and round-trip checks"}
[tool_result] 'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Traceback (most recent call last):
  File "<string>", line 13, in <module>
AttributeError: 'str' object has no attribute 'expressions'
RT CREATE MACRO z() AS 1, (a) AS a
RT CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
RT CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)
RT CREATE MACRO sc(a) AS (a + 1), (a, b) AS a * b
RT CREATE OR REPLACE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
[assistant] Round-trip strings match, but the `Command` warnings show that the parenthesized-body forms are falling back rather than producing a `Create`. Let me see the parse error.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor s in ['CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)', 'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)']:\n    try:\n        print(repr(sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE)))\n    except Exception as ex: print(type(ex).__name__, str(ex)[:400])\n\" 2>&1 | tail -30", "description": "Show raw parse error for parenthesized macro bodies"}
[tool_result] 'CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=CREATE, expression=MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b))
Command(this=CREATE, expression=MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b))
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS (SELECT a)', 'CREATE MACRO t(a) AS (SELECT a), (b) AS 1', 'CREATE MACRO t(a) AS 1, (b) AS (SELECT 1)', 'CREATE MACRO t(a) AS (a), (b) AS (SELECT 1)']:\n    e = sqlglot.parse_one(s, read='duckdb'); print(type(e).__name__, e.sql('duckdb'))\n\" 2>&1 | tail -30", "description": "Isolate which parenthesized body breaks parsing"}
[tool_result] Create CREATE MACRO t(a) AS (SELECT a)
Create CREATE MACRO t(a) AS (SELECT a), (b) AS "1"
Create CREATE MACRO t(a) AS 1, (b) AS (SELECT 1)
Create CREATE MACRO t(a) AS (a), (b) AS (SELECT 1)
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('CREATE MACRO t(a) AS (SELECT a), (b) AS 1', read='duckdb')\nprint(repr(e.expression.expressions[1]))\nprint(repr(sqlglot.parse_one('CREATE MACRO t(a) AS 1, (b) AS 2', read='duckdb').expression.expressions[1].expression))\nprint(repr(sqlglot.parse_one('CREATE MACRO t(a) AS (a), (b) AS (SELECT 1)', read='duckdb').expression.expressions[1]))\n\" 2>&1 | head -80", "description": "Dump AST for overload entries"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 5, in <module>
IndexError: list index out of range
[assistant] The body parse is swallowing the comma: `(SELECT a), (b) AS 1` never becomes an overload list. Let me confirm by checking which of the earlier "successful" round-trips actually produced `MacroOverloads`.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['CREATE MACRO m(a) AS (a + 1), (a, b) AS a * b', 'CREATE MACRO z() AS 1, (a) AS a', 'CREATE MACRO t(a) AS (SELECT a), (b) AS 1', 'CREATE MACRO t(a) AS (a), (b) AS (SELECT 1)', 'CREATE MACRO t(a) AS 1, (b) AS 2']:\n    e = sqlglot.parse_one(s, read='duckdb')\n    print(type(e).__name__, type(e.expression).__name__, '|', e.sql('duckdb'))\n\" 2>&1 | tail -20", "description": "Check AST node type for each overload case"}
[tool_result] Create MacroOverloads | CREATE MACRO m(a) AS (a + 1), (a, b) AS a * b
Create MacroOverloads | CREATE MACRO z() AS 1, (a) AS a
Create Subquery | CREATE MACRO t(a) AS (SELECT a), (b) AS "1"
Create MacroOverloads | CREATE MACRO t(a) AS (a), (b) AS (SELECT 1)
Create MacroOverloads | CREATE MACRO t(a) AS 1, (b) AS 2
[assistant] The failure is specific to a parenthesized `SELECT` body followed by a comma. Let me find which parser path takes the `, (b) AS 1` tail.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS (SELECT a), (b) AS 1', read='duckdb')\nprint(repr(e.expression)[:600])\nprint(e.args.keys())\n\" 2>&1 | tail -30; grep -n \"def _parse_subquery\" -A12 sqlglot/parser.py | head -30", "description": "Inspect subquery body AST and subquery parser"}
[tool_result] Subquery(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]),
  joins=[
    Join(
      this=Subquery(
        this=Table(
          this=Identifier(this=b, quoted=False)),
        alias=TableAlias(
          this=Identifier(this=1, quoted=False))))])
dict_keys(['this', 'kind', 'replace', 'refresh', 'unique', 'expression', 'exists', 'properties', 'indexes', 'no_schema_binding', 'begin', 'clone', 'concurrently', 'clustered'])
4076:    def _parse_subquery(
4077-        self, this: exp.Expr | None, parse_alias: bool = True
4078-    ) -> exp.Subquery | None:
4079-        if not this:
4080-            return None
4081-
4082-        return self.expression(
4083-            exp.Subquery(
4084-                this=this,
4085-                pivots=self._parse_pivots(),
4086-                alias=self._parse_table_alias() if parse_alias else None,
4087-                sample=self._parse_table_sample(),
4088-            )
[assistant] The `(SELECT a)` body picks up `, (b)` as an implicit comma-join on the subquery. Let me see how the parser gates comma-joins.
[tool_use Bash] {"command": "grep -n \"def _parse_join(\" -A30 sqlglot/parser.py | grep -n \"COMMA\" ; grep -n \"def _parse_query_modifiers\" -A25 sqlglot/parser.py | head -40", "description": "Find comma-join parsing in joins"}
[tool_result] 7:4416-        if self._match(TokenType.COMMA):
4119:    def _parse_query_modifiers(self, this: E) -> E: ...
4120-
4121-    @t.overload
4122:    def _parse_query_modifiers(self, this: None) -> None: ...
4123-
4124:    def _parse_query_modifiers(self, this):
4125-        if isinstance(this, self.MODIFIABLES):
4126-            for join in self._parse_joins():
4127-                this.append("joins", join)
4128-            for lateral in iter(self._parse_lateral, None):
4129-                this.a
…[478 chars elided]…
lf.raise_error(
4140-                                f"Found multiple '{modifier_token.text.upper()}' clauses",
4141-                                token=modifier_token,
4142-                            )
4143-
4144-                        this.set(key, expression)
4145-                        if key == "limit":
4146-                            offset = expression.args.get("offset")
4147-                            expression.set("offset", None)
4148-
4149-                            if offset:
[tool_use Bash] {"command": "cd <work>/env-sqlglot/bin/true; cd ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1 && sed -n 4405,4425p sqlglot/parser.py; grep -n \"_parse_query_modifiers(\" sqlglot/parser.py | head -20", "description": "Read comma-join branch in _parse_join"}
[tool_result] (eval):cd:1: no such file or directory: <work>/env-sqlglot/bin/true
                return this.this
            return this

        return self._parse_wrapped_csv(_parse_column_as_identifier, optional=True)

    def _parse_join(
        self,
        skip_join_token: bool = False,
        parse_bracket: bool = False,
        alias_tokens: t.Collection[TokenType] | None = None,
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
       
…[610 chars elided]…
query_modifiers(this)
3937:            this = self._parse_query_modifiers(this)
4119:    def _parse_query_modifiers(self, this: E) -> E: ...
4122:    def _parse_query_modifiers(self, this: None) -> None: ...
4124:    def _parse_query_modifiers(self, this):
5880:                    exp.In(this=this, query=self._parse_query_modifiers(query).subquery(copy=False))
6793:                this=self._parse_query_modifiers(self._parse_set_operations(this)),
8584:        return self._parse_query_modifiers(
[tool_use Bash] {"command": "sed -n 3900,3945p sqlglot/parser.py", "description": "Read parenthesized subquery parsing path"}
[tool_result]                     kind=kind,
                    hint=hint,
                    distinct=distinct,
                    expressions=projections,
                    limit=limit,
                    exclude=exclude,
                    operation_modifiers=operation_modifiers or None,
                )
            )
            this.comments = comments

            into = self._parse_into()
            if into:
                this.set("into", into)

            if not from_:
                from
…[820 chars elided]…
            this = exp.select("*").from_(from_.this, copy=False)
            this = self._parse_query_modifiers(this)
        elif self._match(TokenType.SUMMARIZE):
            table = self._match(TokenType.TABLE)
            this = self._parse_select() or self._parse_string() or self._parse_table()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
            this = self._parse_describe()
        else:
            this = None
[tool_use Bash] {"command": "sed -n 2270,2292p sqlglot/parser.py; sed -n 8575,8590p sqlglot/parser.py", "description": "Find the caller that attaches joins to a subquery body"}
[tool_result]         if not self._curr:
            return None

        if self._match_set(self.STATEMENT_PARSERS):
            comments = self._prev_comments
            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
            stmt.add_comments(comments, prepend=True)
            return stmt

        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
            return self._parse_command()

        if self._match_text_seq("WHILE"):
            return self._parse_whileblock()

       
…[456 chars elided]…
ent(), explicit=True)
                if alias
                else self._parse_assignment()
            )
            or self._parse_select()
        )

    def _parse_ddl_select(self) -> exp.Expr | None:
        return self._parse_query_modifiers(
            self._parse_set_operations(self._parse_select(nested=True, parse_subquery_alias=False))
        )

    def _parse_transaction(self) -> exp.Transaction | exp.Command:
        this = None
        if self._match_texts(self.TRANSACTION_KIND):
[assistant] Found it: `_parse_statement` ends by running `_parse_query_modifiers`, which attaches a comma-join to a parenthesized subquery body and swallows the overload separator. The fix is scoped to DuckDB's function-body parse: if the body is a `Subquery` that picked up joins, rewind and parse it as an expression, which leaves the comma for the overload list. Let me check the body hook's ClickHouse override and how `_parse_expression` treats a subquery first.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parsers/duckdb.py'\ns=open(p).read()\nold='''    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:\n        index = self._index'''\nnew='''    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        index = self._index\n        expression = super()._parse_user_defined_function_expression()\n\n        # A pa
…[925 chars elided]…
REATE MACRO s(a) AS (SELECT a, b FROM x, y), (a) AS (SELECT 1)',\n 'CREATE MACRO t(a) AS TABLE SELECT a FROM x, y',\n]\nfor s in cases:\n    e = sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE)\n    out = e.sql('duckdb'); print(type(e.expression).__name__, 'RT' if out == s else 'DIFF', out)\n\" 2>&1 | tail -20", "description": "Add DuckDB body-parse fix and re-run overload cases"}
[tool_result] MacroOverloads RT CREATE MACRO z() AS 1, (a) AS a
MacroOverloads RT CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
MacroOverloads RT CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b)
MacroOverloads RT CREATE MACRO sc(a) AS (a + 1), (a, b) AS a * b
MacroOverloads RT CREATE OR REPLACE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
MacroOverloads RT CREATE MACRO s(a) AS (SELECT a, b FROM x, y), (a) AS (SELECT 1)
Select RT CREATE MACRO t(a) AS TABLE SELECT a FROM x, y
[assistant] All overload shapes now parse as `MacroOverloads` and round-trip. Next I'll check that DuckDB actually accepts the generated SQL and runs the overloads, including mixed scalar/table entries.
[tool_use Bash] {"command": "cd /tmp && PYTHONPATH=~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1 <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1')\nimport duckdb, sqlglot\nfrom s
…[630 chars elided]…
RT' if out==s else '| DIFF')\n    except Exception as ex: print('DUCKDB FAIL', out, '->', str(ex).splitlines()[0])\nprint(con.execute('select add_x(1,2), add_x(1,2,3), z(), z(5)').fetchall())\nprint(con.execute('select * from t2(10)').fetchall(), con.execute('select * from mx(1, 2)').fetchall() if False else '')\n\" 2>&1 | tail -20", "description": "Validate generated overloads execute in DuckDB"}
[tool_result] DUCKDB OK   CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c | DIFF
DUCKDB OK   CREATE MACRO z() AS 1, (a) AS a | RT
DUCKDB OK   CREATE MACRO t2(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b) | RT
DUCKDB OK   CREATE MACRO t5(a) AS (SELECT a), (a, b) AS (SELECT a + b) | RT
DUCKDB FAIL CREATE MACRO mx(a) AS (SELECT a), (a, b) AS TABLE (SELECT a + b) -> Parser Error: syntax error at or near "TABLE"
DUCKDB FAIL CREATE MACRO mx2(a) AS (a + 1), (a, b) AS TABLE (SELECT a * b) -> Parser Error: syntax error at or near "TABLE"
[(3, 6, 1, 5)]
[(10,)]
Shell cwd was reset to ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1
[assistant] DuckDB accepts the generated SQL for every valid form and runs the overloads (`add_x(1,2)=3`, `add_x(1,2,3)=6`, `z()=1`, `z(5)=5`, table overload returns a row). The mixed scalar-plus-table case is rejected by DuckDB itself, so it's not a valid input and I won't target it. The one "DIFF" is only my input's extra space before `(`.

Now I'll add a regression test next to the existing `test_udf`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\",", "new_string": "    def test_macro_overloads(self):\n        self.validate_identity(\"CREATE MACR
…[511 chars elided]…
 + b, (a, b, c) AS a + b + c\", read=\"duckdb\"\n        )\n        overloads = ast.expression\n        self.assertIsInstance(overloads, exp.MacroOverloads)\n        self.assertEqual(len(overloads.expressions), 2)\n        self.assertEqual(len(overloads.expressions[1].expressions), 3)\n\n    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-122034-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "head -12 tests/dialects/test_duckdb.py | grep -n \"import\"; PY=<work>/env-sqlglot/bin/python; $PY -m ruff --version 2>/dev/null || ls $(dirname $PY) | grep -i ruff", "description": "Check test imports and ruff availability"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
ruff 0.15.6
[assistant] Imports are already present and ruff is available. I'll format the changed files, then run the project's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py && $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py; git diff --stat", "description": "Format and lint changed files"}
[tool_result] 2 files reformatted, 3 files left unchanged
All checks passed!
 sqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generator.py          | 11 +++++++++-
 sqlglot/parser.py             | 48 +++++++++++++++++++++++++++++++++++++++++++
 sqlglot/parsers/duckdb.py     | 11 ++++++++++
 tests/dialects/test_duckdb.py | 17 +++++++++++++++
 5 files changed, 94 insertions(+), 1 deletion(-)
[This command modified 2 files you've previously read: tests/dialects/test_duckdb.py, sqlglot/parser.py. Call Read before editing.]
[assistant] Ruff reformatted two files. I'll confirm the diff only contains my changes, then run the full test suite.
[tool_use Bash] {"command": "git diff sqlglot/parser.py sqlglot/generator.py", "description": "Review parser and generator diffs"}
[tool_result] diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 54b50c77a..7b363b7d6 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -1325,7 +1325,8 @@ class Generator:
         begin = " BEGIN" if expression.args.get("begin") else ""
 
         expression_sql = self.sql(expression, "expression")
-        if expression_sql:
+        # Macro overloads carry their own parameter lists, so they attach directly to the name
+        if expression_sql and not isinstance(expression.expres
…[3044 chars elided]…
  self.raise_error("Expected AS after macro parameters")
+
+        is_table = bool(self._match(TokenType.TABLE))
+        return self.expression(
+            exp.MacroOverload(
+                expressions=params,
+                expression=self._parse_user_defined_function_expression(),
+                is_table=is_table,
+            )
+        )
+
     def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
         literal = self._parse_primary()
         if literal:
[assistant] The diff contains only my changes. Now the full test suite with the project's command.
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite", "timeout": 900000}
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
1114 passed, 18162 subtests passed in 53.37s
[assistant] Overloaded `CREATE MACRO` now parses and round-trips in the DuckDB dialect. The spec example produces `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`, and the full suite passes (1114 tests, including a new `test_macro_overloads`). The changes are uncommitted.

**Representation:** the macro name goes in `Create.this`. Each overload is an `exp.MacroOverload` (`expressions` = parameter list, `expression` = body, `is_table` flag), and `Create.expression` is an `exp.MacroOverloads` holding one entry per overload.

**Changes:**
- `sqlglot/expressions/ddl.py`: adds `MacroOverload` and `Ma
…[1046 chars elided]…
*The parser change is in the shared base parser, not gated to DuckDB.** The `MACRO` keyword maps to `FUNCTION` only in DuckDB, and the new branch only fires when a function body is followed by `, (`, which was a parse error before.

**Limits, which match DuckDB:**
- A bare `SELECT` table body followed by another overload (`AS TABLE SELECT a, (a, b) AS ...`) is rejected by DuckDB too. Sqlglot falls back to `Command` with the text preserved. Parenthesized bodies (`AS TABLE (SELECT ...)`) work.
- Mixing scalar and table overloads in one macro is rejected by DuckDB, so I didn't add support for it.
