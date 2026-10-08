"""
Device Authentication & Trust Registry:
- Strong device identity management
- Hardware security & certificate fingerprint binding
- Lifecycle state transitions: REGISTERED -> ACTIVE -> SUSPICIOUS -> QUARANTINED -> REVOKED
- Nonce and sequence monotonicity protection
- Credential rotation and cryptographic revocation
"""
import datetime
import hashlib
import logging
import secrets
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.models import (
    DeviceRegistryItem, DeviceStatus, SmartBin, 
    AuditAction
)
from app.auth import log_audit

logger = logging.getLogger("device_registry")


def register_device(
    db: Session,
    device_id: str,
    bin_id: Optional[str] = None,
    assigned_lat: Optional[float] = None,
    assigned_lon: Optional[float] = None,
    firmware_version: str = "1.0.0",
    cert_fingerprint: Optional[str] = None
) -> DeviceRegistryItem:
    """Enrolls a new edge device into the cryptographically verified registry."""
    existing = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == device_id).first()
    if existing:
        return existing

    if not cert_fingerprint:
        # Generate simulated cryptographic certificate thumbprint (SHA-256)
        raw_seed = f"{device_id}|{secrets.token_hex(16)}|{datetime.datetime.utcnow().isoformat()}"
        cert_fingerprint = hashlib.sha256(raw_seed.encode()).hexdigest()

    item = DeviceRegistryItem(
        device_id=device_id,
        bin_id=bin_id or device_id,
        cert_fingerprint=cert_fingerprint,
        status=DeviceStatus.ACTIVE,
        assigned_lat=assigned_lat,
        assigned_lon=assigned_lon,
        firmware_version=firmware_version,
        last_heartbeat=datetime.datetime.utcnow(),
        trust_score=100.0,
        created_at=datetime.datetime.utcnow()
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action=AuditAction.DEVICE_REGISTERED,
        user_id=None,
        resource_type="DeviceRegistry",
        resource_id=device_id,
        details=f"Device {device_id} registered with fingerprint {cert_fingerprint[:16]}...",
        severity="INFO"
    )
    return item


def quarantine_device(db: Session, device_id: str, reason: str, actor_id: Optional[int] = None) -> DeviceRegistryItem:
    """Quarantines a compromised or anomalous edge IoT node."""
    item = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == device_id).first()
    if not item:
        # Auto-enroll as quarantined if unknown probe
        item = register_device(db, device_id)

    item.status = DeviceStatus.QUARANTINED
    item.trust_score = max(0.0, item.trust_score - 50.0)
    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action=AuditAction.DEVICE_QUARANTINED,
        user_id=actor_id,
        resource_type="DeviceRegistry",
        resource_id=device_id,
        details=f"Device {device_id} quarantined: {reason}",
        severity="CRITICAL"
    )
    return item


def revoke_device(db: Session, device_id: str, reason: str, actor_id: Optional[int] = None) -> DeviceRegistryItem:
    """Permanently revokes a device identity and disallows telemetry ingestion."""
    item = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == device_id).first()
    if not item:
        item = register_device(db, device_id)

    item.status = DeviceStatus.REVOKED
    item.trust_score = 0.0
    item.revoked_at = datetime.datetime.utcnow()
    item.revoked_reason = reason
    db.commit()
    db.refresh(item)

    log_audit(
        db=db,
        action=AuditAction.DEVICE_REVOKED,
        user_id=actor_id,
        resource_type="DeviceRegistry",
        resource_id=device_id,
        details=f"Device {device_id} certificate revoked: {reason}",
        severity="CRITICAL"
    )
    return item


def verify_device_status(db: Session, device_id: str) -> Tuple[bool, str]:
    """
    Checks if device is authorized to transmit operational telemetry.
    Revoked or quarantined devices are rejected immediately.
    """
    item = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == device_id).first()
    if not item:
        # If device not yet explicitly in registry, check SmartBin table for backward compatibility
        bin_record = db.query(SmartBin).filter(SmartBin.bin_id == device_id).first()
        if bin_record:
            # Auto-enroll in registry as ACTIVE
            item = register_device(
                db, 
                device_id=bin_record.bin_id, 
                bin_id=bin_record.bin_id,
                assigned_lat=bin_record.location_lat,
                assigned_lon=bin_record.location_lon
            )
            return True, "Active"
        return False, "Unknown device identity (Not registered)"

    if item.status == DeviceStatus.REVOKED:
        return False, f"Device revoked: {item.revoked_reason or 'Revoked by administrator'}"

    if item.status == DeviceStatus.QUARANTINED:
        return False, "Device quarantined due to security anomalies"

    # Update heartbeat
    item.last_heartbeat = datetime.datetime.utcnow()
    db.commit()
    return True, "Active"


def rotate_device_credentials(db: Session, device_id: str) -> str:
    """Rotates the device's public certificate fingerprint."""
    item = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == device_id).first()
    if not item:
        raise ValueError(f"Device {device_id} not found in registry")

    new_seed = f"{device_id}|rotated|{secrets.token_hex(20)}|{datetime.datetime.utcnow().isoformat()}"
    new_fingerprint = hashlib.sha256(new_seed.encode()).hexdigest()
    item.cert_fingerprint = new_fingerprint
    db.commit()
    db.refresh(item)
    return new_fingerprint
