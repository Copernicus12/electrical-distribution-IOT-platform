"""Simple independent thermostat model for the standalone panel demo."""

class HeatingSensor:
    def __init__(self, random, panel):
        self.random = random
        self.temperature_c = 20.5
        self.heater_on = False

    def measure(self, elapsed_s):
        self.temperature_c += self.random.uniform(-0.03, 0.03)
        if self.temperature_c < 19.5:
            self.heater_on = True
        elif self.temperature_c > 21.5:
            self.heater_on = False
        power_w = 1500.0 if self.heater_on else 0.0
        if self.heater_on:
            self.temperature_c += min(0.02, max(0.0, elapsed_s) * 0.0002)
        return {
            "room_temperature_c": round(self.temperature_c, 3),
            "heating_demand": int(self.temperature_c < 20.5),
            "heater_on": int(self.heater_on),
            "active_power_w": power_w,
        }
