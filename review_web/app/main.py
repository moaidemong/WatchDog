from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from review_web.app.db import connect, initialize_database
from review_web.app.services import (
    bootstrap_or_sync_from_watchdog,
    export_db_to_manifest,
    manifest_path_from_config,
    media_path_for_event,
    query_reviews,
    update_review,
)
from review_web.app.translations import REVIEW_LABEL_OPTIONS, REVIEW_STATUS_OPTIONS, TEXT_TRANSLATIONS


WATCHDOG_ROOT = Path(os.getenv("WATCHDOG_ROOT", "/home/moai/Workspace/Codex/WatchDog")).resolve()
CONFIG_PATH = Path(
    os.getenv("WATCHDOG_CONFIG", str(WATCHDOG_ROOT / "configs" / "app.tapo.multi.example.yaml"))
).resolve()
DB_PATH = Path(
    os.getenv("REVIEW_WEB_DB_PATH", str(WATCHDOG_ROOT / "review_web" / "data" / "review_web.sqlite3"))
).resolve()

initialize_database(DB_PATH)
with connect(DB_PATH) as conn:
    bootstrap_or_sync_from_watchdog(conn, watchdog_root=WATCHDOG_ROOT, config_path=CONFIG_PATH)

app = FastAPI(title="WatchDog Review Web", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(WATCHDOG_ROOT / "review_web" / "app" / "static")), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WATCHDOG_ROOT / "review_web" / "app" / "index.html").read_text(encoding="utf-8")


@app.get("/view/clip/{event_id}", response_class=HTMLResponse)
def clip_view(event_id: str, request: Request) -> str:
    return_url = request.query_params.get("return") or "/"
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Clip {event_id}</title>
    <style>
      body {{ margin: 0; font-family: "Noto Sans KR", sans-serif; background: #111827; color: #f8fafc; }}
      main {{ padding: 20px; }}
      video {{ width: 100%; max-width: 1100px; height: auto; display: block; background: #000; }}
      a {{ color: #93c5fd; }}
    </style>
  </head>
  <body>
    <main>
      <p><a href="{return_url}">리뷰 목록으로 돌아가기</a></p>
      <h1>{event_id}</h1>
      <video controls autoplay preload="metadata">
        <source src="/media/clip/{event_id}" type="video/mp4" />
      </video>
    </main>
  </body>
</html>"""


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "review_status_options": REVIEW_STATUS_OPTIONS,
        "review_label_options": REVIEW_LABEL_OPTIONS,
        "translations": TEXT_TRANSLATIONS,
    }


@app.post("/api/sync")
def sync_reviews() -> dict[str, Any]:
    with connect(DB_PATH) as conn:
        inserted = bootstrap_or_sync_from_watchdog(conn, watchdog_root=WATCHDOG_ROOT, config_path=CONFIG_PATH)
        export_db_to_manifest(conn, manifest_path_from_config(WATCHDOG_ROOT, CONFIG_PATH))
    return {"inserted": inserted}


@app.get("/api/reviews")
def list_reviews(
    offset: int = 0,
    limit: int = 100,
    camera_id: str | None = None,
    review_status: str | None = None,
    review_label: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    limit = max(1, min(limit, 500))
    with connect(DB_PATH) as conn:
        total, rows = query_reviews(
            conn,
            offset=offset,
            limit=limit,
            camera_id=camera_id,
            review_status=review_status,
            review_label=review_label,
            q=q,
        )
    return {"total": total, "items": rows}


@app.patch("/api/reviews/{event_id}")
def patch_review(event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    version = int(payload.get("version", 0))
    review_status = str(payload.get("review_status", "pending"))
    review_label = str(payload.get("review_label", ""))
    review_notes = str(payload.get("review_notes", ""))

    with connect(DB_PATH) as conn:
        row = update_review(
            conn,
            event_id=event_id,
            version=version,
            review_status=review_status,
            review_label=review_label,
            review_notes=review_notes,
        )
        if row is None:
            raise HTTPException(status_code=409, detail="row was updated by another user")
        export_db_to_manifest(conn, manifest_path_from_config(WATCHDOG_ROOT, CONFIG_PATH))
    return {"item": row}


@app.get("/media/{kind}/{event_id}")
def media(kind: str, event_id: str):
    with connect(DB_PATH) as conn:
        path = media_path_for_event(conn, event_id=event_id, kind=kind, watchdog_root=WATCHDOG_ROOT)
    if path is None:
        raise HTTPException(status_code=404, detail="media not found")
    media_type = None
    if kind == "snapshot":
        media_type = "image/jpeg"
    elif kind == "clip":
        media_type = "video/mp4"
    return FileResponse(path, media_type=media_type)
