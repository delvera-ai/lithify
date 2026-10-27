# trajectory base-1

final message:
Both features are in `sqlglot/lineage.py`, with four new tests in `tests/test_lineage.py`. The full suite passed after the last edit: `SUMMARY: 1100 passed, 17880 subtests passed in 64.73s`, `EXIT: 0`. I did not commit.

**1. `column=None` returns a dict.** `lineage(None, sql, ...)` returns `{name: Node}` for every top-level output column. Single-column calls still return a `Node`. Typing overloads pick the return type: `mypy` resolves `lineage("a", ...)` to `Node` and `lineage(None, ...)` to `dict[str, Node]`.
- All columns share one node cache, so a node reachable from two outputs is one object.
- `column` has no default in any signature, so callers pass `column=None` explicitly. A default would have forced a fake default on `sql`.

**2. `on_node` callback and `Node.payload`.**
- `on_node` is called once for every node created during the walk, including leaf nodes and the set-operation node. Cache hits are not re-reported.
- Each call happens after that node's downstream nodes are populated. A test checks this.
- `Node.payload` is a `dict` field with a default factory. The library never reads or writes it.

**Choices you may want to redirect:**
- A non-`SELECT` input on the single-column path now raises "sql must be SELECT" instead of "Cannot find column". I changed it so both paths share one check.
- A query with duplicate output names, such as `SELECT a, a`, produces one dict key. The lone entry is the same lineage the single-column form returns.
- A `SELECT *` with no schema gives a `'*'` key, matching what the single-column form already accepts.
- `payload` is part of the dataclass's `eq` and `repr`. This is harmless, but say if you want it excluded.

**Verification:**
- `tests/test_lineage.py`: 35 passed.
- `ruff check` and `ruff format --check`: clean.
- `mypy sqlglot/lineage.py`: clean.
- A probe confirmed `on_node` fires exactly once for each node that `walk()` reaches, for a CTE + join query and for `UNION ALL`.

## events
[tool_use Bash] {"command": "git status --short && cat sqlglot/lineage.py && ls .lithify/harness 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -50", "description": "Show lineage module and harness files"}
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
…[16488 chars elided]…
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
guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "cat .lithify/harness/memory.md; echo ---; cat .lithify/harness/tool_guidance.md | head -60; echo ---; grep -rn \"to_node\\|lineage(\" --include='*.py' . | grep -v \"^./tests/\" | head -30; echo ---; grep -rln \"lineage\" tests | head; ls tests | grep -i lineage", "description": "Read harness memory, tool guidance, and find lineage usages"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[2703 chars elided]…
lineage(
tests/test_lineage.py:267:        node = lineage(
tests/test_lineage.py:274:        node = lineage(
tests/test_lineage.py:294:        node = lineage(
tests/test_lineage.py:334:        node = lineage(
tests/test_lineage.py:345:        node = lineage(
tests/test_lineage.py:355:        node = lineage(
tests/test_lineage.py:369:        node = lineage(
tests/test_lineage.py:405:        node = lineage(
tests/test_lineage.py:415:        node = lineage(
---
tests/test_lineage.py
test_lineage.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; sed -n 1,16p tests/test_lineage.py; sed -n 40,70p tests/test_lineage.py", "description": "Check python env and run baseline lineage tests"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
...............................                                          [100%]
31 passed in 0.28s
from __future__ import annotations

import unittest

import sqlglot
from sqlglot.lineage import lineage
from sqlglo
…[611 chars elided]…
      node = lineage("a", ast)
        self.assertEqual(ast.sql(), sql)

        # test that sources are not modified
        ast = sqlglot.parse_one(sql)

        source_sql = "SELECT a FROM y"
        source = sqlglot.parse_one(source_sql)

        node = lineage("a", ast, sources={"x": source})

        self.assertEqual(source.sql(), source_sql)

    def test_lineage_sql_with_cte(self) -> None:
        node = lineage(
            "a",
            "WITH z AS (SELECT a FROM y) SELECT a FROM z",
[tool_use Bash] {"command": "grep -rn \"must be SELECT\\|Cannot find column\" tests sqlglot | head; grep -n \"def selects\\|def named_selects\" -A6 sqlglot/expressions/query.py | head -60", "description": "Check error message usages and select accessors"}
[tool_result] sqlglot/lineage.py:130:        raise SqlglotError("Cannot build lineage, sql must be SELECT")
sqlglot/lineage.py:136:        raise SqlglotError(f"Cannot find column '{column}' in query.")
sqlglot/lineage.py:166:                f"Cannot find column's source with index {column} in query: {selectable.sql(dialect=dialect)}"
81:    def selects(self) -> list[Expr]:
82-        raise NotImplementedError("Subclasses must implement selects")
83-
84-    @property
85:    def named_selects(self) -> list[str]
…[1020 chars elided]…
ance(expr, SetOperation):
1047-            expr = expr.this.unnest()
1048-        return _named_selects(expr)
1049-
1050-    @property
--
1055:    def selects(self) -> list[Expr]:
1056-        expr: Expr = self
1057-        while isinstance(expr, SetOperation):
1058-            expr = expr.this.unnest()
1059-        return getattr(expr, "selects", [])
1060-
1061-    @property
--
1642:    def named_selects(self) -> list[str]:
1643-        selects = []
1644-
1645-        for e in self.expressions:
[assistant] Baseline is green (31 passing). Now the edits: imports and `Node` first, then `lineage()` with overloads, then `to_node`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence\n    from sqlglot._typing import GraphHTMLArgs\n    from typing_extensions import Unpack\n\nlogger = logging.getLogger(\"sqlglot\")\n\n\n@dataclass(frozen=Tru
…[317 chars elided]…
 import GraphHTMLArgs\n    from typing_extensions import Unpack\n\nlogger = logging.getLogger(\"sqlglot\")\n\n\n@dataclass(frozen=True)\nclass Node:\n    name: str\n    expression: exp.Expr\n    source: exp.Expr\n    downstream: list[Node] = field(default_factory=list)\n    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[3037 chars elided]…
args: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each top-level output column name to its lineage node\n        when `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name\n\n    if sources:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Giving `column` a default would force a fake default on `sql`, so I'll make `column` a required parameter in every signature. Passing `column=None` explicitly is what the spec describes anyway.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "@t.overload\ndef lineage(\n    column: None = None,\n    sql: str | exp.Expr = \"\",", "new_string": "@t.overload\ndef lineage(\n    column: None,\n    sql: str | exp.Expr,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column | None = None,\n    sql: str | exp.Expr = \"\",", "new_string": "def lineage(\n    column: str | exp.Column | None,\n    sql: str | exp.Expr,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the tail of `lineage()` (the selection and dispatch logic).
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[1353 chars elided]…
ode, _cache={})\n\n\ndef to_node(\n    column: str | int,\n    scope: Scope,\n    dialect: DialectType,\n    scope_name: str | None = None,\n    upstream: Node | None = None,\n    source_name: str | None = None,\n    reference_node_name: str | None = None,\n    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the `to_node` body: thread `on_node` through the recursive calls and fire it at each node-creation site.
[tool_use Bash] {"command": "grep -n \"_cache=_cache\\|Node(\\|upstream.downstream.append\\|node.downstream.append\\|return \\|created_setop\" sqlglot/lineage.py", "description": "Locate to_node call sites and node creations"}
[tool_result] 75:        return GraphHTML(nodes, edges, **opts)
177:        return {
192:    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})
212:            upstream.downstream.append(cached_node)
213:        return cached_node
240:                _cache=_cache,
247:            return result
250:        created_setop = upstream is None
251:        upstream = upstream or Node(name=name, source=scope.expression, expression=select)
278:                _cache=_cache,

…[191 chars elided]…
       node.downstream.append(
331:                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)
397:                _cache=_cache,
426:                        _cache=_cache,
430:                    node.downstream.append(
431:                        Node(
443:            node.downstream.append(
444:                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
450:    return node
513:        return f"""<div>
532:        return self.__str__()
[tool_use Bash] {"command": "perl -0pi -e 's/^(\\s*)_cache=_cache,/$1on_node=on_node,\\n$1_cache=_cache,/mg' sqlglot/lineage.py && grep -n \"on_node=on_node\" sqlglot/lineage.py", "description": "Pass on_node through recursive to_node calls"}
[tool_result] 183:                on_node=on_node,
192:    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})
240:                on_node=on_node,
279:                on_node=on_node,
325:                on_node=on_node,
400:                on_node=on_node,
430:                        on_node=on_node,
[assistant] The file-changed notice is from my own perl edit. I'll read the to_node body before making the remaining edits.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 248, "limit": 40}
[tool_result] 248	            return result
249	    if isinstance(scope.expression, exp.SetOperation):
250	        name = type(scope.expression).__name__.upper()
251	        created_setop = upstream is None
252	        upstream = upstream or Node(name=name, source=scope.expression, expression=select)
253	
254	        index = (
255	            column
256	            if isinstance(column, int)
257	            else next(
258	                (
259	                    i
260	                    for i, select in enu
…[531 chars elided]…
ect=dialect,
275	                upstream=upstream,
276	                source_name=source_name,
277	                reference_node_name=reference_node_name,
278	                trim_selects=trim_selects,
279	                on_node=on_node,
280	                _cache=_cache,
281	            )
282	
283	        if _cache is not None and created_setop:
284	            _cache[cache_key] = upstream
285	        return upstream
286	
287	    if trim_selects and isinstance(scope.expression, exp.Select):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 330, "limit": 135}
[tool_result] 330	    if isinstance(select, exp.Star):
331	        for src in scope.sources.values():
332	            src_expr = src.expression if isinstance(src, Scope) else src
333	            node.downstream.append(
334	                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)
335	            )
336	
337	    # Find all columns that went into creating this one to list their lineage nodes.
338	    source_columns = set(find_all_in_scope(select, exp.Column))
339	
340	    # If t
…[5553 chars elided]…
sources` map.
447	            col_expr = col_source or exp.Placeholder()
448	            node.downstream.append(
449	                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
450	            )
451	
452	    if _cache is not None:
453	        _cache[cache_key] = node
454	
455	    return node
456	
457	
458	class GraphHTML:
459	    """Node to HTML generator using vis.js.
460	
461	    https://visjs.github.io/vis-network/docs/network/
462	    """
463	
464	    def __init__(
[assistant] I have the full picture. Now the node-creation sites: the set-operation node, the star-source leaves, the pivot and fallthrough leaves, and the main node.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream", "new_string": "        if created_setop and on_node:\n            on_node(upstream)\n        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            node.downstream.append(\n                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            )", "new_string": "            leaf = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    col_expr = col_source or exp.Placeholder()\n                    node.downstream.append(\n                        Node(\n                            name=downstream_column.sql(comments=False),\n     
…[157 chars elided]…
                    col_expr = col_source or exp.Placeholder()\n                    leaf = Node(\n                        name=downstream_column.sql(comments=False),\n                        source=col_expr,\n                        expression=col_expr,\n                    )\n                    node.downstream.append(leaf)\n                    if on_node:\n                        on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[45 chars elided]…
   return node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    if on_node:\n        on_node(node)\n    return node"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] All edits are in. Before writing tests, I'll probe the behaviour directly: the dict form, the callback coverage against `walk()`, and set operations.
[tool_use Bash] {"command": "cat > /private/tmp/claude-501/probe_lineage.py <<'EOF'\nimport sqlglot\nfrom sqlglot.lineage import lineage\n\nschema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}, \"y\": {\"a\": \"int\"}}\nsql = \"WITH z AS (SELECT a, b FROM x) SELECT z.a AS a, z.b + 1 AS c FROM z JOIN y ON z.a = y.a\"\nseen = []\nd = lineage(None, sql, schema=schema, on_node=seen.append)\nprint(type(d), list(d))\nids 
…[800 chars elided]…
a=schema)))\nprint(list(lineage(None, s)))\nEOF\n<work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '.'); exec(open('/private/tmp/claude-501/probe_lineage.py').read())\" 2>&1 | tail -30", "description": "Probe dict form, callback coverage and union behaviour"}
[tool_result] <class 'dict'> ['a', 'c']
calls 6 unique 6
walked 6 covered True extra_called 0
single c WITH z AS (SELECT x.a AS a, x.b AS b FROM x AS x) SELECT z.b + 1 AS c FROM z AS z JOIN y AS y ON z.a = y.a
0
['a', 'b'] 10 True
['0', '0', '1', '1', 'UNION', 'UNION', 'x.a', 'x.a', 'x.b', 'x.b']
['a', 'b']
['*']
[assistant] The probe matches expectations: 6 nodes built and 6 callbacks, with no extras and no misses against `walk()`. Union gives 10 and 10. The payload check at the end was a bad probe (column `c` doesn't reach `a`), so I'll cover payloads properly in the tests. Next I'll add tests, starting with the end of the existing test file.
[tool_use Bash] {"command": "wc -l tests/test_lineage.py && tail -40 tests/test_lineage.py && grep -n \"    def test_\" tests/test_lineage.py | tail -5", "description": "Show end of lineage test file"}
[tool_result]      864 tests/test_lineage.py
        With N=12 that's 4096 expansions.
        """
        n_levels = 12
        ctes = ["cte_0 AS (SELECT a FROM base_table)"]
        for k in range(1, n_levels):
            prev = f"cte_{k - 1}"
            ctes.append(
                f"cte_{k} AS (SELECT t1.a + t2.a AS a FROM {prev} t1 JOIN {prev} t2 ON t1.a = t2.a)"
            )
        sql = "WITH " + ",\n     ".join(ctes) + f"\nSELECT a FROM cte_{n_levels - 1}"

        node = lineage("a", sql, schema=
…[902 chars elided]…
a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
688:    def test_table_udtf_snowflake(self) -> None:
733:    def test_pivot_with_subquery(self) -> None:
770:    def test_copy_flag(self) -> None:
820:    def test_lineage_shared_cte_performance(self) -> None:
857:    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        downstream_names = sorted(d.name for d in node.downstream)\n        self.assertEqual(downstream_names, [\"s1.a\", \"s2.a\"])", "new_string": "        downstream_names = sorted(d.name for d in node.downstream
…[2527 chars elided]…
Placeholder(), expression=exp.Placeholder()).payload, {})\n        for root in nodes.values():\n            for node in root.walk():\n                self.assertIn(\"table\", node.payload)\n\n        for root in nodes.values():\n            for node in root.walk():\n                node.payload[\"visited\"] = True\n        self.assertTrue(all(n.payload[\"visited\"] for n in nodes[\"a\"].walk()))"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[assistant] I left a meaningless assertion in the payload test and need to add the imports. Fixing both now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "        nodes = lineage(None, sql, schema=schema, on_node=tag)\n\n        self.assertEqual(Node(name=\"x\", source=exp.Placeholder(), expression=exp.Placeholder()).payload, {})\n        for root in nodes.values():\n
…[198 chars elided]…
d[\"visited\"] = True\n        self.assertTrue(all(n.payload[\"visited\"] for n in nodes[\"a\"].walk()))", "new_string": "        nodes = lineage(None, sql, schema=schema, on_node=tag)\n\n        for node in nodes[\"a\"].walk():\n            self.assertEqual(node.payload[\"table\"], node.expression.sql())\n        self.assertEqual(nodes[\"a\"].payload, {\"table\": nodes[\"a\"].expression.sql()})"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py", "old_string": "import sqlglot\nfrom sqlglot.lineage import lineage\nfrom sqlglot.schema import MappingSchema", "new_string": "import sqlglot\nfrom sqlglot.lineage import Node, lineage\nfrom sqlglot.schema import MappingSchema"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-204015-lineage-extend-sqlglot-lineage-l/base-1/tests/test_lineage.py has been updated successfully.
[assistant] Now the lineage test file, then ruff and mypy on the module.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -15", "description": "Run lineage tests, ruff, and mypy"}
[tool_result] ...................................                                      [100%]
35 passed in 0.09s
All checks passed!
2 files already formatted
Success: no issues found in 1 source file
[assistant] Lineage tests pass (35, including the 4 new ones), and ruff and mypy are clean. Next I'll confirm the overloads resolve correctly for type checkers, then run the full suite.
[tool_use Bash] {"command": "mkdir -p /private/tmp/claude-501/typecheck && cat > /private/tmp/claude-501/typecheck/overload_check.py <<'EOF'\nfrom sqlglot.lineage import Node, lineage\n\none: Node = lineage(\"a\", \"SELECT a FROM x\")\nmany: dict[str, Node] = lineage(None, \"SELECT a FROM x\", on_node=lambda n: None)\nbad: Node = lineage(None, \"SELECT a FROM x\")\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m mypy --python-executable $PY /private/tmp/claude-501/typecheck/overload_check.py 2>&1 | tail -6", "description": "Type-check overload resolution with a scratch file"}
[tool_result] /private/tmp/claude-501/typecheck/overload_check.py:5: error: Incompatible types in assignment (expression has type "dict[str, Node]", variable has type "Node")  [assignment]
Found 1 error in 1 file (checked 1 source file)
[assistant] The overloads resolve correctly: the only error is the deliberately wrong line 5. Now the full suite in the foreground, as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  22891       00:04 <work>/env-sqlglot/b
  34207 03-01:11:11 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-78cdc8b5dd.log
ELAPSED: 65s
SUMMARY: 1100 passed, 17880 subtests passed in 64.73s (0:01:04)
EXIT: 0
[assistant] Full suite is green after my last edit. Last, a check of the change set and cleanup of my scratch files.
[tool_use Bash] {"command": "rm -rf /private/tmp/claude-501/probe_lineage.py /private/tmp/claude-501/typecheck && git status --short && git diff --stat", "description": "Confirm changed files and clean up scratch files"}
[tool_result]  M sqlglot/lineage.py
 M tests/test_lineage.py
 sqlglot/lineage.py    | 109 ++++++++++++++++++++++++++++++++++++++++----------
 tests/test_lineage.py |  63 ++++++++++++++++++++++++++++-
 2 files changed, 150 insertions(+), 22 deletions(-)
[assistant] Both features are in `sqlglot/lineage.py`, with four new tests in `tests/test_lineage.py`. The full suite passed after the last edit: `SUMMARY: 1100 passed, 17880 subtests passed in 64.73s`, `EXIT: 0`. I did not commit.

**1. `column=None` returns a dict.** `lineage(None, sql, ...)` returns `{name: Node}` for every top-level output column. Single-column calls still return a `Node`. Typing overloads pick the return type: `mypy` resolves `lineage("a", ...)` to `Node` and `lineage(None, ...)` to `dict[str, Node]`.
- All columns share one node cache, so a node reachable from two outputs is one obj
…[756 chars elided]…
ames, such as `SELECT a, a`, produces one dict key. The lone entry is the same lineage the single-column form returns.
- A `SELECT *` with no schema gives a `'*'` key, matching what the single-column form already accepts.
- `payload` is part of the dataclass's `eq` and `repr`. This is harmless, but say if you want it excluded.

**Verification:**
- `tests/test_lineage.py`: 35 passed.
- `ruff check` and `ruff format --check`: clean.
- `mypy sqlglot/lineage.py`: clean.
- A probe confirmed `on_node` fires exactly once for each node that `walk()` reaches, for a CTE + join query and for `UNION ALL`.
