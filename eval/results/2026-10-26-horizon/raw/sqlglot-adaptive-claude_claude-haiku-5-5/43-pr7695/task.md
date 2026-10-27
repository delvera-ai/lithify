Exasol dialect: transpiling MySQL/MariaDB `SHOW DATABASES` (and its alias `SHOW SCHEMAS`) to Exasol currently emits an unsupported, empty statement. Exasol lists schemas through its `SYS.EXA_SCHEMAS` metadata table, so generate:

```
SHOW DATABASES  ->  SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS
SHOW SCHEMAS    ->  SELECT SCHEMA_NAME FROM SYS.EXA_SCHEMAS
```

(`SHOW TABLES` is already transpiled to Exasol.)
