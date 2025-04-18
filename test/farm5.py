import sys
import random
import time
import subprocess
import os
from threading import Thread
from datetime import datetime
from fluvio import Fluvio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QMovie, QColor

ASSETS_DEVICES = "pyqt5/assets/devices"
ASSETS_SENSORS = "pyqt5/assets/sensors"

SENSOR_TOPICS = {
    "dht-temp": ("Temperature", lambda: round(random.uniform(18, 30), 2), "dht-temp.png"),
    "dht-humid": ("Humidity", lambda: round(random.uniform(50, 90), 2), "dht-humid.png"),
    "co2": ("CO2", lambda: round(random.uniform(300, 800), 2), "co2.png"),
    "rain-sensor": ("Rain Sensor", lambda: round(random.uniform(0, 100), 2), "rain-sensor.png"),
    "soil-moisture-1": ("Soil Moisture 1", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png"),
    "soil-moisture-2": ("Soil Moisture 2", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png"),
    "water-level-sensor": ("Water Level", lambda: round(random.uniform(0, 100), 2), None),
}

DEVICE_TOPICS = {
    "fan-1": ("Fan 1", "fan"), "fan-2": ("Fan 2", "fan"), "fan-3": ("Fan 3", "fan"),
    "fan-4": ("Fan 4", "fan"), "fan-5": ("Fan 5", "fan"),
    "light-1": ("Light 1", "light"), "light-2": ("Light 2", "light"),
    "light-3": ("Light 3", "light"), "light-4": ("Light 4", "light"), "light-5": ("Light 5", "light"),
    "ac-1": ("AC 1", "ac"), "ac-2": ("AC 2", "ac"),
    "humidifier-1": ("Humidifier 1", "humidifier"), "humidifier-2": ("Humidifier 2", "humidifier"), "humidifier-3": ("Humidifier 3", "humidifier"),
    "water-pump": ("Water Pump", "water-pump")
}

device_states = {k: "UNKNOWN" for k in DEVICE_TOPICS}


class GreenhouseSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌿 Greenhouse Monitoring Dashboard")
        self.setFixedSize(1200, 800)
        self.setStyleSheet("background-color: white;")

        self.sensor_labels = {}
        self.device_labels = {}

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setup_header()
        self.add_separator()
        self.setup_sensors()
        self.add_separator()
        self.setup_devices()
        self.add_separator()
        self.setup_terminal_output()

        self.fluvio = Fluvio.connect()
        self.producers = {topic: self.fluvio.topic_producer(topic) for topic in SENSOR_TOPICS}

        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)
        self.timer.start(5000)

    def setup_header(self):
        header = QVBoxLayout()
        title = QLabel("<h1>🌱 Greenhouse Monitoring</h1>")
        profile = os.popen("fluvio profile current").read().strip()
        connection = QLabel(f"🟢 Connected to Fluvio | Profile: {profile} | Time: {datetime.now().strftime('%H:%M:%S')}")
        connection.setStyleSheet("color: green;")
        header.addWidget(title)
        header.addWidget(connection)
        self.layout.addLayout(header)

    def setup_sensors(self):
        grid = QGridLayout()
        for i, (topic, (name, _, icon)) in enumerate(SENSOR_TOPICS.items()):
            hbox = QHBoxLayout()
            if icon:
                pixmap = QPixmap(f"{ASSETS_SENSORS}/{icon}").scaled(50, 50, Qt.KeepAspectRatio)
                hbox.addWidget(QLabel(pixmap=pixmap))
            label = QLabel(f"{name}: 0")
            hbox.addWidget(label)
            grid.addLayout(hbox, i, 0)
            self.sensor_labels[topic] = label
        self.layout.addLayout(grid)

    def setup_devices(self):
        rows = [[], [], [], [], []]  # fans, lights, ac+humidifiers, water level + pump
        for topic, (name, dtype) in DEVICE_TOPICS.items():
            label = QLabel()
            gif_file = f"{ASSETS_DEVICES}/{dtype}-on.gif"
            static_file = f"{ASSETS_DEVICES}/{dtype}-off.png"
            label.setPixmap(QPixmap(static_file).scaled(60, 60))
            label.setToolTip(f"{name}: UNKNOWN")
            self.device_labels[topic] = (label, gif_file, static_file)
            if "fan" in topic:
                rows[0].append(label)
            elif "light" in topic:
                rows[1].append(label)
            elif "ac" in topic or "humidifier" in topic:
                rows[2].append(label)
            elif "water-pump" in topic:
                rows[4].append(label)

        for row in rows:
            hbox = QHBoxLayout()
            for lbl in row:
                hbox.addWidget(lbl)
            self.layout.addLayout(hbox)

    def setup_terminal_output(self):
        self.terminal = QTextEdit()
        self.terminal.setFixedHeight(120)
        self.terminal.setStyleSheet("background-color: #f0f0f0; font-family: monospace; font-size: 10pt;")
        self.terminal.setReadOnly(True)
        self.layout.addWidget(self.terminal)

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(line)

    def update_sensors(self):
        for topic, (name, simulator, _) in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            self.sensor_labels[topic].setText(f"{name}: {value}")
        for topic, (label, gif_file, static_file) in self.device_labels.items():
            state = device_states[topic]
            if state == "ON":
                movie = QMovie(gif_file)
                movie.setScaledSize(label.size())
                label.setMovie(movie)
                movie.start()
                label.setToolTip(f"{DEVICE_TOPICS[topic][0]}: ON")
            else:
                label.setPixmap(QPixmap(static_file).scaled(60, 60))
                label.setToolTip(f"{DEVICE_TOPICS[topic][0]}: OFF")

    def listen_control(self, topic):
        def consume():
            process = subprocess.Popen(
                ["fluvio", "consume", topic, "-T20"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            msg = f"📡 Listening for commands on topic '{topic}'..."
            print(msg)
            self.terminal.append(msg)
            while True:
                line = process.stdout.readline()
                if line:
                    command = line.strip().lower()
                    if command in ["on", "off"]:
                        device_states[topic] = command.upper()
                        self.terminal.append(f"✅ {DEVICE_TOPICS[topic][0]} set to {command.upper()}")
                    else:
                        warn = f"⚠️ Unknown command '{command}' on topic {topic}"
                        print(warn)
                        self.terminal.append(warn)
                else:
                    time.sleep(1)
        Thread(target=consume, daemon=True).start()


def check_required_topics():
    required = list(SENSOR_TOPICS.keys()) + list(DEVICE_TOPICS.keys())
    try:
        result = subprocess.run(["fluvio", "topic", "list"], capture_output=True, text=True)
        output = result.stdout
        existing = [line.split()[0] for line in output.splitlines()[1:] if line.strip()]
        missing = [t for t in required if t not in existing]
        if missing:
            print(f"❌ Missing topics: {', '.join(missing)}")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Error checking topics: {e}")
        return False


def main():
    print("🔌 Connecting to Fluvio...")
    if not check_required_topics():
        print("⚠️ Please create the missing topics using `fluvio topic create ...`.")
        return

    print("🌍 Checking Fluvio profile info...")
    current_profile = os.popen("fluvio profile current").read().strip()
    print(f"🟢 Current Profile: {current_profile}")
    profiles = os.popen("fluvio profile list").read()
    print("📄 Available Profiles:\n" + profiles)

    app = QApplication(sys.argv)
    window = GreenhouseSimulator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
