import random
import time
import subprocess
import os
from fluvio import Fluvio

TEMP_TOPIC = "dht-temp"
HUMID_TOPIC = "dht-humid"

def simulate_temperature():
    # Simulated cabbage-friendly temp (18-25°C)
    return round(random.uniform(18, 25), 2)

def simulate_humidity():
    # Simulated humidity (60-80%)
    return round(random.uniform(60, 80), 2)

def check_required_topics(required=["dht-temp", "dht-humid"]):
    try:
        result = subprocess.run(["fluvio", "topic", "list"], capture_output=True, text=True)
        output = result.stdout
        print("\n📋 Fluvio Topics:")
        print(output)

        existing_topics = []
        for line in output.splitlines()[1:]:  # Skip header
            parts = line.strip().split()
            if parts:
                existing_topics.append(parts[0])

        missing = [t for t in required if t not in existing_topics]
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

        show_profile_info()

        if not check_required_topics():
            print("ℹ️ Please run:\n  fluvio topic create dht-temp\n  fluvio topic create dht-humid")
            return

        print("\n🚀 Starting greenhouse simulation for cabbage...\n")
        temp_producer = fluvio.topic_producer(TEMP_TOPIC)
        humid_producer = fluvio.topic_producer(HUMID_TOPIC)

        while True:
            temp = simulate_temperature()
            humid = simulate_humidity()

            temp_producer.send_string(str(temp))
            humid_producer.send_string(str(humid))

            print(f"📤 Sent | Temperature: {temp}°C | Humidity: {humid}%")
            time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
