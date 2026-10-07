"""Count each start in a file, then read requests and never answer them."""

from __future__ import annotations

import sys
from pathlib import Path

with Path(sys.argv[1]).open("a", encoding="utf-8") as starts:
    starts.write("started\n")
for _line in sys.stdin:
    pass
