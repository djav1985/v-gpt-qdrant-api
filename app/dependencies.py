# dependencies.py
import os
import asyncio
from asyncio import Semaphore

# Third-Party Library Imports
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from qdrant_client import AsyncQdrantClient
from fastembed import TextEmbedding

class SingletonTextEmbedding:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")
        return cls._instance

# Dependency to get embeddings model
async def get_embeddings_model(request: Request = None) -> TextEmbedding:
    return SingletonTextEmbedding.get_instance()
    
class SingletonQdrantClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AsyncQdrantClient(
                host=os.getenv("QDRANT_HOST"),
                prefer_grpc=True,
                grpc_port=6334,
                https=False,
                api_key=os.getenv("QDRANT_API_KEY")
            )
        return cls._instance

# Dependency to get Qdrant client
async def get_qdrant_client(request: Request) -> AsyncQdrantClient:
    return SingletonQdrantClient.get_instance()
    
# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# Define a custom Semaphore class with logging
class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self.total_permits = value

    async def acquire(self):
        await super().acquire()
        active_tasks = self.total_permits - self._value  # Calculate active tasks based on the semaphore's remaining value
        print(f"Current active tasks: {active_tasks}")

    def release(self):
        super().release()
        active_tasks = self.total_permits - self._value  # Update active tasks after releasing

    def get_active_tasks(self):
        return self.total_permits - self._value

# Create an instance of the semaphore with logging
semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY", "5")))

# Middleware to limit concurrency and log task status
async def limit_concurrency(request: Request, call_next):
    await semaphore.acquire()  # Acquire semaphore before processing the request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        semaphore.release()  # Always release semaphore after processing the request
