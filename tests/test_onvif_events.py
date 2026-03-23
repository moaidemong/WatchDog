from app.onvif.events import decide_trigger, parse_notification_message, summarize_event


def test_parse_notification_message_extracts_pet_event() -> None:
    message = {
        "Topic": {
            "_value_1": "tns1:RuleEngine/TPSmartEventDetector/TPSmartEvent",
        },
        "Message": {
            "_value_1": (
                '<ns0:Message xmlns:ns0="http://www.onvif.org/ver10/schema" '
                'PropertyOperation="Initialized" UtcTime="2026-03-23T22:17:11Z">'
                "<ns0:Source>"
                '<ns0:SimpleItem Value="MyTPSmartEventDetectorRule" Name="Rule" />'
                "</ns0:Source>"
                "<ns0:Data>"
                '<ns0:SimpleItem Value="true" Name="IsPet" />'
                "</ns0:Data>"
                "</ns0:Message>"
            )
        },
    }

    event = parse_notification_message(message)

    assert event.topic == "tns1:RuleEngine/TPSmartEventDetector/TPSmartEvent"
    assert event.property_operation == "Initialized"
    assert event.source["Rule"] == "MyTPSmartEventDetectorRule"
    assert event.data["IsPet"] == "true"
    assert summarize_event(event)["utc_time"] == "2026-03-23T22:17:11+00:00"


def test_decide_trigger_prefers_pet_and_accepts_motion() -> None:
    pet_event = parse_notification_message(
        {
            "Topic": {"_value_1": "tns1:RuleEngine/TPSmartEventDetector/TPSmartEvent"},
            "Message": {
                "_value_1": (
                    '<ns0:Message xmlns:ns0="http://www.onvif.org/ver10/schema">'
                    "<ns0:Data>"
                    '<ns0:SimpleItem Value="true" Name="IsPet" />'
                    "</ns0:Data>"
                    "</ns0:Message>"
                )
            },
        }
    )
    motion_event = parse_notification_message(
        {
            "Topic": {"_value_1": "tns1:RuleEngine/CellMotionDetector/Motion"},
            "Message": {
                "_value_1": (
                    '<ns0:Message xmlns:ns0="http://www.onvif.org/ver10/schema">'
                    "<ns0:Data>"
                    '<ns0:SimpleItem Value="true" Name="IsMotion" />'
                    "</ns0:Data>"
                    "</ns0:Message>"
                )
            },
        }
    )
    false_event = parse_notification_message(
        {
            "Topic": {"_value_1": "tns1:RuleEngine/CellMotionDetector/Motion"},
            "Message": {
                "_value_1": (
                    '<ns0:Message xmlns:ns0="http://www.onvif.org/ver10/schema">'
                    "<ns0:Data>"
                    '<ns0:SimpleItem Value="false" Name="IsMotion" />'
                    "</ns0:Data>"
                    "</ns0:Message>"
                )
            },
        }
    )

    assert decide_trigger(pet_event).trigger_key == "pet"
    assert decide_trigger(motion_event).trigger_key == "motion"
    assert decide_trigger(false_event).should_trigger is False


def test_parse_notification_message_accepts_dict_style_message_payload() -> None:
    message = {
        "Topic": {"_value_1": "tns1:RuleEngine/CellMotionDetector/Motion"},
        "Message": {
            "UtcTime": "2026-03-23T22:17:12Z",
            "PropertyOperation": "Initialized",
            "Source": {
                "SimpleItem": {
                    "Name": "Rule",
                    "Value": "MyMotionDetectorRule",
                }
            },
            "Data": {
                "SimpleItem": [
                    {
                        "Name": "IsMotion",
                        "Value": "true",
                    }
                ]
            },
        },
    }

    event = parse_notification_message(message)

    assert event.property_operation == "Initialized"
    assert event.source["Rule"] == "MyMotionDetectorRule"
    assert event.data["IsMotion"] == "true"


def test_parse_notification_message_accepts_element_payload() -> None:
    from xml.etree import ElementTree

    xml = (
        '<ns0:Message xmlns:ns0="http://www.onvif.org/ver10/schema" '
        'PropertyOperation="Initialized" UtcTime="2026-03-23T22:17:12Z">'
        "<ns0:Source>"
        '<ns0:SimpleItem Value="MyMotionDetectorRule" Name="Rule" />'
        "</ns0:Source>"
        "<ns0:Data>"
        '<ns0:SimpleItem Value="true" Name="IsMotion" />'
        "</ns0:Data>"
        "</ns0:Message>"
    )
    message = {
        "Topic": {"_value_1": "tns1:RuleEngine/CellMotionDetector/Motion"},
        "Message": {
            "_value_1": ElementTree.fromstring(xml),
        },
    }

    event = parse_notification_message(message)

    assert event.property_operation == "Initialized"
    assert event.source["Rule"] == "MyMotionDetectorRule"
    assert event.data["IsMotion"] == "true"
