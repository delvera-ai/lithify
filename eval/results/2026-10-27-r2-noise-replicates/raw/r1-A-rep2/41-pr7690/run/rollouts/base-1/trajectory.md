# trajectory base-1

final message:
Overloaded `CREATE MACRO` now parses and round-trips in DuckDB, for scalar and table macros. The issue's example produces `exp.MacroOverloads` with two `MacroOverload` entries, and the generated SQL runs in DuckDB 1.5.6 with the right overloads resolving (`add_x(1, 2) = 3`, `add_x(1, 2, 3) = 6`). The full suite passes (1114), and ruff and mypy are clean. I haven't committed.

**Representation**
- Single-overload macros are unchanged. With two or more overloads, `Create.this` is the macro name and `Create.expression` is a `MacroOverloads` node. Each entry is a `MacroOverload(parameters=Tuple, expression=body)`.
- The output is `CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c`. The space before the first parameter list is valid DuckDB.

**Table macros**
- DuckDB only accepts table overloads in the parenthesised form `AS TABLE (SELECT ...)`. An unparenthesised `TABLE SELECT ...` can't be followed by another overload, because DuckDB folds the comma into the SELECT list. I matched that: sqlglot emits `TABLE(SELECT ...)` for overload bodies.
- The `TABLE` keyword on the first body is parsed as a create property, so I move it onto that body when overloads are present.

**Code changes**
- `sqlglot/expressions/ddl.py`: new `MacroOverload` and `MacroOverloads` nodes.
- `sqlglot/parser.py`: the MACRO branch of `_parse_create` now detects a following comma and calls `_parse_macro_overloads`. `_parse_macro_body` parses parenthesised query bodies with `_parse_wrapped`. Without that, the query-modifier logic reads the overload comma as an implicit join.
- `sqlglot/generator.py`: `macrooverload_sql` and `macrooverloads_sql`. The `AS` prefix is skipped for `MacroOverloads`, because each overload carries its own.
- `tests/dialects/test_duckdb.py`: new `test_macro_overloads` covering the issue's example, scalar, parenthesised-query, and table overloads.

If you want the commit made, I'll commit on a branch. Per the repo's CLAUDE.md, the PR title and commit message need the model name appended.

## events
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/tokens.py | head -80; git log --oneline -1", "description": "Find macro references in sqlglot source"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
116ea8210 lithify: probe base
[tool_use Bash] {"command": "ls; grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/*.py sqlglot/tokens.py 2>/dev/null | head -80; grep -rn \"MACRO\" tests/dialects/test_duckdb.py | head -30", "description": "Search macro handling across sqlglot and tests"}
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
tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; sed -n 80,110p sqlglot/dialects/duckdb.py; grep -n \"FUNCTION\\b\" sqlglot/parser.py | head; grep -n \"def _parse_create\" -A5 sqlglot/parser.py | head -20; grep -n \"class Create\\b\" -A30 sqlglot/expressions/*.py | head -50", "description": "Inspect existing macro tests and create parsing"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[6392 chars elided]…
 kind = self.args.get("kind")
sqlglot/expressions/ddl.py-61-        return kind and kind.upper()
sqlglot/expressions/ddl.py-62-
sqlglot/expressions/ddl.py-63-
sqlglot/expressions/ddl.py-64-class SequenceProperties(Expression):
sqlglot/expressions/ddl.py-65-    arg_types = {
sqlglot/expressions/ddl.py-66-        "increment": False,
sqlglot/expressions/ddl.py-67-        "minvalue": False,
sqlglot/expressions/ddl.py-68-        "maxvalue": False,
sqlglot/expressions/ddl.py-69-        "cache": False,
[tool_use Bash] {"command": "sed -n 2346,2470p sqlglot/parser.py; grep -n \"class Create\\|class Function\\|class UserDefinedFunction\\|class .*Macro\" sqlglot/expressions/*.py", "description": "Read _parse_create function/macro branch"}
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
…[4473 chars elided]…
= self._parse_trigger_referencing()
            for_each = self._parse_trigger_for_each()
            when = self._match_text_seq("WHEN") and self._parse_wrapped(
                self._parse_disjunction, optional=True
            )
            execute = self._parse_trigger_execute()

            if execute is None:
                return self._parse_as_command(start)
sqlglot/expressions/ddl.py:39:class Create(Expression, DDL):
sqlglot/expressions/ddl.py:225:class UserDefinedFunction(Expression):
[tool_use Bash] {"command": "grep -n \"def _parse_user_defined_function\" -A40 sqlglot/parser.py | head -90; sed -n 220,240p sqlglot/expressions/ddl.py; grep -n \"UserDefinedFunction\\|AS TABLE\\|\\\"TABLE\\\"\" sqlglot/dialects/duckdb.py sqlglot/generator.py | head; grep -n \"def create_sql\" -A5 sqlglot/generator.py | head -3; grep -n \"_parse_user_defined_function_expression\" -A12 sqlglot/parser.py | head -30", "description": "Read UDF parsing and generation code"}
[tool_result] 7025:    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7026-        return self._parse_statement()
7027-
7028-    def _parse_function_parameter(self) -> exp.Expr | None:
7029-        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7030-
7031:    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032-        this = self._parse_table_parts(schema=True)
7033-
7034-        if not self._match(TokenType.L_P
…[3287 chars elided]…
ment()
7027-
7028-    def _parse_function_parameter(self) -> exp.Expr | None:
7029-        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7030-
7031-    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7032-        this = self._parse_table_parts(schema=True)
7033-
7034-        if not self._match(TokenType.L_PAREN):
7035-            return this
7036-
7037-        expressions = self._parse_csv(self._parse_function_parameter)
[tool_use Bash] {"command": "sed -n 2470,2530p sqlglot/parser.py; sed -n 1287,1300p sqlglot/generator.py; grep -n \"expression_sql\\|def create_sql\" sqlglot/generator.py | sed -n 1,5p; sed -n 1300,1420p sqlglot/generator.py | grep -n \"FUNCTION\\|PROCEDURE\\|expression\\|kind\" ; sed -n 4585,4600p sqlglot/generator.py; grep -n \"CREATE_FUNCTION_RETURN_AS\\|class Generator\" sqlglot/dialects/duckdb.py | head; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.__file__)\"", "description": "Read remaining create parsing and generator bits"}
[tool_result]                 return self._parse_as_command(start)

            trigger_props = self.expression(
                exp.TriggerProperties(
                    table=table,
                    timing=timing,
                    events=events,
                    execute=execute,
                    constraint=is_constraint,
                    referenced_table=referenced_table,
                    deferrable=deferrable,
                    initially=initially,
                    referencing=refer
…[5840 chars elided]…
 f"{this}{expressions}" if expressions.strip() != "" else this

    def joinhint_sql(self, expression: exp.JoinHint) -> str:
        this = self.sql(expression, "this")
        expressions = self.expressions(expression, flat=True)
        return f"{this}({expressions})"

    def kwarg_sql(self, expression: exp.Kwarg) -> str:
        return self.binary(expression, "=>")

~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py
[tool_use Bash] {"command": "sed -n 1300,1345p sqlglot/generator.py; grep -n \"_parse_create\\|class Parser\" sqlglot/dialects/duckdb.py; grep -n \"CREATE_FUNCTION_RETURN_AS\" sqlglot/*.py sqlglot/dialects/duckdb.py; <work>/env-sqlglot/bin/python -c \"import duckdb;print(duckdb.__version__)\"; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''', read='duckdb')))\" 2>&1 | tail -5", "description": "Inspect create generation and reproduce failure"}
[tool_result]             kind = f"CONSTRAINT {kind}"

        properties_locs = self.locate_properties(properties) if properties else defaultdict()

        this = self.createable_sql(expression, properties_locs)

        properties_sql = ""
        if properties_locs.get(exp.Properties.Location.POST_SCHEMA) or properties_locs.get(
            exp.Properties.Location.POST_WITH
        ):
            props_ast = exp.Properties(
                expressions=[
                    *properties_locs[exp.Properties.
…[1451 chars elided]…
s_sql = ""
        if properties_locs.get(exp.Properties.Location.POST_INDEX):
            postindex_props_sql = self.properties(
sqlglot/generator.py:319:    CREATE_FUNCTION_RETURN_AS = True
sqlglot/generator.py:1331:            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):
1.5.6
    raise error
sqlglot.errors.ParseError: Invalid expression / Unexpected token. Line 2, Col: 20.
  CREATE MACRO add_x
    (a, b) AS a + b[4m,[0m
    (a, b, c) AS a + b + c;
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|ddl\" sqlglot/expressions/__init__.py | head -20; grep -n \"def tuple_sql\" -A12 sqlglot/generator.py; grep -n \"def expressions\" -A3 sqlglot/generator.py | head -5; grep -n \"class Tuple\" -A3 sqlglot/expressions/*.py | head; grep -n \"UserDefinedFunction\" -r sqlglot | grep -v \"^sqlglot/parser.py\\|generator.py:4585\" | head", "description": "Check exports, tuple generation and UDF references"}
[tool_result] 14:from sqlglot.expressions.core import *  # noqa: F401,F403
15:from sqlglot.expressions.datatypes import *  # noqa: F401,F403
16:from sqlglot.expressions.constraints import *  # noqa: F401,F403
17:from sqlglot.expressions.properties import *  # noqa: F401,F403
18:from sqlglot.expressions.query import *  # noqa: F401,F403
19:from sqlglot.expressions.ddl import *  # noqa: F401,F403
20:from sqlglot.expressions.dml import *  # noqa: F401,F403
21:from sqlglot.expressions.math import *  # noqa: F401,
…[1722 chars elided]…
ery.py-887-    arg_types = {"expressions": False}
sqlglot/expressions/query.py-888-
sqlglot/expressions/query.py-889-    def isin(
sqlglot/parsers/tsql.py:650:        if kind == TokenType.FUNCTION or isinstance(this, exp.UserDefinedFunction):
sqlglot/parsers/tsql.py:668:        return self.expression(exp.UserDefinedFunction(this=this))
sqlglot/dialects/bigquery.py:136:                isinstance(parent, exp.UserDefinedFunction)
sqlglot/expressions/ddl.py:225:class UserDefinedFunction(Expression):
[assistant] Current behaviour confirmed: the second overload's comma is the parse failure. DuckDB 1.5.6 is installed in the project env, so I can verify round-trips against the real engine. Making the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"parameters\": True, \"expression\": True}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"expressions\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n   
…[3 chars elided]…
                  expression = self.expression(exp.Return(this=expression))\n\n            if (\n                create_token.text.upper() == \"MACRO\"\n                and expression\n                and self._match(TokenType.COMMA, advance=False)\n            ):\n                this, expression = self._parse_macro_overloads(this, expression)\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "            if (\n                create_token.text.upper() == \"MACRO\"\n                and expression\n                and self._match(TokenType.COMMA, advance=False)\n            ):", "new_string": "            if (\n                create_token.text.upper() == \"MACRO\"\n                and isinstance(this, exp.UserDefinedFunction)\n                and expression is not None\n                and self._match(TokenType.COMMA, advance=False)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        expressions = self._parse_csv(self._parse_function_parameter)\n        self._match_r_paren()\n        return self.expression(\n            exp.UserDefinedFunction(this=this, expressions=expressions, wrapped=True)
…[812 chars elided]…
     overloads.append(\n                self.expression(\n                    exp.MacroOverload(\n                        parameters=exp.Tuple(expressions=parameters),\n                        expression=self._parse_user_defined_function_expression(),\n                    )\n                )\n            )\n\n        return this.this, self.expression(exp.MacroOverloads(expressions=overloads))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the generator: skip the `AS` prefix for overloads (each overload carries its own `AS`), and emit each overload.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):", "new_string": "            if not isinstance(expression.expression, exp.MacroOverloads) and (\n                self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return)\n            ):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py", "old_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def joinhint_sql(", "new_string": "        return f\"{this}{expressions}\" if expressions.strip() != \"\" else this\n\n    def macrooverload_sql(self, expression: exp.MacroOverload) -> str:\n        return f\"{self.sql(expression, 'parameters')} AS {self.sql(expression, 'expression')}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        return self.expressions(expression, flat=True)\n\n    def joinhint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nqs = ['''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''',\n'CREATE OR REPLACE MACRO m(a) AS a, () AS 1, (x, y) AS x * y',\n'CREATE MACRO t(a) AS TABLE SELECT a, 1 AS b, (c) AS d FROM x WHERE 1=1',\n'CREATE MACRO t1(a) AS TABLE SELEC
…[5 chars elided]…
ROM x, (a, b) AS z',\n'CREATE MACRO t2(a) AS TABLE SELECT a FROM x, (a, b) AS z',\n]\nfor q in qs:\n  try:\n    e = sqlglot.parse_one(q, read='duckdb')\n    print(repr(e.expression)[:200] if isinstance(e.expression, exp.MacroOverloads) else 'single', '|', e.sql('duckdb'))\n  except Exception as ex: print('ERR', ex)\n\" 2>&1 | tail -30", "description": "Try overloaded macro round-trips in sqlglot"}
[tool_result] MacroOverloads(
  expressions=[
    MacroOverload(
      parameters=Tuple(
        expressions=[
          Identifier(this=a, quoted=False),
          Identifier(this=b, quoted=False)]),
      express | CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
MacroOverloads(
  expressions=[
    MacroOverload(
      parameters=Tuple(
        expressions=[
          Identifier(this=a, quoted=False)]),
      expression=Column(
        this=Identifier(this=a,  | CREATE OR REPLACE MACRO m (a) AS a, () AS 1, (x, y) AS x * y
single | CREATE MACRO t(a) AS TABLE SELECT a, 1 AS b, (c) AS d FROM x WHERE 1 = 1
single | CREATE MACRO t1(a) AS TABLE SELECT a FROM x, (a, b) AS z
single | CREATE MACRO t2(a) AS TABLE SELECT a FROM x, (a, b) AS z
[assistant] Parsing and generation work for the issue's example. Now checking the output against real DuckDB: it must accept the generated SQL and resolve each overload correctly, including table macros.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nimport duckdb, sqlglot\ncon = duckdb.connect()\nsql = sqlglot.transpile('''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''', read='duckdb', write='duckdb')[0]\nprint(sql)\ncon.execute(sql)\nprint(con.sql('SELECT add_x(1, 2), add_x(1, 2, 3)').fetchall())\nt = sqlglot.tran
…[56 chars elided]…
, (a, 2) AS z_, (a) AS q, 3 AS w, (2, 3) AS r', read='duckdb', write='duckdb')[0]\nprint(t)\nfor q in ['CREATE MACRO tm(a) AS TABLE SELECT a AS x, 1 AS y', 'CREATE MACRO tm2(a) AS TABLE SELECT a AS x, 1 AS y, (a, 3) AS z']:\n    try: con.execute(q); print('ok', q)\n    except Exception as e: print('ERR', q, str(e)[:120])\n\" 2>&1 | tail -20", "description": "Execute generated macro SQL in DuckDB"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb, sqlglot\ncon = duckdb.connect()\nsql = sqlglot.transpile('''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''', read='duckdb', write='duckdb')[0]\nprint(sql)\ncon.execute(sql)\nprint(con.sql('SELECT add_x(1, 2), add_x(1, 2, 3)').fetchall())\nt = sqlglot.transpi
…[53 chars elided]…
, (a, 2) AS z_, (a) AS q, 3 AS w, (2, 3) AS r', read='duckdb', write='duckdb')[0]\nprint(t)\nfor q in ['CREATE MACRO tm(a) AS TABLE SELECT a AS x, 1 AS y', 'CREATE MACRO tm2(a) AS TABLE SELECT a AS x, 1 AS y, (a, 3) AS z']:\n    try: con.execute(q); print('ok', q)\n    except Exception as e: print('ERR', q, str(e)[:120])\n\" 2>&1 | tail -20", "description": "Execute generated macro SQL in DuckDB"}
[tool_result] CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
[(3, 6)]
CREATE MACRO tm(a) AS TABLE SELECT a AS x, 1 AS y, (a, 2) AS z_, (a) AS q, 3 AS w, (2, 3) AS r
ok CREATE MACRO tm(a) AS TABLE SELECT a AS x, 1 AS y
ok CREATE MACRO tm2(a) AS TABLE SELECT a AS x, 1 AS y, (a, 3) AS z
[assistant] Scalar overloads execute correctly in DuckDB (`add_x(1,2)=3`, `add_x(1,2,3)=6`). The table-macro cases above are ambiguous: DuckDB itself may fold the comma into the SELECT list. I'll check what DuckDB does with real table overloads before deciding how to handle them.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb, sqlglot\ncon = duckdb.connect()\ntests = [\n 'CREATE MACRO t1(a) AS TABLE SELECT a AS x, 1 AS y, (a, 3) AS z',\n 'CREATE MACRO t2(a) AS TABLE SELECT a AS x, (a, 3) AS z',\n 'CREATE MACRO t3(a) AS TABLE SELECT a AS x, 1 AS y\\n    (a, b) AS TABLE SELECT 1 AS x, 2 AS y',\n 'CREATE MAC
…[133 chars elided]…
, (a, b) AS TABLE SELECT 1 AS x, 2 AS y',\n]\nfor q in tests:\n    try: con.execute(q); print('ok', repr(q))\n    except Exception as e: print('ERR', repr(q), str(e)[:150])\nprint(con.sql(\\\"select function_name, parameters, function_type from duckdb_functions() where function_name like 't%'\\\").fetchall())\n\" 2>&1 | tail -20", "description": "Probe DuckDB behaviour with table macro overloads"}
[tool_result] ok 'CREATE MACRO t1(a) AS TABLE SELECT a AS x, 1 AS y, (a, 3) AS z'
ok 'CREATE MACRO t2(a) AS TABLE SELECT a AS x, (a, 3) AS z'
ERR 'CREATE MACRO t3(a) AS TABLE SELECT a AS x, 1 AS y\n    (a, b) AS TABLE SELECT 1 AS x, 2 AS y' Parser Error: syntax error at or near "("

LINE 2:     (a, b) AS TABLE SELECT 1 AS x, 2 AS y
            ^
ERR 'CREATE MACRO t4(a) AS TABLE SELECT a AS x, 1 AS y, (a, b) AS TABLE SELECT 1 AS x, 2 AS y' Parser Error: syntax error at or near "SELECT"

LINE 1: ... MACRO t4(a)
…[4091 chars elided]…
'scalar'), ('trunc', ['x', 'col1'], 'scalar'), ('trunc', ['x'], 'scalar'), ('trunc', ['x', 'col1'], 'scalar'), ('trunc', ['x'], 'scalar'), ('trunc', ['x', 'col1'], 'scalar'), ('trunc', ['x'], 'scalar'), ('trunc', ['x', 'col1'], 'scalar'), ('try_strptime', ['text', 'format'], 'scalar'), ('try_strptime', ['text', 'format'], 'scalar'), ('txid_current', [], 'scalar'), ('typeof', ['expression'], 'scalar'), ('table_info', ['col0'], 'pragma'), ('t2', ['a'], 'table_macro'), ('t1', ['a'], 'table_macro')]
[assistant] DuckDB folds the comma into the SELECT list for table bodies, and its `(a, b) AS TABLE SELECT ...` overload form is a syntax error. I need to find which table-overload forms DuckDB really accepts before deciding the table case.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb\ntests = [\n 'CREATE MACRO u1(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)',\n 'CREATE MACRO u2(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)',\n 'CREATE MACRO u3(a) AS TABLE SELECT 1 AS x, (a, b) AS TABLE SELECT 2 AS x',\n 'CREATE MACRO u4(a) AS TABLE SELECT a AS 
…[401 chars elided]…
',\n]\ncon = duckdb.connect()\nfor q in tests:\n    try: con.execute(q); print('ok ', q)\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0][:110])\nprint(con.sql(\\\"select function_name, parameters, function_type from duckdb_functions() where function_name like 'u%'\\\").fetchall())\n\" 2>&1 | tail -30", "description": "Probe which table-macro overload forms DuckDB accepts"}
[tool_result] ok  CREATE MACRO u1(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
ok  CREATE MACRO u2(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
ERR CREATE MACRO u3(a) AS TABLE SELECT 1 AS x, (a, b) AS TABLE SELECT 2 AS x -> Parser Error: syntax error at or near "SELECT"
ERR CREATE MACRO u4(a) AS TABLE SELECT a AS x (a, b) AS TABLE SELECT 2 AS x -> Parser Error: syntax error at or near "("
ERR CREATE MACRO u5(a) AS TABLE SELECT a AS x, (a, b) AS (SELECT 2 AS x) -> Parser Error: syntax error
…[767 chars elided]…
ring'], 'scalar'), ('unpivot_list', [], 'scalar'), ('union_value', [], 'scalar'), ('union_tag', ['union'], 'scalar'), ('union_extract', ['union', 'tag'], 'scalar'), ('unicode', ['string'], 'scalar'), ('unhex', ['value'], 'scalar'), ('ucase', ['string'], 'scalar'), ('user_agent', [], 'pragma'), ('u2', ['a'], 'macro'), ('u2', ['a', 'b'], 'macro'), ('user', [], 'macro'), ('u6', ['a'], 'table_macro'), ('u6', ['a', 'b'], 'table_macro'), ('u1', ['a'], 'table_macro'), ('u1', ['a', 'b'], 'table_macro')]
[assistant] DuckDB accepts table overloads only in the parenthesised form `AS TABLE (SELECT ...)` (u1, u6), and `AS (SELECT ...)` for scalar-style bodies (u2). Checking that sqlglot parses and round-trips those forms:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb, sqlglot\nqs = [\n 'CREATE MACRO u1(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)',\n 'CREATE MACRO u2(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)',\n 'CREATE MACRO u6(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT 2 AS x)',\n 'CREATE MACRO s(a) AS TABLE (SELECT a AS x)',\n]\ncon = duckdb.connect()\nfor q in qs:\n    try:\n        out = sqlglot.transpile(q, read='duckdb', write='duckdb')[0]\n        print('SQLGLOT:', out)\n        con.execute(out); print('  duckdb ok')\n    except Exception as e: print('ERR', q, '->', str(e).splitlines()[0][:160])\n\" 2>&1 | tail -30", "description": "Round-trip table-macro overloads through sqlglot and DuckDB"}
[tool_result] 'CREATE MACRO u1(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u2(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO u6(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
SQLGLOT: CREATE MACRO u1(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
  duckdb ok
SQLGLOT: CREATE MACRO u2(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
  duckdb ok
SQLGLOT: CREATE MACRO u6(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT 2 AS x)
  duckdb ok
SQLGLOT: CREATE MACRO s(a) AS TABLE (SELECT a AS x)
  duckdb ok
[assistant] sqlglot falls back to `Command` for the parenthesised forms. Narrowing down which piece fails:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in ['CREATE MACRO s(a) AS TABLE (SELECT a AS x)','CREATE MACRO s(a) AS (SELECT 1)','CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)','CREATE MACRO s(a) AS a, (a, b) AS TABLE (SELECT 2)','CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b', 'CREATE MACRO s(a) AS a, (a, b) AS (SELECT 2)', 'CREATE MACRO s(a) AS a, (a, b) AS TABLE (SELECT 2)']:\n  e = sqlglot.parse_one(q, read='duckdb')\n  print(type(e).__name__, '|', q, '=>', e.sql('duckdb') if hasattr(e,'sql') else e)\n\" 2>&1 | grep -v \"^ *$\" | head -30", "description": "Narrow down which macro body form fails to parse"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b' contains unsupported syntax. Falling back to parsing as a 'Command'.
Create | CREATE MACRO s(a) AS TABLE (SELECT a AS x) => CREATE MACRO s(a) AS TABLE (SELECT a AS x)
Create | CREATE MACRO s(a) AS (SELECT 1) => CREATE MACRO s(a) AS (SELECT 1)
Command | CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2) => CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)
Create | CREATE MACRO s(a) AS a, (a, b) AS TABLE (SELECT 2) => CREATE MACRO s (a) AS a, (a, b) AS TABLE(SELECT 2)
Command | CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b => CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b
Create | CREATE MACRO s(a) AS a, (a, b) AS (SELECT 2) => CREATE MACRO s (a) AS a, (a, b) AS (SELECT 2)
Create | CREATE MACRO s(a) AS a, (a, b) AS TABLE (SELECT 2) => CREATE MACRO s (a) AS a, (a, b) AS TABLE(SELECT 2)
[assistant] Two issues: a parenthesised first body (`AS (SELECT 1), ...`) falls back to `Command`, and table bodies print as `TABLE(SELECT ...)`. Checking what the first-body parse returns in the `(SELECT 1)` case:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.parser import Parser\norig = Parser._parse_macro_overloads\ndef spy(self, this, expression):\n    print('BODY:', repr(expression)[:300]); print('NEXT:', self._curr, self._next, self._prev)\n    return orig(self, this, expression)\nParser._parse_macro_overloads = spy\nfor q in ['CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', 'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b']:\n    e = sqlglot.parse_one(q, read='duckdb'); print(type(e).__name__)\n\" 2>&1 | head -40", "description": "Inspect body parse for parenthesised first overload"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command
Command
[assistant] The hook never fires, so the failure happens earlier in the FUNCTION branch. Re-running with errors raised immediately to see the real cause:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor q in ['CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', 'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b']:\n  try:\n    print(repr(sqlglot.parse_one(q, read='duckdb', error_level=ErrorLevel.IMMEDIATE))[:200])\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" 2>&1 | head -30", "description": "Surface the immediate parse error for these inputs"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command(this=CREATE, expression=MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2))
Command(this=CREATE, expression=MACRO s(a) AS TABLE (SELECT 1), (a, b) AS a+b)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot, traceback\nfrom sqlglot.parser import Parser\norig = Parser._parse_as_command\ndef spy(self, start):\n    traceback.print_stack(limit=6); return orig(self, start)\nParser._parse_as_command = spy\nsqlglot.parse_one('CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', read='duckdb')\n\" 2>&1 | head -40", "description": "Trace where the Command fallback is triggered"}
[tool_result]   File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2156, in _parse
    return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2123, in _parse_batch_statements
    expressions.append(parse_method(self))
  File "~/.cache/li
…[277 chars elided]…
ckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 1090, in <lambda>
    TokenType.CREATE: lambda self: self._parse_create(),
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", line 2589, in _parse_create
    return self._parse_as_command(start)
  File "<string>", line 6, in spy
'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
[tool_use Bash] {"command": "sed -n 2560,2592p sqlglot/parser.py", "description": "Read the end of _parse_create to see the fallback condition"}
[tool_result]                 # exp.Properties.Location.POST_EXPRESSION
                extend_props(self._parse_properties())

                indexes = []
                while True:
                    index = self._parse_index()

                    # exp.Properties.Location.POST_INDEX
                    extend_props(self._parse_properties())
                    if not index:
                        break
                    else:
                        self._match(TokenType.COMMA)
                     
…[386 chars elided]…
           if self._match_texts(self.CLONE_KEYWORDS):
                copy = self._prev.text.lower() == "copy"
                clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = create_token.text.upper()
        return self.expression(
[assistant] The final check fails because the body parse left `_curr` at a token other than `,`/`)`. So the body parse for a parenthesised body is consuming past the comma. Checking what `_parse_statement` does with `(SELECT 1), ...`:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\nfrom sqlglot.dialects.duckdb import DuckDB\nfor src in ['(SELECT 1), (a, b) AS (SELECT 2)', '(SELECT 1) AS z, 3', 'TABLE (SELECT 1), 3', 'a + b, (a, b) AS c']:\n    p = DuckDB().parser()\n    toks = DuckDB().tokenize(src)\n    p.reset(); p.sql = src; p._tokens = toks; p._index=-1; p._advance()\n    e = p._parse_statement()\n    print(repr(src), '->', type(e).__name__, '| curr:', p._curr.text if p._curr else None, '|', e.sql('duckdb') if e else None)\n\" 2>&1 | head", "description": "Check what the statement parser consumes for parenthesised bodies"}
[tool_result] '(SELECT 1), (a, b) AS (SELECT 2)' -> NoneType | curr: None | None
'(SELECT 1) AS z, 3' -> NoneType | curr: None | None
'TABLE (SELECT 1), 3' -> NoneType | curr: None | None
'a + b, (a, b) AS c' -> NoneType | curr: None | None
[assistant] My manual parser setup is wrong. I'll spy on the body parse inside a real parse instead:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._parse_user_defined_function_expression\ndef spy(self):\n    r = orig(self); print('BODY ->', r.sql('duckdb') if r is not None else None, '| curr:', self._curr and self._curr.text); return r\nParser._parse_user_defined_function_expression = spy\nfor q in ['CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', 'CREATE MACRO s(a) AS a + 1, (a, b) AS a', 'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS TABLE (SELECT 2)']:\n    print(type(sqlglot.parse_one(q, read='duckdb')).__name__)\n\" 2>&1 | head -20", "description": "Spy on macro body parse to see consumed tokens"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO s(a) AS TABLE (SELECT 1), (a, b) AS TABLE (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
BODY -> (SELECT 1), (a, b) | curr: (
Command
BODY -> a + 1 | curr: ,
BODY -> a | curr: <Token token_type: TokenType.SENTINEL, text: SENTINEL, line: 1, col: 1, start: 0, end: 0, comments: []>
Create
BODY -> (SELECT 1), (a, b) AS "TABLE" | curr: (
Command
[assistant] The statement parser greedily reads `(SELECT 1), (a, b)` as one comma list, and `AS TABLE (...)` is not handled as a body at all. Checking how the existing `AS TABLE SELECT` body is parsed before deciding the fix:
[tool_use Bash] {"command": "grep -n \"TABLE\" sqlglot/dialects/duckdb.py | head -30; grep -n \"_parse_user_defined_function_expression\\|def _parse_statement\" -A3 sqlglot/dialects/duckdb.py | head; PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE SELECT a', read='duckdb'); print(repr(e.expression)[:400])\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a)', read='duckdb'); print(repr(e.expression)[:400])\n\"", "description": "Check how TABLE macro bodies are represented"}
[tool_result] Select(
  expressions=[
    Column(
      this=Identifier(this=a, quoted=False))])
Subquery(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]))
[tool_use Bash] {"command": "grep -n \"def _parse_statement\" -A32 sqlglot/parser.py", "description": "Read _parse_statement implementation"}
[tool_result] 2269:    def _parse_statement(self) -> exp.Expr | None:
2270-        if not self._curr:
2271-            return None
2272-
2273-        if self._match_set(self.STATEMENT_PARSERS):
2274-            comments = self._prev_comments
2275-            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
2276-            stmt.add_comments(comments, prepend=True)
2277-            return stmt
2278-
2279-        if self._match_set(self.dialect.tokenizer_class.COMMANDS):
2280-            return self._
…[532 chars elided]…
-
2293-    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2294-        start = self._prev
2295-        temporary = self._match(TokenType.TEMPORARY)
2296-        materialized = self._match_text_seq("MATERIALIZED")
2297-        iceberg = self._match_text_seq("ICEBERG")
2298-
2299-        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
2300-        if not kind or (iceberg and kind and kind != "TABLE"):
2301-            return self._parse_as_command(start)
[assistant] The body parse is greedy in `_parse_expression`/`_parse_query_modifiers`. I'll test which entry point stops at the overload comma for parenthesised bodies:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\ndef probe(name):\n    orig = getattr(Parser, name)\n    def spy(self, *a, **k):\n        if self._curr and self._curr.text == '(':\n            r = orig(self, *a, **k); print(name, '->', r.sql('duckdb') if r is not None else None, '| curr:', self.
…[31 chars elided]…
         return r\n        return orig(self, *a, **k)\n    setattr(Parser, name, spy)\nfor n in ['_parse_expression', '_parse_assignment', '_parse_query_modifiers']:\n    probe(n)\nfor q in ['CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)']:\n    print(type(sqlglot.parse_one(q, read='duckdb')).__name__)\n\" 2>&1 | head -20", "description": "Probe which expression parser consumes the comma"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 15, in <module>
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py", line 155, in parse_one
    dialect = Dialect.get_or_raise(read or dialect)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/dialects/dialect.py", line 957, in g
…[635 chars elided]…
3.12.13-macos-aarch64-none/lib/python3.12/importlib/__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\ndef probe(name):\n    orig = getattr(Parser, name)\n    def spy(self, *a, **k):\n        r = orig(self, *a, **k)\n        if self._prev and self._prev.text == ')' and self._curr and self._curr.text == ',' and self._curr_is_body if False else False
…[82 chars elided]…
ckdb import DuckDB\nprint(sqlglot.parse_one('CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', read=DuckDB).sql('duckdb')[:60])\n\" 2>&1 | tail -4; $PY -c \"\nfrom sqlglot.parser import Parser\nprint([n for n in dir(Parser) if n in ('_parse_expression','_parse_assignment','_parse_query_modifiers','_parse_disjunction')])\"", "description": "Check parser method names and dialect import issue"}
[tool_result] 'CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)
['_parse_assignment', '_parse_disjunction', '_parse_expression', '_parse_query_modifiers']
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._parse_expression\ndef spy(self):\n    before = self._curr.text if self._curr else None\n    r = orig(self)\n    print('expr from', before, '->', type(r).__name__, '| curr:', self._curr.text if self._curr else None)\n    return r\nParser._parse_expression = spy\nsqlglot.parse_one('CREATE MACRO s(a) AS (SELECT 1), (a, b) AS (SELECT 2)', read='duckdb')\n\" 2>&1 | grep -v \"^'CREATE\" | head -12", "description": "Probe _parse_expression on parenthesised macro body"}
[tool_result] expr from ROW_NUMBER -> Sub | curr: )
expr from ( -> Paren | curr: None
expr from : -> Mod | curr: None
expr from CASE -> Case | curr: )
expr from ( -> Paren | curr: None
expr from WITH -> NoneType | curr: WITH
expr from SELECT -> NoneType | curr: SELECT
expr from : -> Alias | curr: )
expr from SELECT -> NoneType | curr: SELECT
expr from i -> Column | curr: ,
expr from 1.0 -> Alias | curr: FROM
expr from SELECT -> NoneType | curr: SELECT
[tool_use Bash] {"command": "grep -n \"def _parse_paren\" -A40 sqlglot/parser.py | head -60", "description": "Read the paren expression parser"}
[tool_result] 6773:    def _parse_paren(self) -> exp.Expr | None:
6774-        if not self._match(TokenType.L_PAREN):
6775-            return None
6776-
6777-        comments = self._prev_comments
6778-        query = self._parse_select()
6779-
6780-        if query:
6781-            expressions = [query]
6782-        else:
6783-            expressions = self._parse_expressions()
6784-
6785-        this = seq_get(expressions, 0)
6786-
6787-        if not this and self._match(TokenType.R_PAREN, advance=False):
…[652 chars elided]…
f.expression(exp.Paren(this=this))
6800-
6801-        if this:
6802-            this.add_comments(comments)
6803-
6804-        self._match_r_paren(expression=this)
6805-
6806-        if isinstance(this, exp.Paren) and isinstance(this.this, exp.AggFunc):
6807-            return self._parse_window(this)
6808-
6809-        return this
6810-
6811-    def _parse_primary(self) -> exp.Expr | None:
6812-        if self._match_set(self.PRIMARY_PARSERS):
6813-            token_type = self._prev.token_type
[assistant] The culprit is query modifiers: `_parse_paren` runs `_parse_query_modifiers` on a parenthesised subquery, and that treats a following comma as an implicit join. Checking how comma joins are recognised, to see whether the macro body can stop at the overload comma without a broad change:
[tool_use Bash] {"command": "grep -n \"def _parse_join(\" -A30 sqlglot/parser.py | grep -n \"COMMA\" ; grep -n \"def _parse_query_modifiers\" -A12 sqlglot/parser.py | head -30", "description": "Find where comma joins are parsed"}
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
4129-                this.append("laterals", lateral)
4130-
4131-            while True:
4132-                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4133-                    modifier_token = self._curr
4134-                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
4135-                    key, expression = parser(self)
4136-
[tool_use Bash] {"command": "sed -n 4405,4425p sqlglot/parser.py; grep -n \"MODIFIABLES\" sqlglot/parser.py | head -3; grep -n \"def _parse_joins\" -A8 sqlglot/parser.py", "description": "Read comma-join parsing and joins loop"}
[tool_result]                 return this.this
            return this

        return self._parse_wrapped_csv(_parse_column_as_identifier, optional=True)

    def _parse_join(
        self,
        skip_join_token: bool = False,
        parse_bracket: bool = False,
        alias_tokens: t.Collection[TokenType] | None = None,
    ) -> exp.Join | None:
        if self._match(TokenType.COMMA):
            table = self._try_parse(lambda: self._parse_table(alias_tokens=alias_tokens))
            cross_join = self
…[246 chars elided]…
: t.ClassVar = (exp.Query, exp.Table, exp.TableFromRows, exp.Values)
4125:        if isinstance(this, self.MODIFIABLES):
5072:    def _parse_joins(
5073-        self, alias_tokens: t.Collection[TokenType] | None = None
5074-    ) -> t.Iterator[exp.Join]:
5075-        return iter(lambda: self._parse_join(alias_tokens=alias_tokens), None)
5076-
5077-    def _parse_unpivot_columns(self) -> exp.UnpivotColumns | None:
5078-        if not self._match(TokenType.INTO):
5079-            return None
5080-
[assistant] The comma-join is what swallows the overload separator. Before choosing a fix, I need to see how the `TABLE` keyword is represented in the body AST today:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE SELECT a', read='duckdb')\nprint(e.expression.args.keys(), e.expression.sql('duckdb'))\nprint(repr(sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a)', read='duckdb').expression))\nprint(repr(sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a)', read='duckdb').expression.this))\n\" | head -40; grep -n '\"TABLE\"' sqlglot/generator.py | head", "description": "Inspect AST for TABLE macro bodies"}
[tool_result] dict_keys(['kind', 'hint', 'distinct', 'expressions', 'limit', 'exclude', 'operation_modifiers']) SELECT a
Subquery(
  this=Select(
    expressions=[
      Column(
        this=Identifier(this=a, quoted=False))]))
Select(
  expressions=[
    Column(
      this=Identifier(this=a, quoted=False))])
2425:        table = self.func("TABLE", expression.this)
5072:        target = "DATABASE" if expression.args.get("is_database") else "TABLE"
[assistant] `TABLE SELECT` is stored as `Select(kind="TABLE")`, but `TABLE (SELECT ...)` loses the keyword in the body. Checking where that keyword is kept for the parenthesised form:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE (SELECT a)', read='duckdb')\nprint({k:(type(v).__name__) for k,v in e.args.items()}); print(e.expression.args.keys())\nprint(repr(e.expression.this.args.get('kind')))\nprint(e.expression.this.sql('duckdb'))\n\"; grep -n \"TABLE\" sqlglot/expressions/ddl.py | head; grep -n \"kind.*TABLE\\|\\\"TABLE\\\"\" sqlglot/generator.py | head", "description": "Locate where TABLE keyword is kept for parenthesised body"}
[tool_result] {'this': 'UserDefinedFunction', 'kind': 'str', 'replace': 'bool', 'refresh': 'bool', 'unique': 'bool', 'expression': 'Subquery', 'exists': 'bool', 'properties': 'Properties', 'indexes': 'NoneType', 'no_schema_binding': 'NoneType', 'begin': 'bool', 'clone': 'NoneType', 'concurrently': 'bool', 'clustered': 'NoneType'}
dict_keys(['this', 'pivots', 'alias', 'sample'])
None
SELECT a
1289:        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
1400:        if kind in self.EXPRESSION_PRECEDES_PROPERTIES_CREATABLES:
1788:        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
2425:        table = self.func("TABLE", expression.this)
3264:            sql = f"CREATE{table_kind} TABLE {self.sql(into.this)} AS {sql}"
5072:        target = "DATABASE" if expression.args.get("is_database") else "TABLE"
5856:            kind = f"TABLE {kind}"
[assistant] The `TABLE` keyword is not stored in the body node, yet it round-trips. Finding where the generator emits it:
[tool_use Bash] {"command": "grep -n \"TABLE\" sqlglot/generator.py | grep -v \"TABLE_\\|_TABLE\\|ALTER\\|CREATE\\|DROP\\|INSERT\" | head -20; grep -n \"def _parse_wrapped(\" -A3 sqlglot/parser.py | head -5", "description": "Find how generator emits TABLE keyword"}
[tool_result] 286:        exp.WithJournalTableProperty: lambda self, e: f"WITH JOURNAL TABLE={self.sql(e, 'this')}",
414:    TABLESAMPLE_REQUIRES_PARENS = True
417:    TABLESAMPLE_SIZE_IS_ROWS = True
420:    TABLESAMPLE_KEYWORDS = "TABLESAMPLE"
422:    # Whether the TABLESAMPLE clause supports a method name, like BERNOULLI
423:    TABLESAMPLE_WITH_METHOD = True
426:    TABLESAMPLE_SEED_KEYWORD = "SEED"
660:    EXPRESSION_PRECEDES_PROPERTIES_CREATABLES: t.ClassVar[set[str]] = set()
1110:        return f"UNCACH
…[546 chars elided]…
od and self.TABLESAMPLE_WITH_METHOD else ""
2448:        seed = f" {self.TABLESAMPLE_SEED_KEYWORD} ({seed})" if seed else ""
2451:        if size and self.TABLESAMPLE_SIZE_IS_ROWS:
2455:        if percent and not self.dialect.TABLESAMPLE_SIZE_IS_PERCENT:
8548:    def _parse_wrapped(self, parse_method: t.Callable[[], T], optional: bool = False) -> T:
8549-        wrapped = self._match(TokenType.L_PAREN)
8550-        if not wrapped and not optional:
8551-            self.raise_error("Expecting (")
[tool_use Bash] {"command": "sed -n 2416,2428p sqlglot/generator.py; grep -n \"TABLE\" sqlglot/parser.py | grep -i \"function\\|udf\\|_parse_table_func\\|TABLE, \" | head", "description": "Read generator code near TABLE function output"}
[tool_result]         indexed = expression.args.get("indexed")
        if indexed is not None:
            indexed = f" INDEXED BY {self.sql(indexed)}" if indexed else " NOT INDEXED"
        else:
            indexed = ""

        return f"{only}{table}{changes}{partition}{file_format}{pre_alias}{alias}{indexed}{hints}{pivots}{post_alias}{joins}{laterals}{ordinality}"

    def tablefromrows_sql(self, expression: exp.TableFromRows) -> str:
        table = self.func("TABLE", expression.this)
        alias = self.sql(expression, "alias")
        alias = f" AS {alias}" if alias else ""
        sample = self.sql(expression, "sample")
2368:        if self._match_pair(TokenType.TABLE, TokenType.FUNCTION, advance=False):
[assistant] Decision: for macro bodies, parse parenthesised queries with `_parse_wrapped`, so no comma-join is attempted after the closing paren. `TABLE (...)` maps to the existing `TableFromRows` node, which already generates `TABLE(...)`. I'll check the helper signatures first.
[tool_use Bash] {"command": "grep -n \"def _parse_subquery\\|def _match_pair\\|def _next\\|def _parse_select(\" -A2 sqlglot/parser.py | head -20; grep -n \"class TableFromRows\" -A3 sqlglot/expressions/*.py", "description": "Check helper signatures needed for macro body parser"}
[tool_result] 1934:    def _match_pair(
1935-        self, token_type_a: TokenType, token_type_b: TokenType, advance: bool = True
1936-    ) -> bool:
--
3782:    def _parse_select(
3783-        self,
3784-        nested: bool = False,
--
4076:    def _parse_subquery(
4077-        self, this: exp.Expr | None, parse_alias: bool = True
4078-    ) -> exp.Subquery | None:
sqlglot/expressions/query.py:807:class TableFromRows(Expression, UDTF):
sqlglot/expressions/query.py-808-    arg_types = {
sqlglot/expressions/query.py-809-        "this": True,
sqlglot/expressions/query.py-810-        "alias": False,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                        expression = (\n                            self._parse_user_defined_function_expression()\n                            if create_token_type == TokenType.FUNCTION\n                            else
…[138 chars elided]…
_parse_macro_body()\n                            if create_token.text.upper() == \"MACRO\"\n                            else (\n                                self._parse_user_defined_function_expression()\n                                if create_token_type == TokenType.FUNCTION\n                                else self._parse_block()\n                            )\n                        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_macro_overloads(\n        self, this: exp.UserDefinedFunction, expression: exp.Expr\n    ) -> tuple[exp.Expr, exp.MacroOverloads]:\n        overloads = [\n            exp.MacroOverload(parameters=exp.Tuple
…[2100 chars elided]…
parameters\")\n\n            overloads.append(\n                self.expression(\n                    exp.MacroOverload(\n                        parameters=exp.Tuple(expressions=parameters),\n                        expression=self._parse_macro_body(),\n                    )\n                )\n            )\n\n        return this.this, self.expression(exp.MacroOverloads(expressions=overloads))"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now a broader check: parse, round-trip, and DuckDB execution for scalar, parenthesised, and table overloads.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb, sqlglot\nfrom sqlglot import exp\nqs = [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE OR REPLACE MACRO m(a) AS a, () AS 1, (x, y) AS x * y',\n 'CREATE MACRO p(a) AS (a + 1), (a, b) AS (a * b)',\n 'CREATE MACRO s1(a) AS (SELECT a AS x), (a, b) AS (SELECT 
…[568 chars elided]…
 print('MO' if ok else 'NOT-MO', '|', out, '|', d)\nprint(con.sql(\\\"select function_name, parameters, function_type from duckdb_functions() where function_name in ('add_x','m','p','s1','s2','s3','s4') order by 1\\\").fetchall())\nprint(con.sql('select add_x(1,2), add_x(1,2,3), m(5), m(2,3), p(3)').fetchall())\n\" 2>&1 | tail -30", "description": "Round-trip overload forms and execute in DuckDB"}
[tool_result] MO | CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c | duckdb ok
MO | CREATE OR REPLACE MACRO m (a) AS a, () AS 1, (x, y) AS x * y | duckdb ok
MO | CREATE MACRO p (a) AS (a + 1), (a, b) AS (a * b) | duckdb ok
MO | CREATE MACRO s1 (a) AS (SELECT a AS x), (a, b) AS (SELECT b AS x) | duckdb ok
MO | CREATE MACRO s2 (a) AS (SELECT a AS x), (a, b) AS TABLE(SELECT b AS x) | DUCKDB ERR Parser Error: syntax error at or near "TABLE"
MO | CREATE MACRO s3 (a) AS (SELECT a AS x), (a, b) AS TABLE(SELECT b AS x), (a, b, c) AS TABLE(SELECT c AS x) | DUCKDB ERR Parser Error: syntax error at or near "TABLE"
MO | CREATE MACRO s4 (a) AS (SELECT a AS x), (a, b) AS a + b | duckdb ok
[('add_x', ['a', 'b'], 'macro'), ('add_x', ['a', 'b', 'c'], 'macro'), ('m', ['a'], 'macro'), ('m', [], 'macro'), ('m', ['x', 'y'], 'macro'), ('p', ['a'], 'macro'), ('p', ['a', 'b'], 'macro'), ('s1', ['a'], 'macro'), ('s1', ['a', 'b'], 'macro'), ('s4', ['a'], 'macro'), ('s4', ['a', 'b'], 'macro')]
[(3, 6, 5, 6, 4)]
[assistant] Scalar and parenthesised-query overloads now round-trip and execute in DuckDB, with correct results (`add_x(1,2)=3`, `m(2,3)=6`). The table case fails because the first body lost its `TABLE` keyword: `s2` came out as `AS (SELECT ...)`, which DuckDB reads as a scalar macro. Finding where that token is consumed:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.parser import Parser\norig = Parser._parse_macro_body\ndef spy(self):\n    print('body starts at', self._curr.text if self._curr else None, '| prev', self._prev.text)\n    return orig(self)\nParser._parse_macro_body = spy\ne = sqlglot.parse_one('CREATE MACRO s2(a) AS TABLE (SELECT a AS x)', read='duckdb')\nprint(e.expression.sql('duckdb'), type(e.expression).__name__)\n\" 2>&1 | tail -4; grep -n \"def _parse_heredoc\" -A12 sqlglot/parser.py | head -20", "description": "Find what consumes TABLE before the first body"}
[tool_result] body starts at ( | prev TABLE
(SELECT a AS x) Subquery
9304:    def _parse_heredoc(self) -> exp.Heredoc | None:
9305-        if self._match(TokenType.HEREDOC_STRING):
9306-            return self.expression(exp.Heredoc(this=self._prev.text))
9307-
9308-        if not self._match_text_seq("$"):
9309-            return None
9310-
9311-        tags = ["$"]
9312-        tag_text = None
9313-
9314-        if self._is_connected():
9315-            self._advance()
9316-            tags.append(self._prev.text.upper())
[tool_use Bash] {"command": "grep -n \"def _parse_function_properties\" -A12 sqlglot/parser.py; grep -n \"TokenType.TABLE\" sqlglot/parser.py | sed -n 1,40p | grep -n \"ALIAS\\|AS\\b\" ", "description": "Read function-properties parsing that may consume TABLE"}
[tool_result] 7034:    def _parse_function_properties(self) -> exp.Properties | None:
7035-        return self._parse_properties()
7036-
7037-    def _parse_user_defined_function_expression(self) -> exp.Expr | None:
7038-        return self._parse_statement()
7039-
7040-    def _parse_function_parameter(self) -> exp.Expr | None:
7041-        return self._parse_column_def(this=self._parse_id_var(), computed_column=False)
7042-
7043-    def _parse_user_defined_function(self, kind: TokenType | None = None) -> exp.Expr | None:
7044-        this = self._parse_table_parts(schema=True)
7045-
7046-        if not self._match(TokenType.L_PAREN):
[assistant] The `TABLE` keyword is consumed by the function-properties parser before the body, and the generator prints it back as a post-`AS` property. My generator change skips that whole `AS` block, which drops it. Confirming the property node:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ne = sqlglot.parse_one('CREATE MACRO t(a) AS TABLE SELECT a', read='duckdb')\nprint(repr(e.args.get('properties')))\n\"", "description": "Show the property node that holds the TABLE keyword"}
[tool_result] Properties(
  expressions=[
    ReturnsProperty(
      this=Schema(
        this=Var(this=TABLE)),
      is_table=True)])
[assistant] The `TABLE` keyword is parsed as a `ReturnsProperty(is_table=True)` on the create, which is why it was dropped. I'll move that marker onto the first overload's body when overloads are present, as a `TableFromRows`, and keep the single-macro path unchanged.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                this, expression = self._parse_macro_overloads(this, expression)", "new_string": "                this, expression = self._parse_macro_overloads(this, expression, properties)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_macro_overloads(\n        self, this: exp.UserDefinedFunction, expression: exp.Expr\n    ) -> tuple[exp.Expr, exp.MacroOverloads]:\n        overloads = [\n            exp.MacroOverload(\n                pa
…[568 chars elided]…
ance(prop, exp.ReturnsProperty) and prop.args.get(\"is_table\"):\n                    properties.expressions.remove(prop)\n                    expression = exp.TableFromRows(this=expression.this)\n                    break\n\n        overloads = [\n            exp.MacroOverload(\n                parameters=exp.Tuple(expressions=this.expressions), expression=expression\n            )\n        ]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport duckdb, sqlglot\nfrom sqlglot import exp\nqs = [\n 'CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n 'CREATE OR REPLACE MACRO m(a) AS a, () AS 1, (x, y) AS x * y',\n 'CREATE MACRO p(a) AS (a + 1), (a, b) AS (a * b)',\n 'CREATE MACRO s1(a) AS (SELECT a AS x), (a, b) AS (SELECT 
…[737 chars elided]…
ect function_name, parameters, function_type from duckdb_functions() where function_name in ('add_x','m','p','s1','s2','s3','s4','s5','s6') order by 1,2\\\").fetchall())\nprint(con.sql('select * from s2(1)').fetchall(), con.sql('select * from s3(1,2)').fetchall(), con.sql('select * from s3(1,2,3)').fetchall())\n\" 2>&1 | tail -30", "description": "Re-run overload round-trips and DuckDB execution"}
[tool_result] MO | CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c | duckdb ok
MO | CREATE OR REPLACE MACRO m (a) AS a, () AS 1, (x, y) AS x * y | duckdb ok
MO | CREATE MACRO p (a) AS (a + 1), (a, b) AS (a * b) | duckdb ok
MO | CREATE MACRO s1 (a) AS (SELECT a AS x), (a, b) AS (SELECT b AS x) | duckdb ok
MO | CREATE MACRO s2 (a) AS TABLE(SELECT a AS x), (a, b) AS TABLE(SELECT b AS x) | duckdb ok
MO | CREATE MACRO s3 (a) AS TABLE(SELECT a AS x), (a, b) AS TABLE(SELECT b AS x), (a, b, c) AS TABLE(SEL
…[273 chars elided]…
 'b', 'c'], 'macro'), ('m', [], 'macro'), ('m', ['a'], 'macro'), ('m', ['x', 'y'], 'macro'), ('p', ['a'], 'macro'), ('p', ['a', 'b'], 'macro'), ('s1', ['a'], 'macro'), ('s1', ['a', 'b'], 'macro'), ('s2', ['a'], 'table_macro'), ('s2', ['a', 'b'], 'table_macro'), ('s3', ['a'], 'table_macro'), ('s3', ['a', 'b'], 'table_macro'), ('s3', ['a', 'b', 'c'], 'table_macro'), ('s4', ['a'], 'macro'), ('s4', ['a', 'b'], 'macro'), ('s5', ['a'], 'table_macro'), ('s6', ['a'], 'table_macro')]
[(1,)] [(2,)] [(3,)]
[assistant] All forms now execute in DuckDB and resolve to the right overloads (`macro` and `table_macro`, with `s3(1,2)=2` and `s3(1,2,3)=3`). Single-macro forms are unchanged. Next I'll add tests next to `test_udf`, then run the duckdb suite and formatter.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):", "new_string": "    def test_macro_overloads(self):\n        ast = self.parse_one(\n            \"\"\"\n            CREATE MACRO add_x\n                (a, b) AS a + b,\n     
…[484 chars elided]…
m (a) AS a, () AS 1, (x, y) AS x * y\")\n        self.validate_identity(\"CREATE MACRO p (a) AS (a + 1), (a, b) AS (a * b)\")\n        self.validate_identity(\"CREATE MACRO s (a) AS (SELECT a AS x), (a, b) AS (SELECT b AS x)\")\n        self.validate_identity(\n            \"CREATE MACRO s (a) AS TABLE(SELECT a AS x), (a, b) AS TABLE(SELECT b AS x)\"\n        )\n\n    def test_bitwise_agg(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; head -20 tests/dialects/test_duckdb.py | grep -n \"import\"; $PY -m ruff --version 2>&1; $PY -m ruff format sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py 2>&1 | tail -2; $PY -m ruff check sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -15", "description": "Format, lint, and run the DuckDB dialect tests"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.generator import logger as generator_logger
5:from sqlglot.helper import logger as helper_logger
6:from sqlglot.optimizer.annotate_types import annotate_types
7:from tests.dialects.test_dialect import Validator
ruff 0.15.6
1 file reformatted, 3 files left unchanged
All checks passed!
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <tests.dialects.
…[317 chars elided]…
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: sqlglot.parse_one() got multiple values for keyword argument 'read'

tests/dialects/test_dialect.py:30: TypeError
=========================== short test summary info ============================
FAILED tests/dialects/test_duckdb.py::TestDuckDB::test_macro_overloads - Type...
1 failed, 44 passed, 600 subtests passed in 0.40s
[This command modified 1 file you've previously read: sqlglot/parser.py. Call Read before editing.]
[assistant] One test bug: `self.parse_one` already sets the dialect, so I'll drop the duplicate `read=`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "        ast = self.parse_one(\n            \"\"\"\n            CREATE MACRO add_x\n                (a, b) AS a + b,\n                (a, b, c) AS a + b + c;\n            \"\"\",\n            read=\"duckdb\",\n        )", "new_string": "        ast = self.parse_one(\n            \"\"\"\n            CREATE MACRO add_x\n                (a, b) AS a + b,\n                (a, b, c) AS a + b + c;\n            \"\"\"\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run DuckDB tests then the full project test suite"}
[tool_result] =========================== short test summary info ============================
FAILED tests/dialects/test_duckdb.py::TestDuckDB::test_macro_overloads - Attr...
1 failed, 44 passed, 600 subtests passed in 0.27s
                (a, b) AS a + b,
                (a, b, c) AS a + b + c;
            """
        )
        overloads = ast.expression.expressions
        self.assertIsInstance(ast.expression, exp.MacroOverloads)
        self.assertEqual(len(overloads), 2)
>       self.assertEqual(len(overloads[1].parameters.expressions), 3)
                             ^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'MacroOverload' object has no attribute 'parameters'

tests/dialects/test_duckdb.py:2622: AttributeError
=========================== short test summary info ============================
FAILED tests/dialects/test_duckdb.py::TestDuckDB::test_macro_overloads - Attr...
1 failed, 1113 passed, 18162 subtests passed in 66.97s (0:01:06)
[assistant] Only my new test fails (accessing `.parameters` as an attribute; sqlglot nodes use `.args`). The full suite otherwise passes: 1113 passed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.assertEqual(len(overloads[1].parameters.expressions), 3)", "new_string": "        self.assertEqual(len(overloads[1].args[\"parameters\"].expressions), 3)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -2; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $PY -m ruff format --check sqlglot tests 2>&1 | tail -1; $PY -m ruff check sqlglot tests 2>&1 | tail -1; git status --short; git diff --stat", "description": "Re-run duckdb tests, full suite, lint and diff stat"}
[tool_result] .....................    [100%]
45 passed, 600 subtests passed in 0.25s
.....................................                     [100%]
1114 passed, 18162 subtests passed in 58.55s
237 files already formatted
All checks passed!
 M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
 sqlglot/expressions/ddl.py    |  8 +++++
 sqlglot/generator.py          | 10 +++++-
 sqlglot/parser.py             | 76 +++++++++++++++++++++++++++++++++++++++++--
 tests/dialects/test_duckdb.py | 21 ++++++++++++
 4 files changed, 111 insertions(+), 4 deletions(-)
[assistant] Full suite and lint pass. Reviewing the parser diff before finishing:
[tool_use Bash] {"command": "git diff sqlglot/parser.py sqlglot/generator.py", "description": "Review the parser and generator diff"}
[tool_result] diff --git a/sqlglot/generator.py b/sqlglot/generator.py
index 54b50c77a..a1fa352f1 100644
--- a/sqlglot/generator.py
+++ b/sqlglot/generator.py
@@ -1328,7 +1328,9 @@ class Generator:
         if expression_sql:
             expression_sql = f"{begin}{self.sep()}{expression_sql}"
 
-            if self.CREATE_FUNCTION_RETURN_AS or not isinstance(expression.expression, exp.Return):
+            if not isinstance(expression.expression, exp.MacroOverloads) and (
+                self.CREATE_FUNCTIO
…[4606 chars elided]…
(
+                self.expression(
+                    exp.MacroOverload(
+                        parameters=exp.Tuple(expressions=parameters),
+                        expression=self._parse_macro_body(),
+                    )
+                )
+            )
+
+        return this.this, self.expression(exp.MacroOverloads(expressions=overloads))
+
     def _parse_introducer(self, token: Token) -> exp.Introducer | exp.Identifier:
         literal = self._parse_primary()
         if literal:
[assistant] The logic reads correctly. The `_next` condition came out awkwardly after formatting, so I'll tidy it, then run mypy on the touched modules.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "        if (\n            self._match(TokenType.L_PAREN, advance=False)\n            and self._next\n            and self._next.token_type\n            in (\n                TokenType.SELECT,\n                TokenType.W
…[115 chars elided]…
(self._parse_select), parse_alias=False\n            )", "new_string": "        if (\n            self._match(TokenType.L_PAREN, advance=False)\n            and self._next\n            and self._next.token_type in (TokenType.SELECT, TokenType.WITH)\n        ):\n            return self._parse_subquery(\n                this=self._parse_wrapped(self._parse_select), parse_alias=False\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-094830-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[assistant] The harness reports `parser.py` changed on disk since my last read. I'll check the diff for anything I didn't write before going further:
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff sqlglot/parser.py | grep \"^@@\" ; git diff sqlglot/parser.py | grep \"^[-+]\" | grep -v \"macro\\|MACRO\\|Macro\\|TABLE\\|_parse_user_defined\\|_parse_block\\|create_token_type\\|expression\\|properties\\|this\\|parameters\\|SELECT\\|WITH\\|raise_error\\|Parenthesized\\|separating\\|NOTE\\|^+$\" | head -40", "description": "Check parser.py diff for unexpected external edits"}
[tool_result]  M sqlglot/expressions/ddl.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.py
 sqlglot/expressions/ddl.py    |  8 +++++
 sqlglot/generator.py          | 10 +++++-
 sqlglot/parser.py             | 72 +++++++++++++++++++++++++++++++++++++++++--
 tests/dialects/test_duckdb.py | 21 +++++++++++++
 4 files changed, 107 insertions(+), 4 deletions(-)
@@ -2420,13 +2420,25 @@ class Parser:
@@ -7040,6 +7052,60 @@ class Parser:
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
+ 
…[225 chars elided]…
_match(TokenType.L_PAREN, advance=False)
+            and self._next
+        ):
+            return self._parse_subquery(
+            )
+        self,
+                if isinstance(prop, exp.ReturnsProperty) and prop.args.get("is_table"):
+                    break
+        overloads = [
+            )
+        ]
+        while self._match(TokenType.COMMA):
+            if not self._match(TokenType.ALIAS):
+            overloads.append(
+                    )
+                )
+            )
[assistant] The diff contains only my two hunks, so the notice came from my own earlier formatter run. Re-running tests, lint and mypy:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot tests | tail -1; $PY -m ruff check sqlglot tests | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; (timeout 300 $PY -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -3) ", "description": "Run lint, full tests, and mypy on changed modules"}
[tool_result] 237 files already formatted
All checks passed!
1114 passed, 18162 subtests passed in 53.85s
(eval):1: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/ddl.py 2>&1 | tail -3", "description": "Run mypy on changed modules"}
[tool_result] Success: no issues found in 3 source files
[assistant] Overloaded `CREATE MACRO` now parses and round-trips in DuckDB, for scalar and table macros. The issue's example produces `exp.MacroOverloads` with two `MacroOverload` entries, and the generated SQL runs in DuckDB 1.5.6 with the right overloads resolving (`add_x(1, 2) = 3`, `add_x(1, 2, 3) = 6`). The full suite passes (1114), and ruff and mypy are clean. I haven't committed.

**Representation**
- Single-overload macros are unchanged. With two or more overloads, `Create.this` is the macro name and `Create.expression` is a `MacroOverloads` node. Each entry is a `MacroOverload(parameters=Tuple, e
…[820 chars elided]…
e_macro_body` parses parenthesised query bodies with `_parse_wrapped`. Without that, the query-modifier logic reads the overload comma as an implicit join.
- `sqlglot/generator.py`: `macrooverload_sql` and `macrooverloads_sql`. The `AS` prefix is skipped for `MacroOverloads`, because each overload carries its own.
- `tests/dialects/test_duckdb.py`: new `test_macro_overloads` covering the issue's example, scalar, parenthesised-query, and table overloads.

If you want the commit made, I'll commit on a branch. Per the repo's CLAUDE.md, the PR title and commit message need the model name appended.
