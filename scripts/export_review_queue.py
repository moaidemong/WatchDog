from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

src = Path("review_queue")
dst = Path("exports/review_queue_export")
dst.mkdir(parents=True, exist_ok=True)
if src.exists():
    for file in src.glob("*.json"):
        shutil.copy2(file, dst / file.name)
print(f"exported review queue to {dst}")
