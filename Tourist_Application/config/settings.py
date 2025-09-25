import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_host: str = "0.0.0.0"
    app_port: int = 2040
    debug: bool = True
    app_build_version: str = os.getenv("APP_BUILD_VERSION", "1.0.0")
    app_platform: str = os.getenv("APP_PLATFORM", "web")
    app_external_base_url: Optional[str] = os.getenv("APP_EXTERNAL_BASE_URL")
    
    # Gateway settings
    gateway_url: str = os.getenv("GATEWAY_URL", "http://localhost:2045")
    gateway_mqtt_host: str = os.getenv("GATEWAY_MQTT_HOST", "localhost")
    gateway_mqtt_port: int = int(os.getenv("GATEWAY_MQTT_PORT", "2046"))

    # MoD Core settings
    mod_core_base_url: str = os.getenv("MOD_CORE_BASE_URL", "http://localhost:2030")
    mod_core_ingest_endpoint: str = os.getenv("MOD_CORE_INGEST_ENDPOINT", "/v1/app/ingest")
    mod_core_timeout_seconds: int = int(os.getenv("MOD_CORE_TIMEOUT_SECONDS", "10"))
    mod_core_verify_tls: bool = os.getenv("MOD_CORE_VERIFY_TLS", "false").lower() == "true"
    mod_core_enable_forwarding: bool = os.getenv("MOD_CORE_ENABLE_FORWARDING", "true").lower() == "true"
    mod_core_client_cert_path: Optional[str] = os.getenv("MOD_CORE_CLIENT_CERT_PATH")
    mod_core_client_key_path: Optional[str] = os.getenv("MOD_CORE_CLIENT_KEY_PATH")
    mod_core_ca_cert_path: Optional[str] = os.getenv("MOD_CORE_CA_CERT_PATH")
    
    # Keycloak settings
    keycloak_url: str = os.getenv("KEYCLOAK_URL", "https://localhost:2027")
    keycloak_realm: str = os.getenv("KEYCLOAK_REALM", "mod-core")
    keycloak_client_id: str = os.getenv("KEYCLOAK_CLIENT_ID", "tourist-app")
    keycloak_client_secret: Optional[str] = os.getenv("KEYCLOAK_CLIENT_SECRET")
    
    # Device simulation
    device_id: str = os.getenv("DEVICE_ID", "tourist-sim-001")
    
    # Database
    database_url: str = "sqlite:///./config/local.db"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
