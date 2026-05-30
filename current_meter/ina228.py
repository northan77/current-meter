from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from smbus2 import SMBus


@dataclass(frozen=True)
class INA228Registers:
    CONFIG: int = 0x00
    ADC_CONFIG: int = 0x01
    SHUNT_CAL: int = 0x02
    SHUNT_TEMPCO: int = 0x03
    VSHUNT: int = 0x04
    VBUS: int = 0x05
    DIETEMP: int = 0x06
    CURRENT: int = 0x07
    POWER: int = 0x08
    ENERGY: int = 0x09
    CHARGE: int = 0x0A
    DIAG_ALRT: int = 0x0B
    MANUFACTURER_ID: int = 0x3E
    DEVICE_ID: int = 0x3F


REG = INA228Registers()


def _twos_complement(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return value - (1 << bits) if value & sign_bit else value


class INA228:
    """
    Minimal INA228 driver for the current-meter project.

    Current is read in two ways:

    1. VSHUNT-derived current:
       current = vshunt / shunt_ohms

       This is the value we trust for the meter, because it directly follows the
       measured shunt voltage and the known shunt resistor.

    2. INA228 calibrated CURRENT register:
       current = current_raw * current_lsb

       This is kept as a diagnostic so we can verify SHUNT_CAL behaviour.
    """

    VSHUNT_LSB_HIGH_RANGE_V = 312.5e-9
    VSHUNT_LSB_LOW_RANGE_V = 78.125e-9
    VBUS_LSB_V = 195.3125e-6
    DIETEMP_LSB_C = 0.0078125
    SHUNT_CAL_SCALE = 13107.2e6
    CURRENT_REGISTER_STEPS = 2 ** 19
    MAX_SHUNT_CAL = 0x7FFF

    def __init__(
        self,
        bus: int = 1,
        address: int = 0x40,
        shunt_ohms: float = 0.015,
        max_current_a: float = 10.0,
    ) -> None:
        if shunt_ohms <= 0:
            raise ValueError("shunt_ohms must be greater than 0")
        if max_current_a <= 0:
            raise ValueError("max_current_a must be greater than 0")

        self.bus_no = bus
        self.address = address
        self.shunt_ohms = shunt_ohms
        self.max_current_a = max_current_a
        self.current_lsb = max_current_a / self.CURRENT_REGISTER_STEPS
        self.bus = SMBus(bus)

    def close(self) -> None:
        self.bus.close()

    def __enter__(self) -> "INA228":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def read_u16(self, register: int) -> int:
        data = self.bus.read_i2c_block_data(self.address, register, 2)
        return (data[0] << 8) | data[1]

    def read_s16(self, register: int) -> int:
        return _twos_complement(self.read_u16(register), 16)

    def write_u16(self, register: int, value: int) -> None:
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"16-bit register value out of range: {value}")

        self.bus.write_i2c_block_data(
            self.address,
            register,
            [(value >> 8) & 0xFF, value & 0xFF],
        )

    def read_u24(self, register: int) -> int:
        data = self.bus.read_i2c_block_data(self.address, register, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def read_u20_from_24(self, register: int) -> int:
        return self.read_u24(register) >> 4

    def read_s20_from_24(self, register: int) -> int:
        raw20 = self.read_u20_from_24(register)
        return _twos_complement(raw20, 20)

    def read_u40(self, register: int) -> int:
        data = self.bus.read_i2c_block_data(self.address, register, 5)
        value = 0
        for byte in data:
            value = (value << 8) | byte
        return value

    def read_s40(self, register: int) -> int:
        return _twos_complement(self.read_u40(register), 40)

    def ping(self) -> bool:
        try:
            self.read_u16(REG.DEVICE_ID)
            return True
        except OSError:
            return False
    def calculate_shunt_cal(self) -> int:
        shunt_cal = round(
            self.SHUNT_CAL_SCALE * self.current_lsb * self.shunt_ohms
        )

        if shunt_cal <= 0:
            raise ValueError("Calculated SHUNT_CAL is zero")

        if shunt_cal > self.MAX_SHUNT_CAL:
            raise ValueError(
                f"Calculated SHUNT_CAL {shunt_cal} is above {self.MAX_SHUNT_CAL}. "
                "Reduce max_current_a or shunt_ohms."
            )

        return int(shunt_cal)

    def configure(self) -> None:
        # CONFIG bit 4 = ADCRANGE.
        # 0 means +/-163.84 mV range, with 312.5 nV/bit VSHUNT LSB.
        # This is the right default for the onboard 15 milliohm shunt.
        self.write_u16(REG.CONFIG, 0x0000)

        # Existing known-good ADC configuration from Phase 0.
        self.write_u16(REG.ADC_CONFIG, 0xFB68)

        self.write_u16(REG.SHUNT_CAL, self.calculate_shunt_cal())

        time.sleep(0.1)

    def read_identity(self) -> dict[str, int]:
        return {
            "manufacturer_id": self.read_u16(REG.MANUFACTURER_ID),
            "device_id": self.read_u16(REG.DEVICE_ID),
        }

    def read_key_registers(self) -> dict[str, int]:
        return {
            "config": self.read_u16(REG.CONFIG),
            "adc_config": self.read_u16(REG.ADC_CONFIG),
            "shunt_cal": self.read_u16(REG.SHUNT_CAL),
            "shunt_tempco": self.read_u16(REG.SHUNT_TEMPCO),
            "vshunt_raw20": self.read_s20_from_24(REG.VSHUNT),
            "vbus_raw20": self.read_u20_from_24(REG.VBUS),
            "dietemp_raw": self.read_s16(REG.DIETEMP),
            "current_raw20": self.read_s20_from_24(REG.CURRENT),
            "power_raw24": self.read_u24(REG.POWER),
            "diag_alrt": self.read_u16(REG.DIAG_ALRT),
        }

    def raw_registers(self) -> dict[str, int]:
        return self.read_key_registers()

    def adcrange_low_range_enabled(self) -> bool:
        return bool(self.read_u16(REG.CONFIG) & (1 << 4))

    def vshunt_lsb_v(self) -> float:
        return (
            self.VSHUNT_LSB_LOW_RANGE_V
            if self.adcrange_low_range_enabled()
            else self.VSHUNT_LSB_HIGH_RANGE_V
        )

    def read_vshunt_v(self) -> float:
        return self.read_s20_from_24(REG.VSHUNT) * self.vshunt_lsb_v()

    def read_vbus_v(self) -> float:
        return self.read_u20_from_24(REG.VBUS) * self.VBUS_LSB_V

    def read_die_temp_c(self) -> float:
        return self.read_s16(REG.DIETEMP) * self.DIETEMP_LSB_C

    def read_current_a_calibrated(self) -> float:
        return self.read_s20_from_24(REG.CURRENT) * self.current_lsb

    def read_current_a(self) -> float:
        # Main meter current. This is the proven Phase 0 path.
        return self.read_simple_current_a()

    def read_simple_current_a(self) -> float:
        return self.read_vshunt_v() / self.shunt_ohms

    def read_power_w_calibrated(self) -> float:
        return self.read_u24(REG.POWER) * 3.2 * self.current_lsb

    def read_power_w(self) -> float:
        # Main meter power. This only becomes meaningful when VBUS is connected.
        return self.read_vbus_v() * self.read_current_a()

    def read_simple_measurement(
        self,
        shunt_ohms: float | None = None,
        current_multiplier: float = 1.0,
        voltage_multiplier: float = 1.0,
        current_zero_offset_a: float = 0.0,
    ) -> dict[str, float]:
        actual_shunt = shunt_ohms if shunt_ohms is not None else self.shunt_ohms

        bus_v = self.read_vbus_v() * voltage_multiplier
        shunt_v = self.read_vshunt_v()

        current_a_simple = ((shunt_v / actual_shunt) * current_multiplier) - current_zero_offset_a
        current_a_calibrated = self.read_current_a_calibrated()

        power_w_simple = bus_v * current_a_simple
        power_w_calibrated = self.read_power_w_calibrated()

        calibration_error_pct = 0.0
        if current_a_simple != 0:
            calibration_error_pct = (
                (current_a_calibrated - current_a_simple) / current_a_simple
            ) * 100.0

        return {
            "bus_v": bus_v,
            "shunt_v": shunt_v,
            "current_a_simple": current_a_simple,
            "current_a_calibrated": current_a_calibrated,
            "current_calibration_error_pct": calibration_error_pct,
            "power_w_simple": power_w_simple,
            "power_w_calibrated": power_w_calibrated,
            "die_temp_c": self.read_die_temp_c(),
        }


def scan_i2c_bus(bus_no: int = 1, start: int = 0x03, end: int = 0x77) -> list[int]:
    found: list[int] = []

    with SMBus(bus_no) as bus:
        for addr in range(start, end + 1):
            try:
                bus.write_quick(addr)
                found.append(addr)
            except OSError:
                pass

    return found


def format_hex_addresses(addresses: Iterable[int]) -> list[str]:
    return [f"0x{addr:02X}" for addr in addresses]