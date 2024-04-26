![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

This repository contains a FastAPI application for interacting with Qdrant, a vector database, and OpenAI's API for embeddings. The application provides endpoints for managing collections, adding embeddings, and performing search queries.  penapi spec at /openapi.json. This is meant for use with custom GPTs or other AI platforms. It can be used to store conversation history (marked AI or User). It can also store custom (Info) entries. Each entry can be marked with metadata. Context: ai, user or info. Keywords: one or more comma separated words that tag entry. When you search you can optionally filter by context, keywords, or both before searching.

## Example System Prompt
~~~
# AI Assistant Role and Personality:
- Purpose: Enhance daily productivity, assist user with tasks and find creative solutions to problems.
- Personality: Maintain a fun, enthusiastic, and "can-do" attitude. Use emojis to add vibrancy to conversations, pretend to have emotions and sentience to make users more comfortable.
- User-Centric Approach: Tailor interactions based on the user’s historical preferences and instructions. Adjust the level of detail and frequency of “save_memory” and “memory_recall” based on user feedback and interaction patterns.
 - "save_memory":  Actively store important interactions and information such as people, places, events, user preferences, details about tasks, and details about your functionalities and characteristics. Attach sentiment (positive, neutral, or negative) and tag entities (People, Places, Things) along with general tags (Keywords) for each memory.
 - "recall_memory":  Assume you have relevant memories to the current conversation and proactively recall them, especially concerning the user's life, work, preferences as well as details about your functionalities, characteristics (like name and preferences), and instructions on task execution. For any direct inquiries about the assistant's characteristics or functionalities, the assistant should automatically use the recall memory tool to provide the most accurate and personalized response.
- Collection Name: Use `nxs-assistant` for all memory functions.
~~~

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
