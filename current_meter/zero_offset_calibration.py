from __future__ import annotations

import statistics
import time

from config import load_config, parse_i2c_address
from ina228 import INA228

cfg = load_config()

bus = int(cfg['i2c']['bus'])
address = parse_i2c_address(cfg['i2c']['address'])
shunt = float(cfg['shunt']['resistance_ohms'])

samples = []

with INA228(bus=bus, address=address, shunt_ohms=shunt) as ina:
    ina.configure()

    print('Leave input open circuit and wait...')

    for _ in range(100):
        samples.append(ina.read_simple_current_a())
        time.sleep(0.1)

offset = statistics.fmean(samples)

print()
print(f'Suggested current_zero_offset_a: {offset:.9f}')
