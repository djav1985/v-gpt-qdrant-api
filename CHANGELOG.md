# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## Unreleased
### Added
- Enhanced OpenAPI documentation with detailed response models and endpoint summaries.
### Changed
- Qualified internal imports throughout the application.
- Startup now validates `MEMORIES_API_KEY` and `LOCAL_MODEL` environment variables.
- Pinned Pydantic requirement to v2 and updated Qdrant interactions.
- Qdrant client is closed after use and deletion uses `PointIdsList` selector.
- Root endpoints resolve `index.html` dynamically.
