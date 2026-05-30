# INA228 Characterisation Notes

## Hardware

- Raspberry Pi Zero 2 W
- INA228 module at I2C address 0x40
- 15 mΩ shunt

## Phase 0 Findings

Identity successfully verified.

Observed:

- Manufacturer ID present.
- Device ID present.
- Register access stable.

## Current Measurement Strategy

Two methods were evaluated.

### Method 1: VSHUNT derived current

Current = VSHUNT / RSHUNT

This is the primary measurement path.

Advantages:

- Simple.
- Directly traceable.
- Easy to validate.

### Method 2: CURRENT register

Current = CURRENT_RAW × CURRENT_LSB

Retained for diagnostics.

Advantages:

- Uses INA228 calibration engine.

Disadvantages:

- Additional scaling complexity.
- Requires validation against direct shunt calculations.

## Future Work

- Characterise low-current performance into the µA region.
- Record offset drift.
- Record temperature effects.
- Compare calibrated and VSHUNT-derived current over a wider range.
- Establish practical minimum detectable current.
