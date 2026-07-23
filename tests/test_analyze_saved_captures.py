import httpx

from scripts.analyze_saved_captures import analyze_saved_captures


def test_saved_capture_runner_waits_for_each_job_before_submitting_next() -> None:
    events: list[str] = []
    polls = {"job-1": 0, "job-2": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == "/captures":
            return httpx.Response(200, json={
                "count": 2,
                "captures": [
                    {"capture_id": "cap-1", "status": "captured"},
                    {"capture_id": "cap-2", "status": "captured"},
                ],
            })
        if request.method == "POST" and path.startswith("/captures/"):
            capture_id = path.split("/")[2]
            events.append(f"submit:{capture_id}")
            job_id = "job-1" if capture_id == "cap-1" else "job-2"
            return httpx.Response(202, json={"job_id": job_id, "poll_url": f"/analysis-jobs/{job_id}"})
        if request.method == "GET" and path.startswith("/analysis-jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            polls[job_id] += 1
            events.append(f"poll:{job_id}:{polls[job_id]}")
            status = "completed" if polls[job_id] >= 2 else "running"
            return httpx.Response(200, json={"job_id": job_id, "status": status})
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test") as client:
        results = analyze_saved_captures(
            client,
            batch_id=None,
            mode=None,
            include_failed=False,
            poll_interval_seconds=0,
            timeout_seconds=1,
            capture_ids=None,
        )

    assert [item["status"] for item in results] == ["completed", "completed"]
    assert events == [
        "submit:cap-1",
        "poll:job-1:1",
        "poll:job-1:2",
        "submit:cap-2",
        "poll:job-2:1",
        "poll:job-2:2",
    ]


def test_saved_capture_runner_isolates_failed_job_and_uses_manifest_order() -> None:
    submitted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == "/captures":
            return httpx.Response(200, json={"captures": [
                {"capture_id": "cap-2", "status": "captured"},
                {"capture_id": "cap-1", "status": "captured"},
            ]})
        if request.method == "POST" and path == "/captures/cap-1/analysis-jobs":
            submitted.append("cap-1")
            return httpx.Response(500, json={"error": "Gemma gagal"})
        if request.method == "POST" and path == "/captures/cap-2/analysis-jobs":
            submitted.append("cap-2")
            return httpx.Response(202, json={"poll_url": "/analysis-jobs/job-2"})
        if request.method == "GET" and path == "/analysis-jobs/job-2":
            return httpx.Response(200, json={"status": "completed", "job_id": "job-2"})
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test") as client:
        results = analyze_saved_captures(
            client,
            batch_id=None,
            mode=None,
            include_failed=False,
            poll_interval_seconds=0,
            timeout_seconds=1,
            capture_ids=["cap-1", "cap-2"],
        )

    assert submitted == ["cap-1", "cap-2"]
    assert [result["status"] for result in results] == ["failed", "completed"]
