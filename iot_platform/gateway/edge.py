"""Run the TCP, HTTP, WebSocket and optional MQTT edge gateway together."""

import asyncio
import logging
from pathlib import Path

from ..connections.server import TCPServer
from .api import create_app
from .mqtt import start_mqtt_receiver
from .service import Gateway
from .storage import MessageInbox, TelemetrySnapshot, last_values_path

LOG = logging.getLogger(__name__)


async def serve_edge(tcp_host, tcp_port, api_host, api_port, output_path, stop,
                     tls_cert, tls_key,
                     mqtt_host=None, mqtt_port=1883, mqtt_username=None, mqtt_password=None):
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Install the project dependencies with: pip install -r requirements.txt") from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as output:
        snapshot = TelemetrySnapshot(last_values_path(output_path))
        inbox = MessageInbox(output_path.with_suffix(".inbox.sqlite3"))
        gateway = Gateway(output, snapshot, inbox)
        tcp = await gateway.transport.listen(tcp_host, tcp_port)
        app = create_app(gateway)
        config = uvicorn.Config(
            app, host=api_host, port=api_port, log_level="warning",
            ssl_certfile=tls_cert, ssl_keyfile=tls_key,
        )
        api = uvicorn.Server(config)
        api_task = asyncio.create_task(api.serve())
        mqtt_client = None
        try:
            if mqtt_host:
                mqtt_client = start_mqtt_receiver(
                    gateway, mqtt_host, mqtt_port, mqtt_username, mqtt_password
                )
            LOG.info("Edge gateway TCP listening on %s:%s", tcp_host, tcp_port)
            LOG.info("Edge gateway HTTPS/WSS listening on %s:%s", api_host, api_port)
            while not stop.is_set() and not api.should_exit:
                if api_task.done():
                    await api_task
                    break
                await asyncio.sleep(0.2)
        finally:
            api.should_exit = True
            try:
                if not api_task.done():
                    await api_task
            finally:
                tcp.close()
                await tcp.wait_closed()
                await gateway.transport.close_connections()
                if mqtt_client is not None:
                    mqtt_client.disconnect()
                    mqtt_client.loop_stop()
                inbox.close()


def run_edge_gateway(tcp_host, tcp_port, api_host, api_port, output, stop,
                     tls_cert, tls_key,
                     mqtt_host=None, mqtt_port=1883, mqtt_username=None, mqtt_password=None):
    asyncio.run(serve_edge(
        tcp_host, tcp_port, api_host, api_port, output, stop,
        tls_cert, tls_key,
        mqtt_host, mqtt_port, mqtt_username, mqtt_password,
    ))
