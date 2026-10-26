"""Synthetic door and breaker monitor for the standalone panel demo."""

class EquipmentSensor:
    def __init__(self, random, panel):
        self.panel = panel
        self.random = random
        self.door_open = 0
        self.trip_count = 0
        self.confirmed_operations = 0

    def measure(self, elapsed_s):
        if self.door_open and self.random.random() < 0.02:
            self.door_open = 0
        elif not self.door_open and self.random.random() < 0.001:
            self.door_open = 1
        return {
            "door_open": self.door_open,
            "breaker_closed": 1,
            "trip_count": self.trip_count,
            "confirmed_operations": self.confirmed_operations,
        }
