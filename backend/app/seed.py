"""
Database Seeder for Smart Waste Management System.
Seeds admin user, smart bins, vehicles, drivers, initial readings, and audit logs.
"""
import datetime
import json
from app.database import SessionLocal, init_db
from app.models import (
    User, UserRole, SmartBin, BinStatus, SensorReading, SensorStatus,
    Vehicle, Driver, CollectionRoute, RouteAssignment, RouteStatus,
    AuditLog, AuditAction
)
from app.auth import hash_password

def seed_database():
    init_db()
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).filter(User.username == "admin").first():
            print("Database already contains admin user.")
            return

        print("Seeding initial data...")

        # 1. Users
        # 1. Users for all 4 profiles (password: abc123)
        admin_user = User(
            username="admin",
            email="admin@ecosmart.local",
            hashed_password=hash_password("abc123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        operator_user = User(
            username="operator",
            email="operator@ecosmart.local",
            hashed_password=hash_password("abc123"),
            role=UserRole.OPERATOR,
            is_active=True
        )
        driver_user = User(
            username="driver",
            email="driver@ecosmart.local",
            hashed_password=hash_password("abc123"),
            role=UserRole.DRIVER,
            is_active=True
        )
        analyst_user = User(
            username="analyst",
            email="analyst@ecosmart.local",
            hashed_password=hash_password("abc123"),
            role=UserRole.ANALYST,
            is_active=True
        )
        db.add_all([admin_user, operator_user, driver_user, analyst_user])
        db.commit()
        db.refresh(admin_user)
        db.refresh(operator_user)
        db.refresh(driver_user)
        db.refresh(analyst_user)

        # 2. Smart Bins
        bins_data = [
            ("BIN-001", "super_secret_device_key_for_bin_001", 13.0827, 80.2707, "Central Station, Chennai", 120.0, "Zone A", BinStatus.ACTIVE),
            ("BIN-002", "super_secret_device_key_for_bin_002", 13.0900, 80.2800, "Marina Beach Road, Chennai", 120.0, "Zone A", BinStatus.ACTIVE),
            ("BIN-003", "super_secret_device_key_for_bin_003", 13.0700, 80.2600, "T. Nagar Market, Chennai", 150.0, "Zone B", BinStatus.ACTIVE),
            ("BIN-004", "super_secret_device_key_for_bin_004", 13.0850, 80.2750, "Egmore High Rd, Chennai", 120.0, "Zone A", BinStatus.ACTIVE),
            ("BIN-005", "super_secret_device_key_for_bin_005", 13.0780, 80.2650, "Nungambakkam High Rd, Chennai", 200.0, "Zone B", BinStatus.ACTIVE),
            ("BIN-COMP", "compromised_key_test_bin", 13.1000, 80.2500, "Perambur North, Chennai", 120.0, "Zone C", BinStatus.COMPROMISED),
        ]

        created_bins = []
        for bin_id, key, lat, lon, addr, cap, zone, status in bins_data:
            b = SmartBin(
                bin_id=bin_id,
                device_key=key,
                location_lat=lat,
                location_lon=lon,
                address=addr,
                capacity_liters=cap,
                zone=zone,
                status=status
            )
            db.add(b)
            created_bins.append(b)
        db.commit()

        # Refresh bins
        for b in created_bins:
            db.refresh(b)

        # 3. Sensor Readings (High fill levels for testing optimization)
        readings_data = [
            (created_bins[0], 85.0, 31.5, SensorStatus.NORMAL),
            (created_bins[1], 92.0, 33.0, SensorStatus.WARNING),
            (created_bins[2], 95.0, 34.2, SensorStatus.CRITICAL),
            (created_bins[3], 78.0, 29.8, SensorStatus.NORMAL),
            (created_bins[4], 45.0, 28.0, SensorStatus.NORMAL),
            (created_bins[5], 50.0, 42.0, SensorStatus.MALFUNCTION),
        ]
        for bin_obj, fill, temp, s_status in readings_data:
            r = SensorReading(
                bin_id=bin_obj.id,
                fill_level=fill,
                location_lat=bin_obj.location_lat,
                location_lon=bin_obj.location_lon,
                temperature=temp,
                sensor_status=s_status,
                battery_level=88.5,
                raw_hmac="seeded_reading_hash"
            )
            db.add(r)
        db.commit()

        # 4. Vehicles & Drivers
        v1 = Vehicle(vehicle_id="TRUCK-01", plate_number="TN-01-AB-1234", vehicle_type="compactor", capacity_kg=5000, is_available=True)
        v2 = Vehicle(vehicle_id="TRUCK-02", plate_number="TN-01-CD-5678", vehicle_type="tipper", capacity_kg=3500, is_available=True)
        d1 = Driver(driver_id="DRV-001", name="Rajesh Kumar", license_number="TN-LIC-8891", phone="+919876543210", is_available=True)
        d2 = Driver(driver_id="DRV-002", name="Suresh Babu", license_number="TN-LIC-4421", phone="+919876543211", is_available=True)
        db.add_all([v1, v2, d1, d2])
        db.commit()
        db.refresh(v1)
        db.refresh(d1)

        # 5. Route & Assignment
        route = CollectionRoute(
            route_name="Morning Zone A Priority Route",
            zone="Zone A",
            bin_sequence=json.dumps(["BIN-002", "BIN-001", "BIN-004"]),
            total_distance_km=8.4,
            estimated_time_min=35.0,
            status=RouteStatus.IN_PROGRESS,
            optimized=True,
            created_by=admin_user.id
        )
        db.add(route)
        db.commit()
        db.refresh(route)

        assignment = RouteAssignment(
            route_id=route.id,
            vehicle_id=v1.id,
            driver_id=d1.id,
            assigned_by=admin_user.id,
            scheduled_date=datetime.datetime.utcnow()
        )
        db.add(assignment)

        # 6. Audit Logs
        logs = [
            AuditLog(user_id=None, action=AuditAction.SPOOFING_DETECTED, resource_type="SmartBin", resource_id="BIN-COMP", details="Invalid HMAC signature from unauthenticated probe", ip_address="192.168.1.105", severity="CRITICAL"),
            AuditLog(user_id=None, action=AuditAction.LOCATION_ANOMALY, resource_type="SmartBin", resource_id="BIN-003", details="Geofence alert: coordinates deviated > 50m", ip_address="192.168.1.106", severity="WARNING"),
            AuditLog(user_id=admin_user.id, action=AuditAction.ROUTE_CREATED, resource_type="CollectionRoute", resource_id=str(route.id), details="Morning Zone A Priority Route optimized", ip_address="127.0.0.1", severity="INFO"),
            AuditLog(user_id=admin_user.id, action=AuditAction.LOGIN, resource_type="User", resource_id="admin", details="Admin login successful", ip_address="127.0.0.1", severity="INFO"),
        ]
        db.add_all(logs)
        db.commit()

        # 7. Device Registry & Sensor Health
        from app.models import DeviceRegistryItem, DeviceStatus, SensorHealthRecord, SensorHealthStatus, BinCompositionRecord, SecurityEventRecord
        for b in created_bins:
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

            # Sensor health entries
            for stype in ["ultrasonic", "temperature", "gps", "load_cell", "camera"]:
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

            # Composition entries
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

        # 8. Initial Security Events
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

        print("Database seeded successfully with extended security & intelligence entities!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
