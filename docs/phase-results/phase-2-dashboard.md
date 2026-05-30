# Phase 2 Dashboard Validation

## Objective

Transform the validated INA228 logger into a usable bench instrument with a live web dashboard.

## Features Implemented

### Live Dashboard

The Flask dashboard provides live monitoring of:

1. Current
2. Power
3. Bus voltage
4. Shunt voltage
5. Average current
6. Rolling average current
7. Minimum current
8. Maximum current
9. Used capacity
10. Remaining capacity
11. Remaining capacity percentage
12. Runtime elapsed
13. Runtime remaining estimate
14. Total runtime estimate
15. Energy (Wh)
16. Temperature
17. Status indication

### Battery Characterisation Support

A configurable expected battery capacity can be entered in logger_config.yaml.

The dashboard calculates:

1. Used capacity (mAh)
2. Remaining capacity (mAh)
3. Remaining capacity (%)
4. Estimated runtime remaining
5. Estimated total runtime

This forms the foundation for future battery characterisation and capacity validation features.

## Validation Results

The following items were tested successfully.

### Dashboard Operation

PASS

Dashboard loads correctly.

### Live Measurement Updates

PASS

Values update continuously from the INA228 measurement engine.

### CSV Download

PASS

CSV files can be downloaded from the dashboard.

### Run Statistics

PASS

Minimum, maximum, average, mAh and Wh calculations operate correctly.

### Reset Function

PASS

Reset clears:

1. Runtime
2. Used capacity
3. Energy
4. Min values
5. Max values
6. Average values

### Battery Metrics

PASS

Expected capacity, used capacity, remaining capacity and runtime calculations operate correctly.

## Conclusion

Phase 2 is complete.

The project now operates as a practical bench current meter with a live dashboard and battery discharge estimation capability.

The next priority is measurement robustness followed by graphical visualisation.
