"""Synthetic three-phase electrical analyzer: voltage, current, power and energy."""

from .base import BaseSensor
from ..connections.protocol import PANELS


class ElectricalSensor(BaseSensor):
    def __init__(self, random, panel):
        super().__init__(random, {
            "voltage_v": 230.0,
            "current_a": 12.0 + PANELS.index(panel),
            "frequency_hz": 50.0,
            "power_factor": 0.95,
        }, {
            "voltage_v": (220, 240, 0.5),
            "current_a": (5, 25, 0.3),
            "frequency_hz": (49.9, 50.1, 0.01),
            "power_factor": (0.9, 0.99, 0.002),
        })
        self.energy_kwh = 0.0

    def measure(self, elapsed_s):
        values = super().measure(elapsed_s)
        # Balanced three-phase model: U is phase-to-neutral, I is per phase.
        # Total active power [W] = 3 × U [V] × I [A] × power factor.
        power_w = 3 * values["voltage_v"] * values["current_a"] * values["power_factor"]
        # Integrate sampled power over elapsed seconds; 1 kWh = 3,600,000 W·s.
        self.energy_kwh += power_w * elapsed_s / 3_600_000
        values.update(active_power_w=power_w, energy_kwh=self.energy_kwh)
        return values
