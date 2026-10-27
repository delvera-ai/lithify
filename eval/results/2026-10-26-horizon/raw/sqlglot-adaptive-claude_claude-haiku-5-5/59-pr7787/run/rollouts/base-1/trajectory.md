# trajectory base-1

final message:
Snowflake `CREATE TABLE` now accepts `KEY=VALUE` properties before the column list. Both forms parse and emit the same canonical SQL, `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`.

**Change**
- `sqlglot/parsers/snowflake.py`: I added a `_parse_property_before` override. When the current token is followed by `=`, it uses the generic property parser. Otherwise it defers to the base parser. The base pre-schema pass only recognized entries in `PROPERTY_PARSERS`, so generic `KEY=VALUE` properties were never consumed there.
- `tests/dialects/test_snowflake.py`: added `test_create_table_properties_before_schema`, which covers the leading form (with canonical output) and the trailing form.

**Verification**
- Full suite: 1127 passed, 18271 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.

**Design note**
My first attempt was a plain fallback to `_parse_property()` whenever the base returned nothing. It broke six existing tests, including `CREATE TABLE foo (bar DOUBLE AUTOINCREMENT ...)`. The generic parser calls `_parse_column()` on arbitrary tokens such as `(`, and that can leave parse errors behind even after a retreat. The `=` lookahead avoids that path entirely.

The change is in the Snowflake parser only; base and other dialects are untouched. I haven't committed anything.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/.claude/skills/sqlglot-syntax-support

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

[tool_use Bash] {"command": "ls sqlglot/parsers/ | head -50 && grep -n \"CHANGE_TRACKING\\|_parse_create\\|PROPERTY_PARSERS\\|_parse_properties\" sqlglot/parsers/snowflake.py sqlglot/parser.py | head -60", "description": "Locate Snowflake parser and CREATE property handling"}
[tool_result] __init__.py
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
sqlglot/parsers/snowflake.py:767:    PROPERTY_PARSERS = {
sqlglot/parsers/snowflake.py:768:        **parser.Parser.PROPERTY_PARSERS,
sqlglo
…[2650 chars elided]…
lot/parser.py:7088:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7089:            elif self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7090:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
sqlglot/parser.py:8896:            properties = self._parse_wrapped(self._parse_properties, optional=True)
sqlglot/parser.py:9017:        properties = self._parse_properties()
[assistant] The skill's guidance is loaded. The Claude Docs tools that just appeared aren't needed for this SQL fix, so I'll keep going with the parser. Next I'm reading `_parse_create` to see where properties before the schema are handled.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", "offset": 2360, "limit": 280}
[tool_result] 2360	    def _parse_create(self) -> exp.Create | exp.Command:
2361	        # Note: this can't be None because we've matched a statement parser
2362	        start = self._prev
2363	
2364	        replace = (
2365	            start.token_type == TokenType.REPLACE
2366	            or self._match_pair(TokenType.OR, TokenType.REPLACE)
2367	            or self._match_pair(TokenType.OR, TokenType.ALTER)
2368	        )
2369	        refresh = self._match_pair(TokenType.OR, TokenType.REFRESH)
2370	
2371	  
…[12051 chars elided]…
29	                this=this,
2630	                kind=self.dialect.CREATABLE_KIND_MAPPING.get(create_kind_text) or create_kind_text,
2631	                replace=replace,
2632	                refresh=refresh,
2633	                unique=unique,
2634	                expression=expression,
2635	                exists=exists,
2636	                properties=properties,
2637	                indexes=indexes,
2638	                no_schema_binding=no_schema_binding,
2639	                begin=begin,
[tool_use Bash] {"command": "sed -n 2865,2900p sqlglot/parser.py && grep -n \"CHANGE_TRACKING\\|change_tracking\" -ri sqlglot tests | head; grep -n \"def _parse_schema\\|def _parse_wrapped_csv\" sqlglot/parser.py", "description": "Inspect properties parsing and CHANGE_TRACKING usages"}
[tool_result]         self._match(TokenType.ALIAS)

        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))

    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
        properties = []
        while True:
            if before:
                prop = self._parse_property_before()
            else:
                prop = self._parse_property()
            if not prop:
                break
            for p in ensure_list(prop):
                p
…[650 chars elided]…
ingsProperty:
        return self.expression(
            exp.SettingsProperty(expressions=self._parse_csv(self._parse_assignment))
tests/dialects/test_snowflake.py:5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
tests/dialects/test_snowflake.py:5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
8615:    def _parse_wrapped_csv(
[assistant] Next I'll reproduce both forms to confirm the failure and see what each one parses to.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try:\n        e = sqlglot.parse_one(s, read='snowflake')\n        print(type(e).__name__, '|', e.sql('snowflake'))\n        print(repr(e.args.get('properties')))\n    except Exception as ex: print('ERR', ex)\n\"; grep -n \"_parse_property_before\" -A25 sqlglot/parser.py | head -60", "description": "Reproduce both CREATE TABLE forms in Snowflake"}
[tool_result] ERR Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
Create | CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
Properties(
  expressions=[
    Property(
      this=Var(this=CHANGE_TRACKING),
      value=Boolean(this=True))])
2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
2768-        # only used for teradata currently
2769-        self._match(TokenType.COMMA)
2770-
2771-        kwargs = {
2772-            "no": self._match_text_seq(
…[1530 chars elided]…
    return self.expression(
2888-            exp.FallbackProperty(no=no, protection=self._match_text_seq("PROTECTION"))
2889-        )
2890-
2891-    def _parse_sql_security(self) -> exp.SqlSecurityProperty:
2892-        return self.expression(
2893-            exp.SqlSecurityProperty(
2894-                this=self._match_texts(self.SECURITY_PROPERTY_KEYWORDS) and self._prev.text.upper()
2895-            )
2896-        )
2897-
2898-    def _parse_settings_property(self) -> exp.SettingsProperty:
[assistant] Reproduced: the trailing form parses, and the leading form fails with `Expecting )` at the column list. The cause is that the pre-schema property pass (`_parse_properties(before=True)`) only recognizes entries in `PROPERTY_PARSERS`, so the generic `KEY=VALUE` form is never consumed. I'll look at the generic property path and any existing Snowflake hooks.
[tool_use Bash] {"command": "sed -n 2800,2868p sqlglot/parser.py; echo ----; grep -n \"_parse_property\\b\\|def _parse_property\\|_parse_property_before\" sqlglot/parsers/*.py | head; echo ----; grep -n \"def _parse_schema\" -A30 sqlglot/parser.py | head -45", "description": "Read generic property parsing and schema parsing"}
[tool_result]             return self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)

        if self._match_text_seq("COMPOUND", "SORTKEY"):
            return self._parse_sortkey(compound=True)

        if self._match_text_seq("PARAMETER", "STYLE", "PANDAS"):
            return self.expression(exp.ParameterStyleProperty(this="PANDAS"))

        index = self._index

        seq_props = self._parse_sequence_properties()
        if seq_props:
            return seq_props

        self._retreat(i
…[3274 chars elided]…
uted_column: bool = True
7237-    ) -> exp.Expr | None:
7238-        # column defs are not really columns, they're identifiers
7239-        if isinstance(this, exp.Column):
7240-            this = this.this
7241-
7242-        if not computed_column:
7243-            self._match(TokenType.ALIAS)
7244-
7245-        kind = self._parse_types(schema=True)
7246-
7247-        if self._match_text_seq("FOR", "ORDINALITY"):
7248-            return self.expression(exp.ColumnDef(this=this, ordinality=True))
[assistant] The generic `KEY=VALUE` path (`_parse_property`) is what handles `CHANGE_TRACKING=TRUE` in the trailing position. The pre-schema pass only calls `_parse_property_before`, which never reaches that generic path. I'll check the Snowflake parser's `_parse_create` override and the test file before making a Snowflake-only change.
[tool_use Bash] {"command": "sed -n 1025,1050p sqlglot/parsers/snowflake.py; echo ----; grep -n \"validate_identity(\\\"CREATE TABLE.*CHANGE\\|CREATE.*=TRUE\\|def test_create\\|def test_ddl\" tests/dialects/test_snowflake.py | head -20; grep -n \"_parse_property_before\\|location\\|PROPERTIES_LOCATION\" sqlglot/generators/snowflake.py | head", "description": "Check Snowflake create override and related tests"}
[tool_result]                 self.raise_error("Expected ON after ROW ACCESS POLICY name")
            expressions = self._parse_wrapped_csv(self._parse_id_var)

        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))

    def _parse_create(self) -> exp.Create | exp.Command:
        expression = super()._parse_create()
        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identi
…[747 chars elided]…
    def test_ddl(self):
5941:    def test_create_view_copy_grants(self):
5963:    def test_create_view_row_access_policy(self):
6069:    def test_create_sequence(self):
659:    PROPERTIES_LOCATION = {
660:        **generator.Generator.PROPERTIES_LOCATION,
1020:    def createable_sql(self, expression: exp.Create, locations: defaultdict) -> str:
1030:            post_schema_properties = locations[exp.Properties.Location.POST_SCHEMA]
1040:        return super().createable_sql(expression, locations)
[assistant] The fix belongs in the Snowflake parser: override `_parse_property_before` to fall back to the generic `_parse_property`, which already requires a trailing `=` and retreats otherwise. That keeps the change scoped to Snowflake, and the generator already emits the canonical trailing form. I'll make the edit and test it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "            expression.this.replace(expression.this.this)\n\n        return expression\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html", "new_string": "            expression.this.replace(expression.this.this)\n\n        return expression\n\n    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        return super()._parse_property_before() or self._parse_property()\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) CHANGE_TRACKING=FALSE', 'CREATE TABLE t (id INT)', 'CREATE TABLE t AS SELECT 1']:\n    print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\n\"", "description": "Apply fix and check round-trips for both forms"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE CHANGE_TRACKING=FALSE
CREATE TABLE t (id INT)
CREATE TABLE t AS SELECT 1
[assistant] Both forms now parse and both produce the canonical trailing form. Next I'll add a regression test next to the existing Snowflake CREATE tests.
[tool_use Bash] {"command": "sed -n 5963,5975p tests/dialects/test_snowflake.py", "description": "View neighboring Snowflake CREATE test"}
[tool_result]     def test_create_view_row_access_policy(self):
        self.validate_identity(
            "CREATE VIEW v WITH ROW ACCESS POLICY mypolicy ON (col1) AS SELECT col1 FROM t1"
        )
        self.validate_identity(
            "CREATE OR REPLACE VIEW v WITH ROW ACCESS POLICY db.schema.mypolicy ON (col1, col2) AS SELECT col1, col2 FROM t1"
        )
        self.validate_identity(
            "CREATE VIEW v (COL1 COMMENT 'description') WITH ROW ACCESS POLICY db.schema.policy ON (COL1) COMMENT='some comment' AS (SELECT a FROM t1 LEFT JOIN t2 ON t1.id = t2.id)"
        )
        self.validate_identity(
            "CREATE VIEW v ROW ACCESS POLICY p ON (c) AS SELECT c FROM t",
            "CREATE VIEW v WITH ROW ACCESS POLICY p ON (c) AS SELECT c FROM t",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_create_view_row_access_policy(self):\n        self.validate_identity(", "new_string": "    def test_create_table_properties_before_schema(self):\n        self.validate_identity(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n\n    def test_create_view_row_access_policy(self):\n        self.validate_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Add regression test and run Snowflake dialect tests"}
[tool_result] E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 42.
E             CREATE TABLE foo (bar DOUBLE [4mAUTOINCREMENT[0m START 0 INCREMENT 1)

sqlglot/parser.py:2007: ParseError
----------------------------- Captured stdout call -----------------------------
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu [ 80%]
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
=========================== short test summary info ============================
FAILED tests/dialects/test_snowflake
…[30 chars elided]…
e_view_row_access_policy
SUBFAILED[Constraint prefix: WITH ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
6 failed, 93 passed, 784 subtests passed in 4.44s
[assistant] The override broke six existing tests. The likely cause is that `_parse_property` calls `_parse_column()` on arbitrary tokens such as `(`, and that can record parse errors that a retreat doesn't undo. I'll narrow the override so it only takes the generic path when the current token is followed by `=`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        return super()._parse_property_before() or self._parse_property()", "new_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        if self._next and self._next.token_type == TokenType.EQ:\n            return self._parse_property()\n\n        return super()._parse_property_before()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-103528-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', 'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    print(sqlglot.transpile(s, read='snowflake', write='snowflake')[0])\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -4", "description": "Verify narrowed fix and rerun Snowflake tests"}
[tool_result] CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
................. [ 17%]
................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.46s
[assistant] The Snowflake suite passes, including the new test. Next I'll run the full project test suite and the linter.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; (ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -4", "description": "Run full test suite and lint changed files"}
[tool_result] ............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                           [100%]
1127 passed, 18271 subtests passed in 59.85s
All checks passed!
2 files already formatted
[assistant] Snowflake `CREATE TABLE` now accepts `KEY=VALUE` properties before the column list. Both forms parse and emit the same canonical SQL, `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`.

**Change**
- `sqlglot/parsers/snowflake.py`: I added a `_parse_property_before` override. When the current token is followed by `=`, it uses the generic property parser. Otherwise it defers to the base parser. The base pre-schema pass only recognized entries in `PROPERTY_PARSERS`, so generic `KEY=VALUE` properties were never consumed there.
- `tests/dialects/test_snowflake.py`: added `test_create_table_properties_
…[129 chars elided]…
 passed, 18271 subtests passed.
- `ruff check` and `ruff format --check` pass on both changed files.

**Design note**
My first attempt was a plain fallback to `_parse_property()` whenever the base returned nothing. It broke six existing tests, including `CREATE TABLE foo (bar DOUBLE AUTOINCREMENT ...)`. The generic parser calls `_parse_column()` on arbitrary tokens such as `(`, and that can leave parse errors behind even after a retreat. The `=` lookahead avoids that path entirely.

The change is in the Snowflake parser only; base and other dialects are untouched. I haven't committed anything.
