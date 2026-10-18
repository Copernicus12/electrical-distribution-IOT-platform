import asyncio
import io
import json
from pathlib import Path
import tempfile
import unittest

from iot_platform.gateway.service import Gateway
from iot_platform.connections.protocol import MAX_MESSAGE_BYTES, encode
from iot_platform.sensors.generator import Generator
from iot_platform.gateway.storage import TelemetrySnapshot


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.output = io.StringIO()
        self.temp = tempfile.TemporaryDirectory()
        self.snapshot_path = Path(self.temp.name) / "telemetry_last_values.json"
        self.gateway = Gateway(self.output, TelemetrySnapshot(self.snapshot_path))
        self.server = await asyncio.start_server(self.gateway.transport.handle, "127.0.0.1", 0, limit=MAX_MESSAGE_BYTES)
        self.port = self.server.sockets[0].getsockname()[1]
        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", self.port)

    async def asyncTearDown(self):
        self.writer.close()
        await self.writer.wait_closed()
        self.server.close()
        await self.server.wait_closed()
        for writer in list(self.gateway.transport.writers):
            writer.close()
        await asyncio.gather(*list(self.gateway.transport.tasks), return_exceptions=True)
        self.temp.cleanup()

    async def test_fragmented_concatenated_and_invalid_messages(self):
        generator = Generator("T01", "ambient")
        first = encode(generator.sample(0))
        self.writer.write(first[:30])
        await self.writer.drain()
        await asyncio.sleep(0.02)
        self.assertEqual(self.gateway.count, 0)
        self.writer.write(first[30:] + b"invalid\n{}\n\xff\n" + encode(generator.sample(1)) + encode(generator.sample(1)))
        await self.writer.drain()
        for _ in range(100):
            if self.gateway.count == 3:
                break
            await asyncio.sleep(0.01)
        records = [json.loads(line) for line in self.output.getvalue().splitlines()]
        self.assertEqual([row["sequence"] for row in records], [0, 1, 2])
        self.assertTrue(all("received_at" in row for row in records))
        snapshot = json.loads(self.snapshot_path.read_text())
        self.assertEqual(snapshot["panels"]["T01"]["ambient"]["sequence"], 2)
        self.assertIsNone(snapshot["panels"]["T04"]["ambient"])

    async def test_snapshot_groups_interleaved_panels_and_replaces_latest(self):
        first = Generator("T01", "electrical")
        second = Generator("T04", "ambient")
        for message in (second.sample(0), first.sample(0), second.sample(1), first.sample(1)):
            self.writer.write(encode(message))
        await self.writer.drain()
        for _ in range(100):
            if self.gateway.count == 4:
                break
            await asyncio.sleep(0.01)
        text = self.snapshot_path.read_text()
        data = json.loads(text)
        self.assertEqual(list(data["panels"]), ["T01", "T02", "T03", "T04"])
        self.assertEqual(data["panels"]["T01"]["electrical"]["sequence"], 1)
        self.assertEqual(data["panels"]["T04"]["ambient"]["sequence"], 1)
        self.assertIn('\n  "panels": {', text)
        self.assertEqual(len(self.output.getvalue().splitlines()), 4)
        self.assertEqual(list(Path(self.temp.name).glob("*.tmp")), [])

    async def test_oversized_message_closes_only_its_connection(self):
        self.writer.write(b"x" * (MAX_MESSAGE_BYTES + 1) + b"\n")
        await self.writer.drain()
        self.assertEqual(await asyncio.wait_for(self.reader.read(), 2), b"")
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(encode(Generator("T02", "connections").sample(0)))
        await writer.drain()
        for _ in range(100):
            if self.gateway.count:
                break
            await asyncio.sleep(0.01)
        writer.close()
        await writer.wait_closed()
        self.assertEqual(self.gateway.count, 1)

    async def test_truncated_frame_is_not_saved(self):
        self.writer.write(encode(Generator("T01", "ambient").sample(0))[:-1])
        await self.writer.drain()
        self.writer.write_eof()
        await asyncio.wait_for(self.reader.read(), 2)
        self.assertEqual(self.gateway.count, 0)
