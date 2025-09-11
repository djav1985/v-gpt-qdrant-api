from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings.

    Attributes:
        API_KEY: API authentication key required for requests.
        DIM: Embedding vector dimension.
        QDRANT_HOST: URL of the Qdrant service.
        QDRANT_API_KEY: Optional API key for Qdrant.
        EMBEDDING_ENDPOINT: Optional external embedding endpoint.
        LOCAL_MODEL: Optional identifier for a local embedding model.
        ROOT_PATH: Base path for mounting the API.
        BASE_URL: Public base URL of the service.
    """

    API_KEY: str = Field(..., env="API_KEY")
    DIM: int = Field(..., env="DIM")
    QDRANT_HOST: str = Field(..., env="QDRANT_HOST")
    QDRANT_API_KEY: str | None = None
    EMBEDDING_ENDPOINT: str | None = None
    LOCAL_MODEL: str | None = None
    ROOT_PATH: str = ""
    BASE_URL: str = ""

    @field_validator("DIM", mode="before")
    @classmethod
    def validate_dim(cls, value: str | int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("DIM must be an integer") from exc


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
