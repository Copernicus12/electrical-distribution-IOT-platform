"""Fixed inputs: unit tests do not depend on the live sensor generator."""


def ambient_message(panel="T01", sequence=0):
    return {
        "schema_version": 1,
        "panel_id": panel,
        "sensor_id": panel + "-ambient",
        "sensor_type": "ambient",
        "timestamp": "2026-10-18T10:00:00Z",
        "sequence": sequence,
        "measurements": {"temperature_c": 23.123456, "humidity_pct": 45.0},
    }


def ambient_record(panel="T01", sequence=0):
    return dict(ambient_message(panel, sequence), received_at="2026-10-18T10:00:01Z")
