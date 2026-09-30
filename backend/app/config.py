import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"
if not ENV_PATH.exists():
    ENV_PATH = BASE_DIR.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

class Settings:
    RAW_DB_URL: str = os.getenv(
        "MARKAZI_DB_URL",
        "postgresql://dbadmin:dbadmin@127.0.0.1:5432/markazi_qa_is",
    )
    DB_URL: str = RAW_DB_URL.replace("postgresql+psycopg://", "postgresql://")

    US_DB_URL: str = os.getenv(
        "MARKAZI_US_DB_URL",
        "postgresql://dbadmin:dbadmin@127.0.0.1:5432/markazi_qa_us",
    ).replace("postgresql+psycopg://", "postgresql://")
    LS_DB_URL: str = os.getenv(
        "MARKAZI_LS_DB_URL",
        "postgresql://dbadmin:dbadmin@127.0.0.1:5432/markazi_qa_ls",
    ).replace("postgresql+psycopg://", "postgresql://")
    IS_DB_URL: str = os.getenv(
        "MARKAZI_IS_DB_URL",
        DB_URL,
    ).replace("postgresql+psycopg://", "postgresql://")
    
    DB_MIN_CONNECTIONS: int = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
    DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
    DB_QUERY_TIMEOUT_MS: int = int(os.getenv("DB_QUERY_TIMEOUT_MS", "4000"))

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
    
    QDRANT_STORAGE_PATH: str = str(BASE_DIR / "data" / "qdrant")
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

settings = Settings()
