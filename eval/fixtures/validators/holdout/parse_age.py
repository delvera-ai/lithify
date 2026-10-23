import sys

from _common import check

GOOD = [(0, 0), (42, 42), (150, 150), ("37", 37), (" 8 ", 8)]
BAD = [-1, 151, "abc", "", "4.5", "-3", 3.5, None, True]

sys.exit(check("app.users", "parse_age", GOOD, BAD))
