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
