import sys
import os
import time
import random
import subprocess
from threading import Thread
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QProgressBar, QSizePolicy, QSpacerItem
)
from PyQt5.QtGui import QPixmap, QMovie, QFont
from PyQt5.QtCore import Qt, QTimer
from fluvio import Fluvio

# Image paths
DEVICE_IMG_PATH = "pyqt5/assets/devices"
SENSOR_IMG_PATH = "pyqt5/assets/sensors"

# Data
SENSOR_TOPICS = {
    "dht-temp": lambda: round(random.uniform(18, 30), 2),
    "dht-humid": lambda: round(random.uniform(50, 90), 2),
    "co2": lambda: round(random.uniform(300, 800), 2),
    "soil-moisture-1": lambda: round(random.uniform(10, 70), 2),
    "soil-moisture-2": lambda: round(random.uniform(10, 70), 2),
    "water-level-sensor": lambda: round(random.uniform(0, 100), 2),
}

DEVICE_TOPICS = {
    "fan-1": "Fan 1", "fan-2": "Fan 2", "fan-3": "Fan 3", "fan-4": "Fan 4", "fan-5": "Fan 5",
    "ac-1": "AC 1", "ac-2": "AC 2",
    "humidifier-1": "Humidifier 1", "humidifier-2": "Humidifier 2", "humidifier-3": "Humidifier 3",
    "light-1": "Light 1", "light-2": "Light 2", "light-3": "Light 3", "light-4": "Light 4", "light-5": "Light 5",
    "water-pump": "Water Pump"
}

device_states = {k: "UNKNOWN" for k in DEVICE_TOPICS}


class SensorWidget(QVBoxLayout):
    def __init__(self, name, topic):
        super().__init__()
        self.topic = topic
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("color: black; font-size: 10pt;")
        self.name_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("color: blue; font-size: 11pt; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setFixedSize(60, 60)
        self.image_label.setScaledContents(True)
        path = os.path.join(SENSOR_IMG_PATH, f"{topic}.png")
        self.image_label.setPixmap(QPixmap(path))

        self.setAlignment(Qt.AlignCenter)
        self.addWidget(self.image_label)
        self.addWidget(self.name_label)
        self.addWidget(self.value_label)

    def update_value(self, value):
        self.value_label.setText(str(value))


class WaterLevelWidget(QVBoxLayout):
    def __init__(self, topic):
        super().__init__()
        self.topic = topic
        self.name_label = QLabel("Water Level")
        self.name_label.setStyleSheet("color: black; font-size: 10pt;")
        self.name_label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setFixedSize(80, 60)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #aaa;
                background: #eee;
            }
            QProgressBar::chunk {
                background-color: #1ca9c9;
            }
        """)

        self.percent = QLabel("0%")
        self.percent.setAlignment(Qt.AlignCenter)
        self.percent.setStyleSheet("color: blue; font-size: 11pt; font-weight: bold;")

        self.setAlignment(Qt.AlignCenter)
        self.addWidget(self.progress)
        self.addWidget(self.name_label)
        self.addWidget(self.percent)

    def update_value(self, value):
        self.progress.setValue(int(value))
        self.percent.setText(f"{int(value)}%")


class DeviceWidget(QVBoxLayout):
    def __init__(self, name, topic):
        super().__init__()
        self.topic = topic
        self.name = name

        self.label = QLabel(f"{name}: UNKNOWN")
        self.label.setFont(QFont("Arial", 10))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: black;")

        self.image_label = QLabel()
        self.image_label.setFixedSize(60, 60)
        self.image_label.setScaledContents(True)

        self.setAlignment(Qt.AlignCenter)
        self.addWidget(self.image_label)
        self.addWidget(self.label)
        self.update_image("UNKNOWN")

    def update_image(self, state):
        if state == "ON":
            path = os.path.join(DEVICE_IMG_PATH, f"{self.topic}-on.gif")
            movie = QMovie(path)
            movie.setScaledSize(self.image_label.size())
            self.image_label.setMovie(movie)
            movie.start()
            self.label.setStyleSheet("color: green;")
        else:
            path = os.path.join(DEVICE_IMG_PATH, f"{self.topic}-off.png")
            pixmap = QPixmap(path).scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.label.setStyleSheet("color: red;")
        self.label.setText(f"{self.name}: {state}")


class GreenhouseDashboard(QWidget):
    def __init__(self, fluvio):
        super().__init__()
        self.setWindowTitle("🌿 Greenhouse Simulator")
        self.setFixedSize(1280, 1000)
        self.setStyleSheet("background-color: white;")

        self.fluvio = fluvio
        self.producers = {t: self.fluvio.topic_producer(t) for t in SENSOR_TOPICS}

        self.sensor_widgets = {}
        self.device_widgets = {}

        self.debug_label = QLabel("🛠️ Debug Log:")
        self.debug_label.setStyleSheet("color: #444; font-size: 10pt;")
        self.footer_label = QLabel("Designed by: Aanand Pandit, aanandpandit0001@gmail.com")
        self.footer_label.setAlignment(Qt.AlignCenter)
        self.footer_label.setStyleSheet("font-size: 9pt; color: gray; padding-top: 5px;")

        layout = QVBoxLayout()
        layout.addLayout(self.create_status_header())
        layout.addLayout(self.add_row(["dht-temp", "dht-humid", "co2"], is_sensor=True))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["soil-moisture-1", "soil-moisture-2"], is_sensor=True))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["water-pump", "water-level-sensor"], is_sensor_mixed=True))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["fan-1", "fan-2", "fan-3", "fan-4", "fan-5"]))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["humidifier-1", "humidifier-2", "humidifier-3"]))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["light-1", "light-2", "light-3", "light-4", "light-5"]))
        layout.addWidget(self.line())
        layout.addLayout(self.add_row(["ac-1", "ac-2"]))
        layout.addWidget(self.line())
        layout.addWidget(self.debug_label)
        layout.addWidget(self.footer_label)
        self.setLayout(layout)

        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)

        self.clock = QTimer()
        self.clock.timeout.connect(self.update_time)
        self.clock.start(1000)

        self.set_connection_status()

    def create_status_header(self):
        self.connection_label = QLabel("🔌 Fluvio: Connecting...")
        self.profile_label = QLabel("👤 Profile: ---")
        self.time_label = QLabel("🕒 Time: ---")
        for lbl in (self.connection_label, self.profile_label, self.time_label):
            lbl.setStyleSheet("color: black; font-size: 11pt; padding: 4px;")
        header = QHBoxLayout()
        header.addWidget(self.connection_label)
        header.addWidget(self.profile_label)
        header.addWidget(self.time_label)
        return header

    def line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def add_row(self, topics, is_sensor=False, is_sensor_mixed=False):
        row = QHBoxLayout()
        for topic in topics:
            container = QFrame()
            if is_sensor or topic in SENSOR_TOPICS:
                if topic == "water-level-sensor":
                    widget = WaterLevelWidget(topic)
                else:
                    widget = SensorWidget(topic, topic)
                self.sensor_widgets[topic] = widget
            else:
                widget = DeviceWidget(DEVICE_TOPICS[topic], topic)
                self.device_widgets[topic] = widget
            container.setLayout(widget)
            row.addWidget(container)
        return row

    def update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"🕒 Time: {now}")

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

    def refresh(self):
        debug_lines = []
        for topic, simulator in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            debug_lines.append(f"📤 Sent: {topic} = {value}")
            widget = self.sensor_widgets.get(topic)
            if widget:
                widget.update_value(value)

        for topic, widget in self.device_widgets.items():
            widget.update_image(device_states[topic])
            debug_lines.append(f"📥 Received: {topic} = {device_states[topic]}")

        self.debug_label.setText("🛠️ Debug Log:\n" + "\n".join(debug_lines[-5:]))

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
        print("⚠️ Missing topics detected. Please create them first.")
        return

    app = QApplication(sys.argv)
    window = GreenhouseDashboard(fluvio)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
