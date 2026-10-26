"""Persistent TCP client, send interval and reconnection for a sensor process."""

import logging
import signal
import socket
import time

from .protocol import encode
from ..sensors.generator import Generator

LOG = logging.getLogger(__name__)


def run_sensor(panel, kind, host, port, stop, adaptive=False):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    generator = Generator(panel, kind)
    if adaptive:
        from .adaptive import create_transport_manager

        _run_adaptive(panel, kind, host, port, stop, generator, create_transport_manager)
        return
    delay = 1
    previous = None
    while not stop.is_set():
        try:
            with socket.create_connection((host, port), timeout=2) as connection:
                connection.settimeout(2)
                LOG.info("%s-%s connected", panel, kind)
                while not stop.is_set():
                    now = time.monotonic()
                    message = generator.sample(0 if previous is None else now - previous)
                    previous = now
                    connection.sendall(encode(message))
                    delay = 1
                    if stop.wait(1):
                        break
        except OSError as exc:
            LOG.warning("%s-%s: %s; retry in %ss", panel, kind, exc, delay)
            if stop.wait(delay):
                break
            delay = min(delay * 2, 5)


def _run_adaptive(panel, kind, host, port, stop, generator, create_manager):
    manager = create_manager(panel, kind, host, port)
    previous = None
    try:
        while not stop.is_set():
            now = time.monotonic()
            message = generator.sample(0 if previous is None else now - previous)
            previous = now
            if not manager.publish(message):
                LOG.warning("%s-%s: sample queued; no route acknowledged delivery", panel, kind)
            else:
                manager.drain_pending(max_messages=5)
            if stop.wait(1):
                break
    finally:
        manager.close()
