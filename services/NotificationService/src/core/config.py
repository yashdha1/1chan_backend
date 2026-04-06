from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SRC_DIR = Path(__file__).resolve().parent.parent
_SERVICE_ROOT = _SRC_DIR.parent


def _normalize_pem(value: str) -> str:
    """Allow single-line .env PEM with literal \\n sequences."""
    s = value.strip()
    if "\\n" in s and "BEGIN" in s:
        s = s.replace("\\n", "\n")
    return s


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            _SERVICE_ROOT / ".env",
            _SRC_DIR / ".env",
            Path(".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    PROJECT_NAME: str = "Notification_Service"

    REDIS_PS_HOST: str = "localhost"
    REDIS_PS_PORT: int = 6382
    REDIS_PS_DB: int = 0
    
    JWT_PUBLIC_KEY: str = ""
    JWT_PUBLIC_KEY_FILE: Path | None = None
    JWT_ALGORITHM: str = "RS256"

    @model_validator(mode="after")
    def _resolve_jwt_pem_keys(self) -> "Settings":
        pub = ""
        if self.JWT_PUBLIC_KEY_FILE is not None:
            pub = _normalize_pem(self.JWT_PUBLIC_KEY_FILE.read_text(encoding="utf-8"))
        elif self.JWT_PUBLIC_KEY.strip():
            pub = _normalize_pem(self.JWT_PUBLIC_KEY)
        if not pub:
            raise ValueError(
                "Auth failed"
            )
        if "BEGIN" not in pub:
            raise ValueError(
                "Auth Failed"
            )
        object.__setattr__(self, "JWT_PUBLIC_KEY", pub)
        return self


settings = Settings()