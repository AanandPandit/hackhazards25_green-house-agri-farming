from flask import Flask, render_template_string, request, jsonify
import subprocess
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)
MAX_POINTS = 20

SENSOR_TOPICS = {
    "dht-temp": {"label": "Temperature (°C)", "color": "red"},
    "dht-humid": {"label": "Humidity (%)", "color": "blue"},
    "co2": {"label": "CO₂ (ppm)", "color": "green"},
    "rain-sensor": {"label": "Rain Sensor", "color": "gray"},
    "soil-moisture-1": {"label": "Soil Moisture 1 (%)", "color": "brown"},
    "soil-moisture-2": {"label": "Soil Moisture 2 (%)", "color": "orange"},
    "water-level-sensor": {"label": "Water Level (%)", "color": "purple"}
}

DEVICE_TOPICS = [
    "fan-1", "fan-2", "fan-3", "fan-4", "fan-5",
    "ac-1", "ac-2",
    "humidifier-1", "humidifier-2", "humidifier-3",
    "light-1", "light-2", "light-3", "light-4", "light-5",
    "water-pump"
]

sensor_data = {topic: [] for topic in SENSOR_TOPICS}
timestamps = []
device_states = {topic: "UNKNOWN" for topic in DEVICE_TOPICS}
current_values = {topic: "--" for topic in SENSOR_TOPICS}

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
    <title>🌿 Smart Greenhouse Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f2f2f2; }
        h2 { margin-bottom: 10px; }
        .charts { display: flex; flex-wrap: wrap; gap: 20px; }
        .chart-box { width: 45%; background: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 8px #ccc; }
        .device-control { margin-top: 40px; }
        .device-row { display: flex; align-items: center; margin-bottom: 10px; }
        .toggle { position: relative; width: 60px; height: 30px; margin-left: 10px; }
        .toggle input { display: none; }
        .slider {
            position: absolute; cursor: pointer; top: 0; left: 0;
            right: 0; bottom: 0; background-color: #ccc; transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute; content: "";
            height: 24px; width: 24px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .4s; border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #4CAF50;
        }
        input:checked + .slider:before {
            transform: translateX(30px);
        }
        .current-value { font-weight: bold; color: #333; margin-top: 10px; }
    </style>
</head>
<body>
<h2>🌡️ Smart Greenhouse Dashboard</h2>

<div class="charts">
    {% for topic, config in sensor_topics.items() %}
    <div class="chart-box">
        <h4>{{ config.label }}</h4>
        <div class="current-value">Current: <span id="cur-{{ topic }}">--</span></div>
        <canvas id="chart-{{ topic }}"></canvas>
    </div>
    {% endfor %}
</div>

<div class="device-control">
    <h3>⚙️ Device Control</h3>
    {% for topic in device_topics %}
    <div class="device-row">
        <label>{{ topic }}</label>
        <label class="toggle">
            <input type="checkbox" onchange="toggleDevice(this, '{{ topic }}')" id="switch-{{ topic }}">
            <span class="slider"></span>
        </label>
        <span id="status-{{ topic }}" style="margin-left:10px;"></span>
    </div>
    {% endfor %}
</div>

<script>
const sensorTopics = {{ sensor_topics | tojson }};
const charts = {};
const MAX_POINTS = 20;

function initCharts() {
    for (const [topic, config] of Object.entries(sensorTopics)) {
        const ctx = document.getElementById('chart-' + topic).getContext('2d');
        charts[topic] = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: config.label, data: [], borderColor: config.color, tension: 0.3 }] },
            options: { scales: { x: { ticks: { autoSkip: true, maxTicksLimit: 6 } } } }
        });
    }
}

async function fetchData() {
    const res = await fetch("/data");
    const data = await res.json();
    for (const [topic, values] of Object.entries(data.sensor_data)) {
        const chart = charts[topic];
        if (chart) {
            chart.data.labels = data.timestamps;
            chart.data.datasets[0].data = values;
            chart.update();
        }
        document.getElementById('cur-' + topic).innerText = data.current_values[topic];
    }
}

async function fetchDeviceStates() {
    const res = await fetch("/device-status");
    const data = await res.json();
    for (const [topic, state] of Object.entries(data)) {
        const checkbox = document.getElementById("switch-" + topic);
        const label = document.getElementById("status-" + topic);
        if (checkbox) checkbox.checked = (state === "ON");
        if (label) label.innerText = state;
    }
}

function toggleDevice(elem, topic) {
    const state = elem.checked ? "on" : "off";
    fetch("/device", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, state })
    });
}

initCharts();
setInterval(fetchData, 5000);
setInterval(fetchDeviceStates, 5000);
</script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(HTML_TEMPLATE, sensor_topics=SENSOR_TOPICS, device_topics=DEVICE_TOPICS)

@app.route("/data")
def data():
    return jsonify({
        "timestamps": timestamps,
        "sensor_data": sensor_data,
        "current_values": current_values
    })

@app.route("/device-status")
def device_status():
    return jsonify(device_states)

@app.route("/device", methods=["POST"])
def device_control():
    data = request.json
    topic = data.get("topic", "")
    state = data.get("state", "")
    if topic in DEVICE_TOPICS:
        subprocess.run(["fluvio", "produce", topic], input=state + "\n", text=True)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Invalid topic"}), 400

def consume_numeric(topic):
    process = subprocess.Popen(["fluvio", "consume", topic, "-B"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"✅ Subscribed to {topic}")
    while True:
        line = process.stdout.readline()
        if line:
            try:
                val = float(line.strip())
                sensor_data[topic].append(val)
                current_values[topic] = val
                if len(sensor_data[topic]) > MAX_POINTS:
                    sensor_data[topic].pop(0)
                if topic == "dht-temp":
                    timestamps.append(datetime.now().strftime("%H:%M:%S"))
                    if len(timestamps) > MAX_POINTS:
                        timestamps.pop(0)
            except ValueError:
                print(f"⚠️ Invalid data for {topic}: {line.strip()}")

def consume_state(topic):
    process = subprocess.Popen(["fluvio", "consume", topic, "-B"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        line = process.stdout.readline()
        if line:
            state = line.strip().upper()
            if state in ["ON", "OFF"]:
                device_states[topic] = state

def start_consumers():
    for topic in SENSOR_TOPICS:
        Thread(target=consume_numeric, args=(topic,), daemon=True).start()
    for topic in DEVICE_TOPICS:
        Thread(target=consume_state, args=(topic,), daemon=True).start()

if __name__ == "__main__":
    print("🚀 Starting Smart Greenhouse Dashboard")
    start_consumers()
    app.run(host="0.0.0.0", port=5000)
