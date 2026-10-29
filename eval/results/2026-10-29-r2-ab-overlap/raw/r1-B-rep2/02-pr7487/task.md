ClickHouse dialect: the parametric aggregate syntax of `groupConcat` fails to parse (reported from Superset):

```sql
SELECT groupConcat(', ')(part_name) AS concatenated FROM system.parts
```

raises `ParseError: Invalid expression`. Support `groupConcat`'s parametric form (separator as the parameter, column as the argument) so it parses and round-trips in ClickHouse.
