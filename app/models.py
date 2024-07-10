# models.py
import os
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator


# Class representing the parameters required to save a memory
class SaveParams(BaseModel):
    memory_bank: str = Field(
        ..., description="The name of the memory bank to be created."
    )
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(
        ..., description="A list of entities identified in the memory."
    )
    tags: List[str] = Field(
        ..., description="A list of tags associated with the memory."
    )

    # Validator to split string values into a list by commas
    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


# Class representing the parameters required for searching memories
class SearchParams(BaseModel):
    memory_bank: str = Field(
        ..., description="The name of the memory bank to search in."
    )
    query: str = Field(
        ..., description="The search query used to retrieve similar memories."
    )
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(
        None, description="The sentiment to filter the search."
    )


# Class representing the parameters for managing memories (create, delete, forget)
class ManageMemoryParams(BaseModel):
    memory_bank: str = Field(..., description="The name of the memory bank to manage.")
    action: str = Field(
        ...,
        description="Action to perform on the memory bank: create, delete, or forget.",
    )
    uuid: Optional[str] = Field(
        None, description="The UUID of the memory you want to delete."
    )

    # Validator to ensure the action is one of the specified choices
    @validator("action")
    def validate_action(cls, v):
        if v not in ["create", "delete", "forget"]:
            raise ValueError("Action must be one of: create, delete, forget")
        return v


# Class representing the parameters for generating embeddings
class EmbeddingParams(BaseModel):
    input: Union[str, List[str]]  # The input text or list of texts to embed
    model: str = Field(
        os.getenv("LOCAL_MODEL"), description="The name of the embedding model."
    )
    user: Optional[str] = Field(
        default="unassigned",
        description="Identifier for the user requesting the embedding.",
    )
    encoding_format: Optional[str] = Field(
        default="float", description="Format of the encoding output."
    )

    # Validator to flatten a list of strings into a single string
    @validator("input", pre=True)
    def flatten_input(cls, v):
        if isinstance(v, list):
            return " ".join(v)
        return v

    # Validator to check if the model matches the environment variable LOCAL_MODEL
    @validator("model")
    def validate_model(cls, value):
        if value != os.getenv("LOCAL_MODEL"):
            raise ValueError(
                "Model does not match the environment variable LOCAL_MODEL"
            )
        return value


class ModerationRequest(BaseModel):
    point: str = Field(..., description="The moderation point being handled.")
    params: dict = Field(...,
                         description="The parameters for the moderation request.")

    @validator("point")
    def validate_point(cls, v):
        if v not in {"ping", "app.moderation.input"}:
            raise ValueError(
                'point must be either "ping" or "app.moderation.input"')
        return v
