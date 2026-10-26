import argparse
import logging
import multiprocessing as mp
import os
import signal

from iot_platform.gateway.service import run_gateway
from iot_platform.gateway.edge import run_edge_gateway
from iot_platform.panel import run_panel
from iot_platform.connections.protocol import PANELS
from iot_platform.simulation.runner import run_simulation


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")


def interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description="Electrical distribution IoT simulation and telemetry")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("gateway", "panel"):
        command = commands.add_parser(name)
        command.add_argument("--host", default="127.0.0.1")
        command.add_argument("--port", type=int, default=9000)
        if name == "panel":
            command.add_argument("--id", choices=PANELS, required=True)
            command.add_argument("--adaptive", action="store_true")
            command.add_argument("--full-sensors", action="store_true",
                                 help="include equipment, heating and generation streams")
        else:
            command.add_argument("--output", default="data/telemetry.jsonl")
    edge = commands.add_parser("edge", help="run TCP, HTTPS/WSS and optional MQTT ingestion")
    edge.add_argument("--host", default="127.0.0.1", help="TCP bind address")
    edge.add_argument("--port", type=int, default=9000, help="TCP port")
    edge.add_argument("--api-host", default="127.0.0.1")
    edge.add_argument("--api-port", type=int, default=9443)
    edge.add_argument("--output", default="data/telemetry.jsonl")
    edge.add_argument("--tls-cert", required=True, help="TLS certificate for HTTPS and WSS")
    edge.add_argument("--tls-key", required=True, help="TLS private key for HTTPS and WSS")
    simulation = commands.add_parser("simulate", help="run the 30-apartment, 24-hour network simulation")
    simulation.add_argument("--output", default="data/simulation/telemetry.jsonl.gz")
    simulation.add_argument("--duration-s", type=int, default=86_400)
    simulation.add_argument("--step-s", type=int, default=1)
    simulation.add_argument("--sample-every-s", type=int, default=1)
    simulation.add_argument("--seed", type=int, default=42)
    simulation.add_argument(
        "--scenario",
        choices=("normal", "overload", "overheating", "cold", "sensor-fault", "comms-outage"),
        default="normal",
    )
    simulation.add_argument("--fault-start-s", type=int, default=10_800)
    simulation.add_argument("--manual-support", nargs=2, choices=PANELS,
                            metavar=("DONOR", "RECEIVER"))
    simulation.add_argument("--manual-support-at-s", type=int, default=0)
    simulation.add_argument("--manual-support-lease-s", type=int, default=600)
    args = parser.parse_args()
    if args.command != "simulate" and not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if args.command == "edge" and not 1 <= args.api_port <= 65535:
        parser.error("--api-port must be between 1 and 65535")
    configure_logging()
    stop = mp.get_context("spawn").Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupt)
    try:
        if args.command == "simulate":
            summary, events_path, summary_path = run_simulation(
                args.output,
                duration_s=args.duration_s,
                step_s=args.step_s,
                sample_every_s=args.sample_every_s,
                seed=args.seed,
                scenario=args.scenario,
                fault_start_s=args.fault_start_s,
                manual_support=None if args.manual_support is None else tuple(args.manual_support),
                manual_support_at_s=args.manual_support_at_s,
                manual_support_lease_s=args.manual_support_lease_s,
            )
            logging.info("Simulation complete; summary=%s events=%s", summary_path, events_path)
            logging.info("Samples: %d; events: %d", summary["samples_written"], summary["events"])
        elif args.command == "gateway":
            run_gateway(args.host, args.port, args.output, stop)
        elif args.command == "edge":
            run_edge_gateway(
                args.host, args.port, args.api_host, args.api_port, args.output, stop,
                args.tls_cert, args.tls_key,
                mqtt_host=os.environ.get("IOT_MQTT_HOST"),
                mqtt_port=int(os.environ.get("IOT_MQTT_PORT", "1883")),
                mqtt_username=os.environ.get("IOT_MQTT_USERNAME"),
                mqtt_password=os.environ.get("IOT_MQTT_PASSWORD"),
            )
        else:
            run_panel(args.id, args.host, args.port, stop, args.adaptive, args.full_sensors)
    except KeyboardInterrupt:
        logging.info("Stopping")
    except (RuntimeError, OSError) as exc:
        logging.error("%s", exc)
        return 1
    finally:
        stop.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
