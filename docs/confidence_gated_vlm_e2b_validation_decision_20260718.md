# Confidence-Gated Spatial Description — e2b validation decision

## Run identity

- Protocol: `cgsp-final-candidate-vlm-e2b-20260718-v1`
- Protocol SHA-256: `7d587fe09faa92f07b50236725c3aa4d06f8834e0a161770e38af1a76c97f2d7`
- Source depth run: `cgsp-calibration-holdout-20260718-v1`
- Source gate SHA-256: `966a03b3544828edb5a691d53779b259d45a77b960fb70f463876d044b4b9159`
- Model: `google/gemma-4-e2b`
- Load configuration: `context-length 4096`, `parallel 1`, `gpu max`

The e2b model was explicitly loaded before inference using the LM Studio CLI. A model appearing in `/v1/models` alone was not treated as proof of readiness.

## Controlled result

The 20 held-out images were each sent once to the VLM. The same VLM result was reused for the visual-only and confidence-gated branches, so the branch comparison does not confound two separate generations.

| Metric | Result | Interpretation |
|---|---:|---|
| VLM success | 20/20 (100%) | Runtime path completed |
| Structured output | 20/20 (100%) | Parser contract held |
| Paired same-output rate | 100% | Branch comparison is controlled |
| Mean latency | 10,115 ms | Usable for batch/offline evaluation, not real-time claim |
| Median latency | 10,061 ms | Typical serial e2b latency |
| P95 latency | 10,939 ms | Stable latency in this run |
| Repeat variation | 5/5 images (100%) | Output wording is not reproducible under the current protocol |
| Gated depth coverage | 12/20 (60%) | Same held-out gate coverage as prior depth run |
| Depth accuracy at coverage | 4/12 (33.3%) | Weak spatial signal |
| Unsupported added depth claims | 8/12 (66.7%) | Main safety/reliability weakness |

## Decision

**`REVISE_OR_BLOCK` for thesis evidence.**

The smaller model is technically viable and much more practical than the e4b attempt: all calls completed, all outputs parsed, and latency was approximately 10 seconds per image. This validates an e2b integration path, not the research claim that the fusion method improves image description.

The result cannot be promoted as a successful confidence-gated description method because the repeat test changed on every tested image and the accepted regional depth claims were correct in only one third of accepted cases. The spatial error comes from the calibrated depth branch and is therefore not repaired merely by replacing e4b with e2b.

## What may be claimed

- `google/gemma-4-e2b` can run the frozen prompt and structured parser on this machine under the recorded lightweight load configuration.
- The integration path completed 20/20 held-out calls with 100% structured-output rate.
- e2b is suitable for subsequent offline engineering experiments where approximately 10 seconds/image is acceptable.

## What may not be claimed

- No real-time performance claim.
- No human caption-quality or user-effectiveness claim; there are no independent reference captions or UAT in this run.
- No claim that confidence-gated depth improves description quality.
- No claim of deterministic generation; repeat variation was 100%.
- No pooling of this e2b result with the earlier e4b runtime attempt, because the model and protocol run identity differ.

## Recommended next action

Keep e2b as the implementation model if the project continues, but do not spend effort on a larger VLM run until the protocol explicitly resolves repeatability and the depth branch is improved or its claim is removed. A defensible reduced scope is: structured image description runtime evaluation with e2b, while treating regional depth fusion as an exploratory ablation rather than the main contribution.

Artifacts:

- `prototypes/confidence_gated_spatial_pilot/final_vlm_e2b_protocol.json`
- `results/prototypes/confidence_gated_vlm_e2b_validation_20260718/summary.json`
- `results/prototypes/confidence_gated_vlm_e2b_validation_20260718/vlm_predictions.csv`
- `results/prototypes/confidence_gated_vlm_e2b_validation_20260718/repeat_predictions.csv`
