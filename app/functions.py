import os
from scipy.spatial.distance import cosine
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException

def load_configuration():
    return (
        os.getenv("BASE_URL", "http://localhost"),
        os.getenv("API_KEY"),
    )

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
