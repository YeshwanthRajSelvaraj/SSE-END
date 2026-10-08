"""
SQLAlchemy ORM Models for Smart Waste Management System.
Entities: User, SmartBin, SensorReading, Vehicle, Driver, CollectionRoute,
          RouteAssignment, AuditLog, DeviceToken
"""
import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Text, Enum as SAEnum, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    DRIVER = "driver"
    VIEWER = "viewer"


class BinStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    COMPROMISED = "compromised"


class SensorStatus(str, enum.Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    MALFUNCTION = "malfunction"


class RouteStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    BIN_DATA_RECEIVED = "bin_data_received"
    SPOOFING_DETECTED = "spoofing_detected"
    LOCATION_ANOMALY = "location_anomaly"
    ROUTE_CREATED = "route_created"
    ROUTE_MODIFIED = "route_modified"
    ROUTE_UNAUTHORIZED = "route_unauthorized"
    VEHICLE_ASSIGNED = "vehicle_assigned"
    DRIVER_ASSIGNED = "driver_assigned"
    DEVICE_REGISTERED = "device_registered"
    DEVICE_REVOKED = "device_revoked"
    RATE_LIMIT_HIT = "rate_limit_hit"
    PRIVILEGE_CHANGE = "privilege_change"


# ── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    audit_logs = relationship("AuditLog", back_populates="user")


class SmartBin(Base):
    __tablename__ = "smart_bins"

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(String(50), unique=True, nullable=False, index=True)
    device_key = Column(String(255), nullable=False)  # HMAC key for this device
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    address = Column(String(255))
    capacity_liters = Column(Float, default=120.0)
    status = Column(SAEnum(BinStatus), default=BinStatus.ACTIVE)
    zone = Column(String(50))
    installed_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_collection = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    readings = relationship("SensorReading", back_populates="bin", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("idx_bin_timestamp", "bin_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("smart_bins.id"), nullable=False)
    fill_level = Column(Float, nullable=False)   # 0-100 percentage
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)   # Celsius
    sensor_status = Column(SAEnum(SensorStatus), default=SensorStatus.NORMAL)
    battery_level = Column(Float)                  # 0-100 percentage
    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String(255))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    raw_hmac = Column(String(128))                 # HMAC signature from device

    bin = relationship("SmartBin", back_populates="readings")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String(20), unique=True, nullable=False, index=True)
    plate_number = Column(String(20), unique=True, nullable=False)
    vehicle_type = Column(String(50), default="truck")
    capacity_kg = Column(Float, default=5000.0)
    fuel_type = Column(String(20), default="diesel")
    is_available = Column(Boolean, default=True)
    current_lat = Column(Float)
    current_lon = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    assignments = relationship("RouteAssignment", back_populates="vehicle")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    phone = Column(String(15))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    assignments = relationship("RouteAssignment", back_populates="driver")


class CollectionRoute(Base):
    __tablename__ = "collection_routes"

    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String(100), nullable=False)
    zone = Column(String(50))
    bin_sequence = Column(Text)         # JSON list of bin IDs in order
    total_distance_km = Column(Float)
    estimated_time_min = Column(Float)
    status = Column(SAEnum(RouteStatus), default=RouteStatus.PENDING)
    optimized = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    version = Column(Integer, default=1)  # Tracks route modifications

    assignments = relationship("RouteAssignment", back_populates="route")


class RouteAssignment(Base):
    __tablename__ = "route_assignments"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("collection_routes.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    scheduled_date = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(SAEnum(RouteStatus), default=RouteStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    route = relationship("CollectionRoute", back_populates="assignments")
    vehicle = relationship("Vehicle", back_populates="assignments")
    driver = relationship("Driver", back_populates="assignments")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_action", "action"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(SAEnum(AuditAction), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    details = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String(20), default="INFO")

    user = relationship("User", back_populates="audit_logs")


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("smart_bins.id"), unique=True, nullable=False)
    token_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used = Column(DateTime)
    revoked_at = Column(DateTime)
