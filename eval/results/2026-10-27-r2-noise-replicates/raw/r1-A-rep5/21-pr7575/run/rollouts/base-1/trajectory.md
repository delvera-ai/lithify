# trajectory base-1

final message:
Both parts are implemented in `sqlglot/lineage.py`, with three new tests in `tests/test_lineage.py`. The full suite passes (1099 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

- **`column=None`**: `lineage(None, sql, ...)` returns a dict from each top-level output column name to its `Node`. Typing overloads make `str | exp.Column` return `Node` and `None` return `dict[str, Node]`. All columns share one cache, so a node reused by several outputs is built and reported once.
- **`on_node`**: a keyword argument called for every `Node` created during the walk. It fires after the node's downstream is populated, so children are always reported before their parent. That covers leaf nodes (tables, placeholders, star sources) and the set-operation root that `lineage` creates itself.
- **`Node.payload`**: a `dict` field defaulting to a fresh empty dict per node.

Choices I made that you may want to change:
- **`payload` is excluded from equality** (`compare=False`), so annotating a graph doesn't change how `Node`s compare.
- **Duplicate output names collapse to one key.** For `SELECT a, a`, the dict has a single `"a"` entry that resolves to the first match. This matches how the single-column lookup already behaves.
- **`on_node` is a keyword-only addition after `copy`.** Existing positional calls are unaffected.

## events
[assistant] I'll start by reading the current lineage implementation and its tests.
[tool_use Bash] {"command": "cat sqlglot/lineage.py && git status --short && ls tests | grep -i lineage", "description": "Read lineage module and check worktree state"}
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
…[16438 chars elided]…
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
test_lineage.py
[assistant] The change touches `lineage()`, the recursive `to_node()` walk, and `Node`. Next I'll check the callers of `to_node`, the existing tests, and which `sqlglot` the project's Python actually imports.
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage(\" --include=*.py . | grep -v \"^./tests/test_lineage.py\" | head -40; echo ---; grep -n \"def test\\|Node(\" tests/test_lineage.py | head -80; echo ---; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys; print(sqlglot.__file__, sys.version)\"; grep -rn \"@t.overload\\|@overload\" sqlglot | head -5", "description": "Find lineage callers, tests, and verify imported sqlglot path"}
[tool_result] (eval):1: no matches found: --include=*.py
---
17:    def test_lineage(self) -> None:
67:    def test_lineage_sql_with_cte(self) -> None:
98:    def test_lineage_source_with_cte(self) -> None:
128:    def test_lineage_source_with_star(self) -> None:
148:    def test_lineage_join_with_star(self) -> None:
169:    def test_lineage_join_with_qualified_star(self) -> None:
186:    def test_lineage_external_col(self) -> None:
206:    def test_lineage_values(self) -> None:
228:    def test_lineage_cte_n
…[1090 chars elided]…
f) -> None:
820:    def test_lineage_shared_cte_performance(self) -> None:
857:    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
---
~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/__init__.py 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
sqlglot/helper.py:95:@t.overload
sqlglot/helper.py:99:@t.overload
sqlglot/helper.py:379:@t.overload
sqlglot/helper.py:383:@t.overload
sqlglot/helper.py:387:@t.overload
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage(\" sqlglot tests --include=*.py | grep -v \"tests/test_lineage.py\" ; echo ---; sed -n 1,66p tests/test_lineage.py; echo ---; grep -n \"Node\\b\" tests/test_lineage.py | grep -v \"^.*#\" | head -20", "description": "Inspect callers and existing lineage test conventions"}
[tool_result] (eval):1: no matches found: --include=*.py
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
            schema={"x": {"a": "int"}},
            sour
…[966 chars elided]…
       self.assertIn("to", edge)

        # test that sql is not modified
        sql = "SELECT a FROM x"
        ast = sqlglot.parse_one(sql)
        node = lineage("a", ast)
        self.assertEqual(ast.sql(), sql)

        # test that sources are not modified
        ast = sqlglot.parse_one(sql)

        source_sql = "SELECT a FROM y"
        source = sqlglot.parse_one(source_sql)

        node = lineage("a", ast, sources={"x": source})

        self.assertEqual(source.sql(), source_sql)

---
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage import\\|lineage(\" sqlglot tests | grep -v \"tests/test_lineage.py\"; echo ---; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot import exp, parse_one\nfrom sqlglot.optimizer import qualify, build_scope\ne = parse_one('SELECT * FROM x')\nprint(repr([s.alias_or_name for s in e.selects]))\nprint(repr([s.alias_or_name for s in parse_one('SELECT a, a, b FROM x').selects]))\n\"", "description": "Check lineage call sites and star alias naming"}
[tool_result] sqlglot/lineage.py:77:def lineage(
sqlglot/lineage.py:138:    return to_node(column, scope, dialect, trim_selects=trim_selects, _cache={})
sqlglot/lineage.py:141:def to_node(
sqlglot/lineage.py:177:            result = to_node(
sqlglot/lineage.py:215:            to_node(
sqlglot/lineage.py:262:            to_node(
sqlglot/lineage.py:333:            to_node(
sqlglot/lineage.py:362:                    to_node(
---
['*']
['a', 'a', 'b']
[assistant] `to_node` is only called from `lineage.py`, and star selects surface as `"*"`, which `to_node` already matches. Now I'll make the edits, starting with `Node.payload`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n\n    def walk(self) -> Iterator[Node]:", "new_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    # Caller-managed data, e.g. populated from the `on_node` callback of `lineage`\n    payload: dict[str, t.Any] = field(default_factory=dict, compare=False)\n\n    def walk(self) -> Iterator[Node]:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2921 chars elided]…
 nodes.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each top-level output column name to its lineage node\n        if `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the body of `lineage()`: the `column=None` branch that returns the dict, sharing one cache so nodes shared across output columns are built and reported once.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[667 chars elided]…
ct.alias_or_name for select in selectable.selects)\n        }\n\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot find column '{column}' in query.\")\n\n    return to_node(\n        column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={}\n    )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence", "new_string": "    from collections.abc import Callable, Iterator, Mapping, Sequence"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the recursive walk. `on_node` has to be threaded through every `to_node` call, and each newly created `Node` must trigger the callback. I'll start with the signature and the recursive calls.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    trim_selects: bool = True,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key = ", "new_string": "    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key ="}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n            # Skip caching", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n            # Skip caching"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n\n        if _cache is not None and created_setop:\n            _cach
…[38 chars elided]…
n upstream", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n\n        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        if created_setop and on_node:\n            on_node(upstream)\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                upstream=node,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n\n    # if the select is a star add all scope sources as downstreams\n    if isinstance(select,
…[469 chars elided]…
t is a star add all scope sources as downstreams\n    if isinstance(select, exp.Star):\n        for src in scope.sources.values():\n            src_expr = src.expression if isinstance(src, Scope) else src\n            leaf = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n\n        elif pivot and", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n\n        elif pivot and"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:                 reference_node_name=reference_node_name,
                trim_selects=trim_selects,
                _cache=_cache,
            )

        elif pivot and</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                        reference_node_name=reference_node_name,\n                        trim_selects=trim_selects,\n                        _cache=_cache,\n                    )\n                else:\n              
…[607 chars elided]…
                    col_expr = col_source or exp.Placeholder()\n                    leaf = Node(\n                        name=downstream_column.sql(comments=False),\n                        source=col_expr,\n                        expression=col_expr,\n                    )\n                    node.downstream.append(leaf)\n                    if on_node:\n                        on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[47 chars elided]…
 return node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    if on_node:\n        on_node(node)\n\n    return node"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] The CTE/derived-table call failed to match because there's no blank line before `elif`. I'll view that region and fix it.
[tool_use Bash] {"command": "grep -n \"_cache=_cache,\\|on_node\" sqlglot/lineage.py", "description": "List on_node and _cache call sites"}
[tool_result] 30:    # Caller-managed data, e.g. populated from the `on_node` callback of `lineage`
89:    on_node: Callable[[Node], None] | None = None,
104:    on_node: Callable[[Node], None] | None = None,
118:    on_node: Callable[[Node], None] | None = None,
133:        on_node: A callback invoked with every node created during the walk, once its downstream
179:                name, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache=cache
190:        column, scope, dialect, trim_selects=t
…[257 chars elided]…
ated_setop and on_node:
285:            on_node(upstream)
326:                on_node=on_node,
327:                _cache=_cache,
336:            if on_node:
337:                on_node(leaf)
402:                _cache=_cache,
431:                        on_node=on_node,
432:                        _cache=_cache,
442:                    if on_node:
443:                        on_node(leaf)
452:            if on_node:
453:                on_node(leaf)
458:    if on_node:
459:        on_node(node)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 388, "limit": 22}
[tool_result] 388	            elif col_source.scope_type == ScopeType.CTE:
389	                selected_node, _ = scope.selected_sources.get(table, (None, None))
390	                reference_node_name = selected_node.name if selected_node else None
391	
392	            # The table itself came from a more specific scope. Recurse into that one using the unaliased column name.
393	            to_node(
394	                c.name,
395	                scope=col_source,
396	                dialect=dialect,
397	    
…[111 chars elided]…
et(table) or source_name,
400	                reference_node_name=reference_node_name,
401	                trim_selects=trim_selects,
402	                _cache=_cache,
403	            )
404	        elif pivot and pivot.alias_or_name == c.table:
405	            downstream_columns = []
406	
407	            column_name = c.name
408	            if any(column_name == pivot_column.name for pivot_column in pivot_columns):
409	                downstream_columns.extend(pivot_column_mapping[column_name])
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                _cache=_cache,\n            )\n        elif pivot and pivot.alias_or_name == c.table:", "new_string": "                reference_node_name=reference_node_name,\n                trim_selects=trim_selects,\n                on_node=on_node,\n                _cache=_cache,\n            )\n        elif pivot and pivot.alias_or_name == c.table:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[47 chars elided]…
 return node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    if on_node:\n        on_node(node)\n\n    return node"}
[tool_result ERROR] <tool_use_error>String to replace not found in file.
String:             col_expr = col_source or exp.Placeholder()
            node.downstream.append(
                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
            )

    if _cache is not None:
        _cache[cache_key] = node

    return node</tool_use_error>
[assistant] The final-leaf edit already went through in the earlier batch (the failing one was the CTE call). I'll confirm the tail of `to_node` is correct.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 444, "limit": 22}
[tool_result] 444	                        on_node(leaf)
445	        else:
446	            # The source is not a scope and the column is not in any pivot - we've reached the end
447	            # of the line. At this point, if a source is not found it means this column's lineage
448	            # is unknown. This can happen if the definition of a source used in a query is not
449	            # passed into the `sources` map.
450	            col_expr = col_source or exp.Placeholder()
451	            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
452	            node.downstream.append(leaf)
453	            if on_node:
454	                on_node(leaf)
455	
456	    if _cache is not None:
457	        _cache[cache_key] = node
458	
459	    if on_node:
460	        on_node(node)
461	
462	    return node
463	
464	
465	class GraphHTML:
[assistant] `to_node` is now fully threaded. Before writing tests, I'll run the existing lineage suite and a quick probe of the new behaviour.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage, Node\nsql = 'WITH c AS (SELECT a, b FROM x) SELECT a, b + 1 AS d, a AS e FROM c UNION ALL SELECT a, b, a FROM y'\
…[253 chars elided]…
{'a': 'int', 'b': 'int'}, 'y': {'a': 'int', 'b': 'int'}}, on_node=cb)\nwalked = {id(n) for v in r.values() for n in v.walk()}\nprint(len(seen), len({id(n) for n in seen}), walked == {id(n) for n in seen})\nprint(lineage('a', 'SELECT a FROM x', schema={'x': {'a': 'int'}}).payload)\nprint(lineage(None, 'SELECT * FROM x', schema=None))\n\"", "description": "Run lineage tests and probe new behaviour"}
[tool_result] ...............................                                          [100%]
31 passed in 0.12s
<class 'dict'> ['a', 'd', 'e']
{'a': 'UNION', 'd': 'UNION', 'e': 'UNION'}
16 16 True
{}
{'*': Node(name='*', expression=Star(), source=Select(
  expressions=[
    Star()],
  from_=From(
    this=Table(
      this=Identifier(this=x, quoted=False),
      alias=TableAlias(
        this=Identifier(this=x, quoted=False))))), downstream=[Node(name='*', expression=Table(
  this=Identifier(this=x, quoted=False),
  alias=TableAlias(
    this=Identifier(this=x, quoted=False))), source=Table(
  this=Identifier(this=x, quoted=False),
  alias=TableAlias(
    this=Identifier(this=x, quoted=False))), downstream=[], source_name='', reference_node_name='', payload={})], source_name='', reference_node_name='', payload={})}
[assistant] Existing tests pass (31/31). The probe shows the dict form covers all output columns, and `on_node` fires exactly once per node, matching the graph's `walk()`. Next I'll add tests covering the new behaviour, starting with the end of the test file.
[tool_use Bash] {"command": "tail -30 tests/test_lineage.py", "description": "Show end of lineage test file"}
[tool_result]         node = lineage("a", sql, schema={"base_table": {"a": "int"}})

        # Walk the DAG and verify structure.
        all_nodes = list(node.walk())

        # shared references keep node count small (O(N), not O(2^N)).
        self.assertLess(
            len(all_nodes),
            200,
            f"got {len(all_nodes)} nodes -- DAG walk may be broken",
        )

        # walk() should yield each node exactly once.
        all_ids = [id(n) for n in all_nodes]
        self.assertEqual(l
…[161 chars elided]…
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
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        sql = \"WITH c AS (SELECT a, b FROM x) SELECT a, b + 1 AS d FROM c UNION ALL SELECT a, b FROM y\"\n        schema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}, \"y\": {\"a\": \"int\", \"b\": \"int\"}}\n\n        nodes = lineage(None, sql, schema=schema)\n        self.assertEqual(list(nodes),
…[2325 chars elided]…
de.downstream[0].payload, {\"table\": \"x AS x\"})\nEOF\nsed -i 's/^from sqlglot.lineage import lineage$/from sqlglot.lineage import Node, lineage/' tests/test_lineage.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Append new lineage tests and run lineage test file"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/test_lineage.py
": undefined label 'ests/test_lineage.py'
[assistant] The `sed -i` failed because macOS requires an explicit backup argument. The append ran first, so I'll fix the import with the Edit tool instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "from sqlglot.lineage import lineage\n", "new_string": "from sqlglot.lineage import Node, lineage\n"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[tool_use Bash] {"command": "grep -c \"test_lineage_all_columns\\|test_lineage_payload\" tests/test_lineage.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Confirm new tests present and run lineage tests"}
[tool_result] 2
E       4414869712
E       4414878352

tests/test_lineage.py:907: AssertionError
_______________________ TestLineage.test_lineage_payload _______________________

self = <tests.test_lineage.TestLineage testMethod=test_lineage_payload>

    def test_lineage_payload(self) -> None:
        node = lineage("a", "SELECT a FROM x", schema={"x": {"a": "int"}})
        self.assertEqual(node.payload, {})
        self.assertEqual(node.downstream[0].payload, {})
        self.assertIsNot(node.payload, node
…[244 chars elided]…
e.payload, {"table": "a"})
E       AssertionError: {'table': 'x.a AS a'} != {'table': 'a'}
E       - {'table': 'x.a AS a'}
E       ?            -------
E       
E       + {'table': 'a'}

tests/test_lineage.py:922: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_lineage_on_node - AssertionEr...
FAILED tests/test_lineage.py::TestLineage::test_lineage_payload - AssertionEr...
2 failed, 32 passed in 0.14s
[assistant] Two failures, both from mistakes in my new tests rather than the implementation. The payload test expected the wrong expression text. The `on_node` test compared ids from one graph build against a second, separate build, so the ids can never match. Before fixing them, the "modified on disk" note needs checking, so I'll look at the file's git diff.
[tool_use Bash] {"command": "git status --short && git diff --stat && git diff tests/test_lineage.py | head -20 && grep -n \"def test_\" tests/test_lineage.py | tail -8", "description": "Check git status and recent test file changes"}
[tool_result]  M sqlglot/lineage.py
 M tests/test_lineage.py
 sqlglot/lineage.py    | 107 ++++++++++++++++++++++++++++++++++++++++----------
 tests/test_lineage.py |  61 +++++++++++++++++++++++++++-
 2 files changed, 147 insertions(+), 21 deletions(-)
diff --git a/tests/test_lineage.py b/tests/test_lineage.py
index 13577bb2f..a6455ff7d 100644
--- a/tests/test_lineage.py
+++ b/tests/test_lineage.py
@@ -3,7 +3,7 @@ from __future__ import annotations
 import unittest
 
 import sqlglot
-from sqlglot.lineage impor
…[383 chars elided]…
 a, b FROM x) SELECT a, b + 1 AS d FROM c UNION ALL SELECT a, b FROM y"
688:    def test_table_udtf_snowflake(self) -> None:
733:    def test_pivot_with_subquery(self) -> None:
770:    def test_copy_flag(self) -> None:
820:    def test_lineage_shared_cte_performance(self) -> None:
857:    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
866:    def test_lineage_all_columns(self) -> None:
884:    def test_lineage_on_node(self) -> None:
912:    def test_lineage_payload(self) -> None:
[assistant] The diff holds only my changes, so the "modified on disk" note was just the sed attempt and the edit, not a concurrent writer. Now I'll fix both tests: compare against a single graph build, and use the actual expression text.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        reported = []\n        lineage(\"a\", sql, schema=schema, on_node=on_node)\n        self.assertEqual(\n            {id(n) for n in reported},\n            {id(n) for n in lineage(\"a\", sql, schema=schema).walk()},\n        )", "new_string": "        reported = []\n        node = lineage(\"a\", sql, schema=schema, on_node=on_node)\n        self.assertEqual(\n            {id(n) for n in reported},\n            {id(n) for n in node.walk()},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        def on_node(n: Node) -> None:\n            n.payload[\"table\"] = n.expression.sql()\n\n        node = lineage(\"a\", \"SELECT a FROM x\", schema={\"x\": {\"a\": \"int\"}}, on_node=on_node)\n        self.ass
…[78 chars elided]…
stream[0].payload, {\"table\": \"x AS x\"})", "new_string": "        def on_node(n: Node) -> None:\n            n.payload[\"sql\"] = n.expression.sql()\n\n        node = lineage(\"a\", \"SELECT a FROM x\", schema={\"x\": {\"a\": \"int\"}}, on_node=on_node)\n        self.assertEqual(node.payload, {\"sql\": \"x.a AS a\"})\n        self.assertEqual(node.downstream[0].payload, {\"sql\": \"x AS x\"})"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Run lineage test file after fixes"}
[tool_result] ..................................                                       [100%]
34 passed in 0.11s
[assistant] All 34 lineage tests pass. Next I'll run the project's full test suite and the style and type checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -4; echo \"--- ruff\"; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; echo \"--- mypy\"; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -5", "description": "Run full test suite, ruff, and mypy on changed files"}
[tool_result] ............................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1099 passed, 17880 subtests passed in 56.89s
--- ruff
Would reformat: sqlglot/lineage.py
Would reformat: tests/test_lineage.py
2 files would be reformatted
All checks passed!
--- mypy
Success: no issues found in 1 source file
[assistant] The full suite passes (1099) and mypy is clean. Ruff wants to reformat both files, so I'll look at what it would change before applying it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff sqlglot/lineage.py tests/test_lineage.py 2>&1 | head -60", "description": "Preview ruff formatting changes"}
[tool_result] --- sqlglot/lineage.py
+++ sqlglot/lineage.py
@@ -186,9 +186,7 @@
     ):
         raise SqlglotError(f"Cannot find column '{column}' in query.")
 
-    return to_node(
-        column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={}
-    )
+    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})
 
 
 def to_node(
@@ -203,7 +201,7 @@
     on_node: Callable[[Node], None] | None = None,
     _cache: dict[tuple, Node] | None = None,
 )
…[371 chars elided]…
me for n in lineage(column, sql, schema=schema).walk()),
             )
 
-        self.assertEqual(lineage(None, "SELECT a, a FROM x", schema={"x": {"a": "int"}}).keys(), {"a"})
+        self.assertEqual(
+            lineage(None, "SELECT a, a FROM x", schema={"x": {"a": "int"}}).keys(), {"a"}
+        )
 
     def test_lineage_on_node(self) -> None:
         sql = "WITH c AS (SELECT a, b FROM x) SELECT a, b + 1 AS d, a AS e FROM c UNION ALL SELECT a, b, a FROM y"

2 files would be reformatted
[assistant] The `cache_key =(column` diff is a real defect I introduced: my earlier edit lost the trailing space in `cache_key = `. The other two hunks are formatting. I'll fix the spacing by hand, then apply ruff format, which only touches those lines.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    cache_key =(column, id(scope), scope_name, source_name, reference_node_name)", "new_string": "    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-101324-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/lineage.py tests/test_lineage.py && $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py && git diff sqlglot/lineage.py | head -150", "description": "Apply ruff format and review lineage diff"}
[tool_result] 2 files reformatted
All checks passed!
diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 00b1c1fbd..c74949db7 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -12,7 +12,7 @@ from sqlglot.optimizer.scope import ScopeType
 
 if t.TYPE_CHECKING:
     from sqlglot.dialects.dialect import DialectType
-    from collections.abc import Iterator, Mapping, Sequence
+    from collections.abc import Callable, Iterator, Mapping, Sequence
     from sqlglot._typing import GraphHTMLArgs
    
…[4821 chars elided]…
# Skip caching a passed-in upstream returned by an inner SetOp:
@@ -220,11 +273,14 @@ def to_node(
                 source_name=source_name,
                 reference_node_name=reference_node_name,
                 trim_selects=trim_selects,
+                on_node=on_node,
                 _cache=_cache,
             )
 
         if _cache is not None and created_setop:
[This command modified 2 files you've previously read: sqlglot/lineage.py, tests/test_lineage.py. Call Read before editing.]
[assistant] Ruff only reformatted my own lines; the "changed on disk" notes are from that formatter run. I'll re-run the checks on the final state of both files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git diff sqlglot/lineage.py | tail -75; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2", "description": "Review rest of diff and rerun checks"}
[tool_result]                  dialect=dialect,
                 upstream=node,
                 trim_selects=trim_selects,
+                on_node=on_node,
                 _cache=_cache,
             )
 
@@ -272,9 +329,10 @@ def to_node(
     if isinstance(select, exp.Star):
         for src in scope.sources.values():
             src_expr = src.expression if isinstance(src, Scope) else src
-            node.downstream.append(
-                Node(name=select.sql(comments=False), source=src_expr, expressi
…[2323 chars elided]…
name=c.sql(comments=False), source=col_expr, expression=col_expr)
+            node.downstream.append(leaf)
+            if on_node:
+                on_node(leaf)
 
     if _cache is not None:
         _cache[cache_key] = node
 
+    if on_node:
+        on_node(node)
+
     return node
 
 
Success: no issues found in 1 source file
2 files already formatted
..........................................................                              [100%]
1099 passed, 17880 subtests passed in 51.11s
[assistant] Both parts are implemented in `sqlglot/lineage.py`, with three new tests in `tests/test_lineage.py`. The full suite passes (1099 tests), and ruff and mypy are clean on the changed files. I haven't committed anything.

- **`column=None`**: `lineage(None, sql, ...)` returns a dict from each top-level output column name to its `Node`. Typing overloads make `str | exp.Column` return `Node` and `None` return `dict[str, Node]`. All columns share one cache, so a node reused by several outputs is built and reported once.
- **`on_node`**: a keyword argument called for every `Node` created during the wa
…[164 chars elided]…
es) and the set-operation root that `lineage` creates itself.
- **`Node.payload`**: a `dict` field defaulting to a fresh empty dict per node.

Choices I made that you may want to change:
- **`payload` is excluded from equality** (`compare=False`), so annotating a graph doesn't change how `Node`s compare.
- **Duplicate output names collapse to one key.** For `SELECT a, a`, the dict has a single `"a"` entry that resolves to the first match. This matches how the single-column lookup already behaves.
- **`on_node` is a keyword-only addition after `copy`.** Existing positional calls are unaffected.
