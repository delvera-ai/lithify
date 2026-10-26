GATES: FAIL — test=FAIL(1)

## test: `<work>/env-tenacity/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 1 (1.9s)
/env-tenacity/lib/python3.12/site-packages/_pytest/config/__init__.py", line 253, in _console_main
    code = _main(prog=_get_prog_name(sys.argv))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/_pytest/config/__init__.py", line 229, in _main
    ret: ExitCode | int = config.hook.pytest_cmdline_main(config=config)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/pluggy/_caller.py", line 197, in __call__
    return self._hookexec(
           ^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/pluggy/_manager.py", line 183, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/pluggy/_execution.py", line 195, in _multicall
    raise exception
  File "<work>/env-tenacity/lib/python3.12/site-packages/pluggy/_execution.py", line 147, in _multicall
    res = hook_impl.function(*args)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/_pytest/main.py", line 377, in pytest_cmdline_main
    return wrap_session(config, _main)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<work>/env-tenacity/lib/python3.12/site-packages/_pytest/main.py", line 362, in wrap_session
    os.chdir(session.startpath)
FileNotFoundError: [Errno 2] No such file or directory: '~/.cache/lithify/work/repo-b561bbaa0f70/20261023-155139-regression-since-8-4-2-composing/base-1'

