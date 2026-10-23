import sys

from _common import check

GOOD = [("12345", "12345"), (" 12345-6789 ", "12345-6789")]
BAD = ["1234", "123456", "12345-678", "12345 6789", "ABCDE", "", None, 12345]

sys.exit(check("app.addresses", "parse_postcode", GOOD, BAD))
