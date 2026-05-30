from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, send_file, url_for

from config import ROOT
from measurement_engine import MeasurementEngine

app = Flask(__name__)
engine = MeasurementEngine()
engine.start()


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/live")
def api_live():
    return jsonify(engine.snapshot())


@app.route("/api/reset", methods=["POST"])
def api_reset():
    engine.reset()
    return jsonify({"ok": True})


@app.route("/download/csv")
def download_csv():
    logger_cfg = engine.load_logger_config()
    csv_path = ROOT / str(logger_cfg.get("logging", {}).get("csv_path", "logs/current_meter.csv"))
    if not csv_path.exists():
        return redirect(url_for("index"))
    return send_file(csv_path, as_attachment=True, download_name=Path(csv_path).name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
