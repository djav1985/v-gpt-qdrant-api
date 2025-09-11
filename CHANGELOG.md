# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## Unreleased
- add unit tests for startup events, dependencies, API key validation, memory routes, root endpoint, and models
- add unit tests for pydantic model validators
- document memory API responses and security scheme
- pin Pydantic to v2 and add redis-backed rate limiting
 - restrict Pydantic dependency to <3 and tighten model validations (UUIDs, datetimes, sentiment enum, non-empty strings, memory bank checks)
- add optional embeddings endpoint gated by EMBEDDING_ENDPOINT flag
- fix Qdrant deletion selector and use timezone-aware timestamps
- unify API key handling and standardize container port 8060
- add shared error model and examples for memory management operations
- adopt OpenAPI 3.1 with tag metadata, reusable rate-limit headers, and expanded models

