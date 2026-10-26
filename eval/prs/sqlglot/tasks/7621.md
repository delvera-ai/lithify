Parser: names that are also no-parenthesis functions (e.g. `CURRENT_DATE`, `CURRENT_USER`, `SYSDATE`) are turned into function calls when they appear after a dot in a column reference:

```
SELECT mytable.current_user FROM mytable
-> SELECT mytable.CURRENT_USER() FROM mytable
```

After a dot they are identifiers (column names) and must round-trip as such.
