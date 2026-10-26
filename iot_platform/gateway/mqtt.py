"""MQTT subscriber for the edge gateway; QoS delivery is followed by app ACKs."""

import json
import logging
import re

LOG = logging.getLogger(__name__)


def start_mqtt_receiver(gateway, host, port=1883, username=None, password=None):
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise RuntimeError("Install paho-mqtt with: pip install -r requirements.txt") from exc

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="electrical-edge-gateway")
    if username:
        client.username_pw_set(username, password)

    def on_connect(mqtt_client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            mqtt_client.subscribe("electrical/telemetry/#", qos=1)
            LOG.info("MQTT gateway subscribed to electrical/telemetry/#")
        else:
            LOG.error("MQTT connection rejected: %s", reason_code)

    def on_message(mqtt_client, userdata, message):
        try:
            body = json.loads(message.payload)
            acknowledgement = gateway.accept(message.payload)
            reply_to = body.get("reply_to")
            if isinstance(reply_to, str) and re.fullmatch(r"electrical/acks/[A-Za-z0-9_-]+", reply_to):
                mqtt_client.publish(
                    reply_to, json.dumps(acknowledgement, allow_nan=False), qos=1
                )
        except (ValueError, TypeError, UnicodeError) as exc:
            LOG.warning("Rejected MQTT telemetry on %s: %s", message.topic, exc)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=30)
    client.loop_start()
    return client
