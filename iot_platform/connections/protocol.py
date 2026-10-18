"""Version 1 newline-delimited JSON telemetry contract."""

import json
import math
from datetime import datetime, timezone

MAX_MESSAGE_BYTES = 64 * 1024  # JSON payload, excluding the newline
PANELS = ("T01", "T02", "T03", "T04")
FIELDS = {
    "electrical": ("voltage_v", "current_a", "active_power_w", "energy_kwh", "frequency_hz", "power_factor"),
    "connections": ("temperature_c",),
    "ambient": ("temperature_c", "humidity_pct"),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate(message):
    """Validate shape and types, without imposing nominal measurement limits."""
    if not isinstance(message, dict):
        raise ValueError("message must be an object")
    version = message.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("unsupported schema_version")
    panel = message.get("panel_id")
    kind = message.get("sensor_type")
    if panel not in PANELS or not isinstance(kind, str) or kind not in FIELDS:
        raise ValueError("unknown panel_id or sensor_type")
    if message.get("sensor_id") != "{}-{}".format(panel, kind):
        raise ValueError("sensor_id does not match panel and type")
    sequence = message.get("sequence")
    if type(sequence) is not int or sequence < 0:
        raise ValueError("sequence must be a nonnegative integer")
    stamp = message.get("timestamp")
    if not isinstance(stamp, str):
        raise ValueError("timestamp must be an ISO 8601 UTC string")
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError("timestamp must use UTC")
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid UTC timestamp") from exc
    values = message.get("measurements")
    if not isinstance(values, dict) or set(values) != set(FIELDS[kind]):
        raise ValueError("unexpected measurement fields")
    for value in values.values():
        if type(value) not in (int, float):
            raise ValueError("measurements must be numeric and finite")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError("measurements must be numeric and finite")
    return message


def encode(message):
    validate(message)
    return (json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
