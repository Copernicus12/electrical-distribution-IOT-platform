"""Temperature of electrical connections; unrelated to the TCP connection."""

from .base import BaseSensor


class ConnectionTemperatureSensor(BaseSensor):
    def __init__(self, random, panel):
        # Start at 35 °C, vary by ±0.15 °C per sample, remain within 20–50 °C.
        # This is synthetic variation, not a physical thermal calculation.
        super().__init__(random, {"temperature_c": 35.0}, {"temperature_c": (20, 50, 0.15)})
