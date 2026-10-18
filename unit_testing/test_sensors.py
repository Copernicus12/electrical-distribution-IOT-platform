"""Sensor calculations tested without processes, sockets or real-time waits."""

import unittest
from unittest.mock import Mock, patch

from iot_platform.sensors.ambient import AmbientSensor
from iot_platform.sensors.connection_temperature import ConnectionTemperatureSensor
from iot_platform.sensors.electrical import ElectricalSensor
from iot_platform.sensors.generator import Generator


class ElectricalSensorTests(unittest.TestCase):
    def setUp(self):
        self.sensor = ElectricalSensor(Mock(uniform=Mock(return_value=0)), "T01")

    def test_total_three_phase_power_and_energy_units(self):
        # 3 × 230 V × 12 A × 0.95 = 7866 W; over 1 hour => 7.866 kWh.
        values = self.sensor.measure(3600)
        self.assertAlmostEqual(values["active_power_w"], 7866)
        self.assertAlmostEqual(values["energy_kwh"], 7.866)

    def test_energy_accumulates_across_samples(self):
        self.sensor.measure(1800)
        self.assertAlmostEqual(self.sensor.measure(1800)["energy_kwh"], 7.866)

    def test_first_sample_has_power_but_zero_energy(self):
        values = self.sensor.measure(0)
        self.assertGreater(values["active_power_w"], 0)
        self.assertEqual(values["energy_kwh"], 0)


class TemperatureSensorTests(unittest.TestCase):
    def test_nominal_starting_values_without_noise(self):
        noise = Mock(uniform=Mock(return_value=0))
        self.assertEqual(AmbientSensor(noise, "T01").measure(1),
                         {"temperature_c": 23, "humidity_pct": 45})
        self.assertEqual(ConnectionTemperatureSensor(noise, "T01").measure(1), {"temperature_c": 35})

    def test_repeated_drift_stays_within_nominal_limits(self):
        for drift, ambient_expected, connection_expected in (
            (1, {"temperature_c": 30, "humidity_pct": 65}, 50),
            (-1, {"temperature_c": 18, "humidity_pct": 30}, 20),
        ):
            with self.subTest(drift=drift):
                noise = Mock()
                noise.uniform.side_effect = lambda low, high: high if drift > 0 else low
                ambient = AmbientSensor(noise, "T01")
                connections = ConnectionTemperatureSensor(noise, "T01")
                for _ in range(500):
                    ambient_values = ambient.measure(1)
                    connection_values = connections.measure(1)
                self.assertEqual(ambient_values, ambient_expected)
                self.assertEqual(connection_values["temperature_c"], connection_expected)


class GeneratorTests(unittest.TestCase):
    def test_same_sensor_and_seed_reproduce_measurements(self):
        for panel in ("T01", "T02", "T03", "T04"):
            for kind in ("electrical", "connections", "ambient"):
                with self.subTest(panel=panel, kind=kind):
                    first, second = Generator(panel, kind), Generator(panel, kind)
                    for elapsed in (0, 1, 2):
                        self.assertEqual(first.sample(elapsed)["measurements"], second.sample(elapsed)["measurements"])

    def test_distinct_panels_have_distinct_random_streams(self):
        self.assertNotEqual(Generator("T01", "ambient").sample(0)["measurements"],
                            Generator("T02", "ambient").sample(0)["measurements"])

    @patch("iot_platform.sensors.generator.utc_now", return_value="2026-10-18T10:00:00Z")
    def test_sample_identity_time_and_increasing_sequence(self, clock):
        generator = Generator("T03", "ambient")
        first, second = generator.sample(0), generator.sample(1)
        self.assertEqual(first["sensor_id"], "T03-ambient")
        self.assertEqual(first["panel_id"], "T03")
        self.assertEqual(first["sensor_type"], "ambient")
        self.assertEqual(first["schema_version"], 1)
        self.assertEqual(first["timestamp"], clock.return_value)
        self.assertEqual([first["sequence"], second["sequence"]], [0, 1])
