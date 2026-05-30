# Current Meter Project Phase Plan

## Completed Phases

### Phase 0: Requirements and Hardware Baseline

Completed.

### Phase 1: Platform Bring Up and INA228 Validation

Completed.

Includes:

- Raspberry Pi setup
- Git integration
- INA228 communications
- Calibration system
- Statistics engine
- Measurement validation
- CSV logging foundation

### Phase 2: Dashboard and Battery Metrics

Completed.

Includes:

- Flask dashboard
- Live API
- Current, voltage and power display
- Statistics display
- CSV download
- Runtime metrics
- Battery discharge estimation
- Used capacity calculations
- Remaining capacity calculations
- Runtime prediction

See:

docs/phase-results/phase-2-dashboard.md

---

# Phase 3: Measurement Robustness

## Objective

Ensure the instrument can run unattended for long periods.

### Tasks

#### 3.1 INA228 fault detection

Detect:

- Sensor disconnected
- Invalid readings
- Communication timeout

#### 3.2 I2C recovery

Recover from:

- Bus lockups
- Read failures
- Temporary communication errors

#### 3.3 Sensor offline mode

Dashboard remains operational when measurement hardware is unavailable.

Display:

- Offline state
- Error reason
- Recovery attempts

#### 3.4 Automatic reconnection

Automatically reconnect when the sensor returns.

#### 3.5 Long duration soak testing

Verify:

- Stability
- Memory usage
- Measurement continuity
- Recovery behaviour

### Deliverable

Reliable unattended operation.

---

# Phase 4: Visualisation

## Objective

Transform the dashboard into a practical engineering instrument.

### Tasks

#### 4.1 Current graph

Live scrolling current graph.

#### 4.2 Power graph

Live scrolling power graph.

#### 4.3 Voltage graph

Live scrolling voltage graph.

#### 4.4 Time ranges

Selectable ranges:

- 1 minute
- 5 minutes
- 30 minutes
- Entire run

#### 4.5 Historical buffers

Maintain local history buffers for visualisation.

### Deliverable

Graphical dashboard with live trends.

---

# Phase 5: Instrument Controls

## Objective

Allow operation without editing files or using SSH.

### Tasks

#### 5.1 Start logging

#### 5.2 Stop logging

#### 5.3 New run

Timestamped run creation.

#### 5.4 Zero current

Capture and store offset.

#### 5.5 Configuration page

Modify:

- Sample rates
- Rolling averages
- Calibration values
- Battery capacity

#### 5.6 Save settings

Persist settings through the web interface.

### Deliverable

Fully controllable bench instrument.

---

# Phase 6: Battery Characterisation

## Objective

Characterise batteries rather than simply measuring current.

### Tasks

#### 6.1 Battery profiles

Store battery definitions.

#### 6.2 Capacity validation

Compare measured and claimed capacity.

#### 6.3 Charge cycle logging

#### 6.4 Discharge cycle logging

#### 6.5 Runtime prediction

#### 6.6 Battery health estimation

Calculate:

- Measured capacity
- Remaining health
- Historical degradation

### Deliverable

Battery characterisation platform.

---

# Phase 7: Deployment

## Objective

Create appliance style operation.

### Tasks

#### 7.1 Systemd service

#### 7.2 Automatic startup

#### 7.3 Automatic recovery

#### 7.4 Watchdog support

#### 7.5 Deployment documentation

### Deliverable

Production ready instrument.

---

# Current Priority Order

1. Phase 3 Measurement Robustness
2. Phase 4 Visualisation
3. Phase 5 Instrument Controls
4. Phase 6 Battery Characterisation
5. Phase 7 Deployment
