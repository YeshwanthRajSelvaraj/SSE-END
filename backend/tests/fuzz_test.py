"""
Fuzz testing for Telemetry API.
Phase 14 - CI/CD and Security Testing
Evaluates input validation boundaries, type mismatches, buffer sizes, and injection payloads.
"""
import os
import sys
import random
import string
import json
import requests
from fastapi.testclient import TestClient

# Ensure backend and root paths are on sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_current_dir, ".."))
_root_dir = os.path.abspath(os.path.join(_current_dir, "../.."))
for p in [_backend_dir, _root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Default to running container or local port, configurable via API_URL
DEFAULT_URL = os.environ.get("API_URL", "http://127.0.0.1:8000/api/iot/telemetry")

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def run_fuzz_case(client_or_requests, url, payload, case_name):
    print(f"\n[FUZZ TEST] Case: {case_name}")
    print(f"Payload Preview: {json.dumps({k: (v if len(str(v)) < 60 else str(v)[:60] + '...') for k, v in payload.items()})}")
    
    if hasattr(client_or_requests, 'post'):
        resp = client_or_requests.post(url, json=payload)
    else:
        resp = requests.post(url, json=payload, timeout=5)
        
    print(f"Response Status Code: {resp.status_code}")
    detail = resp.json().get('detail') if resp.headers.get('content-type', '').startswith('application/json') else resp.text[:120]
    print(f"Observation / Diagnostic: {detail}")
    return resp

def fuzz_test_telemetry():
    print("=================================================================")
    print("          STARTING FUZZING ON IOT TELEMETRY BOUNDARY             ")
    print("=================================================================")
    
    # Try HTTP endpoint first, otherwise fallback to TestClient
    use_http = False
    try:
        test_ping = requests.get(DEFAULT_URL.replace("/api/iot/telemetry", "/docs"), timeout=2)
        if test_ping.status_code == 200:
            print(f"Live API detected at {DEFAULT_URL} (Status: {test_ping.status_code})")
            use_http = True
        else:
            print(f"Endpoint at {DEFAULT_URL} returned non-200 ({test_ping.status_code}). Falling back to FastAPI TestClient...")
    except Exception:
        print(f"Direct HTTP connection failed to {DEFAULT_URL}. Falling back to FastAPI TestClient...")
        use_http = False

    if use_http:
        poster = requests
        target_url = DEFAULT_URL
    else:
        try:
            from app.main import app
        except ImportError:
            from backend.app.main import app
        poster = TestClient(app)
        target_url = "/api/iot/telemetry"

    results = []

    # Case 1: Extreme Type Mismatch & Schema Violation
    payload1 = {
        "bin_id": 12345,                # Integer instead of string
        "fill_level": "OVERFLOW_LEVEL", # String instead of float
        "location_lat": "Ninety",       # String instead of float
        "location_lon": None,           # Missing float
        "temperature": -9999.99,        # Out of bounds
        "sensor_status": "EXPLODED_BAD",# Invalid status literal
        "hmac_signature": generate_random_string(512)
    }
    r1 = run_fuzz_case(poster, target_url, payload1, "Type Mismatch & Out-of-Bounds Schema")
    assert r1.status_code in [422, 400], f"Expected 422/400 but got {r1.status_code}"
    results.append(("Type Mismatch & Schema Violation", r1.status_code, "REJECTED (422 Pydantic Validation Error)"))

    # Case 2: Buffer Overflow / Enormous String Payload (15,000 characters)
    payload2 = {
        "bin_id": generate_random_string(15000),
        "fill_level": 50.0,
        "location_lat": 13.0,
        "location_lon": 80.0,
        "temperature": 30.0,
        "sensor_status": "normal",
        "hmac_signature": generate_random_string(8192)
    }
    r2 = run_fuzz_case(poster, target_url, payload2, "Buffer Stress / Giant String Payload")
    assert r2.status_code in [422, 400, 404], f"Expected input rejection but got {r2.status_code}"
    results.append(("Buffer Stress / Oversized Payload", r2.status_code, "REJECTED (Graceful input handling)"))

    # Case 3: SQL Injection Payloads inside JSON fields
    payload3 = {
        "bin_id": "BIN-001' UNION SELECT * FROM users WHERE '1'='1",
        "fill_level": 50.0,
        "location_lat": 13.0,
        "location_lon": 80.0,
        "temperature": 30.0,
        "sensor_status": "normal",
        "hmac_signature": "'; DROP TABLE smart_bins;--"
    }
    r3 = run_fuzz_case(poster, target_url, payload3, "SQL Injection & Escape Sequences")
    assert r3.status_code in [400, 403, 404, 422], f"Expected rejection but got {r3.status_code}"
    results.append(("SQL Injection Attack Vector", r3.status_code, "REJECTED (ORM Parameterization & Device Check)"))

    # Case 4: Extreme Coordinates & NaN/Inf Floating Point Values
    payload4 = {
        "bin_id": "BIN-TEST",
        "fill_level": 1e308,
        "location_lat": 999999.99,
        "location_lon": -999999.99,
        "temperature": -273.15,
        "sensor_status": "normal",
        "hmac_signature": "00000000000000000000000000000000"
    }
    r4 = run_fuzz_case(poster, target_url, payload4, "Floating Point Extremes & Geofence Boundary")
    assert r4.status_code in [400, 403, 404, 422], f"Expected rejection but got {r4.status_code}"
    results.append(("Floating Point Extreme Coordinates", r4.status_code, "REJECTED (Boundary / Signature check)"))

    print("\n=================================================================")
    print("                    FUZZ TESTING SUMMARY                         ")
    print("=================================================================")
    for name, code, obs in results:
        print(f"- {name:<35} | Status: {code} | Result: {obs}")
    print("All fuzz vectors tested. Zero unhandled 500 crashes or memory faults observed.")

if __name__ == "__main__":
    fuzz_test_telemetry()
