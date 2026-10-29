# trajectory base-1

final message:
`parse_one(..., max_nodes=N)` and `Parser(max_nodes=N)` now raise `ParseError` ("Maximum number of AST nodes (N) exceeded") when the parsed trees have more than N nodes. The full suite passes (1083 passed), and ruff check and format pass on the changed files. I haven't committed anything.

**The limit is checked after parsing, not during it.** The parser builds the whole tree before the count runs, so a pathological input still costs its full parse time and memory. A true early abort would need a counter in the `Expression` constructor, which is on the hot path. Counting only in `Parser.expression()` was tried first. It overcounted nodes that get backtracked away, so it rejected queries at exactly their own size, and it missed leaf nodes like literals. I dropped it. If you want early abort, that constructor hook is the next step.

**Changes:**
- `sqlglot/parser.py`: new `max_nodes: int | None = None` on `Parser.__init__`, documented in the class docstring. `_parse` counts nodes with `walk()` when the limit is set. The default is no limit, so normal parsing is unchanged. The option is appended last, so positional callers are unaffected.
- `sqlglot/_typing.py`: `max_nodes` added to `ParserNoDialectArgs`, so `parse_one` and `parse` accept it.
- `sqlglot/parsers/athena.py`: `AthenaParser` has an explicit constructor, so it now takes and forwards `max_nodes` to its Hive and Trino sub-parsers. Without this, `read="athena"` would reject the keyword.
- `tests/test_parser.py`: `test_max_nodes` covers a 500-column query at a generous limit and with no limit, the exact boundary, all three error levels, and Athena.

I checked the boundary against the repo's `tests/fixtures/identity.sql`: at the exact node count every query parses, and one below it every query raises.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"max_errors\\|def __init__\\|def parse_one\\|def parse(\\|def _parse(\" sqlglot/parser.py sqlglot/__init__.py sqlglot/dialects/dialect.py | head -40 && grep -n \"ParseError\" sqlglot/errors.py | head", "description": "Inspect parser init and parse entry points"}
[tool_result] sqlglot/__init__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/dialects/dialect.py:974:    def __init__(self, **kwargs) -> None:
sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
sqlglot/parser.py:291:        max_errors: Maximum number of error messages to include in a raised ParseError.
sqlglot/parser.py:299:        "max_errors",
sql
…[20 chars elided]…
    def __init__(
sqlglot/parser.py:1827:        max_errors: int = 3,
sqlglot/parser.py:1832:        self.max_errors: int = max_errors
sqlglot/parser.py:1996:    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
sqlglot/parser.py:2055:                concat_messages(self.errors, self.max_errors),
sqlglot/parser.py:2104:    def _parse(
37:class ParseError(SqlglotError):
57:    ) -> ParseError:
161:def merge_errors(errors: Sequence[ParseError]) -> list[dict[str, t.Any]]:
[tool_use Bash] {"command": "sed -n 280,320p sqlglot/parser.py && sed -n 1815,1850p sqlglot/parser.py && sed -n 1990,2070p sqlglot/parser.py && sed -n 100,200p sqlglot/__init__.py && grep -n \"ParserArgs\\|class ParserArgs\" -A3 sqlglot/dialects/dialect.py | head -30", "description": "Read parser options, parse loop, and parse_one"}
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
           
…[8635 chars elided]…

1118-    def parse_into(
1119:        self, expression_type: exp.IntoType, sql: str, **opts: Unpack[ParserArgs]
1120-    ) -> list[exp.Expr | None]:
1121-        return self.parser(**opts).parse_into(expression_type, self.tokenize(sql), sql)
1122-
--
1143:    def parser(self, **opts: Unpack[ParserArgs]) -> Parser:
1144:        args: ParserArgs = {"dialect": self, **opts}
1145-        return self.parser_class(**args)
1146-
1147-    def generator(self, **opts: Unpack[GeneratorArgs]) -> Generator:
[tool_use Bash] {"command": "sed -n 1850,1870p sqlglot/parser.py && sed -n 2104,2180p sqlglot/parser.py && grep -n \"def validate_expression\" -A25 sqlglot/parser.py && grep -n \"ParserArgs\\|ParserNoDialectArgs\" -A12 sqlglot/_typing.py | head -40 && grep -c \"self.expression(\" sqlglot/parser.py && grep -c \"exp\\.[A-Z][A-Za-z]*(\" sqlglot/parser.py && grep -n \"max_errors\\|max_nodes\" -r sqlglot tests docs 2>/dev/null | grep -v \"^sqlglot/parser.py\" | head", "description": "Read _parse loop, validate_expression, typing args"}
[tool_result]         self._tokens = []
        self._tokens_size = 0
        self._index = 0
        self._curr = SENTINEL_NONE
        self._next = SENTINEL_NONE
        self._prev = SENTINEL_NONE
        self._prev_comments = []
        self._pipe_cte_counter = 0
        self._chunks = []
        self._chunk_index = 0

    def _advance(self, times: i64 = 1) -> None:
        index = self._index + times
        self._index = index
        tokens = self._tokens
        size = self._tokens_size
        self._c
…[4461 chars elided]…
:    max_errors: int
sqlglot/parsers/athena.py:29:        max_errors: int = 3,
sqlglot/parsers/athena.py:43:            max_errors=max_errors,
sqlglot/parsers/athena.py:50:            max_errors=max_errors,
sqlglot/parsers/athena.py:55:            max_errors=max_errors,
sqlglot/generators/singlestore.py:922:        "max_errors",
tests/test_transpile.py:1050:        more_than_max_errors = "(((("
tests/test_transpile.py:1081:            transpile(more_than_max_errors, error_level=ErrorLevel.RAISE)
[tool_use Bash] {"command": "sed -n 20,60p sqlglot/parsers/athena.py && grep -rn \"def __init__\" sqlglot/parsers/ sqlglot/dialects/ | head -20; sed -n 915,930p sqlglot/generators/singlestore.py; grep -rn \"error_message_context\" sqlglot --include=*.py | grep -v \"parser.py\" | head", "description": "Check dialect parser constructors forwarding options"}
[tool_result]         TokenType.USING: lambda self: self._parse_as_command(self._prev),
    }


class AthenaParser(Parser):
    def __init__(
        self,
        error_level: ErrorLevel | None = None,
        error_message_context: int = 100,
        max_errors: int = 3,
        dialect: DialectType = None,
        hive: Hive | None = None,
        trino: Trino | None = None,
    ) -> None:
        from sqlglot.dialects.hive import Hive
        from sqlglot.dialects.trino import Trino

        hive = hive o
…[906 chars elided]…
ct: DialectType = None) -> None:
sqlglot/dialects/dialect.py:974:    def __init__(self, **kwargs) -> None:
        "mapping",
        "master",
        "match",
        "materialized",
        "max",
        "maxvalue",
        "max_concurrency",
        "max_errors",
        "max_partitions_per_batch",
        "max_queue_depth",
        "max_retries_per_batch_partition",
        "max_rows",
        "mbc",
        "md5",
        "mpl",
        "median",
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -n \"def raise_error\" -A22 sqlglot/parser.py && grep -n \"def _parse_batch_statements\" -A40 sqlglot/parser.py | head -60 && grep -n \"except ParseError\" sqlglot/parser.py | head -30 && grep -n \"def reset\" -B2 sqlglot/parser.py && grep -n \"^from\\|^import\" sqlglot/parser.py | head -30", "description": "Inspect error handling paths in parser"}
[tool_result] 1949:    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
1950-        token = token or self._curr or self._prev or Token.string("")
1951-        formatted_sql, start_context, highlight, end_context = highlight_sql(
1952-            sql=self.sql,
1953-            positions=[(token.start, token.end)],
1954-            context_length=self.error_message_context,
1955-        )
1956-        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_
…[2205 chars elided]…
g
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
[assistant] The parser builds nodes mainly through `Parser.expression()`, and `AthenaParser` has its own explicit constructor that must forward any new option. I'll add the option to `Parser`, count in `expression()`, forward it in Athena, and extend the typed args.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new,count=1):\n    global s\n    assert s.count(old)==count,(s.count(old),old[:60])\n    s=s.replace(old,new)\nrep('''            Default: 3\n    \"\"\"\n\n    __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n''','''            Default: 3\n        max
…[3151 chars elided]…
es=max_nodes,\n        )\n        self._trino_parser = AthenaTrinoParser(\n            error_level=error_level,\n            error_message_context=error_message_context,\n            max_errors=max_errors,\n            dialect=trino,\n            max_nodes=max_nodes,\n        )''')\nopen(p,'w').write(s)\nEOF\ngit diff --stat", "description": "Apply max_nodes changes to parser, typing, and Athena"}
[tool_result]  sqlglot/_typing.py        |  1 +
 sqlglot/parser.py         | 12 ++++++++++++
 sqlglot/parsers/athena.py |  4 ++++
 3 files changed, 17 insertions(+)
[assistant] Now a quick behavioral check, including the wide-query case and the backtracking path (`_try_parse` swallows `ParseError`).
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY - <<'EOF'\nimport sqlglot\nfrom sqlglot import parse_one, ErrorLevel\nfrom sqlglot.errors import ParseError\nwide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\nprint(\"wide default ok:\", len(parse_one(wide).expressions))\nprint(\"wide max_nodes=None ok:\", len(parse_one(wid
…[518 chars elided]…
except ParseError as e: print(\"raised at\", el, str(e).splitlines()[0])\nfor d in [\"athena\", \"hive\", \"duckdb\", \"spark\"]:\n    try: parse_one(wide, read=d, max_nodes=50); print(\"no error\", d)\n    except ParseError: print(\"raised\", d)\nprint(parse_one(\"SELECT a FROM b WHERE c = 1\", read=\"athena\", max_nodes=100).sql())\nEOF", "description": "Run manual checks of max_nodes behavior"}
[tool_result] wide default ok: 500
wide max_nodes=None ok: 500
wide max_nodes=100000 ok: 500
raised: Maximum number of AST nodes (100) exceeded
raised: Maximum number of AST nodes (3) exceeded
raised at ErrorLevel.IGNORE Maximum number of AST nodes (50) exceeded
raised at ErrorLevel.WARN Maximum number of AST nodes (50) exceeded
raised at ErrorLevel.RAISE Maximum number of AST nodes (50) exceeded
raised athena
raised hive
raised duckdb
raised spark
SELECT a FROM b WHERE c = 1
[assistant] Basic behavior works across dialects and error levels. Next, I'll check the backtracking concern: whether a `ParseError` swallowed by `_try_parse` can let a parse succeed while over the limit. I'll test against the repo's identity fixtures.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY - <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.errors import ParseError\nsqls=[l.strip() for l in open(\"tests/fixtures/identity.sql\") if l.strip()]\nbad=0; ok=0; fail=0\ndef count(e): return sum(1 for _ in e.walk())\nfor sql in sqls:\n    try: full=sqlglot.parse_one(sql)\n    except
…[138 chars elided]…
lim)\n            bad+=1; print(\"SUCCESS over limit\", lim, n, sql[:80])\n        except ParseError as e:\n            ok+=1\n            if \"Maximum number\" not in str(e): fail+=1; print(\"other err\", sql[:60], str(e)[:80])\n        except Exception as e:\n            fail+=1\nprint(\"ok\",ok,\"bad\",bad,\"other\",fail)\nEOF", "description": "Fuzz identity fixtures against tight node limits"}
[tool_result] <persisted-output>
Output too large (46KB). Full output saved to: ~/.claude/projects/-Users-user--cache-lithify-work-repo-90e86f132b84-20261028-110816-parser-add-a-safeguard-against-p-base-1/7691a5df-1d9a-4e89-80a8-dde7691a4c29/tool-results/bl6t5jr81.txt

Preview (first 2KB):
SUCCESS over limit 1 2 SUM(1)
SUCCESS over limit 1 2 SUM(1)
SUCCESS over limit 11 12 SUM(CASE WHEN x > 1 THEN 1 ELSE 0 END) / y
SUCCESS over limit 1 1 1
SUCCESS over limit 1 1 1.
SUCCESS over limit 1 1 1.0
S
…[1290 chars elided]…
 over limit 9 10 x >> 1 | 1 & 1 ^ 1
SUCCESS over limit 4 5 x || y
SUCCESS over limit 3 4 a.b.c
SUCCESS over limit 4 5 a.b.c.d
SUCCESS over limit 6 7 a.b.c.d.e
SUCCESS over limit 5 6 x IN (-1, 1)
SUCCESS over limit 4 5 x IN ('a', 'a''a')
SUCCESS over limit 4 5 x IN ((1))
SUCCESS over limit 5 6 x BETWEEN -1 AND 1
SUCCESS over limit 10 11 x BETWEEN 'a' || b AND 'c' || d
SUCCESS over limit 7 8 ((a, b) AS c)
SUCCESS over limit 4 5 NOT x IS NULL
SUCCESS over limit 3 4 x IS TRUE
...
</persisted-output>
[assistant] The fuzz exposed a real gap: counting only in `Parser.expression()` misses leaf nodes such as `Literal`, `Identifier`, and `DataType`, which are built directly. So a limit of 1 lets `SELECT 1` through. I'll keep the early-abort check in `expression()` and add an exact post-parse count over the produced trees, so the limit actually bounds the AST.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new):\n    global s\n    assert s.count(old)==1,old[:60]\n    s=s.replace(old,new)\nrep('''        max_nodes: Maximum number of AST nodes that parsing may build. Exceeding it raises a ParseError,\n            regardless of error_level. Nodes are counted as they are created through `Parser.expression`.\n           
…[1997 chars elided]…
batch_statements(\n            parse_method=parse_method, sep_first_statement=False\n        )\n\n        if self.max_nodes is not None:\n            self._check_nodes(sum(sum(1 for _ in e.walk()) for e in expressions if e))\n\n        return expressions\n''')\nopen(p,'w').write(s)\nEOF\ngrep -n \"_nodes\" sqlglot/parser.py", "description": "Add exact post-parse node count and early-abort helper"}
[tool_result] 294:        max_nodes: Maximum number of AST nodes that parsing may build. Exceeding it raises a ParseError,
304:        "max_nodes",
305:        "_nodes",
1835:        max_nodes: int | None = None,
1840:        self.max_nodes: int | None = max_nodes
1841:        self._nodes: int = 0
1857:        self._nodes = 0
2058:    def _check_nodes(self, count: int) -> None:
2059:        if self.max_nodes is not None and count > self.max_nodes:
2060:            raise ParseError(f"Maximum number of AST nodes ({self.max_nodes}) exceeded")
2079:        if self.max_nodes is not None:
2080:            self._nodes += 1
2081:            self._check_nodes(self._nodes)
2149:        if self.max_nodes is not None:
2150:            self._check_nodes(sum(sum(1 for _ in e.walk()) for e in expressions if e))
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -I - <<'EOF' 2>&1 | tail -15\nimport sys; sys.path.insert(0,\".\")\nimport sqlglot\nfrom sqlglot.errors import ParseError\nsqls=[l.strip() for l in open(\"tests/fixtures/identity.sql\") if l.strip()]\nbad=0; ok=0; other=0; fine=0\nfor sql in sqls:\n    try: full=sqlglot.parse_one(sql)\n    except Excep
…[558 chars elided]…
$PY -I -c \"\nimport sys; sys.path.insert(0,'.')\nfrom sqlglot import parse_one\nwide='SELECT '+', '.join(f'c{i}' for i in range(500))+' FROM t'\nprint(len(parse_one(wide, max_nodes=10**6).expressions))\nparse_one('SELECT 1', max_nodes=3)\ntry: parse_one('SELECT 1', max_nodes=2)\nexcept Exception as e: print(type(e).__name__, e)\n\"", "description": "Re-run fixture fuzz against exact node counts"}
[tool_result] FALSE RAISE 7 7 PRAGMA schema.synchronous = FULL
FALSE RAISE 6 6 PRAGMA schema.memory_limit = '1GB'
FALSE RAISE 6 6 JSON_OBJECT('x': 1 RETURNING VARCHAR(100))
FALSE RAISE 4 4 SELECT if.x
FALSE RAISE 9 9 SELECT cube, cube.x FROM cube
FALSE RAISE 15 15 WITH all AS (SELECT 1 AS count) SELECT all.count FROM all
FALSE RAISE 4 4 SELECT 1 OFFSET 1
FALSE RAISE 4 4 SELECT 1 LIMIT 1
FALSE RAISE 7 7 a.b.c.D()
FALSE RAISE 13 13 a.b.c.d.e.f.G()
FALSE RAISE 4 4 FOO(values.c)
FALSE RAISE 3 3 case.*
FALSE RAISE 14 14 SELECT LAST_VALUE(CASE WHEN interval <> 'foo' THEN interval END) IGNOR
FALSE RAISE 8 8 SELECT NUMRANGE(1.1, 2.2) -|- NUMRANGE(2.2, 3.3)
ok 1845 bad 63 other 7 fine 891
500
[assistant] Two problems. The fixture fuzz finds false raises at `lim == n`, because `expression()` also counts nodes that the parser builds and then backtracks away, so the early counter overcounts and can't be made exact. A post-parse walk is exact, so I'll drop the incremental counter and keep only the exact check. The trade-off is that this bounds the size of the result, not the work done during parsing. I'll say so in the summary.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new):\n    global s\n    assert s.count(old)==1,old[:60]\n    s=s.replace(old,new)\nrep('''        max_nodes: Maximum number of AST nodes that parsing may build. Exceeding it raises a ParseError,\n            regardless of error_level. Nodes built through `Parser.expression` are counted during parsing\n           
…[1023 chars elided]…
ns if e))\n''','''        if self.max_nodes is not None:\n            node_count = sum(sum(1 for _ in e.walk()) for e in expressions if e)\n            if node_count > self.max_nodes:\n                raise ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n''')\nopen(p,'w').write(s)\nEOF\ngit diff sqlglot/parser.py", "description": "Simplify to exact post-parse node count"}
[tool_result] diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 107ad1ec0..3c34bd553 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -291,12 +291,16 @@ class Parser:
         max_errors: Maximum number of error messages to include in a raised ParseError.
             This is only relevant if error_level is ErrorLevel.RAISE.
             Default: 3
+        max_nodes: Maximum number of AST nodes in the parsed trees. Exceeding it raises a ParseError,
+            regardless of error_level.
+   
…[952 chars elided]…
       expressions = self._parse_batch_statements(
+            parse_method=parse_method, sep_first_statement=False
+        )
+
+        if self.max_nodes is not None:
+            node_count = sum(sum(1 for _ in e.walk()) for e in expressions if e)
+            if node_count > self.max_nodes:
+                raise ParseError(f"Maximum number of AST nodes ({self.max_nodes}) exceeded")
+
+        return expressions
 
     def _warn_unsupported(self) -> None:
         if self._tokens_size <= 1:
[assistant] Now I'll re-run the fixture fuzz against the exact count, then add tests and run the suite with the project's interpreter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python && $PY -I - <<'EOF' 2>&1 | tail -5\nimport sys; sys.path.insert(0,\".\")\nimport sqlglot\nfrom sqlglot.errors import ParseError\nsqls=[l.strip() for l in open(\"tests/fixtures/identity.sql\") if l.strip()]\nbad=0; ok=0; fine=0\nfor sql in sqls:\n    try: full=sqlglot.parse_one(sql)\n    except Exception: cont
…[173 chars elided]…
 n: bad+=1; print(\"SUCCESS over limit\", lim, n, sql[:70])\n            else: fine+=1\n        except ParseError as e:\n            if lim >= n: bad+=1; print(\"FALSE RAISE\", lim, n, sql[:70])\n            else: ok+=1\nprint(\"ok\",ok,\"bad\",bad,\"fine\",fine)\nEOF\ngrep -n \"^class\\|def test_\" tests/test_parser.py | head -20", "description": "Verify exact-count fuzz and locate parser tests"}
[tool_result] ok 1852 bad 0 fine 954
11:class TestParser(unittest.TestCase):
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
160:    def test_select(self):
175:    def test_command(self):
185:    def test_lambda_struct(self):
194:    def test_transactions(self):
223:    def test_identify(self):
240:    def test_multi(self):
[assistant] Exact count now agrees with the fixtures: no false raises and no over-limit successes. Adding tests to `tests/test_parser.py`:
[tool_use Bash] {"command": "sed -n 1,12p tests/test_parser.py && sed -n 88,100p tests/test_parser.py", "description": "View test file header and a test example"}
[tool_result] import time
import unittest
from unittest.mock import patch

from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains


class TestParser(unittest.TestCase):
    def test_parse_empty(self):
        with self.assertRaises(ParseError) as ctx:
            parse_one("SELECT 1;", "sqlite", into=[exp.From, exp.Join])

        self.assertEqual(str(ctx.exception), expected_message)
        self.assertEqual(ctx.exception.errors, expected_errors)

    def test_column(self):
        columns = parse_one("select a, ARRAY[1] b, case when 1 then 1 end").find_all(exp.Column)
        assert len(list(columns)) == 1

        self.assertIsNotNone(parse_one("date").find(exp.Column))

    def test_tuple(self):
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/test_parser.py'\ns=open(p).read()\nold='''    def test_column(self):\n        columns = parse_one(\"select a, ARRAY[1] b, case when 1 then 1 end\").find_all(exp.Column)\n'''\nnew='''    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\n        self.assertEqual(len(parse_one(wide, max_nodes=10_0
…[946 chars elided]…
        columns = parse_one(\"select a, ARRAY[1] b, case when 1 then 1 end\").find_all(exp.Column)\n'''\nassert s.count(old)==1\ns=s.replace(old,new)\nopen(p,'w').write(s)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -5", "description": "Add max_nodes tests and run parser tests"}
[tool_result] .............................. [ 46%]
..................................       [100%]
64 passed, 74 subtests passed in 0.19s
[assistant] Parser tests pass. Now the full suite with the project's check command, plus lint/format on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; ($PY -m ruff --version >/dev/null 2>&1 && $PY -m ruff check sqlglot/parser.py sqlglot/_typing.py sqlglot/parsers/athena.py tests/test_parser.py && $PY -m ruff format --check sqlglot/parser.py sqlglot/_typing.py sqlglot/parsers/athena.py tests/test_parser.py) || echo \"ruff unavailable\"", "description": "Run full test suite and lint changed files"}
[tool_result] ...................................................................................................................................... [ 63%]
......................................................... [ 69%]
............................................... [ 73%]
............................................................................................................................................................................................ [ 90%]
.................................. [ 94%]
................. [ 95%]
...............................................           [100%]
1083 passed, 17843 subtests passed in 38.08s
All checks passed!
4 files already formatted
[assistant] `parse_one(..., max_nodes=N)` and `Parser(max_nodes=N)` now raise `ParseError` ("Maximum number of AST nodes (N) exceeded") when the parsed trees have more than N nodes. The full suite passes (1083 passed), and ruff check and format pass on the changed files. I haven't committed anything.

**The limit is checked after parsing, not during it.** The parser builds the whole tree before the count runs, so a pathological input still costs its full parse time and memory. A true early abort would need a counter in the `Expression` constructor, which is on the hot path. Counting only in `Parser.expres
…[585 chars elided]…
des` added to `ParserNoDialectArgs`, so `parse_one` and `parse` accept it.
- `sqlglot/parsers/athena.py`: `AthenaParser` has an explicit constructor, so it now takes and forwards `max_nodes` to its Hive and Trino sub-parsers. Without this, `read="athena"` would reject the keyword.
- `tests/test_parser.py`: `test_max_nodes` covers a 500-column query at a generous limit and with no limit, the exact boundary, all three error levels, and Athena.

I checked the boundary against the repo's `tests/fixtures/identity.sql`: at the exact node count every query parses, and one below it every query raises.
