import os
import asyncio
from asyncio import Semaphore

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

async def get_embeddings_model():
    return await SingletonTextEmbedding.get_instance()

async def get_qdrant_client(request: Request) -> AsyncQdrantClient:
    db_client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST"),
        prefer_grpc=True,
        grpc_port=6334,
        https=False,
        api_key=os.getenv("QDRANT_API_KEY")
    )
    return db_client

async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if os.getenv("MEMORIES_API_KEY") and (not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

class LoggingSemaphore(Semaphore):
    def __init__(self, value: int):
        super().__init__(value)
        self.total_permits = value
    
    async def acquire(self):
        await super().acquire()
        print(f"Current active tasks: {self.total_permits - self._value}")
    
    def release(self):
        super().release()
        print(f"Current active tasks: {self.total_permits - self._value}")

semaphore = LoggingSemaphore(int(os.getenv("API_CONCURRENCY", "5")))

async def limit_concurrency(request: Request, call_next):
    await semaphore.acquire()
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        semaphore.release()
