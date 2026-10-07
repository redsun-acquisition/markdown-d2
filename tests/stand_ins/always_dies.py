"""Exit at once with a message on standard error."""

from __future__ import annotations

import sys

print("render process exploded", file=sys.stderr, flush=True)
raise SystemExit(3)
