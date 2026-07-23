const elements = {
  systemStatusToggle: document.querySelector("#system-status-toggle"),
  systemStatusPanel: document.querySelector("#system-status-panel"),
  systemStatusSummary: document.querySelector("#system-status-summary"),
  systemStatusCaption: document.querySelector("#system-status-caption"),
  backendStatus: document.querySelector("#backend-status-output"),
  gemmaStatus: document.querySelector("#gemma-status-output"),
  sensorRuntimeStatus: document.querySelector("#sensor-runtime-status-output"),
  form: document.querySelector("#analyze-form"),
  uploadDropzone: document.querySelector("#upload-dropzone"),
  imageInput: document.querySelector("#image-input"),
  uploadLabel: document.querySelector("#upload-label"),
  selectedPreview: document.querySelector("#selected-preview"),
  imagePreview: document.querySelector("#image-preview"),
  selectedFileName: document.querySelector("#selected-file-name"),
  removeImage: document.querySelector("#remove-image"),
  mode: document.querySelector("#mode-select"),
  analyze: document.querySelector("#analyze-button"),
  analysisControlPanel: document.querySelector("#analysis-control-panel"),
  sourceTabs: Array.from(document.querySelectorAll(".source-tab")),
  uploadPanel: document.querySelector("#upload-panel"),
  cameraPanel: document.querySelector("#camera-panel"),
  cameraEmptyState: document.querySelector("#camera-empty-state"),
  cameraRetry: document.querySelector("#camera-retry"),
  cameraError: document.querySelector("#camera-error"),
  cameraPreview: document.querySelector("#camera-preview"),
  cameraActions: document.querySelector("#camera-actions"),
  cameraCapture: document.querySelector("#capture-image"),
  cameraSwitch: document.querySelector("#switch-camera"),
  canvas: document.querySelector("#capture-canvas"),
  sensorLivePanel: document.querySelector("#sensor-live-panel"),
  sensorPairStatus: document.querySelector("#sensor-pair-status"),
  liveSensor1: document.querySelector("#sensor-1-output"),
  liveSensor2: document.querySelector("#sensor-2-output"),
  sensorConnectionMeta: document.querySelector("#sensor-connection-meta"),
  calibrationMeasured: document.querySelector("#calibration-measured-cm"),
  calibrationCapture: document.querySelector("#calibration-capture"),
  calibrationReset: document.querySelector("#calibration-reset"),
  calibrationStatus: document.querySelector("#calibration-status"),
  verificationMeasured: document.querySelector("#verification-measured-cm"),
  verificationCapture: document.querySelector("#verification-capture"),
  verificationReset: document.querySelector("#verification-reset"),
  verificationStatus: document.querySelector("#verification-status"),
  error: document.querySelector("#error-message"),
  loading: document.querySelector("#loading-state"),
  loadingSteps: Array.from(document.querySelectorAll(".loading-steps li")),
  resultShell: document.querySelector("#result-shell"),
  finalDescription: document.querySelector("#final-description"),
  finalSystemNote: document.querySelector("#final-system-note"),
  modeOutput: document.querySelector("#mode-output"),
  modeHelper: document.querySelector("#mode-helper"),
  sensorStatusOutput: document.querySelector("#sensor-status-output"),
  sensorStatusHelper: document.querySelector("#sensor-status-helper"),
  frontalReference: document.querySelector("#frontal-reference-output"),
  frontalReferenceHelper: document.querySelector("#frontal-reference-helper"),
  totalLatency: document.querySelector("#total-latency-output"),
  latencyHelper: document.querySelector("#latency-helper"),
  mainObject: document.querySelector("#main-object-output"),
  objectPosition: document.querySelector("#object-position-output"),
  sceneType: document.querySelector("#scene-type-output"),
  gemmaDescription: document.querySelector("#gemma-description"),
  contributionStatus: document.querySelector("#contribution-status"),
  resultSensor1: document.querySelector("#result-sensor-1-output"),
  resultSensor2: document.querySelector("#result-sensor-2-output"),
  disagreement: document.querySelector("#pair-disagreement-output"),
  resultReference: document.querySelector("#result-frontal-reference-output"),
  sensor1Age: document.querySelector("#sensor-1-age-output"),
  sensor2Age: document.querySelector("#sensor-2-age-output"),
  matchTime: document.querySelector("#match-time-output"),
  resultCalibration: document.querySelector("#result-calibration-output"),
  sensorExplanation: document.querySelector("#sensor-explanation"),
  sensorReason: document.querySelector("#sensor-reason"),
  gemmaLatency: document.querySelector("#gemma-latency-output"),
  sensorLatency: document.querySelector("#sensor-latency-output"),
  totalProcessLatency: document.querySelector("#total-process-latency-output"),
  latencyNote: document.querySelector("#latency-output"),
  rawPayload: document.querySelector("#raw-payload-output"),
};
const pageMode = document.body?.dataset.pageMode || "demo";

const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const CAPTURE_BATCH_STORAGE_KEY = "bridge-gap-clean-capture-batch-id-v2";

let selectedBlob = null;
let cameraStream = null;
let cameraFacingMode = "environment";
let activeSource = "upload";
let captureClock = null;
let sensorStatusTimer = null;
let loadingTimer = null;
let loadingIndex = 0;
let latestSensorPaired = false;
let calibrationFrozen = false;
let previewUrl = null;
let captureSaving = false;
const captureBatchId = getOrCreateCaptureBatchId();

elements.systemStatusToggle?.addEventListener("click", () => {
  const expanded = elements.systemStatusToggle.getAttribute("aria-expanded") === "true";
  elements.systemStatusToggle.setAttribute("aria-expanded", String(!expanded));
  elements.systemStatusPanel?.classList.toggle("hidden", expanded);
});

elements.sourceTabs.forEach((tab) => {
  tab.addEventListener("click", () => setSourceTab(tab.id === "source-camera-tab" ? "camera" : "upload"));
});

elements.imageInput?.addEventListener("change", () => {
  const [file] = elements.imageInput.files || [];
  if (file) setSelectedImage(file);
});

elements.uploadDropzone?.addEventListener("dragover", (event) => {
  event.preventDefault();
  elements.uploadDropzone.classList.add("is-dragging");
});

elements.uploadDropzone?.addEventListener("dragleave", () => {
  elements.uploadDropzone.classList.remove("is-dragging");
});

elements.uploadDropzone?.addEventListener("drop", (event) => {
  event.preventDefault();
  elements.uploadDropzone.classList.remove("is-dragging");
  const [file] = event.dataTransfer?.files || [];
  if (file) setSelectedImage(file);
});

elements.removeImage?.addEventListener("click", clearSelectedImage);
elements.cameraRetry?.addEventListener("click", startCamera);
elements.cameraCapture?.addEventListener("click", captureFrame);
elements.cameraSwitch?.addEventListener("click", async () => {
  cameraFacingMode = cameraFacingMode === "environment" ? "user" : "environment";
  await startCamera();
});
elements.form?.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAnalysis();
});
elements.calibrationCapture?.addEventListener("click", captureCalibrationPoint);
elements.calibrationReset?.addEventListener("click", resetCalibration);
elements.verificationCapture?.addEventListener("click", captureVerificationPoint);
elements.verificationReset?.addEventListener("click", resetVerification);
window.addEventListener("beforeunload", () => {
  stopCamera();
  stopSensorStatusPolling();
});

document.querySelectorAll(".help-dot").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    showHelpPopover(button);
  });
});
document.addEventListener("click", hideHelpPopover);
window.addEventListener("resize", hideHelpPopover);

function setSourceTab(source) {
  activeSource = source;
  const cameraActive = source === "camera";
  elements.sourceTabs.forEach((tab) => {
    const active = tab.id === (cameraActive ? "source-camera-tab" : "source-upload-tab");
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  elements.uploadPanel?.classList.toggle("hidden", cameraActive);
  elements.uploadPanel?.toggleAttribute("hidden", cameraActive);
  elements.cameraPanel?.classList.toggle("hidden", !cameraActive);
  elements.cameraPanel?.toggleAttribute("hidden", !cameraActive);
  elements.analysisControlPanel?.classList.toggle("hidden", cameraActive);
  elements.analysisControlPanel?.toggleAttribute("hidden", cameraActive);
  elements.selectedPreview?.classList.toggle("hidden", cameraActive || !selectedBlob);
  if (cameraActive) {
    startCamera();
    startSensorStatusPolling();
  } else {
    stopCamera();
    stopSensorStatusPolling();
  }
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showCameraError("Peramban tidak mendukung akses kamera. Gunakan tab Upload sebagai alternatif.");
    return;
  }
  stopCamera();
  hideCameraError();
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: cameraFacingMode } },
      audio: false,
    });
    elements.cameraPreview.srcObject = cameraStream;
    elements.cameraPreview.classList.remove("hidden");
    elements.cameraEmptyState?.classList.add("hidden");
    elements.cameraActions?.classList.remove("hidden");
    updateCameraCaptureAvailability();
    elements.cameraSwitch.disabled = false;
    elements.cameraSwitch.textContent = cameraFacingMode === "environment"
      ? "Ganti ke kamera depan"
      : "Ganti ke kamera belakang";
    if (!captureClock) syncCaptureClock().catch(() => {});
  } catch (error) {
    showCameraError("Kamera tidak dapat diakses. Periksa izin kamera atau gunakan tab Upload.");
  }
}

function stopCamera() {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  updateCameraCaptureAvailability();
  if (elements.cameraPreview) {
    elements.cameraPreview.srcObject = null;
    elements.cameraPreview.classList.add("hidden");
  }
  elements.cameraActions?.classList.add("hidden");
  elements.cameraEmptyState?.classList.remove("hidden");
}

async function captureFrame() {
  const video = elements.cameraPreview;
  if (!video?.videoWidth || !video?.videoHeight) {
    showCameraError("Frame kamera belum siap.");
    return;
  }
  captureSaving = true;
  updateCameraCaptureAvailability();
  hideCameraError();
  try {
    if (!captureClock) await syncCaptureClock();
    elements.canvas.width = video.videoWidth;
    elements.canvas.height = video.videoHeight;
    elements.canvas.getContext("2d").drawImage(video, 0, 0);
    const capturedAt = Date.now();
    const blob = await new Promise((resolve) => elements.canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob) {
      throw new Error("Frame kamera gagal dibuat.");
    }
    const file = new File([blob], "camera-" + capturedAt + ".jpg", { type: "image/jpeg" });
    const form = new FormData();
    form.append("image", file, file.name);
    form.append("capture_id", createClientId("demo", capturedAt));
    form.append("capture_time_ms", String(capturedAt));
    form.append("camera_facing_mode", cameraFacingMode);
    form.append("mode", elements.mode?.value || "sensor_assisted");
    form.append("clock_offset_ms", String(captureClock.offset_ms));
    form.append("clock_rtt_ms", String(captureClock.rtt_ms));
    if (!window.AnalysisJobClient) {
      throw new Error("Klien antrean analisis tidak tersedia.");
    }
    setSelectedImage(file);
    setLoading(true);
    const payload = await window.AnalysisJobClient.analyze(form);
    renderResult(payload);
  } catch (error) {
    showCameraError(error.message || "Analisis kamera gagal.");
  } finally {
    setLoading(false);
    captureSaving = false;
    updateCameraCaptureAvailability();
  }
}

function setSelectedImage(file) {
  if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
    showError("Format file belum didukung. Gunakan JPG, PNG, atau WebP.");
    return;
  }
  selectedBlob = file;
  showPreview(file);
  setActionAvailability(true);
  hideError();
}

function showPreview(file) {
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  elements.imagePreview.src = previewUrl;
  elements.selectedFileName.textContent = file.name || "Gambar hasil kamera";
  elements.uploadLabel.textContent = "Ganti gambar";
  elements.uploadDropzone?.classList.add("has-image");
  elements.selectedPreview?.classList.remove("hidden");
}

function clearSelectedImage() {
  selectedBlob = null;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  elements.imageInput.value = "";
  elements.imagePreview.removeAttribute("src");
  elements.selectedFileName.textContent = "Gambar terpilih";
  elements.uploadLabel.textContent = "Letakkan gambar dalam ruangan di sini";
  elements.uploadDropzone?.classList.remove("has-image", "is-dragging");
  elements.selectedPreview?.classList.add("hidden");
  setActionAvailability(false);
}

async function submitAnalysis() {
  if (!selectedBlob) return;
  setLoading(true);
  hideError();
  try {
    const form = new FormData();
    form.append("image", selectedBlob, selectedBlob.name || "gambar.jpg");
    form.append("mode", elements.mode?.value || "sensor_assisted");
    form.append("save_result", "true");
    if (!window.AnalysisJobClient) {
      throw new Error("Klien antrean analisis tidak tersedia.");
    }
    const result = await window.AnalysisJobClient.analyze(form);
    renderResult(result);
  } catch (error) {
    showError(error.message || "Analisis gagal.");
  } finally {
    setLoading(false);
  }
}

function renderResult(data) {
  const contribution = data.sensor_contribution || {};
  const evidence = data.sensor_evidence || {};
  const samples = evidence.samples || {};
  const latency = data.latency || {};
  const structured = data.gemma_structured || {};
  const status = contribution.status || "not_applicable";
  const reference = contribution.frontal_reference_cm;
  const sensor1 = contribution.sensor_1_cm ?? samples.sensor_1?.distance_cm;
  const sensor2 = contribution.sensor_2_cm ?? samples.sensor_2?.distance_cm;
  const sensor1Corrected = contribution.sensor_1_corrected_cm;
  const sensor2Corrected = contribution.sensor_2_corrected_cm;
  const disagreement = contribution.pair_disagreement_cm ?? evidence.pair_disagreement_cm;

  renderFinalDescription(data.final_description || "Deskripsi tidak tersedia.");
  elements.finalSystemNote.textContent = data.mode === "gemma_only"
    ? "Deskripsi berasal dari satu citra RGB tanpa kontribusi sensor."
    : "Referensi frontal ditambahkan setelah deskripsi visual dan tidak diikat ke objek bernama.";
  elements.modeOutput.textContent = labelMode(data.mode);
  elements.modeHelper.textContent = data.mode === "gemma_only"
    ? "Gemma membaca satu citra RGB."
    : "Gemma membaca citra; sensor diverifikasi secara deterministik.";
  elements.sensorStatusOutput.textContent = labelContributionStatus(status);
  elements.sensorStatusHelper.textContent = contribution.reason_code
    ? "Gate: " + formatToken(contribution.reason_code)
    : "Pasangan sensor memenuhi gate.";
  elements.frontalReference.textContent = formatCm(reference);
  elements.frontalReferenceHelper.textContent = Number.isFinite(Number(reference))
    ? "Rata-rata nilai Sensor 1 dan Sensor 2 setelah koreksi kalibrasi."
    : "Rata-rata tidak digunakan pada hasil ini.";
  elements.totalLatency.textContent = formatMs(latency.total_ms);
  elements.latencyHelper.textContent = "Waktu proses total; bukan indikator kualitas deskripsi.";

  elements.mainObject.textContent = formatToken(structured.main_object);
  elements.objectPosition.textContent = formatToken(structured.object_position);
  elements.sceneType.textContent = formatToken(structured.scene_type);
  elements.gemmaDescription.textContent = data.gemma_description || "-";

  elements.contributionStatus.textContent = labelContributionStatus(status);
  elements.resultSensor1.textContent = formatRawCorrectedCm(sensor1, sensor1Corrected);
  elements.resultSensor2.textContent = formatRawCorrectedCm(sensor2, sensor2Corrected);
  elements.disagreement.textContent = formatCm(disagreement);
  elements.resultReference.textContent = formatCm(reference);
  elements.sensor1Age.textContent = formatSignedMs(samples.sensor_1?.age_ms);
  elements.sensor2Age.textContent = formatSignedMs(samples.sensor_2?.age_ms);
  elements.matchTime.textContent = formatTimestamp(evidence.match_time_ms);
  elements.resultCalibration.textContent = formatToken(contribution.calibration_status);
  elements.sensorExplanation.textContent = contribution.description || "Tidak berlaku pada mode ini.";
  elements.sensorReason.textContent = contribution.reason_code
    ? "Gate: " + formatToken(contribution.reason_code)
    : "Pasangan sensor memenuhi gate.";

  elements.gemmaLatency.textContent = formatMs(latency.gemma_ms);
  elements.sensorLatency.textContent = formatMs(latency.sensor_ms);
  elements.totalProcessLatency.textContent = formatMs(latency.total_ms);
  elements.latencyNote.textContent = "Gemma " + formatMs(latency.gemma_ms)
    + " · Sensor " + formatMs(latency.sensor_ms)
    + " · Total " + formatMs(latency.total_ms);
  elements.rawPayload.textContent = JSON.stringify(data, null, 2);
  elements.resultShell?.classList.remove("hidden");
  elements.resultShell?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderFinalDescription(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  elements.finalDescription.replaceChildren(paragraph);
}

async function refreshRuntimeStatus() {
  try {
    const [healthResponse, readinessResponse] = await Promise.all([
      fetch("/health", { cache: "no-store" }),
      fetch("/readiness", { cache: "no-store" }),
    ]);
    const health = await healthResponse.json();
    const readiness = await readinessResponse.json();
    const backendReady = healthResponse.ok && health.backend === "ok";
    const gemmaReady = ["ready", "mock"].includes(readiness.checks?.gemma || health.gemma);
    const sensorStatus = readiness.checks?.sensor || "unavailable";
    elements.backendStatus.textContent = backendReady ? "SIAP" : "GALAT";
    elements.gemmaStatus.textContent = gemmaReady ? "SIAP" : formatToken(readiness.checks?.gemma || health.gemma);
    elements.sensorRuntimeStatus.textContent = formatToken(sensorStatus).toUpperCase();
    elements.systemStatusSummary.textContent = backendReady && gemmaReady ? "Sistem analisis siap" : "Periksa sistem";
    elements.systemStatusCaption.textContent = backendReady && gemmaReady ? "SIAP" : "PERIKSA";
    elements.systemStatusToggle?.classList.toggle("is-warning", !(backendReady && gemmaReady));
    elements.systemStatusPanel?.classList.toggle("is-warning", !(backendReady && gemmaReady));
  } catch (_error) {
    elements.backendStatus.textContent = "GALAT";
    elements.gemmaStatus.textContent = "TIDAK DIKETAHUI";
    elements.sensorRuntimeStatus.textContent = "TIDAK DIKETAHUI";
    elements.systemStatusSummary.textContent = "Periksa sistem";
    elements.systemStatusCaption.textContent = "PERIKSA";
  }
}

async function refreshSensorStatus() {
  try {
    const response = await fetch("/sensor-status", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    renderLiveSensorStatus(await response.json());
  } catch (error) {
    renderLiveSensorStatus({
      enabled: true,
      connected: false,
      status: "unavailable",
      samples: {},
      reader_error: "Status sensor tidak tersedia (" + error.message + ").",
    });
  }
}

function renderLiveSensorStatus(evidence) {
  const samples = evidence.samples || {};
  const status = evidence.status || "unavailable";
  latestSensorPaired = status === "paired";
  elements.sensorPairStatus.textContent = labelSensorStatus(status);
  elements.liveSensor1.textContent = formatLiveSample(samples.sensor_1);
  elements.liveSensor2.textContent = formatLiveSample(samples.sensor_2);
  elements.sensorLivePanel?.classList.toggle("is-paired", latestSensorPaired);
  elements.sensorLivePanel?.classList.toggle("is-partial", status === "partial");
  elements.sensorLivePanel?.classList.toggle("is-disconnected", evidence.enabled && !evidence.connected);
  elements.calibrationCapture.disabled = !latestSensorPaired || calibrationFrozen;
  elements.verificationCapture.disabled = !latestSensorPaired || !calibrationFrozen;
  updateCameraCaptureAvailability();
  const port = evidence.port || "port belum dikonfigurasi";
  elements.sensorConnectionMeta.textContent = evidence.reader_error
    ? port + " · " + evidence.reader_error
    : port + " · jendela data ±" + (evidence.window_ms ?? "-") + " ms";
}

async function refreshCalibrationStatus() {
  try {
    const response = await fetch("/sensor-calibration", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    renderCalibrationStatus((await response.json()).profile || {});
  } catch (error) {
    elements.calibrationStatus.textContent = "Status kalibrasi tidak tersedia (" + error.message + ").";
  }
}

function renderCalibrationStatus(profile) {
  const count = Number(profile.capture_count || 0);
  const distinctCount = Number(profile.distinct_reference_count || 0);
  calibrationFrozen = profile.validated === true && Boolean(profile.correction_model?.sensor_1);
  elements.calibrationStatus?.classList.toggle("is-valid", calibrationFrozen);
  elements.calibrationCapture.disabled = !latestSensorPaired || calibrationFrozen;
  elements.verificationCapture.disabled = !latestSensorPaired || !calibrationFrozen;
  if (calibrationFrozen) {
    elements.calibrationStatus.textContent = "Valid dan dibekukan · " + distinctCount
      + " jarak · " + count + "/150 pembacaan";
    return;
  }
  if (profile.validated === true) {
    elements.calibrationStatus.textContent = "Valid · " + count + " titik";
  } else {
    elements.calibrationStatus.textContent = distinctCount + "/5 jarak · "
      + count + "/150 pembacaan kalibrasi";
  }
}

async function captureCalibrationPoint() {
  const measuredCm = Number(elements.calibrationMeasured?.value);
  if (!Number.isFinite(measuredCm) || measuredCm <= 5 || measuredCm > 400) {
    elements.calibrationStatus.textContent = "Masukkan jarak referensi antara 5 dan 400 cm.";
    return;
  }
  elements.calibrationCapture.disabled = true;
  try {
    const response = await fetch("/sensor-calibration/captures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ measured_cm: measuredCm }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "HTTP " + response.status);
    renderCalibrationStatus(payload.profile || {});
  } catch (error) {
    elements.calibrationStatus.textContent = "Titik tidak tersimpan: " + error.message;
  } finally {
    elements.calibrationCapture.disabled = !latestSensorPaired || calibrationFrozen;
  }
}

async function resetCalibration() {
  if (!window.confirm("Hapus seluruh titik dan profil kalibrasi sensor?")) return;
  try {
    const response = await fetch("/sensor-calibration", { method: "DELETE" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    renderCalibrationStatus({ capture_count: 0, validated: false });
    renderVerificationStatus({ capture_count: 0, verified: false });
  } catch (error) {
    elements.calibrationStatus.textContent = "Kalibrasi gagal direset: " + error.message;
  }
}

async function refreshVerificationStatus() {
  try {
    const response = await fetch("/sensor-calibration/verification", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "HTTP " + response.status);
    renderVerificationStatus(payload.summary || {});
  } catch (error) {
    elements.verificationStatus.textContent = calibrationFrozen
      ? "Status verifikasi tidak tersedia (" + error.message + ")."
      : "Menunggu kalibrasi lengkap.";
  }
}

function renderVerificationStatus(summary) {
  const count = Number(summary.capture_count || 0);
  const distinctCount = Number(summary.distinct_reference_count || 0);
  const requiredReferenceCount = Number(summary.required_reference_distances_cm?.length || 4);
  const samplesPerReference = Number(summary.min_samples_per_reference || 30);
  const requiredCaptureCount = requiredReferenceCount * samplesPerReference;
  elements.verificationStatus?.classList.toggle("is-valid", summary.verified === true);
  if (summary.verified === true) {
    const mae = Number(summary.corrected_metrics?.mae_cm);
    elements.verificationStatus.textContent = "Terverifikasi · " + count + "/" + requiredCaptureCount
      + " pembacaan · MAE koreksi "
      + (Number.isFinite(mae) ? mae.toFixed(2) + " cm" : "-");
    return;
  }
  elements.verificationStatus.textContent = distinctCount + "/" + requiredReferenceCount + " jarak · "
    + count + "/" + requiredCaptureCount + " pembacaan verifikasi";
}

async function captureVerificationPoint() {
  const measuredCm = Number(elements.verificationMeasured?.value);
  if (!Number.isFinite(measuredCm) || ![40, 80, 125, 175].includes(measuredCm)) {
    elements.verificationStatus.textContent = "Masukkan titik verifikasi 40, 80, 125, atau 175 cm.";
    return;
  }
  elements.verificationCapture.disabled = true;
  try {
    const response = await fetch("/sensor-calibration/verification/captures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ measured_cm: measuredCm }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "HTTP " + response.status);
    renderVerificationStatus(payload.summary || {});
  } catch (error) {
    elements.verificationStatus.textContent = "Verifikasi tidak tersimpan: " + error.message;
  } finally {
    elements.verificationCapture.disabled = !latestSensorPaired || !calibrationFrozen;
  }
}

async function resetVerification() {
  if (!window.confirm("Hapus seluruh data verifikasi sensor?")) return;
  try {
    const response = await fetch("/sensor-calibration/verification", { method: "DELETE" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    renderVerificationStatus({ capture_count: 0, verified: false });
  } catch (error) {
    elements.verificationStatus.textContent = "Verifikasi gagal direset: " + error.message;
  }
}

async function syncCaptureClock() {
  const startedAt = performance.now();
  const clientBefore = Date.now();
  const response = await fetch("/time-sync", { cache: "no-store" });
  if (!response.ok) throw new Error("Sinkronisasi waktu backend gagal.");
  const payload = await response.json();
  const clientAfter = Date.now();
  captureClock = {
    offset_ms: Math.round(payload.server_time_ms - ((clientBefore + clientAfter) / 2)),
    rtt_ms: Math.max(0, Math.round(performance.now() - startedAt)),
  };
  return captureClock;
}

function startSensorStatusPolling() {
  if (sensorStatusTimer !== null) return;
  refreshSensorStatus();
  refreshCalibrationStatus();
  refreshVerificationStatus();
  sensorStatusTimer = window.setInterval(refreshSensorStatus, 1000);
}

function stopSensorStatusPolling() {
  if (sensorStatusTimer === null) return;
  window.clearInterval(sensorStatusTimer);
  sensorStatusTimer = null;
}

function setLoading(isLoading) {
  elements.loading?.classList.toggle("hidden", !isLoading);
  elements.analyze.disabled = isLoading || !selectedBlob;
  if (isLoading) {
    loadingIndex = 0;
    markLoadingStep();
    loadingTimer = window.setInterval(() => {
      loadingIndex = (loadingIndex + 1) % elements.loadingSteps.length;
      markLoadingStep();
    }, 1000);
  } else if (loadingTimer !== null) {
    window.clearInterval(loadingTimer);
    loadingTimer = null;
  }
}

function markLoadingStep() {
  elements.loadingSteps.forEach((step, index) => step.classList.toggle("is-active", index === loadingIndex));
}

function setActionAvailability(available) {
  elements.analyze.disabled = !available || activeSource === "camera";
}

function updateCameraCaptureAvailability() {
  const sensorRequired = (elements.mode?.value || "sensor_assisted") === "sensor_assisted";
  elements.cameraCapture.disabled = !cameraStream || captureSaving || (sensorRequired && !latestSensorPaired);
}

function getOrCreateCaptureBatchId() {
  try {
    const existing = window.localStorage.getItem(CAPTURE_BATCH_STORAGE_KEY);
    if (existing) return existing;
    const created = createClientId("batch", Date.now());
    window.localStorage.setItem(CAPTURE_BATCH_STORAGE_KEY, created);
    return created;
  } catch (_error) {
    return createClientId("batch", Date.now());
  }
}

function createClientId(prefix, timestamp) {
  return crypto.randomUUID?.() || prefix + "-" + timestamp + "-" + Math.random().toString(16).slice(2);
}

function showError(message) {
  elements.error.textContent = message;
  elements.error.classList.remove("hidden");
}

function hideError() {
  elements.error.textContent = "";
  elements.error.classList.add("hidden");
}

function showCameraError(message) {
  elements.cameraError.textContent = message;
  elements.cameraError.classList.remove("hidden");
}

function hideCameraError() {
  elements.cameraError.textContent = "";
  elements.cameraError.classList.add("hidden");
}

function showHelpPopover(button) {
  hideHelpPopover();
  const popover = document.createElement("div");
  popover.id = "active-help-popover";
  popover.className = "help-popover";
  const title = document.createElement("strong");
  title.textContent = button.dataset.helpTitle || "Informasi";
  const text = document.createElement("p");
  text.textContent = button.dataset.helpText || "";
  popover.append(title, text);
  document.body.append(popover);
  const rect = button.getBoundingClientRect();
  const left = Math.min(window.innerWidth - popover.offsetWidth - 16, Math.max(16, rect.right - popover.offsetWidth));
  popover.style.left = left + "px";
  popover.style.top = Math.min(window.innerHeight - popover.offsetHeight - 16, rect.bottom + 8) + "px";
  button.setAttribute("aria-expanded", "true");
}

function hideHelpPopover() {
  const popover = document.querySelector("#active-help-popover");
  popover?.remove();
  document.querySelectorAll(".help-dot[aria-expanded='true']").forEach((button) => {
    button.setAttribute("aria-expanded", "false");
  });
}

function formatLiveSample(sample) {
  if (!Number.isFinite(Number(sample?.distance_cm))) return "Belum ada sampel valid";
  const age = Number.isFinite(Number(sample.age_ms)) ? " · " + Math.abs(Number(sample.age_ms)) + " ms" : "";
  return Number(sample.distance_cm).toFixed(1) + " cm" + age;
}

function formatCm(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(1) + " cm" : "-";
}

function formatRawCorrectedCm(rawValue, correctedValue) {
  const raw = Number(rawValue);
  const corrected = Number(correctedValue);
  if (!Number.isFinite(raw)) return "-";
  if (!Number.isFinite(corrected)) return formatCm(raw);
  return raw.toFixed(1) + " cm → " + corrected.toFixed(1) + " cm";
}

function formatMs(value) {
  return Number.isFinite(Number(value)) ? Math.round(Number(value)) + " ms" : "-";
}

function formatSignedMs(value) {
  return Number.isFinite(Number(value)) ? Number(value) + " ms" : "-";
}

function formatTimestamp(value) {
  return Number.isFinite(Number(value)) ? new Date(Number(value)).toLocaleString("id-ID") : "-";
}

function formatToken(value) {
  if (value === undefined || value === null || value === "") return "-";
  return String(value).replaceAll("_", " ");
}

function labelMode(mode) {
  return mode === "gemma_only" ? "Gemma Only" : "Sensor Assisted";
}

function labelContributionStatus(status) {
  const labels = {
    applied: "DITERAPKAN",
    conflict: "KONFLIK",
    partial: "PARSIAL",
    stale: "STALE",
    insufficient: "DITAHAN",
    not_applicable: "TIDAK DIGUNAKAN",
  };
  return labels[status] || formatToken(status).toUpperCase();
}

function labelSensorStatus(status) {
  const labels = {
    paired: "2 SENSOR AKTIF",
    partial: "1 SENSOR AKTIF",
    disabled: "NONAKTIF",
    unavailable: "TIDAK TERSEDIA",
  };
  return labels[status] || formatToken(status).toUpperCase();
}

refreshRuntimeStatus();
refreshCalibrationStatus();
refreshVerificationStatus();
window.setInterval(refreshRuntimeStatus, 10000);
