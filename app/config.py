import osfrom dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file (if it exists)
def load_config():    """Loads configuration variables from environment variables."""
    config = {        "openai_api_key": os.getenv("OPENAI_API_KEY"),        "embeddings_model": os.getenv("EMBEDDINGS_MODEL"),        "qdrant_host": os.getenv("QDRANT_HOST"),        "qdrant_port": int(os.getenv("QDRANT_PORT", 6333)),  # Default port 6333        "vector_size": int(os.getenv("VECTOR_SIZE")),        "distance": os.getenv("DISTANCE", "cosine"),  # Default to cosine distance        "hnsw_config": {            "M": int(os.getenv("HNSW_M", 16)),  # Default M = 16            "ef_construct": int(os.getenv("HNSW_EF_CONSTRUCT", 100)),  # Default ef_construct = 100        },    }
    # Validate required configuration values    required_vars = ["openai_api_key", "embeddings_model", "qdrant_host", "vector_size"]    for var in required_vars:        if not config[var]:            raise ValueError(f"Missing required environment variable: {var}")
    return config```
**Explanation:**
1. **`load_dotenv()`:** This line loads environment variables from a `.env` file in the current directory, if it exists. This is a convenient way to manage your configuration without hardcoding values in your Python code.2. **`load_config()` Function:**   - This function retrieves configuration values from environment variables using `os.getenv()`.   - It provides default values for optional settings like `qdrant_port` and HNSW parameters.   - It validates that required environment variables are present and raises a `ValueError` if any are missing.
**How to Use:**
1. **Create a `.env` file (optional):** In your project directory, create a file named `.env` and add your configuration variables in the following format:
   ```   OPENAI_API_KEY=your_openai_api_key   EMBEDDINGS_MODEL=text-embedding-ada-002  # Example model   QDRANT_HOST=localhost   QDRANT_PORT=6333   VECTOR_SIZE=1536   DISTANCE=cosine   HNSW_M=16   HNSW_EF_CONSTRUCT=100   ```
2. **Import and Use in Your Main Application:**
   ```python   from config import load_config
   config = load_config()
   # Access configuration values   openai_api_key = config["openai_api_key"]  
