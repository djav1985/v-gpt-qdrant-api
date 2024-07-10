import os
from typing import List, Optional, Union, Literal
<<<<<<< HEAD
from pydantic import BaseModel, Field, validator, ValidationError, RootModel

=======
from pydantic import BaseModel, Field, validator, RootModel
>>>>>>> main

class BaseParams(BaseModel):
    operation_type: Literal[
        "save_memory",
        "recall_memory",
        "create_memory_bank",
        "delete_memory_bank",
        "forget_memory"
    ]

<<<<<<< HEAD

class SaveParams(BaseParams):
    operation_type: Literal["save_memory"]
    memory_bank: str = Field(...,
                             description="The name of the memory bank to be created.")
    memory: str = Field(...,
                        description="The content of the memory to be stored.")
    sentiment: str = Field(...,
                           description="The sentiment associated with the memory.")
    entities: List[str] = Field(...,
                                description="A list of entities identified in the memory.")
    tags: List[str] = Field(...,
                            description="A list of tags associated with the memory.")
=======
class SaveParams(BaseParams):
    operation_type: Literal["save_memory"]
    memory_bank: str = Field(..., description="The name of the memory bank to be created.")
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")
>>>>>>> main

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

<<<<<<< HEAD

class SearchParams(BaseParams):
    operation_type: Literal["recall_memory"]
    memory_bank: str = Field(...,
                             description="The name of the memory bank to search in.")
    query: str = Field(...,
                       description="The search query used to retrieve similar memories.")
    top_k: int = Field(
        5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(
        None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(
        None, description="The sentiment to filter the search.")


class CreateMemoryBankParams(BaseParams):
    operation_type: Literal["create_memory_bank"]
    memory_bank: str = Field(...,
                             description="The name of the memory bank to create.")


class DeleteMemoryBankParams(BaseParams):
    operation_type: Literal["delete_memory_bank"]
    memory_bank: str = Field(...,
                             description="The name of the memory bank to delete.")


class ForgetMemoryParams(BaseParams):
    operation_type: Literal["forget_memory"]
    memory_bank: str = Field(
        ..., description="The name of the memory bank containing the memory to forget.")
    uuid: Optional[str] = Field(
        None, description="The UUID of the memory to delete.")

=======
class SearchParams(BaseParams):
    operation_type: Literal["recall_memory"]
    memory_bank: str = Field(..., description="The name of the memory bank to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

class CreateMemoryBankParams(BaseParams):
    operation_type: Literal["create_memory_bank"]
    memory_bank: str = Field(..., description="The name of the memory bank to create.")

class DeleteMemoryBankParams(BaseParams):
    operation_type: Literal["delete_memory_bank"]
    memory_bank: str = Field(..., description="The name of the memory bank to delete.")

class ForgetMemoryParams(BaseParams):
    operation_type: Literal["forget_memory"]
    memory_bank: str = Field(..., description="The name of the memory bank containing the memory to forget.")
    uuid: Optional[str] = Field(None, description="The UUID of the memory to delete.")
>>>>>>> main

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

    @validator("input", pre=True)
    def flatten_input(cls, v):
        if isinstance(v, list):
            return " ".join(v)
        return v

    @validator("model")
    def validate_model(cls, value):
        if value != os.getenv("LOCAL_MODEL"):
            raise ValueError(
                "Model does not match the environment variable LOCAL_MODEL"
            )
        return value

<<<<<<< HEAD

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

class UnifiedParams(RootModel):
    root: Union[SaveParams, SearchParams, CreateMemoryBankParams, DeleteMemoryBankParams,
                ForgetMemoryParams] = Field(..., discriminator="operation_type")
=======
class UnifiedParams(RootModel):
    root: Union[SaveParams, SearchParams, CreateMemoryBankParams, DeleteMemoryBankParams, ForgetMemoryParams] = Field(..., discriminator="operation_type")
>>>>>>> main

    @validator('root')
    def validate_params(cls, v):
        return v
