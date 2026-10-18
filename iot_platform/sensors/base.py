"""Shared gradual variation used by the synthetic sensor models."""


class BaseSensor:
    def __init__(self, random, values, limits):
        self.random = random
        self.values = values
        self.limits = limits

    def measure(self, elapsed_s):
        """Add uniform noise, clamp to nominal bounds and round to 4 decimals."""
        for name, value in self.values.items():
            low, high, step = self.limits[name]
            self.values[name] = round(max(low, min(high, value + self.random.uniform(-step, step))), 4)
        return dict(self.values)
