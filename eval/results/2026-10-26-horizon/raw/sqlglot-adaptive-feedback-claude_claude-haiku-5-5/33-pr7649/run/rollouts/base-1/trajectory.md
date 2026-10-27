# trajectory base-1

final message:
T-SQL now parses and round-trips `FOR JSON`, and other dialects drop the clause with the same warning they give for `FOR XML`. The full suite passes: `SUMMARY: 1108 passed, 18034 subtests passed`, `EXIT: 0`, taken after my last edit.

**What changed**
- **`sqlglot/parsers/tsql.py`**: `FOR` now dispatches to `_parse_for`, which returns `for_json` for `FOR JSON` and `for_` for `FOR XML`. `FOR JSON` requires `AUTO` or `PATH` first, then comma-separated `ROOT [('name')]`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. Unknown options and a dangling comma raise `ParseError`.
- **`sqlglot/generator.py`**: `for_modifiers` emits `FOR JSON` from the `for_json` arg. Non-T-SQL dialects go through the existing `queryoption_sql` path, so they log `Unsupported query option.` and omit the clause.
- **`tests/dialects/test_tsql.py`**: new `test_for_json` covering round-trips, pretty output, the AST shape, error cases, and the DuckDB drop-with-warning case.

**Choices you may want to review**
- `FOR JSON` is stored as a separate `for_json` arg, not folded into `for_`. Folding it in would have meant the generator guessing the mode from option names.
- `ROOT('name')` reuses the existing `XMLKeyValueOption` node, the same shape `FOR XML` uses. The class name says XML, but the node is generic.
- Nothing stops `FOR XML` and `FOR JSON` from both appearing in one query. T-SQL rejects that; I didn't add a check.

I did not commit anything.

## events
[assistant] I'll start by finding how `FOR XML` is handled today, since the JSON clause should mirror it.
[tool_use Bash] {"command": "grep -rn \"ForXml\\|FOR XML\\|FOR_XML\\|\\\"XML\\\"\" sqlglot/ --include=*.py | head -50; ls .lithify/harness 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -30", "description": "Locate FOR XML handling across sqlglot"}
[tool_result] (eval):1: no matches found: --include=*.py
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "cat .lithify/memory.md; echo ----; cat .lithify/tool_guidance.md | head -5; echo ----; grep -rn \"XML\" sqlglot/ --include='*.py' | grep -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\\|for xml\" | head -40", "description": "Read project memory and search for FOR XML code"}
[tool_result] cat: .lithify/memory.md: No such file or directory
----
cat: .lithify/tool_guidance.md: No such file or directory
----
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/dialects/tsql.py:184:            "XML": TokenType.XML,
sqlglot/dialects/postgres.py:114:            "XML": TokenType.XML,
[tool_use Bash] {"command": "sed -n 3095,3120p sqlglot/generator.py; echo ----; grep -rn \"for_xml\\|ForXml\\|_parse_for\\b\\|\\\"FOR\\\"\" sqlglot/ | head -40; grep -rn \"for_xml\\|FOR XML\" tests/ | head -30", "description": "Show FOR XML generator and find related parser code"}
[tool_result]             self.sql(expression, "group"),
            self.sql(expression, "having"),
            *[gen(self, expression) for gen in self.AFTER_HAVING_MODIFIER_TRANSFORMS.values()],
            self.sql(expression, "order"),
            *self.offset_limit_modifiers(expression, isinstance(limit, exp.Fetch), limit),
            *self.after_limit_modifiers(expression),
            self.options_modifier(expression),
            self.for_modifiers(expression),
            sep="",
        )

    def 
…[2961 chars elided]…
lse None
sqlglot/parsers/teradata.py:150:        self._match_text_seq("FOR")
tests/dialects/test_tsql.py:640:    def test_for_xml(self):
tests/dialects/test_tsql.py:698:            with self.subTest(f"Testing FOR XML option: {xml_option}"):
tests/dialects/test_tsql.py:699:                self.validate_identity(f"SELECT * FROM t FOR XML {xml_option}")
tests/dialects/test_tsql.py:702:            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
tests/dialects/test_tsql.py:706:FOR XML
[tool_use Bash] {"command": "sed -n 495,520p sqlglot/parsers/tsql.py; echo ----; sed -n 310,330p sqlglot/parsers/tsql.py; echo ----; grep -n \"class QueryOption\\|class Var\\b\\|class Var(\" -A6 sqlglot/expressions/*.py | head -30; echo ----; sed -n 635,715p tests/dialects/test_tsql.py; echo ----; grep -rn \"\\\"for_\\\"\\|for_=\\|for_\\b\" sqlglot/expressions/*.py | head", "description": "Read T-SQL FOR XML parser and tests"}
[tool_result]     def _parse_xml_key_value_option(self) -> exp.XMLKeyValueOption:
        this = self._parse_primary_or_var()
        if self._match(TokenType.L_PAREN, advance=False):
            expression = self._parse_wrapped(self._parse_string)
        else:
            expression = None

        return exp.XMLKeyValueOption(this=this, expression=expression)

    def _parse_for(self) -> list[exp.Expr] | None:
        if not self._match_pair(TokenType.FOR, TokenType.XML):
            return None

        d
…[5184 chars elided]…
_option}")

        self.validate_identity(
            "SELECT * FROM t FOR XML PATH, BINARY BASE64, ELEMENTS XSINIL",
            """SELECT
  *
FROM t
FOR XML
  PATH,
  BINARY BASE64,
  ELEMENTS XSINIL""",
            pretty=True,
        )

    def test_types(self):
        self.validate_identity("CAST(x AS XML)")
        self.validate_identity("CAST(x AS UNIQUEIDENTIFIER)")
----
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
[assistant] Next, the XML option constants, the T-SQL generator's handling of `QueryOption`, and what other dialects currently do with `FOR XML`.
[tool_use Bash] {"command": "grep -n \"XML_OPTIONS\" -A12 sqlglot/parsers/tsql.py | head -30; grep -n \"_parse_var_from_options\" -A20 sqlglot/parser.py | head -30; echo ----; grep -rn \"queryoption\\|QueryOption\\|for_modifiers\\|for_\" sqlglot/generators/tsql.py sqlglot/generator.py sqlglot/generators/*.py | head; echo ----; PYTHONPATH=. ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql
…[144 chars elided]…
4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['duckdb','mysql']:\n    print(d, sqlglot.transpile('SELECT * FROM t FOR XML PATH', read='tsql', write=d))\nprint(repr(sqlglot.parse_one('SELECT * FROM t FOR XML PATH', read='tsql').args.get('for_')))\n\" 2>&1 | tail -20", "description": "Inspect XML options, generator, and cross-dialect FOR XML output"}
[tool_result] 93:XML_OPTIONS: parser.OPTIONS_TYPE = {
94-    **dict.fromkeys(
95-        (
96-            "AUTO",
97-            "EXPLICIT",
98-            "TYPE",
99-        ),
100-        tuple(),
101-    ),
102-    "ELEMENTS": (
103-        "XSINIL",
104-        "ABSENT",
105-    ),
--
511:                    this=self._parse_var_from_options(XML_OPTIONS, raise_unmatched=False)
512-                    or self._parse_xml_key_value_option()
513-                )
514-            )
515-
516-        return self
…[2513 chars elided]…
es_or_default}"
sqlglot/generator.py:2192:        for_or_in = expression.args.get("for_or_in")
sqlglot/generator.py:2193:        for_or_in = f" {for_or_in}" if for_or_in else ""
----
(eval):1: no such file or directory: ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/../../../../../../..<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/ 2>&1 | head; which python3; python3 -c \"import sqlglot,sys;print(sqlglot.__file__)\" 2>&1 | tail -1; sed -n 285,300p sqlglot/generators/tsql.py; sed -n 93,120p sqlglot/parsers/tsql.py", "description": "Locate Python env and read T-SQL option tables"}
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
<work>/env-sqlglot/bin/python3
~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/__init__.py
        name = "TRY_CONVERT" if expression.args.get("safe") else "CONVERT"
        return self.func(n
…[756 chars elided]…
         "TYPE",
        ),
        tuple(),
    ),
    "ELEMENTS": (
        "XSINIL",
        "ABSENT",
    ),
    "BINARY": ("BASE64",),
}


OPTIONS_THAT_REQUIRE_EQUAL = ("MAX_GRANT_PERCENT", "MIN_GRANT_PERCENT", "LABEL")


def _build_formatted_time(
    exp_class: type[E], full_format_mapping: bool | None = None
) -> t.Callable[[list], E]:
    def _builder(args: list) -> E:
        fmt = seq_get(args, 0)
        if isinstance(fmt, exp.Expr):
            from sqlglot.dialects.tsql import TSQL
[assistant] Now a probe of current behaviour: `FOR XML` in T-SQL, and what other dialects emit for it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot.errors import ErrorLevel\ns='SELECT * FROM t FOR XML PATH'\nprint(repr(sqlglot.parse_one(s, read='tsql').args.get('for_')))\nfor d in ['duckdb','mysql','spark']:\n    print(d, repr(sqlglot.transpile(s, read='tsql', write=d)))\nfor s in ['SELECT * FROM t FOR JSON PATH','SELECT * FROM t FOR JSON AUTO, ROOT, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER']:\n  try: print(repr(sqlglot.transpile(s, read='tsql', write='tsql')))\n  except Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\" 2>&1 | tail -20", "description": "Probe current FOR XML and FOR JSON behaviour"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH)))]
duckdb ['SELECT * FROM t']
mysql ['SELECT * FROM t']
spark ['SELECT * FROM t']
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT * FROM t [4mFOR[0m JSON PATH
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT * FROM t [4mFOR[0m JSON AUTO, ROOT, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
[assistant] Current state: T-SQL rejects `FOR JSON` outright, and other dialects silently drop `FOR XML` with an "Unsupported query option." warning. Next I'll read the pieces the new clause touches: the `Select` arg declaration, the modifier loop, the `expressions()` helper, and `_parse_var_from_options`.
[tool_use Bash] {"command": "grep -n '\"for_\"' sqlglot/expressions/*.py sqlglot/*.py sqlglot/*/*.py; echo ----; grep -n \"QUERY_MODIFIER_PARSERS\" -A3 sqlglot/parser.py | grep -n \"for\\|\\.items\\|for key\" ; grep -n \"def _parse_query_modifiers\" -A40 sqlglot/parser.py | grep -n \"set\\|for \" | head; echo ----; grep -n \"def _parse_var_from_options\" -A30 sqlglot/parser.py; echo ----; grep -n \"    def expressions\" -A25 sqlglot/generator.py | head -40; echo ----; grep -n \"JSON\" sqlglot/tokens.py | head -5; ls .lithify/skills; ", "description": "Read Select args, modifier loop, and option helpers"}
[tool_result ERROR] Exit code 1
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
-
…[2407 chars elided]…
ons:
4473-            return ""
4474-
4475-        if flat:
4476-            return sep.join(sql for sql in (self.sql(e) for e in expressions) if sql)
4477-
4478-        num_sqls = len(expressions)
4479-        result_sqls = []
4480-
4481-        for i, e in enumerate(expressions):
----
462:        "JSON": TokenType.JSON,
463:        "JSONB": TokenType.JSONB,
545:    # In tokenizers like JSONPath, dots are always key separators, never decimal points
ls: .lithify/skills: No such file or directory
[assistant] `Select` doesn't declare `for_` in its `arg_types`, so a new query-modifier key needs no class change. Both `FOR XML` and `FOR JSON` begin with the `FOR` token, though, so I need to see how the modifier loop unpacks a parser's result before deciding how to route them.
[tool_use Bash] {"command": "sed -n 4112,4130p sqlglot/parser.py; echo ----; grep -n \"QUERY_MODIFIER_PARSERS: \" -A3 sqlglot/parser.py; grep -n \"class Select(\" -A12 sqlglot/expressions/query.py | grep -n \"options\\|for\" ; echo ----; sed -n 4481,4500p sqlglot/generator.py; echo ----; grep -n \"class QueryOption\\|XMLKeyValueOption\" -B2 -A3 sqlglot/expressions/*.py | head -20; grep -n \"XMLKeyValueOption\\|_parse_xml_key\" sqlglot/parsers/tsql.py", "description": "Inspect modifier dispatch and option expression classes"}
[tool_result]                 this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
                    key, expression = parser(self)

                    if expression:
                        if this.args.get(key):
                            self.raise_error(
                                f"
…[1805 chars elided]…
ot/expressions/query.py-2075-
sqlglot/expressions/query.py-2076-
sqlglot/expressions/query.py:2077:class XMLKeyValueOption(Expression):
sqlglot/expressions/query.py-2078-    arg_types = {"this": True, "expression": False}
sqlglot/expressions/query.py-2079-
sqlglot/expressions/query.py-2080-
495:    def _parse_xml_key_value_option(self) -> exp.XMLKeyValueOption:
502:        return exp.XMLKeyValueOption(this=this, expression=expression)
512:                    or self._parse_xml_key_value_option()
[assistant] The loop unpacks a `(key, value)` tuple from the `FOR` token's parser, and `FOR XML` and `FOR JSON` share that token. So the parser has to pick the key at runtime. Before writing code I need three more facts: how `_match_pair` behaves on a miss, how the test helpers assert unsupported-option warnings, and the harness's run instructions.
[tool_use Bash] {"command": "grep -n \"def _match_pair\" -A10 sqlglot/parser.py; echo ----; grep -n \"def validate_all\" -A12 tests/dialects/test_dialect.py | head -30; grep -n \"unsupported_level\\|assertLogs\" tests/dialects/test_tsql.py | head -8; echo ----; grep -n \"OPTION(LABEL\" -B3 -A12 tests/dialects/test_tsql.py | head -30; echo ----; cat .lithify/harness/memory.md | head -20; echo ----; grep -n \"def unsupported\" -A8 sqlglot/generator.py | head -12", "description": "Read token-pair matcher, test helpers, and harness notes"}
[tool_result] 1933:    def _match_pair(
1934-        self, token_type_a: TokenType, token_type_b: TokenType, advance: bool = True
1935-    ) -> bool:
1936-        if self._curr.token_type == token_type_a and self._next.token_type == token_type_b:
1937-            if advance:
1938-                self._advance(2)
1939-            return True
1940-        return False
1941-
1942-    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1943-        if self._curr.token_type != TokenType
…[2054 chars elided]…
   *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
34-    Decorator that can be used to mark certain args of an `Expr` subclass as unsupported.
35-    It expects a sequence of argument names or pairs of the form (argument_name, diagnostic_msg).
36-    """
37-    diagnostic_by_arg: dict[str, str | None] = {}
38-    for arg in args:
--
971:    def unsupported(self, message: str) -> None:
972-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
[assistant] I have what I need. The plan:

- **Parser:** `TokenType.FOR` dispatches to one `_parse_for` that returns `("for_json", …)` for `FOR JSON` and `("for_", …)` for `FOR XML`. The `FOR JSON` items reuse the `QueryOption` shape that `FOR XML` uses, with `ROOT('name')` as an `XMLKeyValueOption`.
- **Generator:** `for_modifiers` in the base generator emits `FOR JSON` from a `for_json` arg. Non-T-SQL dialects hit the existing `queryoption_sql` warning and drop the clause.

Starting with the parser.
[tool_use Bash] {"command": "grep -n \"^OPTIONS_THAT_REQUIRE_EQUAL\" sqlglot/parsers/tsql.py; grep -rn \"assertLogs\" tests/dialects/*.py | head -3", "description": "Find insertion point and warning-assert pattern in tests"}
[tool_result] 110:OPTIONS_THAT_REQUIRE_EQUAL = ("MAX_GRANT_PERCENT", "MIN_GRANT_PERCENT", "LABEL")
tests/dialects/test_clickhouse.py:1770:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2134:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2143:        with self.assertLogs(helper_logger) as cm:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "OPTIONS_THAT_REQUIRE_EQUAL = (\"MAX_GRANT_PERCENT\", \"MIN_GRANT_PERCENT\", \"LABEL\")", "new_string": "JSON_MODES: parser.OPTIONS_TYPE = {\n    \"AUTO\": tuple(),\n    \"PATH\": tuple(),\n}\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = {\n    \"ROOT\": tuple(),\n    \"INCLUDE_NULL_VALUES\": tuple(),\n    \"WITHOUT_ARRAY_WRAPPER\": tuple(),\n}\n\n\nOPTIONS_THAT_REQUIRE_EQUAL = (\"MAX_GRANT_PERCENT\", \"MIN_GRANT_PERCENT\", \"LABEL\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[assistant] Next, the dispatch entry and `_parse_for`, which now chooses between the two clauses.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "        TokenType.FOR: lambda self: (\"for_\", self._parse_for()),", "new_string": "        TokenType.FOR: lambda self: self._parse_for(),"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[1397 chars elided]…
ected a FOR JSON option\")\n                break\n\n            if option.name == \"ROOT\" and self._match(TokenType.L_PAREN, advance=False):\n                option = exp.XMLKeyValueOption(\n                    this=option, expression=self._parse_wrapped(self._parse_string)\n                )\n\n            options.append(self.expression(exp.QueryOption(this=option)))\n\n        return options"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[assistant] Now the base generator. `for_modifiers` gets a `FOR JSON` branch, and non-T-SQL dialects drop it through the existing `queryoption_sql` warning.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"", "new_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_xml = self.expressions(expression, key=\"for_\")\n        if for_xml:\n            return f\"{self.sep()}FOR XML{self.seg(for_xml)}\"\n\n        for_json = self.expressions(expression, key=\"for_json\")\n        return f\"{self.sep()}FOR JSON{self.seg(for_json)}\" if for_json else \"\""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a probe: round-trips, the AST shape, pretty output, and what other dialects emit.
[tool_use Bash] {"command": "mkdir -p /tmp/fj && cat > /tmp/fj/probe.py <<'EOF'\nimport logging\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.errors import ErrorLevel\n\ncases = [\n    \"SELECT * FROM t FOR JSON AUTO\",\n    \"SELECT * FROM t FOR JSON PATH\",\n    \"SELECT * FROM t FOR JSON PATH, ROOT\",\n    \"SELECT * FROM t FOR JSON PATH, ROOT('name')\",\n    \"SELECT * FROM t FOR JSON AUTO, INCLUDE_N
…[1232 chars elided]…
(e).splitlines()[0])\nEOF\ncd ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1 && PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/fj/probe.py 2>&1", "description": "Probe FOR JSON round-trips and cross-dialect output"}
[tool_result] Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
Unsupported query option.
OK  SELECT * FROM t FOR JSON AUTO -> SELECT * FROM t FOR JSON AUTO
OK  SELECT * FROM t FOR JSON PATH -> SELECT * FROM t FOR JSON PATH
OK  SELECT * FROM t FOR JSON PATH, ROOT -> SELECT * FROM t FOR JSON PATH, ROOT
OK  SELECT * FROM t FOR JSON PATH, ROOT('name') -> SELECT * FROM t FOR JSON PATH, ROOT('name')
OK  SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES -> SELE
…[799 chars elided]…
db ['SELECT * FROM t']
mysql ['SELECT * FROM t']
spark ['SELECT * FROM t']
databricks ['SELECT * FROM t']
postgres ['SELECT * FROM t']
ERR SELECT * FROM t FOR JSON :: ParseError Expected AUTO or PATH after FOR JSON. Line 1, Col: 24.
ERR SELECT * FROM t FOR JSON FOO :: ParseError Unknown option FOO. Line 1, Col: 28.
ERR SELECT * FROM t FOR JSON PATH, FOO :: ParseError Unknown option FOO. Line 1, Col: 34.
ERR SELECT * FROM t FOR JSON PATH, :: ParseError Expected a FOR JSON option. Line 1, Col: 30.
[assistant] The parser and generator behave as intended. Round-trips match, `ROOT('name')` gets the same node shape as the XML sibling, and the four non-T-SQL dialects each drop the clause and log one warning. The five `Unsupported query option.` lines are that warning, emitted once per cross-dialect probe. Before writing tests, I'll check how existing tests assert on logged warnings.
[tool_use Bash] {"command": "sed -n 2128,2150p tests/dialects/test_bigquery.py; grep -n \"helper_logger =\" tests/dialects/test_bigquery.py | head -2; grep -n \"^from\\|^import\" tests/dialects/test_tsql.py", "description": "Read existing warning-assertion test pattern"}
[tool_result]             transpile("SELECT * FROM UNNEST(x) AS x(y)", read="bigquery")

        with self.assertRaises(ParseError):
            transpile("DATE_ADD(x, day)", read="bigquery")

    def test_warnings(self):
        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "WITH cte(c) AS (SELECT * FROM t) SELECT * FROM cte",
                "WITH cte AS (SELECT * FROM t) SELECT * FROM cte",
            )

            self.assertIn("Can't push down CTE column
…[123 chars elided]…
tput[1])

        with self.assertLogs(helper_logger) as cm:
            self.validate_identity(
                "SELECT * FROM t AS t(c1, c2)",
                "SELECT * FROM t AS t",
            )

            self.assertIn("Named columns are not supported in table alias.", cm.output[0])

1:from sqlglot import exp, parse_one
2:from sqlglot.errors import ParseError, UnsupportedError
3:from sqlglot.optimizer.annotate_types import annotate_types
4:from tests.dialects.test_dialect import Validator
[tool_use Bash] {"command": "grep -n \"helper_logger\" tests/dialects/test_bigquery.py | head -2; grep -n \"helper_logger\" tests/dialects/test_dialect.py | head -3; grep -n \"    def test_types\" tests/dialects/test_tsql.py", "description": "Find helper logger name and insertion point in tsql tests"}
[tool_result] 15:from sqlglot.helper import logger as helper_logger
2134:        with self.assertLogs(helper_logger) as cm:
713:    def test_types(self):
752:    def test_types_ints(self):
797:    def test_types_decimals(self):
878:    def test_types_string(self):
919:    def test_types_date(self):
970:    def test_types_bin(self):
[assistant] I'll add a `test_for_json` next to `test_for_xml`. It covers round-trips, the pretty layout, the AST shape, the non-T-SQL drop-with-warning path, and the malformed-input errors.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "    def test_types(self):\n        self.validate_identity(\"CAST(x AS XML)\")", "new_string": "    def test_for_json(self):\n        json_possible_options = [\n            \"AUTO\",\n            \"AUTO, ROOT\"
…[1663 chars elided]…
 read=\"tsql\")\n\n        with self.assertLogs(helper_logger) as cm:\n            self.assertEqual(\n                parse_one(\"SELECT * FROM t FOR JSON PATH\", read=\"tsql\").sql(\"duckdb\"),\n                \"SELECT * FROM t\",\n            )\n\n        self.assertIn(\"Unsupported query option.\", cm.output[0])\n\n    def test_types(self):\n        self.validate_identity(\"CAST(x AS XML)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] The new test uses `helper_logger`, so I need that import in `test_tsql.py`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "from sqlglot.errors import ParseError, UnsupportedError\nfrom sqlglot.optimizer.annotate_types import annotate_types", "new_string": "from sqlglot.errors import ParseError, UnsupportedError\nfrom sqlglot.helper import logger as helper_logger\nfrom sqlglot.optimizer.annotate_types import annotate_types"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-092138-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -15", "description": "Run the T-SQL dialect test file"}
[tool_result] ...................... [ 40%]
................................                                                                   [100%]
54 passed, 672 subtests passed in 0.28s
[assistant] The T-SQL file passes (54 tests). Next I'll run the linter on the changed files, as its own call, then the full suite via the harness script.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff --version || $PY/python -m ruff --version) 2>&1 | tail -1; $PY/ruff check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py 2>&1 | tail -3; $PY/ruff format --check sqlglot/parsers/tsql.py sqlglot/generator.py tests/dialects/test_tsql.py 2>&1 | tail -3", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-14:10:29 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  34213       00:19 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-d567ee3524.log
ELAPSED: 496s
SUMMARY: 1108 passed, 18034 subtests passed in 63.75s (0:01:03)
EXIT: 0
[assistant] T-SQL now parses and round-trips `FOR JSON`, and other dialects drop the clause with the same warning they give for `FOR XML`. The full suite passes: `SUMMARY: 1108 passed, 18034 subtests passed`, `EXIT: 0`, taken after my last edit.

**What changed**
- **`sqlglot/parsers/tsql.py`**: `FOR` now dispatches to `_parse_for`, which returns `for_json` for `FOR JSON` and `for_` for `FOR XML`. `FOR JSON` requires `AUTO` or `PATH` first, then comma-separated `ROOT [('name')]`, `INCLUDE_NULL_VALUES` and `WITHOUT_ARRAY_WRAPPER`. Unknown options and a dangling comma raise `ParseError`.
- **`sqlglot/genera
…[241 chars elided]…
st_for_json` covering round-trips, pretty output, the AST shape, error cases, and the DuckDB drop-with-warning case.

**Choices you may want to review**
- `FOR JSON` is stored as a separate `for_json` arg, not folded into `for_`. Folding it in would have meant the generator guessing the mode from option names.
- `ROOT('name')` reuses the existing `XMLKeyValueOption` node, the same shape `FOR XML` uses. The class name says XML, but the node is generic.
- Nothing stops `FOR XML` and `FOR JSON` from both appearing in one query. T-SQL rejects that; I didn't add a check.

I did not commit anything.
