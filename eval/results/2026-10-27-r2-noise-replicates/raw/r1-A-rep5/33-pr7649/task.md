T-SQL dialect: support the `FOR JSON` query modifier (like the existing `FOR XML` support):

```
FOR JSON { AUTO | PATH } [, ROOT [('name')]] [, INCLUDE_NULL_VALUES] [, WITHOUT_ARRAY_WRAPPER]
```

It should parse and round-trip in T-SQL. Other dialects should emit an unsupported-option warning and drop the clause, as they do for `FOR XML`.
