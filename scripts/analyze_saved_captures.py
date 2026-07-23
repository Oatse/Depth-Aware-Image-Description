import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx


TERMINAL_STATUSES = {"completed", "failed"}


def analyze_saved_captures(
    client: httpx.Client,
    *,
    batch_id: str | None,
    mode: str | None,
    include_failed: bool,
    poll_interval_seconds: float,
    timeout_seconds: float,
    capture_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    params = {"batch_id": batch_id} if batch_id else {}
    response = client.get("/captures", params=params)
    response.raise_for_status()
    allowed_statuses = {"captured", "failed"} if include_failed else {"captured"}
    captures_by_id = {
        str(capture["capture_id"]): capture
        for capture in response.json().get("captures", [])
    }
    selected_ids = capture_ids if capture_ids is not None else list(captures_by_id)
    missing_ids = [capture_id for capture_id in selected_ids if capture_id not in captures_by_id]
    if missing_ids:
        raise ValueError(f"Capture manifest tidak ditemukan di backend: {missing_ids}")
    captures = [
        captures_by_id[capture_id]
        for capture_id in selected_ids
        if captures_by_id[capture_id].get("status") in allowed_statuses
    ]
    results: list[dict[str, Any]] = []
    for capture in captures:
        capture_id = str(capture["capture_id"])
        form = {"mode": mode} if mode else None
        try:
            accepted = client.post(f"/captures/{capture_id}/analysis-jobs", data=form)
            accepted.raise_for_status()
            poll_url = str(accepted.json()["poll_url"])
            deadline = time.monotonic() + timeout_seconds
            while True:
                status_response = client.get(poll_url)
                status_response.raise_for_status()
                payload = status_response.json()
                if payload.get("status") in TERMINAL_STATUSES:
                    results.append({"capture_id": capture_id, **payload})
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Analisis capture {capture_id} melewati {timeout_seconds:g} detik."
                    )
                time.sleep(poll_interval_seconds)
        except (httpx.HTTPError, KeyError, ValueError, TimeoutError) as exc:
            results.append({"capture_id": capture_id, "status": "failed", "error": str(exc)})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit capture tersimpan sebagai job terpisah dan tunggu satu per satu sampai selesai."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--batch-id")
    parser.add_argument("--mode", choices=("sensor_assisted", "gemma_only"))
    parser.add_argument("--include-failed", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.poll_interval < 0:
        parser.error("--poll-interval tidak boleh negatif")
    if args.timeout <= 0:
        parser.error("--timeout harus lebih besar dari nol")

    capture_ids = None
    if args.manifest is not None:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        capture_ids = [str(row["capture_id"]) for row in manifest["captures"]]

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=30.0) as client:
        results = analyze_saved_captures(
            client,
            batch_id=args.batch_id,
            mode=args.mode,
            include_failed=args.include_failed,
            poll_interval_seconds=args.poll_interval,
            timeout_seconds=args.timeout,
            capture_ids=capture_ids,
        )
    compact_results = [
        {
            "capture_id": item["capture_id"],
            "job_id": item.get("job_id"),
            "status": item.get("status"),
            "analysis_run_id": (item.get("result") or {}).get("analysis_run_id"),
            "error": item.get("error"),
        }
        for item in results
    ]
    summary = {
        "submitted": len(results),
        "completed": sum(item.get("status") == "completed" for item in results),
        "failed": sum(item.get("status") == "failed" for item in results),
        "results": compact_results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
