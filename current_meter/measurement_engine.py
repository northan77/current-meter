from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from config import ROOT, load_config, parse_i2c_address
from csv_logger import CsvLogger
from dashboard_state import DashboardState
from history_buffer import HistoryBuffer
from ina228 import INA228
from measurement import Measurement

LOGGER_CONFIG_PATH = ROOT / "logger_config.yaml"


class MeasurementEngine:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.state = DashboardState()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.reset_requested = False
        self.history = HistoryBuffer()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def reset(self) -> None:
        with self.lock:
            self.reset_requested = True

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return asdict(self.state)

    def history_snapshot(self, range_s: float | None = None) -> dict[str, Any]:
        return self.history.snapshot(range_s=range_s)

    def load_logger_config(self) -> dict[str, Any]:
        if not LOGGER_CONFIG_PATH.exists():
            return {}
        with LOGGER_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _safe_close(ina: INA228 | None) -> None:
        if ina is None:
            return
        try:
            ina.close()
        except Exception:
            pass

    @staticmethod
    def _validate_sample(sample: dict[str, float]) -> None:
        required_keys = (
            "bus_v",
            "shunt_v",
            "current_a_simple",
            "power_w_simple",
            "die_temp_c",
        )
        for key in required_keys:
            value = float(sample[key])
            if not math.isfinite(value):
                raise ValueError(f"Invalid INA228 reading for {key}: {value}")

        if float(sample["bus_v"]) < 0:
            raise ValueError(f"Invalid negative bus voltage: {sample['bus_v']}")

    @staticmethod
    def _battery_metrics(
        charge_mah: float,
        current_avg_a: float,
        expected_capacity_mah: float,
    ) -> dict[str, float]:
        used_capacity_mah = max(0.0, charge_mah)
        remaining_capacity_mah = max(0.0, expected_capacity_mah - used_capacity_mah)

        remaining_capacity_percent = 0.0
        if expected_capacity_mah > 0:
            remaining_capacity_percent = (remaining_capacity_mah / expected_capacity_mah) * 100.0

        average_current_ma = abs(current_avg_a) * 1000.0
        runtime_remaining_s = 0.0
        runtime_total_s = 0.0

        if average_current_ma > 0:
            runtime_remaining_s = (remaining_capacity_mah / average_current_ma) * 3600.0
            runtime_total_s = (expected_capacity_mah / average_current_ma) * 3600.0

        return {
            "used_capacity_mah": used_capacity_mah,
            "remaining_capacity_mah": remaining_capacity_mah,
            "remaining_capacity_percent": remaining_capacity_percent,
            "runtime_remaining_s": runtime_remaining_s,
            "runtime_total_s": runtime_total_s,
        }

    def _mark_offline(
        self,
        reason: str,
        sample_rate_hz: float,
        logging_enabled: bool,
        expected_capacity_mah: float,
        recovery_attempts: int,
        consecutive_failures: int,
    ) -> None:
        now = self._utc_now()
        with self.lock:
            self.state.status = "offline"
            self.state.last_update_utc = now
            self.state.error = reason
            self.state.offline_reason = reason
            self.state.sample_rate_hz = sample_rate_hz
            self.state.logging_enabled = logging_enabled
            self.state.expected_capacity_mah = expected_capacity_mah
            self.state.recovery_attempts = recovery_attempts
            self.state.consecutive_failures = consecutive_failures

    def _handle_reset(
        self,
        loop_start: float,
        rolling_currents: deque[float],
    ) -> tuple[bool, dict[str, Any]]:
        with self.lock:
            if not self.reset_requested:
                return False, {}
            self.reset_requested = False

        rolling_currents.clear()
        self.history.clear()
        return True, {
            "sample_count": 0,
            "charge_mah": 0.0,
            "energy_wh": 0.0,
            "current_sum_a": 0.0,
            "power_sum_w": 0.0,
            "current_min_a": None,
            "current_max_a": None,
            "start_time": loop_start,
            "last_sample_time": loop_start,
        }

    def _run(self) -> None:
        cfg = load_config()
        logger_cfg = self.load_logger_config()

        sample_rate_hz = float(logger_cfg.get("logging", {}).get("sample_rate_hz", 2.0))
        sample_period_s = 1.0 / sample_rate_hz if sample_rate_hz > 0 else 0.5
        csv_path = ROOT / str(logger_cfg.get("logging", {}).get("csv_path", "logs/current_meter.csv"))
        logging_enabled = bool(logger_cfg.get("logging", {}).get("enabled", True))
        rolling_window = int(logger_cfg.get("logging", {}).get("rolling_average_samples", 20))
        rolling_window = max(1, rolling_window)

        expected_capacity_mah = float(
            logger_cfg.get("battery", {}).get("expected_capacity_mah", 400.0)
        )

        warning_current_a = float(logger_cfg.get("limits", {}).get("warning_current_a", 8.0))
        overload_current_a = float(logger_cfg.get("limits", {}).get("overload_current_a", 10.0))

        robustness_cfg = logger_cfg.get("robustness", {})
        reconnect_interval_s = float(robustness_cfg.get("reconnect_interval_s", 2.0))
        reconnect_interval_s = max(0.5, reconnect_interval_s)

        bus = int(cfg["i2c"]["bus"])
        address = parse_i2c_address(cfg["i2c"]["address"])
        shunt_ohms = float(cfg["shunt"]["resistance_ohms"])
        max_current_a = float(cfg["shunt"].get("max_current_a", overload_current_a))

        current_multiplier = float(cfg.get("calibration", {}).get("current_multiplier", 1.0))
        voltage_multiplier = float(cfg.get("calibration", {}).get("voltage_multiplier", 1.0))
        current_zero_offset_a = float(cfg.get("calibration", {}).get("current_zero_offset_a", 0.0))

        csv_log = CsvLogger(csv_path)
        csv_header_written = False

        sample_count = 0
        charge_mah = 0.0
        energy_wh = 0.0
        current_sum_a = 0.0
        power_sum_w = 0.0
        current_min_a: float | None = None
        current_max_a: float | None = None
        rolling_currents: deque[float] = deque(maxlen=rolling_window)

        start_time = time.monotonic()
        last_sample_time = start_time
        ina: INA228 | None = None
        recovery_attempts = 0
        consecutive_failures = 0

        while not self.stop_event.is_set():
            loop_start = time.monotonic()

            did_reset, reset_values = self._handle_reset(loop_start, rolling_currents)
            if did_reset:
                sample_count = reset_values["sample_count"]
                charge_mah = reset_values["charge_mah"]
                energy_wh = reset_values["energy_wh"]
                current_sum_a = reset_values["current_sum_a"]
                power_sum_w = reset_values["power_sum_w"]
                current_min_a = reset_values["current_min_a"]
                current_max_a = reset_values["current_max_a"]
                start_time = reset_values["start_time"]
                last_sample_time = reset_values["last_sample_time"]

            if ina is None:
                recovery_attempts += 1
                try:
                    ina = INA228(
                        bus=bus,
                        address=address,
                        shunt_ohms=shunt_ohms,
                        max_current_a=max_current_a,
                    )
                    ina.configure()
                    ina.read_identity()
                    consecutive_failures = 0
                    with self.lock:
                        self.state.status = "recovering"
                        self.state.error = ""
                        self.state.offline_reason = ""
                        self.state.recovery_attempts = recovery_attempts
                        self.state.consecutive_failures = consecutive_failures
                        self.state.last_update_utc = self._utc_now()
                except Exception as exc:
                    self._safe_close(ina)
                    ina = None
                    consecutive_failures += 1
                    last_sample_time = loop_start
                    self._mark_offline(
                        reason=f"INA228 unavailable: {exc}",
                        sample_rate_hz=sample_rate_hz,
                        logging_enabled=logging_enabled,
                        expected_capacity_mah=expected_capacity_mah,
                        recovery_attempts=recovery_attempts,
                        consecutive_failures=consecutive_failures,
                    )
                    time.sleep(reconnect_interval_s)
                    continue

            try:
                sample = ina.read_simple_measurement(
                    shunt_ohms=shunt_ohms,
                    current_multiplier=current_multiplier,
                    voltage_multiplier=voltage_multiplier,
                    current_zero_offset_a=current_zero_offset_a,
                )
                self._validate_sample(sample)
            except Exception as exc:
                self._safe_close(ina)
                ina = None
                consecutive_failures += 1
                last_sample_time = loop_start
                self._mark_offline(
                    reason=f"INA228 read failed: {exc}",
                    sample_rate_hz=sample_rate_hz,
                    logging_enabled=logging_enabled,
                    expected_capacity_mah=expected_capacity_mah,
                    recovery_attempts=recovery_attempts,
                    consecutive_failures=consecutive_failures,
                )
                time.sleep(reconnect_interval_s)
                continue

            elapsed_s = loop_start - start_time
            dt_s = loop_start - last_sample_time
            last_sample_time = loop_start

            current_a = float(sample["current_a_simple"])
            power_w = float(sample["power_w_simple"])

            sample_count += 1
            current_sum_a += current_a
            power_sum_w += power_w
            current_min_a = current_a if current_min_a is None else min(current_min_a, current_a)
            current_max_a = current_a if current_max_a is None else max(current_max_a, current_a)
            rolling_currents.append(current_a)

            current_avg_a = current_sum_a / sample_count
            power_avg_w = power_sum_w / sample_count
            rolling_avg_a = sum(rolling_currents) / len(rolling_currents)

            charge_mah += current_a * (dt_s / 3600.0) * 1000.0
            energy_wh += power_w * (dt_s / 3600.0)
            battery_metrics = self._battery_metrics(
                charge_mah=charge_mah,
                current_avg_a=current_avg_a,
                expected_capacity_mah=expected_capacity_mah,
            )

            measurement = Measurement.from_ina228_sample(
                sample,
                max_current_a=overload_current_a,
                warning_current_a=warning_current_a,
                elapsed_s=elapsed_s,
                current_avg_a=current_avg_a,
                power_avg_w=power_avg_w,
                charge_mah=charge_mah,
                energy_wh=energy_wh,
            )
            self.history.append(
                timestamp_utc=measurement.timestamp_utc,
                elapsed_s=measurement.elapsed_s,
                current_a=measurement.current_a,
                power_w=measurement.power_w,
                bus_v=measurement.bus_v,
            )

            row = measurement.as_csv_row()
            if logging_enabled:
                if not csv_header_written:
                    csv_log.write_header_if_needed(list(row.keys()))
                    csv_header_written = True
                csv_log.append(row)

            with self.lock:
                self.state = DashboardState(
                    timestamp_utc=measurement.timestamp_utc,
                    elapsed_s=measurement.elapsed_s,
                    bus_v=measurement.bus_v,
                    shunt_v=measurement.shunt_v,
                    current_a=measurement.current_a,
                    current_avg_a=measurement.current_avg_a,
                    current_rolling_avg_a=rolling_avg_a,
                    current_min_a=current_min_a or 0.0,
                    current_max_a=current_max_a or 0.0,
                    power_w=measurement.power_w,
                    power_avg_w=measurement.power_avg_w,
                    charge_mah=measurement.charge_mah,
                    energy_wh=measurement.energy_wh,
                    expected_capacity_mah=expected_capacity_mah,
                    used_capacity_mah=battery_metrics["used_capacity_mah"],
                    remaining_capacity_mah=battery_metrics["remaining_capacity_mah"],
                    remaining_capacity_percent=battery_metrics["remaining_capacity_percent"],
                    runtime_remaining_s=battery_metrics["runtime_remaining_s"],
                    runtime_total_s=battery_metrics["runtime_total_s"],
                    die_temp_c=measurement.die_temp_c,
                    status=measurement.status,
                    overload=measurement.overload,
                    warning=measurement.warning,
                    sample_count=sample_count,
                    sample_rate_hz=sample_rate_hz,
                    logging_enabled=logging_enabled,
                    last_update_utc=measurement.timestamp_utc,
                    error="",
                    offline_reason="",
                    recovery_attempts=recovery_attempts,
                    consecutive_failures=consecutive_failures,
                )

            sleep_s = max(0.0, sample_period_s - (time.monotonic() - loop_start))
            time.sleep(sleep_s)

        self._safe_close(ina)
