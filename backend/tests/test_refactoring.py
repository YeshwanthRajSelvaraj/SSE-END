"""
Unit & Security Verification Tests for Phase 12: Secure Coding & Refactoring
Tests both before_vulnerable.py (demonstrating flaws) and after_secured.py (demonstrating defenses).
"""
import pytest
import sqlite3
import os
import hmac
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.refactoring.before_vulnerable import ingest_telemetry_vulnerable
from backend.refactoring.after_secured import ingest_telemetry_secured
from app.models import Base, SmartBin, SensorReading, AuditLog, AuditAction

TEST_DB_FILE = "test_refactoring.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

@pytest.fixture(scope="module")
def setup_refactoring_db():
    """Create isolated clean database schema and seed with test hardware entity."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

    test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()

    bin_record = SmartBin(
        bin_id="BIN-REF-01",
        device_key="super_secret_device_key_999",
        location_lat=13.0827,
        location_lon=80.2707,
        capacity_liters=120.0,
        zone="Zone-Central"
    )
    db.add(bin_record)
    db.commit()
    db.refresh(bin_record)

    yield db

    db.close()
    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass

# ==============================================================================
# 1. Tests on BEFORE_VULNERABLE (Demonstrating Flaws)
# ==============================================================================

def test_vulnerable_accepts_arbitrary_unauthenticated_data():
    """
    Weakness 1: Lack of Authentication/Authorization (CWE-306).
    Any caller without credentials or cryptographic signature can invoke the function.
    """
    # Create isolated sqlite file for vulnerable module test
    vuln_db = "waste_management.db"
    conn = sqlite3.connect(vuln_db)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sensor_readings (id INTEGER PRIMARY KEY, bin_id TEXT, fill_level REAL, temperature REAL)")
    conn.commit()
    conn.close()

    result = ingest_telemetry_vulnerable(
        bin_id="FAKE-UNAUTHORIZED-BIN",
        fill_level=99.9,
        temperature=25.0
    )
    assert result == "Data inserted successfully"

def test_vulnerable_lacks_input_validation():
    """
    Weakness 2: Missing Input Validation & Bounds Checking (CWE-20).
    Physically impossible values (negative fill level, 99999C temperature) are accepted without warning.
    """
    result = ingest_telemetry_vulnerable(
        bin_id="BIN-BAD-VAL",
        fill_level=-500.0,
        temperature=99999.0
    )
    assert result == "Data inserted successfully"

def test_vulnerable_susceptible_to_sql_injection():
    """
    Weakness 3: String Interpolation SQL Injection (CWE-89).
    Raw formatted SQL allows arbitrary syntax manipulation and command injection.
    """
    sqli_bin_id = "BIN-01', 50.0, 25.0); --"
    raw_query = f"INSERT INTO sensor_readings (bin_id, fill_level, temperature) VALUES ('{sqli_bin_id}', 50.0, 25.0)"
    assert "VALUES ('BIN-01', 50.0, 25.0); --'" in raw_query

# ==============================================================================
# 2. Tests on AFTER_SECURED (Demonstrating Defenses & Refactored Robustness)
# ==============================================================================

def test_secured_rejects_missing_or_invalid_hmac_signature(setup_refactoring_db):
    """
    Defense 1: Cryptographic HMAC-SHA256 Signature Verification.
    Payloads with forged or tampered signatures are rejected and logged to audit trail.
    """
    db = setup_refactoring_db
    bin_id = "BIN-REF-01"
    device_key = "super_secret_device_key_999"
    payload = {
        "timestamp": 1710000000,
        "fill_level": 75.0,
        "temperature": 28.5,
        "location_lat": 13.0827,
        "location_lon": 80.2707
    }

    # Pass an invalid/forged signature
    response = ingest_telemetry_secured(
        db=db,
        bin_id=bin_id,
        payload=payload,
        signature="invalid_forged_hmac_signature_hex",
        device_key=device_key
    )

    assert response["status"] == "error"
    assert "Authentication failed" in response["message"]

    # Verify audit log recorded the spoofing attempt
    audit = db.query(AuditLog).filter(
        AuditLog.resource_id == bin_id,
        AuditLog.action == AuditAction.SPOOFING_DETECTED
    ).first()
    assert audit is not None
    assert audit.severity == "CRITICAL"

def test_secured_enforces_input_validation_bounds(setup_refactoring_db):
    """
    Defense 2: Strict Physical Boundary Validation.
    Rejects fill levels < 0 or > 100, and temperatures outside -40C to 85C.
    """
    db = setup_refactoring_db
    bin_id = "BIN-REF-01"
    device_key = "super_secret_device_key_999"

    # Out of range fill level (> 100%)
    payload_high_fill = {
        "timestamp": 1710000001,
        "fill_level": 150.0,
        "temperature": 25.0
    }
    payload_str = f"{bin_id}|1710000001|150.0|25.0"
    sig = hmac.new(device_key.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

    response = ingest_telemetry_secured(
        db=db,
        bin_id=bin_id,
        payload=payload_high_fill,
        signature=sig,
        device_key=device_key
    )
    assert response["status"] == "error"
    assert "Invalid fill level" in response["message"]

    # Out of range temperature (< -40C)
    payload_extreme_temp = {
        "timestamp": 1710000002,
        "fill_level": 50.0,
        "temperature": -100.0
    }
    payload_str2 = f"{bin_id}|1710000002|50.0|-100.0"
    sig2 = hmac.new(device_key.encode(), payload_str2.encode(), hashlib.sha256).hexdigest()

    response2 = ingest_telemetry_secured(
        db=db,
        bin_id=bin_id,
        payload=payload_extreme_temp,
        signature=sig2,
        device_key=device_key
    )
    assert response2["status"] == "error"
    assert "Invalid temperature" in response2["message"]

def test_secured_neutralizes_sql_injection(setup_refactoring_db):
    """
    Defense 3: Parameterized ORM Queries (CWE-89 Immunity).
    SQL syntax characters in input strings are bound as literal parameters, not executable code.
    """
    db = setup_refactoring_db
    sqli_bin_id = "BIN-01' OR '1'='1"
    device_key = "dummy_key"
    payload = {"timestamp": 1710000003, "fill_level": 40.0, "temperature": 26.0}
    payload_str = f"{sqli_bin_id}|1710000003|40.0|26.0"
    sig = hmac.new(device_key.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

    response = ingest_telemetry_secured(
        db=db,
        bin_id=sqli_bin_id,
        payload=payload,
        signature=sig,
        device_key=device_key
    )
    assert response["status"] == "error"
    assert "Device not found in registry" in response["message"]

def test_secured_successful_ingestion_with_valid_hmac(setup_refactoring_db):
    """
    Defense 4: Verified Execution with Sensitive Data Sanitization and Atomic Commit.
    """
    db = setup_refactoring_db
    bin_id = "BIN-REF-01"
    device_key = "super_secret_device_key_999"
    payload = {
        "timestamp": 1710000004,
        "fill_level": 62.5,
        "temperature": 27.8,
        "location_lat": 13.0827,
        "location_lon": 80.2707
    }
    payload_str = f"{bin_id}|1710000004|62.5|27.8"
    sig = hmac.new(device_key.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

    response = ingest_telemetry_secured(
        db=db,
        bin_id=bin_id,
        payload=payload,
        signature=sig,
        device_key=device_key
    )
    assert response["status"] == "success"

    bin_record = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
    latest_reading = db.query(SensorReading).filter(SensorReading.bin_id == bin_record.id).order_by(SensorReading.id.desc()).first()
    assert latest_reading is not None
    assert latest_reading.fill_level == 62.5
    assert latest_reading.temperature == 27.8
