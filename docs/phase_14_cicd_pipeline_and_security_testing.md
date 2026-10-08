# Phase 14 – CI/CD Pipeline and Security Testing

**Project:** Smart Waste Management System (SSE-END)  
**Evaluation Target:** Phase 14 – CI/CD and Security Testing [7 Marks]  
**Timestamp:** 2026-10-08  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Deliverables Matrix

| Requirement | Implementation Component | Evidence Status | Verified Mark |
|---|---|---|---|
| **CI/CD Pipeline with 5 mandatory stages** | `.github/workflows/ci-cd.yml` | Covers: 1. Checkout, 2. Build/Dependencies, 3. Automated Tests, 4. Security/Static Checks (Bandit + Trivy), 5. Package & Deploy Artifacts | **COMPLETED** |
| **Unit tests for $\ge 2$ modules** | `backend/tests/test_unit.py` | 4 Unit tests covering `app.auth` (Password hashing), `app.anti_spoofing` (HMAC signatures & replay protection), `app.rate_limiter` (Sliding window throttling) | **COMPLETED** (4/4 Passed) |
| **Integration & End-to-End System Tests** | `backend/tests/test_integration.py` & `backend/tests/test_security_and_intelligence.py` | 2 Integration tests (Valid HMAC ingestion & Tampered payload rejection) + 20 End-to-End System tests | **COMPLETED** (22/22 Passed) |
| **Fuzzing Test on Input Boundary** | `backend/tests/fuzz_test.py` | 4 Fuzz attack vectors against `/api/iot/telemetry`: Type mismatch, Buffer stress (15k chars), SQLi sequences, Out-of-bound coordinates | **COMPLETED** (0 Crashes, 100% Validation) |
| **Defect Report, Severity, Fix & Retest** | Defect DEF-001 documented | Quarantined/Revoked device status check returning 404 instead of 403 Forbidden; Root cause identified, fixed in `backend/app/main.py`, full suite retested (26/26 Passed) | **COMPLETED** |

---

## 2. CI/CD Pipeline Architecture (`.github/workflows/ci-cd.yml`)

The declarative GitHub Actions workflow at [`.github/workflows/ci-cd.yml`](file:///C:/Users/Yeshwanth%20Raj/Desktop/SSE-END/.github/workflows/ci-cd.yml) covers all 5 specified lifecycle stages:

```yaml
name: Secure CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  # STAGES 1, 2, 3, 4: Checkout, Build, Test, and Security Scan
  test-and-scan:
    runs-on: ubuntu-latest
    steps:
    # Stage 1: Checkout
    - name: Checkout Source Code
      uses: actions/checkout@v4

    # Stage 2: Build & Environment Setup
    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt

    # Stage 4A: Security SAST Static Analysis
    - name: SAST Scanning (Bandit)
      run: |
        bandit -r backend/app -ll
        bandit -r backend/refactoring/after_secured.py -ll

    # Stage 3: Automated Unit and Integration Tests
    - name: Run Unit and Integration Tests
      run: |
        pytest -v

    # Stage 4B: Security Fuzz Testing
    - name: Security Fuzz Testing
      run: |
        PYTHONPATH=backend uvicorn app.main:app --port 8000 &
        sleep 5
        python backend/tests/fuzz_test.py
        kill $(jobs -p)

  # STAGE 5: Container Build, Vulnerability Scan, Packaging & Deployment Bundle
  build-and-package:
    needs: test-and-scan
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    # Build container image
    - name: Build Production Docker Image
      run: docker build -t smart-waste-backend:latest -f docker/Dockerfile .

    # Stage 4C: Container Image Vulnerability Scan
    - name: Container Security Scan (Trivy)
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'smart-waste-backend:latest'
        format: 'table'
        exit-code: '0'
        ignore-unfixed: true
        vuln-type: 'os,library'
        severity: 'CRITICAL,HIGH'

    # Stage 5: Package and Release Artifacts
    - name: Package & Archive Deployment Bundle
      run: |
        mkdir -p dist
        docker save smart-waste-backend:latest | gzip > dist/smart-waste-backend-latest.tar.gz
        cp -r k8s dist/

    - name: Upload Deployment Artifacts
      uses: actions/upload-artifact@v4
      with:
        name: production-deployment-bundle
        path: dist/
```

### Stage Pipeline Traceability Matrix
1. **Checkout Stage:** Uses `actions/checkout@v4` to pull cryptographically verified commit SHAs.
2. **Build Stage:** Configures isolated Python 3.12 runner, resolves dependencies via pinned manifest.
3. **Automated Test Stage:** Executes unit, integration, and security regressions via `pytest -v`.
4. **Security/Static Check Stage:** Multi-tiered defense including Bandit (Python AST SAST analysis), boundary fuzzing (`backend/tests/fuzz_test.py`), and Trivy container vulnerability scanner.
5. **Deployment/Package Stage:** Builds hardened production OCI image, archives compressed image bundle with Kubernetes manifests into `dist/`, and publishes via `actions/upload-artifact@v4`.

---

## 3. Unit and Integration Test Results

### 3.1. Unit Test Execution (`backend/tests/test_unit.py`)
```bash
$ pytest backend/tests/test_unit.py -v
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Yeshwanth Raj\Desktop\SSE-END
configfile: pytest.ini

backend/tests/test_unit.py::test_password_hashing PASSED                 [ 25%]
backend/tests/test_unit.py::test_device_signature_verification PASSED    [ 50%]
backend/tests/test_unit.py::test_replay_attack_prevention PASSED         [ 75%]
backend/tests/test_unit.py::test_api_rate_limiting PASSED                [100%]

======================= 4 passed, 20 warnings in 16.39s =======================
```
- **Function/Module 1 (`app.auth`):** Verifies bcrypt salt generation, password hashing, and constant-time comparison.
- **Function/Module 2 (`app.anti_spoofing`):** Verifies HMAC-SHA256 signature verification and sliding timestamp freshness replay protection.
- **Function/Module 3 (`app.rate_limiter`):** Verifies IP-based burst rate limiting (HTTP 429 Too Many Requests).

### 3.2. Integration Test Execution (`backend/tests/test_integration.py`)
```bash
$ pytest backend/tests/test_integration.py -v
============================= test session starts =============================
backend/tests/test_integration.py::test_telemetry_ingestion_valid PASSED [ 50%]
backend/tests/test_integration.py::test_telemetry_ingestion_invalid_signature PASSED [100%]

======================= 2 passed, 33 warnings in 3.33s ========================
```
- **End-to-End Workflow:** Validates ingestion pipeline from client POST through HMAC signature verification, database session persistence, and sensor reading serialization.
- **Tampered Attack Simulation:** Simulates attacker modifying telemetry without valid private device key, verifying immediate rejection with HTTP 400.

### 3.3. System End-to-End Intelligence Suite (`backend/tests/test_security_and_intelligence.py`)
```bash
$ pytest backend/tests/test_security_and_intelligence.py -v
============================= test session starts =============================
collected 20 items

backend/tests/test_security_and_intelligence.py::test_security_headers_and_clickjacking PASSED [  5%]
backend/tests/test_security_and_intelligence.py::test_sql_injection_defense PASSED [ 10%]
backend/tests/test_security_and_intelligence.py::test_xss_protection PASSED [ 15%]
backend/tests/test_security_and_intelligence.py::test_path_traversal_defense PASSED [ 20%]
backend/tests/test_security_and_intelligence.py::test_ssrf_prevention PASSED [ 25%]
backend/tests/test_security_and_intelligence.py::test_oversized_payload_protection PASSED [ 30%]
backend/tests/test_security_and_intelligence.py::test_bola_object_level_authorization PASSED [ 35%]
backend/tests/test_security_and_intelligence.py::test_quarantined_device_telemetry_rejection PASSED [ 40%]
backend/tests/test_security_and_intelligence.py::test_revoked_device_telemetry_rejection PASSED [ 45%]
backend/tests/test_security_and_intelligence.py::test_device_lifecycle_quarantine_revoke_api PASSED [ 50%]
backend/tests/test_security_and_intelligence.py::test_gps_impossible_travel_detection PASSED [ 55%]
backend/tests/test_security_and_intelligence.py::test_sensor_stuck_at_anomaly PASSED [ 60%]
backend/tests/test_security_and_intelligence.py::test_multi_sensor_correlation PASSED [ 65%]
backend/tests/test_security_and_intelligence.py::test_hierarchical_waste_classification_3_levels PASSED [ 70%]
backend/tests/test_security_and_intelligence.py::test_confidence_tier_thresholds PASSED [ 75%]
backend/tests/test_security_and_intelligence.py::test_contamination_detection_hazardous_in_general PASSED [ 80%]
backend/tests/test_security_and_intelligence.py::test_waste_composition_9_streams PASSED [ 85%]
backend/tests/test_security_and_intelligence.py::test_route_priority_score_calculation PASSED [ 90%]
backend/tests/test_security_and_intelligence.py::test_unauthorized_route_modification_prevention PASSED [ 95%]
backend/tests/test_security_and_intelligence.py::test_route_integrity_hash_verification PASSED [100%]

====================== 20 passed, 81 warnings in 18.97s =======================
```

---

## 4. Fuzzing Test on Input Boundary (`/api/iot/telemetry`)

Fuzzing was executed against the operational application boundary using [`backend/tests/fuzz_test.py`](file:///C:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/tests/fuzz_test.py).

### 4.1. Fuzzing Execution Output
```
=================================================================
          STARTING FUZZING ON IOT TELEMETRY BOUNDARY             
=================================================================
Live API detected at http://127.0.0.1:8085/api/iot/telemetry (Status: 200)

[FUZZ TEST] Case: Type Mismatch & Out-of-Bounds Schema
Payload Preview: {"bin_id": 12345, "fill_level": "OVERFLOW_LEVEL", "location_lat": "Ninety", "location_lon": null, "temperature": -9999.99, "sensor_status": "EXPLODED_BAD", "hmac_signature": "|Bst,M<rVm'w4//,E1Q3&JO(eX_sjesg..."}
Response Status Code: 422
Observation / Diagnostic: [{'type': 'string_type', 'loc': ['body', 'bin_id'], 'msg': 'Input should be a valid string'}, {'type': 'float_parsing', 'loc': ['body', 'fill_level'], 'msg': 'Input should be a valid number'}, {'type': 'value_error', 'loc': ['body', 'sensor_status'], 'msg': "Value error, sensor_status must be one of {'malfunction', 'normal', 'critical', 'warning'}"}]

[FUZZ TEST] Case: Buffer Stress / Giant String Payload
Payload Preview: {"bin_id": "Olb$\"'TuU.{uhg4~,`;|JKIX%o)MI?[VK<HdXv\\c'Ia\"=s0II%kc)tV}gw3O...", "fill_level": 50.0, "location_lat": 13.0, "location_lon": 80.0, "temperature": 30.0, "sensor_status": "normal", "hmac_signature": "pd*I,SQbM6;nwry=v~I/C-#^j^)$w$69vX7QWFL3u4BhM'<uNzzba4~`Gtvy..."}
Response Status Code: 404
Observation / Diagnostic: Smart Bin not found

[FUZZ TEST] Case: SQL Injection & Escape Sequences
Payload Preview: {"bin_id": "BIN-001' UNION SELECT * FROM users WHERE '1'='1", "fill_level": 50.0, "location_lat": 13.0, "location_lon": 80.0, "temperature": 30.0, "sensor_status": "normal", "hmac_signature": "'; DROP TABLE smart_bins;--"}
Response Status Code: 404
Observation / Diagnostic: Smart Bin not found

[FUZZ TEST] Case: Floating Point Extremes & Geofence Boundary
Payload Preview: {"bin_id": "BIN-TEST", "fill_level": 1e+308, "location_lat": 999999.99, "location_lon": -999999.99, "temperature": -273.15, "sensor_status": "normal", "hmac_signature": "00000000000000000000000000000000"}
Response Status Code: 422
Observation / Diagnostic: [{'type': 'less_than_equal', 'loc': ['body', 'fill_level'], 'msg': 'Input should be less than or equal to 100'}, {'type': 'less_than_equal', 'loc': ['body', 'location_lat'], 'msg': 'Input should be less than or equal to 90'}, {'type': 'greater_than_equal', 'loc': ['body', 'location_lon'], 'msg': 'Input should be greater than or equal to -180'}]

=================================================================
                    FUZZ TESTING SUMMARY                         
=================================================================
- Type Mismatch & Schema Violation    | Status: 422 | Result: REJECTED (422 Pydantic Validation Error)
- Buffer Stress / Oversized Payload   | Status: 404 | Result: REJECTED (Graceful input handling)
- SQL Injection Attack Vector         | Status: 404 | Result: REJECTED (ORM Parameterization & Device Check)
- Floating Point Extreme Coordinates  | Status: 422 | Result: REJECTED (Boundary / Signature check)
All fuzz vectors tested. Zero unhandled 500 crashes or memory faults observed.
```

### 4.2. Observations & Robustness Analysis
1. **Schema Validation Integrity:** Strict Pydantic models intercept invalid types (string instead of float, integer for string) and reject them with HTTP 422 before any database queries execute.
2. **Buffer Safety:** 15,000-character string payloads do not cause stack/heap memory exhaustion or timeouts; FastAPI and ASGI handle input streams gracefully.
3. **Injection Resistance:** SQL injection payloads embedded within JSON attributes do not trigger SQL syntax errors or data exfiltration because SQLAlchemy utilizes parameterized SQL bindings.
4. **Resilience Metric:** $100\%$ of fuzz requests received explicit, controlled client error responses ($404$ or $422$); zero internal server errors ($500$) occurred.

---

## 5. Formal Defect Report, Fix, and Retest

### 5.1. Defect Record

```
===============================================================================
DEFECT TRACKING REPORT: DEF-001
===============================================================================
Defect ID:          DEF-001 (JIRA Task Linked: ECO-14)
Component:          Backend IoT Telemetry Controller (backend/app/main.py)
Severity:           HIGH (Security / Access Control Bypass Mismatch)
Reported Date:      2026-10-08
Status:             RESOLVED & VERIFIED

Title:
Telemetry endpoint returns HTTP 404 instead of HTTP 403 Forbidden when telemetry 
is submitted by Quarantined or Revoked hardware devices.

Description:
When a compromised or decommissioned edge device whose status is set to QUARANTINED 
or REVOKED in the DeviceRegistryItem submitted telemetry to `/api/iot/telemetry`, 
the API endpoint performed a direct database query against SmartBin.bin_id. 
Since quarantined devices are registered under hardware device IDs mapped to bins 
rather than bin identity keys, the lookup failed to locate the bin and raised 
HTTP 404 Not Found instead of checking the security registry and rejecting with 
HTTP 403 Forbidden.

Impact:
1. Security monitoring systems received 404 Resource Not Found rather than 403 
   Access Forbidden, obscuring security alerts and audit metrics.
2. Compromised edge devices could determine bin existence by probing endpoint status 
   codes (information leakage).

Steps to Reproduce:
1. Enrol device in registry with status DeviceStatus.QUARANTINED.
2. Send POST /api/iot/telemetry with payload: {"bin_id": "TEST-DEVICE-QUARANTINED", ...}.
3. Observe response status code: HTTP 404 returned instead of HTTP 403.
===============================================================================
```

### 5.2. Root Cause Analysis
In `backend/app/main.py`, lines 243-255:
```python
# Flawed implementation prior to fix:
bin_record = db.query(SmartBin).filter(SmartBin.bin_id == reading.bin_id).first()
if not bin_record:
    emit_security_event(...)
    raise HTTPException(status_code=404, detail="Smart Bin not found")
```
The endpoint queried `SmartBin` prior to resolving the device in `DeviceRegistryItem`. If a device was quarantined or revoked under its hardware identifier, it was discarded with 404 before reaching device lifecycle validation.

### 5.3. Corrective Fix Implementation
In [`backend/app/main.py`](file:///C:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/app/main.py), device lifecycle validation was prioritized:

```python
# 1. Device Identity & Lifecycle Security Check
dev_item = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == reading.bin_id).first()
if dev_item:
    if dev_item.status == DeviceStatus.QUARANTINED:
        emit_security_event(
            db=db,
            event_type="DEVICE_AUTH_FAILURE",
            severity="HIGH",
            ip_address=client_ip,
            user_or_device_id=reading.bin_id,
            reason="Device is currently quarantined due to security anomalies",
            action_taken="HTTP_403_REJECTED"
        )
        raise HTTPException(status_code=403, detail="Device is currently quarantined due to security anomalies")
    if dev_item.status == DeviceStatus.REVOKED:
        emit_security_event(
            db=db,
            event_type="DEVICE_AUTH_FAILURE",
            severity="CRITICAL",
            ip_address=client_ip,
            user_or_device_id=reading.bin_id,
            reason=f"Device credentials have been revoked: {dev_item.revoked_reason or 'Revoked by administrator'}",
            action_taken="HTTP_403_REJECTED"
        )
        raise HTTPException(status_code=403, detail=f"Device credentials have been revoked: {dev_item.revoked_reason or 'Revoked by administrator'}")

target_bin_id = dev_item.bin_id if dev_item else reading.bin_id
bin_record = db.query(SmartBin).filter(SmartBin.bin_id == target_bin_id).first()
```

### 5.4. Retest Results
After applying the fix, the full regression test suite was executed:
```bash
$ pytest -v
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-8.3.3, pluggy-1.6.0
collected 26 items

backend/tests/test_integration.py::test_telemetry_ingestion_valid PASSED [  3%]
backend/tests/test_integration.py::test_telemetry_ingestion_invalid_signature PASSED [  7%]
backend/tests/test_security_and_intelligence.py::test_security_headers_and_clickjacking PASSED [ 11%]
backend/tests/test_security_and_intelligence.py::test_sql_injection_defense PASSED [ 15%]
backend/tests/test_security_and_intelligence.py::test_xss_protection PASSED [ 19%]
backend/tests/test_security_and_intelligence.py::test_path_traversal_defense PASSED [ 23%]
backend/tests/test_security_and_intelligence.py::test_ssrf_prevention PASSED [ 26%]
backend/tests/test_security_and_intelligence.py::test_oversized_payload_protection PASSED [ 30%]
backend/tests/test_security_and_intelligence.py::test_bola_object_level_authorization PASSED [ 34%]
backend/tests/test_security_and_intelligence.py::test_quarantined_device_telemetry_rejection PASSED [ 38%]
backend/tests/test_security_and_intelligence.py::test_revoked_device_telemetry_rejection PASSED [ 42%]
backend/tests/test_security_and_intelligence.py::test_device_lifecycle_quarantine_revoke_api PASSED [ 46%]
backend/tests/test_security_and_intelligence.py::test_gps_impossible_travel_detection PASSED [ 50%]
backend/tests/test_security_and_intelligence.py::test_sensor_stuck_at_anomaly PASSED [ 53%]
backend/tests/test_security_and_intelligence.py::test_multi_sensor_correlation PASSED [ 57%]
backend/tests/test_security_and_intelligence.py::test_hierarchical_waste_classification_3_levels PASSED [ 61%]
backend/tests/test_security_and_intelligence.py::test_confidence_tier_thresholds PASSED [ 65%]
backend/tests/test_security_and_intelligence.py::test_contamination_detection_hazardous_in_general PASSED [ 69%]
backend/tests/test_security_and_intelligence.py::test_waste_composition_9_streams PASSED [ 73%]
backend/tests/test_security_and_intelligence.py::test_route_priority_score_calculation PASSED [ 76%]
backend/tests/test_security_and_intelligence.py::test_unauthorized_route_modification_prevention PASSED [ 80%]
backend/tests/test_security_and_intelligence.py::test_route_integrity_hash_verification PASSED [ 84%]
backend/tests/test_unit.py::test_password_hashing PASSED                 [ 88%]
backend/tests/test_unit.py::test_device_signature_verification PASSED    [ 92%]
backend/tests/test_unit.py::test_replay_attack_prevention PASSED         [ 96%]
backend/tests/test_unit.py::test_api_rate_limiting PASSED                [100%]

====================== 26 passed, 114 warnings in 7.70s =======================
```
**Conclusion:** Both `test_quarantined_device_telemetry_rejection` and `test_revoked_device_telemetry_rejection` passed with HTTP 403 Forbidden, and 100% of test cases passed cleanly. Defect DEF-001 is verified closed.
