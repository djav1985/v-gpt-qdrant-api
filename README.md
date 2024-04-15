# Qdrant FastAPI Application

## Description
This repository contains a FastAPI application for interacting with Qdrant, a vector database, and OpenAI's API for embeddings. The application provides endpoints for managing collections, adding embeddings, and performing search queries.

This is meant for use with custom GPTs or other AI platforms. It can be used to store conversation history (marked AI or User). It can also store custom (Info) entries. Each entry can be marked with metadata. Context: ai, user or info. Keywords: one or more comma separated words that tag entry. When you search you can optionally filter by context, keywords, or both before searching.

## Setup
1. Clone this repository to your local machine.
2. Install the required dependencies by running:
```bash
pip install -r requirements.txt
```
3. Set up your environment variables for Qdrant and OpenAI API keys. Ensure you have appropriate permissions and access levels.
4. Start the FastAPI application by running:
```bash
uvicorn main:app --reload
```
Once the application is running, you can access the API documentation at http://localhost:8000/docs.

## Endpoints
- **POST /collections/**: Create or delete collections in Qdrant.
- **POST /embeddings/**: Add embeddings to a specified collection using OpenAI's API.
- **GET /search/**: Perform search queries to retrieve results from a collection.

## Usage
- **Create a new collection**:
```bash
curl -X POST "http://localhost:8000/collections/" -H "Content-Type: application/json" -d '{"action": "create", "name": "my_collection"}'
```
- **Add an embedding to a collection**:
```bash
curl -X POST "http://localhost:8000/embeddings/" -H "Content-Type: application/json" -d '{"collection": "my_collection", "content": "example_text_to_embed", "keywords": "example_keyword1, example_keyword2", "context": "user"}'
```
- **Search for embeddings**:
```bash
curl -X GET "http://localhost:8000/embeddings/" -H "Content-Type: application/json" -d '{"collection": "my_collection", "content": "example_text_to_embed", "keywords": "example_keyword1, example_keyword2", "context": "user"}'
```