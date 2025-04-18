import sys
import random
import time
import subprocess
import os
from threading import Thread
from fluvio import Fluvio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer

SENSOR_TOPICS = {
    "dht-temp": lambda: round(random.uniform(18, 30), 2),
    "dht-humid": lambda: round(random.uniform(50, 90), 2),
    "co2": lambda: round(random.uniform(300, 800), 2),
    "rain-sensor": lambda: round(random.uniform(0, 100), 2),
    "soil-moisture-1": lambda: round(random.uniform(10, 70), 2),
    "soil-moisture-2": lambda: round(random.uniform(10, 70), 2),
    "water-level-sensor": lambda: round(random.uniform(0, 100), 2),
}

DEVICE_TOPICS = {
    "fan-1": "🌬️ Fan 1",
    "fan-2": "🌬️ Fan 2",
    "fan-3": "🌬️ Fan 3",
    "fan-4": "🌬️ Fan 4",
    "fan-5": "🌬️ Fan 5",
    "ac-1": "❄️ AC 1",
    "ac-2": "❄️ AC 2",
    "humidifier-1": "💧 Humidifier 1",
    "humidifier-2": "💧 Humidifier 2",
    "humidifier-3": "💧 Humidifier 3",
    "light-1": "💡 Light 1",
    "light-2": "💡 Light 2",
    "light-3": "💡 Light 3",
    "light-4": "💡 Light 4",
    "light-5": "💡 Light 5",
    "water-pump": "🚿 Water Pump"
}

device_states = {k: "UNKNOWN" for k in DEVICE_TOPICS}


class GreenhouseSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌱 Greenhouse Simulator")
        self.setGeometry(100, 100, 800, 600)
        self.sensor_labels = {}
        self.device_labels = {}

        layout = QVBoxLayout()

        # Sensor section
        sensor_layout = QGridLayout()
        layout.addWidget(QLabel("🔍 Sensor Readings"), alignment=Qt.AlignLeft)
        for i, (topic, _) in enumerate(SENSOR_TOPICS.items()):
            label = QLabel(f"{topic}: 0")
            self.sensor_labels[topic] = label
            sensor_layout.addWidget(label, i // 2, i % 2)
        layout.addLayout(sensor_layout)

        # Devices section
        layout.addWidget(QLabel("\n🔌 Device States"), alignment=Qt.AlignLeft)
        device_layout = QGridLayout()
        for i, (topic, name) in enumerate(DEVICE_TOPICS.items()):
            label = QLabel(f"{name}: UNKNOWN")
            self.device_labels[topic] = label
            device_layout.addWidget(label, i // 2, i % 2)
        layout.addLayout(device_layout)

        self.setLayout(layout)

        self.fluvio = Fluvio.connect()
        self.producers = {topic: self.fluvio.topic_producer(topic) for topic in SENSOR_TOPICS}

        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)
        self.timer.start(5000)  # update every 5 seconds

    def update_sensors(self):
        for topic, simulator in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            self.sensor_labels[topic].setText(f"{topic}: {value}")
        for topic, label in self.device_labels.items():
            label.setText(f"{DEVICE_TOPICS[topic]}: {device_states[topic]}")

    def listen_control(self, topic):
        def consume():
            process = subprocess.Popen(
                ["fluvio", "consume", topic, "-T20"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            print(f"📡 Listening for commands on topic '{topic}'...")
            while True:
                line = process.stdout.readline()
                if line:
                    command = line.strip().lower()
                    if command in ["on", "off"]:
                        device_states[topic] = command.upper()
                    else:
                        print(f"⚠️ Unknown command '{command}' on topic {topic}")
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


def show_profile_info():
    print("🌍 Checking Fluvio profile info...\n")
    current_profile = os.popen("fluvio profile current").read().strip()
    print(f"🟢 Current Profile: {current_profile}")
    profiles = os.popen("fluvio profile list").read()
    print("📄 Available Profiles:\n" + profiles)


def main():
    print("🔌 Connecting to Fluvio...")
    try:
        if not check_required_topics():
            print("⚠️ Please create the missing topics using `fluvio topic create ...`.")
            return

        show_profile_info()

        app = QApplication(sys.argv)
        window = GreenhouseSimulator()
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
