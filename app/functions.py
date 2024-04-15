import os
import openai
from qdrant_client import QdrantClient

def load_configuration():
    BASE_URL = os.getenv("BASE_URL", "http://localhost")
    API_KEY = os.getenv("API_KEY")
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Set OpenAI API Key globally for the library
    openai.api_key = openai_api_key

    # Initialize the QdrantClient
    qdrant_client = QdrantClient(url=f"http://{qdrant_host}:{qdrant_port}", api_key=qdrant_api_key)

    return BASE_URL, API_KEY, qdrant_host, qdrant_port, qdrant_api_key, qdrant_client
