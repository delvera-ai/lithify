"""Detached supervisor for the approved A launcher; never restarts a failed child."""

from __future__ import annotations

import fcntl
import json
import os
import signal
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "eval"))
    from evalkit import redact

    arguments = sys.argv[1:]
    work = Path(arguments[arguments.index("--work") + 1]).resolve()
    out = Path(arguments[arguments.index("--out") + 1]).resolve()
    status_path = out / "SUPERVISOR.json"
    command = [sys.executable, str(root / "eval/round2/run_a_replicates.py"), *arguments]
    state = {"started_at": datetime.now(UTC).isoformat(), "supervisor_pid": os.getpid(), "status": "starting"}

    def save() -> None:
        temporary = status_path.with_suffix(".tmp")
        temporary.write_text(redact(json.dumps(state, indent=2)) + "\n")
        temporary.replace(status_path)

    with (work / "A_SUPERVISOR.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if status_path.exists():
            raise RuntimeError("supervisor record already exists; inspect before an explicit recovery")
        save()
        child = None

        def stop(signum: int, _frame: object) -> None:
            state["signal"] = signum
            save()
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signum)

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            with (work / "A_SUPERVISOR.console.log").open("a") as log:
                child = subprocess.Popen(
                    command, cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True, close_fds=True
                )
                state.update(status="running", child_pid=child.pid)
                save()
                code = child.wait()
            state.update(status="completed" if code == 0 else "stopped; owner review", exit_code=code)
            return code
        except BaseException:
            state.update(status="supervisor exception; owner review", error=traceback.format_exc())
            raise
        finally:
            state["finished_at"] = datetime.now(UTC).isoformat()
            save()


if __name__ == "__main__":
    raise SystemExit(main())
