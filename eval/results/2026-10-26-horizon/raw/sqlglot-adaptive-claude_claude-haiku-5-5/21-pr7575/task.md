Lineage: extend `sqlglot.lineage.lineage()`:

1. Passing `column=None` returns a dict mapping every top-level output column name to its lineage `Node`. The single-column form keeps returning a `Node`, and typing overloads distinguish the two.
2. An `on_node` callback, called for every `Node` created during the walk (after its downstream nodes are populated), plus a caller-managed `Node.payload` dict, so callers can attach per-node data while the graph is built.

(Stated requirement: the names are `column=None`, `on_node` and `Node.payload`.)
