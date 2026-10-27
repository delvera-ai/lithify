# trajectory base-1

final message:
Both parts are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1101 tests), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`** returns `dict[str, Node]` keyed by each top-level output name. `column` stays a required argument, so callers pass `None` explicitly. Typing overloads make `lineage("a", ...)` resolve to `Node` and `lineage(None, ...)` to `dict[str, Node]`, which I confirmed with mypy.
- **`on_node`** is an optional callback on `lineage()` and `to_node()`. It fires once for every `Node` the walk creates, including leaves and union nodes, after that node's downstream is complete.
- **`Node.payload`** is a `dict` field defaulting to a fresh empty dict per node. It is the last field, so existing positional construction still works.

Choices you may want to redirect:
- For `column=None`, all columns share one memo cache. Shared upstream nodes are reused and `on_node` fires once per node across the whole result.
- With an unexpanded `*` and no schema, the dict key is `"*"`. Duplicate output names collapse into one dict entry.
- I threaded `on_node` through `to_node()` as an explicit keyword before `_cache`, following the pattern `trim_selects` already uses.

When you commit, the repo's CONTRIBUTING rules ask for the model name in the commit message and PR title.

## events
[tool_use Bash] {"command": "cat sqlglot/lineage.py; git status --short | head", "description": "Read lineage module and check git status"}
[tool_result] from __future__ import annotations

import json
import logging
import typing as t
from dataclasses import dataclass, field

from sqlglot import Schema, exp, maybe_parse
from sqlglot.errors import SqlglotError
from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
from sqlglot.optimizer.scope import ScopeType

if t.TYPE_CHECKING:
    from sqlglot.dialects.dialect import DialectType
    from collections.abc import Iterator, Mapping, Sequence
    from sq
…[16422 chars elided]…
lineage"></div>
  {imports}
  <script type="text/javascript">
    var nodes = new vis.DataSet({nodes})
    nodes.forEach(row => row["title"] = new DOMParser().parseFromString(row["title"], "text/html").body.childNodes[0])

    new vis.Network(
        document.getElementById("sqlglot-lineage"),
        {{
            nodes: nodes,
            edges: new vis.DataSet({edges})
        }},
        {options},
    )
  </script>
</div>"""

    def _repr_html_(self) -> str:
        return self.__str__()
[assistant] The lineage module is small. Before editing, I'll check the test environment, existing lineage tests, and other `Node` users that the new field could affect.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; grep -rn \"lineage\\|to_node\" --include=*.py . | grep -v \"^./sqlglot/lineage.py\" | grep -v \"^./tests/test_lineage.py\" | head -30; grep -n \"^class\\|def test\" tests/test_lineage.py | head -60; wc -l tests/test_lineage.py", "description": "Check test python, find lineage usages and existing tests"}
[tool_result] <work>/env-sqlglot/bin/python
(eval):1: no matches found: --include=*.py
10:class TestLineage(unittest.TestCase):
17:    def test_lineage(self) -> None:
67:    def test_lineage_sql_with_cte(self) -> None:
98:    def test_lineage_source_with_cte(self) -> None:
128:    def test_lineage_source_with_star(self) -> None:
148:    def test_lineage_join_with_star(self) -> None:
169:  
…[955 chars elided]…
ot_with_cte(self) -> None:
656:    def test_pivot_with_implicit_column_of_pivoted_source(self) -> None:
670:    def test_pivot_with_implicit_column_of_pivoted_source_and_cte(self) -> None:
688:    def test_table_udtf_snowflake(self) -> None:
733:    def test_pivot_with_subquery(self) -> None:
770:    def test_copy_flag(self) -> None:
820:    def test_lineage_shared_cte_performance(self) -> None:
857:    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
     864 tests/test_lineage.py
[tool_use Bash] {"command": "grep -rln \"lineage\" --include=*.py sqlglot tests benchmarks posts 2>/dev/null; sed -n 1,66p tests/test_lineage.py; sed -n 820,864p tests/test_lineage.py", "description": "Find lineage references and read test file header and tail"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rl \"lineage\" sqlglot tests posts benchmarks 2>/dev/null; echo ---; sed -n 1,66p tests/test_lineage.py; echo ---; sed -n 820,864p tests/test_lineage.py", "description": "Find lineage references and read test file header and tail"}
[tool_result] sqlglot/lineage.py
tests/test_lineage.py
posts/onboarding.md
posts/ast_primer.md
---
from __future__ import annotations

import unittest

import sqlglot
from sqlglot.lineage import lineage
from sqlglot.schema import MappingSchema


class TestLineage(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        sqlglot.schema = MappingSchema()

    def test_lineage(self) -> None:
        node = lineage(
            "a",
            "SELECT a FROM z",
            schema
…[2900 chars elided]…
tGreater(len(leaves), 0)
        self.assertTrue(all("base_table" in n.source.sql() for n in leaves))

    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
        node = lineage(
            "combined",
            "WITH shared AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
[assistant] I have the picture: `to_node` is the recursive walker, and every node is created in one of five places. I'll thread `on_node` through it the same way `_cache` is threaded, add the `payload` field, and add the `column=None` branch with overloads.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence\n    from sqlglot._typing import GraphHTMLArgs\n    from typing_extensions import Unpack\n\nlogger = logging.getLogger(\"sqlglot\")\n\n\n@dataclass(frozen=Tru
…[317 chars elided]…
 import GraphHTMLArgs\n    from typing_extensions import Unpack\n\nlogger = logging.getLogger(\"sqlglot\")\n\n\n@dataclass(frozen=True)\nclass Node:\n    name: str\n    expression: exp.Expr\n    source: exp.Expr\n    downstream: list[Node] = field(default_factory=list)\n    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the public `lineage()` function: overloads, the `column=None` branch, and `on_node`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2916 chars elided]…
a in `payload`.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each output column name to its lineage node if\n        `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[1469 chars elided]…
    return node\n\n\ndef to_node(\n    column: str | int,\n    scope: Scope,\n    dialect: DialectType,\n    scope_name: str | None = None,\n    upstream: Node | None = None,\n    source_name: str | None = None,\n    reference_node_name: str | None = None,\n    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the body of `to_node`: propagate `on_node` into each recursive call and fire it at each node-creation site.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                source_name=source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n            # Skip caching", "new_string": "                source_name=source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n            # Skip caching"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        for s in scope.union_scopes:\n            to_node(\n                index,\n                scope=s,\n                dialect=dialect,\n                upstream=upstream,\n                source_name=source_nam
…[477 chars elided]…
       source_name=source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n\n        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        if created_setop:\n            _emit(upstream, on_node)\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        for name in subquery.named_selects:\n            to_node(\n                name,\n                scope=subquery_scope,\n                dialect=dialect,\n                upstream=node,\n                trim_se
…[824 chars elided]…
rces as downstreams\n    if isinstance(select, exp.Star):\n        for src in scope.sources.values():\n            src_expr = src.expression if isinstance(src, Scope) else src\n            node.downstream.append(\n                _emit(\n                    Node(name=select.sql(comments=False), source=src_expr, expression=src_expr),\n                    on_node,\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                scope_name=table,\n                upstream=node,\n                source_name=source_names.get(table) or source_name,\n                reference_node_name=reference_node_name,\n                trim_sel
…[114 chars elided]…
.table:", "new_string": "                scope_name=table,\n                upstream=node,\n                source_name=source_names.get(table) or source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n        elif pivot and pivot.alias_or_name == c.table:"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                        source_name=source_names.get(table) or source_name,\n                        reference_node_name=reference_node_name,\n                        trim_selects=trim_selects,\n                       
…[838 chars elided]…
       node.downstream.append(\n                        _emit(\n                            Node(\n                                name=downstream_column.sql(comments=False),\n                                source=col_expr,\n                                expression=col_expr,\n                            ),\n                            on_node,\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                _emit(Node(name=c.sql(comments=False), source=col_expr, expression=col_expr), on_node)\n            )\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return _emit(node, on_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] All the edit sites are in. I'll run the existing lineage tests and a quick behavioural check, using the project's test interpreter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Run existing lineage test suite"}
[tool_result] ...............................                                          [100%]
31 passed in 0.32s
[assistant] Existing tests pass. Now I'll check the new behaviour directly: callback coverage against the walked graph, downstream completeness at callback time, `payload` isolation, and the `column=None` form across union, star, subquery and pivot queries.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cd ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1 && $PY - <<'EOF'\nfrom sqlglot.lineage import lineage, Node\n\ncases = [\n    (\"SELECT a, b + 1 AS c FROM x\", {\"x\":
…[1612 chars elided]…
": \"int\"}}, on_node=tag)\nassert isinstance(node, Node)\nprint(\"single:\", type(node).__name__, node.payload, [n.payload for n in node.downstream])\n\n# payload default isolation\na, b = Node(\"a\", None, None), Node(\"b\", None, None)\na.payload[\"k\"] = 1\nassert b.payload == {}\nprint(\"payload isolation OK\")\nEOF", "description": "Check callback coverage, payload, and dict-form behaviour"}
[tool_result] OK SELECT a, b + 1 AS c FROM x | keys: ['a', 'c'] | nodes: 4
OK SELECT a FROM (SELECT a FROM x) AS s | keys: ['a'] | nodes: 3
OK WITH c AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined F | keys: ['combined'] | nodes: 5
OK SELECT a FROM x UNION ALL SELECT a FROM y | keys: ['a'] | nodes: 5
OK SELECT * FROM x JOIN y ON x.a = y.a | keys: ['a', 'b'] | nodes: 4
OK SELECT * FROM x | keys: ['*'] | nodes: 2
OK SELECT a FROM x PIVOT(SUM(b) FOR a IN ('p', 'q')) | keys: ['a'] | nodes: 2
single: Node {'depth_hint': 'c'} [{'depth_hint': 'x.b'}]
payload isolation OK
[assistant] Coverage, ordering, and dict-form checks all hold across seven query shapes. Now I'll add permanent tests to `tests/test_lineage.py`, appended to the existing class.
[tool_use Bash] {"command": "tail -c 200 tests/test_lineage.py | od -c | tail -3", "description": "Check trailing bytes of test file"}
[tool_result] 0000260    a   m   e   s   ,       [   "   s   1   .   a   "   ,       "
0000300    s   2   .   a   "   ]   )  \n                                
0000310
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        downstream_names = sorted(d.name for d in node.downstream)\n        self.assertEqual(downstream_names, [\"s1.a\", \"s2.a\"])", "new_string": "        downstream_names = sorted(d.name for d in node.downstream
…[2456 chars elided]…
wnstream[0].payload, {\"name\": \"x.a\"})\n\n    def test_lineage_node_payload_default(self) -> None:\n        first = sqlglot.lineage.Node(name=\"a\", expression=sqlglot.exp.null(), source=sqlglot.exp.null())\n        second = sqlglot.lineage.Node(name=\"b\", expression=sqlglot.exp.null(), source=sqlglot.exp.null())\n        first.payload[\"k\"] = 1\n        self.assertEqual(second.payload, {})"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Run lineage tests including new ones"}
[tool_result] E       ?   ^    ^

tests/test_lineage.py:888: AssertionError
___________________ TestLineage.test_lineage_on_node_payload ___________________

self = <tests.test_lineage.TestLineage testMethod=test_lineage_on_node_payload>

    def test_lineage_on_node_payload(self) -> None:
        def on_node(node: sqlglot.lineage.Node) -> None:
            node.payload["name"] = node.name
    
        node = lineage(
            "a",
            "SELECT a FROM (SELECT a FROM x) AS s",
            schema={"x"
…[131 chars elided]…
ual(node.downstream[0].payload, {"name": "a"})
E       AssertionError: {'name': 's.a'} != {'name': 'a'}
E       - {'name': 's.a'}
E       ?           --
E       
E       + {'name': 'a'}

tests/test_lineage.py:921: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_lineage_all_columns_union - A...
FAILED tests/test_lineage.py::TestLineage::test_lineage_on_node_payload - Ass...
2 failed, 34 passed in 0.11s
[assistant] Two failures. The payload one is my expectation being wrong: the inner node is named `s.a` by the existing naming scheme. I'll check the union failure before correcting either.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.lineage import lineage\nn = lineage(None, 'SELECT a FROM x UNION ALL SELECT a FROM y', schema={'x': {'a': 'int'}, 'y': {'a': 'int'}})\nprint(n['a'].name, [d.name for d in n['a'].downstream], [d.name for d in n['a'].downstream[0].downstream] if n['a'].downstream else None)\nprint(lineage('a', 'SELECT a FROM x UNION ALL SELECT a FROM y', schema={'x': {'a': 'int'}, 'y': {'a': 'int'}}).name)\n\" 2>&1 | tail -5", "description": "Inspect union lineage node names"}
[tool_result] UNION ['0', '0'] ['x.a']
UNION
[assistant] Both are wrong expectations on my side, not code bugs: the union's children are named by index (`'0'`) and the leaves are `x.a` and `y.a`. I'll correct the tests to assert the real structure, and tidy the `Node` references to a direct import.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(list(nodes), [\"a\"])\n        self.assertEqual(nodes[\"a\"].name, \"UNION\")\n        self.assertEqual(sorted(d.name for d in nodes[\"a\"].downstream), [\"a\", \"a\"])", "new_string": "        self.assertEqual(list(nodes), [\"a\"])\n        self.assertEqual(nodes[\"a\"].name, \"UNION\")\n        leaves = sorted(n.name for n in nodes[\"a\"].walk() if not n.downstream)\n        self.assertEqual(leaves, [\"x.a\", \"y.a\"])"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        self.assertEqual(node.payload, {\"name\": \"a\"})\n        self.assertEqual(node.downstream[0].payload, {\"name\": \"a\"})\n        self.assertEqual(node.downstream[0].downstream[0].payload, {\"name\": \"x.a
…[495 chars elided]…
ame\": \"s.a\"})\n        self.assertEqual(node.downstream[0].downstream[0].payload, {\"name\": \"x.a\"})\n\n    def test_lineage_node_payload_default(self) -> None:\n        first = Node(name=\"a\", expression=exp.null(), source=exp.null())\n        second = Node(name=\"b\", expression=exp.null(), source=exp.null())\n        first.payload[\"k\"] = 1\n        self.assertEqual(second.payload, {})"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-144033-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "sed -i '' 's/^from sqlglot.lineage import lineage$/from sqlglot import exp\\nfrom sqlglot.lineage import Node, lineage/' tests/test_lineage.py && sed -i '' 's/sqlglot\\.lineage\\.Node/Node/g' tests/test_lineage.py && sed -n 1,10p tests/test_lineage.py && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; ls $(dirname $PY) | grep -E \"^(ruff|mypy)$\"", "description": "Tidy imports, rerun lineage tests, check for ruff and mypy"}
[tool_result] from __future__ import annotations

import unittest

import sqlglot
from sqlglot import exp
from sqlglot.lineage import Node, lineage
from sqlglot.schema import MappingSchema


....................................                                     [100%]
36 passed in 0.10s
mypy
ruff
[This command modified 1 file you've previously read: tests/test_lineage.py. Call Read before editing.]
[assistant] All 36 lineage tests pass. The tool notice about `test_lineage.py` is from my own `sed` edit just above, so the file is as intended. Next, the project's style and type checks: ruff and mypy.
[tool_use Bash] {"command": "grep -n -A6 \"^style:\" Makefile; PY=<work>/env-sqlglot/bin; $PY/ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY/ruff check sqlglot/lineage.py tests/test_lineage.py; $PY/mypy sqlglot/lineage.py 2>&1 | tail -15", "description": "Run ruff format, ruff check, and mypy on changed files"}
[tool_result] 96:style:
97-	pre-commit run --all-files
98-	@if [ -f sqlglot-integration-tests/Makefile ]; then $(MAKE) -C sqlglot-integration-tests check-submodule; fi
99-
100-check: style test testc
101-
102-docs:
Would reformat: sqlglot/lineage.py
1 file would be reformatted, 1 file already formatted
All checks passed!
Success: no issues found in 1 source file
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/ruff format sqlglot/lineage.py && git diff --stat && git diff sqlglot/lineage.py | head -150", "description": "Apply ruff formatting and review the lineage diff"}
[tool_result] 1 file reformatted
 sqlglot/lineage.py    | 102 +++++++++++++++++++++++++++++++++++++++++++-------
 tests/test_lineage.py |  68 ++++++++++++++++++++++++++++++++-
 2 files changed, 156 insertions(+), 14 deletions(-)
diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 00b1c1fbd..d5a534ffb 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -12,7 +12,7 @@ from sqlglot.optimizer.scope import ScopeType
 
 if t.TYPE_CHECKING:
     from sqlglot.dialects.dialect import DialectType
-    fr
…[4631 chars elided]…
ce_name, reference_node_name)
@@ -182,6 +243,7 @@ def to_node(
                 source_name=source_name,
                 reference_node_name=reference_node_name,
                 trim_selects=trim_selects,
+                on_node=on_node,
                 _cache=_cache,
             )
             # Skip caching a passed-in upstream returned by an inner SetOp:
@@ -220,11 +282,14 @@ def to_node(
[This command modified 1 file you've previously read: sqlglot/lineage.py. Call Read before editing.]
[assistant] Formatting applied, and the diff reads as intended. Now the full test suite with the harness's command, plus a mypy pass over the test file.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -6; $PY/ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY/ruff check sqlglot/lineage.py tests/test_lineage.py; $PY/mypy sqlglot/lineage.py 2>&1 | tail -2", "description": "Run full test suite, ruff, and mypy"}
[tool_result] ............................................. [ 78%]
....................................................... [ 83%]
..................................................... [ 88%]
................................. [ 91%]
.............................................................................................                            [100%]
1101 passed, 17880 subtests passed in 56.96s
2 files already formatted
All checks passed!
Success: no issues found in 1 source file
[assistant] Full suite passes (1101 tests), and ruff and mypy are clean. Last, a typing check that the overloads resolve `Node` vs `dict[str, Node]` as intended.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; mkdir -p /tmp/lineage_typing && cat > /tmp/lineage_typing/check_overloads.py <<'EOF'\nfrom sqlglot.lineage import Node, lineage\n\nsingle = lineage(\"a\", \"SELECT a FROM x\")\nreveal_type(single)\nmany = lineage(None, \"SELECT a FROM x\")\nreveal_type(many)\nEOF\n$PY/mypy /tmp/lineage_typing/check_overloads.py 2>&1 | tail -4; rm -rf /tmp/lineage_typing", "description": "Type-check overload resolution with a scratch file"}
[tool_result] /tmp/lineage_typing/check_overloads.py:4: note: Revealed type is "sqlglot.lineage.Node"
/tmp/lineage_typing/check_overloads.py:6: note: Revealed type is "dict[str, sqlglot.lineage.Node]"
Success: no issues found in 1 source file
[assistant] Both parts are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1101 tests), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`** returns `dict[str, Node]` keyed by each top-level output name. `column` stays a required argument, so callers pass `None` explicitly. Typing overloads make `lineage("a", ...)` resolve to `Node` and `lineage(None, ...)` to `dict[str, Node]`, which I confirmed with mypy.
- **`on_node`** is an optional callback on `lineage()` and `to_node()`. It fires once for every `Node` the walk creates, including leav
…[153 chars elided]…
 last field, so existing positional construction still works.

Choices you may want to redirect:
- For `column=None`, all columns share one memo cache. Shared upstream nodes are reused and `on_node` fires once per node across the whole result.
- With an unexpanded `*` and no schema, the dict key is `"*"`. Duplicate output names collapse into one dict entry.
- I threaded `on_node` through `to_node()` as an explicit keyword before `_cache`, following the pattern `trim_selects` already uses.

When you commit, the repo's CONTRIBUTING rules ask for the model name in the commit message and PR title.
