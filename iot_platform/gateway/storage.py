"""A compact, readable view of the latest telemetry for each panel."""

import json
import os
from pathlib import Path
import tempfile
import sqlite3

from ..connections.protocol import FIELDS, PANELS


class MessageInbox:
    """Durable message-ID deduplication for transport retries."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.database = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS received_messages "
            "(message_id TEXT PRIMARY KEY, received_at TEXT NOT NULL)"
        )
        self.database.commit()

    def remember(self, message_id, received_at):
        with self.database:
            cursor = self.database.execute(
                "INSERT OR IGNORE INTO received_messages(message_id, received_at) VALUES (?, ?)",
                (message_id, received_at),
            )
        return cursor.rowcount == 1

    def contains(self, message_id):
        return self.database.execute(
            "SELECT 1 FROM received_messages WHERE message_id = ?", (message_id,)
        ).fetchone() is not None

    def close(self):
        self.database.close()


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
            "anomalies": record.get("anomalies", []),
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
