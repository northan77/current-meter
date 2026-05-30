from __future__ import annotations

import time
import yaml

from config import load_config, parse_i2c_address
from csv_logger import CsvLogger
from ina228 import INA228
from measurement import Measurement


def main() -> int:
    cfg = load_config()

    with open('logger_config.yaml', 'r', encoding='utf-8') as f:
        logger_cfg = yaml.safe_load(f)

    sample_rate_hz = logger_cfg['logging']['sample_rate_hz']
    csv_path = logger_cfg['logging']['csv_path']

    warning_current_a = logger_cfg['limits']['warning_current_a']
    overload_current_a = logger_cfg['limits']['overload_current_a']

    bus = int(cfg['i2c']['bus'])
    address = parse_i2c_address(cfg['i2c']['address'])
    shunt_ohms = float(cfg['shunt']['resistance_ohms'])

    csv_log = CsvLogger(csv_path)

    with INA228(bus=bus, address=address, shunt_ohms=shunt_ohms) as ina:
        ina.configure()

        print('Phase 1 logger running. Ctrl+C to stop.')

        first = True

        while True:
            sample = ina.read_simple_measurement(shunt_ohms=shunt_ohms)

            measurement = Measurement.from_ina228_sample(
                sample,
                max_current_a=overload_current_a,
                warning_current_a=warning_current_a,
            )

            row = measurement.as_csv_row()

            if first:
                csv_log.write_header_if_needed(list(row.keys()))
                first = False

            csv_log.append(row)

            print(
                f"{measurement.current_a:.6f} A | "
                f"{measurement.bus_v:.4f} V | "
                f"{measurement.power_w:.6f} W | "
                f"{measurement.status}"
            )

            time.sleep(1.0 / sample_rate_hz)


if __name__ == '__main__':
    raise SystemExit(main())
