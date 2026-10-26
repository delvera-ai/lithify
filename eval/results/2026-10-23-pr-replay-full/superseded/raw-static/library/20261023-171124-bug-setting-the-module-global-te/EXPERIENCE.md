# 20261023-171124-bug-setting-the-module-global-te

**Task:** Bug: setting the module global `tenacity.tornado = None` (the usual way a test suite exercises the non-tornado path without uninstalling tornado) makes any subsequent `@tenacity.retry` decoration raise `AttributeError: 'NoneType' object has no attribute 'gen'`. Whether tornado is available must be read from the live module global at decoration time, so decorating works after the global is set to `None`.

## Transferable lesson

NO_ENTRY — the record showed no reusable execution contrast.

## Edit attribution

| component | verdict | change | observed |
|---|---|---|---|
| — | — | no harness edits were proposed | — |
