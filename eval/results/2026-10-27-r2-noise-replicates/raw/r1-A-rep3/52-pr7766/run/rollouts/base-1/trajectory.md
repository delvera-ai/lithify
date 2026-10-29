# trajectory base-1

final message:
The Postgres dialect now handles the JSONB jsonpath operator `@?`. It tokenizes, parses into a dedicated `exp.JSONBPathExists`, and generates back as `@?`. The full test suite passes (1121 tests) and ruff lint and format are clean. I did not commit.

Your example round-trips unchanged:

```
SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
```

The changes follow the same pattern as the existing `?&`, `?|` and `#-` operators:

- **Token:** new `TokenType.AT_QMARK` in `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer (`sqlglot/dialects/postgres.py`).
- **Expression:** `JSONBPathExists` in `sqlglot/expressions/json.py`, a binary expression with `_sql_names = ["JSONB_PATH_EXISTS"]`. That name is my choice, so `JSONB_PATH_EXISTS(doc, path)` parses to the same node and generates `doc @? path` in Postgres.
- **Parser and generator:** a range-parser entry in `sqlglot/parser.py` and a generator entry in `sqlglot/generator.py` that emits `@?`.
- **Tests:** added to `tests/dialects/test_postgres.py` next to the other JSONB operator tests. They cover the identity round trip and the `JSONBPathExists` node type.

I didn't add a test for the `JSONB_PATH_EXISTS(...)` function form. It is covered only by my manual check, which produced `doc @? '$.a'`.

## events
[tool_use Bash] {"command": "rtk grep -n \"@>\\|ARROW\\|DAT_\\|JSONB_CONTAINS\\|JSONB_EXISTS\\|'@?'\\|@?\" sqlglot/dialects/postgres.py sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Search for existing JSONB operator handling"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n \"@>\\|ARROW\\|DAT_\\|JSONB_CONTAINS\\|JSONB_EXISTS\\|@?\\|AT_QMARK\\|ATAT\\|PLACEHOLDER_PARSERS\\|JSON_PATH\" sqlglot/dialects/postgres.py sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Search for existing JSONB operator handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/tokens.py:233:        "->": TokenType.ARROW,
sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/tokens.py:235:        "=>": TokenType.FARROW,
sqlglot/tokens.py:236:        "#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:        "<->": TokenType.LR_ARROW,
sqlglot/tokens.py:239:        
…[2261 chars elided]…
QUOTE_JSON_PATH:
sqlglot/generator.py:3755:        if self._quote_json_path_key_using_brackets and self.JSON_PATH_SINGLE_QUOTE_ESCAPE:
sqlglot/generator.py:5254:            quoted and self.JSON_PATH_KEY_QUOTED_FORCES_BRACKETS
sqlglot/generator.py:5255:        ) and self.SAFE_JSON_PATH_KEY_RE.match(this):
sqlglot/generator.py:5260:        if quoted and self.QUOTE_JSON_PATH:
sqlglot/generator.py:5268:            if self._quote_json_path_key_using_brackets and self.JSON_PATH_BRACKETED_KEY_SUPPORTED
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/dialects/postgres.py; grep -n \"AT_GT\\|AT_QMARK\\|ArrayContainsAll\\|AT_AT\\|ATAT\\|JSONBContains\\|JSONB_\\|class JSONB\\|class JSONBExists\\|class JSONBContains\" sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/*.py sqlglot/expressions/*.py 2>/dev/null | head -60; ls sqlglot | head -80", "description": "Inspect postgres tokenizer and JSONB-related code"}
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
          
…[2724 chars elided]…
nc):
sqlglot/expressions/json.py:76:    _sql_names = ["JSONB_EXTRACT_SCALAR"]
sqlglot/expressions/json.py:79:class JSONBObjectAgg(Expression, AggFunc):
sqlglot/expressions/json.py:83:class JSONBool(Expression, Func):
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
[tool_use Bash] {"command": "grep -rn \"QMARK_AMP\\|AT_GT\\|LT_AT\\|JSONBContainsAllTopKeys\" sqlglot tests | grep -v \"\\.pyc\"; sed -n 40,70p sqlglot/expressions/json.py; grep -n '\"@\"\\|PARAMETER' sqlglot/tokens.py | head; sed -n 1180,1205p sqlglot/parser.py; sed -n 200,208p sqlglot/generator.py", "description": "Trace how existing JSONB/array operators are wired"}
[tool_result] sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1195:        TokenType.LT_AT: binary_range_parser(exp.ArrayContainsAll, reverse_args=True),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/tokenizer_core.py:67:    LT_AT = auto()
sqlglot/tokenizer_core.py:68:    AT_GT = auto()
sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/generator.py:205:        exp.JSONBContain
…[2941 chars elided]…
a self, e: f"{self.sql(e, 'this')} TO {self.sql(e, 'expression')}",
        exp.Int64: lambda self, e: self.sql(exp.cast(e.this, exp.DType.BIGINT)),
        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
        exp.JSONObject: lambda self, e: self._jsonobject_sql(e),
        exp.JSONObjectAgg: lambda self, e: self._jsonobject_sql(e),
[assistant] Existing JSONB operators (`?&`, `?|`, `#-`) follow a clear pattern: a token type, a Postgres keyword mapping, an expression class, a range parser, and a generator entry. I'll add `@?` the same way.
[tool_use Bash] {"command": "sed -n 64,84p sqlglot/tokenizer_core.py; sed -n 1040,1050p tests/dialects/test_postgres.py; grep -n \"JSONBContains\\b\\|class JSONBExists\" -n sqlglot/expressions/json.py", "description": "View token enum and existing postgres test context"}
[tool_result]     LR_ARROW = auto()
    LLRR_ARROW = auto()
    DAT = auto()
    LT_AT = auto()
    AT_GT = auto()
    DOLLAR = auto()
    PARAMETER = auto()
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

        self.validate_identity(
            """SELECT '{"a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
        )

        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
        self.validate_identity(
            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
        )

49:class JSONBContains(Expression, Binary, Func):
65:class JSONBExists(Expression, Func):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    AT_QMARK = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"?|\": TokenType.QMARK_PIPE,\n", "new_string": "            \"?|\": TokenType.QMARK_PIPE,\n            \"@?\": TokenType.AT_QMARK,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n", "new_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n\n\nclass JSONBPathExists(Expression, Binary, Func):\n    _sql_names = [\"JSONB_PATH_EXISTS\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),\n", "new_string": "        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"a ?& b\").assert_is(exp.JSONBContainsAllTopKeys)", "new_string": "        self.validate_identity(\"doc @? '$.a[*] ? (@ > 2)'\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n\n        self.validate_identity(\"a ?& b\").assert_is(exp.JSONBContainsAllTopKeys)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-141457-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Edits are in. Now I'll run the project's test command, plus a quick check of the `@?` round trip in the requested form.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", read='postgres')\nprint(repr(e.args['where'].this.__class__), e.sql('postgres'))\nprint(sqlglot.transpile(\\\"SELECT doc @? '\\$.a' FROM t\\\", read='postgres', write='postgres'))\nprint(sqlglot.transpile(\\\"SELECT JSONB_PATH_EXISTS(doc, '\\$.a')\\\", read='postgres', write='postgres'))\n\" ; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Verify @? round trip and run postgres and full test suites"}
[tool_result] <class 'sqlglot.expressions.json.JSONBPathExists'> SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
["SELECT doc @? '$.a' FROM t"]
["SELECT doc @? '$.a'"]
..........................                  [100%]
26 passed, 389 subtests passed in 0.25s
............ [ 62%]
...................................................................... [ 68%]
............................................... [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 54.85s
[assistant] The full suite passes (1121 tests). Next I'll run the style checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/ tests/dialects/test_postgres.py && $PY -m ruff format --check sqlglot/ tests/dialects/test_postgres.py) 2>&1 | tail -5; git status --short", "description": "Run ruff lint and format check on changed files"}
[tool_result] ruff 0.15.6
All checks passed!
177 files already formatted
 M sqlglot/dialects/postgres.py
 M sqlglot/expressions/json.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
[assistant] The Postgres dialect now handles the JSONB jsonpath operator `@?`. It tokenizes, parses into a dedicated `exp.JSONBPathExists`, and generates back as `@?`. The full test suite passes (1121 tests) and ruff lint and format are clean. I did not commit.

Your example round-trips unchanged:

```
SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
```

The changes follow the same pattern as the existing `?&`, `?|` and `#-` operators:

- **Token:** new `TokenType.AT_QMARK` in `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer (`sqlglot/dialects/postgres.py`).
- **Expression:**
…[82 chars elided]…
l_names = ["JSONB_PATH_EXISTS"]`. That name is my choice, so `JSONB_PATH_EXISTS(doc, path)` parses to the same node and generates `doc @? path` in Postgres.
- **Parser and generator:** a range-parser entry in `sqlglot/parser.py` and a generator entry in `sqlglot/generator.py` that emits `@?`.
- **Tests:** added to `tests/dialects/test_postgres.py` next to the other JSONB operator tests. They cover the identity round trip and the `JSONBPathExists` node type.

I didn't add a test for the `JSONB_PATH_EXISTS(...)` function form. It is covered only by my manual check, which produced `doc @? '$.a'`.
