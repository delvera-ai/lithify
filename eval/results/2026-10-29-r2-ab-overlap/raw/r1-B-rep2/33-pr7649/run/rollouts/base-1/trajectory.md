# trajectory base-1

final message:
`FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the "Unsupported query option." warning, the same as `FOR XML`. The full suite passes (1108 tests, exit 0), and ruff is clean on the changed files. I haven't committed anything.

What changed:

- **`sqlglot/parsers/tsql.py`**: `_parse_for` accepts `FOR JSON` alongside `FOR XML`. A new `JSON_OPTIONS` table covers `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. `ROOT` and `ROOT('name')` go through the existing key-value path that `FOR XML` uses.
- **`sqlglot/generator.py`**: `for_modifiers` emits `FOR XML` and `FOR JSON` from separate args. JSON clauses are stored under `for_json`, so the existing `FOR XML` AST is unchanged, and a duplicate `FOR JSON` still raises "Found multiple" as it would for `FOR XML`.
- **`tests/dialects/test_tsql.py`**: new `test_for_json` covering option forms, pretty output, the DuckDB unsupported error, and the dropped-clause warning.

Decisions for you to check:

- I added a sibling `test_for_json` method rather than putting the cases inside `test_for_xml`.
- Per the harness, I ran the probe with `PYTHONPATH` pointing at the repo and without `-I`. The venv doesn't install `sqlglot`, and `-I` ignores `PYTHONPATH`. The repo is my own working tree, so I judged this safe, but it is a deviation from the memory note.

## events
[assistant] I'll start by finding how `FOR XML` is handled today, since `FOR JSON` should follow the same path.
[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\" sqlglot/ | head -60; echo ---; grep -rn -i \"for_json\\|ForJson\\|FOR JSON\" sqlglot/ tests/ | head; echo ---; ls .lithify/harness 2>/dev/null; ls .claude 2>/dev/null", "description": "Locate FOR XML handling and any FOR JSON references"}
[tool_result] sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/dialects/tsql.py:184:            "XML": TokenType.XML,
sqlglot/dialects/postgres.py:114:            "XML": TokenType.XML,
---
tests/dialects/test_tsql.py:545:            for json_clause in ("", " NULL ON NULL", " ABSENT ON NULL"):
---
scripts/
skills/
guardrails.md  147B
memory.md  153B
system.md  260B
tool_guidance.md  535B
skills/
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "offset": 470, "limit": 70}
[tool_result] 470	
471	    def _parse_dcolon(self) -> exp.Expr | None:
472	        # We want to use _parse_types() if the first token after :: is a known type,
473	        # otherwise we could parse something like x::varchar(max) into a function
474	        if self._match_set(self.TYPE_TOKENS, advance=False):
475	            return self._parse_types()
476	
477	        return self._parse_function() or self._parse_types()
478	
479	    def _parse_options(self) -> list[exp.Expr] | None:
480	        if not self._m
…[1967 chars elided]…
          (
530	                exp.alias_(projection.expression, projection.this.this, copy=False)
531	                if isinstance(projection, exp.EQ) and isinstance(projection.this, exp.Column)
532	                else projection
533	            )
534	            for projection in projections
535	        ], None
536	
537	    def _parse_commit_or_rollback(self) -> exp.Commit | exp.Rollback:
538	        """Applies to SQL Server and Azure SQL Database
539	        COMMIT [ { TRAN | TRANSACTION }
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "offset": 3070, "limit": 50}
[tool_result] 3070	                after,
3071	                pattern,
3072	                define,
3073	            )
3074	        )
3075	        alias = self.sql(expression, "alias")
3076	        alias = f" {alias}" if alias else ""
3077	        return f"{self.seg('MATCH_RECOGNIZE')} {self.wrap(body)}{alias}"
3078	
3079	    def query_modifiers(self, expression: exp.Expr, *sqls: str) -> str:
3080	        limit = expression.args.get("limit")
3081	
3082	        if self.LIMIT_FETCH == "LIMIT" and isinstance(li
…[1462 chars elided]…
odifiers(self, expression: exp.Expr) -> str:
3111	        for_modifiers = self.expressions(expression, key="for_")
3112	        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
3113	
3114	    def queryoption_sql(self, expression: exp.QueryOption) -> str:
3115	        self.unsupported("Unsupported query option.")
3116	        return ""
3117	
3118	    def offset_limit_modifiers(
3119	        self, expression: exp.Expr, fetch: bool, limit: exp.Fetch | exp.Limit | None
[tool_use Bash] {"command": "grep -rn \"for_xml\\|ForXml\\|XMLTable\\|FOR XML\" tests/ | head -30; grep -rn \"class .*Xml\\|for_xml\" sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null | head; cat .lithify/harness/skills/*/SKILL.md 2>/dev/null | head -80; ls .lithify/harness/skills", "description": "Find FOR XML tests and expression definitions"}
[tool_result] tests/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
sqlglot/expressions/functions.py:178:class CheckXml(Expression, Func):
---
n
…[1336 chars elided]…
ialect, using the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.
parse-failure-triage/
[tool_use Bash] {"command": "sed -n 630,720p tests/dialects/test_tsql.py; echo ---; grep -n \"XML_OPTIONS\" -A25 sqlglot/parsers/tsql.py | head -50; echo ---; cat .lithify/harness/memory.md; echo; grep -rn \"for_\" sqlglot/expressions/query.py | head; echo ---; grep -rn \"unsupported\\|for_\\b\" sqlglot/dialects/*.py | grep -i \"for_xml\\|for_json\" | head; cat .lithify/harness/scripts/probe_parse.py | head -40", "description": "Read FOR XML tests and XML options; probe script"}
[tool_result]                 self.parse_one(query)

        self.validate_all(
            "SELECT col FROM t OPTION(LABEL = 'foo')",
            write={
                "tsql": "SELECT col FROM t OPTION(LABEL = 'foo')",
                "databricks": UnsupportedError,
            },
        )

    def test_for_xml(self):
        xml_possible_options = [
            "RAW('ElementName')",
            "RAW('ElementName'), BINARY BASE64",
            "RAW('ElementName'), TYPE",
            "RAW('ElementName'), R
…[6295 chars elided]…
ef probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out
[assistant] The `FOR XML` clause is parsed into a `for_` list of `QueryOption`s, and other dialects drop it through `queryoption_sql`. Next I'll check the current behavior with the probe script before changing anything.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; grep -rn \"_parse_for\\b\\|\\\"for_\\\"\\|\\\"for_\\\":\" sqlglot/parser.py sqlglot/parsers/*.py | head; printf '%s\\n' \"SELECT * FROM t FOR XML PATH\" \"SELECT * FROM t FOR JSON AUTO\" \"SELECT * FROM t FOR JSON PATH\" \"SELECT * FROM t FOR JSON AUTO, ROOT('r')\" \"SELECT * FROM t FOR JSON PATH, ROOT\" \"S
…[135 chars elided]…
 PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER\" | $PY -I .lithify/harness/scripts/probe_parse.py --read tsql; echo \"exit $?\"; printf '%s\\n' \"SELECT * FROM t FOR XML PATH\" \"SELECT * FROM t FOR XML PATH, ROOT('r')\" | $PY -I .lithify/harness/scripts/probe_parse.py --read tsql --write duckdb; echo \"exit $?\"", "description": "Probe FOR JSON and FOR XML behavior on current code"}
[tool_result] sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/parsers/tsql.py:504:    def _parse_for(self) -> list[exp.Expr] | None:
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit 1
[assistant] The probe failed because `-I` ignores `PYTHONPATH` and the venv has no `sqlglot` installed. I'll check what the venv resolves to before choosing a workaround.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sys; print(sys.version)\"; $PY -m pip show sqlglot 2>/dev/null | head -3; ls $(dirname $PY)/../lib/python*/site-packages | grep -i sqlglot; cat $(dirname $PY)/../lib/python*/site-packages/*.pth 2>/dev/null | head", "description": "Check venv sqlglot installation source"}
[tool_result] 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
sqlglot_mypy-2.3.0.post2.dist-info/
import _virtualenvimport os; var = 'SETUPTOOLS_USE_DISTUTILS'; enabled = os.environ.get(var, 'local') == 'local'; enabled and __import__('_distutils_hack').add_shim();
[assistant] The venv has no `sqlglot` installed, and `-I` also blocks `PYTHONPATH`. The repo is my own trusted working tree, so I'll point `PYTHONPATH` at it and run the probe without `-I`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; printf '%s\\n' \"SELECT * FROM t FOR XML PATH\" \"SELECT * FROM t FOR JSON AUTO\" \"SELECT * FROM t FOR JSON PATH\" \"SELECT * FROM t FOR JSON AUTO, ROOT('r')\" \"SELECT * FROM t FOR JSON PATH, ROOT\" \"SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES\" \"SELECT * FROM t FOR JSON PA
…[41 chars elided]…
OM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER\" | $PY .lithify/harness/scripts/probe_parse.py --read tsql; echo \"exit $?\"; printf '%s\\n' \"SELECT * FROM t FOR XML PATH\" \"SELECT * FROM t FOR XML PATH, ROOT('r')\" | $PY .lithify/harness/scripts/probe_parse.py --read tsql --write duckdb; echo \"exit $?\"", "description": "Probe FOR JSON and FOR XML with repo on path"}
[tool_result] OK        SELECT * FROM t FOR XML PATH
          SELECT * FROM t FOR XML PATH
ERR       SELECT * FROM t FOR JSON AUTO
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
ERR       SELECT * FROM t FOR JSON PATH
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
ERR       SELECT * FROM t FOR JSON AUTO, ROOT('r')
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
ERR       SELECT * FROM t FOR JSON PATH, ROOT
          P
…[252 chars elided]…
UT_ARRAY_WRAPPER
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
ERR       SELECT * FROM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 19.
exit 1
Unsupported query option.
Unsupported query option.
Unsupported query option.
OK        SELECT * FROM t FOR XML PATH
          SELECT * FROM t
OK        SELECT * FROM t FOR XML PATH, ROOT('r')
          SELECT * FROM t
exit 0
[assistant] Reproduced: every `FOR JSON` form fails to parse in T-SQL, and `FOR XML` round-trips. Before choosing where the JSON clause is stored, I'll read the modifier dispatch, the `for_` arg declaration, and the XML option helpers.
[tool_use Bash] {"command": "grep -rn '\"for_\"\\|for_\\b' sqlglot/ | grep -v \"for_system\\|format\" | head -20; echo ---; sed -n 310,330p sqlglot/parsers/tsql.py; echo ---; grep -n \"def _parse_var_from_options\" -A40 sqlglot/parser.py | head -60; echo ---; grep -n \"class QueryOption\\|class XMLKeyValueOption\" -A6 sqlglot/expressions/*.py; echo ---; grep -n \"xmlkeyvalueoption_sql\\|def queryoption\" -A8 sqlglot/dialects/tsql.py sqlglot/generators/tsql.py sqlglot/generator.py 2>/dev/null | head -40", "description": "Read FOR-modifier dispatch and option helpers"}
[tool_result] Binary file sqlglot/parsers/__pycache__/tsql.cpython-312.pyc matches
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/expressions/string.py:102:    ar
…[4684 chars elided]…
elf.sql(expression, "expression")
sqlglot/generator.py-5677-        expr = f"({expr})" if expr else ""
sqlglot/generator.py-5678-        return f"{this}{expr}"
sqlglot/generator.py-5679-
sqlglot/generator.py-5680-    def partitionbyrangeproperty_sql(self, expression: exp.PartitionByRangeProperty) -> str:
sqlglot/generator.py-5681-        partitions = self.expressions(expression, "partition_expressions")
sqlglot/generator.py-5682-        create = self.expressions(expression, "create_expressions")
[assistant] The generator hard-codes `FOR XML`, so the JSON clause needs its own marker to be emitted correctly. I'll check how `Select` declares its args and how query-modifier parsers consume their `(key, value)` tuples.
[tool_use Bash] {"command": "grep -n \"^class Select(\" -A30 sqlglot/expressions/query.py | grep -n \"arg_types\\|options\\|for\" ; grep -n \"QUERY_MODIFIER_PARSERS.items\\|QUERY_MODIFIER_PARSERS\\[\" -B3 -A12 sqlglot/parser.py | head -50; grep -n \"class Expression\\b\\|def set(\" sqlglot/expressions/core.py | head -3; grep -rn \"for_json\\|for_xml\" tests/ sqlglot/ --include=*.py | head", "description": "Inspect Select args and query modifier parsing loop"}
[tool_result] 2:1124-    arg_types = {
4114-            while True:
4115-                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4116-                    modifier_token = self._curr
4117:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
4118-                    key, expression = parser(self)
4119-
4120-                    if expression:
4121-                        if this.args.get(key):
4122-                            self.raise_error(
4123-         
…[31 chars elided]…
multiple '{modifier_token.text.upper()}' clauses",
4124-                                token=modifier_token,
4125-                            )
4126-
4127-                        this.set(key, expression)
4128-                        if key == "limit":
4129-                            offset = expression.args.get("offset")
rg: regex parse error:
    (?:class Expression\b|def set()
    ^
error: unclosed group
0 matches for 'class Expression\b\|def set('
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "sed -n 1124,1150p sqlglot/expressions/query.py", "description": "Read Select arg_types definition"}
[tool_result]     arg_types = {
        "with_": False,
        "kind": False,
        "expressions": False,
        "hint": False,
        "distinct": False,
        "into": False,
        "from_": False,
        "operation_modifiers": False,
        "exclude": False,
        **QUERY_MODIFIERS,
    }

    def from_(
        self,
        expression: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
    ) -> Select:
        """
        Set the FROM expression.

        Example:
            >>> Select().from_("tbl").select("x").sql()
            'SELECT x FROM tbl'
[tool_use Bash] {"command": "grep -n \"^QUERY_MODIFIERS\" -A40 sqlglot/expressions/query.py | grep -n \"for\\|options\\|}\" | head", "description": "Locate for_ in QUERY_MODIFIERS"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"QUERY_MODIFIERS\\s*=\" sqlglot/ --include=*.py; grep -rn '\"for_\":' sqlglot/ --include=*.py", "description": "Find QUERY_MODIFIERS definition"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"QUERY_MODIFIERS = \\|QUERY_MODIFIERS: \" sqlglot/ ; grep -rn '\"for_\"' sqlglot/ ", "description": "Find QUERY_MODIFIERS definition"}
[tool_result] sqlglot/expressions/core.py:2408:QUERY_MODIFIERS = {
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
[tool_use Bash] {"command": "sed -n 2408,2445p sqlglot/expressions/core.py", "description": "Read QUERY_MODIFIERS dict"}
[tool_result] QUERY_MODIFIERS = {
    "match": False,
    "laterals": False,
    "joins": False,
    "connect": False,
    "pivots": False,
    "prewhere": False,
    "where": False,
    "group": False,
    "having": False,
    "qualify": False,
    "windows": False,
    "distribute": False,
    "sort": False,
    "cluster": False,
    "order": False,
    "limit": False,
    "offset": False,
    "locks": False,
    "sample": False,
    "settings": False,
    "format": False,
    "options": False,
}


TIMESTAMP_PARTS = {
    "year": False,
    "month": False,
    "day": False,
    "hour": False,
    "min": False,
    "sec": False,
    "nano": False,
}


@t.overload
[assistant] `for_` is not declared in `QUERY_MODIFIERS`, so the generator reads it by name only. Before writing code I need to confirm three things: that `JSON` is a token type, how the generator's `expressions()` treats empty strings, and how existing tests assert the unsupported-option warning for other dialects.
[tool_use Bash] {"command": "grep -rn \"    JSON = \\|TokenType.JSON\\b\" sqlglot/tokens*.py sqlglot/parsers/tsql.py sqlglot/dialects/tsql.py 2>/dev/null | head -5; grep -rn \"def _match_pair\" sqlglot/parser.py; grep -rn \"for_modifiers\\|queryoption\" sqlglot/generators/*.py sqlglot/dialects/tsql.py | head; grep -n \"def expressions\" -A40 sqlglot/generator.py | grep -n \"if\\|sqls\" | head -12; echo ---; grep -rn \"assertLogs\\|unsupported_level\\|UnsupportedError\" tests/dialects/test_tsql.py | head -8; grep -n \"def validate_all\" -A12 tests/dialects/test_dialect.py | head -30", "description": "Check JSON token, expressions() helper, and test helpers"}
[tool_result] sqlglot/tokens.py:462:        "JSON": TokenType.JSON,
sqlglot/parser.py:1933:    def _match_pair(
sqlglot/generators/oracle.py:126:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
sqlglot/generators/tsql.py:288:    def queryoption_sql(self, expression: exp.QueryOption) -> str:
5:4460-        sqls: t.Collection[str | exp.Expr] | None = None,
15:4470-        expressions = expression.args.get(key or "expressions") if expression else sqls
17:4472-        if not expressions:
20:4475
…[876 chars elided]…
y=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
72-        2. `sql` transpiles to everything in `write`
73-
74-        Args:
75-            sql (str): Main SQL expression
76-            read (dict): Mapping of dialect -> SQL
77-            write (dict): Mapping of dialect -> SQL
78-            pretty (bool): prettify both read and write
79-            identify (bool): quote identifiers in both read and write
80-        """
[assistant] `validate_all` treats unsupported output as an error (the `OPTION` test expects `UnsupportedError`). To test the drop-with-warning behavior I need to see how the suite asserts logged warnings.
[tool_use Bash] {"command": "sed -n 80,100p tests/dialects/test_dialect.py; grep -rn \"assertLogs\" tests/dialects/*.py | head -5; grep -rn \"Unsupported query option\" tests/ | head -3", "description": "Check validate_all error level and warning assertions"}
[tool_result]         """
        expression = self.parse_one(sql)

        for read_dialect, read_sql in (read or {}).items():
            with self.subTest(f"{read_dialect} -> {sql}"):
                self.assertEqual(
                    parse_one(read_sql, read_dialect).sql(
                        self.dialect,
                        unsupported_level=ErrorLevel.IGNORE,
                        pretty=pretty,
                        identify=identify,
                    ),
                    sql,
     
…[294 chars elided]…
dialect, unsupported_level=ErrorLevel.RAISE)
                else:
tests/dialects/test_bigquery.py:2134:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2143:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2151:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2171:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2192:        with self.assertLogs(helper_logger):
[assistant] I have what I need. Plan:

- **Parser:** `_parse_for` accepts `FOR JSON` alongside `FOR XML`, using a `JSON_OPTIONS` table. JSON clauses go under a separate `for_json` arg, so the existing `FOR XML` AST is unchanged.
- **Generator:** `for_modifiers` emits `FOR XML` and `FOR JSON` from their respective args. Other dialects already drop `QueryOption`s with the unsupported warning.

Starting with the parser: the options table first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = dict.fromkeys(\n    (\"AUTO\", \"PATH\", \"INCLUDE_NULL_VALUES\", \"WITHOUT_ARRAY_WRAPPER\"), tuple()\n)\n\n\nOPTIONS_THAT_REQUIRE_EQUAL"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[607 chars elided]…
n            return \"for_\", None\n\n        def _parse_for_option() -> exp.Expr | None:\n            return self.expression(\n                exp.QueryOption(\n                    this=self._parse_var_from_options(options, raise_unmatched=False)\n                    or self._parse_xml_key_value_option()\n                )\n            )\n\n        return key, self._parse_csv(_parse_for_option)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[assistant] Next, the generator: `for_modifiers` now emits each kind from its own arg.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"
…[7 chars elided]…
ew_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_xml = self.expressions(expression, key=\"for_\")\n        for_json = self.expressions(expression, key=\"for_json\")\n        return \"\".join(\n            f\"{self.sep()}FOR {kind}{self.seg(options)}\"\n            for kind, options in ((\"XML\", for_xml), (\"JSON\", for_json))\n            if options\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now I'll re-run the probe on the reported forms and the variants, including the ones that should stay unchanged for `FOR XML`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; cat > /tmp/for_json_probe.sql <<'EOF'\nSELECT * FROM t FOR JSON AUTO\nSELECT * FROM t FOR JSON PATH\nSELECT * FROM t FOR JSON AUTO, ROOT('r')\nSELECT * FROM t FOR JSON PATH, ROOT\nSELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES\nSELECT * FROM t FOR JSON PATH, WITHOUT_ARRAY_WRAPPER\
…[322 chars elided]…
T * FROM t FOR XML RAW('ElementName'), XMLSCHEMA('TargetNameSpaceURI'), ELEMENTS ABSENT\nEOF\n$PY .lithify/harness/scripts/probe_parse.py --read tsql < /tmp/for_json_probe.sql; echo \"tsql exit $?\"; echo ---; $PY .lithify/harness/scripts/probe_parse.py --read tsql --write duckdb < /tmp/for_json_probe.sql 2>&1; echo \"duckdb exit $?\"", "description": "Probe FOR JSON variants in T-SQL and DuckDB"}
[tool_result] OK        SELECT * FROM t FOR JSON AUTO
          SELECT * FROM t FOR JSON AUTO
OK        SELECT * FROM t FOR JSON PATH
          SELECT * FROM t FOR JSON PATH
OK        SELECT * FROM t FOR JSON AUTO, ROOT('r')
          SELECT * FROM t FOR JSON AUTO, ROOT('r')
OK        SELECT * FROM t FOR JSON PATH, ROOT
          SELECT * FROM t FOR JSON PATH, ROOT
OK        SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES
          SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES
OK        SELECT * FROM 
…[2359 chars elided]…
S, WITHOUT_ARRAY_WRAPPER
          SELECT * FROM t
OK        SELECT * FROM t FOR JSON AUTO, ROOT
          SELECT * FROM t
OK        SELECT a.b, c FROM t AS a WHERE x = 1 ORDER BY a.b FOR JSON PATH, ROOT('r')
          SELECT a.b, c FROM t AS a WHERE x = 1 ORDER BY a.b NULLS FIRST
OK        SELECT * FROM t FOR XML PATH, ROOT('r')
          SELECT * FROM t
OK        SELECT * FROM t FOR XML RAW('ElementName'), XMLSCHEMA('TargetNameSpaceURI'), ELEMENTS ABSENT
          SELECT * FROM t
duckdb exit 0
[assistant] All JSON variants now parse and round-trip in T-SQL, and every other dialect drops the clause with the unsupported warning. The `NULLS FIRST` in the DuckDB output comes from the existing ORDER BY handling, not from this change. Next I'll add tests, after confirming the logger name and test imports.
[tool_use Bash] {"command": "grep -n \"getLogger\" sqlglot/generator.py sqlglot/errors.py | head -3; sed -n 1,12p tests/dialects/test_tsql.py; grep -n \"def test_types\" tests/dialects/test_tsql.py", "description": "Check generator logger name and test file imports"}
[tool_result] 1 matches in 1 files:

sqlglot/generator.py:24:logger = logging.getLogger("sqlglot")
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError, UnsupportedError
from sqlglot.optimizer.annotate_types import annotate_types
from tests.dialects.test_dialect import Validator


class TestTSQL(Validator):
    dialect = "tsql"

    def test_tsql(self):
        self.validate_all(
            "WITH x AS (SELECT 1 AS [1]) SELECT TOP 0 * FROM (SELECT * FROM x UNION SELECT * FROM x) AS _l_0 ORDER BY 1",
6 matches in 6 files:

713:0:
752:0:
797:0:
878:0:
919:0:
970:0:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_for_json(self):\n      
…[1034 chars elided]…
},\n        )\n\n        with self.assertLogs(\"sqlglot\") as cm:\n            self.assertEqual(\n                parse_one(\"SELECT * FROM t FOR JSON PATH, ROOT('RootName')\", read=\"tsql\").sql(\n                    \"duckdb\"\n                ),\n                \"SELECT * FROM t\",\n            )\n        self.assertIn(\"Unsupported query option.\", cm.output[0])\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-154051-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] Next I'll run the T-SQL test file with the project's test command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -30", "description": "Run T-SQL dialect test file"}
[tool_result] ........................ [ 44%]
..............................  [100%]
54 passed, 665 subtests passed in 0.29s
[assistant] All 54 T-SQL tests pass. Next I'll run the full suite (the harness's final gate) and the linter on the changed files, in parallel.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m pytest -q -p no:cacheprovider --color=no tests/ > /tmp/full_suite.log 2>&1; echo \"exit $?\" >> /tmp/full_suite.log) & $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py -k for_json -v 2>&1 | grep -i \"for_json\"; ($PY -m ruff --version && $PY -m ruff check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py && $PY -m ruff format --check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py) 2>&1 | tail -8; wait; tail -5 /tmp/full_suite.log", "description": "Run full suite, targeted test, and ruff lint/format check"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
.......... [ 97%]
................ [ 98%]
..............                  [100%]
1108 passed, 18027 subtests passed in 57.14s
exit 0
[assistant] The full suite passes: 1108 tests, exit 0, and ruff is clean. The `-k` check printed nothing, probably because `-q` and `-v` cancel each other, so I'll confirm `test_for_json` was collected and passed.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -p no:cacheprovider --color=no tests/dialects/test_tsql.py -k test_for_json -v 2>&1 | tail -4; git status --short; git diff --stat", "description": "Confirm test_for_json ran and show changed files"}
[tool_result] tests/dialects/test_tsql.py::TestTSQL::test_for_json 
tests/dialects/test_tsql.py::TestTSQL::test_for_json PASSED              [100%]

============= 1 passed, 53 deselected, 9 subtests passed in 0.06s ==============
 M sqlglot/generator.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.pysqlglot/generator.py        |  9 +++++++--
 sqlglot/parsers/tsql.py     | 22 +++++++++++++++-------
 tests/dialects/test_tsql.py | 44 ++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 66 insertions(+), 9 deletions(-)
[assistant] `FOR JSON` now parses and round-trips in T-SQL, and other dialects drop it with the "Unsupported query option." warning, the same as `FOR XML`. The full suite passes (1108 tests, exit 0), and ruff is clean on the changed files. I haven't committed anything.

What changed:

- **`sqlglot/parsers/tsql.py`**: `_parse_for` accepts `FOR JSON` alongside `FOR XML`. A new `JSON_OPTIONS` table covers `AUTO`, `PATH`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. `ROOT` and `ROOT('name')` go through the existing key-value path that `FOR XML` uses.
- **`sqlglot/generator.py`**: `for_modifiers` emits `
…[155 chars elided]…
` still raises "Found multiple" as it would for `FOR XML`.
- **`tests/dialects/test_tsql.py`**: new `test_for_json` covering option forms, pretty output, the DuckDB unsupported error, and the dropped-clause warning.

Decisions for you to check:

- I added a sibling `test_for_json` method rather than putting the cases inside `test_for_xml`.
- Per the harness, I ran the probe with `PYTHONPATH` pointing at the repo and without `-I`. The venv doesn't install `sqlglot`, and `-I` ignores `PYTHONPATH`. The repo is my own working tree, so I judged this safe, but it is a deviation from the memory note.
