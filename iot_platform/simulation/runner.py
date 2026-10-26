"""Offline time-series runner for the complete neighborhood scenario."""

import gzip
import json
import logging
from pathlib import Path

from ..gateway.anomaly import detect_anomalies
from .world import SimulationWorld

LOG = logging.getLogger(__name__)


def run_simulation(output, *, duration_s=86_400, step_s=1, sample_every_s=1,
                   seed=42, scenario="normal", fault_start_s=10_800,
                   manual_support=None, manual_support_at_s=0,
                   manual_support_lease_s=600):
    if duration_s <= 0 or step_s <= 0 or sample_every_s <= 0:
        raise ValueError("duration and intervals must be positive")
    if sample_every_s < step_s or sample_every_s % step_s:
        raise ValueError("sample interval must be a multiple of the simulation step")
    if fault_start_s < 0:
        raise ValueError("fault start time cannot be negative")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    events_path = output_path.with_suffix(".events.jsonl")
    summary_path = output_path.with_suffix(".summary.json")
    opener = gzip.open if output_path.suffix == ".gz" else open
    world = SimulationWorld(seed, scenario, fault_start_s)
    if manual_support is not None:
        world.configure_manual_support(
            manual_support[0], manual_support[1], manual_support_at_s,
            manual_support_lease_s,
        )
    latest = {}
    pending_delivery = []
    summary = {
        "scenario": scenario,
        "manual_support": manual_support,
        "seed": seed,
        "duration_s": duration_s,
        "step_s": step_s,
        "sample_every_s": sample_every_s,
        "samples_written": 0,
        "maximum_transformer_loading_pct": 0.0,
        "maximum_panel_loading_pct": {panel: 0.0 for panel in world.households},
        "minimum_voltage_pu": 2.0,
        "maximum_voltage_pu": 0.0,
        "final_load_kwh": {panel: 0.0 for panel in world.households},
        "final_requested_kwh": {panel: 0.0 for panel in world.households},
        "final_unserved_kwh": {panel: 0.0 for panel in world.households},
        "final_pv_kwh": {panel: 0.0 for panel in world.households},
        "events": 0,
        "event_counts": {},
        "anomaly_counts": {},
        "breaker_trip_counts": {},
        "samples_delayed_by_outage": 0,
        "maximum_delivery_delay_s": 0,
    }

    with opener(output_path, "wt", encoding="utf-8") as telemetry, \
            events_path.open("w", encoding="utf-8") as events_file:
        for elapsed_s in range(0, duration_s, step_s):
            sample_sensors = elapsed_s % sample_every_s == 0
            records, events, results = world.step(step_s, sample_sensors=sample_sensors)
            summary["maximum_transformer_loading_pct"] = max(
                summary["maximum_transformer_loading_pct"], results["transformer_loading_pct"]
            )
            for panel, metrics in results["panels"].items():
                summary["maximum_panel_loading_pct"][panel] = max(
                    summary["maximum_panel_loading_pct"][panel], metrics["line_loading_pct"]
                )
                summary["minimum_voltage_pu"] = min(summary["minimum_voltage_pu"], metrics["voltage_pu"])
                summary["maximum_voltage_pu"] = max(summary["maximum_voltage_pu"], metrics["voltage_pu"])

            for event in events:
                events_file.write(json.dumps(event, allow_nan=False) + "\n")
                summary["events"] += 1
                name = event["event"]
                summary["event_counts"][name] = summary["event_counts"].get(name, 0) + 1

            for message in records:
                pending_delivery.append((elapsed_s, message))

            if world.communication_available and pending_delivery:
                for sampled_at_s, message in pending_delivery:
                    delay_s = elapsed_s - sampled_at_s
                    if delay_s:
                        message["delivery_delay_s"] = delay_s
                        summary["samples_delayed_by_outage"] += 1
                        summary["maximum_delivery_delay_s"] = max(
                            summary["maximum_delivery_delay_s"], delay_s
                        )
                    previous = latest.get(message["sensor_id"])
                    message["anomalies"] = detect_anomalies(message, previous)
                    for anomaly in message["anomalies"]:
                        code = anomaly["code"]
                        summary["anomaly_counts"][code] = summary["anomaly_counts"].get(code, 0) + 1
                    latest[message["sensor_id"]] = message
                    telemetry.write(json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n")
                    summary["samples_written"] += 1
                pending_delivery.clear()

            if elapsed_s and elapsed_s % 3600 == 0:
                LOG.info("Simulated %d of %d seconds", elapsed_s, duration_s)

        # A run ending during an outage retains its queued messages in the
        # artifact and marks the delay as unresolved at the end of the run.
        for sampled_at_s, message in pending_delivery:
            delay_s = duration_s - sampled_at_s
            message["delivery_delay_s"] = delay_s
            message["delivery_pending_at_end"] = True
            summary["samples_delayed_by_outage"] += 1
            summary["maximum_delivery_delay_s"] = max(
                summary["maximum_delivery_delay_s"], delay_s
            )
            previous = latest.get(message["sensor_id"])
            message["anomalies"] = detect_anomalies(message, previous)
            for anomaly in message["anomalies"]:
                code = anomaly["code"]
                summary["anomaly_counts"][code] = summary["anomaly_counts"].get(code, 0) + 1
            latest[message["sensor_id"]] = message
            telemetry.write(json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n")
            summary["samples_written"] += 1

    summary["final_load_kwh"] = {
        panel: round(world.energy_kwh[panel], 4) for panel in world.energy_kwh
    }
    summary["final_requested_kwh"] = {
        panel: round(world.requested_energy_kwh[panel], 4)
        for panel in world.requested_energy_kwh
    }
    summary["final_unserved_kwh"] = {
        panel: round(world.unserved_energy_kwh[panel], 4)
        for panel in world.unserved_energy_kwh
    }
    summary["final_pv_kwh"] = {
        panel: round(world.pv_energy_kwh[panel], 4) for panel in world.pv_energy_kwh
    }
    summary["breaker_trip_counts"] = dict(world.trip_count)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary, events_path, summary_path
