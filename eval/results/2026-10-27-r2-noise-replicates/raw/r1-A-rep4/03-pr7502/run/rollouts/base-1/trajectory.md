# trajectory base-1

final message:
The parser now takes a `max_nodes` option. Parsing raises a `ParseError` containing "Maximum number of AST nodes" once the limit is exceeded. The full suite passes (1082 tests), and ruff format and check are clean.

`max_nodes` is accepted by `Parser(...)`, `parse`, and `parse_one`, which pass it through `**opts`. The default is `None`, so nothing changes unless you set it. A 500-column SELECT parses with `max_nodes=100_000`, and the same query with `max_nodes=100` raises.

What I changed:
- **`sqlglot/parser.py`**: `Parser.__init__` takes `max_nodes`. The count increments in `Parser.expression()`, which is the parser's node-construction helper, and the error is raised there.
- **`sqlglot/_typing.py`**: added `max_nodes` to `ParserNoDialectArgs` so the keyword type-checks.
- **`tests/test_parser.py`**: added `test_max_nodes`, which covers the wide query, the limit being hit, and the default.

Choices and limits to be aware of:
- **Counting covers only nodes built through `self.expression()`.** Parser code that constructs `exp.*` nodes directly is not counted, so the limit is a close approximation rather than an exact node count. I didn't audit the ~370 direct constructions in the parser.
- **The error is raised even under `ErrorLevel.IGNORE`/`WARN`.** It is not routed through `raise_error`, because a safeguard shouldn't be silenced by the error level.
- **Known gap:** if the limit is crossed inside a speculative parse (`_try_parse`, or the `parse_into` fallback loop), that error can be swallowed. The count stays over the limit, so the next node-building call raises again. Only a final node that is built inside a speculative parse and then never followed by another would slip through. I didn't construct a case for that.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"error_level\\|def __init__\\|def parse\\b\\|def _parse(\\|def parse(\\|max_errors\\|self.sql\\b\" sqlglot/parser.py | head -60 && grep -n \"def parse_one\\|def parse(\\|error_level\\|max_errors\" sqlglot/__init__.py sqlglot/dialects/dialect.py | head -40"}
[tool_result] e02907a20 lithify: probe base
286:        error_level: The desired error level.
291:        max_errors: Maximum number of error messages to include in a raised ParseError.
292:            This is only relevant if error_level is ErrorLevel.RAISE.
297:        "error_level",
299:        "max_errors",
1823:    def __init__(
1825:        error_level: ErrorLevel | None = None,
1827:        max_errors: int = 3,
1830:        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1832:       
…[878 chars elided]…
nit__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/__init__.py:189:    error_level: ErrorLevel | None = None,
sqlglot/__init__.py:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
[tool_use Bash] {"command": "sed -n 270,310p sqlglot/parser.py && sed -n 1815,2000p sqlglot/parser.py && sed -n 2040,2070p sqlglot/parser.py && sed -n 2100,2130p sqlglot/parser.py"}
[tool_result] def _resolve_dialect(dialect: DialectType) -> Dialect:
    from sqlglot.dialects.dialect import Dialect

    return Dialect.get_or_raise(dialect)


SENTINEL_NONE: Token = Token(TokenType.SENTINEL, "SENTINEL")


class Parser:
    """
    Parser consumes a list of tokens produced by the Tokenizer and produces a parsed syntax tree.

    Args:
        error_level: The desired error level.
            Default: ErrorLevel.IMMEDIATE
        error_message_context: The amount of context to capture from a
…[8578 chars elided]…
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
[tool_use Bash] {"command": "sed -n 105,220p sqlglot/__init__.py && grep -n \"ParserArgs\\|class ParserArgs\" -A12 sqlglot/dialects/dialect.py | head -60 && sed -n 1110,1125p sqlglot/dialects/dialect.py && grep -n \"error_level\\|max_errors\" sqlglot/dialects/dialect.py sqlglot/*.py | grep -v \"parser.py\" | head -30"}
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
…[5555 chars elided]…
:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
sqlglot/__main__.py:57:    dest="error_level",
sqlglot/__main__.py:71:error_level = sqlglot.ErrorLevel[args.error_level.upper()]
sqlglot/__main__.py:81:            error_level=error_level,
sqlglot/__main__.py:93:        error_level=error_level,
sqlglot/_typing.py:29:    error_level: ErrorLevel | None
sqlglot/_typing.py:31:    max_errors: int
[tool_use Bash] {"command": "sed -n 20,40p sqlglot/_typing.py && grep -n \"_parse_batch_statements\\|def parse_into\" -A3 sqlglot/parser.py | head -40 && grep -n \"ParseError\" sqlglot/errors.py | head && grep -rn \"self.expression(\\|exp\\.\\w*(\" sqlglot/parser.py | wc -l && grep -n \"self.expression(\" sqlglot/parser.py | wc -l"}
[tool_result] BuilderArgs = Sequence[t.Any]
"""Sequence of arguments passed to builder functions."""


class _DialectArg(t.TypedDict, total=False):
    dialect: DialectType


class ParserNoDialectArgs(t.TypedDict, total=False):
    error_level: ErrorLevel | None
    error_message_context: int
    max_errors: int


class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
    pass


class GeneratorNoDialectArgs(t.TypedDict, total=False):
    pretty: bool | int | None
    identify: str | bool
2012:    de
…[324 chars elided]…
batch_statements(parse_method=parse_method, sep_first_statement=False)
2129-
2130-    def _warn_unsupported(self) -> None:
2131-        if self._tokens_size <= 1:
--
2230:                expressions=self._parse_batch_statements(
2231-                    parse_method=lambda self: self._parse_statement()
2232-                )
2233-            )
37:class ParseError(SqlglotError):
57:    ) -> ParseError:
161:def merge_errors(errors: Sequence[ParseError]) -> list[dict[str, t.Any]]:
     816
     448
[tool_use Bash] {"command": "sed -n 2000,2040p sqlglot/parser.py && sed -n 2072,2100p sqlglot/parser.py && grep -n \"^from\\|^import\\|i64\" sqlglot/parser.py | head -30"}
[tool_result]         Args:
            raw_tokens: The list of tokens.
            sql: The original SQL string.

        Returns:
            The list of the produced syntax trees.
        """
        return self._parse(
            parse_method=self.__class__._parse_statement, raw_tokens=raw_tokens, sql=sql
        )

    def parse_into(
        self,
        expression_types: exp.IntoType,
        raw_tokens: list[Token],
        sql: str | None = None,
    ) -> list[exp.Expr | None]:
        """
        
…[2333 chars elided]…
_trie
21:from sqlglot.time import format_time
22:from sqlglot.tokens import Token, Tokenizer, TokenType
23:from sqlglot.trie import TrieResult, in_trie
24:from collections.abc import Sequence
25:from builtins import type as Type
1837:        self._tokens_size: i64 = 0
1838:        self._index: i64 = 0
1845:        self._chunk_index: i64 = 0
1861:    def _advance(self, times: i64 = 1) -> None:
1880:        self._tokens_size = i64(len(self._tokens))
1884:    def _retreat(self, index: i64) -> None:
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new,count=1):\n    global s\n    assert s.count(old)==count,(s.count(old),old)\n    s=s.replace(old,new)\nrep('''            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n''','''            This is only relevant if error_level is ErrorLevel.RAISE.\n      
…[1790 chars elided]…
      if self.max_nodes is not None and self._node_count > self.max_nodes:\n            raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n\n        return instance\n''')\nopen(p,'w').write(s)\n\np='sqlglot/_typing.py'\ns=open(p).read()\nrep('''    max_errors: int\n''','''    max_errors: int\n    max_nodes: int | None\n''')\nopen(p,'w').write(s)\nEOF\ngit diff --stat"}
[tool_result]  sqlglot/_typing.py |  1 +
 sqlglot/parser.py  | 13 +++++++++++++
 2 files changed, 14 insertions(+)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -c \"\nimport sqlglot\nfrom sqlglot import parse_one\nfrom sqlglot.errors import ParseError\ncols=', '.join(f'c{i}' for i in range(500))\nq=f'SELECT {cols} FROM t WHERE a = 1'\nprint(len(parse_one(q, max_nodes=10**6).sql()))\ntry:\n    parse_one('SELECT ' + ' + '.join(['1']*5000), max_nodes=1000); print('no raise')\nexcept ParseError as e: print('raised:', str(e)[:80])\nprint(parse_one('SELECT 1 + 2', max_nodes=50).sql())\ntry: parse_one('SELECT 1', read='duckdb', max_nodes=1)\nexcept ParseError as e: print('raised2:', e.errors[0]['description'])\n\""}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 12, in <module>
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-163414-parser-add-a-safeguard-against-p/base-1/sqlglot/__init__.py", line 176, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-d5521a213087/20261028-163414-parser-add-a-safeguard-against-p/base-1/sqlglot/dialects/dialect.py", line 1116, in parse
    
…[1820 chars elided]…
20261028-163414-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", line 2081, in expression
    raise ParseError(f"Maximum number of AST nodes ({self.max_nodes}) exceeded")
sqlglot.errors.ParseError: Maximum number of AST nodes (1) exceeded

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<string>", line 13, in <module>
IndexError: list index out of range
2914
raised: Maximum number of AST nodes (1000) exceeded
SELECT 1 + 2
[tool_use Bash] {"command": "sed -n 37,75p sqlglot/errors.py"}
[tool_result] class ParseError(SqlglotError):
    def __init__(
        self,
        message: str,
        errors: list[dict[str, t.Any]] | None = None,
    ):
        super().__init__(message)
        self.errors = errors or []

    @classmethod
    def new(
        cls,
        message: str,
        description: str | None = None,
        line: int | None = None,
        col: int | None = None,
        start_context: str | None = None,
        highlight: str | None = None,
        end_context: str | None =
…[44 chars elided]…
 None,
    ) -> ParseError:
        return cls(
            message,
            [
                {
                    "description": description,
                    "line": line,
                    "col": col,
                    "start_context": start_context,
                    "highlight": highlight,
                    "end_context": end_context,
                    "into_expression": into_expression,
                }
            ],
        )


class TokenError(SqlglotError):
    pass
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''            raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")'''\nnew='''            message = f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\"\n            raise ParseError.new(message, description=message)'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\
…[163 chars elided]…
ry: parse_one('SELECT 1', read='duckdb', max_nodes=1)\nexcept ParseError as e: print('raised2:', e.errors[0]['description'], '|', str(e))\ntry: parse_one('SELECT ' + ' + '.join(['1']*5000), max_nodes=1000); print('no raise')\nexcept ParseError as e: print('raised:', str(e))\nprint(parse_one('SELECT 1 + 2', max_nodes=50).sql())\n\" && $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] raised2: Maximum number of AST nodes (1) exceeded | Maximum number of AST nodes (1) exceeded
raised: Maximum number of AST nodes (1000) exceeded
SELECT 1 + 2

sqlglot/parser.py:1852: AttributeError
=========================== short test summary info ============================
FAILED tests/test_parser.py::TestParser::test_expression - AttributeError: 'P...
1 failed, 1081 passed, 17840 subtests passed in 38.69s
[tool_use Bash] {"command": "grep -n \"def test_expression\" -A12 tests/test_parser.py | head -30; sed -n 1845,1855p sqlglot/parser.py"}
[tool_result] 256:    def test_expression(self):
257-        ignore = Parser(error_level=ErrorLevel.IGNORE)
258-        self.assertIsInstance(ignore.expression(exp.Hint(expressions=[])), exp.Hint)
259-        self.assertIsInstance(ignore.expression(exp.Hint(y="")), exp.Hint)
260-        self.assertIsInstance(ignore.expression(exp.Hint()), exp.Hint)
261-
262-        default = Parser(error_level=ErrorLevel.RAISE)
263-        with self.assertRaises(TypeError):
264-            default.expression(exp.Hint(y=""))
2
…[65 chars elided]…
essions=[])), exp.Hint)
266-        default.expression(exp.Hint())
267-        self.assertEqual(len(default.errors), 2)
268-
        self._curr: Token = SENTINEL_NONE
        self._next: Token = SENTINEL_NONE
        self._prev: Token = SENTINEL_NONE
        self._prev_comments: list[str] = []
        self._pipe_cte_counter: int = 0
        self._chunks: list[list[Token]] = []
        self._chunk_index: i64 = 0
        self._node_count: i64 = 0

    def reset(self) -> None:
        self.sql = ""
[assistant] The one failure is my omission: `_node_count` isn't in `__slots__`. Adding it.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''        \"_chunks\",\n'''\nassert s.count(old)==1\ns=s.replace(old,old+'''        \"_chunk_index\",\n        \"_node_count\",\n''') if '\"_chunk_index\",' not in s else s.replace(old,old+'''        \"_node_count\",\n''')\nopen(p,'w').write(s)\nEOF\ngrep -n '\"_chunks\"' -A4 sqlglot/parser.py; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2"}
[tool_result] 314:        "_chunks",
315-        "_node_count",
316-        "_chunk_index",
317-        "_tokens_size",
318-    )
.................               [100%]
1082 passed, 17840 subtests passed in 39.02s
[assistant] All 1082 tests pass. Now I'll add a regression test for the new option.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|    def test_\" tests/test_parser.py | head -20"}
[tool_result] 1:import time
2:import unittest
3:from unittest.mock import patch
5:from sqlglot import Parser, exp, parse, parse_one
6:from sqlglot.errors import ErrorLevel, ParseError
7:from sqlglot.parser import logger as parser_logger
8:from tests.helpers import assert_logger_contains
12:    def test_parse_empty(self):
16:    def test_parse_into(self):
45:    def test_parse_into_error(self):
66:    def test_parse_into_errors(self):
94:    def test_column(self):
100:    def test_tuple(self):
103:    def test_structs(self):
112:    def test_float(self):
115:    def test_unnest(self):
122:    def test_unnest_projection(self):
128:    def test_unary_plus(self):
131:    def test_table(self):
135:    def test_union(self):
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/test_parser.py'\ns=open(p).read()\nold='''    def test_column(self):\n'''\nnew='''    def test_max_nodes(self):\n        wide = f\"SELECT {', '.join(f'c{i}' for i in range(500))} FROM t\"\n        self.assertEqual(len(parse_one(wide, max_nodes=100_000).expressions), 500)\n\n        with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n 
…[320 chars elided]…
==1\nopen(p,'w').write(s.replace(old,new+old))\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -2; (ruff --version && ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && ruff check sqlglot/parser.py tests/test_parser.py) 2>&1 | tail -4; git diff --stat"}
[tool_result] ...............................          [100%]
64 passed, 71 subtests passed in 0.13s
ruff 0.15.6
3 files already formatted
All checks passed!
 sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 15 +++++++++++++++
 tests/test_parser.py | 12 ++++++++++++
 3 files changed, 28 insertions(+)
[tool_use Bash] {"command": "git diff sqlglot/"}
[tool_result] diff --git a/sqlglot/_typing.py b/sqlglot/_typing.py
index fe7e80ee3..578d6c262 100644
--- a/sqlglot/_typing.py
+++ b/sqlglot/_typing.py
@@ -29,6 +29,7 @@ class ParserNoDialectArgs(t.TypedDict, total=False):
     error_level: ErrorLevel | None
     error_message_context: int
     max_errors: int
+    max_nodes: int | None
 
 
 class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 107ad1ec0..4c093e9ae 100644
--- a/sqlglot/parser.
…[1906 chars elided]…
     instance.add_comments(comments) if comments else self._add_comments(instance)
         if not instance.is_primitive:
             instance = self.validate_expression(instance)
+
+        self._node_count += 1
+        if self.max_nodes is not None and self._node_count > self.max_nodes:
+            message = f"Maximum number of AST nodes ({self.max_nodes}) exceeded"
+            raise ParseError.new(message, description=message)
+
         return instance
 
     def _parse_batch_statements(
[assistant] The parser now takes a `max_nodes` option. Parsing raises a `ParseError` containing "Maximum number of AST nodes" once the limit is exceeded. The full suite passes (1082 tests), and ruff format and check are clean.

`max_nodes` is accepted by `Parser(...)`, `parse`, and `parse_one`, which pass it through `**opts`. The default is `None`, so nothing changes unless you set it. A 500-column SELECT parses with `max_nodes=100_000`, and the same query with `max_nodes=100` raises.

What I changed:
- **`sqlglot/parser.py`**: `Parser.__init__` takes `max_nodes`. The count increments in `Parser.expressio
…[548 chars elided]…
 didn't audit the ~370 direct constructions in the parser.
- **The error is raised even under `ErrorLevel.IGNORE`/`WARN`.** It is not routed through `raise_error`, because a safeguard shouldn't be silenced by the error level.
- **Known gap:** if the limit is crossed inside a speculative parse (`_try_parse`, or the `parse_into` fallback loop), that error can be swallowed. The count stays over the limit, so the next node-building call raises again. Only a final node that is built inside a speculative parse and then never followed by another would slip through. I didn't construct a case for that.
