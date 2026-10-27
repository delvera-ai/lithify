Optimizer: `canonicalize` crashes when a `DATEDIFF` argument has no inferred type:

```python
from sqlglot import parse_one
from sqlglot.optimizer.canonicalize import canonicalize
canonicalize(parse_one("SELECT DATEDIFF(a, b) FROM t"))
# AttributeError: 'NoneType' object has no attribute 'this'
```

Arguments with unknown type must be left alone instead of crashing, like the other date-coercion helpers do.
