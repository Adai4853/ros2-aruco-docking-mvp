"""CSV experiment logger."""

import csv
from pathlib import Path
from typing import Dict


FIELDNAMES = [
    "timestamp_sec",
    "state",
    "marker_found",
    "marker_id",
    "horizontal_error",
    "distance_m",
    "front_obstacle_m",
    "linear_x",
    "angular_z",
    "stop_reason",
]


class CsvLogger:
    def __init__(self, path: str) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        file_is_empty = not self.path.exists() or self.path.stat().st_size == 0
        self._stream = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=FIELDNAMES)
        if file_is_empty:
            self._writer.writeheader()
            self._stream.flush()

    def write(self, row: Dict[str, object]) -> None:
        self._writer.writerow({name: row.get(name, "") for name in FIELDNAMES})
        self._stream.flush()

    def close(self) -> None:
        self._stream.close()
