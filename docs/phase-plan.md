Pre Phase work: Setup Pi Zero 2 W

Task.

Load Pi Lite OS 64.

Configure name and SSH into via VS Code. Done: `ssh tim@labpi.local`, IP = `192.168.0.63`, configured static in router.

Create folder for project and current-meter. Done.

Create `INA228_test.py` file ready for next phase. Done.

# Phase 0: Requirements Freeze

## Objective

Lock down the hardware assumptions before any software development.

### Tasks

#### 0.1 Confirm INA228 module

Record:

- Manufacturer
- Module link
- INA228 I2C address
- Fitted shunt value
- Maximum practical current

#### 0.2 Define measurement targets

Example:

| Range     | Target       |
| --------- | ------------ |
| Current   | 1 µA to 1 A  |
| Voltage   | 0 V to 36 V  |
| Power     | Derived      |
| Logging   | 1 Hz minimum |
| Dashboard | 2 to 10 Hz   |

#### 0.3 Define acceptance criteria

Example:

- Current within ±2%
- Voltage within ±1%
- Stable zero reading
- mAh integration verified

**Deliverable:** Frozen specification and hardware baseline.

------

# Phase 1: Raspberry Pi Platform Bring-Up

## Objective

Get a stable Pi environment.

### Tasks

### 1.1 Install OS

- Raspberry Pi OS Lite
- Hostname:
  - `currentmeter`
- Static or DHCP address

### 1.2 Enable services

- SSH
- I2C

Verify:

```text
ssh currentmeter.local
```

and

```text
i2cdetect -y 1
```

### 1.3 Create project structure

```text
/home/tim/current_meter
```

Exactly as defined in the specification.

### 1.4 Git repository

Strongly recommended.

Even if local only.

**Deliverable:** Pi accessible over WiFi and SSH.

------

# Phase 2: INA228 Driver Development

## Objective

Trustworthy sensor readings.

### Tasks

### 2.1 Read raw registers

Verify:

- Bus voltage
- Shunt voltage
- Current
- Power

No web dashboard yet.

Just terminal output.

### 2.2 Implement conversion maths

Build:

```text
ina228.py
```

Functions:

```text
read_voltage()
read_current()
read_power()
read_temperature()
```

### 2.3 Validate against instruments

Test:

- Open circuit
- Known resistor
- Bench PSU
- Known current source

### 2.4 Implement calibration

Support:

- Current multiplier
- Voltage multiplier
- Zero offset

Stored in:

```text
config.yaml
```

### 2.5 Statistics engine

Track:

- Min
- Max
- Average
- Rolling average

**Deliverable:** Trustworthy measurements from terminal.

------

# Phase 3: Measurement Engine

## Objective

Create the core measurement service.

### Tasks

### 3.1 Background sampling thread

Runs continuously.

Example:

```text
10Hz
50Hz
100Hz
```

Selectable.

### 3.2 Shared state object

Contains:

- Latest current
- Voltage
- Power
- Statistics
- Status

### 3.3 mAh integration

Calculate:

```text
Current × Time
```

### 3.4 Wh integration

Calculate:

```text
Power × Time
```

### 3.5 Error handling

Detect:

- INA228 missing
- I2C failure
- Invalid data

**Deliverable:** Headless measurement engine.

------

# Phase 4: Flask Dashboard

## Objective

Get live data visible.

### Tasks

### 4.1 Flask server

Create:

```text
/
```

Dashboard

```text
/api/live
```

JSON endpoint

### 4.2 Live dashboard

Display:

- Current
- Voltage
- Power
- Min
- Max
- Average
- mAh
- Wh

### 4.3 Status indicators

Show:

- Logging active
- INA228 online
- Sample rate

### 4.4 Auto refresh

Polling:

```text
2Hz to 10Hz
```

Exactly as specified.

**Deliverable:** Live browser dashboard.

------

# Phase 5: Configuration System

## Objective

Allow operation without SSH.

### Tasks

### 5.1 Config editor

Modify:

- Shunt value
- Multipliers
- Offset
- Rates

### 5.2 Save settings

Write:

```text
config.yaml
```

### 5.3 Zero current button

Button:

```text
Zero Offset
```

Captures current reading.

Stores offset.

### 5.4 Reset statistics

Reset:

- Min
- Max
- Average
- mAh
- Wh

**Deliverable:** Fully configurable meter.

------

# Phase 6: Logging System

## Objective

Capture useful test data.

### Tasks

### 6.1 CSV logger

Implement:

```text
logger.py
```

### 6.2 Run management

Create:

```text
logs/
    run_20260529_120000.csv
```

### 6.3 Download support

Browser download.

### 6.4 Verify timestamps

Check:

- Missing samples
- Sample spacing

**Deliverable:** Reliable logging.

------

# Phase 7: Systemd Integration

## Objective

Appliance-style operation.

### Tasks

### 7.1 Create service

```text
current_meter.service
```

### 7.2 Auto-start

Verify:

```text
reboot
```

Dashboard returns automatically.

### 7.3 Recovery

Test:

```text
kill -9
```

Ensure restart.

### 7.4 Journal logging

Verify:

```text
journalctl -u current_meter
```

**Deliverable:** Production-ready operation.

------

# Phase 8: Validation and Calibration

## Objective

Prove measurements can be trusted.

### Tasks

### 8.1 Open-circuit test

Expected:

```text
0 A
```

or stable offset.

### 8.2 Resistor loads

Use:

- 1kΩ
- 100Ω
- 10Ω

Known currents.

### 8.3 Battery test

Run:

- Small LiPo
- ESP32 device

Verify:

- mAh
- Wh

### 8.4 Long-duration test

24-hour logging.

Check:

- Drift
- Stability
- Memory leaks

**Deliverable:** Signed-off Version 1.

------

# Phase 9: Version 1 Release

## Success Criteria

You should be able to:

1. Power the Pi.
2. Connect to WiFi.
3. Browse to `currentmeter.local`.
4. See live current, voltage and power.
5. Start logging.
6. Download a CSV.
7. Trust the readings.

At that point, stop.

Only after that start Version 2 features such as:

- Live graphs
- SQLite
- Battery discharge mode
- Trigger capture
- Multiple profiles
- Multiple INA228 boards
- Sleep current analysis
