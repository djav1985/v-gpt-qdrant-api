# dependencies.py
import os
import time
import asyncio
from asyncio import Semaphore

# Third-Party Library Imports
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from qdrant_client import AsyncQdrantClient
from fastembed import TextEmbedding

class SingletonTextEmbedding:
    _instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                cls._instance = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")
        return cls._instance

async def initialize_text_embedding():
    await SingletonTextEmbedding.get_instance()

# Dependency to get embeddings model
async def get_embeddings_model():
    return await SingletonTextEmbedding.get_instance()

class SingletonQdrantClient:
    _instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                cls._instance = await cls.create_instance()
        return cls._instance

    @classmethod
    async def create_instance(cls):
        try:
            # Attempt to create a new instance of AsyncQdrantClient
            return AsyncQdrantClient(
                host=os.getenv("QDRANT_HOST"),
                prefer_grpc=True,
                grpc_port=6334,
                https=False,
                api_key=os.getenv("QDRANT_API_KEY")
            )
        except Exception as e:
            print(f"Failed to create Qdrant client instance: {e}")
            # Handle connection errors and attempt to reconnect
            await asyncio.sleep(5)  # Wait for a short time before retrying
            return await cls.create_instance()  # Recursive call to retry creation

# Method to reconnect Qdrant client if it gets disconnected
async def reconnect_qdrant_client():
    qdrant_client = await get_qdrant_client()
    if not qdrant_client.is_connected():
        # Reinitialize the Qdrant client instance
        SingletonQdrantClient._instance = None
        await get_qdrant_client()

# Dependency to get Qdrant client
async def get_qdrant_client():
    try:
        qdrant_client = await SingletonQdrantClient.get_instance()
        return qdrant_client
    except Exception as e:
        print(f"Error getting Qdrant client: {e}")
        # Attempt to reconnect
        await reconnect_qdrant_client()
        # Retry getting the Qdrant client instance
        return await SingletonQdrantClient.get_instance()

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
        elapsed_time = time.monotonic() - self.task_start_times.pop(task_id)
        print(f"Task completed in: {elapsed_time:.4f} seconds.")

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
        semaphore.release()  # Release semaphore after processing
