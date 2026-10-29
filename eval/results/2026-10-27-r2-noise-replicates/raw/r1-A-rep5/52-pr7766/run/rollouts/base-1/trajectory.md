# trajectory base-1

final message:
Postgres now tokenizes `@?` as its own token, parses it into `exp.JSONBPathExists`, and generates it back as `@?`. The full suite passes (1121 tests), and ruff lint and format are clean. I did not commit.

The changes:
- **Token:** `TokenType.QMARK_AT` added in `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer.
- **Expression:** `JSONBPathExists(Binary, Predicate, Func)` in `sqlglot/expressions/json.py`, next to the other JSONB expressions.
- **Parser:** `RANGE_PARSERS` entry in `sqlglot/parser.py`, using `binary_range_parser`, same as `?|` and `?&`.
- **Generator:** `"@?"` mapping in `sqlglot/generator.py`.
- **Test:** `tests/dialects/test_postgres.py` covers `a @? b` as `JSONBPathExists` and the example `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` as a round trip.

Two things to be aware of:
- Because the class is a `Func`, the function form `JSONB_PATH_EXISTS(doc, '$.a')` also parses to this node and comes back out as `doc @? '$.a'`. That is equivalent in Postgres, but it is a change in output for code that used the function form.
- Transpiling to other dialects emits `@?` verbatim, which DuckDB does not accept. The existing `?|` and `?&` operators behave the same way, so I left it consistent with them.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"@>\\|<@\\|?|\\|@?\\|JSONBContains\\|JSONBExists\\|ARROW\\|DCOLON\\|HASH_ARROW\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Check repo state and find JSONB operator handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:79:            "<@": TokenType.LT_AT,
sqlglot/dialects/postgres.py:81:            "?|": TokenType.QMARK_PIPE,
sqlglot/tokens.py:223:        "::": TokenType.DCOLON,
sqlglot/tokens.py:224:        "?::": TokenType.QDCOLON,
sqlglot/tokens.py:233:        "->": TokenType.ARROW,
sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/to
…[1691 chars elided]…
kenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1789:    JSON_ARROWS_REQUIRE_JSON_TYPE: t.ClassVar = False
sqlglot/parser.py:4959:            expression = self._match(TokenType.FARROW) and self._parse_bitwise()
sqlglot/parser.py:6262:            if not self._match(TokenType.FARROW):
sqlglot/parser.py:6728:                elif self._match(TokenType.DCOLON):
[tool_use Bash] {"command": "sed -n 60,95p sqlglot/dialects/postgres.py; echo ---; grep -n \"AT_GT\\|LT_AT\\|QMARK_PIPE\\|QMARK_AMP\\|JSONBContains\\b\\|class JSONBContains\\|class JSONBExists\\|class JSONBContainsAll\" sqlglot/*.py sqlglot/dialects/*.py; echo ---; grep -n '\"@\"\\|\"?\"' sqlglot/tokens.py; echo ---; grep -rn \"JSONBExtract\\b\" sqlglot/expressions.py | head -3", "description": "Inspect postgres tokenizer and related JSONB expressions"}
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
          
…[1524 chars elided]…
AT_GT,
sqlglot/dialects/duckdb.py:83:            "<@": TokenType.LT_AT,
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:79:            "<@": TokenType.LT_AT,
sqlglot/dialects/postgres.py:80:            "?&": TokenType.QMARK_AMP,
sqlglot/dialects/postgres.py:81:            "?|": TokenType.QMARK_PIPE,
---
161:        "?": TokenType.PLACEHOLDER,
162:        "@": TokenType.PARAMETER,
---
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "ls sqlglot | head -50; grep -rn \"class JSONBContainsAllTopKeys\\|class JSONBContainsAnyTopKeys\\|class JSONBContains\\b\" sqlglot/ ; sed -n 1180,1205p sqlglot/parser.py; grep -n \"QMARK_AMP\\|QMARK_PIPE\" sqlglot/tokenizer_core.py sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/*.py | head; grep -rn \"?|\\|?&\" tests/dialects/test_postgres.py | head", "description": "Locate JSONB expression classes and existing tests"}
[tool_result] __init__.py
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
sqlglot/expressions/json.py:49:class JSONBContains(Expression, Binary, Func):
sqlglot/expressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:57:class JSONBContains
…[2158 chars elided]…
a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
tests/dialects/test_postgres.py:1042:            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
tests/dialects/test_postgres.py:1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
tests/dialects/test_postgres.py:1047:            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
tests/dialects/test_postgres.py:1048:            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
[tool_use Bash] {"command": "sed -n 1,80p sqlglot/expressions/json.py; echo ---; sed -n 1030,1055p tests/dialects/test_postgres.py; echo ---; grep -n \"JSONBContainsAnyTopKeys\\|JSONBDeleteAtPath\" -r sqlglot/ | grep -v \"expressions/json.py\"", "description": "Read JSONB expression definitions and related tests"}
[tool_result] """sqlglot expressions - JSON functions."""

from __future__ import annotations

from sqlglot.expressions.core import Expression, Func, AggFunc, Binary, Predicate


class CheckJson(Expression, Func):
    arg_types = {"this": True}


class JSONArray(Expression, Func):
    arg_types = {
        "expressions": False,
        "null_handling": False,
        "return_type": False,
        "strict": False,
    }
    is_var_len_args = True


class JSONArrayAgg(Expression, AggFunc):
    arg_types = {
   
…[2435 chars elided]…
]'::jsonb #- '{1,b}'""",
            """SELECT CAST('["a", {"b":1}]' AS JSONB) #- '{1,b}'""",
        )
---
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
[tool_use Bash] {"command": "sed -n 60,90p sqlglot/tokenizer_core.py; echo ---; grep -n \"PATH\\|Path\" sqlglot/expressions/json.py | head -20; echo ---; sed -n 196,210p sqlglot/generator.py; grep -n \"def binary_range_parser\" -A12 sqlglot/parser.py | head -20", "description": "Review token enum, JSON expressions, and generator mappings"}
[tool_result]     FARROW = auto()
    HASH = auto()
    HASH_ARROW = auto()
    DHASH_ARROW = auto()
    LR_ARROW = auto()
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
    E
…[1364 chars elided]…
False
65-) -> t.Callable[[Parser, exp.Expr | None], exp.Expr | None]:
66-    def _parse_binary_range(self: Parser, this: exp.Expr | None) -> exp.Expr | None:
67-        expression = self._parse_bitwise()
68-        if reverse_args:
69-            this, expression = expression, this
70-        return self._parse_escape(self.expression(expr_type(this=this, expression=expression)))
71-
72-    return _parse_binary_range
73-
74-
75-def build_logarithm(args: BuilderArgs, dialect: Dialect) -> exp.Func:
[tool_use Bash] {"command": "sed -n 80,92p sqlglot/expressions/json.py; grep -n \"exp.JSONB\\|JSONBObjectAgg\" sqlglot/generator.py sqlglot/parser.py | head", "description": "Read JSON expression tail and generator JSONB entries"}
[tool_result]     arg_types = {"this": True, "expression": True}


class JSONBool(Expression, Func):
    pass


class JSONExists(Expression, Func):
    arg_types = {
        "this": True,
        "path": True,
        "passing": False,
        "on_condition": False,
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDelet
…[93 chars elided]…
tract(this=this, expression=path)
sqlglot/parser.py:1034:            exp.JSONBExtractScalar(this=this, expression=path)
sqlglot/parser.py:1037:            exp.JSONBContains(this=this, expression=key)
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    QMARK_AT = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"@>\": TokenType.AT_GT,\n            \"<@\": TokenType.LT_AT,\n            \"?&\": TokenType.QMARK_AMP,", "new_string": "            \"@>\": TokenType.AT_GT,\n            \"@?\": TokenType.QMARK_AT,\n            \"<@\": TokenType.LT_AT,\n            \"?&\": TokenType.QMARK_AMP,"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBool(Expression, Func):", "new_string": "class JSONBPathExists(Expression, Binary, Predicate, Func):\n    _sql_names = [\"JSONB_PATH_EXISTS\"]\n\n\nclass JSONBool(Expression, Func):"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.HASH_DASH", "new_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.QMARK_AT: binary_range_parser(exp.JSONBPathExists),\n        TokenType.HASH_DASH"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"a #- b\").assert_is(exp.JSONBDeleteAtPath)", "new_string": "        self.validate_identity(\"a @? b\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"\"\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\"\"\",\n            \"\"\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\"\"\",\n        )\n\n        self.validate_identity(\"a #- b\").assert_is(exp.JSONBDeleteAtPath)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"\"\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\"\"\",\n            \"\"\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\"\"\",\n        )", "new_string": "        self.validate_identity(\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\")"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-130823-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", read='postgres')\nprint(repr(e.args['where'].this.__class__), e.sql('postgres'), e.sql('duckdb'))\nprint(sqlglot.transpile(\\\"SELECT JSONB_PATH_EXISTS(doc, '\\$.a')\\\", read='postgres', write='postgres'))\nprint(sqlglot.transpile(\\\"SELECT doc @? '\\$.a'\\\", read='postgres', write='duckdb'))\n\"", "description": "Run postgres dialect tests and sanity-check output"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.39s
<class 'sqlglot.expressions.json.JSONBPathExists'> SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)' SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
["SELECT doc @? '$.a'"]
["SELECT doc @? '$.a'"]
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_postgres.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_postgres.py 2>&1 | tail -2; git diff --stat", "description": "Run full test suite, ruff lint and format check"}
[tool_result] ................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 50.05s
All checks passed!
177 files already formatted
 sqlglot/dialects/postgres.py    | 1 +
 sqlglot/expressions/json.py     | 4 ++++
 sqlglot/generator.py            | 1 +
 sqlglot/parser.py               | 1 +
 sqlglot/tokenizer_core.py       | 1 +
 tests/dialects/test_postgres.py | 3 +++
 6 files changed, 11 insertions(+)
[assistant] Postgres now tokenizes `@?` as its own token, parses it into `exp.JSONBPathExists`, and generates it back as `@?`. The full suite passes (1121 tests), and ruff lint and format are clean. I did not commit.

The changes:
- **Token:** `TokenType.QMARK_AT` added in `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer.
- **Expression:** `JSONBPathExists(Binary, Predicate, Func)` in `sqlglot/expressions/json.py`, next to the other JSONB expressions.
- **Parser:** `RANGE_PARSERS` entry in `sqlglot/parser.py`, using `binary_range_parser`, same as `?|` and `?&`.
- **Generator:** `"
…[59 chars elided]…
dialects/test_postgres.py` covers `a @? b` as `JSONBPathExists` and the example `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` as a round trip.

Two things to be aware of:
- Because the class is a `Func`, the function form `JSONB_PATH_EXISTS(doc, '$.a')` also parses to this node and comes back out as `doc @? '$.a'`. That is equivalent in Postgres, but it is a change in output for code that used the function form.
- Transpiling to other dialects emits `@?` verbatim, which DuckDB does not accept. The existing `?|` and `?&` operators behave the same way, so I left it consistent with them.
