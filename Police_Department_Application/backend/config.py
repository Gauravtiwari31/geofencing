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
    mod_core_url: str = Field(
        default="https://localhost:2025",
        description="MoD Core base URL"
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
