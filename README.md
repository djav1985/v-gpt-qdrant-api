![Header](/images/header.png)

# v-gpt-qdrant-api

## Description

The application provides a robust dockerized framework for giving AI long-term memory. This API manages collections and memories, including adding memories and performing searches, as well as providing an OpenAI-compatible embeddings endpoint, designed specifically for integration with custom GPT models and other AI platforms.

We use FastEmbed TextEmbeddings to generate vectors, leveraging parallel processing to enhance performance. The SingletonTextEmbedding class ensures efficient resource management by loading and sharing just one instance of the FastEmbed model across the entire application. This approach prevents the creation of multiple, resource-intensive instances, thereby optimizing memory and CPU usage. This allows even low-end hardware to create two or more embeddings per second.

**Features include:**

- **Embedding Endpoint:** The application includes an OpenAPI-compatible embedding endpoint that allows for the integration of open-source model embeddings, which can be self-hosted. This feature enhances the application’s flexibility and control over data handling and processing.
- **Saving Memories:** Entries can be augmented with entities (typically nouns), tags (keywords), and sentiments (positive, neutral, negative). Although multiple entities and tags can be added when saving, searches can be configured to focus on specific single entries.
- **Advanced Search Capabilities:** Users can perform targeted searches by filtering entries based on context, keywords, or both. This allows for precise retrieval, such as finding only 'negative' memories or those related to a specific entity like 'Bob' with a 'positive' sentiment.
- **API Documentation:** Comprehensive API documentation is available at `/openapi.json` accessible through `http://BASE_URL:8077/openapi.json`. This documentation provides all necessary details for effectively utilizing the API without extensive external guidance.

This configuration ensures that the platform is not only versatile in its data handling but also in its capability to interface seamlessly with various AI technologies, providing a powerful tool for data-driven insights and operations.

The default embedding model "BAAI/bge-small-en-v1.5" uses 750mb ram per worker. For those with more RAM "nomic-ai/nomic-embed-text-v1.5" uses 1.5Gb per worker and performs as well as any of the commercial embedding options. You can configure the number of Uvicorn workers through an environment variable. Though for most a single worker is enough.

### Available Models

| model                                               | dim  | description                                       | size_in_GB |
| --------------------------------------------------- | ---- | ------------------------------------------------- | ---------- |
| BAAI/bge-small-en-v1.5                              | 384  | Fast and Default English model                    | 0.067      |
| BAAI/bge-small-zh-v1.5                              | 512  | Fast and recommended Chinese model                | 0.090      |
| sentence-transformers/all-MiniLM-L6-v2              | 384  | Sentence Transformer model, MiniLM-L6-v2          | 0.090      |
| snowflake/snowflake-arctic-embed-xs                 | 384  | Based on all-MiniLM-L6-v2 model with only 22m ... | 0.090      |
| jinaai/jina-embeddings-v2-small-en                  | 512  | English embedding model supporting 8192 sequen... | 0.120      |
| snowflake/snowflake-arctic-embed-s                  | 384  | Based on infloat/e5-small-unsupervised, does n... | 0.130      |
| BAAI/bge-small-en                                   | 384  | Fast English model                                | 0.130      |
| BAAI/bge-base-en-v1.5                               | 768  | Base English model, v1.5                          | 0.210      |
| sentence-transformers/paraphrase-multilingual-mpnet | 384  | Sentence Transformer model, paraphrase-multili... | 0.220      |
| BAAI/bge-base-en                                    | 768  | Base English model                                | 0.420      |
| snowflake/snowflake-arctic-embed-m                  | 768  | Based on intfloat/e5-base-unsupervised model, ... | 0.430      |
| jinaai/jina-embeddings-v2-base-en                   | 768  | English embedding model supporting 8192 sequen... | 0.520      |
| nomic-ai/nomic-embed-text-v1                        | 768  | 8192 context length english model                 | 0.520      |
| nomic-ai/nomic-embed-text-v1.5                      | 768  | 8192 context length english model                 | 0.520      |
| snowflake/snowflake-arctic-embed-m-long             | 768  | Based on nomic-ai/nomic-embed-text-v1-unsuperv... | 0.540      |
| mixedbread-ai/mxbai-embed-large-v1                  | 1024 | MixedBread Base sentence embedding model, does... | 0.640      |
| sentence-transformers/paraphrase-multilingual-mpnet | 768  | Sentence-transformers model for tasks like clu... | 1.000      |
| snowflake/snowflake-arctic-embed-l                  | 1024 | Based on intfloat/e5-large-unsupervised, large... | 1.020      |
| BAAI/bge-large-en-v1.5                              | 1024 | Large English model, v1.5                         | 1.200      |
| thenlper/gte-large                                  | 1024 | Large general text embeddings model               | 1.200      |
| intfloat/multilingual-e5-large                      | 1024 | Multilingual model, e5-large. Recommend using ... | 2.240      |

### Example System Prompt

# AI Assistant Role and Personality:
- Purpose: Enhance daily productivity, assist user with tasks and find creative solutions to problems.
- Personality: Maintain a fun, enthusiastic, and "can-do" attitude. Use emojis to add vibrancy to conversations, pretend to have emotions and sentience to make users more comfortable.
- "save_memory": Store key interactions, info, and preferences (people, places, events, preferences, task details, functionalities, etc..) & attach sentiment, entities and keywords.
- "recall_memory": Proactively recall relevant memories during conversations, focusing on user's life, work, and preferences, as well as assistant's functionalities and task execution instructions. Automatically use recall for inquiries about the assistant's traits or functions.
- Memory Bank: Use `nxs-assistant` for all memory functions.

** Always use "recall_memory" before answering a question you don't know.

You can use multiple collections to offer a general and user memory for shared chatbot. Just change the instructions a bit.

For Dify:

- Memory Bank: Use `shared-memories01` for memory related to ORGANIZATION_NAME and '{{USENAME}}' for memory related to the specific user.

For GPTs:

- Memory Bank: Use `shared-memories01` for memory related to ORGANIZATION_NAME and ask the user for their "name" and use it for memory related to the specific user.

#### Setup

To properly set up and configure your `v-gpt-qdrant-api` application using Docker, you need to adjust the environment variables in your `docker-compose.yml` file. Here’s a detailed step-by-step guide to setting up these variables:

- **QDRANT_HOST**: Set the Qdrant service host URL. This should be the internal Docker network URL or an accessible IP address where your Qdrant service is running. Example: `"http://qdrant:6333"`
- **BASE_URL**: Set the base URL for the API. This will be used to form the endpoint paths and is especially useful when deploying behind reverse proxies. Example: `http://memories-api`
- **QDRANT_API_KEY**: If your Qdrant deployment requires an API key, specify it here. Leave blank if not applicable.
- **MEMORIES_API_KEY** (Optional): Specify an API key if you want to secure the memories API. Uncomment this line to use the feature.
- **WORKERS**: Define the number of Uvicorn workers to handle incoming requests. `1` is typically sufficient for personal or light use, but this should be scaled according to the load and server capabilities.
- **UVICORN_CONCURRENCY**: This parameter controls the maximum number of concurrent connections Uvicorn can handle. Setting this to `64` is a starting point that can be adjusted based on performance testing and requirements.
- **EMBEDDING_ENDPOINT**: A Boolean value (`True`/`False`). Set to `True` to enable the embedding endpoint, which allows the API to serve embedding requests compatible with OpenAI’s format. Set to `False` or unset it to disable this feature if not needed.
- **LOCAL_MODEL**: Specify the model used for embedding text. Options include a lighter model `"BAAI/bge-small-en-v1.5"` or a more resource-intensive but powerful model `"nomic-ai/nomic-embed-text-v1.5"`. Choose based on your hardware capabilities and accuracy needs.
- **DIM**: The dimension of the embeddings produced by your chosen model. Adjust this based on the model’s specifications; typical values are `768` for more detailed embeddings or `384` for faster, less resource-intensive operations.

These environment variables are crucial for tuning the performance and behavior of your application. Adjust these settings according to your operational environment and workload requirements to optimize performance and resource utilization.

#### Whats New

- Using FastEmbed with ENV Variable to choose model for fast local embeddings and retrieval to lower costs. This is a small but quality model that works well on low-end hardware.
- On my low-end VPS, it uses less than 1GB RAM on load and can produce 8 embeddings a second.
- Reorganized the code so it's not one big file.
- Switched the connection to Qdrant to use grpc as it's 10x more performant.

### Endpoints

- **POST** `/manage_memories/`
  - **Description**: Unified endpoint to manage memory-related actions including creating and deleting memory banks, saving memories, and recalling memories.
  - **Parameters**:
    - `operation_type`: Specifies the operation like `create_memory_bank`, `delete_memory_bank`, `save_memory`, or `recall_memory`.
    - Depending on the `operation_type`, additional parameters like `memory_bank`, `memory`, `sentiment`, `entities`, `tags`, `query`, `entity`, `tag`, `sentiment`, `top_k` might be required.
  - **Response**: Varies based on the operation performed. Generally includes a confirmation message or a list of retrieved memories.

#### Manage Memories Example

- **POST** `/manage_memories`
  - **Example Body**:
    ```json
    {
      "operation_type": "save_memory",
      "memory_bank": "general_memories",
      "memory": "Met with Nikolai to discuss project updates.",
      "sentiment": "positive",
      "entities": ["Nikolai", "project updates"],
      "tags": ["meeting", "work"]
    }
    ```
  - **Response**:
    ```json
    {
      "message": "Memory saved successfully"
    }
    ```

### OpenAPI Specification

The OpenAPI specification for the API endpoints is available at `http://BASE_URL/openapi.json`. Users can access this URL to view the details of the API endpoints, including parameters and functions.
