Postgres dialect: `CREATE TYPE` falls back to an unparsed command:

```python
from sqlglot import parse_one
parse_one("CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')", "postgres")
# '... contains unsupported syntax. Falling back to parsing as a Command.'
```

Parse `CREATE TYPE` statements into proper AST nodes, at least enum types (`AS ENUM (...)`) and composite types (`AS (attr type, ...)`), so they round-trip in Postgres.
