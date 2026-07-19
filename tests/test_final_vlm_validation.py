import json

from prototypes.confidence_gated_spatial_pilot.run_final_vlm_validation import json_signature


def test_json_signature_is_order_stable() -> None:
    first = json_signature({"b": 2, "a": 1}, "  Terlihat   meja. ")
    second = json_signature({"a": 1, "b": 2}, "Terlihat meja.")

    assert first == second


def test_json_signature_is_json_serializable() -> None:
    value = json_signature(None, "Deskripsi")

    assert json.loads(value)["description"] == "Deskripsi"

