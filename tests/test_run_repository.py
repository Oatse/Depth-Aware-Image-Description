import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from services.run_repository import RunRepository


def test_repository_appends_concurrent_records_without_mixing(tmp_path) -> None:
    repository = RunRepository(tmp_path / "analysis_runs.jsonl")
    with ThreadPoolExecutor(max_workers=8) as executor:
        ids = list(executor.map(lambda index: repository.append({"capture_id": f"cap-{index}"}), range(40)))
    records = repository.read_all()
    assert len(records) == 40
    assert len(set(ids)) == 40
    assert {record["capture_id"] for record in records} == {f"cap-{index}" for index in range(40)}


def test_repository_rejects_unknown_schema_and_never_stores_raw_bytes(tmp_path) -> None:
    path = tmp_path / "analysis_runs.jsonl"
    repository = RunRepository(path)
    repository.append({"capture_id": "cap-1", "image_bytes": "secret"})
    assert "image_bytes" not in repository.read_all()[0]
    path.write_text(json.dumps({"schema_version": 99}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema_version"):
        repository.read_all()
