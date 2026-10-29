# trajectory base-1

final message:
Overloaded DuckDB macros now parse and round-trip, including scalar, zero-argument, and table forms. The full suite passes (1114 tests, 18162 subtests), and ruff and mypy are clean. I haven't committed anything.

```python
sqlglot.parse_one("CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;", read="duckdb").sql("duckdb")
# CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
```

I also ran the generated SQL through DuckDB 1.5.6. It accepts it and registers each overload with the right arity.

**Representation.** For an overloaded macro, `Create.this` is an `exp.MacroOverloads` holding the macro name, one `exp.MacroOverload` per overload (its parameter list and body), and a `table` flag. This differs from the single-macro shape, where the name and params sit in `Create.this` and the body in `Create.expression`. Overloads go in `Create.this` because the generator emits the name and the `(params) AS body` list together. Say if you'd rather have them in `Create.expression`.

**Changes:**
- `sqlglot/expressions/ddl.py`: adds `MacroOverloads` and `MacroOverload`.
- `sqlglot/parser.py`: a `_parse_macro_overloads` hook that returns `None` in the base parser.
- `sqlglot/parsers/duckdb.py`: the DuckDB override of that hook, which parses the extra overloads. It also overrides body parsing so a parenthesized query body doesn't swallow the separator comma as a join. The override backtracks unless the query is followed by a comma or the end of the statement. Without that, `(SELECT 1) + 1` and `(SELECT 1) UNION (SELECT 2)` regressed to `Command`. I checked both against the base parser.
- `sqlglot/generators/duckdb.py`: `macrooverloads_sql`.
- `tests/dialects/test_duckdb.py`: a new `test_macro_overloads`. No existing tests changed.

**DuckDB rules I matched.** All overloads must be the same kind. Table overloads need a parenthesized body, `AS TABLE (SELECT ...)`; the bare `TABLE SELECT ...` form only works for a single definition.

**Known gap.** A table overload built programmatically with a bare `Select` body would be emitted without parentheses, which DuckDB rejects. Parsed SQL is fine.

## events
[tool_use Bash] {"command": "grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/expressions.py sqlglot/parser.py sqlglot/generator.py sqlglot/tokens.py | head -80; git log --oneline -1", "description": "Find existing macro handling in sources"}
[tool_result] grep: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
a2581b8d0 lithify: probe base
[tool_use Bash] {"command": "ls; grep -rn -i \"macro\" sqlglot/dialects/duckdb.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions/*.py 2>/dev/null | head -60; grep -rln \"Macro\\|MACRO\" sqlglot tests | head -30", "description": "Locate macro references in source and tests"}
[tool_result] .agents/
.claude/
.github/
.lithify/
benchmarks/
pdoc/
posts/
sqlglot/
sqlglot-integration-tests/
sqlglotc/
tests/
.gitignore  1.9K
.gitmodules  135B
.gitpod.yml  217B
.pre-commit-config.yaml  1.7K
AGENTS.md  18.1K
CHANGELOG.md  1.8M
CLAUDE.md -> AGENTS.md  9B
CONTRIBUTING.md  3.8K
LICENSE  1.0K
MANIFEST.in  70B
Makefile  3.2K
README.md  22.6K
pyproject.toml  1.3K
setup.cfg  241B
setup.py  1.2K
sqlglot.png  7.2K
sqlglot/dialects/duckdb.py:95:            "MACRO": TokenType.FUNCTION,
sqlglot/dialects/duckdb.py
sqlglot/dialects/mysql.py
tests/dialects/test_duckdb.py
[tool_use Bash] {"command": "grep -n -i \"macro\" tests/dialects/test_duckdb.py sqlglot/dialects/mysql.py; grep -rn \"MACRO\\|Macro\" sqlglot/*.py | head; grep -n \"def _parse_create\\b\" -A5 sqlglot/parser.py | head; ls sqlglot | head -50; cat sqlglot/dialects/duckdb.py | sed -n 80,110p", "description": "Inspect macro tests and duckdb tokenizer mapping"}
[tool_result] tests/dialects/test_duckdb.py:2589:        for keyword in ("FUNCTION", "MACRO"):
sqlglot/dialects/mysql.py:138:            "_MACROMAN": TokenType.INTRODUCER,
2346:    def _parse_create(self) -> exp.Create | exp.Command:
2347-        # Note: this can't be None because we've matched a statement parser
2348-        start = self._prev
2349-
2350-        replace = (
2351-            start.token_type == TokenType.REPLACE
dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__
…[1128 chars elided]…
COMMAND,
            "ROW": TokenType.STRUCT,
            "SIGNED": TokenType.INT,
            "STRING": TokenType.TEXT,
            "SUMMARIZE": TokenType.SUMMARIZE,
            "TIMESTAMP": TokenType.TIMESTAMPNTZ,
            "TIMESTAMP_S": TokenType.TIMESTAMP_S,
            "TIMESTAMP_MS": TokenType.TIMESTAMP_MS,
            "TIMESTAMP_NS": TokenType.TIMESTAMP_NS,
            "TIMESTAMP_US": TokenType.TIMESTAMP,
            "UBIGINT": TokenType.UBIGINT,
            "UINTEGER": TokenType.UINT,
[tool_use Bash] {"command": "sed -n 2570,2640p tests/dialects/test_duckdb.py; grep -n \"FUNCTION\\b\" sqlglot/parser.py | head -20; grep -rn \"class Create\\b\" -A40 sqlglot/expressions/*.py | grep -n \"arg_types\\|class\" | head; ls sqlglot/expressions sqlglot/parsers sqlglot/generators", "description": "View existing duckdb macro test and parser hooks"}
[tool_result]         ast.assert_is(exp.Install).name == "httpfs"
        assert isinstance(ast.this, exp.Identifier)

        self.validate_identity("INSTALL httpfs FROM community")
        self.validate_identity("INSTALL httpfs FROM 'https://extensions.duckdb.org'")
        self.validate_identity("FORCE INSTALL httpfs").assert_is(exp.Install).name == "httpfs"
        self.validate_identity("FORCE INSTALL httpfs FROM community")
        self.validate_identity("FORCE INSTALL httpfs FROM 'https://extensions.du
…[4453 chars elided]…
ouse.py  32.9K
databricks.py  1.7K
doris.py  5.0K
dremio.py  3.8K
drill.py  662B
druid.py  108B
duckdb.py  15.4K
dune.py  124B
exasol.py  6.5K
fabric.py  1.3K
hive.py  11.0K
materialize.py  1.3K
mysql.py  24.1K
oracle.py  9.4K
postgres.py  12.9K
presto.py  5.3K
prql.py  6.9K
redshift.py  5.8K
risingwave.py  2.2K
singlestore.py  10.4K
snowflake.py  52.4K
solr.py  353B
spark.py  5.2K
spark2.py  4.2K
sqlite.py  3.5K
starrocks.py  6.4K
tableau.py  507B
teradata.py  7.4K
trino.py  2.0K
tsql.py  26.4K
[tool_use Bash] {"command": "sed -n 2346,2480p sqlglot/parser.py; sed -n 39,64p sqlglot/expressions/ddl.py", "description": "Read _parse_create and Create expression definition"}
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
…[5326 chars elided]…
e,
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
        kind = self.args.get("kind")
        return kind and kind.upper()


class SequenceProperties(Expression):
[tool_use Bash] {"command": "grep -n \"def _parse_user_defined_function\\b\" -A40 sqlglot/parser.py; grep -n \"def _parse_user_defined_function_expression\" -A15 sqlglot/parser.py; grep -n \"def _parse_function_properties\\|def _parse_heredoc\" -A3 sqlglot/parser.py; grep -n \"class UserDefinedFunction\\b\" -A8 sqlglot/expressions/*.py; grep -n \"def userdefinedfunction\\|def createable_sql\\|UserDefinedFunction\\|def create_sql\" sqlglot/generator.py sqlglot/generators/*.py sqlglot/dialects/duckdb.py | head -20", "description": "Read UDF/macro parse and generate helpers"}
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
…[3656 chars elided]…
/snowflake.py:1015:def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
sqlglot/generators/starrocks.py:276:def create_sql(self, expression: exp.Create) -> str:
sqlglot/generators/teradata.py:148:def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
sqlglot/generators/tsql.py:384:def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
sqlglot/generators/tsql.py:401:def create_sql(self, expression: exp.Create) -> str:
[tool_use Bash] {"command": "sed -n 1284,1340p sqlglot/generator.py; sed -n 4585,4600p sqlglot/generator.py; sed -n 2480,2530p sqlglot/parser.py; grep -n \"class Generator\\|def create_sql\\|def createable_sql\\|UserDefinedFunction\\|FUNCTION\" sqlglot/generators/duckdb.py | head", "description": "Read generator create/UDF output logic"}
[tool_result]     def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
        return self.sql(expression, "this")

    def create_sql(self, expression: exp.Create) -> str:
        kind = self.sql(expression, "kind")
        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind

        properties = expression.args.get("properties")

        if (
            kind == "TRIGGER"
            and properties
            and properties.expressions
            and isinstance
…[4495 chars elided]…

                expression = self._parse_types()
                props = self._parse_properties()
                if props:
                    sequence_props = exp.SequenceProperties()
                    options = []
                    for prop in props:
                        if isinstance(prop, exp.SequenceProperties):
4 matches in 4 files:

1853:0:t.ClassVar = _IGNORE_RESPECT_NULLS_WINDOW_FUNCTIONS
3813:0:
3907:0:
sqlglot/generators/duckdb.py:92:_IGNORE_RESPECT_NULLS_WINDOW_FUNCTIONS = (
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sys;print(sqlglot.__file__, sys.version)\"; $PY -c \"import duckdb;print(duckdb.__version__)\"; $PY -c \"\nimport sqlglot\nfor s in ['''CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;''']:\n    try: print(repr(sqlglot.parse_one(s, read='duckdb')))\n    except Exception as e: print('ERR', type(e), e)\n\"", "description": "Check env, duckdb availability, and reproduce failure"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/__init__.py 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
1.5.6
ERR <class 'sqlglot.errors.ParseError'> Invalid expression / Unexpected token. Line 1, Col: 35.
  CREATE MACRO add_x (a, b) AS a + b[4m,[0m (a, b, c) AS a + b + c;
[tool_use Bash] {"command": "cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\nc=duckdb.connect()\ntests=['CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c',\n'CREATE MACRO t(a) AS TABLE SELECT a AS x, 1 AS y, (a) AS TABLE SELECT 2 AS x, 3 AS y',\n'CREATE MACRO t(a) AS TABLE SELECT a AS x FROM range(3), (a) AS TABLE SELECT 2 AS x',\n'CREATE MAC
…[300 chars elided]…
   try:\n        c.execute(t); print('OK ', t)\n    except Exception as e: print('ERR', t, '->', str(e)[:200])\nprint(c.sql(\\\"select function_name, function_type, parameters, parameter_types, macro_definition from duckdb_functions() where function_type in ('macro','table_macro') and function_name in ('add_x','t','m','s')\\\"))\n\"", "description": "Probe DuckDB overloaded macro syntax behavior"}
[tool_result] OK  CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c
ERR CREATE MACRO t(a) AS TABLE SELECT a AS x, 1 AS y, (a) AS TABLE SELECT 2 AS x, 3 AS y -> Parser Error: syntax error at or near "SELECT"

LINE 1: ... MACRO t(a) AS TABLE SELECT a AS x, 1 AS y, (a) AS TABLE SELECT 2 AS x, 3 AS y
                                                              
ERR CREATE MACRO t(a) AS TABLE SELECT a AS x FROM range(3), (a) AS TABLE SELECT 2 AS x -> Parser Error: syntax error at or near ")"

LINE 1: CRE
…[1418 chars elided]…
 │ (a + b)          │
│ add_x         │ macro         │ [a, b, c]  │ [NULL, NULL, NULL] │ ((a + b) + c)    │
│ m             │ macro         │ []         │ []                 │ 1                │
│ m             │ macro         │ [a]        │ [NULL]             │ (a * 2)          │
└───────────────┴───────────────┴────────────┴────────────────────┴──────────────────┘
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1
[tool_use Bash] {"command": "cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\ntests=['CREATE MACRO t1(a) AS TABLE SELECT a AS x, (b) AS TABLE SELECT 2 AS x',\n'CREATE MACRO t2(a) AS TABLE SELECT a AS x, (b, c) AS TABLE SELECT 2 AS x',\n'CREATE MACRO t3(a) AS TABLE SELECT 1 AS x, (b) AS (SELECT 2 AS x)',\n'CREATE MACRO t4(a) AS TABLE SELECT 1 AS x',\n'CR
…[848 chars elided]…
cratch/env-sqlglot/bin/python -I -c \"\nimport duckdb\nc=duckdb.connect()\nc.execute('CREATE MACRO t(a) AS TABLE SELECT 1 AS x')\nc.execute('CREATE MACRO t2(a) AS TABLE SELECT 1 AS x')\nprint(c.sql(\\\"select function_name, function_type, parameters, macro_definition from duckdb_functions() where function_type like '%macro%' \\\"))\n\"", "description": "Probe table macro overload syntax variants"}
[tool_result] ERR CREATE MACRO t1(a) AS TABLE SELECT a AS x, (b) AS TABLE SELECT 2 AS x -> Parser Error: syntax error at or near "SELECT"
ERR CREATE MACRO t2(a) AS TABLE SELECT a AS x, (b, c) AS TABLE SELECT 2 AS x -> Parser Error: syntax error at or near "SELECT"
ERR CREATE MACRO t3(a) AS TABLE SELECT 1 AS x, (b) AS (SELECT 2 AS x) -> Parser Error: syntax error at or near "("
OK  CREATE MACRO t4(a) AS TABLE SELECT 1 AS x
ERR CREATE MACRO t5(a) AS TABLE SELECT 1 AS x, (b) AS TABLE SELECT 2 AS x -> Parser Erro
…[4001 chars elided]…
       │
│ t                         │ table_macro   │ [a]                                 │ SELECT 1 AS x                      │
└───────────────────────────┴───────────────┴─────────────────────────────────────┴────────────────────────────────────┘
  137 rows (20 shown)                                                                                        4 columns
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1
[tool_use Bash] {"command": "cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\nfor t in ['CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)',\n'CREATE MACRO t8(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)',\n'CREATE MACRO t9(a) AS a+1, (a, b) AS TABLE (SELECT 2 AS x)',\n'CREATE MACRO t10(a) AS TABLE (SELECT 1 AS x), (a, b) 
…[472 chars elided]…
)')\nprint(c.sql(\\\"select function_name, function_type, parameters, macro_definition from duckdb_functions() where function_name='t7'\\\"))\n\"; cd ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1 && grep -n \"TABLE\\b\" sqlglot/dialects/duckdb.py | head -20", "description": "Confirm table macro overload forms and duckdb TABLE handling"}
[tool_result] OK  CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
OK  CREATE MACRO t8(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
ERR CREATE MACRO t9(a) AS a+1, (a, b) AS TABLE (SELECT 2 AS x) -> Parser Error: syntax error at or near "TABLE"
ERR CREATE MACRO t10(a) AS TABLE (SELECT 1 AS x), (a, b) AS a+1 -> Parser Error: syntax error at or near "a"
ERR CREATE MACRO t11(a) AS TABLE SELECT 1 AS x, (a, b) AS TABLE (SELECT 2 AS x) -> Parser Error: syntax error at or near "("
OK  
…[209 chars elided]…
me parameters
┌───────────────┬───────────────┬────────────┬──────────────────┐
│ function_name │ function_type │ parameters │ macro_definition │
│    varchar    │    varchar    │ varchar[]  │     varchar      │
├───────────────┼───────────────┼────────────┼──────────────────┤
│ t7            │ table_macro   │ [a]        │ SELECT 1 AS x    │
│ t7            │ table_macro   │ [a, b]     │ SELECT 2 AS x    │
└───────────────┴───────────────┴────────────┴──────────────────┘

0 matches for 'TABLE\b'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS TABLE SELECT 1 AS x', 'CREATE MACRO t(a) AS TABLE (SELECT 1 AS x)', 'CREATE MACRO t(a) AS (SELECT 1 AS x)', 'CREATE MACRO m(a) AS a + 1', 'CREATE MACRO m(a) AS (a + 1)']:\n    try:\n        e=sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n    except Exception as x: print('ERR', x)\n\" 2>&1 | head -80", "description": "Dump current AST for single macro forms"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS TABLE SELECT 1 AS x', 'CREATE MACRO t(a) AS TABLE (SELECT 1 AS x)', 'CREATE MACRO t(a) AS (SELECT 1 AS x)', 'CREATE MACRO m(a) AS a + 1', 'CREATE MACRO m() AS 1']:\n    try:\n        e=sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n    except Exception as x: print('ERR', x)\n\" 2>&1 | head -120", "description": "Dump current AST for single macro forms"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE MACRO t(a) AS TABLE SELECT 1 AS x', 'CREATE MACRO t(a) AS TABLE (SELECT 1 AS x)', 'CREATE MACRO t(a) AS (SELECT 1 AS x)', 'CREATE MACRO m(a) AS a + 1', 'CREATE MACRO m() AS 1']:\n    try:\n        e=sqlglot.parse_one(s, read='duckdb'); print(repr(e)); print(e.sql('duckdb'))\n    except Exception as x: print('ERR', x)\n\" 2>&1 | head -150", "description": "Dump current AST for single macro forms"}
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
      Alias(
        this=Literal(this=1, is_string=False),
        alias=Identifier(this=x, quoted=False))]),
  exists=False,
  properties=Properties(
    expressions=[
      ReturnsProperty(
        this=Schema(
       
…[1551 chars elided]…
Add(
    this=Column(
      this=Identifier(this=a, quoted=False)),
    expression=Literal(this=1, is_string=False)),
  exists=False,
  begin=False,
  concurrently=False)
CREATE MACRO m(a) AS a + 1
Create(
  this=UserDefinedFunction(
    this=Table(
      this=Identifier(this=m, quoted=False)),
    wrapped=True),
  kind=MACRO,
  replace=False,
  refresh=False,
  unique=False,
  expression=Literal(this=1, is_string=False),
  exists=False,
  begin=False,
  concurrently=False)
CREATE MACRO m() AS 1
[tool_use Bash] {"command": "grep -rn \"is_table\" sqlglot/ | head -20; grep -n \"def _parse_returns\" -A30 sqlglot/parser.py | head -50", "description": "Locate table-macro RETURNS/TABLE handling"}
[tool_result] Binary file sqlglot/parsers/__pycache__/duckdb.cpython-312.pyc matches
sqlglot/parsers/duckdb.py:243:                        is_table=True,
sqlglot/optimizer/qualify_tables.py:55:        db.meta["is_table"] = True
sqlglot/optimizer/qualify_tables.py:59:        catalog.meta["is_table"] = True
Binary file sqlglot/__pycache__/schema.cpython-312.pyc matches
Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:3333:        is_table = self._match(TokenType.TABLE)
sqlglot/pa
…[2148 chars elided]…
   return self.expression(exp.ReturnsProperty(this=value, is_table=is_table, null=null))
3351-
3352-    def _parse_describe(self) -> exp.Describe:
3353-        kind = self._prev.text if self._match_set(self.CREATABLES) else None
3354-        style: str | None = (
3355-            self._prev.text.upper() if self._match_texts(self.DESCRIBE_STYLES) else None
3356-        )
3357-        if self._match(TokenType.DOT):
3358-            style = None
3359-            self._retreat(self._index - 2)
3360-
[tool_use Bash] {"command": "sed -n 200,275p sqlglot/parsers/duckdb.py; grep -n \"MACRO\\|Macro\\|ReturnsProperty\\|returnsproperty\" sqlglot/generators/duckdb.py sqlglot/dialects/duckdb.py | head; grep -n \"def returnsproperty_sql\" -A25 sqlglot/generator.py", "description": "Read duckdb parser macro/table handling and returns generator"}
[tool_result ERROR] Exit code 1
        "MAP": lambda self: self._parse_map(),
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
        # https://duckdb.org/docs/sql/d
…[2247 chars elided]…
 Moves the comment next to the alias in `alias: expr /* comment */`
                comments += this.pop_comments() or []

            return self.expression(exp.Alias(this=this, alias=alias), comments=comments)

3 matches in 2 files:

sqlglot/dialects/duckdb.py:95:"MACRO": TokenType.FUNCTION,
sqlglot/generators/duckdb.py:1647:exp.ReturnsProperty: lambda self, e: "TABLE" if isinstance(e.this, exp.Schema...
sqlglot/generators/duckdb.py:1848:exp.ReturnsProperty: exp.Properties.Location.POST_ALIAS,
[tool_use Bash] {"command": "sed -n 1340,1380p sqlglot/generator.py; sed -n 1640,1650p sqlglot/generators/duckdb.py; grep -n \"ReturnsProperty\\|POST_ALIAS\" sqlglot/generator.py | head; grep -n \"class MacroOverloads\\|class UserDefinedFunction\" sqlglot/expressions/*.py; sed -n 220,230p sqlglot/expressions/ddl.py", "description": "Read rest of create_sql and returns generation"}
[tool_result]                 postalias_props_sql = f" {postalias_props_sql}" if postalias_props_sql else ""
                expression_sql = f" AS{postalias_props_sql}{expression_sql}"

        postindex_props_sql = ""
        if properties_locs.get(exp.Properties.Location.POST_INDEX):
            postindex_props_sql = self.properties(
                exp.Properties(expressions=properties_locs[exp.Properties.Location.POST_INDEX]),
                wrapped=False,
                prefix=" ",
            )

    
…[1903 chars elided]…
ies.Location.POST_ALIAS,
732:0:exp.Properties.Location.POST_SCHEMA,
sqlglot/generator.py:1336:expressions=properties_locs[exp.Properties.Location.POST_ALIAS]
1 matches in 1 files:

sqlglot/expressions/ddl.py:225:class UserDefinedFunction(Expression):
        "json": False,
        "iceberg": False,
    }


class UserDefinedFunction(Expression):
    arg_types = {"this": True, "expressions": False, "wrapped": False}


class CharacterSet(Expression):
    arg_types = {"this": True, "default": False}
[assistant] Current state confirmed: a single macro is `Create(this=UDF(name, params), expression=body)`, and the trailing `, (...) AS ...` makes the parser fail. DuckDB itself only accepts overloads where every overload is the same kind (all scalar, or all `TABLE (SELECT ...)`). Checking a few helper signatures before editing.
[tool_use Bash] {"command": "grep -n \"def _parse_wrapped_csv\\|def _parse_csv\\|def _parse_wrapped(\" -A3 sqlglot/parser.py | head -20; grep -n \"def wrap\\b\" -A3 sqlglot/generator.py; grep -n \"def expressions\" -A12 sqlglot/generator.py | head -30; grep -n \"_parse_user_defined_function_expression\\|_parse_function_properties\" sqlglot/parser.py sqlglot/parsers/*.py | head; grep -rn \"UserDefinedFunction\" sqlglot --include=*.py | grep -v \"^sqlglot/parser.py\\|generator.py\" | head", "description": "Check helper signatures and hook conventions"}
[tool_result] 8489:    def _parse_csv(
8490-        self, parse_method: t.Callable[[], T | None], sep: TokenType = TokenType.COMMA
8491-    ) -> list[T]:
8492-        parse_result = parse_method()
--
8507:    def _parse_wrapped_csv(
8508-        self,
8509-        parse_method: t.Callable[[], T | None],
8510-        sep: TokenType = TokenType.COMMA,
--
8517:    def _parse_wrapped(self, parse_method: t.Callable[[], T], optional: bool = False) -> T:
8518-        wrapped = self._match(TokenType.L_PAREN)
8519-   
…[905 chars elided]…
ssion()
sqlglot/parser.py:7022:def _parse_function_properties(self) -> exp.Properties | None:
sqlglot/parser.py:7025:def _parse_user_defined_function_expression(self) -> exp.Expr | None:
sqlglot/parsers/clickhouse.py:486:def _parse_user_defined_function_expression(self) -> exp.Expr | None:
sqlglot/parsers/duckdb.py:237:def _parse_function_properties(self) -> exp.Properties | None:
sqlglot/parsers/duckdb.py:247:return super()._parse_function_properties()
(eval):1: no matches found: --include=*.py
[assistant] Helpers match what I need. Now the edits: a new expression pair, a base-parser hook that returns `None` (so only DuckDB takes the branch), the DuckDB parser override, and the DuckDB generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py", "old_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n", "new_string": "class UserDefinedFunction(Expression):\n    arg_types = {\"this\": True, \"expressions\": False, \"wrapped\": False}\n\n\nclass MacroOverloads(Expression):\n    arg_types = {\"this\": True, \"expressions\": True, \"table\": False}\n\n\nclass MacroOverload(Expression):\n    arg_types = {\"expressions\": False, \"expression\": True}\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "offset": 2420, "limit": 40}
[tool_result] 2420	                        extend_props(self._parse_properties())
2421	                    else:
2422	                        expression = (
2423	                            self._parse_user_defined_function_expression()
2424	                            if create_token_type == TokenType.FUNCTION
2425	                            else self._parse_block()
2426	                        )
2427	
2428	                    if return_:
2429	                        expression = self.expression(exp.Return(
…[948 chars elided]…
50	            timing_var = self._parse_var_from_options(self.TRIGGER_TIMING, raise_unmatched=False)
2451	            timing = timing_var.this if timing_var else None
2452	            if not timing:
2453	                return self._parse_as_command(start)
2454	
2455	            events = self._parse_trigger_events()
2456	            if not self._match(TokenType.ON):
2457	                self.raise_error("Expected ON in trigger definition")
2458	
2459	            table = self._parse_table_parts()
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n        elif create_token_type == TokenType.INDEX:", "new_string": "                    if return_:\n                        expression = self.expression(exp.Return(this=expression))\n\n            if create_token_type == TokenType.FUNCTION and (\n                overloads := self._parse_macro_overloads(this, expression, properties)\n            ):\n                this, expression = overloads, None\n        elif create_token_type == TokenType.INDEX:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py", "old_string": "    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        return self._parse_statement()\n", "new_string": "    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        return self._parse_statement()\n\n    def _parse_macro_overloads(\n        self, this: exp.Expr | None, expression: exp.Expr | None, properties: exp.Properties | None\n    ) -> exp.MacroOverloads | None:\n        return None\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the DuckDB parser override, placed next to the existing `_parse_function_properties` override it depends on.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "        return super()._parse_function_properties()\n\n    def _parse_lambda(", "new_string": "        return super()._parse_function_properties()\n\n    def _parse_macro_overloads(\n        self, this: exp.Expr 
…[727 chars elided]…
o overload parameters\")\n            self._match(TokenType.TABLE)\n            overloads.append(\n                exp.MacroOverload(\n                    expressions=params, expression=self._parse_user_defined_function_expression()\n                )\n            )\n\n        return self.expression(exp.MacroOverloads(this=this.this, expressions=overloads, table=table))\n\n    def _parse_lambda("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now the DuckDB generator. Let me find the existing method style in that file.
[tool_use Bash] {"command": "grep -n \"^def \\|^class \\|^    def \" sqlglot/generators/duckdb.py | head -80", "description": "List generator method layout in duckdb generator"}
[tool_result] 193 matches in 176 files:

1025:0:DuckDBGenerator, expression: exp.AnyValue) -> str:
1067:0:DuckDBGenerator, literal: str) -> str:
1150:0:DuckDBGenerator, expression: exp.Initcap) -> str:
1163:0:DuckDBGenerator, expression: exp.BoolxorAgg) -> str:
1255:0:DuckDBGenerator, expression: exp.Floor | exp.Ceil) -> str:
1330:0:exp.DateFromParts) -> str:
1361:0:exp.Expr, round_input: bool | None = None) -> exp.Expr:
1367:0:DuckDBGenerator, expression: exp.Boolnot) -> str:
1372:0:DuckDBGenerator, expressi
…[1944 chars elided]…
:exp.TimeFromParts) -> str:
2855:0:exp.Extract) -> str:
292:0:DuckDBGenerator, expression: exp.Date) -> str:
2920:0:exp.TimestampFromParts) -> str:
2949:0:exp.TimestampLtzFromParts) -> str:
2958:0:exp.TimestampTzFromParts) -> str:
2996:0:exp.Join) -> str:
3013:0:exp.CountIf) -> str:
3020:0:exp.Bracket) -> str:
3042:0:exp.WithinGroup) -> str:
3084:0:exp.Length) -> str:
310:0:DuckDBGenerator, expression: exp.TimeDiff) -> str:
3111:0:exp.BitLength) -> str:
3118:0:exp.Chr, name: str = "CHR") -> str:
[tool_use Bash] {"command": "sed -n 2555,2566p sqlglot/generators/duckdb.py", "description": "View style of a small duckdb generator function"}
[tool_result]             exp.Literal.string("DESC" if descending else "ASC"),
            exp.Literal.string("NULLS FIRST"),
        )

    def install_sql(self, expression: exp.Install) -> str:
        force = "FORCE " if expression.args.get("force") else ""
        this = self.sql(expression, "this")
        from_clause = expression.args.get("from_")
        from_clause = f" FROM {from_clause}" if from_clause else ""
        return f"{force}INSTALL {this}{from_clause}"

    def approxtopk_sql(self, expression: exp.ApproxTopK) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py", "old_string": "        return f\"{force}INSTALL {this}{from_clause}\"\n\n    def approxtopk_sql(", "new_string": "        return f\"{force}INSTALL {this}{from_clause}\"\n\n    def macrooverloads_sql(self, expression: exp.MacroOverloads) -> str:\n        table = \" TABLE\" if expression.args.get(\"table\") else \"\"\n        overloads = \", \".join(\n            f\"{self.wrap(self.expressions(overload, flat=True))} AS{table} {self.sql(overload, 'expression')}\"\n            for overload in expression.expressions\n        )\n        return f\"{self.sql(expression, 'this')}{overloads}\"\n\n    def approxtopk_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[assistant] Now let me exercise the change against the cases from the issue plus the scalar, zero-arg, and table forms DuckDB accepts.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n'''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''',\n'CREATE MACRO m() AS 1, (a) AS a * 2',\n'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)',\n'CREATE MACRO t(a) AS TABLE SELECT 1 AS x',\n]\nfor s in cases:\n    e = sqlglot.parse_one(s, read='duckdb')\n    print(e.sql('duckdb'))\nprint(repr(sqlglot.parse_one(cases[1], read='duckdb').this))\n\" 2>&1 | head -80", "description": "Check round-trip for overloaded macro cases"}
[tool_result] 'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
CREATE OR REPLACE MACRO add_2(a, b) AS a + b
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE MACRO m() AS 1, (a) AS a * 2
CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
CREATE MACRO t(a) AS TABLE SELECT 1 AS x
MacroOverloads(
  this=Table(
    this=Identifier(this=add_x, quoted=False)),
  expressions=[
 
…[252 chars elided]…
 this=Identifier(this=b, quoted=False)))),
    MacroOverload(
      expressions=[
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
          this=Identifier(this=c, quoted=False))))],
  table=False)
[assistant] The scalar overloads now parse and round-trip. The `TABLE (SELECT ...)` case falls back to a `Command`, so I'll find out where it stops.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\nfor s in ['CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)', 'CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)', 'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x)']:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE); print(type(e).__name__, e.sql('duckdb'))\n    except Exception as x: print('ERR', str(x)[:300])\n\"", "description": "Debug table overload parse failure"}
[tool_result] 'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
Command CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
Create CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.dialects.duckdb import DuckDB\nP = DuckDB.Parser\norig = P._parse_macro_overloads\ndef spy(self, this, expression, properties):\n    print('hook: curr=', self._curr.text if self._curr else None, 'expr=', type(expression).__name__, repr(expression)[:200].replace(chr(10),' '))\n    return orig(self, this, expression, properties)\nP._parse_macro_overloads = spy\ns='CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)'\ne = sqlglot.parse_one(s, read='duckdb')\nprint(type(e).__name__)\nprint(repr(sqlglot.parse_one('SELECT 1', read='duckdb')))\n\" 2>&1 | tail -20", "description": "Trace hook invocation for subquery body overloads"}
[tool_result] 'CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)' contains unsupported syntax. Falling back to parsing as a 'Command'.
hook: curr= ( expr= Subquery Subquery(   this=Select(     expressions=[       Alias(         this=Literal(this=1, is_string=False),         alias=Identifier(this=x, quoted=False))]),   joins=[     Join(       this=Subquery(      
Command
Select(
  expressions=[
    Literal(this=1, is_string=False)])
[assistant] The subquery body swallows the following `, (a, b)` as an implicit comma join inside the parenthesized query. Let me see where that happens in the parser.
[tool_use Bash] {"command": "grep -n \"def _parse_subquery\\|def _parse_query_modifiers\\|def _parse_join(\\|def _parse_statement\\|NO_PAREN_IF_COMMANDS\\|def _parse_paren\" sqlglot/parser.py; sed -n \"$(grep -n 'def _parse_subquery' sqlglot/parser.py | cut -d: -f1),+25p\" sqlglot/parser.py", "description": "Locate subquery and query-modifier parsing functions"}
[tool_result] rg: regex parse error:
    (?:def _parse_subquery|def _parse_query_modifiers|def _parse_join(|def _parse_statement|NO_PAREN_IF_COMMANDS|def _parse_paren)
    ^
error: unclosed group
0 matches for 'def _parse_subquery\|def _parse_query_modifiers\|def _parse_join(\|def _parse_statement\|NO_PAREN_IF_COMMANDS\|def _parse_paren'
    def _parse_subquery(
        self, this: exp.Expr | None, parse_alias: bool = True
    ) -> exp.Subquery | None:
        if not this:
            return None

        ret
…[356 chars elided]…
er.normalize_identifiers import normalize_identifiers as _norm

        refs = {_norm(this.args["from_"].this.copy(), dialect=self.dialect).alias_or_name}
        for i, join in enumerate(this.args.get("joins") or []):
            table = join.this
            normalized_table = table.copy()
            normalized_table.meta["maybe_column"] = True
            normalized_table = _norm(normalized_table, dialect=self.dialect)

            if isinstance(table, exp.Table) and not join.args.get("on"):
[tool_use Bash] {"command": "grep -n \"_parse_query_modifiers(\" sqlglot/parser.py | head; grep -n \"def _parse_query_modifiers\" -A25 sqlglot/parser.py | head -45; grep -n \"def _parse_join(\" -A12 sqlglot/parser.py | head -20", "description": "Inspect query modifier and join parsing"}
[tool_result] rg: regex parse error:
    (?:_parse_query_modifiers()
    ^
error: unclosed group
0 matches for '_parse_query_modifiers('
4116:    def _parse_query_modifiers(self, this: E) -> E: ...
4117-
4118-    @t.overload
4119:    def _parse_query_modifiers(self, this: None) -> None: ...
4120-
4121:    def _parse_query_modifiers(self, this):
4122-        if isinstance(this, self.MODIFIABLES):
4123-            for join in self._parse_joins():
4124-                this.append("joins", join)
4125-            
…[1143 chars elided]…
4410-        parse_bracket: bool = False,
4411-        alias_tokens: t.Collection[TokenType] | None = None,
4412-    ) -> exp.Join | None:
4413-        if self._match(TokenType.COMMA):
4414-            table = self._try_parse(lambda: self._parse_table(alias_tokens=alias_tokens))
4415-            cross_join = self.expression(exp.Join(this=table)) if table else None
4416-
4417-            if cross_join and self.JOINS_HAVE_EQUAL_PRECEDENCE:
4418-                cross_join.set("kind", "CROSS")
4419-
[assistant] The comma gets consumed by the base parser's query-modifier logic for a parenthesized `Subquery`. Let me look at how a parenthesized select is parsed to find the narrowest place to stop that.
[tool_use Bash] {"command": "grep -n \"def _parse_paren\\b\\|def _parse_paren(\" sqlglot/parser.py; L=$(grep -n \"def _parse_paren(\" sqlglot/parser.py | cut -d: -f1); sed -n \"${L},$((L+75))p\" sqlglot/parser.py | grep -n \"\" | sed -n 1,80p", "description": "Read paren/subquery parse path"}
[tool_result] 6770:    def _parse_paren(self) -> exp.Expr | None:
1:    def _parse_paren(self) -> exp.Expr | None:
2:        if not self._match(TokenType.L_PAREN):
3:            return None
4:
5:        comments = self._prev_comments
6:        query = self._parse_select()
7:
8:        if query:
9:            expressions = [query]
10:        else:
11:            expressions = self._parse_expressions()
12:
13:        this = seq_get(expressions, 0)
14:
15:        if not this and self._match(TokenType.R_PAREN, ad
…[2017 chars elided]…
nc: bool = False,
66:    ) -> exp.Expr | None:
67:        if anonymous_func:
68:            field = (
69:                self._parse_function(anonymous=anonymous_func, any_token=any_token)
70:                or self._parse_primary()
71:            )
72:        else:
73:            field = self._parse_primary() or self._parse_function(
74:                anonymous=anonymous_func, any_token=any_token
75:            )
76:        return field or self._parse_id_var(any_token=any_token, tokens=tokens)
[assistant] The culprit is the statement-level `(`-prefixed branch in `_parse_select`, which applies `_parse_query_modifiers` (and so comma joins) to a parenthesized query. Let me check for an existing token set for query starts before choosing a narrow fix.
[tool_use Bash] {"command": "grep -n \"SELECT_START\\|DDL_SELECT_TOKENS\\s*=\\|QUERY_START\" sqlglot/parser.py | head; L=$(grep -n \"    def _parse_select(\" sqlglot/parser.py | cut -d: -f1); sed -n \"$L,$((L+12))p\" sqlglot/parser.py; grep -n \"elif self._match(TokenType.L_PAREN)\" -A12 sqlglot/parser.py | sed -n 1,30p", "description": "Find query-start token sets and paren select branch"}
[tool_result] 1697:    SELECT_START_TOKENS: t.ClassVar = {TokenType.L_PAREN, TokenType.WITH, TokenType.SELECT}
7127:        if self._match_set(self.SELECT_START_TOKENS):
    def _parse_select(
        self,
        nested: bool = False,
        table: bool = False,
        parse_subquery_alias: bool = True,
        parse_set_operation: bool = True,
        consume_pipe: bool = True,
        from_: exp.From | None = None,
    ) -> exp.Expr | None:
        query = self._parse_select_query(
            nested=ne
…[125 chars elided]…
Type.L_PAREN):
3510-                conflict_keys = self._parse_csv(self._parse_id_var)
3511-                self._match_r_paren()
3512-
3513-        index_predicate = self._parse_where()
3514-
3515-        action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
3516-        if self._prev.token_type == TokenType.UPDATE:
3517-            self._match(TokenType.SET)
3518-            expressions = self._parse_csv(self._parse_equality)
3519-        else:
3520-            expressions = None
3521-
[tool_use Bash] {"command": "L=$(grep -n \"    def _parse_select_query(\" sqlglot/parser.py | cut -d: -f1); sed -n \"$L,$((L+60))p\" sqlglot/parser.py | grep -n \"L_PAREN\" -A14 | head -40", "description": "Read paren branch inside select-query parser"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"TokenType.L_PAREN\" sqlglot/parser.py | sed -n 1,60p", "description": "List L_PAREN handling sites in parser"}
[tool_result] 61 matches in 45 files:

10010:0:
1408:0:
1567:0:t.ClassVar = {TokenType.SELECT, TokenType.WITH, TokenType.L_PAREN}
1697:0:t.ClassVar = {TokenType.L_PAREN, TokenType.WITH, TokenType.SELECT}
1712:0:t.ClassVar = {TokenType.ON, TokenType.COMMA, TokenType.L_PAREN}
2313:0:
2505:0:
2894:0:
2912:0:
2953:0:
3509:0:
3730:0:
3919:0:
4056:0:
4288:0:
4517:0:
4579:0:
4950:0:
5041:0:
5136:0:
5174:0:
5871:0:
6245:0:
6313:0:
6771:0:
6908:0:
7044:0:
7085:0:
7122:0:
7221:0:
7242:0:
7259:0:
7293:0:
7527:0:
7669:0:
…[554 chars elided]…
hed_l_paren = self._prev.token_type == TokenType.L_PAREN
sqlglot/parser.py:6618:and (not self._next or self._next.token_type != TokenType.L_PAREN)
sqlglot/parser.py:7180:or self._next.token_type == TokenType.L_PAREN
sqlglot/parser.py:7523:and self._next.token_type == TokenType.L_PAREN
sqlglot/parser.py:8528:wrapped = self._match(TokenType.L_PAREN)
sqlglot/parser.py:8770:if self._match(TokenType.L_PAREN, advance=False) or self._match_text_seq(
sqlglot/parser.py:9421:self._match(TokenType.L_PAREN)
[tool_use Bash] {"command": "sed -n 5866,5900p sqlglot/parser.py", "description": "Read the parenthesized query branch in select parser"}
[tool_result]     def _parse_in(self, this: exp.Expr | None, alias: bool = False) -> exp.In:
        unnest = self._parse_unnest(with_alias=False)
        if unnest:
            this = self.expression(exp.In(this=this, unnest=unnest))
        elif self._match_set((TokenType.L_PAREN, TokenType.L_BRACKET)):
            matched_l_paren = self._prev.token_type == TokenType.L_PAREN
            expressions = self._parse_csv(lambda: self._parse_select_or_expression(alias=alias))

            if len(expressions) == 1
…[481 chars elided]…
raise_error("Expecting ]")
        else:
            this = self.expression(exp.In(this=this, field=self._parse_column()))

        return this

    def _parse_between(self, this: exp.Expr | None) -> exp.Between:
        symmetric = None
        if self._match_text_seq("SYMMETRIC"):
            symmetric = True
        elif self._match_text_seq("ASYMMETRIC"):
            symmetric = False

        low = self._parse_bitwise()
        self._match(TokenType.AND)
        high = self._parse_bitwise()
[assistant] That isn't the statement-level path. Rather than chase every branch, I'll override the body parser in the DuckDB parser: a body that starts with a parenthesized query gets parsed as just the paren'd subquery, so the separator comma is left for the overload loop. Other bodies keep the base behavior.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "    def _parse_macro_overloads(\n        self, this: exp.Expr | None, expression: exp.Expr | None, properties: exp.Properties | None\n    ) -> exp.MacroOverloads | None:", "new_string": "    def _parse_user_defin
…[189 chars elided]…
, advance=False) and self._next.token_type in (\n            TokenType.SELECT,\n            TokenType.WITH,\n        ):\n            return self._parse_paren()\n        return super()._parse_user_defined_function_expression()\n\n    def _parse_macro_overloads(\n        self, this: exp.Expr | None, expression: exp.Expr | None, properties: exp.Properties | None\n    ) -> exp.MacroOverloads | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\ncases = [\n'CREATE OR REPLACE MACRO add_2(a, b) AS a + b',\n'''CREATE MACRO add_x\n    (a, b) AS a + b,\n    (a, b, c) AS a + b + c;''',\n'CREATE MACRO m() AS 1, (a) AS a * 2',\n'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 A
…[98 chars elided]…
 TABLE SELECT 1 AS x',\n'CREATE MACRO t(a) AS (SELECT 1 AS x)',\n'CREATE MACRO t(a) AS (a + 1) * 2',\n]\nfor s in cases:\n    try:\n        e = sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE)\n        print(type(e).__name__, '|', e.sql('duckdb'))\n    except Exception as x: print('ERR', s, '->', str(x)[:150])\n\"", "description": "Re-run overload round-trip cases after body fix"}
[tool_result] Create | CREATE OR REPLACE MACRO add_2(a, b) AS a + b
Create | CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
Create | CREATE MACRO m() AS 1, (a) AS a * 2
Create | CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
Create | CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
Create | CREATE MACRO t(a) AS TABLE SELECT 1 AS x
Create | CREATE MACRO t(a) AS (SELECT 1 AS x)
Create | CREATE MACRO t(a) AS (a + 1) * 2
[assistant] All eight cases now parse and round-trip, including the existing single-macro outputs. Next I'll verify the generated SQL is accepted by DuckDB itself, and check the test helper signature before adding tests.
[tool_use Bash] {"command": "grep -n \"def validate_identity\" -A12 tests/dialects/test_dialect.py | head -20; cd /tmp && <work>/env-sqlglot/bin/python -I -c \"\nimport duckdb\nc = duckdb.connect()\nfor s in ['CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c', 'CREATE MACRO m() AS 1, (a) AS a * 2', 'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)', 'CREATE MACRO t8(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)']:\n    c.execute(s); print('duckdb accepted:', s)\nprint(c.sql(\\\"select function_name, parameters, function_type from duckdb_functions() where function_name in ('add_x','m','t7','t8') order by 1\\\"))\n\"", "description": "Verify sqlglot-generated overloads run in DuckDB"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
60-        else:
61-            expression = self.parse_one(sql)
62-
63-        self.assertEqual(
64-            write_sql or sql,
…[630 chars elided]…
x         │ [a, b, c]  │ macro         │
│ m             │ []         │ macro         │
│ m             │ [a]        │ macro         │
│ t7            │ [a]        │ table_macro   │
│ t7            │ [a, b]     │ table_macro   │
│ t8            │ [a]        │ macro         │
│ t8            │ [a, b]     │ macro         │
└───────────────┴────────────┴───────────────┘
Shell cwd was reset to ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1
[assistant] DuckDB accepts the generated SQL and registers each overload with the right arity and kind. Now I'll add a regression test next to the existing UDF/macro test, leaving existing tests untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\",", "new_string": "    def test_macro_overloads(self):\n        self.validate_identity(\n           
…[418 chars elided]…
identity(\"CREATE MACRO m() AS 1, (a) AS a * 2\")\n        self.validate_identity(\"CREATE MACRO m(a) AS (SELECT a), (a, b) AS (SELECT a + b)\")\n        self.validate_identity(\n            \"CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS x)\"\n        )\n\n    def test_bitwise_agg(self):\n        self.validate_all(\n            \"SELECT BIT_OR(int_value) FROM t\","}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_duckdb.py 2>&1 | tail -25", "description": "Run DuckDB dialect tests"}
[tool_result] ........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.32s
[assistant] DuckDB tests pass. Now the full suite with the project's check command, then lint.
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
1114 passed, 18162 subtests passed in 46.05s
[assistant] The full suite passes (1114 tests, 18162 subtests). Now lint and format on the changed files, since one generator line is long.
[tool_use Bash] {"command": "grep -n \"^style\" -A6 Makefile; ENV=<work>/env-sqlglot/bin; ls $ENV | grep -i \"ruff\\|mypy\"; $ENV/ruff --version 2>/dev/null; $ENV/ruff format --check sqlglot/parser.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py tests/dialects/test_duckdb.py 2>&1 | tail -5; $ENV/ruff check sqlglot tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Run ruff format and lint checks on changed files"}
[tool_result] 96:style:
97-	pre-commit run --all-files
98-	@if [ -f sqlglot-integration-tests/Makefile ]; then \
99-		MYPYPATH=$(abspath .) $(MAKE) -C sqlglot-integration-tests style && \
100-		$(MAKE) -C sqlglot-integration-tests check-submodule; \
101-	fi
102-
dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
ruff 0.15.6
Would reformat: sqlglot/parsers/duckdb.py
1 file would be reformatted, 4 files already formatted
All checks passed!
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; $ENV/ruff format --diff sqlglot/parsers/duckdb.py 2>&1 | head -30", "description": "Show the formatting diff for duckdb parser"}
[tool_result] --- sqlglot/parsers/duckdb.py
+++ sqlglot/parsers/duckdb.py
@@ -278,7 +278,9 @@
                 )
             )
 
-        return self.expression(exp.MacroOverloads(this=this.this, expressions=overloads, table=table))
+        return self.expression(
+            exp.MacroOverloads(this=this.this, expressions=overloads, table=table)
+        )
 
     def _parse_lambda(self, alias: bool = False) -> exp.Expr | None:
         index = self._index

1 file would be reformatted
[assistant] Only a line-wrap difference in my new parser method. I'll apply the formatter to that file and run mypy on the touched modules, since the project's pre-commit includes it.
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; $ENV/ruff format sqlglot/parsers/duckdb.py && $ENV/ruff format --check sqlglot tests/dialects/test_duckdb.py | tail -1; grep -n \"mypy\" -A8 .pre-commit-config.yaml | head -15; $ENV/mypy sqlglot/parser.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -8", "description": "Format duckdb parser and run mypy on touched modules", "timeout": 600000}
[tool_result] 1 file reformatted
177 files already formatted
48:      - id: mypy
49:        name: mypy
50:        entry: mypy sqlglot tests
51-        language: system
52-        types: [ python ]
53-        files: ^(sqlglot/|tests/)
54-        pass_filenames: false
Success: no issues found in 4 source files
[This command modified 1 file you've previously read: sqlglot/parsers/duckdb.py. Call Read before editing.]
[assistant] That file change is my own `ruff format` run, as expected. mypy is clean and ruff reports everything formatted. Let me review the full diff.
[tool_use Bash] {"command": "git status --short && git diff", "description": "Show the full working tree diff"}
[tool_result]  M sqlglot/expressions/ddl.py
 M sqlglot/generators/duckdb.py
 M sqlglot/parser.py
 M sqlglot/parsers/duckdb.py
 M tests/dialects/test_duckdb.pysqlglot/expressions/ddl.py    |  8 ++++++++
 sqlglot/generators/duckdb.py  |  8 ++++++++
 sqlglot/parser.py             | 10 ++++++++++
 sqlglot/parsers/duckdb.py     | 36 ++++++++++++++++++++++++++++++++++++
 tests/dialects/test_duckdb.py | 17 +++++++++++++++++
 5 files changed, 79 insertions(+)

--- Changes ---

sqlglot/expressions/ddl.py
  @@ -226,6 +
…[4455 chars elided]…
+        self.assertEqual(len(ast.this.expressions), 2)
  +
  +        self.validate_identity("CREATE MACRO m() AS 1, (a) AS a * 2")
  +        self.validate_identity("CREATE MACRO m(a) AS (SELECT a), (a, b) AS (SELECT a + b)")
  +        self.validate_identity(
  +            "CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS x)"
  +        )
  +
       def test_bitwise_agg(self):
           self.validate_all(
               "SELECT BIT_OR(int_value) FROM t",
  +17 -0
[assistant] The diff is close. Before tidying, one risk to check: the body override also applies to single-definition macros that begin with `(SELECT`. I'll compare a few such bodies against the base parser's behavior using a monkeypatch, not a stash.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import parser\nfrom sqlglot.dialects.duckdb import DuckDB\nfrom sqlglot.errors import ErrorLevel\ncases = ['CREATE MACRO m() AS (SELECT 1) + 1', 'CREATE MACRO m() AS (SELECT 1) UNION (SELECT 2)', 'CREATE MACRO m(a) AS (SELECT a) AS x', 'CREATE MACRO m(a) AS (WITH c AS (SELECT 
…[195 chars elided]…
evel.RAISE); print(tag, type(e).__name__, '|', e.sql('duckdb'))\n        except Exception as x: print(tag, 'ERR', str(x).split(chr(10))[0][:110])\nrun('new ')\nDuckDB.Parser._parse_user_defined_function_expression = parser.Parser._parse_user_defined_function_expression\nrun('base')\n\" 2>&1 | grep -v \"unsupported syntax\"", "description": "Compare paren-body parsing against base parser behavior"}
[tool_result] new  Command | CREATE MACRO m() AS (SELECT 1) + 1
new  Command | CREATE MACRO m() AS (SELECT 1) UNION (SELECT 2)
new  Command | CREATE MACRO m(a) AS (SELECT a) AS x
new  Create | CREATE MACRO m(a) AS (WITH c AS (SELECT 1) SELECT * FROM c)
new  Command | CREATE MACRO m(a) AS TABLE (SELECT 1) ORDER BY 1
base Create | CREATE MACRO m() AS (SELECT 1) + 1
base Create | CREATE MACRO m() AS (SELECT 1) UNION (SELECT 2)
base Create | CREATE MACRO m(a) AS (SELECT a) AS x
base Create | CREATE MACRO m(a) AS (WITH c AS (SELECT 1) SELECT * FROM c)
base Create | CREATE MACRO m(a) AS TABLE (SELECT 1) ORDER BY 1
[assistant] That's a regression: `(SELECT 1) + 1` and `(SELECT 1) UNION (SELECT 2)` parsed before and now fall back to `Command`. I'll narrow the override so it only keeps the parenthesized query when the next token is the overload separator or the end of the statement, and otherwise backtracks to the base behavior.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "    def _parse_user_defined_function_expression(self) -> exp.Expr | None:\n        # A parenthesized query body must not absorb the comma that separates overloads as a join\n        if self._match(TokenType.L_PAR
…[498 chars elided]…
t.token_type in (\n            TokenType.SELECT,\n            TokenType.WITH,\n        ):\n            index = self._index\n            query = self._parse_paren()\n            if self._curr is None or self._curr.token_type in (TokenType.COMMA, TokenType.SEMICOLON):\n                return query\n            self._retreat(index)\n\n        return super()._parse_user_defined_function_expression()"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py", "old_string": "        # A parenthesized query body followed by an overload separator must not absorb the comma as a join\n", "new_string": "        # Don't let a parenthesized query body absorb the overload separator comma as a join\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/parsers/duckdb.py has been updated successfully.
[assistant] Now I'll tidy the generator's long f-string into two literal parts and simplify the awkward first assertion in the test, then re-run the regression comparison.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py", "old_string": "            f\"{self.wrap(self.expressions(overload, flat=True))} AS{table} {self.sql(overload, 'expression')}\"\n            for overload in expression.expressions", "new_string": "            f\"{self.wrap(self.expressions(overload, flat=True))} AS{table} \"\n            f\"{self.sql(overload, 'expression')}\"\n            for overload in expression.expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\n            \"CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c\",\n        ).assert_is(exp.Create).this.assert_is(exp.MacroOverloads)\n\n        ast = self.validate_i
…[945 chars elided]…
 2\")\n        self.validate_identity(\"CREATE MACRO m(a) AS (SELECT a), (a, b) AS (SELECT a + b)\")\n        self.validate_identity(\n            \"CREATE MACRO t(a) AS TABLE (SELECT a AS x), (a, b) AS TABLE (SELECT a + b AS x)\"\n        )\n        self.validate_identity(\"CREATE MACRO m() AS (SELECT 1) + 1\")\n        self.validate_identity(\"CREATE MACRO m() AS (SELECT 1) UNION (SELECT 2)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-194157-duckdb-dialect-overloaded-macro/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] Now the checks again: formatter, lint, mypy, the regression comparison, and the test suites.
[tool_use Bash] {"command": "ENV=<work>/env-sqlglot/bin; $ENV/ruff format sqlglot tests/dialects/test_duckdb.py | tail -1; $ENV/ruff check sqlglot tests/dialects/test_duckdb.py | tail -1; $ENV/mypy sqlglot/parser.py sqlglot/parsers/duckdb.py sqlglot/generators/duckdb.py sqlglot/expressions/ddl.py 2>&1 | tail -1; $ENV/python -m pytest -q -p no:cacheprovider --color=no te
…[189 chars elided]…
 'CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)', 'CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)']:\n    print(sqlglot.parse_one(s, read='duckdb', error_level=ErrorLevel.RAISE).sql('duckdb'))\n\"; $ENV/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Format, lint, type-check, and run all tests", "timeout": 900000}
[tool_result] 1 file reformatted, 176 files left unchanged
All checks passed!
Success: no issues found in 4 source files
........................ [ 53%]
.....................    [100%]
45 passed, 600 subtests passed in 0.22s
CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
CREATE MACRO t7(a) AS (SELECT 1 AS x), (a, b) AS (SELECT 2 AS x)
CREATE MACRO t7(a) AS TABLE (SELECT 1 AS x), (a, b) AS TABLE (SELECT 2 AS x)
.....................................                     [100%]
1114 passed, 18162 subtests passed in 45.62s
[This command modified 1 file you've previously read: sqlglot/parsers/duckdb.py. Call Read before editing.]
[assistant] Overloaded DuckDB macros now parse and round-trip, including scalar, zero-argument, and table forms. The full suite passes (1114 tests, 18162 subtests), and ruff and mypy are clean. I haven't committed anything.

```python
sqlglot.parse_one("CREATE MACRO add_x (a, b) AS a + b, (a, b, c) AS a + b + c;", read="duckdb").sql("duckdb")
# CREATE MACRO add_x(a, b) AS a + b, (a, b, c) AS a + b + c
```

I also ran the generated SQL through DuckDB 1.5.6. It accepts it and registers each overload with the right arity.

**Representation.** For an overloaded macro, `Create.this` is an `exp.MacroOverloads` 
…[926 chars elided]…
CT 1) UNION (SELECT 2)` regressed to `Command`. I checked both against the base parser.
- `sqlglot/generators/duckdb.py`: `macrooverloads_sql`.
- `tests/dialects/test_duckdb.py`: a new `test_macro_overloads`. No existing tests changed.

**DuckDB rules I matched.** All overloads must be the same kind. Table overloads need a parenthesized body, `AS TABLE (SELECT ...)`; the bare `TABLE SELECT ...` form only works for a single definition.

**Known gap.** A table overload built programmatically with a bare `Select` body would be emitted without parentheses, which DuckDB rejects. Parsed SQL is fine.
