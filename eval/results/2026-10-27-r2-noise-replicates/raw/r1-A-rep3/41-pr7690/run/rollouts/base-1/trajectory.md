# trajectory base-1

final message:
Overloaded `CREATE MACRO` now parses and round-trips in DuckDB, for scalar and table macros. The full suite passes (1113 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**Representation.** `Create.this` is the bare macro name. `Create.expression` is an `exp.MacroOverloads` with one `exp.MacroOverload` per overload, each holding its parameter list (`expressions`), its body (`expression`), and an `is_table` flag. A single-overload macro still parses exactly as before.

**Changes:**
- `sqlglot/expressions/ddl.py`: the two new node classes.
- `sqlglot/parser.py`: `_parse_create` collects the remaining `, (params) AS body` overloads after the first body. I also added a small lookahead in `_parse_join` so a subquery body followed by `, (params) AS` isn't read as an implicit comma join.
- `sqlglot/generator.py`: the create generator omits `AS` before an overload list, and renders each overload.
- `tests/dialects/test_duckdb.py`: identity tests added to `test_udf`, which runs for both `FUNCTION` and `MACRO`.

**Checked against DuckDB 1.5.6:** the generated SQL runs, and each call dispatches to the right overload (e.g. `add_x(1,2)=3`, `add_x(1,2,3)=6`, and `t(4)` / `t(4,5)` pick the matching table overload).

**Decisions to review:**
- Table overload bodies must be parenthesized (`AS TABLE (SELECT ...)`). DuckDB rejects the unparenthesized form when more overloads follow, so I followed it rather than guessing at the grammar.
- The lookahead can match `FROM a, (b) AS c`, which is treated as an overload. DuckDB rejects that form in a query anyway, so I judged it acceptable, but it's a heuristic.

## events
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py | head -80; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\""}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/ --include=*.py | grep -v \"^sqlglot/dialects/[a-z_]*.py:.*macro_\" | head -60; echo ---; grep -rn -i \"macro\" tests/ --include=*.py | head -30"}
[tool_result] (eval):1: no matches found: --include=*.py
---
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot tests --include='*.py' | grep -v -i \"macros\\b\" | head -60"}
[tool_result] sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
tests/dialects/test_clickhouse.py:57:        self.validate_identity("@macro").assert_is(exp.Parameter).this.assert_is(exp.Var)
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; grep -n \"FUNCTION\\b\" sqlglot/dialects/duckdb.py | head; grep -n \"def _parse_create\\b\" -A80 sqlglot/parser.py | grep -n -i \"function\\|kind\\|expression\" | head -40"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[3375 chars elided]…

66:2411-                    expression = self._parse_as_command(self._prev)
73:2418-                        # # https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement
74:2419-                        expression = self._parse_string()
77:2422-                        expression = (
78:2423-                            self._parse_user_defined_function_expression()
79:2424-                            if create_token_type == TokenType.FUNCTION
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -I -c \"\nimport sqlglot\nfor s in ['CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c', 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b', 'CREATE MACRO t(a) AS TABLE SELECT a']:\n  try: print(repr(sqlglot.parse_one(s, read='duckdb')))\n  except Exception as e: print('ERR', e)\n\"; sed -n 2395,2445p sqlglot/parser.py; grep -n \"def _parse_user_defined_function\" -A45 sqlglot/parser.py"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
            if properties and temp_props:
                properties.expressions.extend(temp_props.expressions)
            elif temp_props:
                properties = temp_props

        if create_token_type in (TokenType.FUNCTION, TokenType.PROCEDURE):
            this = self._parse_user_defined_function(kind=create_token_type)

            # exp.Properties.Location.POST_S
…[3763 chars elided]…
bool = False) -> exp.Expr | None:
7064-        next_token_type = self._next.token_type
7065-
7066-        # Fast path: simple atom (column, literal, null, bool) followed by , or )
7067-        if (
7068-            next_token_type in self.LAMBDA_ARG_TERMINATORS
7069-            and (atom := self._parse_atom()) is not None
7070-        ):
7071-            return atom
7072-
7073-        index = self._index
7074-
7075-        if self._match(TokenType.L_PAREN):
7076-            expressions = t.cast(
[tool_use Bash] {"command": "grep -n \"def create_sql\" -A75 sqlglot/generator.py | head -120; grep -n \"TABLE\\|Create\\|UserDefined\" sqlglot/dialects/duckdb.py | head -40"}
[tool_result] 1287:    def create_sql(self, expression: exp.Create) -> str:
1288-        kind = self.sql(expression, "kind")
1289-        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
1290-
1291-        properties = expression.args.get("properties")
1292-
1293-        if (
1294-            kind == "TRIGGER"
1295-            and properties
1296-            and properties.expressions
1297-            and isinstance(properties.expressions[0], exp.TriggerProperties)
1298-            and pro
…[2670 chars elided]…
  indexes = f" {indexes}" if indexes else ""
1353-        index_sql = indexes + postindex_props_sql
1354-
1355-        replace = " OR REPLACE" if expression.args.get("replace") else ""
1356-        refresh = " OR REFRESH" if expression.args.get("refresh") else ""
1357-        unique = " UNIQUE" if expression.args.get("unique") else ""
1358-
1359-        clustered = expression.args.get("clustered")
1360-        if clustered is None:
1361-            clustered_sql = ""
1362-        elif clustered:
[tool_use Bash] {"command": "sed -n 2360,2380p sqlglot/parser.py; grep -n \"def createable_sql\" -A12 sqlglot/generator.py; grep -n \"class Create(\" -A30 sqlglot/expressions/*.py | head -45; grep -n \"class UserDefinedFunction\" -A8 sqlglot/expressions/*.py; grep -rn \"class UserDefinedFunction\\|UserDefinedFunction\\b\" sqlglot/generator.py | head"}
[tool_result]             clustered = True
        elif self._match_text_seq("NONCLUSTERED", "COLUMNSTORE") or self._match_text_seq(
            "COLUMNSTORE"
        ):
            clustered = False
        else:
            clustered = None

        if self._match_pair(TokenType.TABLE, TokenType.FUNCTION, advance=False):
            self._advance()

        properties = None
        create_token = self._match_set(self.CREATABLES) and self._prev

        if not create_token:
            # exp.Properties.Loca
…[2568 chars elided]…
s = {"this": True, "expressions": False, "wrapped": False}
sqlglot/expressions/ddl.py-227-
sqlglot/expressions/ddl.py-228-
sqlglot/expressions/ddl.py-229-class CharacterSet(Expression):
sqlglot/expressions/ddl.py-230-    arg_types = {"this": True, "default": False}
sqlglot/expressions/ddl.py-231-
sqlglot/expressions/ddl.py-232-
sqlglot/expressions/ddl.py-233-class AlterColumn(Expression):
sqlglot/generator.py:4585:    def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c', 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b']:\n  try:\n    e=sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n  except Exception as ex: print('ERR', ex)\n\"; sed -n 4585,4592p sqlglot/generator.py; grep -n \"def _parse_create\" sqlglot/parser.py"}
[tool_result] Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      Identifier(this=a, quoted=False)],
    wrapped=True),
  kind=MACRO,
  replace=False,
  refresh=False,
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
        is_table=True
…[766 chars elided]…
_sql(self, expression: exp.UserDefinedFunction) -> str:
        this = self.sql(expression, "this")
        expressions = self.no_identify(self.expressions, expression)
        expressions = (
            self.wrap(expressions) if expression.args.get("wrapped") else f" {expressions}"
        )
        return f"{this}{expressions}" if expressions.strip() != "" else this

2346:    def _parse_create(self) -> exp.Create | exp.Command:
3296:    def _parse_create_like(self) -> exp.LikeProperty | None:
[tool_use Bash] {"command": "grep -rn \"is_table\\|_parse_user_defined_function_expression\\|CREATE_FUNCTION_RETURN_AS\" sqlglot | head -20; grep -n \"def returnsproperty_sql\" -A20 sqlglot/generator.py; grep -n \"def _parse_heredoc\" -A3 sqlglot/parser.py"}
[tool_result] sqlglot/schema.py:540:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:564:            normalized_keys = [self._normalize_name(key, is_table=True) for key in keys]
sqlglot/schema.py:601:            parts = [self._normalize_name(part, dialect=dialect, is_table=True) for part in parts]
sqlglot/schema.py:627:                        normalize_name(part, dialect=dialect, is_table=True, normalize=normalize)
sqlglot/schema.py:637:        is_tabl
…[905 chars elided]…
ouse.py:486:    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
sqlglot/parsers/duckdb.py:243:                        is_table=True,
sqlglot/optimizer/qualify_tables.py:55:        db.meta["is_table"] = True
sqlglot/optimizer/qualify_tables.py:59:        catalog.meta["is_table"] = True
9250:    def _parse_heredoc(self) -> exp.Heredoc | None:
9251-        if self._match(TokenType.HEREDOC_STRING):
9252-            return self.expression(exp.Heredoc(this=self._prev.text))
9253-
[tool_use Bash] {"command": "sed -n 215,265p sqlglot/parsers/duckdb.py; grep -n \"ReturnsProperty\" -B2 -A12 sqlglot/generator.py | head -60; ls sqlglot/parsers sqlglot/generators 2>/dev/null | head -50"}
[tool_result]         exp.DType.DECIMAL: build_default_decimal_type(precision=18, scale=3),
        # https://duckdb.org/docs/sql/data_types/text
        exp.DType.TEXT: _convert_text_type,
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.ATTACH: lambda self: self._parse_attach_detach(),
        TokenType.DETACH: lambda self: self._parse_attach_detach(is_attach=False),
        TokenType.FORCE: lambda self: self._parse_force(),
        TokenType.INSTALL: lambda self
…[3667 chars elided]…
__
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
postgres.py
presto.py
prql.py
python.py
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

sqlglot/parsers:
__init__.py
__pycache__
athena.py
base.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
[tool_use Bash] {"command": "sed -n 2346,2352p sqlglot/parser.py; sed -n 2383,2400p sqlglot/parser.py; sed -n 2440,2475p sqlglot/parser.py; grep -n \"def expressions\" -A12 sqlglot/generator.py | head -20; grep -n \"def wrap\" -A3 sqlglot/generator.py; grep -n \"def _parse_function_properties\" -A12 sqlglot/parser.py"}
[tool_result]     def _parse_create(self) -> exp.Create | exp.Command:
        # Note: this can't be None because we've matched a statement parser
        start = self._prev

        replace = (
            start.token_type == TokenType.REPLACE
            or self._match_pair(TokenType.OR, TokenType.REPLACE)

        concurrently = self._match_text_seq("CONCURRENTLY")
        exists = self._parse_exists(not_=True)
        this = None
        expression: exp.Expr | None = None
        indexes = None
        no
…[2794 chars elided]…
   def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7026-        return self._parse_statement()
7027-
7028-    def _parse_function_parameter(self) -> exp.Expr | None:
7029-        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7030-
7031-    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032-        this = self._parse_table_parts(schema=True)
7033-
7034-        if not self._match(TokenType.L_PAREN):
[assistant] Overloads need a parser change in `_parse_create` (the FUNCTION branch), a new expression node, and generator support. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n   
…[979 chars elided]…
               )\n                ]\n                while True:\n                    overloads.append(self._parse_macro_overload())\n                    if not self._match(TokenType.COMMA):\n                        break\n\n                this = this.this\n                expression = self.expression(exp.MacroOverloads(expressions=overloads))\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:", "new_string": "    def _parse_macro_overload(self) -> exp.MacroOverload:\n        expressions = self._parse_wrapped_csv(self
…[153 chars elided]…
n\n        is_table = bool(self._match(TokenType.TABLE))\n        return self.expression(\n            exp.MacroOverload(\n                expressions=expressions,\n                expression=self._parse_user_defined_function_expression(),\n                is_table=is_table,\n            )\n        )\n\n    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the expression nodes, next to `UserDefinedFunction`:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True, \"is_table\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Next, the generator: skip the `AS` keyword before an overload list, and render each overload.
[tool_use Bash] {"command": "sed -n 1027,1040p sqlglot/generator.py && sed -n 1328,1345p sqlglot/generator.py && grep -n \"def userdefinedfunction_sql\" -A8 sqlglot/generator.py"}
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
        original = s
…[935 chars elided]…
    def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
4586-        this = self.sql(expression, "this")
4587-        expressions = self.no_identify(self.expressions, expression)
4588-        expressions = (
4589-            self.wrap(expressions) if expression.args.get("wrapped") else f" {expressions}"
4590-        )
4591-        return f"{this}{expressions}" if expressions.strip() != "" else this
4592-
4593-    def joinhint_sql(self, expression: exp.JoinHint) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "                postalias_props_sql = f\" {postalias_props_sql}\" if postalias_props_sql else \"\"\n                expression_sql = f\" AS{postalias_props_sql}{expression_sql}\"", "new_string": "                postalias_props_sql = f\" {postalias_props_sql}\" if postalias_props_sql else \"\"\n                as_sql = \"\" if isinstance(expression.expression, exp.MacroOverloads) else \" AS\"\n                expression_sql = f\"{as_sql}{postalias_props_sql}{expression_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def joinhint_sql(", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def ma
…[29 chars elided]…
sion: exp.MacroOverloads) -> str:\n        return self.expressions(expression)\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        params = self.wrap(self.expressions(expression, flat=True))\n        table = \"TABLE \" if expression.args.get(\"is_table\") else \"\"\n        return f\"{params} AS {table}{self.sql(expression, 'expression')}\"\n\n    def joinhint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ncases = ['''\nCREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''', 'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b', 'CREATE OR REPLACE MACRO f() AS 1, (a) AS (SELECT a)', 'CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b']\nfor s in cases:\n  try:\n    e=sqlglot.parse_one(s, read='duckdb'); out=e.sql('duckdb'); print(out); print(sqlglot.parse_one(out,read='duckdb').sql('duckdb')==out)\n  except Exception as ex: print('ERR', ex)\nprint(repr(sqlglot.parse_one('CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c', read='duckdb')))\n\""}
[tool_result] 'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
True
CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS TABLE SELECT a + b
True
CREATE OR REPLACE MACRO f () AS 1, (a) AS (SELECT a)
True
CREATE MACRO t(a) AS TABLE SELECT
…[623 chars elided]…
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
        is_table=False)]),
  exists=False,
  begin=False,
  concurrently=False)
[assistant] Two things to fix from that run. The table-overload case I tried was a bad test: `SELECT a, (a, b) ...` makes the comma part of the select list, which is inherent to an unparenthesized body. Separately, the output `f () AS 1` has a stray space before the parameter list, and I want `add_x(a, b) AS ...`. I'll restructure the create_sql branch so overloads attach directly to the name.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        expression_sql = self.sql(expression, \"expression\")\n        if expression_sql:\n            expression_sql = f\"{begin}{self.sep()}{expression_sql}\"\n\n            if self.CREATE_FUNCTION_RETURN_AS or not 
…[156 chars elided]…
ion.expression, exp.MacroOverloads):\n            # Overloads attach directly to the name, e.g. CREATE MACRO m(a) AS a, (a, b) AS a + b\n            expression_sql = f\"{begin}{expression_sql}\"\n        elif expression_sql:\n            expression_sql = f\"{begin}{self.sep()}{expression_sql}\"\n\n            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "                as_sql = \"\" if isinstance(expression.expression, exp.MacroOverloads) else \" AS\"\n                expression_sql = f\"{as_sql}{postalias_props_sql}{expression_sql}\"", "new_string": "                expression_sql = f\" AS{postalias_props_sql}{expression_sql}\""}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ncases = ['''\nCREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''', 'CREATE OR REPLACE MACRO f() AS 1, (a) AS (SELECT a)', 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', 'CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE OR RE
…[53 chars elided]…
 AS a, (a, b) AS TABLE SELECT a + b FROM t']\nfor s in cases:\n  try:\n    e=sqlglot.parse_one(s, read='duckdb'); out=e.sql('duckdb'); print(out); print(sqlglot.parse_one(out,read='duckdb').sql('duckdb')==out)\n  except Exception as ex: print('ERR', ex)\nprint(sqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb').sql('duckdb', pretty=True))\n\""}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
True
CREATE OR REPLACE MACRO f() AS 1, (a) AS (SELECT a)
True
CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
True
CREATE MACRO t(a) AS TABLE SELECT a
True
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
True
CREATE MACRO m(a) AS a, (a, b) AS TABLE SELECT a + b FROM t
True
CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
[assistant] The `TABLE (SELECT ...)` form falls back to a Command, so something in that path raises. Checking the error:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nprint(repr(sqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)', read='duckdb', error_level=ErrorLevel.IGNORE)))\n\" 2>&1 | head -30; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE MACRO m(a) AS (SELECT a)', read='duckdb')))\" | head -5; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a)', read='duckdb')))\" | head -5"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=CREATE, expression=MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b))
Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=m, quoted=False)),
    expressions=[
Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=m, quoted=False)),
    expressions=[
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; for s in 'CREATE MACRO m(a) AS (SELECT a), (a, b) AS 1' 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS 1' 'CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS 1' 'CREATE MACRO m(a) AS 1, (a, b) AS TABLE (SELECT a)'; do PYTHONPATH=$PWD $P -c \"\nimport sqlglot,sys\nfrom sqlglot.errors import ErrorLevel\ne=sqlglot.parse_one(sys.argv[1], read='duckdb', error_level=ErrorLevel.IGNORE); print(type(e).__name__, e.sql('duckdb'))\n\" \"$s\" 2>&1 | tail -2; done"}
[tool_result] Create CREATE MACRO m(a) AS (SELECT a), (a, b) AS "1"
Create CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS "1"
Create CREATE MACRO m(a) AS TABLE SELECT a, (a, b) AS "1"
Create CREATE MACRO m(a) AS 1, (a, b) AS TABLE (SELECT a)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; for s in 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' 'CREATE MACRO m(a) AS 1, (a, b) AS TABLE (SELECT a + b)'; do PYTHONPATH=$PWD $P -c \"\nimport sqlglot,sys\nfrom sqlglot.errors import ErrorLevel\ntry:\n  e=sqlglot.parse_one(sys.argv[1], read='duckdb'); print(type(e).__name__, e.sql('duckdb'))\nexcept Exception as x: print(x)\n\" \"$s\" 2>&1 | tail -12; done"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS TABLE (SELECT a + b)
'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)
Create CREATE MACRO m(a) AS 1, (a, b) AS TABLE (SELECT a + b)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nsqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)', read='duckdb', error_level=ErrorLevel.RAISE)\n\" 2>&1 | tail -8"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\nfrom sqlglot.tokens import Tokenizer\nd=DuckDB()\ntoks=d.tokenize('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)')\np=d.parser(); p.sql='x'\nimport traceback\ntry:\n  r=p.parse(toks, 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)')\n  print(r)\nexcept Exception: traceback.print_exc()\n\" 2>&1 | tail -30"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
[Command(this=CREATE, expression=MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b))]
[tool_use Bash] {"command": "awk 'NR>=2346 && NR<=2700 && /_parse_as_command\\(start\\)|properties/ {print NR\": \"$0}' sqlglot/parser.py | tail -30"}
[tool_result] 2371:         properties = None
2376:             properties = self._parse_properties()
2379:             if not properties or not create_token:
2380:                 return self._parse_as_command(start)
2394:             nonlocal properties
2395:             if properties and temp_props:
2396:                 properties.expressions.extend(temp_props.expressions)
2398:                 properties = temp_props
2404:             extend_props(self._parse_properties())
2407:             extend_props(
…[792 chars elided]…
se_properties())
2550:                 extend_props(self._parse_properties())
2554:                 props = self._parse_properties()
2582:                 extend_props(self._parse_properties())
2589:                     extend_props(self._parse_properties())
2599:                 extend_props(self._parse_properties())
2610:             return self._parse_as_command(start)
2622:                 properties=properties,
2632:     def _parse_sequence_properties(self) -> exp.SequenceProperties | None:
[tool_use Bash] {"command": "sed -n 2600,2630p sqlglot/parser.py"}
[tool_result]             shallow = self._match_text_seq("SHALLOW")

            if self._match_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = c
…[161 chars elided]…
ING.get(create_kind_text) or create_kind_text,
                replace=replace,
                refresh=refresh,
                unique=unique,
                expression=expression,
                exists=exists,
                properties=properties,
                indexes=indexes,
                no_schema_binding=no_schema_binding,
                begin=begin,
                clone=clone,
                concurrently=concurrently,
                clustered=clustered,
            )
        )
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nfrom sqlglot.parser import Parser\norig=Parser._parse_macro_overload\ndef wrap(self):\n    print('overload start curr=', self._curr and self._curr.text, 'next=', self._next and self._next.text)\n    r=orig(self); print('overload parsed', r.sql('duckdb'), 'curr=', self._curr and self._curr.text); return r\nParser._parse_macro_overload=wrap\no=Parser._parse_create\ndef pc(self):\n    r=o(self); print('create ->', type(r).__name__); return r\nParser._parse_create=pc\nsqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)', read='duckdb')\n\" 2>&1 | tail -12"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
create -> Command
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\no=Parser._parse_user_defined_function_expression\ndef pc(self):\n    print('before body curr=', self._curr.text, self._curr.token_type)\n    r=o(self); print('body ->', r.sql('duckdb') if r else r, 'curr=', self._curr and self._curr.text); return r\nParser._parse_user_defined_function_expression=pc\nsqlglot.parse_one('CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)', read='duckdb')\n\" 2>&1 | tail -12"}
[tool_result] 'CREATE MACRO m(a) AS TABLE (SELECT a), (a, b) AS (SELECT a + b)' contains unsupported syntax. Falling back to parsing as a 'Command'.
before body curr= ( TokenType.L_PAREN
body -> (SELECT a), (a, b) curr= (
[assistant] The body parser reads `(SELECT a), (a, b)` as one tuple, so a parenthesized first body followed by a comma is misparsed. That is a real case (`AS (a + 1), (a, b) AS ...`), so I need to look at how parenthesized expressions produce tuples.
[tool_use Bash] {"command": "grep -n \"exp.Tuple(\" sqlglot/parser.py | head; grep -n \"def _parse_paren\" -A45 sqlglot/parser.py | head -80"}
[tool_result] 3757:            return self.expression(exp.Tuple(expressions=expressions))
3762:            return self.expression(exp.Tuple(expressions=[expression]))
4919:            expression: exp.Expr | None = self.expression(exp.Tuple(expressions=[start, end]))
4923:                exp.Tuple(expressions=self._parse_wrapped_csv(self._parse_bitwise))
6809:            this = self.expression(exp.Tuple())
6818:            this = self.expression(exp.Tuple(expressions=expressions))
6794:    def _parse_paren(sel
…[1362 chars elided]…
 exp.AggFunc):
6828-            return self._parse_window(this)
6829-
6830-        return this
6831-
6832-    def _parse_primary(self) -> exp.Expr | None:
6833-        if self._match_set(self.PRIMARY_PARSERS):
6834-            token_type = self._prev.token_type
6835-            primary = self.PRIMARY_PARSERS[token_type](self, self._prev)
6836-
6837-            if token_type == TokenType.STRING:
6838-                expressions = [primary]
6839-                while self._match(TokenType.STRING):
[tool_use Bash] {"command": "sed -n 3735,3765p sqlglot/parser.py; grep -n \"def _parse_statement\" -A22 sqlglot/parser.py | head -40"}
[tool_result]         )

    def _parse_partition(self) -> exp.Partition | None:
        if not self._match_texts(self.PARTITION_KEYWORDS):
            return None

        return self.expression(
            exp.Partition(
                subpartition=self._prev.text.upper() == "SUBPARTITION",
                expressions=self._parse_wrapped_csv(self._parse_disjunction),
            )
        )

    def _parse_value(self, values: bool = True) -> exp.Tuple | None:
        def _parse_value_expression() -> exp.E
…[1221 chars elided]…
        if self._match_text_seq("WHILE"):
2283-            return self._parse_whileblock()
2284-
2285-        expression = self._parse_expression()
2286-        expression = self._parse_set_operations(expression) if expression else self._parse_select()
2287-
2288-        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
2289-            expression = self._parse_pipe_syntax_query(expression)
2290-
2291-        return self._parse_query_modifiers(expression)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nd=DuckDB()\nfor s in ['(SELECT a), (a, b)', '(a + 1), (a, b)', '(a + 1)']:\n  p=d.parser()\n  toks=d.tokenize(s)\n  p.reset(); p.sql=s; p._tokens=toks; p._index=-1; p._advance()\n  r=p._parse_statement(); print(repr(s), type(r).__name__, r.sql('duckdb'), 'curr=', p._curr and p._curr.text)\n\" 2>&1 | tail -8"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 9, in <module>
AttributeError: 'NoneType' object has no attribute 'sql'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nd=DuckDB()\nfor s in ['(SELECT a), (a, b)', '(a + 1), (a, b)', '(a + 1)']:\n  p=d.parser()\n  toks=d.tokenize(s)\n  p.reset(); p.sql=s; p._tokens=toks; p._index=-1; p._advance()\n  r=p._parse_statement(); print(repr(s), type(r).__name__, r and r.sql('duckdb'), 'curr=', p._curr and p._curr.text)\n\" 2>&1 | tail -8"}
[tool_result] '(SELECT a), (a, b)' NoneType None curr= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
'(a + 1), (a, b)' NoneType None curr= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
'(a + 1)' NoneType None curr= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nimport traceback\no=Parser._parse_paren\ndef pp(self):\n    r=o(self); print('paren ->', r.__class__.__name__, r.sql('duckdb'), 'curr=', self._curr and self._curr.text); return r\nParser._parse_paren=pp\nsqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')\n\" 2>&1 | head; grep -n \"def _parse_expression\\b\" -A12 sqlglot/parser.py | head -30"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 9, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py", line 155, in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/dialects/dialect.py", line 957, in ge
…[442 chars elided]…
elf) -> exp.Expr | None:
5753-        this = self._parse_disjunction()
5754-        if not this and self._next.token_type in self.ASSIGNMENT:
5755-            # This allows us to parse <non-identifier token> := <expr>
5756-            this = exp.column(
5757-                t.cast(str, self._advance_any(ignore_reserved=True) and self._prev.text)
5758-            )
5759-
5760-        while self._match_set(self.ASSIGNMENT):
5761-            if isinstance(this, exp.Column) and len(this.parts) == 1:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\no=Parser._parse_paren\ndef pp(self):\n    r=o(self); print('paren ->', r.__class__.__name__, r.sql('duckdb'), 'curr=', self._curr and self._curr.text); return r\nParser._parse_paren=pp\nsqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')\n\" 2>&1 | head"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 8, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py", line 155, in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/dialects/dialect.py", line 957, in get_or_raise
    result = cls.get(dialect_name.strip())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/dialects/dialect.py", line 225, in get
    cls._try_load(key)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\no=Parser._parse_paren\ndef pp(self):\n    r=o(self); print('paren ->', r.__class__.__name__, r.sql('duckdb'), 'curr=', self._curr and self._curr.text); return r\nParser._parse_paren=pp\nsqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')\n\" 2>&1 | tail -15"}
[tool_result]                    ^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 6550, in _parse_column
    this = self._parse_column_reference()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 6637, in _parse_column_reference
    this = self._parse_field()
       
…[96 chars elided]…
2507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 6866, in _parse_field
    field = self._parse_primary() or self._parse_function(
            ^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 6852, in _parse_primary
    return self._parse_paren()
           ^^^^^^^^^^^^^^^^^^^
  File "<string>", line 6, in pp
AttributeError: 'NoneType' object has no attribute 'sql'
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\no=Parser._parse_paren\ndef pp(self):\n    r=o(self); print('paren ->', r and r.__class__.__name__, r and r.sql('duckdb'), 'curr=', self._curr and self._curr.text); return r\nParser._parse_paren=pp\nsqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')\n\" 2>&1 | grep paren"}
[tool_result]     return self._parse_paren()
paren -> None None curr= ROW_NUMBER
paren -> None None curr= )
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot, traceback\nfrom sqlglot import exp\nfrom sqlglot.parser import Parser\no=Parser.expression\ndef ex(self, instance=None, *a, **k):\n    if isinstance(instance, exp.Tuple):\n        print('TUPLE from:', [f.name for f in traceback.extract_stack()[-6:-1]])\n    return o(self, instance, *a, **k)\nParser.expression=ex\nprint(repr(sqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')))\n\" 2>&1 | grep -A3 \"TUPLE\" | head -20"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\no=Parser._parse_user_defined_function_expression\ndef pc(self):\n    r=o(self); print('body ->', r and r.sql('duckdb'), type(r).__name__, 'curr=', self._curr and self._curr.text); return r\nParser._parse_user_defined_function_expression=pc\nsqlglot.parse_one('CREATE MACRO m(a) AS (a + 1), (a, b) AS 1', read='duckdb')\nsqlglot.parse_one('CREATE MACRO m(a) AS (SELECT a), (a, b) AS 1', read='duckdb')\n\" 2>&1 | grep body"}
[tool_result] body -> (a + 1) Paren curr= ,
body -> 1 Literal curr= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
body -> (SELECT a), (a, b) AS "1" Subquery curr= <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfor name in ['_parse_set_operations','_parse_query_modifiers','_parse_alias','_parse_subquery']:\n  o=getattr(Parser,name)\n  def mk(o,name):\n    def f(self,*a,**k):\n      r=o(self,*a,**k)\n      if r is not None and 'Subquery' in type(r).__name__ or (r is not None and type(r).__name__=='Subquery'):\n        print(name,'->',r.sql('duckdb'),'curr=',self._curr and self._curr.text)\n      return r\n    return f\n  setattr(Parser,name,mk(o,name))\nsqlglot.parse_one('CREATE MACRO m(a) AS (SELECT a), (a, b) AS 1', read='duckdb')\n\" 2>&1 | grep -- \"->\" | head"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\ne=sqlglot.parse_one('CREATE MACRO m(a) AS (SELECT a), (a, b) AS 1', read='duckdb')\nprint(repr(e.expression)[:600])\nprint(repr(sqlglot.parse_one('SELECT 1 FROM t WHERE x IN ((SELECT a), (a, b))', read='duckdb')))\n\" 2>&1 | head -60"}
[tool_result] Subquery(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]),
  joins=[
    Join(
      this=Subquery(
        this=Table(
          this=Identifier(this=a, quoted=False),
          joins=[
            Join(
              this=Table(
                this=Identifier(this=b, quoted=False)))]),
        alias=TableAlias(
          this=Identifier(this=1, quoted=False))))])
Select(
  expressions=[
    Literal(this=1, is_string=False)],
  from_=From(
    th
…[11 chars elided]…
     this=Identifier(this=t, quoted=False))),
  where=Where(
    this=In(
      this=Column(
        this=Identifier(this=x, quoted=False)),
      expressions=[
        Subquery(
          this=Select(
            expressions=[
              Column(
                this=Identifier(this=a, quoted=False))])),
        Tuple(
          expressions=[
            Column(
              this=Identifier(this=a, quoted=False)),
            Column(
              this=Identifier(this=b, quoted=False))])])))
[assistant] The subquery body absorbs `, (a, b)` as a comma join, and a table body's select list can absorb it the same way. Before choosing a fix, I want to see how DuckDB itself handles these forms. Checking whether duckdb is available here:
[tool_use Bash] {"command": "cd /tmp && P=<work>/env-sqlglot/bin/python; $P -c \"import duckdb; print(duckdb.__version__)\" 2>&1; python3 -c \"import duckdb; print(duckdb.__version__)\" 2>&1 | tail -1"}
[tool_result] 1.5.6
1.5.6
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1
[tool_use Bash] {"command": "cd /tmp && P=<work>/env-sqlglot/bin/python; $P -c \"\nimport duckdb\nc=duckdb.connect()\ntests = [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE MACRO f(a) AS (a + 1), (a, b) AS (a * b)',\n 'CREATE MACRO f(a) AS (SELECT a), (a, b) AS 1',\n 'CREATE MACRO t(a) AS TABLE SELECT a AS x, (a, b) AS TABLE SELECT a + b AS 
…[241 chars elided]…
ABLE SELECT 1',\n]\nfor t in tests:\n  try:\n    c.execute(t); print('OK  ', t)\n  except Exception as e: print('FAIL', t, '|', str(e)[:150])\nprint(c.execute(\\\"select duckdb_functions() \\\").fetchall()[:0])\nfor r in c.execute(\\\"select function_name, macro_definition, parameters from duckdb_functions() where function_type='macro' or function_type='table_macro'\\\").fetchall(): print(r)\n\""}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 17, in <module>
_duckdb.BinderException: Binder Error: Function "duckdb_functions" is a table function but it was used as a scalar function. This function has to be called in a FROM clause (similar to a table).

LINE 1: select duckdb_functions() 
               ^
OK   CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
OK   CREATE MACRO f(a) AS (a + 1), (a, b) AS (a * b)
FAIL CREATE MACRO f(a) AS (SELECT a), (a, b) AS 
…[338 chars elided]…
a AS x), (a, b) AS TABLE (SELECT a + b AS y)
FAIL CREATE MACRO t(a) AS TABLE SELECT a AS x, (a, b) AS TABLE SELECT a + b AS y | Parser Error: syntax error at or near "SELECT"

LINE 1: CREATE MACRO t(a) AS TABLE SELECT a AS x, (a, b) AS TABLE SELECT a + b AS y
                  
FAIL CREATE MACRO t2(a) AS TABLE SELECT a AS x FROM range(1), (a, b) AS TABLE SELECT 1 | Parser Error: syntax error at or near ","

LINE 1: CREATE MACRO t2(a) AS TABLE SELECT a AS x FROM range(1), (a, b) AS TABLE SELECT 1
[assistant] DuckDB settles the body question. Table-macro bodies in an overload list must be parenthesized (`AS TABLE (SELECT ...)`), and an unparenthesized `AS TABLE SELECT ..., (a, b) AS ...` is a syntax error. The remaining problem is narrower: a parenthesized subquery body followed by `, (params) AS` gets its comma taken as an implicit join. I'll guard the comma-join path with a lookahead for the `, (params) AS` shape, so ordinary `FROM a, b` and `FROM a, (SELECT ...)` are unaffected.
[tool_use Bash] {"command": "grep -n \"TokenType.COMMA\" sqlglot/parser.py | sed -n 1,80p | grep -i \"join\\|comma)\" | head -20; grep -n \"def _parse_join(\" -A22 sqlglot/parser.py | head -40"}
[tool_result] 2434:                and self._match(TokenType.COMMA)
2454:                    if not self._match(TokenType.COMMA):
2539:            self._match(TokenType.COMMA)
2593:                        self._match(TokenType.COMMA)
2609:        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
2639:            self._match(TokenType.COMMA)
2755:        self._match(TokenType.COMMA)
2927:                self._match(TokenType.COMMA)
2943:                self._match(Toke
…[1260 chars elided]…
, "CROSS")
4443-
4444-            return cross_join
4445-
4446-        index = self._index
4447-        method, side, kind = self._parse_join_parts()
4448-        directed = self._match_text_seq("DIRECTED")
4449-        hint = self._prev.text if self._match_texts(self.JOIN_HINTS) else None
4450-        join = self._match(TokenType.JOIN) or (kind and kind.token_type == TokenType.STRAIGHT_JOIN)
4451-        join_comments = self._prev_comments
4452-
4453-        if not skip_join_token and not join:
[tool_use Bash] {"command": "grep -n \"self._tokens\\[\" sqlglot/parser.py | head -5; grep -n \"def _advance(\" -A12 sqlglot/parser.py | head -20"}
[tool_result] 2164:        sql = self._find_sql(self._tokens[0], self._tokens[-1])[: self.error_message_context]
2891:            pre_volatile_token = self._tokens[self._index - 2]
4190:        end = self._tokens[self._index - 1]
5616:        name = self._tokens[self._index + 1] if self._index + 1 < len(self._tokens) else None
5620:        alias_tok = self._tokens[self._index + 2] if self._index + 2 < len(self._tokens) else None
1885:    def _advance(self, times: i64 = 1) -> None:
1886-        index = self._index + times
1887-        self._index = index
1888-        tokens = self._tokens
1889-        size = self._tokens_size
1890-        self._curr = tokens[index] if index < size else SENTINEL_NONE
1891-        self._next = tokens[index + 1] if index + 1 < size else SENTINEL_NONE
1892-
1893-        if index > 0:
1894-            prev = tokens[index - 1]
1895-            self._prev = prev
1896-            self._prev_comments = prev.comments
1897-        else:
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\nold='''    def _parse_join(\n        self,\n        skip_join_token: bool = False,\n        parse_bracket: bool = False,\n        alias_tokens: t.Collection[TokenType] | None = None,\n    ) -> exp.Join | None:\n        if self._match(TokenType.COMMA):\n'''\nnew='''    def _parse_join(\n        self,\n        skip_j
…[1743 chars elided]…
x FROM c, d',\n 'CREATE MACRO t() AS TABLE SELECT * FROM a, (SELECT 1) AS b',\n 'CREATE OR REPLACE MACRO f() AS 1, (a) AS (SELECT a)',\n 'CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b']\nfor s in cases:\n  e=sqlglot.parse_one(s, read='duckdb'); out=e.sql('duckdb'); print(type(e).__name__, out, sqlglot.parse_one(out,read='duckdb').sql('duckdb')==out)\n\" 2>&1"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 12, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/dialects/dialect.py", line 1124, in parse
    re
…[2846 chars elided]…
, in raise_error
    raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 50.
  CREATE MACRO t() AS TABLE SELECT * FROM a, ([4mSELECT[0m 1) AS b
Create CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c True
Create CREATE MACRO f(a) AS (a + 1), (a, b) AS (a * b) True
Create CREATE MACRO f(a) AS (SELECT a), (a, b) AS 1 True
Create CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS y) True
Create CREATE MACRO t(a) AS TABLE SELECT a AS x FROM c, d True
[assistant] The lookahead is too loose: `, (SELECT 1) AS b` matches the pattern because it only checks for parens and `AS`. I'll require every token inside the parens to be a bare identifier or a comma.
[tool_use Bash] {"command": "grep -n \"    ID_VAR_TOKENS\" sqlglot/parser.py | head -3 && python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''        index += 2\n        while index < len(tokens) and tokens[index].token_type not in (\n            TokenType.L_PAREN,\n            TokenType.R_PAREN,\n        ):\n            index += 1\n\n        return (\n            index + 1 < len(tokens)\n         
…[1161 chars elided]…
 * FROM a, (b) AS c',\n 'CREATE OR REPLACE MACRO f() AS 1, () AS 2',\n 'CREATE MACRO t(a) AS TABLE SELECT a', 'CREATE OR REPLACE MACRO add_2(a, b) AS a + b']\nfor s in cases:\n  try:\n    e=sqlglot.parse_one(s, read='duckdb'); out=e.sql('duckdb'); print(type(e).__name__, out, sqlglot.parse_one(out,read='duckdb').sql('duckdb')==out)\n  except Exception as x: print('ERR', s, str(x)[:120])\n\" 2>&1"}
[tool_result] 666:    ID_VAR_TOKENS: t.ClassVar[set] = {
Create CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c True
Create CREATE MACRO f(a) AS (a + 1), (a, b) AS (a * b) True
Create CREATE MACRO f(a) AS (SELECT a), (a, b) AS 1 True
Create CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS y) True
Create CREATE MACRO t(a) AS TABLE SELECT a AS x FROM c, d True
Create CREATE MACRO t() AS TABLE SELECT * FROM a, (SELECT 1) AS b True
Create CREATE MACRO t() AS TABLE SELECT * FROM a, (b) AS c True
Create CREATE OR REPLACE MACRO f() AS 1, () AS 2 True
Create CREATE MACRO t(a) AS TABLE SELECT a True
Create CREATE OR REPLACE MACRO add_2(a, b) AS a + b True
[assistant] Round-trips now hold for all of these, and the trailing-join and subquery cases are correct. Next, tests in the existing `test_udf` in `tests/dialects/test_duckdb.py`, then the full suite.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_duckdb.py'\ns=open(p).read()\nold='''                self.validate_identity(\n                    f\"CREATE {keyword} my_table_function(a, b) AS TABLE SELECT x, y FROM (VALUES (a, b)) AS tbl(x, y)\"\n                ).assert_is(exp.Create)\n'''\nnew='''                self.validate_identity(\n                    f\"CREATE {keyword} my_table_fu
…[747 chars elided]…
date_identity(\n                    f\"CREATE {keyword} t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS y)\"\n                )\n                self.validate_identity(\n                    f\"CREATE {keyword} t(a) AS TABLE SELECT * FROM a, (b) AS c, (d, e) AS TABLE (SELECT 1)\"\n                )\n'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\necho done"}
[tool_result] done
[assistant] I added a test line I need to check: `FROM a, (b) AS c` matches the overload lookahead. Testing in DuckDB whether that form is valid there:
[tool_use Bash] {"command": "cd /tmp && P=<work>/env-sqlglot/bin/python; $P -c \"\nimport duckdb\nc=duckdb.connect()\nc.execute('create table a as select 1 as x'); c.execute('create table b as select 2 as y')\nfor q in ['SELECT * FROM a, (b) AS c', 'SELECT * FROM a, (b)', 'SELECT * FROM a, (SELECT 1) AS d', 'CREATE MACRO t() AS TABLE SELECT * FROM a, (b) AS c', 'CREATE MACRO t2() AS TABLE SELECT * FROM a, (b) AS c, (d, e) AS TABLE (SELECT 1)']:\n  try: print('OK  ', c.execute(q).fetchall() if q.startswith('SELECT') else 'created', '|', q)\n  except Exception as e: print('FAIL', q, '|', str(e).splitlines()[0][:120])\n\""}
[tool_result] FAIL SELECT * FROM a, (b) AS c | Parser Error: syntax error at or near ")"
FAIL SELECT * FROM a, (b) | Parser Error: syntax error at or near ")"
OK   [(1, 1)] | SELECT * FROM a, (SELECT 1) AS d
OK   created | CREATE MACRO t() AS TABLE SELECT * FROM a, (b) AS c
OK   created | CREATE MACRO t2() AS TABLE SELECT * FROM a, (b) AS c, (d, e) AS TABLE (SELECT 1)
Shell cwd was reset to ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1
[assistant] DuckDB rejects `FROM a, (b) AS c` at query time, so the false positive only touches SQL that DuckDB can't use anyway. I'll drop that edge case from the test, keep the cases DuckDB accepts, and then run the suite.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_duckdb.py'\ns=open(p).read()\nold='''                self.validate_identity(\n                    f\"CREATE {keyword} t(a) AS TABLE SELECT * FROM a, (b) AS c, (d, e) AS TABLE (SELECT 1)\"\n                )\n'''\nnew='''                self.validate_identity(\n                    f\"CREATE {keyword} t(a) AS TABLE SELECT * FROM a, (SELECT 1) AS b\"\n                )\n'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\nP=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -15"}
[tool_result] ........................ [ 54%]
....................   [100%]
44 passed, 602 subtests passed in 0.32s
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"import sqlglot,sys; print(sqlglot.__file__)\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py -k test_udf 2>&1 | tail -3; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] ~/.cache/lithify/work/repo-90e86f132b84/20261028-132507-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py
.                                                                [100%]
1 passed, 43 deselected, 8 subtests passed in 0.05s
.............. [ 29%]
............... [ 31%]
................ [ 32%]
...................................................................................................................................................................... [ 47%]
.....
…[221 chars elided]…
................................................. [ 69%]
................................................................................................................................................. [ 82%]
...................................... [ 85%]
................................................................................................ [ 94%]
....................... [ 96%]
......................................                    [100%]
1113 passed, 18164 subtests passed in 52.01s
[assistant] Full suite passes (1113 passed). Next I'll confirm that DuckDB accepts the generated SQL and that the overloads resolve, then run the linters on the changed files.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot, duckdb\nsrc='''CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;\nCREATE OR REPLACE MACRO f(a) AS (a + 1), (a, b) AS (a * b);\nCREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS y);'''\nout=sqlglot.transpile(src, read='duckdb', writ
…[230 chars elided]…
dd_x(1,2,3), f(3), f(2,5)').fetchall())\nprint(c.execute('select * from t(4)').fetchall(), c.execute('select * from t(4, 5)').fetchall())\nprint(sqlglot.transpile(src, read='duckdb', write='duckdb', pretty=True)[0])\n\"; ruff --version 2>/dev/null; $P -m ruff check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -3; $P -m ruff format --check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -3"}
[tool_result] CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE OR REPLACE MACRO f(a) AS (a + 1), (a, b) AS (a * b)
CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS y)

[(3, 6, 4, 10)]
[(4,)] [(9,)]
CREATE MACRO add_x  (
    a, b
  ) AS a + b,
  (
    a, b, c
  ) AS a + b + c
ruff 0.15.6
All checks passed!
177 files already formatted
[assistant] DuckDB accepts the output and dispatches each overload correctly (`add_x(1,2)=3`, `add_x(1,2,3)=6`, `t(4)` picks the one-parameter table overload, `t(4,5)` the two-parameter one). The pretty output has extra spacing, so I'll compare it against the existing single-macro pretty output to confirm it matches house style:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $P -c \"\nimport sqlglot\nprint(sqlglot.transpile('CREATE MACRO add_2(a, b) AS a + b', read='duckdb', write='duckdb', pretty=True)[0]); print('---')\nprint(sqlglot.transpile('CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c', read='duckdb', write='duckdb', pretty=True)[0])\""}
[tool_result] CREATE MACRO add_2(
    a,
    b
) AS
a + b
---
CREATE MACRO add_x  (
    a, b
  ) AS a + b,
  (
    a, b, c
  ) AS a + b + c
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/generator.py'\ns=open(p).read()\nold='''    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression)\n'''\nnew='''    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)\n'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace
…[171 chars elided]…
RO add_x(a, b) AS a + b, (a, b, c) AS a + b + c', read='duckdb', write='duckdb', pretty=True)[0])\nprint(sqlglot.transpile('CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c', read='duckdb', write='duckdb')[0])\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -1; $P -m ruff check sqlglot tests && $P -m ruff format --check sqlglot tests | tail -1"}
[tool_result] CREATE MACRO add_x(
  a, b
) AS a + b, (
  a, b, c
) AS a + b + c
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
44 passed, 602 subtests passed in 0.23s
All checks passed!
237 files already formatted
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] Linting passes. The pretty output now matches the house style of the single-macro form. The system note about `generator.py` is from my own scripted edit a moment ago, which is expected. Last, a type check on the touched modules, since the project runs mypy in pre-commit:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m mypy --version 2>&1 | tail -1; timeout 600 $P -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -5; git status --short; git diff --stat"}
[tool_result] mypy 2.3.0.post2 (compiled: yes)
(eval):1: command not found: timeout
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
 sqlglot/expressions/ddl.py    |  8 ++++++
 sqlglot/generator.py          | 13 ++++++++-
 sqlglot/parser.py             | 67 +++++++++++++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 17 +++++++++++
 4 files changed, 104 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -5"}
[tool_result] Success: no issues found in 3 source files
[assistant] Type check is clean. Running the full suite once more after the last generator change:
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git diff sqlglot/parser.py | head -120"}
[tool_result] ......................................                    [100%]
1113 passed, 18164 subtests passed in 54.80s
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 73e0520b5..b8140c92e 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -2427,6 +2427,35 @@ class Parser:
 
                     if return_:
                         expression = self.expression(exp.Return(this=expression))
+
+            if (
+                create_token_type == TokenType.FUNCTION
+                and isin
…[2994 chars elided]…
r("Expected AS after macro overload parameters")
+
+        is_table = bool(self._match(TokenType.TABLE))
+        return self.expression(
+            exp.MacroOverload(
+                expressions=expressions,
+                expression=self._parse_user_defined_function_expression(),
+                is_table=is_table,
+            )
+        )
+
     def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
         this = self._parse_table_parts(schema=True)
[assistant] Overloaded `CREATE MACRO` now parses and round-trips in DuckDB, for scalar and table macros. The full suite passes (1113 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

**Representation.** `Create.this` is the bare macro name. `Create.expression` is an `exp.MacroOverloads` with one `exp.MacroOverload` per overload, each holding its parameter list (`expressions`), its body (`expression`), and an `is_table` flag. A single-overload macro still parses exactly as before.

**Changes:**
- `sqlglot/expressions/ddl.py`: the two new node classes.
- `sqlglot/parse
…[452 chars elided]…
RO`.

**Checked against DuckDB 1.5.6:** the generated SQL runs, and each call dispatches to the right overload (e.g. `add_x(1,2)=3`, `add_x(1,2,3)=6`, and `t(4)` / `t(4,5)` pick the matching table overload).

**Decisions to review:**
- Table overload bodies must be parenthesized (`AS TABLE (SELECT ...)`). DuckDB rejects the unparenthesized form when more overloads follow, so I followed it rather than guessing at the grammar.
- The lookahead can match `FROM a, (b) AS c`, which is treated as an overload. DuckDB rejects that form in a query anyway, so I judged it acceptable, but it's a heuristic.
