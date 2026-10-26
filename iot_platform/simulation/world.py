"""Coordinates household profiles, network power flow and panel sensors."""

from datetime import datetime, timedelta, timezone
import random

from ..connections.protocol import ALL_FIELDS, PANELS
from ..sensors.generator import Generator
from .control import EdgeController
from .network import DistributionNetwork
from .profiles import Household, SolarProfile, outdoor_temperature

APARTMENTS = {"T01": 8, "T02": 7, "T03": 8, "T04": 7}
GROUPS = {"T01": "PV1", "T02": "PV1", "T03": "PV2", "T04": "PV2"}


class SimulationWorld:
    def __init__(self, seed=42, scenario="normal", fault_start_s=10_800):
        if scenario not in ("normal", "overload", "overheating", "cold", "sensor-fault", "comms-outage"):
            raise ValueError("unknown simulation scenario")
        self.seed = seed
        self.scenario = scenario
        self.fault_start_s = fault_start_s
        self.network = DistributionNetwork()
        self.controller = EdgeController()
        self.households = {panel: [] for panel in PANELS}
        self.panel_generators = {
            panel: {kind: Generator(panel, kind) for kind in ALL_FIELDS}
            for panel in PANELS
        }
        apartment = 0
        for panel in PANELS:
            for _ in range(APARTMENTS[panel]):
                apartment += 1
                rng = random.Random(seed + apartment * 37)
                monthly_kwh = rng.uniform(150, 250)
                self.households[panel].append(
                    Household(apartment, panel, monthly_kwh, seed + apartment * 101)
                )
        self.solar = {
            "PV1": SolarProfile(30, seed + 1001),
            "PV2": SolarProfile(30, seed + 2002),
        }
        self.connection_temperatures = {panel: 34.0 for panel in PANELS}
        self.cabinet_temperatures = {panel: 24.0 for panel in PANELS}
        self.cabinet_humidity = {panel: 45.0 for panel in PANELS}
        self.door_state = {panel: 0 for panel in PANELS}
        self.door_rng = {panel: random.Random(seed + index * 701) for index, panel in enumerate(PANELS)}
        self.trip_count = {panel: 0 for panel in PANELS}
        self.breaker_closed = {panel: True for panel in PANELS}
        self.overcurrent_since_s = {panel: None for panel in PANELS}
        self.confirmed_operations = {panel: 0 for panel in PANELS}
        self.energy_kwh = {panel: 0.0 for panel in PANELS}
        self.requested_energy_kwh = {panel: 0.0 for panel in PANELS}
        self.unserved_energy_kwh = {panel: 0.0 for panel in PANELS}
        self.pv_energy_kwh = {panel: 0.0 for panel in PANELS}
        self.elapsed_s = 0
        self.last_results = None
        self.last_events = []
        self.start_time = datetime.now(timezone.utc)
        self.comms_outage_active = False
        self.communication_available = True
        self.manual_support = None
        self.manual_support_applied = False

    def configure_manual_support(self, donor, receiver, start_s=0, lease_s=600):
        if donor not in PANELS or receiver not in PANELS or donor == receiver:
            raise ValueError("manual support requires two different valid panels")
        if start_s < 0 or not 0 < lease_s <= 3600:
            raise ValueError("manual support start must be nonnegative and lease between 1 and 3600 seconds")
        self.manual_support = (donor, receiver, start_s, lease_s)

    def step(self, step_s=1, sample_sensors=True):
        elapsed = self.elapsed_s
        outside_c = outdoor_temperature(elapsed, self.scenario)
        panel_parts = {}
        panel_load_kw = {}
        panel_requested_kw = {}
        flexible_kw = {}
        heat_kw = {}
        room_temps = {}

        for panel, homes in self.households.items():
            per_home_shed = (
                self.controller.shed_kw.get(panel, 0.0) / len(homes)
                if self.breaker_closed[panel] else float("inf")
            )
            parts = [home.sample(elapsed, outside_c, per_home_shed, step_s) for home in homes]
            essential = sum(item["essential_kw"] for item in parts)
            flexible_available = sum(item["flexible_available_kw"] for item in parts)
            flexible = sum(item["flexible_kw"] for item in parts)
            heating = sum(item["heating_kw"] for item in parts)
            panel_parts[panel] = parts
            flexible_kw[panel] = flexible_available
            heat_kw[panel] = heating
            room_temps[panel] = sum(item["room_temperature_c"] for item in parts) / len(parts)
            panel_load_kw[panel] = essential + flexible + heating
            panel_requested_kw[panel] = essential + flexible_available

        if self.scenario == "overload" and self.fault_start_s <= elapsed < self.fault_start_s + 3600:
            panel_load_kw["T02"] += 35.0
            panel_requested_kw["T02"] += 35.0

        pv_kw = {name: profile.sample(elapsed, step_s) for name, profile in self.solar.items()}
        results = self.network.solve(panel_load_kw, pv_kw)
        events = []
        if (self.manual_support and not self.manual_support_applied
                and elapsed >= self.manual_support[2]):
            donor, receiver, _, lease_s = self.manual_support
            try:
                events.append(self.controller.request_manual_support(
                    donor, receiver, elapsed, lease_s, self.network
                ))
            except ValueError as exc:
                events.append(self._event(elapsed, "manual_support_rejected", receiver, reason=str(exc)))
            self.manual_support_applied = True
            results = self.network.last_results

        events.extend(self.controller.update(elapsed, results, flexible_kw, self.network))
        results = self.network.last_results

        # A simulated 50 A feeder breaker trips after five seconds above 125%.
        # It remains open until an explicit reset is added to the live-control path.
        for panel in PANELS:
            metrics = results["panels"][panel]
            if not self.breaker_closed[panel]:
                continue
            if metrics["line_loading_pct"] >= 125:
                if self.overcurrent_since_s[panel] is None:
                    self.overcurrent_since_s[panel] = elapsed
                elif elapsed - self.overcurrent_since_s[panel] >= 5:
                    self.breaker_closed[panel] = False
                    self.network.set_breaker(panel, False)
                    self.trip_count[panel] += 1
                    self.confirmed_operations[panel] += 1
                    events.append(self._event(elapsed, "breaker_tripped", panel,
                                              trip_count=self.trip_count[panel],
                                              loading_pct=metrics["line_loading_pct"]))
                    results = self.network.solve(panel_load_kw, pv_kw)
            else:
                self.overcurrent_since_s[panel] = None

        for event in events:
            if event["event"] in ("support_enabled", "automatic_restore", "manual_support_enabled"):
                self.confirmed_operations[event["panel_id"]] += 1

        event_timestamp = (self.start_time + timedelta(seconds=elapsed)).isoformat().replace("+00:00", "Z")
        for event in events:
            event["timestamp"] = event_timestamp

        outage_active = (
            self.scenario == "comms-outage"
            and self.fault_start_s <= elapsed < self.fault_start_s + 600
        )
        if outage_active != self.comms_outage_active:
            self.comms_outage_active = outage_active
            self.communication_available = not outage_active
            events.append(self._event(
                elapsed,
                "communication_outage_start" if outage_active else "communication_outage_end",
                "T01",
                duration_s=600,
            ))
            events[-1]["timestamp"] = event_timestamp

        measurements = {}
        for panel in PANELS:
            metrics = results["panels"][panel]
            load_w = metrics["load_kw"] * 1000
            self.energy_kwh[panel] += load_w * step_s / 3_600_000
            requested_w = panel_requested_kw[panel] * 1000
            self.requested_energy_kwh[panel] += requested_w * step_s / 3_600_000
            self.unserved_energy_kwh[panel] = max(
                0.0, self.requested_energy_kwh[panel] - self.energy_kwh[panel]
            )
            line_target = 24 + 55 * (metrics["line_loading_pct"] / 100) ** 2
            if self.scenario == "overheating" and panel == "T02" and elapsed >= self.fault_start_s:
                line_target += 60
            self.connection_temperatures[panel] += (
                line_target - self.connection_temperatures[panel]
            ) * min(1.0, step_s / 240)
            cabinet_target = 22 + max(0, outside_c - 18) * 0.12 + 2 * metrics["line_loading_pct"] / 100
            self.cabinet_temperatures[panel] += (
                cabinet_target - self.cabinet_temperatures[panel]
            ) * min(1.0, step_s / 600)
            self.cabinet_humidity[panel] = min(75, max(25, 48 - 0.35 * (outside_c - 18)))

            group = GROUPS[panel]
            group_homes = APARTMENTS["T01"] + APARTMENTS["T02"] if group == "PV1" else APARTMENTS["T03"] + APARTMENTS["T04"]
            share = APARTMENTS[panel] / group_homes
            panel_pv_w = pv_kw[group] * share * 1000
            self.pv_energy_kwh[panel] += panel_pv_w * step_s / 3_600_000
            rng = self.door_rng[panel]
            if self.door_state[panel] and rng.random() < step_s / 90:
                self.door_state[panel] = 0
            elif not self.door_state[panel] and rng.random() < step_s / 7200:
                self.door_state[panel] = 1

            heating_count = sum(item["heating_demand"] for item in panel_parts[panel])
            heater_count = sum(item["heater_on"] for item in panel_parts[panel])
            values = {
                "electrical": {
                    "voltage_v": round(metrics["voltage_v"], 3),
                    "current_a": round(metrics["current_a"], 3),
                    "active_power_w": round(load_w, 3),
                    "energy_kwh": round(self.energy_kwh[panel], 6),
                    "frequency_hz": 50.0,
                    "power_factor": 0.95,
                },
                "connections": {"temperature_c": round(self.connection_temperatures[panel], 3)},
                "ambient": {
                    "temperature_c": round(self.cabinet_temperatures[panel], 3),
                    "humidity_pct": round(self.cabinet_humidity[panel], 3),
                },
                "equipment": {
                    "door_open": self.door_state[panel],
                    "breaker_closed": int(self.breaker_closed[panel]),
                    "trip_count": self.trip_count[panel],
                    "confirmed_operations": self.confirmed_operations[panel],
                },
                "heating": {
                    "room_temperature_c": round(room_temps[panel], 3),
                    "heating_demand": heating_count,
                    "heater_on": heater_count if self.breaker_closed[panel] else 0,
                    "active_power_w": round(heat_kw[panel] * 1000 if self.breaker_closed[panel] else 0.0, 3),
                },
                "generation": {
                    "pv_power_w": round(panel_pv_w, 3),
                    "energy_kwh": round(self.pv_energy_kwh[panel], 6),
                },
            }
            if self.scenario == "sensor-fault" and panel == "T02" and elapsed >= self.fault_start_s:
                values["ambient"]["temperature_c"] = 150.0
            measurements[panel] = values

        records = []
        if sample_sensors:
            for panel in PANELS:
                for kind, generator in self.panel_generators[panel].items():
                    message = generator.sample(
                        step_s, measurements[panel][kind],
                        timestamp=event_timestamp,
                    )
                    message["simulation_elapsed_s"] = elapsed
                    records.append(message)

        self.elapsed_s += step_s
        self.last_results = results
        self.last_events = events
        return records, events, results

    @staticmethod
    def _event(elapsed_s, event, panel, **details):
        return {
            "event_id": "{}-{}-{}".format(event, panel, elapsed_s),
            "simulation_elapsed_s": elapsed_s,
            "event": event,
            "panel_id": panel,
            **details,
        }
