"""Concurrent TCP reception, newline framing and connection cleanup."""

import asyncio
import json
import logging

from .protocol import MAX_MESSAGE_BYTES

LOG = logging.getLogger(__name__)


class TCPServer:
    def __init__(self, on_message):
        self.on_message = on_message
        self.writers = set()
        self.tasks = set()

    async def listen(self, host, port):
        return await asyncio.start_server(self.handle, host, port, limit=MAX_MESSAGE_BYTES)

    async def handle(self, reader, writer):
        task = asyncio.current_task()
        self.tasks.add(task)
        self.writers.add(writer)
        peer = writer.get_extra_info("peername")
        LOG.info("Connection from %s", peer)
        try:
            while True:
                try:
                    line = await reader.readline()
                except ValueError:
                    LOG.warning("Oversized message from %s; closing connection", peer)
                    break
                if not line:
                    break
                if len(line.rstrip(b"\n")) > MAX_MESSAGE_BYTES:
                    LOG.warning("Oversized message from %s; closing connection", peer)
                    break
                if not line.endswith(b"\n"):
                    LOG.warning("Incomplete message from %s", peer)
                    break
                try:
                    response = self.on_message(line)
                    if response is not None:
                        writer.write((json.dumps(response, allow_nan=False) + "\n").encode("utf-8"))
                        await writer.drain()
                except (ValueError, UnicodeError, RecursionError) as exc:
                    LOG.warning("Invalid message from %s: %s", peer, exc)
        except (ConnectionError, OSError) as exc:
            LOG.warning("Connection/storage error for %s: %s", peer, exc)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
            self.writers.discard(writer)
            self.tasks.discard(task)
            LOG.info("Disconnected %s", peer)

    async def close_connections(self):
        for writer in list(self.writers):
            writer.close()
        if self.tasks:
            await asyncio.gather(*list(self.tasks), return_exceptions=True)
