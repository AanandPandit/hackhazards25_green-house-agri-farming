from flask import Flask, render_template_string, request, jsonify
import subprocess
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)
temp_data = []
humid_data = []
timestamps = []
device_states = {}

MAX_POINTS = 20

DEVICE_TOPICS = [
    "led-red", "led-green", "led-blue", "led-yellow", "led-white",
    "fan-1", "fan-2", "fan-3", "fan-4", "fan-5",
    "ac-1", "ac-2",
    "water-pump"
]

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>🌿 Greenhouse Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .charts { display: flex; gap: 20px; }
        .chart-box { width: 45%; }
        .device-control { margin-top: 30px; }
        .device-row { display: flex; align-items: center; margin-bottom: 10px; }
        .toggle {
            position: relative;
            width: 60px;
            height: 30px;
            margin-left: 10px;
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
            height: 24px; width: 24px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #4CAF50;
        }
        input:checked + .slider:before {
            transform: translateX(30px);
        }
    </style>
</head>
<body>
    <h2>🌡️ Greenhouse Climate Dashboard</h2>
    <div class="charts">
        <div class="chart-box">
            <h4>Temperature (°C)</h4>
            <canvas id="tempChart" height="180"></canvas>
        </div>
        <div class="chart-box">
            <h4>Humidity (%)</h4>
            <canvas id="humidChart" height="180"></canvas>
        </div>
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
let tempChart, humidChart;

function initCharts() {
    const tempCtx = document.getElementById('tempChart').getContext('2d');
    const humidCtx = document.getElementById('humidChart').getContext('2d');

    tempChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                borderColor: 'red',
                data: [],
                tension: 0.2
            }]
        },
        options: { scales: { x: { ticks: { autoSkip: true, maxTicksLimit: 6 } } } }
    });

    humidChart = new Chart(humidCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humidity (%)',
                borderColor: 'blue',
                data: [],
                tension: 0.2
            }]
        },
        options: { scales: { x: { ticks: { autoSkip: true, maxTicksLimit: 6 } } } }
    });
}

async function fetchData() {
    const res = await fetch("/data");
    const data = await res.json();

    tempChart.data.labels = data.timestamps;
    humidChart.data.labels = data.timestamps;

    tempChart.data.datasets[0].data = data.temps;
    humidChart.data.datasets[0].data = data.humids;

    tempChart.update();
    humidChart.update();
}

async function fetchDeviceStates() {
    const res = await fetch("/device-status");
    const data = await res.json();
    for (const [topic, state] of Object.entries(data)) {
        const checkbox = document.getElementById("switch-" + topic);
        const label = document.getElementById("status-" + topic);
        if (checkbox) checkbox.checked = (state === "ON");
        if (label) label.innerText =x state;
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
    return render_template_string(HTML_TEMPLATE, device_topics=DEVICE_TOPICS)

@app.route("/data")
def data():
    return jsonify({
        "timestamps": timestamps,
        "temps": temp_data,
        "humids": humid_data
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

def consume_numeric(topic, target_list):
    process = subprocess.Popen(["fluvio", "consume", topic, "-B"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"✅ Subscribed to '{topic}'")

    while True:
        line = process.stdout.readline()
        if line:
            try:
                value = float(line.strip())
                target_list.append(value)
                if topic == "dht-temp":
                    print(f"🌡️ Temperature: {value}°C")
                elif topic == "dht-humid":
                    print(f"💧 Humidity: {value}%")
                if len(target_list) > MAX_POINTS:
                    target_list.pop(0)
                # Append a timestamp only once per cycle (temp triggers it)
                if topic == "dht-temp":
                    timestamps.append(datetime.now().strftime("%H:%M:%S"))
                    if len(timestamps) > MAX_POINTS:
                        timestamps.pop(0)
            except ValueError:
                print(f"⚠️ Invalid numeric value on {topic}: {line.strip()}")
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
    Thread(target=consume_numeric, args=("dht-temp", temp_data), daemon=True).start()
    Thread(target=consume_numeric, args=("dht-humid", humid_data), daemon=True).start()
    for topic in DEVICE_TOPICS:
        device_states[topic] = "UNKNOWN"
        Thread(target=consume_state, args=(topic,), daemon=True).start()

if __name__ == "__main__":
    print("🚀 Starting Greenhouse Dashboard")
    start_consumers()
    app.run(host="0.0.0.0", port=5000)
