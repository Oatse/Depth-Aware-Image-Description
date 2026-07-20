# Acceptance report — 2026-07-21

## Code and build gates

- Branch: `feat/complete-iot-assisted-analysis`
- Commit tested before this report: `a949693c6f8dd1638d5470ce243d35657ba7537d`
- Pytest: **122 passed**
- JavaScript syntax: `static/app.js` and `static/analysis-job-client.js` passed
- `git diff --check`: passed
- ESP32 PlatformIO `hcsr04`: build passed
- Depth Anything real inference: success, `(518, 518)`, 1,839 ms, `mock=false`

## Live runtime evidence

- `/health`: backend `ok`, Gemma health `ready`, depth `ready`
- `/sensor-status`: COM7 connected, `paired`, sensor 1 `233.63 cm`, sensor 2 `233.77 cm`, disagreement `0.14 cm`
- `/readiness`: `ready=false` with explicit reason: calibration profile `missing`; sensor freshness and secure context checks were visible and correct

## External/manual gates not claimed as passed

- LM Studio `/v1/models` reports the configured model loaded, but real `/v1/chat/completions` vision inference did not return within the configured 240-second acceptance attempt. This is an LM Studio/model runtime blocker, not converted into a mock success.
- HTTPS LAN from a real phone requires a locally generated certificate trusted by that phone; no private key or certificate is stored in the repository.
- Sensor-camera calibration requires at least three measured planar targets and an accepted residual gate. No profile is marked validated without those measurements.
- Real HP camera-back capture, reconnect, and paired IoT comparison remain manual steps in `docs/mobile-test-protocol.md`.

The implementation therefore passes all reproducible code, build, depth, serial, API, and audit gates while keeping the external LM Studio, certificate trust, and physical calibration gates explicitly visible.
