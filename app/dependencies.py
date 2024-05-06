# dependencies.py
import os
import time
import asyncio
from asyncio import Semaphore
from queue import Queue

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

# This function checks if the provided API key is valid or not
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

class LoggingSemaphore(asyncio.Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self.total_permits = value
        self.task_start_times = {}
        self.request_queue = Queue()

    async def acquire(self):
        task_id = str(id(asyncio.current_task()))[-6:]  # Using the last six digits of the task ID
        if self._value <= 0:
            await self.enqueue_request()
        await super().acquire()
        self.task_start_times[task_id] = time.monotonic()  # Log start time when task acquires the semaphore
        active_tasks = self.total_permits - self._value
        print(f"Task {task_id} acquired semaphore. Currently active tasks: {active_tasks}")

    async def enqueue_request(self):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self.request_queue.put(future)
        await future  # Wait until the semaphore is available

    def release(self):
        task_id = str(id(asyncio.current_task()))[-6:]  # Using the last six digits of the task ID
        start_time = self.task_start_times.pop(task_id, None)
        if start_time is not None:
            elapsed_time = time.monotonic() - start_time
            super().release()
            active_tasks = self.total_permits - self._value
            print(f"Task {task_id} completed in: {elapsed_time:.4f} seconds. Currently active tasks: {active_tasks}")
            if not self.request_queue.empty():
                future = self.request_queue.get()
                future.set_result(None)
        else:
            print("Release called without a corresponding acquire or task ID mismatch.")

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
