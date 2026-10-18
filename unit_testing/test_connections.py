"""TCP retry policy with mocked sockets, time, stop event and sensor output."""

import unittest
from unittest.mock import Mock, call, patch

from iot_platform.connections.client import run_sensor


class ClientTests(unittest.TestCase):
    def setUp(self):
        for target in ('signal.signal', 'logging.basicConfig', 'LOG'):
            mock = patch('iot_platform.connections.client.' + target)
            mock.start()
            self.addCleanup(mock.stop)
        self.stop = Mock()
        self.stop.is_set.return_value = False

    @patch('iot_platform.connections.client.socket.create_connection', side_effect=OSError('offline'))
    def test_retry_delay_grows_and_is_capped_without_sleeping(self, connect):
        self.stop.wait.side_effect = [False, False, False, False, True]
        run_sensor('T01', 'ambient', '127.0.0.1', 9000, self.stop)
        self.assertEqual(self.stop.wait.call_args_list, [call(1), call(2), call(4), call(5), call(5)])
        self.assertEqual(connect.call_count, 5)

    @patch('iot_platform.connections.client.time.monotonic', side_effect=[10.0, 11.0])
    @patch('iot_platform.connections.client.encode', return_value=b'{}\n')
    @patch('iot_platform.connections.client.Generator')
    @patch('iot_platform.connections.client.socket.create_connection')
    def test_success_resets_retry_delay_and_samples_elapsed_time(self, connect, generator, encode, clock):
        connection = Mock()
        connection.sendall.side_effect = [None, OSError('disconnected')]
        context = Mock()
        context.__enter__ = Mock(return_value=connection)
        context.__exit__ = Mock(return_value=False)
        connect.side_effect = [OSError('offline'), OSError('offline'), context]
        self.stop.wait.side_effect = [False, False, False, True]
        run_sensor('T01', 'ambient', '127.0.0.1', 9000, self.stop)
        # Retry 1s, retry 2s, normal 1s sampling interval, retry reset to 1s.
        self.assertEqual(self.stop.wait.call_args_list, [call(1), call(2), call(1), call(1)])
        self.assertEqual(generator.return_value.sample.call_args_list, [call(0), call(1)])
        self.assertEqual(connection.sendall.call_args_list, [call(b'{}\n'), call(b'{}\n')])
        context.__exit__.assert_called_once()
