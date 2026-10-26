"""Gateway message validation, persistence, summaries and service lifecycle."""

import asyncio
import json
import logging
from pathlib import Path
import threading

from ..connections.protocol import utc_now, validate
from ..connections.server import TCPServer
from .anomaly import detect_anomalies
from .storage import MessageInbox, TelemetrySnapshot, last_values_path

LOG = logging.getLogger(__name__)


class Gateway:
    def __init__(self, output, snapshot=None, inbox=None):
        self.output = output
        self.snapshot = snapshot
        self.inbox = inbox
        self.lock = threading.RLock()
        self.latest = {}
        self.count = 0
        self.transport = TCPServer(self.accept)

    def accept(self, line):
        message = validate(json.loads(line))
        # reply_to is MQTT transport metadata, not part of stored telemetry.
        message.pop("reply_to", None)
        message_id = message.get(
            "message_id", "{}:{}".format(message["sensor_id"], message["sequence"])
        )
        with self.lock:
            received_at = utc_now()
            if self.inbox is not None and self.inbox.contains(message_id):
                return {"acknowledged_id": message_id, "accepted": True, "duplicate": True}

            previous = self.latest.get(message["sensor_id"])
            record = dict(message, received_at=received_at)
            anomalies = detect_anomalies(message, previous)
            if anomalies:
                record["anomalies"] = anomalies
            self.output.write(json.dumps(record, allow_nan=False) + "\n")
            self.output.flush()
            if self.snapshot is not None:
                self.snapshot.update(record)
                self.snapshot.save()
            if self.inbox is not None:
                self.inbox.remember(message_id, received_at)
            self.latest[message["sensor_id"]] = message
            self.count += 1
        return {"acknowledged_id": message_id, "accepted": True}

    async def summarize(self, stop):
        elapsed = 0
        while not stop.is_set():
            await asyncio.sleep(0.2)
            elapsed += 0.2
            if elapsed >= 5:
                LOG.info("Summary: %d messages, %d sensors, %d connections", self.count, len(self.latest), len(self.transport.writers))
                for identity, message in sorted(self.latest.items()):
                    LOG.info("%s sequence=%s %s", identity, message["sequence"], message["measurements"])
                elapsed = 0


async def serve(host, port, path, stop):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as output:
        snapshot_path = last_values_path(output_path)
        snapshot = TelemetrySnapshot(snapshot_path)
        inbox = MessageInbox(output_path.with_suffix(".inbox.sqlite3"))
        gateway = Gateway(output, snapshot, inbox)
        server = await gateway.transport.listen(host, port)
        summary = asyncio.create_task(gateway.summarize(stop))
        try:
            snapshot.save()
            LOG.info("Gateway listening on %s:%s; output=%s", host, port, path)
            LOG.info("Readable telemetry: %s", snapshot_path)
            async with server:
                while not stop.is_set():
                    await asyncio.sleep(0.2)
        finally:
            server.close()
            await server.wait_closed()
            summary.cancel()
            await asyncio.gather(summary, return_exceptions=True)
            await gateway.transport.close_connections()
            inbox.close()


def run_gateway(host, port, path, stop):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(processName)s %(levelname)s %(message)s")
    try:
        asyncio.run(serve(host, port, path, stop))
    except OSError as exc:
        LOG.error("Gateway could not start/run: %s", exc)
        raise SystemExit(1)
