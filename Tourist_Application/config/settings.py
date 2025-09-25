import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_host: str = "0.0.0.0"
    app_port: int = 2040
    debug: bool = True
    
    # Gateway settings
    gateway_url: str = os.getenv("GATEWAY_URL", "http://localhost:2045")
    gateway_mqtt_host: str = os.getenv("GATEWAY_MQTT_HOST", "localhost")
    gateway_mqtt_port: int = int(os.getenv("GATEWAY_MQTT_PORT", "2046"))
    
    # Keycloak settings
    keycloak_url: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    keycloak_realm: str = os.getenv("KEYCLOAK_REALM", "tourism")
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
