from __future__ import annotations
import os, json, threading
from datetime import datetime
from typing import Any, Dict, Optional


def _iso_now() -> str:
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


class Ledger:
    """
    Tiny JSONL ledger. Thread-safe. If enabled=False, all methods no-op.
    Writes to: {run_dir}/{run_id}/trace.jsonl
    """

    def __init__(self, run_dir: str = "./runs", run_id: Optional[str] = None, enabled: bool = True):
        self.enabled = bool(enabled)
        self.run_dir = run_dir
        self.run_id = run_id or datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        self._path = os.path.join(self.run_dir, self.run_id)
        self._file = None
        self._lock = threading.Lock()

        if self.enabled:
            os.makedirs(self._path, exist_ok=True)
            self._file = open(os.path.join(self._path, "trace.jsonl"), "a", encoding="utf-8")

    @property
    def path(self) -> str:
        return self._path

    def log(self, kind: str, data: Dict[str, Any]) -> None:
        if not self.enabled or self._file is None:
            return
        with self._lock:
            rec = {"ts": _iso_now(), "run_id": self.run_id, "kind": kind, "data": data}
            self._file.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._file.flush()

    def close(self) -> None:
        if not self.enabled or self._file is None:
            return
        with self._lock:
            try:
                self._file.flush()
            finally:
                self._file.close()
                self._file = None

    # Convenience helpers
    def log_message(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.log("message", {"role": role, "content": content, "meta": meta or {}})

    def log_tool_call(self, name: str, params: Dict[str, Any], result: Dict[str, Any], status: str) -> None:
        self.log("tool_call", {"name": name, "params": params, "result": result, "status": status})

    def log_plan(self, plan: Dict[str, Any], issues: Optional[list] = None) -> None:
        self.log("white_plan", {"plan": plan, "issues": issues or []})

    def log_eval(self, decision: Dict[str, Any]) -> None:
        self.log("green_eval", decision)

    def log_error(self, where: str, message: str) -> None:
        self.log("error", {"where": where, "message": message})
