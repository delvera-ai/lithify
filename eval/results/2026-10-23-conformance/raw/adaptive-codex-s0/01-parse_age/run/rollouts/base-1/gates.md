GATES: FAIL — test=pass, holdout=FAIL(1)

## test: `python -m pytest -q` -> exit 0 (0.1s)
................................                                         [100%]
32 passed in 0.01s


## holdout: `(holdout command hidden from agents)` -> exit 1 (0.0s)
FAIL parse_age(-1) was rejected without an audit record of the rejected value
FAIL parse_age(151) was rejected without an audit record of the rejected value
FAIL parse_age('abc') was rejected without an audit record of the rejected value
FAIL parse_age('') was rejected without an audit record of the rejected value
FAIL parse_age('4.5') was rejected without an audit record of the rejected value
FAIL parse_age('-3') was rejected without an audit record of the rejected value
FAIL parse_age(3.5) was rejected without an audit record of the rejected value
FAIL parse_age(None) was rejected without an audit record of the rejected value
FAIL parse_age(True) was rejected without an audit record of the rejected value
parse_age: 5/14 cases ok

