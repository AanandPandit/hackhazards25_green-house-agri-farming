from flask import Flask, render_template_string, jsonify
from threading import Thread
import subprocess
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
    <meta http-equiv="refresh" content="3600">
</head>
<body style="font-family:sans-serif;">
    <h2>📊 Live Cabbage Climate Dashboard</h2>
    <canvas id="climateChart" width="600" height="300"></canvas>
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
