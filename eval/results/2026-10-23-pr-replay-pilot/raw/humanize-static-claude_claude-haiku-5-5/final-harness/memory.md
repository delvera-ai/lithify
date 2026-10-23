- The project's checks run with `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Imports in `src/humanize/`: a stdlib module used only inside function bodies is imported inside
  the function that uses it (`import math` in `time.py::precisedelta` and in each `number.py`
  function; `import datetime as dt` in each `time.py` function). A top-level one is named in that
  module's `__lazy_modules__` set (`filesize.py`: `"math"`; `number.py`: `"bisect"`). Never add a
  plain top-level `import math` to `time.py` or `number.py`.
- Tests: `@pytest.mark.parametrize` names are one csv string, `"test_input, expected"`, never a
  tuple `("test_input", "expected")` (`[tool.ruff]` `parametrize-names-type = "csv"`, rule `PT006`).
