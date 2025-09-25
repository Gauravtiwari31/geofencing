"""
Police SEDI Application Configuration
Manages environment variables and application settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://sedi_user:sedi_password@localhost:2036/sedi_db",
        description="Database connection URL"
    )
    postgres_user: str = Field(default="sedi_user", description="PostgreSQL user")
    postgres_password: str = Field(default="sedi_password", description="PostgreSQL password") 
    postgres_db: str = Field(default="sedi_db", description="PostgreSQL database name")
    
    # MoD Core Configuration
    mod_core_enabled: bool = Field(
        default=True,
        description="Enable or disable MoD Core integration"
    )
    mod_core_url: str = Field(
        default="https://localhost:2025",
        description="MoD Core base URL (mTLS endpoint)"
    )
    mod_core_stream_path: str = Field(
        default="/v1/police/stream",
        description="Path for the MoD Core SSE stream"
    )
    mod_core_ack_path: str = Field(
        default="/v1/police/ack",
        description="Path for acknowledging incidents back to MoD Core"
    )
    mod_core_health_path: str = Field(
        default="/health",
        description="Path for health checking MoD Core"
    )
    mod_client_cert_path: str = Field(
        default="/workspace/certs/sedi.crt",
        description="Path to client certificate for mTLS"
    )
    mod_client_key_path: str = Field(
        default="/workspace/certs/sedi.key", 
        description="Path to client private key"
    )
    mod_ca_cert_path: str = Field(
        default="/workspace/certs/ca.crt",
        description="Path to CA certificate"
    )
    mod_core_retry_delay_seconds: int = Field(
        default=5,
        description="Initial delay in seconds before retrying failed MoD Core connections"
    )
    mod_core_retry_backoff_multiplier: float = Field(
        default=2.0,
        description="Backoff multiplier for MoD Core reconnection attempts"
    )
    mod_core_retry_max_delay_seconds: int = Field(
        default=60,
        description="Maximum delay between MoD Core reconnection attempts"
    )
    mod_core_stream_timeout_seconds: int = Field(
        default=65,
        description="Read timeout for MoD Core SSE stream (should exceed server heartbeat interval)"
    )
    mod_core_ack_timeout_seconds: int = Field(
        default=10,
        description="Timeout for acknowledgments sent back to MoD Core"
    )
    mod_core_static_token: Optional[str] = Field(
        default=None,
        description="Optional pre-issued bearer token for MoD Core (skips OIDC token retrieval)"
    )
    mod_core_token_url: Optional[str] = Field(
        default=None,
        description="OIDC token endpoint for MoD Core client credentials flow"
    )
    mod_core_token_audience: Optional[str] = Field(
        default=None,
        description="Audience claim requested when obtaining MoD Core token"
    )
    mod_core_token_scope: str = Field(
        default="openid",
        description="Scope requested when obtaining MoD Core token"
    )
    mod_core_client_id: Optional[str] = Field(
        default=None,
        description="Client ID used for MoD Core token retrieval"
    )
    mod_core_client_secret: Optional[str] = Field(
        default=None,
        description="Client secret used for MoD Core token retrieval"
    )
    
    # OIDC Configuration
    oidc_issuer_url: str = Field(
        default="https://keycloak.example.com/auth/realms/police",
        description="OIDC issuer URL"
    )
    oidc_client_id: str = Field(
        default="sedi-police-app",
        description="OIDC client ID"
    )
    oidc_client_secret: str = Field(
        default="your-client-secret",
        description="OIDC client secret"
    )
    oidc_redirect_uri: str = Field(
        default="https://localhost:2035/auth/callback",
        description="OIDC redirect URI"
    )
    
    # Application Configuration
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="Secret key for JWT signing"
    )
    debug: bool = Field(default=True, description="Debug mode")
    port: int = Field(default=2035, description="Application port")
    host: str = Field(default="0.0.0.0", description="Application host")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Frontend static files
    static_directory: str = Field(
        default="/workspace/frontend/dist",
        description="Directory containing built frontend files"
    )
    
    model_config = {
        "env_file": "/workspace/config.env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }


def get_settings() -> Settings:
    """Get application settings (cached)"""
    return Settings()


# Global settings instance
settings = get_settings()
