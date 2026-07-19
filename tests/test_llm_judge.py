import json
from pathlib import Path

from PIL import Image

from services.llm_judge import JudgeResult, aggregate_judgements, build_judge_messages
from scripts.run_llm_judge import _image_data_url


def test_judge_messages_blind_experiment_mode_and_use_structured_annotation() -> None:
    annotation = {
        "image_name": "indoor_001.webp",
        "main_object": "kursi",
        "object_position": "tengah",
        "distance_category": "dekat",
        "has_obstacle": "yes",
        "safer_direction": "kanan",
        "notes": "",
    }
    prediction = {
        "image_name": "indoor_001.webp",
        "mode": "gemma_depth",
        "final_description": "Terlihat kursi dekat di tengah.",
    }

    messages = build_judge_messages(
        annotation,
        prediction,
        "data:image/jpeg;base64,aW1hZ2U=",
    )
    serialized = json.dumps(messages, ensure_ascii=False)

    assert "gemma_depth" not in serialized
    assert "kursi" in serialized
    assert '"type": "image_url"' in serialized
    assert "citra sebagai bukti visual utama" in serialized


def test_judge_messages_define_the_structured_output_contract() -> None:
    messages = build_judge_messages(
        {"main_object": "kursi"},
        {"final_description": "Terlihat kursi."},
        "data:image/jpeg;base64,aW1hZ2U=",
    )

    system_message = messages[0]["content"]
    required_fields = {
        "semantic_correctness",
        "spatial_accuracy",
        "groundedness",
        "clarity",
        "overall",
        "rationale",
        "critical_errors",
        "visual_evidence",
    }

    assert all(field in system_message for field in required_fields)


def test_aggregate_judgements_reports_mean_and_disagreement() -> None:
    judgements = [
        JudgeResult(5, 4, 5, 4, 5, "baik", ("kursi di tengah",), ()),
        JudgeResult(3, 2, 4, 4, 3, "berbeda", ("kursi terlihat",), ("posisi",)),
        JudgeResult(4, 3, 3, 5, 4, "cukup", ("kursi di tengah",), ()),
    ]

    aggregate = aggregate_judgements(judgements)

    assert aggregate.repeat_count == 3
    assert aggregate.semantic_correctness_mean == 4.0
    assert aggregate.spatial_accuracy_mean == 3.0
    assert aggregate.overall_mean == 4.0
    assert aggregate.overall_stddev > 0.0
    assert aggregate.visual_evidence_union == ("kursi di tengah", "kursi terlihat")
    assert aggregate.critical_error_union == ("posisi",)


def test_image_data_url_preprocesses_a_real_image(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.webp"
    Image.new("RGB", (24, 16), color=(10, 20, 30)).save(image_path, format="WEBP")

    data_url = _image_data_url(image_path)

    assert data_url.startswith("data:image/jpeg;base64,")
