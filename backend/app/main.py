"""
FastAPI Main Application
Includes API endpoints, middleware, and exception handling.
Preserves 100% of existing baseline endpoints and contracts while integrating:
- Hierarchical Waste Classification & Contamination APIs
- Waste Composition Analytics APIs
- Device Authentication & Registry APIs
- Sensor Health & Location Integrity APIs
- Central Security Events & Threat Metrics APIs
- Route Integrity Verification & Authorized Modification APIs
- OWASP Security Controls (CSP, XSS, SQLi, Path Traversal, SSRF, BOLA)
"""
import time
import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db, init_db
from app.config import settings
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role, log_audit
)
from app.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    SmartBinCreate, SmartBinResponse, SensorReadingCreate, SensorReadingResponse,
    RouteCreate, RouteResponse, VehicleCreate, VehicleResponse, DriverCreate, DriverResponse,
    AssignmentCreate, AssignmentResponse,
    WasteClassificationRequest, WasteClassificationResponse,
    BinContaminationResponse, BinCompositionResponse,
    DeviceRegistryCreate, DeviceRegistryUpdate, DeviceRegistryResponse,
    SensorHealthResponse, LocationIntegrityResponse,
    SecurityEventResponse, RouteIntegrityResponse
)
from app.models import (
    User, UserRole, SmartBin, SensorReading, Vehicle, Driver,
    CollectionRoute, RouteAssignment, AuditLog, AuditAction,
    DeviceRegistryItem, DeviceStatus, SensorHealthRecord, LocationIntegrityRecord,
    WasteClassificationRecord, BinContaminationRecord, BinCompositionRecord,
    SecurityEventRecord, RouteAuditVersion
)
from app.anti_spoofing import process_telemetry_security
from app.route_optimizer import (
    optimize_route, verify_route_integrity, modify_route_authorized
)
from app.rate_limiter import rate_limit_ip
from app.waste_classifier import (
    classify_waste_item, recalculate_bin_composition,
    TAXONOMY_LEVEL1, TAXONOMY_LEVEL2_RECYCLABLE, TAXONOMY_LEVEL3_MAP,
    calculate_waste_density_and_correlate
)
from app.device_registry import (
    register_device, quarantine_device, revoke_device,
    rotate_device_credentials
)
from app.security_engine import (
    emit_security_event, detect_sqli_payload, detect_xss_payload,
    safe_canonical_path, validate_url_for_ssrf, check_object_authorization
)

logger = logging.getLogger("main_app")

# Initialize Database
init_db()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# Security Middleware - CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_and_rate_limit(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    # 1. Payload Size Check (Availability / DoS Defense)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload exceeds maximum allowed size limit of 10MB"}
        )

    # 2. Sliding Window Rate Limiting
    try:
        rate_limit_ip(client_ip)
    except HTTPException as exc:
        db = next(get_db())
        try:
            emit_security_event(
                db=db,
                event_type="RATE_LIMIT_EXCEEDED",
                severity="WARNING",
                ip_address=client_ip,
                reason="Client exceeded request threshold rate limit",
                action_taken="HTTP_429_THROTTLED"
            )
        finally:
            db.close()
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # 3. Request Parameter Threat Inspection (SQLi / XSS scanning on query strings)
    query_str = str(request.url.query)
    if query_str:
        if detect_sqli_payload(query_str):
            db = next(get_db())
            try:
                emit_security_event(
                    db=db,
                    event_type="SQL_INJECTION_ATTEMPT",
                    severity="CRITICAL",
                    ip_address=client_ip,
                    resource=request.url.path,
                    reason=f"SQL injection heuristic triggered on query parameter: {query_str[:80]}",
                    action_taken="REQUEST_BLOCKED_400"
                )
            finally:
                db.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Malicious payload detected: SQL injection pattern attempt blocked."}
            )


        if detect_xss_payload(query_str):
            db = next(get_db())
            try:
                emit_security_event(
                    db=db,
                    event_type="XSS_ATTEMPT",
                    severity="HIGH",
                    ip_address=client_ip,
                    resource=request.url.path,
                    reason=f"Cross-site scripting heuristic triggered on query parameter: {query_str[:80]}",
                    action_taken="REQUEST_BLOCKED_400"
                )
            finally:
                db.close()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Malicious payload detected: XSS injection attempt blocked."}
            )

    response = await call_next(request)

    # 4. Comprehensive Defense-in-Depth Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https:; frame-ancestors 'none'; object-src 'none';"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response



# ── Global Safe Exception Handler ───────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log raw exception internally, but never leak stack trace or internal paths to client
    logger.error(f"Internal server error processing {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred while processing your request."}
    )


# ── Auth Endpoints (Preserved Baseline) ──────────────────────────────────────

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_pwd = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        role=UserRole(user.role)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log_audit(db, AuditAction.LOGIN, new_user.id, "User", new_user.username, "User registered")
    return new_user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(user: UserLogin, request: Request, db: Session = Depends(get_db)):
    login_identifier = user.username.strip()
    db_user = db.query(User).filter(
        (User.username == login_identifier) | (User.email == login_identifier)
    ).first()
    ip = request.client.host if request.client else "unknown"
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        log_audit(db, AuditAction.LOGIN_FAILED, None, "User", login_identifier, "Failed login attempt", ip, "WARNING")
        emit_security_event(
            db=db,
            event_type="AUTH_FAILURE",
            severity="WARNING",
            ip_address=ip,
            user_or_device_id=login_identifier,
            reason="Invalid credentials on login",
            action_taken="LOGIN_REJECTED"
        )
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
        
    access_token = create_access_token(data={"sub": db_user.username, "role": db_user.role.value})
    log_audit(db, AuditAction.LOGIN, db_user.id, "User", db_user.username, "Successful login", ip)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": db_user.role.value,
        "username": db_user.username,
        "email": db_user.email
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/auth/profiles")
def get_auth_profiles():
    return {
        "profiles": [
            {
                "id": "admin",
                "name": "System Administrator",
                "role": "admin",
                "badge": "SUPER ADMIN",
                "username": "admin",
                "email": "admin@ecosmart.local",
                "modules": ["Dashboard", "Live Telemetry Map", "Optimized Routes", "Intrusion Logs", "Security Center", "Security Gateway Lab"],
                "description": "Full access to all 6 enterprise modules, cryptographic controls, and administration."
            },
            {
                "id": "operator",
                "name": "Operations Dispatcher",
                "role": "operator",
                "badge": "OPERATOR",
                "username": "operator",
                "email": "operator@ecosmart.local",
                "modules": ["Dashboard", "Live Telemetry Map", "Optimized Routes", "Security Center"],
                "description": "Fleet logistics, TSP route dispatch, vehicle assignments, and real-time GIS monitoring."
            },
            {
                "id": "driver",
                "name": "Rajesh Kumar (Field Driver)",
                "role": "driver",
                "badge": "DRIVER",
                "username": "driver",
                "email": "driver@ecosmart.local",
                "modules": ["Optimized Routes"],
                "description": "Assigned route waypoints, driver manifest checklist, and bin collection completion."
            },
            {
                "id": "analyst",
                "name": "SOC Security Analyst",
                "role": "analyst",
                "badge": "ANALYST",
                "username": "analyst",
                "email": "analyst@ecosmart.local",
                "modules": ["Intrusion Logs", "Security Center", "Security Gateway Lab", "Dashboard", "Live Telemetry Map"],
                "description": "Real-time intrusion detection, HMAC-SHA256 signature verification, and edge security lab."
            }
        ]
    }


# ── IoT Telemetry Endpoints (Preserved Baseline Enhanced) ───────────────────

@app.post("/api/iot/telemetry", status_code=status.HTTP_201_CREATED)
def receive_telemetry(reading: SensorReadingCreate, request: Request, db: Session = Depends(get_db)):
    """
    Ingest telemetry from Smart Bins. Requires HMAC signature.
    Enhanced with strong device lifecycle validation and multi-sensor correlation.
    """
    client_ip = request.client.host if request.client else "unknown"
    
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
    if not bin_record:
        emit_security_event(
            db=db,
            event_type="DEVICE_AUTH_FAILURE",
            severity="HIGH",
            ip_address=client_ip,
            user_or_device_id=reading.bin_id,
            reason="Unrecognized device ID submitted telemetry",
            action_taken="HTTP_404_REJECTED"
        )
        raise HTTPException(status_code=404, detail="Smart Bin not found")
        
    # Process Security (Anti-Spoofing, Replay, Geofence, Device Trust)
    timestamp_unix = reading.timestamp_unix or int(time.time())
    is_valid, error_reason = process_telemetry_security(
        db, bin_record, reading.dict(), reading.hmac_signature, timestamp_unix, client_ip
    )
    
    if not is_valid:
        emit_security_event(
            db=db,
            event_type="INVALID_TELEMETRY_SIGNATURE" if "signature" in error_reason.lower() else "GPS_SPOOFING_SUSPECTED" if "geofence" in error_reason.lower() else "SENSOR_SPOOFING_SUSPECTED",
            severity="CRITICAL" if "signature" in error_reason.lower() else "HIGH",
            ip_address=client_ip,
            user_or_device_id=reading.bin_id,
            resource=f"SmartBin/{reading.bin_id}",
            reason=error_reason,
            action_taken="TELEMETRY_REJECTED_400"
        )
        raise HTTPException(status_code=400, detail=f"Telemetry rejected: {error_reason}")
        
    # Save reading
    new_reading = SensorReading(
        bin_id=bin_record.id,
        fill_level=reading.fill_level,
        location_lat=reading.location_lat,
        location_lon=reading.location_lon,
        temperature=reading.temperature,
        sensor_status=reading.sensor_status,
        battery_level=reading.battery_level,
        raw_hmac=reading.hmac_signature
    )
    db.add(new_reading)
    db.commit()
    return {"status": "success", "message": "Telemetry securely ingested"}


# ── Route Management (Admin/Operator) (Preserved Baseline) ──────────────────

@app.post("/api/routes/optimize", response_model=RouteResponse)
def generate_optimized_route(
    name: str, zone: str = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))
):
    """
    Generate optimized route based on multi-factor priority scoring and TSP heuristic.
    """
    route = optimize_route(db, name, zone)
    if not route:
        raise HTTPException(status_code=400, detail="No bins require collection currently.")
        
    route.created_by = current_user.id
    db.commit()
    log_audit(db, AuditAction.ROUTE_CREATED, current_user.id, "CollectionRoute", str(route.id), f"Optimized route {name} created.")
    return route


@app.post("/api/assignments", response_model=AssignmentResponse)
def assign_vehicle_driver(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Assign vehicle and driver to an optimized route.
    """
    route = db.query(CollectionRoute).filter(CollectionRoute.id == assignment.route_id).first()
    vehicle = db.query(Vehicle).filter(Vehicle.id == assignment.vehicle_id).first()
    driver = db.query(Driver).filter(Driver.id == assignment.driver_id).first()
    
    if not all([route, vehicle, driver]):
        raise HTTPException(status_code=404, detail="Route, Vehicle, or Driver not found")
        
    new_assignment = RouteAssignment(
        route_id=route.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        scheduled_date=assignment.scheduled_date,
        assigned_by=current_user.id
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    log_audit(db, AuditAction.VEHICLE_ASSIGNED, current_user.id, "RouteAssignment", str(new_assignment.id), f"Assigned Vehicle {vehicle.vehicle_id} and Driver {driver.driver_id} to Route {route.id}")
    return new_assignment


# ── Preserved Read Endpoints ────────────────────────────────────────────────

@app.get("/api/bins", response_model=List[SmartBinResponse])
def get_bins(db: Session = Depends(get_db)):
    return db.query(SmartBin).all()


@app.get("/api/routes")
def get_routes(db: Session = Depends(get_db)):
    return db.query(CollectionRoute).all()


@app.get("/api/security/logs")
def get_security_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "action": l.action.value if hasattr(l.action, "value") else str(l.action),
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "severity": l.severity,
            "details": l.details,
            "ip_address": l.ip_address
        }
        for l in logs
    ]


# ── NEW: Waste Intelligence Endpoints ───────────────────────────────────────

@app.get("/api/waste/taxonomy")
def get_waste_taxonomy():
    """Returns the hierarchical multi-level waste classification taxonomy."""
    return {
        "level1_categories": TAXONOMY_LEVEL1,
        "level2_recyclable": TAXONOMY_LEVEL2_RECYCLABLE,
        "level3_typology": TAXONOMY_LEVEL3_MAP
    }


@app.post("/api/waste/classify", response_model=WasteClassificationResponse)
def classify_waste(req: WasteClassificationRequest, db: Session = Depends(get_db)):
    """
    Submits an edge or optical inspection frame to the hierarchical classification pipeline.
    Applies confidence triage (>=90% Auto, 70-89% Rule check, <70% Unknown human review).
    """
    bin_record = db.query(SmartBin).filter(SmartBin.bin_id == req.bin_id).first()
    if not bin_record:
        raise HTTPException(status_code=404, detail="Smart Bin not found")

    hint = {
        "level1": req.level1_category,
        "level2": req.level2_subcategory,
        "level3": req.level3_object,
        "confidence": req.confidence_score
    } if req.confidence_score is not None else None

    rec = classify_waste_item(
        db=db,
        bin_id=req.bin_id,
        image_ref=req.image_ref,
        features_hint=hint
    )
    return rec


@app.get("/api/waste/composition/{bin_id}", response_model=BinCompositionResponse)
def get_bin_composition(bin_id: str, db: Session = Depends(get_db)):
    """Calculates and returns the 9-part waste composition breakdown for a specific bin."""
    comp = recalculate_bin_composition(db, bin_id)
    return comp


@app.get("/api/waste/contamination/{bin_id}", response_model=List[BinContaminationResponse])
def get_bin_contamination_logs(bin_id: str, db: Session = Depends(get_db)):
    """Returns all detected cross-contamination events for a specific bin."""
    records = db.query(BinContaminationRecord).filter(
        BinContaminationRecord.bin_id == bin_id
    ).order_by(BinContaminationRecord.timestamp.desc()).all()
    return records


@app.get("/api/waste/classifications", response_model=List[WasteClassificationResponse])
def list_waste_classifications(bin_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Returns waste classification records with confidence triage status."""
    q = db.query(WasteClassificationRecord)
    if bin_id:
        q = q.filter(WasteClassificationRecord.bin_id == bin_id)
    return q.order_by(WasteClassificationRecord.timestamp.desc()).limit(limit).all()


@app.post("/api/waste/verify/{classification_id}")
def verify_waste_classification(
    classification_id: int,
    verified_category: str,
    verified_subcategory: Optional[str] = None,
    verified_object: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Human verification endpoint for uncertain predictions (<70% confidence).
    Promotes prediction to verified status and updates composition.
    """
    rec = db.query(WasteClassificationRecord).filter(WasteClassificationRecord.id == classification_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Classification record not found")
    
    rec.level1_category = verified_category
    rec.level2_subcategory = verified_subcategory
    rec.level3_object = verified_object
    rec.verification_status = f"VERIFIED_BY_OPERATOR_{current_user.username}"
    rec.status = "HUMAN_VERIFIED"
    db.commit()
    db.refresh(rec)
    recalculate_bin_composition(db, rec.bin_id)
    return {
        "status": "success",
        "message": "Human verification recorded successfully",
        "classification_id": rec.id,
        "verified_category": rec.level1_category,
        "verification_status": rec.verification_status
    }


@app.get("/api/waste/contaminations", response_model=List[BinContaminationResponse])
def list_all_contaminations(limit: int = 50, db: Session = Depends(get_db)):
    """Returns all detected contamination events across the smart bin network."""
    return db.query(BinContaminationRecord).order_by(BinContaminationRecord.timestamp.desc()).limit(limit).all()


@app.get("/api/sensors/health", response_model=List[SensorHealthResponse])
def list_all_sensor_health(db: Session = Depends(get_db)):
    """Returns the complete sensor health matrix across all registered nodes."""
    return db.query(SensorHealthRecord).all()


@app.get("/api/waste/density/{bin_id}")
def get_waste_density_analytics(bin_id: str, weight_kg: Optional[float] = 18.5, db: Session = Depends(get_db)):
    """Correlates ultrasonic volume, mass load cell reading, and temperature."""
    bin_rec = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
    if not bin_rec:
        raise HTTPException(status_code=404, detail="Smart Bin not found")

    latest = db.query(SensorReading).filter(SensorReading.bin_id == bin_rec.id).order_by(SensorReading.timestamp.desc()).first()
    fill = latest.fill_level if latest else 50.0
    temp = latest.temperature if latest else 28.0

    density, anomaly, reason = calculate_waste_density_and_correlate(
        fill_level_pct=fill,
        weight_kg=weight_kg,
        capacity_liters=bin_rec.capacity_liters,
        temperature=temp
    )
    return {
        "bin_id": bin_id,
        "fill_level_pct": fill,
        "weight_kg": weight_kg,
        "density_kg_m3": density,
        "has_sensor_anomaly": anomaly,
        "anomaly_details": reason
    }


# ── NEW: Device Authentication & Registry Endpoints ─────────────────────────

@app.get("/api/devices", response_model=List[DeviceRegistryResponse])
def list_devices(db: Session = Depends(get_db)):
    """Returns registered edge IoT device nodes and their cryptographic trust status."""
    return db.query(DeviceRegistryItem).all()


@app.post("/api/devices/register", response_model=DeviceRegistryResponse)
def api_register_device(
    item: DeviceRegistryCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Registers a new edge device into the trust registry."""
    registered = register_device(
        db=db,
        device_id=item.device_id,
        bin_id=item.bin_id,
        assigned_lat=item.assigned_lat,
        assigned_lon=item.assigned_lon,
        firmware_version=item.firmware_version,
        cert_fingerprint=item.cert_fingerprint
    )
    return registered


@app.post("/api/devices/{device_id}/quarantine")
def api_quarantine_device(
    device_id: str,
    reason: str = "Administrator initiated quarantine",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SECURITY_AUDITOR))
):
    """Locks and quarantines a suspect device node."""
    q_item = quarantine_device(db, device_id, reason, actor_id=current_user.id)
    return {"status": "quarantined", "device_id": device_id, "trust_score": q_item.trust_score}


@app.post("/api/devices/{device_id}/revoke")
def api_revoke_device(
    device_id: str,
    reason: str = "Compromised credential revocation",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Permanently revokes an edge device certificate."""
    r_item = revoke_device(db, device_id, reason, actor_id=current_user.id)
    return {"status": "revoked", "device_id": device_id}


@app.post("/api/devices/{device_id}/rotate-cert")
def api_rotate_device_cert(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Rotates cryptographic certificate thumbprint for a device."""
    new_fp = rotate_device_credentials(db, device_id)
    return {"status": "rotated", "device_id": device_id, "new_fingerprint": new_fp}


# ── NEW: Sensor Health & Location Integrity Endpoints ───────────────────────

@app.get("/api/sensors/health/{bin_id}", response_model=List[SensorHealthResponse])
def get_sensor_health(bin_id: str, db: Session = Depends(get_db)):
    """Returns the multi-sensor status matrix for a smart bin."""
    return db.query(SensorHealthRecord).filter(SensorHealthRecord.bin_id == bin_id).all()


@app.get("/api/location/integrity/{bin_id}", response_model=List[LocationIntegrityResponse])
def get_location_integrity_records(bin_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Returns GPS telemetry velocity, jump analysis, and geofence tracking."""
    return db.query(LocationIntegrityRecord).filter(
        LocationIntegrityRecord.bin_id == bin_id
    ).order_by(LocationIntegrityRecord.timestamp.desc()).limit(limit).all()


# ── NEW: Central Security Event Engine & Threat Analytics ───────────────────

@app.get("/api/security/events", response_model=List[SecurityEventResponse])
def get_security_events(limit: int = 50, db: Session = Depends(get_db)):
    """Returns immutable security incident audit events."""
    return db.query(SecurityEventRecord).order_by(SecurityEventRecord.timestamp.desc()).limit(limit).all()


@app.get("/api/security/metrics")
def get_security_metrics(db: Session = Depends(get_db)):
    """Aggregates threat event frequencies and quarantine counts."""
    total_events = db.query(SecurityEventRecord).count()
    sqli_count = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_type == "SQL_INJECTION_ATTEMPT").count()
    xss_count = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_type == "XSS_ATTEMPT").count()
    gps_spoof = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_type.in_(["GPS_SPOOFING_SUSPECTED", "LOCATION_ANOMALY"])).count()
    replay_count = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_type == "REPLAY_ATTACK").count()
    bola_count = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_type == "BOLA_DENIED").count()
    quarantined_devices = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.status == "quarantined").count()
    revoked_devices = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.status == "revoked").count()

    return {
        "total_security_events": total_events,
        "sqli_attempts_blocked": sqli_count,
        "xss_attempts_blocked": xss_count,
        "gps_spoofing_prevented": gps_spoof,
        "replay_attacks_neutralized": replay_count,
        "bola_access_denied": bola_count,
        "quarantined_nodes": quarantined_devices,
        "revoked_nodes": revoked_devices
    }


# ── NEW: Route Security & Integrity Endpoints ───────────────────────────────

@app.get("/api/routes/{route_id}/verify-integrity", response_model=RouteIntegrityResponse)
def verify_route(route_id: int, db: Session = Depends(get_db)):
    """Verifies that the route waypoint sequence matches the signed cryptographic audit hash."""
    is_valid, msg, audit = verify_route_integrity(db, route_id)
    route = db.query(CollectionRoute).filter(CollectionRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    return {
        "route_id": route_id,
        "version": route.version,
        "route_hash": audit.route_hash if audit else "unknown",
        "is_valid": is_valid,
        "status": "VALID" if is_valid else "TAMPERED",
        "last_modified_by": audit.modified_by if audit else route.created_by,
        "timestamp": audit.timestamp if audit else route.created_at
    }


@app.put("/api/routes/{route_id}")
def update_route_sequence(
    route_id: int,
    new_bin_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Authorized route modification endpoint.
    Strictly forbids Drivers from modifying route sequences (enforces RBAC & Route Security).
    """
    success, msg, updated_route = modify_route_authorized(
        db=db,
        route_id=route_id,
        new_bin_ids=new_bin_ids,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    if not success:
        emit_security_event(
            db=db,
            event_type="ROUTE_MODIFICATION_DENIED",
            severity="HIGH",
            user_or_device_id=current_user.username,
            resource=f"CollectionRoute/{route_id}",
            reason=msg,
            action_taken="HTTP_403_FORBIDDEN"
        )
        raise HTTPException(status_code=403, detail=msg)

    return {"status": "success", "message": msg, "version": updated_route.version}


# ── NEW: OWASP Path Traversal & SSRF Defense Demonstration Endpoints ────────

@app.get("/api/reports/download")
def download_secure_report(filename: str):
    """
    Secure report retrieval endpoint with path traversal containment.
    Strictly forbids directory traversal attacks (../, %2e%2e, null byte).
    """
    base_docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
    safe_path = safe_canonical_path(base_docs_dir, filename)

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Requested report document not found")

    with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return {"filename": os.path.basename(safe_path), "content": content}


@app.post("/api/security/verify-url")
def verify_external_url(url: str, db: Session = Depends(get_db)):
    """
    Validates outbound URLs to prevent Server-Side Request Forgery (SSRF).
    Blocks private subnets, localhost, and AWS metadata endpoints.
    """
    is_safe, reason = validate_url_for_ssrf(url)
    if not is_safe:
        emit_security_event(
            db=db,
            event_type="SSRF_ATTEMPT",
            severity="CRITICAL",
            resource=url,
            reason=reason,
            action_taken="REQUEST_BLOCKED_400"
        )
        raise HTTPException(status_code=400, detail=reason)

    return {"status": "valid", "url": url, "message": "Target URL passed outbound security boundaries."}


# ── NEW: BOLA / Object-Level Authorization Endpoint ─────────────────────────

@app.get("/api/assignments/{assignment_id}")
def get_assignment_details(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves route assignment with Object-Level Authorization (BOLA/IDOR protection).
    Ensures drivers can only access assignments assigned directly to them.
    """
    assignment = db.query(RouteAssignment).filter(RouteAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Route assignment not found")

    is_authorized = check_object_authorization(
        db=db,
        current_user=current_user,
        resource_type="RouteAssignment",
        resource_id=assignment_id,
        action="read"
    )

    if not is_authorized:
        emit_security_event(
            db=db,
            event_type="BOLA_DENIED",
            severity="HIGH",
            user_or_device_id=current_user.username,
            resource=f"RouteAssignment/{assignment_id}",
            reason=f"User {current_user.username} (Role: {current_user.role.value}) attempted unauthorized object access",
            action_taken="HTTP_403_FORBIDDEN"
        )
        raise HTTPException(status_code=403, detail="BOLA Protection: You are not authorized to view this assignment object.")

    return assignment


# ── Gemini AI Agent & Intelligence Endpoints ─────────────────────────────────
from app.gemini_agent import (
    classify_waste_with_gemini,
    analyze_threat_with_gemini,
    ask_operations_agent
)

@app.post("/api/ai/classify")
def ai_classify_waste(payload: dict):
    """
    Multimodal & semantic AI waste classification powered by Google Gemini.
    """
    item = payload.get("item_description", payload.get("description", "general municipal waste"))
    image_b64 = payload.get("image_b64")
    result = classify_waste_with_gemini(item_description=item, image_b64=image_b64)
    return result


@app.post("/api/ai/analyze-threat")
def ai_analyze_threat(payload: dict):
    """
    AI-driven cybersecurity and IoT anomaly assessment powered by Google Gemini.
    """
    event_type = payload.get("event_type", "ANOMALY_DETECTED")
    details = payload.get("details", {})
    return analyze_threat_with_gemini(event_type=event_type, details=details)


@app.post("/api/ai/chat")
def ai_chat_assistant(payload: dict):
    """
    Conversational AI assistant for dispatchers, drivers, and security analysts.
    """
    query = payload.get("query", payload.get("message", "How is the system operating?"))
    role = payload.get("role", "operator")
    context = payload.get("context", {})
    response_text = ask_operations_agent(user_query=query, user_role=role, context=context)
    return {"query": query, "response": response_text, "model": settings.GEMINI_MODEL}


# ── Mount Frontend UI Static Files ──────────────────────────────────────────
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
