import sys
import os
import time
import random
import subprocess
from threading import Thread
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer
from fluvio import Fluvio

# Paths
DEVICE_IMG_PATH = "pyqt5/assets/devices"
SENSOR_IMG_PATH = "pyqt5/assets/sensors"

# Sensors generate data
SENSOR_TOPICS = {
    "dht-temp": lambda: round(random.uniform(18, 30), 2),
    "dht-humid": lambda: round(random.uniform(50, 90), 2),
    "co2": lambda: round(random.uniform(300, 800), 2),
    "soil-moisture-1": lambda: round(random.uniform(10, 70), 2),
    "soil-moisture-2": lambda: round(random.uniform(10, 70), 2),
    "water-level-sensor": lambda: round(random.uniform(0, 100), 2),
}

# Devices have ON/OFF state
DEVICE_TOPICS = {
    "fan-1": "Fan 1",
    "fan-2": "Fan 2",
    "fan-3": "Fan 3",
    "fan-4": "Fan 4",
    "fan-5": "Fan 5",
    "ac-1": "AC 1",
    "ac-2": "AC 2",
    "humidifier-1": "Humidifier 1",
    "humidifier-2": "Humidifier 2",
    "humidifier-3": "Humidifier 3",
    "light-1": "Light 1",
    "light-2": "Light 2",
    "light-3": "Light 3",
    "light-4": "Light 4",
    "light-5": "Light 5",
    "water-pump": "Water Pump"
}

device_states = {k: "UNKNOWN" for k in DEVICE_TOPICS}


class DeviceWidget(QVBoxLayout):
    def __init__(self, name, topic):
        super().__init__()
        self.topic = topic
        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_label.setFixedSize(60, 60)
        self.image_label.setScaledContents(True)
        self.addWidget(self.image_label)
        self.addWidget(self.label)
        self.update_image("UNKNOWN")

    def update_image(self, state):
        if state == "ON":
            path = os.path.join(DEVICE_IMG_PATH, f"{self.topic.split('-')[0]}-on.gif")
            movie = QMovie(path)
            movie.setScaledSize(self.image_label.size())
            self.image_label.setMovie(movie)
            movie.start()
        else:
            path = os.path.join(DEVICE_IMG_PATH, f"{self.topic.split('-')[0]}-off.png")
            pixmap = QPixmap(path).scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)


class SensorWidget(QVBoxLayout):
    def __init__(self, name, topic):
        super().__init__()
        self.topic = topic
        self.label = QLabel(f"{name}: 0")
        self.label.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_label.setFixedSize(60, 60)
        self.image_label.setScaledContents(True)
        path = os.path.join(SENSOR_IMG_PATH, f"{topic.split('-')[0]}.png")
        self.image_label.setPixmap(QPixmap(path))
        self.addWidget(self.image_label)
        self.addWidget(self.label)

    def update_value(self, value):
        self.label.setText(f"{self.topic}: {value}")


class GreenhouseDashboard(QWidget):
    def __init__(self, fluvio):
        super().__init__()
        self.setWindowTitle("🌿 Greenhouse Simulator")
        self.setFixedSize(1280, 800)

        self.fluvio = fluvio
        self.producers = {t: self.fluvio.topic_producer(t) for t in SENSOR_TOPICS}

        self.device_widgets = {}
        self.sensor_widgets = {}

        main_layout = QVBoxLayout()

        # Header
        self.connection_label = QLabel("🔌 Fluvio: Checking...")
        self.profile_label = QLabel("👤 Profile: ---")
        self.time_label = QLabel("🕒 Time: ---")

        header = QHBoxLayout()
        for label in [self.connection_label, self.profile_label, self.time_label]:
            label.setStyleSheet("font-size: 14px; padding: 6px;")
            header.addWidget(label)
        main_layout.addLayout(header)

        # Grouped Rows
        main_layout.addLayout(self.create_row(["fan-1", "fan-2", "fan-3", "fan-4", "fan-5", "co2"]))
        main_layout.addLayout(self.create_row(["humidifier-1", "humidifier-2", "humidifier-3", "dht-humid"]))
        main_layout.addLayout(self.create_row(["light-1", "light-2", "light-3", "light-4", "light-5"]))
        main_layout.addLayout(self.create_row(["water-pump", "water-level-sensor"]))
        main_layout.addLayout(self.create_row(["dht-temp", "ac-1", "ac-2"]))
        main_layout.addLayout(self.create_row(["soil-moisture-1", "soil-moisture-2"]))

        self.setLayout(main_layout)

        # Start listeners
        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)

        # Start clock timer
        self.clock = QTimer()
        self.clock.timeout.connect(self.update_time)
        self.clock.start(1000)

        # Set profile & connection
        self.set_connection_status()

    def create_row(self, topics):
        row = QHBoxLayout()
        for topic in topics:
            if topic in DEVICE_TOPICS:
                widget = DeviceWidget(DEVICE_TOPICS[topic], topic)
                self.device_widgets[topic] = widget
            else:
                widget = SensorWidget(topic, topic)
                self.sensor_widgets[topic] = widget
            container = QFrame()
            container.setLayout(widget)
            row.addWidget(container)
        return row

    def set_connection_status(self):
        try:
            profiles = os.popen("fluvio profile list").read()
            current_profile = os.popen("fluvio profile current").read().strip()
            if not current_profile:
                self.connection_label.setText("🔌 Fluvio: Login Required")
            else:
                self.connection_label.setText("🔌 Fluvio: Connected")
                self.profile_label.setText(f"👤 Profile: {current_profile}")
        except:
            self.connection_label.setText("🔌 Fluvio: Not Connected")

    def update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"🕒 Time: {now}")

    def refresh(self):
        for topic, simulator in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            if topic in self.sensor_widgets:
                self.sensor_widgets[topic].update_value(value)

        for topic, widget in self.device_widgets.items():
            widget.update_image(device_states[topic])

    def listen_control(self, topic):
        def consume():
            process = subprocess.Popen(
                ["fluvio", "consume", topic, "-T20"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            while True:
                line = process.stdout.readline()
                if line:
                    command = line.strip().lower()
                    if command in ["on", "off"]:
                        device_states[topic] = command.upper()
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
    print("🔌 Starting Greenhouse Simulator...")
    try:
        fluvio = Fluvio.connect()
    except Exception as e:
        print(f"❌ Fluvio Connection Error: {e}")
        return

    if not check_required_topics():
        print("⚠️ Please create missing topics using: `fluvio topic create <topic>`")
        return

    app = QApplication(sys.argv)
    window = GreenhouseDashboard(fluvio)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
