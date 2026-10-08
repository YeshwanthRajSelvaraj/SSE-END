"""
IoT Security Module: Anti-Spoofing and Integrity Checks
Mitigates: Sensor Spoofing, Location Manipulation, Replay Attacks
"""
import hmac
import hashlib
import time
import logging
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import SmartBin, SensorReading, BinStatus, AuditAction
from app.auth import log_audit
from geopy.distance import geodesic

logger = logging.getLogger("anti_spoofing")

# In-memory nonce cache to prevent replay attacks
# Key: bin_id:timestamp, Value: received_time
nonce_cache = {}
REPLAY_WINDOW_SECONDS = 300  # 5 minutes


def verify_device_signature(bin_id: str, payload_str: str, signature: str, device_key: str) -> bool:
    """
    Verify the HMAC-SHA256 signature of the incoming telemetry.
    The payload string should be a deterministic serialization (e.g., bin_id|timestamp|fill_level).
    """
    if not signature or not device_key:
        return False
    
    expected_hmac = hmac.new(
        key=device_key.encode('utf-8'),
        msg=payload_str.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_hmac, signature)


def check_replay_attack(bin_id: str, timestamp_unix: int) -> bool:
    """
    Check if the telemetry timestamp is too old or has been seen recently.
    """
    current_time = int(time.time())
    
    # Check window
    if abs(current_time - timestamp_unix) > REPLAY_WINDOW_SECONDS:
        return True
        
    nonce_key = f"{bin_id}:{timestamp_unix}"
    if nonce_key in nonce_cache:
        return True
        
    # Add to cache and cleanup old entries
    nonce_cache[nonce_key] = current_time
    keys_to_delete = [k for k, v in nonce_cache.items() if current_time - v > REPLAY_WINDOW_SECONDS]
    for k in keys_to_delete:
        del nonce_cache[k]
        
    return False


def validate_location_plausibility(
    bin_record: SmartBin, 
    reported_lat: float, 
    reported_lon: float, 
    last_reading: Optional[SensorReading] = None
) -> Tuple[bool, str]:
    """
    Verify the reported location against the registered location (Geofencing)
    and physical plausibility (speed/jump from last location).
    """
    registered_coords = (bin_record.location_lat, bin_record.location_lon)
    reported_coords = (reported_lat, reported_lon)
    
    # 1. Geofence Check (must not deviate more than 50 meters from registered location)
    distance_from_base = geodesic(registered_coords, reported_coords).meters
    if distance_from_base > 50:
        return False, f"Geofence violation: Reported location is {distance_from_base:.2f}m from base."
        
    # 2. Physics/Jump Check (if the bin 'moved' too fast since last reading)
    if last_reading:
        last_coords = (last_reading.location_lat, last_reading.location_lon)
        distance_jump = geodesic(last_coords, reported_coords).kilometers
        time_diff_hours = (time.time() - last_reading.timestamp.timestamp()) / 3600
        
        if time_diff_hours > 0:
            speed_kmh = distance_jump / time_diff_hours
            if speed_kmh > 100:  # A bin shouldn't move faster than 100km/h
                return False, f"Impossible speed anomaly: {speed_kmh:.2f} km/h detected."
                
    return True, ""


def process_telemetry_security(
    db: Session, 
    bin_record: SmartBin, 
    payload_dict: dict, 
    signature: str,
    timestamp_unix: int,
    ip_address: str
) -> Tuple[bool, str]:
    """
    Comprehensive security pipeline for incoming telemetry.
    Returns (is_valid, error_reason).
    """
    from app.device_registry import verify_device_status
    from app.location_security import evaluate_location_security, LocationTrustStatus
    from app.sensor_trust import evaluate_sensor_trust_matrix

    # 0. Strong Device Identity & Trust Lifecycle Check
    dev_ok, dev_msg = verify_device_status(db, bin_record.bin_id)
    if not dev_ok:
        log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_record.bin_id, f"Rejected: {dev_msg}", ip_address, "CRITICAL")
        return False, f"Device access denied: {dev_msg}"

    # Nonce check if present
    nonce = payload_dict.get("nonce")
    if nonce:
        nonce_key = f"{bin_record.bin_id}:nonce:{nonce}"
        if nonce_key in nonce_cache:
            log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_record.bin_id, "Duplicate nonce reused", ip_address, "HIGH")
            return False, "Duplicate nonce: Replay attempt detected"
        nonce_cache[nonce_key] = time.time()

    # 1. Verify Signature (Authentication & Integrity)
    # Reconstruct payload string deterministically for signing
    payload_str = f"{bin_record.bin_id}|{timestamp_unix}|{payload_dict.get('fill_level')}|{payload_dict.get('temperature')}"
    
    if not verify_device_signature(bin_record.bin_id, payload_str, signature, bin_record.device_key):
        bin_record.status = BinStatus.COMPROMISED
        log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_record.bin_id, "Invalid HMAC signature", ip_address, "CRITICAL")
        return False, "Invalid signature"
        
    # 2. Replay Attack Prevention
    if check_replay_attack(bin_record.bin_id, timestamp_unix):
        log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_record.bin_id, "Replay attack detected (timestamp reused/expired)", ip_address, "HIGH")
        return False, "Replay attack detected"
        
    # 3. Location Integrity (Anti-Location Manipulation & Geofence)
    reported_lat = payload_dict.get('location_lat')
    reported_lon = payload_dict.get('location_lon')
    seq_num = payload_dict.get('sequence_number')

    loc_status, loc_score, loc_reason = evaluate_location_security(
        db=db,
        bin_record=bin_record,
        reported_lat=reported_lat,
        reported_lon=reported_lon,
        device_timestamp_unix=timestamp_unix,
        sequence_number=seq_num,
        ip_address=ip_address
    )
    
    if loc_status in [LocationTrustStatus.REJECTED, LocationTrustStatus.QUARANTINED]:
        return False, loc_reason
        
    # 4. Multi-Sensor Trust Matrix & Invariants
    fill = payload_dict.get('fill_level', 0)
    temp = payload_dict.get('temperature', 0)
    weight = payload_dict.get('weight_kg')

    sensors_ok, sensor_matrix = evaluate_sensor_trust_matrix(
        db=db,
        bin_id=bin_record.bin_id,
        fill_level=fill,
        temperature=temp,
        weight_kg=weight,
        location_valid=True,
        ip_address=ip_address
    )

    if fill < settings.FILL_LEVEL_MIN or fill > settings.FILL_LEVEL_MAX:
        return False, "Fill level out of physical bounds"
    if temp < settings.TEMPERATURE_MIN or temp > settings.TEMPERATURE_MAX:
        return False, "Temperature out of physical bounds"
        
    return True, ""
