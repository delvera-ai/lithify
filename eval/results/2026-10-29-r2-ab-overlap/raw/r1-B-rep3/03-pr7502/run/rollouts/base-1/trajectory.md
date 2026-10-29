# trajectory base-1

final message:
Added the `max_nodes` option to the parser. Passing `max_nodes=N` to `parse_one` (or `parse`, or `Parser`) raises a `ParseError` containing "Maximum number of AST nodes" once more than N nodes have been built. The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed.

**Changes**
- `sqlglot/parser.py`: new `max_nodes: int | None = None` argument on `Parser`, stored in `__slots__`. The count is kept in `_node_count` and reset per parse. The check sits in `Parser.expression()`, the main node builder, so the parser stops as soon as the limit is crossed rather than building the whole tree first. The error is raised even under `ErrorLevel.IGNORE` or `WARN`.
- `sqlglot/_typing.py`: `max_nodes` added to `ParserNoDialectArgs` so it type-checks through `parse_one` and the dialect entry points.
- `tests/test_parser.py`: `test_max_nodes` covers a 500-column query that parses with `max_nodes=10_000`, and a 5000-term expression that raises at `max_nodes=1_000`, including under `ErrorLevel.IGNORE`.

**Limits of the count**
- It is a lower bound. Nodes built by calling `exp.X(...)` directly, rather than through `self.expression()`, are not counted. On the 500-column query, the smallest accepted limit was 2513 while the built tree has 3016 nodes (about 17% low). On the 5000-term expression, the count matched the tree exactly.
- Nodes built during backtracking attempts that get discarded still count. This can only make the limit stricter, never looser.

**Choices I made**
- The default is `None`, so existing behaviour is unchanged unless the option is passed.
- I did not pick a recommended production value. Callers should choose one based on the largest legitimate query they expect.

## events
[assistant] I'll start by reading the parser's entry points and how it counts and raises errors.
[tool_use Bash] {"command": "git status --short | head && grep -n \"def parse_one\\|def parse\\b\\|def parse(\\|error_level\\|max_errors\\|def __init__\\|def _parse(\\|def raise_error\\|def expression(\\|def validate_expression\\|def _add_comments\\|self._index\\b\" sqlglot/parser.py | head -80; grep -n \"def parse_one\\|def parse(\" -A25 sqlglot/__init__.py | head -80", "description": "Inspect repo state and parser entry points"}
[tool_use Bash] {"command": "grep -n \"def parse_one\\|def parse(\" -A30 sqlglot/__init__.py sqlglot/dialects/dialect.py | head -120; grep -n \"class ParseError\" -A20 sqlglot/errors.py", "description": "Read parse_one, parse and ParseError definitions"}
[tool_result] sqlglot/__init__.py:108:def parse(
sqlglot/__init__.py-109-    sql: str,
sqlglot/__init__.py-110-    read: DialectType = None,
sqlglot/__init__.py-111-    dialect: DialectType = None,
sqlglot/__init__.py-112-    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py-113-) -> list[Expr | None]:
sqlglot/__init__.py-114-    """
sqlglot/__init__.py-115-    Parses the given SQL string into a collection of syntax trees, one per parsed SQL statement.
sqlglot/__init__.py-116-
sqlglot/__init__.py-117- 
…[5796 chars elided]…
Any]] | None = None,
42-    ):
43-        super().__init__(message)
44-        self.errors = errors or []
45-
46-    @classmethod
47-    def new(
48-        cls,
49-        message: str,
50-        description: str | None = None,
51-        line: int | None = None,
52-        col: int | None = None,
53-        start_context: str | None = None,
54-        highlight: str | None = None,
55-        end_context: str | None = None,
56-        into_expression: str | None = None,
57-    ) -> ParseError:
[tool_result] okrg: regex parse error:
    (?:def parse_one|def parse\b|def parse(|error_level|max_errors|def __init__|def _parse(|def raise_error|def expression(|def validate_expression|def _add_comments|self._index\b)
                                                                                          ^
error: unclosed group
0 matches for 'def parse_one\|def parse\b\|def parse(\|error_level\|max_errors\|def __init__\|def _parse(\|def raise_error\|def expression(\|def validate_expression\|def _add_comme
…[1649 chars elided]…
, "presto", "mysql").
163-        dialect: the SQL dialect (alias for read)
164-        into: the SQLGlot Expr to parse into.
165-        **opts: other `sqlglot.parser.Parser` options.
166-
167-    Returns:
168-        A single syntax tree if one statement is parsed, otherwise a Block expression containing all parsed syntax trees.
169-    """
170-
171-    dialect = Dialect.get_or_raise(read or dialect)
172-
173-    if into:
174-        result = dialect.parse_into(into, sql, **opts)
175-    else:
[assistant] The grep pattern was malformed. I'll retry with fixed-string matching to find the parser internals.
[tool_use Bash] {"command": "grep -nE \"def (__init__|_parse|raise_error|expression|validate_expression|_add_comments|parse|parse_into|_parse_statement)\\b|max_errors|error_level|self\\._index = |self\\._tokens\" sqlglot/parser.py | head -80; echo ---; grep -n \"Parser\\b.*Unpack\\|class ParserArgs\\|ParserNoDialectArgs\" -A12 sqlglot/parser.py sqlglot/dialects/dialect.py | head -60", "description": "Locate parser core methods and option definitions"}
[tool_result] 286:        error_level: The desired error level.
291:        max_errors: Maximum number of error messages to include in a raised ParseError.
292:            This is only relevant if error_level is ErrorLevel.RAISE.
297:        "error_level",
299:        "max_errors",
1823:    def __init__(
1825:        error_level: ErrorLevel | None = None,
1827:        max_errors: int = 3,
1830:        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1832:        self.max_errors: int = max_er
…[1303 chars elided]…
_tokens_size:
2104:    def _parse(
2131:        if self._tokens_size <= 1:
2136:        sql = self._find_sql(self._tokens[0], self._tokens[-1])[: self.error_message_context]
2241:    def _parse_statement(self) -> exp.Expr | None:
2820:            pre_volatile_token = self._tokens[self._index - 2]
4091:        end = self._tokens[self._index - 1]
7422:            map_token = seq_get(self._tokens, self._index - 2)
8752:            mode = f"WITH {self._tokens[self._index - 2].text.upper()} MODE"
---
[tool_use Bash] {"command": "sed -n 270,310p sqlglot/parser.py; echo ----; sed -n 1820,1880p sqlglot/parser.py; echo ----; sed -n 1945,2140p sqlglot/parser.py", "description": "Read parser init, error handling, expression builder"}
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
…[9089 chars elided]…
ment=False)

    def _warn_unsupported(self) -> None:
        if self._tokens_size <= 1:
            return

        # We use _find_sql because self.sql may comprise multiple chunks, and we're only
        # interested in emitting a warning for the one being currently processed.
        sql = self._find_sql(self._tokens[0], self._tokens[-1])[: self.error_message_context]

        logger.warning(
            f"'{sql}' contains unsupported syntax. Falling back to parsing as a 'Command'."
        )
[assistant] The natural choke point is `Parser.expression()`, which the parser funnels nearly every node through. Next I'll check the option TypedDicts and `__slots__` that a new keyword must be added to.
[tool_use Bash] {"command": "grep -rn \"class ParserNoDialectArgs\\|class ParserArgs\" -A10 sqlglot/ | head -40; sed -n 310,325p sqlglot/parser.py; grep -n \"^from\\|^import\" sqlglot/parser.py | head -30; grep -c \"self.expression(\" sqlglot/parser.py; grep -cE \"\\bexp\\.[A-Z][A-Za-z]*\\(\" sqlglot/parser.py; ls tests | head -50; grep -rn \"max_errors\\|error_level\" tests/test_parser.py | head", "description": "Inspect option typing, slots, and existing parser tests"}
[tool_result] sqlglot/_typing.py:28:class ParserNoDialectArgs(t.TypedDict, total=False):
sqlglot/_typing.py-29-    error_level: ErrorLevel | None
sqlglot/_typing.py-30-    error_message_context: int
sqlglot/_typing.py-31-    max_errors: int
sqlglot/_typing.py-32-
sqlglot/_typing.py-33-
sqlglot/_typing.py:34:class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
sqlglot/_typing.py-35-    pass
sqlglot/_typing.py-36-
sqlglot/_typing.py-37-
sqlglot/_typing.py-38-class GeneratorNoDialectArgs(t.TypedDict,
…[2782 chars elided]…
ror_level=ErrorLevel.RAISE,
tests/test_parser.py:301:        self.assertEqual(parse_one("as as", error_level=ErrorLevel.IGNORE).sql(), "AS as")
tests/test_parser.py:573:            error_level=ErrorLevel.WARN,
tests/test_parser.py:585:            error_level=ErrorLevel.WARN,
tests/test_parser.py:597:            error_level=ErrorLevel.WARN,
tests/test_parser.py:834:            error_level=ErrorLevel.IGNORE,
tests/test_parser.py:1063:            parse_one(sql, error_level=ErrorLevel.IGNORE).sql(),
[assistant] I have the shape of the change. `expression()` is the single choke point, but about 530 nodes are built with direct `exp.X(...)` calls, so the counter will be an approximation. I'll measure how close it is after implementing. First, the edits: the constructor, slots, `reset()`, and `expression()`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        max_errors: Maximum number of error messages to include in a raised ParseError.\n            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n\n    __slots__ = (\n  
…[850 chars elided]…
sage_context\",\n        \"max_errors\",\n        \"max_nodes\",\n        \"dialect\",\n        \"sql\",\n        \"errors\",\n        \"_tokens\",\n        \"_index\",\n        \"_curr\",\n        \"_next\",\n        \"_prev\",\n        \"_prev_comments\",\n        \"_pipe_cte_counter\",\n        \"_chunks\",\n        \"_chunk_index\",\n        \"_tokens_size\",\n        \"_node_count\",\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        max_errors: int = 3,\n        dialect: DialectType = None,\n    ):\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n  
…[118 chars elided]…
    max_errors: int = 3,\n        dialect: DialectType = None,\n        max_nodes: int | None = None,\n    ):\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n        self.max_errors: int = max_errors\n        self.max_nodes: int | None = max_nodes\n        self.dialect: t.Any = _resolve_dialect(dialect)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        self._chunks: list[list[Token]] = []\n        self._chunk_index: i64 = 0\n\n    def reset(self) -> None:\n        self.sql = \"\"\n        self.errors = []\n        self._tokens = []\n        self._tokens_size =
…[430 chars elided]…
        self.sql = \"\"\n        self.errors = []\n        self._tokens = []\n        self._tokens_size = 0\n        self._index = 0\n        self._curr = SENTINEL_NONE\n        self._next = SENTINEL_NONE\n        self._prev = SENTINEL_NONE\n        self._prev_comments = []\n        self._pipe_cte_counter = 0\n        self._chunks = []\n        self._chunk_index = 0\n        self._node_count = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        comments: list[str] | None = None,\n    ) -> E:\n        if token:\n            instance.update_positions(token)", "new_string": "        comments: list[str] | None = None,\n    ) -> E:\n        if self.max_nodes is not None:\n            self._node_count += 1\n            if self._node_count > self.max_nodes:\n                raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n\n        if token:\n            instance.update_positions(token)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py", "old_string": "    max_errors: int\n\n\nclass ParserArgs(", "new_string": "    max_errors: int\n    max_nodes: int | None\n\n\nclass ParserArgs("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py has been updated successfully.
[assistant] The change is in place. Next I'll measure the real node counts for a 500-column query and a large expression, to choose sensible limits and check the counter against the built tree.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY - <<'EOF'\nimport sqlglot\nfrom sqlglot import parse_one\nfrom sqlglot.errors import ParseError\nwide = \"SELECT \" + \", \".join(f\"c{i} + 1 AS x{i}\" for i in range(500)) + \" FROM t WHERE a = 1 AND b IN (1, 2, 3)\"\ntree = parse_one(wide)\nprint(\"tree nodes:\", sum(1 for _ in tree.walk()))\nfor n in 
…[49 chars elided]…
(wide, max_nodes=n); print(\"ok\", n)\n    except ParseError as e: print(\"err\", n, str(e)[:80])\nbig = \"SELECT \" + \" + \".join([\"1\"]*5000)\nfor n in (1000, 10000, None):\n    try:\n        parse_one(big, max_nodes=n); print(\"ok big\", n)\n    except ParseError as e: print(\"err big\", n, str(e).splitlines()[0][:100])\nEOF", "description": "Measure node counts and test max_nodes behaviour"}
[tool_result] tree nodes: 3016
err 1000 Maximum number of AST nodes (1000) exceeded
ok 5000
ok 10000
err big 1000 Maximum number of AST nodes (1000) exceeded
ok big 10000
ok big None
[assistant] Both queries behave as intended. Next I'll check how the counter compares with the real tree size, by finding the smallest limit each query accepts.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY - <<'EOF'\nfrom sqlglot import parse_one\nfrom sqlglot.errors import ParseError\ndef minimal(sql):\n    lo, hi = 1, 200000\n    while lo < hi:\n        mid = (lo + hi) // 2\n        try:\n            parse_one(sql, max_nodes=mid); hi = mid\n        except ParseError: lo = mid + 1\n    return lo\nwide = \"SELECT \" + \", \".join(f\"c{i} + 1 AS x{i}\" for i in range(500)) + \" FROM t WHERE a = 1 AND b IN (1, 2, 3)\"\nbig = \"SELECT \" + \" + \".join([\"1\"]*5000)\nfor s in (wide, big):\n    print(\"tree nodes:\", sum(1 for _ in parse_one(s).walk()), \"min max_nodes:\", minimal(s))\nEOF", "description": "Compare counter against tree size"}
[tool_result] tree nodes: 3016 min max_nodes: 2513
tree nodes: 10000 min max_nodes: 10000
[assistant] The counter is exact for the pathological case but about 17% low on the wide query, because some nodes are built by direct constructors and never pass through `expression()`. I'll state that in the summary. Next, I'll add tests next to the existing error-handling tests.
[tool_use Bash] {"command": "sed -n 1,20p tests/test_parser.py | grep -n \"import\"; sed -n 250,305p tests/test_parser.py", "description": "View imports and existing error-level tests"}
[tool_result] 1:import time
2:import unittest
3:from unittest.mock import patch
5:from sqlglot import Parser, exp, parse, parse_one
6:from sqlglot.errors import ErrorLevel, ParseError
7:from sqlglot.parser import logger as parser_logger
8:from tests.helpers import assert_logger_contains

        expressions = parse("SELECT 1; ; SELECT 2")

        assert len(expressions) == 3
        assert expressions[1] is None

    def test_expression(self):
        ignore = Parser(error_level=ErrorLevel.IGNORE)
        se
…[1330 chars elided]…
se",
                error_level=ErrorLevel.RAISE,
            ).sql(dialect="clickhouse"),
            "CREATE TABLE t (i UInt8) ENGINE=AggregatingMergeTree() ORDER BY tuple()",
        )

        with self.assertRaises(ParseError):
            parse_one("SELECT A[:")

        self.assertEqual(parse_one("as as", error_level=ErrorLevel.IGNORE).sql(), "AS as")

    def test_space(self):
        self.assertEqual(
            parse_one("SELECT ROW() OVER(PARTITION  BY x) FROM x GROUP  BY y").sql(),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py", "old_string": "        self.assertEqual(parse_one(\"as as\", error_level=ErrorLevel.IGNORE).sql(), \"AS as\")\n\n    def test_space(self):", "new_string": "        self.assertEqual(parse_one(\"as as\", error_level=ErrorLevel.IGNORE
…[308 chars elided]…
   with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            parse_one(big, max_nodes=1_000)\n\n        with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            parse_one(big, max_nodes=1_000, error_level=ErrorLevel.IGNORE)\n\n        self.assertEqual(len(parse_one(big).sql()), len(big) + 3 * 4999 - 4999 * 0)\n\n    def test_space(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py has been updated successfully.
[assistant] The last assertion I wrote in that test is meaningless, so I'm removing it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py", "old_string": "            parse_one(big, max_nodes=1_000, error_level=ErrorLevel.IGNORE)\n\n        self.assertEqual(len(parse_one(big).sql()), len(big) + 3 * 4999 - 4999 * 0)\n", "new_string": "            parse_one(big, max_nodes=1_000, error_level=ErrorLevel.IGNORE)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-172759-parser-add-a-safeguard-against-p/base-1/tests/test_parser.py has been updated successfully.
[assistant] Now I'll run the parser tests and the full suite with the project's check command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run new test and full pytest suite"}
[tool_result] .                                                                        [100%]
1 passed, 63 deselected in 0.18s
.............................................. [ 51%]
...................................................................................................................................... [ 63%]
......................................................... [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 40.89s
[assistant] The full suite passes (1083 tests). The project also runs ruff and mypy through `make style`, so I'll run those on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ls $PY/ | grep -E \"ruff|mypy\"; ($PY/ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && $PY/ruff check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py) 2>&1 | tail -5; ($PY/mypy sqlglot/parser.py sqlglot/_typing.py 2>&1 | tail -3) || true; git diff --stat", "description": "Run ruff and mypy on changed files"}
[tool_result] dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
3 files already formatted
All checks passed!
Success: no issues found in 2 source files
sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 13 +++++++++++++
 tests/test_parser.py | 11 +++++++++++
 3 files changed, 25 insertions(+)
[assistant] Added the `max_nodes` option to the parser. Passing `max_nodes=N` to `parse_one` (or `parse`, or `Parser`) raises a `ParseError` containing "Maximum number of AST nodes" once more than N nodes have been built. The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I haven't committed.

**Changes**
- `sqlglot/parser.py`: new `max_nodes: int | None = None` argument on `Parser`, stored in `__slots__`. The count is kept in `_node_count` and reset per parse. The check sits in `Parser.expression()`, the main node builder, so the parser stops as soon as the limit is cro
…[543 chars elided]…
rather than through `self.expression()`, are not counted. On the 500-column query, the smallest accepted limit was 2513 while the built tree has 3016 nodes (about 17% low). On the 5000-term expression, the count matched the tree exactly.
- Nodes built during backtracking attempts that get discarded still count. This can only make the limit stricter, never looser.

**Choices I made**
- The default is `None`, so existing behaviour is unchanged unless the option is passed.
- I did not pick a recommended production value. Callers should choose one based on the largest legitimate query they expect.
