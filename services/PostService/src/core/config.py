from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 
_SRC_DIR = Path(__file__).resolve().parent.parent
_SERVICE_ROOT = _SRC_DIR.parent

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
    PROJECT_NAME: str = "Post Service"
    JWT_PUBLIC_KEY: str = ""

    @model_validator(mode="after")
    def _resolve_jwt_pem_keys(self) -> "Settings":
        if not self.JWT_PUBLIC_KEY:
            raise ValueError(
                "JWT RS256 requires RSA key material in PEM form. Set JWT_PUBLIC_KEY to PEM string  ."
            )
        object.__setattr__(self, "JWT_PUBLIC_KEY", self.JWT_PUBLIC_KEY)
        return self


settings = Settings()