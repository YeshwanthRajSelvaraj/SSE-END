"""
Secured Implementation: Answer Submission / Telemetry Ingestion
Improvements:
1. Strong Authentication (HMAC SHA-256 signature verification).
2. SQL Injection Prevention (Using SQLAlchemy ORM parameterized queries).
3. Strict Input Validation (Pydantic schema bounds).
4. Secure Error Handling (Catch exceptions, generic error messages).
5. Audit Logging (Tracks security events).
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import SmartBin, SensorReading
from app.anti_spoofing import verify_device_signature
from app.auth import log_audit, AuditAction

logger = logging.getLogger("secure_ingestion")

def ingest_telemetry_secured(db: Session, bin_id: str, payload: dict, signature: str, device_key: str):
    try:
        # 1. Authentication & Integrity Check
        payload_str = f"{bin_id}|{payload.get('timestamp')}|{payload.get('fill_level')}|{payload.get('temperature')}"
        if not verify_device_signature(bin_id, payload_str, signature, device_key):
            log_audit(db, AuditAction.SPOOFING_DETECTED, None, "SmartBin", bin_id, "Signature mismatch", severity="CRITICAL")
            raise ValueError("Authentication failed. Invalid device signature.")

        # 3. Strict Input Validation (Bounds checking)
        fill = float(payload.get('fill_level', 0))
        temp = float(payload.get('temperature', 0))
        if not (0 <= fill <= 100):
            raise ValueError("Invalid fill level. Must be between 0 and 100.")
        if not (-40 <= temp <= 85):
            raise ValueError("Invalid temperature. Must be between -40 and 85 Celsius.")

        # 2. Parameterized Database Queries (ORM) preventing SQL Injection
        bin_record = db.query(SmartBin).filter(SmartBin.bin_id == bin_id).first()
        if not bin_record:
            raise ValueError("Device not found in registry.")

        reading = SensorReading(
            bin_id=bin_record.id,
            fill_level=fill,
            temperature=temp,
            location_lat=payload.get('location_lat'),
            location_lon=payload.get('location_lon'),
            raw_hmac=signature
        )
        db.add(reading)
        db.commit()
        return {"status": "success"}

    # 4. Secure Error Handling
    except ValueError as ve:
        logger.warning(f"Validation error during ingestion: {ve}")
        return {"status": "error", "message": str(ve)}
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"Database error during ingestion: {se}")
        return {"status": "error", "message": "Internal processing error."}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "message": "An unexpected error occurred."}
