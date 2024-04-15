import os
import openai
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionDescription

# Load configuration from environment variables
def load_configuration():
    BASE_URL = os.getenv("BASE_URL", "http://localhost")  # Ensure HTTP protocol is included for BASE_URL if needed elsewhere
    API_KEY = os.getenv("API_KEY")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")  # No protocol should be included here
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Initialize the QdrantClient without protocol in the host
    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port, api_key=qdrant_api_key)

    return BASE_URL, API_KEY, qdrant_host, qdrant_port, qdrant_api_key, openai_api_key, qdrant_client
