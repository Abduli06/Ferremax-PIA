import os
from dataclasses import dataclass
from pathlib import Path


def normalizar_db_url(url: str) -> str:
    """Render/Railway entregan postgres:// o postgresql://; SQLAlchemy+psycopg3 pide +psycopg."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    database_url: str = "sqlite:///./ferremax.db"
    data_dir: Path = Path("datos")

    @classmethod
    def desde_entorno(cls) -> "Settings":
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            database_url=normalizar_db_url(
                os.getenv("DATABASE_URL", "sqlite:///./ferremax.db")
            ),
            data_dir=Path(os.getenv("DATA_DIR", "datos")),
        )
