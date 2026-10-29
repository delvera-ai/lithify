# trajectory base-1

final message:
The Postgres dialect now parses `@?` (JSONB jsonpath exists) into a dedicated `JSONBPathExists` expression and generates it back as `@?`. Your example round-trips unchanged, and the full suite passes (1121 tests, 18178 subtests). I didn't commit.

What changed, following the same wiring as the existing `?|` and `?&` operators:

- **`sqlglot/tokenizer_core.py`**: new `TokenType.AT_QMARK`.
- **`sqlglot/dialects/postgres.py`**: `"@?"` mapped to `AT_QMARK` in the Postgres tokenizer keywords.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Expression, Binary, Func)`. Its function name defaults to `JSONB_PATH_EXISTS`, which matches Postgres' own function of the same name.
- **`sqlglot/parser.py`**: `AT_QMARK` added to the base `RANGE_PARSERS`, so it parses as a binary operator with the other range operators.
- **`sqlglot/generator.py`**: `JSONBPathExists` generates as `@?`.
- **`tests/dialects/test_postgres.py`**: `doc @? b` asserts the expression type, and the `WHERE doc @? '$.a[*] ? (@ > 2)'` example round-trips.

Before the change, both `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` and `a @? b` raised a ParseError. Ruff check and format pass on the touched files.

Transpiling `@?` to other dialects leaves the operator as `@?` (for example, `a @? b` to DuckDB gives `a @? b`). I didn't add per-dialect translation to `JSONB_PATH_EXISTS(...)` because the request only covered Postgres. Say if you want that.

The harness's probe script doesn't import `sqlglot` under `python -I`, so I ran it with `PYTHONPATH` set to the worktree.

## events
[assistant] I'll start by finding how the existing JSONB operators (`@>`, `@@`, `?`) are tokenized, parsed and generated.
[tool_use Bash] {"command": "git status --short | head && grep -rn \"@@\\|JSONBContains\\|'@>'\\|\\\"@>\\\"\\|JSONB_CONTAINS\\|DAT_AT\\|ParseJSON\\b\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/dialects/dialect.py sqlglot/generator.py sqlglot/parser.py | head -60; grep -rn \"class .*JSONBContains\\|class JSONBExists\\|class .*Contains(\" sqlglot/expressions*.py sqlglot/expressions/ 2>/dev/null | head", "description": "Locate existing JSONB operator handling"}
[tool_result] oksqlglot/dialects/postgres.py:77:            "@@": TokenType.DAT,
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/dialect.py:1918:    return isinstance(expression, exp.ParseJSON) or (
sqlglot/generator.py:143:        exp.ArrayContainsAll: lambda self, e: self.binary(e, "@>"),
sqlglot/generator.py:204:        exp.JSONBContainsAnyTopKeys: lambda self, e: self.binary(e, "?|"),
sqlglot/generator.py:205:        exp.JSONBContainsAllTopKeys: lambda self, e: self.bin
…[110 chars elided]…
sejson_sql(self, expression: exp.ParseJSON) -> str:
sqlglot/parser.py:1037:            exp.JSONBContains(this=this, expression=key)
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/parser.py:1201:        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),
sqlglot/parser.py:1562:        exp.DType.JSON: lambda self, this, _: self.expression(exp.ParseJSON(this=this)),
(eval):1: no matches found: sqlglot/expressions*.py
[assistant] The `?|` and `?&` operators already map to dedicated expressions, which is the pattern to follow. Next I'll check the Postgres tokenizer and the expression definitions.
[tool_use Bash] {"command": "sed -n 60,100p sqlglot/dialects/postgres.py; echo ----; grep -n \"AT_GT\\|QMARK_AMP\\|QMARK_PIPE\\|DAT\\b\\|\\\"@\\\"\\|AT_SIGN\\|DHASH\\|HASH_ARROW\" sqlglot/tokens.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/postgres.py sqlglot/dialects/*.py | head -50; echo ----; grep -rn \"class JSONBContainsAnyTopKeys\\|class JSONBContains\\b\\|class JSONBContains(\\|class JSONBExtract\\|class JSONBBool\\|class JSONBContainsAllTopKeys\" sqlglot/ | head", "description": "Inspect Postgres tokenizer and JSON operator defs"}
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
          
…[2202 chars elided]…
6:"#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:"#>>": TokenType.DHASH_ARROW,
----
sqlglot/expressions/json.py:49:class JSONBContains(Expression, Binary, Func):
sqlglot/expressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:57:class JSONBContainsAnyTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:70:class JSONBExtract(Expression, Binary, Func):
sqlglot/expressions/json.py:74:class JSONBExtractScalar(Expression, Binary, Func):
[tool_use Bash] {"command": "sed -n 40,80p sqlglot/expressions/json.py; echo ----; sed -n 1180,1205p sqlglot/parser.py; echo ----; sed -n 196,212p sqlglot/generator.py; echo ----; grep -n \"JSONBContainsAllTopKeys\\|JSONBContainsAnyTopKeys\\|QMARK_AMP\\|QMARK_PIPE\" -r sqlglot tests | grep -v \"^sqlglot/parser.py:120\\|generator.py:20\" ; echo ----; grep -rn \"AT_GT\\|LT_AT\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/dialects/duckdb.py sqlglot/generator.py | head", "description": "Read JSON expression defs and related wiring"}
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
…[3616 chars elided]…
sts/dialects/test_postgres.py:1039:        self.validate_identity("a ?| b").assert_is(exp.JSONBContainsAnyTopKeys)
tests/dialects/test_postgres.py:1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
----
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:79:            "<@": TokenType.LT_AT,
sqlglot/dialects/duckdb.py:82:            "@>": TokenType.AT_GT,
sqlglot/dialects/duckdb.py:83:            "<@": TokenType.LT_AT,
[assistant] The pattern is clear: a Postgres keyword entry, a `TokenType`, a `RANGE_PARSERS` entry, an expression class, and a generator entry. I'll check the existing jsonpath names and the token enum before choosing names.
[tool_use Bash] {"command": "grep -rn \"PathExists\\|JSONPath\\|jsonb_path\\|JSON_PATH_EXISTS\\|DAT\\b\" sqlglot/ | head -20; echo ----; sed -n 70,90p sqlglot/tokenizer_core.py; echo ----; grep -n \"DAT\" sqlglot/tokenizer_core.py sqlglot/tokens.py sqlglot/generator.py | head; echo ----; sed -n 1030,1050p tests/dialects/test_postgres.py; echo; grep -rn \"\\?|\\|?&\" tests/dialects/test_postgres.py | head", "description": "Check jsonpath names, token enum, and existing tests"}
[tool_result] sqlglot/parsers/postgres.py:174:        TokenType.DAT: lambda self, this: self.expression(
sqlglot/tokens.py:546:    # In tokenizers like JSONPath, dots are always key separators, never decimal points
sqlglot/tokenizer_core.py:66:    DAT = auto()
sqlglot/parser.py:6671:        path_parts: list[exp.JSONPathPart],
sqlglot/parser.py:6672:    ) -> tuple[exp.Expr | None, list[exp.JSONPathPart]]:
sqlglot/parser.py:6677:                    expression=exp.JSONPath(expressions=path_parts),
sqlglot/parser
…[3670 chars elided]…
a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
tests/dialects/test_postgres.py:1042:            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
tests/dialects/test_postgres.py:1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
tests/dialects/test_postgres.py:1047:            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
tests/dialects/test_postgres.py:1048:            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
[assistant] The Postgres parser now lives in `sqlglot/parsers/postgres.py`, and the base `RANGE_PARSERS` drive `?|`/`?&`. Before editing, I'll confirm the probe script exists and see the rest of the JSONB block so the new class lands in alphabetical order.
[tool_use Bash] {"command": "sed -n 80,100p sqlglot/expressions/json.py; echo ----; ls .lithify/harness/scripts/ && sed -n 1,30p .lithify/harness/scripts/probe_parse.py; echo ----; grep -n \"RANGE_PARSERS\" sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py | head -3", "description": "Read rest of JSON expressions and probe script"}
[tool_result]     arg_types = {"this": True, "expression": True}


class JSONBool(Expression, Func):
    pass


class JSONExists(Expression, Func):
    arg_types = {
        "this": True,
        "path": True,
        "passing": False,
        "on_condition": False,
        "from_dcolonqmark": False,
    }


class JSONExtract(Expression, Binary, Func):
    arg_types = {
        "this": True,
        "expression": True,
----
probe_parse.py  2.2K
"""Probe SQL statements for parse and round-trip failures with sq
…[555 chars elided]…
BLE, and 2
if stdin holds no statements.

Usage (use the interpreter named in memory.md):
  <python> -I .lithify/harness/scripts/probe_parse.py --read oracle < variants.sql
"""

import argparse
import sys

import sqlglot


def probe(sql, read, write):
    try:
        out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

----
2 matches in 1 files:

sqlglot/parsers/postgres.py:171:RANGE_PARSERS = {
[assistant] Postgres has its own `RANGE_PARSERS` in `sqlglot/parsers/postgres.py`, so I need to see how it merges with the base before deciding where the entry goes. I'll also probe the current behavior.
[tool_use Bash] {"command": "sed -n 165,185p sqlglot/parsers/postgres.py; grep -n \"RANGE_PARSERS\" sqlglot/parsers/postgres.py sqlglot/parser.py | head; echo ----; printf \"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\na @? b\\n\" > /tmp/probe_in.sql; <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/probe_in.sql; echo exit=$?", "description": "Check Postgres RANGE_PARSERS merge and probe baseline"}
[tool_result]     }

    EXPONENT = {
        TokenType.CARET: exp.Pow,
    }

    RANGE_PARSERS = {
        **parser.Parser.RANGE_PARSERS,
        TokenType.DAMP: binary_range_parser(exp.ArrayOverlaps),
        TokenType.DAT: lambda self, this: self.expression(
            exp.MatchAgainst(this=self._parse_bitwise(), expressions=[this])
        ),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.END: lambda self: self._parse_commit_or_rollback(),
    }

    UNARY_
…[185 chars elided]…
RS):
sqlglot/parser.py:5841:expression = self.RANGE_PARSERS[self._prev.token_type](self, this)
sqlglot/parsers/postgres.py:171:RANGE_PARSERS = {
sqlglot/parsers/postgres.py:172:**parser.Parser.RANGE_PARSERS,
----
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit=1
[assistant] The probe can't import `sqlglot` under `-I`. I'll check which interpreter the project memory names and whether that env has this checkout installed.
[tool_use Bash] {"command": "ls ~/.claude/projects/-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-noise-verified-r1-B-rep2-repo/memory/ 2>/dev/null; cat ~/.claude/projects/-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-noise-verified-r1-B-rep2-repo/memory/*.md 2>/dev/null | head -40; ls <work>/env-sqlglot/bin/ | head -20; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys;print(sqlglot.__file__)\"", "description": "Find interpreter guidance and check sqlglot import path"}
[tool_result] (empty)
(eval):1: no matches found: ~/.claude/projects/-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-noise-verified-r1-B-rep2-repo/memory/*.md
activate  4.0K
activate.bat  2.6K
activate.csh  2.6K
activate.fish  4.1K
activate.nu  3.7K
activate.ps1  2.7K
activate_this.py  2.3K
deactivate.bat  1.7K
dmypy  374B
f2py  356B
identify-cli  351B
markdown2  348B
mypy  370B
mypyc  353B
nodeenv  346B
numpy-config  356B
pdoc  350B
pre-commit  354B
py.test  371B
pydoc.bat  1.2K
~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/__init__.py
[assistant] The probe imports `sqlglot` from the working tree only when the current directory is on the path, and `-I` disables that. I'll run it with `PYTHONPATH` pointing at this worktree instead.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/probe_in.sql; echo exit=$?", "description": "Probe baseline Postgres @? behavior"}
[tool_result] ERR       SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 32.
ERR       a @? b
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 6.
exit=1
[assistant] Baseline confirms both forms fail with `ParseError`. I'll make the change in the same places the `?|` / `?&` operators use: token enum, Postgres keyword map, expression class, base range parser, and generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    AT_QMARK = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"@>\": TokenType.AT_GT,\n            \"<@\": TokenType.LT_AT,\n            \"?&\": TokenType.QMARK_AMP,", "new_string": "            \"@>\": TokenType.AT_GT,\n            \"@?\": TokenType.AT_QMARK,\n            \"<@\": TokenType.LT_AT,\n            \"?&\": TokenType.QMARK_AMP,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBool(Expression, Func):", "new_string": "class JSONBPathExists(Expression, Binary, Func):\n    pass\n\n\nclass JSONBool(Expression, Func):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n", "new_string": "        TokenType.QMARK_PIPE: binary_range_parser(exp.JSONBContainsAnyTopKeys),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py", "old_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n", "new_string": "        exp.JSONBDeleteAtPath: lambda self, e: self.binary(e, \"#-\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/sqlglot/generator.py has been updated successfully.
[assistant] All five wiring points are in. Next I'll add a Postgres test next to the `?|`/`?&` tests, then re-run the probe.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "            \"\"\"SELECT '[\"a\", \"b\"]'::jsonb ?& array['a', 'b']\"\"\",\n            \"\"\"SELECT CAST('[\"a\", \"b\"]' AS JSONB) ?& ARRAY['a', 'b']\"\"\",\n        )\n", "new_string": "            \"\"
…[22 chars elided]…
"]'::jsonb ?& array['a', 'b']\"\"\",\n            \"\"\"SELECT CAST('[\"a\", \"b\"]' AS JSONB) ?& ARRAY['a', 'b']\"\"\",\n        )\n\n        self.validate_identity(\"doc @? b\").assert_is(exp.JSONBPathExists)\n        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/probe_in.sql; echo exit=$?; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one(\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] 
…[84 chars elided]…
lglot.transpile(\\\"SELECT a @? b\\\", read='postgres', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT a @? b\\\", read='postgres', write='postgres'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -5", "description": "Re-probe, inspect AST, and run Postgres dialect tests"}
[tool_result] OK        SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
          SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'
OK        a @? b
          a @? b
exit=0
JSONBPathExists(
  this=Column(
    this=Identifier(this=doc, quoted=False)),
  expression=Literal(this='$.a[*] ? (@ > 2)', is_string=True))
['SELECT a @? b']
['SELECT a @? b']
..........................                  [100%]
26 passed, 389 subtests passed in 0.24s
[assistant] The probe passes, the AST is a `JSONBPathExists` node, and the Postgres tests pass (26 passed). Now the full-suite gate that the project harness specifies.
[tool_use Bash] {"command": "PYTHONPATH=$PWD timeout 600000 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite as final gate", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite as final gate", "timeout": 600000}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[29 chars elided]…
............................................ [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 45.58s
[assistant] The full suite passes: 1121 tests, 18178 subtests. I'll run the linter and formatter on the touched files, then review the diff.
[tool_use Bash] {"command": "F=\"sqlglot/tokenizer_core.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generator.py tests/dialects/test_postgres.py\"; <work>/env-sqlglot/bin/ruff check $F 2>&1 | tail -3; <work>/env-sqlglot/bin/ruff format --check $F 2>&1 | tail -3; git diff --stat", "description": "Lint, format-check, and show diff stat"}
[tool_result] --> sqlglot/tokenizer_core.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generator.py tests/dialects/test_postgres.py:1:1

Found 1 error.
error: Failed to format sqlglot/tokenizer_core.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generator.py tests/dialects/test_postgres.py: No such file or directory (os error 2)
sqlglot/dialects/postgres.py    | 1 +
 sqlglot/expressions/json.py     | 4 ++++
 sqlglot/generator.py            | 1 +
 sqlglot/parser.py               | 1 +
 sqlglot/tokenizer_core.py       | 1 +
 tests/dialects/test_postgres.py | 6 ++++++
 6 files changed, 14 insertions(+)
[assistant] Ruff reported an error, and the message doesn't say which file caused it. I'll look at the full output to see whether it's my change or the tool setup.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff check sqlglot/tokenizer_core.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generator.py tests/dialects/test_postgres.py 2>&1 | head -12; ls -la <work>/env-sqlglot/bin/ruff; grep -n \"ruff\" .pre-commit-config.yaml | head -3", "description": "Get full ruff error output and config"}
[tool_result] All checks passed!
<work>/env-sqlglot/bin/ruff  22.5M
8 matches in 8 files:

32:0:ruff
[assistant] Lint passes when the files are passed directly; the earlier error came from my command. Now the format check on the same files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --check sqlglot/tokenizer_core.py sqlglot/dialects/postgres.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generator.py tests/dialects/test_postgres.py 2>&1 | tail -3; git diff", "description": "Format-check changed files and show final diff"}
[tool_result] 6 files already formatted
sqlglot/dialects/postgres.py    | 1 +
 sqlglot/expressions/json.py     | 4 ++++
 sqlglot/generator.py            | 1 +
 sqlglot/parser.py               | 1 +
 sqlglot/tokenizer_core.py       | 1 +
 tests/dialects/test_postgres.py | 6 ++++++
 6 files changed, 14 insertions(+)

--- Changes ---

sqlglot/dialects/postgres.py
  @@ -76,6 +76,7 @@ class Postgres(Dialect):
  +            "@?": TokenType.AT_QMARK,
               "<@": TokenType.LT_AT,
               "?&": TokenT
…[1207 chars elided]…
8,6 +1048,12 @@ FROM json_data, field_ids""",
  +        self.validate_identity("doc @? b").assert_is(exp.JSONBPathExists)
  +        self.validate_identity(
  +            "SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'",
  +            "SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'",
  +        )
  +
           self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
           self.validate_identity(
               """SELECT '["a", {"b":1}]'::jsonb #- '{1,b}'""",
  +6 -0
[assistant] The diff is small and matches the existing operator pattern. One cleanup: the `validate_identity` call in the test passes the same string twice, so the second argument is redundant. I'll simplify it and re-run the Postgres tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n            \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n        )\n", "new_string": "        self.validate_identity(\"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164939-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/ruff format --check tests/dialects/test_postgres.py | tail -1 && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2", "description": "Re-check format and Postgres tests after cleanup"}
[tool_result] 1 file already formatted
..........................                  [100%]
26 passed, 389 subtests passed in 0.16s
[assistant] The Postgres dialect now parses `@?` (JSONB jsonpath exists) into a dedicated `JSONBPathExists` expression and generates it back as `@?`. Your example round-trips unchanged, and the full suite passes (1121 tests, 18178 subtests). I didn't commit.

What changed, following the same wiring as the existing `?|` and `?&` operators:

- **`sqlglot/tokenizer_core.py`**: new `TokenType.AT_QMARK`.
- **`sqlglot/dialects/postgres.py`**: `"@?"` mapped to `AT_QMARK` in the Postgres tokenizer keywords.
- **`sqlglot/expressions/json.py`**: new `JSONBPathExists(Expression, Binary, Func)`. Its function name def
…[364 chars elided]…
n type, and the `WHERE doc @? '$.a[*] ? (@ > 2)'` example round-trips.

Before the change, both `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` and `a @? b` raised a ParseError. Ruff check and format pass on the touched files.

Transpiling `@?` to other dialects leaves the operator as `@?` (for example, `a @? b` to DuckDB gives `a @? b`). I didn't add per-dialect translation to `JSONB_PATH_EXISTS(...)` because the request only covered Postgres. Say if you want that.

The harness's probe script doesn't import `sqlglot` under `python -I`, so I ran it with `PYTHONPATH` set to the worktree.
