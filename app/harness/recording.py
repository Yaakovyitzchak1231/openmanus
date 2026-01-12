import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class RunRecorder:
    def __init__(self, run_id: str, log_dir: Path) -> None:
        self.run_id = run_id
        self.log_dir = Path(log_dir)
        self.path = self.log_dir / f"{run_id}.jsonl"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
        }
        if payload:
            record["data"] = payload
        self._handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        self._handle.flush()

    def close(self) -> None:
        if self._handle:
            self._handle.close()
            self._handle = None
