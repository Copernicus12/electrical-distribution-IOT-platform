"""End-to-end checks using real subprocesses and TCP, without third-party tools."""

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from iot_platform.connections.protocol import FIELDS, PANELS, validate

ROOT = Path(__file__).resolve().parents[1]


def unused_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "telemetry.jsonl"
        self.processes = []
        self.logs = []

    def start(self, *args):
        log = tempfile.TemporaryFile(mode="w+")
        self.logs.append(log)
        process = subprocess.Popen([sys.executable, str(ROOT / "main.py"), *map(str, args)],
                                   cwd=ROOT, stdout=log, stderr=log, start_new_session=True)
        self.processes.append(process)
        return process

    def halt(self, process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
        self.assertEqual(process.wait(timeout=15), 0)

    def records(self):
        if not self.path.exists():
            return []
        # The writer can be active: inspect only complete newline-terminated records.
        content = self.path.read_bytes()
        return [json.loads(line) for line in content.split(b"\n")[:-1]]

    def wait_for(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.1)
        self.fail("Timed out waiting for telemetry")

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        for log in self.logs:
            log.close()
        self.temp.cleanup()

    def test_manual_commands_12_sensors_15_seconds_and_clean_shutdown(self):
        port = unused_port()
        gateway = self.start("gateway", "--port", port, "--output", self.path)
        panels = [self.start("panel", "--id", panel, "--port", port) for panel in PANELS]
        self.wait_for(lambda: len({row["sensor_id"] for row in self.records()}) == 12)
        time.sleep(15)
        for panel in panels:
            self.halt(panel)
        self.halt(gateway)
        records = self.records()
        self.assertTrue(self.path.read_bytes().endswith(b"\n"))
        expected = {"{}-{}".format(panel, kind) for panel in PANELS for kind in FIELDS}
        self.assertEqual({row["sensor_id"] for row in records}, expected)
        sequences = {}
        for row in records:
            validate(row)
            identity = row["sensor_id"]
            self.assertGreater(row["sequence"], sequences.get(identity, -1))
            sequences[identity] = row["sequence"]
        self.assertTrue(all(value >= 14 for value in sequences.values()))
        snapshot = json.loads(self.path.with_name("telemetry_last_values.json").read_text())
        self.assertEqual(set(snapshot["panels"]), set(PANELS))
        for panel in PANELS:
            for kind in FIELDS:
                latest = snapshot["panels"][panel][kind]
                self.assertEqual(latest["sequence"], sequences["{}-{}".format(panel, kind)])
        # Each manually launched command owns its own process group.
        for process in [gateway, *panels]:
            self.wait_for(lambda: not self.group_exists(process.pid), timeout=5)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", port))

    @staticmethod
    def group_exists(pid):
        # Inspect membership rather than sending signal 0: macOS can return
        # EPERM for a group during teardown. Zombies are already terminated.
        result = subprocess.run(["ps", "-axo", "pgid=,stat="], capture_output=True, text=True, check=True)
        return any(int(group) == pid and not state.startswith("Z")
                   for group, state in (line.split() for line in result.stdout.splitlines()))

    def test_panel_reconnects_after_gateway_restart(self):
        port = unused_port()
        gateway = self.start("gateway", "--port", port, "--output", self.path)
        panel = self.start("panel", "--id", "T01", "--port", port)
        self.wait_for(lambda: len({row["sensor_id"] for row in self.records()}) == 3)
        self.halt(gateway)
        time.sleep(3)
        count = len(self.records())
        gateway = self.start("gateway", "--port", port, "--output", self.path)
        self.wait_for(lambda: len({row["sensor_id"] for row in self.records()[count:]}) == 3)
        self.halt(panel)
        self.halt(gateway)
        records = self.records()
        self.assertTrue(all("received_at" in row for row in records))

    def test_gateway_occupied_port_fails(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            process = self.start("gateway", "--port", occupied.getsockname()[1], "--output", self.path)
            self.assertEqual(process.wait(timeout=15), 1)
        log = self.logs[-1]
        log.seek(0)
        self.assertIn("Gateway could not start/run", log.read())
        self.assertEqual(self.records(), [])
