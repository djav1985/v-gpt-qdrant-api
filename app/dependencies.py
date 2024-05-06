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
        return AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST"),
            prefer_grpc=True,
            grpc_port=6334,
            https=False,
            api_key=os.getenv("QDRANT_API_KEY")
        )

# Dependency to get Qdrant client
async def get_qdrant_client():
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
        self.task_start_times = {}  # Dictionary to store task start times

    async def acquire(self):
        task_id = asyncio.current_task().get_name()  # Get the name of the current task
        self.task_start_times[task_id] = time.monotonic()  # Store the start time of the task
        await super().acquire()

    def release(self):
        task_id = asyncio.current_task().get_name()
        start_time = self.task_start_times.pop(task_id)  # Retrieve and remove the task's start time
        elapsed_time = time.monotonic() - start_time
        super().release()
        active_tasks = self.total_permits - self._value  # Calculate active tasks after releasing
        print(f"Task completed in: {elapsed_time:.4f} seconds. Current active tasks: {active_tasks}")

    def get_active_tasks(self):
        return self.total_permits - self._value

# Create an instance of the semaphore with logging
semaphore = LoggingSemaphore(int(os.getenv("API_CONCERNS", "8")))

# Middleware to limit concurrency and log task status
async def limit_concurrency(request: Request, call_next):
    await semaphore.acquire()  # Acquire semaphore before processing the request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error processing request: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    finally:
        semaphore.release()  # Always release semaphore after processing
