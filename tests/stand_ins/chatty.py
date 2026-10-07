"""Print a log line and a reply to another request before each real reply."""

from __future__ import annotations

import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    print("D2 says hello", flush=True)
    print(
        json.dumps({"id": -1, "boards": [{"name": "stale", "light": "", "dark": ""}]}),
        flush=True,
    )
    print(
        json.dumps(
            {
                "id": request["id"],
                "boards": [{"name": "", "light": "<svg/>", "dark": "<svg/>"}],
            }
        ),
        flush=True,
    )
