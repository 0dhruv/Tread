"""
Configuration module for the Stock Trading Platform.
Uses pydantic-settings for type-safe environment variable management.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/stock_trading",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=0, ge=0)
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000, ge=1, le=65535)
    API_WORKERS: int = Field(default=4, ge=1, le=32)
    DEBUG: bool = Field(default=False)
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    
    # AI Model Configuration
    GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key (optional)")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key (optional)")
    
    # Data Collection Settings
    MARKET_DATA_UPDATE_INTERVAL: int = Field(
        default=300,
        description="Market data update interval in seconds"
    )
    HISTORICAL_DATA_DAYS: int = Field(
        default=365,
        description="Number of days of historical data to fetch"
    )
    MAX_CONCURRENT_DOWNLOADS: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent stock downloads"
    )
    
    # Application Settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    LOG_LEVEL: str = Field(default="INFO")
    TIMEZONE: str = Field(default="Asia/Kolkata")
    
    # Paper Trading Settings
    INITIAL_PORTFOLIO_VALUE: float = Field(
        default=1000000.0,
        description="Initial portfolio value in INR"
    )
    MAX_POSITION_SIZE: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Maximum position size as fraction of portfolio"
    )
    TRANSACTION_FEE_PERCENT: float = Field(
        default=0.0005,
        description="Transaction fee as decimal (0.05%)"
    )
    
    @field_validator("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    @classmethod
    def api_key_validator(cls, v: str, info) -> str:
        """Validate that at least one AI API key is provided"""
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency function to get settings instance"""
    return settings
