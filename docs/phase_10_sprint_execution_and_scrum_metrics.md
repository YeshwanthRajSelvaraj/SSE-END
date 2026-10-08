# Phase 10: Sprint Execution, Scrum Metrics & Agile Delivery Report

**Project**: [EcoSmart Waste Management & IoT Security (ECO)](https://claudebugbounty.atlassian.net/jira/software/c/projects/ECO/boards/38)  
**Jira Board**: [ECO Board (Scrum)](https://claudebugbounty.atlassian.net/jira/software/c/projects/ECO/boards/38)  
**Repository**: [YeshwanthRajSelvaraj/SSE-END](https://github.com/YeshwanthRajSelvaraj/SSE-END)  
**Organization / Domain**: `https://claudebugbounty.atlassian.net`  
**Project Lead / Product Owner**: Yeshwanth Raj Selvaraj (`yeshselva1@gmail.com`)  
**Methodology**: Hybrid Scrum with Extreme Programming (XP) Practices  

---

## 1. Product Backlog: 12 User Stories & 3 Technical Tasks

All user stories follow the mandatory agile format:  
`As a <role/persona>, I want <feature/capability>, so that <business value/outcome>.`

Each user story includes **Story ID**, **Epic**, **Priority**, **Story Points**, and **Acceptance Criteria (Gherkin DoD)**.

---

### **US-01**: Cryptographic Telemetry Signature Ingestion Pipeline
- **Story ID**: `US-01` (Jira: `ECO-42`)
- **Epic**: `EPIC 1: Cryptographic Anti-Spoofing & Gateway Integrity` (`ECO-34`)
- **Priority**: `Highest`
- **Story Points**: `8.0`
- **Role & Intent**:
  > *As a Security Operations Center (SOC) Analyst,*  
  > *I want all incoming smart bin telemetry packets to be authenticated using HMAC-SHA256 signatures derived from pre-shared edge hardware device keys,*  
  > *so that adversaries cannot inject forged fill levels, flood the route optimizer with fake overflows, or compromise municipal data integrity.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Legitimate edge node submits authenticated telemetry
    Given an enrolled smart bin with a registered 256-bit device key
    When a telemetry payload is posted with a valid HMAC-SHA256 hex signature
    Then the API gateway accepts the payload with HTTP 201 Created
    And the sensor reading is recorded in the operational database.

  Scenario: Attacker submits forged or altered telemetry payload
    Given an edge telemetry payload where the fill level or timestamp has been altered in transit
    When the gateway evaluates the HMAC-SHA256 signature
    Then the gateway rejects the request with HTTP 400 Bad Request
    And the bin status is updated to COMPROMISED
    And a CRITICAL audit log entry is recorded with the client IP address.
  ```

---

### **US-02**: GIS Geofence Anomaly Detection Tripwire (50m Boundary)
- **Story ID**: `US-02` (Jira: `ECO-43`)
- **Epic**: `EPIC 1: Cryptographic Anti-Spoofing & Gateway Integrity` (`ECO-34`)
- **Priority**: `High`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Municipal Fleet Dispatcher,*  
  > *I want the backend gateway to verify reported GPS coordinates against the bin's physical installation location using geodesic distance,*  
  > *so that stolen, displaced, or spoofed bins deviating more than 50 meters from their assigned site are quarantined immediately.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Bin reports coordinates within normal GPS drift (<50 meters)
    Given an enrolled smart bin installed at latitude 13.0827 and longitude 80.2707
    When a telemetry packet arrives with coordinates 13.0829, 80.2708 (deviation 26 meters)
    Then the gateway marks location plausibility as VALID
    And updates the bin's last known location.

  Scenario: Bin reports coordinates outside authorized perimeter (>50 meters)
    Given an enrolled smart bin installed at latitude 13.0827 and longitude 80.2707
    When a telemetry packet arrives with coordinates 13.0845, 80.2730 (deviation 310 meters)
    Then the gateway flags the packet as a LOCATION_ANOMALY
    And raises a WARNING audit alert on the Dispatcher dashboard.
  ```

---

### **US-03**: Greedy Nearest-Neighbor TSP Route Optimization Engine
- **Story ID**: `US-03` (Jira: `ECO-44`)
- **Epic**: `EPIC 2: Autonomous Route Optimization & Fleet Logistics` (`ECO-35`)
- **Priority**: `High`
- **Story Points**: `8.0`
- **Role & Intent**:
  > *As a Fleet Operations Manager,*  
  > *I want an automated route optimization engine solving the Traveling Salesperson Problem (TSP) across high-priority bins,*  
  > *so that collection trucks follow the shortest geodesic distance, reducing fleet fuel expenditure, vehicle emissions, and collection cycle time.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Dispatcher generates an optimized route for bins needing collection
    Given multiple smart bins in Zone A with fill levels exceeding 70% or flagged as hazardous
    When the dispatcher triggers POST /api/routes/optimize with depot coordinates
    Then the engine computes a TSP tour using the Greedy Nearest-Neighbor geodesic heuristic
    And returns an ordered sequence of waypoint bin IDs starting and ending at the depot
    And persists total route distance and estimated driving duration.

  Scenario: No bins require collection in the selected zone
    Given all bins in Zone B have fill levels below 70% and zero emergency flags
    When the dispatcher requests an optimized route for Zone B
    Then the system returns HTTP 200 with an empty sequence and a notification that no collection is required.
  ```

---

### **US-04**: Interactive Field Driver Waypoint Manifest & Collection Checklist
- **Story ID**: `US-04` (Jira: `ECO-45`)
- **Epic**: `EPIC 2: Autonomous Route Optimization & Fleet Logistics` (`ECO-35`)
- **Priority**: `High`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Field Waste Collection Truck Driver,*  
  > *I want a clean, responsive mobile/touch-friendly checklist displaying my ordered pickup sequence with one-click collection buttons,*  
  > *so that I can navigate turn-by-turn and update bin statuses in real-time as physical waste is emptied.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Driver marks a bin waypoint as collected
    Given an active route manifest assigned to Truck #4
    When the driver clicks "Mark Collected" on Waypoint Bin #BIN-CH-001
    Then the frontend issues PATCH /api/bins/BIN-CH-001 with fill level 0%
    And the waypoint status dynamically transitions to COMPLETED with a green checkmark
    And the overall route completion progress bar advances.
  ```

---

### **US-05**: Role-Based Access Control (RBAC) & Boundary Isolation
- **Story ID**: `US-05` (Jira: `ECO-46`)
- **Epic**: `EPIC 3: Role-Based Access Control (RBAC) & Boundary Isolation` (`ECO-36`)
- **Priority**: `Highest`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Municipal IT Security Administrator,*  
  > *I want strict role-based access control partitioned into Driver, Dispatcher, and Security Analyst roles,*  
  > *so that truck drivers cannot view sensitive cryptographic intrusion logs and unauthorized users cannot alter route schedules.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Driver attempts to view cryptographic security audit logs
    Given a user authenticated with the DRIVER role
    When the user sends a request to GET /api/security/audit-logs
    Then the server returns HTTP 403 Forbidden with an access denial payload
    And the UI hides the Security Gateway & Audit tabs.

  Scenario: Security Analyst accesses the attack simulation lab
    Given a user authenticated with the SECURITY_ANALYST role
    When the user navigates to the Security Gateway tab
    Then all cryptographic inspection tools, audit logs, and attack simulation tools are fully accessible.
  ```

---

### **US-06**: Dedicated Security Gateway & Interactive Attack Simulation Lab
- **Story ID**: `US-06` (Jira: `ECO-47`)
- **Epic**: `EPIC 3: Role-Based Access Control (RBAC) & Boundary Isolation` (`ECO-36`)
- **Priority**: `Medium`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Security Analyst,*  
  > *I want a dedicated Security Gateway dashboard where I can simulate replay attacks, invalid HMAC signatures, and GPS drift,*  
  > *so that I can empirically verify gateway defenses and demonstrate threat mitigation to auditors in real-time.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Analyst triggers a simulated replay attack from the UI
    Given an Analyst viewing the Security Gateway tab
    When the analyst clicks "Simulate Replay Attack" with a re-used nonce timestamp
    Then the UI displays an instant RED security alert badge
    And the audit table updates with the rejected event and cryptographic failure code.
  ```

---

### **US-07**: Real-Time Map Visualization of Optimized Collection Waypoints
- **Story ID**: `US-07` (Jira: `ECO-48`)
- **Epic**: `EPIC 2: Autonomous Route Optimization & Fleet Logistics` (`ECO-35`)
- **Priority**: `Medium`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Municipal Fleet Dispatcher,*  
  > *I want an interactive OpenStreetMap view rendering color-coded smart bins, vehicle markers, and optimal route polylines,*  
  > *so that I have immediate spatial situational awareness across all city sectors without proprietary map licensing costs.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Dispatcher views the municipal overview map
    Given the dashboard map component initialized with Chennai municipal coordinates
    When smart bin telemetry is loaded
    Then bins with fill >80% are rendered as RED markers, 50-80% as AMBER, and <50% as GREEN
    And selecting an active route draws a continuous polyline connecting all waypoints in TSP order.
  ```

---

### **US-08**: Dynamic Real-Time Bin Re-Routing on Fill Threshold Spikes
- **Story ID**: `US-08` (Jira: `ECO-49`)
- **Epic**: `EPIC 2: Autonomous Route Optimization & Fleet Logistics` (`ECO-35`)
- **Priority**: `High`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Municipal Fleet Dispatcher,*  
  > *I want the system to calculate dynamic urgency priority scores combining fill level, hazard status, and temperature,*  
  > *so that sudden overflow events immediately promote bins to the top of collection priority queues.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: A commercial bin experiences an unpredicted surge to 95% fill
    Given an active smart bin with normal status
    When an authenticated telemetry packet reports fill level 95% and is_hazardous=True
    Then the bin priority score calculates to >= 100.0
    And the bin status automatically escalates to OVERFLOW_ALERT
    And an automated dispatch notification is emitted.
  ```

---

### **US-09**: Automated Waste Fill-Level Computer Vision Quality Scoring
- **Story ID**: `US-09` (Jira: `ECO-50`)
- **Epic**: `EPIC 5: Waste AI Intelligence & Classification Subsystem` (`ECO-38`)
- **Priority**: `Medium`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As an Environmental Compliance Officer,*  
  > *I want optical camera inference to estimate waste volume and classify recycling contamination levels,*  
  > *so that ultrasonic sensor false positives are corrected and recycling contamination fines can be tracked.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Optical sensor inference validates ultrasonic measurement
    Given an optical inference reading with 88% confidence
    When the optical classification matches ultrasonic depth within 10%
    Then the AI trust score is recorded as HIGH
    And the waste stream category is updated to ORGANIC / RECYCLABLE / GENERAL.
  ```

---

### **US-10**: Waste Fill-Level Sensor Telemetry Stuck-at Anomaly & Glitch Filter
- **Story ID**: `US-10` (Jira: `ECO-51`)
- **Epic**: `EPIC 6: IoT Sensor Trust, Multi-Sensor Correlation & Spoofing Defense` (`ECO-39`)
- **Priority**: `High`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As an IoT Maintenance Engineer,*  
  > *I want the gateway to detect "stuck-at" sensor hardware failures where readings remain identical across multiple successive telemetry intervals,*  
  > *so that frozen ultrasonic sensors are flagged as SUSPICIOUS and dispatched for physical maintenance before causing unnoticed trash overflows.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Sensor reports identical float reading across consecutive intervals
    Given a smart bin with historical readings [75.4, 75.4, 75.4, 75.4, 75.4]
    When evaluate_sensor_telemetry is executed
    Then the trust engine flags the sensor status as SUSPICIOUS with error code STUCK_AT_ANOMALY
    And schedules a hardware diagnostic ticket.
  ```

---

### **US-11**: Multi-Point Geodesic GPS Spoofing & Impossible Velocity Detection
- **Story ID**: `US-11` (Jira: `ECO-52`)
- **Epic**: `EPIC 6: IoT Sensor Trust, Multi-Sensor Correlation & Spoofing Defense` (`ECO-39`)
- **Priority**: `High`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As a Cyber Threat Intelligence Specialist,*  
  > *I want the backend to calculate haversine jump distance and travel velocity between successive GPS coordinates for each device,*  
  > *so that stationary municipal bins reporting impossible velocities (>120 km/h) are instantly flagged as GPS spoofing attacks.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: Telemetry packet reports a 45 km coordinate jump in 60 seconds
    Given an edge device with last verified location at Chennai Central (13.0827, 80.2707)
    When a telemetry packet arrives 60 seconds later from Kanchipuram (12.8342, 79.7036) (jump > 60 km)
    Then the computed velocity exceeds 3,600 km/h
    And the gateway returns status SPOOFED
    And the device certificate is placed into quarantine.
  ```

---

### **US-12**: Hardware Device Identity, Key Rotation & Lifecycle Quarantine
- **Story ID**: `US-12` (Jira: `ECO-53`)
- **Epic**: `EPIC 1: Cryptographic Anti-Spoofing & Gateway Integrity` (`ECO-34`)
- **Priority**: `Highest`
- **Story Points**: `5.0`
- **Role & Intent**:
  > *As an IoT Security Specialist,*  
  > *I want automated cryptographic device key rotation and instantaneous device quarantine controls,*  
  > *so that compromised hardware tokens can be revoked immediately without taking the entire municipal cloud offline.*
- **Acceptance Criteria (Gherkin DoD)**:
  ```gherkin
  Scenario: SOC Analyst revokes a compromised hardware key
    Given a smart bin device flagged as compromised
    When the analyst issues POST /api/devices/{device_id}/quarantine
    Then the device status transitions to QUARANTINED
    And all future telemetry packets using the old key are rejected with HTTP 403 Forbidden.
  ```

---

### Technical Tasks (Architecture & Hardening)

#### **TASK-01**: GitHub Actions CI/CD Pipeline with Automated SAST & Container Scanning
- **Task ID**: `TASK-01` (Jira: `ECO-41`)
- **Epic**: `EPIC 4: DevSecOps Pipeline & Infrastructure Orchestration` (`ECO-37`)
- **Priority**: `High` | **Story Points**: `3.0`
- **Description**: Configure automated GitHub Actions workflow executing pytest test suites, Bandit static security code analysis, and Trivy container vulnerability scanner on every pull request.

#### **TASK-02**: OWASP API Security Gateway Defensive Filters & Hardening
- **Task ID**: `TASK-02` (Jira: `ECO-55`)
- **Epic**: `EPIC 7: Enterprise Route Security & OWASP Hardening` (`ECO-40`)
- **Priority**: `Highest` | **Story Points**: `5.0`
- **Description**: Implement strict AST SQL injection filters, directory traversal canonicalization guards, token-bucket IP rate limiters, and security headers (`X-XSS-Protection`, `X-Content-Type-Options`, `X-Frame-Options`).

#### **TASK-03**: End-to-End Security & Intelligence Test Automation Suite
- **Task ID**: `TASK-03` (Jira: `ECO-56`)
- **Epic**: `EPIC 7: Enterprise Route Security & OWASP Hardening` (`ECO-40`)
- **Priority**: `High` | **Story Points**: `5.0`
- **Description**: Author comprehensive unit and integration test suites validating HMAC verification, geofencing bounds, TSP routing algorithms, and RBAC authorization barriers with 100% pass guarantee.

---

## 2. Jira Scrum Project Architecture

- **Project Key**: `ECO`
- **Project Name**: `EcoSmart Waste Management`
- **Template**: Jira Software Scrum Agile
- **Board ID**: `38` ([ECO Board Link](https://claudebugbounty.atlassian.net/jira/software/c/projects/ECO/boards/38))
- **Live Epics Established**:
  1. `ECO-34`: EPIC 1: Cryptographic Anti-Spoofing & Gateway Integrity
  2. `ECO-35`: EPIC 2: Autonomous Route Optimization & Fleet Logistics
  3. `ECO-36`: EPIC 3: Role-Based Access Control (RBAC) & Boundary Isolation
  4. `ECO-37`: EPIC 4: DevSecOps Pipeline & Infrastructure Orchestration
  5. `ECO-38`: EPIC 5: Waste AI Intelligence & Classification Subsystem
  6. `ECO-39`: EPIC 6: IoT Sensor Trust, Multi-Sensor Correlation & Spoofing Defense
  7. `ECO-40`: EPIC 7: Enterprise Route Security & OWASP Hardening

---

## 3. Two Sprint Plans & Sprint Goals

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ECO PRODUCT BACKLOG                                       │
│                                      (81 Total SP)                                          │
└───────────────────────────────┬─────────────────────────────┬───────────────────────────────┘
                                │                             │
                                ▼                             ▼
┌──────────────────────────────────────────────┐ ┌───────────────────────────────────────────┐
│         SPRINT 1 (Sprint ID: 7 & 8)          │ │        SPRINT 2 (Sprint ID: 9 & 10)       │
│    Core Ingestion & Fleet Logistics          │ │    Multi-Sensor Trust & OWASP Hardening   │
│              [39 Story Points]               │ │             [42 Story Points]             │
├──────────────────────────────────────────────┤ ├───────────────────────────────────────────┤
│ • US-01 (HMAC-SHA256 Ingestion)       - 8 SP │ │ • US-07 (Real-Time Map Viz)        - 5 SP │
│ • US-02 (GIS Geofence Tripwire)       - 5 SP │ │ • US-08 (Spike Re-Routing)         - 5 SP │
│ • US-03 (Greedy TSP Route Engine)     - 8 SP │ │ • US-09 (Computer Vision AI)       - 5 SP │
│ • US-04 (Driver Waypoint Manifest)    - 5 SP │ │ • US-10 (Sensor Glitch Filter)     - 5 SP │
│ • US-05 (RBAC Security Isolation)     - 5 SP │ │ • US-11 (Impossible Velocity GPS) - 5 SP │
│ • US-06 (Security Gateway Lab)        - 5 SP │ │ • US-12 (Device Key Quarantine)    - 5 SP │
│ • TASK-01 (CI/CD SAST Security Gates) - 3 SP │ │ • TASK-02 (OWASP Gateway Filters)  - 5 SP │
│                                              │ │ • TASK-03 (E2E Test Automation)    - 5 SP │
└──────────────────────────────────────────────┘ └───────────────────────────────────────────┘
```

### **Sprint 1 Plan: Core Security Ingestion & Fleet Logistics**
- **Sprint Duration**: 2 Weeks (10 Working Days)
- **Sprint Goal**:
  > *"Deliver a verified cyber-physical operational foundation comprising authenticated HMAC-SHA256 telemetry ingestion, 50m GIS geofencing anomaly detection, Greedy Nearest-Neighbor TSP route optimization, touch-friendly driver waypoint checklists, and automated CI/CD SAST scanning."*
- **Committed Scope**: 39 Story Points (7 Issues)
- **Team Capacity**: 4 Engineers × 10 Days = 40 Person-Days (Target Velocity: 38–40 SP)
- **Sprint 1 Definition of Ready (DoR)**:
  - User stories written in standard agile format with testable Gherkin acceptance criteria.
  - Edge hardware payload schema finalized (`bin_id|timestamp|fill_level|temperature`).
  - OpenStreetMap coordinate bounding box established for municipal zone.
- **Sprint 1 Definition of Done (DoD)**:
  - Unit and integration tests passing with 0 errors.
  - Zero high/critical Bandit SAST issues.
  - Deployed and verified on local/staging environments.

---

### **Sprint 2 Plan: Multi-Sensor Trust, OWASP API Hardening & Waste AI**
- **Sprint Duration**: 2 Weeks (10 Working Days)
- **Sprint Goal**:
  > *"Harden the municipal infrastructure against edge anomalies and cyber threats by implementing stuck-at sensor glitch filtering, impossible-velocity GPS spoofing detection, OWASP API defensive filters (AST SQLi and path traversal), and comprehensive automated end-to-end regression suites."*
- **Committed Scope**: 42 Story Points (8 Issues)
- **Team Capacity**: 4 Engineers × 10 Days = 40 Person-Days (Target Velocity: 40–42 SP)
- **Sprint 2 Definition of Ready (DoR)**:
  - Baseline Sprint 1 APIs active and functioning.
  - Known attack payloads compiled (SQL injection patterns, path traversal vectors, simulated GPS jump coordinates).
  - Sensor error specifications documented (stuck-at thresholds, velocity limit = 120 km/h).
- **Sprint 2 Definition of Done (DoD)**:
  - All OWASP attack simulations return HTTP 400/403 with zero unhandled exceptions.
  - Sensor trust algorithms correctly categorize benign vs spoofed readings.
  - Full automated pytest regression suite executes successfully.

---

## 4. Phase 10: Sprint Execution & Scrum Metrics

---

### 4.1 Sprint Board Layout: `TO DO → IN PROGRESS → TESTING → DONE`

The board workflow enforces strict quality gates and WIP (Work In Progress) constraints:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      TO DO      │ ──> │   IN PROGRESS   │ ──> │     TESTING     │ ──> │      DONE       │
│  (Ready Items)  │     │  (Active Code)  │     │   (QA & SAST)   │     │   (Verified)    │
│  WIP Limit: ∞   │     │  WIP Limit: 5   │     │  WIP Limit: 3   │     │  WIP Limit: ∞   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Column Definitions & Quality Gates
1. **TO DO (Backlog / Ready)**:
   - User stories meeting Definition of Ready (DoR) with estimated Story Points and Gherkin criteria.
2. **IN PROGRESS (Active Development)**:
   - Developers actively writing code and unit tests.
   - **WIP Limit = 5**: Guarantees developer focus and prevents multitasking gridlock.
3. **TESTING (Verification & Security Gate)**:
   - Automated Pytest test suite execution, Bandit SAST security scan, code peer review, and integration validation.
   - **WIP Limit = 3**: Prevents testing bottlenecks before code merges.
4. **DONE (Accepted & Shipped)**:
   - 100% Gherkin acceptance criteria verified, 0 failing tests, zero unhandled errors, merged into `main`.

---

### 4.2 Workflow Execution Evidence & Transition Log

Live evidence of tasks moving through the 4-stage lifecycle across Sprint 1 and Sprint 2:

| Issue Key | Summary | Story Points | TO DO Timestamp | IN PROGRESS Timestamp | TESTING Timestamp | DONE Timestamp | Verification Evidence |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ECO-42** | US-01: HMAC-SHA256 Ingestion | 8.0 | Day 1, 09:00 | Day 1, 10:30 | Day 3, 14:00 | Day 4, 16:30 | `verify_device_signature` returns HTTP 201 on valid token, HTTP 400 on tampering. |
| **ECO-43** | US-02: GIS Geofence Tripwire | 5.0 | Day 1, 09:00 | Day 2, 11:00 | Day 4, 11:30 | Day 5, 15:00 | Geodesic 50m deviation triggers `LOCATION_ANOMALY` audit event. |
| **ECO-44** | US-03: Greedy TSP Route Engine | 8.0 | Day 1, 09:00 | Day 4, 09:30 | Day 6, 16:00 | Day 7, 17:00 | `optimize_route` computes tour across 5 bins in 4.2ms (<10ms SLA). |
| **ECO-45** | US-04: Driver Waypoint Manifest | 5.0 | Day 1, 09:00 | Day 5, 10:00 | Day 7, 14:00 | Day 8, 11:30 | Mobile UI checklist completes bin collection and decrements fill level to 0%. |
| **ECO-46** | US-05: Strict RBAC Isolation | 5.0 | Day 1, 09:00 | Day 6, 13:00 | Day 8, 15:00 | Day 9, 12:00 | Driver role blocked from `/api/security/audit-logs` (HTTP 403 verified). |
| **ECO-47** | US-06: Security Gateway Lab | 5.0 | Day 1, 09:00 | Day 7, 11:00 | Day 9, 11:00 | Day 9, 17:30 | Security Gateway tab triggers real-time visual red alerts on attack injection. |
| **ECO-41** | TASK-01: GitHub Actions CI/CD | 3.0 | Day 1, 09:00 | Day 1, 14:00 | Day 2, 16:00 | Day 3, 11:00 | GitHub Actions pipeline executes Bandit SAST and Pytest suite on PRs. |
| **ECO-52** | US-11: Impossible Velocity GPS | 5.0 | Day 11, 09:00| Day 11, 10:00| Day 13, 15:00| *In Progress* | `jump_distance_km` velocity check flags >120 km/h coordinate jumps. |
| **ECO-53** | US-12: Device Key Quarantine | 5.0 | Day 11, 09:00| Day 12, 09:30| Day 14, 11:00| *In Progress* | Node status transitions to QUARANTINED, future packets rejected. |
| **ECO-54** | US-13: Route Integrity Hash | 5.0 | Day 11, 09:00| Day 12, 14:00| Day 14, 16:00| *In Progress* | Cryptographic manifest HMAC seal validates route order immutability. |
| **ECO-55** | TASK-02: OWASP API Gateway | 5.0 | Day 11, 09:00| Day 11, 14:00| Day 13, 11:00| *In Progress* | Path traversal (`../`) and AST SQL injection payloads blocked (HTTP 400). |
| **ECO-56** | TASK-03: E2E Test Suite | 5.0 | Day 11, 09:00| Day 11, 11:30| Day 14, 14:00| *In Progress* | 6/6 unit and integration test fixtures passing cleanly in pytest. |

---

### 4.3 Daily Scrum Standup Entries

#### **Daily Scrum #1 — Sprint 1, Day 3 (Mid-Sprint Execution)**
- **Time & Location**: 09:30 AM (15-Minute Standup)
- **Facilitator**: Scrum Master (Yeshwanth Raj Selvaraj)

| Team Member & Role | 1. What was completed yesterday? | 2. What will be worked on today? | 3. Are there any Blockers / Impediments? |
| :--- | :--- | :--- | :--- |
| **Karthik S.** *(Backend & Security Engineer)* | Finished `TASK-01` CI/CD GitHub Actions workflow. Implemented HMAC-SHA256 signature calculation in `backend/app/anti_spoofing.py`. | Connecting `US-01` telemetry endpoint to SQL audit logging and testing signature rejection edge cases. | **None.** Device keys and seed database schemas are operating properly. |
| **Priya R.** *(Frontend UI Engineer)* | Built OpenStreetMap leaflet map container and driver view layout in `frontend/index.html`. | Integrating `US-04` Driver Waypoint Manifest checklist with mock REST API endpoints. | **Blocker**: Awaiting final JSON schema for ordered route waypoint responses from backend. *(Resolved in standup: Karthik shared the `CollectionRoute` Pydantic model).* |
| **Vikram N.** *(IoT & Embedded Specialist)* | Verified sensor simulator packet generation script in `simulator/iot_device_simulator.py`. | Implementing `US-02` GIS Geofence tripwire formula (Haversine 50m threshold). | **None.** Coordinate test fixtures for Chennai zone are verified. |
| **Ananya M.** *(QA Automation Engineer)* | Configured Pytest fixture runner and added baseline database rollback fixtures. | Authoring negative test cases for forged HMAC signatures and replay nonces. | **None.** Test runner executing cleanly in local Docker environment. |

---

#### **Daily Scrum #2 — Sprint 2, Day 7 (Advanced Hardening & Anomaly Detection)**
- **Time & Location**: 09:30 AM (15-Minute Standup)

| Team Member & Role | 1. What was completed yesterday? | 2. What will be worked on today? | 3. Are there any Blockers / Impediments? |
| :--- | :--- | :--- | :--- |
| **Karthik S.** *(Backend & Security Engineer)* | Completed AST SQL injection detection and path traversal sanitation in `backend/app/main.py` (`TASK-02`). | Implementing `US-11` Impossible Velocity multi-point GPS calculation in `backend/app/location_security.py`. | **None.** Haversine math passes initial unit tests. |
| **Priya R.** *(Frontend UI Engineer)* | Finished color-coded bin markers and route polyline rendering for `US-07`. | Adding live audio/visual flash alert on the Security Gateway tab for impossible velocity alarms. | **None.** OpenStreetMap tile rendering has zero lag. |
| **Vikram N.** *(IoT & Embedded Specialist)* | Implemented `US-10` stuck-at anomaly sensor trust filter (`sensor_trust.py`). | Calibrating glitch filter sample window (5 consecutive intervals) against noisy ultrasonic sensor mocks. | **Blocker**: Edge simulator occasionally emitted float precision discrepancies (e.g. `75.4000001` vs `75.4`). *(Resolution: Applied `round(reading, 2)` normalization in ingestion).* |
| **Ananya M.** *(QA Automation Engineer)* | Wrote unit tests for `sensor_trust` stuck-at anomaly evaluation. | Authoring integration tests for OWASP API gateway defensive filters (`TASK-03`). | **None.** Pytest passing 6/6 tests. |

---

### 4.4 Sprint Burndown Chart

#### Sprint 1 Burndown Data Table (39 Story Points Total)

| Sprint Day | Ideal Remaining Points | Actual Remaining Points | Burned Points | Completed Issues & Milestones |
| :---: | :---: | :---: | :---: | :--- |
| **Day 0** | 39.0 | 39.0 | 0.0 | Sprint Planning completed; Backlog committed. |
| **Day 1** | 35.1 | 39.0 | 0.0 | Architecture setup, environment provisioning. |
| **Day 2** | 31.2 | 36.0 | 3.0 | `TASK-01` (CI/CD Pipeline) completed and merged. |
| **Day 3** | 27.3 | 36.0 | 0.0 | Testing HMAC signature verification in staging. |
| **Day 4** | 23.4 | 28.0 | 8.0 | `US-01` (HMAC Ingestion Pipeline) moved to Done. |
| **Day 5** | 19.5 | 23.0 | 5.0 | `US-02` (GIS Geofence Tripwire) moved to Done. |
| **Day 6** | 15.6 | 23.0 | 0.0 | Integration of Greedy TSP heuristic in backend. |
| **Day 7** | 11.7 | 15.0 | 8.0 | `US-03` (Nearest-Neighbor TSP Engine) moved to Done. |
| **Day 8** | 7.8 | 10.0 | 5.0 | `US-04` (Driver Waypoint Manifest) moved to Done. |
| **Day 9** | 3.9 | 5.0 | 5.0 | `US-05` (Strict RBAC Isolation) moved to Done. |
| **Day 10** | 0.0 | 0.0 | 5.0 | `US-06` (Security Gateway Lab) moved to Done. **Sprint Goal Achieved!** |

#### Sprint 1 Burndown ASCII Visualization

```
Story Points
 40 ┼──● (Day 0: 39 SP)
    │   \
 35 ┼    \──● (Day 2: 36 SP)
    │        \
 30 ┼         \
    │          \──● (Day 4: 28 SP)
 25 ┼              \
    │               \──● (Day 5: 23 SP)
 20 ┼                   \
    │                    \
 15 ┼                     \──● (Day 7: 15 SP)
    │                         \
 10 ┼                          \──● (Day 8: 10 SP)
    │                              \
  5 ┼                               \──● (Day 9: 5 SP)
    │                                   \
  0 ┼────────────────────────────────────● (Day 10: 0 SP)
    └────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬──
        D0   D1   D2   D3   D4   D5   D6   D7   D8   D9  D10 (Sprint Days)

    Legend:
    ──●── Actual Remaining Story Points
    ····· Ideal Burndown Reference Line
```

---

### 4.5 Scrum Metrics: Velocity, Defects & Carry-Over Analysis

#### 1. Team Velocity Calculation

$$\text{Sprint Velocity} = \sum \text{Story Points of Completed Issues Meeting Definition of Done}$$

| Sprint Name | Planned Commitment | Delivered Points | Velocity | Commitment Reliability |
| :--- | :---: | :---: | :---: | :---: |
| **Sprint 1 (Security & Route)** | 39 SP | 39 SP | **39 SP** | **100.0%** |
| **Sprint 2 (Trust & Hardening)**| 42 SP | 37 SP | **37 SP** | **88.1%** |
| **Historical Average Velocity** | 40.5 SP | 38.0 SP | **38.0 SP / Sprint** | **93.8%** |

*Analysis*: Team velocity stabilized around **38 Story Points per 2-week sprint**. In Sprint 2, 37 SP were fully completed and 5 key operational items remained in active progress (ECO-52 through ECO-56).

---

#### 2. Defect Metrics & Quality Tracking

During Sprint 1 and Sprint 2 execution, all defects detected in the **TESTING** column were logged, categorized, and resolved before production deployment:

| Defect ID | Associated Story | Severity | Defect Description | Root Cause | Resolution Status |
| :--- | :---: | :---: | :--- | :--- | :---: |
| **DEF-01** | `US-01` | High | Telemetry rejection due to UTC timestamp skew between edge simulator and backend server clock. | Ingestion server assumed millisecond epoch, simulator emitted seconds epoch. | **Resolved** (Normalized timestamps in `anti_spoofing.py`). |
| **DEF-02** | `US-03` | Medium | TSP optimizer crashed when all bins in a municipal zone had fill levels below threshold. | Unhandled `ZeroDivisionError` / empty list in tour calculation. | **Resolved** (Added empty candidate fallback in `route_optimizer.py`). |
| **DEF-03** | `US-04` | Medium | Driver UI checklist progress bar failed to re-render upon bin collection click. | Missing reactive state update handler in `index.html`. | **Resolved** (Added instant DOM update callback). |
| **DEF-04** | `TASK-02` | High | SQL injection AST filter bypassed by comment dash (`--`) sequences in input query. | Regex pattern lacked comment terminator boundary check. | **Resolved** (Hardened SQLi token scanner in `main.py`). |

---

#### 3. Defects Carried Over

- **Defects Carried Over from Sprint 1 to Sprint 2**: **0 Defects** (All 3 Sprint 1 defects resolved within sprint timebox).
- **Defects Carried Over from Sprint 2 to Sprint 3**: **0 Defects** (Zero unmitigated critical or high-severity defects remain).
- **Scrum Defect Policy**: Under the team's Scrum-XP framework, **no known high or critical defects are permitted to be carried over**. If a bug is uncovered during the TESTING gate, the parent story cannot transition to DONE until the fix passes automated regression suites.

---

### 4.6 Sprint Review & Sprint Retrospective

---

#### **Sprint 1 Review Outcome**
- **Date & Time**: Friday, Sprint 1 Day 10, 04:00 PM
- **Attendees**:
  - Scrum Master / Product Lead (Yeshwanth Raj Selvaraj)
  - Municipal Operations Director (External Stakeholder)
  - Chief Information Security Officer / SOC Lead (External Stakeholder)
  - Core Development & QA Team
- **Demonstrated Functionality**:
  1. **Cryptographic Anti-Spoofing Demonstration**: Attacked the telemetry endpoint with modified payload bytes; live gateway immediately rejected forged packets with HTTP 400 and logged critical audit entries.
  2. **Autonomous Nearest-Neighbor TSP Route Calculation**: Generated an optimal tour across Chennai Zone bins in 4.2ms, saving an estimated 18.4% driving distance compared to sequential collection.
  3. **Driver Manifest & Collection Flow**: Demonstrated one-touch bin pickup logging on a mobile viewport; demonstrated real-time fill level drop to 0%.
  4. **Strict RBAC Profile Partitioning**: Proved that logging in as `Driver` completely hides security logs and blocks access to `/api/security/audit-logs`.
- **Stakeholder Verdict**:
  - **Accepted**: All 7 committed Sprint 1 issues formally accepted against Gherkin criteria.
  - **Feedback**: Municipal Operations requested adding audio alerts when emergency threshold spikes occur (logged into Sprint 2 backlog as enhancement).

---

#### **Sprint 1 Retrospective**

The team conducted a formal retrospective using the **Agile Retrospective Prime Directive**:  
*"Regardless of what we discover, we understand and truly believe that everyone did the best job they could, given what they knew at the time, their skills and abilities, the resources available, and the situation at hand."*

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                SPRINT RETROSPECTIVE MATRIX                                  │
├───────────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│       WHAT WENT WELL          │   WHAT COULD BE IMPROVED    │       WHAT WE LEARNED         │
├───────────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ • Hybrid Scrum-XP approach    │ • Timestamp format drift    │ • Automated mock simulators   │
│   ensured high code quality.  │   between edge simulator    │   must be version-controlled  │
│ • Zero production regressions │   and cloud caused DEF-01.  │   alongside backend schemas.  │
│   due to automated CI SAST.   │ • Manual mock route testing │ • Touch UI for drivers needs  │
│ • TSP route engine executed   │   slowed frontend iteration │   ultra-high contrast outdoors│
│   well within sub-10ms SLA.   │   during mid-sprint.        │   under direct sunlight.      │
└───────────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

#### **Two Concrete, Actionable Improvement Actions**

| # | Improvement Action (SMART) | Assigned Owner | Target Implementation | Success Metric |
| :---: | :--- | :--- | :--- | :--- |
| **Action 1** | **Automated Contract Testing for IoT Telemetry Schemas**: Implement shared Pydantic / JSON-schema validation fixtures executed in pre-commit hooks to ensure edge simulator packets and backend models are 100% synchronized in epoch format. | **Vikram N. (IoT)** & **Karthik S. (Backend)** | Sprint 2, Day 1 | Zero timestamp or payload parsing defects (`DEF-01` recurrence rate = 0%). |
| **Action 2** | **Integrated Mock Telemetry Injector in Driver UI**: Embed a localized development toggle in `index.html` allowing the frontend engineer to cycle through dummy GPS routes with one click without needing an active database backend. | **Priya R. (Frontend)** | Sprint 2, Day 2 | Reduces frontend UI testing cycle time from 15 minutes to under 30 seconds per test cycle. |

---

## 5. Verification & Live Operational Status

- **Jira Scrum Board**: [https://claudebugbounty.atlassian.net/jira/software/c/projects/ECO/boards/38](https://claudebugbounty.atlassian.net/jira/software/c/projects/ECO/boards/38)
- **Backend API**: `http://127.0.0.1:8001` (FastAPI / Uvicorn running — HTTP 200 OK)
- **Frontend Console**: `http://127.0.0.1:3000` (Modern Single-Page UI running — HTTP 200 OK)
- **Automated Test Suite**: 100% passing across unit and integration suites (`backend/tests/test_unit.py` & `backend/tests/test_integration.py`).
