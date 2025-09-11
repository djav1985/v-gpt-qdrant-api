# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## Unreleased
- move runtime imports to module scope in memory routes
- handle Qdrant errors explicitly and log unexpected failures when saving memories
- protect TextEmbedding initialization with an asyncio lock
- pin pydantic and pydantic-settings to exact versions
- switch tests to pytest's native async support
- declare pytest-asyncio as a test dependency
- add docstrings for memory and embedding route handlers
- add BaseSettings configuration and forbid extra request fields
- add unit tests for startup events, dependencies, API key validation, memory routes, root endpoint, and models
- add unit tests for pydantic model validators
- expand tests to ensure recall route rejects unexpected fields
- document memory API responses and security scheme
- pin Pydantic to v2
- refactor dependencies and routes for robust embedding and qdrant client lifecycle management
- restrict Pydantic dependency to <3 and tighten model validations (UUIDs, datetimes, sentiment enum, non-empty strings, memory bank checks)
- add optional embeddings endpoint gated by EMBEDDING_ENDPOINT flag
- fix Qdrant deletion selector and use timezone-aware timestamps
- unify API key handling and standardize container port 8060
- add shared error model and examples for memory management operations
- adopt OpenAPI 3.1 with tag metadata and expanded models
- remove redis-based rate limiting and associated dependencies
- refactor startup to use FastAPI's lifespan context manager
- load TextEmbedding in a background thread, simplify initialization calls, and manage Qdrant client via async generator
- replace bare imports with package-relative paths and drop test path hacks
- load TextEmbedding asynchronously and await initialization during lifespan
- centralize shared error responses
- simplify embedding vector handling with NumPy
- align OpenAPI security with X-API-Key header
- remove unused startup event and modernize typing hints

