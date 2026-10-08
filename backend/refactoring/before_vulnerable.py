"""
Vulnerable Implementation: Answer Submission / Telemetry Ingestion
Security Weaknesses:
1. No Authentication/Authorization (Anyone can send data without verification).
2. SQL Injection vulnerability (Direct string formatting in SQL).
3. No Input Validation (Missing bounds check for physical values).
4. No Exception Handling (Can crash server or leak stack traces).
"""
import sqlite3

def ingest_telemetry_vulnerable(bin_id, fill_level, temperature):
    # 1. No auth check! Anyone calling this function can inject data.
    
    # 2. SQL Injection vulnerability
    conn = sqlite3.connect('waste_management.db')
    cursor = conn.cursor()
    
    query = f"INSERT INTO sensor_readings (bin_id, fill_level, temperature) VALUES ('{bin_id}', {fill_level}, {temperature})"
    
    # 3. No validation (temperature could be 9999999, fill_level could be negative)
    
    # 4. No error handling, will throw raw DB exception to caller if something fails
    cursor.execute(query)
    conn.commit()
    conn.close()
    
    return "Data inserted successfully"
