# Calibration deviations

Initial launch was refused by a CLI session limit, with zero tokens and $0
in the raw result. Reset notice: 2:10pm Africa/Johannesburg on 2026-10-27.
The old runner missed the notice because it checked only rollout trajectories,
which do not exist when the pipeline aborts before writing outcome.json. It
incorrectly wrote a zero-execution failed row and exited 0. That row, its logs,
and the captured raw stream are preserved under invalid-limit-1 and excluded
from calibration analysis. Progress was repaired to task 1, since no task ran.

A second defect was found before resuming: render_config emits an empty
adapter_args table, dropping the attempted CLI budget. The evaluation writer
now persists adapter arguments and verifies the round trip; a regression test
checks the actual adapter command. The limit guard now checks lithify.log;
a regression test uses the observed notice without any outcome directory.
The rejected launch consumed no tokens or dollars, so the missing flag caused
no spend. Both defects were fixed before resuming under the standing CLI-limit
rule. No completed task is repeated. Automatic resumes are counted by UTC day
in AUTO_RESUMES.json, with a maximum of three per run per day.
