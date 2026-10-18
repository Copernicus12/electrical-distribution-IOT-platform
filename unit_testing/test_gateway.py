"""Gateway message processing in memory, without a TCP listener or disk writes."""

import io
import json
import unittest
from unittest.mock import Mock, patch

from iot_platform.gateway.service import Gateway
from unit_testing.fixtures import ambient_message


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.snapshot = Mock()
        # Test processing independently of network and protocol validation.
        transport = patch('iot_platform.gateway.service.TCPServer')
        transport.start()
        self.addCleanup(transport.stop)
        validator = patch('iot_platform.gateway.service.validate', side_effect=lambda message: message)
        self.validate = validator.start()
        self.addCleanup(validator.stop)
        clock = patch('iot_platform.gateway.service.utc_now', return_value='2026-10-18T10:00:01Z')
        clock.start()
        self.addCleanup(clock.stop)
        self.gateway = Gateway(self.output, self.snapshot)

    def test_valid_message_is_stored_with_reception_time(self):
        message = ambient_message()
        self.gateway.accept(json.dumps(message).encode())
        record = json.loads(self.output.getvalue())
        self.assertEqual(record, dict(message, received_at='2026-10-18T10:00:01Z'))
        self.assertEqual(self.gateway.count, 1)
        self.assertEqual(self.gateway.latest, {'T01-ambient': message})
        self.snapshot.update.assert_called_once_with(record)
        self.snapshot.save.assert_called_once_with()

    def test_new_sample_replaces_latest_but_preserves_history(self):
        for sequence in (0, 1):
            self.gateway.accept(json.dumps(ambient_message(sequence=sequence)))
        records = [json.loads(line) for line in self.output.getvalue().splitlines()]
        self.assertEqual([record['sequence'] for record in records], [0, 1])
        self.assertEqual(self.gateway.latest['T01-ambient']['sequence'], 1)
        self.assertEqual(self.gateway.count, 2)

    def test_rejected_message_does_not_change_state_or_storage(self):
        self.validate.side_effect = ValueError('invalid message')
        with self.assertRaises(ValueError):
            self.gateway.accept(json.dumps(ambient_message()))
        self.assertEqual(self.output.getvalue(), '')
        self.assertEqual(self.gateway.count, 0)
        self.assertEqual(self.gateway.latest, {})
        self.snapshot.update.assert_not_called()
        self.snapshot.save.assert_not_called()

    def test_malformed_json_does_not_reach_validation(self):
        with self.assertRaises(ValueError):
            self.gateway.accept(b'not JSON')
        self.validate.assert_not_called()
        self.assertEqual(self.output.getvalue(), '')
        self.snapshot.save.assert_not_called()
