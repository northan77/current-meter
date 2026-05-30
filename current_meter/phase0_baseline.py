from __future__ import annotations

import argparse
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASELINE_PATH, load_config, parse_i2c_address, save_yaml
from ina228 import INA228, REG, format_hex_addresses, scan_i2c_bus


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def stdev(values: list[float]) -> float | None:
    return statistics.pstdev(values) if len(values) > 1 else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 0 INA228 hardware baseline capture")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--out", default=str(BASELINE_PATH), help="Output baseline YAML path")
    parser.add_argument("--samples", type=int, default=None, help="Number of quick samples to capture")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    bus_no = int(cfg.get("i2c", {}).get("bus", 1))
    address = parse_i2c_address(cfg.get("i2c", {}).get("address", "0x40"))
    shunt_ohms = float(cfg.get("shunt", {}).get("resistance_ohms", 0.015))
    max_current_a = float(cfg.get("shunt", {}).get("max_current_a", 10.0))
    samples = args.samples or int(cfg.get("sampling", {}).get("samples", 20))
    delay_s = float(cfg.get("sampling", {}).get("delay_s", 0.1))

    print("Scanning I2C bus...")
    found = scan_i2c_bus(bus_no)
    print("Found:", ", ".join(format_hex_addresses(found)) or "nothing")

    baseline: dict[str, Any] = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "hardware": cfg.get("hardware", {}),
        "i2c": {
            "bus": bus_no,
            "address": f"0x{address:02X}",
            "detected_addresses": format_hex_addresses(found),
        },
        "shunt": {
            "resistance_ohms": shunt_ohms,
            "max_current_a": max_current_a,
        },
        "acceptance": cfg.get("acceptance", {}),
        "status": "unknown",
        "identity": {},
        "registers": {},
        "calibration_debug": {},
        "quick_samples": {},
    }

    if address not in found:
        baseline["status"] = "ina228_not_detected_at_configured_address"
        save_yaml(baseline, Path(args.out))
        print(f"INA228 not seen at 0x{address:02X}. Check wiring, power, I2C enabled, and address jumpers.")
        print(f"Baseline written to {args.out}")
        return 2

    bus_values: list[float] = []
    shunt_values: list[float] = []
    current_simple_values: list[float] = []
    current_calibrated_values: list[float] = []
    calibration_error_values: list[float] = []
    power_simple_values: list[float] = []
    power_calibrated_values: list[float] = []
    temp_values: list[float] = []

    with INA228(bus=bus_no, address=address) as ina:
        ina.configure()
        baseline["identity"] = ina.read_identity()

        registers = ina.read_key_registers()
        baseline["registers"] = {
            k: f"0x{v:X}" if isinstance(v, int) else v
            for k, v in registers.items()
        }

        config = ina.read_u16(REG.CONFIG)
        adc_config = ina.read_u16(REG.ADC_CONFIG)
        shunt_cal = ina.read_u16(REG.SHUNT_CAL)
        current_raw = ina.read_s20_from_24(REG.CURRENT)
        power_raw = ina.read_u24(REG.POWER)

        baseline["calibration_debug"] = {
            "config_hex": f"0x{config:04X}",
            "adc_config_hex": f"0x{adc_config:04X}",
            "shunt_cal": shunt_cal,
            "current_raw": current_raw,
            "power_raw": power_raw,
            "current_lsb": ina.current_lsb,
        }

        print()
        print("Calibration debug:")
        print(f"  CONFIG      : 0x{config:04X}")
        print(f"  ADC_CONFIG  : 0x{adc_config:04X}")
        print(f"  SHUNT_CAL   : {shunt_cal}")
        print(f"  CURRENT_RAW : {current_raw}")
        print(f"  POWER_RAW   : {power_raw}")
        print(f"  CURRENT_LSB : {ina.current_lsb:.12f} A/bit")
        print()

        for _ in range(samples):
            m = ina.read_simple_measurement(
                shunt_ohms=shunt_ohms,
                current_multiplier=float(cfg.get("calibration", {}).get("current_multiplier", 1.0)),
                voltage_multiplier=float(cfg.get("calibration", {}).get("voltage_multiplier", 1.0)),
                current_zero_offset_a=float(cfg.get("calibration", {}).get("current_zero_offset_a", 0.0)),
            )

            bus_values.append(m["bus_v"])
            shunt_values.append(m["shunt_v"])
            current_simple_values.append(m["current_a_simple"])
            power_simple_values.append(m["power_w_simple"])
            temp_values.append(m["die_temp_c"])

            if "current_a_calibrated" in m:
                current_calibrated_values.append(m["current_a_calibrated"])

            if "current_calibration_error_pct" in m:
                calibration_error_values.append(m["current_calibration_error_pct"])

            if "power_w_calibrated" in m:
                power_calibrated_values.append(m["power_w_calibrated"])

            time.sleep(delay_s)

    baseline["status"] = "ina228_detected"
    baseline["quick_samples"] = {
        "sample_count": samples,
        "delay_s": delay_s,
        "bus_v_mean": mean(bus_values),
        "bus_v_stdev": stdev(bus_values),
        "shunt_v_mean": mean(shunt_values),
        "shunt_v_stdev": stdev(shunt_values),
        "current_a_simple_mean": mean(current_simple_values),
        "current_a_simple_stdev": stdev(current_simple_values),
        "current_a_calibrated_mean": mean(current_calibrated_values),
        "current_calibrated_stdev": stdev(current_calibrated_values),
        "current_calibration_error_pct_mean": mean(calibration_error_values),
        "power_w_simple_mean": mean(power_simple_values),
        "power_w_calibrated_mean": mean(power_calibrated_values),
        "die_temp_c_mean": mean(temp_values),
    }

    save_yaml(baseline, Path(args.out))

    print(f"INA228 detected at 0x{address:02X}")
    print(f"Bus voltage mean: {baseline['quick_samples']['bus_v_mean']:.6f} V")
    print(f"Simple current mean: {baseline['quick_samples']['current_a_simple_mean']:.9f} A")

    if baseline["quick_samples"]["current_a_calibrated_mean"] is not None:
        print(f"Calibrated current mean: {baseline['quick_samples']['current_a_calibrated_mean']:.9f} A")

    if baseline["quick_samples"]["current_calibration_error_pct_mean"] is not None:
        print(f"Calibration error mean: {baseline['quick_samples']['current_calibration_error_pct_mean']:.3f} %")

    print(f"Baseline written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())