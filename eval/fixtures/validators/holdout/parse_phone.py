import sys

from _common import check

GOOD = [("555-1234", "5551234"), ("+44 (20) 7946 0958", "+442079460958"), ("123456789012345", "123456789012345")]
BAD = ["123456", "1234567890123456", "555-CALL-NOW", "", "++4412345678", None, 5551234]

sys.exit(check("app.users", "parse_phone", GOOD, BAD))
