from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ui_defaults_to_sensor_assisted_and_exposes_two_modes() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert '<option value="sensor_assisted" selected>Sensor Assisted</option>' in html
    assert '<option value="gemma_only">Gemma Only</option>' in html
    assert html.count("<option value=") == 2


def test_ui_shows_full_sensor_provenance_without_object_binding() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    for field_id in (
        "sensor-1-output",
        "sensor-2-output",
        "pair-disagreement-output",
        "frontal-reference-output",
        "sensor-1-age-output",
        "sensor-2-age-output",
        "match-time-output",
        "contribution-status",
    ):
        assert f'id="{field_id}"' in html
    assert 'elements.mode?.value || "sensor_assisted"' in javascript
    assert "sensor_evidence" in javascript
    assert "sensor_contribution" in javascript


def test_ui_has_no_retired_runtime_surface() -> None:
    content = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").lower()
        for path in ("templates/index.html", "static/app.js", "static/style.css")
    )
    for retired in ("peta kedalaman", "kedalaman model", "perbandingan model", "gambar kedua"):
        assert retired not in content


def test_ui_preserves_console_layout_and_replaces_only_result_sections() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for original_surface in (
        'class="minimal-header"',
        'class="composer-shell"',
        'id="camera-panel"',
        'id="selected-preview"',
        'id="result-shell"',
        'class="metric-grid"',
        'class="analysis-grid"',
        'class="accordion-stack"',
    ):
        assert original_surface in html

    assert "Verifikasi sensor frontal" in html
    assert "Durasi proses" in html
    assert 'id="result-sensor-1-output"' in html
    assert 'id="result-sensor-2-output"' in html
    assert 'id="result-frontal-reference-output"' in html


def test_ui_uses_camera_as_the_only_image_source() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    for retired_upload_surface in ("source-upload-tab", "upload-panel", "image-input", "upload-dropzone"):
        assert retired_upload_surface not in html
        assert retired_upload_surface not in javascript
    assert 'id="camera-panel" class="source-panel camera-panel"' in html
    assert "startCamera();" in javascript


def test_ui_hides_workflow_strip_and_omits_redundant_sensor_helper() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="workflow-state"' not in html
    assert 'id="workflow-state-label"' not in html
    assert 'class="workflow-status"' not in html
    assert 'id="sensor-mode-reason"' not in html
    assert "Referensi frontal hanya ditambahkan" not in html
    assert "grid-template-columns: minmax(0, 1fr);" in css


def test_calibration_reference_input_is_retained_after_capture() -> None:
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert 'elements.calibrationMeasured.value = ""' not in javascript
    assert 'elements.verificationMeasured.value = ""' not in javascript


def test_ui_exposes_separate_verification_capture_without_replacing_layout() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    for field_id in ("verification-measured-cm", "verification-capture", "verification-status"):
        assert f'id="{field_id}"' in html
    assert 'fetch("/sensor-calibration/verification/captures"' in javascript
    assert "40, 80, 125, dan 175 cm" in html
    assert 'id="verification-measured-cm" type="number" min="5.1" max="200"' in html
    assert "[40, 80, 125, 175].includes(measuredCm)" in javascript
    assert 'required_reference_distances_cm?.length || 4' in javascript


def test_camera_capture_is_saved_without_exposing_dataset_or_batch_analysis_controls() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert 'id="capture-count"' not in html
    assert 'class="capture-distance-control"' in html
    assert 'id="capture-ground-truth-cm" type="number" min="20" max="200"' in html
    assert 'elements.captureMeasured' in javascript
    assert "Capture tersimpan pada sesi ini" not in html
    assert 'window.AnalysisJobClient.analyze(form)' in javascript
    assert 'form.append("ground_truth_cm", String(groundTruthCm))' not in javascript
    assert 'form.append("capture_time_ms", String(capturedAt))' in javascript
    assert 'fetch("/captures/count?batch_id="' not in javascript
    assert "Lihat Dataset" not in html
    assert "Analisis Semua" not in html
    assert "stopCamera();\n    setActionAvailability(true);" not in javascript


def test_clean_capture_v2_uses_a_new_session_batch_and_cache_busted_script() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert 'const CAPTURE_BATCH_STORAGE_KEY = "bridge-gap-clean-capture-batch-id-v2";' in javascript
    assert '/static/app.js?v=20260723-ui-clean' in html
    assert 'form.append("ground_truth_cm", String(groundTruthCm))' not in javascript
    assert 'window.AnalysisJobClient.analyze(form)' in javascript
    assert "sensorRequired = (elements.mode?.value || \"sensor_assisted\") === \"sensor_assisted\"" in javascript
    assert "latestSensorPaired = status === \"paired\";" in javascript
    assert "window.localStorage.getItem(CAPTURE_BATCH_STORAGE_KEY)" in javascript
    assert "window.localStorage.setItem(CAPTURE_BATCH_STORAGE_KEY, created)" in javascript
