# trajectory base-1

final message:
Snowflake now accepts `KEY = VALUE` properties before the column list, so `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)` parses and round-trips to `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1126 tests), and ruff check and format are clean. I haven't committed anything.

The change is in `sqlglot/parsers/snowflake.py`. The base parser already had a hook for properties that come right after the table name, but it only handled the Teradata-style keyword properties. I added a Snowflake override of `_parse_property_before` that also falls back to the generic `key = value` parser. It's wrapped in `_try_parse`, so a parenthesised column list like `CREATE VIEW v (COL1 COMMENT 'd')` is rewound instead of raising. My first version without that guard broke six Snowflake tests.

I added a regression assertion to `test_ddl` in `tests/dialects/test_snowflake.py`. Sequences, schemas, CTAS and the existing post-schema forms still round-trip.

The probe script needs `PYTHONPATH=.` and must be run without `-I`, because the env python has no installed `sqlglot`.

## events
[assistant] I'll reproduce the failure first, then look at how the parser handles properties in `CREATE`.
[tool_use Bash] {"command": "ls .lithify/harness/scripts/ && printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --help 2>&1 | head -30", "description": "List harness scripts and inspect probe script usage"}
[tool_result] probe_parse.py  2.2K
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --dialect snowflake 2>&1 | head -60", "description": "Probe the two CREATE TABLE forms in snowflake"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The probe script can't import `sqlglot` from this worktree. I'll check how it locates the package.
[tool_use Bash] {"command": "sed -n 1,40p .lithify/harness/scripts/probe_parse.py; printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\n' | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --dialect snowflake 2>&1 | head -60", "description": "Read probe script and rerun with worktree on path"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[469 chars elided]…
e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out

usage: probe_parse.py [-h] [--read READ] [--write WRITE]
probe_parse.py: error: unrecognized arguments: --dialect snowflake
[tool_use Bash] {"command": "printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\n' | PYTHONPATH=. <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read snowflake 2>&1 | head -60", "description": "Probe both CREATE TABLE forms with snowflake reader"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores `PYTHONPATH`, so I'll check what the project env has installed.
[tool_use Bash] {"command": "E=<work>/env-sqlglot/bin/python; $E -c \"import sys;print(sys.path)\"; ls $(dirname $E)/../lib/python*/site-packages | grep -i sqlglot; ls <work>/ 2>&1", "description": "Check env interpreter and sqlglot installation"}
[tool_result] ['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
sqlglot_mypy-2.3.0.post2.dist-info/
ab-load-preflight/
archive-b2-before-task4-20261029T104902Z/
claude-2.1.309/
cl
…[833 chars elided]…
-1-3.log  1.2K
AB-preflight-1-4.log  1.2K
A_SUPERVISOR.bootstrap.log  0B
A_SUPERVISOR.console.log  41.3K
A_SUPERVISOR.lock  0B
B-preflight-0-0.log  1006B
B-preflight-0-1.log  1006B
B-preflight-0-2.log  1006B
B-preflight-0-3.log  1006B
B-preflight-0-4.log  1006B
B-preflight-0-5.log  1002B
B-preflight-0-6.log  1006B
B-preflight-0-7.log  1006B
B_AB_OVERLAP.console.log  72B
B_PARALLEL.console.log  549B
B_PARALLEL.lock  0B
r1-B-rep2.console.log  10.9K
recovery-20261028-A2-before-resume.tar.gz  612.0M
[assistant] The env has no installed `sqlglot`; the earlier run with `PYTHONPATH=.` got past the import, so I'll rerun the probe that way.
[tool_use Bash] {"command": "printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\n' | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read snowflake 2>&1 | head -60", "description": "Probe both CREATE TABLE forms with snowflake reader"}
[tool_result] ERR       CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)
          ParseError: Expecting ). Line 1, Col: 39.
OK        CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
          CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
[assistant] Reproduced: the property-before-schema form fails with `Expecting )`. Next I'll read the create-parsing code.
[tool_use Bash] {"command": "grep -n \"def _parse_create\\|def _parse_schema\\|def _parse_properties\\|def _parse_property\\b\\|def _parse_with_property\\|POST_SCHEMA\\|PROPERTY_PARSERS\\b\" sqlglot/parser.py | head -60; grep -n \"PROPERTY_PARSERS\\|POST_SCHEMA\\|CREATE_\" sqlglot/dialects/snowflake.py | head", "description": "Locate create and property parsing functions"}
[tool_result] 19 matches in 13 files:

1227:0:t.ClassVar[dict[str, t.Callable]] = {
2360:0:
2783:0:
2795:0:
2796:0:
2799:0:
2869:0:bool | None = None) -> exp.Properties | None:
2992:0:
3350:0:
7087:0:
7089:0:
7218:0:exp.Expr | None = None) -> exp.Expr | None:
sqlglot/parser.py:2417:# exp.Properties.Location.POST_SCHEMA ("schema" here is the UDF's type signat...
sqlglot/parser.py:2558:# exp.Properties.Location.POST_SCHEMA and POST_WITH
sqlglot/parser.py:2784:parser = self.PROPERTY_PARSERS[self._prev.text.upper()]
sqlglot/parser.py:2797:return self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:2800:return self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
sqlglot/parser.py:7088:prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7090:prop = self.PROPERTY_PARSERS[self._prev.text.upper()](self, default=True)
0 matches for 'PROPERTY_PARSERS\|POST_SCHEMA\|CREATE_'
[tool_use Bash] {"command": "grep -n \"def _parse_create\\|def _parse_schema\\|def _parse_properties\\|def _parse_property\\|POST_SCHEMA\\|POST_WITH\\|POST_EXPRESSION\" sqlglot/parser.py | head -60", "description": "Find create, schema, and property parser definitions"}
[tool_result] 10 matches in 8 files:

2360:0:
2767:0:
2795:0:
2863:0:type[E], **kwargs: t.Any) -> E:
2869:0:bool | None = None) -> exp.Properties | None:
3350:0:
7218:0:exp.Expr | None = None) -> exp.Expr | None:
sqlglot/parser.py:2417:# exp.Properties.Location.POST_SCHEMA ("schema" here is the UDF's type signat...
sqlglot/parser.py:2558:# exp.Properties.Location.POST_SCHEMA and POST_WITH
sqlglot/parser.py:2595:# exp.Properties.Location.POST_EXPRESSION
[assistant] The grep output is odd, so I'll search with a narrower pattern.
[tool_use Bash] {"command": "/usr/bin/grep -n \"def _parse_create\\|def _parse_schema\\|def _parse_properties\" sqlglot/parser.py", "description": "Search parser for create and schema functions"}
[tool_result] 2360:    def _parse_create(self) -> exp.Create | exp.Command:
2869:    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
3350:    def _parse_create_like(self) -> exp.LikeProperty | None:
7218:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", "offset": 2360, "limit": 150}
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
…[6017 chars elided]…
         table = self._parse_table_parts()
2503	            referenced_table = self._parse_table_parts() if self._match(TokenType.FROM) else None
2504	            deferrable, initially = self._parse_trigger_deferrable()
2505	            referencing = self._parse_trigger_referencing()
2506	            for_each = self._parse_trigger_for_each()
2507	            when = self._match_text_seq("WHEN") and self._parse_wrapped(
2508	                self._parse_disjunction, optional=True
2509	            )
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", "offset": 2869, "limit": 40}
[tool_result] 2869	    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2870	        properties = []
2871	        while True:
2872	            if before:
2873	                prop = self._parse_property_before()
2874	            else:
2875	                prop = self._parse_property()
2876	            if not prop:
2877	                break
2878	            for p in ensure_list(prop):
2879	                properties.append(p)
2880	
2881	        if properties:
2882	            
…[650 chars elided]…
operty(self) -> exp.SettingsProperty:
2899	        return self.expression(
2900	            exp.SettingsProperty(expressions=self._parse_csv(self._parse_assignment))
2901	        )
2902	
2903	    def _parse_called_on_null_input_property(self) -> exp.CalledOnNullInputProperty | None:
2904	        if not self._match_text_seq("ON", "NULL", "INPUT"):
2905	            self._retreat(self._index - 1)
2906	            return None
2907	
2908	        return self.expression(exp.CalledOnNullInputProperty())
[assistant] Next, the table branch of `_parse_create`, where the schema and trailing properties are parsed.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", "offset": 2520, "limit": 150}
[tool_result] 2520	                    execute=execute,
2521	                    constraint=is_constraint,
2522	                    referenced_table=referenced_table,
2523	                    deferrable=deferrable,
2524	                    initially=initially,
2525	                    referencing=referencing,
2526	                    for_each=for_each,
2527	                    when=when,
2528	                )
2529	            )
2530	
2531	            this = trigger_name
2532	            extend_props(exp.Prop
…[6049 chars elided]…
        elif self._match(TokenType.START_WITH) or self._match_text_seq("START"):
2663	                self._match_text_seq("=")
2664	                seq.set("start", self._parse_term())
2665	            elif self._match_text_seq("CACHE"):
2666	                # T-SQL allows empty CACHE which is initialized dynamically
2667	                seq.set("cache", self._parse_number() or True)
2668	            elif self._match_text_seq("OWNED", "BY"):
2669	                # "OWNED BY NONE" is the default
[assistant] The base parser already has a POST_NAME hook (`_parse_properties(before=True)`). I'll check how `CHANGE_TRACKING` is handled and what `_parse_property_before` accepts.
[tool_use Bash] {"command": "/usr/bin/grep -rn \"CHANGE_TRACKING\\|ChangeTracking\\|change_tracking\" sqlglot tests | head -20; /usr/bin/grep -n \"def _parse_property_before\\|def _parse_property(\" -A30 sqlglot/parser.py | head -120", "description": "Find CHANGE_TRACKING handling and property parser functions"}
[tool_result] tests/dialects/test_snowflake.py:5758:        self.validate_identity("ALTER TABLE foo SET CHANGE_TRACKING=FALSE")
tests/dialects/test_snowflake.py:5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
2768-        # only used for teradata currently
2769-        self._match(TokenType.COMMA)
2770-
2771-        kwargs = {
2772-            "no": self._match_text_seq("NO"
…[1960 chars elided]…
(index)
2815-        key = self._parse_column()
2816-
2817-        if not self._match(TokenType.EQ):
2818-            self._retreat(index)
2819-            return None
2820-
2821-        # Transform the key to exp.Dot if it's dotted identifiers wrapped in exp.Column or to exp.Var otherwise
2822-        if isinstance(key, exp.Column):
2823-            key = key.to_dot() if len(key.parts) > 1 else exp.var(key.name)
2824-
2825-        value = self._parse_bitwise() or self._parse_var(any_token=True)
[assistant] `CREATE TABLE` only parses the generic `key = value` property after the schema. The POST_NAME hook (`_parse_property_before`) only handles the `PROPERTY_PARSERS` keywords (Teradata). I'll check the other callers and the Snowflake parser's existing overrides before choosing where to hook in.
[tool_use Bash] {"command": "/usr/bin/grep -rn \"_parse_property_before\\|_parse_properties(before\" sqlglot | head; /usr/bin/grep -n \"class Parser\" -A12 sqlglot/dialects/snowflake.py | head -30; /usr/bin/grep -n \"        def _parse_\\|    class Parser\\|    class Generator\" sqlglot/dialects/snowflake.py | head -40", "description": "Check callers and Snowflake parser overrides"}
[tool_result] Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:2554:            extend_props(self._parse_properties(before=True))
sqlglot/parser.py:2767:    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:
sqlglot/parser.py:2873:                prop = self._parse_property_before()
[tool_use Bash] {"command": "/usr/bin/grep -n \"class Parser\\|def _parse_\\|class Tokenizer\\|class Generator\" sqlglot/dialects/snowflake.py | head -40", "description": "List Snowflake parser method overrides"}
[tool_result] 135:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "/usr/bin/grep -n \"Parser\\|^    class \\|PROPERTY_PARSERS\" sqlglot/dialects/snowflake.py | head -40", "description": "Locate parser class in Snowflake dialect"}
[tool_result] 10:    SnowflakeParser,
129:    class JSONPathTokenizer(jsonpath.JSONPathTokenizer):
133:    Parser = SnowflakeParser
135:    class Tokenizer(tokens.Tokenizer):
[tool_use Bash] {"command": "F=$(/usr/bin/grep -rln \"class SnowflakeParser\" sqlglot); echo $F; /usr/bin/grep -n \"    def _parse_\\|PROPERTY_PARSERS\" $F | head -60", "description": "Find SnowflakeParser definition and its methods"}
[tool_result] sqlglot/parsers/snowflake.py
767:    PROPERTY_PARSERS = {
768:        **parser.Parser.PROPERTY_PARSERS,
921:    def _parse_directory(self) -> exp.DirectoryStage:
926:    def _parse_describe(self) -> exp.Describe:
952:    def _parse_use(self) -> exp.Use:
976:    def _parse_tag(self) -> exp.Tags:
979:    def _parse_with_constraint(self) -> exp.Expr | None:
1004:    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
1013:    def _parse_row_access_policy(self) -> exp.RowAccessProper
…[893 chars elided]…
self) -> exp.FileFormatProperty:
1304:    def _parse_credentials_property(self) -> exp.CredentialsProperty:
1307:    def _parse_semantic_view(self) -> exp.SemanticView:
1324:    def _parse_set(self, unset: bool = False, tag: bool = False) -> exp.Set | exp.Command:
1333:    def _parse_position(self, haystack_first: bool = False) -> exp.StrPosition:
1338:    def _parse_substring(self) -> exp.Substring:
1355:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "offset": 1000, "limit": 42}
[tool_result] 1000	            return self._parse_tag()
1001	
1002	        return None
1003	
1004	    def _parse_with_property(self) -> exp.Expr | None | list[exp.Expr]:
1005	        if self._match(TokenType.TAG):
1006	            return self._parse_tag()
1007	
1008	        if self._match_text_seq("ROW", "ACCESS", "POLICY"):
1009	            return self._parse_row_access_policy()
1010	
1011	        return super()._parse_with_property()
1012	
1013	    def _parse_row_access_policy(self) -> exp.RowAccessProperty
…[1027 chars elided]…
BLE_CREATABLES:
1033	            # Replace the Table node with the enclosed Identifier
1034	            expression.this.replace(expression.this.this)
1035	
1036	        return expression
1037	
1038	    # https://docs.snowflake.com/en/sql-reference/functions/date_part.html
1039	    # https://docs.snowflake.com/en/sql-reference/functions-date-time.html#label-supported-date-time-parts
1040	    def _parse_date_part(self) -> exp.Expr | None:
1041	        this = self._parse_var() or self._parse_type()
[assistant] Before choosing the hook, I need the rest of `_parse_property` to see how the generic `key = value` branch is built.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parser.py", "offset": 2825, "limit": 20}
[tool_result] 2825	        value = self._parse_bitwise() or self._parse_var(any_token=True)
2826	
2827	        # Transform the value to exp.Var if it was parsed as exp.Column(exp.Identifier())
2828	        if isinstance(value, exp.Column):
2829	            value = exp.var(value.name)
2830	
2831	        return self.expression(exp.Property(this=key, value=value))
2832	
2833	    def _parse_stored(self) -> exp.FileFormatProperty | exp.StorageHandlerProperty:
2834	        if self._match_text_seq("BY"):
2835	            return self.expression(exp.StorageHandlerProperty(this=self._parse_var_or_string()))
2836	
2837	        self._match(TokenType.ALIAS)
2838	        input_format = self._parse_string() if self._match_text_seq("INPUTFORMAT") else None
2839	        output_format = self._parse_string() if self._match_text_seq("OUTPUTFORMAT") else None
2840	
2841	        return self.expression(
2842	            exp.FileFormatProperty(
2843	                this=(
2844	                    self.expression(
[assistant] I'll override `_parse_property_before` in the Snowflake parser so the POST_NAME hook also accepts generic `key = value` properties. The base class is untouched, so other dialects keep their current behaviour.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))\n\n    def _parse_create(self) -> exp.Create | exp.Command:", "new_string": "        return self.expression(exp.RowAccessProperty(this=policy, expressions=expressions))\n\n    def _parse_property_before(self) -> exp.Expr | list[exp.Expr] | None:\n        # Snowflake also accepts KEY=VALUE properties before the column definitions\n        return super()._parse_property_before() or self._parse_property()\n\n    def _parse_create(self) -> exp.Create | exp.Command:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\nCREATE TABLE t CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1 (id INT, b TEXT) COMMENT=%s\\nCREATE SEQUENCE s START 1 INCREMENT 1\\nCREATE SCHEMA s DATA_RETENTION_TIME_IN_DAYS=1\\nCREATE TABLE t AS SELECT 1\\n' \"'x'\" | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read snowflake 2>&1 | head -60", "description": "Apply parser override and reprobe CREATE variants"}
[tool_result] OK        CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)
          CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
OK        CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
          CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
OK        CREATE TABLE t CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1 (id INT, b TEXT) COMMENT='x'
          CREATE TABLE t (id INT, b VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1
OK        CREATE SEQUENCE s START 1 INCREMENT 1
          CREATE SEQUENCE s START WITH 1 INCREMENT BY 1
OK        CREATE SCHEMA s DATA_RETENTION_TIME_IN_DAYS=1
          CREATE SCHEMA s DATA_RETENTION_TIME_IN_DAYS=1
OK        CREATE TABLE t AS SELECT 1
          CREATE TABLE t AS SELECT 1
[assistant] The probe now passes for both forms, and the sequence, schema, and CTAS cases still round-trip. Next I'll add a regression test next to the existing Snowflake DDL tests.
[tool_use Bash] {"command": "/usr/bin/grep -n \"def test_ddl\\|def test_create\\|def test_table\" tests/dialects/test_snowflake.py; /usr/bin/grep -n \"DATA_RETENTION_TIME_IN_DAYS\" tests/dialects/test_snowflake.py | head -5", "description": "Find Snowflake DDL test methods"}
[tool_result] 4240:    def test_ddl(self):
4443:    def test_table_function(self):
5941:    def test_create_view_copy_grants(self):
5963:    def test_create_view_row_access_policy(self):
6069:    def test_create_sequence(self):
5755:        self.validate_identity("ALTER TABLE tbl SET DATA_RETENTION_TIME_IN_DAYS=1")
5769:        self.validate_identity("ALTER TABLE foo UNSET DATA_RETENTION_TIME_IN_DAYS, CHANGE_TRACKING")
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "offset": 4240, "limit": 25}
[tool_result] 4240	    def test_ddl(self):
4241	        for constraint_prefix in ("WITH ", ""):
4242	            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4243	                self.validate_identity(
4244	                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
4245	                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
4246	                )
4247	                self.validate_identity(
4248	                    f"CREATE TABLE t (id INT {constrain
…[560 chars elided]…
                  "CREATE TABLE t (id INT TAG (key1='value_1', key2='value_2'))",
4258	                )
4259	
4260	        self.validate_identity("CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)")
4261	        self.validate_identity("USE SECONDARY ROLES ALL")
4262	        self.validate_identity("USE SECONDARY ROLES NONE")
4263	        self.validate_identity("USE SECONDARY ROLES a, b, c")
4264	        self.validate_identity("CREATE SECURE VIEW table1 AS (SELECT a FROM table2)")
[assistant] I'll add the test right after the existing `COPY GRANTS` identity checks in `test_ddl`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")", "new_string": "        self.validate_identity(\"CREATE OR REPLACE TABLE foo COPY GRANTS USING TEMPLATE (SELECT 1)\")\n        self.validate_identity(\n            \"CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\",\n            \"CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\",\n        )\n        self.validate_identity(\"USE SECONDARY ROLES ALL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Run Snowflake dialect test file"}
[tool_result] E           sqlglot.errors.ParseError: Expecting ). Line 1, Col: 42.
E             CREATE TABLE foo (bar DOUBLE [4mAUTOINCREMENT[0m START 0 INCREMENT 1)

sqlglot/parser.py:2007: ParseError
----------------------------- Captured stdout call -----------------------------
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu [ 80%]
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
=========================== short test summary info ============================
FAILED tests/dialects/test_snowflake
…[30 chars elided]…
e_view_row_access_policy
SUBFAILED[Constraint prefix: WITH ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
SUBFAILED[Constraint prefix: ] tests/dialects/test_snowflake.py::TestSnowflake::test_ddl
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_ddl - sqlglot.er...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_rely_options - s...
FAILED tests/dialects/test_snowflake.py::TestSnowflake::test_snowflake - sqlg...
6 failed, 92 passed, 784 subtests passed in 2.80s
[assistant] Six Snowflake tests now fail, including ones with no `CHANGE_TRACKING` involved. I need the first traceback to see which path my override is hitting.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py::TestSnowflake::test_create_view_row_access_policy 2>&1 | grep -v \"^$\" | head -60", "description": "Show traceback for row access policy test failure"}
[tool_result] F                                                                        [100%]
=================================== FAILURES ===================================
_______________ TestSnowflake.test_create_view_row_access_policy _______________
self = <tests.dialects.test_snowflake.TestSnowflake testMethod=test_create_view_row_access_policy>
    def test_create_view_row_access_policy(self):
        self.validate_identity(
            "CREATE VIEW v WITH ROW ACCESS POLICY mypolicy ON (col1) AS SELEC
…[2185 chars elided]…
elf._parse_property_before()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlglot/parsers/snowflake.py:1032: in _parse_property_before
    return super()._parse_property_before() or self._parse_property()
                                               ^^^^^^^^^^^^^^^^^^^^^^
sqlglot/parser.py:2815: in _parse_property
    key = self._parse_column()
          ^^^^^^^^^^^^^^^^^^^^
sqlglot/parser.py:6578: in _parse_column
    this = self._parse_column_reference()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[assistant] The override is too broad: at POST_NAME, `_parse_property` calls `_parse_column`, and that raises on `CREATE VIEW v (COL1 COMMENT ...)`, where the parenthesised column list is not a property. I'll look at `_try_parse` to see whether it can guard that call.
[tool_use Bash] {"command": "/usr/bin/grep -n \"def _try_parse\" -A22 sqlglot/parser.py", "description": "Read _try_parse helper semantics"}
[tool_result] 2021:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
2022-        index = self._index
2023-        error_level = self.error_level
2024-        this: T | None = None
2025-
2026-        self.error_level = ErrorLevel.IMMEDIATE
2027-        try:
2028-            this = parse_method()
2029-        except ParseError:
2030-            this = None
2031-        finally:
2032-            if not this or retreat:
2033-                self._retreat(index)
2034-            self.error_level = error_level
2035-
2036-        return this
2037-
2038-    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
2039-        """
2040-        Parses a list of tokens and returns a list of syntax trees, one tree
2041-        per parsed SQL statement.
2042-
2043-        Args:
[assistant] `_try_parse` runs the method at immediate error level and rewinds on failure or `None`, so wrapping `_parse_property` with it should stop the view's parenthesised column list from being mistaken for a property.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return super()._parse_property_before() or self._parse_property()", "new_string": "        return super()._parse_property_before() or self._try_parse(self._parse_property)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-171033-snowflake-dialect-in-create-stat/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -4", "description": "Apply guarded override and rerun Snowflake tests"}
[tool_result] ............................... [ 32%]
.................................................................                                                                 [100%]
96 passed, 1568 subtests passed in 0.47s
[assistant] The Snowflake file passes (96 tests). Next I'll rerun the probe variants and the full suite, which the harness asks for as the final gate.
[tool_use Bash] {"command": "printf 'CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)\\nCREATE TABLE t (id INT) CHANGE_TRACKING=TRUE\\nCREATE TABLE t CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1 (id INT, b TEXT) COMMENT=%s\\nCREATE SEQUENCE s START 1 INCREMENT 1\\nCREATE VIEW v (COL1 COMMENT %s) AS SELECT 1\\n' \"'x'\" \"'d'\" | PYTHONPATH=. <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read snowflake 2>&1; time <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -6", "description": "Reprobe variants and run full test suite"}
[tool_result] OK        CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)
          CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
OK        CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
          CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE
OK        CREATE TABLE t CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1 (id INT, b TEXT) COMMENT='x'
          CREATE TABLE t (id INT, b VARCHAR) COMMENT='x' CHANGE_TRACKING=TRUE DATA_RETENTION_TIME_IN_DAYS=1
OK        CREATE SEQUENCE s START 1 INCREMENT 1
          CREATE SE
…[460 chars elided]…
................................................................................................................................................................................................................................                                            [100%]
1126 passed, 18271 subtests passed in 46.44s
<work>/env-sqlglot/bin/python -m   114.01s user 12.61s system 271% cpu 46.670 total
tail -6  0.00s user 0.00s system 0% cpu 46.669 total
[assistant] The full suite passes (1126 tests). I'll run the linter and formatter on the two changed files, then check the final diff.
[tool_use Bash] {"command": "E=<work>/env-sqlglot/bin; ($E/ruff --version && $E/ruff check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py && $E/ruff format --check sqlglot/parsers/snowflake.py tests/dialects/test_snowflake.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files; show diff stat"}
[tool_result] ruff 0.15.6
All checks passed!
2 files already formatted
sqlglot/parsers/snowflake.py     | 4 ++++
 tests/dialects/test_snowflake.py | 4 ++++
 2 files changed, 8 insertions(+)
[assistant] Snowflake now accepts `KEY = VALUE` properties before the column list, so `CREATE TABLE t CHANGE_TRACKING=TRUE (id INT)` parses and round-trips to `CREATE TABLE t (id INT) CHANGE_TRACKING=TRUE`. The full suite passes (1126 tests), and ruff check and format are clean. I haven't committed anything.

The change is in `sqlglot/parsers/snowflake.py`. The base parser already had a hook for properties that come right after the table name, but it only handled the Teradata-style keyword properties. I added a Snowflake override of `_parse_property_before` that also falls back to the generic `key = value` parser. It's wrapped in `_try_parse`, so a parenthesised column list like `CREATE VIEW v (COL1 COMMENT 'd')` is rewound instead of raising. My first version without that guard broke six Snowflake tests.

I added a regression assertion to `test_ddl` in `tests/dialects/test_snowflake.py`. Sequences, schemas, CTAS and the existing post-schema forms still round-trip.

The probe script needs `PYTHONPATH=.` and must be run without `-I`, because the env python has no installed `sqlglot`.
