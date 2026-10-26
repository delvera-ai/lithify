Postgres dialect: support the PostGIS 3D distance operator `<<->>` (e.g. `SELECT a <<->> b FROM t`), so it tokenizes, parses as a binary operator and generates back as `<<->>`.
