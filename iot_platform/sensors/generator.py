"""Choose a sensor model and add stable identity, sequence and sample time."""

import random
import uuid

from ..connections.protocol import ALL_FIELDS, PANELS, utc_now
from .ambient import AmbientSensor
from .connection_temperature import ConnectionTemperatureSensor
from .electrical import ElectricalSensor
from .equipment import EquipmentSensor
from .heating import HeatingSensor
from .generation import GenerationSensor

MODELS = {
    "electrical": ElectricalSensor,
    "connections": ConnectionTemperatureSensor,
    "ambient": AmbientSensor,
    "equipment": EquipmentSensor,
    "heating": HeatingSensor,
    "generation": GenerationSensor,
}


class Generator:
    def __init__(self, panel, kind):
        self.panel, self.kind = panel, kind
        seed = 1000 + PANELS.index(panel) * 10 + list(ALL_FIELDS).index(kind)
        self.sensor = MODELS[kind](random.Random(seed), panel)
        self.sequence = 0

    def sample(self, elapsed_s, measurements=None, timestamp=None):
        values = self.sensor.measure(elapsed_s) if measurements is None else dict(measurements)
        if set(values) != set(ALL_FIELDS[self.kind]):
            raise ValueError("unexpected measurement fields for {}".format(self.kind))
        message = dict(schema_version=1, panel_id=self.panel,
                       sensor_id="{}-{}".format(self.panel, self.kind), sensor_type=self.kind,
                       timestamp=utc_now() if timestamp is None else timestamp,
                       sequence=self.sequence, message_id=str(uuid.uuid4()), measurements=values)
        self.sequence += 1
        return message
