import os
from typing import List, Optional, Dict, Union

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, validator

# Class for memory parameters
class MemoryParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")
    memory: str = Field(..., description="The content of the memory to be stored.")
    sentiment: str = Field(..., description="The sentiment associated with the memory.")
    entities: List[str] = Field(..., description="A list of entities identified in the memory.")
    tags: List[str] = Field(..., description="A list of tags associated with the memory.")

    @validator("entities", "tags", pre=True)
    def split_str_values(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

# Class for search parameters
class SearchParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to search in.")
    query: str = Field(..., description="The search query used to retrieve similar memories.")
    top_k: int = Field(5, description="The number of most similar memories to return.")
    entity: Optional[str] = Field(None, description="An entity to filter the search.")
    tag: Optional[str] = Field(None, description="A tag to filter the search.")
    sentiment: Optional[str] = Field(None, description="The sentiment to filter the search.")

# Class for creating a new collection
class CreateCollectionParams(BaseModel):
    collection_name: str = Field(..., description="The name of the collection to be created.")

# Class for embedding parameters
class EmbeddingParams(BaseModel):
    input: Union[str, List[str]]
    model: str
    user: Optional[str] = "unassigned"
    encoding_format: Optional[str] = "float"

    @validator('input', pre=True)
    def flatten_input(cls, v):
        if isinstance(v, list):
            return ' '.join(v)
        return v
