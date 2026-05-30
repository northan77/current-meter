from __future__ import annotations

import time
from pathlib import Path

import yaml

from config import ROOT, load_config, parse_i2c_address
from csv_logger import CsvLogger
from ina228 import INA228
from measurement import Measurement

LOGGER_CONFIG_PATH = ROOT / "logger_config.yaml"


def load_logger_config(path: Path = LOGGER_CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    cfg = load_config()
    logger_cfg = load_logger_config()

    sample_rate_hz = float(logger_cfg.get("logging", {}).get("sample_rate_hz", 2.0))
    csv_path = ROOT / str(logger_cfg.get("logging", {}).get("csv_path", "logs/current_meter.csv"))

    warning_current_a = float(logger_cfg.get("limits", {}).get("warning_current_a", 8.0))
    overload_current_a = float(logger_cfg.get("limits", {}).get("overload_current_a", 10.0))

    bus = int(cfg["i2c"]["bus"])
    address = parse_i2c_address(cfg["i2c"]["address"])
    shunt_ohms = float(cfg["shunt"]["resistance_ohms"])

    current_multiplier = float(cfg.get("calibration", {}).get("current_multiplier", 1.0))
    voltage_multiplier = float(cfg.get("calibration", {}).get("voltage_multiplier", 1.0))
    current_zero_offset_a = float(cfg.get("calibration", {}).get("current_zero_offset_a", 0.0))

    csv_log = CsvLogger(csv_path)

    sample_count = 0
    charge_mah = 0.0
    energy_wh = 0.0
    current_sum_a = 0.0
    power_sum_w = 0.0

    start_time = time.monotonic()
    last_sample_time = start_time

    with INA228(bus=bus, address=address, shunt_ohms=shunt_ohms) as ina:
        ina.configure()

        print("Phase 1 logger running. Ctrl+C to stop.")
        print(f"CSV: {csv_path}")
        print(f"Sample rate: {sample_rate_hz:g} Hz")
        print(f"Zero offset: {current_zero_offset_a:.9f} A")

        first = True

        try:
            while True:
                now = time.monotonic()
                elapsed_s = now - start_time
                dt_s = now - last_sample_time
                last_sample_time = now

                sample = ina.read_simple_measurement(
                    shunt_ohms=shunt_ohms,
                    current_multiplier=current_multiplier,
                    voltage_multiplier=voltage_multiplier,
                    current_zero_offset_a=current_zero_offset_a,
                )

                current_a = float(sample["current_a_simple"])
                power_w = float(sample["power_w_simple"])

                sample_count += 1
                current_sum_a += current_a
                power_sum_w += power_w

                current_avg_a = current_sum_a / sample_count
                power_avg_w = power_sum_w / sample_count

                charge_mah += current_a * (dt_s / 3600.0) * 1000.0
                energy_wh += power_w * (dt_s / 3600.0)

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

                row = measurement.as_csv_row()

                if first:
                    csv_log.write_header_if_needed(list(row.keys()))
                    first = False

                csv_log.append(row)

                print(
                    f"{measurement.current_a:.6f} A | "
                    f"avg {measurement.current_avg_a:.6f} A | "
                    f"{measurement.power_w:.6f} W | "
                    f"{measurement.charge_mah:.6f} mAh | "
                    f"{measurement.energy_wh:.9f} Wh | "
                    f"{measurement.status}"
                )

                sleep_s = max(0.0, (1.0 / sample_rate_hz) - (time.monotonic() - now))
                time.sleep(sleep_s)

        except KeyboardInterrupt:
            runtime_s = time.monotonic() - start_time
            print("\nPhase 1 logger stopped.")
            print(f"Runtime: {runtime_s:.1f} s")
            print(f"Average current: {current_avg_a:.9f} A")
            print(f"Average power: {power_avg_w:.9f} W")
            print(f"Charge: {charge_mah:.9f} mAh")
            print(f"Energy: {energy_wh:.9f} Wh")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
