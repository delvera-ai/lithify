# trajectory base-1

final message:
T-SQL now parses and round-trips `FOR JSON { AUTO | PATH } [, ROOT [('name')]] [, INCLUDE_NULL_VALUES] [, WITHOUT_ARRAY_WRAPPER]`. Other dialects warn and drop the clause, as they do for `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean. I haven't committed anything.

Before the change, `SELECT a FROM t FOR JSON AUTO` failed with a ParseError, so this was a real gap rather than something already working.

**What changed**
- **`sqlglot/expressions/query.py`:** new `exp.ForJSON` node that wraps the `FOR JSON` options. The XML path's flat list of `QueryOption`s has no way to carry a prefix, so JSON needed a wrapper. The XML AST is unchanged.
- **`sqlglot/parsers/tsql.py`:** a `JSON_OPTIONS` table (AUTO, PATH, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER) and a `FOR JSON` branch in `_parse_for`. `ROOT('name')` goes through the existing key-value option parser that XML uses. I pulled the option-building closure into a `_parse_for_option` helper so both clauses share it.
- **`sqlglot/generator.py`:** `for_modifiers` routes a `ForJSON` wrapper to `forjson_sql`. The base `forjson_sql` emits the "Unsupported query option." warning and returns nothing, which drops the clause.
- **`sqlglot/generators/tsql.py`:** `forjson_sql` emits `FOR JSON` plus the options, inline or pretty-printed.
- **`tests/dialects/test_tsql.py`:** a `test_for_json` covering the option combinations, pretty output, and the duckdb drop.

**Choices to review**
- Unrecognised options in the `FOR JSON` list are accepted as generic key-value options, the same leniency the XML path has. For example, `FOR JSON PATH, FOO` parses rather than erroring. Tightening that would mean rejecting unknown names in the JSON option set.
- I used the existing "Unsupported query option." message for the warning, not a clause-specific one.

## events
[assistant] I'll start by finding how `FOR XML` is handled, and load the syntax-support skill the repo asks for since this is JSON-related.
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/.claude/skills/sqlglot-syntax-support

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

[tool_use Bash] {"command": "grep -rn -i \"for_xml\\|ForXml\\|FOR XML\\|\\\"XML\\\"\" sqlglot/ | head -80; echo ---; grep -rn -i \"for json\\|ForJSON\\|for_json\" sqlglot/ tests/ | head -30", "description": "Search for FOR XML handling and existing FOR JSON references"}
[tool_result] sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/parsers/tsql.py:508:        def _parse_for_xml() -> exp.Expr | None:
sqlglot/parsers/tsql.py:516:        return self._parse_csv(_parse_for_xml)
sqlglot/dialects/tsql.py:184:            "XML": TokenType.XML,
sqlglot/dialects/postgres.py:114:            "XML": TokenType.XML,
---
tests/dialects/test_tsql.py:545:            for json_clause in ("", " NULL ON NULL", " ABSENT ON NULL"):
[assistant] The skill says to check whether the quoted example already works before deciding it's a gap. I'll read the existing `FOR XML` code and probe the current behaviour.
[tool_use Bash] {"command": "sed -n 495,520p sqlglot/parsers/tsql.py; echo ---; sed -n 3085,3115p sqlglot/generator.py; echo ---; grep -rn \"for_xml\\|QueryOption\\|class Option\\|XML\" sqlglot/expressions/query.py | head; echo ---; grep -rn -i \"for xml\" tests/ | head -20; echo ---; grep -rn \"unsupported\\|for_modifiers\" sqlglot/dialects/tsql.py sqlglot/generators/tsql.py | head; echo ---; ls sqlglot/expressi
…[270 chars elided]…
INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER','SELECT a FROM t FOR XML PATH']:\n    try:\n        print(sqlglot.transpile(s, read='tsql', write='tsql'))\n    except Exception as e: print('ERR', e)\n    try:\n        print(sqlglot.transpile(s, read='tsql', write='duckdb'))\n    except Exception as e: print('ERR', e)\n\"", "description": "Inspect FOR XML parser/generator and probe FOR JSON behaviour"}
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
…[3528 chars elided]…
SELECT a FROM t [4mFOR[0m JSON AUTO
ERR Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT a FROM t [4mFOR[0m JSON AUTO
ERR Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT a FROM t [4mFOR[0m JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
ERR Invalid expression / Unexpected token. Line 1, Col: 19.
  SELECT a FROM t [4mFOR[0m JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
['SELECT a FROM t FOR XML PATH']
['SELECT a FROM t']
[assistant] `FOR JSON` fails to parse today, so the requested feature is a real gap. Next I'll read the option tables, the `QueryOption` node and the existing XML tests.
[tool_use Bash] {"command": "grep -n \"XML_OPTIONS\" -A 25 sqlglot/parsers/tsql.py | head -60; echo ---; sed -n 905,925p sqlglot/expressions/query.py; echo ---; sed -n 2070,2090p sqlglot/expressions/query.py; echo ---; grep -n \"for_\\|\\\"options\\\"\" sqlglot/expressions/query.py | head; echo ---; sed -n 685,720p tests/dialects/test_tsql.py; echo ---; grep -n \"def queryoption_sql\\|def xmlkeyvalueoption_sql\\|def xmlnamespace_sql\" -A 8 sqlglot/generator.py; echo ---; grep -n \"def _parse_var_from_options\" -A 25 sqlglot/parser.py", "description": "Read XML option parsing, QueryOption node, and XML tests"}
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
106-    "BINARY": ("BASE64",),
107-}
108-
109-
110-OPTIONS_THAT_REQUIRE_EQUAL = ("MAX_GRANT_PERCENT", "MIN_GRANT_PERCENT", "LABEL")
111-
112-
113-def _build_formatted_time(
114-    exp_class: type[E], full_format_mapping: bool 
…[5651 chars elided]…
       if isinstance(keywords, str):
9154-                keywords = (keywords,)
9155-
9156-            if self._match_text_seq(*keywords):
9157-                option = f"{option} {' '.join(keywords)}"
9158-                break
9159-        else:
9160-            if continuations or continuations is None:
9161-                if raise_unmatched:
9162-                    self.raise_error(f"Unknown option {option}")
9163-
9164-                self._retreat(index)
9165-                return None
[assistant] The XML path hardcodes the `FOR XML` prefix in `for_modifiers`, so JSON needs a way to carry its own prefix. I'll check where `for_` is used before choosing the AST shape.
[tool_use Bash] {"command": "grep -rn \"\\\"for_\\\"\\|for_=\\|_parse_for\\b\\|\\.for_\\|for_modifiers\\|\\\"for_\\\"\" sqlglot/ tests/ | grep -v \"^.*#\" | head -30; echo ---; grep -n \"\\\"for_\\\"\" sqlglot/expressions/query.py; echo ---; grep -rn \"FOR XML\\|for_\" tests/*.py | head -5; git log --oneline -3 -- sqlglot/parsers/tsql.py | cat", "description": "Find all uses of the for_ arg and XML option parsing"}
[tool_result] sqlglot/parser.py:9656:                for_=_parse_overlay_arg("FOR"),
sqlglot/generator.py:3102:            self.for_modifiers(expression),
sqlglot/generator.py:3110:    def for_modifiers(self, expression: exp.Expr) -> str:
sqlglot/generator.py:3111:        for_modifiers = self.expressions(expression, key="for_")
sqlglot/generator.py:3112:        return f"{self.sep()}FOR XML{self.seg(for_modifiers)}" if for_modifiers else ""
sqlglot/generator.py:5546:        for_sql = self.sql(expression, "for_")
sqlglot/parsers/tsql.py:321:        TokenType.FOR: lambda self: ("for_", self._parse_for()),
sqlglot/parsers/tsql.py:504:    def _parse_for(self) -> list[exp.Expr] | None:
sqlglot/expressions/string.py:102:    arg_types = {"this": True, "expression": True, "from_": True, "for_": False}
---
---
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
f7bb6bea8 chore: use collections.abc and built-in types for typing to avoid deprecation (#7329)
ea76ca554 Chore: unpin ruff (#7287)
[tool_use Bash] {"command": "grep -rn \"for_\" sqlglot/expressions/ sqlglot/parser.py | head; echo ---; grep -n \"QUERY_MODIFIER_PARSERS\\|def _parse_query_modifiers\" sqlglot/parser.py | head -5; echo ---; sed -n 5540,5550p sqlglot/generator.py; echo ---; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ne=sqlglot.parse_one('SELECT a FROM t FOR XML PATH, ROOT(\\'r\\')', read='tsql')\nprint(repr(e))\nprint(e.args.get('for_'))\n\" 2>&1 | head -40", "description": "Locate how the for_ modifier is registered on Select"}
[tool_result] sqlglot/expressions/properties.py:266:        "for_or_in": False,
sqlglot/expressions/ddl.py:87:        "for_each": False,
sqlglot/expressions/ddl.py:215:        "for_table": False,
sqlglot/expressions/ddl.py:216:        "for_group": False,
sqlglot/expressions/ddl.py:217:        "for_user": False,
sqlglot/expressions/ddl.py:218:        "for_role": False,
sqlglot/expressions/query.py:1106:    https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#for_system_time_as_of
sqlglot/
…[1045 chars elided]…
=a, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  for_=[
    QueryOption(
      this=XMLKeyValueOption(
        this=Var(this=PATH))),
    QueryOption(
      this=XMLKeyValueOption(
        this=Var(this=ROOT),
        expression=Literal(this='r', is_string=True)))])
[QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=PATH))), QueryOption(
  this=XMLKeyValueOption(
    this=Var(this=ROOT),
    expression=Literal(this='r', is_string=True)))]
[assistant] The `for_` list is a flat list of `QueryOption` nodes and `for_modifiers` hardcodes `FOR XML`, so a JSON clause needs its own wrapper to carry the prefix. Before writing it, I'll confirm the remaining pieces: the `JSON` token, `_match_pair`, the tail of `_parse_var_from_options`, and the tsql generator's base class.
[tool_use Bash] {"command": "sed -n 9165,9175p sqlglot/parser.py; echo ---; grep -n \"    JSON\\b\\|TokenType.JSON\\b\" sqlglot/tokens.py sqlglot/parsers/tsql.py | head -3; echo ---; grep -n \"^class TSQL\\|class Generator\" sqlglot/generators/tsql.py | head -3; grep -n \"^from\\|^import\" sqlglot/parsers/tsql.py | head; echo ---; grep -n \"def queryoption_sql\\|def forjson\\|def for_modifiers\" -B2 sqlglot/generators/*.py | head; echo ---; grep -n \"validate_all\" -A3 tests/dialects/test_tsql.py | sed -n 1,8p", "description": "Check JSON token, option parsing tail, and generator base classes"}
[tool_result]                 return None

        return exp.var(option)

    def _parse_as_command(self, start: Token) -> exp.Command:
        while self._curr:
            self._advance()
        text = self._find_sql(start, self._prev)
        size = len(start.text)
        self._warn_unsupported()
        return exp.Command(this=text[:size], expression=text[size:])
---
sqlglot/tokens.py:462:        "JSON": TokenType.JSON,
---
118:class TSQLGenerator(generator.Generator):
1:from __future__ import annotati
…[718 chars elided]…
ption_sql(self, expression: exp.QueryOption) -> str:
---
11:        self.validate_all(
12-            "WITH x AS (SELECT 1 AS [1]) SELECT TOP 0 * FROM (SELECT * FROM x UNION SELECT * FROM x) AS _l_0 ORDER BY 1",
13-            read={
14-                "": "WITH x AS (SELECT 1) SELECT * FROM x UNION SELECT * FROM x ORDER BY 1 LIMIT 0",
--
89:        self.validate_all(
90-            "CREATE TABLE test_table([ID] [BIGINT] NOT NULL,[EffectiveFrom] [DATETIME2] (3) NOT NULL)",
91-            write={
[assistant] The tsql generator already overrides `queryoption_sql`, so I'll read that and the base `Generator` class's method placement before editing.
[tool_use Bash] {"command": "sed -n 286,300p sqlglot/generators/tsql.py; echo ---; grep -n \"^from\\|^import\" sqlglot/generators/tsql.py | head -5; grep -n \"^class\\|__init__\" sqlglot/expressions/query.py | sed -n 1,3p; grep -rn \"in_depth_xml\\|ForXML\\|ForJSON\" sqlglot | head -3", "description": "Read tsql queryoption override and imports"}
[tool_result]         return self.func(name, expression.this, expression.expression, expression.args.get("style"))

    def queryoption_sql(self, expression: exp.QueryOption) -> str:
        option = self.sql(expression, "this")
        value = self.sql(expression, "expression")
        if value:
            optional_equal_sign = "= " if option in OPTIONS_THAT_REQUIRE_EQUAL else ""
            return f"{option} {optional_equal_sign}{value}"
        return option

    def lateral_op(self, expression: exp.Lateral) -> str:
        cross_apply = expression.args.get("cross_apply")
        if cross_apply is True:
            return "CROSS APPLY"
        if cross_apply is False:
---
1:from __future__ import annotations
3:from functools import reduce
5:from sqlglot import exp, generator, transforms
6:from sqlglot.dialects.dialect import (
18:from sqlglot.helper import seq_get
80:class Selectable(Expr):
96:class DerivedTable(Selectable):
104:class UDTF(DerivedTable):
[assistant] I have what I need. The plan:

- **Node:** add `exp.ForJSON` (holds the JSON options as `QueryOption`s) next to `QueryOption`. It is the wrapper that carries the `FOR JSON` prefix.
- **Parser:** in tsql, add a `JSON_OPTIONS` table and a `FOR JSON` branch in `_parse_for`, reusing the XML option helpers.
- **Generator:** the base `for_modifiers` routes a `ForJSON` wrapper to `forjson_sql`. The base `forjson_sql` warns and drops the clause, as `queryoption_sql` does. The tsql generator overrides it to emit `FOR JSON`.

Starting with the node:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/expressions/query.py", "old_string": "class QueryOption(Expression):\n    arg_types = {\"this\": True, \"expression\": False}\n", "new_string": "class QueryOption(Expression):\n    arg_types = {\"this\": True, \"expression\": False}\n\n\nclass ForJSON(Expression):\n    arg_types = {\"expressions\": True}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/expressions/query.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py", "old_string": "    def for_modifiers(self, expression: exp.Expr) -> str:\n        for_modifiers = self.expressions(expression, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"
…[537 chars elided]…
, key=\"for_\")\n        return f\"{self.sep()}FOR XML{self.seg(for_modifiers)}\" if for_modifiers else \"\"\n\n    def queryoption_sql(self, expression: exp.QueryOption) -> str:\n        self.unsupported(\"Unsupported query option.\")\n        return \"\"\n\n    def forjson_sql(self, expression: exp.ForJSON) -> str:\n        self.unsupported(\"Unsupported query option.\")\n        return \"\"\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py", "old_string": "    def queryoption_sql(self, expression: exp.QueryOption) -> str:\n        option = self.sql(expression, \"this\")", "new_string": "    def forjson_sql(self, expression: exp.ForJSON) -> str:\n        return f\"FOR JSON{self.seg(self.expressions(expression))}\"\n\n    def queryoption_sql(self, expression: exp.QueryOption) -> str:\n        option = self.sql(expression, \"this\")"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/generators/tsql.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    \"BINARY\": (\"BASE64\",),\n}\n", "new_string": "    \"BINARY\": (\"BASE64\",),\n}\n\nJSON_OPTIONS: parser.OPTIONS_TYPE = {\n    \"AUTO\": tuple(),\n    \"PATH\": tuple(),\n    \"INCLUDE_NULL_VALUES\": tuple(),\n    \"WITHOUT_ARRAY_WRAPPER\": tuple(),\n}\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[assistant] Now the parser's `_parse_for`, which adds the `FOR JSON` branch and a shared option helper for both clauses:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py", "old_string": "    def _parse_for(self) -> list[exp.Expr] | None:\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        def _parse_for_xml() -> exp.Expr | None:\n            return s
…[742 chars elided]…
rn [\n                self.expression(\n                    exp.ForJSON(\n                        expressions=self._parse_csv(lambda: self._parse_for_option(JSON_OPTIONS))\n                    )\n                )\n            ]\n\n        if not self._match_pair(TokenType.FOR, TokenType.XML):\n            return None\n\n        return self._parse_csv(lambda: self._parse_for_option(XML_OPTIONS))"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/sqlglot/parsers/tsql.py has been updated successfully.
[assistant] Now I'll probe the spec's forms in T-SQL and in another dialect, including pretty output.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases=['SELECT * FROM t FOR JSON AUTO','SELECT * FROM t FOR JSON PATH','SELECT * FROM t FOR JSON PATH, ROOT',\\\"SELECT * FROM t FOR JSON PATH, ROOT('r')\\\",'SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES','
…[209 chars elided]…
n cases:\n    out=sqlglot.transpile(s, read='tsql', write='tsql')[0]\n    print(out==s, '|', out)\nprint(sqlglot.transpile(cases[-2], read='tsql', write='tsql', pretty=True)[0])\nprint(repr(sqlglot.transpile(cases[2], read='tsql', write='duckdb')[0]))\nprint(repr(sqlglot.transpile(cases[0], read='tsql', write='duckdb')[0]))\n\" 2>&1", "description": "Probe FOR JSON parse and round-trip behaviour"}
[tool_result] Unsupported query option.
Unsupported query option.
True | SELECT * FROM t FOR JSON AUTO
True | SELECT * FROM t FOR JSON PATH
True | SELECT * FROM t FOR JSON PATH, ROOT
True | SELECT * FROM t FOR JSON PATH, ROOT('r')
True | SELECT * FROM t FOR JSON AUTO, INCLUDE_NULL_VALUES
True | SELECT * FROM t FOR JSON PATH, INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
True | SELECT * FROM t FOR JSON PATH, ROOT('r'), INCLUDE_NULL_VALUES, WITHOUT_ARRAY_WRAPPER
True | SELECT * FROM t FOR XML PATH
SELECT
  *
FROM t
FOR JSON
  PATH,
  ROOT('r'),
  INCLUDE_NULL_VALUES,
  WITHOUT_ARRAY_WRAPPER
'SELECT * FROM t'
'SELECT * FROM t'
[assistant] All the spec forms parse and round-trip, pretty-print works, and other dialects drop the clause with the warning. Next I'll add tests next to the existing `FOR XML` test.
[tool_use Bash] {"command": "awk 'NR>=660 && NR<=700 && /def test_/{print NR\": \"$0}' tests/dialects/test_tsql.py", "description": "Find the test method containing FOR XML tests"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -n \"def test_\" tests/dialects/test_tsql.py | awk -F: '$1<700' | tail -2", "description": "Locate enclosing test method name"}
[tool_result] 561:    def test_option(self):
640:    def test_for_xml(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_types(self):", "new_string": "  ELEMENTS XSINIL\"\"\",\n            pretty=True,\n        )\n\n    def test_for_json(self):\n      
…[827 chars elided]…
UES\"\"\",\n            pretty=True,\n        )\n\n        self.validate_all(\n            \"SELECT * FROM t\",\n            read={\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO\",\n            },\n            write={\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO\",\n                \"duckdb\": \"SELECT * FROM t\",\n            },\n        )\n\n    def test_types(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] The `validate_all` call I just wrote is wrong: the `sql` argument is the T-SQL input, so it should be the `FOR JSON` query, with duckdb as the write target. Fixing that:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py", "old_string": "        self.validate_all(\n            \"SELECT * FROM t\",\n            read={\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO\",\n            },\n            write={\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO\",\n                \"duckdb\": \"SELECT * FROM t\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"SELECT * FROM t FOR JSON AUTO\",\n            write={\n                \"tsql\": \"SELECT * FROM t FOR JSON AUTO\",\n                \"duckdb\": \"SELECT * FROM t\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-005920-t-sql-dialect-support-the-for-js/base-1/tests/dialects/test_tsql.py has been updated successfully.
[assistant] Now I'll run the tsql test file, then the full suite with the project's check command from the repo's CLAUDE.md harness.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_tsql.py 2>&1 | tail -15", "description": "Run T-SQL dialect tests"}
[tool_result] ...................................................... [100%]
54 passed, 666 subtests passed in 0.29s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; echo ---; (ruff check sqlglot tests 2>/dev/null || <work>/env-sqlglot/bin/python -m ruff check sqlglot tests) 2>&1 | tail -3; (ruff format --check sqlglot tests 2>/dev/null || <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests) 2>&1 | tail -3", "description": "Run full test suite and lint/format checks"}
[tool_result] ............................................... [ 71%]
.......................................................................................................... [ 81%]
....................... [ 83%]
....................................................................................................................... [ 94%]
....................... [ 96%]
.......................... [ 98%]
...............                 [100%]
1108 passed, 18028 subtests passed in 58.27s
---
All checks passed!
236 files already formatted
[assistant] The full suite passes (1108 tests), and ruff lint and format are clean. The repo also runs mypy in pre-commit, so I'll run it on the changed modules.
[tool_use Bash] {"command": "timeout 300 <work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/tsql.py sqlglot/generators/tsql.py sqlglot/generator.py sqlglot/expressions/query.py 2>&1 | tail -5; git status --short", "description": "Type-check changed modules and show changed files"}
[tool_result] (eval):1: command not found: timeout
 M sqlglot/expressions/query.py
 M sqlglot/generator.py
 M sqlglot/generators/tsql.py
 M sqlglot/parsers/tsql.py
 M tests/dialects/test_tsql.py
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m mypy sqlglot/parsers/tsql.py sqlglot/generators/tsql.py sqlglot/generator.py sqlglot/expressions/query.py 2>&1 | tail -5", "description": "Type-check changed modules with mypy"}
[tool_result] Success: no issues found in 4 source files
[assistant] T-SQL now parses and round-trips `FOR JSON { AUTO | PATH } [, ROOT [('name')]] [, INCLUDE_NULL_VALUES] [, WITHOUT_ARRAY_WRAPPER]`. Other dialects warn and drop the clause, as they do for `FOR XML`. The full suite passes (1108 tests), and ruff and mypy are clean. I haven't committed anything.

Before the change, `SELECT a FROM t FOR JSON AUTO` failed with a ParseError, so this was a real gap rather than something already working.

**What changed**
- **`sqlglot/expressions/query.py`:** new `exp.ForJSON` node that wraps the `FOR JSON` options. The XML path's flat list of `QueryOption`s has no way
…[631 chars elided]…
/tsql.py`:** `forjson_sql` emits `FOR JSON` plus the options, inline or pretty-printed.
- **`tests/dialects/test_tsql.py`:** a `test_for_json` covering the option combinations, pretty output, and the duckdb drop.

**Choices to review**
- Unrecognised options in the `FOR JSON` list are accepted as generic key-value options, the same leniency the XML path has. For example, `FOR JSON PATH, FOO` parses rather than erroring. Tightening that would mean rejecting unknown names in the JSON option set.
- I used the existing "Unsupported query option." message for the warning, not a clause-specific one.
