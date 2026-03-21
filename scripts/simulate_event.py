from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sample = {
    "event_id": "manual-sample-1",
    "note": "Use this file as a template for manual review annotations.",
    "label": "failed_get_up_attempt",
}

out = Path("exports/manual_review_sample.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(sample, indent=2), encoding="utf-8")
print(f"wrote {out}")
