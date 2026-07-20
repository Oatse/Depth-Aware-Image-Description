from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ui_exposes_explicit_workflow_and_iot_gate() -> None:
    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for state in ("runtime", "camera", "sensor", "captured", "analyzing", "result"):
        assert f'data-workflow-state="{state}"' in html
    assert 'id="iot-mode-option" value="iot_assisted" disabled' in html
    assert 'id="iot-mode-reason"' in html


def test_browser_uses_backend_comparison_and_sensor_provenance() -> None:
    javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "buildControlledLateFusion" not in javascript
    assert 'window.AnalysisJobClient.compare(formData)' in javascript
    assert 'source: "sensor"' in javascript
    assert 'fetch("/readiness"' in javascript
