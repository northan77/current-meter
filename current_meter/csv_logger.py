from __future__ import annotations

import csv
from pathlib import Path


class CsvLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def write_header_if_needed(self, fieldnames: list[str]) -> None:
        if self.path.exists():
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def append(self, row: dict) -> None:
        with self.path.open('a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writerow(row)
