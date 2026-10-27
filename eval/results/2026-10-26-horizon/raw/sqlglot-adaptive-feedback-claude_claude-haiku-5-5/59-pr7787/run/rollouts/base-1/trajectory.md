# trajectory base-1

final message:
Snowflake now accepts `KEY=VALUE` properties before the column list, and both forms produce the same AST. Full suite: `SUMMARY: 1126 passed, 18271 subtests passed in 50.98s` / `EXIT: 0`.

**Cause:** the name-then-properties slot in `_parse_create` calls `_parse_property_before`, which is Teradata-only and only accepts keywords from `PROPERTY_PARSERS`. The generic `KEY=VALUE` parsing sits in `_parse_property`, which only runs after the schema.

**Fix** (`sqlglot/parsers/snowflake.py`): Snowflake overrides `_parse_property_before`. It tries the base behaviour first, and on a miss it retreats and falls back to `_parse_property()`. It skips the fallback when the next token is `(`. My first version didn't skip it, and that broke `id INT WITH MASKING POLICY` column constraints; the guard fixed that. The change is scoped to Snowflake, so other dialects are untouched.

**Tests** (`tests/dialects/test_snowflake.py`, `test_ddl`): added `CHANGE_TRACKING=TRUE (id INT)` and an `OR REPLACE` form with two properties, both expected to print with the properties after the columns. I also checked by hand that `CREATE TABLE t A=1 B=2 (id INT)` and the `COMMENT=` / `CLUSTER BY` variants still parse to the same AST as their after-schema forms.

**Things to know:**
- The `ast_check.py` output for the first form shows `[DIFFERS]` and `FUNCTION CHANGED: TRUE missing`. Both are checker artifacts: its regex reads `TRUE (` as a function call, and the `[DIFFERS]` comes from the intended reordering. The real AST comparison is equal.
- Transpiling to DuckDB still emits "Unsupported property" warnings and drops the property. That is the existing behaviour for the after-schema form too, so I left it alone.
- Ruff check and format pass on both files.

## events
[assistant] I'll start with the DDL skill that matches this task, then find where Snowflake parses CREATE properties.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-ddl-statements/SKILL.md; echo ----; grep -n \"CHANGE_TRACKING\\|_parse_create\\|PROPERTY_PARSERS\\|POST_SCHEMA\\|def _parse_property\" sqlglot/parsers/snowflake.py sqlglot/parser.py | head -60", "description": "Read DDL skill and locate CREATE parsing code"}
[tool_result] ---
name: sqlglot-ddl-statements
description: Load when a task adds or changes parsing/generation of a DDL statement in sqlglot (CREATE / ALTER / DROP of a TABLE, VIEW, TYPE, SEQUENCE, FUNCTION, MACRO, INDEX, TRIGGER, …, including statements with several repeated clauses such as overloaded DuckDB macros), or when a statement "contains unsupported syntax. Falling back to parsing as a Command" and must become a real AST node (exp.Create, exp.Alter, …) in any dialect.
---

# DDL statements (exp.Cre
…[8583 chars elided]…
) -> E:
sqlglot/parser.py:3350:    def _parse_create_like(self) -> exp.LikeProperty | None:
sqlglot/parser.py:7087:            if self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7088:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7089:            elif self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7090:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
[tool_use Bash] {"command": "sed -n 1025,1060p sqlglot/parsers/snowflake.py; echo ----; sed -n 2360,2480p sqlglot/parser.py", "description": "Read Snowflake _parse_create and base _parse_create"}
[tool_result]                 self.raise_error("Expected ON after ROW ACCESS POLICY name")
            expressions = self._parse_wrapped_csv(self._parse_id_var)

        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))

    def _parse_create(self) -> exp.Create | exp.Command:
        expression = super()._parse_create()
        if isinstance(expression, exp.Create) and expression.kind in self.NON_TABLE_CREATABLES:
            # Replace the Table node with the enclosed Identi
…[5670 chars elided]…

                expression = self._parse_macro_overloads(
                    t.cast(exp.UserDefinedFunction, this), expression, is_table
                )
        elif create_token_type == TokenType.INDEX:
            # Postgres allows anonymous indexes, eg. CREATE INDEX IF NOT EXISTS ON t(c)
            if not self._match(TokenType.ON):
                index = self._parse_id_var()
                anonymous = False
            else:
                index = None
                anonymous = True
[tool_use Bash] {"command": "sed -n 2480,2600p sqlglot/parser.py", "description": "Read rest of base _parse_create table branch"}
[tool_result]                 anonymous = True

            this = self._parse_index(index=index, anonymous=anonymous)
        elif (
            create_token_type == TokenType.CONSTRAINT and self._match(TokenType.TRIGGER)
        ) or create_token_type == TokenType.TRIGGER:
            if is_constraint := (create_token_type == TokenType.CONSTRAINT):
                create_token = self._prev

            trigger_name = self._parse_id_var()
            if not trigger_name:
                return self._parse_as
…[4136 chars elided]…
g a table as an alias instead of a SELECT.
                # Here we fallback to this as an alternative.
                if not expression and has_alias:
                    expression = self._try_parse(self._parse_table_parts)

            if create_token_type == TokenType.TABLE:
                # exp.Properties.Location.POST_EXPRESSION
                extend_props(self._parse_properties())

                indexes = []
                while True:
                    index = self._parse_index()
[assistant] The base parser already calls `_parse_properties(before=True)` after the name. I'll probe the failing form to see where it breaks.
[tool_use Bash] {"command": "cat > /tmp/probe_sf.py <<'EOF'\nimport sqlglot\nfor sql in [\n \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n \"CREATE TABLE t COMMENT='x' (id INT)\",\n \"CREATE TABLE t CLUSTER BY (id) (id INT)\",\n \"CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 (id INT)\",\n]:\n    try:\n        e = sqlglot.parse_one(sql, read=\"snowflake\")\n
…[153 chars elided]…
ons if e.args.get(\"properties\") else [])])\n    except Exception as ex:\n        print(\"ERR\", sql, \"->\", str(ex)[:200])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_sf.py 2>&1 | head -40", "description": "Probe Snowflake CREATE property placement variants"}
[tool_result] ERR CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) -> Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
Create | CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
  props: ['Property']
Create | CREATE TABLE t (id INT) COMMENT='x'
  props: ['SchemaCommentProperty']
Create | CREATE TABLE t (id INT) CLUSTER BY (id)
  props: ['ClusterProperty']
ERR CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 (id INT) -> Expecting ). Line 1, Col: 48.
  CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 ([4mid[0m INT)
[assistant] The name-then-property path fails for generic `KEY=VALUE`. Next I'll check `_parse_property_before` versus `_parse_property`, since the generic fallback is probably only in the latter.
[tool_use Bash] {"command": "sed -n 2740,2830p sqlglot/parser.py", "description": "Read property parsing helpers"}
[tool_result]                 if new_alias is not None:
                    self.raise_error("Duplicate NEW clause in REFERENCING")
                new_alias = alias
            else:
                break

        if old_alias is None and new_alias is None:
            self.raise_error("REFERENCING clause requires at least OLD TABLE or NEW TABLE")

        return self.expression(exp.TriggerReferencing(old=old_alias, new=new_alias))

    def _parse_trigger_for_each(self) -> str | None:
        if not self._ma
…[2633 chars elided]…

            return None

        # Transform the key to exp.Dot if it's dotted identifiers wrapped in exp.Column or to exp.Var otherwise
        if isinstance(key, exp.Column):
            key = key.to_dot() if len(key.parts) > 1 else exp.var(key.name)

        value = self._parse_bitwise() or self._parse_var(any_token=True)

        # Transform the value to exp.Var if it was parsed as exp.Column(exp.Identifier())
        if isinstance(value, exp.Column):
            value = exp.var(value.name)
[tool_use Bash] {"command": "sed -n 2830,2862p sqlglot/parser.py; echo ----; grep -n \"def _parse_properties\" -A 22 sqlglot/parser.py; echo ----; grep -rn \"_parse_property_before\\|before=True\" sqlglot/ | head", "description": "Read _parse_properties and before-mode usages"}
[tool_result]         return self.expression(exp.Property(this=key, value=value))

    def _parse_stored(self) -> exp.FileFormatProperty | exp.StorageHandlerProperty:
        if self._match_text_seq("BY"):
            return self.expression(exp.StorageHandlerProperty(this=self._parse_var_or_string()))

        self._match(TokenType.ALIAS)
        input_format = self._parse_string() if self._match_text_seq("INPUTFORMAT") else None
        output_format = self._parse_string() if self._match_text_seq("OUTPUTFORM
…[1433 chars elided]…
xp.FallbackProperty:
2887-        return self.expression(
2888-            exp.FallbackProperty(no=no, protection=self._match_text_seq("PROTECTION"))
2889-        )
2890-
2891-    def _parse_sql_security(self) -> exp.SqlSecurityProperty:
----
sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
[assistant] The cause is clear. The name-then-properties slot calls `_parse_property_before`, which only accepts keywords from `PROPERTY_PARSERS` (a Teradata-only path). The generic `KEY=VALUE` handling lives in `_parse_property`, which only runs after the schema. I'll check the existing Snowflake test layout and then override the before-name hook in the Snowflake parser, falling back to the generic property parser and retreating on failure.
[tool_use Bash] {"command": "grep -n \"def test_ddl\" -A 6 tests/dialects/test_snowflake.py | head -20; grep -n \"CHANGE_TRACKING\\|DATA_RETENTION\" tests/dialects/test_snowflake.py | head; sed -n 1026,1030p sqlglot/parsers/snowflake.py", "description": "Inspect Snowflake test layout and existing usages"}
[tool_result] 4240:    def test_ddl(self):
4241-        for constraint_prefix in ("WITH ", ""):
4242-            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4243-                self.validate_identity(
4244-                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
4245-                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
4246-                )
5755:        self.validate_identity("ALTER TABLE tbl SET DATA_RETENTION_TIME_IN_DAYS=1")
5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
            expressions = self._parse_wrapped_csv(self._parse_id_var)

        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))

    def _parse_create(self) -> exp.Create | exp.Command:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()", "new_string": "    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        index = self._index\n        prop = super()._parse_property_before()\n        if prop:\n            return prop\n\n        # Snowflake accepts generic KEY=VALUE properties between the table name and the schema\n        self._retreat(index)\n        return self._parse_property()\n\n    def _parse_create(self) -> exp.Create | exp.Command:\n        expression = super()._parse_create()"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now I'll run the probe and compare the ASTs of the two forms.
[tool_use Bash] {"command": "cat > /tmp/probe_sf2.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\npairs = [\n (\"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\", \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\"),\n (\"CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 (id INT)\", \"CREATE TABLE t (id INT) DATA_RETENTION_TIME_IN_DAYS=1\"),\n (\"CREATE TABLE t A=1 B=2 (id INT)\", \"CREATE TABLE t (id INT) A=1 B=2\"),
…[694 chars elided]…
\"| transpile duckdb:\", e.sql(\"duckdb\"))\n    except Exception as ex:\n        print(\"ERR\", before, \"->\", str(ex)[:150])\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_sf2.py 2>&1 | head -40", "description": "Re-run probe comparing before/after-schema ASTs"}
[tool_result] Unsupported property property
Unsupported property property
Unsupported property property
Unsupported property property
Unsupported property property
Unsupported property schemacommentproperty
Unsupported property clusterproperty
OK  CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) -> CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 (id INT) -> CREATE TABLE t (id INT) DATA_RETENTION_TIME_IN_DAY
…[325 chars elided]…
ACKING=TRUE
   same AST: True | transpile duckdb: CREATE OR REPLACE TABLE t (id INT, x TEXT)
OK  CREATE TABLE t COMMENT='x' (id INT) -> CREATE TABLE t (id INT) COMMENT='x'
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t CLUSTER BY (id) (id INT) -> CREATE TABLE t (id INT) CLUSTER BY (id)
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t CLONE src -> CREATE TABLE t CLONE src
OK  CREATE TABLE t AS SELECT 1 -> CREATE TABLE t AS SELECT 1
[assistant] Both forms now produce identical ASTs, and the DuckDB "Unsupported property" warnings are the same ones the second form already gave, so they're pre-existing behaviour. Next I'll add regression tests next to the existing Snowflake DDL tests, then run the harness's AST check.
[tool_use Bash] {"command": "sed -n 4240,4262p tests/dialects/test_snowflake.py; echo ----; ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/; .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --help 2>&1 | head -5", "description": "View test_ddl section and ast_check script"}
[tool_result]     def test_ddl(self):
        for constraint_prefix in ("WITH ", ""):
            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
                self.validate_identity(
                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
                )
                self.validate_identity(
                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p USING (c1, c2, c3))
…[436 chars elided]…
1='value_1', key2='value_2'))",
                    "CREATE TABLE t (id INT TAG (key1='value_1', key2='value_2'))",
                )

        self.validate_identity("CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)")
        self.validate_identity("USE SECONDARY ROLES ALL")
        self.validate_identity("USE SECONDARY ROLES NONE")
----
ast_check.py
into_dialect.py
value_check.py
(eval):1: permission denied: .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")", "new_string": "        self.validate_id
…[162 chars elided]…
(id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\n            \"CREATE OR REPLACE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE OR REPLACE TABLE t (id INT) DATA_RETENTION_TIME_IN_DAYS=1 CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Next I'll run the Snowflake test file and the AST check (invoked through Python, since the script isn't executable).
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -5; echo ----; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read snowflake --repr \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\" 2>&1 | tail -15", "description": "Run Snowflake tests and AST check on the example"}
[tool_result] SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
6 failed, 92 passed, 784 subtests passed in 3.02s
----
        ColumnDef(
          this=Identifier(this=id, quoted=False),
          kind=DataType(this=DType.INT, nested=False))]),
    kind=TABLE,
    replace=False,
    refresh=False,
    unique=False,
    exists=False,
    properties=Properties(
      expressions=[
        Property(
          this=Var(this=CHANGE_TRACKING),
          value=Boolean(this=True))]),
    concurrently=False)
  snowflake (round-trip)  [DIFFERS]  [FUNCTION CHANGED: TRUE missing]: CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
[assistant] Six Snowflake tests failed, so I'll look at those errors before anything else.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | grep -E \"Error|error|Expecting|Unsupported|^E \" | head -30", "description": "Show error messages from failing Snowflake tests"}
[tool_result]     self.raise_error("Expecting )")
message = 'Expecting )'
    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
            context_length=self.error_message_context,
        error = ParseError.new(
        if self.error_level == ErrorLevel.IMMEDIATE:
>           raise error
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 41.
E             CREATE VIEW v (COL1 COMMENT [4m'description'[0m) WITH ROW ACCESS POLICY db.schema.policy ON (COL1) COMMENT='some
…[523 chars elided]…
parser.py:2007: ParseError
    self.raise_error("Expecting )")
message = 'Expecting )'
    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
            context_length=self.error_message_context,
        error = ParseError.new(
        if self.error_level == ErrorLevel.IMMEDIATE:
>           raise error
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 30.
E             CREATE TABLE t (id INT [4mMASKING[0m POLICY p.q.r)
sqlglot/parser.py:2007: ParseError
[assistant] The failures are in column-level `WITH MASKING POLICY` parsing, which my change shouldn't touch. I'll check the traceback to see what calls my override.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nsqlglot.parse_one('CREATE TABLE t (id INT WITH MASKING POLICY p.q.r)', read='snowflake')\n\" 2>&1 | grep -E \"File|line\" | tail -25", "description": "Get traceback for masking policy parse failure"}
[tool_result]   File "<string>", line 3, in <module>
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/__init__.py", line 160, in parse_one
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/dialects/dialect.py", line 1129, in parse
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.
…[2210 chars elided]…
primary
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", line 6849, in _parse_paren
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", line 9424, in _match_r_paren
  File "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", line 2007, in raise_error
[assistant] The generic `_parse_property` path calls `_parse_column` on the opening `(` of the column list, which parses it as a parenthesised expression and raises. I'll stop the fallback when the next token is `(`, so the schema is still handled by the normal path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        # Snowflake accepts generic KEY=VALUE properties between the table name and the schema\n        self._retreat(index)\n        return self._parse_property()", "new_string": "        # Snowflake accepts generic KEY=VALUE properties between the table name and the schema\n        self._retreat(index)\n        if not self._match(TokenType.L_PAREN, advance=False):\n            return self._parse_property()\n        return None"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-120022-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -3; PYTHONPATH=. $PY /tmp/probe_sf2.py 2>/dev/null", "description": "Re-run Snowflake tests and probe script"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.46s
OK  CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) -> CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t DATA_RETENTION_TIME_IN_DAYS=1 (id INT) -> CREATE TABLE t (id INT) DATA_RETENTION_TIME_IN_DAYS=1
   same A
…[312 chars elided]…
ACKING=TRUE
   same AST: True | transpile duckdb: CREATE OR REPLACE TABLE t (id INT, x TEXT)
OK  CREATE TABLE t COMMENT='x' (id INT) -> CREATE TABLE t (id INT) COMMENT='x'
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t CLUSTER BY (id) (id INT) -> CREATE TABLE t (id INT) CLUSTER BY (id)
   same AST: True | transpile duckdb: CREATE TABLE t (id INT)
OK  CREATE TABLE t CLONE src -> CREATE TABLE t CLONE src
OK  CREATE TABLE t AS SELECT 1 -> CREATE TABLE t AS SELECT 1
[assistant] The Snowflake file passes (96 tests). Next, the `ast_check` flagged `TRUE missing`, so I need to know whether that is real or a checker artifact. I'll run it on the already-working second form as a control.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\" \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\"; do $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read snowflake --repr \"$s\" 2>&1 | grep -E \"round-trip|DIFFER|WORDS|FUNCTION\" ; echo ---; done", "description": "Compare ast_check results for both forms"}
[tool_result]   snowflake (round-trip)  [DIFFERS]  [FUNCTION CHANGED: TRUE missing]: CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
---
  snowflake (round-trip): CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
---
[assistant] The control passes and the fixed form doesn't, even though my earlier check showed the two ASTs are equal. I'll read how `ast_check` computes the "FUNCTION CHANGED" comparison before deciding whether it's a real difference.
[tool_use Bash] {"command": "grep -n \"FUNCTION CHANGED\\|def \\|WORDS DROPPED\" .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py | head -40", "description": "Locate comparison logic in ast_check script"}
[tool_result] 14:  [FUNCTION CHANGED] a function called in the input (e.g. DATE_SUB) is missing from
17:  [WORDS DROPPED]    a keyword/identifier in the input (outside string literals) is
23:4 = parsed, but at least one statement has FUNCTION CHANGED or WORDS DROPPED.
37:def _norm(sql: str) -> str:
41:def _calls(sql: str) -> Counter:
45:def _words(sql: str) -> Counter:
51:def main() -> int:
91:            flag += f"  [FUNCTION CHANGED: {', '.join(lost)} missing]"
95:            flag += f"  [WORDS DROPPED: {', '.join(dropped)}]"
[tool_use Bash] {"command": "sed -n 37,50p .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py; sed -n 70,96p .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py", "description": "Read ast_check helper and comparison body"}
[tool_result] def _norm(sql: str) -> str:
    return " ".join(sql.upper().split()).rstrip(";").rstrip()


def _calls(sql: str) -> Counter:
    return Counter(m.group(1).upper() for m in _CALL.finditer(sql))


def _words(sql: str) -> Counter:
    return Counter(
        w.upper() for w in _WORD.findall(_STRING.sub(" ", sql)) if w.upper() not in _ELIDED
    )


        print(f"== {sql}")
        try:
            tree = sqlglot.parse_one(sql, read=args.read)
        except Exception as e:  # noqa: BLE001
       
…[660 chars elided]…
 repr(inner).replace("\n", "\n  "))
        rt = tree.sql(args.read)
        lost = sorted((_calls(sql) - _calls(rt)).keys())
        flag = "" if _norm(rt) == _norm(sql) else "  [DIFFERS]"
        if lost:
            flag += f"  [FUNCTION CHANGED: {', '.join(lost)} missing]"
            status = status or 4
        dropped = sorted((_words(sql) - _words(rt) - _calls(sql)).keys())
        if dropped:
            flag += f"  [WORDS DROPPED: {', '.join(dropped)}]"
            status = status or 4
[assistant] The `[DIFFERS]`/`FUNCTION CHANGED` flags come from the checker, not the parser. Its `_CALL` regex reads `TRUE (id INT)` in the input as a function call named `TRUE`, and the `[DIFFERS]` is only because the output moves the property after the column list, which is the intended change. The real check, the AST equality, already passed. Now the full suite, run in the foreground as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -25", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-16:30:42 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-aa9146a0a2.log
ELAPSED: 52s
SUMMARY: 1126 passed, 18271 subtests passed in 50.98s
EXIT: 0
[assistant] The full suite passes. I'll finish with the linters the project uses on the two edited files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py 2>&1 | tail -3; git diff --stat", "description": "Lint and format-check edited files, show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parsers/snowflake.py     | 12 ++++++++++++
 tests/dialects/test_snowflake.py |  8 ++++++++
 2 files changed, 20 insertions(+)
[assistant] Snowflake now accepts `KEY=VALUE` properties before the column list, and both forms produce the same AST. Full suite: `SUMMARY: 1126 passed, 18271 subtests passed in 50.98s` / `EXIT: 0`.

**Cause:** the name-then-properties slot in `_parse_create` calls `_parse_property_before`, which is Teradata-only and only accepts keywords from `PROPERTY_PARSERS`. The generic `KEY=VALUE` parsing sits in `_parse_property`, which only runs after the schema.

**Fix** (`sqlglot/parsers/snowflake.py`): Snowflake overrides `_parse_property_before`. It tries the base behaviour first, and on a miss it retreats and
…[546 chars elided]…
the `COMMENT=` / `CLUSTER BY` variants still parse to the same AST as their after-schema forms.

**Things to know:**
- The `ast_check.py` output for the first form shows `[DIFFERS]` and `FUNCTION CHANGED: TRUE missing`. Both are checker artifacts: its regex reads `TRUE (` as a function call, and the `[DIFFERS]` comes from the intended reordering. The real AST comparison is equal.
- Transpiling to DuckDB still emits "Unsupported property" warnings and drops the property. That is the existing behaviour for the after-schema form too, so I left it alone.
- Ruff check and format pass on both files.
