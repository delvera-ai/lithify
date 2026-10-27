# trajectory base-1

final message:
`parse_one` and `parse` now accept `max_nodes`. Exceeding it raises a `ParseError` whose message contains "Maximum number of AST nodes". The full suite passes (1083 tests), and ruff, ruff format and mypy are clean on the changed files. I haven't committed anything.

- **Behaviour:** with the default `max_nodes=None`, nothing changes. A 500-column `SELECT` parses to 500 expressions with or without a generous limit, and a limit of 100 raises.
- **Coverage:** the count is taken in `Parser.expression()`, the central node-building hook, plus a final check at the end of each parse so a limit hit inside a backtracking attempt still surfaces. It is an approximation: about 530 direct `exp.X(...)` constructions in `parser.py` are not counted.
- **`into=` path:** `parse_into` previously crashed with `IndexError` on this error, because it indexes `e.errors[0]`. It now re-raises the node-limit error directly.

Changes are in `sqlglot/parser.py`, `sqlglot/_typing.py` (the typed option), and a new assertion block in `tests/test_parser.py::test_max_nodes`.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"def __init__\" -A 40 sqlglot/parser.py | head -80 && grep -n \"def parse_one\\|def parse(\\|def __init__\\|max_errors\\|error_level\" sqlglot/__init__.py sqlglot/parser.py | head -60", "description": "Inspect repo state and parser constructor"}
[tool_result] 964550da9 lithify: probe base
1823:    def __init__(
1824-        self,
1825-        error_level: ErrorLevel | None = None,
1826-        error_message_context: int = 100,
1827-        max_errors: int = 3,
1828-        dialect: DialectType = None,
1829-    ):
1830-        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1831-        self.error_message_context: int = error_message_context
1832-        self.max_errors: int = max_errors
1833-        self.dialect: t.Any = _resolve_d
…[2406 chars elided]…
.error_level
sqlglot/parser.py:1984:        self.error_level = ErrorLevel.IMMEDIATE
sqlglot/parser.py:1992:            self.error_level = error_level
sqlglot/parser.py:1996:    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
sqlglot/parser.py:2050:        if self.error_level == ErrorLevel.WARN:
sqlglot/parser.py:2053:        elif self.error_level == ErrorLevel.RAISE and self.errors:
sqlglot/parser.py:2055:                concat_messages(self.errors, self.max_errors),
[tool_use Bash] {"command": "sed -n 280,310p sqlglot/parser.py && sed -n 1996,2070p sqlglot/parser.py && grep -n \"    def expression\\|    def validate_expression\\|    def _parse_statement\\|    def _parse_csv\" -A 25 sqlglot/parser.py | sed -n 1,80p && sed -n 100,215p sqlglot/__init__.py", "description": "Read parse loop, expression helpers, and top-level API"}
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
           
…[9544 chars elided]…
  the source and the target dialect.
        error_level: the desired error level of the parser.
        **opts: other `sqlglot.generator.Generator` options.

    Returns:
        The list of transpiled SQL statements.
    """
    write = (read if write is None else write) if identity else write
    write = Dialect.get_or_raise(write)
    return [
        write.generate(expression, copy=False, **opts) if expression else ""
        for expression in parse(sql, read, error_level=error_level)
    ]
[tool_use Bash] {"command": "grep -c \"self\\.expression(\" sqlglot/parser.py; grep -c \"exp\\.[A-Z][A-Za-z]*(\" sqlglot/parser.py; grep -n \"ParserNoDialectArgs\" -A 12 sqlglot/*.py | head -40; grep -n \"    def parse(\\|    def parse_into\" -A 12 sqlglot/dialects/dialect.py | head -40; grep -n \"def _parse(\" -A 30 sqlglot/parser.py | head -45; grep -n \"is_primitive\" -A3 sqlglot/expressions.py | head; grep -rn \"max_errors\\|ParseError(\" sqlglot/errors.py | head", "description": "Locate option typing, dialect parse path, and node-building hooks"}
[tool_result] 448
533
sqlglot/_typing.py:28:class ParserNoDialectArgs(t.TypedDict, total=False):
sqlglot/_typing.py-29-    error_level: ErrorLevel | None
sqlglot/_typing.py-30-    error_message_context: int
sqlglot/_typing.py-31-    max_errors: int
sqlglot/_typing.py-32-
sqlglot/_typing.py-33-
sqlglot/_typing.py:34:class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
sqlglot/_typing.py-35-    pass
sqlglot/_typing.py-36-
sqlglot/_typing.py-37-
sqlglot/_typing.py-38-class GeneratorNoDialectArgs(t.Ty
…[3095 chars elided]…
].append(token)
2125-
2126-        self._chunks = chunks
2127-
2128-        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
2129-
2130-    def _warn_unsupported(self) -> None:
2131-        if self._tokens_size <= 1:
2132-            return
2133-
2134-        # We use _find_sql because self.sql may comprise multiple chunks, and we're only
ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/errors.py:37:class ParseError(SqlglotError):
[tool_use Bash] {"command": "grep -n \"    def raise_error\" -A 25 sqlglot/parser.py; sed -n 1,30p tests/test_parser.py; grep -n \"max_errors\\|error_level\" tests/test_parser.py | head; grep -n \"ErrorLevel.RAISE\" -B3 -A8 tests/test_parser.py | head -30", "description": "Read raise_error and existing parser tests"}
[tool_result] 1949:    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
1950-        token = token or self._curr or self._prev or Token.string("")
1951-        formatted_sql, start_context, highlight, end_context = highlight_sql(
1952-            sql=self.sql,
1953-            positions=[(token.start, token.end)],
1954-            context_length=self.error_message_context,
1955-        )
1956-        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_
…[3210 chars elided]…
TABLE t (i UInt8) ENGINE = AggregatingMergeTree() ORDER BY tuple()",
292-                read="clickhouse",
293:                error_level=ErrorLevel.RAISE,
294-            ).sql(dialect="clickhouse"),
295-            "CREATE TABLE t (i UInt8) ENGINE=AggregatingMergeTree() ORDER BY tuple()",
296-        )
297-
298-        with self.assertRaises(ParseError):
299-            parse_one("SELECT A[:")
300-
301-        self.assertEqual(parse_one("as as", error_level=ErrorLevel.IGNORE).sql(), "AS as")
[tool_use Bash] {"command": "sed -n 297,312p sqlglot/parser.py && sed -n 2104,2106p sqlglot/parser.py && grep -n \"class ParseError\" -A 12 sqlglot/errors.py && grep -n \"def parser\" -A6 sqlglot/dialects/dialect.py | head -12", "description": "Check slots, ParseError constructor, dialect parser factory"}
[tool_result]         "error_level",
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
    def _parse(
        self,
        parse_method: t.Callable[[Parser], exp.Expr | None],
37:class ParseError(SqlglotError):
38-    def __init__(
39-        se
…[110 chars elided]…
er().__init__(message)
44-        self.errors = errors or []
45-
46-    @classmethod
47-    def new(
48-        cls,
49-        message: str,
1143:    def parser(self, **opts: Unpack[ParserArgs]) -> Parser:
1144-        args: ParserArgs = {"dialect": self, **opts}
1145-        return self.parser_class(**args)
1146-
1147-    def generator(self, **opts: Unpack[GeneratorArgs]) -> Generator:
1148-        args: GeneratorArgs = {"dialect": self, **opts}
1149-        return self.generator_class(**args)
[assistant] Now I'll make the edits: the constructor option and counter, the per-node check in `expression()`, a final check in `_parse`, and the typed option.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new,count=1):\n    global s\n    assert s.count(old)==count,(s.count(old),old)\n    s=s.replace(old,new)\nrep('''            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n''','''            This is only relevant if error_level is ErrorLevel.RAISE.\n      
…[2874 chars elided]…
eeded\")\n\n        return expressions\n''')\nopen(p,'w').write(s)\np='sqlglot/_typing.py'\ns=open(p).read()\nrep('''    max_errors: int\n\n\nclass ParserArgs''','''    max_errors: int\n    max_nodes: int | None\n\n\nclass ParserArgs''')\nopen(p,'w').write(s)\nEOF\ngrep -n \"^from\\|^import\\|i64\" sqlglot/parser.py | head -20", "description": "Add max_nodes option, counter, and checks to parser"}
[tool_result] 1:from __future__ import annotations
3:import itertools
4:import logging
5:import re
6:import typing as t
7:from collections import defaultdict
9:from sqlglot import exp
10:from sqlglot.errors import (
18:from sqlglot.expressions import apply_index_offset
19:from sqlglot.helper import ensure_list, i64, seq_get
20:from sqlglot.trie import new_trie
21:from sqlglot.time import format_time
22:from sqlglot.tokens import Token, Tokenizer, TokenType
23:from sqlglot.trie import TrieResult, in_trie
24:from collections.abc import Sequence
25:from builtins import type as Type
1840:        self._nodes: i64 = 0
1845:        self._tokens_size: i64 = 0
1846:        self._index: i64 = 0
1853:        self._chunk_index: i64 = 0
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''        if self.max_nodes is not None:\n            self._check_nodes()\n        if token:'''\nnew='''        if self.max_nodes is not None:\n            self._nodes += 1\n            if self._nodes > self.max_nodes:\n                raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n      
…[982 chars elided]…
s=200); print(\"NO RAISE 2\")\nexcept ParseError as e: print(\"multi raised:\", str(e)[:80])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/mn_check.py').read())\"", "description": "Simplify check and run ad-hoc behavior check"}
[tool_result] wide default: 500
wide with generous limit: 500
raised: Maximum number of AST nodes (100) exceeded
small ok: SELECT a FROM t
multi raised: Maximum number of AST nodes (200) exceeded
[assistant] Behavior checks pass. Next I'll add a regression test and run the project's test suite and linters.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/test_parser.py'\ns=open(p).read()\nold='''    def test_parse_empty(self):\n        with self.assertRaises(ParseError):\n            parse_one(\"\")\n'''\nnew=old+'''\n    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\n        self.assertEqual(len(parse_one(wide).expressions), 500)\n        s
…[398 chars elided]…
pen(p,'w').write(s)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -I -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -5; $PY -I -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Add test and run parser and full test suites"}
[tool_result] ................................. [ 51%]
...............................          [100%]
64 passed, 71 subtests passed in 0.22s
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 38.79s
[assistant] Full suite passes (1083). Now the style and type checks.
[tool_use Bash] {"command": "PYDIR=<work>/env-sqlglot/bin; ($PYDIR/ruff check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && $PYDIR/ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py) 2>&1 | tail -5; ($PYDIR/mypy sqlglot/parser.py 2>&1 | tail -3) || true; git diff --stat", "description": "Run ruff and mypy on changed files"}
[tool_result] All checks passed!
3 files already formatted
Success: no issues found in 1 source file
 sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 24 +++++++++++++++++++++++-
 tests/test_parser.py | 11 +++++++++++
 3 files changed, 35 insertions(+), 1 deletion(-)
[assistant] Checks are clean. One gap I want to close before finishing: `parse_one(..., into=...)` goes through `parse_into`, which wraps per-type `ParseError`s in a generic "Failed to parse" error, so the node-limit message would be lost there. Let me verify and fix it.
[tool_use bash] {"command": "cd ~/.cache/lithify/work/repo-161bf5b46800/20261026-154600-parser-add-a-safeguard-against-p/base-1 && PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one\nwide = 'SELECT ' + ', '.join(f'c{i}' for i in range(500)) + ' FROM t'\ntry: parse_one(wide, into=__import__('sqlglot').exp.Select, max_nodes=100)\nexcept Exception as e: print(type(e).__name__, str(e)[:90])\n\"", "description": "Confirm parse_into hides the node-limit message"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: bash. Tool names are case-sensitive: call Bash instead.</tool_use_error>
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot import parse_one, exp\nwide = 'SELECT ' + ', '.join(f'c{i}' for i in range(500)) + ' FROM t'\ntry: parse_one(wide, into=exp.Select, max_nodes=100)\nexcept Exception as e: print(type(e).__name__, str(e)[:90])\n\"", "description": "Confirm parse_into hides the node-limit message"}
[tool_result] IndexError list index out of range
[assistant] That's worse than a missing message: `parse_into` indexes `e.errors[0]`, and my `ParseError` carries no `errors` list, so it crashes with `IndexError`. I'll make `parse_into` re-raise the node-limit error immediately.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''            except ParseError as e:\n                e.errors[0][\"into_expression\"] = expression_type\n'''\nnew='''            except ParseError as e:\n                if self.max_nodes is not None and self._nodes > self.max_nodes:\n                    raise\n                e.errors[0][\"into_expression\"] = express
…[508 chars elided]…
/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $PY -m ruff check sqlglot tests/test_parser.py | tail -1; $PY -m ruff format --check sqlglot/parser.py tests/test_parser.py | tail -1; $PY -m mypy sqlglot/parser.py | tail -1; git status --short", "description": "Fix parse_into path, then rerun tests and linters"}
[tool_result] (eval):23: permission denied: <work>/env-sqlglot/bin
(eval):23: permission denied: <work>/env-sqlglot/bin
(eval):23: permission denied: <work>/env-sqlglot/bin
(eval):23: permission denied: <work>/env-sqlglot/bin
 M sqlglot/_typing.py
 M sqlglot/parser.py
 M tests/test_parser.py
[assistant] The `PY` variable was missing `/python` in that command, so nothing ran. Rerunning with the correct interpreter path.
[tool_use Bash] {"command": "BIN=<work>/env-sqlglot/bin; $BIN/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; $BIN/ruff check sqlglot tests/test_parser.py | tail -1; $BIN/ruff format --check sqlglot/parser.py tests/test_parser.py | tail -1; $BIN/mypy sqlglot/parser.py | tail -1", "description": "Rerun full tests and linters with correct interpreter"}
[tool_result] ..................              [100%]
1083 passed, 17840 subtests passed in 47.08s
All checks passed!
2 files already formatted
Success: no issues found in 1 source file
[assistant] `parse_one` and `parse` now accept `max_nodes`. Exceeding it raises a `ParseError` whose message contains "Maximum number of AST nodes". The full suite passes (1083 tests), and ruff, ruff format and mypy are clean on the changed files. I haven't committed anything.

- **Behaviour:** with the default `max_nodes=None`, nothing changes. A 500-column `SELECT` parses to 500 expressions with or without a generous limit, and a limit of 100 raises.
- **Coverage:** the count is taken in `Parser.expression()`, the central node-building hook, plus a final check at the end of each parse so a limit hit inside a backtracking attempt still surfaces. It is an approximation: about 530 direct `exp.X(...)` constructions in `parser.py` are not counted.
- **`into=` path:** `parse_into` previously crashed with `IndexError` on this error, because it indexes `e.errors[0]`. It now re-raises the node-limit error directly.

Changes are in `sqlglot/parser.py`, `sqlglot/_typing.py` (the typed option), and a new assertion block in `tests/test_parser.py::test_max_nodes`.
