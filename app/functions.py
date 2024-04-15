import os
import openai
from qdrant_client import QdrantClient
from scipy.spatial.distance import cosine
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException

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