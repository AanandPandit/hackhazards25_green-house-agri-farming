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
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QMovie

ASSETS_DEVICES = "greenhouse/assets/devices"
ASSETS_SENSORS = "greenhouse/assets/sensors"

SENSOR_TOPICS = {
    "dht-temp": ("    Temperature", lambda: round(random.uniform(18, 30), 2), "dht-temp.png", "°C"),
    "dht-humid": ("    Humidity", lambda: round(random.uniform(50, 90), 2), "dht-humid.png", "%"),
    "co2": ("    CO2", lambda: round(random.uniform(300, 800), 2), "co2.png", "ppm"),
    "rain-sensor": ("    Rain Sensor", lambda: round(random.uniform(0, 100), 2), "rain-sensor.png", "%"),
    "soil-moisture-1": ("    Soil Moisture 1", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png", "%"),
    "soil-moisture-2": ("    Soil Moisture 2", lambda: round(random.uniform(10, 70), 2), "soil-moisture.png", "%"),
    "water-level-sensor": ("    Water Tank", lambda: round(random.uniform(0, 100), 2), None, "%"),
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


class FluvioConnector(QObject):
    connected = pyqtSignal(object, object)
    status_update = pyqtSignal(str)
    profile_update = pyqtSignal(str)

    def run(self):
        self.status_update.emit("🟡 Connecting to Fluvio...")
        try:
            profile = os.popen("fluvio profile current").read().strip()
            self.profile_update.emit(profile)
            fluvio = Fluvio.connect()
            producers = {topic: fluvio.topic_producer(topic) for topic in SENSOR_TOPICS}
            self.status_update.emit("🟢 Connected to Fluvio")
            self.connected.emit(fluvio, producers)
        except Exception as e:
            self.status_update.emit(f"🔴 Connection Failed: {e}")


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
        self.connection_status = QLabel("🔴 Not Connected")
        self.profile_label = QLabel("")
        self.connected = False
        self.active_consumers = []

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

        self.fluvio = None
        self.producers = {}

        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensors)

        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

        self.connect_to_fluvio()

        Thread(target=self.monitor_internet, daemon=True).start()

    def setup_header(self):
        header = QHBoxLayout()
        title = QLabel("<h1>🌱 Virtual Greenhouse</h1>")
        title.setStyleSheet("margin-right: 50px; color: #333")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.connection_status.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
        self.profile_label.setStyleSheet("font-size: 13px; color: #222;")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.connection_status)
        header.addSpacing(20)
        header.addWidget(self.profile_label)
        header.addSpacing(20)
        header.addWidget(self.time_label)
        self.layout.addLayout(header)

    def connect_to_fluvio(self):
        self.fluvio_connector = FluvioConnector()
        self.fluvio_connector.connected.connect(self.set_fluvio)
        self.fluvio_connector.status_update.connect(self.update_connection_status)
        self.fluvio_connector.profile_update.connect(self.update_profile_label)
        Thread(target=self.fluvio_connector.run, daemon=True).start()

    def monitor_internet(self):
        while True:
            response = os.system("ping -c 1 google.com > /dev/null 2>&1")
            if response == 0 and not self.connected:
                self.log_terminal("🌐 Internet restored. Reconnecting to Fluvio...")
                self.connect_to_fluvio()
            elif response != 0 and self.connected:
                self.connected = False
                self.sensor_timer.stop()
                self.log_terminal("🛑 Attempting to reconnect...")
                self.update_connection_status("🔴 Connection lost. Attempting to reconnect...")
            time.sleep(5)

    def update_connection_status(self, status):
        self.connection_status.setText(status)
        self.connected = status.startswith("🟢")

    def update_profile_label(self, profile):
        self.profile_label.setText(f"Profile: {profile}")

    def set_fluvio(self, fluvio, producers):
        self.fluvio = fluvio
        self.producers = producers
        self.connected = True
        self.sensor_timer.start(5000)
        self.log_terminal("✅ Fluvio connection established. Starting simulation...")

        for topic in DEVICE_TOPICS:
            self.listen_control(topic)

    def update_time(self):
        self.time_label.setText(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def setup_sensors(self):
        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        row, col = 0, 0
        for topic, (name, _, icon, _) in SENSOR_TOPICS.items():
            if topic == "water-level-sensor":
                continue
            sensor_box = QHBoxLayout()
            if icon:
                pixmap = QPixmap(f"{ASSETS_SENSORS}/{icon}").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                sensor_box.addWidget(icon_label, alignment=Qt.AlignRight)
            label = QLabel(f"    {name}: 0")
            label.setStyleSheet("font-size: 13px; color: #333; font-weight: bold;")
            sensor_box.addWidget(label)
            self.sensor_labels[topic] = label
            grid.addLayout(sensor_box, row, col)
            col += 1
            if col > 1:
                row += 1
                col = 0

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
        rows = [[], [], [], [], []]
        for topic, (name, dtype) in DEVICE_TOPICS.items():
            container = QVBoxLayout()
            container.setAlignment(Qt.AlignHCenter)

            icon_label = QLabel()
            icon_label.setFixedSize(50, 50)
            icon_label.setAlignment(Qt.AlignCenter)
            gif_file = f"{ASSETS_DEVICES}/{dtype}-on.gif"
            static_file = f"{ASSETS_DEVICES}/{dtype}-off.png"
            icon_label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio))

            status_label = QLabel(f"{name}: UNKNOWN")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("color: gray; font-weight: bold; font-size: 10px;")

            container.addWidget(icon_label)
            container.addWidget(status_label)

            self.device_labels[topic] = (icon_label, gif_file, static_file, status_label)

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
            hbox.setSpacing(5)
            for widget in row:
                hbox.addLayout(widget)
            self.layout.addLayout(hbox)

    def setup_terminal_output(self):
        self.terminal = QTextEdit()
        self.terminal.setFixedHeight(150)
        self.terminal.setStyleSheet("""
            background-color: #f0f0f0;
            font-family: monospace;
            font-size: 10pt;
            color: black;
        """)
        self.terminal.setReadOnly(True)
        label = QLabel("🖥️ Terminal Output:")
        label.setStyleSheet("color: #333333; font-size: 12pt; font-weight: bold; font-family: Arial;")
        self.layout.addWidget(label)
        self.layout.addWidget(self.terminal)

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(line)

    def update_sensors(self):
        if not self.connected:
            return
        for topic, (name, simulator, _, unit) in SENSOR_TOPICS.items():
            value = simulator()
            self.producers[topic].send_string(str(value))
            if topic == "water-level-sensor":
                self.water_bar.setValue(int(value))
                self.water_value_label.setText(f"{value} {unit}")
            else:
                self.sensor_labels[topic].setText(f"{name}: {value} {unit}")
            self.log_terminal(f"📤 Sent:: {name.strip()}          -->         {value} {unit}         -->         {topic}")

        for topic, (label, gif_file, static_file, status_label) in self.device_labels.items():
            state = device_states[topic]
            name = DEVICE_TOPICS[topic][0]
            if state == "ON":
                movie = QMovie(gif_file)
                movie.setScaledSize(label.size())
                label.setMovie(movie)
                movie.start()
                status_label.setText(f"{name}: ON")
                status_label.setStyleSheet("color: green; font-weight: bold;")
            elif state == "OFF":
                label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio))
                status_label.setText(f"{name}: OFF")
                status_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                label.setPixmap(QPixmap(static_file).scaled(50, 50, Qt.KeepAspectRatio))
                status_label.setText(f"{name}: UNKNOWN")
                status_label.setStyleSheet("color: gray; font-weight: bold;")

    def listen_control(self, topic):
        def consume():
            process = subprocess.Popen(["fluvio", "consume", topic, "-T1"], stdout=subprocess.PIPE, text=True)
            while self.connected:
                line = process.stdout.readline()
                if line:
                    command = line.strip().lower()
                    if command in ["on", "off"]:
                        device_states[topic] = command.upper()
                        self.log_terminal(f"✅ {DEVICE_TOPICS[topic][0]} set to {command.upper()}")
                    else:
                        self.log_terminal(f"❓ Unknown command '{command}' on topic {topic}")
        thread = Thread(target=consume, daemon=True)
        self.active_consumers.append(thread)
        thread.start()

    def log_terminal(self, msg):
        self.terminal.append(msg)
        self.terminal.verticalScrollBar().setValue(self.terminal.verticalScrollBar().maximum())


def main():
    app = QApplication(sys.argv)
    window = GreenhouseSimulator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
