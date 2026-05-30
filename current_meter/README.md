# Current Meter Phase 0

This is the first Pi-side code for the INA228 current meter.

Phase 0 is not the dashboard yet. It freezes the hardware assumptions and proves that the Pi can see the INA228.

## Install on the Pi

From VS Code terminal on the Pi:

```bash
cd /home/tim/current_meter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Make sure I2C is enabled:

```bash
sudo raspi-config
```

Then use:

```bash
i2cdetect -y 1
```

## Files

`config.yaml` is where the module details, I2C address, shunt value and acceptance criteria live.

`INA228_test.py` does a simple scan and raw register read.

`phase0_baseline.py` creates `hardware_baseline.yaml` for the frozen Phase 0 record.

`ina228.py` is a small conservative probe driver. It reads raw registers and calculates simple current from shunt voltage divided by configured shunt resistance. Full INA228 calibration comes in Phase 2.

## First run

With the INA228 wired to the Pi:

```bash
source .venv/bin/activate
python INA228_test.py
```

Then capture the baseline:

```bash
python phase0_baseline.py
```

## What to edit first

Open `config.yaml` and set:

```yaml
hardware:
  manufacturer: "Adafruit or other module maker"
  module_link: "module product page"

shunt:
  resistance_ohms: 0.1
  max_current_a: 1.0
```

Do not trust the default shunt value until you confirm the fitted resistor marking or module documentation.
