# Current Meter Project Map

Refactor commit: 8457fdc Refactor dashboard into modules

## Status

Phase 0 complete
Phase 1 complete
Phase 2 complete
Phase 3 complete
Phase 4 preparation complete
Phase 4 implementation next

## Main Files

current_meter/app.py
Flask entry point. Starts the measurement engine and owns the web routes.

current_meter/dashboard_state.py
DashboardState dataclass used by the live API.

current_meter/measurement_engine.py
Measurement thread, INA228 setup, recovery handling, calculations, CSV logging and reset handling.

current_meter/measurement.py
Measurement model and CSV row conversion.

current_meter/ina228.py
Low-level INA228 driver.

current_meter/csv_logger.py
CSV helper.

current_meter/config.py
Configuration loading and I2C address parsing.

current_meter/logger_config.yaml
Runtime settings for logging, limits, battery capacity and robustness.

current_meter/templates/dashboard.html
Dashboard HTML layout.

current_meter/static/dashboard.css
Dashboard styling.

current_meter/static/dashboard.js
Frontend update loop and reset button handling.

## Current Routes

/ Dashboard page
/api/live Live dashboard state
/api/reset Reset run statistics
/download/csv Download CSV log

## Phase 4 Next Steps

1. Add current_meter/history_buffer.py for bounded current, power and voltage history.
2. Extend measurement_engine.py to append valid samples to the history buffer.
3. Add an API route for graph history data.
4. Add graph panels to dashboard.html.
5. Add graph styling to dashboard.css.
6. Add canvas graph drawing to dashboard.js.

## Phase 4 Acceptance

Dashboard loads normally.
Live metric cards update.
Reset works.
CSV download works.
Current graph updates live.
Power graph updates live.
Voltage graph updates live.
Selectable ranges work for 1 minute, 5 minutes, 30 minutes and entire run.
Offline and recovery states do not break the dashboard.
