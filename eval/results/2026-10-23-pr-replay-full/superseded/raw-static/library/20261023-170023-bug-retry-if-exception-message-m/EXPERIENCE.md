# 20261023-170023-bug-retry-if-exception-message-m

**Task:** Bug: `retry_if_exception_message(message="")` raises `TypeError` ("missing 1 required argument 'message' or 'match'"), even though an empty string is a valid message to match (e.g. `str(RuntimeError()) == ""`). An empty `message` (or empty `match`) must be accepted and matched correctly; passing neither or both must still raise `TypeError`. The same applies to `retry_if_not_exception_message`.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
