import sys

from _common import check

GOOD = [(0, 0.0), (100, 100.0), (12.5, 12.5), ("12.5", 12.5), ("40%", 40.0)]
BAD = [-0.5, 100.5, "abc", "", "%", "12%%", float("nan"), True, None]

sys.exit(check("app.orders", "parse_discount", GOOD, BAD))
