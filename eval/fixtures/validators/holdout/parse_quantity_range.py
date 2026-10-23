import sys

from _common import check

GOOD = [("2-5", (2, 5)), (" 1 - 999 ", (1, 999)), ("7-7", (7, 7))]
BAD = ["5-2", "0-3", "1-1000", "3", "a-b", "1-2-3", "", None, (1, 2)]

sys.exit(check("app.orders", "parse_quantity_range", GOOD, BAD))
