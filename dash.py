from flask import Flask, render_template_string, request, jsonify
import subprocess
from threading import Thread
import time

app = Flask(__name__)
temp_data = []
humid_data = []
MAX_POINTS = 20

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>🌿 Greenhouse Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body style="font-family:sans-serif;">
    <h2>📊 Live Cabbage Climate Dashboard</h2>
    <canvas id="climateChart" width="600" height="300"></canvas>
    <br>
    <h3>💡 LED Control</h3>
    <button onclick="controlLED('on')">Turn ON</button>
    <button onclick="controlLED('off')">Turn OFF</button>
    <script>
    const ctx = document.getElementById('climateChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '🌡️ Temperature (°C)',
                    borderColor: 'rgb(255, 99, 132)',
                    data: [],
                    tension: 0.2
                },
                {
                    label: '💧 Humidity (%)',
                    borderColor: 'rgb(54, 162, 235)',
                    data: [],
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    async function fetchData() {
        const res = await fetch("/data");
        const data = await res.json();
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.temps;
        chart.data.datasets[1].data = data.humids;
        chart.update();
    }

    function controlLED(state) {
        fetch("/led", {
            method: "POST",
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({state})
        });
    }

    fetchData();
    setInterval(fetchData, 5000);
    </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route("/data")
def data():
    labels = list(range(len(temp_data)))
    return jsonify({
        "labels": labels,
        "temps": temp_data,
        "humids": humid_data
    })

@app.route("/led", methods=["POST"])
def led_control():
    state = request.json.get("state", "")
    try:
        subprocess.run(["fluvio", "produce", "led-control"], input=state + "\n", text=True)
        print(f"💡 LED control command sent: {state}")
        return jsonify({"status": "ok", "command": state})
    except Exception as e:
        print(f"❌ LED control error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def consume_topic(topic, target_list):
    process = subprocess.Popen(
        ["fluvio", "consume", topic, "-B"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print(f"✅ Subscribed to '{topic}' using Fluvio CLI")

    while True:
        line = process.stdout.readline()
        if line:
            try:
                value = float(line.strip())
                target_list.append(value)
                if len(target_list) > MAX_POINTS:
                    target_list.pop(0)
                print(f"[{topic}] {value}")
            except ValueError:
                print(f"⚠️ Skipping non-numeric data: {line.strip()}")
        else:
            time.sleep(1)

def start_consumers():
    Thread(target=consume_topic, args=("dht-temp", temp_data), daemon=True).start()
    Thread(target=consume_topic, args=("dht-humid", humid_data), daemon=True).start()

if __name__ == "__main__":
    print("🚀 Starting Flask + Fluvio CLI Dashboard")
    start_consumers()
    app.run(host="0.0.0.0", port=5000)
