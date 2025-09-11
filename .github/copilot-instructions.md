
# Copilot Instructions for v-gpt-qdrant-api

## Essential Architecture & Patterns
- **FastAPI API** for memory and vector embedding management. All API logic is in `app/`:
  - `main.py`: Entrypoint, registers all routes, sets up singleton embedding model (see model loading logic).
  - `models.py`: Pydantic schemas for requests/responses, memory/embedding structures.
  - `dependencies.py`: Dependency injection, shared resources.
  - `routes/`: Domain endpoints (`memory.py`, `embeddings.py`, `root.py`).
- **Singleton pattern** for embedding models: always load once, reuse (see `main.py`).
- **Qdrant**: Vector DB, configured via `.env` and environment variables. All vector operations route through Qdrant.
- **Docker-first**: All dev and deployment is containerized. Use Docker Compose; do not run on host unless customizing.

## Developer Workflows
- **Run locally:**
  - `docker-compose up -d` (starts all services; see `docker-compose.yml`).
  - API available at `http://localhost:8060`.
- **Environment config:**
  - `.env` required for Qdrant, model, and API settings. See `README.md` for example.
- **API docs:**
  - Auto-generated at `/openapi.json` (see FastAPI setup in `main.py`).
- **Testing:**
  - Add/modify tests in a dedicated test directory (not present by default). Follow `AGENTS.md` for test requirements and coverage.
- **Linting:**
  - Run linter before PR. See `AGENTS.md` for workflow.

## Project-Specific Conventions
- **Endpoints:**
  - All routes in `app/routes/`, registered in `main.py`.
  - Memory endpoints: `/manage_memories/`, `/save_memory/`, `/recall_memory/` (CRUD/search).
  - Embeddings endpoint: `/v1/embeddings/` (OpenAI-compatible; uses local/remote models as per env config).
- **Model selection:**
  - Controlled by env vars (`LOCAL_MODEL`, `DIM`).
- **Integration points:**
  - Qdrant (vector DB), FastEmbed (embedding generation, singleton), OpenAI API compatibility (embeddings endpoint).

## Contributor Guidance
- **Testing:** Always update/create unit tests for any feature, bug fix, or refactor. Cover edge cases, not just happy paths. See `AGENTS.md` for details.
- **Documentation:** Update `CHANGELOG.md` for notable changes. Update `README.md` if instructions or usage change. Always sync public docs (`README.md`, `CHANGELOG.md`, etc.) together.
- **Local verification:** Run all tests and lint before commit. Never push untested or lint-failing code.
- **PRs:** Must pass all checks. Include summary and reference related issues/tickets.

## Key References
- See `README.md` for setup, endpoints, and model options.
- See `AGENTS.md` for contributor workflow, testing, and documentation standards.
- Key files: `app/main.py`, `app/models.py`, `app/routes/memory.py`, `app/routes/embeddings.py`, `docker-compose.yml`, `.env`.

---

For changes affecting public docs, always sync `README.md`, `CHANGELOG.md`, and other docs (see AGENTS.md: Doc Sync).

---

**Feedback:** If any section is unclear or missing, please specify so it can be improved for future AI agents.
