# trajectory base-1

final message:
Postgres now tokenizes `@?`, parses it into a dedicated `exp.JSONBPathExists` node, and generates it back as `@?`. The example from the request round-trips unchanged, and the full test suite passes (1121 tests), as do `ruff check` and `ruff format --check`.

Changes:
- **Token:** `AT_QMARK` added to `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer (`sqlglot/dialects/postgres.py`).
- **Node:** `JSONBPathExists(Expression, Binary, Predicate)` in `sqlglot/expressions/json.py`. I left out `Func`, so it is not parsed from a `JSONB_PATH_EXISTS(...)` function call.
- **Parser:** a `binary_range_parser` entry in `sqlglot/parser.py`, next to the `?&` and `?|` operators.
- **Generator:** a `self.binary(e, "@?")` entry in `sqlglot/generator.py`.
- **Tests:** `tests/dialects/test_postgres.py` gets an `a @? b` assertion on the node type and a `validate_identity` for the example query.

Two things to be aware of:
- The generator entry lives in the base generator, following `?&` and `?|`. So `@?` is emitted for any dialect that gets this node, not only Postgres. Nothing else produces it today, but it matters if a non-Postgres dialect later parses `@?` into this node.
- I did not commit. The changes are in the working tree.

## events
[assistant] I'll start by loading the syntax-support skill the project harness points to for this kind of task.
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/.claude/skills/sqlglot-syntax-support

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

[tool_use Bash] {"command": "git status --short | head && grep -rn \"@>\\|JSONBContains\\|ARROW\\|DHASH\\|JSONB_CONTAINS\\|PARAMETER\\b\" sqlglot/tokens.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/parser.py sqlglot/expressions/json.py | head -60", "description": "Check status and grep JSONB operator handling"}
[tool_result] sqlglot/generators/postgres.py:326:        exp.JSONBContains: lambda self, e: self.binary(e, "?"),
sqlglot/tokens.py:162:        "@": TokenType.PARAMETER,
sqlglot/tokens.py:233:        "->": TokenType.ARROW,
sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/tokens.py:235:        "=>": TokenType.FARROW,
sqlglot/tokens.py:236:        "#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:        "<->": TokenType.LR_ARROW,
sqlglot/
…[2166 chars elided]…
 JSON_ARROWS_REQUIRE_JSON_TYPE = True
sqlglot/parsers/postgres.py:194:        TokenType.ARROW: lambda self, this, path: self.validate_expression(
sqlglot/parsers/postgres.py:196:                exp.JSONExtract, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
sqlglot/parsers/postgres.py:199:        TokenType.DARROW: lambda self, this, path: self.validate_expression(
sqlglot/parsers/postgres.py:201:                exp.JSONExtractScalar, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
[assistant] The skill says to check whether the quoted example already round-trips before writing anything. I'll test that, and look for existing `@@` / jsonpath handling to model the change on.
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\nfor s in [\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", \\\"SELECT doc @@ '\\$.a' FROM t\\\"]:\n    try:\n        e=sqlglot.parse_one(s, read='postgres'); print(repr(e.find(sqlglot.exp.Where))); print(e.sql('postgres'))\n    except Exception as ex: print('ERR', ex)\n\" ; grep -rn \"@@\\|JSONB_PATH\\|jsonpath\\|JSONPATH\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/*.py | head -30; grep -n \"QMARK_AMP\\|QMARK_PIPE\\|AT_GT\\|LT_AT\" sqlglot/tokens.py sqlglot/generators/postgres.py sqlglot/parsers/postgres.py", "description": "Test quoted example and find existing JSONB token handling"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 32.
  SELECT * FROM events WHERE doc [4m@[0m? '$.a[*] ? (@ > 2)'
None
SELECT doc @@ '$.a' FROM t
sqlglot/generators/postgres.py:461:        expressions = [f"{self.sql(e)} @@ {this}" for e in expression.expressions]
[assistant] The quoted example fails at `@?` as expected. Next I'll look at how the neighbouring JSONB operators (`?&`, `?|`, `@>`) are tokenized, parsed and generated.
[tool_use Bash] {"command": "grep -n \"QMARK_AMP\\|QMARK_PIPE\\|\\\"@>\\|\\\"<@\\|\\\"?&\\|\\\"?|\\|\\\"@@\\|\\\"@\" sqlglot/tokens.py sqlglot/parsers/postgres.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/generator.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py; sed -n 1,70p sqlglot/expressions/json.py; sed -n 1190,1205p sqlglot/parser.py; sed -n 320,332p sqlglot/generators/postgres.py", "description": "Locate JSONB operator tokens, parsers and generators"}
[tool_result] sqlglot/tokens.py:162:        "@": TokenType.PARAMETER,
sqlglot/generator.py:143:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:664:    PARAMETER_TOKEN = "@"
sqlglot/generator.py:3401:        return f"@@{kind}{this}"
sqlglot/dialects/postgres.py:77:         
…[3423 chars elided]…
self, e: self.binary(e, "#>"),
        exp.JSONBExtractScalar: lambda self, e: self.binary(e, "#>>"),
        exp.JSONBContains: lambda self, e: self.binary(e, "?"),
        exp.ParseJSON: lambda self, e: self.sql(exp.cast(e.this, exp.DType.JSON)),
        exp.JSONPathKey: json_path_key_only_name,
        exp.JSONPathRoot: lambda *_: "",
        exp.JSONPathSubscript: lambda self, e: self.json_path_part(e.this),
        exp.LastDay: no_last_day_sql,
        exp.LogicalOr: rename_func("BOOL_OR"),
[assistant] The existing `?&` / `?|` operators give a clear precedent: a Postgres tokenizer entry, a `binary_range_parser` in the base parser, and a `self.binary` generator entry. I'll check where the token enum lives and whether a `jsonb_path_exists` function already exists.
[tool_use Bash] {"command": "grep -rn \"AT_GT\\|QMARK_AMP\" sqlglot/ tests/ | grep -v \"\\.pyc\"; grep -rni \"path_exists\\|PathExists\" sqlglot tests | head; sed -n 198,206p sqlglot/generator.py; grep -n \"JSONB\" tests/dialects/test_postgres.py | head -20", "description": "Find token enum, existing refs and postgres tests"}
[tool_result] sqlglot/tokenizer_core.py:68:    AT_GT = auto()
sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/dialects/duckdb.py:82:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:80:            "?&": TokenType.QMARK_AMP,
    
…[1517 chars elided]…
, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
1048:            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
1051:        self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
1054:            """SELECT CAST('["a", {"b":1}]' AS JSONB) #- '{1,b}'""",
1171:        self.validate_identity("CREATE TABLE test (elems JSONB[])")
1174:        self.validate_identity("CREATE TABLE test (foo JSONB)")
[assistant] The token enum lives in `tokenizer_core.py`. I'll read the surrounding enum entries, the existing `?&` tests, and the rest of the JSONB node block before editing.
[tool_use Bash] {"command": "sed -n 64,72p sqlglot/tokenizer_core.py; sed -n 76,84p sqlglot/tokenizer_core.py; sed -n 70,90p sqlglot/expressions/json.py; sed -n 1036,1056p tests/dialects/test_postgres.py; sed -n 72,84p sqlglot/dialects/postgres.py", "description": "Read enum, expression block and existing tests"}
[tool_result]     LR_ARROW = auto()
    LLRR_ARROW = auto()
    DAT = auto()
    LT_AT = auto()
    AT_GT = auto()
    DOLLAR = auto()
    PARAMETER = auto()
    SESSION = auto()
    SESSION_PARAMETER = auto()
    AMP_GT = auto()
    ADJACENT = auto()
    XOR = auto()
    DSTAR = auto()
    QMARK_AMP = auto()
    QMARK_PIPE = auto()
    HASH_DASH = auto()
    EXCLAMATION = auto()

class JSONBExtract(Expression, Binary, Func):
    _sql_names = ["JSONB_EXTRACT"]


class JSONBExtractScalar(Expression, Binary, Fu
…[1248 chars elided]…
b":1}]' AS JSONB) #- '{1,b}'""",
        )

        HEREDOC_STRING_ALTERNATIVE = TokenType.PARAMETER

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "~": TokenType.RLIKE,
            "@@": TokenType.DAT,
            "@>": TokenType.AT_GT,
            "<@": TokenType.LT_AT,
            "?&": TokenType.QMARK_AMP,
            "?|": TokenType.QMARK_PIPE,
            "#-": TokenType.HASH_DASH,
            "|/": TokenType.PIPE_SLASH,
            "||/": TokenType.DPIPE_SLASH,
[assistant] I have the full pattern now. The change touches four places: a new `AT_QMARK` token, the Postgres keyword mapping, a `JSONBPathExists` predicate node, and its parser and generator entries. I'll read the exact edit targets first, since the editor needs them read.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "offset": 64, "limit": 20}
[tool_result] 64	    LR_ARROW = auto()
65	    LLRR_ARROW = auto()
66	    DAT = auto()
67	    LT_AT = auto()
68	    AT_GT = auto()
69	    DOLLAR = auto()
70	    PARAMETER = auto()
71	    SESSION = auto()
72	    SESSION_PARAMETER = auto()
73	    SESSION_USER = auto()
74	    DAMP = auto()
75	    AMP_LT = auto()
76	    AMP_GT = auto()
77	    ADJACENT = auto()
78	    XOR = auto()
79	    DSTAR = auto()
80	    QMARK_AMP = auto()
81	    QMARK_PIPE = auto()
82	    HASH_DASH = auto()
83	    EXCLAMATION = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "offset": 70, "limit": 25}
[tool_result] 70	class JSONBExtract(Expression, Binary, Func):
71	    _sql_names = ["JSONB_EXTRACT"]
72	
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
84	    pass
85	
86	
87	class JSONExists(Expression, Func):
88	    arg_types = {
89	        "this": True,
90	        "path": True,
91	        "passing": False,
92	        "on_condition": False,
93	        "from_dcolonqmark": False,
94	    }
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "offset": 1198, "limit": 5}
[tool_result] 1198	        TokenType.SIMILAR_TO: binary_range_parser(exp.SimilarTo),
1199	        TokenType.FOR: lambda self, this: self._parse_comprehension(this),
1200	        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
1201	        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
1202	        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "offset": 203, "limit": 4}
[tool_result] 203	        exp.Int64: lambda self, e: self.sql(exp.cast(e.this, exp.DType.BIGINT)),
204	        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
205	        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
206	        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "offset": 79, "limit": 3}
[tool_result] 79	            "<@": TokenType.LT_AT,
80	            "?&": TokenType.QMARK_AMP,
81	            "?|": TokenType.QMARK_PIPE,
[assistant] Everything is read. Now the edits: token, keyword mapping, node, parser entry, generator entry.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    AT_QMARK = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"?|\": TokenType.QMARK_PIPE,", "new_string": "            \"?|\": TokenType.QMARK_PIPE,\n            \"@?\": TokenType.AT_QMARK,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBObjectAgg(Expression, AggFunc):\n    arg_types = {\"this\": True, \"expression\": True}\n\n\n", "new_string": "class JSONBObjectAgg(Expression, AggFunc):\n    arg_types = {\"this\": True, \"expression\": True}\n\n\nclass JSONBPathExists(Expression, Binary, Predicate):\n    pass\n\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n", "new_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, \"?&\"),\n", "new_string": "        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, \"?&\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the test. I'll read the region after the `#-` block in the Postgres test file so the new test sits beside the existing JSONB operator tests.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "offset": 1050, "limit": 10}
[tool_result] 1050	
1051	        self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
1052	        self.validate_identity(
1053	            """SELECT '["a", {"b":1}]'::jsonb #- '{1,b}'""",
1054	            """SELECT CAST('["a", {"b":1}]' AS JSONB) #- '{1,b}'""",
1055	        )
1056	
1057	        self.validate_identity("SELECT JSON_AGG(DISTINCT name) FROM users")
1058	        self.validate_identity(
1059	            "SELECT JSON_AGG(c1 ORDER BY c1) FROM (VALUES ('c'), ('b'), ('a')) AS t(c1)"
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "            \"\"\"SELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n", "new_string": "            \"\"\"SELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n\n        self.validate_identity(\"a @? b\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-101552-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll run the Postgres tests, then the full suite, using the project's pytest interpreter from the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; [ -x $PY ] || PY=python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run postgres tests and full pytest suite"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.43s
................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
...
…[120 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 57.59s
[assistant] The full suite passes (1121 tests). I'll confirm the exact example from the request and run the project's lint and format checks on the touched files.
[tool_use Bash] {"command": "python -c \"\nimport sqlglot\ns=\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\"\ne=sqlglot.parse_one(s, read='postgres'); print(type(e.args['where'].this).__name__); print(e.sql('postgres'))\nprint(sqlglot.transpile(s, read='postgres', write='duckdb'))\n\" ; (ruff check sqlglot tests/dialects/test_postgres.py && ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -5; git status --short", "description": "Verify example round-trip and run lint and format checks"}
[tool_result] JSONBPathExists
SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
["SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'"]
All checks passed!
177 files already formatted
 M sqlglot/dialects/postgres.py
 M sqlglot/expressions/json.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
[assistant] Postgres now tokenizes `@?`, parses it into a dedicated `exp.JSONBPathExists` node, and generates it back as `@?`. The example from the request round-trips unchanged, and the full test suite passes (1121 tests), as do `ruff check` and `ruff format --check`.

Changes:
- **Token:** `AT_QMARK` added to `sqlglot/tokenizer_core.py`, mapped from `"@?"` in the Postgres tokenizer (`sqlglot/dialects/postgres.py`).
- **Node:** `JSONBPathExists(Expression, Binary, Predicate)` in `sqlglot/expressions/json.py`. I left out `Func`, so it is not parsed from a `JSONB_PATH_EXISTS(...)` function call.
- **Parser
…[52 chars elided]…
.py`, next to the `?&` and `?|` operators.
- **Generator:** a `self.binary(e, "@?")` entry in `sqlglot/generator.py`.
- **Tests:** `tests/dialects/test_postgres.py` gets an `a @? b` assertion on the node type and a `validate_identity` for the example query.

Two things to be aware of:
- The generator entry lives in the base generator, following `?&` and `?|`. So `@?` is emitted for any dialect that gets this node, not only Postgres. Nothing else produces it today, but it matters if a non-Postgres dialect later parses `@?` into this node.
- I did not commit. The changes are in the working tree.
