import requests
import csv
import os
import yaml
from datetime import datetime, timedelta
from collections import defaultdict

# === LOAD TOKEN FROM secrets.yaml ===
SECRETS_FILE = "/config/secrets.yaml"

with open(SECRETS_FILE, "r") as f:
    secrets = yaml.safe_load(f)

TOKEN = secrets["ha_api_token"]

# === CONFIGURATION ===
HASS_URL = "http://homeassistant.local:8123"  # Or your HA IP
SENSORS = [
    "sensor.ambient_temperature",
    "sensor.ambient_humidity",
    "sensor.localised_temperature",
    "sensor.localised_humidity",
    "sensor.scale_weight",
    "sensor.power_meter_power"
]
# Save to /config/www so it is accessible via the browser at /local/
OUTPUT_DIR = "/config/www/Exports"

# === SCRIPT LOGIC ===
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Calculate last 24 hours
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)

# Query Home Assistant History API
url = f"{HASS_URL}/api/history/period/{start_time.isoformat()}?end_time={end_time.isoformat()}&filter_entity_id={','.join(SENSORS)}"
response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()

# Merge by timestamp
merged_data = defaultdict(dict)
for sensor_entries in data:
    for entry in sensor_entries:
        ts = entry["last_changed"].split(".")[0].replace("T", " ")
        merged_data[ts][entry["entity_id"]] = entry["state"]

timestamps = sorted(merged_data.keys())

# CSV filename includes timestamp of export
csv_filename = f"{OUTPUT_DIR}/sensors_last12h_{end_time.strftime('%Y%m%d_%H%M%S')}.csv"

with open(csv_filename, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["datetime"] + SENSORS)
    for ts in timestamps:
        row = [ts] + [merged_data[ts].get(sensor, "") for sensor in SENSORS]
        writer.writerow(row)

print(f"✅ CSV created: {csv_filename}")
print(f"📂 File location: {csv_filename}")
print(f"🌍 Access via Web: {HASS_URL}/local/Exports/{os.path.basename(csv_filename)}")
