# dependencies.py
import os
import asyncio
from asyncio import Semaphore

# Third-Party Library Imports
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from qdrant_client import AsyncQdrantClient
from fastembed import TextEmbedding

# SingletonTextEmbedding Class Definition
class SingletonTextEmbedding:
    _instance = None

    # Method to get the instance of SingletonTextEmbedding
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")
        return cls._instance

# Function to get embeddings model
def get_embeddings_model():
    # Returns the singleton instance
    return SingletonTextEmbedding.get_instance()

# Dependency function to get Qdrant client
async def get_qdrant_client(request: Request) -> AsyncQdrantClient:
    db_client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST"),
        prefer_grpc=True,
        grpc_port=6334,
        https=False,
        api_key=os.getenv("QDRANT_API_KEY")
    )
    return db_client

# Function to validate API key
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    # Checks if the provided API key is valid or not
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# Custom Semaphore class with logging
class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self.total_permits = value

    # Method to acquire semaphore
    async def acquire(self):
        await super().acquire()
        # Calculate active tasks based on the semaphore's remaining value
        active_tasks = self.total_permits - self._value
        print(f"Current active tasks: {active_tasks}")

    # Method to release semaphore
    def release(self):
        super().release()
        # Update active tasks after releasing
        active_tasks = self.total_permits - self._value

    # Method to get active tasks
    def get_active_tasks(self):
        return self.total_permits - self._value

# Create an instance of the semaphore with logging
semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY", "5")))

# Middleware function to limit concurrency and log task status
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
