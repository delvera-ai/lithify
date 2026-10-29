# trajectory base-1

final message:
Snowflake now accepts `KEY = VALUE` properties before the column list. Both forms produce `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1127 tests) and ruff is clean.

**Cause:** the base parser only looks for pre-schema properties among the known `PROPERTY_PARSERS` keywords. `CHANGE_TRACKING` isn't one of them, so it was skipped. The parser then read `(id INT)` as a subquery and failed.

**Change:**
- `sqlglot/parsers/snowflake.py`: `SnowflakeParser._parse_property_before` now delegates to the generic `_parse_property`, so `KEY=VALUE` is accepted between the name and the schema. It returns `None` when the next token is `(`. Without that guard, the generic parser consumed the column list and broke existing tests for `COMMENT`, `PRIMARY KEY`, and row access policy cases.
- `tests/dialects/test_snowflake.py`: added `test_create_table_properties_before_schema`, covering the existing after-schema form and the new before-schema form.

Only Snowflake is affected; the base parser and other dialects are unchanged.

## events
[tool_use Bash] {"command": "grep -n \"CHANGE_TRACKING\\|_parse_create\\b\\|def _parse_create\\|PROPERTY_PARSERS\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -50; grep -n \"CHANGE_TRACKING\" -r tests/dialects/test_snowflake.py | head", "description": "Locate create/property parsing code"}
[tool_result] sqlglot/parser.py:1089:        TokenType.CREATE: lambda self: self._parse_create(),
sqlglot/parser.py:1227:    PROPERTY_PARSERS: t.ClassVar[dict[str, t.Callable]] = {
sqlglot/parser.py:2360:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/parser.py:2783:        if self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:2784:            parser = self.PROPERTY_PARSERS[self._prev.text.upper()]
sqlglot/parser.py:2796:        if self._match_texts(self.PROPERTY_PARSERS):
sqlglot/pa
…[550 chars elided]…
xt.upper()](self)
sqlglot/parser.py:7089:            elif self._match(TokenType.DEFAULT) and self._match_texts(self.PROPERTY_PARSERS):
sqlglot/parser.py:7090:                prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
tests/dialects/test_snowflake.py:5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
tests/dialects/test_snowflake.py:5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
[tool_use Bash] {"command": "sed -n 2360,2480p sqlglot/parser.py; sed -n 2770,2810p sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake').sql('snowflake')))\n    except Exception as e: print('ERR', e)\n\"", "description": "Read create parser and reproduce both forms"}
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
…[5783 chars elided]…
er()](self, default=True)

        if self._match_text_seq("COMPOUND", "SORTKEY"):
            return self._parse_sortkey(compound=True)

        if self._match_text_seq("PARAMETER", "STYLE", "PANDAS"):
            return self.expression(exp.ParameterStyleProperty(this="PANDAS"))

        index = self._index

        seq_props = self._parse_sequence_properties()
ERR Expecting ). Line 1, Col: 39.
  CREATE TABLE t CHANGE_TRACKING=TRUE ([4mid[0m INT)
'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE'
[tool_use Bash] {"command": "sed -n 2480,2600p sqlglot/parser.py; grep -n \"def _parse_schema\\|def _parse_properties\\|def _parse_with_property\\|def _parse_wrapped_properties\" sqlglot/parser.py; grep -n \"CHANGE_TRACKING\\|class Generator\\|def create_sql\\|PROPERTIES_LOCATION\" sqlglot/dialects/snowflake.py | head", "description": "Read rest of _parse_create and schema helpers"}
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
…[4468 chars elided]…
RESSION
                extend_props(self._parse_properties())

                indexes = []
                while True:
                    index = self._parse_index()
2792:    def _parse_wrapped_properties(self) -> list[exp.Expr | list[exp.Expr]]:
2869:    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2992:    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 2869,2900p sqlglot/parser.py; grep -n \"before\" sqlglot/parser.py | sed -n 1,80p | grep -i \"prop\\|before=\" ; grep -n \"CHANGE_TRACKING\\|DATA_RETENTION\\|\\\"TAG\\\"\\|def _parse_create\\|Properties.Location\" sqlglot/dialects/snowflake.py | head -30", "description": "Inspect _parse_properties and before handling"}
[tool_result]     def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
        properties = []
        while True:
            if before:
                prop = self._parse_property_before()
            else:
                prop = self._parse_property()
            if not prop:
                break
            for p in ensure_list(prop):
                properties.append(p)

        if properties:
            return self.expression(exp.Properties(expressions=properties))

      
…[550 chars elided]…
rn self.expression(
            exp.SettingsProperty(expressions=self._parse_csv(self._parse_assignment))
2554:            extend_props(self._parse_properties(before=True))
2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
2869:    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2873:                prop = self._parse_property_before()
4993:                at_before=self._parse_historical_data(),
169:            "TAG": TokenType.TAG,
[tool_use Bash] {"command": "sed -n 2600,2640p sqlglot/parser.py; sed -n 2767,2770p sqlglot/parser.py; grep -n \"_parse_property_before\\|def _parse_property_assignment\\|def _parse_wrapped_properties\" sqlglot/dialects/*.py | head; grep -n \"CHANGE_TRACKING\\|def _parse_property_assignment\" -r sqlglot/ | head; ls tests/dialects | head -3; grep -n \"CREATE TABLE.*=TRUE\\|CREATE TABLE.*= *TRUE\" tests/dialects/test_snowflake.py | head", "description": "Read rest of table create and find Snowflake property tests"}
[tool_result]                     index = self._parse_index()

                    # exp.Properties.Location.POST_INDEX
                    extend_props(self._parse_properties())
                    if not index:
                        break
                    else:
                        self._match(TokenType.COMMA)
                        indexes.append(index)
            elif create_token_type == TokenType.VIEW:
                if self._match_text_seq("WITH", "NO", "SCHEMA", "BINDING"):
                
…[1022 chars elided]…
sts=exists,
                properties=properties,
                indexes=indexes,
                no_schema_binding=no_schema_binding,
                begin=begin,
                clone=clone,
    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
        # only used for teradata currently
        self._match(TokenType.COMMA)

sqlglot/parser.py:2863:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
__init__.py
test_athena.py
test_bigquery.py
[tool_use Bash] {"command": "sed -n 2767,2770p sqlglot/parser.py; grep -n \"_parse_property_before\" -A25 sqlglot/dialects/teradata.py | head -60; grep -n \"class Parser\\|PROPERTY_PARSERS\\|def _parse_\" sqlglot/dialects/snowflake.py | head -60", "description": "Look at Teradata before-property parser and Snowflake parser"}
[tool_result]     def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
        # only used for teradata currently
        self._match(TokenType.COMMA)
[tool_use Bash] {"command": "sed -n 2767,2790p sqlglot/parser.py; grep -rn \"before=True\\|_parse_property_before\" sqlglot/ | head; grep -n \"class Parser\\|class Generator\\|    def _parse_\\|PROPERTY\" sqlglot/dialects/snowflake.py | head -60", "description": "Read property-before parser and Snowflake parser hooks"}
[tool_result]     def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
        # only used for teradata currently
        self._match(TokenType.COMMA)

        kwargs = {
            "no": self._match_text_seq("NO"),
            "dual": self._match_text_seq("DUAL"),
            "before": self._match_text_seq("BEFORE"),
            "default": self._match_text_seq("DEFAULT"),
            "local": (self._match_text_seq("LOCAL") and "LOCAL")
            or (self._match_text_seq("NOT", "LOCAL") an
…[306 chars elided]…
rev.text.upper()]
            try:
                return parser(self, **{k: v for k, v in kwargs.items() if v})
            except TypeError:
                self.raise_error(f"Cannot parse property '{self._prev.text}'")

        return None
sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
[tool_use Bash] {"command": "sed -n 7218,7240p sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot.dialects.snowflake import Snowflake\np = Snowflake().parser()\nprint(p.__class__)\n\" ; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one('CREATE TABLE t CHANGE_TRACKING=TRUE', read='snowflake')))\nprint(repr(sqlglot.parse_one('CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', read='snowflake')))\n\" 2>&1 | tail -5", "description": "Read _parse_schema and probe parse behavior"}
[tool_result]     def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
        index = self._index
        if not self._match(TokenType.L_PAREN):
            return this

        # Disambiguate between schema and subquery/CTE, e.g. in INSERT INTO table (<expr>),
        # expr can be of both types
        if self._match_set(self.SELECT_START_TOKENS):
            self._retreat(index)
            return this
        args = self._parse_csv(lambda: self._parse_constraint() or self._parse_fiel
…[176 chars elided]…
n self._parse_column_def(self._parse_field(any_token=True))

    def _parse_column_def(
        self, this: exp.Expr | None, computed_column: bool = True
    ) -> exp.Expr | None:
        # column defs are not really columns, they're identifiers
        if isinstance(this, exp.Column):
            this = this.this
<class 'sqlglot.parsers.snowflake.SnowflakeParser'>
    expressions=[
      Property(
        this=Var(this=CHANGE_TRACKING),
        value=Boolean(this=True))]),
  concurrently=False)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=1 (id INT)','CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t CHANGE_TRACKING=TRUE, (id INT)', 'CREATE TABLE t COMMENT=\\'x\\' (id INT)', 'CREATE TABLE t CLUSTER BY (id) (id INT)']:\n    try: print(repr(sqlglot.parse_one(s, read='snowflake').sql('snowflake')))\n    except Exception as e: print('ERR', s, str(e).splitlines()[0])\n\" 2>&1; grep -n \"def _parse_property_assignment\" -A12 sqlglot/parser.py; grep -n \"def _parse_property(\" -A60 sqlglot/parser.py | sed -n 20,60p", "description": "Probe value-parsing edge cases for schema-less property"}
[tool_result] ERR CREATE TABLE t CHANGE_TRACKING=1 (id INT) Expecting ). Line 1, Col: 36.
ERR CREATE TABLE t CHANGE_TRACKING=TRUE (id INT) Expecting ). Line 1, Col: 39.
ERR CREATE TABLE t CHANGE_TRACKING=TRUE, (id INT) Expecting ). Line 1, Col: 40.
"CREATE TABLE t (id INT) COMMENT='x'"
'CREATE TABLE t (id INT) CLUSTER BY (id)'
2863:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
2864-        self._match(TokenType.EQ)
2865-        self._match(TokenType.ALIAS)
2866-
2867-    
…[1792 chars elided]…
2844-                    self.expression(
2845-                        exp.InputOutputFormat(
2846-                            input_format=input_format, output_format=output_format
2847-                        )
2848-                    )
2849-                    if input_format or output_format
2850-                    else self._parse_var_or_string() or self._parse_number() or self._parse_id_var()
2851-                ),
2852-                hive_format=True,
2853-            )
2854-        )
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot, traceback\ntry: sqlglot.parse_one('CREATE TABLE t CHANGE_TRACKING=1 (id INT)', read='snowflake')\nexcept Exception: traceback.print_exc()\n\" 2>&1 | grep -v \"^    \" | tail -30", "description": "Get traceback for failing parse"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/__init__.py", line 160, in parse_one
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/dialects/dialect.py", line 1129, in parse
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in
…[1504 chars elided]…
t/base-1/sqlglot/parser.py", line 3977, in _parse_select_query
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", line 9424, in _match_r_paren
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", line 2007, in raise_error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 36.
  CREATE TABLE t CHANGE_TRACKING=1 ([4mid[0m INT)
[tool_use Bash] {"command": "sed -n 1015,1050p sqlglot/parsers/snowflake.py; grep -n \"_parse_schema\\|_parse_property\" sqlglot/parsers/*.py | head -30", "description": "Read Snowflake _parse_create override"}
[tool_result]         if self._match(TokenType.HASH):
            policy: exp.Expr | None = self._parse_var(any_token=True)
            if policy:
                policy = exp.Var(this=f"#{policy.name}")
            expressions = None
        else:
            policy = self._parse_column()
            if isinstance(policy, exp.Column):
                policy = policy.to_dot()
            if not self._match(TokenType.ON):
                self.raise_error("Expected ON after ROW ACCESS POLICY name")
            
…[1660 chars elided]…
ignment(exp.LockProperty),
sqlglot/parsers/mysql.py:257:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parsers/spark2.py:96:            self.expression(exp.Drop(this=self._parse_schema(), kind="COLUMNS"))
sqlglot/parsers/snowflake.py:977:        return self.expression(exp.Tags(expressions=self._parse_wrapped_csv(self._parse_property)))
sqlglot/parsers/tsql.py:751:            this = self._parse_schema(self._parse_id_var(any_token=False))
[tool_use Bash] {"command": "grep -n \"^class \\|    def _parse_\" sqlglot/parsers/snowflake.py | head -40; grep -n \"_parse_property_before\" -B2 -A3 sqlglot/parsers/*.py | head; sed -n 5750,5775p tests/dialects/test_snowflake.py", "description": "Survey Snowflake parser structure and related tests"}
[tool_result] 329:class SnowflakeParser(parser.Parser):
921:    def _parse_directory(self) -> exp.DirectoryStage:
926:    def _parse_describe(self) -> exp.Describe:
952:    def _parse_use(self) -> exp.Use:
976:    def _parse_tag(self) -> exp.Tags:
979:    def _parse_with_constraint(self) -> exp.Expr | None:
1004:    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
1013:    def _parse_row_access_policy(self) -> exp.RowAccessProperty:
1030:    def _parse_create(self) -> exp.Create | exp.Comma
…[2310 chars elided]…
TER TABLE tbl SET STAGE_COPY_OPTIONS = (ON_ERROR=SKIP_FILE SIZE_LIMIT=5 PURGE=TRUE MATCH_BY_COLUMN_NAME=CASE_SENSITIVE)"""
        )

        self.validate_identity("ALTER TABLE foo UNSET TAG a, b, c")
        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")

    def test_alter_session(self):
        expr = self.validate_identity(
            "ALTER SESSION SET autocommit = FALSE, QUERY_TAG = 'qtag', JSON_INDENT = 1"
        )
        self.assertEqual(
[assistant] I've traced the failure: for `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)`, the base parser only tries properties that come before the schema via `PROPERTY_PARSERS`, so `CHANGE_TRACKING=TRUE` is skipped, the schema is never matched, and `(id INT)` is parsed as a subquery. I'll make Snowflake's pre-schema property hook accept generic `KEY = VALUE` properties.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return expression\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html", "new_string": "        return expression\n\n    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake allows KEY=VALUE properties between the table name and its column definitions\n        return self._parse_property()\n\n    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now a test next to the existing Snowflake create tests, then a check of both forms.
[tool_use Bash] {"command": "grep -n \"def test_create\\|def test_ddl\" tests/dialects/test_snowflake.py | head; grep -n \"CHANGE_TRACKING\\|DATA_RETENTION_TIME_IN_DAYS=\" tests/dialects/test_snowflake.py | head -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)','CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE','CREATE TABLE t COMMENT=\\'x\\' (id INT)','CREATE TABLE t AS SELECT 1','CREATE TABLE t (id INT) CLUSTER BY (id)']:\n    print(repr(sqlglot.parse_one(s, read='snowflake').sql('snowflake')))\n\"", "description": "Find create tests and verify both forms parse"}
[tool_result] 4240:    def test_ddl(self):
5941:    def test_create_view_copy_grants(self):
5963:    def test_create_view_row_access_policy(self):
6069:    def test_create_sequence(self):
5755:        self.validate_identity("ALTER TABLE tbl SET DATA_RETENTION_TIME_IN_DAYS=1")
5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE'
'CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE'
"CREATE TABLE t (id INT) COMMENT='x'"
'CREATE TABLE t AS SELECT 1'
'CREATE TABLE t (id INT) CLUSTER BY (id)'
[tool_use Bash] {"command": "sed -n 5941,5963p tests/dialects/test_snowflake.py", "description": "Read nearby create view test for style"}
[tool_result]     def test_create_view_copy_grants(self):
        # for normal views, 'COPY GRANTS' goes *after* the column list. ref: https://docs.snowflake.com/en/sql-reference/sql/create-view#syntax
        self.validate_identity(
            "CREATE OR REPLACE VIEW FOO (A, B) COPY GRANTS AS SELECT A, B FROM TBL"
        )

        # for materialized views, 'COPY GRANTS' must go *before* the column list or an error will be thrown. ref: https://docs.snowflake.com/en/sql-reference/sql/create-materialized-vie
…[213 chars elided]…
ist and other properties still go after
        self.validate_identity(
            "CREATE OR REPLACE MATERIALIZED VIEW FOO COPY GRANTS (A, B) COMMENT='foo' TAG (a='b') AS SELECT A, B FROM TBL"
        )

        # no COPY GRANTS
        self.validate_identity("CREATE OR REPLACE VIEW FOO (A, B) AS SELECT A, B FROM TBL")
        self.validate_identity(
            "CREATE OR REPLACE MATERIALIZED VIEW FOO (A, B) AS SELECT A, B FROM TBL"
        )

    def test_create_view_row_access_policy(self):
[tool_use Bash] {"command": "sed -n 1,12p tests/dialects/test_snowflake.py; grep -n \"def validate_identity\" -A4 tests/dialects/test_dialect.py", "description": "Check test imports and validate_identity signature"}
[tool_result] from unittest import mock

from sqlglot import ParseError, UnsupportedError, exp, parse_one
from sqlglot.optimizer.annotate_types import annotate_types
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify_columns import quote_identifiers
from sqlglot.parser import logger as parser_logger
from tests.dialects.test_dialect import Validator


class TestSnowflake(Validator):
    maxDiff = None
53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "    def test_create_view_copy_grants(self):", "new_string": "    def test_create_table_properties_before_schema(self):\n        self.validate_identity(\"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\")\n        self.assertEqual(\n            parse_one(\"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\", read=\"snowflake\").sql(\n                \"snowflake\"\n            ),\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n\n    def test_create_view_copy_grants(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now the project's test command, the Snowflake suite first, then the full suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Run Snowflake dialect tests"}
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
6 failed, 93 passed, 784 subtests passed in 2.89s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"test_rely_options or row_access\" 2>&1 | grep -B3 \"Error\\b\\|Error:\" | head -40", "description": "Inspect specific failing test errors"}
[tool_result]         )
        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_sql}"
    
        error = ParseError.new(
--
    
        if self.error_level == ErrorLevel.IMMEDIATE:
>           raise error
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 41.
E             CREATE VIEW v (COL1 COMMENT [4m'description'[0m) WITH ROW ACCESS POLICY db.schema.policy ON (COL1) COMMENT='some comment' AS (SELECT a FROM t1 LEFT

sqlglot/parser.py:2007: ParseError
--
        )
        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_sql}"
    
        error = ParseError.new(
--
    
        if self.error_level == ErrorLevel.IMMEDIATE:
>           raise error
E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 36.
E             CREATE TABLE t (col1 INT [4mPRIMARY KEY[0m NORELY, col2 INT UNIQUE NORELY, col3 INT NOT NULL FOREIGN KEY REFERENCES other_t (id) NORELY)

sqlglot/parser.py:2007: ParseError
[assistant] The generic property parser is consuming the opening `(` of the column list. I'll guard the hook so it only runs when the current token isn't `(`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        # Snowflake allows KEY=VALUE properties between the table name and its column definitions\n        return self._parse_property()", "new_string": "        # Snowflake allows KEY=VALUE properties between the table name and its column definitions\n        if self._match(TokenType.L_PAREN, advance=False):\n            return None\n\n        return self._parse_property()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-162101-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -4", "description": "Re-run Snowflake dialect tests"}
[tool_result] ................. [ 17%]
................................................................................                                                                [100%]
97 passed, 1568 subtests passed in 0.65s
[assistant] All Snowflake tests pass now. Running the full suite, plus a check that the `CHANGE_TRACKING` example still parses.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)', read='snowflake', write='snowflake'))\nprint(sqlglot.transpile('CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE', read='snowflake', write='snowflake'))\n\"; git status --short", "description": "Run full test suite and verify both forms"}
[tool_result] ............................................. [ 74%]
.......................................... [ 78%]
....................................................................................................................................................................................................................................................                                           [100%]
1127 passed, 18271 subtests passed in 52.02s
['CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']
['CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE']
 M sqlglot/parsers/snowflake.py
 M tests/dialects/test_snowflake.py
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Snowflake now accepts `KEY = VALUE` properties before the column list. Both forms produce `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1127 tests) and ruff is clean.

**Cause:** the base parser only looks for pre-schema properties among the known `PROPERTY_PARSERS` keywords. `CHANGE_TRACKING` isn't one of them, so it was skipped. The parser then read `(id INT)` as a subquery and failed.

**Change:**
- `sqlglot/parsers/snowflake.py`: `SnowflakeParser._parse_property_before` now delegates to the generic `_parse_property`, so `KEY=VALUE` is accepted between the name and the schema. It returns `None` when the next token is `(`. Without that guard, the generic parser consumed the column list and broke existing tests for `COMMENT`, `PRIMARY KEY`, and row access policy cases.
- `tests/dialects/test_snowflake.py`: added `test_create_table_properties_before_schema`, covering the existing after-schema form and the new before-schema form.

Only Snowflake is affected; the base parser and other dialects are unchanged.
