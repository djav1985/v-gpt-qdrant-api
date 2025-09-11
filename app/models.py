# models.py
import os
from enum import Enum
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator


class ActionEnum(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    FORGET = "forget"


def is_valid_identifier(value: str) -> bool:
    """
    Check if a string is a valid Python identifier.
    """
    return value.isidentifier()


class SaveParams(BaseModel):
    """
    Parameters required to save a memory.
    """

    memory_bank: str = Field(
        ..., description="The name of the memory bank where the memory will be stored."
    )
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(
        ..., description="A list of entities identified in the memory."
    )
    tags: List[str] = Field(
        ..., description="A list of tags associated with the memory."
    )

    @field_validator("entities", "tags", mode="before")
    def split_str_values(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Convert comma-separated strings into list format.
        """
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value


class SearchParams(BaseModel):
    """
    Parameters required for searching memories.
    """

    memory_bank: str = Field(
        ..., description="The name of the memory bank to search in."
    )
    query: str = Field(
        ..., description="The search query used to retrieve similar memories."
    )
    top_k: int = Field(
        5,
        ge=1,
        le=100,
        description="The number of most similar memories to return (1-100).",
    )
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(
        None, description="The sentiment to filter the search."
    )


class ManageMemoryParams(BaseModel):
    """
    Parameters for managing memories (create, delete, forget).
    """

    memory_bank: str = Field(..., description="The name of the memory bank to manage.")
    action: ActionEnum = Field(
        ..., description="Action to perform on the memory bank: create, delete, or forget."
    )
    uuid: Optional[str] = Field(
        None, description="The UUID of the memory to be forgotten (required for forget)."
    )

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value


class EmbeddingParams(BaseModel):
    """
    Parameters for generating embeddings.
    """

    input: Union[str, List[str]] = Field(
        ..., description="The input text or list of texts to embed."
    )
    model: str = Field(
        default=os.getenv("LOCAL_MODEL"),
        description="The name of the embedding model (must match LOCAL_MODEL).",
    )
    user: Optional[str] = Field(
        default="unassigned",
        description="Identifier for the user requesting the embedding.",
    )
    encoding_format: Optional[str] = Field(
        default="float", description="Format of the encoding output."
    )

    @field_validator("input", mode="before")
    def flatten_input(cls, v):
        if isinstance(v, list):
            return " ".join(v)
        return v

    @field_validator("model")
    def validate_model(cls, value: str) -> str:
        expected = os.getenv("LOCAL_MODEL")
        if expected and value != expected:
            raise ValueError(
                f"Model does not match environment variable LOCAL_MODEL ({expected})"
            )
        return value


class MessageResponse(BaseModel):
    """Standard response containing a status message."""

    message: str = Field(..., description="Human-readable description of the result")


class MemoryRecord(BaseModel):
    """Representation of a single stored memory item."""

    id: str = Field(..., description="Unique identifier of the memory")
    memory: str = Field(..., description="Original memory content")
    timestamp: str = Field(..., description="ISO-8601 timestamp when the memory was stored")
    sentiment: Optional[str] = Field(
        None, description="Sentiment label associated with the memory"
    )
    entities: Optional[List[str]] = Field(
        default=None, description="Entities extracted from the memory"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Tags associated with the memory"
    )
    score: Optional[float] = Field(
        None, description="Vector similarity score returned by the search"
    )


class RecallMemoryResponse(BaseModel):
    """Response containing search results for memory recall."""

    results: List[MemoryRecord] = Field(
        ..., description="List of memories ranked by similarity"
    )


class EmbeddingUsage(BaseModel):
    """Token usage statistics for an embedding request."""

    prompt_tokens: int = Field(..., description="Number of tokens in the input text")
    total_tokens: int = Field(..., description="Total tokens processed including output")


class EmbeddingData(BaseModel):
    """Embedding vector returned by the service."""

    object: Literal["embedding"] = Field(
        "embedding", description="Type of the returned object"
    )
    embedding: List[float] = Field(
        ..., description="Embedding vector representing the input text"
    )
    index: int = Field(..., description="Index of the embedding in the batch")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation requests."""

    object: Literal["list"] = Field("list", description="Type of the top-level object")
    data: List[EmbeddingData] = Field(
        ..., description="List containing embedding information for each input"
    )
    model: str = Field(..., description="Name of the embedding model used")
    usage: EmbeddingUsage = Field(
        ..., description="Token usage statistics for the request"
    )
