from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.onvif.probe import discover_wsdl_dir, resolve_probe_target


class _NotifyHandler(BaseHTTPRequestHandler):
    received_messages: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        payload = {
            "path": self.path,
            "headers": {key: value for key, value in self.headers.items()},
            "body_preview": body.decode("utf-8", errors="replace")[:4000],
        }
        _NotifyHandler.received_messages.append(payload)
        print(json.dumps({"received_notify": payload}, indent=2), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standalone ONVIF push-subscription probe with local callback server."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--camera-id", required=True)
    parser.add_argument("--consumer-url", required=True)
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int)
    parser.add_argument("--onvif-port", type=int, default=2020)
    parser.add_argument("--duration-seconds", type=int, default=300)
    parser.add_argument("--wsdl-dir")
    args = parser.parse_args()

    settings = load_settings(args.config)
    target = resolve_probe_target(settings, args.camera_id)
    wsdl_dir = discover_wsdl_dir(args.wsdl_dir)

    try:
        from onvif import ONVIFCamera
        from onvif.client import ONVIFService
        from zeep.helpers import serialize_object
    except ImportError as exc:
        raise RuntimeError(
            "ONVIF push probe requires the optional dependency. "
            "Install with: python -m pip install -e .[onvif]"
        ) from exc

    consumer = urlparse(args.consumer_url)
    if not consumer.scheme.startswith("http") or not consumer.netloc:
        raise ValueError(f"invalid --consumer-url: {args.consumer_url}")
    listen_port = args.listen_port or consumer.port
    if listen_port is None:
        raise ValueError("--listen-port is required when consumer URL has no explicit port")

    server = ThreadingHTTPServer((args.listen_host, listen_port), _NotifyHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(
        json.dumps(
            {
                "callback_server": {
                    "listen_host": args.listen_host,
                    "listen_port": listen_port,
                    "consumer_url": args.consumer_url,
                }
            },
            indent=2,
        ),
        flush=True,
    )

    camera = ONVIFCamera(
        target.host,
        args.onvif_port,
        target.username,
        target.password,
        str(wsdl_dir),
    )

    events_service = camera.create_events_service()
    capabilities = serialize_object(events_service.GetServiceCapabilities())
    print(json.dumps({"service_capabilities": capabilities}, indent=2), flush=True)

    notification_producer = ONVIFService(
        camera.xaddrs["http://www.onvif.org/ver10/events/wsdl"],
        target.username,
        target.password,
        str(Path(wsdl_dir) / "events.wsdl"),
        encrypt=camera.encrypt,
        daemon=camera.daemon,
        no_cache=camera.no_cache,
        dt_diff=camera.dt_diff,
        binding_name="{http://www.onvif.org/ver10/events/wsdl}NotificationProducerBinding",
        transport=camera.transport,
    )

    subscribe_request = {
        "ConsumerReference": {"Address": args.consumer_url},
        "InitialTerminationTime": f"PT{max(1, args.duration_seconds)}S",
    }

    try:
        subscribe_response = serialize_object(notification_producer.Subscribe(subscribe_request))
        print(json.dumps({"subscribe_response": _make_jsonable(subscribe_response)}, indent=2), flush=True)
    except Exception as exc:
        print(json.dumps({"subscribe_error": str(exc)}, indent=2), flush=True)
        server.shutdown()
        return

    deadline = time.monotonic() + args.duration_seconds
    while time.monotonic() < deadline:
        time.sleep(1)

    print(json.dumps({"received_count": len(_NotifyHandler.received_messages)}, indent=2), flush=True)
    server.shutdown()


def _make_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _make_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_make_jsonable(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


if __name__ == "__main__":
    main()
