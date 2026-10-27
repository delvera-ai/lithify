# trajectory base-1

final message:
I added the `max_nodes` option to the parser. `parse_one(sql, max_nodes=N)` raises a `ParseError` containing "Maximum number of AST nodes exceeded" when a statement needs more than N nodes. The default is `None`, so existing behaviour is unchanged. The full suite passes (1083 tests), and ruff and mypy are clean.

**What changed**
- `sqlglot/parser.py`: `Parser` takes `max_nodes`, which flows through `parse_one`, `parse` and dialect parsing. Nodes are counted in `Parser.expression()` so runaway parses abort early. Each statement is then walked and checked against the limit, so the final tree is counted exactly.
- `sqlglot/_typing.py`: `max_nodes` added to the parser option types.
- `tests/test_parser.py`: `test_max_nodes` covers a 500-column query under the default and at the exact limit, a limit one below that raising, an arithmetic chain raising, the error still raising under `ErrorLevel.IGNORE`, and multi-statement input.

**Checks I ran**
- A 500-column `SELECT` parses as before with no limit and with a generous limit.
- The smallest accepted `max_nodes` equals the walked tree size for four sample queries (for example, the 500-column query needs exactly 1004).
- The limit trips at every error level.

**Decisions to confirm**
- **Per statement, not per call.** For a multi-statement string, the limit applies to each statement separately. For a single statement, the two readings are identical. Tell me if you want a whole-call total instead.
- **Counts include backtracked nodes.** The early-abort counter also counts nodes the parser builds and then discards while backtracking. A query can therefore hit the limit mid-parse even if its final tree is smaller. The final per-statement check uses only the returned tree.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && ls sqlglot/ && grep -n \"error_level\\|def parse\\b\\|def __init__\\|max_errors\\|def _parse\\b\\|def parse(\" sqlglot/parser.py | head -60", "description": "Inspect repo state and parser entry points"}
[tool_result] 7ed65162e lithify: probe base
__init__.py
__main__.py
_typing.py
_version.py
dialects
diff.py
errors.py
executor
expressions
generator.py
generators
helper.py
jsonpath.py
lineage.py
optimizer
parser.py
parsers
planner.py
py.typed
schema.py
serde.py
time.py
tokenizer_core.py
tokens.py
transforms.py
trie.py
typing
286:        error_level: The desired error level.
291:        max_errors: Maximum number of error messages to include in a raised ParseError.
292:            This is only relevant if err
…[376 chars elided]…

1974:        if self.error_level != ErrorLevel.IGNORE:
1981:        error_level = self.error_level
1984:        self.error_level = ErrorLevel.IMMEDIATE
1992:            self.error_level = error_level
1996:    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
2050:        if self.error_level == ErrorLevel.WARN:
2053:        elif self.error_level == ErrorLevel.RAISE and self.errors:
2055:                concat_messages(self.errors, self.max_errors),
2104:    def _parse(
[tool_use Bash] {"command": "sed -n 1815,1860p sqlglot/parser.py && echo ---- && sed -n 1960,2130p sqlglot/parser.py && echo ---- && grep -n \"def parse_one\\|def parse(\\|def parse_into\\|def _parse_statement\\|def _parse(\" -A3 sqlglot/__init__.py sqlglot/dialects/dialect.py sqlglot/parser.py | head -60", "description": "Read parser init and parse internals"}
[tool_result]     # Whether INTERVAL spans with literal format '\d+ hh:[mm:[ss[.ff]]]'
    # can omit the span unit `DAY TO MINUTE` or `DAY TO SECOND`
    SUPPORTS_OMITTED_INTERVAL_SPAN_UNIT: t.ClassVar = False

    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
    SET_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SET_PARSERS)

    def __init__(
        self,
        error_level: ErrorLevel | None = None,
        error_message_context: int = 100,
        max_erro
…[8613 chars elided]…
ession_types: exp.IntoType,
sqlglot/parser.py-2015-        raw_tokens: list[Token],
--
sqlglot/parser.py:2104:    def _parse(
sqlglot/parser.py-2105-        self,
sqlglot/parser.py-2106-        parse_method: t.Callable[[Parser], exp.Expr | None],
sqlglot/parser.py-2107-        raw_tokens: list[Token],
--
sqlglot/parser.py:2241:    def _parse_statement(self) -> exp.Expr | None:
sqlglot/parser.py-2242-        if not self._curr:
sqlglot/parser.py-2243-            return None
sqlglot/parser.py-2244-
[tool_use Bash] {"command": "grep -n \"def parse_one\\|def parse(\\|def parse_into\" -A40 sqlglot/__init__.py | head -120; grep -n \"def parse\\b\\|def parse(\" -A12 sqlglot/dialects/dialect.py | head -40", "description": "Read top-level parse_one and dialect parse"}
[tool_result] 108:def parse(
109-    sql: str,
110-    read: DialectType = None,
111-    dialect: DialectType = None,
112-    **opts: Unpack[ParserNoDialectArgs],
113-) -> list[Expr | None]:
114-    """
115-    Parses the given SQL string into a collection of syntax trees, one per parsed SQL statement.
116-
117-    Args:
118-        sql: the SQL code string to parse.
119-        read: the SQL dialect to apply during parsing (eg. "spark", "hive", "presto", "mysql").
120-        dialect: the SQL dialect (alias 
…[2241 chars elided]…
s).parse(self.tokenize(sql), sql)
1117-
1118-    def parse_into(
1119-        self, expression_type: exp.IntoType, sql: str, **opts: Unpack[ParserArgs]
1120-    ) -> list[exp.Expr | None]:
1121-        return self.parser(**opts).parse_into(expression_type, self.tokenize(sql), sql)
1122-
1123-    def generate(
1124-        self, expression: exp.Expr, copy: bool = True, **opts: Unpack[GeneratorArgs]
1125-    ) -> str:
1126-        return self.generator(**opts).generate(expression, copy=copy)
1127-
[tool_use Bash] {"command": "sed -n 270,310p sqlglot/parser.py; grep -c \"self.expression(\" sqlglot/parser.py; grep -c \"exp\\.[A-Z][A-Za-z]*(\" sqlglot/parser.py; grep -rn \"max_errors\\|error_message_context\" sqlglot/ --include=*.py | grep -v \"^sqlglot/parser.py\" | head; grep -n \"class ParseError\" -A30 sqlglot/errors.py | head -50", "description": "Inspect parser args, direct node construction, ParseError"}
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
…[1158 chars elided]…
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
[tool_use Bash] {"command": "grep -rn \"class ParserArgs\\|class ParserNoDialectArgs\" -A12 sqlglot/ ; grep -n \"def parser(\" -A12 sqlglot/dialects/dialect.py; sed -n 1940,1960p sqlglot/parser.py; grep -n \"def expression\" -B2 sqlglot/parser.py; grep -n \"^from\\|^import\" sqlglot/parser.py | head -30", "description": "Find parser option typing and expression builder"}
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
…[1968 chars elided]…
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
[tool_use Bash] {"command": "sed -n 2059,2075p sqlglot/parser.py && sed -n 10,17p sqlglot/parser.py && grep -n \"max_errors\" sqlglot/parser.py && ls tests | head -50 && grep -n \"max_errors\\|error_message_context\" tests/*.py | head", "description": "Read expression() body and existing option tests"}
[tool_result]     def expression(
        self,
        instance: E,
        token: Token | None = None,
        comments: list[str] | None = None,
    ) -> E:
        if token:
            instance.update_positions(token)
        instance.add_comments(comments) if comments else self._add_comments(instance)
        if not instance.is_primitive:
            instance = self.validate_expression(instance)
        return instance

    def _parse_batch_statements(
        self,
        parse_method: t.Callable[[Par
…[569 chars elided]…
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
[assistant] Now I'll implement the option: a counter in the parser's central `expression()` builder, reset per parse, with the limit exposed through `Parser` args so `parse_one(..., max_nodes=...)` picks it up.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new,count=1):\n    global s\n    assert s.count(old)==count,(s.count(old),old)\n    s=s.replace(old,new)\nrep('''            Default: 3\n    \"\"\"\n''','''            Default: 3\n        max_nodes: Maximum number of AST nodes that parsing may build. A ParseError is raised\n            once the limit is
…[1460 chars elided]…
\n            instance.update_positions(token)\n        instance.add_comments(comments) if comments else self._add_comments(instance)\n''')\nopen(p,'w').write(s)\np='sqlglot/_typing.py'\ns=open(p).read()\nrep('''    max_errors: int\n''','''    max_errors: int\n    max_nodes: int | None\n''')\nopen(p,'w').write(s)\nEOF\ngit diff --stat", "description": "Apply max_nodes option to parser and typing"}
[tool_result]  sqlglot/_typing.py |  1 +
 sqlglot/parser.py  | 11 +++++++++++
 2 files changed, 12 insertions(+)
[assistant] Now let me verify behaviour: wide queries under the default, the limit tripping, and whether the error can be swallowed by backtracking.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY && cat > /tmp/mn_check.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.errors import ParseError\nwide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\nt = sqlglot.parse_one(wide)\np
…[610 chars elided]…
: NO ERROR\")\n    except ParseError as e:\n        print(\"transpile ParseError:\", str(e).splitlines()[0])\n    try:\n        sqlglot.parse_one(q, max_nodes=lim, error_level=sqlglot.ErrorLevel.IGNORE)\n        print(\"IGNORE: NO ERROR\")\n    except ParseError as e:\n        print(\"IGNORE ParseError ok\")\nEOF\n$PY -I /tmp/mn_check.py", "description": "Run ad-hoc checks of max_nodes behaviour"}
[tool_result ERROR] Exit code 1
<work>/env-sqlglot/bin/python
Traceback (most recent call last):
  File "/tmp/mn_check.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY /tmp/mn_check.py", "description": "Run ad-hoc max_nodes checks with repo on path"}
[tool_result ERROR] Exit code 1
wide ok, columns: 500 walk nodes: 1004
wide with max_nodes=10000: 500
ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
Traceback (most recent call last):
  File "/tmp/mn_check.py", line 15, in <module>
    sqlglot.transpile(q, max_nodes=lim)
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-1/sqlglot/__init__.py", line 211, in transpile
    write.generate(expression, copy=False, **opts) if expression els
…[155 chars elided]…
-against-p/base-1/sqlglot/dialects/dialect.py", line 1126, in generate
    return self.generator(**opts).generate(expression, copy=copy)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-1/sqlglot/dialects/dialect.py", line 1149, in generator
    return self.generator_class(**args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Generator.__init__() got an unexpected keyword argument 'max_nodes'
[assistant] The `transpile` failure is my test script's mistake: `transpile` forwards kwargs to the generator too, so parser-only options don't belong there. I'll drop that case and check the remaining ones.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; sed -i '/transpile/,+2d' /tmp/mn_check.py && PYTHONPATH=$PWD $PY /tmp/mn_check.py", "description": "Re-run max_nodes checks without transpile case"}
[tool_result ERROR] Exit code 1
sed: 1: "/tmp/mn_check.py
": invalid command code m
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/mn_check.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.errors import ParseError, ErrorLevel\nwide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\nt = sqlglot.parse_one(wide)\
…[410 chars elided]…
vl in [None, ErrorLevel.RAISE, ErrorLevel.IGNORE, ErrorLevel.WARN]:\n        try:\n            sqlglot.parse_one(q, max_nodes=lim, error_level=lvl)\n            print(lvl, lim, \"NO ERROR\")\n        except ParseError as e:\n            print(lvl, lim, \"ParseError:\", str(e).splitlines()[0])\nEOF\nPYTHONPATH=$PWD $PY /tmp/mn_check.py", "description": "Re-run max_nodes checks across error levels"}
[tool_result] wide default columns: 500 walk nodes: 1004
wide max_nodes=10000 columns: 500
None 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.RAISE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.IGNORE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.WARN 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
None 50 ParseError: Maximum number of AST nodes exceeded (max_nodes=50)
ErrorLevel.RAISE 50
…[64 chars elided]…

ErrorLevel.IGNORE 50 ParseError: Maximum number of AST nodes exceeded (max_nodes=50)
ErrorLevel.WARN 50 ParseError: Maximum number of AST nodes exceeded (max_nodes=50)
None 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.RAISE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.IGNORE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.WARN 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
[assistant] The limit trips at every error level. Next I'll check how completely the counter covers real nodes, since some nodes are built by direct `exp.X(...)` calls rather than `self.expression()`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/mn_count.py <<'EOF'\nimport sqlglot\nfrom sqlglot.errors import ParseError\nqs = {\n \"wide\": \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\",\n \"join_where\": \"SELECT a.x, b.y FROM a JOIN b ON 
…[392 chars elided]…
mit that still parses\n    hi = n * 2\n    while lo < hi:\n        mid = (lo + hi) // 2\n        try:\n            sqlglot.parse_one(q, max_nodes=mid); hi = mid\n        except ParseError:\n            lo = mid + 1\n    print(f\"{name}: walk nodes={n}, smallest max_nodes that parses={lo}\")\nEOF\nPYTHONPATH=$PWD $PY /tmp/mn_count.py", "description": "Compare counted nodes against walked AST size"}
[tool_result] wide: walk nodes=1004, smallest max_nodes that parses=503
join_where: walk nodes=43, smallest max_nodes that parses=33
cte: walk nodes=30, smallest max_nodes that parses=23
case: walk nodes=16, smallest max_nodes that parses=14
[assistant] The counter only sees nodes created through `self.expression()`, so it undercounts the final tree by roughly half (the 500-column query builds 1004 nodes but trips at 503). I'll make the limit exact: count in-flight nodes for early abort, then verify each statement's tree against the limit, with the count scoped per statement.
[tool_use Bash] {"command": "grep -n \"_parse_batch_statements(\" sqlglot/ -r && python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\ndef rep(old,new,count=1):\n    global s\n    assert s.count(old)==count,(s.count(old),old)\n    s=s.replace(old,new)\nrep('''        self.max_nodes: int | None = max_nodes\n        self._node_count: int = 0\n''','''        self.max_nodes: int | None = max_nodes\n        self
…[1268 chars elided]…
ement_limited(parse_method))\n\n            if self._index''')\nrep('''            expressions.append(parse_method(self))\n''','''            expressions.append(self._parse_statement_limited(parse_method))\n''')\nopen(p,'w').write(s)\nEOF\ngrep -n \"_parse_statement_limited\\|_node_count\\|_check_node_limit\" sqlglot/parser.py", "description": "Scope node count per statement and verify tree size"}
[tool_result] sqlglot/parser.py:2083:    def _parse_batch_statements(
sqlglot/parser.py:2139:        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
sqlglot/parser.py:2241:                expressions=self._parse_batch_statements(
1838:        self._node_count: int = 0
2065:    def _check_node_limit(self, node_count: int) -> None:
2069:    def _parse_statement_limited(self, parse_method: t.Callable[[Parser], E]) -> E:
2070:        self._node_count = 0
2073:            self._check_node_limit(sum(1 for _ in expression.walk()))
2082:        self._node_count += 1
2083:        self._check_node_limit(self._node_count)
2102:            expressions.append(self._parse_statement_limited(parse_method))
2115:            expressions.append(self._parse_statement_limited(parse_method))
[assistant] I'll match the signature style of `_parse_batch_statements` instead of the `E` TypeVar, then rerun the checks and the test suite.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''    def _parse_statement_limited(self, parse_method: t.Callable[[Parser], E]) -> E:'''\nnew='''    def _parse_statement_limited(\n        self, parse_method: t.Callable[[Parser], exp.Expr | None]\n    ) -> exp.Expr | None:'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\nPY=/private/tmp/claude-50
…[355 chars elided]…
M t'\nprint(len(sqlglot.parse_one(w, max_nodes=1004).expressions))\ntry: sqlglot.parse_one(w, max_nodes=1003); print('no err')\nexcept ParseError as e: print('1003 ->', str(e))\nprint(sqlglot.parse_one('SELECT 1; SELECT 2', max_nodes=5).sql() if False else [x.sql() for x in sqlglot.parse('SELECT 1; SELECT 2', max_nodes=5)])\n\"", "description": "Recheck exact limits and multi-statement behaviour"}
[tool_result] wide: walk nodes=1004, smallest max_nodes that parses=1004
join_where: walk nodes=43, smallest max_nodes that parses=43
cte: walk nodes=30, smallest max_nodes that parses=30
case: walk nodes=16, smallest max_nodes that parses=16
wide default columns: 500 walk nodes: 1004
wide max_nodes=10000 columns: 500
None 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.RAISE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
ErrorLevel.IGNORE 100 ParseError: Maximum number of AST nodes exceeded (max_nodes=100)
500
1003 -> Maximum number of AST nodes exceeded (max_nodes=1003)
['SELECT 1', 'SELECT 2']
[assistant] The limit is now exact: the smallest accepted `max_nodes` equals the walked tree size for each query. Next I'll add regression tests to `tests/test_parser.py`.
[tool_use Bash] {"command": "sed -n 1,20p tests/test_parser.py && grep -n \"^class \\|    def test_\" tests/test_parser.py | tail -8 && tail -5 tests/test_parser.py", "description": "Look at test_parser.py structure"}
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
…[302 chars elided]…
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
[tool_use Bash] {"command": "cat >> tests/test_parser.py <<'EOF'\n\n    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\n        self.assertEqual(len(parse_one(wide).expressions), 500)\n        self.assertEqual(len(parse_one(wide, max_nodes=10000).expressions), 500)\n\n        node_count = sum(1 for _ in parse_one(wide).walk())\n        self.assertE
…[527 chars elided]…
IGNORE)\n\n        self.assertEqual(len(parse(\"SELECT 1; SELECT 2\", max_nodes=5)), 2)\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -15", "description": "Add max_nodes tests and run them"}
[tool_result] .                                                                        [100%]
1 passed, 63 deselected in 0.07s
[assistant] The new test passes. Now the full suite with the project's command, plus lint and type checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff --version && ruff check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py) 2>&1 | tail -5; (mypy --version && mypy sqlglot/parser.py sqlglot/_typing.py) 2>&1 | tail -3", "description": "Run full test suite, ruff, and mypy"}
[tool_result]         dialect: DialectType = None,
        max_nodes: int | None = None,
    ):
        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
        self.error_message_context: int = error_message_context
        self.max_errors: int = max_errors
        self.max_nodes: int | None = max_nodes
>       self._node_count: int = 0
        ^^^^^^^^^^^^^^^^
E       AttributeError: 'Parser' object has no attribute '_node_count'

sqlglot/parser.py:1838: AttributeError
====================
…[71 chars elided]…
ts/test_parser.py::TestParser::test_expression - AttributeError: 'P...
1 failed, 1082 passed, 17840 subtests passed in 46.38s
ruff 0.15.6
All checks passed!
3 files already formatted
sqlglot/parser.py:2072: error: Trying to assign name "_node_count" that is not in "__slots__" of type "sqlglot.parser.Parser"  [misc]
sqlglot/parser.py:2084: error: Trying to assign name "_node_count" that is not in "__slots__" of type "sqlglot.parser.Parser"  [misc]
Found 3 errors in 1 file (checked 2 source files)
[assistant] Two real issues: `_node_count` is missing from `__slots__`, which breaks `Parser` and mypy. Fixing that and rerunning.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''        \"max_errors\",\n        \"max_nodes\",\n        \"dialect\",'''\nnew='''        \"max_errors\",\n        \"max_nodes\",\n        \"_node_count\",\n        \"dialect\",'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\nPY=/private/tmp/claude-501/-Users-user-Coding-delvera-foundational-l
…[33 chars elided]…
bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; ruff check sqlglot tests/test_parser.py | tail -1; ruff format --check sqlglot/parser.py tests/test_parser.py | tail -1; mypy sqlglot/parser.py sqlglot/_typing.py 2>&1 | tail -4; git stash list | head -0; git diff HEAD --stat", "description": "Fix slots, rerun suite, ruff, and mypy"}
[tool_result] .......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 50.59s
All checks passed!
2 files already formatted
Success: no issues found in 2 source files
head: illegal line count -- 0
 sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 27 +++++++++++++++++++++++++--
 tests/test_parser.py | 19 +++++++++++++++++++
 3 files changed, 45 insertions(+), 2 deletions(-)
[assistant] All 1083 tests pass, and ruff and mypy are clean. Let me review the final diff.
[tool_use Bash] {"command": "git diff HEAD -- sqlglot/ && rm -f /tmp/mn_check.py /tmp/mn_count.py", "description": "Review the final source diff"}
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
index 107ad1ec0..0aa922a3c 100644
--- a/sqlglot/parser.
…[2604 chars elided]…
atement_limited(parse_method))
 
         chunks_length = len(self._chunks)
         while self._chunk_index < chunks_length:
@@ -2092,7 +2115,7 @@ class Parser:
                 expressions.append(exp.EndStatement())
                 continue
 
-            expressions.append(parse_method(self))
+            expressions.append(self._parse_statement_limited(parse_method))
 
             if self._index < self._tokens_size:
                 self.raise_error("Invalid expression / Unexpected token")
[assistant] The diff is as intended, but the docstring says "parsing" when the limit is actually applied per statement. I'll make that explicit.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''        max_nodes: Maximum number of AST nodes that parsing may build. A ParseError is raised\n            once the limit is exceeded. Default: None (no limit).'''\nnew='''        max_nodes: Maximum number of AST nodes that may be built for a single statement. A\n            ParseError is raised once the limit is excee
…[62 chars elided]…
n(p,'w').write(s.replace(old,new))\nEOF\nPY=<work>/env-sqlglot/bin/python; ruff format --check sqlglot/parser.py | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -1", "description": "Clarify max_nodes docstring and rerun parser tests"}
[tool_result] 1 file already formatted
64 passed, 71 subtests passed in 0.14s
[assistant] I added the `max_nodes` option to the parser. `parse_one(sql, max_nodes=N)` raises a `ParseError` containing "Maximum number of AST nodes exceeded" when a statement needs more than N nodes. The default is `None`, so existing behaviour is unchanged. The full suite passes (1083 tests), and ruff and mypy are clean.

**What changed**
- `sqlglot/parser.py`: `Parser` takes `max_nodes`, which flows through `parse_one`, `parse` and dialect parsing. Nodes are counted in `Parser.expression()` so runaway parses abort early. Each statement is then walked and checked against the limit, so the final tree is
…[542 chars elided]…
e 500-column query needs exactly 1004).
- The limit trips at every error level.

**Decisions to confirm**
- **Per statement, not per call.** For a multi-statement string, the limit applies to each statement separately. For a single statement, the two readings are identical. Tell me if you want a whole-call total instead.
- **Counts include backtracked nodes.** The early-abort counter also counts nodes the parser builds and then discards while backtracking. A query can therefore hit the limit mid-parse even if its final tree is smaller. The final per-statement check uses only the returned tree.
