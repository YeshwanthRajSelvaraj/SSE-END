"""
Integration Tests for Telemetry Ingestion and End-to-End flows.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import SmartBin, User, UserRole

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Setup test data
    test_bin = SmartBin(
        bin_id="TEST-BIN-01",
        device_key="test_key_123",
        location_lat=13.0,
        location_lon=80.0,
        capacity_liters=100.0,
        zone="Zone-A"
    )
    db.add(test_bin)
    db.commit()
    from app.rate_limiter import reset_rate_limits
    reset_rate_limits()
    yield

    Base.metadata.drop_all(bind=engine)

def test_telemetry_ingestion_valid():
    from app.rate_limiter import reset_rate_limits
    reset_rate_limits()
    import time, hmac, hashlib
    
    timestamp = int(time.time())
    payload_str = f"TEST-BIN-01|{timestamp}|45.0|28.0"
    sig = hmac.new(b"test_key_123", payload_str.encode(), hashlib.sha256).hexdigest()
    
    payload = {
        "bin_id": "TEST-BIN-01",
        "fill_level": 45.0,
        "location_lat": 13.0,
        "location_lon": 80.0,
        "temperature": 28.0,
        "sensor_status": "normal",
        "hmac_signature": sig
    }
    
    response = client.post("/api/iot/telemetry", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"

def test_telemetry_ingestion_invalid_signature():
    payload = {
        "bin_id": "TEST-BIN-01",
        "fill_level": 45.0,
        "location_lat": 13.0,
        "location_lon": 80.0,
        "temperature": 28.0,
        "sensor_status": "normal",
        "hmac_signature": "fake_signature"
    }
    
    response = client.post("/api/iot/telemetry", json=payload)
    assert response.status_code == 400
    assert "Invalid signature" in response.json()["detail"]
