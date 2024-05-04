import os
import asyncio
from asyncio import Semaphore
from datetime import datetime
from typing import List, Optional, Union

from fastapi import FastAPI, HTTPException, Depends, Request, Security
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

# Now get_embeddings_model simply returns the singleton instance
def get_embeddings_model():
    return SingletonTextEmbedding.get_instance()

# Dependency to get Qdrant client
async def get_qdrant_client(request: Request) -> AsyncQdrantClient:
    db_client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST"),
        prefer_grpc=True,
        grpc_port=6334,
        https=False,
        api_key=os.getenv("QDRANT_API_KEY")
    )
    return db_client

# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# Define a custom Semaphore class with logging
class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self._waiting_tasks = 0
        self._active_tasks = 0

    async def acquire(self):
        print("Attempting to acquire semaphore...")
        self._waiting_tasks += 1
        await super().acquire()
        self._waiting_tasks -= 1
        self._active_tasks += 1
        print(f"Semaphore acquired. Active: {self._active_tasks}, Waiting: {self._waiting_tasks}")

    def release(self):
        print("Releasing semaphore...")
        self._active_tasks -= 1
        super().release()
        print(f"Semaphore released. Active: {self._active_tasks}, Waiting: {self._waiting_tasks}")

    def get_waiting_tasks(self):
        return self._waiting_tasks

    def get_active_tasks(self):
        return self._active_tasks

semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY", "8")))


# Create an instance of the semaphore with logging
semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY", "8")))

# Middleware to limit concurrency and log task status
async def limit_concurrency(request: Request, call_next):
    print(f"New Task: Active tasks now: {semaphore.get_active_tasks()}, Number of pending tasks: {semaphore.get_waiting_tasks()}")
    await semaphore.acquire()  # Acquire semaphore before processing the request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        print(f"Task Complete: Active tasks now: {semaphore.get_active_tasks()}, Number of pending tasks: {semaphore.get_waiting_tasks()}")
        semaphore.release()  # Always release semaphore after processing the request
