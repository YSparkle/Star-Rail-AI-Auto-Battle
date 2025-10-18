import json
import os
from typing import Any, Dict, Optional

DEFAULT_MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "game_data")
DEFAULT_MEMORY_PATH = os.path.abspath(os.path.join(DEFAULT_MEMORY_DIR, "memory.json"))


class MemoryStore:
    """Simple JSON file memory for persisting computed stats and plans between runs."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or DEFAULT_MEMORY_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write({})

    def _read(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        data = self._read()
        return data.get(key, default)

    def set(self, key: str, value: Any):
        data = self._read()
        data[key] = value
        self._write(data)

    def update(self, key: str, patch: Dict[str, Any]):
        data = self._read()
        cur = data.get(key, {})
        if isinstance(cur, dict):
            cur.update(patch)
            data[key] = cur
            self._write(data)
        else:
            data[key] = patch
            self._write(data)
