from __future__ import annotations

import threading
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HistorySample:
    timestamp_utc: str
    elapsed_s: float
    current_a: float
    power_w: float
    bus_v: float


class HistoryBuffer:
    def __init__(self, max_samples: int = 50000) -> None:
        self.lock = threading.Lock()
        self.samples: deque[HistorySample] = deque(maxlen=max_samples)

    def append(
        self,
        *,
        timestamp_utc: str,
        elapsed_s: float,
        current_a: float,
        power_w: float,
        bus_v: float,
    ) -> None:
        sample = HistorySample(
            timestamp_utc=timestamp_utc,
            elapsed_s=elapsed_s,
            current_a=current_a,
            power_w=power_w,
            bus_v=bus_v,
        )
        with self.lock:
            self.samples.append(sample)

    def clear(self) -> None:
        with self.lock:
            self.samples.clear()

    def snapshot(self, range_s: float | None = None) -> dict[str, Any]:
        with self.lock:
            samples = list(self.samples)

        if range_s is not None and samples:
            end_elapsed_s = samples[-1].elapsed_s
            start_elapsed_s = max(0.0, end_elapsed_s - range_s)
            samples = [sample for sample in samples if sample.elapsed_s >= start_elapsed_s]

        return {
            "count": len(samples),
            "samples": [asdict(sample) for sample in samples],
        }
