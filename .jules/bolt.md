## 2026-01-17 - LLM Response Caching Implementation
**Learning:** The `LLM` class had infrastructure for response caching (`_response_cache`, `_cache_get`, `_cache_set`) but it was completely unused in the main `ask` and `ask_with_images` methods, leading to redundant expensive API calls.
**Action:** Always verify that "enabled" features are actually wired up in the execution path, especially for performance-critical components like LLM calls.
