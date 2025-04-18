from flask import Flask, render_template, request, jsonify
import subprocess
from threading import Thread, Lock
import time
from datetime import datetime, timezone
import pytz

app = Flask(__name__, static_folder='assets')

lock = Lock()

local_tz = pytz.timezone("Asia/Kolkata")
LAST_N = 20
timestamps = []
sensor_data = {topic: [] for topic in [
    "dht-temp", "dht-humid", "co2", "rain-sensor",
    "soil-moisture-1", "soil-moisture-2", "water-level-sensor"
]}
sensor_timestamps = {topic: None for topic in sensor_data}
last_data_epoch = [time.time() * 1000]
device_states = {}
DEVICE_TOPICS = [
    "fan-1", "fan-2", "fan-3", "fan-4", "fan-5",
    "ac-1", "ac-2",
    "humidifier-1", "humidifier-2", "humidifier-3",
    "light-1", "light-2", "light-3", "light-4", "light-5",
    "water-pump"
]

def generate_insights(vals):
    ins = {}
    for k, v in vals.items():
        try:
            x = float(v)
            if k == "dht-temp":
                ins[k] = "Normal temperature" if 18 <= x <= 25 else ("⚠️ High temperature" if x > 25 else "⚠️ Low temperature")
            elif k == "dht-humid":
                ins[k] = "Normal humidity" if 50 <= x <= 70 else ("⚠️ High humidity" if x > 70 else "⚠️ Low humidity")
            elif k == "co2":
                ins[k] = "Safe" if x <= 1000 else "⚠️ High CO2"
            elif "soil-moisture" in k:
                ins[k] = "Good moisture" if 30 <= x <= 70 else ("⚠️ Soil too wet" if x > 70 else "⚠️ Soil too dry")
            elif k == "rain-sensor":
                ins[k] = "🌧️ Rain detected" if x > 0 else "Clear"
            elif k == "water-level-sensor":
                ins[k] = "Low water level" if x < 20 else "Sufficient water"
            else:
                ins[k] = "OK"
        except:
            ins[k] = "N/A"
    return ins

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        sensor_topics=list(sensor_data.keys()),
        device_topics=DEVICE_TOPICS
    )

@app.route("/data")
def data():
    with lock:
        return jsonify({
            "timestamps": timestamps,
            "sensors": sensor_data,
            "last_timestamp_display": sensor_timestamps["dht-temp"],
            "last_update_epoch": last_data_epoch[0]
        })

@app.route("/insights")
def insights():
    cvs = {k: (sensor_data[k][-1] if sensor_data[k] else "--") for k in sensor_data}
    return jsonify({
        "current_values": cvs,
        "insights": generate_insights(cvs)
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
            return jsonify(status="ok")
        except Exception as e:
            print(f"❌ Error sending to {topic}: {e}")
            return jsonify(status="error", message=str(e)), 500
    return jsonify(status="error", message="Invalid topic"), 400

def consume_numeric(topic):
    proc = subprocess.Popen(
        ["fluvio", "consume", topic, "-T20", "--format={{time}},{{value}}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    print(f"✅ Subscribed to '{topic}'")
    while True:
        line = proc.stdout.readline()
        if line:
            try:
                ts_full, val_str = line.strip().split(",", 1)
                try:
                    dt_utc = datetime.strptime(ts_full, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    dt_utc = datetime.strptime(ts_full, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                dt_local = dt_utc.astimezone(local_tz)
                ts = dt_local.strftime("%H:%M:%S")

                val = float(val_str)
                with lock:
                    sensor_data[topic].append(val)
                    if len(sensor_data[topic]) > LAST_N:
                        sensor_data[topic].pop(0)
                    sensor_timestamps[topic] = ts
                    last_data_epoch[0] = time.time() * 1000
                    if topic == "dht-temp":
                        timestamps.append(ts)
                        if len(timestamps) > LAST_N:
                            timestamps.pop(0)
                print(f"📥 {topic}: {val} @ {ts}")
            except Exception as e:
                print(f"⚠️ Parse error for {topic}: {line.strip()}")
        else:
            time.sleep(0.1)

def consume_state(topic):
    proc = subprocess.Popen(
        ["fluvio", "consume", topic, "-B"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    print(f"✅ Listening to '{topic}' for device status")
    while True:
        line = proc.stdout.readline()
        if line:
            st = line.strip().upper()
            if st in ["ON", "OFF"]:
                device_states[topic] = st
                print(f"🔄 {topic} status → {st}")
        else:
            time.sleep(0.1)

def start_consumers():
    for t in sensor_data:
        Thread(target=consume_numeric, args=(t,), daemon=True).start()
    for t in DEVICE_TOPICS:
        device_states[t] = "UNKNOWN"
        Thread(target=consume_state, args=(t,), daemon=True).start()

if __name__ == "__main__":
    print("🚀 Starting Smart Greenhouse Dashboard")
    start_consumers()
    app.run(host="0.0.0.0", port=5000)
