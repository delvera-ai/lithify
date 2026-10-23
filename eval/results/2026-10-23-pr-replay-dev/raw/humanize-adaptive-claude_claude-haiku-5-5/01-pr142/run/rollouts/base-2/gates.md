GATES: FAIL — test=FAIL(1)

## test: `PYTHONPATH=src <work>/env-humanize/bin/python -m pytest -q -p no:cacheprovider --color=no` -> exit 1 (0.7s)
      ([1, False, False], "1 Byte"),
            ([3141592, False, False, "%.2f"], "3.14 MB"),
            ([3000, False, True, "%.3f"], "2.930K"),
            ([3000000000, False, True, "%.0f"], "3G"),
            ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
        ],
    )
    def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
>       assert humanize.naturalsize(*test_args) == expected
E       AssertionError: assert '3.0 RB' == '3000.0 YB'
E         
E         - 3000.0 YB
E         + 3.0 RB

tests/test_filesize.py:37: AssertionError
__________________ test_naturalsize[test_args19-2481.542 YiB] __________________

test_args = [3000000000000000000000000000, True, False, '%.3f']
expected = '2481.542 YiB'

    @pytest.mark.parametrize(
        "test_args, expected",
        [
            ([300], "300 Bytes"),
            ([3000], "3.0 kB"),
            ([3000000], "3.0 MB"),
            ([3000000000], "3.0 GB"),
            ([3000000000000], "3.0 TB"),
            ([300, True], "300 Bytes"),
            ([3000, True], "2.9 KiB"),
            ([3000000, True], "2.9 MiB"),
            ([300, False, True], "300B"),
            ([3000, False, True], "2.9K"),
            ([3000000, False, True], "2.9M"),
            ([1024, False, True], "1.0K"),
            ([10**26 * 30, False, True], "2481.5Y"),
            ([10**26 * 30, True], "2481.5 YiB"),
            ([10**26 * 30], "3000.0 YB"),
            ([1, False, False], "1 Byte"),
            ([3141592, False, False, "%.2f"], "3.14 MB"),
            ([3000, False, True, "%.3f"], "2.930K"),
            ([3000000000, False, True, "%.0f"], "3G"),
            ([10**26 * 30, True, False, "%.3f"], "2481.542 YiB"),
        ],
    )
    def test_naturalsize(test_args: list[int] | list[int | bool], expected: str) -> None:
>       assert humanize.naturalsize(*test_args) == expected
E       AssertionError: assert '2.423 RiB' == '2481.542 YiB'
E         
E         - 2481.542 YiB
E         + 2.423 RiB

tests/test_filesize.py:37: AssertionError
=========================== short test summary info ============================
FAILED tests/test_filesize.py::test_naturalsize[test_args12-2481.5Y] - Assert...
FAILED tests/test_filesize.py::test_naturalsize[test_args13-2481.5 YiB] - Ass...
FAILED tests/test_filesize.py::test_naturalsize[test_args14-3000.0 YB] - Asse...
FAILED tests/test_filesize.py::test_naturalsize[test_args19-2481.542 YiB] - A...
4 failed, 557 passed, 23 skipped in 0.51s

