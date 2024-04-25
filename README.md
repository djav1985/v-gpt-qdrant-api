![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

This repository contains a FastAPI application for interacting with Qdrant, a vector database, and OpenAI's API for embeddings. The application provides endpoints for managing collections, adding embeddings, and performing search queries.  penapi spec at /openapi.json. This is meant for use with custom GPTs or other AI platforms. It can be used to store conversation history (marked AI or User). It can also store custom (Info) entries. Each entry can be marked with metadata. Context: ai, user or info. Keywords: one or more comma separated words that tag entry. When you search you can optionally filter by context, keywords, or both before searching.

## Setup

Install the required dependencies by running:

pip install -r requirements.txt

Set up your environment variables for Qdrant and OpenAI API keys. Make sure you have appropriate permissions and access levels.

Start the FastAPI application by running:

uvicorn main:app --reload

## Endpoints

- POST `/collections/`: Create or delete collections in Qdrant.
- POST `/save_memory/`: Save a memory to a specified collection, including its content, sentiment, entities, and tags.
- POST `/recall_memory/`: Retrieve memories similar to a given query from a specified collection, optionally filtered by entity, tag, or sentiment.

## Usage

**Create a new collection:**

curl -X POST "http://localhost:8000/save_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "memory": "example_memory", "sentiment": "positive", "entities": ["entity1", "entity2"], "tags": ["tag1", "tag2"]}'

**Save a memory:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity1", "tag": "tag1", "sentiment": "positive"}'

**Retrieve memories:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity1", "tag": "tag1", "sentiment": "positive"}'

## OpenAPI Specification

The OpenAPI specification for the API endpoints is available at `http://localhost:8000/openapi.json`. Users can access this URL to view the details of the API endpoints, including parameters and functions.
