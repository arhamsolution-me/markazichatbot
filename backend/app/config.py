import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR.parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

POSTGRES_PREFIX = "postgresql://"
DEFAULT_DB_PORT = 5432


def _encode_auth_part(val: str) -> str:
    """Safely percent-encode credentials without double-encoding."""
    return urllib.parse.quote_plus(urllib.parse.unquote(val)) if val else ""


def _build_auth_segment(user: str, password: str) -> str:
    """Build URI user:password@ authentication segment."""
    if not user:
        return ""
    enc_user = _encode_auth_part(user)
    if not password:
        return f"{enc_user}@"
    enc_pass = _encode_auth_part(password)
    return f"{enc_user}:{enc_pass}@"


def _parse_port(val: str) -> int:
    """Parse port number with safe fallback to DEFAULT_DB_PORT."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return DEFAULT_DB_PORT


@dataclass(frozen=True)
class DatabaseConfig:
    """Strongly typed, immutable database configuration."""

    host: str = ""
    port: int = DEFAULT_DB_PORT
    user: str = ""
    password: str = ""
    name: str = ""

    @property
    def dsn(self) -> str:
        """Construct standard PostgreSQL connection URI with safely encoded credentials."""
        if not self.host or not self.name:
            return ""
        auth = _build_auth_segment(self.user, self.password)
        return f"{POSTGRES_PREFIX}{auth}{self.host}:{self.port}/{self.name}"

    @property
    def safe_dsn(self) -> str:
        """Construct connection URI with password masked for safe logging and diagnostics."""
        if not self.host or not self.name:
            return ""
        auth = f"{self.user}:****@" if self.user else ""
        return f"{POSTGRES_PREFIX}{auth}{self.host}:{self.port}/{self.name}"

    def as_dict(self) -> dict[str, Any]:
        """Return raw connection parameters suitable for psycopg connection kwargs."""
        return {
            "host": self.host,
            "port": self.port,
            "user": urllib.parse.unquote(self.user) if self.user else "",
            "password": urllib.parse.unquote(self.password) if self.password else "",
            "dbname": self.name,
        }

    @classmethod
    def from_env(cls, service_name: str) -> "DatabaseConfig":
        """Resolve database configuration cleanly from environment variables without duplication."""
        svc = service_name.upper()
        host = os.getenv(f"DB_{svc}_HOST") or os.getenv("DB_HOST", "")
        port = _parse_port(os.getenv(f"DB_{svc}_PORT") or os.getenv("DB_PORT", str(DEFAULT_DB_PORT)))
        user = os.getenv(f"DB_{svc}_USER") or os.getenv("DB_USER", "")
        password = os.getenv(f"DB_{svc}_PASSWORD") or os.getenv("DB_PASSWORD", "")
        name = os.getenv(f"DB_{svc}_NAME", "")

        return cls(
            host=host.strip(),
            port=port,
            user=user.strip(),
            password=password.strip(),
            name=name.strip(),
        )


class Settings:
    """Centralized application settings."""

    # Strongly typed multi-database configurations (IS, US, LS)
    is_db: DatabaseConfig = DatabaseConfig.from_env("IS")
    us_db: DatabaseConfig = DatabaseConfig.from_env("US")
    ls_db: DatabaseConfig = DatabaseConfig.from_env("LS")

    # DSN connection URLs as class attributes (avoids python:S100 method naming violation)
    DB_URL: str = is_db.dsn
    RAW_DB_URL: str = is_db.dsn
    IS_DB_URL: str = is_db.dsn
    US_DB_URL: str = us_db.dsn
    LS_DB_URL: str = ls_db.dsn

    # Database Pool Settings
    DB_MIN_CONNECTIONS: int = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
    DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
    DB_QUERY_TIMEOUT_MS: int = int(os.getenv("DB_QUERY_TIMEOUT_MS", "4000"))

    # Groq Settings
    RAW_KEYS: str = os.getenv("GROQ_API_KEYS", "")
    SINGLE_KEY: str = os.getenv("GROQ_API_KEY", "")

    @property
    def groq_keys(self) -> list[str]:
        keys = [k.strip() for k in self.RAW_KEYS.split(",") if k.strip()]
        if not keys and self.SINGLE_KEY:
            keys = [self.SINGLE_KEY.strip()]
        return keys

    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_FALLBACK_MODEL: str = "openai/gpt-oss-20b"
    MAX_TOKENS: int = int(os.getenv("GROQ_OUTPUT_TOKENS", "1800"))

    # Vector & Embedding Settings
    QDRANT_STORAGE_PATH: str = str(BASE_DIR / "data" / "qdrant")
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"


settings = Settings()
