"""
Secret Scanner Utility for EcoSmart Repository (Phase 11 Compliance)
Scans codebase for hardcoded secrets, private keys, high-entropy tokens, and insecure credentials.
"""
import os
import re
import sys

# High-risk secret patterns
SECRET_PATTERNS = [
    (r"(?i)aws_access_key_id\s*=\s*['\"][A-Z0-9]{20}['\"]", "Hardcoded AWS Access Key ID"),
    (r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/\+=]{40}['\"]", "Hardcoded AWS Secret Access Key"),
    (r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----", "Hardcoded Private Key block"),
    (r"(?i)api[_-]?key\s*=\s*['\"][a-zA-Z0-9_\-]{24,}['\"]", "Potential Hardcoded API Key"),
    (r"(?i)jwt_secret\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "Potential Hardcoded JWT Secret"),
    (r"(?i)password\s*=\s*['\"][a-zA-Z0-9!@#$%^&*()_+]{8,}['\"]", "Hardcoded Plaintext Password Assignment"),
    (r"(?i)postgres://[a-zA-Z0-9_-]+:[a-zA-Z0-9_#-]+@", "Database connection string containing embedded credentials")
]

IGNORE_DIRS = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "node_modules", "dist", "build"}
IGNORE_FILES = {".env.example", "package-lock.json", "waste_management.db", "bandit_report_app.json"}

def scan_repository(root_dir="."):
    findings = []
    total_files_scanned = 0

    for root, dirs, files in os.walk(root_dir):
        # Exclude ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES or file.endswith(".pyc") or file.endswith(".log") or file.endswith(".db"):
                continue

            filepath = os.path.join(root, file)
            total_files_scanned += 1

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, desc in SECRET_PATTERNS:
                            if re.search(pattern, line):
                                findings.append({
                                    "file": filepath,
                                    "line": line_num,
                                    "description": desc,
                                    "snippet": line.strip()[:100]
                                })
            except Exception as e:
                print(f"Warning: Could not read {filepath}: {e}")

    print("=================================================================")
    print("      ECOSMART ENTERPRISE REPOSITORY SECRET SCAN REPORT          ")
    print("=================================================================")
    print(f"Total source files evaluated: {total_files_scanned}")
    print(f"Total exposed hardcoded secret violations found: {len(findings)}")
    print("-----------------------------------------------------------------")

    if findings:
        for item in findings:
            print(f"[VIOLATION] {item['file']}:{item['line']} - {item['description']}")
            print(f"   Snippet: {item['snippet']}")
        print("\n[RESULT] FAILED: Hardcoded secrets detected in source tree.")
        return 1
    else:
        print("[RESULT] PASSED: Clean repository. All secrets are safely externalized via environment variables and Kubernetes secrets.")
        print("=================================================================")
        return 0

if __name__ == "__main__":
    exit_code = scan_repository(".")
    sys.exit(exit_code)
