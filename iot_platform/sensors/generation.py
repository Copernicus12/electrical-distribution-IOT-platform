"""Simple day-shaped PV model for the standalone panel demo."""

import math


class GenerationSensor:
    def __init__(self, random, panel):
        self.random = random
        self.panel = panel
        self.energy_kwh = 0.0
        self.elapsed_s = 0.0

    def measure(self, elapsed_s):
        hour = (self.elapsed_s / 3600) % 24
        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        power_w = 7500 * daylight * self.random.uniform(0.9, 1.0)
        self.energy_kwh += power_w * elapsed_s / 3_600_000
        self.elapsed_s += elapsed_s
        return {"pv_power_w": power_w, "energy_kwh": self.energy_kwh}
