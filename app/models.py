# models.py
import os
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator

# Class for memory parameters
class from pydantic import BaseModel, Field, validator
from typing import List, Optional

class SaveParams(BaseModel):
    memory_bank: str = Field(..., description="The name of the memory bank to be created.")
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

class SearchParams(BaseModel):
    memory_bank: str = Field(..., description="The name of the memory bank to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

class ManageMemoryParams(BaseModel):
    memory_bank: str = Field(..., description="The name of the memory bank to be created.")
    action: str = Field(..., description="Action to perform on the memory bank: create, delete, or forget.")
    uuid: Optional[str] = Field(None, description="The UUID of the memory you want to delete.")

    @validator('action')
    def validate_action(cls, v):
        if v not in ['create', 'delete', 'forget']:
            raise ValueError('Action must be one of: create, delete, forget')
        return v

# Class for embedding parameters
class EmbeddingParams(BaseModel):
    input: Union[str, List[str]]
    model: str = Field(os.getenv("LOCAL_MODEL"), description="The name of the embedding model.")
    user: Optional[str] = "unassigned"
    encoding_format: Optional[str] = "float"

    @validator('input', pre=True)
    def flatten_input(cls, v):
        if isinstance(v, list):
            return ' '.join(v)
        return v

    @validator("model")
    def validate_model(cls, value):
        if value != os.getenv("LOCAL_MODEL"):
            raise ValueError("Model does not match the environment variable LOCAL_MODEL")
        return value
