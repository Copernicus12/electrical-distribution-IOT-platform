"""Deterministic household, PV and ambient profiles for the 24-hour scenario."""

import math
import random


class Household:
    def __init__(self, apartment_id, panel_id, monthly_kwh, seed):
        self.apartment_id = apartment_id
        self.panel_id = panel_id
        self.monthly_kwh = monthly_kwh
        self.random = random.Random(seed)
        self.phase_hours = self.random.uniform(-0.8, 0.8)
        self.flexible_share = self.random.uniform(0.25, 0.4)
        self.essential_share = 1 - self.flexible_share
        self.setpoint_c = self.random.uniform(20, 22)
        self.indoor_temperature_c = self.random.uniform(19.5, 21.5)
        self.heater_on = False
        self.heater_kw = self.random.uniform(1.2, 1.8)
        self.thermal_capacity_kwh_per_c = self.random.uniform(3.5, 5.0)
        self.heat_loss_kw_per_c = self.random.uniform(0.07, 0.11)
        self.profile_mean = self._daily_mean()

    def _shape(self, hour):
        morning = 0.45 * math.exp(-((hour - 7.3 - self.phase_hours) / 1.4) ** 2)
        evening = 1.25 * math.exp(-((hour - 19.2 - self.phase_hours) / 2.2) ** 2)
        midday = 0.18 * math.exp(-((hour - 13.0) / 3.0) ** 2)
        return 0.22 + morning + evening + midday

    def _daily_mean(self):
        return sum(self._shape(hour / 4) for hour in range(96)) / 96

    def sample(self, elapsed_s, outdoor_temperature_c, curtailment=0.0, step_s=1):
        hour = (elapsed_s / 3600) % 24
        average_kw = self.monthly_kwh / 30 / 24
        total_kw = average_kw * self._shape(hour) / self.profile_mean
        total_kw *= self.random.uniform(0.97, 1.03)
        essential_kw = total_kw * self.essential_share
        flexible_kw = total_kw * self.flexible_share

        if self.indoor_temperature_c <= self.setpoint_c - 0.4:
            self.heater_on = True
        elif self.indoor_temperature_c >= self.setpoint_c + 0.2:
            self.heater_on = False

        heater_kw = self.heater_kw if self.heater_on else 0.0
        shed_kw = min(flexible_kw + heater_kw, max(0.0, curtailment))
        shed_from_appliances = min(flexible_kw, shed_kw)
        remaining_shed = shed_kw - shed_from_appliances
        served_flexible_kw = flexible_kw - shed_from_appliances
        served_heater_kw = max(0.0, heater_kw - remaining_shed)

        hours = step_s / 3600
        heat_loss_kw = self.heat_loss_kw_per_c * (
            self.indoor_temperature_c - outdoor_temperature_c
        )
        temperature_change = (served_heater_kw - heat_loss_kw) * hours / self.thermal_capacity_kwh_per_c
        self.indoor_temperature_c = min(30.0, max(5.0, self.indoor_temperature_c + temperature_change))

        return {
            "essential_kw": essential_kw,
            "flexible_kw": served_flexible_kw,
            "flexible_available_kw": flexible_kw + heater_kw,
            "heating_kw": served_heater_kw,
            "heating_demand": int(self.heater_on),
            "heater_on": int(served_heater_kw > 0),
            "room_temperature_c": round(self.indoor_temperature_c, 3),
        }


class SolarProfile:
    def __init__(self, capacity_kw, seed):
        self.capacity_kw = capacity_kw
        self.random = random.Random(seed)
        self.cloud_factor = 0.9

    def sample(self, elapsed_s, step_s=1):
        hour = (elapsed_s / 3600) % 24
        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        variation = self.random.uniform(-0.012, 0.012) * math.sqrt(max(1, step_s))
        self.cloud_factor = min(1.0, max(0.35, self.cloud_factor + variation))
        return self.capacity_kw * daylight * self.cloud_factor


def outdoor_temperature(elapsed_s, scenario="normal"):
    hour = (elapsed_s / 3600) % 24
    temperature = 13 + 7 * math.sin(2 * math.pi * (hour - 8) / 24)
    if scenario == "cold":
        temperature -= 18
    return temperature
