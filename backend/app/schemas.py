"""
Pydantic schemas for request/response validation.
"""
import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="viewer")


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    username: Optional[str] = None
    email: Optional[str] = None


# ── Smart Bin Schemas ────────────────────────────────────────────────────────

class SmartBinCreate(BaseModel):
    bin_id: str = Field(..., min_length=3, max_length=50)
    location_lat: float = Field(..., ge=-90, le=90)
    location_lon: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    capacity_liters: float = Field(default=120.0, gt=0)
    zone: Optional[str] = None


class SmartBinResponse(BaseModel):
    id: int
    bin_id: str
    location_lat: float
    location_lon: float
    address: Optional[str]
    capacity_liters: float
    status: str
    zone: Optional[str]
    installed_at: datetime.datetime
    last_collection: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class SmartBinUpdate(BaseModel):
    address: Optional[str] = None
    capacity_liters: Optional[float] = Field(default=None, gt=0)
    status: Optional[str] = None
    zone: Optional[str] = None


# ── Sensor Reading Schemas ───────────────────────────────────────────────────

class SensorReadingCreate(BaseModel):
    """Payload sent by IoT smart bin devices."""
    bin_id: str = Field(..., description="Unique bin identifier")
    fill_level: float = Field(..., ge=0, le=100, description="Fill percentage 0-100")
    location_lat: float = Field(..., ge=-90, le=90)
    location_lon: float = Field(..., ge=-180, le=180)
    temperature: float = Field(..., ge=-50, le=150, description="Temperature in Celsius")
    sensor_status: str = Field(default="normal")
    battery_level: Optional[float] = Field(default=None, ge=0, le=100)
    hmac_signature: Optional[str] = Field(default=None, description="HMAC-SHA256 signature")
    device_token: Optional[str] = Field(default=None, description="Device auth token")
    weight_kg: Optional[float] = Field(default=None, ge=0, le=1000, description="Weight measured by load cell")
    nonce: Optional[str] = Field(default=None, description="Unique telemetry request nonce")
    sequence_number: Optional[int] = Field(default=None, ge=0, description="Monotonically increasing sequence number")
    timestamp_unix: Optional[int] = Field(default=None, description="Device UNIX timestamp")
    image_ref: Optional[str] = Field(default=None, description="Reference ID for captured camera frame")

    @field_validator("sensor_status")
    @classmethod
    def validate_sensor_status(cls, v):
        allowed = {"normal", "warning", "critical", "malfunction"}
        if v.lower() not in allowed:
            raise ValueError(f"sensor_status must be one of {allowed}")
        return v.lower()


class SensorReadingResponse(BaseModel):
    id: int
    bin_id: int
    fill_level: float
    location_lat: float
    location_lon: float
    temperature: float
    sensor_status: str
    battery_level: Optional[float]
    is_anomaly: bool
    anomaly_reason: Optional[str]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# ── Vehicle Schemas ──────────────────────────────────────────────────────────

class VehicleCreate(BaseModel):
    vehicle_id: str = Field(..., min_length=2, max_length=20)
    plate_number: str = Field(..., min_length=2, max_length=20)
    vehicle_type: str = Field(default="truck")
    capacity_kg: float = Field(default=5000.0, gt=0)
    fuel_type: str = Field(default="diesel")


class VehicleResponse(BaseModel):
    id: int
    vehicle_id: str
    plate_number: str
    vehicle_type: str
    capacity_kg: float
    fuel_type: str
    is_available: bool
    current_lat: Optional[float]
    current_lon: Optional[float]

    class Config:
        from_attributes = True


# ── Driver Schemas ───────────────────────────────────────────────────────────

class DriverCreate(BaseModel):
    driver_id: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    license_number: str = Field(..., min_length=5, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=15)


class DriverResponse(BaseModel):
    id: int
    driver_id: str
    name: str
    license_number: str
    phone: Optional[str]
    is_available: bool

    class Config:
        from_attributes = True


# ── Route Schemas ────────────────────────────────────────────────────────────

class RouteCreate(BaseModel):
    route_name: str = Field(..., min_length=3, max_length=100)
    zone: Optional[str] = None
    bin_ids: List[str] = Field(..., min_length=1, description="Ordered list of bin IDs")


class RouteResponse(BaseModel):
    id: int
    route_name: str
    zone: Optional[str]
    bin_sequence: Optional[str]
    total_distance_km: Optional[float]
    estimated_time_min: Optional[float]
    status: str
    optimized: bool
    created_at: datetime.datetime
    version: int

    class Config:
        from_attributes = True


class RouteOptimizeRequest(BaseModel):
    route_id: int
    strategy: str = Field(default="nearest_neighbor", description="Optimization algorithm")


# ── Assignment Schemas ───────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    route_id: int
    vehicle_id: int
    driver_id: int
    scheduled_date: datetime.datetime


class AssignmentResponse(BaseModel):
    id: int
    route_id: int
    vehicle_id: int
    driver_id: int
    scheduled_date: datetime.datetime
    status: str
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


# ── Audit Log Schema ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime.datetime
    severity: str

    class Config:
        from_attributes = True


# ── Dashboard Schemas ────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_bins: int
    active_bins: int
    offline_bins: int
    compromised_bins: int
    average_fill_level: float
    bins_above_80_percent: int
    total_vehicles: int
    available_vehicles: int
    total_drivers: int
    available_drivers: int
    active_routes: int
    total_collections_today: int
    security_alerts_today: int


# ── Waste Intelligence & Classification Schemas ─────────────────────────────

class WasteClassificationRequest(BaseModel):
    bin_id: str
    image_ref: Optional[str] = None
    level1_category: Optional[str] = None
    level2_subcategory: Optional[str] = None
    level3_object: Optional[str] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    simulated_raw_features: Optional[dict] = None


class WasteClassificationResponse(BaseModel):
    id: int
    bin_id: str
    level1_category: str
    level2_subcategory: Optional[str]
    level3_object: Optional[str]
    confidence_score: float
    status: str
    model_version: str
    verification_status: str
    image_ref: Optional[str]
    timestamp: datetime.datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class BinContaminationResponse(BaseModel):
    id: int
    bin_id: str
    contamination_detected: bool
    expected_category: Optional[str]
    found_category: Optional[str]
    confidence_score: float
    details: Optional[str]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class BinCompositionResponse(BaseModel):
    bin_id: str
    organic_pct: float
    plastic_pct: float
    paper_pct: float
    cardboard_pct: float
    glass_pct: float
    metal_pct: float
    ewaste_pct: float
    hazardous_pct: float
    other_pct: float
    calculated_at: datetime.datetime

    class Config:
        from_attributes = True


# ── Device Registry & Sensor Health Schemas ──────────────────────────────────

class DeviceRegistryCreate(BaseModel):
    device_id: str = Field(..., min_length=3, max_length=50)
    bin_id: Optional[str] = None
    cert_fingerprint: Optional[str] = None
    assigned_lat: Optional[float] = None
    assigned_lon: Optional[float] = None
    firmware_version: str = Field(default="1.0.0")


class DeviceRegistryUpdate(BaseModel):
    status: Optional[str] = None
    firmware_version: Optional[str] = None
    assigned_lat: Optional[float] = None
    assigned_lon: Optional[float] = None
    revoked_reason: Optional[str] = None


class DeviceRegistryResponse(BaseModel):
    id: int
    device_id: str
    bin_id: Optional[str]
    cert_fingerprint: Optional[str]
    status: str
    assigned_lat: Optional[float]
    assigned_lon: Optional[float]
    firmware_version: str
    last_heartbeat: datetime.datetime
    trust_score: float
    created_at: datetime.datetime
    revoked_at: Optional[datetime.datetime]
    revoked_reason: Optional[str]

    class Config:
        from_attributes = True


class SensorHealthResponse(BaseModel):
    id: int
    bin_id: str
    sensor_type: str
    status: str
    last_reading_value: Optional[float]
    last_heartbeat: datetime.datetime
    anomaly_count: int
    details: Optional[str]

    class Config:
        from_attributes = True


class LocationIntegrityResponse(BaseModel):
    id: int
    bin_id: str
    reported_lat: float
    reported_lon: float
    prev_lat: Optional[float]
    prev_lon: Optional[float]
    distance_meters: float
    implied_speed_kmh: float
    trust_score: float
    status: str
    anomaly_reason: Optional[str]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# ── Security Event Schemas ───────────────────────────────────────────────────

class SecurityEventResponse(BaseModel):
    id: int
    event_id: str
    event_type: str
    severity: str
    source: str
    user_or_device_id: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    reason: Optional[str]
    action_taken: str
    correlation_id: Optional[str]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# ── Route Integrity Schemas ──────────────────────────────────────────────────

class RouteIntegrityResponse(BaseModel):
    route_id: int
    version: int
    route_hash: str
    is_valid: bool
    status: str
    last_modified_by: Optional[int]
    timestamp: datetime.datetime
