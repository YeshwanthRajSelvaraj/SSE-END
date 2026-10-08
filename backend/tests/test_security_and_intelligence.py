"""
Comprehensive Automated Test Suite for SmartWaste Intelligence & Security Controls.
Covers all requirements from OWASP API Security, IoT Trust, GPS Spoofing,
Sensor Integrity, Waste AI Classification, Contamination, and Route Protection.
"""
import pytest
import json
import time
import hmac
import hashlib
import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import (
    SmartBin, User, UserRole, DeviceRegistryItem, DeviceStatus,
    SensorReading, CollectionRoute, RouteAssignment, Vehicle, Driver, RouteStatus,
    WasteClassificationRecord, ClassificationConfidenceStatus,
    BinContaminationRecord, BinCompositionRecord, SecurityEventRecord
)

from app.auth import hash_password, create_access_token
from app.waste_classifier import (
    run_waste_inference, evaluate_confidence_tier,
    calculate_waste_density_and_correlate, detect_bin_contamination,
    recalculate_bin_composition
)
from app.location_security import evaluate_location_telemetry, calculate_haversine_distance
from app.sensor_trust import evaluate_sensor_telemetry
from app.route_optimizer import (
    calculate_bin_priority_score, compute_route_integrity_hash,
    verify_route_integrity, modify_route_authorized
)
from app.security_engine import (
    detect_sql_injection, sanitize_for_xss,
    safe_canonical_path, validate_url_for_ssrf, check_object_authorization
)

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_environment():
    """Sets up a comprehensive test database with bins, users, and cryptographic anchors."""
    Base.metadata.create_all(bind=engine)
    from app.rate_limiter import reset_rate_limits
    reset_rate_limits()
    db: Session = SessionLocal()

    # Pre-clean test entities to prevent UNIQUE constraint collisions
    db.query(RouteAssignment).filter(RouteAssignment.status == RouteStatus.PENDING).delete()
    db.query(CollectionRoute).filter(CollectionRoute.route_name.like("%Security%")).delete()
    db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id.in_(["TEST-SEC-BIN-01", "TEST-DEVICE-QUARANTINED", "TEST-DEVICE-REVOKED"])).delete()
    db.query(SmartBin).filter(SmartBin.bin_id.in_(["TEST-SEC-BIN-01", "TEST-SEC-BIN-RECYCLE"])).delete()
    db.query(User).filter(User.username.in_(["admin_sec_test", "operator_sec_test", "driver1_sec_test", "driver2_sec_test"])).delete()
    db.query(Driver).filter(Driver.driver_id.in_(["DRV-SEC-01", "DRV-SEC-02"])).delete()
    db.query(Vehicle).filter(Vehicle.vehicle_id == "TRUCK-SEC-01").delete()
    db.commit()



    # 1. Test Bins
    bin1 = SmartBin(
        bin_id="TEST-SEC-BIN-01",
        device_key="device_key_sec_01",
        location_lat=13.0827,
        location_lon=80.2707,
        capacity_liters=120.0,
        zone="Zone A",
        status="active"
    )
    bin_recycle = SmartBin(
        bin_id="TEST-SEC-BIN-RECYCLE",
        device_key="device_key_recycle",
        location_lat=13.0900,
        location_lon=80.2800,
        capacity_liters=120.0,
        zone="Zone Recycle",
        status="active"
    )
    db.add(bin1)
    db.add(bin_recycle)

    # 2. Test Users with strict RBAC roles
    admin_user = User(
        username="admin_sec_test",
        email="admin_sec@example.com",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True
    )
    operator_user = User(
        username="operator_sec_test",
        email="operator_sec@example.com",
        hashed_password=hash_password("OperatorPass123!"),
        role=UserRole.OPERATOR,
        is_active=True
    )
    driver1 = User(
        username="driver1_sec_test",
        email="driver1_sec@example.com",
        hashed_password=hash_password("DriverPass123!"),
        role=UserRole.DRIVER,
        is_active=True
    )
    driver2 = User(
        username="driver2_sec_test",
        email="driver2_sec@example.com",
        hashed_password=hash_password("DriverPass123!"),
        role=UserRole.DRIVER,
        is_active=True
    )
    db.add_all([admin_user, operator_user, driver1, driver2])
    db.commit()


    # 3. Test Devices in Registry
    dev1 = DeviceRegistryItem(
        device_id="TEST-SEC-BIN-01",
        bin_id="TEST-SEC-BIN-01",
        cert_fingerprint="sha256_cert_fingerprint_01",
        status=DeviceStatus.ACTIVE,
        assigned_lat=13.0827,
        assigned_lon=80.2707,
        firmware_version="1.2.0",
        trust_score=100.0
    )
    dev_quar = DeviceRegistryItem(
        device_id="TEST-DEVICE-QUARANTINED",
        bin_id="TEST-SEC-BIN-01",
        cert_fingerprint="sha256_quar_fingerprint",
        status=DeviceStatus.QUARANTINED,
        assigned_lat=13.0827,
        assigned_lon=80.2707,
        firmware_version="1.0.0",
        trust_score=30.0
    )
    dev_rev = DeviceRegistryItem(
        device_id="TEST-DEVICE-REVOKED",
        bin_id="TEST-SEC-BIN-01",
        cert_fingerprint="sha256_rev_fingerprint",
        status=DeviceStatus.REVOKED,
        assigned_lat=13.0827,
        assigned_lon=80.2707,
        firmware_version="0.9.0",
        trust_score=0.0
    )
    db.add_all([dev1, dev_quar, dev_rev])

    # 4. Test Vehicle & Drivers
    veh1 = Vehicle(
        vehicle_id="TRUCK-SEC-01",
        plate_number="TN-01-SEC-1234",
        vehicle_type="truck",
        capacity_kg=5000.0
    )
    db.add(veh1)
    db.commit()
    db.refresh(veh1)

    drv1 = Driver(
        driver_id="DRV-SEC-01",
        name="driver1_sec_test",
        license_number="DL-SEC-12345",
        phone="9876543210"
    )
    drv2 = Driver(
        driver_id="DRV-SEC-02",
        name="driver2_sec_test",
        license_number="DL-SEC-67890",
        phone="9876543211"
    )
    db.add_all([drv1, drv2])
    db.commit()
    db.refresh(drv1)
    db.refresh(drv2)

    # 5. Test Route & Assignment
    import json
    route1 = CollectionRoute(
        route_name="Route Alpha Security",
        zone="Zone A",
        bin_sequence=json.dumps(["TEST-SEC-BIN-01", "TEST-SEC-BIN-RECYCLE"]),
        total_distance_km=4.5,
        status=RouteStatus.PENDING,
        version=1
    )
    db.add(route1)
    db.commit()
    db.refresh(route1)

    assign1 = RouteAssignment(
        route_id=route1.id,
        vehicle_id=veh1.id,
        driver_id=drv1.id,
        scheduled_date=datetime.datetime.utcnow(),
        status=RouteStatus.PENDING
    )
    assign2 = RouteAssignment(
        route_id=route1.id,
        vehicle_id=veh1.id,
        driver_id=drv2.id,
        scheduled_date=datetime.datetime.utcnow(),
        status=RouteStatus.PENDING
    )
    db.add_all([assign1, assign2])
    db.commit()


    yield {
        "admin_token": create_access_token({"sub": "admin_sec_test"}),
        "operator_token": create_access_token({"sub": "operator_sec_test"}),
        "driver1_token": create_access_token({"sub": "driver1_sec_test"}),
        "driver2_token": create_access_token({"sub": "driver2_sec_test"}),
        "route_id": route1.id,
        "assign1_id": assign1.id,
        "assign2_id": assign2.id
    }

    db.query(RouteAssignment).filter(RouteAssignment.status == RouteStatus.PENDING).delete()
    db.query(CollectionRoute).filter(CollectionRoute.route_name.like("%Security%")).delete()
    db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id.in_(["TEST-SEC-BIN-01", "TEST-DEVICE-QUARANTINED", "TEST-DEVICE-REVOKED"])).delete()
    db.query(SmartBin).filter(SmartBin.bin_id.in_(["TEST-SEC-BIN-01", "TEST-SEC-BIN-RECYCLE"])).delete()
    db.query(User).filter(User.username.in_(["admin_sec_test", "operator_sec_test", "driver1_sec_test", "driver2_sec_test"])).delete()
    db.query(Driver).filter(Driver.driver_id.in_(["DRV-SEC-01", "DRV-SEC-02"])).delete()
    db.query(Vehicle).filter(Vehicle.vehicle_id == "TRUCK-SEC-01").delete()
    db.commit()
    db.close()



# ── 1. OWASP Web & API Security Tests ──────────────────────────────────────────

def test_security_headers_and_clickjacking(setup_test_environment):
    """Verifies CSP, X-Frame-Options, HSTS, and X-Content-Type-Options headers."""
    response = client.get("/api/bins")
    headers = response.headers

    assert headers.get("x-frame-options") == "DENY"
    assert "frame-ancestors 'none'" in headers.get("content-security-policy", "")
    assert headers.get("x-content-type-options") == "nosniff"
    assert "max-age=" in headers.get("strict-transport-security", "")
    assert headers.get("x-xss-protection") == "1; mode=block"


def test_sql_injection_defense():
    """Validates regex detection and parameterized query protection against SQL injection."""
    sqli_payloads = [
        "' OR 1=1--",
        "admin'--",
        "' UNION SELECT null, username, password FROM users--",
        "1; DROP TABLE smart_bins;--"
    ]
    for payload in sqli_payloads:
        is_attack, reason = detect_sql_injection(payload)
        assert is_attack is True, f"Failed to detect SQL injection: {payload}"

    # Test via API query parameters
    res = client.get("/api/bins?search=%27%20OR%201=1--")
    assert res.status_code == 400
    assert "SQL injection pattern" in res.json()["detail"]


def test_xss_protection():
    """Validates XSS string sanitization and HTML escaping."""
    dangerous_input = "<script>alert('xss')</script>Bin Location <b>HQ</b>"
    sanitized = sanitize_for_xss(dangerous_input)
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    assert "alert" in sanitized


def test_path_traversal_defense():
    """Validates strict path normalization and sandbox escape prevention."""
    base_dir = "C:\\test\\sandbox"
    malicious_paths = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\cmd.exe",
        "subdir/../../../secret.txt",
        "safe_file.txt\0/../root"
    ]
    for p in malicious_paths:
        with pytest.raises(Exception):
            safe_canonical_path(base_dir, p)

    # API endpoint test
    res = client.get("/api/reports/download?filename=../../etc/passwd")
    assert res.status_code == 400
    assert "Directory traversal attempt detected" in res.json()["detail"]


def test_ssrf_prevention():
    """Validates outbound URL filtering against loopback, link-local, and private RFC-1918 subnets."""
    dangerous_urls = [
        "http://127.0.0.1:8000/admin",
        "http://localhost:8080/metrics",
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata service
        "http://192.168.1.1/router_settings",
        "http://10.0.0.5:9000/internal",
        "file:///etc/shadow",
        "gopher://127.0.0.1:6379/_"
    ]
    for u in dangerous_urls:
        is_safe, reason = validate_url_for_ssrf(u)
        assert is_safe is False, f"SSRF vulnerability: {u} should be blocked"

    # API validation endpoint
    res = client.post("/api/security/verify-url?url=http://169.254.169.254/latest/meta-data/")
    assert res.status_code == 400


def test_oversized_payload_protection():
    """Ensures oversized payloads (> 10MB) are rejected with 413 Request Entity Too Large."""
    res = client.post(
        "/api/iot/telemetry",
        content="X" * 100,
        headers={"content-length": str(15 * 1024 * 1024)}  # 15 MB
    )
    assert res.status_code == 413


def test_bola_object_level_authorization(setup_test_environment):
    """Verifies Broken Object Level Authorization (BOLA/IDOR) protection for route assignments."""
    data = setup_test_environment
    driver1_token = data["driver1_token"]
    assign2_id = data["assign2_id"]

    # Driver 1 tries to access Driver 2's assignment
    res = client.get(
        f"/api/assignments/{assign2_id}",
        headers={"Authorization": f"Bearer {driver1_token}"}
    )
    assert res.status_code == 403
    assert "BOLA Protection" in res.json()["detail"]


# ── 2. Device Identity & Telemetry Security Tests ─────────────────────────────

def test_quarantined_device_telemetry_rejection(setup_test_environment):
    """Ensures a quarantined device cannot submit valid telemetry."""
    timestamp = int(time.time())
    payload = {
        "bin_id": "TEST-DEVICE-QUARANTINED",
        "fill_level": 50.0,
        "location_lat": 13.0827,
        "location_lon": 80.2707,
        "temperature": 25.0,
        "sensor_status": "normal",
        "hmac_signature": "signature_for_quarantined_device"
    }
    res = client.post("/api/iot/telemetry", json=payload)
    assert res.status_code == 403
    assert "Device is currently quarantined" in res.json()["detail"]


def test_revoked_device_telemetry_rejection(setup_test_environment):
    """Ensures a revoked device is rejected immediately."""
    payload = {
        "bin_id": "TEST-DEVICE-REVOKED",
        "fill_level": 50.0,
        "location_lat": 13.0827,
        "location_lon": 80.2707,
        "temperature": 25.0,
        "sensor_status": "normal",
        "hmac_signature": "signature_for_revoked_device"
    }
    res = client.post("/api/iot/telemetry", json=payload)
    assert res.status_code == 403
    assert "Device credentials have been revoked" in res.json()["detail"]



def test_device_lifecycle_quarantine_revoke_api(setup_test_environment):
    """Validates device quarantine and revocation via admin endpoints."""
    admin_token = setup_test_environment["admin_token"]

    # 1. Quarantine
    res = client.post(
        "/api/devices/TEST-SEC-BIN-01/quarantine",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "quarantined"

    # 2. Rotate Certificate
    res_rot = client.post(
        "/api/devices/TEST-SEC-BIN-01/rotate-cert",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_rot.status_code == 200
    assert "new_fingerprint" in res_rot.json()


# ── 3. Location Security & GPS Spoofing Tests ─────────────────────────────────

def test_gps_impossible_travel_detection():
    """Validates impossible travel velocity calculation (> 100 km/h for stationary smart bin)."""
    # Baseline: Chennai (13.0827, 80.2707)
    now = datetime.datetime.utcnow()
    # 2 minutes later, reported at Bengaluru (12.9716, 77.5946) -> ~290 km away
    later = now + datetime.timedelta(minutes=2)

    db = SessionLocal()
    status, score, reason = evaluate_location_telemetry(
        db=db,
        bin_id="TEST-SEC-BIN-01",
        reported_lat=12.9716,
        reported_lon=77.5946,
        assigned_lat=13.0827,
        assigned_lon=80.2707,
        reported_timestamp=later
    )
    db.close()

    assert status == "SUSPICIOUS" or status == "REJECTED"
    assert "Impossible velocity" in reason or "Geofence boundary breach" in reason


def test_haversine_distance_calculation():
    """Verifies geodesic distance computation between known coordinates."""
    # Distance between Chennai Central and Marina Beach is ~2.1 km
    dist = calculate_haversine_distance(13.0827, 80.2707, 13.0900, 80.2800)
    assert 1.0 < dist < 3.0


# ── 4. Sensor Trust & Correlation Tests ───────────────────────────────────────

def test_sensor_stuck_at_anomaly():
    """Validates detection of frozen/stuck-at ultrasonic sensor values."""
    db = SessionLocal()
    # 7 identical consecutive readings
    for i in range(7):
        health, reason = evaluate_sensor_telemetry(
            db=db,
            bin_id="TEST-SEC-BIN-01",
            sensor_type="ultrasonic",
            current_value=85.0
        )
    db.close()

    assert health == "SUSPICIOUS" or health == "WARNING"
    assert "Stuck-at sensor reading detected" in reason


def test_waste_density_sensor_correlation():
    """Validates physical correlation between ultrasonic volume, weight load cell, and temperature."""
    # Anomaly 1: Full bin (90%) but 0 kg load cell -> Ultrasonic stuck/blocked
    dens1, is_anom1, reason1 = calculate_waste_density_and_correlate(
        fill_level_pct=90.0, weight_kg=0.0
    )
    assert is_anom1 is True
    assert "Ultrasonic stuck" in reason1

    # Anomaly 2: Empty bin (5%) but 45 kg load cell -> Load cell drift
    dens2, is_anom2, reason2 = calculate_waste_density_and_correlate(
        fill_level_pct=5.0, weight_kg=45.0
    )
    assert is_anom2 is True
    assert "drift or ultrasonic failure" in reason2

    # Anomaly 3: High temperature (65°C) -> Thermal hazard
    dens3, is_anom3, reason3 = calculate_waste_density_and_correlate(
        fill_level_pct=50.0, weight_kg=20.0, temperature=65.0
    )
    assert is_anom3 is True
    assert "Thermal anomaly" in reason3


# ── 5. Waste Intelligence & Contamination Tests ───────────────────────────────

def test_hierarchical_waste_classification_confidence_triage():
    """Validates Level 1, 2, 3 classification and 3-tier confidence triage."""
    # 1. High confidence >= 90% -> AUTOMATIC
    t1, v1 = evaluate_confidence_tier(94.5)
    assert t1 == ClassificationConfidenceStatus.AUTOMATIC

    # 2. Medium confidence 70-89% -> RULE_VALIDATED
    t2, v2 = evaluate_confidence_tier(78.0)
    assert t2 == ClassificationConfidenceStatus.RULE_VALIDATED

    # 3. Low confidence < 70% -> UNKNOWN_HUMAN_REQUIRED
    t3, v3 = evaluate_confidence_tier(55.0)
    assert t3 == ClassificationConfidenceStatus.UNKNOWN_HUMAN_REQUIRED
    assert v3 == "PENDING_HUMAN_VERIFICATION"


def test_contamination_detection_hazardous_in_general():
    """Verifies cross-contamination detection for hazardous material in municipal streams."""
    db = SessionLocal()
    contam = detect_bin_contamination(
        db=db,
        bin_id="TEST-SEC-BIN-01",
        classified_l1="Hazardous",
        classified_l3="Battery",
        confidence=95.0
    )
    assert contam is not None
    assert contam.contamination_detected is True
    assert "Hazardous" in contam.details
    db.close()


def test_waste_composition_9_streams():
    """Validates 9-part waste composition distribution calculation."""
    db = SessionLocal()
    comp = recalculate_bin_composition(db, "TEST-SEC-BIN-01")
    total = (
        comp.organic_pct + comp.plastic_pct + comp.paper_pct + comp.cardboard_pct +
        comp.glass_pct + comp.metal_pct + comp.ewaste_pct + comp.hazardous_pct + comp.other_pct
    )
    assert 99.0 <= total <= 101.0  # Accounts for minor float rounding
    db.close()



# ── 6. Route Security & Anti-Override Prioritization Tests ────────────────────

def test_smart_collection_priority_anti_override():
    """
    CRITICAL PRINCIPLE:
    A high fill level (95%) must NOT automatically override a hazardous/security event.
    """
    # High fill, normal bin
    score_high_fill_normal = calculate_bin_priority_score(
        fill_percentage=95.0,
        category="General",
        is_hazardous=False,
        temperature=28.0,
        device_trust_score=100.0
    )

    # Moderate fill (75%), but HAZARDOUS contamination
    score_hazardous = calculate_bin_priority_score(
        fill_percentage=75.0,
        category="Hazardous",
        is_hazardous=True,
        temperature=30.0,
        device_trust_score=100.0
    )

    # Moderate fill (70%), but THERMAL FIRE / SMOLDERING HAZARD
    score_thermal_hazard = calculate_bin_priority_score(
        fill_percentage=70.0,
        category="General",
        is_hazardous=False,
        temperature=65.0,  # Smoldering
        device_trust_score=100.0
    )

    assert score_hazardous > score_high_fill_normal, "Hazardous event must override pure fill level"
    assert score_thermal_hazard > score_high_fill_normal, "Thermal hazard must override pure fill level"


def test_unauthorized_route_modification_prevention(setup_test_environment):
    """Verifies that Drivers are strictly forbidden from modifying route definitions (HTTP 403)."""
    data = setup_test_environment
    driver_token = data["driver1_token"]
    route_id = data["route_id"]

    res = client.put(
        f"/api/routes/{route_id}",
        json=["TEST-SEC-BIN-01"],
        headers={"Authorization": f"Bearer {driver_token}"}
    )
    assert res.status_code == 403
    assert "Drivers are strictly forbidden" in res.json()["detail"]


def test_route_integrity_hash_verification(setup_test_environment):
    """Verifies cryptographic route hash validation and detection of tampered sequences."""
    db = SessionLocal()
    route_id = setup_test_environment["route_id"]

    # 1. Authorize modification by Operator
    success, msg, route = modify_route_authorized(
        db=db,
        route_id=route_id,
        new_bin_ids=["TEST-SEC-BIN-01", "TEST-SEC-BIN-RECYCLE"],
        actor_id=1,
        actor_role=UserRole.OPERATOR
    )
    assert success is True

    # 2. Verify valid route hash
    is_valid, vmsg, audit = verify_route_integrity(db, route_id)
    assert is_valid is True

    # 3. Simulate unauthorized database tampering behind the scenes
    route.bin_sequence = json.dumps(["UNAUTHORIZED-BIN-999", "TEST-SEC-BIN-01"])
    db.commit()


    is_tampered_valid, tmsg, _ = verify_route_integrity(db, route_id)
    assert is_tampered_valid is False
    assert "Cryptographic hash mismatch" in tmsg

    db.close()
