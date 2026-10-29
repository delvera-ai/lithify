StarRocks dialect: several functions are generated in forms StarRocks rejects (inherited from MySQL or the base dialect). StarRocks needs:

- `MIN_BY` / `MAX_BY` (it has no `ARG_MIN` / `ARG_MAX`), including the window form;
- `MAP(k1, v1, k2, v2, ...)`: its variadic map constructor, for maps read from other dialects too (e.g. the two-array form from DuckDB, Presto or Snowflake);
- `ARRAY_CONTAINS_ALL(a, b)` rather than the Postgres `@>` operator;
- a `TRIM` syntax StarRocks accepts.

Generate StarRocks-native syntax for these, and parse StarRocks' own forms back.
