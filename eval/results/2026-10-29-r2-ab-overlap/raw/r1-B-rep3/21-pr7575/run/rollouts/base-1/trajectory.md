# trajectory base-1

final message:
Both changes are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean on the touched files. I did not commit.

**What changed**

- **`column=None` returns a dict.** `lineage(None, sql, ...)` returns `{output_name: Node}` for every top-level select. The single-column form still returns a `Node`. Two `@t.overload` signatures distinguish the return types. `column` remains a required argument, so passing `None` is explicit.
- **`on_node` callback.** `lineage()` and `to_node()` take `on_node: Callable[[Node], object] | None = None`. It fires once per node created during the walk, not once per cache hit. Each node is reported after its downstream nodes are populated, which holds for the main node, the set-operation node, and the leaf nodes (star sources, pivot leaves, and plain column leaves).
- **`Node.payload`.** A new `payload: dict[str, Any]` field with `default_factory=dict`. I set `compare=False`, so payload contents do not affect `Node` equality. Say if you want payload to count toward equality.

**Tests added**

- `test_lineage_all_columns`: dict keys, node names, and that each node matches the single-column result.
- `test_lineage_on_node`: across a union, a derived table, and a CTE, every node in `walk()` is reported exactly once, and `downstream` is already complete when the callback runs.
- `test_lineage_payload`: payload set in the callback is visible afterward, and defaults to `{}`.

**Choices you may want to change**

- Dict keys are the top-level output names (`alias_or_name`). Duplicate output names collapse to one key, because the dict cannot hold both.
- In dict mode the walk shares one cache across columns, so common upstream nodes are built once and shared.

## events
[tool_use Bash] {"command": "git status --short | head && wc -l sqlglot/lineage.py && cat sqlglot/lineage.py", "description": "Check worktree status and read lineage module"}
[tool_result] ok477
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
    f
…[16428 chars elided]…
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
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage(\\|Node(\" --include=*.py . | grep -v \"^./tests/fixtures\" | head -50; echo ---; sed -n 1,60p tests/test_lineage.py; echo ---; grep -n \"requires-python\\|python_requires\" pyproject.toml setup.py 2>/dev/null; grep -n \"overload\" -r sqlglot/*.py | head -5", "description": "Find lineage callers, tests, and Python version"}
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
…[1048 chars elided]…
sql = "SELECT a FROM x"
        ast = sqlglot.parse_one(sql)
        node = lineage("a", ast)
        self.assertEqual(ast.sql(), sql)

        # test that sources are not modified
        ast = sqlglot.parse_one(sql)

        source_sql = "SELECT a FROM y"
---
1 matches in 1 files:

pyproject.toml:9:requires-python = ">= 3.9"
sqlglot/__init__.py:113:@t.overload
sqlglot/__init__.py:124:@t.overload
sqlglot/helper.py:95:@t.overload
sqlglot/helper.py:99:@t.overload
sqlglot/helper.py:379:@t.overload
[tool_use Bash] {"command": "grep -rn \"to_node\\|lineage(\\|Node(\" sqlglot tests --include='*.py' | grep -v \"^tests/fixtures\" | grep -v \"sqlglot/lineage.py\" | head -30; echo ---; grep -n \"def test_\\|^class\" tests/test_lineage.py | tail -30; wc -l tests/test_lineage.py; sed -n 105,135p sqlglot/__init__.py", "description": "Find other lineage usages, test layout, overload example"}
[tool_result] tests/test_lineage.py:17:    def test_lineage(self) -> None:
tests/test_lineage.py:18:        node = lineage(
tests/test_lineage.py:54:        node = lineage("a", ast)
tests/test_lineage.py:63:        node = lineage("a", ast, sources={"x": source})
tests/test_lineage.py:68:        node = lineage(
tests/test_lineage.py:99:        node = lineage(
tests/test_lineage.py:129:        node = lineage(
tests/test_lineage.py:149:        node = lineage(
tests/test_lineage.py:170:        node = lineage(
tes
…[1560 chars elided]…
e collection.
    """
    return Dialect.get_or_raise(read or dialect).parse(sql, **opts)


@t.overload
def parse_one(
    sql: str,
    *,
    read: DialectType = ...,
    dialect: DialectType = ...,
    into: Type[E],
    **opts: Unpack[ParserNoDialectArgs],
) -> E: ...


@t.overload
def parse_one(
    sql: str,
    read: DialectType = ...,
    dialect: DialectType = ...,
    into: exp.IntoType | None = ...,
    **opts: Unpack[ParserNoDialectArgs],
) -> Expr: ...


def parse_one(
    sql: str,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "limit": 30}
[tool_result] 1	from __future__ import annotations
2	
3	import json
4	import logging
5	import typing as t
6	from dataclasses import dataclass, field
7	
8	from sqlglot import Schema, exp, maybe_parse
9	from sqlglot.errors import SqlglotError
10	from sqlglot.optimizer import Scope, build_scope, find_all_in_scope, normalize_identifiers, qualify
11	from sqlglot.optimizer.scope import ScopeType
12	
13	if t.TYPE_CHECKING:
14	    from sqlglot.dialects.dialect import DialectType
15	    from collections.abc import Iterator, Mapping, Sequence
16	    from sqlglot._typing import GraphHTMLArgs
17	    from typing_extensions import Unpack
18	
19	logger = logging.getLogger("sqlglot")
20	
21	
22	@dataclass(frozen=True)
23	class Node:
24	    name: str
25	    expression: exp.Expr
26	    source: exp.Expr
27	    downstream: list[Node] = field(default_factory=list)
28	    source_name: str = ""
29	    reference_node_name: str = ""
30	
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np = \"sqlglot/lineage.py\"\ns = open(p).read()\ns, n = re.subn(r\"^(\\s*)_cache=_cache,\\n\", lambda m: f\"{m.group(0)}{m.group(1)}on_node=on_node,\\n\", s, flags=re.M)\nprint(\"recursive call sites updated:\", n)\nopen(p, \"w\").write(s)\nEOF\ngrep -n \"_cache=_cache\" -A1 sqlglot/lineage.py | head -40", "description": "Thread on_node kwarg through recursive to_node calls"}
[tool_result] recursive call sites updated: 5
185:                _cache=_cache,
186-                on_node=on_node,
--
224:                _cache=_cache,
225-                on_node=on_node,
--
270:                _cache=_cache,
271-                on_node=on_node,
--
345:                _cache=_cache,
346-                on_node=on_node,
--
375:                        _cache=_cache,
376-                        on_node=on_node,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    from collections.abc import Iterator, Mapping, Sequence\n    from sqlglot._typing import GraphHTMLArgs\n    from typing_extensions import Unpack\n\nlogger = logging.getLogger(\"sqlglot\")\n\n\n@dataclass(frozen=Tru
…[426 chars elided]…
n\n@dataclass(frozen=True)\nclass Node:\n    name: str\n    expression: exp.Expr\n    source: exp.Expr\n    downstream: list[Node] = field(default_factory=list)\n    source_name: str = \"\"\n    reference_node_name: str = \"\"\n    # Caller-managed data, e.g. attached from an `on_node` callback. Excluded from equality.\n    payload: dict[str, t.Any] = field(default_factory=dict, compare=False)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "def lineage(\n    column: str | exp.Column,\n    sql: str | exp.Expr,\n    schema: dict | Schema | None = None,\n    sources: Mapping[str, str | exp.Query] | None = None,\n    dialect: DialectType = None,\n    scope: S
…[3024 chars elided]…
set `Node.payload`.\n        **kwargs: Qualification optimizer kwargs.\n\n    Returns:\n        A lineage node, or a dict of output column names to lineage nodes if `column` is None.\n    \"\"\"\n\n    expression = maybe_parse(sql, copy=copy, dialect=dialect)\n    if column is not None:\n        column = normalize_identifiers.normalize_identifiers(column, dialect=dialect).name\n\n    if sources:"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    selectable = scope.expression\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot fi
…[622 chars elided]…
node,\n            )\n            for select in selectable.selects\n        }\n\n    if not isinstance(selectable, exp.Selectable) or not any(\n        select.alias_or_name == column for select in selectable.selects\n    ):\n        raise SqlglotError(f\"Cannot find column '{column}' in query.\")\n\n    return to_node(column, scope, dialect, trim_selects=trim_selects, _cache={}, on_node=on_node)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "    trim_selects: bool = True,\n    _cache: dict[tuple, Node] | None = None,\n) -> Node:\n    cache_key", "new_string": "    trim_selects: bool = True,\n    _cache: dict[tuple, Node] | None = None,\n    on_node: Callable[[Node], object] | None = None,\n) -> Node:\n    cache_key"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[assistant] Now the SetOperation path, where a node is created locally and returned directly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        if _cache is not None and created_setop:\n            _cache[cache_key] = upstream\n        return upstream", "new_string": "        if created_setop:\n            if on_node:\n                on_node(upstream)\n            if _cache is not None:\n                _cache[cache_key] = upstream\n        return upstream"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "        for src in scope.sources.values():\n            src_expr = src.expression if isinstance(src, Scope) else src\n            node.downstream.append(\n                Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            )", "new_string": "        for src in scope.sources.values():\n            src_expr = src.expression if isinstance(src, Scope) else src\n            leaf = Node(name=select.sql(comments=False), source=src_expr, expression=src_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "                    col_expr = col_source or exp.Placeholder()\n                    node.downstream.append(\n                        Node(\n                            name=downstream_column.sql(comments=False),\n     
…[157 chars elided]…
                    col_expr = col_source or exp.Placeholder()\n                    leaf = Node(\n                        name=downstream_column.sql(comments=False),\n                        source=col_expr,\n                        expression=col_expr,\n                    )\n                    node.downstream.append(leaf)\n                    if on_node:\n                        on_node(leaf)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py", "old_string": "            col_expr = col_source or exp.Placeholder()\n            node.downstream.append(\n                Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            )\n\n    if _cache is not
…[45 chars elided]…
   return node", "new_string": "            col_expr = col_source or exp.Placeholder()\n            leaf = Node(name=c.sql(comments=False), source=col_expr, expression=col_expr)\n            node.downstream.append(leaf)\n            if on_node:\n                on_node(leaf)\n\n    if on_node:\n        on_node(node)\n    if _cache is not None:\n        _cache[cache_key] = node\n\n    return node"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-183743-lineage-extend-sqlglot-lineage-l/base-1/sqlglot/lineage.py has been updated successfully.
[tool_use Bash] {"command": "tail -25 tests/test_lineage.py && grep -n \"UNION\" tests/test_lineage.py | head -3", "description": "Inspect end of lineage test file"}
[tool_result]         # shared references keep node count small (O(N), not O(2^N)).
        self.assertLess(
            len(all_nodes),
            200,
            f"got {len(all_nodes)} nodes -- DAG walk may be broken",
        )

        # walk() should yield each node exactly once.
        all_ids = [id(n) for n in all_nodes]
        self.assertEqual(len(all_ids), len(set(all_ids)))

        # Leaf nodes should reference base_table.
        leaves = [n for n in all_nodes if not n.downstream]
        self
…[126 chars elided]…
age_cte_self_join_distinct_aliases(self) -> None:
        node = lineage(
            "combined",
            "WITH shared AS (SELECT a FROM x) SELECT s1.a + s2.a AS combined FROM shared s1, shared s2",
            schema={"x": {"a": "int"}},
        )
        downstream_names = sorted(d.name for d in node.downstream)
        self.assertEqual(downstream_names, ["s1.a", "s2.a"])
8 matches in 1 files:

tests/test_lineage.py:263:"SELECT ax AS x FROM a UNION SELECT bx FROM b UNION SELECT cx FROM c",
[tool_use Bash] {"command": "cat >> tests/test_lineage.py <<'EOF'\n\n    def test_lineage_all_columns(self) -> None:\n        sql = \"SELECT a, b + 1 AS c FROM x JOIN y ON x.id = y.id\"\n        schema = {\"x\": {\"id\": \"int\", \"a\": \"int\"}, \"y\": {\"id\": \"int\", \"b\": \"int\"}}\n\n        nodes = lineage(None, sql, schema=schema)\n        self.assertEqual(list(nodes), [\"a\", \"c\"])\n\n        for colu
…[2058 chars elided]…
read()\ns=s.replace(\"import sqlglot\\nfrom sqlglot.lineage import lineage\\n\",\"import sqlglot\\nfrom sqlglot.lineage import Node, lineage\\n\",1)\nopen(p,\"w\").write(s)\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/test_lineage.py 2>&1 | tail -40", "description": "Add lineage tests and run lineage test module"}
[tool_result] ..................................                                   [100%]
34 passed, 4 subtests passed in 0.24s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -m ruff --version 2>&1; $PY -m ruff format --check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m ruff check sqlglot/lineage.py tests/test_lineage.py 2>&1 | tail -3; $PY -m mypy --version 2>&1 | tail -1", "description": "Run full test suite and style checks"}
[tool_result] ........................... [ 85%]
.......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1099 passed, 17884 subtests passed in 46.90s
ruff 0.15.6
Would reformat: tests/test_lineage.py
1 file would be reformatted, 1 file already formatted
All checks passed!
mypy 2.3.0.post2 (compiled: yes)
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/test_lineage.py && git diff --stat && $PY -m mypy sqlglot/lineage.py 2>&1 | tail -5; git stash list | head -0; git show HEAD:sqlglot/lineage.py > /tmp/orig_lineage_check.py 2>/dev/null; $PY -m mypy sqlglot/lineage.py 2>&1 | grep -c error", "description": "Format tests and run mypy on lineage module"}
[tool_result] 1 file reformatted
sqlglot/lineage.py    | 109 +++++++++++++++++++++++++++++++++++++++++---------
 tests/test_lineage.py |  56 +++++++++++++++++++++++++-
 2 files changed, 144 insertions(+), 21 deletions(-)
Success: no issues found in 1 source file
head: illegal line count -- 0

thread 'main' (44143534) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
0
[tool_use Bash] {"command": "rm -f /tmp/orig_lineage_check.py && PY=<work>/env-sqlglot/bin/python; $PY -I -c \"\nfrom sqlglot.lineage import lineage\nprint(list(lineage(None, 'SELECT * FROM x', schema={'x': {'a': 'int'}})))\nprint({k: v.source.sql() for k, v in lineage(None, 'SELECT a, a + 1 AS b FROM x UNION ALL SELECT a, 2 FROM y', schema={'x': {'a': 'int'}, 'y': {'a': 'int'}}).items()})\nprint(lineage(None, 'SELECT a FROM x', schema={'x': {'a': 'int'}}).__class__)\n\"", "description": "Spot-check star and union behavior in dict mode"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY -I -c \"\nfrom sqlglot.lineage import lineage\nprint(list(lineage(None, 'SELECT * FROM x', schema={'x': {'a': 'int'}})))\nprint({k: v.source.sql() for k, v in lineage(None, 'SELECT a, a + 1 AS b FROM x UNION ALL SELECT a, 2 FROM y', schema={'x': {'a': 'int'}, 'y': {'a': 'int'}}).items()})\nprint(lineage(None, 'SELECT a FROM x', schema={'x': {'a': 'int'}}).__class__)\n\"", "description": "Spot-check star and union behavior in dict mode"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.lineage import lineage\nprint(list(lineage(None, 'SELECT * FROM x', schema={'x': {'a': 'int'}})))\nprint({k: v.source.sql() for k, v in lineage(None, 'SELECT a, a + 1 AS b FROM x UNION ALL SELECT a, 2 FROM y', schema={'x': {'a': 'int'}, 'y': {'a': 'int'}}).items()})\nprint(lineage(None, 'SELECT a FROM x', schema={'x': {'a': 'int'}}).__class__)\n\"", "description": "Spot-check star and union behavior in dict mode"}
[tool_result] ['a']
{'a': 'SELECT x.a AS a, x.a + 1 AS b FROM x AS x UNION ALL SELECT y.a AS a, 2 AS "2" FROM y AS y', 'b': 'SELECT x.a AS a, x.a + 1 AS b FROM x AS x UNION ALL SELECT y.a AS a, 2 AS "2" FROM y AS y'}
<class 'dict'>
[assistant] Both changes are in `sqlglot/lineage.py`, with tests in `tests/test_lineage.py`. The full suite passes (1099 passed), and ruff and mypy are clean on the touched files. I did not commit.

**What changed**

- **`column=None` returns a dict.** `lineage(None, sql, ...)` returns `{output_name: Node}` for every top-level select. The single-column form still returns a `Node`. Two `@t.overload` signatures distinguish the return types. `column` remains a required argument, so passing `None` is explicit.
- **`on_node` callback.** `lineage()` and `to_node()` take `on_node: Callable[[Node], object] | None
…[576 chars elided]…
e matches the single-column result.
- `test_lineage_on_node`: across a union, a derived table, and a CTE, every node in `walk()` is reported exactly once, and `downstream` is already complete when the callback runs.
- `test_lineage_payload`: payload set in the callback is visible afterward, and defaults to `{}`.

**Choices you may want to change**

- Dict keys are the top-level output names (`alias_or_name`). Duplicate output names collapse to one key, because the dict cannot hold both.
- In dict mode the walk shares one cache across columns, so common upstream nodes are built once and shared.
