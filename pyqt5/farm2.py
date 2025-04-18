import sys
import random
import time
import subprocess
import os
from threading import Thread
from fluvio import Fluvio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QMovie

ASSET_PATH = "pyqt5/assets"

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
    def __init__(self, fluvio):
        super().__init__()
        self.setWindowTitle("🌱 Greenhouse Simulator")
        self.setFixedSize(1200, 700)  # Increased width to fit 5 fans
        self.sensor_labels = {}
        self.device_labels = {}
        self.fan_images = {}
        self.fluvio = fluvio

        layout = QVBoxLayout()

        # Sensor section
        sensor_layout = QGridLayout()
        layout.addWidget(QLabel("🔍 Sensor Readings"), alignment=Qt.AlignLeft)
        for i, (topic, _) in enumerate(SENSOR_TOPICS.items()):
            label = QLabel(f"{topic}: 0")
            self.sensor_labels[topic] = label
            sensor_layout.addWidget(label, i // 2, i % 2)
        layout.addLayout(sensor_layout)

        # Fan row layout
        layout.addWidget(QLabel("\n🌬️ Fan Status"), alignment=Qt.AlignLeft)
        fan_row_layout = QHBoxLayout()
        for fan_topic in [f"fan-{i}" for i in range(1, 6)]:
            vbox = QVBoxLayout()

            # Fan label
            fan_label = QLabel()
            fan_label.setFixedSize(80, 80)
            fan_label.setScaledContents(True)
            self.fan_images[fan_topic] = fan_label
            self.update_fan_image(fan_topic, "UNKNOWN")
            vbox.addWidget(fan_label, alignment=Qt.AlignCenter)

            # Text label
            name = DEVICE_TOPICS[fan_topic]
            label = QLabel(f"{name}: UNKNOWN")
            label.setAlignment(Qt.AlignCenter)
            self.device_labels[fan_topic] = label
            vbox.addWidget(label)

            fan_row_layout.addLayout(vbox)

        layout.addLayout(fan_row_layout)

        # Other devices
        layout.addWidget(QLabel("\n🔌 Other Devices"), alignment=Qt.AlignLeft)
        other_devices_layout = QGridLayout()
        row = 0
        col = 0
        for topic, name in DEVICE_TOPICS.items():
            if topic.startswith("fan-"):
                continue
            label = QLabel(f"{name}: UNKNOWN")
            self.device_labels[topic] = label
            other_devices_layout.addWidget(label, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        layout.addLayout(other_devices_layout)

        self.setLayout(layout)

        # Start Fluvio producers & listeners
        self.producers = {topic: fluvio.topic_producer(topic) for topic in SENSOR_TOPICS}
        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

        # Periodic sensor update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)
        self.timer.start(5000)

    def update_sensors(self):
        for topic, simulator in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            self.sensor_labels[topic].setText(f"{topic}: {value}")

        for topic, label in self.device_labels.items():
            state = device_states[topic]
            label.setText(f"{DEVICE_TOPICS[topic]}: {state}")
            if topic.startswith("fan-"):
                self.update_fan_image(topic, state)

    def update_fan_image(self, topic, state):
        label = self.fan_images.get(topic)
        if not label:
            return
        if state == "ON":
            movie = QMovie(f"{ASSET_PATH}/fan-on.gif")
            movie.setScaledSize(label.size())
            label.setMovie(movie)
            movie.start()
        else:
            pixmap = QPixmap(f"{ASSET_PATH}/fan-off.png").scaled(
                label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)

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
        fluvio = Fluvio.connect()
        print("✅ Connected to Fluvio Cloud")
    except Exception as e:
        print("❌ Could not connect to Fluvio Cloud.")
        print(f"Error: {e}")
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Fluvio Connection Error")
        msg.setText("❌ Could not connect to Fluvio Cloud.\nPlease check your network and try again.")
        msg.exec_()
        return

    if not check_required_topics():
        print("⚠️ Please create the missing topics using `fluvio topic create ...`.")
        return

    show_profile_info()

    app = QApplication(sys.argv)
    window = GreenhouseSimulator(fluvio)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
