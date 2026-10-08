"""
Verification script for all profile logins and security controls.
"""
import requests

base = 'http://localhost:8001'
passw = 'abc123'

profiles = [
    ('admin', 'admin', 'System Administrator'),
    ('operator', 'operator', 'Operations Dispatcher'),
    ('driver', 'driver', 'Field Driver (Rajesh Kumar)'),
    ('analyst', 'security_auditor', 'SOC Security Analyst')
]

print("=== VERIFYING LOGIN FOR ALL PROFILES ===")
for user, expected_role, name in profiles:
    # 1. Test Login
    res = requests.post(f"{base}/api/auth/login", json={"username": user, "password": passw})
    assert res.status_code == 200, f"Failed login for {user}: {res.status_code} - {res.text}"
    data = res.json()
    token = data["access_token"]
    role = data["role"]
    print(f"[SUCCESS] {name:<32} (username: '{user}') -> HTTP 200, role: '{role}'")

    # 2. Test /api/auth/me with Bearer token
    me_res = requests.get(f"{base}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200, f"Failed /me for {user}: {me_res.status_code}"
    me_data = me_res.json()
    print(f"          -> Verified Bearer Token: user '{me_data['username']}', email: '{me_data['email']}'")

print("\n=== VERIFYING SECURITY AND NEGATIVE TESTS ===")
# 3. Wrong password
res_bad = requests.post(f"{base}/api/auth/login", json={"username": "admin", "password": "wrongpassword!"})
assert res_bad.status_code == 401, f"Expected 401, got {res_bad.status_code}"
print(f"[SECURITY] Bad password rejected -> HTTP {res_bad.status_code}: {res_bad.json().get('detail')}")

# 4. Unknown user
res_fake = requests.post(f"{base}/api/auth/login", json={"username": "unknown_actor", "password": "abc123"})
assert res_fake.status_code == 401, f"Expected 401, got {res_fake.status_code}"
print(f"[SECURITY] Unknown username rejected -> HTTP {res_fake.status_code}: {res_fake.json().get('detail')}")

# 5. Profiles metadata endpoint
prof_res = requests.get(f"{base}/api/auth/profiles")
assert prof_res.status_code == 200, f"Failed /profiles: {prof_res.status_code}"
profiles_list = prof_res.json()["profiles"]
print(f"[PROFILES] /api/auth/profiles returned {len(profiles_list)} operational profiles.")

print("\n=== ALL TEST CHECKS PASSED 100% ===")
