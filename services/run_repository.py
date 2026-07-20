from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1


class RunRepository:
    _lock = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: dict[str, Any]) -> str:
        version = record.get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported analysis run schema_version: {version}")
        run_id = str(record.get("analysis_run_id") or uuid4().hex)
        canonical = {"schema_version": SCHEMA_VERSION, "analysis_run_id": run_id, **record}
        canonical.pop("image_bytes", None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
        return run_id

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("schema_version") != SCHEMA_VERSION:
                raise ValueError(f"Unsupported analysis run schema_version: {record.get('schema_version')}")
            records.append(record)
        return records
