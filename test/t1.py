import random
import time
import subprocess
import os
from threading import Thread
from fluvio import Fluvio

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
check_required_topics()

def show_profile_info():
    print("🌍 Checking Fluvio profile info...\n")
    current_profile = os.popen("fluvio profile current").read().strip()
    print(f"🟢 Current Profile: {current_profile}")
    profiles = os.popen("fluvio profile list").read()
    print("📄 Available Profiles:\n" + profiles)
# show_profile_info()
