import argparse
import logging
import multiprocessing as mp
import signal

from iot_platform.gateway.service import run_gateway
from iot_platform.panel import run_panel
from iot_platform.connections.protocol import PANELS


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")


def interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description="Local multiprocess IoT telemetry over TCP")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("gateway", "panel"):
        command = commands.add_parser(name)
        command.add_argument("--host", default="127.0.0.1")
        command.add_argument("--port", type=int, default=9000)
        if name == "panel":
            command.add_argument("--id", choices=PANELS, required=True)
        else:
            command.add_argument("--output", default="data/telemetry.jsonl")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    configure_logging()
    stop = mp.get_context("spawn").Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupt)
    try:
        if args.command == "gateway":
            run_gateway(args.host, args.port, args.output, stop)
        else:
            run_panel(args.id, args.host, args.port, stop)
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
