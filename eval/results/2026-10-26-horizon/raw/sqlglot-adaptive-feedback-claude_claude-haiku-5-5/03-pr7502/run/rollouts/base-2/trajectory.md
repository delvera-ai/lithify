# trajectory base-2

final message:
`parse_one`, `parse`, and `Parser` now accept `max_nodes`. Exceeding it raises a `ParseError` containing "Maximum number of AST nodes exceeded (max_nodes=N)". The default is `None`, so existing behaviour is unchanged. The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I did not commit.

**What changed**
- `sqlglot/parser.py`: `Parser.__init__` takes `max_nodes`. `expression()` counts every node it builds and raises once the count passes the limit. The count is checked again at the end of `_parse`, and in `parse_into`'s error handler, so a limit error swallowed by backtracking still surfaces with the right message.
- `sqlglot/_typing.py`: adds `max_nodes` to the typed parser options so `parse_one` accepts it.
- `tests/test_parser.py`: adds `test_max_nodes`. It covers a 500-column select (parses by default and under a large limit, fails under 100), a deep `+` chain, `parse_one(into=exp.Select)`, and `parse`.

**Things to know**
- **Counting is partial.** Nodes built through `self.expression()` are counted. Some function builders construct nodes directly, and those are not counted. The limit bounds the main node path, not an exact total of AST nodes.
- **500 columns is about 1000 nodes.** Walking the AST of a 500-column select gives 1004 nodes, so a limit under ~1000 rejects that query. Pick the limit with that in mind.
- **Nodes built during backtracking count too.** The parser tries alternatives and discards some, and those count toward the limit. This is conservative and only matters when a limit is set.

If you want, I can commit this with the Co-Authored-By line from the project instructions.

## events
[assistant] I'll start by reading how the parser is configured and how `parse_one` passes options through.
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"error_level\\|def __init__\\|self.error_level\\|_parse(\\|def parse\\b\\|def _parse\\b\" sqlglot/parser.py | head -60 && grep -n \"def parse_one\\|def parse(\\|error_level\\|max_errors\" sqlglot/__init__.py sqlglot/dialects/dialect.py | head -30", "description": "Check repo state and locate parser options"}
[tool_result] 17eb4a163 lithify: probe base
286:        error_level: The desired error level.
292:            This is only relevant if error_level is ErrorLevel.RAISE.
297:        "error_level",
1823:    def __init__(
1825:        error_level: ErrorLevel | None = None,
1830:        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE
1968:        if self.error_level == ErrorLevel.IMMEDIATE:
1974:        if self.error_level != ErrorLevel.IGNORE:
1979:    def _try_parse(self, parse_method: t.Calla
…[1328 chars elided]…
nit__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/__init__.py:189:    error_level: ErrorLevel | None = None,
sqlglot/__init__.py:202:        error_level: the desired error level of the parser.
sqlglot/__init__.py:212:        for expression in parse(sql, read, error_level=error_level)
sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
[tool_use Bash] {"command": "sed -n 270,320p sqlglot/parser.py && sed -n 1815,1870p sqlglot/parser.py && sed -n 1990,2140p sqlglot/parser.py && sed -n 100,220p sqlglot/__init__.py && grep -n \"ParserArgs\\|class ParserArgs\" -A12 sqlglot/dialects/dialect.py | head -40", "description": "Read parser init, parse loop, and entry points"}
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
…[13049 chars elided]…
0-            self.generate(expression, copy=False, **opts) if expression else ""
1131-            for expression in self.parse(sql)
--
1143:    def parser(self, **opts: Unpack[ParserArgs]) -> Parser:
1144:        args: ParserArgs = {"dialect": self, **opts}
1145-        return self.parser_class(**args)
1146-
1147-    def generator(self, **opts: Unpack[GeneratorArgs]) -> Generator:
1148-        args: GeneratorArgs = {"dialect": self, **opts}
1149-        return self.generator_class(**args)
1150-
[assistant] The entry points all forward `**opts` into `Parser.__init__`, so a new constructor argument flows through `parse`, `parse_one`, and `parse_into` without extra plumbing. Next I need a central place to count nodes, so I'll look at `validate_expression` and the typed arg definitions.
[tool_use Bash] {"command": "grep -n \"def validate_expression\" -A30 sqlglot/parser.py | head -50; grep -n \"ParserArgs\\|ParserNoDialectArgs\" -A10 sqlglot/_typing.py | head -40; grep -n \"def raise_error\" -A25 sqlglot/parser.py | head -40; grep -n \"class ParseError\" -A30 sqlglot/errors.py | head -50; grep -c \"self.expression(\" sqlglot/parser.py sqlglot/parsers/*.py | awk -F: '{s+=$2} END {print \"self.expression calls:\", s}'", "description": "Inspect validate_expression, ParseError, and typed args"}
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
…[2833 chars elided]…
5-        end_context: str | None = None,
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
self.expression calls: 662
[assistant] Before choosing where to count, I need to know whether `self.expression()` is the single path nodes take. The `_try_parse` helper also swallows `ParseError`, which affects how a limit error would propagate.
[tool_use Bash] {"command": "grep -n \"def expression\\|self.expression(\" sqlglot/parser.py | head -5; echo ---; grep -rnE \"exp\\.[A-Z][A-Za-z]+\\(\" sqlglot/parser.py sqlglot/parsers/*.py | wc -l; grep -rnE \"exp\\.[A-Z][A-Za-z]+\\(\" sqlglot/parser.py sqlglot/parsers/*.py | head -5; echo ---; grep -n \"__slots__\\|class Parser\" sqlglot/parser.py | head; ls tests | grep -i pars; grep -rn \"max_errors\\|error_message_context\" tests/*.py | head -5", "description": "Check node construction paths and existing parser tests"}
[tool_result] 70:        return self._parse_escape(self.expression(expr_type(this=this, expression=expression)))
970:        TokenType.ARROW: lambda self, expressions: self.expression(
979:        TokenType.FARROW: lambda self, expressions: self.expression(
991:        TokenType.DOTCOLON: lambda self, this, to: self.expression(exp.JSONCast(this=this, to=to)),
995:        TokenType.ARROW: lambda self, this, path: self.expression(
---
    1064
sqlglot/parsers/databricks.py:25:        "UNIFORM": lambda args: exp
…[69 chars elided]…
sion(exp.CurrentDate())
sqlglot/parsers/doris.py:23:    return exp.TimestampTrunc(this=this, unit=unit)
sqlglot/parsers/doris.py:76:            exp.PartitionByRangeProperty(
sqlglot/parsers/doris.py:89:        every = self.expression(exp.Interval(this=number, unit=unit))
---
281:class Parser:
296:    __slots__ = (
test_parser.py
tests/test_transpile.py:1050:        more_than_max_errors = "(((("
tests/test_transpile.py:1081:            transpile(more_than_max_errors, error_level=ErrorLevel.RAISE)
[assistant] Most nodes are built through `self.expression()`, so that is the natural counting point. Two `except ParseError` sites (`_try_parse` and `parse_into`) could swallow a limit error, so I'll check for any others before deciding how to re-raise.
[tool_use Bash] {"command": "grep -rn \"except ParseError\\|except (ParseError\" sqlglot | head -20; sed -n 1,40p tests/test_parser.py | head -40; grep -n \"def test_\" tests/test_parser.py | tail -5", "description": "Find all ParseError catch sites and test file layout"}
[tool_result] sqlglot/parser.py:1987:        except ParseError:
sqlglot/parser.py:2039:            except ParseError as e:
sqlglot/parser.py:4110:        except ParseError:
sqlglot/dialects/dialect.py:1107:            except ParseError as e:
sqlglot/expressions/builders.py:324:    except (ParseError, TokenError):
sqlglot/expressions/builders.py:372:    except ParseError:
sqlglot/expressions/builders.py:409:    except ParseError:
sqlglot/expressions/datatypes.py:358:            except ParseError:
sqlglot/expre
…[1474 chars elided]…
 self.assertRaises(ParseError) as ctx:
            parse_one("SELECT * FROM tbl", into=exp.Table)

        self.assertEqual(
            str(ctx.exception),
            "Failed to parse 'SELECT * FROM tbl' into <class 'sqlglot.expressions.query.Table'>",
1042:    def test_qualified_function(self):
1048:    def test_pivot_missing_agg_func(self):
1054:    def test_multiple_query_modifiers(self):
1067:    def test_parse_into_grant_principal(self):
1082:    def test_parse_into_grant_privilege(self):
[assistant] There are several other `except ParseError` sites in builders and datatypes that silently fall back, so a limit error raised in one of them would be lost. My plan is a sticky counter: `expression()` raises as soon as the limit is passed, and `_parse` re-checks the total at the end so a swallowed error still surfaces. `parse_into` also re-checks in its `except` so the message survives. Now I'll make the edits.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py", "old_string": "        max_errors: Maximum number of error messages to include in a raised ParseError.\n            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n\n    __slots__ = (\n  
…[260 chars elided]…
 is ErrorLevel.RAISE.\n            Default: 3\n        max_nodes: Maximum number of AST nodes that parsing may build. A ParseError is raised once\n            the limit is exceeded. Default: None (no limit)\n    \"\"\"\n\n    __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n        \"max_nodes\",\n        \"_node_count\",\n        \"dialect\","}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py", "old_string": "        max_errors: int = 3,\n        dialect: DialectType = None,\n    ):\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n  
…[1941 chars elided]…
        self.sql = \"\"\n        self.errors = []\n        self._tokens = []\n        self._tokens_size = 0\n        self._index = 0\n        self._curr = SENTINEL_NONE\n        self._next = SENTINEL_NONE\n        self._prev = SENTINEL_NONE\n        self._prev_comments = []\n        self._pipe_cte_counter = 0\n        self._chunks = []\n        self._chunk_index = 0\n        self._node_count = 0"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py", "old_string": "        comments: list[str] | None = None,\n    ) -> E:\n        if token:\n            instance.update_positions(token)\n        instance.add_comments(comments) if comments else self._add_comments(instance)\n        if
…[348 chars elided]…
ments) if comments else self._add_comments(instance)\n        if not instance.is_primitive:\n            instance = self.validate_expression(instance)\n        return instance\n\n    def _check_max_nodes(self) -> None:\n        if self.max_nodes is not None and self._node_count > self.max_nodes:\n            raise ParseError(f\"Maximum number of AST nodes exceeded (max_nodes={self.max_nodes})\")"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py", "old_string": "        self._chunks = chunks\n\n        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)", "new_string": "        self._chunks = chunks\n\n        expressions = self._parse_batch_statements(\n            parse_method=parse_method, sep_first_statement=False\n        )\n        # A limit error may have been swallowed by a backtracking attempt, so re-check the total\n        self._check_max_nodes()\n        return expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py", "old_string": "            except ParseError as e:\n                e.errors[0][\"into_expression\"] = expression_type\n                errors.append(e)", "new_string": "            except ParseError as e:\n                self._check_max_nodes()\n                e.errors[0][\"into_expression\"] = expression_type\n                errors.append(e)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/_typing.py", "old_string": "    max_errors: int\n\n\nclass ParserArgs", "new_string": "    max_errors: int\n    max_nodes: int | None\n\n\nclass ParserArgs"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/sqlglot/_typing.py has been updated successfully.
[assistant] The edits are in. Next I'll check behavior directly: the limit should trigger, normal queries and 500-column selects should parse under a generous limit, and `parse_one(into=...)` should keep the message.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY >/dev/null 2>&1 && echo venv-ok || echo venv-missing; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import parse_one, exp\nfrom sqlglot.errors import ParseError\nwide = 'SELECT ' + ', '.join(f'c{i}' for i in range(500
…[468 chars elided]…
r as e:\n        print('raised:', str(e).splitlines()[0])\nprint('into:', end=' ')\ntry: parse_one('SELECT ' + ','.join(['a']*200) + ' FROM t', into=exp.Select, max_nodes=50)\nexcept ParseError as e: print(str(e).splitlines()[0])\nprint('transpile default:', sqlglot.transpile('SELECT 1 AS x', read='duckdb', write='spark'))\n\" 2>&1 | tail -20", "description": "Smoke-test the new max_nodes option"}
[tool_result] venv-ok
wide nodes walked: 1004
wide default ok: 500
wide with limit 10000 ok: 500
raised: Maximum number of AST nodes exceeded (max_nodes=100)
raised: Maximum number of AST nodes exceeded (max_nodes=50)
raised: Maximum number of AST nodes exceeded (max_nodes=1)
into: Maximum number of AST nodes exceeded (max_nodes=50)
transpile default: ['SELECT 1 AS x']
[assistant] The counter behaves as intended: wide queries parse unchanged, the limit raises with the required message, and the `into=` path keeps it. Next I'll add regression tests to `tests/test_parser.py` and run the project checks.
[tool_use Bash] {"command": "tail -15 tests/test_parser.py", "description": "View end of parser test file"}
[tool_result]             parse_one("ROLE `blah`", into=exp.GrantPrincipal, dialect="databricks"),
            exp.GrantPrincipal,
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/tests/test_parser.py", "old_string": "    def test_parse_into_grant_privilege(self):\n        self.assertIsInstance(parse_one(\"SELECT\", into=exp.GrantPrivilege), exp.GrantPrivilege)\n        self.assertIsInstance(\n            parse_one(\"ALL PRIVILEGE
…[797 chars elided]…
aximum number of AST nodes\"):\n            parse_one(\"SELECT \" + \" + \".join([\"a\"] * 300), read=\"duckdb\", max_nodes=50)\n\n        with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            parse_one(wide, into=exp.Select, max_nodes=100)\n\n        with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            parse(wide, max_nodes=100)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-155133-parser-add-a-safeguard-against-p/base-2/tests/test_parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; ($PY -m ruff check sqlglot tests/test_parser.py && $PY -m ruff format --check sqlglot tests/test_parser.py) 2>&1 | tail -5", "description": "Run new test, full suite, and linter"}
[tool_result] .                                                                        [100%]
1 passed, 63 deselected in 0.07s
.............................................. [ 51%]
...................................................................................................................................... [ 63%]
......................................................... [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 95%]
.......................... [ 98%]
..................              [100%]
1083 passed, 17840 subtests passed in 47.16s
All checks passed!
174 files already formatted
[assistant] The full suite passes (1083 tests) and ruff is clean. I'll run mypy on the changed modules as well, since the project's pre-commit hooks include it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; timeout 500 $PY -m mypy sqlglot/parser.py sqlglot/_typing.py 2>&1 | tail -5; git diff --stat", "description": "Run mypy on parser and show diff stats"}
[tool_result] (eval):1: command not found: timeout
 sqlglot/_typing.py   |  1 +
 sqlglot/parser.py    | 22 +++++++++++++++++++++-
 tests/test_parser.py | 18 ++++++++++++++++++
 3 files changed, 40 insertions(+), 1 deletion(-)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/parser.py sqlglot/_typing.py 2>&1 | tail -5", "description": "Run mypy on parser and typing modules"}
[tool_result] Success: no issues found in 2 source files
[assistant] `parse_one`, `parse`, and `Parser` now accept `max_nodes`. Exceeding it raises a `ParseError` containing "Maximum number of AST nodes exceeded (max_nodes=N)". The default is `None`, so existing behaviour is unchanged. The full suite passes (1083 tests), and ruff and mypy are clean on the changed files. I did not commit.

**What changed**
- `sqlglot/parser.py`: `Parser.__init__` takes `max_nodes`. `expression()` counts every node it builds and raises once the count passes the limit. The count is checked again at the end of `_parse`, and in `parse_into`'s error handler, so a limit error swallowe
…[456 chars elided]…
ome function builders construct nodes directly, and those are not counted. The limit bounds the main node path, not an exact total of AST nodes.
- **500 columns is about 1000 nodes.** Walking the AST of a 500-column select gives 1004 nodes, so a limit under ~1000 rejects that query. Pick the limit with that in mind.
- **Nodes built during backtracking count too.** The parser tries alternatives and discards some, and those count toward the limit. This is conservative and only matters when a limit is set.

If you want, I can commit this with the Co-Authored-By line from the project instructions.
