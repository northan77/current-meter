from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Measurement:
    """Single INA228 measurement sample used by the Phase 1 logger."""

    timestamp_utc: str
    bus_v: float
    shunt_v: float
    current_a: float
    power_w: float
    die_temp_c: float
    status: str
    overload: bool
    warning: bool

    @classmethod
    def from_ina228_sample(
        cls,
        sample: dict[str, float],
        max_current_a: float,
        warning_current_a: float,
    ) -> "Measurement":
        current_a = float(sample["current_a_simple"])
        abs_current_a = abs(current_a)
        overload = abs_current_a >= max_current_a
        warning = abs_current_a >= warning_current_a

        if overload:
            status = "overload"
        elif warning:
            status = "warning"
        else:
            status = "ok"

        return cls(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            bus_v=float(sample["bus_v"]),
            shunt_v=float(sample["shunt_v"]),
            current_a=current_a,
            power_w=float(sample["power_w_simple"]),
            die_temp_c=float(sample["die_temp_c"]),
            status=status,
            overload=overload,
            warning=warning,
        )

    def as_csv_row(self) -> dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "bus_v": self.bus_v,
            "shunt_v": self.shunt_v,
            "current_a": self.current_a,
            "power_w": self.power_w,
            "die_temp_c": self.die_temp_c,
            "status": self.status,
            "overload": int(self.overload),
            "warning": int(self.warning),
        }
