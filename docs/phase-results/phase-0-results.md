# Phase 0 – INA228 Hardware Validation and Characterisation

## Objective

Validate the hardware assumptions before beginning application development.

## Completed

- Raspberry Pi Zero 2 W configured.
- SSH operational.
- I2C operational.
- INA228 detected at 0x40.
- Manufacturer ID verified.
- Device ID verified.
- Baseline capture implemented.
- Configuration system implemented.
- Initial characterisation completed.

## Key Decisions

- 15 mΩ shunt selected.
- VSHUNT-derived current selected as primary measurement path.
- INA228 calibrated current retained for diagnostics.
- No automatic ranging in Version 1.

## Outcome

The hardware platform has been proven sufficiently for progression to Phase 1.

## Status

COMPLETE – PASSED
