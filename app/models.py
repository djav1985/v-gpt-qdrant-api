# models.py
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class ActionEnum(str, Enum):
    CREATE = "create"
    DELETE = "delete"
    FORGET = "forget"


class SentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


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
        ...,
        description="The name of the memory bank where the memory will be stored.",  # noqa: E501
        example="personal_bank",
    )
    memory: str = Field(
        ...,
        min_length=1,
        description="The content of the memory to be stored.",
        example="Met Alice at the park",
    )
    sentiment: SentimentEnum = Field(
        ...,
        description="The sentiment associated with the memory.",
        example="positive",
    )
    entities: List[str] = Field(
        ...,
        description="A list of entities identified in the memory.",
        example=["alice"],
    )
    tags: List[str] = Field(
        ...,
        description="A list of tags associated with the memory.",
        example=["friends"],
    )

    @field_validator("entities", "tags", mode="before")
    def split_str_values(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Convert comma-separated strings into list format.
        """
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("memory", mode="before")
    def strip_memory(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v:
            raise ValueError("memory cannot be blank")
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
        ...,
        description="The name of the memory bank to search in.",
        example="personal_bank",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="The search query used to retrieve similar memories.",
        example="Alice park meeting",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=100,
        description="The number of most similar memories to return (1-100).",
        example=5,
    )
    entity: Optional[str] = Field(
        None, description="An entity to filter the search.", example="alice"
    )
    tag: Optional[str] = Field(
        None, description="A tag to filter the search.", example="friends"
    )
    sentiment: Optional[SentimentEnum] = Field(
        None,
        description="The sentiment to filter the search.",
        example="positive",  # noqa: E501
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


class ManageMemoryParams(BaseModel):
    """
    Parameters for managing memories (create, delete, forget).
    """

    memory_bank: str = Field(
        ...,
        description="The name of the memory bank to manage.",
        example="personal_bank",
    )
    action: ActionEnum = Field(
        ...,
        description="Action to perform on the memory bank: create, delete, or forget.",  # noqa: E501
        example="create",
    )
    uuid: Optional[UUID] = Field(
        None,
        description="The UUID of the memory to be forgotten (required for forget).",  # noqa: E501
        example="123e4567-e89b-12d3-a456-426614174000",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"memory_bank": "personal_bank", "action": "create"},
                {"memory_bank": "personal_bank", "action": "delete"},
                {
                    "memory_bank": "personal_bank",
                    "action": "forget",
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                },
            ]
        }
    )

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value

    @model_validator(mode="after")
    def check_uuid_action(self):
        if self.action == ActionEnum.FORGET:
            if self.uuid is None:
                raise ValueError("uuid is required when action is forget")
        elif self.uuid is not None:
            raise ValueError("uuid is only allowed when action is forget")
        return self


class MemoryRecord(BaseModel):
    id: UUID = Field(
        ...,
        description="Unique memory identifier",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    memory: str = Field(
        ...,
        description="Stored memory text",
        example="Met Alice at the park",
    )
    timestamp: datetime = Field(
        ...,
        description="ISO-8601 timestamp when the memory was saved",
        example="2024-01-01T12:00:00Z",
    )
    sentiment: SentimentEnum = Field(
        ...,
        description="Sentiment label associated with the memory",
        example="positive",
    )
    entities: List[str] = Field(
        ...,
        description="Recognized entities in the memory",
        example=["alice"],
    )
    tags: List[str] = Field(
        ...,
        description="Tags associated with the memory",
        example=["friends"],
    )
    score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Similarity score for the recalled memory",
        example=0.85,
    )


class SaveMemoryResponse(BaseModel):
    message: str = Field(
        ...,
        description="Result of the save operation",
        example="Memory saved successfully",
    )


class RecallMemoryResponse(BaseModel):
    results: List[MemoryRecord] = Field(
        ..., description="List of recalled memories matching the query"
    )


class ManageMemoryResponse(BaseModel):
    message: str = Field(
        ...,
        description="Result of the management operation",
        example="Memory Bank 'personal_bank' created successfully",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Explanation of the error",
        example="Invalid API key",
    )
