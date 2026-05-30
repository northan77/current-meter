from __future__ import annotations

from config import load_config, parse_i2c_address
from ina228 import INA228, format_hex_addresses, scan_i2c_bus


def main() -> int:
    cfg = load_config()
    bus = int(cfg.get("i2c", {}).get("bus", 1))
    address = parse_i2c_address(cfg.get("i2c", {}).get("address", "0x40"))
    shunt_ohms = float(cfg.get("shunt", {}).get("resistance_ohms", 0.1))

    print(f"I2C scan on bus {bus}")
    found = scan_i2c_bus(bus)
    print("Found:", ", ".join(format_hex_addresses(found)) or "nothing")

    if address not in found:
        print(f"Configured INA228 address 0x{address:02X} not found")
        return 2

    with INA228(bus=bus, address=address) as ina:
        ina.configure()
        print("Identity:", ina.read_identity())
        print("Registers:")
        for name, value in ina.read_key_registers().items():
            print(f"  {name:14s} 0x{value:X} ({value})")
        print("Measurement, simple Vshunt/Rshunt conversion:")
        m = ina.read_simple_measurement(shunt_ohms=shunt_ohms)
        for name, value in m.items():
            print(f"  {name:18s} {value:.9f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
