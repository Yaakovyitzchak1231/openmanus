import datetime
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from app.logger import logger
from app.tool.base import BaseTool


class FeedbackLogger(BaseTool):
    """
    A tool to log human feedback and corrections into a SQLite database.
    This enables long-term learning and pattern analysis of agent failures.
    """

    name: str = "feedback_logger"
    description: str = "Logs user feedback and corrections for future improvement."

    db_path: str = "feedback.db"

    def __init__(self, **data):
        super().__init__(**data)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    step_text TEXT,
                    agent_name TEXT,
                    user_feedback TEXT,
                    successful_correction INTEGER
                )
            """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize feedback database: {e}")

    async def execute(
        self,
        step_text: str,
        agent_name: str,
        user_feedback: str,
        successful_correction: bool = True,
    ) -> str:
        """
        Record a feedback entry.

        Args:
            step_text: The description of the step being corrected.
            agent_name: The name of the agent that performed the step.
            user_feedback: The content of the user's correction or feedback.
            successful_correction: Whether the feedback led to a successful outcome.
        """
        try:
            timestamp = datetime.datetime.now().isoformat()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO feedback (timestamp, step_text, agent_name, user_feedback, successful_correction)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    step_text,
                    agent_name,
                    user_feedback,
                    1 if successful_correction else 0,
                ),
            )
            conn.commit()
            conn.close()
            return f"Feedback logged successfully for step: {step_text}"
        except Exception as e:
            error_msg = f"Error logging feedback: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def to_param(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "step_text": {
                        "type": "string",
                        "description": "The text of the step being providing feedback for.",
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "The name of the agent involved in the step.",
                    },
                    "user_feedback": {
                        "type": "string",
                        "description": "The content of the feedback or correction.",
                    },
                    "successful_correction": {
                        "type": "boolean",
                        "description": "Whether the correction was successful (default: true).",
                    },
                },
                "required": ["step_text", "agent_name", "user_feedback"],
            },
        }
