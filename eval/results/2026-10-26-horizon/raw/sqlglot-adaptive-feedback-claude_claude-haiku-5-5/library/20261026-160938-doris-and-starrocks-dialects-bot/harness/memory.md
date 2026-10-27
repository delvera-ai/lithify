- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 tests) takes 60–80 s when it runs alone. The slowest test is
  `tests/test_executor.py::TestExecutor::test_execute_tpcds`; with several pytest runs competing
  for CPU it sits there for minutes and looks hung, but it is only slow. Run the dialect's own
  test file first (well under a second), then the full suite once.
