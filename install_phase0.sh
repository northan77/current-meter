#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/tim/current_meter"
mkdir -p "$PROJECT_DIR"
cp -r current_meter/* "$PROJECT_DIR"/
cd "$PROJECT_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Installed Phase 0 files into $PROJECT_DIR"
echo "Next: enable I2C, wire INA228, then run:"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  python INA228_test.py"
echo "  python phase0_baseline.py"
