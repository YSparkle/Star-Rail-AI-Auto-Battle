"""
本地记忆存储
- 将角色、敌人、计算出的衍生数值以及策略计划落盘，便于后续加载
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

DEFAULT_ROOT = os.path.join(os.getcwd(), "data", "memory")


class MemoryStore:
    def __init__(self, root: Optional[str] = None):
        self.root = root or DEFAULT_ROOT
        os.makedirs(self.root, exist_ok=True)

    def _path(self, name: str) -> str:
        return os.path.join(self.root, f"{name}.json")

    def save(self, name: str, data: Dict[str, Any]) -> str:
        path = self._path(name)
        payload = {
            "_saved_at": int(time.time()),
            "data": data,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        path = self._path(name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj.get("data")
