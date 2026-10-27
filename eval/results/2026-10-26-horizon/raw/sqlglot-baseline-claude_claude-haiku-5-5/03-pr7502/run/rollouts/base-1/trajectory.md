# trajectory base-1

final message:
`parse_one` now takes `max_nodes`, and parsing raises a `ParseError` containing "Maximum number of AST nodes" once the limit is exceeded. The full test suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

- **Default:** no limit (`None`), so existing behavior is unchanged. When the option is unset, the code path adds no counting.
- **Counting:** nodes are counted in `Parser.expression()`, the central node factory, so the parse aborts as soon as the limit is crossed. A query with 500 columns builds about 503 counted nodes, so `max_nodes=1000` parses it normally.
- **`into=`:** `parse_one(..., into=...)` re-raises the limit error directly instead of wrapping it as "Failed to parse ... into ...".
- **Sticky limit:** once exceeded, the limit can't be swallowed by internal fallback parsing (for example in `_try_parse`). The parse still fails at the end.
- **Athena:** `AthenaParser` accepts and forwards the option to its hive and trino sub-parsers, so `read="athena"` works too.
- **Tests:** added `test_max_nodes` in `tests/test_parser.py`. It covers the 500-column query under and over the limit, the `into=` path, and that `error_level=IGNORE` still raises.

Limitations:
- Nodes built directly with `exp.X(...)` instead of through `self.expression()` are not counted, so the limit is approximate. I didn't audit how many call sites bypass it.
- Very deep nesting, such as 300 nested parentheses, hits Python's recursion limit before any node limit applies. That behavior predates this change, and I didn't address it.
- `transpile(..., max_nodes=...)` raises a `TypeError`, because `transpile` only forwards generator options. The request only named `parse_one`, so I left it alone.

The changes are in `sqlglot/parser.py`, `sqlglot/_typing.py`, `sqlglot/parsers/athena.py` and `tests/test_parser.py`.

## events
[assistant] I'll start by reading the parser's entry points and how options flow through `parse_one`.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"error_level\\|def __init__\\|def parse\\b\\|def _parse(\\|def parse_into\\|self.sql = \\|self.max_\\|__slots__\\|def raise_error\\|def _advance\\|def _parse_statement\\|def expression(\" sqlglot/parser.py | head -80 && grep -n \"def parse_one\\|def parse(\\|error_level\" sqlglot/__init__.py sqlglot/dialects/dialect.py | head -30"}
[tool_result] ffcd422ff lithify: probe base
286:        error_level: The desired error level.
292:            This is only relevant if error_level is ErrorLevel.RAISE.
296:    __slots__ = (
297:        "error_level",
1823:    def __init__(
1825:        error_level: ErrorLevel | None = None,
1830:        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1832:        self.max_errors: int = max_errors
1848:        self.sql = ""
1861:    def _advance(self, times: i64 = 1) -> None:
1877:    def _a
…[901 chars elided]…
nit__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/__init__.py:189:    error_level: ErrorLevel | None = None,
sqlglot/__init__.py:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
[tool_use Bash] {"command": "sed -n 280,300p sqlglot/parser.py && sed -n 1815,1860p sqlglot/parser.py && sed -n 1945,2130p sqlglot/parser.py"}
[tool_result] class Parser:
    """
    Parser consumes a list of tokens produced by the Tokenizer and produces a parsed syntax tree.

    Args:
        error_level: The desired error level.
            Default: ErrorLevel.IMMEDIATE
        error_message_context: The amount of context to capture from a query string when displaying
            the error message (in number of characters).
            Default: 100
        max_errors: Maximum number of error messages to include in a raised ParseError.
           
…[7704 chars elided]…
Token]] = [[]]

        for i, token in enumerate(raw_tokens):
            if token.token_type == TokenType.SEMICOLON:
                if token.comments:
                    chunks.append([token])

                if i < total - 1:
                    chunks.append([])
            else:
                chunks[-1].append(token)

        self._chunks = chunks

        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)

    def _warn_unsupported(self) -> None:
[assistant] Most nodes go through `Parser.expression()`, which looks like the natural counting point. Next I'll check how keyword options reach the `Parser` constructor.
[tool_use Bash] {"command": "sed -n 105,230p sqlglot/__init__.py && sed -n 1105,1130p sqlglot/dialects/dialect.py && grep -n \"ParserArgs\\|class ParserArgs\" -A8 sqlglot/dialects/dialect.py | head -30 && grep -rn \"max_errors\" sqlglot/ | grep -v \"^sqlglot/parser.py:29\" | head -20; grep -n \"class ParseError\" -A30 sqlglot/errors.py | head -50"}
[tool_result]     return Dialect.get_or_raise(read or dialect).tokenize(sql)


def parse(
    sql: str,
    read: DialectType = None,
    dialect: DialectType = None,
    **opts: Unpack[ParserNoDialectArgs],
) -> list[Expr | None]:
    """
    Parses the given SQL string into a collection of syntax trees, one per parsed SQL statement.

    Args:
        sql: the SQL code string to parse.
        read: the SQL dialect to apply during parsing (eg. "spark", "hive", "presto", "mysql").
        dialect: the SQL di
…[6362 chars elided]…
light: str | None = None,
55-        end_context: str | None = None,
56-        into_expression: str | None = None,
57-    ) -> ParseError:
58-        return cls(
59-            message,
60-            [
61-                {
62-                    "description": description,
63-                    "line": line,
64-                    "col": col,
65-                    "start_context": start_context,
66-                    "highlight": highlight,
67-                    "end_context": end_context,
[assistant] Keyword options flow through `Dialect.parser(**opts)` into `Parser.__init__`, so a new `max_nodes` argument needs to be added in a few places. Next I'll check the typed arg dicts, the `__slots__` list, and the athena subclass that re-forwards args.
[tool_use Bash] {"command": "sed -n 296,312p sqlglot/parser.py && sed -n 20,60p sqlglot/_typing.py && sed -n 20,60p sqlglot/parsers/athena.py && sed -n 915,930p sqlglot/generators/singlestore.py && grep -n \"def merge_errors\\|def concat_messages\" -A12 sqlglot/errors.py | head -40 && grep -rn \"ParseError\" tests/test_parser.py | head -5; grep -rln \"error_level\\|max_errors\" tests | head"}
[tool_result]     __slots__ = (
        "error_level",
        "error_message_context",
        "max_errors",
        "dialect",
        "sql",
        "errors",
        "_tokens",
        "_index",
        "_curr",
        "_next",
        "_prev",
        "_prev_comments",
        "_pipe_cte_counter",
        "_chunks",
        "_chunk_index",
        "_tokens_size",
BuilderArgs = Sequence[t.Any]
"""Sequence of arguments passed to builder functions."""


class _DialectArg(t.TypedDict, total=False):
    dial
…[2780 chars elided]…
[e_dict for error in errors for e_dict in error.errors]
tests/test_parser.py:6:from sqlglot.errors import ErrorLevel, ParseError
tests/test_parser.py:13:        with self.assertRaises(ParseError):
tests/test_parser.py:35:        with self.assertRaises(ParseError) as ctx:
tests/test_parser.py:60:        with self.assertRaises(ParseError) as ctx:
tests/test_parser.py:88:        with self.assertRaises(ParseError) as ctx:
tests/test_parser.py
tests/test_transpile.py
tests/dialects/test_clickhouse.py
[assistant] The athena parser has its own `__init__` and delegates to hive/trino sub-parsers, so it has to forward the new option too. I'll check for other `__init__` overrides and look at the existing test style.
[tool_use Bash] {"command": "grep -rn \"def __init__\" sqlglot/parser.py sqlglot/parsers/ sqlglot/dialects/ | head -20; sed -n 312,325p sqlglot/parser.py; grep -n \"_hive_parser\\|_trino_parser\" sqlglot/parsers/athena.py | head; sed -n 1,30p tests/test_parser.py; grep -n \"def test_\" tests/test_parser.py | tail -5; tail -20 tests/test_parser.py"}
[tool_result] sqlglot/parser.py:1823:    def __init__(
sqlglot/parsers/athena.py:25:    def __init__(
sqlglot/dialects/dialect.py:974:    def __init__(self, **kwargs) -> None:
sqlglot/dialects/athena.py:70:        def __init__(self, dialect: DialectType = None) -> None:
        "_tokens_size",
    )

    FUNCTIONS: t.ClassVar[dict[str, t.Callable]] = {
        **{name: func.from_arg_list for name, func in exp.FUNCTION_BY_NAME.items()},
        **dict.fromkeys(("COALESCE", "IFNULL", "NVL"), build_coalesce),
  
…[2920 chars elided]…
.GrantPrincipal,
        )
        self.assertEqual(
            parse_one("ROLE `blah`", into=exp.GrantPrincipal, dialect="databricks").sql(
                dialect="databricks"
            ),
            "ROLE `blah`",
        )

    def test_parse_into_grant_privilege(self):
        self.assertIsInstance(parse_one("SELECT", into=exp.GrantPrivilege), exp.GrantPrivilege)
        self.assertIsInstance(
            parse_one("ALL PRIVILEGES", into=exp.GrantPrivilege), exp.GrantPrivilege
        )
[assistant] I have what I need. The plan:

- Add `max_nodes: int | None = None` to `Parser` (no limit by default, so existing behavior is unchanged).
- Count nodes in `Parser.expression()`, the central node factory, and raise `ParseError` once the count goes over the limit. The count is only tracked when the limit is set, so the default path pays nothing.
- Keep the error sticky, so swallowed errors (e.g. in `_try_parse`) still fail the parse, and make `parse_into` re-raise it rather than masking it as "Failed to parse".
- Thread the option through `ParserNoDialectArgs` and the athena parser.

Starting with the core parser edits:
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np = \"sqlglot/parser.py\"\ns = open(p).read()\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (s.count(old), old[:80])\n    s = s.replace(old, new)\n\nrep(\"\"\"            Default: 3\n    \\\"\\\"\\\"\n\n    __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n        \"dialec
…[4787 chars elided]…
", \"\"\"            max_errors=max_errors,\n            max_nodes=max_nodes,\n        )\n        self._trino_parser\"\"\")\nrep(\"\"\"            max_errors=max_errors,\n            dialect=trino,\n        )\"\"\", \"\"\"            max_errors=max_errors,\n            max_nodes=max_nodes,\n            dialect=trino,\n        )\"\"\")\nopen(p, \"w\").write(s)\nprint(\"ok\")\nEOF\ngit diff --stat"}
[tool_result] ok
 sqlglot/_typing.py        |  1 +
 sqlglot/parser.py         | 28 +++++++++++++++++++++++++++-
 sqlglot/parsers/athena.py |  4 ++++
 3 files changed, 32 insertions(+), 1 deletion(-)
[assistant] The edits are in. Next I'll check the behavior directly: node counts for a 500-column query, the limit firing, the `into=` path, and the athena forwarding.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; PY=<work>/env-sqlglot/bin/python; [ -x $PY ] || PY=python3; echo \"PY=$PY\"; PYTHONPATH=. $PY - <<'EOF'\
…[1289 chars elided]…
na ok:\", type(parse_one(\"SELECT 1\", read=\"athena\", max_nodes=100)).__name__)\ntry:\n    parse_one(\"SELECT 1; SELECT 2\", max_nodes=1)\nexcept ParseError as e:\n    print(\"multi:\", str(e).splitlines()[0])\nprint(\"error_level IGNORE still raises:\", end=\" \")\ntry:\n    parse_one(wide, max_nodes=100, error_level=sqlglot.ErrorLevel.IGNORE)\nexcept ParseError as e:\n    print(\"yes\")\nEOF"}
[tool_result ERROR] Exit code 1
<work>/env-sqlglot/bin/python
PY=<work>/env-sqlglot/bin/python
wide default: 500
wide node count: 503
wide with max_nodes=10**9: 500
wide limit err: ParseError Maximum number of AST nodes exceeded (max_nodes=100)
Traceback (most recent call las
…[9040 chars elided]…
/sqlglot/parser.py", line 6426, in _parse_column
    this = self._parse_column_reference()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-132945-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", line 6513, in _parse_column_reference
    this = self._parse_field()
           ^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-132945-parser-add-a-safeguard-against-p/base-1/sqlglot/parse
[assistant] The 500-column case works: it takes about 503 counted nodes. The crash is from my 300-deep parenthesis test, which hit Python's recursion limit inside the existing recursive-descent parser, before any node limit could apply. That's a separate, pre-existing limit, so I'll rerun with a smaller nesting depth and a flat large list.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY - 2>&1 <<'EOF' | tail -30\nimport sqlglot\nfrom sqlglot import parse_one, exp\nfrom sqlglot.errors import ParseError\nwide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\nprint(\"wide ok w
…[850 chars elided]…
\"athena limit 1000\", lambda: parse_one(wide, read=\"athena\", max_nodes=1000))\nshow(\"multi limit 1\", lambda: parse_one(\"SELECT 1; SELECT 2\", max_nodes=1))\nshow(\"IGNORE level limit\", lambda: parse_one(wide, max_nodes=100, error_level=sqlglot.ErrorLevel.IGNORE))\nshow(\"transpile\", lambda: sqlglot.transpile(wide, max_nodes=100))\nshow(\"parse_one default\", lambda: parse_one(wide))\nEOF"}
[tool_result] wide ok with limit 1000: 500
wide limit 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
deep40 limit 50 OK Select
deep40 no limit OK Select
into limit 1 ParseError: Maximum number of AST nodes exceeded (max_nodes=1)
into limit 100 OK Select
athena limit 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
athena limit 1000 OK Select
multi limit 1 ParseError: Maximum number of AST nodes exceeded (max_nodes=1)
IGNORE level limit ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
transpile OTHER TypeError Generator.__init__() got an unexpected keyword argument 'max_nodes'
parse_one default OK Select
[assistant] Everything behaves as intended. `transpile(..., max_nodes=...)` raises a `TypeError` because `transpile` only forwards generator options and the spec names `parse_one`, so I'm leaving that as is and will mention it. Next I'll add tests to the existing parser test class.
[tool_use Bash] {"command": "cat >> tests/test_parser.py <<'EOF'\n\n    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\n        self.assertEqual(len(parse_one(wide, max_nodes=1000).expressions), 500)\n\n        with self.assertRaises(ParseError) as ctx:\n            parse_one(wide, max_nodes=100)\n        self.assertIn(\"Maximum number of AST nodes
…[365 chars elided]…
ssertIn(\"Maximum number of AST nodes\", str(ctx.exception))\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -5; (timeout 900 $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15)"}
[tool_result] .                                                                        [100%]
1 passed, 63 deselected in 0.06s
(eval):19: command not found: timeout
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15"}
[tool_result] ................................................................................. [  7%]
........................................................................................................................................... [ 20%]
......................................................................................... [ 28%]
...................................................................................................................................................................... 
…[236 chars elided]…
..... [ 63%]
......................................................... [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 50.39s
[assistant] The full suite passes (1083 tests). Next I'll run the repo's linters on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parser.py sqlglot/_typing.py sqlglot/parsers/athena.py tests/test_parser.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/_typing.py sqlglot/parsers/athena.py tests/test_parser.py) 2>&1 | tail -8; ($PY -m mypy --version >/dev/null 2>&1 && $PY -m mypy sqlglot/parser.py sqlglot/parsers/athena.py sqlglot/_typing.py 2>&1 | tail -5) || echo \"mypy not available\"; git diff"}
[tool_result] ruff 0.15.6
All checks passed!
4 files already formatted
Success: no issues found in 3 source files
diff --git a/sqlglot/_typing.py b/sqlglot/_typing.py
index fe7e80ee3..578d6c262 100644
--- a/sqlglot/_typing.py
+++ b/sqlglot/_typing.py
@@ -29,6 +29,7 @@ class ParserNoDialectArgs(t.TypedDict, total=False):
     error_level: ErrorLevel | None
     error_message_context: int
     max_errors: int
+    max_nodes: int | None
 
 
 class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
diff -
…[5362 chars elided]…
parse_one(wide, max_nodes=100)
+        self.assertIn("Maximum number of AST nodes", str(ctx.exception))
+
+        with self.assertRaises(ParseError) as ctx:
+            parse_one("SELECT 1", into=exp.Select, max_nodes=1)
+        self.assertIn("Maximum number of AST nodes", str(ctx.exception))
+
+        with self.assertRaises(ParseError) as ctx:
+            parse_one(wide, max_nodes=100, error_level=ErrorLevel.IGNORE)
+        self.assertIn("Maximum number of AST nodes", str(ctx.exception))
[assistant] `parse_one` now takes `max_nodes`, and parsing raises a `ParseError` containing "Maximum number of AST nodes" once the limit is exceeded. The full test suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

- **Default:** no limit (`None`), so existing behavior is unchanged. When the option is unset, the code path adds no counting.
- **Counting:** nodes are counted in `Parser.expression()`, the central node factory, so the parse aborts as soon as the limit is crossed. A query with 500 columns builds about 503 counted nodes, so `max_nodes=100
…[668 chars elided]…
xp.X(...)` instead of through `self.expression()` are not counted, so the limit is approximate. I didn't audit how many call sites bypass it.
- Very deep nesting, such as 300 nested parentheses, hits Python's recursion limit before any node limit applies. That behavior predates this change, and I didn't address it.
- `transpile(..., max_nodes=...)` raises a `TypeError`, because `transpile` only forwards generator options. The request only named `parse_one`, so I left it alone.

The changes are in `sqlglot/parser.py`, `sqlglot/_typing.py`, `sqlglot/parsers/athena.py` and `tests/test_parser.py`.
