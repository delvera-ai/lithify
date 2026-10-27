# trajectory base-1

final message:
Both requested extensions are in `sqlglot/lineage.py`, and the full suite passes (1099 passed). I did not commit.

- **`column=None` returns a dict.** It maps each top-level output name (`named_selects`) to its `Node`, and the walk shares one cache so common upstream nodes are built once. Typing overloads make `str | exp.Column` return `Node` and `None` return `dict[str, Node]`. `column` stays a required positional argument, so callers pass `None` explicitly.
- **`on_node` callback.** It fires for every `Node` the walk creates, including leaves, union placeholders and star/pivot leaves. It is called after the node's downstream is populated, so the root is always last. Cache hits create no new node and so trigger no callback.
- **`Node.payload`.** A `dict[str, Any]` field defaulting to empty. Cached nodes are the same objects, so a payload set in the callback is visible in the returned graph.

Choices I made that you may want to change:
- Column-name normalization moved to after the `None` branch, since `None` can't be normalized. Behaviour is unchanged.
- Dict-form keys come from `named_selects`. With `SELECT *` and no schema, the key is whatever `named_selects` yields for the star.

Tests added in `tests/test_lineage.py` cover the dict form, the union case, and callback ordering with payloads. The `test_lineage` cases and the rest of the module pass, and `ruff format`, `ruff check` and `mypy` are clean on the changed files.

## events
[tool_use Bash] {"command": "cat sqlglot/lineage.py; git log --oneline -1; ls tests | grep -i lineage", "description": "Read lineage module and locate lineage tests"}
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
…[16468 chars elided]…
xt/javascript">
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
23303e7aa lithify: probe base
test_lineage.py
[tool_use Bash] {"command": "grep -rn \"lineage\\|Node(\" --include=*.py sqlglot tests | grep -v \"^sqlglot/lineage.py\" | grep -i \"lineage\\|lineage.Node\\|import.*Node\" | head -40; grep -rn \"@overload\" sqlglot | head -5; grep -n \"requires-python\" pyproject.toml; sed -n 1,40p tests/test_lineage.py", "description": "Find lineage usages, overload conventions, and test header"}
[tool_result] (eval):1: no matches found: --include=*.py
9:requires-python = ">= 3.9"
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
            schema={"x": {"a": 
…[241 chars elided]…
ource: y */) AS z /* source: z */",
        )
        self.assertEqual(node.source_name, "")

        downstream = node.downstream[0]
        self.assertEqual(
            downstream.source.sql(),
            "SELECT y.a AS a FROM (SELECT x.a AS a FROM x AS x) AS y /* source: y */",
        )
        self.assertEqual(downstream.source_name, "z")

        downstream = downstream.downstream[0]
        self.assertEqual(
            downstream.source.sql(),
            "SELECT x.a AS a FROM x AS x",
[tool_use Bash] {"command": "grep -rn \"lineage\" sqlglot tests --include=*.py -l; grep -rln \"@t.overload\\|@overload\" sqlglot | head; grep -rn \"Node(\" sqlglot tests --include=*.py | grep -v \"^sqlglot/lineage.py\" | head; grep -n \"def test_\" tests/test_lineage.py | tail -3; tail -5 tests/test_lineage.py", "description": "Search lineage usages and overload conventions"}
[tool_result ERROR] Exit code 1
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rln \"lineage\" sqlglot tests; echo ---; grep -rn \"overload\" sqlglot | head -5; echo ---; grep -rn \"Node(\" sqlglot tests | grep -v \"sqlglot/lineage.py\" | head; echo ---; grep -n \"def test_\" tests/test_lineage.py | tail -3; tail -5 tests/test_lineage.py", "description": "Search lineage usages and overload conventions"}
[tool_result] sqlglot/lineage.py
tests/test_lineage.py
---
sqlglot/__init__.py:113:@t.overload
sqlglot/__init__.py:124:@t.overload
sqlglot/parser.py:4071:    @t.overload
sqlglot/parser.py:4074:    @t.overload
sqlglot/parser.py:7883:    @t.overload
---
---
770:    def test_copy_flag(self) -> None:
820:    def test_lineage_shared_cte_performance(self) -> None:
857:    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
            "WITH shared AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
[tool_use Bash] {"command": "grep -rn \"def named_selects\" -A4 sqlglot/expressions/*.py | head -30; ls <work>/env-sqlglot/bin/python 2>&1; which ruff mypy; grep -n \"^style\\|ruff\\|mypy\" Makefile | head", "description": "Inspect named_selects and available tooling"}
[tool_result] sqlglot/expressions/ddl.py:30:    def named_selects(self) -> list[str]:
sqlglot/expressions/ddl.py-31-        """
sqlglot/expressions/ddl.py-32-        If this statement contains a query (e.g. a CTAS), this returns the output
sqlglot/expressions/ddl.py-33-        names of the query's projections.
sqlglot/expressions/ddl.py-34-        """
sqlglot/expressions/query.py:85:    def named_selects(self) -> list[str]:
sqlglot/expressions/query.py-86-        return _named_selects(self)
sqlglot/expression
…[1106 chars elided]…
-Coding-delvera-foundational-lithify/f0ecd001-19e9-4b3c-8461-34bf1f0fcf2a/scratchpad/hwork/env-sqlglot/bin/python
<work>/env-sqlglot/bin/ruff
<work>/env-sqlglot/bin/mypy
41:# sqlglotc requires Python 3.10+ (sqlglot-mypy 1.20+ dropped 3.9). On 3.9
96:style:
[assistant] Tooling is available and `named_selects` already handles set operations. Starting with the imports and the `Node.payload` field.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence", "new_string": "    from collections.abc import Callable, Iterator, Mapping, Sequence"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n\n    def walk", "new_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n\n    def walk"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the `lineage()` overloads, the `None` branch, and the `on_node` parameter.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2722 chars elided]…
\n        on_node: A callback invoked with every lineage node as it is created, after its downstream nodes are populated.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a mapping of each top-level output column name to its lineage node if column is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n\n    if sources:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[684 chars elided]…
umn = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot find column '{column}' in query.\")\n\n    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now `to_node`: thread `on_node` through the signature and every recursive call, and fire it at each node-creation site.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    trim_selects: bool = True,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key", "new_string": "    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n            # Skip caching", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n            # Skip caching"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        for s in scope.union_scopes:\n            to_node(\n                index,\n                scope=s,\n                dialect=dialect,\n                upstream=upstream,\n                source_name=source_nam
…[482 chars elided]…
  source_name=source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n\n        if created_setop and on_node:\n            on_node(upstream)\n        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        for name in subquery.named_selects:\n            to_node(\n                name,\n                scope=subquery_scope,\n                dialect=dialect,\n                upstream=node,\n                trim_se
…[810 chars elided]…
 all scope sources as downstreams\n    if isinstance(select, exp.Star):\n        for src in scope.sources.values():\n            src_expr = src.expression if isinstance(src, Scope) else src\n            star_node = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(star_node)\n            if on_node:\n                on_node(star_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n        elif pivot and pivot.alias_or_name == c.table:", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n        elif pivot and pivot.alias_or_name == c.table:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    to_node(\n                        downstream_column.name,\n                        scope=col_source,\n                        scope_name=table,\n                        dialect=dialect,\n           
…[1273 chars elided]…
  col_expr = col_source or exp.Placeholder()\n                    pivot_node = Node(\n                        name=downstream_column.sql(comments=False),\n                        source=col_expr,\n                        expression=col_expr,\n                    )\n                    node.downstream.append(pivot_node)\n                    if on_node:\n                        on_node(pivot_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[22 chars elided]…
[cache_key] = node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf_node = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf_node)\n            if on_node:\n                on_node(leaf_node)\n\n    if on_node:\n        on_node(node)\n    if _cache is not None:\n        _cache[cache_key] = node"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                scope_name=table,\n                upstream=node,\n                source_name=source_names.get(table) or source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,", "new_string": "                scope_name=table,\n                upstream=node,\n                source_name=source_names.get(table) or source_name,\n                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:                 scope_name=table,
                upstream=node,
                source_name=source_names.get(table) or source_name,
                reference_node_name=reference_node_name,
                trim_selects=trim_selects,
                _cache=_cache,</tool_use_error>
[assistant] The last edit failed because the `col_source` call site was already updated by an earlier edit. Checking that every recursive call now passes `on_node`.
[tool_use Bash] {"command": "grep -n \"_cache=_cache\\|on_node\" sqlglot/lineage.py && <work>/env-sqlglot/bin/ruff format sqlglot/lineage.py && <work>/env-sqlglot/bin/ruff check sqlglot/lineage.py && <work>/env-sqlglot/bin/mypy sqlglot/lineage.py 2>&1 | tail -5", "description": "Check call sites, then format, lint and type-check lineage"}
[tool_result] 88:    on_node: Callable[[Node], None] | None = None,
103:    on_node: Callable[[Node], None] | None = None,
117:    on_node: Callable[[Node], None] | None = None,
131:        on_node: A callback invoked with every lineage node as it is created, after its downstream nodes are populated.
176:                on_node=on_node,
177:                _cache=_cache,
188:    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})
200:    on_node: Callable[[Node], None
…[315 chars elided]…
          if on_node:
334:                on_node(star_node)
399:                on_node=on_node,
400:                _cache=_cache,
429:                        on_node=on_node,
430:                        _cache=_cache,
440:                    if on_node:
441:                        on_node(pivot_node)
450:            if on_node:
451:                on_node(leaf_node)
453:    if on_node:
454:        on_node(node)
1 file left unchanged
All checks passed!
Success: no issues found in 1 source file
[assistant] Format, lint and mypy are clean. Now a quick behavioural check of the three new paths: dict form, union, and `on_node` ordering with payloads.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/lin_probe.py <<'EOF'\nfrom sqlglot.lineage import lineage, Node\nschema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\nsql = \"SELECT a, b + 1 AS c FROM x\"\nnodes = lineage(None, sql, schema=schema)\nprint({k: v.name for 
…[499 chars elided]…
N SELECT a FROM x\"\nseen = []\nr = lineage(\"a\", u, schema=schema, on_node=lambda n: seen.append(n))\nprint(\"union:\", r.name, len(seen), seen[-1] is r, {id(n) for n in r.walk()} <= {id(n) for n in seen})\nd = lineage(None, u, schema=schema)\nprint(\"union dict:\", list(d))\nEOF\n$PY -I /tmp/lin_probe.py; rm /tmp/lin_probe.py", "description": "Probe new lineage behaviour with a scratch script"}
[tool_result] Traceback (most recent call last):
  File "/tmp/lin_probe.py", line 1, in <module>
    from sqlglot.lineage import lineage, Node
ModuleNotFoundError: No module named 'sqlglot'
[assistant] `-I` ignores `PYTHONPATH`, so I'll rerun with the repo on the path. The probe is my own script, not untrusted input.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; mkdir -p /tmp/linprobe && cat > /tmp/linprobe/probe.py <<'EOF'\nfrom sqlglot.lineage import lineage, Node\nschema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\nsql = \"SELECT a, b + 1 AS c FROM x\"\nnodes = lineage(None, sql, schema
…[519 chars elided]…
N SELECT a FROM x\"\nseen = []\nr = lineage(\"a\", u, schema=schema, on_node=lambda n: seen.append(n))\nprint(\"union:\", r.name, len(seen), seen[-1] is r, {id(n) for n in r.walk()} <= {id(n) for n in seen})\nprint(\"union dict:\", list(lineage(None, u, schema=schema)))\nEOF\nPYTHONPATH=. $PY /tmp/linprobe/probe.py; rm -rf /tmp/linprobe", "description": "Run lineage probe script against the repo"}
[tool_result] {'a': 'a', 'c': 'c'}
<class 'sqlglot.lineage.Node'>
3 ['Table', 'Alias', 'Alias'] {'idx': 2}
all reachable seen: True
root emitted last: True
union: UNION 5 True True
union dict: ['a']
[assistant] All three paths behave as specified: the dict form, the post-order callback with the root last, and union nodes. Adding regression tests to the existing lineage test class.
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        nodes = lineage(\n            None,\n            \"SELECT a, b + 1 AS c FROM x\",\n            schema={\"x\": {\"a\": \"int\", \"b\": \"int\"}},\n        )\n        self.assertEqual(list(nodes), [\"a\", \"c\"])\n        self.assertEqual(nodes[\"a\"].name, \"a\")\n        self.assertEqual(n
…[1078 chars elided]…
,\n        )\n        self.assertEqual(len({id(node) for node in seen}), len(seen))\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Append lineage tests and run lineage test module"}
[tool_result] self = <tests.test_lineage.TestLineage testMethod=test_lineage_all_columns>

    def test_lineage_all_columns(self) -> None:
        nodes = lineage(
            None,
            "SELECT a, b + 1 AS c FROM x",
            schema={"x": {"a": "int", "b": "int"}},
        )
        self.assertEqual(list(nodes), ["a", "c"])
        self.assertEqual(nodes["a"].name, "a")
        self.assertEqual(nodes["c"].name, "c")
>       self.assertEqual(
            [d.name for d in nodes["c"].downstream],
            ["b"],
        )
E       AssertionError: Lists differ: ['x.b'] != ['b']
E       
E       First differing element 0:
E       'x.b'
E       'b'
E       
E       - ['x.b']
E       ?   --
E       
E       + ['b']

tests/test_lineage.py:875: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_lineage_all_columns - Asserti...
1 failed, 33 passed in 0.13s
[assistant] That failure is my expectation, not the code: downstream leaves are qualified (`x.b`), as the existing lineage tests show. Correcting the assertion in my new test.
[tool_use Bash] {"command": "sed -i 's/            \\[\"b\"\\],/            [\"x.b\"],/' tests/test_lineage.py && PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff format --check tests/test_lineage.py sqlglot/lineage.py; $PY -m ruff check tests/test_lineage.py sqlglot/lineage.py; $PY -m mypy sqlglot/lineage.py | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Fix test expectation and run lint, types and full suite"}
[tool_result] sed: 2: "tests/test_lineage.py
": undefined label 'ests/test_lineage.py'
(eval):1: command not found: -m
(eval):1: command not found: -m
(eval):1: command not found: -m
(eval):1: command not found: -m
(eval):1: command not found: -m
[assistant] The `sed -i` call failed on macOS (it needs an explicit backup suffix), so the rest of the chain ran with no interpreter set. Redoing that step with the Edit tool.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "            [d.name for d in nodes[\"c\"].downstream],\n            [\"b\"],", "new_string": "            [d.name for d in nodes[\"c\"].downstream],\n            [\"x.b\"],"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-200221-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff format --check tests/test_lineage.py sqlglot/lineage.py; $PY -m ruff check tests/test_lineage.py sqlglot/lineage.py; $PY -m mypy sqlglot/lineage.py | tail -1; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Run lineage tests, lint, types and full suite"}
[tool_result] ..................................                                       [100%]
34 passed in 0.08s
2 files already formatted
All checks passed!
Success: no issues found in 1 source file
................................. [ 94%]
..........................................................                              [100%]
1099 passed, 17880 subtests passed in 47.83s
[assistant] Both requested extensions are in `sqlglot/lineage.py`, and the full suite passes (1099 passed). I did not commit.

- **`column=None` returns a dict.** It maps each top-level output name (`named_selects`) to its `Node`, and the walk shares one cache so common upstream nodes are built once. Typing overloads make `str | exp.Column` return `Node` and `None` return `dict[str, Node]`. `column` stays a required positional argument, so callers pass `None` explicitly.
- **`on_node` callback.** It fires for every `Node` the walk creates, including leaves, union placeholders and star/pivot leaves. It is 
…[248 chars elided]…
ad set in the callback is visible in the returned graph.

Choices I made that you may want to change:
- Column-name normalization moved to after the `None` branch, since `None` can't be normalized. Behaviour is unchanged.
- Dict-form keys come from `named_selects`. With `SELECT *` and no schema, the key is whatever `named_selects` yields for the star.

Tests added in `tests/test_lineage.py` cover the dict form, the union case, and callback ordering with payloads. The `test_lineage` cases and the rest of the module pass, and `ruff format`, `ruff check` and `mypy` are clean on the changed files.
