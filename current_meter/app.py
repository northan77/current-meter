from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, jsonify, redirect, render_template_string, send_file, url_for

from config import ROOT, load_config, parse_i2c_address
from csv_logger import CsvLogger
from ina228 import INA228
from measurement import Measurement

LOGGER_CONFIG_PATH = ROOT / "logger_config.yaml"


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Current Meter</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, Helvetica, sans-serif;
      background: #101418;
      color: #e8eef2;
    }
    body {
      margin: 0;
      padding: 24px;
      background: #101418;
    }
    h1 {
      margin: 0 0 20px 0;
      font-size: 30px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      max-width: 1220px;
    }
    .card {
      background: #182028;
      border: 1px solid #2d3a45;
      border-radius: 14px;
      padding: 16px;
    }
    .label {
      color: #96a6b3;
      font-size: 13px;
      margin-bottom: 8px;
    }
    .value {
      font-size: 28px;
      font-weight: 700;
      line-height: 1.15;
    }
    .small {
      font-size: 15px;
      color: #b8c3cc;
    }
    .status-ok { color: #69d487; }
    .status-warning { color: #ffd166; }
    .status-overload { color: #ff6b6b; }
    .status-error { color: #ff6b6b; }
    .actions {
      margin-top: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    a, button {
      background: #24313d;
      color: #e8eef2;
      border: 1px solid #3b4b59;
      border-radius: 10px;
      padding: 10px 14px;
      text-decoration: none;
      font-size: 15px;
      cursor: pointer;
    }
    a:hover, button:hover {
      background: #304253;
    }
  </style>
</head>
<body>
  <h1>Current Meter</h1>

  <div class="grid">
    <div class="card"><div class="label">Current</div><div id="current" class="value">...</div></div>
    <div class="card"><div class="label">Power</div><div id="power" class="value">...</div></div>
    <div class="card"><div class="label">Bus voltage</div><div id="bus" class="value">...</div></div>
    <div class="card"><div class="label">Shunt voltage</div><div id="shunt" class="value">...</div></div>
    <div class="card"><div class="label">Average current</div><div id="avg" class="value">...</div></div>
    <div class="card"><div class="label">Rolling average</div><div id="rolling" class="value">...</div></div>
    <div class="card"><div class="label">Min current</div><div id="min" class="value">...</div></div>
    <div class="card"><div class="label">Max current</div><div id="max" class="value">...</div></div>
    <div class="card"><div class="label">Used capacity</div><div id="used" class="value">...</div><div id="expected" class="small"></div></div>
    <div class="card"><div class="label">Remaining capacity</div><div id="remaining" class="value">...</div></div>
    <div class="card"><div class="label">Remaining capacity</div><div id="remainingPct" class="value">...</div></div>
    <div class="card"><div class="label">Runtime elapsed</div><div id="elapsed" class="value">...</div></div>
    <div class="card"><div class="label">Runtime remaining</div><div id="runtimeRemaining" class="value">...</div></div>
    <div class="card"><div class="label">Estimated total runtime</div><div id="runtimeTotal" class="value">...</div></div>
    <div class="card"><div class="label">Energy</div><div id="wh" class="value">...</div></div>
    <div class="card"><div class="label">Temperature</div><div id="temp" class="value">...</div></div>
    <div class="card"><div class="label">Status</div><div id="status" class="value">...</div><div id="detail" class="small"></div></div>
  </div>

  <div class="actions">
    <button onclick="resetRun()">Reset run stats</button>
    <a href="/download/csv">Download CSV</a>
  </div>

  <script>
    function fmtCurrent(a) {
      const abs = Math.abs(a);
      if (abs < 0.001) return (a * 1000000).toFixed(1) + " uA";
      if (abs < 1) return (a * 1000).toFixed(3) + " mA";
      return a.toFixed(6) + " A";
    }

    function fmtDuration(seconds) {
      if (!Number.isFinite(seconds) || seconds <= 0) return "n/a";
      const totalSeconds = Math.round(seconds);
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const secs = totalSeconds % 60;
      if (hours > 0) return hours + " h " + minutes + " min";
      if (minutes > 0) return minutes + " min " + secs + " s";
      return secs + " s";
    }

    function fmtMah(value) {
      return value.toFixed(3) + " mAh";
    }

    function setText(id, text) {
      document.getElementById(id).textContent = text;
    }

    async function update() {
      try {
        const res = await fetch("/api/live", { cache: "no-store" });
        const data = await res.json();

        setText("current", fmtCurrent(data.current_a));
        setText("power", data.power_w.toFixed(6) + " W");
        setText("bus", data.bus_v.toFixed(6) + " V");
        setText("shunt", (data.shunt_v * 1000).toFixed(6) + " mV");
        setText("avg", fmtCurrent(data.current_avg_a));
        setText("rolling", fmtCurrent(data.current_rolling_avg_a));
        setText("min", fmtCurrent(data.current_min_a));
        setText("max", fmtCurrent(data.current_max_a));
        setText("used", fmtMah(data.used_capacity_mah));
        setText("expected", "Expected " + fmtMah(data.expected_capacity_mah));
        setText("remaining", fmtMah(data.remaining_capacity_mah));
        setText("remainingPct", data.remaining_capacity_percent.toFixed(1) + " %");
        setText("elapsed", fmtDuration(data.elapsed_s));
        setText("runtimeRemaining", fmtDuration(data.runtime_remaining_s));
        setText("runtimeTotal", fmtDuration(data.runtime_total_s));
        setText("wh", data.energy_wh.toFixed(9) + " Wh");
        setText("temp", data.die_temp_c.toFixed(2) + " °C");
        setText("status", data.status);
        setText("detail", "Sample " + data.sample_count + " | " + data.sample_rate_hz + " Hz | " + data.last_update_utc);

        const status = document.getElementById("status");
        status.className = "value status-" + data.status;
      } catch (err) {
        setText("status", "error");
        setText("detail", String(err));
        document.getElementById("status").className = "value status-error";
      }
    }

    async function resetRun() {
      await fetch("/api/reset", { method: "POST" });
      update();
    }

    update();
    setInterval(update, 500);
  </script>
</body>
</html>
"""


@dataclass
class DashboardState:
    timestamp_utc: str = ""
    elapsed_s: float = 0.0
    bus_v: float = 0.0
    shunt_v: float = 0.0
    current_a: float = 0.0
    current_avg_a: float = 0.0
    current_rolling_avg_a: float = 0.0
    current_min_a: float = 0.0
    current_max_a: float = 0.0
    power_w: float = 0.0
    power_avg_w: float = 0.0
    charge_mah: float = 0.0
    energy_wh: float = 0.0
    expected_capacity_mah: float = 0.0
    used_capacity_mah: float = 0.0
    remaining_capacity_mah: float = 0.0
    remaining_capacity_percent: float = 0.0
    runtime_remaining_s: float = 0.0
    runtime_total_s: float = 0.0
    die_temp_c: float = 0.0
    status: str = "starting"
    overload: bool = False
    warning: bool = False
    sample_count: int = 0
    sample_rate_hz: float = 2.0
    logging_enabled: bool = True
    last_update_utc: str = ""
    error: str = ""


class MeasurementEngine:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.state = DashboardState()
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.reset_requested = False

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def reset(self) -> None:
        with self.lock:
            self.reset_requested = True

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return asdict(self.state)

    def _load_logger_config(self) -> dict[str, Any]:
        if not LOGGER_CONFIG_PATH.exists():
            return {}
        with LOGGER_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _battery_metrics(
        charge_mah: float,
        current_avg_a: float,
        expected_capacity_mah: float,
    ) -> dict[str, float]:
        used_capacity_mah = max(0.0, charge_mah)
        remaining_capacity_mah = max(0.0, expected_capacity_mah - used_capacity_mah)

        remaining_capacity_percent = 0.0
        if expected_capacity_mah > 0:
            remaining_capacity_percent = (remaining_capacity_mah / expected_capacity_mah) * 100.0

        average_current_ma = abs(current_avg_a) * 1000.0
        runtime_remaining_s = 0.0
        runtime_total_s = 0.0

        if average_current_ma > 0:
            runtime_remaining_s = (remaining_capacity_mah / average_current_ma) * 3600.0
            runtime_total_s = (expected_capacity_mah / average_current_ma) * 3600.0

        return {
            "used_capacity_mah": used_capacity_mah,
            "remaining_capacity_mah": remaining_capacity_mah,
            "remaining_capacity_percent": remaining_capacity_percent,
            "runtime_remaining_s": runtime_remaining_s,
            "runtime_total_s": runtime_total_s,
        }

    def _run(self) -> None:
        cfg = load_config()
        logger_cfg = self._load_logger_config()

        sample_rate_hz = float(logger_cfg.get("logging", {}).get("sample_rate_hz", 2.0))
        sample_period_s = 1.0 / sample_rate_hz if sample_rate_hz > 0 else 0.5
        csv_path = ROOT / str(logger_cfg.get("logging", {}).get("csv_path", "logs/current_meter.csv"))
        logging_enabled = bool(logger_cfg.get("logging", {}).get("enabled", True))
        rolling_window = int(logger_cfg.get("logging", {}).get("rolling_average_samples", 20))
        rolling_window = max(1, rolling_window)

        expected_capacity_mah = float(
            logger_cfg.get("battery", {}).get("expected_capacity_mah", 400.0)
        )

        warning_current_a = float(logger_cfg.get("limits", {}).get("warning_current_a", 8.0))
        overload_current_a = float(logger_cfg.get("limits", {}).get("overload_current_a", 10.0))

        bus = int(cfg["i2c"]["bus"])
        address = parse_i2c_address(cfg["i2c"]["address"])
        shunt_ohms = float(cfg["shunt"]["resistance_ohms"])
        max_current_a = float(cfg["shunt"].get("max_current_a", overload_current_a))

        current_multiplier = float(cfg.get("calibration", {}).get("current_multiplier", 1.0))
        voltage_multiplier = float(cfg.get("calibration", {}).get("voltage_multiplier", 1.0))
        current_zero_offset_a = float(cfg.get("calibration", {}).get("current_zero_offset_a", 0.0))

        csv_log = CsvLogger(csv_path)
        csv_header_written = False

        sample_count = 0
        charge_mah = 0.0
        energy_wh = 0.0
        current_sum_a = 0.0
        power_sum_w = 0.0
        current_min_a: float | None = None
        current_max_a: float | None = None
        rolling_currents: deque[float] = deque(maxlen=rolling_window)

        start_time = time.monotonic()
        last_sample_time = start_time

        try:
            with INA228(
                bus=bus,
                address=address,
                shunt_ohms=shunt_ohms,
                max_current_a=max_current_a,
            ) as ina:
                ina.configure()

                while not self.stop_event.is_set():
                    loop_start = time.monotonic()

                    with self.lock:
                        if self.reset_requested:
                            self.reset_requested = False
                            sample_count = 0
                            charge_mah = 0.0
                            energy_wh = 0.0
                            current_sum_a = 0.0
                            power_sum_w = 0.0
                            current_min_a = None
                            current_max_a = None
                            rolling_currents.clear()
                            start_time = loop_start
                            last_sample_time = loop_start

                    elapsed_s = loop_start - start_time
                    dt_s = loop_start - last_sample_time
                    last_sample_time = loop_start

                    sample = ina.read_simple_measurement(
                        shunt_ohms=shunt_ohms,
                        current_multiplier=current_multiplier,
                        voltage_multiplier=voltage_multiplier,
                        current_zero_offset_a=current_zero_offset_a,
                    )

                    current_a = float(sample["current_a_simple"])
                    power_w = float(sample["power_w_simple"])

                    sample_count += 1
                    current_sum_a += current_a
                    power_sum_w += power_w
                    current_min_a = current_a if current_min_a is None else min(current_min_a, current_a)
                    current_max_a = current_a if current_max_a is None else max(current_max_a, current_a)
                    rolling_currents.append(current_a)

                    current_avg_a = current_sum_a / sample_count
                    power_avg_w = power_sum_w / sample_count
                    rolling_avg_a = sum(rolling_currents) / len(rolling_currents)

                    charge_mah += current_a * (dt_s / 3600.0) * 1000.0
                    energy_wh += power_w * (dt_s / 3600.0)
                    battery_metrics = self._battery_metrics(
                        charge_mah=charge_mah,
                        current_avg_a=current_avg_a,
                        expected_capacity_mah=expected_capacity_mah,
                    )

                    measurement = Measurement.from_ina228_sample(
                        sample,
                        max_current_a=overload_current_a,
                        warning_current_a=warning_current_a,
                        elapsed_s=elapsed_s,
                        current_avg_a=current_avg_a,
                        power_avg_w=power_avg_w,
                        charge_mah=charge_mah,
                        energy_wh=energy_wh,
                    )

                    row = measurement.as_csv_row()
                    if logging_enabled:
                        if not csv_header_written:
                            csv_log.write_header_if_needed(list(row.keys()))
                            csv_header_written = True
                        csv_log.append(row)

                    with self.lock:
                        self.state = DashboardState(
                            timestamp_utc=measurement.timestamp_utc,
                            elapsed_s=measurement.elapsed_s,
                            bus_v=measurement.bus_v,
                            shunt_v=measurement.shunt_v,
                            current_a=measurement.current_a,
                            current_avg_a=measurement.current_avg_a,
                            current_rolling_avg_a=rolling_avg_a,
                            current_min_a=current_min_a or 0.0,
                            current_max_a=current_max_a or 0.0,
                            power_w=measurement.power_w,
                            power_avg_w=measurement.power_avg_w,
                            charge_mah=measurement.charge_mah,
                            energy_wh=measurement.energy_wh,
                            expected_capacity_mah=expected_capacity_mah,
                            used_capacity_mah=battery_metrics["used_capacity_mah"],
                            remaining_capacity_mah=battery_metrics["remaining_capacity_mah"],
                            remaining_capacity_percent=battery_metrics["remaining_capacity_percent"],
                            runtime_remaining_s=battery_metrics["runtime_remaining_s"],
                            runtime_total_s=battery_metrics["runtime_total_s"],
                            die_temp_c=measurement.die_temp_c,
                            status=measurement.status,
                            overload=measurement.overload,
                            warning=measurement.warning,
                            sample_count=sample_count,
                            sample_rate_hz=sample_rate_hz,
                            logging_enabled=logging_enabled,
                            last_update_utc=measurement.timestamp_utc,
                            error="",
                        )

                    sleep_s = max(0.0, sample_period_s - (time.monotonic() - loop_start))
                    time.sleep(sleep_s)

        except Exception as exc:
            with self.lock:
                self.state.status = "error"
                self.state.error = str(exc)


app = Flask(__name__)
engine = MeasurementEngine()
engine.start()


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/live")
def api_live():
    return jsonify(engine.snapshot())


@app.route("/api/reset", methods=["POST"])
def api_reset():
    engine.reset()
    return jsonify({"ok": True})


@app.route("/download/csv")
def download_csv():
    logger_cfg = engine._load_logger_config()
    csv_path = ROOT / str(logger_cfg.get("logging", {}).get("csv_path", "logs/current_meter.csv"))
    if not csv_path.exists():
        return redirect(url_for("index"))
    return send_file(csv_path, as_attachment=True, download_name=Path(csv_path).name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
