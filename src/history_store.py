import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _default_history_path():
    configured = os.environ.get("PERFECTDRAFT_HISTORY_DB")
    if configured:
        return configured

    data_dir = Path("/data")
    if data_dir.exists():
        return str(data_dir / "history.db")

    return str(Path(__file__).resolve().parent.parent / "data" / "history.db")


class HistoryStore:
    def __init__(self, db_path=None, retention_days=30):
        self.db_path = db_path or _default_history_path()
        self.retention_days = retention_days
        self._lock = threading.Lock()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS machine_history (
                    timestamp TEXT NOT NULL,
                    machine_id TEXT,
                    temperature REAL,
                    target_temperature REAL,
                    keg_volume_liters REAL,
                    keg_volume_pct REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_machine_history_timestamp ON machine_history(timestamp)"
            )

    def record_machine_sample(self, machine_id, machine_info):
        if not machine_info:
            return

        details = machine_info.get("details") or {}
        setting = machine_info.get("setting") or {}
        settings_nested = details.get("settings") or {}

        temperature = self._to_float(details.get("temperature"))
        target_temperature = self._to_float(
            setting.get("temperature", settings_nested.get("temperature"))
        )
        keg_volume_liters = self._to_float(details.get("kegVolume"))
        keg_volume_pct = None
        if keg_volume_liters is not None:
            keg_volume_pct = max(0.0, min(100.0, (keg_volume_liters / 6.0) * 100.0))

        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        sample_time = datetime.now(timezone.utc).isoformat()

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO machine_history (
                    timestamp,
                    machine_id,
                    temperature,
                    target_temperature,
                    keg_volume_liters,
                    keg_volume_pct
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_time,
                    machine_id,
                    temperature,
                    target_temperature,
                    keg_volume_liters,
                    keg_volume_pct,
                ),
            )
            connection.execute("DELETE FROM machine_history WHERE timestamp < ?", (cutoff,))

    def get_recent_history(self, machine_id=None, days=30):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = (
            "SELECT timestamp, machine_id, temperature, target_temperature, keg_volume_liters, keg_volume_pct "
            "FROM machine_history WHERE timestamp >= ?"
        )
        params = [cutoff]
        if machine_id:
            query += " AND machine_id = ?"
            params.append(machine_id)
        query += " ORDER BY timestamp ASC"

        with self._lock, self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    @staticmethod
    def _to_float(value):
        if isinstance(value, (int, float)):
            return float(value)
        return None


history_store = HistoryStore()