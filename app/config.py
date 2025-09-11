from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str | None = None
    DIM: int | None = None
    QDRANT_HOST: str | None = None
    QDRANT_API_KEY: str | None = None
    EMBEDDING_ENDPOINT: str | None = None
    LOCAL_MODEL: str | None = None
    ROOT_PATH: str = ""
    BASE_URL: str = ""

    @field_validator("DIM", mode="before")
    @classmethod
    def validate_dim(cls, value: str | int | None) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("DIM must be an integer") from exc


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
