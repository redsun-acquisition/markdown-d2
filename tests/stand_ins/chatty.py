"""Print a log line and a reply to another request before each real reply."""

from __future__ import annotations

import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    print("D2 says hello", flush=True)
    print(json.dumps({"id": -1, "boards": ["stale"]}), flush=True)
    print(json.dumps({"id": request["id"], "boards": [""]}), flush=True)
