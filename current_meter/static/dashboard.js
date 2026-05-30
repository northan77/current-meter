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

const graphSeries = [
  { canvasId: "currentGraph", key: "current_a", label: "A" },
  { canvasId: "powerGraph", key: "power_w", label: "W" },
  { canvasId: "voltageGraph", key: "bus_v", label: "V" },
];

let selectedRange = "60";

function setupRangeControls() {
  document.querySelectorAll(".range-button").forEach((button) => {
    button.addEventListener("click", () => {
      selectedRange = button.dataset.range;
      document.querySelectorAll(".range-button").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      updateHistory();
    });
  });
}

function resizeCanvas(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.floor(canvas.clientWidth * ratio));
  const height = Math.max(1, Math.floor(canvas.clientHeight * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return ratio;
}

function formatAxisValue(value) {
  const abs = Math.abs(value);
  if (abs >= 100) return value.toFixed(0);
  if (abs >= 10) return value.toFixed(1);
  if (abs >= 1) return value.toFixed(2);
  return value.toPrecision(3);
}

function drawGraph(canvasId, samples, key, unit) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ratio = resizeCanvas(canvas);
  const ctx = canvas.getContext("2d");
  const width = canvas.width / ratio;
  const height = canvas.height / ratio;

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#101418";
  ctx.fillRect(0, 0, width, height);

  const plotLeft = 58;
  const plotRight = 12;
  const plotTop = 12;
  const plotBottom = 28;
  const plotWidth = Math.max(1, width - plotLeft - plotRight);
  const plotHeight = Math.max(1, height - plotTop - plotBottom);

  ctx.strokeStyle = "#2d3a45";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i <= 4; i += 1) {
    const y = plotTop + (plotHeight * i) / 4;
    ctx.moveTo(plotLeft, y);
    ctx.lineTo(width - plotRight, y);
  }
  ctx.stroke();

  ctx.fillStyle = "#96a6b3";
  ctx.font = "12px Arial, Helvetica, sans-serif";
  ctx.textBaseline = "middle";

  if (samples.length === 0) {
    ctx.textAlign = "center";
    ctx.fillText("No graph data", width / 2, height / 2);
    return;
  }

  const values = samples.map((sample) => Number(sample[key])).filter(Number.isFinite);
  if (values.length === 0) return;

  let minValue = Math.min(...values);
  let maxValue = Math.max(...values);
  if (minValue === maxValue) {
    const padding = Math.max(Math.abs(minValue) * 0.1, 0.001);
    minValue -= padding;
    maxValue += padding;
  } else {
    const padding = (maxValue - minValue) * 0.08;
    minValue -= padding;
    maxValue += padding;
  }

  const startElapsed = samples[0].elapsed_s;
  const endElapsed = samples[samples.length - 1].elapsed_s;
  const elapsedRange = Math.max(1, endElapsed - startElapsed);

  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i += 1) {
    const value = maxValue - ((maxValue - minValue) * i) / 4;
    const y = plotTop + (plotHeight * i) / 4;
    ctx.fillText(formatAxisValue(value), plotLeft - 8, y);
  }

  ctx.textAlign = "left";
  ctx.textBaseline = "alphabetic";
  ctx.fillText(unit, plotLeft, height - 8);

  ctx.strokeStyle = "#69d487";
  ctx.lineWidth = 2;
  ctx.beginPath();
  let hasPoint = false;
  samples.forEach((sample) => {
    const value = Number(sample[key]);
    if (!Number.isFinite(value)) return;
    const x = plotLeft + ((sample.elapsed_s - startElapsed) / elapsedRange) * plotWidth;
    const y = plotTop + ((maxValue - value) / (maxValue - minValue)) * plotHeight;
    if (!hasPoint) {
      ctx.moveTo(x, y);
      hasPoint = true;
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
}

async function updateHistory() {
  try {
    const res = await fetch("/api/history?range=" + encodeURIComponent(selectedRange), {
      cache: "no-store",
    });
    const data = await res.json();
    const samples = Array.isArray(data.samples) ? data.samples : [];
    graphSeries.forEach((series) => {
      drawGraph(series.canvasId, samples, series.key, series.label);
    });
  } catch (err) {
    graphSeries.forEach((series) => {
      drawGraph(series.canvasId, [], series.key, series.label);
    });
  }
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
  updateHistory();
}

setupRangeControls();
update();
updateHistory();
setInterval(update, 500);
setInterval(updateHistory, 1000);
window.addEventListener("resize", updateHistory);
