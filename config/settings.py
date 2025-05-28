"""
Arcadia Platform Configuration
Centralized settings management for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).parent.parent

class Settings:
    """Application settings"""
    
    # Application Info
    APP_NAME: str = os.getenv("APP_NAME", "Arcadia")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://arcadia_user:arcadia_pass@localhost:5432/arcadia")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Game Configuration
    DEFAULT_TOKENS: int = int(os.getenv("DEFAULT_TOKENS", "100"))
    SUBSCRIPTION_PRICE: float = float(os.getenv("SUBSCRIPTION_PRICE", "9.99"))
    CREATOR_REVENUE_SHARE: float = float(os.getenv("CREATOR_REVENUE_SHARE", "0.35"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / "logs"
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL for SQLAlchemy"""
        return cls.DATABASE_URL

# Global settings instance
settings = Settings()
