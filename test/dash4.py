from flask import Flask, render_template_string, request, jsonify
import subprocess
from threading import Thread, Lock
import time
from datetime import datetime

app = Flask(__name__)
lock = Lock()

# only keep last 4 points
LAST_N = 4

# sensor storage
timestamps = []
sensor_data = {topic: [] for topic in [
    "dht-temp", "dht-humid", "co2", "rain-sensor",
    "soil-moisture-1", "soil-moisture-2", "water-level-sensor"
]}
# track last cloud‑sent time for each topic (HH:MM:SS)
sensor_timestamps = {topic: None for topic in sensor_data}
# track epoch ms of last data arrival (for online/offline)
last_data_epoch = [time.time() * 1000]

device_states = {}
DEVICE_TOPICS = [
    "fan-1", "fan-2", "fan-3", "fan-4", "fan-5",
    "ac-1", "ac-2",
    "humidifier-1", "humidifier-2", "humidifier-3",
    "light-1", "light-2", "light-3", "light-4", "light-5",
    "water-pump"
]

HTML = """
<!doctype html>
<html>
<head>
  <title>🌿 Smart Greenhouse Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f2f6ff; margin:0; padding:20px; }
    h2,h3 { color:#2c3e50 }
    .status-box {
      display:flex; justify-content:space-between; align-items:center;
      background:#fff; padding:10px 15px; border-radius:10px;
      box-shadow:0 2px 6px rgba(0,0,0,0.1); margin-bottom:20px;
    }
    .status-online { color:green; font-weight:bold }
    .status-offline { color:red; font-weight:bold }
    .charts-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:20px }
    .chart-box {
      background:#fff; padding:15px; border-radius:12px;
      box-shadow:0 2px 6px rgba(0,0,0,0.1);
    }
    .device-control { margin-top:40px }
    .device-grid {
      display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:15px
    }
    .device-card {
      background:#fff; padding:10px 15px; border-radius:10px;
      box-shadow:0 2px 5px rgba(0,0,0,0.1);
      display:flex; justify-content:space-between; align-items:center
    }
    .toggle { position:relative; width:50px; height:24px }
    .toggle input { display:none }
    .slider {
      position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0;
      background:#ccc; transition:.4s; border-radius:34px
    }
    .slider:before {
      position:absolute; content:""; height:18px; width:18px;
      left:3px; bottom:3px; background:#fff; transition:.4s; border-radius:50%
    }
    input:checked + .slider { background:#4CAF50 }
    input:checked + .slider:before { transform:translateX(26px) }
  </style>
</head>
<body>
  <h2>🌱 Smart Greenhouse Dashboard</h2>
  <div class="status-box">
    <div>🔌 Greenhouse: <span id="status-text" class="status-online">Online</span></div>
    <div>📅 Last Cloud Time: <span id="last-update">--</span></div>
    <div>🕒 System Time: <span id="sys-datetime">--</span></div>
  </div>

  <h3>📋 Greenhouse Condition</h3>
  <ul id="conditions-list">
    <!-- filled by JS -->
  </ul>

  <div class="charts-grid">
    {% for t in sensor_topics %}
    <div class="chart-box">
      <h4>{{ t.replace('-', ' ').title() }} (<span id="{{t}}-value">--</span>)</h4>
      <canvas id="{{t}}-chart" height="150"></canvas>
    </div>
    {% endfor %}
  </div>

  <div class="device-control">
    <h3>🛠 Device Control</h3>
    <div class="device-grid">
      {% for t in device_topics %}
      <div class="device-card">
        <span>{{ t }}</span>
        <label class="toggle">
          <input type="checkbox" onchange="toggleDevice(this,'{{t}}')" id="switch-{{t}}">
          <span class="slider"></span>
        </label>
      </div>
      {% endfor %}
    </div>
  </div>

<script>
  let charts = {};

  function createChart(id, label) {
    const ctx = document.getElementById(id).getContext('2d');
    return new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label, data: [], tension: 0.3 }] },
      options: {
        responsive: true,
        plugins: { legend:{display:false} },
        scales: { x:{ ticks:{ maxTicksLimit:4 } } }
      }
    });
  }

  async function fetchData() {
    const res = await fetch('/data');
    const js = await res.json();
    const now = Date.now();
    const online = (now - js.last_update_epoch < 10000);

    // status
    const st = document.getElementById('status-text');
    st.textContent = online ? 'Online' : 'Offline';
    st.className = online ? 'status-online' : 'status-offline';
    document.getElementById('last-update').textContent = js.last_timestamp_display || '--';

    // charts & legends
    for (let t of Object.keys(js.sensors)) {
      const ch = charts[t];
      ch.data.labels = js.timestamps;
      ch.data.datasets[0].data = js.sensors[t];
      ch.update();
      document.getElementById(t + '-value').textContent = 
        js.sensors[t].slice(-1)[0] ?? '--';
    }

    // disable controls if offline
    document.querySelectorAll('.toggle input')
      .forEach(i=> i.disabled = !online);
  }

  async function fetchStates() {
    const res = await fetch('/device-status');
    const ds = await res.json();
    for (let [t, s] of Object.entries(ds)) {
      const cb = document.getElementById('switch-' + t);
      if (cb) cb.checked = (s === 'ON');
    }
  }

  async function fetchInsights() {
    const res = await fetch('/insights');
    const js = await res.json();
    const ul = document.getElementById('conditions-list');
    ul.innerHTML = '';
    for (let t of Object.keys(js.current_values)) {
      const li = document.createElement('li');
      const name = t.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
      li.textContent = `${name}: ${js.current_values[t]} → ${js.insights[t]}`;
      ul.appendChild(li);
    }
  }

  function toggleDevice(el, topic) {
    fetch('/device', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({topic, state: el.checked?'on':'off'})
    });
  }

  function updateSystemTime() {
    document.getElementById('sys-datetime')
      .textContent = new Date().toLocaleString();
  }

  window.onload = () => {
    const topics = {{ sensor_topics|tojson }};
    topics.forEach((t,i) => charts[t] = createChart(`${t}-chart`, t));
    // initial fetch
    fetchData(); fetchStates(); fetchInsights(); updateSystemTime();
    // intervals
    setInterval(fetchData, 5000);
    setInterval(fetchStates, 5000);
    setInterval(fetchInsights, 10000);
    setInterval(updateSystemTime, 1000);
  }
</script>
</body>
</html>
"""

def generate_insights(vals):
    ins = {}
    for k, v in vals.items():
        try:
            x = float(v)
            if k == "dht-temp":
                ins[k] = "Normal temperature" if 18<=x<=25 else ("⚠️ High temperature" if x>25 else "⚠️ Low temperature")
            elif k == "dht-humid":
                ins[k] = "Normal humidity" if 50<=x<=70 else ("⚠️ High humidity" if x>70 else "⚠️ Low humidity")
            elif k == "co2":
                ins[k] = "Safe" if x<=1000 else "⚠️ High CO2"
            elif "soil-moisture" in k:
                ins[k] = "Good moisture" if 30<=x<=70 else ("⚠️ Soil too wet" if x>70 else "⚠️ Soil too dry")
            elif k == "rain-sensor":
                ins[k] = "🌧️ Rain detected" if x>0 else "Clear"
            elif k == "water-level-sensor":
                ins[k] = "Low water level" if x<20 else "Sufficient water"
            else:
                ins[k] = "OK"
        except:
            ins[k] = "N/A"
    return ins

@app.route("/")
def dashboard():
    cvs = {k: (sensor_data[k][-1] if sensor_data[k] else "--") for k in sensor_data}
    return render_template_string(
        HTML,
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
    topic = data.get("topic","")
    state = data.get("state","")
    if topic in DEVICE_TOPICS:
        try:
            subprocess.run(["fluvio","produce",topic], input=state+"\n", text=True)
            print(f"⚙️ Command sent → {topic}: {state.upper()}")
            return jsonify(status="ok")
        except Exception as e:
            print(f"❌ Error sending to {topic}: {e}")
            return jsonify(status="error",message=str(e)),500
    return jsonify(status="error",message="Invalid topic"),400

def consume_numeric(topic):
    proc = subprocess.Popen(
        ["fluvio","consume",topic,"-B"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    print(f"✅ Subscribed to '{topic}'")
    while True:
        line = proc.stdout.readline()
        if line:
            parts = line.strip().split("=>")
            if len(parts)>=2:
                ts_raw = parts[0].strip()
                # get only HH:MM:SS
                ts = ts_raw.split()[-1]
                val_str = parts[-1].strip()
            else:
                ts = datetime.now().strftime("%H:%M:%S")
                val_str = line.strip()
            try:
                val = float(val_str)
                with lock:
                    sensor_data[topic].append(val)
                    if len(sensor_data[topic])>LAST_N:
                        sensor_data[topic].pop(0)
                    sensor_timestamps[topic] = ts
                    last_data_epoch[0] = time.time()*1000
                    if topic=="dht-temp":
                        timestamps.append(ts)
                        if len(timestamps)>LAST_N:
                            timestamps.pop(0)
                print(f"📥 {topic} @ {ts}: {val}")
            except ValueError:
                print(f"⚠️ Invalid from {topic}: {line.strip()}")
        else:
            time.sleep(0.1)  # small sleep in thread only

def consume_state(topic):
    proc = subprocess.Popen(
        ["fluvio","consume",topic,"-B"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    print(f"✅ Listening to '{topic}' for device status")
    while True:
        line = proc.stdout.readline()
        if line:
            st = line.strip().upper()
            if st in ["ON","OFF"]:
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
