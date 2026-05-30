# Raspberry Pi INA228 Current Meter Specification

## 1. Purpose

Build a small bench current meter using a Raspberry Pi Zero 2 W and an INA228 current, voltage and power monitor connected over I2C.

The Pi reads measurements from the INA228 and serves a local web dashboard over WiFi. The unit is accessed by SSH for setup, maintenance and code updates.

The first version should be simple, reliable and useful for checking battery powered electronics, especially low power embedded devices.

## 2. Core hardware

### 2.1 Controller

Raspberry Pi Zero 2 W.

Expected roles:

1. Read INA228 over I2C.
2. Run a local Python service.
3. Host a web dashboard.
4. Store captured logs locally.
5. Allow SSH access over WiFi.

### 2.2 Current measurement IC

INA228 connected to the Pi over I2C.

Expected measurements:

1. Bus voltage.
2. Shunt voltage.
3. Current.
4. Power.
5. Energy or accumulated charge if useful later.
6. Die temperature if exposed and useful.

### 2.3 Shunt resistor and module limitations

The INA228 is being used on a ready made module, not on a custom PCB layout.

This means the design does not control:

1. Shunt layout.
2. Kelvin routing quality.
3. Via placement.
4. Trace length matching.
5. Current path quality.
6. Fitted shunt value.

The software should treat the hardware as a known fixed module rather than a flexible measurement front end.

Low current readings may be affected by offset, trace resistance, thermal effects and noise. The software should therefore make calibration and zero correction easy rather than pretending the module is a precision lab layout.

Important practical points:

1. Store the shunt value in configuration.
2. Allow calibration values to be changed from the web page.
3. Provide a zero offset function.
4. Show diagnostic values to spot bad readings.
5. Do not assume the module is accurate just because the INA228 chip is capable.

## 3. Scope for version 1

Version 1 should do 1 job well: show live current, voltage and power on a web page and optionally log the readings.

Required version 1 features:

1. Raspberry Pi boots headless.
2. User can SSH into the Pi over WiFi.
3. INA228 is detected on the I2C bus.
4. Python service reads INA228 measurements.
5. Web page shows live readings.
6. Web page works from another device on the same WiFi network.
7. Continuous sampling loop runs independently from the web dashboard refresh rate.
8. Web dashboard refreshes at 2Hz to 10Hz.
9. Logging can run at its own configured rate.
10. Calibration and static configuration values can be viewed and edited from the web page.
11. Dashboard includes live values and useful summary values.
12. Clear configuration file for shunt value, calibration and display units.
13. Simple service install using systemd.

Not included in version 1:

1. Cloud access.
2. User account system.
3. Battery powered operation of the meter itself.
4. High speed oscilloscope style capture.

## 4. Software architecture

### 4.1 Language

Python is preferred for version 1 because it is quick to develop, easy to maintain over SSH and has good Raspberry Pi support.

### 4.2 Main components

Recommended project structure:

```text
/home/tim/current_meter/
  app.py
  ina228.py
  config.py
  logger.py
  requirements.txt
  current_meter.service
  config.yaml
  logs/
  static/
  templates/
```

Suggested responsibilities:

1. `ina228.py` handles INA228 register access and conversion maths.
2. `config.py` loads shunt value, I2C address and logging settings.
3. `logger.py` handles CSV or SQLite logging.
4. `app.py` runs the web server and live data loop.
5. `config.yaml` contains calibration and user editable settings.

### 4.3 Web framework

Use Flask for the first version.

Reasons:

1. Simple.
2. Easy to debug.
3. Good enough for a local meter dashboard.
4. Suitable for live readings using polling or server sent events later.

## 5. Web dashboard

### 5.1 Required display values

The dashboard should show from the start:

1. Current in microamps, milliamps or amps depending on value.
2. Bus voltage.
3. Shunt voltage.
4. Power.
5. Minimum current for the active run.
6. Maximum current for the active run.
7. Average current for the active run.
8. Rolling average current.
9. Estimated mAh for the active run.
10. Estimated Wh for the active run.
11. Measurement status.
12. Logging status.
13. Sample rate.
14. Log rate.
15. Last update time.

### 5.2 Configuration and calibration page

Required editable values:

1. Shunt resistance.
2. Current calibration multiplier.
3. Voltage calibration multiplier.
4. Current zero offset.
5. Display refresh rate.
6. Logging rate.
7. Rolling average window.
8. Logging enabled or disabled.

Useful controls:

1. Apply settings.
2. Save settings permanently.
3. Zero current offset.
4. Start new run.
5. Stop logging.
6. Download CSV.
7. Reset min, max and average counters.

### 5.3 Update method

The software should separate 3 rates:

1. Sensor sampling rate.
2. Logging rate.
3. Web dashboard refresh rate.

The logger must record from the measurement loop, not from the browser refresh.

For version 1, browser polling is acceptable. Later, server sent events or WebSockets can be used if smoother updates are needed.

## 6. Logging

CSV logging is enough for version 1, but logging should be designed properly from the start.

Suggested fields:

```text
timestamp_iso, timestamp_s, bus_v, shunt_v, current_a, power_w, die_temp_c, current_min_a, current_max_a, current_avg_a, mah, wh, status
```

SQLite can be added later for proper sessions and dashboard queries.

Possible tables:

1. `runs`
2. `samples`
3. `calibration`
4. `device_config`

## 7. Configuration

Use `config.yaml` so the meter can be adjusted without editing Python code.

Suggested values:

```yaml
i2c:
  bus: 1
  address: 0x40

shunt:
  resistance_ohms: 0.015
  max_current_a: 10.0

calibration:
  current_multiplier: 1.0
  voltage_multiplier: 1.0
  current_zero_offset_a: 0.0

sampling:
  sensor_hz: 10
  display_hz: 5
  log_hz: 1
  rolling_average_seconds: 10

logging:
  enabled: false
  folder: logs

web:
  host: 0.0.0.0
  port: 8080
```

## 8. Measurement behaviour

The main interest is microamp measurement and checking battery capacity.

The shunt value and INA228 settings should give useful low current resolution without creating too much voltage drop for the device under test.

The meter must show or account for shunt voltage drop.

A later battery capacity test mode should:

1. Start a logging run.
2. Record current and voltage over time.
3. Integrate current over time to calculate mAh.
4. Optionally stop when voltage falls below a configured cutoff.

## 9. System service

The current meter should run automatically after boot using systemd.

Expected behaviour:

1. Service starts after network is available.
2. Service restarts on failure.
3. Logs can be checked with `journalctl`.
4. Code can still be edited over SSH.

Suggested service name:

```text
current_meter.service
```

## 10. WiFi and access

Version 1 assumes the Pi joins an existing WiFi network.

Access methods:

1. SSH for maintenance.
2. Browser dashboard using the Pi hostname or IP address.

Possible hostname:

```text
currentmeter.local
```

Later option:

1. WiFi access point mode so the meter can be used away from the home network.

## 11. Known design decisions

### 11.1 No auto range for version 1

Auto ranging with multiple shunts or multiple INA228 devices is interesting but should not be part of version 1.

Reasons:

1. It increases hardware complexity.
2. It risks measurement errors from leakage paths and switching resistance.
3. It delays getting a useful tool working.
4. The practical need is better served by choosing the correct shunt or meter setup for the test.

### 11.2 Keep the Pi as the test platform

The Pi Zero 2 W is a good choice because it can run the dashboard, logging and SSH without needing another microcontroller.

### 11.3 Keep the first dashboard boring

The first dashboard should be clear, stable and easy to trust. Fancy graphs and animated displays can come later.

## 12. Future features

Possible later features:

1. Multiple saved profiles for different shunts.
2. Calibration page.
3. Start and stop logging from the web dashboard.
4. Live graph.
5. Download CSV from browser.
6. SQLite run history.
7. Battery capacity test mode.
8. Low current sleep profile test mode.
9. Triggered capture when current crosses a threshold.
10. Remote zero offset correction.
11. OLED or small local display.
12. WiFi access point mode.
13. API endpoint for other tools.
14. Multiple INA228 boards selectable by config, not automatic range switching.
15. Export summary showing average current, peak current, mAh and Wh.

## 13. First implementation milestone

Milestone 1 should prove the full path end to end:

1. Pi boots.
2. I2C bus is enabled.
3. INA228 is visible with `i2cdetect`.
4. Python can read raw INA228 registers.
5. Python converts readings into real units.
6. Flask serves `/api/live` JSON.
7. Browser page displays live current, voltage and power.
8. systemd starts the service at boot.

## 14. Validation plan

### 14.1 Electrical validation

Use known loads:

1. Open circuit check.
2. Known resistor load.
3. Small LED load.
4. Known USB powered board.
5. Battery powered embedded device.

### 14.2 Software validation

Check:

1. Web page refreshes correctly.
2. API returns sensible JSON.
3. Logs are written correctly.
4. Service restarts after reboot.
5. Error shown clearly if INA228 is missing.

## 15. Risks

Main risks:

1. Wrong shunt value gives poor resolution or too much voltage drop.
2. INA228 register setup is wrong and readings look believable but are scaled incorrectly.
3. PCB layout causes inaccurate shunt readings.
4. WiFi connection makes the meter awkward to access.
5. Scope creep delays a working first version.

## 16. Immediate next steps

1. Confirm INA228 I2C address.
2. Confirm shunt value and expected current range.
3. Set up Raspberry Pi OS Lite on the Pi Zero 2 W.
4. Enable I2C and SSH.
5. Install Python dependencies.
6. Write minimal INA228 register read test.
7. Build the Flask dashboard.
8. Add logging once live readings are trustworthy.
