"""
Memory Tool - Persistent storage for long-running agents.

Allows agents to store/retrieve information outside the active context window.
Uses SQLite for persistence, works with any LLM provider.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.tool.base import BaseTool, ToolResult


class MemoryTool(BaseTool):
    """
    Persistent memory storage for long-running agents.

    Allows agents to store/retrieve information outside active context.
    Useful for:
    - Saving important context before it gets compacted
    - Storing key discoveries, decisions, and learnings
    - Retrieving previously stored information
    - Searching across stored memories
    """

    name: str = "memory"
    description: str = """Store and retrieve persistent information outside the active context window.

Actions:
- store: Save a value with a unique key and optional category
- retrieve: Get a stored value by key
- search: Find memories matching a query
- list: List all memories (optionally filtered by category)
- clear: Remove memories by key or category

Use this to preserve important information that might be lost during context compaction."""

    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["store", "retrieve", "search", "list", "clear"],
                "description": "Action to perform",
            },
            "key": {
                "type": "string",
                "description": "Unique key for store/retrieve operations",
            },
            "value": {
                "type": "string",
                "description": "Value to store (for 'store' action)",
            },
            "query": {
                "type": "string",
                "description": "Search query (for 'search' action)",
            },
            "category": {
                "type": "string",
                "description": "Optional category for organization (e.g., 'decisions', 'discoveries', 'todos')",
            },
        },
        "required": ["action"],
    }

    # Configuration
    db_path: str = Field(
        default="workspace/memory.db", description="Path to SQLite database"
    )

    def model_post_init(self, __context: Any) -> None:
        """Initialize database after model creation"""
        self._ensure_db()

    def _ensure_db(self):
        """Initialize SQLite database with required tables"""
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON memories(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_updated ON memories(updated_at)"
            )
            conn.commit()
        finally:
            conn.close()

    async def execute(
        self,
        action: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        query: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ToolResult:
        """Execute memory operation"""
        try:
            if action == "store":
                return await self._store(key, value, category)
            elif action == "retrieve":
                return await self._retrieve(key)
            elif action == "search":
                return await self._search(query, category)
            elif action == "list":
                return await self._list(category)
            elif action == "clear":
                return await self._clear(key, category)
            else:
                return ToolResult(
                    error=f"Unknown action: {action}. Valid actions: store, retrieve, search, list, clear"
                )
        except Exception as e:
            return ToolResult(error=f"Memory operation failed: {str(e)}")

    async def _store(
        self, key: Optional[str], value: Optional[str], category: Optional[str]
    ) -> ToolResult:
        """Store a value with a key"""
        if not key:
            return ToolResult(error="'key' is required for store action")
        if not value:
            return ToolResult(error="'value' is required for store action")

        conn = sqlite3.connect(self.db_path)
        try:
            now = datetime.now().isoformat()
            # Use INSERT OR REPLACE to handle updates, preserving created_at for existing keys
            conn.execute(
                """
                INSERT INTO memories (key, value, category, created_at, updated_at, access_count)
                VALUES (?, ?, ?,
                    COALESCE((SELECT created_at FROM memories WHERE key = ?), ?),
                    ?,
                    COALESCE((SELECT access_count FROM memories WHERE key = ?), 0)
                )
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
            """,
                (key, value, category, key, now, now, key),
            )
            conn.commit()
            return ToolResult(
                output=f"Stored memory with key: '{key}'"
                + (f" in category: '{category}'" if category else "")
            )
        finally:
            conn.close()

    async def _retrieve(self, key: Optional[str]) -> ToolResult:
        """Retrieve a value by key"""
        if not key:
            return ToolResult(error="'key' is required for retrieve action")

        conn = sqlite3.connect(self.db_path)
        try:
            # Update access count
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1 WHERE key = ?",
                (key,),
            )
            conn.commit()

            row = conn.execute(
                "SELECT key, value, category, created_at, updated_at, access_count FROM memories WHERE key = ?",
                (key,),
            ).fetchone()

            if row:
                result = {
                    "key": row[0],
                    "value": row[1],
                    "category": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "access_count": row[5],
                }
                return ToolResult(output=json.dumps(result, indent=2))
            return ToolResult(error=f"No memory found with key: '{key}'")
        finally:
            conn.close()

    async def _search(
        self, query: Optional[str], category: Optional[str]
    ) -> ToolResult:
        """Search memories by query and/or category"""
        if not query and not category:
            return ToolResult(
                error="Either 'query' or 'category' is required for search action"
            )

        conn = sqlite3.connect(self.db_path)
        try:
            if query and category:
                rows = conn.execute(
                    """SELECT key, value, category FROM memories
                       WHERE category = ? AND (key LIKE ? OR value LIKE ?)
                       ORDER BY updated_at DESC""",
                    (category, f"%{query}%", f"%{query}%"),
                ).fetchall()
            elif query:
                rows = conn.execute(
                    """SELECT key, value, category FROM memories
                       WHERE key LIKE ? OR value LIKE ?
                       ORDER BY updated_at DESC""",
                    (f"%{query}%", f"%{query}%"),
                ).fetchall()
            else:  # category only
                rows = conn.execute(
                    """SELECT key, value, category FROM memories
                       WHERE category = ?
                       ORDER BY updated_at DESC""",
                    (category,),
                ).fetchall()

            results = []
            for r in rows:
                value_preview = r[1][:200] + "..." if len(r[1]) > 200 else r[1]
                results.append(
                    {"key": r[0], "value_preview": value_preview, "category": r[2]}
                )

            return ToolResult(
                output=json.dumps(
                    {
                        "results": results,
                        "count": len(results),
                        "query": query,
                        "category": category,
                    },
                    indent=2,
                )
            )
        finally:
            conn.close()

    async def _list(self, category: Optional[str]) -> ToolResult:
        """List all memories, optionally filtered by category"""
        conn = sqlite3.connect(self.db_path)
        try:
            if category:
                rows = conn.execute(
                    """SELECT key, category, access_count, updated_at FROM memories
                       WHERE category = ?
                       ORDER BY updated_at DESC""",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT key, category, access_count, updated_at FROM memories
                       ORDER BY updated_at DESC"""
                ).fetchall()

            items = []
            for r in rows:
                items.append(
                    {
                        "key": r[0],
                        "category": r[1],
                        "access_count": r[2],
                        "updated_at": r[3],
                    }
                )

            # Get category summary
            categories = conn.execute(
                "SELECT category, COUNT(*) FROM memories GROUP BY category"
            ).fetchall()
            category_summary = {c[0] or "uncategorized": c[1] for c in categories}

            return ToolResult(
                output=json.dumps(
                    {
                        "memories": items,
                        "count": len(items),
                        "categories": category_summary,
                    },
                    indent=2,
                )
            )
        finally:
            conn.close()

    async def _clear(self, key: Optional[str], category: Optional[str]) -> ToolResult:
        """Clear memories by key, category, or all"""
        conn = sqlite3.connect(self.db_path)
        try:
            if key:
                cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
                conn.commit()
                if cursor.rowcount > 0:
                    return ToolResult(output=f"Cleared memory with key: '{key}'")
                return ToolResult(error=f"No memory found with key: '{key}'")
            elif category:
                cursor = conn.execute(
                    "DELETE FROM memories WHERE category = ?", (category,)
                )
                conn.commit()
                return ToolResult(
                    output=f"Cleared {cursor.rowcount} memories in category: '{category}'"
                )
            else:
                cursor = conn.execute("DELETE FROM memories")
                conn.commit()
                return ToolResult(output=f"Cleared all {cursor.rowcount} memories")
        finally:
            conn.close()
