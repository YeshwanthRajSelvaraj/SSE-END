"""
IoT Device Simulator
Generates valid, spoofed, and tampered telemetry for Smart Bins.
"""
import time
import hmac
import hashlib
import requests
import random
import json

API_URL = "http://127.0.0.1:8001/api/iot/telemetry"
DEVICE_KEY = "super_secret_device_key_for_bin_001"
BIN_ID = "BIN-001"

def generate_signature(payload_str: str, key: str) -> str:
    return hmac.new(
        key.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def send_valid_telemetry():
    """Send correct telemetry with valid signature."""
    timestamp = int(time.time())
    fill_level = random.uniform(20.0, 80.0)
    temp = random.uniform(25.0, 35.0)
    
    payload_str = f"{BIN_ID}|{timestamp}|{fill_level}|{temp}"
    signature = generate_signature(payload_str, DEVICE_KEY)
    
    data = {
        "bin_id": BIN_ID,
        "fill_level": fill_level,
        "location_lat": 13.0827,
        "location_lon": 80.2707,
        "temperature": temp,
        "sensor_status": "normal",
        "battery_level": 90.0,
        "hmac_signature": signature
    }
    
    resp = requests.post(API_URL, json=data)
    print(f"[Valid] Response: {resp.status_code} - {resp.text}")
    return resp

def send_spoofed_telemetry():
    """Send telemetry with fake/invalid signature."""
    timestamp = int(time.time())
    fill_level = 95.0
    temp = 45.0
    
    # Tampered signature
    signature = "invalid_fake_signature_hash_12345"
    
    data = {
        "bin_id": BIN_ID,
        "fill_level": fill_level,
        "location_lat": 13.0827,
        "location_lon": 80.2707,
        "temperature": temp,
        "sensor_status": "warning",
        "battery_level": 85.0,
        "hmac_signature": signature
    }
    
    resp = requests.post(API_URL, json=data)
    print(f"[Spoofed] Response: {resp.status_code} - {resp.text}")

def send_location_manipulation():
    """Send telemetry with impossible coordinates (Geofence violation)."""
    timestamp = int(time.time())
    fill_level = 50.0
    temp = 30.0
    
    payload_str = f"{BIN_ID}|{timestamp}|{fill_level}|{temp}"
    signature = generate_signature(payload_str, DEVICE_KEY)
    
    data = {
        "bin_id": BIN_ID,
        "fill_level": fill_level,
        "location_lat": 28.7041, # Delhi (Not Chennai) -> Geofence trigger
        "location_lon": 77.1025,
        "temperature": temp,
        "sensor_status": "normal",
        "battery_level": 90.0,
        "hmac_signature": signature
    }
    
    resp = requests.post(API_URL, json=data)
    print(f"[Loc Manipulation] Response: {resp.status_code} - {resp.text}")


if __name__ == "__main__":
    print("--- Starting IoT Simulator ---")
    send_valid_telemetry()
    time.sleep(1)
    send_spoofed_telemetry()
    time.sleep(1)
    send_location_manipulation()
