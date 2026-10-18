"""Latest-value grouping and atomic save policy, with filesystem calls mocked."""

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from iot_platform.gateway.storage import TelemetrySnapshot
from unit_testing.fixtures import ambient_record


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = TelemetrySnapshot('unused/telemetry_last_values.json')

    def test_new_session_has_four_panels_with_no_readings(self):
        self.assertEqual(list(self.snapshot.data['panels']), ['T01', 'T02', 'T03', 'T04'])
        self.assertIsNone(self.snapshot.data['updated_at'])
        for sensors in self.snapshot.data['panels'].values():
            self.assertEqual(sensors, {'electrical': None, 'connections': None, 'ambient': None})

    def test_interleaved_updates_preserve_other_panels_and_replace_latest(self):
        self.snapshot.update(ambient_record('T04', 0))
        self.snapshot.update(ambient_record('T01', 0))
        self.snapshot.update(ambient_record('T04', 1))
        panels = self.snapshot.data['panels']
        self.assertEqual(panels['T01']['ambient']['sequence'], 0)
        self.assertEqual(panels['T04']['ambient']['sequence'], 1)
        self.assertIsNone(panels['T02']['ambient'])
        self.assertEqual(self.snapshot.data['updated_at'], '2026-10-18T10:00:01Z')

    def test_display_rounding_does_not_mutate_original_measurements(self):
        record = ambient_record()
        original = deepcopy(record)
        self.snapshot.update(record)
        values = self.snapshot.data['panels']['T01']['ambient']['measurements']
        self.assertEqual(values['temperature_c'], 23.1235)
        self.assertEqual(record, original)

    def test_atomic_save_replaces_target_only_after_complete_write(self):
        output = MagicMock()
        output.name = 'unused/staged.tmp'
        with patch.object(Path, 'mkdir'), \
                patch('iot_platform.gateway.storage.tempfile.NamedTemporaryFile') as temporary, \
                patch('iot_platform.gateway.storage.json.dump') as dump, \
                patch('iot_platform.gateway.storage.os.replace') as replace, \
                patch('iot_platform.gateway.storage.os.path.exists', return_value=False):
            temporary.return_value.__enter__.return_value = output
            dump.side_effect = lambda *args, **kwargs: replace.assert_not_called()
            self.snapshot.save()
            dump.assert_called_once_with(self.snapshot.data, output, indent=2, ensure_ascii=False, allow_nan=False)
            output.write.assert_called_once_with('\n')
            replace.assert_called_once_with(output.name, self.snapshot.path)

    def test_write_failure_keeps_previous_target_and_cleans_temporary_file(self):
        output = MagicMock()
        output.name = 'unused/staged.tmp'
        with patch.object(Path, 'mkdir'), \
                patch('iot_platform.gateway.storage.tempfile.NamedTemporaryFile') as temporary, \
                patch('iot_platform.gateway.storage.json.dump', side_effect=OSError('disk full')), \
                patch('iot_platform.gateway.storage.os.replace') as replace, \
                patch('iot_platform.gateway.storage.os.path.exists', return_value=True), \
                patch('iot_platform.gateway.storage.os.unlink') as unlink:
            temporary.return_value.__enter__.return_value = output
            with self.assertRaises(OSError):
                self.snapshot.save()
            replace.assert_not_called()
            unlink.assert_called_once_with(output.name)
