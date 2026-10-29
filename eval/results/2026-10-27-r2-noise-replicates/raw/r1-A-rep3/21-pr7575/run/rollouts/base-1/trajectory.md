# trajectory base-1

final message:
Both extensions are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1100 passed), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`**: `lineage(None, sql, ...)` returns a dict from each top-level output column name to its root `Node`. The single-column form still returns a `Node`. Two `@t.overload` signatures make the return type depend on whether `column` is `None`.
- **`on_node`**: a new keyword argument on `lineage()`, threaded through `to_node`. It fires once per `Node` created during the walk, after that node's downstream nodes are complete. That covers the root, intermediate nodes, set-operation nodes, and the leaf placeholder and star-source nodes. Cache hits don't fire it again.
- **`Node.payload`**: a `dict` field defaulting to a fresh empty dict per node. It's the last field, so existing positional construction is unaffected.

Choices I made that you may want to change:
- `column` is still a required positional argument; pass `None` explicitly rather than making it optional.
- For `column=None`, duplicate output names keep the first occurrence, matching the single-column lookup.
- `on_node` is a keyword argument placed before `**kwargs`, so it isn't forwarded to qualify.
- `to_html()` ignores `payload`.

## events
[tool_use Bash] {"command": "cat sqlglot/lineage.py && git status --short && ls tests | grep -i lineage", "description": "Show lineage module and repo status"}
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
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage(\\|Node(\" --include=*.py . | grep -v \"^./tests/fixtures\" | grep -i \"lineage\\|to_node\" | head -40; echo ---; sed -n 1,60p tests/test_lineage.py; echo ---; grep -n \"def test_\\|Cannot\" tests/test_lineage.py | head -60; echo ---; tail -30 tests/test_lineage.py", "description": "Find lineage callers and view existing tests"}
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
…[3665 chars elided]…
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
[tool_use Bash] {"command": "grep -rln \"to_node\\|sqlglot.lineage\\|from sqlglot import lineage\" --exclude-dir=.git . | grep -v fixtures; echo ---; grep -n \"overload\" sqlglot/*.py | head -5; grep -n \"Callable\" sqlglot/*.py | head -5", "description": "Find lineage module references and typing idioms"}
[tool_result] posts/ast_primer.md
posts/onboarding.md
sqlglot/lineage.py
tests/test_lineage.py
---
sqlglot/__init__.py:113:@t.overload
sqlglot/__init__.py:124:@t.overload
sqlglot/jsonpath.py:70:    @t.overload
sqlglot/jsonpath.py:74:    @t.overload
sqlglot/helper.py:95:@t.overload
sqlglot/diff.py:426:    seq_a: Sequence[T], seq_b: Sequence[T], equal: t.Callable[[T, T], bool]
sqlglot/helper.py:20:    def mypyc_attr(*attrs: str, **kwattrs: object) -> t.Callable[[t.Any], t.Any]:  # type: ignore[misc]
sqlglot/helper.py:164:def while_changing(expression: E, func: t.Callable[[E], E]) -> E:
sqlglot/helper.py:260:def name_sequence(prefix: str) -> t.Callable[[], str]:
sqlglot/jsonpath.py:218:JSON_PATH_PART_TRANSFORMS: dict[type[exp.Expr], t.Callable[..., str]] = {
[assistant] I have what I need. Plan: add `Node.payload`, thread an `on_node` callback through `to_node` at every point a `Node` is constructed (firing post-order, once per node), and make `lineage()` overloaded so `column=None` returns a dict sharing one cache.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n\n    def walk(self) -> Iterator[Node]:", "new_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n\n    def walk(self) -> Iterator[Node]:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the public `lineage()` with overloads, the `column=None` path, and the `on_node` parameter.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2904 chars elided]…
been populated.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each output column name to its lineage node when\n        `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[1434 chars elided]…
ode, _cache={})\n\n\ndef to_node(\n    column: str | int,\n    scope: Scope,\n    dialect: DialectType,\n    scope_name: str | None = None,\n    upstream: Node | None = None,\n    source_name: str | None = None,\n    reference_node_name: str | None = None,\n    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, thread `on_node` into every recursive `to_node` call. Each of those call sites ends with `_cache=_cache,`, so I'll add the argument ahead of each one.
[tool_use Bash] {"command": "/usr/bin/python3 - <<'EOF'\nimport re\np = \"sqlglot/lineage.py\"\nsrc = open(p).read()\nnew, n = re.subn(r\"^(\\s+)_cache=_cache,\\n\", lambda m: f\"{m.group(1)}on_node=on_node,\\n{m.group(0)}\", src, flags=re.M)\nprint(\"inserted\", n)\nopen(p, \"w\").write(new)\nEOF\ngrep -n \"on_node=on_node\\|_cache=_cache\" sqlglot/lineage.py", "description": "Thread on_node into recursive to_node calls"}
[tool_result] inserted 5
182:                on_node=on_node,
193:    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})
241:                on_node=on_node,
242:                _cache=_cache,
280:                on_node=on_node,
281:                _cache=_cache,
326:                on_node=on_node,
327:                _cache=_cache,
401:                on_node=on_node,
402:                _cache=_cache,
431:                        on_node=on_node,
432:                        _cache=_cache,
[assistant] The file changed on disk only from my scripted insert, so I'll keep going from its current state. Now the node-creation sites: the set-operation node, the main node, and the leaf nodes.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 296, "limit": 50}
[tool_result] 296	
297	    # Create the node for this step in the lineage chain, and attach it to the previous one.
298	    node = Node(
299	        name=f"{scope_name}.{column}" if scope_name else str(column),
300	        source=source,
301	        expression=select,
302	        source_name=source_name or "",
303	        reference_node_name=reference_node_name or "",
304	    )
305	
306	    if upstream:
307	        upstream.downstream.append(node)
308	
309	    subquery_scopes = {
310	        id(subquery_scope
…[1086 chars elided]…
ource=src_expr, expression=src_expr)
336	            )
337	
338	    # Find all columns that went into creating this one to list their lineage nodes.
339	    source_columns = set(find_all_in_scope(select, exp.Column))
340	
341	    # If the source is a UDTF find columns used in the UDTF to generate the table
342	    if isinstance(source, exp.UDTF):
343	        source_columns |= set(source.find_all(exp.Column))
344	        derived_tables: Sequence[exp.Expr] = [
345	            src.expression.parent
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            src_expr = src.expression if isinstance(src, Scope) else src\n            node.downstream.append(\n                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            )", "new_string": "            src_expr = src.expression if isinstance(src, Scope) else src\n            src_node = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(src_node)\n            if on_node:\n                on_node(src_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    col_expr = col_source or exp.Placeholder()\n                    node.downstream.append(\n                        Node(\n                            name=downstream_column.sql(comments=False),\n     
…[157 chars elided]…
                    col_expr = col_source or exp.Placeholder()\n                    leaf = Node(\n                        name=downstream_column.sql(comments=False),\n                        source=col_expr,\n                        expression=col_expr,\n                    )\n                    node.downstream.append(leaf)\n                    if on_node:\n                        on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[9 chars elided]…
       _cache[cache_key] = node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if on_node:\n        on_node(node)\n\n    if _cache is not None:\n        _cache[cache_key] = node"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Last site: the set-operation node, which is created in the set-operation branch and needs its callback after the union branches are attached.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream", "new_string": "        if created_setop:\n            if on_node:\n                on_node(upstream)\n            if _cache is not None:\n                _cache[cache_key] = upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the `Callable` import, which is only needed for annotations.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence", "new_string": "    from collections.abc import Callable, Iterator, Mapping, Sequence"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-121703-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now tests covering the dict form, the callback (once per node, post-order, across union/CTE/star/join shapes), and `payload`.
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        sql = \"WITH shared AS (SELECT a, b FROM x) SELECT s1.a AS a, s2.b + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a\"\n        schema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\n\n        nodes = lineage(None, sql, schema=schema)\n        self.assertEqual(list(nodes), [\"a\", \"c\"])
…[3024 chars elided]…
ge\\n\", \"import sqlglot\\nfrom sqlglot import exp\\nfrom sqlglot.errors import SqlglotError\\nfrom sqlglot.lineage import Node, lineage\\n\", 1)\nopen(p, \"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -40", "description": "Append lineage tests and run lineage test file"}
[tool_result] self = <tests.test_lineage.TestLineage testMethod=test_lineage_all_columns>

    def test_lineage_all_columns(self) -> None:
        sql = "WITH shared AS (SELECT a, b FROM x) SELECT s1.a AS a, s2.b + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a"
        schema = {"x": {"a": "int", "b": "int"}}
    
        nodes = lineage(None, sql, schema=schema)
        self.assertEqual(list(nodes), ["a", "c"])
    
        for column, node in nodes.items():
            expected = lineage(column, sql, 
…[845 chars elided]…
mns_not_select(self) -> None:
>       with self.assertRaises(SqlglotError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AssertionError: SqlglotError not raised

tests/test_lineage.py:895: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_lineage_all_columns - Asserti...
FAILED tests/test_lineage.py::TestLineage::test_lineage_all_columns_not_select
2 failed, 34 passed, 3 subtests passed in 0.27s
[assistant] Both failures are mistakes in my test expectations, not the implementation. `s1.a` and `s2.b` are different columns, so they share no leaves. And `CREATE TABLE ... AS SELECT` does produce a scope, so it doesn't raise. I'll make both output columns reference the same CTE column so the sharing is real, and drop the wrong assertion.
[tool_use Bash] {"command": "/usr/bin/python3 - <<'EOF'\np = \"tests/test_lineage.py\"\ns = open(p).read()\ns = s.replace('SELECT s1.a AS a, s2.b + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a\"\\n        schema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\\n\\n        nodes',\n              'SELECT s1.a AS a, s2.a + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a\"\\n        schema = {\"x\": {\"a\": \"
…[165 chars elided]…
rror):\n            lineage(None, \"CREATE TABLE t AS SELECT 1\")\n\n''', \"\")\ns = s.replace(\"from sqlglot.errors import SqlglotError\\n\", \"\")\nopen(p, \"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -5", "description": "Fix test expectations and rerun lineage tests"}
[tool_result] tests/test_lineage.py:886: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lineage.py::TestLineage::test_lineage_all_columns - Asserti...
1 failed, 34 passed, 3 subtests passed in 0.10s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfrom sqlglot.lineage import lineage\nsql='WITH shared AS (SELECT a, b FROM x) SELECT s1.a AS a, s2.a + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a'\nn=lineage(None, sql, schema={'x':{'a':'int','b':'int'}})\nfor k,v in n.items():\n    print(k, [(id(x)) for x in v.walk()][:0], [ (x.name, x.source.sql()[:60]) for x in v.walk() if not x.downstream])\nprint({id(x) for x in n['a'].walk()} & {id(x) for x in n['c'].walk()})\nprint([x.name for x in n['a'].walk()], [x.name for x in n['c'].walk()])\n\" 2>&1 | tail -20", "description": "Inspect shared nodes between output columns"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nsql='WITH shared AS (SELECT a, b FROM x) SELECT s1.a AS a, s2.a + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a'\nn=lineage(None, sql, schema={'x':{'a':'int','b':'int'}})\nprint([x.name for x in n['a'].walk()]); print([x.name for x in n['c'].walk()])\nprint({id(x) for x in n['a'].walk()} & {id(x) for x in n['c'].walk()})\n\" 2>&1 | tail -20", "description": "Inspect shared nodes between output columns"}
[tool_result] ['a', 's1.a', 'x.a']
['c', 's2.a', 'x.a']
set()
[assistant] The two columns resolve through different aliases (`s1`, `s2`), so their nodes are distinct objects by design. I'll use a single alias so the cache genuinely shares the subtree.
[tool_use Bash] {"command": "/usr/bin/python3 - <<'EOF'\np = \"tests/test_lineage.py\"\ns = open(p).read()\nold = 'sql = \"WITH shared AS (SELECT a, b FROM x) SELECT s1.a AS a, s2.a + 1 AS c FROM shared s1 JOIN shared s2 ON s1.a = s2.a\"'\nassert s.count(old) == 1\ns = s.replace(old, 'sql = \"WITH shared AS (SELECT a, b FROM x) SELECT s.a AS a, s.a + 1 AS c FROM shared s\"')\nopen(p, \"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3", "description": "Use single CTE alias in shared-node test"}
[tool_result] ...................................                                   [100%]
35 passed, 3 subtests passed in 0.09s
[assistant] Lineage tests pass. Now the full suite plus the project's style and type checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; echo \"--- ruff\"; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; echo \"--- mypy\"; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -5", "description": "Run full test suite, ruff, and mypy"}
[tool_result] ................................. [ 91%]
...............................................................................................                          [100%]
1100 passed, 17883 subtests passed in 50.17s
--- ruff
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
All checks passed!
--- mypy
Success: no issues found in 1 source file
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_lineage.py && $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -1 && git diff --stat", "description": "Apply ruff formatting and recheck lineage tests"}
[tool_result] 1 file reformatted
2 files already formatted
35 passed, 3 subtests passed in 0.09s
 sqlglot/lineage.py    | 110 +++++++++++++++++++++++++++++++++++++++++---------
 tests/test_lineage.py |  70 +++++++++++++++++++++++++++++++-
 2 files changed, 159 insertions(+), 21 deletions(-)
[assistant] Full suite passes (1100 passed). I'll confirm the test-file diff only touches the import line and my new tests.
[tool_use Bash] {"command": "git diff tests/test_lineage.py | grep \"^-\" ; git diff tests/test_lineage.py | head -20", "description": "Check test file diff for removed lines"}
[tool_result] --- a/tests/test_lineage.py
-from sqlglot.lineage import lineage
diff --git a/tests/test_lineage.py b/tests/test_lineage.py
index 13577bb2f..49301a413 100644
--- a/tests/test_lineage.py
+++ b/tests/test_lineage.py
@@ -3,7 +3,8 @@ from __future__ import annotations
 import unittest
 
 import sqlglot
-from sqlglot.lineage import lineage
+from sqlglot import exp
+from sqlglot.lineage import Node, lineage
 from sqlglot.schema import MappingSchema
 
 
@@ -862,3 +863,70 @@ class TestLineage(unittest.TestCase):
         )
         downstream_names = sorted(d.name for d in node.downstream)
         self.assertEqual(downstream_names, ["s1.a", "s2.a"])
+
+    def test_lineage_all_columns(self) -> None:
[assistant] Both extensions are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1100 passed), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`**: `lineage(None, sql, ...)` returns a dict from each top-level output column name to its root `Node`. The single-column form still returns a `Node`. Two `@t.overload` signatures make the return type depend on whether `column` is `None`.
- **`on_node`**: a new keyword argument on `lineage()`, threaded through `to_node`. It fires once per `Node` created during the walk, after that node's downstream 
…[99 chars elided]…
ceholder and star-source nodes. Cache hits don't fire it again.
- **`Node.payload`**: a `dict` field defaulting to a fresh empty dict per node. It's the last field, so existing positional construction is unaffected.

Choices I made that you may want to change:
- `column` is still a required positional argument; pass `None` explicitly rather than making it optional.
- For `column=None`, duplicate output names keep the first occurrence, matching the single-column lookup.
- `on_node` is a keyword argument placed before `**kwargs`, so it isn't forwarded to qualify.
- `to_html()` ignores `payload`.
