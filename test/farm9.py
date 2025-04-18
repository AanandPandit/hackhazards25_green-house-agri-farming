import sys
import random
import time
import subprocess
import os
from threading import Thread
from datetime import datetime
from fluvio import Fluvio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QMovie

ASSETS_DEVICES = "pyqt5/assets/devices"
ASSETS_SENSORS = "pyqt5/assets/sensors"

SENSOR_TOPICS = {
    "dht-temp": ("Temperature", lambda: round(random.uniform(18, 30), 2), "dht-temp.png"),
    "dht-humid": ("Humidity", lambda: round(random.uniform(50, 90), 2), "dht-humid.png"),
    "co2": ("CO2", lambda: round(random.uniform(300, 800), 2), "co2.png"),
    "rain-sensor": ("Rain Sensor", lambda: round(random.uniform(0, 100), 2), "rain-sensor.png"),
    "soil-moisture-1": ("Soil Moisture 1", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png"),
    "soil-moisture-2": ("Soil Moisture 2", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png"),
    "water-level-sensor": ("Water Tank", lambda: round(random.uniform(0, 100), 2), None),
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
        self.setFixedSize(1000, 750)
        self.setStyleSheet("background-color: white;")

        self.sensor_labels = {}
        self.device_labels = {}
        self.water_bar = None
        self.water_value_label = QLabel()
        self.time_label = QLabel()

        self.layout = QVBoxLayout()
        self.layout.setSpacing(6)
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

        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensors)
        self.sensor_timer.start(5000)

        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

    def setup_header(self):
        header = QHBoxLayout()
        title = QLabel("<h1>🌱 Virtual Greenhouse</h1>")
        title.setStyleSheet("margin-right: 50px; color: #333")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        profile = os.popen("fluvio profile current").read().strip()
        profile_info = QLabel(f"🟢 Connected to Fluvio   ||   Profile: {profile}    ")
        profile_info.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(profile_info)
        header.addWidget(self.time_label)
        self.layout.addLayout(header)

    def update_time(self):
        self.time_label.setText(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def setup_sensors(self):
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        row, col = 0, 0

        for topic, (name, _, icon) in SENSOR_TOPICS.items():
            if topic == "water-level-sensor":
                continue

            sensor_box = QHBoxLayout()
            if icon:
                pixmap = QPixmap(f"{ASSETS_SENSORS}/{icon}").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                sensor_box.addWidget(icon_label, alignment=Qt.AlignRight)

            label = QLabel(f"    {name}: 0")
            label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
            label.setAlignment(Qt.AlignLeft)
            sensor_box.addWidget(label)
            self.sensor_labels[topic] = label

            grid.addLayout(sensor_box, row, col)
            col += 1
            if col > 1:
                row += 1
                col = 0

        # Water Tank with vertical black progress bar and raw value
        vbox = QVBoxLayout()
        water_label = QLabel("Water Tank")
        water_label.setAlignment(Qt.AlignCenter)
        water_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333")

        self.water_bar = QProgressBar()
        self.water_bar.setOrientation(Qt.Vertical)
        self.water_bar.setFixedSize(30, 90)
        self.water_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #1ca9c9; }"
            "QProgressBar { border: 1px solid gray; background-color: white; }"
        )
        self.water_value_label.setAlignment(Qt.AlignCenter)
        self.water_value_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")

        vbox.addWidget(water_label)
        vbox.addWidget(self.water_bar, alignment=Qt.AlignCenter)
        vbox.addWidget(self.water_value_label)

        grid.addLayout(vbox, 0, 2, 3, 1)
        self.layout.addLayout(grid)

    def setup_devices(self):
        rows = [[], [], [], [], []]  # fans, lights, ac+humidifiers, water pump
        for topic, (name, dtype) in DEVICE_TOPICS.items():
            container = QVBoxLayout()
            container.setAlignment(Qt.AlignHCenter)

            label = QLabel()
            label.setFixedSize(50, 50)
            label.setAlignment(Qt.AlignCenter)
            gif_file = f"{ASSETS_DEVICES}/{dtype}-on.gif"
            static_file = f"{ASSETS_DEVICES}/{dtype}-off.png"
            label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("font-size: 11px;")

            status_label = QLabel("UNKNOWN")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("color: gray; font-weight: bold; font-size: 10px;")

            container.addWidget(label)
            container.addWidget(name_label)
            container.addWidget(status_label)

            self.device_labels[topic] = (label, gif_file, static_file, status_label)

            if "fan" in topic:
                rows[0].append(container)
            elif "light" in topic:
                rows[1].append(container)
            elif "ac" in topic or "humidifier" in topic:
                rows[2].append(container)
            elif "water-pump" in topic:
                rows[4].append(container)

        for row in rows:
            hbox = QHBoxLayout()
            hbox.setSpacing(1)
            for widget in row:
                hbox.addLayout(widget)
            self.layout.addLayout(hbox)

    def setup_terminal_output(self):
        self.terminal = QTextEdit()
        self.terminal.setFixedHeight(140)
        self.terminal.setStyleSheet("""
            background-color: #f0f0f0;
            font-family: monospace;
            font-size: 10pt;
            color: black;
        """)

        self.terminal.setReadOnly(True)
        label = QLabel("🖥️ Terminal Output:")
        label.setStyleSheet("""
            color: #333333;
            font-size: 12pt;
            font-weight: bold;
            font-family: Arial;
        """)
        self.layout.addWidget(label)
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

            # Update dashboard
            if topic == "water-level-sensor":
                self.water_bar.setValue(int(value))
                self.water_value_label.setText(str(value))
            else:
                self.sensor_labels[topic].setText(f"{name}: {value}")

            # Log sensor update
            self.log_terminal(f"📤 Sent:: {name}              --> {value}                   --> {topic}")

        for topic, (label, gif_file, static_file, status_label) in self.device_labels.items():
            state = device_states[topic]
            if state == "ON":
                movie = QMovie(gif_file)
                movie.setScaledSize(label.size())
                label.setMovie(movie)
                movie.start()
                status_label.setText("ON")
                status_label.setStyleSheet("color: green; font-weight: bold;")
            elif state == "OFF":
                label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio))
                status_label.setText("OFF")
                status_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio))
                status_label.setText("UNKNOWN")
                status_label.setStyleSheet("color: gray; font-weight: bold;")

    def listen_control(self, topic):
        def consume():
            process = subprocess.Popen(
                ["fluvio", "consume", topic, "-T20"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.log_terminal(f"📡 Listening for commands on topic '{topic}'...")
            while True:
                line = process.stdout.readline()
                if line:
                    command = line.strip().lower()
                    if command in ["on", "off"]:
                        device_states[topic] = command.upper()
                        self.log_terminal(f"✅ {DEVICE_TOPICS[topic][0]} set to {command.upper()}")
                    else:
                        self.log_terminal(f"Unknown command '{command}' on topic {topic}")
                else:
                    time.sleep(1)
        Thread(target=consume, daemon=True).start()

    def log_terminal(self, msg):
        self.terminal.append(msg)
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())


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
