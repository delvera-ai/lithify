# trajectory base-1

final message:
Postgres now tokenizes `@?`, parses it into `exp.JSONBPathExists`, and generates it back as `@?`. The full suite passes (1121 tests) and `ruff check` / `ruff format --check` are clean. I didn't commit.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: maps `"@?"` to `AT_QMARK` in the Postgres tokenizer.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Expression, Binary)`.
- **`sqlglot/parser.py`**: `AT_QMARK` is parsed with `binary_range_parser`, the same way as `?&` and `?|`.
- **`sqlglot/generator.py`**: generates `@?` from the expression, next to the other JSONB operators.
- **`tests/dialects/test_postgres.py`**: identity test for the `@?` example from the request, asserting the expression type.

Decisions to review:
- I made the expression Binary-only, without `Func`, like `Adjacent`. That keeps `jsonb_path_exists(doc, path)` as a plain function call. If it were a `Func`, that call would be rewritten to `doc @? path`. The two aren't equivalent in Postgres: the operator suppresses certain path errors, and the function doesn't by default.
- The generator mapping lives in the base generator, following `?&` and `#-`. As a side effect, other dialects also emit `@?` for this expression. For example, Postgres input `doc @? '$.a' AND x = 1` transpiled to DuckDB comes out as `doc @? '$.a' AND x = 1`. That matches how the existing JSONB operators behave, but it's not a valid DuckDB operator. Moving the mapping into the Postgres generator would fix it, at the cost of diverging from the `?&` pattern.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"@@\\|JSONB_CONTAINS\\|DCOLONAT\\|AT_GT\\|AT_QMARK\\|ContainsAll\\|JSONBContains\\|'@'\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | head -80", "description": "Check repo state and find JSON operator handling"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/postgres.py:77:            "@@": TokenType.DAT,
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/generator.py:143:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/g
…[35 chars elided]…
@{kind}{this}"
sqlglot/parser.py:1037:            exp.JSONBContains(this=this, expression=key)
sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1195:        TokenType.LT_AT: binary_range_parser(exp.ArrayContainsAll, reverse_args=True),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/dialects/postgres.py; grep -n \"QMARK_AMP\\|QMARK_PIPE\\|AT_GT\\|LT_AT\\|JSONB_EXISTS\\|JSONBExists\\|JSONBContains\\b\" sqlglot/tokens.py sqlglot/dialects/*.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py sqlglot/dialects/*.py | head -40; sed -n 1025,1045p sqlglot/parser.py; sed -n 1180,1205p sqlglot/parser.py; grep -n \"class JSONBContains\" -A6 sqlglot/expressions.py; grep -n \"JSONB_ALL\\|JSON_PATH\\|class JSONPath\" sqlglot/expressions.py | head", "description": "Inspect Postgres tokenizer and JSON expression definitions"}
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
          
…[4222 chars elided]…
sAllTopKeys),
        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
        TokenType.ADJACENT: binary_range_parser(exp.Adjacent),
        TokenType.OPERATOR: lambda self, this: self._parse_operator(this),
        TokenType.AMP_LT: binary_range_parser(exp.ExtendsLeft),
ugrep: warning: sqlglot/expressions.py: No such file or directory
ugrep: warning: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"JSONBContainsAllTopKeys\\|JSONBDeleteAtPath\\|QMARK_AMP\\|\\\"?&\\\"\\|'?&'\" sqlglot tests | grep -v \"\\.pyc\"; grep -n \"class JSONBContains\" -A8 sqlglot/expressions/*.py | head -30", "description": "Locate JSONB expression classes and token usages"}
[tool_result] sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
sqlglot/dialects/postgres.py:80:            "?&": TokenT
…[759 chars elided]…
xpressions/json.py-55-
sqlglot/expressions/json.py-56-
sqlglot/expressions/json.py:57:class JSONBContainsAnyTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py-58-    pass
sqlglot/expressions/json.py-59-
sqlglot/expressions/json.py-60-
sqlglot/expressions/json.py-61-class JSONBDeleteAtPath(Expression, Binary, Func):
sqlglot/expressions/json.py-62-    pass
sqlglot/expressions/json.py-63-
sqlglot/expressions/json.py-64-
sqlglot/expressions/json.py-65-class JSONBExists(Expression, Func):
[tool_use Bash] {"command": "sed -n 1035,1060p tests/dialects/test_postgres.py; sed -n 40,80p sqlglot/expressions/json.py; grep -n \"QMARK_PIPE\\|QMARK_AMP\\|HASH_DASH\" sqlglot/tokenizer_core.py sqlglot/tokens.py sqlglot/*.py | head; sed -n 70,95p sqlglot/tokenizer_core.py; grep -n \"JSONBExists\" -r sqlglot | head -5", "description": "Review existing JSONB tests and token definitions"}
[tool_result]         self.validate_identity("SELECT * FROM foo WHERE id = %s")
        self.validate_identity("SELECT * FROM foo WHERE id = %(id_param)s")
        self.validate_identity("SELECT * FROM foo WHERE id = ?")

        self.validate_identity("a ?| b").assert_is(exp.JSONBContainsAnyTopKeys)
        self.validate_identity(
            """SELECT '{"a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
        )

        s
…[2650 chars elided]…
to()

    SPACE = auto()
    BREAK = auto()

    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()
sqlglot/parsers/postgres.py:315:    def _parse_jsonb_exists(self) -> exp.JSONBExists:
sqlglot/parsers/postgres.py:317:            exp.JSONBExists(
sqlglot/expressions/json.py:65:class JSONBExists(Expression, Func):
sqlglot/generators/singlestore.py:168:        exp.JSONBExists: lambda self, e: self.func(
sqlglot/generators/duckdb.py:1611:        exp.JSONBExists: rename_func("JSON_EXISTS"),
[tool_use Bash] {"command": "grep -rn \"(Binary)\" sqlglot/expressions/ | head -5; grep -rn \"\\\"@\\\"\\|'@'\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/tokenizer_core.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py | head; grep -n \"JSONB\\|AT_GT\\|QMARK\" sqlglot/generators/postgres.py | head; grep -n \"ArrayContainsAll\\|class Adjacent\" -A2 sqlglot/expressions/*.py | head -12; ls tests/dialects | head -3; git log --oneline -1 -- sqlglot/parsers/postgres.py", "description": "Check conventions for binary-only expressions and tokenizer"}
[tool_result] sqlglot/expressions/core.py:1636:class Connector(Binary):
sqlglot/tokens.py:162:        "@": TokenType.PARAMETER,
324:        exp.JSONBExtract: lambda self, e: self.binary(e, "#>"),
325:        exp.JSONBExtractScalar: lambda self, e: self.binary(e, "#>>"),
326:        exp.JSONBContains: lambda self, e: self.binary(e, "?"),
390:        exp.JSONBObjectAgg: rename_func("JSONB_OBJECT_AGG"),
sqlglot/expressions/array.py:113:class ArrayContainsAll(Expression, Binary, Func):
sqlglot/expressions/array.py-114-    _sql_names = ["ARRAY_CONTAINS_ALL", "ARRAY_HAS_ALL"]
sqlglot/expressions/array.py-115-
sqlglot/expressions/core.py:2232:class Adjacent(Expression, Binary):
sqlglot/expressions/core.py-2233-    pass
sqlglot/expressions/core.py-2234-
__init__.py
test_athena.py
test_bigquery.py
7e7cf8b06 Refactor: make dialect in build_formatted_time optional, fetch it from parser (#7639)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "offset": 78, "limit": 6}
[tool_result] 78	    XOR = auto()
79	    DSTAR = auto()
80	    QMARK_AMP = auto()
81	    QMARK_PIPE = auto()
82	    HASH_DASH = auto()
83	    EXCLAMATION = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "offset": 203, "limit": 4}
[tool_result] 203	        exp.Int64: lambda self, e: self.sql(exp.cast(e.this, exp.DType.BIGINT)),
204	        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
205	        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
206	        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "offset": 56, "limit": 10}
[tool_result] 56	
57	class JSONBContainsAnyTopKeys(Expression, Binary, Func):
58	    pass
59	
60	
61	class JSONBDeleteAtPath(Expression, Binary, Func):
62	    pass
63	
64	
65	class JSONBExists(Expression, Func):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "offset": 1199, "limit": 4}
[tool_result] 1199	        TokenType.FOR: lambda self, this: self._parse_comprehension(this),
1200	        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
1201	        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
1202	        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "offset": 77, "limit": 5}
[tool_result] 77	            "@@": TokenType.DAT,
78	            "@>": TokenType.AT_GT,
79	            "<@": TokenType.LT_AT,
80	            "?&": TokenType.QMARK_AMP,
81	            "?|": TokenType.QMARK_PIPE,
[assistant] I have the picture now. The plan follows the existing `?&` / `#-` JSONB operators: a token, a range parser, and a generator entry. I'm making the expression Binary-only, like `Adjacent`, so the `jsonb_path_exists()` function form is not silently rewritten into the operator, since the two differ on error suppression.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    AT_QMARK = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"@>\": TokenType.AT_GT,\n            \"<@\": TokenType.LT_AT,", "new_string": "            \"@>\": TokenType.AT_GT,\n            \"@?\": TokenType.AT_QMARK,\n            \"<@\": TokenType.LT_AT,"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n", "new_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n\n\nclass JSONBPathExists(Expression, Binary):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n", "new_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the test, next to the existing JSONB operator tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"a #- b\").assert_is(exp.JSONBDeleteAtPath)", "new_string": "        self.validate_identity(\"doc @? '$.a[*] ? (@ > 2)'\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n\n        self.validate_identity(\"a #- b\").assert_is(exp.JSONBDeleteAtPath)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261029-082754-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\nprint(repr(sqlglot.parse_one(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", read='postgres').args['where']))\nprint(sqlglot.transpile(\\\"SELECT jsonb_path_exists(doc, '\\$.a')\\\", read='postgres', write='postgres'))\nprint(sqlglot.transpile(\\\"SELECT doc @? '\\$.a' AND x = 1\\\", read='postgres', write='duckdb'))\n\"", "description": "Run Postgres dialect tests and spot-check the new operator"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.42s
Where(
  this=JSONBPathExists(
    this=Column(
      this=Identifier(this=doc, quoted=False)),
    expression=Literal(this='$.a[*] ? (@ > 2)', is_string=True)))
["SELECT JSONB_PATH_EXISTS(doc, '$.a')"]
["SELECT doc @? '$.a' AND x = 1"]
[assistant] Postgres tests pass and the operator round-trips. Now the full suite, plus lint, since the project's style checks are part of "done".
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; (<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -8", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 48.19s
All checks passed!
177 files already formatted
[assistant] Postgres now tokenizes `@?`, parses it into `exp.JSONBPathExists`, and generates it back as `@?`. The full suite passes (1121 tests) and `ruff check` / `ruff format --check` are clean. I didn't commit.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `AT_QMARK` token type.
- **`sqlglot/dialects/postgres.py`**: maps `"@?"` to `AT_QMARK` in the Postgres tokenizer.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Expression, Binary)`.
- **`sqlglot/parser.py`**: `AT_QMARK` is parsed with `binary_range_parser`, the same way as `?&` and `?|`.
- **`sqlglot/generator.py`**: generates `@?` fro
…[387 chars elided]…
 to `doc @? path`. The two aren't equivalent in Postgres: the operator suppresses certain path errors, and the function doesn't by default.
- The generator mapping lives in the base generator, following `?&` and `#-`. As a side effect, other dialects also emit `@?` for this expression. For example, Postgres input `doc @? '$.a' AND x = 1` transpiled to DuckDB comes out as `doc @? '$.a' AND x = 1`. That matches how the existing JSONB operators behave, but it's not a valid DuckDB operator. Moving the mapping into the Postgres generator would fix it, at the cost of diverging from the `?&` pattern.
