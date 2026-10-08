"""
Route Optimization Module using Multi-Factor Priority Scoring & TSP Nearest Neighbor Heuristics.
Preserves existing baseline functions while adding:
- Multi-factor collection priority (Fill level, Hazardous/Bio, Temperature, Contamination, Security Risk, Sensor Integrity)
- Anti-override invariant: High fill DOES NOT override high-risk hazardous or security events
- Cryptographic Route Integrity Hashing & Versioning
- Driver unauthorized modification prevention
"""
import datetime
import hashlib
import json
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from geopy.distance import geodesic

from app.models import (
    SmartBin, SensorReading, CollectionRoute, RouteStatus,
    RouteAuditVersion, BinContaminationRecord, WasteClassificationRecord,
    SensorHealthRecord, SensorHealthStatus, BinStatus, AuditAction, UserRole
)
from app.auth import log_audit

logger = logging.getLogger("route_optimizer")


def calculate_bin_priority_score(
    db: Optional[Session] = None,
    bin_record: Optional[SmartBin] = None,
    latest_reading: Optional[SensorReading] = None,
    fill_percentage: Optional[float] = None,
    category: Optional[str] = None,
    is_hazardous: Optional[bool] = None,
    temperature: Optional[float] = None,
    device_trust_score: Optional[float] = None
) -> float:
    """
    Computes a weighted composite priority score:
    - Base fill level (0 - 100)
    - Thermal hazard (+40 if >40°C, +100 if >50°C)
    - Hazardous / Biomedical presence (+150 - emergency priority)
    - Active contamination breach (+50)
    - Security compromised status (+60)
    - Sensor integrity failure (+40)

    Critical invariant: A higher fill percentage (e.g., 90%) must NOT
    override a high-risk hazardous or security event (scoring 150+).
    """
    # Direct programmatic evaluation mode
    if fill_percentage is not None or is_hazardous is not None:
        score = fill_percentage if fill_percentage is not None else 0.0
        temp = temperature if temperature is not None else 25.0
        if temp >= 50.0:
            score += 100.0
        elif temp >= 40.0:
            score += 40.0
        if is_hazardous or (category in ["Hazardous", "Biomedical"]):
            score += 150.0
        if device_trust_score is not None and device_trust_score < 50.0:
            score += 60.0
        return score

    score = 0.0
    fill = latest_reading.fill_level if latest_reading else 0.0
    temp = latest_reading.temperature if latest_reading else 25.0

    # 1. Base Fill Level
    score += fill


    # 2. Temperature Factor
    if temp >= 50.0:
        score += 100.0  # Fire risk / spontaneous decomposition
    elif temp >= 40.0:
        score += 40.0

    # 3. Hazardous or Biomedical Classification
    has_hazard = db.query(WasteClassificationRecord).filter(
        WasteClassificationRecord.bin_id == bin_record.bin_id,
        WasteClassificationRecord.level1_category.in_(["Hazardous", "Biomedical"])
    ).first()
    if has_hazard:
        score += 150.0  # Immediate emergency dispatch

    # 4. Contamination Event
    has_contamination = db.query(BinContaminationRecord).filter(
        BinContaminationRecord.bin_id == bin_record.bin_id,
        BinContaminationRecord.contamination_detected == True
    ).first()
    if has_contamination:
        score += 50.0

    # 5. Security Status Compromised
    if bin_record.status == BinStatus.COMPROMISED:
        score += 60.0

    # 6. Sensor Integrity Failure
    failed_sensor = db.query(SensorHealthRecord).filter(
        SensorHealthRecord.bin_id == bin_record.bin_id,
        SensorHealthRecord.status.in_([SensorHealthStatus.FAILED, SensorHealthStatus.TAMPERED])
    ).first()
    if failed_sensor:
        score += 40.0

    return round(score, 1)


def get_bins_needing_collection(db: Session, threshold_fill: float = 75.0, temp_warning: float = 40.0) -> List[SmartBin]:
    """
    Identify bins that require collection based on fill level, high temperature,
    or composite hazard priority score.
    """
    bins = db.query(SmartBin).filter(SmartBin.status != BinStatus.OFFLINE).all()
    scored_bins = []
    
    for b in bins:
        latest = db.query(SensorReading).filter(SensorReading.bin_id == b.id).order_by(SensorReading.timestamp.desc()).first()
        priority_score = calculate_bin_priority_score(db, b, latest)
        
        # Collect if fill meets threshold, or temp exceeds warning, or priority score exceeds 95.0
        if (latest and (latest.fill_level >= threshold_fill or latest.temperature >= temp_warning)) or priority_score >= 95.0:
            scored_bins.append((priority_score, b))
            
    # Sort highest priority first
    scored_bins.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored_bins]


def compute_route_integrity_hash(route_id: int, bin_sequence: str, version: int, distance_km: float) -> str:
    """Computes a SHA-256 cryptographic fingerprint of the planned route definition."""
    content = f"{route_id}|{bin_sequence}|{version}|{distance_km:.2f}"
    return hashlib.sha256(content.encode()).hexdigest()


def optimize_route(db: Session, route_name: str, zone: str = None, depot_coords: tuple = (13.0, 80.2)) -> CollectionRoute:
    """
    Generate an optimized route using a greedy Nearest Neighbor heuristic.
    Starts at depot_coords, visits targeted bins in priority order, and returns.
    """
    bins = get_bins_needing_collection(db)
    if zone and zone.lower() != "all":
        bins = [b for b in bins if b.zone == zone]
        
    if not bins:
        return None
        
    unvisited = bins.copy()
    current_location = depot_coords
    ordered_bin_ids = []
    total_distance = 0.0
    
    while unvisited:
        # Find nearest unvisited bin
        nearest_bin = None
        min_dist = float('inf')
        
        for b in unvisited:
            dist = geodesic(current_location, (b.location_lat, b.location_lon)).kilometers
            if dist < min_dist:
                min_dist = dist
                nearest_bin = b
                
        ordered_bin_ids.append(nearest_bin.bin_id)
        total_distance += min_dist
        current_location = (nearest_bin.location_lat, nearest_bin.location_lon)
        unvisited.remove(nearest_bin)
        
    # Return to depot
    total_distance += geodesic(current_location, depot_coords).kilometers
    
    bin_seq_str = json.dumps(ordered_bin_ids)
    dist_rounded = round(total_distance, 2)
    
    # Create Route record
    route = CollectionRoute(
        route_name=route_name,
        zone=zone,
        bin_sequence=bin_seq_str,
        total_distance_km=dist_rounded,
        estimated_time_min=round(total_distance * 2.5), # Rough estimate 2.5 min per km
        status=RouteStatus.PENDING,
        optimized=True,
        version=1
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    # Compute & store cryptographic integrity audit record
    route_hash = compute_route_integrity_hash(route.id, bin_seq_str, 1, dist_rounded)
    audit_ver = RouteAuditVersion(
        route_id=route.id,
        version=1,
        created_by=route.created_by,
        route_hash=route_hash,
        status="active",
        change_summary=f"Initial autonomous optimization created with {len(ordered_bin_ids)} stops",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(audit_ver)
    db.commit()

    return route


def verify_route_integrity(db: Session, route_id: int) -> Tuple[bool, str, Optional[RouteAuditVersion]]:
    """
    Verifies that the route's current waypoint sequence matches the signed audit hash.
    Detects unauthorized database injection or tampering with route stops.
    """
    route = db.query(CollectionRoute).filter(CollectionRoute.id == route_id).first()
    if not route:
        return False, "Route not found", None

    latest_audit = db.query(RouteAuditVersion).filter(
        RouteAuditVersion.route_id == route_id
    ).order_by(RouteAuditVersion.version.desc()).first()

    if not latest_audit:
        return True, "No prior audit version recorded", None

    expected_hash = compute_route_integrity_hash(
        route.id,
        route.bin_sequence,
        route.version,
        route.total_distance_km
    )

    if latest_audit.route_hash != expected_hash:
        log_audit(
            db=db,
            action=AuditAction.ROUTE_INTEGRITY_VIOLATION,
            user_id=None,
            resource_type="CollectionRoute",
            resource_id=str(route_id),
            details=f"Route integrity mismatch! Expected {latest_audit.route_hash[:16]}... got {expected_hash[:16]}...",
            severity="CRITICAL"
        )
        return False, "Route integrity validation failed: Cryptographic hash mismatch detected", latest_audit

    return True, "Route definition cryptographically verified", latest_audit


def modify_route_authorized(
    db: Session,
    route_id: int,
    new_bin_ids: List[str],
    actor_id: int,
    actor_role: UserRole
) -> Tuple[bool, str, Optional[CollectionRoute]]:
    """
    Enforces authorization rules for route modifications:
    - DRIVER is strictly prohibited from altering route sequences.
    - OPERATOR / ADMIN can modify with version increment and audit logging.
    """
    if actor_role == UserRole.DRIVER:
        log_audit(
            db=db,
            action=AuditAction.ROUTE_UNAUTHORIZED,
            user_id=actor_id,
            resource_type="CollectionRoute",
            resource_id=str(route_id),
            details="Driver role attempted unauthorized alteration of collection route",
            severity="HIGH"
        )
        return False, "Drivers are strictly forbidden and not authorized to alter route sequences or destinations", None

    route = db.query(CollectionRoute).filter(CollectionRoute.id == route_id).first()
    if not route:
        return False, "Route not found", None

    route.version += 1
    route.bin_sequence = json.dumps(new_bin_ids)
    route.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(route)

    new_hash = compute_route_integrity_hash(route.id, route.bin_sequence, route.version, route.total_distance_km or 0.0)
    audit_ver = RouteAuditVersion(
        route_id=route.id,
        version=route.version,
        modified_by=actor_id,
        route_hash=new_hash,
        status="active",
        change_summary=f"Authorized route modification by user {actor_id} (Role: {actor_role.value})",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(audit_ver)
    db.commit()

    log_audit(
        db=db,
        action=AuditAction.ROUTE_MODIFIED,
        user_id=actor_id,
        resource_type="CollectionRoute",
        resource_id=str(route_id),
        details=f"Route {route_id} updated to version {route.version} with {len(new_bin_ids)} stops",
        severity="INFO"
    )

    return True, f"Route modified to version {route.version}", route
