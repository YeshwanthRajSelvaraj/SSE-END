# Phase 12 – Secure Coding and Refactoring
**Project:** EcoSmart Enterprise Cloud — Autonomous Waste Management & IoT Security  
**Repository:** [YeshwanthRajSelvaraj/SSE-END](https://github.com/YeshwanthRajSelvaraj/SSE-END)  
**Deliverable:** Source Code, Before/After Evidence, Test Suite, and Security Justification  
**Marks Allocation:** [4 Marks]

---

## 1. Executive Summary & Module Scope

Phase 12 demonstrates the identification, analysis, and refactoring of software vulnerabilities in a critical subsystem of the **EcoSmart Enterprise Cloud** platform: the **Telemetry Ingestion & Answer/Metric Submission Module**.

In an autonomous municipal waste management system, field sensor units installed on smart bins periodically transmit fill levels, ambient temperature readings, GPS coordinates, and hardware battery states. The ingestion module must securely authenticate edge hardware, validate data integrity, enforce physical bounds, protect persistence databases, and log anomalies.

This deliverable documents:
1. The **initial vulnerable implementation** and its vulnerabilities.
2. An in-depth security analysis detailing **five distinct weaknesses** (CWE-89, CWE-306, CWE-20, CWE-209, CWE-778).
3. The **refactored, hardened implementation** with input validation, cryptographic authorization, defensive error handling, and sensitive-data sanitization.
4. **Before/After comparative diff and automated verification evidence** via a dedicated unit test suite ([`backend/tests/test_refactoring.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/tests/test_refactoring.py)).

---

## 2. Initial (Vulnerable) Implementation

The initial version of the module was authored with rapid prototyping in mind, prioritizing functional happy-path insertion over defensive engineering.

**File:** [`backend/refactoring/before_vulnerable.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/refactoring/before_vulnerable.py)

```python
"""
Vulnerable Implementation: Answer Submission / Telemetry Ingestion
Security Weaknesses:
1. No Authentication/Authorization (Anyone can send data without verification).
2. SQL Injection vulnerability (Direct string formatting in SQL).
3. No Input Validation (Missing bounds check for physical values).
4. No Exception Handling (Can crash server or leak stack traces).
"""
import sqlite3

def ingest_telemetry_vulnerable(bin_id, fill_level, temperature):
    # 1. No auth check! Anyone calling this function can inject data.
    
    # 2. SQL Injection vulnerability
    conn = sqlite3.connect('waste_management.db')
    cursor = conn.cursor()
    
    query = f"INSERT INTO sensor_readings (bin_id, fill_level, temperature) VALUES ('{bin_id}', {fill_level}, {temperature})"
    
    # 3. No validation (temperature could be 9999999, fill_level could be negative)
    
    # 4. No error handling, will throw raw DB exception to caller if something fails
    cursor.execute(query)
    conn.commit()
    conn.close()
    
    return "Data inserted successfully"
```

---

## 3. Analysis of Vulnerabilities and Code-Quality Issues

| # | Vulnerability / Issue | Classification | Impact & Exploit Scenario |
|---|---|---|---|
| **1** | **SQL Injection (Dynamic String Formatting)** | **CWE-89** / OWASP A03:2021 | The query uses Python f-string interpolation: `f"INSERT ... VALUES ('{bin_id}', ...)"`. An attacker can pass `bin_id = "BIN-01', 50, 25); DROP TABLE sensor_readings; --"`. This executes arbitrary SQL, allowing database destruction, privilege escalation, or exfiltration of sensitive fleet records. |
| **2** | **Missing Authentication & Authorization** | **CWE-306** / OWASP A01:2021 | The function accepts raw parameters without verifying caller identity or cryptographic proof of possession of a hardware key. Rogue actors can inject fabricated 100% fill levels across the city, overwhelming municipal dispatch trucks with fake collection runs. |
| **3** | **Improper Input Validation (No Bounds Checking)** | **CWE-20** / OWASP A04:2021 | The function performs zero type checking or range validation. An input of `fill_level = -500.0` or `temperature = 99999.0` is accepted, polluting optimization algorithms and causing arithmetic crashes downstream. |
| **4** | **Improper Error Handling & Information Disclosure** | **CWE-209** / **CWE-703** | If SQLite encounters a syntax error, lock conflict, or disk full error, unhandled raw exceptions bubble up to the caller. This leaks table names, column structures, and file system paths. |
| **5** | **Lack of Security Auditing & Nonce Tracking** | **CWE-778** | The function does not record an audit log or verify timestamps, leaving the system completely blind to injection attempts and vulnerable to replay attacks. |

---

## 4. Refactored (Hardened) Implementation

The refactored module incorporates enterprise defensive programming principles, parameterization, and cryptographic integrity verification.

**File:** [`backend/refactoring/after_secured.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/refactoring/after_secured.py)

```python
"""
Secured Implementation: Answer Submission / Telemetry Ingestion
Improvements:
1. Strong Authentication (HMAC SHA-256 signature verification).
2. SQL Injection Prevention (Using SQLAlchemy ORM parameterized queries).
3. Strict Input Validation (Pydantic schema bounds).
4. Secure Error Handling (Catch exceptions, generic error messages).
5. Audit Logging (Tracks security events).
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import SmartBin, SensorReading
from app.anti_spoofing import verify_device_signature
from app.auth import log_audit, AuditAction

logger = logging.getLogger("secure_ingestion")

def ingest_telemetry_secured(db: Session, bin_id: str, payload: dict, signature: str, device_key: str):
    try:
        # 1. Authentication & Integrity Check (HMAC-SHA256)
        payload_str = f"{bin_id}|{payload.get('timestamp')}|{payload.get('fill_level')}|{payload.get('temperature')}"
        if not verify_device_signature(bin_id, payload_str, signature, device_key):
            log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_id, "Signature mismatch", severity="CRITICAL")
            raise ValueError("Authentication failed. Invalid device signature.")

        # 2. Strict Input Validation (Bounds checking)
        fill = float(payload.get('fill_level', 0))
        temp = float(payload.get('temperature', 0))
        if not (0.0 <= fill <= 100.0):
            raise ValueError("Invalid fill level. Must be between 0 and 100.")
        if not (-40.0 <= temp <= 85.0):
            raise ValueError("Invalid temperature. Must be between -40 and 85 Celsius.")

        # 3. Parameterized Database Queries (ORM) preventing SQL Injection
        bin_record = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
        if not bin_record:
            raise ValueError("Device not found in registry.")

        reading = SensorReading(
            bin_id=bin_record.id,
            fill_level=fill,
            temperature=temp,
            location_lat=payload.get('location_lat', bin_record.location_lat),
            location_lon=payload.get('location_lon', bin_record.location_lon),
            raw_hmac=signature
        )
        db.add(reading)
        db.commit()
        return {"status": "success"}

    # 4. Secure Error Handling & Atomic Rollback
    except ValueError as ve:
        logger.warning(f"Validation error during ingestion: {ve}")
        return {"status": "error", "message": str(ve)}
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"Database error during ingestion: {se}")
        return {"status": "error", "message": "Internal processing error."}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "message": "An unexpected error occurred."}
```

---

## 5. Security and Maintainability Justification

### 5.1 Input Validation
- **Type Safety**: Parameters extracted from the untrusted dictionary are explicitly cast to `float`, catching string injection and malformed objects early.
- **Physical Domain Boundaries**: Fill percentage is restricted to `[0.0, 100.0]%` and sensor temperature is restricted to operating bounds `[-40.0, 85.0]°C`. Out-of-bounds submissions raise clean `ValueError` exceptions immediately, preventing corrupted data from entering the database.

### 5.2 Cryptographic Authorization
- **Hardware-Level Identity**: Ingestion requires a cryptographic `HMAC-SHA256` signature computed across the concatenation of `bin_id`, `timestamp`, `fill_level`, and `temperature`.
- **Timing Attack Mitigation**: Under the hood, `verify_device_signature` utilizes Python’s `hmac.compare_digest()` constant-time comparator, preventing adversaries from guessing valid tokens via side-channel timing analysis.
- **Non-Repudiation & Audit**: Forged signatures immediately trigger a `CRITICAL` audit record (`AuditAction.SPOOFING_DETECTED`) linked to the device identifier in the database.

### 5.3 SQL Injection Immunity
- Direct string interpolation was replaced with **SQLAlchemy ORM** session queries.
- ORM queries are compiled with bound parameters by the database driver, treating input values strictly as literals and neutralizing SQL injection completely.

### 5.4 Defensive Error Handling & Transaction Integrity
- **Granular Exception Handling**: Differentiates between client input validation errors (`ValueError`), database operational failures (`SQLAlchemyError`), and system exceptions (`Exception`).
- **Atomic Rollback**: In the event of a database error, `db.rollback()` is executed, preventing aborted transactions from leaving database connections in corrupted states.
- **Sanitized Client Feedback**: The API caller receives generic responses (`"Internal processing error."`), while detailed operational logs are routed internally to secure logger streams, preventing information disclosure.

---

## 6. Before / After Comparison Matrix

```diff
--- before_vulnerable.py
+++ after_secured.py
@@ -1,15 +1,41 @@
-def ingest_telemetry_vulnerable(bin_id, fill_level, temperature):
-    # 1. No auth check! Anyone calling this function can inject data.
-    
-    # 2. SQL Injection vulnerability
-    conn = sqlite3.connect('waste_management.db')
-    cursor = conn.cursor()
-    
-    query = f"INSERT INTO sensor_readings (bin_id, fill_level, temperature) VALUES ('{bin_id}', {fill_level}, {temperature})"
-    
-    # 3. No validation (temperature could be 9999999, fill_level could be negative)
-    
-    # 4. No error handling, will throw raw DB exception to caller if something fails
-    cursor.execute(query)
-    conn.commit()
-    conn.close()
-    return "Data inserted successfully"
+def ingest_telemetry_secured(db: Session, bin_id: str, payload: dict, signature: str, device_key: str):
+    try:
+        # 1. Authentication & Integrity Check
+        payload_str = f"{bin_id}|{payload.get('timestamp')}|{payload.get('fill_level')}|{payload.get('temperature')}"
+        if not verify_device_signature(bin_id, payload_str, signature, device_key):
+            log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_id, "Signature mismatch", severity="CRITICAL")
+            raise ValueError("Authentication failed. Invalid device signature.")
+
+        # 2. Strict Input Validation (Bounds checking)
+        fill = float(payload.get('fill_level', 0))
+        temp = float(payload.get('temperature', 0))
+        if not (0.0 <= fill <= 100.0):
+            raise ValueError("Invalid fill level. Must be between 0 and 100.")
+        if not (-40.0 <= temp <= 85.0):
+            raise ValueError("Invalid temperature. Must be between -40 and 85 Celsius.")
+
+        # 3. Parameterized Database Queries (ORM)
+        bin_record = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
+        if not bin_record:
+            raise ValueError("Device not found in registry.")
+
+        reading = SensorReading(
+            bin_id=bin_record.id,
+            fill_level=fill,
+            temperature=temp,
+            location_lat=payload.get('location_lat', bin_record.location_lat),
+            location_lon=payload.get('location_lon', bin_record.location_lon),
+            raw_hmac=signature
+        )
+        db.add(reading)
+        db.commit()
+        return {"status": "success"}
+    except ValueError as ve:
+        logger.warning(f"Validation error: {ve}")
+        return {"status": "error", "message": str(ve)}
+    except SQLAlchemyError as se:
+        db.rollback()
+        logger.error(f"Database error: {se}")
+        return {"status": "error", "message": "Internal processing error."}
```

---

## 7. Verification Evidence: Automated Test Suite Execution

A dedicated automated test suite was developed in [`backend/tests/test_refactoring.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/tests/test_refactoring.py) to test both implementations.

### 7.1 Test Execution Command & Output

```bash
$ python -m pytest backend/tests/test_refactoring.py -v
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Yeshwanth Raj\Desktop\SSE-END
configfile: pytest.ini
collected 7 items

backend/tests/test_refactoring.py::test_vulnerable_accepts_arbitrary_unauthenticated_data PASSED [ 14%]
backend/tests/test_refactoring.py::test_vulnerable_lacks_input_validation PASSED         [ 28%]
backend/tests/test_refactoring.py::test_vulnerable_susceptible_to_sql_injection PASSED   [ 42%]
backend/tests/test_refactoring.py::test_secured_rejects_missing_or_invalid_hmac_signature PASSED [ 57%]
backend/tests/test_refactoring.py::test_secured_enforces_input_validation_bounds PASSED   [ 71%]
backend/tests/test_refactoring.py::test_secured_neutralizes_sql_injection PASSED          [ 85%]
backend/tests/test_refactoring.py::test_secured_successful_ingestion_with_valid_hmac PASSED [100%]

======================== 7 passed, 5 warnings in 3.08s ========================
```

### 7.2 Test Assertions Breakdown

1. `test_vulnerable_accepts_arbitrary_unauthenticated_data`: Proves that the vulnerable function accepts data without an HMAC signature or authentication token.
2. `test_vulnerable_lacks_input_validation`: Proves that the vulnerable function accepts negative fill percentages (-500%) and absurd temperatures (99,999°C).
3. `test_vulnerable_susceptible_to_sql_injection`: Proves that the vulnerable query string breaks out of quotes when provided with `' OR '1'='1`.
4. `test_secured_rejects_missing_or_invalid_hmac_signature`: Proves that forged or tampered signatures are rejected with `"Authentication failed"` and logged as `AuditAction.SPOOFING_DETECTED` (Severity: `CRITICAL`).
5. `test_secured_enforces_input_validation_bounds`: Proves that out-of-range inputs (150% fill, -100°C temperature) return clear validation errors.
6. `test_secured_neutralizes_sql_injection`: Proves that SQL strings are safely parameterized without syntax errors or injection execution.
7. `test_secured_successful_ingestion_with_valid_hmac`: Proves that validly signed, well-formed sensor payloads are committed cleanly to the database.
