"""Exit at the first start, then answer every request with one board."""

from __future__ import annotations

import json
import sys
from pathlib import Path

flag = Path(sys.argv[1])
if not flag.exists():
    flag.write_text("started", encoding="utf-8")
    raise SystemExit(3)
for line in sys.stdin:
    request = json.loads(line)
    print(
        json.dumps(
            {
                "id": request["id"],
                "boards": [
                    {"name": "", "light": "<svg/>", "dark": "<svg/>", "label": ""}
                ],
            }
        ),
        flush=True,
    )
