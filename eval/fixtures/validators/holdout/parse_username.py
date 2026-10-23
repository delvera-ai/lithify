import sys

from _common import check

GOOD = [("ada", "ada"), (" ada_99 ", "ada_99"), ("a" * 20, "a" * 20)]
BAD = ["ab", "a" * 21, "9lives", "Ada", "ada-lovelace", "_ada", "", None, 123]

sys.exit(check("app.users", "parse_username", GOOD, BAD))
