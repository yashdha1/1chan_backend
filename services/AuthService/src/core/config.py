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
    PROJECT_NAME: str = "Auth Service"

    # RS256: RSA PEM. Set either inline PEM or *_FILE paths (files win if set).
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_PRIVATE_KEY_FILE: Path | None = None
    JWT_PUBLIC_KEY_FILE: Path | None = None
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    @model_validator(mode="after")
    def _resolve_jwt_pem_keys(self) -> "Settings":
        priv = ""
        if self.JWT_PRIVATE_KEY_FILE is not None:
            priv = _normalize_pem(self.JWT_PRIVATE_KEY_FILE.read_text(encoding="utf-8"))
        elif self.JWT_PRIVATE_KEY.strip():
            priv = _normalize_pem(self.JWT_PRIVATE_KEY)

        pub = ""
        if self.JWT_PUBLIC_KEY_FILE is not None:
            pub = _normalize_pem(self.JWT_PUBLIC_KEY_FILE.read_text(encoding="utf-8"))
        elif self.JWT_PUBLIC_KEY.strip():
            pub = _normalize_pem(self.JWT_PUBLIC_KEY)

        if not priv or not pub:
            raise ValueError(
                "Auth failed"
            )
        if "BEGIN" not in priv or "BEGIN" not in pub:
            raise ValueError(
                "Auth failed"
            )
        object.__setattr__(self, "JWT_PRIVATE_KEY", priv)
        object.__setattr__(self, "JWT_PUBLIC_KEY", pub)
        return self


settings = Settings()