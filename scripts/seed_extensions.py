"""
Extension seed script for Device Registry, Sensor Health, Waste Composition, and Security Events.
"""
import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import SessionLocal, init_db
from app.models import (
    SmartBin, DeviceRegistryItem, DeviceStatus, SensorHealthRecord, 
    SensorHealthStatus, BinCompositionRecord, SecurityEventRecord,
    WasteClassificationRecord, ClassificationConfidenceStatus
)

def run():
    init_db()
    db = SessionLocal()
    try:
        bins = db.query(SmartBin).all()
        print(f"Found {len(bins)} bins in database.")
        
        # 1. Device Registry & Sensor Health
        for b in bins:
            existing_dev = db.query(DeviceRegistryItem).filter(DeviceRegistryItem.device_id == b.bin_id).first()
            if not existing_dev:
                dev = DeviceRegistryItem(
                    device_id=b.bin_id,
                    bin_id=b.bin_id,
                    cert_fingerprint=f"cert_sha256_{b.bin_id.lower()}_valid_anchor",
                    status=DeviceStatus.QUARANTINED if b.bin_id == "BIN-COMP" else DeviceStatus.ACTIVE,
                    assigned_lat=b.location_lat,
                    assigned_lon=b.location_lon,
                    firmware_version="1.2.0",
                    trust_score=20.0 if b.bin_id == "BIN-COMP" else 100.0,
                    last_heartbeat=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow()
                )
                db.add(dev)

            # Sensor health
            for stype in ["ultrasonic", "temperature", "gps", "load_cell", "camera"]:
                existing_sh = db.query(SensorHealthRecord).filter(
                    SensorHealthRecord.bin_id == b.bin_id,
                    SensorHealthRecord.sensor_type == stype
                ).first()
                if not existing_sh:
                    sh = SensorHealthRecord(
                        bin_id=b.bin_id,
                        sensor_type=stype,
                        status=SensorHealthStatus.TAMPERED if (b.bin_id == "BIN-COMP" and stype == "ultrasonic") else SensorHealthStatus.HEALTHY,
                        last_reading_value=85.0 if stype == "ultrasonic" else 30.0,
                        last_heartbeat=datetime.datetime.utcnow(),
                        anomaly_count=1 if b.bin_id == "BIN-COMP" else 0,
                        details="Operational" if b.bin_id != "BIN-COMP" else "Simulated sensor anomaly"
                    )
                    db.add(sh)

            # Composition
            existing_comp = db.query(BinCompositionRecord).filter(BinCompositionRecord.bin_id == b.bin_id).first()
            if not existing_comp:
                comp = BinCompositionRecord(
                    bin_id=b.bin_id,
                    organic_pct=42.0,
                    plastic_pct=24.5,
                    paper_pct=14.0,
                    cardboard_pct=9.5,
                    glass_pct=4.0,
                    metal_pct=3.5,
                    ewaste_pct=1.5,
                    hazardous_pct=0.5,
                    other_pct=0.5,
                    calculated_at=datetime.datetime.utcnow()
                )
                db.add(comp)

        # 2. Sample Waste Classifications
        if db.query(WasteClassificationRecord).count() == 0:
            samples = [
                ("BIN-001", "Recyclable", "Plastic", "PET Bottle", 96.5, ClassificationConfidenceStatus.AUTOMATIC, "VERIFIED_AUTOMATIC"),
                ("BIN-001", "Recyclable", "Paper", "Newspaper", 92.0, ClassificationConfidenceStatus.AUTOMATIC, "VERIFIED_AUTOMATIC"),
                ("BIN-002", "Recyclable", "Glass", "Glass Bottle", 88.0, ClassificationConfidenceStatus.RULE_VALIDATED, "RULE_VALIDATED"),
                ("BIN-003", "Organic / Wet", None, "Food Waste", 94.0, ClassificationConfidenceStatus.AUTOMATIC, "VERIFIED_AUTOMATIC"),
                ("BIN-004", "Recyclable", "Cardboard", "Cardboard Box", 95.0, ClassificationConfidenceStatus.AUTOMATIC, "VERIFIED_AUTOMATIC"),
                ("BIN-COMP", "Hazardous", None, "Battery", 91.0, ClassificationConfidenceStatus.AUTOMATIC, "CRITICAL_HAZARD")
            ]
            for bid, l1, l2, l3, conf, stat, vstat in samples:
                wc = WasteClassificationRecord(
                    bin_id=bid,
                    level1_category=l1,
                    level2_subcategory=l2,
                    level3_object=l3,
                    confidence_score=conf,
                    status=stat,
                    model_version="v1.2.0-quantized",
                    verification_status=vstat,
                    image_ref=f"img_{bid.lower()}_{l1.lower()[:3]}",
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(wc)

        # 3. Security Events
        if db.query(SecurityEventRecord).count() == 0:
            sec_events = [
                SecurityEventRecord(
                    event_id="SEC-INIT001",
                    event_type="SQL_INJECTION_ATTEMPT",
                    severity="CRITICAL",
                    source="api_gateway_waf",
                    user_or_device_id="unauth_scanner",
                    ip_address="192.168.1.105",
                    resource="/api/bins",
                    reason="SQL injection probe blocked: ' OR 1=1-- detected in query parameter",
                    action_taken="REQUEST_BLOCKED_400",
                    correlation_id="REQ-SEED01",
                    timestamp=datetime.datetime.utcnow()
                ),
                SecurityEventRecord(
                    event_id="SEC-INIT002",
                    event_type="GPS_SPOOFING_SUSPECTED",
                    severity="HIGH",
                    source="telemetry_engine",
                    user_or_device_id="BIN-003",
                    ip_address="192.168.1.106",
                    resource="SmartBin/BIN-003",
                    reason="Geofence breach: Coordinates displaced by 1,760 km from Chennai anchor",
                    action_taken="TELEMETRY_QUARANTINED",
                    correlation_id="REQ-SEED02",
                    timestamp=datetime.datetime.utcnow()
                ),
                SecurityEventRecord(
                    event_id="SEC-INIT003",
                    event_type="INVALID_TELEMETRY_SIGNATURE",
                    severity="CRITICAL",
                    source="hmac_gateway",
                    user_or_device_id="BIN-COMP",
                    ip_address="10.0.2.15",
                    resource="SmartBin/BIN-COMP",
                    reason="Cryptographic signature mismatch: HMAC digest verification failed",
                    action_taken="DEVICE_QUARANTINED",
                    correlation_id="REQ-SEED03",
                    timestamp=datetime.datetime.utcnow()
                )
            ]
            db.add_all(sec_events)

        db.commit()
        print("Extended entities successfully committed to database!")
    finally:
        db.close()

if __name__ == "__main__":
    run()
