# trajectory base-1

final message:
The `max_nodes` option is in place: `parse_one(sql, max_nodes=N)` raises a `ParseError` containing "Maximum number of AST nodes" once parsing builds more than N nodes. Normal queries are unchanged when the option is unset, and a 500-column SELECT parses fine at any limit at or above its tree size (1004 nodes). The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

What changed:

- **`sqlglot/parser.py`**: `Parser` takes a `max_nodes` argument, default `None`. Nodes are counted in `Parser.expression()` so parsing stops early once the limit is hit. After parsing, the result trees are walked as well, which catches nodes built by direct constructor calls (`exp.Literal(...)` and similar) that bypass `expression()`. The walk only runs when the limit is set.
- **`sqlglot/_typing.py`**: `max_nodes` is added to `ParserNoDialectArgs`, so `parse`, `parse_one` and `parse_into` accept it.
- **`tests/test_parser.py`**: `test_max_nodes` covers a 500-column query at the exact boundary, a limit one below it, a small `IN` list, and multiple statements.

Two things to know:

- I checked the minimum passing limit for four queries (simple select, 500 columns, 500 CAST expressions, a 2000-item `IN` list). In each case it equalled the final tree size, so speculative parse attempts aren't inflating the count in these cases.
- `transpile()` doesn't forward `max_nodes`, since it only passes `error_level` through. Say if you want it added there too.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"error_level\\|def __init__\\|def parse(\\|def _parse(\\|def _parse_statement\\|def expression(\\|def validate_expression\\|def _add_comments\\|max_errors\\|class Parser\\|def raise_error\" sqlglot/parser.py | head -80 && grep -n \"def parse_one\\|def parse(\\|def maybe_parse\\|max_errors\\|error_level\" sqlglot/__init__.py sqlglot/dialects/dialect.py | head -30"}
[tool_result] 281:class Parser:
286:        error_level: The desired error level.
291:        max_errors: Maximum number of error messages to include in a raised ParseError.
292:            This is only relevant if error_level is ErrorLevel.RAISE.
297:        "error_level",
299:        "max_errors",
1823:    def __init__(
1825:        error_level: ErrorLevel | None = None,
1827:        max_errors: int = 3,
1830:        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1832:        self.max_er
…[914 chars elided]…
nit__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/__init__.py:189:    error_level: ErrorLevel | None = None,
sqlglot/__init__.py:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "offset": 1820, "limit": 260}
[tool_result] 1820	    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
1821	    SET_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SET_PARSERS)
1822	
1823	    def __init__(
1824	        self,
1825	        error_level: ErrorLevel | None = None,
1826	        error_message_context: int = 100,
1827	        max_errors: int = 3,
1828	        dialect: DialectType = None,
1829	    ):
1830	        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1831	      
…[9422 chars elided]…
_add_comments(instance)
2068	        if not instance.is_primitive:
2069	            instance = self.validate_expression(instance)
2070	        return instance
2071	
2072	    def _parse_batch_statements(
2073	        self,
2074	        parse_method: t.Callable[[Parser], exp.Expr | None],
2075	        sep_first_statement: bool = True,
2076	    ) -> list[exp.Expr | None]:
2077	        expressions = []
2078	
2079	        # Chunkification binds if/while statements with the first statement of the body
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "offset": 281, "limit": 30}
[tool_result] 281	class Parser:
282	    """
283	    Parser consumes a list of tokens produced by the Tokenizer and produces a parsed syntax tree.
284	
285	    Args:
286	        error_level: The desired error level.
287	            Default: ErrorLevel.IMMEDIATE
288	        error_message_context: The amount of context to capture from a query string when displaying
289	            the error message (in number of characters).
290	            Default: 100
291	        max_errors: Maximum number of error messages to
…[20 chars elided]…
 ParseError.
292	            This is only relevant if error_level is ErrorLevel.RAISE.
293	            Default: 3
294	    """
295	
296	    __slots__ = (
297	        "error_level",
298	        "error_message_context",
299	        "max_errors",
300	        "dialect",
301	        "sql",
302	        "errors",
303	        "_tokens",
304	        "_index",
305	        "_curr",
306	        "_next",
307	        "_prev",
308	        "_prev_comments",
309	        "_pipe_cte_counter",
310	        "_chunks",
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/__init__.py", "offset": 105, "limit": 110}
[tool_result] 105	    return Dialect.get_or_raise(read or dialect).tokenize(sql)
106	
107	
108	def parse(
109	    sql: str,
110	    read: DialectType = None,
111	    dialect: DialectType = None,
112	    **opts: Unpack[ParserNoDialectArgs],
113	) -> list[Expr | None]:
114	    """
115	    Parses the given SQL string into a collection of syntax trees, one per parsed SQL statement.
116	
117	    Args:
118	        sql: the SQL code string to parse.
119	        read: the SQL dialect to apply during parsing (eg. "spa
…[2959 chars elided]…
r_level: the desired error level of the parser.
203	        **opts: other `sqlglot.generator.Generator` options.
204	
205	    Returns:
206	        The list of transpiled SQL statements.
207	    """
208	    write = (read if write is None else write) if identity else write
209	    write = Dialect.get_or_raise(write)
210	    return [
211	        write.generate(expression, copy=False, **opts) if expression else ""
212	        for expression in parse(sql, read, error_level=error_level)
213	    ]
214	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "offset": 2104, "limit": 140}
[tool_result] 2104	    def _parse(
2105	        self,
2106	        parse_method: t.Callable[[Parser], exp.Expr | None],
2107	        raw_tokens: list[Token],
2108	        sql: str | None = None,
2109	    ) -> list[exp.Expr | None]:
2110	        self.reset()
2111	        self.sql = sql or ""
2112	
2113	        total = len(raw_tokens)
2114	        chunks: list[list[Token]] = [[]]
2115	
2116	        for i, token in enumerate(raw_tokens):
2117	            if token.token_type == TokenType.SEMICOLON:
2118	         
…[4640 chars elided]…
  expressions=self._parse_batch_statements(
2231	                    parse_method=lambda self: self._parse_statement()
2232	                )
2233	            )
2234	        )
2235	
2236	    def _parse_whileblock(self) -> exp.WhileBlock:
2237	        return self.expression(
2238	            exp.WhileBlock(this=self._parse_condition(), body=self._parse_block())
2239	        )
2240	
2241	    def _parse_statement(self) -> exp.Expr | None:
2242	        if not self._curr:
2243	            return None
[tool_use Bash] {"command": "grep -rn \"ParserNoDialectArgs\\|ParserArgs\" sqlglot/*.py sqlglot/dialects/dialect.py | head; grep -rn \"class ParseError\" -A30 sqlglot/errors.py | head -60; grep -rn \"def _parse(\" -A3 sqlglot/parser.py; grep -c \"self.expression(\" sqlglot/parser.py; grep -c \"exp\\.[A-Z][A-Za-z]*(\" sqlglot/parser.py; grep -rn \"ErrorLevel\" sqlglot/dialects/dialect.py | head -5"}
[tool_result] sqlglot/__init__.py:74:    from sqlglot._typing import E, GeneratorArgs, ParserNoDialectArgs
sqlglot/__init__.py:112:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:136:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:146:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:155:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/_typing.py:28:class ParserNoDialectArgs(t.TypedDict, total=False):
sqlglot/_typing.py:34:class ParserArgs(ParserNoDialectArgs, _DialectArg,
…[1635 chars elided]…
   "line": line,
sqlglot/errors.py-64-                    "col": col,
sqlglot/errors.py-65-                    "start_context": start_context,
sqlglot/errors.py-66-                    "highlight": highlight,
sqlglot/errors.py-67-                    "end_context": end_context,
sqlglot/parser.py:2104:    def _parse(
sqlglot/parser.py-2105-        self,
sqlglot/parser.py-2106-        parse_method: t.Callable[[Parser], exp.Expr | None],
sqlglot/parser.py-2107-        raw_tokens: list[Token],
448
533
[tool_use Bash] {"command": "grep -n \"def _parse_primary\\|def _parse_column(\\|def _parse_column_reference\\|def _parse_field(\\|def _parse_id_var\\|def _parse_csv\\|def _parse_in(\" sqlglot/parser.py; grep -n \"def walk\\|def dfs\\|def bfs\" -A12 sqlglot/expressions.py | head -60; sed -n 2080,2103p sqlglot/parser.py"}
[tool_result] 5749:    def _parse_in(self, this: exp.Expr | None, alias: bool = False) -> exp.In:
6397:    def _parse_column(self) -> exp.Expr | None:
6486:    def _parse_column_reference(self) -> exp.Expr | None:
6682:    def _parse_primary(self) -> exp.Expr | None:
6704:    def _parse_field(
7342:    def _parse_primary_key_part(self) -> exp.Expr | None:
7357:    def _parse_primary_key(
8230:    def _parse_id_var(
8291:    def _parse_primary_or_var(self) -> exp.Expr | None:
8332:    def _parse_csv(
ugrep: wa
…[296 chars elided]…
ce_chunk()

            if self._match(TokenType.ELSE, advance=False):
                return expressions

            if expressions and not self._next and self._match(TokenType.END):
                expressions.append(exp.EndStatement())
                continue

            expressions.append(parse_method(self))

            if self._index < self._tokens_size:
                self.raise_error("Invalid expression / Unexpected token")

            self.check_errors()

        return expressions
[tool_use Bash] {"command": "sed -n 6682,6704p sqlglot/parser.py; sed -n 6397,6420p sqlglot/parser.py; grep -n \"def walk\\|def dfs\\|def bfs\" -A14 sqlglot/expressions/core.py 2>/dev/null | head -60 || ls sqlglot/expressions*"}
[tool_result]     def _parse_primary(self) -> exp.Expr | None:
        if self._match_set(self.PRIMARY_PARSERS):
            token_type = self._prev.token_type
            primary = self.PRIMARY_PARSERS[token_type](self, self._prev)

            if token_type == TokenType.STRING:
                expressions = [primary]
                while self._match(TokenType.STRING):
                    expressions.append(exp.Literal.string(self._prev.text))

                if len(expressions) > 1:
                    re
…[3044 chars elided]…
       Returns:
1005-            The generator object.
1006-        """
1007-        stack = [self]
1008-
1009-        while stack:
1010-            node = stack.pop()
1011-            yield node
1012-            if prune and prune(node):
1013-                continue
--
1017:    def bfs(self, prune: t.Callable[[Expr], bool] | None = None) -> Iterator[Expr]:
1018-        """
1019-        Returns a generator object which visits all nodes in this tree in
1020-        the BFS (Breadth-first) order.
[tool_use Bash] {"command": "sed -n 20,40p sqlglot/_typing.py; sed -n 1110,1125p sqlglot/dialects/dialect.py; grep -n \"def parser(\" -A4 sqlglot/dialects/dialect.py; ls tests | head -50; grep -rn \"max_errors\" tests/*.py | head -5; grep -n \"max_errors\\|error_message_context\" CHANGELOG.md docs 2>/dev/null | head -3"}
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
           
…[943 chars elided]…
oints.py
test_dialect_imports.py
test_diff.py
test_docs.py
test_errors.py
test_executor.py
test_expressions.py
test_generator.py
test_helper.py
test_integration_loader.py
test_jsonpath.py
test_lineage.py
test_optimizer.py
test_parser.py
test_schema.py
test_serde.py
test_time.py
test_tokens.py
test_transforms.py
test_transpile.py
tests/test_transpile.py:1050:        more_than_max_errors = "(((("
tests/test_transpile.py:1081:            transpile(more_than_max_errors, error_level=ErrorLevel.RAISE)
[assistant] Plan: add a `max_nodes` option to `Parser` (default `None`, so no overhead when unset). It counts nodes in `Parser.expression()` for early exit, and does an exact walk of the result trees at the end to catch nodes built by direct construction. Both raise `ParseError` with the required message.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py", "old_string": "    max_errors: int\n\n\nclass ParserArgs(", "new_string": "    max_errors: int\n    max_nodes: int | None\n\n\nclass ParserArgs("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n\n    __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n    
…[515 chars elided]…
 __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n        \"max_nodes\",\n        \"dialect\",\n        \"sql\",\n        \"errors\",\n        \"_tokens\",\n        \"_index\",\n        \"_curr\",\n        \"_next\",\n        \"_prev\",\n        \"_prev_comments\",\n        \"_pipe_cte_counter\",\n        \"_node_count\",\n        \"_chunks\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        max_errors: int = 3,\n        dialect: DialectType = None,\n    ):\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n  
…[1879 chars elided]…
n    def reset(self) -> None:\n        self.sql = \"\"\n        self.errors = []\n        self._tokens = []\n        self._tokens_size = 0\n        self._index = 0\n        self._curr = SENTINEL_NONE\n        self._next = SENTINEL_NONE\n        self._prev = SENTINEL_NONE\n        self._prev_comments = []\n        self._pipe_cte_counter = 0\n        self._node_count = 0\n        self._chunks = []"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the counting in `expression()` and the final check in `_parse`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "    def expression(\n        self,\n        instance: E,\n        token: Token | None = None,\n        comments: list[str] | None = None,\n    ) -> E:\n        if token:", "new_string": "    def _check_max_nodes(self, n
…[93 chars elided]…
es:\n            raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n\n    def expression(\n        self,\n        instance: E,\n        token: Token | None = None,\n        comments: list[str] | None = None,\n    ) -> E:\n        if self.max_nodes is not None:\n            self._node_count += 1\n            self._check_max_nodes(self._node_count)\n\n        if token:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        self._chunks = chunks\n\n        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)", "new_string": "        self._chunks = chunks\n\n        expressions = self._parse_batc
…[21 chars elided]…
      parse_method=parse_method, sep_first_statement=False\n        )\n\n        # Nodes built without self.expression() (e.g. direct constructor calls) are only visible in the trees\n        if self.max_nodes is not None:\n            built = sum(1 for e in expressions if e for _ in e.walk(bfs=False))\n            self._check_max_nodes(max(built, self._node_count))\n\n        return expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now let me measure node counts on normal and wide queries, to see how much the speculative-parse counting inflates the number.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp, parse_one\nfrom sqlglot.errors import ParseError\ndef true_count(e): return sum(1 for _ in e.walk(bfs=False))\nqs = {\n 'simple': 'SELECT a, b + 1 AS c FROM d WHERE x = 1',\n 'wide500': 'SELECT ' + ', '.join(f'col{i}' for i in range(500)) + '
…[376 chars elided]…
     mid = (lo+hi)//2\n        try:\n            parse_one(q, max_nodes=mid); hi = mid\n        except ParseError: lo = mid+1\n    print(k, 'tree nodes', tc, 'min max_nodes', lo)\ntry:\n    parse_one(qs['wide500'], max_nodes=100)\nexcept ParseError as ex: print('ERR:', ex)\nprint(parse_one(qs['wide500'], max_nodes=10**5).sql()[:40])\nprint(sqlglot.parse_one('SELECT 1', max_nodes=None).sql())\n\""}
[tool_result] simple tree nodes 17 min max_nodes 17
wide500 tree nodes 1004 min max_nodes 1004
wide500_expr tree nodes 4004 min max_nodes 4004
in_list tree nodes 2009 min max_nodes 2009
ERR: Maximum number of AST nodes (100) exceeded
SELECT col0, col1, col2, col3, col4, col
SELECT 1
[assistant] The minimum passing limit equals the final tree size in every case, so speculative parsing isn't inflating the count here. Now I'll add tests and run the project's check command.
[tool_use Bash] {"command": "sed -n 1,20p tests/test_parser.py && grep -n \"^class \\|    def test_\" tests/test_parser.py | tail -6 && tail -5 tests/test_parser.py"}
[tool_result] import time
import unittest
from unittest.mock import patch

from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains


class TestParser(unittest.TestCase):
    def test_parse_empty(self):
        with self.assertRaises(ParseError):
            parse_one("")

    def test_parse_into(self):
        self.assertIsInstance(parse_one("(1)", into=exp.Tuple), ex
…[225 chars elided]…
est_qualified_function(self):
1048:    def test_pivot_missing_agg_func(self):
1054:    def test_multiple_query_modifiers(self):
1067:    def test_parse_into_grant_principal(self):
1082:    def test_parse_into_grant_privilege(self):
    def test_parse_into_grant_privilege(self):
        self.assertIsInstance(parse_one("SELECT", into=exp.GrantPrivilege), exp.GrantPrivilege)
        self.assertIsInstance(
            parse_one("ALL PRIVILEGES", into=exp.GrantPrivilege), exp.GrantPrivilege
        )
[tool_use Bash] {"command": "cat >> tests/test_parser.py <<'EOF'\n\n    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"col{i}\" for i in range(500)) + \" FROM t\"\n        node_count = sum(1 for _ in parse_one(wide).walk(bfs=False))\n\n        self.assertEqual(parse_one(wide, max_nodes=node_count).sql(), parse_one(wide).sql())\n        self.assertEqual(parse_one(wide, max_nodes=10**6).sql(
…[210 chars elided]…
Error, \"Maximum number of AST nodes\"):\n            parse_one(\"SELECT a, b, c FROM t WHERE x IN (1, 2, 3, 4)\", max_nodes=5)\n\n        self.assertEqual(parse(\"SELECT 1; SELECT 2\", max_nodes=20).__len__(), 2)\nEOF\nPYTHONPATH=. timeout 600 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -5"}
[tool_result] (eval):18: command not found: timeout
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py", "old_string": "        self.assertEqual(parse(\"SELECT 1; SELECT 2\", max_nodes=20).__len__(), 2)", "new_string": "        self.assertEqual(len(parse(\"SELECT 1; SELECT 2\", max_nodes=20)), 2)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-155436-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -5; PYTHONPATH=. <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5"}
[tool_result] ................................. [ 51%]
...............................          [100%]
64 passed, 71 subtests passed in 0.22s
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 39.07s
[assistant] Full suite passes (1083 tests). Next, lint and type checks on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py) 2>&1 | tail -8; ($PY -m mypy --version && $PY -m mypy sqlglot/parser.py) 2>&1 | tail -4; git -C . diff --stat"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
mypy 2.3.0.post2 (compiled: yes)
Success: no issues found in 1 source file
 sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 27 ++++++++++++++++++++++++++-
 tests/test_parser.py | 15 +++++++++++++++
 3 files changed, 42 insertions(+), 1 deletion(-)
[assistant] The `max_nodes` option is in place: `parse_one(sql, max_nodes=N)` raises a `ParseError` containing "Maximum number of AST nodes" once parsing builds more than N nodes. Normal queries are unchanged when the option is unset, and a 500-column SELECT parses fine at any limit at or above its tree size (1004 nodes). The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

What changed:

- **`sqlglot/parser.py`**: `Parser` takes a `max_nodes` argument, default `None`. Nodes are counted in `Parser.expression()` so parsing stops early once the
…[308 chars elided]…
`, `parse_one` and `parse_into` accept it.
- **`tests/test_parser.py`**: `test_max_nodes` covers a 500-column query at the exact boundary, a limit one below it, a small `IN` list, and multiple statements.

Two things to know:

- I checked the minimum passing limit for four queries (simple select, 500 columns, 500 CAST expressions, a 2000-item `IN` list). In each case it equalled the final tree size, so speculative parse attempts aren't inflating the count in these cases.
- `transpile()` doesn't forward `max_nodes`, since it only passes `error_level` through. Say if you want it added there too.
