import os
from functools import lru_cache
from pathlib import Path


def _read_dotenv() -> None:
    """Load simple KEY=value entries without overriding real environment variables."""
    env_file = Path(".env")
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class Settings:
    def __init__(self):
        _read_dotenv()
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_name = os.getenv("APP_NAME", "ApplyTrack API")
        self.api_v1_prefix = os.getenv("API_V1_PREFIX", "/api/v1")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./applytrack.db")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.session_ttl_days = int(os.getenv("SESSION_TTL_DAYS", "30"))
        self.session_token_pepper = os.getenv("SESSION_TOKEN_PEPPER", "development-only-change-me")
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/integrations/google/callback")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.token_encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
        if self.app_env.lower() == "production" and self.session_token_pepper == "development-only-change-me":
            raise ValueError("SESSION_TOKEN_PEPPER must be set to a unique secret in production")
        if self.session_ttl_days < 1:
            raise ValueError("SESSION_TTL_DAYS must be at least 1")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
