# Copilot Instructions for v-gpt-qdrant-api

## Project Architecture
- **FastAPI-based API** for memory management and vector embeddings.
- **app/** contains main logic:
  - `main.py`: FastAPI app entrypoint, includes API setup and startup logic.
  - `models.py`: Data models (Pydantic schemas, memory/embedding structures).
  - `dependencies.py`: Dependency injection and shared resources.
  - `routes/`: API endpoints split by domain (`memory.py`, `embeddings.py`).
- **Singleton pattern** for embedding models (see `main.py` and model loading logic) to optimize resource usage.
- **Qdrant** is used for vector storage; configuration via environment variables and `.env` file.

## Key Workflows
- **Run locally**: `docker-compose up -d` (uses Dockerfile and docker-compose.yml)
- **Environment config**: `.env` file required for Qdrant, model, and API settings (see README for example).
- **API docs**: Auto-generated at `/openapi.json` (see FastAPI setup in `main.py`).
- **Testing**: Add/modify tests in a dedicated test directory (not present by default; follow AGENTS.md for test requirements).
- **Linting**: Run project linter before PR (see AGENTS.md for workflow).

## Patterns & Conventions
- **Endpoints**: All API routes are defined in `app/routes/` and registered in `main.py`.
- **Memory management**: Use `/manage_memories/`, `/save_memory/`, `/recall_memory/` endpoints for CRUD and search.
- **Embeddings**: `/v1/embeddings/` endpoint is OpenAI-compatible; uses local or remote models as configured.
- **Model selection**: Controlled via environment variables (`LOCAL_MODEL`, `DIM`).
- **Docker-first**: All deployment and local dev is containerized; avoid running directly on host unless customizing.

## Integration Points
- **Qdrant**: External vector DB, configured via env vars.
- **FastEmbed**: Used for embedding generation; model loading is centralized and singleton.
- **OpenAI API compatibility**: Embeddings endpoint mimics OpenAI spec for easy integration.

## References
- See `README.md` for setup, endpoints, and model options.
- See `AGENTS.md` for contributor workflow, testing, and documentation standards.
- Key files: `app/main.py`, `app/models.py`, `app/routes/memory.py`, `app/routes/embeddings.py`, `docker-compose.yml`, `.env`.

---

For changes affecting public docs, always sync `README.md`, `CHANGELOG.md`, and other docs (see AGENTS.md: Doc Sync).

---

**Feedback:** If any section is unclear or missing, please specify so it can be improved for future AI agents.
