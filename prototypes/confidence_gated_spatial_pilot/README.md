# Confidence-Gated Spatial Description Pilot

This directory contains a six-sample feasibility pilot for Alternative 1. The frozen protocol is `protocol.json`. The run uses an unofficial Hugging Face conversion of the NYU Depth V2 validation data and the existing local Depth Anything V2 Metric Indoor Small ONNX checkpoint.

Run from the `Program` directory:

```powershell
python -m pip install -r prototypes/confidence_gated_spatial_pilot/requirements.txt
python -m prototypes.confidence_gated_spatial_pilot.run_pilot
```

The pilot compares `no_depth`, `always_fuse`, and `confidence_gated` at the level of regional spatial claims. It does not invoke a VLM because all three policies would share the same frozen image-description branch; the feasibility question here is whether the depth evidence gate is measurable, non-degenerate, and capable of lowering selective risk against aligned RGB-D ground truth.

Passing this pilot permits only a larger calibration pilot. It does not establish thesis-level superiority, generalization, navigation safety, or object-specific distance grounding.

The follow-up calibration and held-out run has a separate frozen protocol:

```powershell
python -m prototypes.confidence_gated_spatial_pilot.run_calibration_holdout
```

It uses 20 calibration images to select one configuration from a fixed 27-candidate grid, writes the selected gate to `frozen_holdout_gate.json`, and only then evaluates 20 different held-out images. The source does not expose scene IDs, so the systematic sample spread must not be described as scene-stratified.
