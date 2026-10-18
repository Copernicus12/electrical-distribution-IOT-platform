"""A compact, readable view of the latest telemetry for each panel."""

import json
import os
from pathlib import Path
import tempfile

from ..connections.protocol import FIELDS, PANELS


def last_values_path(history_path):
    """Keep readable last values beside the history, with a distinct filename."""
    history_path = Path(history_path)
    return history_path.with_name(history_path.stem + "_last_values.json")


class TelemetrySnapshot:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {
            "updated_at": None,
            "panels": {panel: {kind: None for kind in FIELDS} for panel in PANELS},
        }

    def update(self, record):
        self.data["updated_at"] = record["received_at"]
        self.data["panels"][record["panel_id"]][record["sensor_type"]] = {
            "timestamp": record["timestamp"],
            "received_at": record["received_at"],
            "sequence": record["sequence"],
            "measurements": {
                name: round(value, 4) if isinstance(value, float) else value
                for name, value in record["measurements"].items()
            },
        }

    def save(self):
        # Replace the entire file atomically so readers never see partial JSON.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=self.path.name + ".", suffix=".tmp", delete=False) as output:
                temporary = output.name
                json.dump(self.data, output, indent=2, ensure_ascii=False, allow_nan=False)
                output.write("\n")
            os.replace(temporary, self.path)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)
