from app.storage.alert_deduplicator import AlertDeduplicator


def test_alert_cooldown_logic() -> None:
    dedup = AlertDeduplicator(cooldown_seconds=300.0)
    assert dedup.should_send("dog-rise", 10.0) is True
    assert dedup.should_send("dog-rise", 100.0) is False
    assert dedup.should_send("dog-rise", 311.0) is True
