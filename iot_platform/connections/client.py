"""Persistent TCP client, send interval and reconnection for a sensor process."""

import logging
import signal
import socket
import time

from .protocol import encode
from ..sensors.generator import Generator

LOG = logging.getLogger(__name__)


def run_sensor(panel, kind, host, port, stop):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    generator = Generator(panel, kind)
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
