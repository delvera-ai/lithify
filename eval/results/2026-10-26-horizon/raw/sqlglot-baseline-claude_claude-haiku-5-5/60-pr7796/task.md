Snowflake dialect: Snowflake can invoke a function under a dynamically resolved name, but sqlglot raises a `ParseError` on the argument list after `IDENTIFIER(...)`:

```sql
SET fn = 'add_one';
SELECT IDENTIFIER($fn)(41);
SELECT IDENTIFIER('my_func')(1, 2);
SELECT IDENTIFIER($fn)();
```

```
ParseError: Required keyword: 'expressions' missing for Aliases
```

Support dynamic function invocation through `IDENTIFIER()` (with zero or more arguments), so these parse and round-trip in Snowflake.
