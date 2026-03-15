from typing import List, Optional
from pydantic import computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(v: str) -> List[str]:
    """Parse comma-separated CORS origins from env."""
    if not v or not v.strip():
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [x.strip() for x in v.split(",") if x.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    project_name: str = "המחלץ"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/hamachletz"

    # Security
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    # Single admin: password from env (no user table)
    admin_password: str = ""

    # CORS: in .env use comma-separated string, e.g. CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        return _parse_cors_origins(self.cors_origins_str)

    # WhatsApp (optional until 4.1)
    whatsapp_provider: Optional[str] = None  # "twilio" | "greenapi"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None
    greenapi_instance_id: Optional[str] = None
    greenapi_token: Optional[str] = None



settings = Settings()
