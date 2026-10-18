"""A panel coordinator owns three independent sensor processes."""

import logging

from .connections.protocol import FIELDS
from .connections.client import run_sensor

LOG = logging.getLogger(__name__)


def stop_children(children):
    # All workers share the stop event; allow socket timeouts and cleanup to finish.
    for child in children:
        child.join(timeout=4)
    for child in children:
        if child.is_alive():
            LOG.warning("Terminating unresponsive process %s", child.name)
            child.terminate()
            child.join(timeout=2)
        if child.is_alive():
            child.kill()
            child.join()


def run_panel(panel, host, port, stop):
    import multiprocessing as mp

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")
    children = []
    reported = set()
    try:
        for kind in FIELDS:
            process = mp.get_context("spawn").Process(
                target=run_sensor, args=(panel, kind, host, port, stop), name="{}-{}".format(panel, kind))
            process.start()
            children.append(process)
        while not stop.wait(0.2):
            for child in children:
                if child.exitcode is not None and child.pid not in reported:
                    LOG.error("Sensor %s stopped unexpectedly (exit=%s); no restart", child.name, child.exitcode)
                    reported.add(child.pid)
    finally:
        stop.set()
        stop_children(children)
