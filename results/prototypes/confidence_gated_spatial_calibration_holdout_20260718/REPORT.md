# Confidence-Gated Spatial Calibration and Held-Out Pilot

Run ID: `cgsp-calibration-holdout-20260718-v1`
Decision: **PROCEED_TO_FINAL_PROTOCOL_DESIGN**

## Calibration

- Samples: 20
- Selected configuration: `{"maximum_relative_mad": 0.05, "minimum_distance_category_agreement": 0.6, "minimum_nearest_region_agreement": 1.0}`
- Selected coverage: 0.6000
- Selected risk: 0.4167

## Held-out

- Samples: 20
- Always-fuse joint accuracy: 0.2500
- Always-fuse risk: 0.7500
- Gated coverage: 0.6000
- Gated accuracy at coverage: 0.3333
- Gated risk: 0.6667
- Gated minus always risk: -0.0833
- Bootstrap snapshot interval: (-0.25, 0.06666666666666665)
- Error capture: 7/15
- False rejection rate: 0.2

## Frozen gates

- `all_depth_calls_succeeded`: PASS
- `heldout_coverage_is_non_degenerate`: PASS
- `heldout_gated_risk_not_worse_than_always_fuse`: PASS
- `captured_at_least_one_always_fuse_error`: PASS
- `false_rejection_rate_within_limit`: PASS
- `inference_time_within_budget`: PASS

## Boundary

This is a calibration and held-out feasibility run. It is not scene-stratified, does not invoke a VLM, and does not establish thesis-level superiority or object-specific distance grounding.
