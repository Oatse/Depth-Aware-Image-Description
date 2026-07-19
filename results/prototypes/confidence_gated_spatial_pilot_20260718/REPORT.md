# Confidence-Gated Spatial Description Pilot

Pilot ID: `cgsp-nyuv2-20260718-v1`
Decision: **PROCEED_TO_CALIBRATION_PILOT**

## Mechanical result

- Samples: 6
- Depth calls: 30/30
- Total inference time: 24.254 s
- Always-fuse joint accuracy: 0.6667
- Always-fuse selective risk: 0.3333
- Confidence-gated coverage: 0.6667
- Confidence-gated selective risk: 0.25

## Frozen feasibility gates

- `all_depth_calls_succeeded`: PASS
- `coverage_is_non_degenerate`: PASS
- `gated_risk_not_worse_than_always_fuse`: PASS
- `inference_time_within_budget`: PASS

## Interpretation boundary

This six-sample run is a feasibility pilot only. It cannot establish generalization, statistical superiority, or object-specific distance grounding. A final experiment requires a separate calibration split, held-out test split, and a new frozen protocol.
