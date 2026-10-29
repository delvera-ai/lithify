# trajectory base-1

final message:
`parse_one` (and `parse`, `Parser`) now accept `max_nodes`. When a parse builds more nodes than that, it raises a `ParseError` whose message contains "Maximum number of AST nodes". The full test suite passes (1083 tests), and ruff and mypy are clean. I haven't committed anything.

**What changed**
- `sqlglot/parser.py`: `Parser.__init__` takes `max_nodes: int | None = None`. The count is incremented in `Parser.expression()`, the parser's node builder, and checked against the limit there.
- The check also runs at the end of `_parse`, because `_try_parse` swallows `ParseError` during speculative parses. Without that, a limit hit inside a speculative branch could be silently discarded.
- `parse_into` re-raises the limit error instead of trying the next expression type.
- `sqlglot/_typing.py`: added `max_nodes` to `ParserNoDialectArgs`, so `parse_one(..., max_nodes=...)` type-checks.
- `tests/test_parser.py`: new `test_max_nodes`. It covers the 500-column query parsing with no limit or a limit of 10,000, failure at a limit of 100, the error still raising with `error_level=IGNORE`, the `into=` path, and a small non-wide query.

**Choices I made**
- The limit is opt-in (default `None`), so existing behaviour is unchanged unless callers pass it.
- The limit ignores `error_level` on purpose: it is a hard resource cap, not a validation warning.
- The budget is per parse call. Multi-statement input shares one budget, and each `parse_into` attempt gets a fresh one.

**Limitation:** only nodes built through `Parser.expression()` are counted. Nodes the parser constructs directly with `exp.*(...)` bypass the count, so the limit is an approximation of total AST size, not an exact one. A 500-column `SELECT` builds roughly 1,000 nodes.

## events
[tool_use Bash] {"command": "git status --short | head && git log --oneline -1 && grep -n \"max_errors\\|def __init__\\|def parse_one\\|def parse(\\|def _parse(\\|self.error_level\\|_add_node\\|class Parser\\|def reset\\|self._index = \\|def raise_error\\|def expression(\" sqlglot/parser.py sqlglot/__init__.py | head -80", "description": "Inspect parser state and entry points"}
[tool_result] 0cf180fee lithify: probe base
sqlglot/__init__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/parser.py:281:class Parser:
sqlglot/parser.py:291:        max_errors: Maximum number of error messages to include in a raised ParseError.
sqlglot/parser.py:299:        "max_errors",
sqlglot/parser.py:1823:    def __init__(
sqlglot/parser.py:1827:        max_errors: int = 3,
sqlglot/parser.py:1830:        self
…[708 chars elided]…
E
sqlglot/parser.py:1992:            self.error_level = error_level
sqlglot/parser.py:1996:    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
sqlglot/parser.py:2050:        if self.error_level == ErrorLevel.WARN:
sqlglot/parser.py:2053:        elif self.error_level == ErrorLevel.RAISE and self.errors:
sqlglot/parser.py:2055:                concat_messages(self.errors, self.max_errors),
sqlglot/parser.py:2059:    def expression(
sqlglot/parser.py:2104:    def _parse(
[tool_use Bash] {"command": "sed -n 281,310p sqlglot/parser.py && echo ---- && sed -n 1820,1880p sqlglot/parser.py && echo ---- && sed -n 1996,2060p sqlglot/parser.py && echo ---- && sed -n 2059,2140p sqlglot/parser.py", "description": "Read parser init, parse, and expression code"}
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
           
…[7187 chars elided]…
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
[tool_use Bash] {"command": "sed -n 100,200p sqlglot/__init__.py && echo ---- && grep -n \"max_errors\\|error_level\" sqlglot/*.py | grep -v \"^sqlglot/parser.py\" | head -30", "description": "Read parse_one and max_errors usages"}
[tool_result]         dialect: the SQL dialect (alias for read).

    Returns:
        The resulting list of tokens.
    """
    return Dialect.get_or_raise(read or dialect).tokenize(sql)


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
        read
…[2710 chars elided]…
lglot.ErrorLevel[args.error_level.upper()]
sqlglot/__main__.py:81:            error_level=error_level,
sqlglot/__main__.py:93:        error_level=error_level,
sqlglot/_typing.py:29:    error_level: ErrorLevel | None
sqlglot/_typing.py:31:    max_errors: int
sqlglot/__init__.py:189:    error_level: ErrorLevel | None = None,
sqlglot/__init__.py:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
[tool_use Bash] {"command": "grep -n \"def validate_expression\" -A12 sqlglot/parser.py | head -30; echo ----; grep -c \"self.expression(\" sqlglot/parser.py; grep -c \"self.expression(\" sqlglot/dialects/*.py | awk -F: '{s+=$2} END {print \"dialect uses\", s}'; echo ----; sed -n 20,40p sqlglot/_typing.py; echo ----; grep -n \"def parse\\b\\|def parse(\" -A8 sqlglot/dialects/dialect.py | head -30; echo ----; grep -n \"class ParseError\" -A40 sqlglot/errors.py | head -70; echo ----; grep -n \"ErrorLevel\\|max_errors\" tests/test_parser.py | head; ls tests | head -50", "description": "Inspect validation, typing, dialect parse, errors"}
[tool_result] 1973:    def validate_expression(self, expression: E, args: list | None = None) -> E:
1974-        if self.error_level != ErrorLevel.IGNORE:
1975-            for error_message in expression.error_messages(args):
1976-                self.raise_error(error_message)
1977-        return expression
1978-
1979-    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
1980-        index = self._index
1981-        error_level = self.error_level
1982-        this: T |
…[2711 chars elided]…
_level=ErrorLevel.WARN,
834:            error_level=ErrorLevel.IGNORE,
__init__.py
dialects
fixtures
gen_fixtures.py
helpers.py
sqlglot
test_build.py
test_dialect_entry_points.py
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
[tool_use Bash] {"command": "sed -n 1949,1972p sqlglot/parser.py; sed -n 1979,1995p sqlglot/parser.py; grep -n \"except ParseError\\|except (ParseError\\|except Exception\\|except.*Error\" sqlglot/parser.py | head -30; grep -n \"except ParseError\\|except (ParseError\" sqlglot/*.py sqlglot/dialects/*.py | grep -v \"^sqlglot/parser.py\" | head", "description": "Read raise_error and speculative parse handling"}
[tool_result]     def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
        token = token or self._curr or self._prev or Token.string("")
        formatted_sql, start_context, highlight, end_context = highlight_sql(
            sql=self.sql,
            positions=[(token.start, token.end)],
            context_length=self.error_message_context,
        )
        formatted_message = f"{message}. Line {token.line}, Col: {token.col}.\n  {formatted_sql}"

        error = ParseError.new(
 
…[634 chars elided]…
thod()
        except ParseError:
            this = None
        finally:
            if not this or retreat:
                self._retreat(index)
            self.error_level = error_level

        return this

1987:        except ParseError:
2039:            except ParseError as e:
2702:            except TypeError:
4110:        except ParseError:
6077:                except TokenError:
6840:                except TypeError:
sqlglot/dialects/dialect.py:1107:            except ParseError as e:
[assistant] The parser is recursive descent with `_try_parse` swallowing `ParseError` during speculative parses, so the limit has to be sticky, not just a one-time raise. Making the edits now.
[tool_use Bash] {"command": "grep -n \"^from\\|^import\\|i64\" sqlglot/parser.py | head -30; grep -n \"_parse_batch_statements(\" sqlglot/parser.py sqlglot/dialects/*.py | head; sed -n 2029,2033p sqlglot/parser.py", "description": "Check imports and batch parse call sites"}
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
24:fr
…[314 chars elided]…
at(self, index: i64) -> None:
sqlglot/parser.py:2072:    def _parse_batch_statements(
sqlglot/parser.py:2128:        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)
sqlglot/parser.py:2230:                expressions=self._parse_batch_statements(
            The target Expr.
        """
        errors = []
        for expression_type in ensure_list(expression_types):
            parser = self.EXPRESSION_PARSERS.get(t.cast(type[exp.Expr], expression_type))
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np = \"sqlglot/parser.py\"\ns = open(p).read()\n\ndef rep(old, new, count=1):\n    global s\n    assert s.count(old) == count, (s.count(old), old[:80])\n    s = s.replace(old, new)\n\nrep('''        max_errors: Maximum number of error messages to include in a raised ParseError.\n            This is only relevant if error_level is ErrorLevel.RAISE.\n       
…[2913 chars elided]…
  e.errors[0][\"into_expression\"] = expression_type\n''')\nopen(p, \"w\").write(s)\n\np = \"sqlglot/_typing.py\"\ns = open(p).read()\nrep('''    error_message_context: int\n    max_errors: int\n''', '''    error_message_context: int\n    max_errors: int\n    max_nodes: int | None\n''')\nopen(p, \"w\").write(s)\nEOF\ngit diff --stat", "description": "Apply max_nodes changes to parser and typings"}
[tool_result]  sqlglot/_typing.py |  1 +
 sqlglot/parser.py  | 21 ++++++++++++++++++++-
 2 files changed, 21 insertions(+), 1 deletion(-)
[assistant] Edits applied. Now I'll check that `ParseError` is imported in parser.py and look at the existing test style before adding tests.
[tool_use Bash] {"command": "sed -n 10,17p sqlglot/parser.py; sed -n 250,305p tests/test_parser.py; grep -n \"^class \\|    def test_\" tests/test_parser.py | head -20", "description": "Check imports and existing parser test style"}
[tool_result] from sqlglot.errors import (
    ErrorLevel,
    ParseError,
    TokenError,
    concat_messages,
    highlight_sql,
    merge_errors,
)

        expressions = parse("SELECT 1; ; SELECT 2")

        assert len(expressions) == 3
        assert expressions[1] is None

    def test_expression(self):
        ignore = Parser(error_level=ErrorLevel.IGNORE)
        self.assertIsInstance(ignore.expression(exp.Hint(expressions=[])), exp.Hint)
        self.assertIsInstance(ignore.expression(exp.Hint(y="")
…[1874 chars elided]…
rs(self):
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
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nfrom sqlglot import parse_one, exp\nfrom sqlglot.parser import Parser\nq = 'SELECT ' + ', '.join(f'c{i}' for i in range(500)) + ' FROM t'\nprint(len(list(parse_one(q).walk())))\nprint(parse_one(q, max_nodes=100000).sql()[:30])\nfor n in (1000, 2000, 3000): \n    try: parse_one(q, max_nodes=n); print(n, 'ok')\n    except Exception as e: print(n, type(e).__name__, e)\n\" 2>&1 | tail -8", "description": "Measure node counts for 500-column query"}
[tool_result] 1004
SELECT c0, c1, c2, c3, c4, c5,
1000 ok
2000 ok
3000 ok
[assistant] The 500-column query builds about 1,000 nodes, so the test will use a limit of 100 for the failure case and 10,000 for the success case. Adding tests next.
[tool_use Bash] {"command": "python3 - <<'EOF'\np = \"tests/test_parser.py\"\ns = open(p).read()\nold = '''    def test_space(self):\n'''\nnew = '''    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i}\" for i in range(500)) + \" FROM t\"\n\n        self.assertEqual(len(parse_one(wide).expressions), 500)\n        self.assertEqual(len(parse_one(wide, max_nodes=10000).expressions), 500)\n\
…[432 chars elided]…
\n\n        with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            Parser(max_nodes=10).parse(Tokenizer().tokenize(\"SELECT a + b + c + d + e + f + g\"), \"\")\n\n    def test_space(self):\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\nopen(p, \"w\").write(s)\nEOF\nsed -n 1,10p tests/test_parser.py", "description": "Add max_nodes test to parser test file"}
[tool_result] import time
import unittest
from unittest.mock import patch

from sqlglot import Parser, exp, parse, parse_one
from sqlglot.errors import ErrorLevel, ParseError
from sqlglot.parser import logger as parser_logger
from tests.helpers import assert_logger_contains
[assistant] I referenced `Tokenizer` without importing it, and the last assertion is awkward. Replacing it with a simpler `parse_one` call.
[tool_use Bash] {"command": "python3 - <<'EOF'\np = \"tests/test_parser.py\"\ns = open(p).read()\nold = '''            Parser(max_nodes=10).parse(Tokenizer().tokenize(\"SELECT a + b + c + d + e + f + g\"), \"\")\n'''\nnew = '''            parse_one(\"SELECT a + b + c + d + e + f + g\", max_nodes=3)\n'''\nassert s.count(old) == 1\nopen(p, \"w\").write(s.replace(old, new))\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -15", "description": "Run parser tests"}
[tool_result]         dialect: DialectType = None,
        max_nodes: int | None = None,
    ):
        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
        self.error_message_context: int = error_message_context
        self.max_errors: int = max_errors
        self.max_nodes: int | None = max_nodes
>       self._node_count: i64 = 0
        ^^^^^^^^^^^^^^^^
E       AttributeError: 'Parser' object has no attribute '_node_count'

sqlglot/parser.py:1838: AttributeError
=========================== short test summary info ============================
FAILED tests/test_parser.py::TestParser::test_expression - AttributeError: 'P...
1 failed, 63 passed, 71 subtests passed in 0.29s
[assistant] I forgot to add `_node_count` to `__slots__`. Fixing that.
[tool_use Bash] {"command": "python3 - <<'EOF'\np = \"sqlglot/parser.py\"\ns = open(p).read()\nold = '''        \"max_nodes\",\n        \"dialect\",\n'''\nnew = '''        \"max_nodes\",\n        \"_node_count\",\n        \"dialect\",\n'''\nassert s.count(old) == 1\nopen(p, \"w\").write(s.replace(old, new))\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py 2>&1 | tail -3 && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run parser tests then full test suite"}
[tool_result] ................................. [ 51%]
...............................          [100%]
64 passed, 71 subtests passed in 0.20s
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 46.66s
[assistant] The full suite passes (1083 tests). Next I'll run the linters on the changed files, since the project's pre-commit uses ruff and mypy.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ($PY/ruff check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py && $PY/ruff format --check sqlglot/parser.py sqlglot/_typing.py tests/test_parser.py) 2>&1 | tail -5; ls $PY | grep -i \"mypy\\|ruff\"; $PY/mypy sqlglot/parser.py 2>&1 | tail -3; git diff", "description": "Run ruff and mypy on changed files"}
[tool_result] All checks passed!
3 files already formatted
dmypy
mypy
mypyc
ruff
Success: no issues found in 1 source file
diff --git a/sqlglot/_typing.py b/sqlglot/_typing.py
index fe7e80ee3..578d6c262 100644
--- a/sqlglot/_typing.py
+++ b/sqlglot/_typing.py
@@ -29,6 +29,7 @@ class ParserNoDialectArgs(t.TypedDict, total=False):
     error_level: ErrorLevel | None
     error_message_context: int
     max_errors: int
+    max_nodes: int | None
 
 
 class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False
…[3999 chars elided]…
se_one(wide, max_nodes=100, error_level=ErrorLevel.IGNORE)
+
+        with self.assertRaisesRegex(ParseError, "Maximum number of AST nodes"):
+            parse_one(wide, max_nodes=100, into=exp.Select)
+
+        with self.assertRaisesRegex(ParseError, "Maximum number of AST nodes"):
+            parse_one("SELECT a + b + c + d + e + f + g", max_nodes=3)
+
     def test_space(self):
         self.assertEqual(
             parse_one("SELECT ROW() OVER(PARTITION  BY x) FROM x GROUP  BY y").sql(),
[assistant] `parse_one` (and `parse`, `Parser`) now accept `max_nodes`. When a parse builds more nodes than that, it raises a `ParseError` whose message contains "Maximum number of AST nodes". The full test suite passes (1083 tests), and ruff and mypy are clean. I haven't committed anything.

**What changed**
- `sqlglot/parser.py`: `Parser.__init__` takes `max_nodes: int | None = None`. The count is incremented in `Parser.expression()`, the parser's node builder, and checked against the limit there.
- The check also runs at the end of `_parse`, because `_try_parse` swallows `ParseError` during speculative
…[548 chars elided]…
es I made**
- The limit is opt-in (default `None`), so existing behaviour is unchanged unless callers pass it.
- The limit ignores `error_level` on purpose: it is a hard resource cap, not a validation warning.
- The budget is per parse call. Multi-statement input shares one budget, and each `parse_into` attempt gets a fresh one.

**Limitation:** only nodes built through `Parser.expression()` are counted. Nodes the parser constructs directly with `exp.*(...)` bypass the count, so the limit is an approximation of total AST size, not an exact one. A 500-column `SELECT` builds roughly 1,000 nodes.
