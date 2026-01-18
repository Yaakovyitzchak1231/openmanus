## 2026-01-18 - Side Effects in Message Formatting
**Learning:** `LLM.format_messages` was modifying input dictionaries in-place (shallow copy issue). This caused subsequent calls with the same input variables to send modified messages (e.g., duplicated images), breaking caching logic and potentially costing more tokens.
**Action:** Always ensure deep copies or at least shallow copies of mutable inputs before modification in utility functions, especially those used in preparation for API calls.
