from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.onvif.events import decide_trigger, parse_notification_message, summarize_event
from app.onvif.probe import discover_wsdl_dir, resolve_probe_target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe ONVIF PullPoint events for a configured TAPO camera."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--camera-id", required=True)
    parser.add_argument("--onvif-port", type=int, default=2020)
    parser.add_argument("--duration-seconds", type=int, default=30)
    parser.add_argument("--pull-timeout-seconds", type=int, default=5)
    parser.add_argument("--message-limit", type=int, default=10)
    parser.add_argument("--wsdl-dir")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    settings = load_settings(args.config)
    target = resolve_probe_target(settings, args.camera_id)
    wsdl_dir = discover_wsdl_dir(args.wsdl_dir)

    try:
        from onvif import ONVIFCamera
        from zeep.helpers import serialize_object
    except ImportError as exc:
        raise RuntimeError(
            "ONVIF probe requires the optional dependency. "
            "Install with: python -m pip install -e .[onvif]"
        ) from exc

    camera = ONVIFCamera(
        target.host,
        args.onvif_port,
        target.username,
        target.password,
        str(wsdl_dir),
    )

    device_info = serialize_object(camera.devicemgmt.GetDeviceInformation())
    print(json.dumps({"camera_id": target.camera_id, "host": target.host, "device_info": device_info}, indent=2))

    events_service = camera.create_events_service()
    event_properties = serialize_object(events_service.GetEventProperties())
    print(
        json.dumps(
            {
                "topic_namespace_location": event_properties.get("TopicNamespaceLocation"),
                "fixed_topic_set": event_properties.get("FixedTopicSet"),
            },
            indent=2,
        )
    )

    subscription = events_service.CreatePullPointSubscription(
        {"InitialTerminationTime": f"PT{max(1, args.duration_seconds)}S"}
    )
    subscription_data = serialize_object(subscription)
    subscription_xaddr = _extract_subscription_xaddr(subscription_data)
    print(json.dumps({"subscription_xaddr": subscription_xaddr}, indent=2))

    camera.xaddrs["http://www.onvif.org/ver10/events/wsdl/PullPointSubscription"] = subscription_xaddr
    pullpoint_service = camera.create_pullpoint_service()

    deadline = time.monotonic() + args.duration_seconds
    total_messages = 0
    topic_counts: Counter[str] = Counter()
    trigger_counts: Counter[str] = Counter()
    while time.monotonic() < deadline:
        remaining = max(1, min(args.pull_timeout_seconds, int(deadline - time.monotonic())))
        response = pullpoint_service.PullMessages(
            {"Timeout": f"PT{remaining}S", "MessageLimit": args.message_limit}
        )
        serialized = serialize_object(response)
        messages = serialized.get("NotificationMessage") or []
        for message in messages:
            total_messages += 1
            event = parse_notification_message(message)
            topic_counts[event.topic] += 1
            decision = decide_trigger(event)
            if decision.trigger_key:
                trigger_counts[decision.trigger_key] += 1
            if not args.quiet:
                print(
                    json.dumps(
                        {
                            "event": summarize_event(event),
                            "trigger": {
                                "should_trigger": decision.should_trigger,
                                "trigger_key": decision.trigger_key,
                                "reason": decision.reason,
                            },
                        },
                        indent=2,
                    )
                )

    print(
        json.dumps(
            {
                "total_messages": total_messages,
                "topic_counts": dict(topic_counts),
                "trigger_counts": dict(trigger_counts),
            },
            indent=2,
        )
    )

    try:
        pullpoint_service.Unsubscribe()
    except Exception:
        pass


def _extract_subscription_xaddr(subscription_data: dict[str, Any]) -> str:
    reference = subscription_data.get("SubscriptionReference") or {}
    address = reference.get("Address")
    if isinstance(address, dict):
        address = address.get("_value_1")
    if isinstance(address, list):
        address = address[0] if address else None
    if not address:
        raise RuntimeError(f"unable to extract PullPoint subscription address: {subscription_data}")
    return str(address)

if __name__ == "__main__":
    main()
