"""Block archiving unredacted text or compressed session evidence (zero tokens)."""

import sys
from pathlib import Path

from evalkit import require_redacted

for argument in sys.argv[1:] or ["eval/results"]:
    require_redacted(Path(argument))
print("Evidence leak scan passed")
