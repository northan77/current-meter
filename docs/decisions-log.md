# Engineering Decisions Log

## 2026-05-29

### Platform

Decision: Raspberry Pi Zero 2 W selected as the host platform.

Reason:

- Native Linux environment.
- SSH access.
- Local web dashboard capability.
- Easy logging and storage.

## 2026-05-30

### Current Measurement Device

Decision: INA228 selected as the measurement front end.

Reason:

- High resolution current measurement.
- Voltage, current and power support.
- Suitable for low power embedded analysis.

### Shunt Value

Decision: Use fitted 15 mΩ shunt.

Reason:

- Verified against measured behaviour.
- Acceptable voltage drop.

### Measurement Method

Decision: Use VSHUNT-derived current as the primary measurement path.

Reason:

- Directly traceable to measured shunt voltage.
- Easier to validate.

The INA228 CURRENT register remains available for diagnostics and calibration comparison.

### Auto Ranging

Decision: No automatic ranging in Version 1.

Reason:

- Reduces complexity.
- Avoids switching errors.
- Faster route to a useful instrument.

### Source Control

Decision: GitHub repository is the project source of truth.

Reason:

- Version control.
- Documentation storage.
- Remote review.
- Automated Pi backup.

### Development Workflow

Decision: VS Code save triggers automatic commit and push.

Reason:

- Eliminates manual synchronisation.
- Keeps GitHub current.
- Enables repository review against latest code.
