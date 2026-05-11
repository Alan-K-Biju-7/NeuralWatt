from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = ""
    mongodb_db_name: str = "neuralwatt"

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    # Device API Key
    device_api_key: str = ""

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: object) -> object:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"release", "prod", "production"}:
                return False
            if lowered in {"dev", "development"}:
                return True
        return value

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
