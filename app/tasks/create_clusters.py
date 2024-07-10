# /tasks/create_clusters.py
import numpy as np
import asyncio
from qdrant_client import models
from sklearn.cluster import DBSCAN
from dependencies import create_qdrant_client, compute_dynamic_dbscan_params

# Function to process collections and update cluster_id fields


async def create_clusters():
    # Create Qdrant client
    Qdrant = await create_qdrant_client()

    try:
        # List all collections
        collections = await Qdrant.get_collections()
        for collection in collections['collections']:
            collection_name = collection['name']
            print(f"Processing collection: {collection_name}")

            # Retrieve all vectors and their IDs from the collection
            response = await Qdrant.scroll(
                collection_name=collection_name,
                limit=1000
            )

            vectors = []
            vector_ids = []
            for point in response['points']:
                vectors.append(point.vector)
                vector_ids.append(point.id)

            if not vectors:
                continue

            vectors = np.array(vectors)

            # Compute dynamic `eps` and `min_samples` for DBSCAN
            eps, min_samples = compute_dynamic_dbscan_params(
                vectors, k=5)  # Adjust `k` based on your data
            print(f"Computed eps: {eps}, min_samples: {min_samples}")

            # Apply DBSCAN clustering with dynamic `eps` and `min_samples`
            dbscan = DBSCAN(eps=eps, min_samples=min_samples).fit(vectors)
            cluster_labels = dbscan.labels_

            # Update cluster_id fields
            updates = []
            for vector_id, cluster_label in zip(vector_ids, cluster_labels):
                updates.append(
                    models.PointStruct(
                        id=vector_id,
                        payload={"cluster_id": int(cluster_label)}
                    )
                )

            await Qdrant.upsert(collection_name=collection_name, points=updates)

        return {"message": "Collections processed and cluster_id fields updated successfully"}
    except Exception as e:
        print(f"Internal server error: {str(e)}")
