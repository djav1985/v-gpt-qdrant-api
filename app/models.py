# models.py
from enum import Enum
from typing import List, Optional, Union
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
        ...,
        description="Action to perform on the memory bank: create, delete, or forget.",
    )
    uuid: Optional[str] = Field(
        None,
        description="The UUID of the memory to be forgotten (required for forget).",
    )

    @field_validator("memory_bank")
    def validate_memory_bank(cls, value: str) -> str:
        if not is_valid_identifier(value):
            raise ValueError("Invalid memory bank name.")
        return value
