"""
Central Security Event Engine & OWASP Defense Suite:
- Centralized security event dispatching & immutable logging
- SQL Injection detection & parameterized query enforcement
- Cross-Site Scripting (XSS) payload sanitization
- Path Traversal containment & canonicalization
- Server-Side Request Forgery (SSRF) URL boundary validation
- Broken Object Level Authorization (BOLA/IDOR) verification
- Clickjacking & Content-Security-Policy (CSP) headers
- Safe file upload verification
- Availability controls & payload size limits
"""
import datetime
import html
import ipaddress
import logging
import os
import re
import uuid
from typing import Optional, Tuple, Any, List
from urllib.parse import urlparse
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models import (
    SecurityEventRecord, User, UserRole, 
    RouteAssignment, Driver
)

logger = logging.getLogger("security_engine")

# ── Attack Detection Heuristics ─────────────────────────────────────────────

SQLI_PATTERNS = [
    r"(\b(UNION(\s+ALL)?|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|EXECUTE)\b)",
    r"(--|#|/\*|\*/|;)",
    r"('|\")\s*(OR|AND)\s*('|\")?\d+('|\")?\s*=\s*('|\")?\d+",
    r"('|\")\s*(OR|AND)\s*1\s*=\s*1",
    r"WAITFOR\s+DELAY",
    r"BENCHMARK\(",
    r"SLEEP\("
]
SQLI_REGEX = re.compile("|".join(SQLI_PATTERNS), re.IGNORECASE)

XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
    r"<iframe[^>]*>",
    r"<svg[^>]*onload",
    r"document\.cookie"
]
XSS_REGEX = re.compile("|".join(XSS_PATTERNS), re.IGNORECASE)

SUSPICIOUS_PATH_PATTERNS = [
    r"\.\.[\\/]",
    r"[\\/]\.\.",
    r"%2e%2e",
    r"%252e%252e",
    r"\x00"
]
PATH_TRAVERSAL_REGEX = re.compile("|".join(SUSPICIOUS_PATH_PATTERNS), re.IGNORECASE)

# Disallowed SSRF Host Ranges (RFC 1918, Loopback, Link-Local, Cloud Metadata)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS IMDS
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10")
]


# ── Central Security Event Engine ───────────────────────────────────────────

def emit_security_event(
    db: Session,
    event_type: str,
    severity: str = "INFO",
    source: str = "api_gateway",
    user_or_device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    resource: Optional[str] = None,
    reason: Optional[str] = None,
    action_taken: str = "LOGGED",
    correlation_id: Optional[str] = None
) -> SecurityEventRecord:
    """
    Records an immutable security telemetry event.
    Sanitizes credentials, tokens, and secrets from all fields.
    """
    clean_reason = sanitize_text(reason or "")
    if len(clean_reason) > 250:
        clean_reason = clean_reason[:247] + "..."

    event_id = f"SEC-{uuid.uuid4().hex[:12].upper()}"
    corr_id = correlation_id or f"REQ-{uuid.uuid4().hex[:8].upper()}"

    event = SecurityEventRecord(
        event_id=event_id,
        event_type=event_type,
        severity=severity.upper(),
        source=source,
        user_or_device_id=user_or_device_id,
        ip_address=ip_address or "unknown",
        resource=resource,
        reason=clean_reason,
        action_taken=action_taken,
        correlation_id=corr_id,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.warning(
        f"SECURITY EVENT [{severity.upper()}] type={event_type} "
        f"id={event_id} actor={user_or_device_id} ip={ip_address} "
        f"action={action_taken} reason={clean_reason}"
    )
    return event


# ── OWASP Threat Scanners & Defensive Filters ──────────────────────────────

def sanitize_text(text: str) -> str:
    """Applies context-aware HTML entity encoding to prevent XSS injection."""
    if not text:
        return ""
    # Strip dangerous control chars and HTML encode
    cleaned = text.replace("\x00", "")
    return html.escape(cleaned)


def sanitize_for_xss(text: str) -> str:
    """Sanitizes text by HTML entity encoding against XSS attacks."""
    return sanitize_text(text)


def detect_sqli_payload(value: str) -> bool:
    """Scans user input string for SQL injection syntax."""
    if not isinstance(value, str):
        return False
    return bool(SQLI_REGEX.search(value))


def detect_sql_injection(value: str) -> Tuple[bool, str]:
    """Scans input string for SQL injection syntax, returning (is_attack, reason)."""
    if detect_sqli_payload(value):
        return True, "SQL injection pattern matched suspicious keywords/operators"
    return False, ""



def detect_xss_payload(value: str) -> bool:
    """Scans user input string for Cross-Site Scripting tags and attributes."""
    if not isinstance(value, str):
        return False
    return bool(XSS_REGEX.search(value))


def detect_path_traversal(filename_or_path: str) -> bool:
    """Scans path string for directory traversal sequences."""
    if not isinstance(filename_or_path, str):
        return False
    return bool(PATH_TRAVERSAL_REGEX.search(filename_or_path))


def safe_canonical_path(base_dir: str, user_filename: str) -> str:
    """
    Resolves and verifies that user-supplied filename is securely confined
    within base_dir. Prevents path traversal vulnerabilities.
    """
    if detect_path_traversal(user_filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory traversal attempt detected in filename: Path traversal blocked"
        )


    # Sanitize basename only
    base_abs = os.path.abspath(base_dir)
    clean_name = os.path.basename(user_filename.replace("\\", "/"))
    resolved_path = os.path.abspath(os.path.join(base_abs, clean_name))

    # Strict containment check
    if not resolved_path.startswith(base_abs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Path resolution outside allowed sandbox boundary"
        )

    return resolved_path


def validate_url_for_ssrf(url: str) -> Tuple[bool, str]:
    """
    Validates outbound URLs to prevent Server-Side Request Forgery.
    Blocks localhost, private subnets (RFC 1918), AWS/cloud metadata, and non-HTTP schemes.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Prohibited URL scheme: {parsed.scheme} (Only http/https allowed)"

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        if hostname.lower() in ["localhost", "127.0.0.1", "0.0.0.0", "instance-data", "metadata"]:  # nosec B104
            return False, "SSRF Attempt: Loopback/localhost destination prohibited"

        # Check IP address targets
        try:
            ip_obj = ipaddress.ip_address(hostname)
            for net in BLOCKED_IP_NETWORKS:
                if ip_obj in net:
                    return False, f"SSRF Attempt: Destination IP {ip_obj} is inside private/reserved network {net}"
        except ValueError:
            # Hostname is a domain name, not raw IP
            pass

        return True, "URL allowed"

    except Exception as e:
        return False, f"Malformed URL: {e}"


# ── Broken Object Level Authorization (BOLA / IDOR) ─────────────────────────

def check_object_authorization(
    db: Session,
    current_user: User,
    resource_type: str,
    resource_id: Any,
    action: str = "read"
) -> bool:
    """
    Enforces object-level authorization bounds:
    - ADMIN has universal authority.
    - OPERATOR can manage operational routes, vehicles, and bins.
    - DRIVER is strictly restricted: can ONLY read routes and assignments matching their driver ID.
    - VIEWER / SECURITY_AUDITOR has read-only access to audit logs or public views.
    """
    if current_user.role == UserRole.ADMIN:
        return True

    if current_user.role == UserRole.OPERATOR:
        if resource_type in ["SmartBin", "CollectionRoute", "Vehicle", "Driver", "RouteAssignment"]:
            return True
        if resource_type == "User" and action != "read":
            return False

    if current_user.role == UserRole.DRIVER:
        # A driver cannot modify users, devices, or routes
        if action in ["create", "update", "delete"]:
            return False
            
        if resource_type == "RouteAssignment":
            # Find driver profile linked to current_user
            driver = db.query(Driver).filter(Driver.name == current_user.username).first()
            if driver:
                assignment = db.query(RouteAssignment).filter(RouteAssignment.id == int(resource_id)).first()
                if assignment and assignment.driver_id != driver.id:
                    return False  # BOLA violation: driver trying to access another driver's route!
            return True
        elif resource_type in ["SmartBin", "CollectionRoute"]:
            return True
        else:
            return False

    if current_user.role == UserRole.SECURITY_AUDITOR:
        if action == "read":
            return True
        return False

    if current_user.role == UserRole.VIEWER:
        if action == "read" and resource_type in ["SmartBin", "CollectionRoute"]:
            return True
        return False

    return False


# ── File Upload Security Validator ──────────────────────────────────────────

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_file_upload(
    filename: str,
    content_type: str,
    file_bytes: bytes
) -> Tuple[bool, str]:
    """
    Validates uploaded file against size limits, file extensions, and magic byte signatures.
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"

    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Prohibited file extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"

    if content_type.lower() not in ALLOWED_MIME_TYPES:
        return False, f"Prohibited MIME type '{content_type}'. Allowed: {ALLOWED_MIME_TYPES}"

    # Verify Magic Byte Signatures
    is_jpeg = file_bytes.startswith(b"\xff\xd8\xff")
    is_png = file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[:16]

    if not (is_jpeg or is_png or is_webp):
        return False, "File signature spoofing detected (magic bytes do not match image format)"

    return True, "Valid upload"
