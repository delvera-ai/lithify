# trajectory base-1

final message:
The Postgres `@?` operator now tokenizes, parses into a dedicated `JSONBPathExists` expression, and generates back as `@?`. The full test suite passes (1121 tests), and the example from your request round-trips unchanged.

Changes, following the pattern the existing `?|`, `?&`, and `#-` operators use:

- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: `"@?"` maps to `AT_QMARK` in the postgres tokenizer.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Binary, Func)` expression.
- **`sqlglot/parser.py`**: `AT_QMARK` is parsed as a binary range operator.
- **`sqlglot/generator.py`**: `JSONBPathExists` generates `@?`.
- **`tests/dialects/test_postgres.py`**: identity tests for `a @? b` and the full `WHERE doc @? '$.a[*] ? (@ > 2)'` query.

Decisions for you to check:
- **Base dialect, not postgres-only.** The parser and generator entries live in the base classes, as the sibling JSONB operators do. Other dialects therefore also emit `@?` for this expression, including DuckDB, which has no such operator. If you want the output to be postgres-only, the generator entry should move into the postgres generator.
- **Not run against a live Postgres.** The project's guidance asks that dialect tests be checked against the real database, but none is available here, so the tests only check sqlglot's own round-trip behaviour.

## events
[assistant] I'll start by checking how the existing JSONB operators are tokenized and parsed in the Postgres dialect.
[tool_use Bash] {"command": "rtk grep -n \"@@\\|DAT_AT\\|JSONB_CONTAINS\\|ARROW_CONTAINS\\|ATAT\\|JSONBContains\\|JSONBExists\\|JSONB_EXISTS\\|DAT_QUESTION\\|PLACEHOLDER\\|QMARK\" sqlglot/dialects/postgres.py sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -60", "description": "Search JSONB operator handling across core files"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "rtk grep -n \"JSONB\\|jsonb\" sqlglot/dialects/postgres.py | head -60; rtk grep -n \"class JSONB\\|class .*JSONPath\\|class JSONBExists\\|class JSONBContains\" sqlglot/expressions.py", "description": "Find JSONB handling in postgres dialect and expressions"}
[tool_result ERROR] Exit code 127
(eval):1: command not found: rtk
(eval):1: command not found: rtk
[assistant] The `rtk` wrapper isn't installed here, so I'll use plain `grep`.
[tool_use Bash] {"command": "grep -n \"@@\\|JSONB_CONTAINS\\|ARROW_CONTAINS\\|ATAT\\|DAT_\\|JSONBExists\\|JSONBContains\\|JSONB_EXISTS\\|QMARK\\|JSONB\" sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80; echo ---; grep -n \"JSONB\\|jsonb\\|@\" sqlglot/dialects/postgres.py | head -80", "description": "Search JSONB and operator tokens in core and postgres files"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/tokens.py:241:        "??": TokenType.DQMARK,
sqlglot/tokens.py:464:        "JSONB": TokenType.JSONB,
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
sqlglot/generator.py:3401:    
…[309 chars elided]…
ression=key)
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
sqlglot/parser.py:6058:            elif self._match(TokenType.DQMARK):
---
77:            "@@": TokenType.DAT,
78:            "@>": TokenType.AT_GT,
79:            "<@": TokenType.LT_AT,
[tool_use Bash] {"command": "sed -n 60,110p sqlglot/dialects/postgres.py; echo ---; grep -n \"AT_GT\\|LT_AT\\|DAT\\b\\|QMARK_AMP\\|HASH_DASH\\|QMARK_PIPE\\|HASH_ARROW\\|DQMARK\\|PLACEHOLDER\" sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/*.py | head -60; echo ---; grep -rn \"class JSONBContains\\b\\|class JSONBContains(\\|class JSONBContainsAllTopKeys\\|class JSONBDeleteAtPath\\|class ArrayContains\\|class JSONBExists\\|class JSONBContainsAnyTopKeys\\|class JSONBBContains\" sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null", "description": "Inspect postgres tokenizer and operator definitions"}
[tool_result]         "yyyy": "%Y",  # 2015
        "YYYY": "%Y",  # 2015
    }

    class Tokenizer(tokens.Tokenizer):
        BIT_STRINGS = [("b'", "'"), ("B'", "'")]
        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
        BYTE_STRINGS = [("e'", "'"), ("E'", "'")]
        BYTE_STRING_ESCAPES = ["'", "\\"]
        HEREDOC_STRINGS = ["$"]

        HEREDOC_TAG_IS_IDENTIFIER = True
        HEREDOC_STRING_ALTERNATIVE = TokenType.PARAMETER

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
          
…[3866 chars elided]…
inary, Func):
sqlglot/expressions/array.py:113:class ArrayContainsAll(Expression, Binary, Func):
sqlglot/expressions/json.py:49:class JSONBContains(Expression, Binary, Func):
sqlglot/expressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:57:class JSONBContainsAnyTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:61:class JSONBDeleteAtPath(Expression, Binary, Func):
sqlglot/expressions/json.py:65:class JSONBExists(Expression, Func):
[assistant] Postgres already maps several JSONB operators through `KEYWORDS`, binary range parsers, and a generator entry. Next I'll check the expression definitions, how `@` is tokenized today, and whether `@?` is already a known token.
[tool_use Bash] {"command": "sed -n 40,75p sqlglot/expressions/json.py; echo ---; grep -n '\"@\"\\|PARAMETER\\|SINGLE_TOKENS' sqlglot/tokens.py | head; echo ---; grep -rn \"JSONBContains\\b\\|JSONBExists\\|QMARK_AMP\\|HASH_DASH\\|AT_GT\" sqlglot/ --include=*.py | grep -v \"^sqlglot/expressions/json.py\"; echo ---; grep -rn \"@?\" tests/ | head", "description": "Inspect JSON expression classes and existing usages"}
[tool_result]     _sql_names = ["JSON_ARRAY_CONTAINS"]


class JSONArrayInsert(Expression, Func):
    arg_types = {"this": True, "expressions": True}
    is_var_len_args = True
    _sql_names = ["JSON_ARRAY_INSERT"]


class JSONBContains(Expression, Binary, Func):
    _sql_names = ["JSONB_CONTAINS"]


class JSONBContainsAllTopKeys(Expression, Binary, Func):
    pass


class JSONBContainsAnyTopKeys(Expression, Binary, Func):
    pass


class JSONBDeleteAtPath(Expression, Binary, Func):
    pass


class JSONBEx
…[279 chars elided]…
ion": True, "json_type": False}
---
71:    SINGLE_TOKENS: t.ClassVar[dict[str, TokenType]]
73:    VAR_SINGLE_TOKENS: t.ClassVar[set[str]]
131:            if " " in key or any(single in key for single in cls.SINGLE_TOKENS)
136:    SINGLE_TOKENS = {
162:        "@": TokenType.PARAMETER,
180:    VAR_SINGLE_TOKENS: t.ClassVar[set[str]] = set()
566:            single_tokens=self.SINGLE_TOKENS,
584:            var_single_tokens=self.VAR_SINGLE_TOKENS,
---
(eval):1: no matches found: --include=*.py
---
[assistant] The `--include` flag broke under zsh globbing, so I'll rerun that search quoted. I also want the generator entries around line 204.
[tool_use Bash] {"command": "grep -rn \"JSONBContains\\|JSONBExists\\|QMARK_AMP\\|HASH_DASH\\|JSONBContainsAll\\|JSONBDeleteAtPath\" sqlglot/ tests/ | grep -v \"expressions/json.py\"; echo ---; sed -n 196,210p sqlglot/generator.py; echo ---; grep -n \"def binary\\|def jsonpath\\|JSONPath\" sqlglot/generator.py | head -20; echo ---; grep -rn \"@?\" tests/dialects/test_postgres.py | head -5; grep -n \"?&\\|?|\\|#-\" tests/dialects/test_postgres.py | head", "description": "Locate JSONB operator usages across sqlglot and tests"}
[tool_result] sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/tokenizer_core.py:82:    HASH_DASH = auto()
sqlglot/parser.py:1037:            exp.JSONBContains(this=this, expression=key)
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
sqlglot/generat
…[3272 chars elided]…
 "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
1047:            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
1048:            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
1051:        self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
1053:            """SELECT '["a", {"b":1}]'::jsonb #- '{1,b}'""",
1054:            """SELECT CAST('["a", {"b":1}]' AS JSONB) #- '{1,b}'""",
[assistant] The repo has been split into `parsers/`, `generators/`, and `expressions/` packages, so I'll check the current locations of the postgres parser and generator. I also need the existing test block and any existing path-exists expression to avoid a name clash.
[tool_use Bash] {"command": "grep -rni \"path_exists\\|PathExists\\|jsonpath\" sqlglot/expressions/*.py | head; echo ---; sed -n 1030,1062p tests/dialects/test_postgres.py; echo ---; sed -n 1185,1205p sqlglot/parser.py; echo ---; sed -n 315,325p sqlglot/parsers/postgres.py; echo ---; sed -n 320,330p sqlglot/generators/postgres.py; echo ---; grep -n \"RANGE_PARSERS\\|class Parser\\|ARRAY_CONTAINS\\|_parse_jsonb\" sqlglot/parsers/postgres.py | head -20; echo ---; git -C . log --oneline -1; git status --short", "description": "Review tests, range parser wiring, and postgres parser layout"}
[tool_result] sqlglot/expressions/query.py:1969:class JSONPath(Expression):
sqlglot/expressions/query.py:1978:class JSONPathPart(Expression):
sqlglot/expressions/query.py:1982:class JSONPathFilter(JSONPathPart):
sqlglot/expressions/query.py:1986:class JSONPathKey(JSONPathPart):
sqlglot/expressions/query.py:1990:class JSONPathRecursive(JSONPathPart):
sqlglot/expressions/query.py:1994:class JSONPathRoot(JSONPathPart):
sqlglot/expressions/query.py:1998:class JSONPathScript(JSONPathPart):
sqlglot/expressions/quer
…[3768 chars elided]…
.binary(e, "?"),
        exp.ParseJSON: lambda self, e: self.sql(exp.cast(e.this, exp.DType.JSON)),
        exp.JSONPathKey: json_path_key_only_name,
        exp.JSONPathRoot: lambda *_: "",
        exp.JSONPathSubscript: lambda self, e: self.json_path_part(e.this),
---
159:        "JSONB_EXISTS": lambda self: self._parse_jsonb_exists(),
171:    RANGE_PARSERS = {
172:        **parser.Parser.RANGE_PARSERS,
315:    def _parse_jsonb_exists(self) -> exp.JSONBExists:
---
0be38c8de lithify: probe base
[assistant] The sibling JSONB operators (`?|`, `?&`, `#-`) follow one pattern: a `KEYWORDS` entry in the postgres tokenizer, a `RANGE_PARSERS` entry in the base parser, a `Binary, Func` expression, and a generator entry. I'll follow that. The one open question is whether a new `TokenType` is needed, so I'll look at the token enum and the expression file.
[tool_use Bash] {"command": "sed -n 70,90p sqlglot/tokenizer_core.py; echo ---; grep -n \"AT_GT\\|LT_AT\" sqlglot/tokenizer_core.py sqlglot/tokens.py; echo ---; sed -n 1,5p sqlglot/expressions/json.py; grep -n \"class JSONBExtractScalar\" -A4 sqlglot/expressions/json.py; echo ---; sed -n 1,30p sqlglot/tokenizer_core.py | head -5; ls sqlglot/*.so sqlglot/**/*.so 2>/dev/null | head -3", "description": "Check token enum definitions and json expressions layout"}
[tool_result]     PARAMETER = auto()
    SESSION = auto()
    SESSION_PARAMETER = auto()
    SESSION_USER = auto()
    DAMP = auto()
    AMP_LT = auto()
    AMP_GT = auto()
    ADJACENT = auto()
    XOR = auto()
    DSTAR = auto()
    QMARK_AMP = auto()
    QMARK_PIPE = auto()
    HASH_DASH = auto()
    EXCLAMATION = auto()

    URI_START = auto()

    BLOCK_START = auto()
    BLOCK_END = auto()

    SPACE = auto()
---
sqlglot/tokenizer_core.py:67:    LT_AT = auto()
sqlglot/tokenizer_core.py:68:    AT_GT = auto()
---
"""sqlglot expressions - JSON functions."""

from __future__ import annotations

from sqlglot.expressions.core import Expression, Func, AggFunc, Binary, Predicate
74:class JSONBExtractScalar(Expression, Binary, Func):
75-    arg_types = {"this": True, "expression": True, "json_type": False}
76-    _sql_names = ["JSONB_EXTRACT_SCALAR"]
77-
78-
---
from __future__ import annotations

import typing as t
from enum import IntEnum, auto

(eval):1: no matches found: sqlglot/*.so
[assistant] The plan is settled: a new `AT_QMARK` token, a postgres keyword entry, a `JSONBPathExists` expression, a base parser range entry, a base generator entry, and tests. I'll read each target region before editing, since the edit tool requires a prior read.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "offset": 64, "limit": 6}
[tool_result] 64	    LR_ARROW = auto()
65	    LLRR_ARROW = auto()
66	    DAT = auto()
67	    LT_AT = auto()
68	    AT_GT = auto()
69	    DOLLAR = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "offset": 72, "limit": 12}
[tool_result] 72	
73	
74	class JSONBExtractScalar(Expression, Binary, Func):
75	    arg_types = {"this": True, "expression": True, "json_type": False}
76	    _sql_names = ["JSONB_EXTRACT_SCALAR"]
77	
78	
79	class JSONBObjectAgg(Expression, AggFunc):
80	    arg_types = {"this": True, "expression": True}
81	
82	
83	class JSONBool(Expression, Func):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "offset": 77, "limit": 5}
[tool_result] 77	            "@@": TokenType.DAT,
78	            "@>": TokenType.AT_GT,
79	            "<@": TokenType.LT_AT,
80	            "?&": TokenType.QMARK_AMP,
81	            "?|": TokenType.QMARK_PIPE,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "offset": 1199, "limit": 4}
[tool_result] 1199	        TokenType.FOR: lambda self, this: self._parse_comprehension(this),
1200	        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
1201	        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
1202	        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "offset": 205, "limit": 2}
[tool_result] 205	        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
206	        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    AT_GT = auto()\n    DOLLAR = auto()", "new_string": "    AT_GT = auto()\n    AT_QMARK = auto()\n    DOLLAR = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "    _sql_names = [\"JSONB_EXTRACT_SCALAR\"]\n\n\nclass JSONBObjectAgg(Expression, AggFunc):", "new_string": "    _sql_names = [\"JSONB_EXTRACT_SCALAR\"]\n\n\nclass JSONBPathExists(Expression, Binary, Func):\n    pass\n\n\nclass JSONBObjectAgg(Expression, AggFunc):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"@>\": TokenType.AT_GT,\n            \"<@\": TokenType.LT_AT,", "new_string": "            \"@>\": TokenType.AT_GT,\n            \"@?\": TokenType.AT_QMARK,\n            \"<@\": TokenType.LT_AT,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),", "new_string": "        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Source edits are in. Now the tests: I'll add cases beside the existing `?|`, `?&`, and `#-` tests in the postgres test file, reading the region first.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "offset": 1050, "limit": 6}
[tool_result] 1050	
1051	        self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
1052	        self.validate_identity(
1053	            """SELECT '["a", {"b":1}]'::jsonb #- '{1,b}'""",
1054	            """SELECT CAST('["a", {"b":1}]' AS JSONB) #- '{1,b}'""",
1055	        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "            \"\"\"SELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n", "new_string": "            \"\"\"SELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n\n        self.validate_identity(\"a @? b\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-103151-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll run the project's own check command, the full pytest suite, using the interpreter the harness specifies.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run full project test suite", "timeout": 900000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
...............................................................................
…[394 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 50.06s
[assistant] All 1121 tests pass. Next I'll check the exact example from the request end to end, plus the transpile output for another dialect.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nq = \\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\"\nt = sqlglot.parse_one(q, read='postgres')\nprint(repr(t.args['where'].this.__class__.__name__), t.sql('postgres'))\nprint(t.sql('duckdb'))\nprint(sqlglot.parse_one(\\\"a @? b\\\", read='postgres').sql('postgres'))\n\"", "description": "Verify the example query round-trips in postgres"}
[tool_result] 'JSONBPathExists' SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
a @? b
[assistant] The example round-trips as `@?` and parses to `JSONBPathExists`. Last, I'll confirm the diff contains only the intended changes.
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Show changed files and diff stats"}
[tool_result]  M sqlglot/dialects/postgres.py
 M sqlglot/expressions/json.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
 sqlglot/dialects/postgres.py    | 1 +
 sqlglot/expressions/json.py     | 4 ++++
 sqlglot/generator.py            | 1 +
 sqlglot/parser.py               | 1 +
 sqlglot/tokenizer_core.py       | 1 +
 tests/dialects/test_postgres.py | 5 +++++
 6 files changed, 13 insertions(+)
[assistant] The Postgres `@?` operator now tokenizes, parses into a dedicated `JSONBPathExists` expression, and generates back as `@?`. The full test suite passes (1121 tests), and the example from your request round-trips unchanged.

Changes, following the pattern the existing `?|`, `?&`, and `#-` operators use:

- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: `"@?"` maps to `AT_QMARK` in the postgres tokenizer.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Binary, Func)` expression.
- **`sqlglot/parser.py`**: `AT_QMARK` is parsed as a binar
…[190 chars elided]…
 > 2)'` query.

Decisions for you to check:
- **Base dialect, not postgres-only.** The parser and generator entries live in the base classes, as the sibling JSONB operators do. Other dialects therefore also emit `@?` for this expression, including DuckDB, which has no such operator. If you want the output to be postgres-only, the generator entry should move into the postgres generator.
- **Not run against a live Postgres.** The project's guidance asks that dialect tests be checked against the real database, but none is available here, so the tests only check sqlglot's own round-trip behaviour.
