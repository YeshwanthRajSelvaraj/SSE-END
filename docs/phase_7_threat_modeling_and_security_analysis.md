# Phase 7 – Threat Modeling and Security Analysis
**Project:** EcoSmart Enterprise Cloud — Autonomous Waste Management & IoT Security  
**Repository:** [YeshwanthRajSelvaraj/SSE-END](https://github.com/YeshwanthRajSelvaraj/SSE-END)  
**Deliverable:** Asset/CIA Classification, STRIDE Threat Model, Information Flow Analysis, and Vulnerability Analysis  
**Marks Allocation:** [10 Marks]

---

## 1. Executive Summary & Scope

Phase 7 delivers a comprehensive security analysis and threat model for the **EcoSmart Enterprise Cloud** cyber-physical smart waste management infrastructure. Because this system integrates Internet-of-Things (IoT) edge sensors, GPS-tracked municipal fleet logistics, and mission-critical automated route optimization algorithms, securing its data flows and control processes is vital to public infrastructure resilience.

This document covers:
1. **Eight Primary Assets** classified across **Confidentiality, Integrity, and Availability (CIA)**.
2. A formal **Data Flow Diagram (DFD)** decomposition and **STRIDE Threat Analysis** identifying 12 concrete threats.
3. A detailed **Threat Matrix** mapping DFD elements, threats, STRIDE categories, impact levels, and concrete mitigations.
4. **Information Flow Analysis** for three sensitive assets across trust boundaries.
5. A **Vulnerability Analysis** detailing six specific vulnerabilities, associated CWEs, exploit scenarios, and implemented mitigations.

---

## 2. Asset Identification and CIA Classification

The EcoSmart platform processes cyber-physical, cryptographic, and logistical assets. Below are eight primary assets classified by CIA requirements:

| # | Asset Name | Description & Storage Location | Confidentiality (C) | Integrity (I) | Availability (A) | CIA Rationale & Impact of Compromise |
|---|---|---|---|---|---|---|
| **A1** | **IoT Device HMAC Secret Keys** | Cryptographic shared secrets provisioned on edge microcontrollers and stored in `smart_bins.device_key`. | **HIGH** | **HIGH** | **MEDIUM** | If exposed, adversaries can impersonate municipal bins, spoof telemetry, and disrupt collection schedules. Integrity is critical to guarantee data origin authenticity. |
| **A2** | **Sensor Telemetry Data Stream** | Real-time sensor readings (fill level %, temperature °C, location GPS) transmitted by edge bins. | **LOW** | **HIGH** | **HIGH** | Fill level is public municipal information (low confidentiality), but compromised integrity can trigger phantom collection runs or mask overflowing bins. Availability is critical for dispatch decisions. |
| **A3** | **Municipal User Credentials & Hashes** | User account records, email addresses, and bcrypt password hashes stored in `users`. | **HIGH** | **HIGH** | **HIGH** | Compromise allows account takeover of municipal administrators, dispatchers, or drivers, leading to unauthorized fleet commandeering and data tampering. |
| **A4** | **JWT Access & Refresh Tokens** | Ephemeral `HS256`-signed bearer tokens granting session access to protected REST APIs. | **HIGH** | **HIGH** | **MEDIUM** | Stolen tokens grant impersonation privileges during the token lifetime (30 minutes). Integrity ensures tokens cannot be modified to elevate roles. |
| **A5** | **Collection Route Manifests & Fleet Waypoints** | TSP-optimized driver routes, waypoint orders, and real-time vehicle dispatch instructions. | **MEDIUM** | **HIGH** | **HIGH** | Tampering with routes can misdirect garbage trucks, cause traffic congestion, or skip hazardous waste sites. High availability is required for field operations. |
| **A6** | **Smart Bin Master Inventory & State Database** | Persistent relational database schema (`smart_bins`, `sensor_readings`, `vehicles`) in SQLite/PostgreSQL. | **MEDIUM** | **HIGH** | **HIGH** | Unauthorized data deletion or modification cripples municipal operations and invalidates historical compliance records. |
| **A7** | **Security Audit Logs & Intrusion Records** | Immutable historical logs of security events (`audit_logs`), signature failures, and spoofing detections. | **MEDIUM** | **HIGH** | **HIGH** | Audit records require strict tamper-resistance to support forensic investigations and regulatory audits (e.g., ISO/IEC 27001). |
| **A8** | **CI/CD Pipeline & Deployment Secrets** | GitHub Actions secrets, Docker registry credentials, and Kubernetes secrets (`backend-secrets`). | **HIGH** | **HIGH** | **HIGH** | Exposure allows supply-chain compromise, arbitrary container injection, and total cluster takeover. |

---

## 3. Data Flow Diagram (DFD) and STRIDE Threat Model

### 3.1 DFD Architecture and Elements

```
                      TRUST BOUNDARY 1 (Public Edge / Internet)
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    ▼                                                              ▼
[ EE1: Smart Bin ] ──(DF1: Telemetry HTTPS)──► ┌───────────────────────────────────┐
[ Edge Sensor    ]                            │ P1: Ingestion & Verification      │
                                              │ (/api/iot/telemetry)              │
                                              └─────────────────┬─────────────────┘
                                                                │
                                              TRUST BOUNDARY 2  │ (Internal App)
                                                                ▼
                                              ┌───────────────────────────────────┐
                                              │ P4: Security Engine & Audit       │
                                              │ (anti_spoofing.py, log_audit)     │
                                              └────────┬─────────────────┬────────┘
                                                       │                 │
                                                       ▼                 ▼
[ EE2: Field Driver     ] ──(DF2: Driver API)─► ┌─────────────┐   ┌───────────────┐
[ Mobile Web App        ]                       │ P2: Route   │   │ DS1: Relational│
                                                │ Optimization│◄──┤ Database      │
[ EE3: City Dispatcher  ] ──(DF3: Admin Auth)─► │ Engine (TSP)│   │ (smart_bins,  │
[ Web Command Center    ]                       └──────┬──────┘   │  sensor_read) │
                                                       │          └───────────────┘
                                                       ▼                 ▲
                                                ┌─────────────┐          │
                                                │ P3: RBAC &  │──────────┘
                                                │ Auth Service│
                                                └─────────────┘
                                                       │
                                                       ▼
                                                ┌───────────────┐
                                                │ DS2: Nonce &  │
                                                │ Rate Limiter  │
                                                │ Cache (RAM)   │
                                                └───────────────┘
```

#### DFD Element Inventory:
- **External Entities (EE)**:
  - `EE1`: Smart Bin Edge Microcontroller (Ultrasonic & Temperature sensors).
  - `EE2`: Field Truck Driver (Mobile touch browser).
  - `EE3`: Municipal Operations Dispatcher / Admin (Desktop browser).
- **Processes (P)**:
  - `P1`: Telemetry Ingestion & Signature Verification (`/api/iot/telemetry`).
  - `P2`: Route Optimization Engine (Greedy Nearest Neighbor / TSP solver).
  - `P3`: Authentication & RBAC Service (`/api/auth/login`, `verify_token`).
  - `P4`: Threat Detection & Audit Logging (`security_engine.py`, `log_audit`).
- **Data Stores (DS)**:
  - `DS1`: Relational Database (`waste_management.db` / PostgreSQL).
  - `DS2`: In-Memory Nonce Cache & Token Bucket Rate Limiter (`nonce_cache`, `rate_limiter.py`).
- **Data Flows (DF)**:
  - `DF1`: Raw Signed Telemetry Packet (EE1 -> P1).
  - `DF2`: Route Manifest Request & Bin Collection Acknowledgment (EE2 -> P2).
  - `DF3`: Login Credentials & Admin Management Requests (EE3 -> P3).
  - `DF4`: Read/Write Database Operations (P1, P2, P3 -> DS1).
  - `DF5`: Nonce Verification & Window Eviction (P1 -> DS2).

---

## 4. Threat Matrix: STRIDE Analysis (12 Threats Identified)

The **STRIDE** methodology (**S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, **E**levation of Privilege) was applied across all DFD elements:

| Threat ID | DFD Element | Threat Description | STRIDE Category | Risk Level (DREAD) | Impact Description | Concrete Mitigation Implemented in SSE-END |
|---|---|---|---|---|---|---|
| **T01** | `EE1 / DF1` | **Rogue Device Spoofing**: Adversary injects fake sensor packets claiming to be a legitimate bin. | **Spoofing** | **HIGH** | Inaccurate fill metrics lead to wasted fleet fuel and skipped overflowing bins. | Mandatory **HMAC-SHA256 signature verification** (`verify_device_signature`) using device-specific secret keys. |
| **T02** | `DF1` | **In-Transit Telemetry Tampering**: Man-in-the-Middle adversary intercepts and modifies sensor readings. | **Tampering** | **HIGH** | Altered readings mask overflowing bins or cause false emergency alerts. | Payload serialization hash verified against HMAC signature; enforced **TLS 1.3 encryption** in transit. |
| **T03** | `EE2 / DF2` | **Driver Action Repudiation**: Driver claims they collected a bin that was never visited. | **Repudiation** | **MEDIUM** | Lack of operational accountability; uncollected waste accumulates. | **Geofence validation** (`verify_geofence`) requiring driver GPS coordinates within 50 meters of bin location + audit timestamping. |
| **T04** | `P1 / DF4` | **SQL Injection via Malicious Telemetry**: Attacker inserts SQL metacharacters into `bin_id` or sensor parameters. | **Information Disclosure / Tampering** | **CRITICAL** | Database exfiltration, deletion, or arbitrary remote command execution. | Parameterized queries using **SQLAlchemy ORM** (`after_secured.py`) and Pydantic schema validation. |
| **T05** | `P1 / DF1` | **Volumetric DoS on Ingestion Endpoint**: Flooding the telemetry API with thousands of concurrent packets. | **Denial of Service** | **HIGH** | Exhausts server worker pool; legitimate sensor readings and dispatch updates drop. | In-memory **Token Bucket Rate Limiting** (`rate_limiter.py`) capping requests to 100 req/min per IP with HTTP 429 responses. |
| **T06** | `P3 / EE2` | **Vertical Privilege Escalation**: Driver modifies client-side token or request to access Admin analytics. | **Elevation of Privilege** | **CRITICAL** | Unauthorized users modify system configuration, delete audit logs, or alter accounts. | Strict **Role-Based Access Control (RBAC)** in `auth.py` (`require_role(UserRole.ADMIN)`) enforced on backend routes. |
| **T07** | `DF1 / DS2` | **Telemetry Replay Attack**: Eavesdropper captures a valid signed telemetry packet and replays it continuously. | **Tampering / Spoofing** | **HIGH** | Freezes bin state in the past, hiding real fill-level changes. | **Timestamp Nonce Cache** (`check_replay_attack`): Rejects packets older than 300s or containing previously seen timestamps. |
| **T08** | `DF3 / P3` | **Credential Snooping in Transit**: Interception of plaintext login passwords over unencrypted HTTP. | **Information Disclosure** | **HIGH** | Account compromise and administrative takeover. | HTTP to HTTPS redirection, strict transport security (HSTS), and token hashing with bcrypt. |
| **T09** | `P2` | **TSP Route Optimizer Algorithmic Complexity Attack**: Submitting thousands of bogus bins to force combinatorial explosion. | **Denial of Service** | **MEDIUM** | CPU exhaustion in the backend, starving other concurrent API workers. | **Greedy Nearest Neighbor** heuristic capped at $O(N^2)$ with maximum waypoint batch size limit (50 bins) and pre-filtered active bins. |
| **T10** | `EE3 / P3` | **Brute-Force Password Guessing**: Automated dictionary attack against the `/api/auth/login` endpoint. | **Spoofing / DoS** | **HIGH** | Unauthorized account access to dispatcher command center. | Rate limiting on authentication routes (5 attempts/min) plus audit logging of failed login attempts (`LOGIN_FAILED`). |
| **T11** | `Container` | **Container Breakout via Root Execution**: Attacker exploiting a vulnerability in a Python library to escape to host. | **Elevation of Privilege** | **HIGH** | Full control of Kubernetes node and access to underlying host file system. | Dockerfile runs as **non-root user** (`appuser`, UID 10001) with `readOnlyRootFilesystem: true` and all Linux capabilities dropped. |
| **T12** | `Source / CI`| **Hardcoded Secret Exposure**: Committing API keys, database passwords, or JWT secrets to git repository. | **Information Disclosure** | **CRITICAL** | Complete system compromise through static repository harvesting. | Automated **Secret Scanner** (`scripts/scan_secrets.py`) and Pydantic environment variable externalization. |

---

## 5. Information Flow Analysis for Three Sensitive Assets

### 5.1 Asset 1: IoT Device Private HMAC Secret Key (`device_key`)

```
[ Hardware Provisioning ] ──► [ Database (smart_bins.device_key) ] ──► [ App Memory ]
                                                                             │
                                                                             ▼
                                                                  [ verify_device_signature ]
                                                                             │
                                                                             ▼
                                                                  [ constant-time compare ]
```

- **Origin & Provisioning**: Device keys are generated as 256-bit cryptographically secure pseudorandom strings (`secrets.token_hex(16)`) during device manufacturing or registration.
- **Storage at Rest**: Persisted in the `smart_bins` table in the protected database. Only accessible to the backend application database user.
- **Transmission in Transit**: The private key is **NEVER** transmitted over the network during normal telemetry transmission. Both the edge device and server possess the shared key independently.
- **Runtime Processing**: When telemetry arrives, `ingest_telemetry_secured` loads the `device_key` into memory and computes `expected_hmac = hmac.new(key, msg, sha256).hexdigest()`.
- **Trust Boundaries Crossed**:
  1. *Boundary 1 (Storage to Application)*: Loaded across the secure SQL connection into application heap memory.
  2. *Boundary 2 (Application to Comparator)*: Processed strictly in memory using `hmac.compare_digest()`, eliminating timing leakage. Memory is deallocated upon request completion.

---

### 5.2 Asset 2: Sensor Telemetry & Fill-Level Stream

```
[ Ultrasonic Sensor ] ──► [ Microcontroller ] ──(HTTPS/TLS 1.3)──► [ FastAPI Ingress ]
                                                                          │
    ┌─────────────────────────────────────────────────────────────────────┴──────────┐
    ▼                                     ▼                                          ▼
[ HMAC Validation ]            [ Physical Range Check ]                   [ Anti-Replay Nonce ]
(Anti-Spoofing Gate)           (0 <= fill <= 100%)                        (abs(t - now) < 300s)
    │                                     │                                          │
    └─────────────────────────────────────┬──────────────────────────────────────────┘
                                          │ ALL PASS
                                          ▼
                               [ SensorReading ORM ] ──► [ Database (sensor_readings) ]
                                          │
                                          ▼
                               [ TSP Route Optimizer ]
```

- **Origin**: Ultrasonic echo sensors calculate distance to waste surface inside the bin, converting it to a fill percentage `[0.0, 100.0]%`.
- **Transmission in Transit**: Edge device serializes `{bin_id, timestamp, fill_level, temperature}` into a string, hashes it with HMAC-SHA256, and posts the JSON payload over **TLS 1.3 encrypted HTTPS** to `/api/iot/telemetry`.
- **Boundary Verification Gates**:
  1. *Cryptographic Gate*: Checks that the signature matches the payload.
  2. *Freshness Gate*: Verifies that the timestamp is within 300 seconds and has not been processed before (`check_replay_attack`).
  3. *Sanity & Boundary Gate*: Validates that fill level is between 0% and 100% and temperature is within operating range (`-40°C` to `85°C`).
- **Storage & Processing**: Committed to `sensor_readings` via parameterized ORM entity. The current fill level in `smart_bins` is updated, making it available to the TSP route optimization heuristic.

---

### 5.3 Asset 3: User Credentials & JWT Access Tokens

```
[ Web Client / Browser ] ──(HTTPS POST /api/auth/login)──► [ FastAPI Auth Controller ]
                                                                  │
                                                                  ▼
                                                      [ Bcrypt Password Verify ]
                                                      (passlib CryptContext)
                                                                  │
                                                                  ▼
                                                      [ Generate JWT Access Token ]
                                                      (HS256 with SECRET_KEY, exp: 30m)
                                                                  │
                                                                  ▼
[ Client Local Storage ] ◄──(Bearer Token Response)───────────────┘
          │
          ▼
(HTTP Request + Authorization: Bearer <token>)
          │
          ▼
[ FastAPI Dependency: get_current_user ] ──► [ Role Check: require_role(ADMIN) ]
```

- **Origin**: Administrator or driver inputs username and plaintext password in the frontend login interface.
- **Transmission in Transit**: Transmitted via HTTPS POST payload to `/api/auth/login`.
- **Password Verification**: Backend searches the `users` table for the matching username. The submitted plaintext password is evaluated against the stored hash using `bcrypt.verify()`. The plaintext password is never stored or logged.
- **Token Generation**: Upon successful authentication, a JWT is generated containing `{"sub": username, "role": role, "exp": now + 30m, "iat": now}`. The token is cryptographically signed using `SECRET_KEY` and returned as a bearer token.
- **Request Authorization**: On subsequent requests, the client includes the token in the `Authorization: Bearer <token>` header. The FastAPI dependency `get_current_user` decodes the token, validates signature and expiration, and enforces role boundaries (`ADMIN`, `DISPATCHER`, `DRIVER`).

---

## 6. Vulnerability Analysis (Six Primary Vulnerabilities)

The security audit identified six distinct vulnerabilities in traditional IoT waste management systems, along with their mitigations in EcoSmart:

### Vulnerability 1: SQL Injection in Telemetry Ingestion
- **Affected Element**: `P1: Ingestion Process` / `DS1: Relational Database`.
- **Related STRIDE Threat**: `T04` (Tampering / Information Disclosure).
- **CWE Identifier**: **CWE-89** (Improper Neutralization of Special Elements used in an SQL Command).
- **Vulnerability Mechanism**: Legacy code used string formatting: `f"INSERT INTO sensor_readings VALUES ('{bin_id}', ...)"`.
- **Impact**: Attackers can execute arbitrary SQL commands to dump user tables, drop audit records, or modify bin statuses.
- **Mitigation & Evidence**: Refactored to **SQLAlchemy ORM** parameterized queries in [`after_secured.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/refactoring/after_secured.py). Verified by Bandit SAST and unit test `test_secured_neutralizes_sql_injection`.

---

### Vulnerability 2: Unauthenticated Telemetry Injection (Missing Signature Check)
- **Affected Element**: `EE1: Edge Hardware` / `P1: Ingestion API`.
- **Related STRIDE Threat**: `T01` (Spoofing).
- **CWE Identifier**: **CWE-306** (Missing Authentication for Critical Function).
- **Vulnerability Mechanism**: Ingestion endpoints accepting raw JSON payloads without verifying hardware identity.
- **Impact**: Attackers can spoof sensor data across the city, generating thousands of fake overflowing bin alerts and overwhelming municipal sanitation operations.
- **Mitigation & Evidence**: Enforced **HMAC-SHA256 signature verification** on every payload (`verify_device_signature`). Tampering triggers `AuditAction.SPOOFING_DETECTED` with severity `CRITICAL`. Verified by test `test_secured_rejects_missing_or_invalid_hmac_signature`.

---

### Vulnerability 3: Telemetry Replay Attack
- **Affected Element**: `DF1: Telemetry Data Flow` / `P1: Ingestion Process`.
- **Related STRIDE Threat**: `T07` (Tampering / Spoofing).
- **CWE Identifier**: **CWE-294** (Authentication Bypass by Capture-replay).
- **Vulnerability Mechanism**: Even with HMAC signatures, if timestamps are not validated, an adversary who captures a signed payload can replay it repeatedly.
- **Impact**: Real fill-level progression is masked by replayed historical readings, preventing necessary waste collections.
- **Mitigation & Evidence**: Implemented in-memory sliding **Nonce Cache** (`check_replay_attack` in `anti_spoofing.py`). Telemetry with timestamps older than 300 seconds or matching previously seen nonces is rejected. Verified by unit test `test_replay_attack_prevention`.

---

### Vulnerability 4: Unrestricted Resource Consumption & Missing Rate Limiting
- **Affected Element**: `P1 / P2 / P3` (All Public API Endpoints).
- **Related STRIDE Threat**: `T05` (Denial of Service).
- **CWE Identifier**: **CWE-400** (Uncontrolled Resource Consumption) / **CWE-307** (Improper Restriction of Excessive Authentication Attempts).
- **Vulnerability Mechanism**: Endpoints lack request quotas, allowing single clients to flood the server.
- **Impact**: Server worker starvation, high CPU utilization, service degradation, and vulnerability to brute-force credential stuffing.
- **Mitigation & Evidence**: Custom sliding-window **Token Bucket Rate Limiting Middleware** in [`rate_limiter.py`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/backend/app/rate_limiter.py). Automatically limits IP addresses to 100 req/min and returns HTTP 429 Too Many Requests. Verified by test `test_api_rate_limiting`.

---

### Vulnerability 5: Broken Object-Level Authorization & RBAC Bypass
- **Affected Element**: `P3: Authorization Service` / `EE2 / EE3`.
- **Related STRIDE Threat**: `T06` (Elevation of Privilege).
- **CWE Identifier**: **CWE-285** (Improper Authorization).
- **Vulnerability Mechanism**: Endpoints verifying token validity but failing to enforce specific role permissions for sensitive operations.
- **Impact**: Field drivers can invoke administrative APIs to view security audit logs, reconfigure city-wide parameters, or access other users' data.
- **Mitigation & Evidence**: Declarative dependency injection via `require_role(UserRole.ADMIN)` on administrative routes, restricting drivers exclusively to assigned route waypoints. Tested in `test_security_and_intelligence.py`.

---

### Vulnerability 6: Insecure Container Configuration & Root Execution
- **Affected Element**: `Deployment Environment` / `Host Infrastructure`.
- **Related STRIDE Threat**: `T11` (Elevation of Privilege).
- **CWE Identifier**: **CWE-250** (Execution with Unnecessary Privileges).
- **Vulnerability Mechanism**: Default container images executing as the root user (`UID 0`) with default Linux capabilities.
- **Impact**: A vulnerability in a runtime dependency (e.g., Python standard library or web server) could allow container escape to the host node.
- **Mitigation & Evidence**: Multi-stage Docker build creating a dedicated unprivileged user (`appuser`, UID 10001) in [`docker/Dockerfile`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/docker/Dockerfile). Kubernetes manifests in [`k8s/deployment.yaml`](file:///c:/Users/Yeshwanth%20Raj/Desktop/SSE-END/k8s/deployment.yaml) enforce `runAsNonRoot: true`, `drop: ["ALL"]`, and a read-only root filesystem.
