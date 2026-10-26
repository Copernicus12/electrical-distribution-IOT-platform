"""Nominal-range and sequence checks that preserve original measurements."""

RANGES = {
    "electrical": {
        "voltage_v": (207, 253), "current_a": (0, 50), "active_power_w": (-40_000, 40_000),
        "frequency_hz": (49.5, 50.5), "power_factor": (0, 1), "energy_kwh": (0, None),
    },
    "connections": {"temperature_c": (-20, 80)},
    "ambient": {"temperature_c": (-20, 70), "humidity_pct": (0, 100)},
    "equipment": {"door_open": (0, 1), "breaker_closed": (0, 1),
                  "trip_count": (0, None), "confirmed_operations": (0, None)},
    "heating": {"room_temperature_c": (-20, 50), "heating_demand": (0, 30),
                "heater_on": (0, 30), "active_power_w": (0, 60_000)},
    "generation": {"pv_power_w": (0, 30_000), "energy_kwh": (0, None)},
}


def detect_anomalies(message, previous=None):
    anomalies = []
    kind = message["sensor_type"]
    for field, value in message["measurements"].items():
        limits = RANGES.get(kind, {}).get(field)
        if limits is None:
            continue
        low, high = limits
        if value < low or (high is not None and value > high):
            anomalies.append({
                "code": "out_of_nominal_range",
                "field": field,
                "value": value,
                "minimum": low,
                "maximum": high,
            })

    if previous is not None:
        if message["sequence"] <= previous["sequence"]:
            anomalies.append({"code": "duplicate_or_replayed_sequence", "sequence": message["sequence"]})
        elif message["sequence"] > previous["sequence"] + 1:
            anomalies.append({
                "code": "sequence_gap",
                "expected": previous["sequence"] + 1,
                "received": message["sequence"],
            })
    return anomalies
