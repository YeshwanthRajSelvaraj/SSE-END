"""
Configuration module for Smart Waste Management System.
Uses environment variables with secure defaults.
"""
import os
import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Smart Waste Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEVICE_TOKEN_EXPIRE_HOURS: int = 24
    HMAC_SECRET: str = os.environ.get("HMAC_SECRET", secrets.token_hex(16))

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./waste_management.db")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Sensor Validation Thresholds
    FILL_LEVEL_MIN: float = 0.0
    FILL_LEVEL_MAX: float = 100.0
    TEMPERATURE_MIN: float = -40.0
    TEMPERATURE_MAX: float = 85.0
    FILL_RATE_MAX_CHANGE: float = 30.0  # Max % change per reading interval

    # Geofencing - default city bounds (Chennai)
    GEO_LAT_MIN: float = 12.8
    GEO_LAT_MAX: float = 13.3
    GEO_LON_MIN: float = 80.1
    GEO_LON_MAX: float = 80.4
    MAX_LOCATION_JUMP_KM: float = 5.0  # Max km between consecutive readings

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "security_audit.log"

    # AI & Gemini Intelligence
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
