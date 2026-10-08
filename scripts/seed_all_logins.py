"""
Database update script to ensure all login profiles exist and have password 'abc123'.
Supports both root and backend SQLite database files.
"""
import sys
import os
import sqlite3

# Ensure app path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.auth import hash_password
from app.models import UserRole

PASSWORD = "abc123"
hashed_pwd = hash_password(PASSWORD)

# Profile definitions: (username, email, enum_name)
PROFILES = [
    ("admin", "admin@ecosmart.local", UserRole.ADMIN.name),
    ("operator", "operator@ecosmart.local", UserRole.OPERATOR.name),
    ("operator1", "operator1@ecosmart.local", UserRole.OPERATOR.name),
    ("driver", "driver@ecosmart.local", UserRole.DRIVER.name),
    ("driver1", "driver1@ecosmart.local", UserRole.DRIVER.name),
    ("rajesh", "rajesh@ecosmart.local", UserRole.DRIVER.name),
    ("analyst", "analyst@ecosmart.local", UserRole.SECURITY_AUDITOR.name),
    ("analyst1", "analyst1@ecosmart.local", UserRole.SECURITY_AUDITOR.name),
]

db_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "waste_management.db")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "waste_management.db")),
]

for db_path in db_paths:
    if not os.path.exists(db_path):
        continue
    print(f"Updating DB at: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cur.fetchone():
        print(f"Users table does not exist in {db_path}, skipping.")
        conn.close()
        continue
        
    for username, email, enum_name in PROFILES:
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            # Update password and role
            cur.execute("""
                UPDATE users 
                SET hashed_password = ?, role = ?, email = ?, is_active = 1 
                WHERE username = ?
            """, (hashed_pwd, enum_name, email, username))
            print(f"  Updated user: {username} ({enum_name}) -> password set to {PASSWORD}")
        else:
            # Insert user
            cur.execute("""
                INSERT INTO users (username, email, hashed_password, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, datetime('now'), datetime('now'))
            """, (username, email, hashed_pwd, enum_name))
            print(f"  Inserted user: {username} ({enum_name}) -> password set to {PASSWORD}")
            
    conn.commit()
    conn.close()

print("\nAll login profiles successfully configured with password 'abc123'.")
