# trajectory base-1

final message:
`parse_one` and `parse` now accept `max_nodes`. Exceeding it raises a `ParseError` whose message starts with "Maximum number of AST nodes (N) exceeded". The default is `None` (no limit), so existing queries parse as before. The full suite passes (1084 tests, including 2 new ones), and ruff and mypy are clean. The changes are uncommitted in the worktree.

- **Scope of the limit:** the check is exact on the output tree. A query parses when `max_nodes` equals its node count and fails one below it. It is raised regardless of `error_level`, so `ErrorLevel.IGNORE` doesn't swallow it.
- **Runaway builds:** the parser also counts nodes created through `Parser.expression()` and raises as soon as that count passes the limit. This stops a pathological parse early instead of running to completion. That count is a lower bound on nodes built, because the parser constructs many nodes directly.
- **Backtracking:** the limit error is re-raised past the parser's internal try/fallback paths, so it is not swallowed and retried.
- **Wide queries:** a 500-column query parses normally, and a limit set at its exact node count (2016) passes.
- **Athena:** its custom constructor now forwards `max_nodes` to its sub-parsers. `_typing.py` gained the keyword for typed `parse_one` calls.

I did not hook `Expr.__init__`, which would count every node in every context. It would touch the hot path for all node creation and need a per-parse, thread-safe counter. I also did not benchmark the default path; it adds one increment and one method call per parsed node.

Files changed: `sqlglot/parser.py`, `sqlglot/_typing.py`, `sqlglot/parsers/athena.py`, `tests/test_parser.py`.

## events
[tool_use Bash] {"command": "git status --short && git log --oneline -1 && grep -n \"max_errors\\|def __init__\\|def parse_one\\|def parse(\\|class ParseError\\|def raise_error\\|def _parse_statement\\|def _parse(\" sqlglot/parser.py sqlglot/errors.py sqlglot/__init__.py | head -60", "description": "Check repo state and locate parser options"}
[tool_result] a3dd58323 lithify: probe base
sqlglot/__init__.py:108:def parse(
sqlglot/__init__.py:130:def parse_one(
sqlglot/__init__.py:141:def parse_one(
sqlglot/__init__.py:150:def parse_one(
sqlglot/errors.py:37:class ParseError(SqlglotError):
sqlglot/errors.py:38:    def __init__(
sqlglot/parser.py:291:        max_errors: Maximum number of error messages to include in a raised ParseError.
sqlglot/parser.py:299:        "max_errors",
sqlglot/parser.py:1823:    def __init__(
sqlglot/parser.py:1827:        max_errors: int = 3,
sqlglot/parser.py:1832:        self.max_errors: int = max_errors
sqlglot/parser.py:1949:    def raise_error(self, message: str, token: Token = SENTINEL_NONE) -> None:
sqlglot/parser.py:1996:    def parse(self, raw_tokens: list[Token], sql: str) -> list[exp.Expr | None]:
sqlglot/parser.py:2055:                concat_messages(self.errors, self.max_errors),
sqlglot/parser.py:2104:    def _parse(
sqlglot/parser.py:2241:    def _parse_statement(self) -> exp.Expr | None:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "offset": 280, "limit": 40}
[tool_result] 280	
281	class Parser:
282	    """
283	    Parser consumes a list of tokens produced by the Tokenizer and produces a parsed syntax tree.
284	
285	    Args:
286	        error_level: The desired error level.
287	            Default: ErrorLevel.IMMEDIATE
288	        error_message_context: The amount of context to capture from a query string when displaying
289	            the error message (in number of characters).
290	            Default: 100
291	        max_errors: Maximum number of error messag
…[450 chars elided]…
  "_prev_comments",
309	        "_pipe_cte_counter",
310	        "_chunks",
311	        "_chunk_index",
312	        "_tokens_size",
313	    )
314	
315	    FUNCTIONS: t.ClassVar[dict[str, t.Callable]] = {
316	        **{name: func.from_arg_list for name, func in exp.FUNCTION_BY_NAME.items()},
317	        **dict.fromkeys(("COALESCE", "IFNULL", "NVL"), build_coalesce),
318	        "ARRAY": lambda args, dialect: exp.Array(expressions=args),
319	        "ARRAYAGG": lambda args, dialect: exp.ArrayAgg(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "offset": 1815, "limit": 200}
[tool_result] 1815	
1816	    # Whether INTERVAL spans with literal format '\d+ hh:[mm:[ss[.ff]]]'
1817	    # can omit the span unit `DAY TO MINUTE` or `DAY TO SECOND`
1818	    SUPPORTS_OMITTED_INTERVAL_SPAN_UNIT: t.ClassVar = False
1819	
1820	    SHOW_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SHOW_PARSERS)
1821	    SET_TRIE: t.ClassVar[dict] = new_trie(key.split(" ") for key in SET_PARSERS)
1822	
1823	    def __init__(
1824	        self,
1825	        error_level: ErrorLevel | None = None,
18
…[6824 chars elided]…
ee
1999	        per parsed SQL statement.
2000	
2001	        Args:
2002	            raw_tokens: The list of tokens.
2003	            sql: The original SQL string.
2004	
2005	        Returns:
2006	            The list of the produced syntax trees.
2007	        """
2008	        return self._parse(
2009	            parse_method=self.__class__._parse_statement, raw_tokens=raw_tokens, sql=sql
2010	        )
2011	
2012	    def parse_into(
2013	        self,
2014	        expression_types: exp.IntoType,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/__init__.py", "offset": 100, "limit": 90}
[tool_result] 100	        dialect: the SQL dialect (alias for read).
101	
102	    Returns:
103	        The resulting list of tokens.
104	    """
105	    return Dialect.get_or_raise(read or dialect).tokenize(sql)
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
11
…[1783 chars elided]…
 = dialect.parse_into(into, sql, **opts)
175	    else:
176	        result = dialect.parse(sql, **opts)
177	
178	    if not result or result[0] is None:
179	        raise ParseError(f"No expression was parsed from '{sql}'")
180	
181	    return exp.Block(expressions=result) if len(result) > 1 else result[0]
182	
183	
184	def transpile(
185	    sql: str,
186	    read: DialectType = None,
187	    write: DialectType = None,
188	    identity: bool = True,
189	    error_level: ErrorLevel | None = None,
[tool_use Bash] {"command": "grep -n \"ParserNoDialectArgs\" -A12 sqlglot/parser.py | head -30; grep -n \"    def expression\\|    def expressions\\|def parse(\\|def parse_into\" -A3 sqlglot/parser.py sqlglot/dialects/dialect.py | head -60; sed -n 1996,2110p sqlglot/parser.py; grep -n \"ErrorLevel.RAISE\\|class ParseError\" -B2 -A12 sqlglot/errors.py | head -60", "description": "Inspect parser option types and expression creation"}
[tool_result] sqlglot/dialects/dialect.py:1115:    def parse(self, sql: str, **opts: Unpack[ParserArgs]) -> list[exp.Expr | None]:
sqlglot/dialects/dialect.py-1116-        return self.parser(**opts).parse(self.tokenize(sql), sql)
sqlglot/dialects/dialect.py-1117-
sqlglot/dialects/dialect.py:1118:    def parse_into(
sqlglot/dialects/dialect.py-1119-        self, expression_type: exp.IntoType, sql: str, **opts: Unpack[ParserArgs]
sqlglot/dialects/dialect.py-1120-    ) -> list[exp.Expr | None]:
sqlglot/dialects/
…[4651 chars elided]…
 parse_method: t.Callable[[Parser], exp.Expr | None],
        raw_tokens: list[Token],
        sql: str | None = None,
    ) -> list[exp.Expr | None]:
        self.reset()
35-
36-
37:class ParseError(SqlglotError):
38-    def __init__(
39-        self,
40-        message: str,
41-        errors: list[dict[str, t.Any]] | None = None,
42-    ):
43-        super().__init__(message)
44-        self.errors = errors or []
45-
46-    @classmethod
47-    def new(
48-        cls,
49-        message: str,
[tool_use Bash] {"command": "echo \"self.expression: $(grep -c 'self\\.expression(' sqlglot/parser.py)\"; echo \"direct exp.X(: $(grep -cE 'exp\\.[A-Z][A-Za-z0-9]*\\(' sqlglot/parser.py)\"; echo \"self.expression in dialects: $(grep -c 'self\\.expression(' sqlglot/dialects/*.py | awk -F: '{s+=$2} END {print s}')\"; sed -n 2110,2140p sqlglot/parser.py; grep -n \"def _parse_statement\" -A3 sqlglot/parser.py | head; grep -rn \"ParseError\" sqlglot/parser.py | head -30", "description": "Count node-construction call sites and parse flow"}
[tool_result] self.expression: 448
direct exp.X(: 533
self.expression in dialects: 0
        self.reset()
        self.sql = sql or ""

        total = len(raw_tokens)
        chunks: list[list[Token]] = [[]]

        for i, token in enumerate(raw_tokens):
            if token.token_type == TokenType.SEMICOLON:
                if token.comments:
                    chunks.append([token])

                if i < total - 1:
                    chunks.append([])
            else:
                chunks[-1].appen
…[779 chars elided]…
seError,
sqlglot/parser.py:291:        max_errors: Maximum number of error messages to include in a raised ParseError.
sqlglot/parser.py:1835:        self.errors: list[ParseError] = []
sqlglot/parser.py:1958:        error = ParseError.new(
sqlglot/parser.py:1987:        except ParseError:
sqlglot/parser.py:2039:            except ParseError as e:
sqlglot/parser.py:2043:        raise ParseError(
sqlglot/parser.py:2054:            raise ParseError(
sqlglot/parser.py:4110:        except ParseError:
[tool_use Bash] {"command": "grep -rn \"ParserNoDialectArgs\\|class ParserArgs\\|ParserArgs = \\|def parser(\" sqlglot | head; grep -n \"class ParserNoDialectArgs\" -A12 sqlglot/*.py sqlglot/dialects/dialect.py; grep -n \"    def parser\" -A3 sqlglot/dialects/dialect.py; sed -n 4100,4118p sqlglot/parser.py; grep -n \"max_errors\\|error_message_context\" -r sqlglot docs README.md 2>/dev/null | grep -v \"^sqlglot/parser.py\" | head", "description": "Find parser option typing and other ParseError catch sites"}
[tool_result] sqlglot/_typing.py:28:class ParserNoDialectArgs(t.TypedDict, total=False):
sqlglot/_typing.py:34:class ParserArgs(ParserNoDialectArgs, _DialectArg, total=False):
sqlglot/__init__.py:74:    from sqlglot._typing import E, GeneratorArgs, ParserNoDialectArgs
sqlglot/__init__.py:112:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:136:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:146:    **opts: Unpack[ParserNoDialectArgs],
sqlglot/__init__.py:155:    **opts: Unpack[ParserN
…[1830 chars elided]…
/parsers/athena.py:29:        max_errors: int = 3,
sqlglot/parsers/athena.py:42:            error_message_context=error_message_context,
sqlglot/parsers/athena.py:43:            max_errors=max_errors,
sqlglot/parsers/athena.py:49:            error_message_context=error_message_context,
sqlglot/parsers/athena.py:50:            max_errors=max_errors,
sqlglot/parsers/athena.py:54:            error_message_context=error_message_context,
sqlglot/parsers/athena.py:55:            max_errors=max_errors,
[tool_use Bash] {"command": "grep -rln \"max_errors\" sqlglot | sort; echo ---; grep -rn \"def __init__\" sqlglot/parsers sqlglot/dialects | head -20; echo ---; sed -n 1,60p sqlglot/parsers/athena.py | head -70; ls tests | head -50; grep -rn \"max_errors\" tests | head", "description": "Find parser subclasses that forward constructor args"}
[tool_result] sqlglot/_typing.py
sqlglot/generators/singlestore.py
sqlglot/parser.py
sqlglot/parsers/athena.py
---
sqlglot/parsers/athena.py:25:    def __init__(
sqlglot/dialects/dialect.py:974:    def __init__(self, **kwargs) -> None:
sqlglot/dialects/athena.py:70:        def __init__(self, dialect: DialectType = None) -> None:
---
from __future__ import annotations

import typing as t

from sqlglot import exp
from sqlglot.errors import ErrorLevel
from sqlglot.parser import Parser
from sqlglot.parsers.trino 
…[1728 chars elided]…
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
[tool_use Bash] {"command": "timeout 900 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run baseline test suite before changes", "timeout": 900000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run baseline test suite before changes", "timeout": 900000}
[tool_result] ................................................................................. [  7%]
........................................................................................................................................... [ 20%]
......................................................................................... [ 28%]
...................................................................................................................................................................... 
…[244 chars elided]…
64%]
......................................................... [ 69%]
............................................... [ 73%]
.................................................................................................................................................................................................................................................. [ 96%]
............ [ 97%]
.............. [ 98%]
.................               [100%]
1082 passed, 17840 subtests passed in 40.21s
[assistant] Baseline is green (1082 passed). Now the edits: parser state and option first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        max_errors: Maximum number of error messages to include in a raised ParseError.\n            This is only relevant if error_level is ErrorLevel.RAISE.\n            Default: 3\n    \"\"\"\n\n    __slots__ = (\n  
…[270 chars elided]…
evel.RAISE.\n            Default: 3\n        max_nodes: Maximum number of AST nodes that parsing may build. Exceeding it raises a\n            ParseError regardless of error_level. Default: None (no limit).\n    \"\"\"\n\n    __slots__ = (\n        \"error_level\",\n        \"error_message_context\",\n        \"max_errors\",\n        \"max_nodes\",\n        \"_node_count\",\n        \"dialect\","}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        max_errors: int = 3,\n        dialect: DialectType = None,\n    ):\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n  
…[301 chars elided]…
\n        self.error_level: ErrorLevel = error_level or ErrorLevel.IMMEDIATE\n        self.error_message_context: int = error_message_context\n        self.max_errors: int = max_errors\n        self.max_nodes: int | None = max_nodes\n        self._node_count: int = 0\n        self.dialect: t.Any = _resolve_dialect(dialect)\n        self.sql: str = \"\"\n        self.errors: list[ParseError] = []"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "    def reset(self) -> None:\n        self.sql = \"\"\n        self.errors = []\n        self._tokens = []", "new_string": "    def reset(self) -> None:\n        self.sql = \"\"\n        self.errors = []\n        self._node_count = 0\n        self._tokens = []"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the counting point in `expression()`, the backtracking sites that must not swallow the limit error, and a final check in `_parse`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "    def expression(\n        self,\n        instance: E,\n        token: Token | None = None,\n        comments: list[str] | None = None,\n    ) -> E:\n        if token:", "new_string": "    def _node_limit_exceeded(sel
…[124 chars elided]…
lf) -> ParseError:\n        return ParseError(f\"Maximum number of AST nodes ({self.max_nodes}) exceeded\")\n\n    def expression(\n        self,\n        instance: E,\n        token: Token | None = None,\n        comments: list[str] | None = None,\n    ) -> E:\n        self._node_count += 1\n        if self._node_limit_exceeded():\n            raise self._node_limit_error()\n\n        if token:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        try:\n            this = parse_method()\n        except ParseError:\n            this = None", "new_string": "        try:\n            this = parse_method()\n        except ParseError:\n            if self._node_limit_exceeded():\n                raise\n            this = None"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "            try:\n                return self._parse(parser, raw_tokens, sql)\n            except ParseError as e:\n                e.errors[0][\"into_expression\"] = expression_type", "new_string": "            try:\n                return self._parse(parser, raw_tokens, sql)\n            except ParseError as e:\n                if self._node_limit_exceeded():\n                    raise\n                e.errors[0][\"into_expression\"] = expression_type"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        self._chunks = chunks\n\n        return self._parse_batch_statements(parse_method=parse_method, sep_first_statement=False)", "new_string": "        self._chunks = chunks\n\n        expressions = self._parse_batch_statements(\n            parse_method=parse_method, sep_first_statement=False\n        )\n\n        # Backtracking may have swallowed the limit error, so re-check before returning\n        if self._node_limit_exceeded():\n            raise self._node_limit_error()\n\n        return expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the typed-kwargs entry and the Athena parser, which re-declares its constructor and would otherwise drop the option.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py", "old_string": "    max_errors: int\n\n\nclass ParserArgs", "new_string": "    max_errors: int\n    max_nodes: int | None\n\n\nclass ParserArgs"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/_typing.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parsers/athena.py", "old_string": "        max_errors: int = 3,\n        dialect: DialectType = None,\n        hive: Hive | None = None,\n        trino: Trino | None = None,\n    ) -> None:\n        from sqlglot.dialects.hive import Hive\n       
…[1406 chars elided]…
evel,\n            error_message_context=error_message_context,\n            max_errors=max_errors,\n            max_nodes=max_nodes,\n        )\n        self._trino_parser = AthenaTrinoParser(\n            error_level=error_level,\n            error_message_context=error_message_context,\n            max_errors=max_errors,\n            dialect=trino,\n            max_nodes=max_nodes,\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parsers/athena.py has been updated successfully.
[assistant] Now I'll check behavior empirically: wide query, a pathological input, and how much of the real tree the counter sees (the parser builds many nodes directly, not via `expression()`).
[tool_use Bash] {"command": "cat > /tmp/max_nodes_probe.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfrom sqlglot.errors import ParseError\nfrom sqlglot.parser import Parser\n\nwide = \"SELECT \" + \", \".join(f\"c{i} AS a{i}\" for i in range(500)) + \" FROM t WHERE x = 1 AND y IN (1, 2, 3)\"\ntree = sqlglot.parse_one(wide)\ntotal = sum(1 for _ in tree.walk())\nprint(\"wide total nodes:\", total)\nprint(\
…[1076 chars elided]…
e(big, max_nodes=lim)\n        print(\"big ok under\", lim)\n    except ParseError as e:\n        print(\"big raised under\", lim, \"->\", str(e).splitlines()[0])\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/max_nodes_probe.py').read())\"", "description": "Probe max_nodes behavior and counter accuracy"}
[tool_result] wide total nodes: 2016
default ok: True
max_nodes=total ok: True
NO RAISE at total-1
counter 1513 real 2016 SELECT c0 AS a0, c1 AS a1, c2 AS a2, c3 
counter 27 real 36 SELECT a + b * c FROM t JOIN u ON t.id =
counter 10 real 13 SELECT COUNT(*) FROM (SELECT x FROM y) A
big raised under 1000 -> Maximum number of AST nodes (1000) exceeded
big ok under 100000
[assistant] The counter undercounts: the wide query has 2016 real nodes but `expression()` only sees 1513, so a limit at the true size doesn't fire. Counting at `expression()` is not the right place. Let me see whether node construction itself is a cheap central hook.
[tool_use Bash] {"command": "grep -rn \"class Expression\\b\\|class Expression(\" sqlglot/expressions/*.py sqlglot/*.py | head -3; f=$(grep -rln \"^class Expression(\" sqlglot | head -1); echo $f; n=$(grep -n \"^class Expression(\" $f | cut -d: -f1); sed -n \"$n,$((n+60))p\" $f | grep -n \"def __init__\" -A25 | head -45; ls sqlglot/expressions/ | head -30", "description": "Inspect Expression constructor for a central counting hook"}
[tool_result] sqlglot/expressions/core.py:532:class Expression(Expr):
sqlglot/expressions/core.py
__init__.py
__pycache__
aggregate.py
array.py
builders.py
constraints.py
core.py
datatypes.py
ddl.py
dml.py
functions.py
json.py
math.py
properties.py
query.py
string.py
temporal.py
[tool_use Bash] {"command": "grep -n \"def __init__\" sqlglot/expressions/core.py | head; sed -n 532,600p sqlglot/expressions/core.py | grep -n \"__init__\\|__slots__\\|def \" | head -20; grep -n \"class Expr\\b\\|class Expr(\" -A5 sqlglot/expressions/core.py | head -20", "description": "Locate Expression.__init__ in core module"}
[tool_result] 113:    def __init__(self, **args: object) -> None:
2003:    def __init__(self, **args: object) -> None:
2:    __slots__ = (
13:    def __eq__(self, other: object) -> bool:
16:    def __ne__(self, other: object) -> bool:
19:    def __hash__(self) -> int:
57:    def __reduce__(
68:    def this(self) -> t.Any:
52:class Expr:
53-    """
54-    The base class for all expressions in a syntax tree. Each Expr encapsulates any necessary
55-    context, such as its child expressions, their names (arg keys), and whether a given child expression
56-    is optional or not.
57-
[tool_use Bash] {"command": "sed -n 108,130p sqlglot/expressions/core.py; sed -n 1998,2015p sqlglot/expressions/core.py", "description": "Read both __init__ bodies in core.py"}
[tool_result]         # This is so that docstrings are not inherited in pdoc
        setattr(cls, "__doc__", getattr(cls, "__doc__", None) or "")

    is_primitive: t.ClassVar[bool] = False

    def __init__(self, **args: object) -> None:
        self.args: dict[str, t.Any] = args
        self.parent: Expr | None = None
        self.arg_key: str | None = None
        self.index: int | None = None
        self.comments: list[str] | None = None
        self._type: DataType | None = None
        self._meta: dict
…[383 chars elided]…

    def __init__(self, **args: object) -> None:
        super().__init__(**args)

        unit = self.args.get("unit")
        if (
            unit
            and type(unit) in TimeUnit.VAR_LIKE
            and not (isinstance(unit, Column) and len(unit.parts) != 1)
        ):
            unit = Var(this=(self.UNABBREVIATED_UNIT_NAME.get(unit.name) or unit.name).upper())
            self.args["unit"] = unit
            self._set_parent("unit", unit)
        elif type(unit).__name__ == "Week":
[assistant] `Expr.__init__` is the one place every node passes through, but hooking it means touching the hot path for every node in every context (parser, optimizer, generator), and the counter would need to be per-parse and thread-safe. That's too invasive for this change. I'll keep the counter in the parser and make the final check exact by counting the output tree too. Checking `walk()` first:
[tool_use Bash] {"command": "grep -n \"    def walk\" -A12 sqlglot/expressions/core.py | head -30", "description": "Check Expr.walk signature"}
[tool_result] 253:    def walk(
254-        self, bfs: bool = True, prune: t.Callable[[Expr], bool] | None = None
255-    ) -> Iterator[Expr]:
256-        raise NotImplementedError
257-
258-    def dfs(self, prune: t.Callable[[Expr], bool] | None = None) -> Iterator[Expr]:
259-        raise NotImplementedError
260-
261-    def bfs(self, prune: t.Callable[[Expr], bool] | None = None) -> Iterator[Expr]:
262-        raise NotImplementedError
263-
264-    def unnest(self) -> Expr:
265-        raise NotImplemented
…[60 chars elided]…
e, prune: t.Callable[[Expr], bool] | None = None
981-    ) -> Iterator[Expr]:
982-        """
983-        Returns a generator object which visits all nodes in this tree.
984-
985-        Args:
986-            bfs: if set to True the BFS traversal order will be applied,
987-                otherwise the DFS traversal will be used instead.
988-            prune: callable that returns True if the generator should stop traversing
989-                this branch of the tree.
990-
991-        Returns:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py", "old_string": "        # Backtracking may have swallowed the limit error, so re-check before returning\n        if self._node_limit_exceeded():\n            raise self._node_limit_error()\n\n        return expressions", "new_string": 
…[53 chars elided]…
error, and created nodes are not always\n        # visible through `expression`, so the output tree is counted as well\n        if self.max_nodes is not None:\n            output_nodes = sum(sum(1 for _ in e.walk()) for e in expressions if e)\n            if self._node_limit_exceeded() or output_nodes > self.max_nodes:\n                raise self._node_limit_error()\n\n        return expressions"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-090729-parser-add-a-safeguard-against-p/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "cat > /tmp/max_nodes_probe2.py <<'EOF'\nimport sqlglot\nfrom sqlglot.errors import ParseError\n\ndef output_count(tree):\n    return sum(1 for _ in tree.walk())\n\nqueries = [\n    \"SELECT \" + \", \".join(f\"c{i} AS a{i}\" for i in range(500)) + \" FROM t WHERE x = 1 AND y IN (1, 2, 3)\",\n    \"SELECT a + b * c FROM t JOIN u ON t.id = u.id WHERE CAST(x AS INT) > 3 GROUP BY 1 ORDER 
…[1044 chars elided]…
g ok under 1000\")\nexcept ParseError as e:\n    print(\"big raised:\", str(e).splitlines()[0])\nprint(\"big default:\", len(sqlglot.parse_one(big).sql()) > 0)\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/tmp/max_nodes_probe2.py').read())\"", "description": "Verify exact node-limit boundary across queries"}
[tool_result] exact boundary ok: 2016 SELECT c0 AS a0, c1 AS a1, c2 AS a2, c3 AS a3, c4 
exact boundary ok: 36 SELECT a + b * c FROM t JOIN u ON t.id = u.id WHER
exact boundary ok: 13 SELECT COUNT(*) FROM (SELECT x FROM y) AS z
exact boundary ok: 17 SELECT 1; SELECT 2 FROM t; CREATE TABLE x (a INT, 
exact boundary ok: 17 SELECT ((((((1)))))) + (2 * (3 - (4)))
exact boundary ok: 19 WITH a AS (SELECT 1 AS x) SELECT * FROM a UNION AL
big raised: Maximum number of AST nodes (1000) exceeded
big default: True
[assistant] The boundary is exact: each query parses at its true node count and fails one below it. Now tests. Let me check the existing parser test layout.
[tool_use Bash] {"command": "sed -n 1,20p tests/test_parser.py; grep -n \"^class \\|    def test_\" tests/test_parser.py | tail -8; tail -5 tests/test_parser.py", "description": "Inspect test_parser.py structure"}
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
[tool_use Bash] {"command": "cat >> tests/test_parser.py <<'EOF'\n\n    def test_max_nodes(self):\n        wide = \"SELECT \" + \", \".join(f\"c{i} AS a{i}\" for i in range(500)) + \" FROM t\"\n        node_count = sum(1 for _ in parse_one(wide).walk())\n\n        self.assertIsNotNone(parse_one(wide))\n        self.assertIsNotNone(parse_one(wide, max_nodes=node_count))\n\n        with self.assertRaisesRegex(Parse
…[341 chars elided]…
 with self.assertRaisesRegex(ParseError, \"Maximum number of AST nodes\"):\n            parse(\"SELECT a, b, c, d, e, f FROM t\", max_nodes=3, error_level=ErrorLevel.IGNORE)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_parser.py -k max_nodes 2>&1 | tail -15", "description": "Add max_nodes tests and run them"}
[tool_result] ..                                                                       [100%]
2 passed, 63 deselected in 0.08s
[assistant] Both new tests pass. Now the full suite, plus the linter and type checker the project uses.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"--- ruff\"; $PY -m ruff check sqlglot/parser.py sqlglot/parsers/athena.py sqlglot/_typing.py tests/test_parser.py 2>&1 | tail -3; $PY -m ruff format --check sqlglot/parser.py sqlglot/parsers/athena.py sqlglot/_typing.py tests/test_parser.
…[182 chars elided]…
m sqlglot.dialects.athena import Athena; from sqlglot.errors import ParseError\ntry:\n  Athena().parse('SELECT a, b, c, d FROM t', max_nodes=3); print('athena no raise')\nexcept ParseError as e: print('athena raised:', str(e).splitlines()[0])\nprint(len(Athena().parse('SELECT a, b, c, d FROM t', max_nodes=1000)))\"", "description": "Run full tests, ruff, mypy, and Athena check", "timeout": 900000}
[tool_result] .......................... [ 98%]
...................             [100%]
1084 passed, 17840 subtests passed in 38.21s
--- ruff
All checks passed!
4 files already formatted
--- mypy
Success: no issues found in 2 source files
--- athena
athena raised: Maximum number of AST nodes (3) exceeded
1
[assistant] All green. Last, a look at the final diff.
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff sqlglot/parser.py | head -150", "description": "Review final diff of parser changes"}
[tool_result]  M sqlglot/_typing.py
 M sqlglot/parser.py
 M sqlglot/parsers/athena.py
 M tests/test_parser.py
 sqlglot/_typing.py        |  1 +
 sqlglot/parser.py         | 35 ++++++++++++++++++++++++++++++++++-
 sqlglot/parsers/athena.py |  4 ++++
 tests/test_parser.py      | 17 +++++++++++++++++
 4 files changed, 56 insertions(+), 1 deletion(-)
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 107ad1ec0..0fa3a0538 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -291,12 +291,16 @@ class Pars
…[3109 chars elided]…
e swallowed the limit error, and created nodes are not always
+        # visible through `expression`, so the output tree is counted as well
+        if self.max_nodes is not None:
+            output_nodes = sum(sum(1 for _ in e.walk()) for e in expressions if e)
+            if self._node_limit_exceeded() or output_nodes > self.max_nodes:
+                raise self._node_limit_error()
+
+        return expressions
 
     def _warn_unsupported(self) -> None:
         if self._tokens_size <= 1:
[assistant] `parse_one` and `parse` now accept `max_nodes`. Exceeding it raises a `ParseError` whose message starts with "Maximum number of AST nodes (N) exceeded". The default is `None` (no limit), so existing queries parse as before. The full suite passes (1084 tests, including 2 new ones), and ruff and mypy are clean. The changes are uncommitted in the worktree.

- **Scope of the limit:** the check is exact on the output tree. A query parses when `max_nodes` equals its node count and fails one below it. It is raised regardless of `error_level`, so `ErrorLevel.IGNORE` doesn't swallow it.
- **Runaway bui
…[464 chars elided]…
arses normally, and a limit set at its exact node count (2016) passes.
- **Athena:** its custom constructor now forwards `max_nodes` to its sub-parsers. `_typing.py` gained the keyword for typed `parse_one` calls.

I did not hook `Expr.__init__`, which would count every node in every context. It would touch the hot path for all node creation and need a per-parse, thread-safe counter. I also did not benchmark the default path; it adds one increment and one method call per parsed node.

Files changed: `sqlglot/parser.py`, `sqlglot/_typing.py`, `sqlglot/parsers/athena.py`, `tests/test_parser.py`.
