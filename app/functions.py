import os
import openai
import uuid
from qdrant_client import QdrantClient
from scipy.spatial.distance import cosine
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException

def load_configuration():
    """Loads and returns application configuration details as a tuple."""
    # Set OpenAI API Key globally for the library
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = openai_api_key

    # Initialize and return all configuration details along with QdrantClient
    qdrant_client = QdrantClient(
        url=f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{int(os.getenv('QDRANT_PORT', 6333))}",
        api_key=os.getenv("QDRANT_API_KEY")
    )

    return (
        os.getenv("BASE_URL", "http://localhost"),
        os.getenv("API_KEY"),
        os.getenv("QDRANT_HOST", "localhost"),
        int(os.getenv("QDRANT_PORT", 6333)),
        os.getenv("QDRANT_API_KEY"),
        qdrant_client,
        openai.api_key
    )

def get_qdrant_client():
    """Simply returns the QdrantClient from the loaded configuration."""
    _, _, _, _, _, qdrant_client, _ = load_configuration()
    return qdrant_client

def calculate_similarity_scores(text_entries, query_embedding):
    results = []
    for entry in text_entries:
        entry_embedding = entry['embedding']
        similarity_score = 1 - cosine(query_embedding, entry_embedding)
        results.append({"text_entry": entry, "similarity_score": similarity_score})
    return results

def get_text_entries(qdrant_client, collection, keywords):
    try:
        # Fetch all points from the specified collection
        response = qdrant_client.http.points_api.get_points(collection_name=collection)
        # If keywords are provided, filter the points by checking if the 'keywords' field in the metadata contains any of the specified keywords
        if keywords:
            filtered_points = []
            for point in response.result.points:
                point_keywords = point.payload.get('keywords', [])
                # Check if any keyword in the list matches the entry's keywords
                if any(keyword in point_keywords for keyword in keywords):
                    filtered_points.append(point)
            return filtered_points
        else:
            return response.result.points
    except Exception as e:
        print(f"Failed to fetch or filter entries from Qdrant: {str(e)}")
        return []  # Return an empty list if there's an error

def generate_unique_identifier():
    # Generate a unique identifier using UUID4
    return str(uuid.uuid4())