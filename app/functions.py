import openai
import os
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionDescription

# Load configuration from environment variables
def load_configuration():
    # The base URL for the application, defaulting to "http://localhost"
    BASE_URL = os.getenv("BASE_URL", "http://localhost")

    # The API key for authentication
    API_KEY = os.getenv("API_KEY")

    # Environment variables
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
    qdrant_api_key = os.getenv('QDRANT_API_KEY', '')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    # Configure Qdrant client
    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port, api_key=qdrant_api_key)
    openai.api_key = openai_api_key
    return BASE_URL, API_KEY