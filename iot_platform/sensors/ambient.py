"""Synthetic cabinet temperature and relative humidity sensor."""

from .base import BaseSensor


class AmbientSensor(BaseSensor):
    def __init__(self, random, panel):
        # Temperature starts at 23 °C and varies by ±0.1 °C in [18, 30].
        # Relative humidity starts at 45% and varies by ±0.3 points in [30, 65].
        super().__init__(random, {"temperature_c": 23.0, "humidity_pct": 45.0}, {
            "temperature_c": (18, 30, 0.1),
            "humidity_pct": (30, 65, 0.3),
        })
