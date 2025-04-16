import random
import time
import subprocess
import os
from threading import Thread
from fluvio import Fluvio

# All control topics mapped to their emoji/label
DEVICE_TOPICS = {
    "led-red": "🔴",
    "led-green": "🟢",
    "led-blue": "🔵",
    "led-yellow": "🟡",
    "led-white": "⚪",
    "fan-1": "🌬️ Fan 1",
    "fan-2": "🌬️ Fan 2",
    "fan-3": "🌬️ Fan 3",
    "fan-4": "🌬️ Fan 4",
    "fan-5": "🌬️ Fan 5",
    "ac-1": "❄️ AC 1",
    "ac-2": "❄️ AC 2",
    "water-pump": "🚿 Water Pump"
}

TEMP_TOPIC = "dht-temp"
HUMID_TOPIC = "dht-humid"

# ✅ Updated name to reflect all device states
device_states = {k: "UNKNOWN" for k in DEVICE_TOPICS}

def simulate_temperature():
    return round(random.uniform(18, 25), 2)

def simulate_humidity():
    return round(random.uniform(60, 80), 2)

def check_required_topics():
    required = [TEMP_TOPIC, HUMID_TOPIC] + list(DEVICE_TOPICS.keys())
    try:
        result = subprocess.run(["fluvio", "topic", "list"], capture_output=True, text=True)
        output = result.stdout
        print("\n📋 Fluvio Topics:")
        print(output)
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

# ✅ Updated: Device state updated when commands are received
def listen_control(topic):
    def consume():
        process = subprocess.Popen(
            ["fluvio", "consume", topic, "-B"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print(f"📡 Listening for commands on topic '{topic}'...")
        while True:
            line = process.stdout.readline()
            if line:
                command = line.strip().lower()
                if command in ["on", "off"]:
                    device_states[topic] = command.upper()
                    print(f"{DEVICE_TOPICS[topic]} → {command.upper()}")
                else:
                    print(f"⚠️ Unknown command '{command}' on topic {topic}")
            else:
                time.sleep(1)
    Thread(target=consume, daemon=True).start()

def main():
    print("🔌 Connecting to Fluvio...")
    try:
        fluvio = Fluvio.connect()
        print("✅ Connected to Fluvio Cloud")

        show_profile_info()

        if not check_required_topics():
            print("⚠️ Please create the missing topics using `fluvio topic create ...`.")
            return

        temp_producer = fluvio.topic_producer(TEMP_TOPIC)
        humid_producer = fluvio.topic_producer(HUMID_TOPIC)

        # ✅ Start control listeners for all device topics
        for topic in DEVICE_TOPICS:
            listen_control(topic)

        print("🚀 Greenhouse simulation started...\n")

        while True:
            temp = simulate_temperature()
            humid = simulate_humidity()
            temp_producer.send_string(str(temp))
            humid_producer.send_string(str(humid))

            device_status = " | ".join([f"{DEVICE_TOPICS[k]}: {v}" for k, v in device_states.items()])
            print(f"📤 Temp: {temp}°C | Humid: {humid}% | Devices: {device_status}")
            time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
