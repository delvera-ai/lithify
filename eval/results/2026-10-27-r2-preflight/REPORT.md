# Zero-token horizon oracle preflight

2026-10-27. All 60 frozen horizon tasks (#7492 through #7796 in the
original merge order) passed all required checks. No task was fixed or excluded.

| check | result |
|---|---:|
| hidden tests at base | 60/60 fail (pytest exit 1) |
| hidden tests at merge | 60/60 pass (exit 0) |
| full repository test command at merge | 60/60 pass (exit 0) |
| agent tokens / cost | 0 / $0 |

Evidence: oracle.csv, per-task JSON records, and logs/<PR>/ for all three
checks. Base and merge hashes match eval/round2/INPUT_MANIFEST.json. Hidden
files were re-extracted deterministically from the frozen merge commits.

Commands use the absolute env-sqlglot/bin/python (Python 3.12.13), as
configured by eval/repos.py, plus its bin directory on PATH for test_lazy_load's
internal python subprocess. The runner uses project-venv Python 3.14.4.
A version stub is written by the existing prepare_checkout helper. The suite
command is the original pytest -q -p no:cacheprovider --color=no command.
Three isolated clones ran in parallel; each task's checks were sequential.
Reproduce with eval/round2/oracle_preflight.py. No task texts or tests changed.

This establishes that the restored oracle environment works; it measures no
agent capability. Round-2 cumulative recorded spend remains $3.6267.
