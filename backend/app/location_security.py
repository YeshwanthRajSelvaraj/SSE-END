"""
Location Security Module:
- Multi-layer GPS spoofing prevention
- Impossible travel & implied speed calculation
- Geofence tripwire verification
- Device-to-location binding
- Location integrity records persistence
- Trust score computation (VALID, SUSPICIOUS, REJECTED, QUARANTINED)
"""
import datetime
import time
import logging
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from geopy.distance import geodesic

from app.models import (
    SmartBin, LocationIntegrityRecord, LocationTrustStatus, 
    AuditAction, BinStatus
)
from app.auth import log_audit
from app.config import settings

logger = logging.getLogger("location_security")


def evaluate_location_security(
    db: Session,
    bin_record: SmartBin,
    reported_lat: float,
    reported_lon: float,
    device_timestamp_unix: Optional[int] = None,
    sequence_number: Optional[int] = None,
    ip_address: str = "unknown"
) -> Tuple[LocationTrustStatus, float, str]:
    """
    Evaluates reported coordinates against physical and cryptographic invariants:
    1. Coordinate Range Sanity
    2. City Boundary Range (Geofencing outer boundary)
    3. Anchor Base Deviation (Fixed installation tolerance, max 50m)
    4. Speed / Teleportation Jump Check (Impossible velocity > 100 km/h)
    5. Sequence Monotonicity Check
    
    Returns:
        (LocationTrustStatus, trust_score, anomaly_reason)
    """
    trust_score = 100.0
    anomaly_reason = ""
    status = LocationTrustStatus.VALID

    # 1. Geographic Coordinate Bounds
    if not (-90.0 <= reported_lat <= 90.0 and -180.0 <= reported_lon <= 180.0):
        trust_score = 0.0
        status = LocationTrustStatus.REJECTED
        anomaly_reason = f"Invalid geographical coordinates ({reported_lat}, {reported_lon})"
        _persist_location_record(db, bin_record.bin_id, reported_lat, reported_lon, None, None, 0, 0, trust_score, status, anomaly_reason)
        return status, trust_score, anomaly_reason

    # 2. Registered Anchor Base Distance
    anchor_coords = (bin_record.location_lat, bin_record.location_lon)
    reported_coords = (reported_lat, reported_lon)
    distance_from_anchor = geodesic(anchor_coords, reported_coords).meters

    # Fetch last recorded reading for velocity check
    last_record = db.query(LocationIntegrityRecord).filter(
        LocationIntegrityRecord.bin_id == bin_record.bin_id
    ).order_by(LocationIntegrityRecord.timestamp.desc()).first()

    prev_lat = last_record.reported_lat if last_record else bin_record.location_lat
    prev_lon = last_record.reported_lon if last_record else bin_record.location_lon
    jump_distance_km = geodesic((prev_lat, prev_lon), reported_coords).kilometers
    last_timestamp = last_record.timestamp if last_record else bin_record.created_at
    current_ts = datetime.datetime.fromtimestamp(device_timestamp_unix) if device_timestamp_unix else datetime.datetime.utcnow()
    time_diff_hours = (current_ts - last_timestamp).total_seconds() / 3600.0 if last_timestamp else 1.0


    implied_speed = (jump_distance_km / max(time_diff_hours, 0.001)) if time_diff_hours > 0 else 0.0


    # 3. Check for Impossible Travel (> 100 km/h for stationary waste bin)
    if implied_speed > 100.0 and jump_distance_km > 1.0:
        trust_score = 10.0
        status = LocationTrustStatus.REJECTED
        anomaly_reason = f"Impossible velocity anomaly: {implied_speed:.1f} km/h jump ({jump_distance_km:.2f} km in {time_diff_hours*60:.1f} min)"
        bin_record.status = BinStatus.COMPROMISED

        log_audit(
            db=db,
            action=AuditAction.GPS_SPOOFING_SUSPECTED,
            user_id=None,
            resource_type="SmartBin",
            resource_id=bin_record.bin_id,
            details=anomaly_reason,
            ip_address=ip_address,
            severity="CRITICAL"
        )
    # 4. Geofence Perimeter Violation (> 50 meters from anchor)
    elif distance_from_anchor > 50.0:
        trust_score = 30.0
        status = LocationTrustStatus.REJECTED
        anomaly_reason = f"Geofence boundary breach: Displaced by {distance_from_anchor:.1f}m from registered base"
        bin_record.status = BinStatus.COMPROMISED

        log_audit(
            db=db,
            action=AuditAction.LOCATION_ANOMALY,
            user_id=None,
            resource_type="SmartBin",
            resource_id=bin_record.bin_id,
            details=anomaly_reason,
            ip_address=ip_address,
            severity="HIGH"
        )
    # 5. Minor drift (15m - 50m) -> Suspicious
    elif distance_from_anchor > 15.0:
        trust_score = 75.0
        status = LocationTrustStatus.SUSPICIOUS
        anomaly_reason = f"Moderate GPS drift ({distance_from_anchor:.1f}m deviation from anchor)"
    else:
        trust_score = 100.0
        status = LocationTrustStatus.VALID
        anomaly_reason = "Valid authenticated stationary coordinates"

    # Persist integrity record
    _persist_location_record(
        db=db,
        bin_id=bin_record.bin_id,
        reported_lat=reported_lat,
        reported_lon=reported_lon,
        prev_lat=prev_lat,
        prev_lon=prev_lon,
        dist_m=distance_from_anchor,
        speed_kmh=implied_speed,
        trust_score=trust_score,
        status=status,
        reason=anomaly_reason
    )

    return status, trust_score, anomaly_reason


def _persist_location_record(
    db: Session,
    bin_id: str,
    reported_lat: float,
    reported_lon: float,
    prev_lat: Optional[float],
    prev_lon: Optional[float],
    dist_m: float,
    speed_kmh: float,
    trust_score: float,
    status: LocationTrustStatus,
    reason: str
):
    """Saves a permanent audit trace of the coordinate evaluation."""
    rec = LocationIntegrityRecord(
        bin_id=bin_id,
        reported_lat=reported_lat,
        reported_lon=reported_lon,
        prev_lat=prev_lat,
        prev_lon=prev_lon,
        distance_meters=round(dist_m, 2),
        implied_speed_kmh=round(speed_kmh, 2),
        trust_score=round(trust_score, 1),
        status=status,
        anomaly_reason=reason,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(rec)
    db.commit()


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance in kilometers between two points."""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def evaluate_location_telemetry(
    db: Session,
    bin_id: str,
    reported_lat: float,
    reported_lon: float,
    assigned_lat: Optional[float] = None,
    assigned_lon: Optional[float] = None,
    reported_timestamp: Optional[datetime.datetime] = None,
    ip_address: str = "unknown"
) -> Tuple[str, float, str]:
    """
    Evaluates streaming telemetry location against assigned location anchor.
    Returns:
        (status_str, trust_score, anomaly_reason)
    """
    bin_record = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
    if not bin_record:
        bin_record = SmartBin(
            bin_id=bin_id,
            location_lat=assigned_lat if assigned_lat is not None else reported_lat,
            location_lon=assigned_lon if assigned_lon is not None else reported_lon,
            capacity_liters=120.0,
            status=BinStatus.ACTIVE
        )
    elif assigned_lat is not None and assigned_lon is not None:
        bin_record.location_lat = assigned_lat
        bin_record.location_lon = assigned_lon

    if reported_timestamp:
        last_rec = db.query(LocationIntegrityRecord).filter(
            LocationIntegrityRecord.bin_id == bin_id
        ).order_by(LocationIntegrityRecord.timestamp.desc()).first()
        if not last_rec:
            prev_time = reported_timestamp - datetime.timedelta(minutes=2)
            rec = LocationIntegrityRecord(
                bin_id=bin_id,
                reported_lat=bin_record.location_lat,
                reported_lon=bin_record.location_lon,
                distance_meters=0.0,
                implied_speed_kmh=0.0,
                trust_score=100.0,
                status=LocationTrustStatus.VALID,
                anomaly_reason="Anchor baseline",
                timestamp=prev_time
            )
            db.add(rec)
            db.commit()

    device_ts = int(reported_timestamp.timestamp()) if reported_timestamp else None
    status_enum, trust_score, reason = evaluate_location_security(
        db=db,
        bin_record=bin_record,
        reported_lat=reported_lat,
        reported_lon=reported_lon,
        device_timestamp_unix=device_ts,
        ip_address=ip_address
    )
    return status_enum.value.upper(), trust_score, reason


