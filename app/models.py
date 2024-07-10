# /models.py

# Importing standard libraries for operating system interaction and async functionality
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
        ...,
        description="A list of entities identified in the memory. Multiple words allowed.",
    )
    tags: List[str] = Field(
        ...,
        description="A list of tags associated with the memory. Single words allowed.",
    )

    # Validator to split string values into a list by commas for tags (single words)
    @validator("tags", pre=True)
    def split_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v

    # Validator to split string values into a list by commas for entities (multiple words allowed)
    @validator("entities", pre=True)
    def split_entities(cls, v):
        if isinstance(v, str):
            return [entity.strip() for entity in v.split(",") if entity.strip()]
        return v

    # Validator to ensure sentiment is one of the specified choices
    @validator("sentiment")
    def validate_sentiment(cls, v):
        if v not in ["positive", "neutral", "negative"]:
            raise ValueError("Sentiment must be one of: positive, neutral, negative")
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
    entity: Optional[str] = Field(
        None, description="An entity to filter the search. Multiple words allowed."
    )
    tag: Optional[str] = Field(
        None, description="A tag to filter the search. Single word allowed."
    )
    sentiment: Optional[str] = Field(
        None,
        description="The sentiment to filter the search. One of: positive, neutral, negative.",
    )

    # Validator to ensure top_k is numerical
    @validator("top_k")
    def validate_top_k(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError("top_k must be a positive integer")
        return v

    # Validator to ensure sentiment is one of the specified choices
    @validator("sentiment")
    def validate_sentiment(cls, v):
        if v not in ["positive", "neutral", "negative"]:
            raise ValueError("Sentiment must be one of: positive, neutral, negative")
        return v

    # Validator to ensure tag is a single word
    @validator("tag")
    def validate_tag(cls, v):
        if v and " " in v:
            raise ValueError("Tag must be a single word")
        return v


# Class representing the parameters for managing memories (create, delete, forget)
class ManageMemoryParams(BaseModel):
    memory_bank: str = Field(..., description="The name of the memory bank to manage.")
    action: str = Field(
        ...,
        description="Action to perform on the memory bank: create, delete, or forget.",
    )
    uuid: Optional[str] = Field(
        None, description="The UUID of the memory you want to take action on."
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


# Class representing the parameters for a moderation request
class ModerationRequest(BaseModel):
    point: str = Field(..., description="The moderation point being handled.")
    params: dict = Field(..., description="The parameters for the moderation request.")

    # Validator to check if the moderation point is valid
    @validator("point")
    def validate_point(cls, v):
        if v not in {"ping", "app.moderation.input"}:
            raise ValueError('point must be either "ping" or "app.moderation.input"')
        return v
