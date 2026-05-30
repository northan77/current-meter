# Phase 1 Live Logging

## Goal

Capture stable live INA228 measurements and write them to CSV.

## Success Criteria

* INA228 detected
* Current displayed continuously
* CSV logging functional
* Stable for 10 minutes minimum
* Overload warning generated correctly

## Run

```bash
python phase1_logger.py
```

## Output

CSV file containing:

* Timestamp
* Bus voltage
* Shunt voltage
* Current
* Power
* Temperature
* Status flags
