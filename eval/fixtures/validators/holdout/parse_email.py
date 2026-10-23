import sys

from _common import check

GOOD = [("Ada@Example.com", "ada@example.com"), (" bob@mail.co.uk ", "bob@mail.co.uk")]
BAD = ["", "no-at.example.com", "a@@b.com", "@example.com", "a@example", "a b@example.com", "a@.com", "a@example.", None, 5]

sys.exit(check("app.users", "parse_email", GOOD, BAD))
