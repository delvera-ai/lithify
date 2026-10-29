# trajectory base-1

final message:
Postgres `@?` now tokenizes, parses into a dedicated expression, and generates back as `@?`. The full suite passes (1121 tests, 18178 subtests) and ruff is clean.

Changes:
- **Token:** `QMARK_AT` added in `sqlglot/tokenizer_core.py`, mapped from `@?` in the Postgres tokenizer's `KEYWORDS` (`sqlglot/dialects/postgres.py`), next to `?&` and `?|`.
- **Expression:** `exp.JSONBPathExists` (binary) in `sqlglot/expressions/json.py`.
- **Parser:** a `binary_range_parser` entry in `sqlglot/parser.py`, so `doc @? '$.a[*] ? (@ > 2)'` sits at comparison precedence, e.g. `... WHERE doc @? '...' AND c = 1` parses correctly.
- **Generator:** `exp.JSONBPathExists` emits `@?` in `sqlglot/generator.py`.
- **Tests:** a Postgres round-trip in `tests/dialects/test_postgres.py` covering the class assertion and the example from your request.

One thing to know: the generator entry lives in the base generator, following the existing `?|`, `?&` and `#-` entries there. So a transpile to another dialect emits the Postgres spelling, e.g. `SELECT a @? b` for DuckDB, which has no `@?` operator. Moving the entry into the Postgres generator would change that, but it would also break the base-dialect symmetry the other JSONB operators follow.

Nothing is committed. I left the working tree for you to review.

## events
[tool_use Bash] {"command": "rtk git status --short | head; rtk grep -n \"AT_GT\\|DAT\\|JSONB_CONTAINS\\|ARROW\\|HASH_ARROW\\|JSONBContains\\|JSONBExists\\|QMARK\\b\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/expressions.py sqlglot/generator.py sqlglot/parser.py | head -80", "description": "Check repo state and find JSONB operator handling"}
[tool_result] ok171 matches in 4 files:

sqlglot/dialects/postgres.py:8:from sqlglot.typing.postgres import EXPRESSION_METADATA
sqlglot/dialects/postgres.py:12:EXPRESSION_METADATA = EXPRESSION_METADATA.copy()
sqlglot/dialects/postgres.py:77:"@@": TokenType.DAT,
sqlglot/dialects/postgres.py:78:"@>": TokenType.AT_GT,
sqlglot/generator.py:177:exp.DatabaseProperty: lambda *_: "DATABASE",
sqlglot/generator.py:204:exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:exp.JSONBC
…[3614 chars elided]…
,
sqlglot/tokens.py:239:"<<->>": TokenType.LLRR_ARROW,
sqlglot/tokens.py:241:"??": TokenType.DQMARK,
sqlglot/tokens.py:272:"CURRENT_DATE": TokenType.CURRENT_DATE,
sqlglot/tokens.py:278:"DATABASE": TokenType.DATABASE,
sqlglot/tokens.py:402:"UPDATE": TokenType.UPDATE,
sqlglot/tokens.py:499:"DATE": TokenType.DATE,
sqlglot/tokens.py:500:"DATETIME": TokenType.DATETIME,
sqlglot/tokens.py:511:"DATERANGE": TokenType.DATERANGE,
sqlglot/tokens.py:512:"DATEMULTIRANGE": TokenType.DATEMULTIRANGE,
[+101 more]
[tool_use Bash] {"command": "grep -n \"AT_GT\\|JSONBContains\\|JSONBExists\\|JSONBDeleteAtArray\\|DAT\\b\\|ATAT\\|TokenType.AT\\b\\|\\\"@\\\"\\|\\\"@?\\\"\\|\\\"@@\\\"\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/dialects/dialect.py sqlglot/expressions.py sqlglot/generator.py sqlglot/parser.py sqlglot/dialects/*.py | sort -u | head -60; grep -n \"class JSONB\" -A4 sqlglot/expressions.py | head -80", "description": "Find JSONB and @-operator references"}
[tool_result] 880 matches in 16 files:
[+772 more]
sqlglot/dialects/__init__.py:2:"""
sqlglot/dialects/__init__.py:62:"""
sqlglot/dialects/athena.py:14:"""
sqlglot/dialects/athena.py:49:"""
sqlglot/dialects/athena.py:80:return [Token(TokenType.HIVE_TOKEN_STREAM, "")] + self._hive_tokenizer.tokeni...
sqlglot/dialects/bigquery.py:169:QUOTES = ["'", '"', '"""', "'''"]
sqlglot/dialects/bigquery.py:174:HEX_STRINGS = [("0x", ""), ("0X", "")]
sqlglot/dialects/clickhouse.py:76:BIT_STRINGS = [("0b", "")]
sqlglot/diale
…[3157 chars elided]…
rator.py:1124:options = f" OPTIONS({self.sql(options[0])} = {self.sql(options[1])})" if opt...
sqlglot/generator.py:1126:sql = f" AS{self.sep()}{sql}" if sql else ""
sqlglot/generator.py:1131:default = "DEFAULT " if expression.args.get("default") else ""
sqlglot/generator.py:1147:join_mark = " (+)" if expression.args.get("join_mark") else ""
sqlglot/generator.py:1150:join_mark = ""
sqlglot/generator.py:1160:this = f" {this}" if this else ""
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "grep -rn \"AT_GT\\|JSONBContains\\b\\|class JSONBContains\\|JSONBExists\\|\\\"@?\\\"\\|DAT\\b\" sqlglot/ | grep -v \"^sqlglot/dialects/__init__\" | head -40; grep -n \"class JSONBContains\" -A6 sqlglot/expressions/*.py", "description": "Search for AT_GT and JSONB expression classes"}
[tool_result] sqlglot/parsers/postgres.py:174:        TokenType.DAT: lambda self, this: self.expression(
sqlglot/parsers/postgres.py:315:    def _parse_jsonb_exists(self) -> exp.JSONBExists:
sqlglot/parsers/postgres.py:317:            exp.JSONBExists(
sqlglot/tokenizer_core.py:66:    DAT = auto()
sqlglot/tokenizer_core.py:68:    AT_GT = auto()
sqlglot/parser.py:1037:            exp.JSONBContains(this=this, expression=key)
sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll
…[1044 chars elided]…
JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py-54-    pass
sqlglot/expressions/json.py-55-
sqlglot/expressions/json.py-56-
sqlglot/expressions/json.py:57:class JSONBContainsAnyTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py-58-    pass
sqlglot/expressions/json.py-59-
sqlglot/expressions/json.py-60-
sqlglot/expressions/json.py-61-class JSONBDeleteAtPath(Expression, Binary, Func):
sqlglot/expressions/json.py-62-    pass
sqlglot/expressions/json.py-63-
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/dialects/postgres.py; echo ----; sed -n 160,190p sqlglot/parsers/postgres.py; echo ----; sed -n 305,330p sqlglot/parsers/postgres.py; echo ----; sed -n 40,80p sqlglot/expressions/json.py; echo ----; sed -n 315,335p sqlglot/generators/postgres.py; echo ----; sed -n 60,72p sqlglot/tokenizer_core.py; grep -n \"DAT\\b\\|AT_GT\" sqlglot/*.py sqlglot/*/*.py | head -30", "description": "Read Postgres tokenizer, parser, generator, and expression code"}
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
          
…[4903 chars elided]…
TER = auto()
    SESSION = auto()
    SESSION_PARAMETER = auto()
7 matches in 5 files:

sqlglot/dialects/duckdb.py:82:"@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:77:"@@": TokenType.DAT,
sqlglot/dialects/postgres.py:78:"@>": TokenType.AT_GT,
sqlglot/parser.py:1187:TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parsers/postgres.py:174:TokenType.DAT: lambda self, this: self.expression(
sqlglot/tokenizer_core.py:66:DAT = auto()
sqlglot/tokenizer_core.py:68:AT_GT = auto()
[tool_use Bash] {"command": "grep -rn \"QMARK_AMP\\|JSONBContainsAllTopKeys\\|JSONBDeleteAtPath\" sqlglot/ tests/ | head -30; grep -n '\"@\"\\|SINGLE_TOKENS' sqlglot/tokens.py | head; grep -n \"def binary_range_parser\" -A12 sqlglot/parser.py sqlglot/parsers/*.py | head -30; grep -rn \"JSONBExists\\|JSONBContains\" sqlglot/typing/ | head; ls tests/dialects | grep -i postg; grep -n \"@>\\|@@\" tests/dialects/test_postgres.py | head", "description": "Investigate related tokens, classes, tests"}
[tool_result] sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1202:        TokenType.HASH_DASH: binary_range_parser(exp.JSONBDeleteAtPath),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
sqlglot/generator.py:206:        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
sqlglot/dialects/postgres.py:80:            "?&": TokenT
…[1522 chars elided]…
ot/parser.py-74-
sqlglot/parser.py-75-def build_logarithm(args: BuilderArgs, dialect: Dialect) -> exp.Func:
test_postgres.py  92.2K
7 matches in 5 files:

1452:0:
518:0:"SELECT [1, 2, 3] @> [1, 2]",
521:0:"SELECT [1, 2, 3] @> [1, 2]",
523:0:"SELECT ARRAY[1, 2, 3] @> ARRAY[1, 2]",
tests/dialects/test_postgres.py:44:self.validate_identity("x @@ y")
tests/dialects/test_postgres.py:216:"SELECT ARRAY[1, 2] @> ARRAY[1, 2, 3]",
tests/dialects/test_postgres.py:516:"SELECT ARRAY[1, 2, 3] @> ARRAY[1, 2]",
[tool_use Bash] {"command": "sed -n 74,84p sqlglot/tokenizer_core.py; sed -n 1190,1210p sqlglot/parser.py; sed -n 1035,1060p tests/dialects/test_postgres.py; sed -n 40,46p tests/dialects/test_postgres.py; sed -n 136,160p sqlglot/tokens.py; grep -n \"QMARK_PIPE\\|QMARK_AMP\" sqlglot/*.py sqlglot/*/*.py | head", "description": "Read token ordering, parser ranges, and existing tests"}
[tool_result]     DAMP = auto()
    AMP_LT = auto()
    AMP_GT = auto()
    ADJACENT = auto()
    XOR = auto()
    DSTAR = auto()
    QMARK_AMP = auto()
    QMARK_PIPE = auto()
    HASH_DASH = auto()
    EXCLAMATION = auto()

        TokenType.ILIKE: binary_range_parser(exp.ILike),
        TokenType.IN: lambda self, this: self._parse_in(this),
        TokenType.IRLIKE: binary_range_parser(exp.RegexpILike),
        TokenType.IS: lambda self, this: self._parse_is(this),
        TokenType.LIKE: binary_range_pars
…[3372 chars elided]…
pe.BACKSLASH,
        "*": TokenType.STAR,
        "~": TokenType.TILDE,
6 matches in 3 files:

sqlglot/dialects/postgres.py:80:"?&": TokenType.QMARK_AMP,
sqlglot/dialects/postgres.py:81:"?|": TokenType.QMARK_PIPE,
sqlglot/parser.py:1200:TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/tokenizer_core.py:80:QMARK_AMP = auto()
sqlglot/tokenizer_core.py:81:QMARK_PIPE = auto()
[tool_use Bash] {"command": "ls sqlglot/tokenizer_core* ; grep -rn \"QMARK_PIPE\" --include=* -l . 2>/dev/null | grep -v \"^./.git/\" | head; sed -n 200,210p sqlglot/generator.py; grep -n \"JSONBDeleteAtPath\\|JSONBContainsAllTopKeys\" -B2 -A2 sqlglot/expressions/json.py | head -5", "description": "Check token files and generator context"}
[tool_result] sqlglot/tokenizer_core.py  34.5K
(eval):1: no matches found: --include=*
        exp.InputModelProperty: lambda self, e: f"INPUT{self.sql(e, 'this')}",
        exp.Intersect: lambda self, e: self.set_operations(e),
        exp.IntervalSpan: lambda self, e: f"{self.sql(e, 'this')} TO {self.sql(e, 'expression')}",
        exp.Int64: lambda self, e: self.sql(exp.cast(e.this, exp.DType.BIGINT)),
        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
        exp.JSONBContainsAllTopKeys: lambda self, e: self.binary(e, "?&"),
        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, "#-"),
        exp.JSONObject: lambda self, e: self._jsonobject_sql(e),
        exp.JSONObjectAgg: lambda self, e: self._jsonobject_sql(e),
        exp.LanguageProperty: lambda self, e: self.naked_property(e),
        exp.LocationProperty: lambda self, e: self.naked_property(e),
51-
52-
53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
54-    pass
55-
[assistant] Now the edits: token, keyword mapping, parser range entry, expression class, and generator entry, each next to its `?&` / `?|` / `#-` siblings.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n", "new_string": "    QMARK_PIPE = auto()\n    QMARK_AT = auto()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"?|\": TokenType.QMARK_PIPE,\n", "new_string": "            \"?|\": TokenType.QMARK_PIPE,\n            \"@?\": TokenType.QMARK_AT,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n", "new_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.QMARK_AT: binary_range_parser(exp.JSONBPathExists),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n", "new_string": "class JSONBDeleteAtPath(Expression, Binary, Func):\n    pass\n\n\nclass JSONBPathExists(Expression, Binary, Func):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"a #- b\").assert_is(exp.JSONBDeleteAtPath)\n        self.validate_identity(\n            \"\"\"SELECT '[\"a\", {\"b\":1}]'::jsonb #- '{1,b}'\"\"\",\n            \"\"\"SELEC
…[226 chars elided]…
\", {\"b\":1}]'::jsonb #- '{1,b}'\"\"\",\n            \"\"\"SELECT CAST('[\"a\", {\"b\":1}]' AS JSONB) #- '{1,b}'\"\"\",\n        )\n\n        self.validate_identity(\"doc @? b\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\", read='postgres
…[8 chars elided]…
t(repr(e.args['where'].this.__class__), e.sql('postgres'))\nprint(sqlglot.transpile(\\\"SELECT a @? b\\\", read='postgres', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT a @? b AND c = 1\\\", read='postgres', write='postgres'))\nprint(sqlglot.transpile(\\\"SELECT a @? b\\\", read='postgres', write='postgres', pretty=True))\n\"", "description": "Run Postgres dialect tests and manual checks"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.36s
<class 'sqlglot.expressions.json.JSONBPathExists'> SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
['SELECT a @? b']
['SELECT a @? b AND c = 1']
['SELECT\n  a @? b']
[assistant] Postgres tests pass and the expression round-trips. Next I'll tidy the test to a single-argument round-trip, then run the full suite and lint.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n", "new_string": "        self.validate_identity(\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-202518-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff --version && ruff check sqlglot tests/dialects/test_postgres.py && ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -5", "description": "Run full test suite and lint checks"}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[91 chars elided]…
......................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 46.52s
ruff 0.15.6
Ruff: No issues found
177 files already formatted
[assistant] Postgres `@?` now tokenizes, parses into a dedicated expression, and generates back as `@?`. The full suite passes (1121 tests, 18178 subtests) and ruff is clean.

Changes:
- **Token:** `QMARK_AT` added in `sqlglot/tokenizer_core.py`, mapped from `@?` in the Postgres tokenizer's `KEYWORDS` (`sqlglot/dialects/postgres.py`), next to `?&` and `?|`.
- **Expression:** `exp.JSONBPathExists` (binary) in `sqlglot/expressions/json.py`.
- **Parser:** a `binary_range_parser` entry in `sqlglot/parser.py`, so `doc @? '$.a[*] ? (@ > 2)'` sits at comparison precedence, e.g. `... WHERE doc @? '...' AND c = 1`
…[96 chars elided]…
- **Tests:** a Postgres round-trip in `tests/dialects/test_postgres.py` covering the class assertion and the example from your request.

One thing to know: the generator entry lives in the base generator, following the existing `?|`, `?&` and `#-` entries there. So a transpile to another dialect emits the Postgres spelling, e.g. `SELECT a @? b` for DuckDB, which has no `@?` operator. Moving the entry into the Postgres generator would change that, but it would also break the base-dialect symmetry the other JSONB operators follow.

Nothing is committed. I left the working tree for you to review.
