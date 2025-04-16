from flask import Flask, render_template_string, request, jsonify
import subprocess
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)
timestamps = []
sensor_data = {k: [] for k in [
    "dht-temp", "dht-humid", "co2", "rain-sensor",
    "soil-moisture-1", "soil-moisture-2", "water-level-sensor"
]}
device_states = {}

MAX_POINTS = 20

DEVICE_TOPICS = [
    "fan-1", "fan-2", "fan-3", "fan-4", "fan-5",
    "ac-1", "ac-2",
    "humidifier-1", "humidifier-2", "humidifier-3",
    "light-1", "light-2", "light-3", "light-4", "light-5",
    "water-pump"
]

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>🌿 Smart Greenhouse Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f2f6ff; margin: 0; padding: 20px; }
        h2 { color: #2c3e50; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .chart-box {
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .device-control {
            margin-top: 40px;
        }
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .device-card {
            background: white;
            padding: 10px 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .toggle {
            position: relative;
            width: 50px;
            height: 24px;
        }
        .toggle input { display: none; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0;
            right: 0; bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 18px; width: 18px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #4CAF50;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
    </style>
</head>
<body>
    <h2>🌱 Smart Greenhouse Dashboard</h2>

    <div class="charts-grid">
        {% for topic in sensor_topics %}
        <div class="chart-box">
            <h4>{{ topic.replace('-', ' ').title() }}</h4>
            <canvas id="{{ topic }}-chart" height="150"></canvas>
        </div>
        {% endfor %}
    </div>

    <div class="device-control">
        <h3>🛠 Device Control</h3>
        <div class="device-grid">
        {% for topic in device_topics %}
            <div class="device-card">
                <span>{{ topic }}</span>
                <label class="toggle">
                    <input type="checkbox" onchange="toggleDevice(this, '{{ topic }}')" id="switch-{{ topic }}">
                    <span class="slider"></span>
                </label>
            </div>
        {% endfor %}
        </div>
    </div>

<script>
let charts = {};

function createChart(id, label, color) {
    const ctx = document.getElementById(id).getContext("2d");
    return new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label, data: [], borderColor: color, tension: 0.3 }] },
        options: {
            responsive: true,
            scales: { x: { ticks: { maxTicksLimit: 5 } } }
        }
    });
}

async function fetchData() {
    const res = await fetch("/data");
    const data = await res.json();
    for (const topic of Object.keys(data.sensors)) {
        if (!charts[topic]) continue;
        charts[topic].data.labels = data.timestamps;
        charts[topic].data.datasets[0].data = data.sensors[topic];
        charts[topic].update();
    }
}

async function fetchDeviceStates() {
    const res = await fetch("/device-status");
    const data = await res.json();
    for (const [topic, state] of Object.entries(data)) {
        const checkbox = document.getElementById("switch-" + topic);
        if (checkbox) checkbox.checked = (state === "ON");
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

window.onload = () => {
    const topics = {{ sensor_topics|tojson }};
    const colors = ["red", "blue", "green", "orange", "purple", "teal", "gray"];
    topics.forEach((t, i) => charts[t] = createChart(`${t}-chart`, t, colors[i % colors.length]));

    setInterval(fetchData, 5000);
    setInterval(fetchDeviceStates, 5000);
}
</script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(HTML_TEMPLATE, sensor_topics=list(sensor_data.keys()), device_topics=DEVICE_TOPICS)

@app.route("/data")
def data():
    return jsonify({
        "timestamps": timestamps,
        "sensors": sensor_data
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
        try:
            subprocess.run(["fluvio", "produce", topic], input=state + "\n", text=True)
            print(f"⚙️ Command sent → {topic}: {state.upper()}")
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "Invalid topic"}), 400

def consume_numeric(topic):
    process = subprocess.Popen(["fluvio", "consume", topic, "-B"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"✅ Subscribed to '{topic}'")
    while True:
        line = process.stdout.readline()
        if line:
            try:
                value = float(line.strip())
                sensor_data[topic].append(value)
                if len(sensor_data[topic]) > MAX_POINTS:
                    sensor_data[topic].pop(0)
                if topic == "dht-temp":
                    timestamps.append(datetime.now().strftime("%H:%M:%S"))
                    if len(timestamps) > MAX_POINTS:
                        timestamps.pop(0)
            except ValueError:
                print(f"⚠️ Invalid value from {topic}: {line.strip()}")
        else:
            time.sleep(1)

def consume_state(topic):
    process = subprocess.Popen(["fluvio", "consume", topic, "-B"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"✅ Listening to '{topic}' for device status")
    while True:
        line = process.stdout.readline()
        if line:
            state = line.strip().upper()
            if state in ["ON", "OFF"]:
                device_states[topic] = state
                print(f"🔄 {topic} status updated to {state}")
        else:
            time.sleep(1)

def start_consumers():
    for topic in sensor_data:
        Thread(target=consume_numeric, args=(topic,), daemon=True).start()
    for topic in DEVICE_TOPICS:
        device_states[topic] = "UNKNOWN"
        Thread(target=consume_state, args=(topic,), daemon=True).start()

if __name__ == "__main__":
    print("🚀 Starting Smart Greenhouse Dashboard")
    start_consumers()
    app.run(host="0.0.0.0", port=5000)
