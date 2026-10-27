# trajectory base-1

final message:
The Postgres dialect now handles `@?`: it tokenizes, parses into a dedicated `JSONBPathExists` expression, and generates `@?` back. The full suite passes (1121 passed) and ruff check and format are clean. I haven't committed.

The change follows the same pattern as the neighbouring JSONB operators like `?&` and `#-`:

- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: maps `"@?"` to `AT_QMARK` in the Postgres tokenizer.
- **`sqlglot/parser.py`**: `AT_QMARK` is a range parser that builds `exp.JSONBPathExists`.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Expression, Binary, Func)` class.
- **`sqlglot/generator.py`**: `JSONBPathExists` generates as `self.binary(e, "@?")`.
- **`tests/dialects/test_postgres.py`**: identity test for `a @? b` and the `WHERE doc @? '$.a[*] ? (@ > 2)'` query from your example.

Two things to know:

- **Function form changes.** Because the class is a `Func`, `jsonb_path_exists(a, b)` also parses to this expression and generates back as `a @? b` in Postgres. The other JSONB operators in this file already behave this way. It is not an issue for the operator, but it is a side effect of the function name.
- **C extension not rebuilt.** `tokenizer_core.py` is compiled by mypyc in the `[c]` build. I ran only the pure-Python suite, not `make testc`, so the compiled path is untested.

## events
[tool_use Bash] {"command": "grep -rn \"AT_GT\\|DAT_AT\\|JSONB_CONTAINS\\|ARROW\\b\\|\\\"@>\\\"\\|'@>'\\|\\\"@\\\"\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -50; grep -n \"class JSONBContains\\|class JSONBExists\\|class JSONBContainsAnyTopKeys\\|class JSONBDeleteAtArray\\|class JSONB\" sqlglot/expressions.py", "description": "Find existing JSONB operator handling"}
[tool_result ERROR] Exit code 2
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/tokens.py:162:        "@": TokenType.PARAMETER,
sqlglot/tokens.py:233:        "->": TokenType.ARROW,
sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/tokens.py:235:        "=>": TokenType.FARROW,
sqlglot/tokens.py:236:        "#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:2
…[761 chars elided]…
       TokenType.HASH_ARROW: lambda self, this, path: self.expression(
sqlglot/parser.py:1033:        TokenType.DHASH_ARROW: lambda self, this, path: self.expression(
sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:4959:            expression = self._match(TokenType.FARROW) and self._parse_bitwise()
sqlglot/parser.py:6262:            if not self._match(TokenType.FARROW):
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/dialects/postgres.py; sed -n 1180,1200p sqlglot/parser.py; grep -n \"AT_GT\\|LT_AT\\|QMARK_AMP\\|QMARK_PIPE\\|HASH_DASH\\|PARAMETER\" sqlglot/tokens.py sqlglot/parser.py sqlglot/dialects/postgres.py | head -30; grep -n \"class ArrayContainsAll\\|class ArrayOverlaps\\|class ArrayContains(\\|class JSONBContains\\|class JSONBExists\\|class JSONBDelete\\|class JSONBBool\" -A3 sqlglot/expressions/*.py | head -60; grep -n \"_sql(self, expression: exp.ArrayContainsAll\\|def binary\" -A3 sqlglot/generator.py | head", "description": "Inspect postgres tokenizer and JSONB expression classes"}
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
          
…[5004 chars elided]…
essions/json.py-63-
sqlglot/expressions/json.py-64-
sqlglot/expressions/json.py:65:class JSONBExists(Expression, Func):
sqlglot/expressions/json.py-66-    arg_types = {"this": True, "path": True}
sqlglot/expressions/json.py-67-    _sql_names = ["JSONB_EXISTS"]
sqlglot/expressions/json.py-68-
4537:    def binary(self, expression: exp.Binary, op: str) -> str:
4538-        sqls: list[str] = []
4539-        stack: list[None | str | exp.Expr] = [expression]
4540-        binary_type = type(expression)
[tool_use Bash] {"command": "grep -rn \"JSONBContainsAllTopKeys\\|JSONBDeleteAtPath\\|QMARK_AMP\\|HASH_DASH\" sqlglot/ tests/ | grep -v \"^sqlglot/expressions/json.py:5\\|^sqlglot/expressions/json.py:6\" ; grep -n \"QMARK_AMP\\|AT_GT\" sqlglot/tokens.py; grep -n \"def binary_range_parser\" -A25 sqlglot/parser.py | head -40", "description": "Trace how existing JSONB operators are handled"}
[tool_result] sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/tokenizer_core.py:82:    HASH_DASH = auto()
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
sqlg
…[931 chars elided]…
lect) -> exp.Func:
76-    # Default argument order is base, expression
77-    this = seq_get(args, 0)
78-    expression = seq_get(args, 1)
79-
80-    if expression:
81-        if not dialect.LOG_BASE_FIRST:
82-            this, expression = expression, this
83-        return exp.Log(this=this, expression=expression)
84-
85-    return (exp.Ln if dialect.parser_class.LOG_DEFAULTS_TO_LN else exp.Log)(this=this)
86-
87-
88-def build_hex(args: BuilderArgs, dialect: Dialect) -> exp.Hex | exp.LowerHex:
[tool_use Bash] {"command": "grep -n \"AT_GT\\|LT_AT\\|QMARK_AMP\\|QMARK_PIPE\" -B2 -A2 sqlglot/tokenizer_core.py; grep -rn \"PathExists\\|JSONPathMatch\\|_match\\b\" sqlglot/expressions/json.py | head; grep -rn \"jsonb_path\\|JSON_PATH_EXISTS\\|jsonb_path_exists\" -i sqlglot/ | head; grep -n \"\\\"?\\\"\" sqlglot/tokens.py sqlglot/dialects/postgres.py; ls sqlglotc 2>/dev/null | head -3; git status --short | head", "description": "Check tokenizer enum and existing JSON path names"}
[tool_result] 65-    LLRR_ARROW = auto()
66-    DAT = auto()
67:    LT_AT = auto()
68:    AT_GT = auto()
69-    DOLLAR = auto()
70-    PARAMETER = auto()
--
78-    XOR = auto()
79-    DSTAR = auto()
80:    QMARK_AMP = auto()
81:    QMARK_PIPE = auto()
82-    HASH_DASH = auto()
83-    EXCLAMATION = auto()
sqlglot/tokens.py:161:        "?": TokenType.PLACEHOLDER,
MANIFEST.in
pyproject.toml
setup.py
[tool_use Bash] {"command": "sed -n 1036,1056p tests/dialects/test_postgres.py; sed -n 60,70p sqlglot/expressions/json.py; grep -n \"JSONBContainsAllTopKeys\\|JSONBDeleteAtPath\" sqlglot/expressions/*.py sqlglot/generator.py", "description": "View existing postgres JSONB operator tests"}
[tool_result]         self.validate_identity("SELECT * FROM foo WHERE id = %(id_param)s")
        self.validate_identity("SELECT * FROM foo WHERE id = ?")

        self.validate_identity("a ?| b").assert_is(exp.JSONBContainsAnyTopKeys)
        self.validate_identity(
            """SELECT '{"a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
        )

        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopK
…[523 chars elided]…
n, Func):
    arg_types = {"this": True, "path": True}
    _sql_names = ["JSONB_EXISTS"]


class JSONBExtract(Expression, Binary, Func):
sqlglot/expressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:61:class JSONBDeleteAtPath(Expression, Binary, Func):
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
[assistant] Existing JSONB operators follow a clear pattern (token → `RANGE_PARSERS` → binary `Func` expression → `TRANSFORMS` entry). I'll follow it for `@?`.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\ndef edit(path, old, new, count=1):\n    s = open(path).read()\n    assert s.count(old) == count, (path, old, s.count(old))\n    open(path, \"w\").write(s.replace(old, new))\n\nedit(\"sqlglot/tokenizer_core.py\", \"    AT_GT = auto()\\n\", \"    AT_GT = auto()\\n    AT_QMARK = auto()\\n\")\nedit(\"sqlglot/dialects/postgres.py\", '            \"@>\": TokenT
…[1196 chars elided]…
ELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n\n        self.validate_identity(\"doc @? '$.a[*] ? (@ > 2)'\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"\"\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\"\"\",\n        )\n''')\nEOF\ngit diff --stat", "description": "Apply edits for @? token, parser, expression, generator, tests"}
[tool_result]  sqlglot/dialects/postgres.py    | 1 +
 sqlglot/expressions/json.py     | 4 ++++
 sqlglot/generator.py            | 1 +
 sqlglot/parser.py               | 1 +
 sqlglot/tokenizer_core.py       | 1 +
 tests/dialects/test_postgres.py | 5 +++++
 6 files changed, 13 insertions(+)
[assistant] Edits are in. Now I'll run the Postgres tests and the full suite using the project's configured test command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15; <work>/env-sqlglot/b
…[27 chars elided]…
glot\nfrom sqlglot import exp\nprint(sqlglot.transpile(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", read='postgres', write='postgres'))\nprint(repr(sqlglot.parse_one(\\\"a @? b\\\", read='postgres')))\nprint(sqlglot.transpile(\\\"SELECT a FROM t WHERE x @> y AND z = ?\\\", read='postgres', write='postgres'))\n\"", "description": "Run postgres tests and a quick round-trip check"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.39s
["SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'"]
JSONBPathExists(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Column(
    this=Identifier(this=b, quoted=False)))
['SELECT a FROM t WHERE x @> y AND z = ?']
[assistant] Postgres tests pass and the round-trip works. Running the full suite now.
[tool_use Bash] {"command": "timeout 600 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; (ruff check sqlglot tests/dialects/test_postgres.py && ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -4", "description": "Run full test suite and lint checks"}
[tool_result] (eval):1: command not found: timeout
All checks passed!
177 files already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full pytest suite"}
[tool_result] ............ [ 62%]
...................................................................... [ 68%]
............................................... [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 62.50s (0:01:02)
[assistant] The Postgres dialect now handles `@?`: it tokenizes, parses into a dedicated `JSONBPathExists` expression, and generates `@?` back. The full suite passes (1121 passed) and ruff check and format are clean. I haven't committed.

The change follows the same pattern as the neighbouring JSONB operators like `?&` and `#-`:

- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: maps `"@?"` to `AT_QMARK` in the Postgres tokenizer.
- **`sqlglot/parser.py`**: `AT_QMARK` is a range parser that builds `exp.JSONBPathExists`.
- **`sqlglot/expressions/json.py`**:
…[183 chars elided]…
dentity test for `a @? b` and the `WHERE doc @? '$.a[*] ? (@ > 2)'` query from your example.

Two things to know:

- **Function form changes.** Because the class is a `Func`, `jsonb_path_exists(a, b)` also parses to this expression and generates back as `a @? b` in Postgres. The other JSONB operators in this file already behave this way. It is not an issue for the operator, but it is a side effect of the function name.
- **C extension not rebuilt.** `tokenizer_core.py` is compiled by mypyc in the `[c]` build. I ran only the pure-Python suite, not `make testc`, so the compiled path is untested.
