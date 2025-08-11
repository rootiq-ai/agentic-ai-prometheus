"""
Application settings and configuration management.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    api_workers: int = 1
    
    # Prometheus Configuration
    prometheus_url: str = "http://localhost:9090"
    prometheus_timeout: int = 30
    prometheus_max_retries: int = 3
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.3
    
    # Streamlit Configuration
    streamlit_port: int = 8501
    api_base_url: str = "http://localhost:8000"
    
    # Security
    secret_key: Optional[str] = None
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Database (Optional)
    database_url: str = "sqlite:///./prometheus_agent.db"
    
    # Agent Settings
    max_conversation_history: int = 20
    default_time_range_hours: int = 1
    max_query_timeout: int = 60
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour in seconds
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    @validator("openai_api_key")
    def validate_openai_api_key(cls, v):
        if not v or v == "your_openai_api_key_here":
            raise ValueError("OpenAI API key must be provided")
        return v
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Environment variable mapping
        fields = {
            "openai_api_key": {"env": "OPENAI_API_KEY"},
            "prometheus_url": {"env": "PROMETHEUS_URL"},
            "api_host": {"env": "API_HOST"},
            "api_port": {"env": "API_PORT"},
            "streamlit_port": {"env": "STREAMLIT_PORT"},
            "secret_key": {"env": "SECRET_KEY"},
            "database_url": {"env": "DATABASE_URL"},
            "log_level": {"env": "LOG_LEVEL"},
        }

# Global settings instance
settings = Settings()

# Derived configurations
PROMETHEUS_CONFIG = {
    "url": settings.prometheus_url,
    "timeout": settings.prometheus_timeout,
    "max_retries": settings.prometheus_max_retries,
}

OPENAI_CONFIG = {
    "api_key": settings.openai_api_key,
    "model": settings.openai_model,
    "max_tokens": settings.openai_max_tokens,
    "temperature": settings.openai_temperature,
}

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "default": {
            "level": settings.log_level,
            "formatter": settings.log_format,
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": settings.log_level,
            "formatter": settings.log_format,
            "class": "logging.FileHandler",
            "filename": "logs/prometheus_agent.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": settings.log_level,
            "propagate": False,
        },
    },
}
