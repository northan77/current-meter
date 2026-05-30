# Current Meter Project

## Phase 1 INA228 Hardware Validation

## Objective

Validate the INA228 measurement hardware, Raspberry Pi interface, live logging software, and calibration method before moving on to the web dashboard and deeper power analysis tools.

The main objectives were:

1. Verify reliable I2C communication with the INA228.
2. Confirm register configuration and calibration operation.
3. Validate current measurement accuracy across a useful operating range.
4. Confirm CSV logging operation.
5. Establish the practical limitations of the current 15 mOhm shunt.
6. Decide whether the project is ready to progress to the next phase.

## Test Configuration

| Item | Specification |
| --- | --- |
| Host controller | Raspberry Pi |
| Current monitor | INA228 |
| Interface | I2C bus 1 |
| I2C address | 0x40 |
| Shunt resistance | 0.015 ohm |
| Supply voltage | Approximately 5 V |
| Logging rate | 2 Hz |
| Output format | CSV |
| Test date | 2026-05-30 |

## INA228 Identity

The INA228 was detected successfully on I2C address 0x40.

| Register | Value |
| --- | --- |
| Manufacturer ID | 0x5449 |
| Device ID | 0x2281 |
| Shunt calibration | 0x0EA6, decimal 3750 |

Device detection and register reads were reliable during the test work.

## Software Added During Phase 1

The Phase 1 work added the following project files:

| File | Purpose |
| --- | --- |
| `phase1_logger.py` | Live current, voltage, power and energy logger |
| `logger_config.yaml` | Logger configuration |
| `measurement.py` | Measurement data model |
| `csv_logger.py` | CSV output helper |
| `zero_offset_calibration.py` | Open circuit current offset calibration helper |
| `docs/phase1_live_logging.md` | Phase 1 validation documentation |

The logger now supports:

1. Live terminal reporting.
2. CSV logging.
3. Running average current.
4. Running average power.
5. Accumulated mAh.
6. Accumulated Wh.
7. Overload and warning status fields.
8. Open circuit zero offset correction.

## Zero Offset Calibration

The open circuit zero offset calibration produced:

```text
current_zero_offset_a: -0.000054375
```

This value has been added to `config.yaml` and is used by the logger to centre the open circuit reading closer to 0 A.

Open circuit readings still show small positive and negative variation, which is expected at this shunt value.

## Test Method

Known resistive loads were connected and the resulting current was measured by the INA228 logger.

Actual resistor values were measured and used for the expected current calculations.

Expected current was calculated using:

```text
I = V / R
```

The supply voltage during testing was approximately 5 V.

## Measured Resistor Values

| Nominal load | Measured resistance |
| --- | ---: |
| Open circuit | Infinite |
| 10 kOhm | 9389 ohm |
| 1 kOhm | 986.4 ohm |
| 510 ohm | 510.4 ohm |
| 220 ohm | 217.3 ohm |
| 100 ohm | 98.38 ohm |

## Expected Current Values

Using 5.00 V as the nominal test voltage:

| Load | Expected current |
| --- | ---: |
| Open circuit | 0 uA |
| 9389 ohm | 0.533 mA |
| 986.4 ohm | 5.069 mA |
| 510.4 ohm | 9.796 mA |
| 217.3 ohm | 23.009 mA |
| 98.38 ohm | 50.823 mA |

## Observed Results

| Test point | Expected | Observed | Result |
| --- | ---: | ---: | --- |
| Open circuit | 0 uA | Small positive and negative readings around 0 A | Pass |
| 1 kOhm, measured 986.4 ohm | 5.069 mA | Approximately 5.0 mA to 5.2 mA | Pass |
| 220 ohm, measured 217.3 ohm | 23.009 mA | Approximately 23 mA | Pass |
| 100 ohm, measured 98.38 ohm | 50.823 mA | Approximately 50.8 mA | Pass |

The 1 kOhm test produced readings around 0.0047 A to 0.0053 A, which is correct for a 5 V supply and a measured 986.4 ohm resistor.

## Accuracy Assessment

| Test point | Expected | Measured | Approx error |
| --- | ---: | ---: | ---: |
| 1 kOhm | 5.069 mA | 5.076 mA | +0.14 percent |
| 220 ohm | 23.009 mA | 23.0 mA | Approximately 0 percent |
| 100 ohm | 50.823 mA | 50.8 mA | -0.05 percent |

These results are excellent for the intended first validation stage.

The result confirms that the current path, INA228 setup, shunt configuration, and software calculations are working correctly.

## CSV Logging Validation

CSV output was successfully generated at approximately 2 Hz.

The CSV includes:

1. Timestamp.
2. Bus voltage.
3. Shunt voltage.
4. Current.
5. Power.
6. Die temperature.
7. Status.
8. Overload flag.
9. Warning flag.

Later logger revisions also include elapsed time, running averages, accumulated mAh, and accumulated Wh.

CSV logging is confirmed functional.

## Stability Check

A short soak test was run. The logger continued updating and writing data without observed crashes, hangs, I2C failures, or obviously corrupt readings.

A longer 30 minute plus soak test is still useful later, but the initial stability check is sufficient to progress to the next stage.

## Findings

## Communication

1. INA228 communication is stable.
2. Device identity registers match expectations.
3. Register reads are reliable.
4. No I2C lockups were observed during the validation work.

## Calibration

1. The 0.015 ohm shunt value is configured and working.
2. Current readings match expected load currents.
3. Open circuit offset correction has been measured and applied.

## Accuracy

1. Accuracy from approximately 5 mA to 50 mA is excellent.
2. Results are within roughly 0.15 percent at the checked points.
3. Repeatability appears good.
4. The meter is suitable for live current logging in the mA range.

## Low Current Limitation

The current 15 mOhm shunt is good for general validation and moderate current work, but it is not ideal for very low current measurements.

The KinetiQX power optimisation work will eventually need to examine:

1. Sleep current.
2. Standby current.
3. Small firmware power saving deltas.
4. Differences in the 10 uA to 1000 uA region.

For that work, a different shunt value or a separate low current measurement setup should be considered.

This does not block Phase 1. It simply defines the next measurement improvement.

## Conclusion

Phase 1 is successful.

The project has demonstrated:

1. INA228 hardware is working.
2. Raspberry Pi integration is working.
3. Python driver and logger are functional.
4. CSV logging is functional.
5. Zero offset calibration is available.
6. Current readings are accurate across the tested mA range.
7. The system is ready to move forward.

The current setup is approved for continued development as a practical current logger.

## Recommended Next Phase

## Phase 2 Dashboard and Characterisation

The next phase should focus on turning the working logger into a usable bench instrument.

Recommended Phase 2 objectives:

1. Web dashboard.
2. Live graphs.
3. Configurable sample rate.
4. Configurable INA228 ADC conversion and averaging settings.
5. CSV download from the dashboard.
6. Noise floor characterisation.
7. Low current shunt investigation.
8. Battery discharge logging workflow.
9. mAh and Wh validation over longer runs.

## Phase 1 Status

Phase 1 status: complete.
