# trajectory base-1

final message:
Overloaded DuckDB macros now parse and round-trip. The example from the issue produces `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`. The full test suite passes (1114 tests), and ruff check and format are clean. The changes are uncommitted in the worktree.

**Representation:** the name stays on `Create.this`, and every overload becomes an entry in `exp.MacroOverloads`. Each `exp.MacroOverload` holds its parameter list (`expressions`), its body (`expression`), and an `is_table` flag. Single-overload macros keep their existing AST shape.

**Changes:**
- `sqlglot/expressions/ddl.py`: new `MacroOverload` and `MacroOverloads` classes.
- `sqlglot/parsers/duckdb.py`: `_parse_create` override. When a `MACRO` create is followed by a comma, it parses the remaining overloads. `_parse_macro_overload` handles each `(params) [AS] [TABLE] body`.
- `sqlglot/generators/duckdb.py`: `create_sql` override for the overloaded form, plus `macrooverloads_sql` and `macrooverload_sql`. Anything without overloads falls through to the base generator.
- `tests/dialects/test_duckdb.py`: `test_macro_overloads` covers round-trips with `OR REPLACE` and `IF NOT EXISTS`, a table overload, and the multi-line form from the issue.

**Choices I made:**
- Output glues the parameter list to the name (`add_x(a, b)`), matching the existing single-macro output.
- Overloads are DuckDB-only. The base parser and generator are untouched apart from new methods.

**Limitation:** a table overload (`AS TABLE SELECT ...`) only works as the last overload. When it's followed by a comma, the comma is read as part of the SELECT list. Scalar overloads can appear anywhere, and a table overload can be the last one. Fixing the middle-position case would need the table body wrapped in parentheses, which is a different syntax, so I left it.

## events
[tool_use Bash] {"command": "git status --short && grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/*.py sqlglot/parser.py sqlglot/generator.py | grep -v \"^.*#\" | head -80; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Inspect git status and search for macro handling"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ --include=*.py | head -60; echo ---; grep -rn -i \"macro\" tests/ | head -30", "description": "Search whole package and tests for macro references"}
[tool_result] (eval):1: no matches found: --include=*.py
---
tests/dialects/test_clickhouse.py:57:        self.validate_identity("@macro").assert_is(exp.Parameter).this.assert_is(exp.Var)
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; echo ---; grep -n \"FUNCTION\" sqlglot/parser.py sqlglot/generator.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py | head -30", "description": "Read existing DuckDB macro tests and FUNCTION handling"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[4812 chars elided]…
kenType.FUNCTION,
sqlglot/parser.py:769:        *NO_PAREN_FUNCTIONS,
sqlglot/parser.py:1469:    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
sqlglot/parser.py:1483:    FUNCTIONS_WITH_ALIASED_ARGS: t.ClassVar = {"STRUCT"}
sqlglot/parser.py:1487:    FUNCTION_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
sqlglot/parser.py:2189:        if kind.token_type in (TokenType.FUNCTION, TokenType.PROCEDURE):
sqlglot/parser.py:2368:        if self._match_pair(TokenType.TABLE, TokenType.FUNCTION, advance=False):
[assistant] Let me look at how `CREATE` is parsed for function kinds, and reproduce the failure.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['CREATE OR REPLACE MACRO add_2(a, b) AS a + b;', '''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''']:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb'); print(repr(e)[:400]); print(e.sql('duckdb'))\n    except Exception as ex: print('ERR', type(ex), ex)\n\"; sed -n 2170,2260p sqlglot/parser.py; sed -n 2355,2400p sqlglot/parser.py", "description": "Reproduce the macro parse behavior and read CREATE parsing"}
[tool_result] Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=add_2, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False),
      Identifier(this=b, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=True,
  refresh=False,
  unique=False,
  expression=Add(
    this=Column(
      this=Identifier(this=a, quoted=False)),
    expression=Column(
      this=Id
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
ERR <class 'sqlglot.errors.ParseError'> Invalid expres
…[4647 chars elided]…

        expression: exp.Expr | None = None
        indexes = None
        no_schema_binding = None
        begin = None
        clone = None

        def extend_props(temp_props: exp.Properties | None) -> None:
            nonlocal properties
            if properties and temp_props:
                properties.expressions.extend(temp_props.expressions)
            elif temp_props:
                properties = temp_props

        if create_token_type in (TokenType.FUNCTION, TokenType.PROCEDURE):
[tool_use Bash] {"command": "sed -n 2400,2440p sqlglot/parser.py; echo ----; grep -n \"_parse_user_defined_function\\b\" -A45 sqlglot/parser.py | sed -n '1,70p' | grep -v \"^--$\" | head -80", "description": "Read CREATE function branch and UDF parser"}
[tool_result]         if create_token_type in (TokenType.FUNCTION, TokenType.PROCEDURE):
            this = self._parse_user_defined_function(kind=create_token_type)

            # exp.Properties.Location.POST_SCHEMA ("schema" here is the UDF's type signature)
            extend_props(self._parse_properties())

            expression = self._parse_heredoc() if self._match(TokenType.ALIAS) else None
            extend_props(self._parse_function_properties())

            if not expression:
                if s
…[4426 chars elided]…
igQuery's JavaScript UDF definitions that end in an OPTIONS property
2418-                        # # https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement
2419-                        expression = self._parse_string()
2420-                        extend_props(self._parse_properties())
2421-                    else:
2422-                        expression = (
2423-                            self._parse_user_defined_function_expression()
[tool_use Bash] {"command": "grep -n \"def _parse_user_defined_function\\b\" -A40 sqlglot/parser.py; grep -n \"def _parse_user_defined_function_expression\" -A25 sqlglot/parser.py; echo ----; grep -n \"def create_sql\" -A12 sqlglot/generator.py | head -5; sed -n 2225,2265p sqlglot/generator.py; grep -n \"class UserDefinedFunction\" -A5 sqlglot/expressions/*.py; grep -rn \"Create(\\|TABLE SELECT\\|AS TABLE\" sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py | head", "description": "Read UDF parsing and generation helpers"}
[tool_result] 7031:    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032-        this = self._parse_table_parts(schema=True)
7033-
7034-        if not self._match(TokenType.L_PAREN):
7035-            return this
7036-
7037-        expressions = self._parse_csv(self._parse_function_parameter)
7038-        self._match_r_paren()
7039-        return self.expression(
7040-            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
7041-        
…[4404 chars elided]…
lict}{default_values}{returning}"
        else:
            expression_sql = f"{returning}{expression_sql}{on_conflict}"

sqlglot/expressions/ddl.py:225:class UserDefinedFunction(Expression):
sqlglot/expressions/ddl.py-226-    arg_types = {"this": True, "expressions": False, "wrapped": False}
sqlglot/expressions/ddl.py-227-
sqlglot/expressions/ddl.py-228-
sqlglot/expressions/ddl.py-229-class CharacterSet(Expression):
sqlglot/expressions/ddl.py-230-    arg_types = {"this": True, "default": False}
[tool_use Bash] {"command": "sed -n 1287,1350p sqlglot/generator.py; echo ----; grep -n \"class Create(\" -A12 sqlglot/expressions/ddl.py; grep -rn \"TABLE\\b\" sqlglot/generators/duckdb.py | grep -i \"macro\\|function\\|return\\|udf\" ; grep -n \"userdefinedfunction\\|UserDefinedFunction\\|def create_sql\\|_parse_create\\|def _parse_create\" sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/generator.py sqlglot/parser.py | head -30", "description": "Read create_sql generator and DuckDB CREATE hooks"}
[tool_result]     def create_sql(self, expression: exp.Create) -> str:
        kind = self.sql(expression, "kind")
        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind

        properties = expression.args.get("properties")

        if (
            kind == "TRIGGER"
            and properties
            and properties.expressions
            and isinstance(properties.expressions[0], exp.TriggerProperties)
            and properties.expressions[0].args.get("constraint")
        ):
   
…[2968 chars elided]…
.py:1090:        TokenType.CREATE: lambda self: self._parse_create(),
sqlglot/parser.py:1285:        "LIKE": lambda self: self._parse_create_like(),
sqlglot/parser.py:1380:        "LIKE": lambda self: self._parse_create_like(),
sqlglot/parser.py:2346:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parser.py:3296:    def _parse_create_like(self) -> exp.LikeProperty | None:
sqlglot/parser.py:7040:            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a, b) AS TABLE SELECT a, b', read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\ne = sqlglot.parse_one('CREATE MACRO t(a) AS (SELECT a)', read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n\" ; grep -n \"INVERSE_CREATABLE_KIND_MAPPING\\|CREATABLE_KIND_MAPPING\" -A3 sqlglot/dialects/duckdb.py sqlglot/dialect.py | head; grep -n \"class Return\\b\" -A3 sqlglot/expressions/*.py; grep -n \"^class Create\\|^class Macro\" sqlglot/expressions/*.py", "description": "Inspect AST for table macro and related classes"}
[tool_result] Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False),
      Identifier(this=b, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=False,
  refresh=False,
  unique=False,
  expression=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False)),
      Column(
        this=Identifier(this=b, quoted=False))]),
  exists=False,
  properties=Properties(
    expression
…[431 chars elided]…
ression=Subquery(
    this=Select(
      expressions=[
        Column(
          this=Identifier(this=a, quoted=False))])),
  exists=False,
  begin=False,
  concurrently=False)
CREATE MACRO t(a) AS (SELECT a)
ugrep: warning: sqlglot/dialect.py: No such file or directory
sqlglot/expressions/query.py:882:class Return(Expression):
sqlglot/expressions/query.py-883-    pass
sqlglot/expressions/query.py-884-
sqlglot/expressions/query.py-885-
sqlglot/expressions/ddl.py:39:class Create(Expression, DDL):
[tool_use Bash] {"command": "grep -rn \"is_table\" sqlglot/ | head; grep -n \"def _parse_function_properties\" -A30 sqlglot/parser.py | head -45", "description": "Locate table-macro property parsing"}
[tool_result] sqlglot/parser.py:3333:        is_table = self._match(TokenType.TABLE)
sqlglot/parser.py:3335:        if is_table:
sqlglot/parser.py:3350:        return self.expression(exp.ReturnsProperty(this=value, is_table=is_table, null=null))
sqlglot/schema.py:540:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:564:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:601:            parts = [sel
…[1292 chars elided]…
-        )
7042-
7043-    def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
7044-        literal = self._parse_primary()
7045-        if literal:
7046-            return self.expression(exp.Introducer(this=token.text, expression=literal), token)
7047-
7048-        return self._identifier_expression(token)
7049-
7050-    def _parse_session_parameter(self) -> exp.SessionParameter:
7051-        kind = None
7052-        this = self._parse_id_var() or self._parse_primary()
[tool_use Bash] {"command": "sed -n 3325,3352p sqlglot/parser.py; grep -n \"_parse_properties\\b\" -A3 sqlglot/parser.py | head -20; grep -n \"ReturnsProperty\" -B2 -A12 sqlglot/generators/duckdb.py | head -40; grep -n \"def returnsproperty_sql\" -A25 sqlglot/generator.py", "description": "Read returns property parsing and generation"}
[tool_result]         self._match_text_seq("WITH", "CONNECTION")
        return self.expression(
            exp.RemoteWithConnectionModelProperty(this=self._parse_table_parts())
        )

    def _parse_returns(self) -> exp.ReturnsProperty:
        value: exp.Expr | None
        null = None
        is_table = self._match(TokenType.TABLE)

        if is_table:
            if self._match(TokenType.LT):
                value = self.expression(
                    exp.Schema(this="TABLE", expressions=self._pars
…[2582 chars elided]…
_EXPRESSION,
1850-        exp.IcebergProperty: exp.Properties.Location.POST_CREATE,
1851-    }
1852-
1853-    IGNORE_RESPECT_NULLS_WINDOW_FUNCTIONS: t.ClassVar = _IGNORE_RESPECT_NULLS_WINDOW_FUNCTIONS
1854-
1855-    # Template for ZIPF transpilation - placeholders get replaced with actual parameters
1856-    ZIPF_TEMPLATE: exp.Expr = exp.maybe_parse(
1857-        """
1858-        WITH rand AS (SELECT :random_expr AS r),
1859-        weights AS (
1860-            SELECT i, 1.0 / POWER(i, :s) AS w
[assistant] The single-macro path already works; the failure is the comma after the first body. Before designing the representation, I'll check the DuckDB parser/generator structure and how `Create` is generated.
[tool_use Bash] {"command": "grep -n \"^class \\|    def _parse\\|^from\\|^import\" sqlglot/parsers/duckdb.py | head -40; grep -n \"^class \\|    def \\(\\w*\\)_sql\" sqlglot/generators/duckdb.py | head -20; sed -n 2346,2352p sqlglot/parser.py; grep -n \"def createable_sql\" -A8 sqlglot/generator.py; sed -n 225,228p sqlglot/expressions/ddl.py; grep -n \"ddl\\|query\" sqlglot/expressions/__init__.py | head -5", "description": "Inspect DuckDB parser/generator layout and Create helpers"}
[tool_result] 1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
15:from sqlglot.helper import seq_get
16:from sqlglot.parser import binary_range_parser
17:from sqlglot.tokens import TokenType
18:from collections.abc import Collection
63:    def _parse(self: DuckDBParser) -> exp.Show:
74:class DuckDBParser(parser.Parser):
237:    def _parse_function_properties(self) -> exp.Properties | None:
2
…[2871 chars elided]…
nd = self.sql(expression, "kind")
1289-        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
1290-
1291-        properties = expression.args.get("properties")
1292-
class UserDefinedFunction(Expression):
    arg_types = {"this": True, "expressions": False, "wrapped": False}


18:from sqlglot.expressions.query import *  # noqa: F401,F403
19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
43:from sqlglot.expressions.query import _apply_cte_builder  # noqa: F401,E402
[assistant] Design decision: for overloaded macros, the name stays on `Create.this` and every overload (including the first) becomes an entry in `exp.MacroOverloads`. Each entry holds its parameter list, body, and a table flag. Parsing hooks into the DuckDB parser, and generation is DuckDB-specific. Checking the existing UDF generator and `expressions()` helper first so the output matches.
[tool_use Bash] {"command": "sed -n 4585,4595p sqlglot/generator.py; grep -n \"    def expressions(\" -A12 sqlglot/generator.py | head -16; sed -n 1455,1470p sqlglot/generators/duckdb.py; grep -n \"TRANSFORMS = {\" sqlglot/generators/duckdb.py | head -2; grep -n \"def create_sql\\|def _parse_create\\|kind = \" sqlglot/parser.py | sed -n 1,10p", "description": "Read UDF generator, expressions helper, and Create kind handling"}
[tool_result]     def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
        this = self.sql(expression, "this")
        expressions = self.no_identify(self.expressions, expression)
        expressions = (
            self.wrap(expressions) if expression.args.get("wrapped") else f" {expressions}"
        )
        return f"{this}{expressions}" if expressions.strip() != "" else this

    def joinhint_sql(self, expression: exp.JoinHint) -> str:
        this = self.sql(expression, "th
…[1014 chars elided]…
E_PAIR_SEP = ","
    IGNORE_NULLS_IN_FUNC = True
1491:    TRANSFORMS = {
2185:        kind = self._match_set(self.CREATABLES) and self._prev
2299:        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
2346:    def _parse_create(self) -> exp.Create | exp.Command:
2919:        kind = "HASH"
2924:            kind = "RANDOM"
3143:            kind = "TABLE"
3145:            kind = "VIEW"
3147:            kind = "ROW"
3149:            kind = "DATABASE"
3151:            kind = None
[assistant] I have what I need. Making the edits: the expression classes first, then the parser hook, then the generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True, \"is_table\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "offset": 230, "limit": 25}
[tool_result] 230	        **parser.Parser.SET_PARSERS,
231	        "VARIABLE": lambda self: self._parse_set_item_assignment("VARIABLE"),
232	    }
233	
234	    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
235	    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)
236	
237	    def _parse_function_properties(self) -> exp.Properties | None:
238	        if self._match(TokenType.TABLE):
239	            return exp.Properties(
240	                expressions=[
241	                    exp.Retu
…[36 chars elided]…
     this=exp.Schema(this=exp.var("TABLE")),
243	                        is_table=True,
244	                    ),
245	                ]
246	            )
247	        return super()._parse_function_properties()
248	
249	    def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
250	        index = self._index
251	        if not self._match_text_seq("LAMBDA"):
252	            return super()._parse_lambda(alias=alias)
253	
254	        expressions = self._parse_csv(self._parse_lambda_arg)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "        return super()._parse_function_properties()\n\n    def _parse_lambda(", "new_string": "        return super()._parse_function_properties()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n    
…[1158 chars elided]…
) -> exp.MacroOverload:\n        params = self._parse_wrapped_csv(self._parse_function_parameter)\n        self._match(TokenType.ALIAS)\n        is_table = bool(self._match(TokenType.TABLE))\n        return self.expression(\n            exp.MacroOverload(\n                expressions=params, expression=self._parse_statement(), is_table=is_table\n            )\n        )\n\n    def _parse_lambda("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py", "offset": 2184, "limit": 8}
[tool_result] 2184	    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2185	        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
2186	        return self.sql(
2187	            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
2188	        )
2189	
2190	    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2191	        """
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py", "old_string": "    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:", "new_string": "    def create_sql(self, expression: exp.Create) -> str:\n        if not isinstance(expression.express
…[536 chars elided]…
ue)\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        params = self.wrap(self.no_identify(self.expressions, expression))\n        table = \"TABLE \" if expression.args.get(\"is_table\") else \"\"\n        return f\"{params} AS {table}{self.sql(expression, 'expression')}\"\n\n    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now a quick check of the reported cases, the single-overload path, and table/OR REPLACE variants:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = ['''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''',\n 'CREATE OR REPLACE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO t(a) AS TABLE SELECT a, (b) 
…[52 chars elided]…
a) AS a + 1, (a, b) AS TABLE SELECT a, b',\n 'CREATE MACRO f(a) AS a + 1',\n 'CREATE MACRO f() AS 1, (a) AS a',\n]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb'); print(e.sql('duckdb')); \n    except Exception as ex: print('ERR', ex)\nprint(repr(sqlglot.parse_one(cases[0], read='duckdb'))[:600])\n\"", "description": "Exercise overloaded macro parse and generate cases"}
[tool_result] 'CREATE MACRO t(a) AS TABLE SELECT a, (b) AS TABLE SELECT b' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE OR REPLACE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE MACRO t(a) AS TABLE SELECT a, (b) AS TABLE SELECT b
CREATE MACRO IF NOT EXISTS f(a) AS a + 1, (a, b) AS TABLE SELECT a, b
CREATE MACRO f(a) AS a + 1
CREATE MACRO f() AS 1, (a) AS a
Create(
  this=Table(
    this=Identifier(this=add_x, q
…[45 chars elided]…

  refresh=False,
  unique=False,
  expression=MacroOverloads(
    expressions=[
      MacroOverload(
        expressions=[
          Identifier(this=a, quoted=False),
          Identifier(this=b, quoted=False)],
        expression=Add(
          this=Column(
            this=Identifier(this=a, quoted=False)),
          expression=Column(
            this=Identifier(this=b, quoted=False))),
        is_table=False),
      MacroOverload(
        expressions=[
          Identifier(this=a, quoted=Fa
[assistant] Single-overload macros are unchanged, and the issue's example now round-trips. One limitation: a table overload followed by another overload (`AS TABLE SELECT a, (a, b) AS ...`) is ambiguous, since the trailing comma gets read as part of the SELECT list. Table overloads work when they are last. I'll note that in the final report and not paper over it. Next, the tests:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):", "new_string": "    def test_macro_overloads(self):\n        self.validate_identity(\"CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c\")\n        self.validate_ident
…[320 chars elided]…
    \"\"\"\n            CREATE MACRO add_x\n                (a, b) AS a + b,\n                (a, b, c) AS a + b + c;\n            \"\"\"\n        )\n        ast.assert_is(exp.Create).expression.assert_is(exp.MacroOverloads)\n        self.assertEqual(len(ast.expression.expressions), 2)\n        self.assertEqual(len(ast.expression.expressions[1].expressions), 3)\n\n    def test_bitwise_agg(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-091146-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k \"macro or udf\" 2>&1 | tail -30; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run DuckDB macro tests and then the full test suite"}
[tool_result] ..                                                                 [100%]
2 passed, 43 deselected, 6 subtests passed in 0.12s
.................................................................................................................................................................................................................................................................................. [ 24%]
.................................... [ 27%]
................................................
…[392 chars elided]…
......................................................... [ 69%]
....................................................................................................................................................................................... [ 85%]
................................................................................................ [ 94%]
....................... [ 96%]
.....................................                     [100%]
1114 passed, 18162 subtests passed in 57.84s
[assistant] The full suite passes (1114 tests, including the new one). Now the project's lint and format checks on the changed files:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; F=\"sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py\"; ($PY/ruff check $F; $PY/ruff format --check $F) 2>&1 | tail -15; ($PY/mypy sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -5) ; git status --short", "description": "Run ruff lint, format check and mypy on changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py:1:1

Found 1 error.
error: Failed to format sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py: No such file or directory (os error 2)
Success: no issues found in 3 source files
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/duckdb.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.py
[assistant] Ruff received the file list as one argument (zsh doesn't split unquoted variables). Re-running with explicit paths:
[tool_use Bash] {"command": "RUFF=<work>/env-sqlglot/bin/ruff; $RUFF check sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py; $RUFF format --check sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py", "description": "Run ruff check and format check on changed files"}
[tool_result ERROR] Exit code 1
All checks passed!
Would reformat: sqlglot/parsers/duckdb.py
1 file would be reformatted, 3 files already formatted
[tool_use Bash] {"command": "RUFF=<work>/env-sqlglot/bin/ruff; $RUFF format --diff sqlglot/parsers/duckdb.py 2>&1 | head -30", "description": "Show the formatting diff for the parser file"}
[tool_result] --- sqlglot/parsers/duckdb.py
+++ sqlglot/parsers/duckdb.py
@@ -259,14 +259,10 @@
         params = this.expressions if isinstance(this, exp.UserDefinedFunction) else []
         name = this.this if isinstance(this, exp.UserDefinedFunction) else this
         properties = create.args.get("properties")
-        is_table = bool(
-            properties and any(p.args.get("is_table") for p in properties.expressions)
-        )
+        is_table = bool(properties and any(p.args.get("is_table") for p in properties.expressions))
 
         overloads = [
-            exp.MacroOverload(
-                expressions=params, expression=create.expression, is_table=is_table
-            ),
+            exp.MacroOverload(expressions=params, expression=create.expression, is_table=is_table),
             self._parse_macro_overload(),
         ]
         while self._match(TokenType.COMMA):

1 file would be reformatted
[tool_use Bash] {"command": "RUFF=<work>/env-sqlglot/bin/ruff; $RUFF format sqlglot/parsers/duckdb.py && $RUFF format --check sqlglot/expressions/ddl.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py tests/dialects/test_duckdb.py && PY=<work>/env-sqlglot/bin/python && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2 && git diff --stat", "description": "Apply ruff formatting, recheck, and rerun DuckDB tests"}
[tool_result] 1 file reformatted
4 files already formatted
.....................    [100%]
45 passed, 600 subtests passed in 0.23s
 sqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generators/duckdb.py  | 17 +++++++++++++++++
 sqlglot/parsers/duckdb.py     | 37 +++++++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 19 +++++++++++++++++++
 4 files changed, 81 insertions(+)
[assistant] Overloaded DuckDB macros now parse and round-trip. The example from the issue produces `CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c`. The full test suite passes (1114 tests), and ruff check and format are clean. The changes are uncommitted in the worktree.

**Representation:** the name stays on `Create.this`, and every overload becomes an entry in `exp.MacroOverloads`. Each `exp.MacroOverload` holds its parameter list (`expressions`), its body (`expression`), and an `is_table` flag. Single-overload macros keep their existing AST shape.

**Changes:**
- `sqlglot/expressions/ddl.py`
…[623 chars elided]…
ue.

**Choices I made:**
- Output glues the parameter list to the name (`add_x(a, b)`), matching the existing single-macro output.
- Overloads are DuckDB-only. The base parser and generator are untouched apart from new methods.

**Limitation:** a table overload (`AS TABLE SELECT ...`) only works as the last overload. When it's followed by a comma, the comma is read as part of the SELECT list. Scalar overloads can appear anywhere, and a table overload can be the last one. Fixing the middle-position case would need the table body wrapped in parentheses, which is a different syntax, so I left it.
