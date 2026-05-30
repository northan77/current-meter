from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardState:
    timestamp_utc: str = ""
    elapsed_s: float = 0.0
    bus_v: float = 0.0
    shunt_v: float = 0.0
    current_a: float = 0.0
    current_avg_a: float = 0.0
    current_rolling_avg_a: float = 0.0
    current_min_a: float = 0.0
    current_max_a: float = 0.0
    power_w: float = 0.0
    power_avg_w: float = 0.0
    charge_mah: float = 0.0
    energy_wh: float = 0.0
    expected_capacity_mah: float = 0.0
    used_capacity_mah: float = 0.0
    remaining_capacity_mah: float = 0.0
    remaining_capacity_percent: float = 0.0
    runtime_remaining_s: float = 0.0
    runtime_total_s: float = 0.0
    die_temp_c: float = 0.0
    status: str = "starting"
    overload: bool = False
    warning: bool = False
    sample_count: int = 0
    sample_rate_hz: float = 2.0
    logging_enabled: bool = True
    last_update_utc: str = ""
    error: str = ""
    offline_reason: str = ""
    recovery_attempts: int = 0
    consecutive_failures: int = 0
