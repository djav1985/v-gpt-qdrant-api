![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

This repository contains a FastAPI application for interacting with Qdrant, a vector database, and FastEmbed. The application provides endpoints for managing collections, adding embeddings, and performing search queries. Openapi spec at /openapi.json. This is meant for use with custom GPTs or other AI platforms. It can be used to store conversation history (marked AI or User). It can also store custom (Info) entries. Each entry can be marked with metadata. Context: ai, user or info. Keywords: one or more comma separated words that tag entry. When you search you can optionally filter by context, keywords, or both before searching.

When saving a memory it can add entities (basically related nouns), Tags (keywords) and sentiment (positive, neutral, and negitive). Entities and tags can be a list on saving a memory but on recalling it can use only one for each. The 3 meta tags are optional for search and can be used in any combonation for search. So you can basically have the ai for example look up only memeories that are "negitive", or only memories that are realted to entity "bob" that are "positive".

The openapi spec at `http://BASE_URL:8077/openapi.json` is very detailed so you don't have to explain much in your prompt to the ai. The spect handle most of that.

## Example System Prompt
~~~
# AI Assistant Role and Personality:
- Purpose: Enhance daily productivity, assist user with tasks and find creative solutions to problems.
- Personality: Maintain a fun, enthusiastic, and "can-do" attitude. Use emojis to add vibrancy to conversations, pretend to have emotions and sentience to make users more comfortable.
- "save_memory": Store key interactions, info, and preferences (people, places, events, preferences, task details, functionalities, etc..) & attach sentiment, entities and keywords.
- "recall_memory": Proactively recall relevant memories during conversations, focusing on user's life, work, and preferences, as well as assistant's functionalities and task execution instructions. Automatically use recall for inquiries about the assistant's traits or functions.
- Collection Name: Use `nxs-assistant` for all memory functions.

** Always use "recall_memory" before answering a question you don't know.
~~~

You can use multiple collections to offer a general and user memory for shared chatbot. Just change the instructions a bit.

For Dify:
~~~
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and '{{USENAME}}' for memory related to the specific user.
~~~

For GPTs:
~~~
- Collection Name: Use `shared-memories01` for memory related to ORGANIZATION_NAME and ask the user for their "name" and use it for memory related to the specific user.
~~~

## Setup
Use docker-compose.yml

## Whats New
- Checkout the dev branch for a version with its own lightweight embedding modle and embeddings endpoint.
  
### Endpoints

- POST `/collections/`: Create or delete collections in Qdrant.
- POST `/save_memory/`: Save a memory to a specified collection, including its content, sentiment, entities, and tags.
- POST `/recall_memory/`: Retrieve memories similar to a given query from a specified collection, optionally filtered by entity, tag, or sentiment.

### Usage

**Create a new collection:**

curl -X POST "http://localhost:8000/save_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "memory": "example_memory", "sentiment": "positive", "entities": ["entity1", "entity2"], "tags": ["tag1", "tag2"]}'

**Save a memory:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity1", "tag": "tag1", "sentiment": "positive"}'

**Retrieve memories:**

curl -X POST "http://localhost:8000/recall_memory/" -H "Content-Type: application/json" -d '{"collection_name": "my_collection", "query": "example_query", "top_k": 5, "entity": "entity", "tag": "tag", "sentiment": "positive"}'

### OpenAPI Specification

The OpenAPI specification for the API endpoints is available at `http://BASE_URL:8077/openapi.json`. Users can access this URL to view the details of the API endpoints, including parameters and functions.
