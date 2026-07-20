from __future__ import annotations

from models.fusion_types import SensorFusionResult


def fuse_sensor_reference(
    sensor_evidence: dict | None,
    *,
    calibration_validated: bool,
) -> SensorFusionResult:
    if not sensor_evidence:
        return _insufficient("sensor_unavailable", "Referensi sensor frontal tidak tersedia.")
    status = sensor_evidence.get("status")
    samples = sensor_evidence.get("samples") or {}
    if status == "direction_mismatch":
        return _insufficient(
            "camera_sensor_direction_mismatch",
            "Referensi sensor frontal tidak diterapkan karena frame berasal dari kamera depan.",
        )
    if status == "pair_conflict":
        values = [float(sample["distance_cm"]) for sample in samples.values() if sample.get("distance_cm") is not None]
        text = "Referensi sensor frontal saling berbeda sehingga tidak dirata-ratakan."
        if len(values) >= 2:
            text = f"Referensi sensor frontal berbeda: sensor 1 {values[0]:.1f} cm dan sensor 2 {values[1]:.1f} cm; nilai tidak dirata-ratakan."
        return {
            "status": "conflict",
            "reason_code": "sensor_pair_disagreement",
            "frontal_reference_cm": None,
            "depth_consistency": "not_evaluated",
            "description": text,
            "warnings": ["Dua sensor frontal tidak sepakat."],
        }
    if status != "paired" or len(samples) < 2:
        return _insufficient(
            sensor_evidence.get("reason_code") or f"sensor_{status or 'unavailable'}",
            "Referensi sensor frontal belum cukup karena evidence tidak paired dan segar.",
        )
    values = [float(sample["distance_cm"]) for sample in samples.values()]
    reference = round(sum(values) / len(values), 2)
    consistency = "not_evaluated" if not calibration_validated else "distance_reference_validated"
    calibration_text = (
        " Akurasi jarak belum lolos kalibrasi terhadap pengukuran fisik."
        if not calibration_validated
        else " Akurasi jarak telah lolos gate residual terhadap bidang datar; nilai ini tetap tidak diikat ke objek atau ROI gambar."
    )
    return {
        "status": "applied",
        "reason_code": None,
        "frontal_reference_cm": reference,
        "depth_consistency": consistency,
        "description": f"Referensi sensor frontal sekitar {reference:.1f} cm pada bidang pandang sensor.{calibration_text}",
        "warnings": [],
    }


def append_sensor_section(base_description: str | None, contribution: SensorFusionResult) -> str:
    base = (base_description or "Deskripsi visual-spasial tidak tersedia.").strip()
    return f"{base} Referensi sensor frontal: {contribution['description']}"


def _insufficient(reason_code: str, description: str) -> SensorFusionResult:
    return {
        "status": "insufficient",
        "reason_code": reason_code,
        "frontal_reference_cm": None,
        "depth_consistency": "not_evaluated",
        "description": description,
        "warnings": [],
    }
