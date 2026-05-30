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

    let detail = "Sample " + data.sample_count + " | " + data.sample_rate_hz + " Hz | " + data.last_update_utc;
    if (data.recovery_attempts > 0) detail += " | recovery attempts " + data.recovery_attempts;
    if (data.offline_reason) detail += " | " + data.offline_reason;
    if (data.error) detail += " | " + data.error;
    setText("detail", detail);

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
