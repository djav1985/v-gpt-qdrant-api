<p align="center">
  <img src="v-gpt-qdrant-api.png" width="60%" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">V-GPT-QDRANT-API</h1>
</p>
<p align="center">
    <em>Empower Memory with Scalable Vector Intelligence</em>
</p>
<p align="center">
	<!-- local repository, no metadata badges. -->
<p>
<p align="center">
		<em>Developed with the software and tools below.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat-square&logo=Pydantic&logoColor=white" alt="Pydantic">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat-square&logo=YAML&logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat-square&logo=Docker&logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/NumPy-013243.svg?style=flat-square&logo=NumPy&logoColor=white" alt="NumPy">
	<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&logo=FastAPI&logoColor=white" alt="FastAPI">
</p>

<br><!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary><br>

- [📍 Overview](#-overview)
  - [Available Models](#available-models)
- [🧩 Features](#-features)
- [🗂️ Repository Structure](#️-repository-structure)
- [📦 Modules](#-modules)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
    - [Environment Variables](#environment-variables)
    - [Running the Docker Containers](#running-the-docker-containers)
- [🛠 Project Roadmap](#-project-roadmap)
- [🎗 License](#-license)
</details>
<hr>

## 📍 Overview

The v-gpt-qdrant-api is a FastAPI-based application designed to manage and process memory operations using semantic vector embeddings. By leveraging Qdrant for vector storage and ONNX Runtime for efficient model execution, it facilitates the creation, retrieval, and deletion of memory entities. The project ensures robust interaction between core API services and Qdrant, encapsulating embeddings and memory management functionalities. Its containerized deployment via Docker and environment orchestration through docker-compose seamlessly integrate dependencies, making the system scalable and efficient. This API serves as a powerful tool for applications requiring sophisticated text embedding and memory handling capabilities.

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

---

## 🧩 Features

|    |   Feature         | Description |
|----|-------------------|---------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project uses a FastAPI framework, coupled with Qdrant for vector storage and ONNX Runtime for model execution. Docker and Docker Compose are used for containerization and orchestration. |
| 🔩 | **Code Quality**  | The code appears modular and structured with single responsibility principles. Various files manage dependencies, models, routes, and main application logic, indicating a clean and maintainable codebase. |
| 📄 | **Documentation** | Documentation is spread across the Dockerfile, docker-compose.yml, requirements.txt, and in-code comments. Each file is well-documented to explain its purpose and usage. |
| 🔌 | **Integrations**  | Integrates with Qdrant for vector storage, ONNX Runtime for model inference, and FastAPI for API management. Utilizes Docker for seamless deployment environments. |
| 🧩 | **Modularity**    | The project is modular, with separate files for dependencies, main app logic, routes, and models. This allows for easy extension and maintenance. |
| 🧪 | **Testing**       | Although specific testing frameworks are not mentioned in the provided details, the project can potentially include tests given the structured nature of the code. |
| ⚡️  | **Performance**   | Performance is optimized using ONNX Runtime for efficient model execution and Uvicorn ASGI server to handle asynchronous operations. Docker ensures efficient resource usage. |
| 🛡️ | **Security**      | API key validation is implemented for secure access. Dependencies like python-dotenv are used for managing environment variables securely. |
| 📦 | **Dependencies**  | Key dependencies include `qdrant-client`, `fastembed`, `python-dotenv`, `uvicorn`, `pydantic`, `numpy`, and `onnxruntime`. Managed through `requirements.txt` and Dockerfile. |
| 🚀 | **Scalability**   | Designed for scalability with Docker to handle containerized deployments and Qdrant for efficient vector operations. FastAPI and Uvicorn facilitate handling increased traffic. |

---

## 🗂️ Repository Structure

```sh
└── v-gpt-qdrant-api/
    ├── Dockerfile
    ├── LICENSE
    ├── README.md
    ├── app
    │   ├── __init__.py
    │   ├── dependencies.py
    │   ├── main.py
    │   ├── models.py
    │   └── routes
    ├── docker-compose.yml
    ├── requirements.txt
    └── v-gpt-qdrant-api.png
```

---

## 📦 Modules

<details closed><summary>.</summary>

| File                                     | Summary                                                                                                                                                                                                                                                                                                                        |
| ---                                      | ---                                                                                                                                                                                                                                                                                                                            |
| [Dockerfile](Dockerfile)                 | Facilitates building and deploying the FastAPI-based application by defining a multi-stage Docker build process, installing dependencies into a virtual environment, and setting up the necessary runtime configuration to ensure efficient execution and scalability of the API server within a containerized environment.    |
| [docker-compose.yml](docker-compose.yml) | Define and orchestrate the applications service architecture by setting up essential containers, dependencies, and configurations. Enable seamless interaction between the core memory API and Qdrant service while managing environment-specific variables and storage volumes for model embeddings and Qdrant data.          |
| [requirements.txt](requirements.txt)     | Specify required dependencies for the FastAPI-based application, enabling the integration of key libraries such as Qdrant for vector storage, ONNX Runtime for model execution, and fastembed for embeddings. Ensure environment variable management with python-dotenv and optimize performance with the Uvicorn ASGI server. |

</details>

<details closed><summary>app</summary>

| File                                   | Summary                                                                                                                                                                                                                                                                                                       |
| ---                                    | ---                                                                                                                                                                                                                                                                                                           |
| [dependencies.py](app/dependencies.py) | Manage the initialization and dependencies for text embedding and Qdrant client, ensuring singleton behavior for the text embedding model. Include API key validation for secure access, tailored for seamless integration within the repository’s FastAPI-based architecture.                                |
| [main.py](app/main.py)                 | Launches a FastAPI application for saving memories with a text embedding feature. Initializes necessary dependencies on startup and conditionally includes specific API routes based on environment variables, aligning with the architectures need for modular and scalable endpoint management.             |
| [models.py](app/models.py)             | Define data models essential for various memory operations such as saving, recalling, creating, deleting, and forgetting memory banks. Implement validation logic to ensure the integrity of input data. Facilitate embedding tasks by providing a structured format for input texts and associated metadata. |

</details>

<details closed><summary>app.routes</summary>

| File                                      | Summary                                                                                                                                                                                                                                                                                                                                |
| ---                                       | ---                                                                                                                                                                                                                                                                                                                                    |
| [embeddings.py](app/routes/embeddings.py) | Manage embedding requests by incrementing a global counter, validating API key dependencies, and leveraging an embedding model to generate vector embeddings. Provides detailed response data including model usage, processing times, and error handling, integral to the overall APIs functionality within the repository structure. |
| [memory.py](app/routes/memory.py)         | Manage memory operations in the v-GPT-Qdrant-API repository by enabling creation, retrieval, storage, and deletion of memory entities in a semantic vector database. Utilizes FastAPI for routing and Qdrant for vector operations, ensuring efficient memory handling and search functionalities.                                     |

</details>

---

## 🚀 Getting Started

This guide will help you set up and run the application using Docker Compose.

### Prerequisites

Ensure you have the following installed on your system:

- **Docker**
- **Docker Compose**

### Configuration

Before running the Docker containers, configure the environment variables in the `docker-compose.yml` file. The necessary variables include:

#### Environment Variables

```yaml
QDRANT_HOST: "http://qdrant:6333"  # Set Qdrant host URL
BASE_URL: "http://memories-api/"  # Base URL for the API
QDRANT_API_KEY: "your-qdrant-api-key"  # Environment variable for Qdrant API key (value should be provided)
MEMORIES_API_KEY: "your-optional-api-key"  # Optional API key for authentication
WORKERS: 1  # Number of uvicorn workers; 1 is sufficient for personal use
UVICORN_CONCURRENCY: 64  # Max connections; excess requests are queued or rejected
EMBEDDING_ENDPOINT: True  # Enable embedding endpoint
LOCAL_MODEL: "BAAI/bge-small-en-v1.5"  # Local model name for text embedding; try BAAI/bge-small-en-v1.5 (384) or nomic-ai/nomic-embed-text-v1.5 (768)
DIM: 384  # Dimensions for the embedding model
```
#### Running the Docker Containers

To run the application, use Docker Compose. Navigate to the directory containing your docker-compose.yml file and execute the following command:
```sh
docker-compose up -d
```
This command will start the services defined in the docker-compose.yml file in detached mode. The memories-api service will be available on port 8060 of your host machine.

## 🛠 Project Roadmap


## 🎗 License

This project is protected under the [MIT License](https://opensource.org/license/mit) License.
