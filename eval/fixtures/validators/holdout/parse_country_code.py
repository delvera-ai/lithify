import sys

from _common import check

GOOD = [("gb", "GB"), (" Us ", "US")]
BAD = ["G", "GBR", "G1", "", "ÉS", None, 44]

sys.exit(check("app.addresses", "parse_country_code", GOOD, BAD))
