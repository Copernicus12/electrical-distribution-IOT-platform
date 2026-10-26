"""Adaptive MQTT, HTTPS, WSS and TCP delivery with a SQLite outbox."""

import json
import logging
import math
import os
import socket
import sqlite3
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .protocol import encode

LOG = logging.getLogger(__name__)


class SQLiteOutbox:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.database = sqlite3.connect(path, timeout=30)
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS outbox "
            "(message_id TEXT PRIMARY KEY, body TEXT NOT NULL, created_at REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0)"
        )
        self.database.commit()

    def enqueue(self, message):
        body = json.dumps(message, allow_nan=False, separators=(",", ":"))
        with self.database:
            self.database.execute(
                "INSERT OR IGNORE INTO outbox(message_id, body, created_at) VALUES (?, ?, ?)",
                (message["message_id"], body, time.time()),
            )

    def first(self):
        row = self.database.execute(
            "SELECT message_id, body FROM outbox ORDER BY created_at LIMIT 1"
        ).fetchone()
        return None if row is None else (row[0], json.loads(row[1]))

    def attempted(self, message_id):
        with self.database:
            self.database.execute(
                "UPDATE outbox SET attempts = attempts + 1 WHERE message_id = ?", (message_id,)
            )

    def acknowledge(self, message_id):
        with self.database:
            self.database.execute("DELETE FROM outbox WHERE message_id = ?", (message_id,))

    def close(self):
        self.database.close()


class TCPTransport:
    name = "tcp"

    def __init__(self, host, port, timeout=3):
        self.host, self.port, self.timeout = host, port, timeout

    def probe(self):
        started = time.monotonic()
        with socket.create_connection((self.host, self.port), timeout=self.timeout):
            return (time.monotonic() - started) * 1000

    def send(self, message):
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as connection:
            connection.settimeout(self.timeout)
            connection.sendall(encode(message))
            response = self._readline(connection)
        ack = json.loads(response)
        return ack.get("accepted") is True and ack.get("acknowledged_id") == message["message_id"]

    @staticmethod
    def _readline(connection):
        received = bytearray()
        while len(received) <= 4096:
            chunk = connection.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                return received.decode("utf-8")
            received.extend(chunk)
        raise OSError("gateway returned an incomplete acknowledgement")


class HTTPSTransport:
    name = "https"

    def __init__(self, endpoint, token=None, timeout=3):
        if not endpoint.startswith("https://"):
            raise ValueError("HTTP telemetry endpoint must use https://")
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout
        parts = urlsplit(endpoint)
        self.health_url = "https://{}{}".format(parts.netloc, "/health")

    def probe(self):
        started = time.monotonic()
        request = Request(self.health_url, headers=self._headers())
        with urlopen(request, timeout=self.timeout) as response:
            if response.status != 200:
                raise OSError("HTTPS health check failed with {}".format(response.status))
            response.read(1024)
        return (time.monotonic() - started) * 1000

    def send(self, message):
        body = json.dumps(message, allow_nan=False).encode("utf-8")
        request = Request(self.endpoint, data=body, headers=self._headers(), method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                ack = json.loads(response.read(4096))
        except (URLError, TimeoutError, ValueError) as exc:
            raise OSError("HTTPS telemetry delivery failed: {}".format(exc)) from exc
        return ack.get("accepted") is True and ack.get("acknowledged_id") == message["message_id"]

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        return headers


class WSSTransport:
    name = "wss"

    def __init__(self, endpoint, token=None, timeout=3):
        if not endpoint.startswith("wss://"):
            raise ValueError("WebSocket telemetry endpoint must use wss://")
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout

    def probe(self):
        from websockets.sync.client import connect

        started = time.monotonic()
        try:
            with connect(self.endpoint, open_timeout=self.timeout, close_timeout=self.timeout,
                         additional_headers=self._headers()):
                return (time.monotonic() - started) * 1000
        except Exception as exc:
            raise OSError("WSS health check failed: {}".format(exc)) from exc

    def send(self, message):
        from websockets.sync.client import connect

        try:
            with connect(self.endpoint, open_timeout=self.timeout, close_timeout=self.timeout,
                         additional_headers=self._headers()) as websocket:
                websocket.send(json.dumps(message, allow_nan=False))
                ack = json.loads(websocket.recv(timeout=self.timeout))
        except Exception as exc:
            raise OSError("WSS telemetry delivery failed: {}".format(exc)) from exc
        return ack.get("accepted") is True and ack.get("acknowledged_id") == message["message_id"]

    def _headers(self):
        return {"Authorization": "Bearer " + self.token} if self.token else None


class MQTTTransport:
    name = "mqtt"

    def __init__(self, host, port, panel, kind, username=None, password=None, timeout=5):
        import paho.mqtt.client as mqtt

        self.mqtt = mqtt
        self.timeout = timeout
        self.client_id = "{}-{}-{}".format(panel, kind, os.getpid())
        self.ack_topic = "electrical/acks/" + self.client_id
        self.telemetry_topic = "electrical/telemetry/{}".format(panel)
        self.acknowledged = {}
        self.connected = __import__("threading").Event()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        if username:
            self.client.username_pw_set(username, password)
        self.host, self.port = host, port
        self.timeout = timeout
        self.loop_started = False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(self.ack_topic, qos=1)
            self.connected.set()

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.connected.clear()

    def _on_message(self, client, userdata, message):
        try:
            ack = json.loads(message.payload)
        except (ValueError, UnicodeError):
            return
        message_id = ack.get("acknowledged_id")
        if message_id:
            self.acknowledged[message_id] = ack.get("accepted") is True

    def probe(self):
        started = time.monotonic()
        with socket.create_connection((self.host, self.port), timeout=self.timeout):
            pass
        if not self.connected.is_set():
            try:
                if not self.loop_started:
                    self.client.connect(self.host, self.port, keepalive=30)
                    self.client.loop_start()
                    self.loop_started = True
                if not self.connected.wait(self.timeout):
                    raise OSError("MQTT connection timed out")
            except Exception as exc:
                raise OSError("MQTT connection failed: {}".format(exc)) from exc
        return (time.monotonic() - started) * 1000

    def send(self, message):
        message = dict(message, reply_to=self.ack_topic)
        try:
            info = self.client.publish(
                self.telemetry_topic, json.dumps(message, allow_nan=False), qos=1
            )
            info.wait_for_publish(timeout=self.timeout)
        except Exception as exc:
            raise OSError("MQTT publish failed: {}".format(exc)) from exc
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if message["message_id"] in self.acknowledged:
                return self.acknowledged.pop(message["message_id"])
            time.sleep(0.01)
        return False

    def close(self):
        client = getattr(self, "client", None)
        if client is not None:
            client.disconnect()
            if self.loop_started:
                client.loop_stop()


class TransportManager:
    def __init__(self, adapters, outbox, probe_interval_s=5, cooldown_s=30, stable_s=15):
        self.adapters = {adapter.name: adapter for adapter in adapters}
        if not self.adapters:
            raise ValueError("at least one transport is required")
        self.outbox = outbox
        self.health = {
            name: {"latency_ms": math.inf, "probe_failures": 0, "send_failures": 0,
                   "healthy": False, "bytes": 0, "messages": 0}
            for name in self.adapters
        }
        self.probe_interval_s = probe_interval_s
        self.cooldown_s = cooldown_s
        self.stable_s = stable_s
        self.active = None
        self.candidate = None
        self.candidate_since = 0.0
        self.last_switch = 0.0
        self.last_probe = 0.0

    def publish(self, message):
        self.outbox.enqueue(message)
        return self.send_pending()

    def drain_pending(self, max_messages=5):
        sent = 0
        while sent < max_messages and self.send_pending():
            sent += 1
        return sent

    def send_pending(self):
        now = time.monotonic()
        if now - self.last_probe >= self.probe_interval_s:
            self.refresh()
        route = self._select(time.monotonic())
        item = self.outbox.first()
        if route is None or item is None:
            return False

        message_id, message = item
        if self._expired(message.get("expires_at")):
            self.outbox.acknowledge(message_id)
            LOG.warning("Dropping expired command %s", message_id)
            return False
        try:
            acknowledged = self.adapters[route].send(message)
        except OSError as exc:
            LOG.warning("%s delivery failed: %s", route, exc)
            acknowledged = False
        if not acknowledged:
            self._send_failure(route)
            self.outbox.attempted(message_id)
            return False

        state = self.health[route]
        state["send_failures"] = 0
        state["healthy"] = True
        state["bytes"] += len(json.dumps(message, allow_nan=False).encode("utf-8"))
        state["messages"] += 1
        self.outbox.acknowledge(message_id)
        return True

    def refresh(self):
        for name, adapter in self.adapters.items():
            try:
                elapsed_ms = adapter.probe()
                state = self.health[name]
                old = state["latency_ms"]
                state["latency_ms"] = elapsed_ms if not math.isfinite(old) else 0.7 * old + 0.3 * elapsed_ms
                state["probe_failures"] = 0
                state["send_failures"] = 0
                state["healthy"] = True
            except OSError as exc:
                LOG.debug("%s probe failed: %s", name, exc)
                state = self.health[name]
                state["probe_failures"] += 1
                if state["probe_failures"] >= 3:
                    state["healthy"] = False
        self.last_probe = time.monotonic()

    def _select(self, now):
        available = [
            name for name, state in self.health.items()
            if state["healthy"] and state["probe_failures"] < 3 and state["send_failures"] < 3
        ]
        if not available:
            return None
        configured_alternates = [name for name in available if name != "tcp"]
        if configured_alternates:
            available = configured_alternates
        best = min(available, key=self._score)
        if self.active not in available:
            self.active = best
            self.last_switch = now
            self.candidate = None
            LOG.info("Using %s transport", best)
            return best
        if best == self.active:
            self.candidate = None
            return self.active
        if self.active == "tcp" and best != "tcp":
            self.active = best
            self.last_switch = now
            self.candidate = None
            LOG.info("Using %s transport", best)
            return best
        if self._score(best) > self._score(self.active) * 0.8 or now - self.last_switch < self.cooldown_s:
            self.candidate = None
            return self.active
        if self.candidate != best:
            self.candidate = best
            self.candidate_since = now
            return self.active
        if now - self.candidate_since >= self.stable_s:
            self.active = best
            self.last_switch = now
            self.candidate = None
            LOG.info("Switched to %s transport", best)
        return self.active

    def _score(self, name):
        state = self.health[name]
        average_bytes = state["bytes"] / max(1, state["messages"])
        failures = state["probe_failures"] + state["send_failures"]
        return state["latency_ms"] + failures * 500 + average_bytes / 10_000

    def _send_failure(self, name):
        state = self.health[name]
        state["send_failures"] += 1
        if state["send_failures"] >= 3:
            state["healthy"] = False

    @staticmethod
    def _expired(stamp):
        if stamp is None:
            return False
        from datetime import datetime, timezone
        expires = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return expires <= datetime.now(timezone.utc)

    def close(self):
        self.outbox.close()
        for adapter in self.adapters.values():
            close = getattr(adapter, "close", None)
            if close is not None:
                close()


def create_transport_manager(panel, kind, host, port):
    adapters = [TCPTransport(host, port)]
    http_endpoint = os.environ.get("IOT_HTTPS_ENDPOINT")
    if http_endpoint:
        adapters.append(HTTPSTransport(http_endpoint, os.environ.get("IOT_HTTPS_TOKEN")))
    wss_endpoint = os.environ.get("IOT_WSS_ENDPOINT")
    if wss_endpoint:
        adapters.append(WSSTransport(wss_endpoint, os.environ.get("IOT_HTTPS_TOKEN")))
    mqtt_host = os.environ.get("IOT_MQTT_HOST")
    if mqtt_host:
        adapters.append(MQTTTransport(
            mqtt_host,
            int(os.environ.get("IOT_MQTT_PORT", "1883")),
            panel,
            kind,
            os.environ.get("IOT_MQTT_USERNAME"),
            os.environ.get("IOT_MQTT_PASSWORD"),
        ))
    safe_kind = kind.replace("/", "_")
    outbox = SQLiteOutbox(Path("data/outbox") / "{}-{}.sqlite3".format(panel, safe_kind))
    return TransportManager(adapters, outbox)
