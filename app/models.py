"""Common data models and request/response schemas."""

from enum import Enum
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime
import keyword

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
    constr,
    conlist,
)


class ErrorResponse(BaseModel):
    """Standard error response format across all apps."""
    status: int = Field(..., description="HTTP status code of the error")
    code: str = Field(..., description="Application-specific error identifier")
    message: str = Field(..., description="Human-readable summary of the error")
    details: Optional[str] = Field(
        None, description="Additional information that may help resolve the error"
    )

    model_config = ConfigDict(extra="forbid")


class ActionEnum(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    FORGET = "forget"
    LIST = "list"
    UPDATE = "update"


class SentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


def is_valid_identifier(value: str) -> bool:
    """
    Check if a string is a valid Python identifier.
    """
    return value.isidentifier() and not keyword.iskeyword(value)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SaveParams(StrictBaseModel):
    """
    Parameters required to save a memory.
    """
    memory_bank: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="The name of the memory bank where the memory will be "
        "stored.",
        json_schema_extra={"example": "personal_bank"},
    )
    memory: str = Field(
        ...,
        description="The content of the memory to be stored.",
        json_schema_extra={"example": "Met Alice at the park"},
    )
    sentiment: SentimentEnum = Field(
        ...,
        description="The sentiment associated with the memory.",
        json_schema_extra={"example": "positive"},
    )
    entities: Annotated[list[str], conlist(str, min_length=1)] = Field(
        ...,
        description="A list of entities identified in the memory.",
        json_schema_extra={"example": ["alice"]},
    )
    tags: Annotated[list[str], conlist(str, min_length=1)] = Field(
        ...,
        description="A list of tags associated with the memory.",
        json_schema_extra={"example": ["friends"]},
    )

    @field_validator("entities", "tags", mode="before")
    def split_str_values(cls, v: str | list[str]):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("memory", mode="before")
    def strip_memory(cls, v):
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("memory cannot be blank")
        return v

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value):
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value


class SearchParams(StrictBaseModel):
    """
    Parameters required for searching memories.
    """

    memory_bank: Annotated[
        str, constr(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    ] = Field(
        ...,
        description="The name of the memory bank to search in.",
        json_schema_extra={"example": "personal_bank"},
    )
    query: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="The search query used to retrieve similar memories.",
        json_schema_extra={"example": "Alice park meeting"},
    )
    top_k: int = Field(
        5,
        ge=1,
        le=100,
        description="The number of most similar memories to return (1-100).",
        json_schema_extra={"example": 5},
    )
    entity: Optional[Annotated[str, constr(min_length=1)]] = Field(
        None,
        description="A single entity to filter the search (exact match).",
        json_schema_extra={"example": "alice"},
    )
    entities: Optional[list[Annotated[str, constr(min_length=1)]]] = Field(
        None,
        description="Multiple entities to filter the search (OR logic).",
        json_schema_extra={"example": ["alice", "bob"]},
    )
    tag: Optional[Annotated[str, constr(min_length=1)]] = Field(
        None,
        description="A single tag to filter the search (exact match).",
        json_schema_extra={"example": "friends"},
    )
    tags: Optional[list[Annotated[str, constr(min_length=1)]]] = Field(
        None,
        description="Multiple tags to filter the search (OR logic).",
        json_schema_extra={"example": ["friends", "family"]},
    )
    sentiment: Optional[SentimentEnum] = Field(
        None,
        description="The sentiment to filter the search.",
        json_schema_extra={"example": "positive"},
    )
    min_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0.0–1.0). Results below this are excluded.",
        json_schema_extra={"example": 0.6},
    )

    @field_validator("query", mode="before")
    def strip_query(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("query cannot be blank")
        return v

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value


class ManageMemoryParams(StrictBaseModel):
    """
    Parameters for managing memories (create, delete, forget).
    """

    memory_bank: Annotated[
        str, constr(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    ] = Field(
        ...,
        description="The name of the memory bank to manage.",
        json_schema_extra={"example": "personal_bank"},
    )
    action: ActionEnum = Field(
        ...,
        description=(
            "Action to perform on the memory bank: create, delete, or forget."
        ),
        json_schema_extra={"example": "create"},
    )
    uuid: Optional[UUID] = Field(
        None,
        description=(
            "The UUID of the memory to be forgotten or updated (required for forget and update)."
        ),
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"},
    )
    memory: Optional[str] = Field(
        None,
        description="Updated memory text (required for update action).",
        json_schema_extra={"example": "Met Alice at the coffee shop"},
    )
    sentiment: Optional[SentimentEnum] = Field(
        None,
        description="Updated sentiment (required for update action).",
        json_schema_extra={"example": "positive"},
    )
    entities: Optional[list[str]] = Field(
        None,
        description="Updated list of entities (required for update action).",
        json_schema_extra={"example": ["alice"]},
    )
    tags: Optional[list[str]] = Field(
        None,
        description="Updated list of tags (required for update action).",
        json_schema_extra={"example": ["friends"]},
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"memory_bank": "personal_bank", "action": "create"},
                {"memory_bank": "personal_bank", "action": "delete"},
                {"memory_bank": "personal_bank", "action": "list"},
                {
                    "memory_bank": "personal_bank",
                    "action": "forget",
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                },
                {
                    "memory_bank": "personal_bank",
                    "action": "update",
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "memory": "Met Alice at the coffee shop",
                    "sentiment": "positive",
                    "entities": ["alice"],
                    "tags": ["friends"],
                },
            ]
        },
    )

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value

    @field_validator("entities", "tags", mode="before")
    def split_str_values(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def check_uuid_action(self):
        if self.action == ActionEnum.FORGET:
            if self.uuid is None:
                raise ValueError("uuid is required when action is forget")
            if any(f is not None for f in [self.memory, self.sentiment, self.entities, self.tags]):
                raise ValueError("memory, sentiment, entities, tags are only allowed for update action")
        elif self.action == ActionEnum.UPDATE:
            if self.uuid is None:
                raise ValueError("uuid is required when action is update")
            if self.memory is None:
                raise ValueError("memory is required when action is update")
            if self.sentiment is None:
                raise ValueError("sentiment is required when action is update")
            if self.entities is None:
                raise ValueError("entities is required when action is update")
            if self.tags is None:
                raise ValueError("tags is required when action is update")
        elif self.uuid is not None:
            raise ValueError("uuid is only allowed when action is forget or update")
        elif any(f is not None for f in [self.memory, self.sentiment, self.entities, self.tags]):
            raise ValueError("memory, sentiment, entities, tags are only allowed for update action")
        return self


class MemoryRecord(StrictBaseModel):
    id: UUID = Field(
        ...,
        description="Unique memory identifier",
        json_schema_extra={
            "example": "123e4567-e89b-12d3-a456-426614174000"
        },
    )
    memory: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="Stored memory text",
        json_schema_extra={"example": "Met Alice at the park"},
    )
    timestamp: datetime = Field(
        ...,
        description="ISO-8601 timestamp when the memory was saved",
        json_schema_extra={"example": "2024-01-01T12:00:00Z"},
    )
    sentiment: SentimentEnum = Field(
        ...,
        description="Sentiment label associated with the memory",
        json_schema_extra={"example": "positive"},
    )
    entities: Annotated[list[str], conlist(str, min_length=1)] = Field(
        ...,
        description="Recognized entities in the memory",
        json_schema_extra={"example": ["alice"]},
    )
    tags: Annotated[list[str], conlist(str, min_length=1)] = Field(
        ...,
        description="Tags associated with the memory",
        json_schema_extra={"example": ["friends"]},
    )
    score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Similarity score for the recalled memory",
        json_schema_extra={"example": 0.85},
    )


class SaveMemoryResponse(StrictBaseModel):
    message: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="Result of the save operation",
        json_schema_extra={"example": "Memory saved successfully"},
    )
    uuid: UUID = Field(
        ...,
        description="Unique identifier for the saved memory",
        json_schema_extra={
            "example": "123e4567-e89b-12d3-a456-426614174000"
        },
    )


class RecallMemoryResponse(StrictBaseModel):
    results: list[MemoryRecord] = Field(
        ..., description="List of recalled memories matching the query"
    )


class ManageMemoryResponse(StrictBaseModel):
    message: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="Result of the management operation",
        json_schema_extra={
            "example": "Memory Bank 'personal_bank' created successfully"
        },
    )
    banks: Optional[list[str]] = Field(
        None,
        description="List of available memory bank names (only present for list action).",
        json_schema_extra={"example": ["personal_bank", "shared_bank"]},
    )


class EmbeddingRequest(StrictBaseModel):
    text: Annotated[str, constr(min_length=1)] = Field(
        ...,
        description="Text for which to generate an embedding.",
        json_schema_extra={"example": "Hello world"},
    )


class EmbeddingResponse(StrictBaseModel):
    embedding: Annotated[list[float], conlist(float, min_length=1)] = Field(
        ..., description="Embedding vector", json_schema_extra={"example": [0.1, 0.2]}
    )
