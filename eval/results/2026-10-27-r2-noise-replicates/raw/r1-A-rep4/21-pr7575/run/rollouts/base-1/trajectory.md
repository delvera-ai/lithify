# trajectory base-1

final message:
Both parts are implemented in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean. I did not commit.

- **`column=None`:** `lineage(None, sql, ...)` returns a dict from each top-level output name to its `Node`. The single-column form still returns a `Node`. `lineage` has two `@t.overload` signatures so type checkers pick the right return type. `column` is still a required positional argument, so existing calls are unaffected.
- **`on_node`:** a keyword argument on `lineage()`, threaded through the internal `to_node` walk. It fires once for each `Node` created, after that node's downstream is populated. That includes leaf placeholders, star children and set-operation nodes. Cache hits don't re-fire it.
- **`Node.payload`:** a `dict[str, Any]` field defaulting to empty. Callers can write to it from `on_node`.

Choices you may want to change:
- `payload` is a regular dataclass field, so it participates in `Node` equality and repr. Two nodes that differ only in payload compare unequal.
- In `column=None` mode, all output columns share one memoization cache. Duplicate output names collapse to a single dict key, which resolves to the first matching select, as in the single-column form.
- For a non-`SELECT` root, the error now reads "sql must be SELECT" rather than "Cannot find column 'x'". This keeps the message from showing `'None'` in the new mode. No tests depended on the old text.

## events
[tool_use Bash] {"command": "git status --short | head && cat sqlglot/lineage.py && ls tests | grep -i lineage", "description": "Show lineage module and test files"}
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
[tool_use Bash] {"command": "grep -rn \"lineage(\" --include=*.py --include=*.md . | grep -v \"^./tests/test_lineage.py\" | head -30; echo ---; grep -n \"^def \\|^class \\|^    def \" tests/test_lineage.py | head -60; echo ---; sed -n 1,60p tests/test_lineage.py; ls <work>/env-sqlglot/bin/ | head -50", "description": "Find lineage usages, test layout, and env tools"}
[tool_result] (eval):1: no matches found: --include=*.py
---
10:class TestLineage(unittest.TestCase):
14:    def setUpClass(cls):
17:    def test_lineage(self) -> None:
67:    def test_lineage_sql_with_cte(self) -> None:
98:    def test_lineage_source_with_cte(self) -> None:
128:    def test_lineage_source_with_star(self) -> None:
148:    def test_lineage_join_with_star(self) -> None:
169:    def test_lineage_join_with_qualified_star(self) -> None:
186:    def test_lineage_external_col(self) -> None:
206:    
…[2887 chars elided]…
ineage("a", ast)
        self.assertEqual(ast.sql(), sql)

        # test that sources are not modified
        ast = sqlglot.parse_one(sql)

        source_sql = "SELECT a FROM y"
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
dmypy
f2py
identify-cli
markdown2
mypy
mypyc
nodeenv
numpy-config
pdoc
pre-commit
py.test
pydoc.bat
pygmentize
pyperf
pytest
python
python3
python3.12
ruff
setuptools-scm
stubgen
stubtest
vcs-versioning
virtualenv
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"import sqlglot,sys; print(sqlglot.__file__, sys.version)\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -3; grep -n \"lineage\" docs/* README.md 2>/dev/null | head; grep -n \"payload\\|on_node\" sqlglot/lineage.py | head", "description": "Check imported sqlglot path and baseline lineage tests"}
[tool_result] ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/__init__.py 3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
...............................                                          [100%]
31 passed in 0.12s
(eval):1: no matches found: docs/*
[assistant] Baseline lineage tests pass (31). Now the `Node` change: add the caller-managed `payload` dict.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n\n    def walk(self) -> Iterator[Node]:", "new_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n\n    def walk(self) -> Iterator[Node]:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, the `lineage()` signature with typing overloads, the `None` branch, and `on_node` threading.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2912 chars elided]…
e been populated.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each output column name to its lineage node if\n        `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[1267 chars elided]…
, _cache=cache)\n\n\ndef to_node(\n    column: str | int,\n    scope: Scope,\n    dialect: DialectType,\n    scope_name: str | None = None,\n    upstream: Node | None = None,\n    source_name: str | None = None,\n    reference_node_name: str | None = None,\n    trim_selects: bool = True,\n    on_node: Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] I need to check one thing: the non-`Selectable` error message would read "Cannot find column 'None'" in the `None` case. Let me see whether tests depend on that message before I change it.
[tool_use Bash] {"command": "grep -rn \"Cannot find column\\|sql must be SELECT\\|Cannot build lineage\" tests sqlglot | head; grep -n \"class SetOperation\\|class Query(\\|class Selectable\\|class Subquery(\\|class DerivedTable\" sqlglot/expressions.py", "description": "Check error message usages and Selectable classes"}
[tool_result ERROR] Exit code 2
sqlglot/lineage.py:167:        raise SqlglotError("Cannot build lineage, sql must be SELECT")
sqlglot/lineage.py:171:        raise SqlglotError(f"Cannot find column '{column}' in query.")
sqlglot/lineage.py:189:        raise SqlglotError(f"Cannot find column '{column}' in query.")
sqlglot/lineage.py:220:                f"Cannot find column's source with index {column} in query: {selectable.sql(dialect=dialect)}"
ugrep: warning: sqlglot/expressions.py: No such file or directory
[assistant] No tests depend on those messages. I'll give the non-`Selectable` case its own message so `None` never reports `'None'`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable):\n        raise SqlglotError(f\"Cannot find column '{column}' in query.\")\n\n    cache", "new_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable):\n        raise SqlglotError(\"Cannot build lineage, sql must be SELECT\")\n\n    cache"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now `to_node`. Every recursive call already passes `_cache=_cache,` on its own line, so I'll thread `on_node` through all of them in one scripted, count-checked edit, then add the emission points by hand.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I - <<'EOF'\nimport re\np = \"sqlglot/lineage.py\"\nsrc = open(p).read()\nnew, n = re.subn(r\"^(\\s*)_cache=_cache,$\", r\"\\1on_node=on_node,\\n\\1_cache=_cache,\", src, flags=re.M)\nprint(\"replaced\", n)\nassert n == 5, n\nopen(p, \"w\").write(new)\nEOF\ngrep -n \"on_node\" sqlglot/lineage.py", "description": "Thread on_node through recursive to_node calls"}
[tool_result] replaced 5
88:    on_node: Callable[[Node], None] | None = None,
103:    on_node: Callable[[Node], None] | None = None,
117:    on_node: Callable[[Node], None] | None = None,
132:        on_node: A callback invoked with every Node created while walking the lineage graph,
182:                on_node=on_node,
191:    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache=cache)
203:    on_node: Callable[[Node], None] | None = None,
239:                on_node=on_node,
278:                on_node=on_node,
324:                on_node=on_node,
399:                on_node=on_node,
429:                        on_node=on_node,
[assistant] That change was my own scripted edit, so the file is as I intended. I'll re-read the `to_node` body before the remaining edits.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 228, "limit": 120}
[tool_result] 228	
229	    if isinstance(scope.expression, exp.Subquery):
230	        for inner_scope in scope.subquery_scopes:
231	            result = to_node(
232	                column,
233	                scope=inner_scope,
234	                dialect=dialect,
235	                upstream=upstream,
236	                source_name=source_name,
237	                reference_node_name=reference_node_name,
238	                trim_selects=trim_selects,
239	                on_node=on_node,
240	               
…[4022 chars elided]…
 = set(find_all_in_scope(select, exp.Column))
338	
339	    # If the source is a UDTF find columns used in the UDTF to generate the table
340	    if isinstance(source, exp.UDTF):
341	        source_columns |= set(source.find_all(exp.Column))
342	        derived_tables: Sequence[exp.Expr] = [
343	            src.expression.parent
344	            for src in scope.sources.values()
345	            if isinstance(src, Scope) and src.is_derived_table and src.expression.parent
346	        ]
347	    else:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream", "new_string": "        if created_setop:\n            if on_node:\n                on_node(upstream)\n            if _cache is not None:\n                _cache[cache_key] = upstream\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            node.downstream.append(\n                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            )", "new_string": "            star_node = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(star_node)\n            if on_node:\n                on_node(star_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 410, "limit": 70}
[tool_result] 410	            if any(column_name == pivot_column.name for pivot_column in pivot_columns):
411	                downstream_columns.extend(pivot_column_mapping[column_name])
412	            else:
413	                # The column is not in the pivot, so it must be an implicit column of the
414	                # pivoted source -- adapt column to be from the implicit pivoted source.
415	                pivot_parent = pivot.parent
416	                downstream_columns.append(
417	                   
…[2014 chars elided]…
lass GraphHTML:
462	    """Node to HTML generator using vis.js.
463	
464	    https://visjs.github.io/vis-network/docs/network/
465	    """
466	
467	    def __init__(
468	        self,
469	        nodes: dict,
470	        edges: list,
471	        imports: bool = True,
472	        options: Mapping[str, object] | None = None,
473	    ):
474	        self.imports = imports
475	
476	        self.options = {
477	            "height": "500px",
478	            "width": "100%",
479	            "layout": {
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    col_expr = col_source or exp.Placeholder()\n                    node.downstream.append(\n                        Node(\n                            name=downstream_column.sql(comments=False),\n     
…[1518 chars elided]…
ssed into the `sources` map.\n            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if on_node:\n        on_node(node)\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return node"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the `Callable` import for the annotations, then a quick behavioural check.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence", "new_string": "    from collections.abc import Callable, Iterator, Mapping, Sequence"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-174358-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I - <<'EOF'\nimport sys; sys.path.insert(0, \".\")\nfrom sqlglot.lineage import lineage, Node\nsql = \"SELECT a, b + 1 AS c FROM (SELECT a, b FROM x) AS y\"\nschema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\nd = lineage(None, sql, schema=schema)\nprint(type(d), list(d))\nprint(d[\"c\"].name, d[\"a\"].name, d[
…[465 chars elided]…
T * FROM x\", schema=None)\nprint(\"star\", list(d), d[\"*\"].name)\n# payload\ndef tag(node): node.payload[\"seen\"] = True\nn = lineage(\"a\", sql, schema=schema, on_node=tag)\nprint([x.payload for x in n.walk()][:2])\ntry:\n    lineage(None, \"CREATE TABLE q AS SELECT 1 AS a\")\nexcept Exception as e: print(type(e).__name__, e)\nEOF", "description": "Smoke-test dict mode, on_node, and payload"}
[tool_result] <class 'dict'> ['a', 'c']
c a SELECT y.a AS a FROM (SELECT x.a AS a, x.b AS b FROM x AS x) AS y
single Node 3 True
union ['a'] 5 ['x.a', '0', 'z.a', '0', 'UNION']
star ['*'] *
[{'seen': True}, {'seen': True}]
[assistant] Dict mode, the union case, star handling, `on_node` and `payload` all behave as intended. Next, tests in the existing style. Let me look at the end of the test file.
[tool_use Bash] {"command": "tail -40 tests/test_lineage.py; wc -l tests/test_lineage.py", "description": "Show end of lineage test file"}
[tool_result]         With N=12 that's 4096 expansions.
        """
        n_levels = 12
        ctes = ["cte_0 AS (SELECT a FROM base_table)"]
        for k in range(1, n_levels):
            prev = f"cte_{k - 1}"
            ctes.append(
                f"cte_{k} AS (SELECT t1.a + t2.a AS a FROM {prev} t1 JOIN {prev} t2 ON t1.a = t2.a)"
            )
        sql = "WITH " + ",\n     ".join(ctes) + f"\nSELECT a FROM cte_{n_levels - 1}"

        node = lineage("a", sql, schema={"base_table": {"a": "int"}})


…[621 chars elided]…
  self.assertTrue(all("base_table" in n.source.sql() for n in leaves))

    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
        node = lineage(
            "combined",
            "WITH shared AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
     864 tests/test_lineage.py
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        sql = \"SELECT a, b + 1 AS c FROM (SELECT a, b FROM x) AS y\"\n        schema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\n\n        nodes = lineage(None, sql, schema=schema)\n        self.assertEqual(list(nodes), [\"a\", \"c\"])\n\n        for name, node in nodes.items():\n            sel
…[1568 chars elided]…
 \"int\"}}).payload, {})\nEOF\nsed -i 's/^from sqlglot.lineage import lineage$/from sqlglot.lineage import Node, lineage/' tests/test_lineage.py && head -8 tests/test_lineage.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Add lineage tests and run lineage test file"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/test_lineage.py
": undefined label 'ests/test_lineage.py'
[assistant] The append succeeded, but BSD `sed -i` needs an explicit backup suffix on macOS, so the import rewrite didn't run. I'll redo that step with the correct syntax.
[tool_use Bash] {"command": "sed -i '' 's/^from sqlglot.lineage import lineage$/from sqlglot.lineage import Node, lineage/' tests/test_lineage.py && head -6 tests/test_lineage.py && grep -c \"def test_lineage_all_columns\\|def test_lineage_payload\\|def test_lineage_on_node\" tests/test_lineage.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Fix import line and run lineage tests"}
[tool_result] from __future__ import annotations

import unittest

import sqlglot
from sqlglot.lineage import Node, lineage
3
..................................                                       [100%]
34 passed in 0.09s
[assistant] All 34 lineage tests pass. Now the full suite plus the project's lint and type checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -15", "description": "Run full test suite, ruff, and mypy"}
[tool_result] (eval):1: permission denied: <work>/env-sqlglot/bin
(eval):1: permission denied: <work>/env-sqlglot/bin
(eval):1: permission denied: <work>/env-sqlglot/bin
(eval):1: permission denied: <work>/env-sqlglot/bin
[assistant] I set `PY` to the `bin` directory instead of the interpreter. Fixing that.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY -m mypy sqlglot/lineage.py 2>&1 | tail -15", "description": "Run full test suite, ruff, and mypy"}
[tool_result] ............................................. [ 78%]
............................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1099 passed, 17880 subtests passed in 48.40s
All checks passed!
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
Success: no issues found in 1 source file
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_lineage.py && $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -1 && git diff --stat && git diff sqlglot/lineage.py | head -150", "description": "Format test file, re-verify, and review diff"}
[tool_result] 1 file reformatted
2 files already formatted
34 passed in 0.09s
 sqlglot/lineage.py    | 114 ++++++++++++++++++++++++++++++++++++++++----------
 tests/test_lineage.py |  49 +++++++++++++++++++++-
 2 files changed, 139 insertions(+), 24 deletions(-)
diff --git a/sqlglot/lineage.py b/sqlglot/lineage.py
index 00b1c1fbd..e4e3f0df4 100644
--- a/sqlglot/lineage.py
+++ b/sqlglot/lineage.py
@@ -12,7 +12,7 @@ from sqlglot.optimizer.scope import ScopeType
 
 if t.TYPE_CHECKING:
     from sqlglot.dialects.
…[4684 chars elided]…
   source_name=source_name,
                 reference_node_name=reference_node_name,
                 trim_selects=trim_selects,
+                on_node=on_node,
                 _cache=_cache,
             )
             # Skip caching a passed-in upstream returned by an inner SetOp:
@@ -220,11 +275,15 @@ def to_node(
                 source_name=source_name,
                 reference_node_name=reference_node_name,
                 trim_selects=trim_selects,
+                on_node=on_node,
[assistant] The diff reads as intended. One last check: whether anything else calls `to_node` positionally, since I inserted `on_node` just before `_cache`.
[tool_use Bash] {"command": "grep -rn \"to_node\\b\" --include=*.py . | grep -v \"^./sqlglot/lineage.py\" | head; grep -rln \"from sqlglot.lineage\\|sqlglot import lineage\\|lineage\\.lineage\" --include=*.py . | head", "description": "Find external callers of to_node and lineage"}
[tool_result] (eval):1: no matches found: --include=*.py
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "git grep -n \"to_node\\|sqlglot.lineage\" -- '*.py' | grep -v \"^sqlglot/lineage.py\" | head", "description": "Search tracked Python files for to_node and lineage imports"}
[tool_result] tests/test_lineage.py:6:from sqlglot.lineage import Node, lineage
tests/test_lineage.py:824:        (t1.a + t2.a), so without memoization to_node() is called 2^N times.
[assistant] Both parts are implemented in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean. I did not commit.

- **`column=None`:** `lineage(None, sql, ...)` returns a dict from each top-level output name to its `Node`. The single-column form still returns a `Node`. `lineage` has two `@t.overload` signatures so type checkers pick the right return type. `column` is still a required positional argument, so existing calls are unaffected.
- **`on_node`:** a keyword argument on `lineage()`, threaded through the internal `to_node` walk
…[275 chars elided]…
t from `on_node`.

Choices you may want to change:
- `payload` is a regular dataclass field, so it participates in `Node` equality and repr. Two nodes that differ only in payload compare unequal.
- In `column=None` mode, all output columns share one memoization cache. Duplicate output names collapse to a single dict key, which resolves to the first matching select, as in the single-column form.
- For a non-`SELECT` root, the error now reads "sql must be SELECT" rather than "Cannot find column 'x'". This keeps the message from showing `'None'` in the new mode. No tests depended on the old text.
