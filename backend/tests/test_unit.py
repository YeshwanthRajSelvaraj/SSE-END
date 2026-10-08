"""
Unit Tests for Auth and Security Controls.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import hash_password, verify_password, create_access_token
from app.anti_spoofing import verify_device_signature, check_replay_attack
from app.database import Base, engine, SessionLocal
import time

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_unit_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword!", hashed)

def test_device_signature_verification():
    bin_id = "BIN-100"
    device_key = "secret_key"
    payload_str = "BIN-100|1690000000|50.0|30.0"
    
    import hmac
    import hashlib
    valid_signature = hmac.new(device_key.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    
    assert verify_device_signature(bin_id, payload_str, valid_signature, device_key) is True
    assert verify_device_signature(bin_id, payload_str, "invalid_sig", device_key) is False

def test_replay_attack_prevention():
    bin_id = "BIN-200"
    current_time = int(time.time())
    
    # First time should pass
    assert check_replay_attack(bin_id, current_time) is False
    
    # Second time with same timestamp should fail (replay detected)
    assert check_replay_attack(bin_id, current_time) is True
    
    # Old timestamp should fail
    old_time = current_time - 600 # 10 mins ago
    assert check_replay_attack(bin_id, old_time) is True

def test_api_rate_limiting():
    # Attempt to hit an endpoint multiple times to trigger rate limit (or just check the function logic)
    # Since rate limiter is applied as middleware, we can spam an endpoint
    responses = []
    for _ in range(105):
        responses.append(client.get("/api/bins"))
        
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes # Too Many Requests should be triggered
    from app.rate_limiter import reset_rate_limits
    reset_rate_limits()

