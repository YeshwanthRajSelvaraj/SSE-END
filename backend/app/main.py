"""
FastAPI Main Application
Includes API endpoints, middleware, and exception handling.
"""
import time
import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    AssignmentCreate, AssignmentResponse
)
from app.models import (
    User, UserRole, SmartBin, SensorReading, Vehicle, Driver,
    CollectionRoute, RouteAssignment, AuditLog, AuditAction
)
from app.anti_spoofing import process_telemetry_security
from app.route_optimizer import optimize_route
from app.rate_limiter import rate_limit_ip

# Initialize Database
init_db()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse

@app.middleware("http")
async def security_headers_and_rate_limit(request: Request, call_next):
    # Apply rate limit
    client_ip = request.client.host if request.client else "unknown"
    try:
        rate_limit_ip(client_ip)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    
    response = await call_next(request)
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Auth Endpoints ──────────────────────────────────────────────────────────

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
    db_user = db.query(User).filter(User.username == user.username).first()
    ip = request.client.host if request.client else "unknown"
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        log_audit(db, AuditAction.LOGIN_FAILED, None, "User", user.username, "Failed login attempt", ip, "WARNING")
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access_token = create_access_token(data={"sub": db_user.username})
    log_audit(db, AuditAction.LOGIN, db_user.id, "User", db_user.username, "Successful login", ip)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "role": db_user.role.value
    }


# ── IoT Telemetry Endpoints ──────────────────────────────────────────────────

@app.post("/api/iot/telemetry", status_code=status.HTTP_201_CREATED)
def receive_telemetry(reading: SensorReadingCreate, request: Request, db: Session = Depends(get_db)):
    """
    Ingest telemetry from Smart Bins. Requires HMAC signature.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    bin_record = db.query(SmartBin).filter(SmartBin.bin_id == reading.bin_id).first()
    if not bin_record:
        raise HTTPException(status_code=404, detail="Smart Bin not found")
        
    # Process Security (Anti-Spoofing, Replay, Geofence)
    timestamp_unix = int(time.time()) # In real scenario, timestamp comes from device payload
    is_valid, error_reason = process_telemetry_security(
        db, bin_record, reading.dict(), reading.hmac_signature, timestamp_unix, client_ip
    )
    
    if not is_valid:
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


# ── Route Management (Admin/Operator) ────────────────────────────────────────

@app.post("/api/routes/optimize", response_model=RouteResponse)
def generate_optimized_route(
    name: str, zone: str = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))
):
    """
    Generate optimized route based on fill levels and TSP heuristic.
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

# Additional Read Endpoints
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


# Mount Frontend UI Static Files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
