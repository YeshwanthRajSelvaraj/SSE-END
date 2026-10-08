# ♻️ EcoSmart: Zero-Trust Smart Waste Management & Logistics Platform

[![Secure CI/CD Pipeline](https://github.com/YeshwanthRajSelvaraj/SSE-END/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YeshwanthRajSelvaraj/SSE-END/actions/workflows/ci-cd.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Security Standards](https://img.shields.io/badge/Compliance-OWASP%20ASVS%20%7C%20NIST%20Zero--Trust-green.svg)](https://owasp.org/)
[![AI Powered](https://img.shields.io/badge/AI-Google%20Gemini%203.1%20Flash--Lite-orange.svg)](https://ai.google.dev/)

**EcoSmart** is an enterprise-grade, secure IoT and AI-driven municipal waste management system engineered according to rigorous Secure Software Engineering (SSE) and DevSecOps principles. Designed for modern smart cities, it combines hardware sensor trust, cryptographic telemetry verification, zero-trust RBAC/BOLA defenses, automated vehicle route optimization, and multi-modal AI waste classification powered by Google Gemini.

---

## 📑 Table of Contents
1. [System Architecture](#-system-architecture)
2. [Key Capabilities & Modules](#-key-capabilities--modules)
3. [End-to-End Security Framework](#-end-to-end-security-framework)
4. [Google Gemini AI Intelligence](#-google-gemini-ai-intelligence)
5. [Repository Structure](#-repository-structure)
6. [Quick Start & Local Deployment](#-quick-start--local-deployment)
7. [Automated Testing & Security Validation](#-automated-testing--security-validation)
8. [DevSecOps CI/CD Pipeline](#-devsecops-cicd-pipeline)
9. [Artifacts & Phase Deliverables](#-artifacts--phase-deliverables)

---

## 🏛️ System Architecture

```
                                  +------------------------------------+
                                  |     Edge IoT Smart Bins            |
                                  | (Fill Level, Temp, GPS, Tamper)    |
                                  +-----------------+------------------+
                                                    | HMAC-SHA256 Signed
                                                    | Nonce + Timestamp
                                                    v
                                  +------------------------------------+
                                  |    Secure Ingestion Gateway        |
                                  | (Rate Limiter, Replay Defense)     |
                                  +-----------------+------------------+
                                                    |
                                                    v
+-----------------------+         +------------------------------------+         +-----------------------+
|  Hardware Sensor      |<------->|    Central Security Engine         |<------->|  Google Gemini 3.1    |
|  Trust & Lifecycle    |         | (BOLA, RBAC, Device Quarantine)    |         |  Flash-Lite AI Engine |
+-----------------------+         +-----------------+------------------+         +-----------------------+
                                                    |
                                                    v
+-----------------------+         +------------------------------------+         +-----------------------+
|  GIS & Fleet Route    |<------->|     FastAPI Enterprise Backend     |<------->|  Real-Time HTML5/JS   |
|  Hash Integrity Verif |         |    (SQLAlchemy ORM + SQLite/PG)    |         |  Operations Dashboard |
+-----------------------+         +------------------------------------+         +-----------------------+
```

---

## 🚀 Key Capabilities & Modules

- **Cryptographic Telemetry Ingestion**: Telemetry payloads must be authenticated using device-unique HMAC-SHA256 signatures over concatenated payload states with replay protection.
- **Hardware Sensor Trust & Fault Engine**: Detects sensor drift, flatlined sensor telemetry (stuck-at faults), impossible fill deltas, and cross-correlates weight-to-volume density.
- **Geofencing & GPS Spoofing Defenses**: Validates latitude/longitude against municipal bounds (Chennai geo-boundary) and calculates Haversine distance to detect impossible physical travel (>120 km/h).
- **Device Lifecycle Management**: Full support for administrative quarantine, credential rotation, and key revocation for compromised edge hardware.
- **Dynamic Route Optimization**: Computes critical fill priority collection routes with cryptographic SHA-256 state signatures to prevent in-transit driver tampering or redirection.
- **Multi-Role Operations Portal**: Granular access control for 8 distinct roles:
  - System Administrator
  - Waste Operations Manager
  - Security Analyst
  - Fleet Dispatcher
  - Maintenance Technician
  - Municipal Driver
  - Environmental Auditor
  - Field Inspector

---

## 🛡️ End-to-End Security Framework

The system implements security controls derived from NIST SP 800-207 Zero Trust and OWASP ASVS:

| Threat / Vulnerability | OWASP / CWE Category | Defense Implementation |
| :--- | :--- | :--- |
| **SQL Injection** | CWE-89 | Parameterized ORM queries via SQLAlchemy. Raw string interpolation completely eliminated. |
| **Broken Object-Level Auth (BOLA)** | OWASP API1:2023 | Strict role ownership and entity boundary checks on bin, route, and audit logs. |
| **Sensor Spoofing & Replay Attacks** | CWE-294 / CWE-347 | HMAC-SHA256 device key signatures, 5-minute sliding replay tolerance windows, nonce cache. |
| **GPS Impossible Travel** | CWE-345 | Haversine velocity evaluation rejecting impossible physical hardware jumps. |
| **Clickjacking** | CWE-1021 | Strict HTTP headers: `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'`. |
| **Code Smells & Technical Debt** | Clean Code / Phase 12 | Decomposed monoliths, separated concerns into dedicated micro-modules, removed duplicate blocks. |

---

## 🤖 Google Gemini AI Intelligence

Powered by **`gemini-3.1-flash-lite`**, the platform delivers real-time AI security and operations assistance:

1. **Autonomous Waste Classification (`POST /api/ai/classify`)**:
   - Classifies waste into 9 streams (Organic, Recyclable Plastic, Paper, Glass, Metal, Hazardous, E-Waste, Biomedical, General Residual).
   - Flags hazardous and biomedical contamination with safety handling protocols.
2. **Automated Threat Intelligence (`POST /api/ai/analyze-threat`)**:
   - Evaluates security events (e.g. replay attacks, brute force, signature mismatches) and provides mitigation recommendations.
3. **Conversational Copilot (`POST /api/ai/chat`)**:
   - Role-conditioned assistant guiding municipal staff and field dispatchers with real-time telemetry analysis.

---

## 📁 Repository Structure

```
SSE-END/
├── backend/
│   ├── app/
│   │   ├── anti_spoofing.py         # Replay defense, signature verification, rate limiting
│   │   ├── auth.py                  # JWT authentication, Argon2/bcrypt password hashing
│   │   ├── config.py                # Environment configuration loader (zero hardcoded secrets)
│   │   ├── database.py              # Database engine & session maker
│   │   ├── device_registry.py       # Hardware lifecycle, quarantine, and key rotation
│   │   ├── gemini_agent.py          # Gemini 3.1 Flash-Lite AI integration engine
│   │   ├── location_security.py     # Geofence boundary & Haversine impossible travel validator
│   │   ├── main.py                  # FastAPI REST API routing & middleware
│   │   ├── models.py                # SQLAlchemy relational database models
│   │   ├── rate_limiter.py          # Token bucket IP rate limiting
│   │   ├── route_optimizer.py       # Priority routing with cryptographic tamper validation
│   │   ├── schemas.py               # Pydantic input/output validation models
│   │   ├── security_engine.py       # Central security event audit logging
│   │   ├── sensor_trust.py          # Sensor health, flatline fault, and density correlation
│   │   └── waste_classifier.py     # 9-stream waste categorization & contamination triage
│   ├── refactoring/
│   │   ├── before_vulnerable.py     # Pre-refactored vulnerable code baseline (CWE demonstrations)
│   │   └── after_secured.py         # Refactored, parameterized, cryptographically hardened module
│   └── tests/
│       ├── fuzz_test.py             # API boundary fuzzing & injection test suite
│       ├── test_integration.py      # End-to-end API integration tests
│       ├── test_refactoring.py      # Comparative security & regression tests
│       ├── test_security_and_intelligence.py # Zero-trust security & AI verification tests
│       └── test_unit.py             # Cryptography & unit test suite
├── diagrams/                        # Draw.io architectural models (UML, STRIDE, Dataflow)
├── docker/
│   ├── Dockerfile                   # Hardened multi-stage non-root container image
│   └── docker-compose.yml           # Local multi-container orchestration
├── docs/
│   ├── specifications/              # Academic exam briefs, SRS, and refactoring guidelines
│   └── phase_*.md                   # Phases 7, 10, 11, 12, 13, 14 comprehensive reports
├── evidence/
│   ├── recordings/                  # Browser recordings of GIS map & area search demo
│   └── screenshots/                 # High-resolution operations & evidence screenshots
├── frontend/                        # Operations Portal (HTML5, Vanilla CSS, JS)
├── k8s/                             # Kubernetes manifests (Deployment, Service, Secret, HPA)
├── reports/                         # PDF & HTML Capstone Deliverables (Phases 1–16)
├── scripts/                         # Verification, secret scanning, and Jira sync utilities
├── .gitignore                       # Enterprise exclusion rules (secrets, binaries, logs)
└── pytest.ini                       # Test execution configuration
```

---

## ⚡ Quick Start & Local Deployment

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Clone & Setup
```bash
git clone https://github.com/YeshwanthRajSelvaraj/SSE-END.git
cd SSE-END
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Create a local `.env` file in the root folder:
```env
SECRET_KEY=generate_a_secure_hex_secret_here
HMAC_SECRET=generate_a_secure_hmac_secret_here
DATABASE_URL=sqlite:///./waste_management.db
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

### 4. Database Seeding & Startup
```bash
# Seed initial users, smart bins, and test data
python backend/app/seed.py

# Start Backend API Server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload

# Start Frontend Portal (in a separate terminal)
cd frontend
python -m http.server 3000
```
Open your browser at **`http://localhost:3000`** to access the operations dashboard.

---

## 🧪 Automated Testing & Security Validation

Execute the full automated test suite (33 tests covering unit, integration, refactoring, and security intelligence):

```bash
pytest -v
```

### Static Analysis Security Testing (Bandit)
```bash
bandit -r backend/app -ll
bandit -r backend/refactoring/after_secured.py -ll
```

### Secret Leak Prevention Scanner
```bash
python scripts/scan_secrets.py
```

### Security Boundary Fuzz Testing
```bash
python backend/tests/fuzz_test.py
```

---

## 🔄 DevSecOps CI/CD Pipeline

The GitHub Actions workflow ([`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)) runs on every push and pull request:
1. **Secret Scanning**: Runs custom regex engine detecting leaked keys, tokens, and credentials.
2. **SAST Scan (Bandit)**: Validates Python code against CWE vulnerabilities.
3. **Automated Testing (Pytest)**: Runs the complete 33-test suite across unit, integration, and security layers.
4. **Boundary Fuzzing**: Executes live fuzzing tests against API telemetry endpoints.
5. **Container Build & Trivy Vulnerability Scan**: Builds the Docker container and scans for OS/library vulnerabilities.
6. **Artifact Generation**: Packages deployment bundles for Kubernetes production staging.

---

## 📜 Academic Compliance & Project Context
- **Course**: 24CYS401 – Secure Software Engineering
- **Phase 7**: Threat Modeling & Security Architecture
- **Phase 9 & 10**: Agile Project Management & Jira Scrum Metrics
- **Phase 11**: Secure Development & Environment Hardening
- **Phase 12**: Secure Coding, Code Smell Remediation & Refactoring
- **Phase 13**: Docker Containerization & Kubernetes Orchestration
- **Phase 14**: Automated CI/CD & DevSecOps Security Gates
