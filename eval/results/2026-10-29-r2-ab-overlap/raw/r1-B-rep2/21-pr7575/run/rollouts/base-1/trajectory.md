# trajectory base-1

final message:
Both changes are in `sqlglot/lineage.py`, with tests added to `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`:** returns `dict[str, Node]` keyed by each top-level output name, sharing one walk cache. The single-column form still returns a `Node`. Two `@t.overload` signatures distinguish the return types.
- **`on_node`:** a keyword argument on `lineage()`, threaded through `to_node()`. It is called once per created node, after that node's downstream is populated. That covers the per-scope nodes, the set-operation node, and the leaf nodes.
- **`Node.payload`:** a `dict[str, Any]` field defaulting to an empty dict, left for callers to use.

Choices I made that you may want to change:
- Duplicate output names collapse into one dict key, since the lookup is by name.
- For a set operation, `column=None` keys by the left-hand arm's names, the same as `selects` does.
- `payload` takes part in `Node` equality, because it's a normal dataclass field.

## events
[tool_use Bash] {"command": "cat sqlglot/lineage.py && git status --short && ls .lithify/harness/scripts/ && grep -rn \"lineage\" tests/ --include=*.py -l", "description": "Read lineage module and list lineage tests"}
[tool_result ERROR] Exit code 1
from __future__ import annotations

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
…[9039 chars elided]…
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
okprobe_parse.py  2.2K
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "sed -n 150,290p sqlglot/lineage.py", "description": "Read middle section of lineage.py"}
[tool_result]     _cache: dict[tuple, Node] | None = None,
) -> Node:
    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)

    if _cache is not None and cache_key in _cache:
        cached_node = _cache[cache_key]
        if upstream:
            upstream.downstream.append(cached_node)
        return cached_node

    # Find the specific select clause that is the source of the column we want.
    # This can either be a specific, named select or a generic `*` clause.
    selectable
…[4466 chars elided]…
 their lineage nodes.
    source_columns = set(find_all_in_scope(select, exp.Column))

    # If the source is a UDTF find columns used in the UDTF to generate the table
    if isinstance(source, exp.UDTF):
        source_columns |= set(source.find_all(exp.Column))
        derived_tables: Sequence[exp.Expr] = [
            src.expression.parent
            for src in scope.sources.values()
            if isinstance(src, Scope) and src.is_derived_table and src.expression.parent
        ]
    else:
[tool_use Bash] {"command": "grep -rln \"lineage\" tests/ ; grep -rn \"lineage\" sqlglot --include=*.py | grep -v \"^sqlglot/lineage.py\" | head -30; git status --short", "description": "Find lineage usages and tests"}
[tool_result] tests/test_lineage.py
(eval):1: no matches found: --include=*.py
ok
[tool_use Bash] {"command": "grep -n \"Node(\\|to_node(\\|def \\|downstream\" sqlglot/lineage.py; sed -n 290,330p sqlglot/lineage.py; grep -n \"^def \\|^class \\|lineage(\" tests/test_lineage.py | head -60; sed -n 1,30p tests/test_lineage.py", "description": "Locate Node creation sites and test file layout"}
[tool_result] rg: regex parse error:
    (?:Node(|to_node(|def |downstream)
           ^
error: unclosed group
0 matches for 'Node(\|to_node(\|def \|downstream'
    else:
        derived_tables = scope.derived_tables

    source_names = {
        dt.alias: dt.comments[0].split()[1]
        for dt in derived_tables
        if dt.comments and dt.comments[0].startswith("source: ")
    }

    pivots = scope.pivots
    pivot = pivots[0] if len(pivots) == 1 and not pivots[0].unpivot else None
    if pivot:
        
…[2120 chars elided]…
lineage(self) -> None:
        node = lineage(
            "a",
            "SELECT a FROM z",
            schema={"x": {"a": "int"}},
            sources={"y": "SELECT * FROM x", "z": "SELECT a FROM y"},
        )
        self.assertEqual(
            node.source.sql(),
            "SELECT z.a AS a FROM (SELECT y.a AS a FROM (SELECT x.a AS a FROM x AS x) AS y /* source: y */) AS z /* source: z */",
        )
        self.assertEqual(node.source_name, "")

        downstream = node.downstream[0]
[tool_use Grep] {"pattern": "Node\\(|to_node\\(", "path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "output_mode": "content", "-n": "true"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 330, "limit": 30}
[tool_result] 330	                reference_node_name = selected_node.name if selected_node else None
331	
332	            # The table itself came from a more specific scope. Recurse into that one using the unaliased column name.
333	            to_node(
334	                c.name,
335	                scope=col_source,
336	                dialect=dialect,
337	                scope_name=table,
338	                upstream=node,
339	                source_name=source_names.get(table) or source_name,
340	       
…[508 chars elided]…
The column is not in the pivot, so it must be an implicit column of the
352	                # pivoted source -- adapt column to be from the implicit pivoted source.
353	                pivot_parent = pivot.parent
354	                downstream_columns.append(
355	                    exp.column(c.this, table=pivot_parent.alias_or_name if pivot_parent else "")
356	                )
357	
358	            for downstream_column in downstream_columns:
359	                table = downstream_column.table
[assistant] Node creation sites are: the set-operation node, the main per-scope node, and four leaf `Node(...)` constructions appended inline. I'll make the edits now.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n\n    def walk(self) -> Iterator[Node]:", "new_string": "    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    payload: dict[str, t.Any] = field(default_factory=dict)\n\n    def walk(self) -> Iterator[Node]:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[2904 chars elided]…
e been populated.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict mapping each output column name to its lineage node if\n        `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[552 chars elided]…
ct.fromkeys(select.alias_or_name for select in selectable.selects)\n        }\n\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot find column '{column}' in query.\")\n\n    return to_node(column, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache={})"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Next, thread `on_node` through `to_node` and notify at each creation site.
[tool_use Bash] {"command": "perl -0pi -e 's/^(\\s*)_cache=_cache,/$1on_node=on_node,\\n$1_cache=_cache,/mg' sqlglot/lineage.py && grep -c \"on_node=on_node,\" sqlglot/lineage.py && git diff --stat", "description": "Thread on_node kwarg through recursive to_node calls"}
[tool_result] 7
sqlglot/lineage.py | 64 +++++++++++++++++++++++++++++++++++++++++++++++++-----
 1 file changed, 59 insertions(+), 5 deletions(-)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "offset": 150, "limit": 30}
[tool_result] 150	                for k, v in sources.items()
151	            },
152	            dialect=dialect,
153	            copy=copy,
154	        )
155	
156	    if not scope:
157	        expression = qualify.qualify(
158	            expression,
159	            dialect=dialect,
160	            schema=schema,
161	            **{"validate_qualify_columns": False, "identify": False, **kwargs},  # type: ignore
162	        )
163	
164	        scope = build_scope(expression)
165	
166	    if not scope:
167	    
…[87 chars elided]…
ble = scope.expression
170	    if column is None:
171	        if not isinstance(selectable, exp.Selectable):
172	            raise SqlglotError("Cannot build lineage, sql must be SELECT")
173	
174	        cache: dict[tuple, Node] = {}
175	        return {
176	            name: to_node(
177	                name, scope, dialect, trim_selects=trim_selects, on_node=on_node, _cache=cache
178	            )
179	            for name in dict.fromkeys(select.alias_or_name for select in selectable.selects)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    trim_selects: bool = True,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)", "new_string": "    trim_selects: bool = True,\n    on_node: t.Callable[[Node], None] | None = None,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key = (column, id(scope), scope_name, source_name, reference_node_name)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        upstream = upstream or Node(name=name, source=scope.expression, expression=select)", "new_string": "        created_setop_node = upstream is None\n        upstream = upstream or Node(name=name, source=scope.expression, expression=select)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream", "new_string": "        if created_setop:\n            _notify(upstream, on_node)\n        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        created_setop_node = upstream is None\n        upstream = upstream or Node(name=name, source=scope.expression, expression=select)", "new_string": "        created_setop = upstream is None\n        upstream = upstream or Node(name=name, source=scope.expression, expression=select)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "grep -n \"created_setop\\|Node(\\|_cache\\[cache_key\\]\\|downstream.append\" sqlglot/lineage.py", "description": "Locate creation and cache sites in lineage.py"}
[tool_result ERROR] Exit code 2
rg: regex parse error:
    (?:created_setop|Node(|_cache\[cache_key\]|downstream.append)
    ^
error: unclosed group
0 matches for 'created_setop\|Node(\|_cache\[cache_key\]\|downstream.append'
[tool_use Bash] {"command": "awk '/created_setop|Node\\(|_cache\\[cache_key\\]|downstream.append/{print FILENAME\":\"FNR\": \"$0}' sqlglot/lineage.py", "description": "Locate creation and cache sites in lineage.py"}
[tool_result] sqlglot/lineage.py:205:         cached_node = _cache[cache_key]
sqlglot/lineage.py:207:             upstream.downstream.append(cached_node)
sqlglot/lineage.py:242:                 _cache[cache_key] = result
sqlglot/lineage.py:246:         created_setop = upstream is None
sqlglot/lineage.py:247:         created_setop = upstream is None
sqlglot/lineage.py:248:         upstream = upstream or Node(name=name, source=scope.expression, expression=select)
sqlglot/lineage.py:279:         if created_setop
…[271 chars elided]…
           node.downstream.append(
sqlglot/lineage.py:332:                 Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)
sqlglot/lineage.py:433:                     node.downstream.append(
sqlglot/lineage.py:434:                         Node(
sqlglot/lineage.py:446:             node.downstream.append(
sqlglot/lineage.py:447:                 Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)
sqlglot/lineage.py:451:         _cache[cache_key] = node
[assistant] Line 246–247 now has a duplicate `created_setop` assignment from my edit. Removing it, then wiring the leaf and main-node sites.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        created_setop = upstream is None\n        created_setop = upstream is None\n", "new_string": "        created_setop = upstream is None\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            node.downstream.append(\n                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            )", "new_string": "            node.downstream.append(\n                _notify(\n                    Node(name=select.sql(comments=False), source=src_expr, expression=src_expr),\n                    on_node,\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    node.downstream.append(\n                        Node(\n                            name=downstream_column.sql(comments=False),\n                            source=col_expr,\n                       
…[108 chars elided]…
     node.downstream.append(\n                        _notify(\n                            Node(\n                                name=downstream_column.sql(comments=False),\n                                source=col_expr,\n                                expression=col_expr,\n                            ),\n                            on_node,\n                        )\n                    )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return node", "new_string": "            node.downstream.append(\n                _notify(\n                    Node(name=c.sql(comments=False), source=col_expr, expression=col_expr),\n                    on_node,\n                )\n            )\n\n    _notify(node, on_node)\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return node"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def to_node(\n    column: str | int,", "new_string": "def _notify(node: Node, on_node: t.Callable[[Node], None] | None) -> Node:\n    if on_node:\n        on_node(node)\n    return node\n\n\ndef to_node(\n    column: str | int,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now a quick behavioural check: multi-column, union, star, callback ordering, and node count versus the walk.
[tool_use Bash] {"command": "mkdir -p /tmp/lin_probe && cat > /tmp/lin_probe/probe.py <<'EOF'\nimport sys\nfrom sqlglot.lineage import lineage, Node\nschema = {\"x\": {\"a\": \"int\", \"b\": \"int\"}}\nsql = \"SELECT a, b + 1 AS c FROM x\"\nseen = []\ndef cb(n):\n    n.payload[\"seen\"] = len(n.downstream)\n    seen.append(n)\nres = lineage(None, sql, schema=schema, on_node=cb)\nprint(type(res).__name__, list(res
…[743 chars elided]…
hema=schema)).__name__)\nEOF\ncd /tmp/lin_probe && <work>/env-sqlglot/bin/python -I -c \"import sys; sys.path.insert(0, '~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1'); exec(open('/tmp/lin_probe/probe.py').read())\"", "description": "Probe lineage column=None, on_node and payload behaviour"}
[tool_result] dict ['a', 'c']
{'a': 'a', 'c': 'c'}
walked 4 callbacks 4 unique 4 all walked True
payload [{'seen': 0}, {'seen': 1}, {'seen': 0}]
cb x.a Table
cb 0 Alias
cb x.a Table
cb 0 Alias
cb UNION Alias
union ok UNION
star {'a': Node(name='a', expression=Alias(
  this=Column(
    this=Identifier(this=a, quoted=False),
    table=Identifier(this=x, quoted=False)),
  alias=Identifier(this=a, quoted=False)), source=Select(
  expressions=[
    Alias(
      this=Column(
        this=Identifier(this=a, quoted=F
…[1252 chars elided]…
(this=x, quoted=False),
  alias=TableAlias(
    this=Identifier(this=x, quoted=False))), source=Table(
  this=Identifier(this=x, quoted=False),
  alias=TableAlias(
    this=Identifier(this=x, quoted=False))), downstream=[], source_name='', reference_node_name='', payload={})], source_name='', reference_node_name='', payload={})}
union none {'a': 'UNION'}
single Node
Shell cwd was reset to ~/.cache/lithify/work/repo-3abf279ffb90/20261029-145716-lineage-extend-sqlglot-lineage-l/base-1
[assistant] Behaviour matches the spec: the dict keys are output names, the callback fires post-order with downstream populated, and every walked node is notified exactly once. Next I'll add tests to the existing lineage test file.
[tool_use Bash] {"command": "wc -l tests/test_lineage.py && tail -30 tests/test_lineage.py && grep -n \"    def test_\" tests/test_lineage.py | tail -5", "description": "Inspect end of lineage test file"}
[tool_result] 864

        node = lineage("a", sql, schema={"base_table": {"a": "int"}})

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
        self.assertEq
…[200 chars elided]…
elf.assertTrue(all("base_table" in n.source.sql() for n in leaves))

    def test_lineage_cte_self_join_distinct_aliases(self) -> None:
        node = lineage(
            "combined",
            "WITH shared AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
733:0:
770:0:
820:0:
857:0:
98:0:
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        sql = \"SELECT a, b + 1 AS c FROM x\"\n        nodes = lineage(None, sql, schema={\"x\": {\"a\": \"int\", \"b\": \"int\"}})\n\n        self.assertEqual(list(nodes), [\"a\", \"c\"])\n        self.assertEqual(nodes[\"a\"].name, \"a\")\n        self.assertEqual(nodes[\"c\"].name, \"c\")\n    
…[1336 chars elided]…
.assertIn(node, calls)\n        self.assertEqual(len({id(n) for n in calls}), len(calls))\n        self.assertEqual({id(n) for n in calls}, {id(n) for n in node.walk()})\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -30", "description": "Append lineage tests and run lineage test module"}
[tool_result] ..................................                                       [100%]
34 passed in 0.15s
[assistant] Lineage tests pass. Now formatting, lint and type checks on the two files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; ls $PY | grep -E \"ruff|mypy\"; $PY/ruff format --check sqlglot/lineage.py tests/test_lineage.py; $PY/ruff check sqlglot/lineage.py tests/test_lineage.py; $PY/mypy sqlglot/lineage.py 2>&1 | tail -15", "description": "Run ruff format, ruff check and mypy on changed files"}
[tool_result] dmypy  374B
mypy  370B
mypyc  353B
ruff  22.5M
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
All checks passed!
Success: no issues found in 1 source file
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin; $PY/ruff format tests/test_lineage.py && git diff tests/test_lineage.py | head -80", "description": "Apply ruff format to lineage test file and show diff"}
[tool_result] 1 file reformatted
tests/test_lineage.py | 47 +++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 47 insertions(+)

--- Changes ---

tests/test_lineage.py
  @@ -862,3 +862,50 @@ class TestLineage(unittest.TestCase):
  +
  +    def test_lineage_all_columns(self) -> None:
  +        sql = "SELECT a, b + 1 AS c FROM x"
  +        nodes = lineage(None, sql, schema={"x": {"a": "int", "b": "int"}})
  +
  +        self.assertEqual(list(nodes), ["a", "c"])
  +        self.assertEqual(nodes[
…[1143 chars elided]…

  +    def test_lineage_on_node_set_operation(self) -> None:
  +        calls = []
  +        node = lineage(
  +            "a",
  +            "SELECT a FROM x UNION SELECT a FROM y",
  +            schema={"x": {"a": "int"}, "y": {"a": "int"}},
  +            on_node=calls.append,
  +        )
  +
  +        self.assertIn(node, calls)
  +        self.assertEqual(len({id(n) for n in calls}), len(calls))
  +        self.assertEqual({id(n) for n in calls}, {id(n) for n in node.walk()})
  +47 -0
[assistant] Formatting, lint and mypy are clean. Running the full suite as the final gate.
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 600000}
[tool_result] ..................................................................... [ 38%]
................................................ [ 42%]
...................................................................................................................................... [ 54%]
.................. [ 56%]
...................... [ 58%]
............................................ [ 62%]
....................................... [ 66%]
......................................... [ 69%]
.... [ 70%]
.................................................. [ 74%]
............................................. [ 78%]
............................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1099 passed, 17880 subtests passed in 60.90s (0:01:00)
[assistant] Both changes are in `sqlglot/lineage.py`, with tests added to `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean. I haven't committed anything.

- **`column=None`:** returns `dict[str, Node]` keyed by each top-level output name, sharing one walk cache. The single-column form still returns a `Node`. Two `@t.overload` signatures distinguish the return types.
- **`on_node`:** a keyword argument on `lineage()`, threaded through `to_node()`. It is called once per created node, after that node's downstream is populated. That covers the per-scope nodes, the set-operation node, and the leaf nodes.
- **`Node.payload`:** a `dict[str, Any]` field defaulting to an empty dict, left for callers to use.

Choices I made that you may want to change:
- Duplicate output names collapse into one dict key, since the lookup is by name.
- For a set operation, `column=None` keys by the left-hand arm's names, the same as `selects` does.
- `payload` takes part in `Node` equality, because it's a normal dataclass field.
