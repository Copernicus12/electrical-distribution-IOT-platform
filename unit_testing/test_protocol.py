"""Wire contract validation against fixed valid and invalid inputs."""

import json
import math
import unittest

from iot_platform.connections.protocol import encode, validate
from unit_testing.fixtures import ambient_message


class ProtocolTests(unittest.TestCase):
    def test_accepts_valid_message(self):
        message = ambient_message()
        self.assertEqual(validate(message), message)

    def test_out_of_nominal_range_is_allowed_for_future_anomalies(self):
        message = ambient_message()
        message['measurements']['temperature_c'] = 150
        validate(message)

    def test_rejects_invalid_metadata(self):
        for key, value in (
            ('schema_version', True), ('schema_version', 2), ('sequence', -1),
            ('sequence', True), ('sequence', 1.5), ('sensor_id', 'T02-ambient'),
            ('panel_id', 'T05'), ('sensor_type', []), ('sensor_type', 'unknown'),
        ):
            with self.subTest(key=key, value=value):
                message = ambient_message()
                message[key] = value
                with self.assertRaises(ValueError):
                    validate(message)

    def test_requires_utc_timestamp(self):
        for timestamp in (None, 'invalid', '2026-10-18T10:00:00', '2026-10-18T10:00:00+03:00'):
            with self.subTest(timestamp=timestamp):
                message = ambient_message()
                message['timestamp'] = timestamp
                with self.assertRaises(ValueError):
                    validate(message)

    def test_rejects_missing_or_extra_measurement_fields(self):
        for values in ({}, {'temperature_c': 23}, {'temperature_c': 23, 'humidity_pct': 45, 'extra': 1}):
            with self.subTest(values=values):
                message = ambient_message()
                message['measurements'] = values
                with self.assertRaises(ValueError):
                    validate(message)

    def test_rejects_nonnumeric_and_nonfinite_measurements(self):
        for value in (True, '23', None, math.nan, math.inf, -math.inf, 10 ** 400):
            with self.subTest(value=repr(value)[:30]):
                message = ambient_message()
                message['measurements']['temperature_c'] = value
                with self.assertRaises(ValueError):
                    validate(message)

    def test_rejects_nonobject_messages_and_missing_metadata(self):
        for message in ([], None, 'text', {}):
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    validate(message)

    def test_encoding_is_utf8_json_with_one_newline(self):
        message = ambient_message()
        payload = encode(message)
        self.assertIsInstance(payload, bytes)
        self.assertTrue(payload.endswith(b'\n'))
        self.assertEqual(payload.count(b'\n'), 1)
        self.assertEqual(json.loads(payload.decode('utf-8')), message)
