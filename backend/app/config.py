import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")

    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DB_NAME: str = Field(default="ai_study_planner")

    # ── Auth / JWT ───────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(default="dev_jwt_secret_key_study_planner_adaptive_ai_2026")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # ── AI ───────────────────────────────────────────────────────────────────
    AI_PROVIDER: str = Field(default="mock")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")

    # ── OTP ──────────────────────────────────────────────────────────────────
    OTP_DEMO_MODE: bool = Field(default=True)
    OTP_EXPIRY_SECONDS: int = Field(default=300)
    OTP_RESEND_COOLDOWN_SECONDS: int = Field(default=60)
    OTP_MAX_ATTEMPTS: int = Field(default=5)

    # Real OTP delivery (used when OTP_DEMO_MODE=false)
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM: str = Field(default="")
    SMS_PROVIDER: str = Field(default="")
    FAST2SMS_API_KEY: str = Field(default="")

    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
