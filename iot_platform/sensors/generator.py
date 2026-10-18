"""Choose a sensor model and add stable identity, sequence and sample time."""

import random

from ..connections.protocol import FIELDS, PANELS, utc_now
from .ambient import AmbientSensor
from .connection_temperature import ConnectionTemperatureSensor
from .electrical import ElectricalSensor

MODELS = {
    "electrical": ElectricalSensor,
    "connections": ConnectionTemperatureSensor,
    "ambient": AmbientSensor,
}


class Generator:
    def __init__(self, panel, kind):
        self.panel, self.kind = panel, kind
        seed = 1000 + PANELS.index(panel) * 10 + list(FIELDS).index(kind)
        self.sensor = MODELS[kind](random.Random(seed), panel)
        self.sequence = 0

    def sample(self, elapsed_s):
        values = self.sensor.measure(elapsed_s)
        message = dict(schema_version=1, panel_id=self.panel,
                       sensor_id="{}-{}".format(self.panel, self.kind), sensor_type=self.kind,
                       timestamp=utc_now(), sequence=self.sequence, measurements=values)
        self.sequence += 1
        return message
