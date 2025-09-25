"""
MoD Core Configuration Management
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "MoD Core Safety Backend"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(
        default="postgresql://moduser:modpass@localhost:2026/modcore",
        env="DATABASE_URL"
    )
    
    # Authentication
    keycloak_url: str = Field(
        default="http://localhost:2027",
        env="KEYCLOAK_URL"
    )
    keycloak_realm: str = Field(default="mod-core", env="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="mod-api", env="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: Optional[str] = Field(default=None, env="KEYCLOAK_CLIENT_SECRET")
    
    # SSL/TLS
    ssl_cert_path: str = Field(default="/workspace/ssl-certs/server.crt", env="SSL_CERT_PATH")
    ssl_key_path: str = Field(default="/workspace/ssl-certs/server.key", env="SSL_KEY_PATH")
    ca_cert_path: str = Field(default="/workspace/ssl-certs/ca.crt", env="CA_CERT_PATH")
    
    # Ethereum
    ethereum_network: str = Field(default="sepolia", env="ETHEREUM_NETWORK")
    ethereum_rpc_url: str = Field(
        default="https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
        env="ETHEREUM_RPC_URL"
    )
    ethereum_private_key: Optional[str] = Field(default=None, env="ETHEREUM_PRIVATE_KEY")
    
    # Redis (for caching and session)
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate limiting
    rate_limit_requests: int = Field(default=60, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # SOS and alerting
    sos_max_response_time: int = Field(default=120, env="SOS_MAX_RESPONSE_TIME")  # seconds
    alert_stream_interval: int = Field(default=5, env="ALERT_STREAM_INTERVAL")  # seconds
    
    # Geofencing
    default_safety_score: int = Field(default=100, env="DEFAULT_SAFETY_SCORE")
    red_zone_penalty: int = Field(default=40, env="RED_ZONE_PENALTY")
    
    # Data retention
    location_retention_days: int = Field(default=30, env="LOCATION_RETENTION_DAYS")
    alert_retention_days: int = Field(default=90, env="ALERT_RETENTION_DAYS")
    
    # Monitoring
    prometheus_port: int = Field(default=2028, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=2029, env="GRAFANA_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
