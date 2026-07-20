const systemStatusToggle = document.querySelector("#system-status-toggle");
const systemStatusPanel = document.querySelector("#system-status-panel");
const systemStatusSummary = document.querySelector("#system-status-summary");
const systemStatusCaption = document.querySelector("#system-status-caption");
const backendStatusOutput = document.querySelector("#backend-status-output");
const gemmaStatusOutput = document.querySelector("#gemma-status-output");
const depthRuntimeStatusOutput = document.querySelector("#depth-runtime-status-output");
const formElement = document.querySelector("#analyze-form");
const uploadDropzone = document.querySelector("#upload-dropzone");
const imageInput = document.querySelector("#image-input");
const uploadLabel = document.querySelector("#upload-label");
const selectedPreview = document.querySelector("#selected-preview");
const selectedFileName = document.querySelector("#selected-file-name");
const removeImageButton = document.querySelector("#remove-image");
const modeSelect = document.querySelector("#mode-select");
const analyzeButton = document.querySelector("#analyze-button");
const compareButton = document.querySelector("#compare-button");
const imagePreview = document.querySelector("#image-preview");
const sourceTabs = Array.from(document.querySelectorAll(".source-tab"));
const sourceUploadTab = document.querySelector("#source-upload-tab");
const sourceCameraTab = document.querySelector("#source-camera-tab");
const uploadPanel = document.querySelector("#upload-panel");
const cameraPanel = document.querySelector("#camera-panel");
const cameraEmptyState = document.querySelector("#camera-empty-state");
const cameraRetryButton = document.querySelector("#camera-retry");
const cameraError = document.querySelector("#camera-error");
const errorMessage = document.querySelector("#error-message");
const loadingState = document.querySelector("#loading-state");
const loadingSteps = Array.from(document.querySelectorAll(".loading-steps li"));
const resultShell = document.querySelector("#result-shell");
const finalDescription = document.querySelector("#final-description");
const finalSystemNote = document.querySelector("#final-system-note");
const gemmaDescription = document.querySelector("#gemma-description");
const depthSummary = document.querySelector("#depth-summary");
const latencyOutput = document.querySelector("#latency-output");
const modeOutput = document.querySelector("#mode-output");
const distanceCategoryOutput = document.querySelector("#distance-category-output");
const nearestRegionOutput = document.querySelector("#nearest-region-output");
const totalLatencyOutput = document.querySelector("#total-latency-output");
const modeHelperOutput = document.querySelector("#mode-helper");
const distanceCategoryHelperOutput = document.querySelector("#distance-category-helper");
const nearestRegionHelperOutput = document.querySelector("#nearest-region-helper");
const latencyHelperOutput = document.querySelector("#latency-helper");
const modeHelpButton = document.querySelector("#mode-help");
const distanceCategoryHelpButton = document.querySelector("#distance-category-help");
const nearestRegionHelpButton = document.querySelector("#nearest-region-help");
const latencyHelpButton = document.querySelector("#latency-help");
const gemmaLatencyOutput = document.querySelector("#gemma-latency-output");
const depthLatencyOutput = document.querySelector("#depth-latency-output");
const fusionLatencyOutput = document.querySelector("#fusion-latency-output");
const mainObjectOutput = document.querySelector("#main-object-output");
const objectPositionOutput = document.querySelector("#object-position-output");
const sceneTypeOutput = document.querySelector("#scene-type-output");
const depthStatusOutput = document.querySelector("#depth-status-output");
const openAreaOutput = document.querySelector("#safe-direction-output");
const depthContribution = document.querySelector("#depth-contribution");
const comparisonStatus = document.querySelector("#comparison-status");
const comparisonOutput = document.querySelector("#comparison-output");
const depthMapPreview = document.querySelector("#depth-map-preview");
const depthMapGridWrap = document.querySelector("#depth-map-grid-wrap");
const depthRegionGrid = document.querySelector("#depth-region-grid");
const captureImageButton = document.querySelector("#capture-image");
const switchCameraButton = document.querySelector("#switch-camera");
const cameraPreview = document.querySelector("#camera-preview");
const cameraActions = document.querySelector("#camera-actions");
const captureCanvas = document.querySelector("#capture-canvas");
const sensorLivePanel = document.querySelector("#sensor-live-panel");
const sensorPairStatus = document.querySelector("#sensor-pair-status");
const sensor1Output = document.querySelector("#sensor-1-output");
const sensor2Output = document.querySelector("#sensor-2-output");
const sensorConnectionMeta = document.querySelector("#sensor-connection-meta");
const sensorCaptureStatus = document.querySelector("#sensor-capture-status");
let captureClock = null;

const REGION_LABELS = {
  upper_left: "atas-kiri",
  upper_center: "atas-tengah",
  upper_right: "atas-kanan",
  middle_left: "tengah-kiri",
  middle_center: "tengah",
  middle_right: "tengah-kanan",
  lower_left: "bawah-kiri",
  lower_center: "bawah-tengah",
  lower_right: "bawah-kanan",
  tidak_diketahui: "tidak diketahui",
};

const MODE_LABELS = {
  gemma_only: "Gemma Baseline",
  depth_only: "Kedalaman Saja",
  gemma_depth: "Gemma + Kedalaman Late Fusion",
};

const PROVENANCE_LABELS = {
  gemma: "Gemma",
  depth: "Depth",
  inference: "Inferensi",
  template: "Template",
  guardrail: "Batasan",
};

const SCENE_LABELS = {
  indoor: "dalam ruangan",
  non_indoor: "luar ruangan",
  tidak_diketahui: "tidak diketahui",
};

let selectedBlob = null;
let selectedCaptureMeta = null;
let cameraStream = null;
let cameraFacingMode = "environment";
let activeSource = "upload";
let loadingTimer = null;
let loadingIndex = 0;
let dragDepth = 0;
let sensorStatusTimer = null;

const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

function stopCameraStream() {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  cameraPreview.srcObject = null;
  cameraPreview.classList.add("hidden");
  cameraActions.classList.add("hidden");
  captureImageButton.disabled = true;
  switchCameraButton.disabled = true;
  cameraEmptyState.classList.remove("hidden");
}

function hideCameraError() {
  cameraError.textContent = "";
  cameraError.classList.add("hidden");
}

function showCameraError(message) {
  cameraError.textContent = message;
  cameraError.classList.remove("hidden");
}

function formatSensorSample(sample) {
  if (!sample || !Number.isFinite(Number(sample.distance_cm))) {
    return "Belum ada sampel valid";
  }
  const age = Number.isFinite(Number(sample.age_ms)) ? ` · selisih ${Math.abs(Number(sample.age_ms))} ms` : "";
  return `${Number(sample.distance_cm).toFixed(1)} cm${age}`;
}

function getSensorStatusLabel(status, connected) {
  const labels = {
    paired: "2 SENSOR AKTIF",
    partial: "1 SENSOR AKTIF",
    disabled: "NONAKTIF",
    camera_sensor_direction_mismatch: "ARAH TIDAK SESUAI",
  };
  return labels[status] || (connected ? "MENUNGGU DATA" : "TERPUTUS");
}

function renderLiveSensorStatus(evidence) {
  if (!sensorLivePanel) {
    return;
  }
  const status = evidence?.status || "unavailable";
  const samples = evidence?.samples || {};
  sensorPairStatus.textContent = getSensorStatusLabel(status, evidence?.connected);
  sensor1Output.textContent = formatSensorSample(samples.sensor_1);
  sensor2Output.textContent = formatSensorSample(samples.sensor_2);
  sensorLivePanel.classList.toggle("is-paired", status === "paired");
  sensorLivePanel.classList.toggle("is-partial", status === "partial");
  sensorLivePanel.classList.toggle("is-disconnected", Boolean(evidence?.enabled && !evidence?.connected));

  const port = evidence?.port || "port belum dikonfigurasi";
  const attempts = Number(evidence?.connection_attempts || 0);
  sensorConnectionMeta.textContent = evidence?.reader_error
    ? `${port} · gagal tersambung (${attempts} percobaan): ${evidence.reader_error}`
    : `${port} · jendela data ±${evidence?.window_ms ?? "-"} ms`;
}

function renderCapturedSensorEvidence(evidence) {
  if (!sensorCaptureStatus) {
    return;
  }
  if (!evidence) {
    sensorCaptureStatus.textContent = "Analisis ini tidak membawa metadata capture kamera.";
    return;
  }
  if (evidence.status === "camera_sensor_direction_mismatch") {
    sensorCaptureStatus.textContent = "Evidence tidak dipasangkan karena frame berasal dari kamera depan, sedangkan sensor menghadap ke depan perangkat.";
    return;
  }
  const source = evidence.match_time_source === "client_capture" ? "waktu frame kamera" : "waktu terima server";
  const count = Object.keys(evidence.samples || {}).length;
  sensorCaptureStatus.textContent = `Capture ${evidence.capture_id || "tanpa ID"}: ${count}/2 sensor cocok memakai ${source} dalam jendela ±${evidence.window_ms ?? "-"} ms.`;
}

async function refreshSensorStatus() {
  try {
    const response = await fetch("/sensor-status", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    renderLiveSensorStatus(await response.json());
  } catch (error) {
    renderLiveSensorStatus({
      status: "unavailable",
      connected: false,
      samples: {},
      reader_error: `status web tidak tersedia (${error.message})`,
    });
  }
}

function startSensorStatusPolling() {
  if (sensorStatusTimer !== null) {
    return;
  }
  refreshSensorStatus();
  sensorStatusTimer = window.setInterval(refreshSensorStatus, 1000);
}

function stopSensorStatusPolling() {
  if (sensorStatusTimer === null) {
    return;
  }
  window.clearInterval(sensorStatusTimer);
  sensorStatusTimer = null;
}

async function activateCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showCameraError("Peramban tidak mendukung akses kamera. Gunakan tab Upload sebagai alternatif.");
    return;
  }

  try {
    await openCamera(cameraFacingMode);
    hideCameraError();
  } catch (_error) {
    showCameraError("Kamera tidak dapat diakses. Periksa izin kamera atau gunakan tab Upload.");
  }
}

function setSourceTab(source, { focus = false } = {}) {
  activeSource = source;
  const cameraActive = source === "camera";

  sourceTabs.forEach((tab) => {
    const isActive = tab === (cameraActive ? sourceCameraTab : sourceUploadTab);
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
  });

  uploadPanel.classList.toggle("hidden", cameraActive);
  uploadPanel.hidden = cameraActive;
  cameraPanel.classList.toggle("hidden", !cameraActive);
  cameraPanel.hidden = !cameraActive;

  if (focus) {
    (cameraActive ? sourceCameraTab : sourceUploadTab)?.focus();
  }

  if (cameraActive) {
    activateCamera();
    startSensorStatusPolling();
  } else {
    stopCameraStream();
    stopSensorStatusPolling();
    hideCameraError();
  }
}

sourceTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => {
    setSourceTab(tab === sourceCameraTab ? "camera" : "upload");
  });

  tab.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const nextIndex = event.key === "ArrowRight" ? (index + 1) % sourceTabs.length : (index - 1 + sourceTabs.length) % sourceTabs.length;
    setSourceTab(nextIndex === 1 ? "camera" : "upload", { focus: true });
  });
});

cameraRetryButton?.addEventListener("click", activateCamera);
window.addEventListener("pagehide", () => {
  stopCameraStream();
  stopSensorStatusPolling();
});

refreshHealth();
syncCaptureClock().catch(() => {
  captureClock = null;
});

systemStatusToggle?.addEventListener("click", () => {
  if (!systemStatusPanel) {
    return;
  }

  const isOpen = !systemStatusPanel.classList.contains("hidden");
  systemStatusPanel.classList.toggle("hidden", isOpen);
  systemStatusToggle.setAttribute("aria-expanded", String(!isOpen));
});

document.addEventListener("click", (event) => {
  if (!systemStatusPanel || !systemStatusToggle || systemStatusPanel.classList.contains("hidden")) {
    return;
  }

  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }

  if (systemStatusPanel.contains(target) || systemStatusToggle.contains(target)) {
    return;
  }

  systemStatusPanel.classList.add("hidden");
  systemStatusToggle.setAttribute("aria-expanded", "false");
});

imageInput?.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  if (!file) {
    clearSelectedImage();
    return;
  }

  setSelectedImage(file);
});

imageInput?.addEventListener("focus", () => {
  uploadDropzone?.classList.add("is-focused");
});

imageInput?.addEventListener("blur", () => {
  uploadDropzone?.classList.remove("is-focused");
});

if (uploadDropzone) {
  ["dragenter", "dragover"].forEach((eventName) => {
    uploadDropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      event.stopPropagation();

      if (eventName === "dragenter") {
        dragDepth += 1;
      }

      uploadDropzone.classList.add("is-dragging");
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = "copy";
      }
    });
  });

  uploadDropzone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragDepth = Math.max(0, dragDepth - 1);

    if (dragDepth === 0) {
      uploadDropzone.classList.remove("is-dragging");
    }
  });

  uploadDropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dragDepth = 0;
    uploadDropzone.classList.remove("is-dragging");

    const file = event.dataTransfer?.files?.[0];
    if (!file) {
      showError("Tidak ada file gambar yang diterima.");
      return;
    }

    setSelectedImage(file);
  });
}

function renderMetricExplanations(data, depth, latency, distanceCategory, nearestRegion) {
  const modeLabel = MODE_LABELS[data.mode] || data.mode || "mode tidak diketahui";
  const modeReason = buildModeTooltip(data.mode);
  const distanceReason = buildDistanceCategoryTooltip(distanceCategory, nearestRegion);
  const regionReason = buildNearestRegionTooltip(nearestRegion, distanceCategory);
  const latencyReason = buildLatencyTooltip(latency, data.mode);

  modeHelperOutput.textContent = buildModeHelper(data.mode);
  distanceCategoryHelperOutput.textContent = buildDistanceCategoryHelper(distanceCategory);
  nearestRegionHelperOutput.textContent = buildNearestRegionHelper(nearestRegion);
  latencyHelperOutput.textContent = buildLatencyHelper(latency, data.mode);

  setHelpText(
    modeHelpButton,
    "Mode",
    `Nilai saat ini ${modeLabel}. ${modeReason}`,
  );
  setHelpText(
    distanceCategoryHelpButton,
    "Kategori Kedalaman",
    `${distanceReason} Kategori ini memakai threshold internal pada estimasi peta kedalaman dan belum dikalibrasi sebagai jarak meter presisi.`,
  );
  setHelpText(
    nearestRegionHelpButton,
    "Area Terdekat",
    `${regionReason} Area ini adalah label UI dari region teknis pada peta kedalaman, bukan identitas objek yang pasti.`,
  );
  setHelpText(
    latencyHelpButton,
    "Latensi",
    `${latencyReason} Angka ini menghitung durasi proses, bukan kualitas deskripsi.`,
  );
}

function setHelpText(button, title, text) {
  if (!button) {
    return;
  }
  button.setAttribute("data-help-title", title);
  button.setAttribute("data-help-text", text);
}

function buildModeHelper(mode) {
  if (mode === "gemma_depth") {
    return "Visual + depth regional berbatas bukti.";
  }
  if (mode === "gemma_only") {
    return "Hanya deskripsi visual.";
  }
  if (mode === "depth_only") {
    return "Hanya estimasi kedalaman.";
  }
  return "Mode inferensi terpilih.";
}

function buildModeTooltip(mode) {
  if (mode === "gemma_depth") {
    return "Mode ini menggabungkan deskripsi Gemma dengan ringkasan depth regional. Klaim depth tidak ditempelkan pada objek tertentu karena pipeline belum memiliki lokalisasi objek yang dapat membuktikan ikatan tersebut.";
  }
  if (mode === "gemma_only") {
    return "Mode ini hanya memakai deskripsi visual Gemma, sehingga kontribusi peta kedalaman tidak dihitung pada hasil akhir.";
  }
  if (mode === "depth_only") {
    return "Mode ini memakai ringkasan peta kedalaman saja untuk membaca struktur jarak relatif tanpa deskripsi visual Gemma.";
  }
  return "Mode inferensi berasal dari pilihan analisis saat gambar diproses.";
}

function buildDistanceCategoryHelper(distanceCategory) {
  if (!distanceCategory || distanceCategory === "-" || distanceCategory === "tidak diketahui") {
    return "Belum terbaca dari depth.";
  }
  return `Kedalaman relatif: ${distanceCategory}.`;
}

function buildDistanceCategoryTooltip(distanceCategory, nearestRegion) {
  if (!distanceCategory || distanceCategory === "-" || distanceCategory === "tidak diketahui") {
    return "Kategori belum cukup terbaca karena depth summary tidak menyediakan kategori jarak relatif.";
  }
  return `Nilai ${distanceCategory} muncul karena skor kedalaman pada region teknis ${nearestRegion} masuk ke threshold internal kategori kedalaman relatif ${distanceCategory}.`;
}

function buildNearestRegionHelper(nearestRegion) {
  if (!nearestRegion || nearestRegion === "-" || nearestRegion === "tidak diketahui") {
    return "Area terdekat belum tersedia.";
  }
  return "Region gambar dengan skor depth terdekat.";
}

function buildNearestRegionTooltip(nearestRegion, distanceCategory) {
  if (!nearestRegion || nearestRegion === "-" || nearestRegion === "tidak diketahui") {
    return "Region terdekat belum dapat ditentukan dari peta kedalaman.";
  }
  return `Region teknis ${nearestRegion} dipilih karena area grid tersebut memiliki skor kedalaman terdekat; kategorinya terbaca ${distanceCategory}.`;
}

function buildLatencyHelper(latency, mode) {
  const total = formatMs(latency.total_ms);
  if (total === "-") {
    return "Metadata waktu belum tersedia.";
  }
  const stages = getLatencyStageRuns(mode);
  const stageCount = [stages.gemma, stages.depth, stages.fusion].filter(Boolean).length;
  return `${total}, ${stageCount} tahap berjalan.`;
}

function buildLatencyTooltip(latency, mode) {
  const total = formatMs(latency.total_ms);
  if (total === "-") {
    return "Latensi belum tersedia karena proses belum menghasilkan metadata waktu.";
  }
  const latencyStages = getLatencyStageRuns(mode);
  return `Total ${total} mencakup durasi Gemma ${formatStageMs(latency.gemma_ms, latencyStages.gemma)}, Kedalaman ${formatStageMs(latency.depth_ms, latencyStages.depth)}, dan Fusi ${formatStageMs(latency.fusion_ms, latencyStages.fusion)}. Nilai <1 ms berarti tahap berjalan sangat cepat pada resolusi tampilan milidetik.`;
}

removeImageButton?.addEventListener("click", () => {
  clearSelectedImage();
});

formElement?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedBlob) {
    showError("Pilih atau ambil gambar terlebih dahulu.");
    return;
  }

  setLoading(true);
  hideError();
  try {
    const data = await analyzeMode(modeSelect?.value || "gemma_depth", true);
    renderResult(data);
    renderSingleModeComparison(data);
  } catch (error) {
    showError(error.message || "Analisis gagal.");
  } finally {
    setLoading(false);
  }
});

compareButton?.addEventListener("click", async () => {
  if (!selectedBlob) {
    showError("Pilih atau ambil gambar terlebih dahulu.");
    return;
  }

  setComparisonLoading(true);
  hideError();
  try {
    const comparison = await compareModes();
    const { gemma_only: gemmaOnly, gemma_depth: gemmaDepth, iot_assisted: iotAssisted } = comparison.modes;
    renderResult(iotAssisted.success ? iotAssisted : gemmaDepth);
    renderModeComparison(gemmaOnly, gemmaDepth, iotAssisted);
  } catch (error) {
    comparisonStatus.textContent = "Gagal";
    showError(error.message || "Perbandingan mode gagal.");
  } finally {
    setComparisonLoading(false);
  }
});

async function openCamera(facingMode) {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: { ideal: facingMode } },
    audio: false,
  });
  cameraPreview.srcObject = cameraStream;
  const actualFacingMode = cameraStream.getVideoTracks()[0]?.getSettings().facingMode;
  cameraFacingMode = actualFacingMode || facingMode;
  cameraEmptyState.classList.add("hidden");
  cameraPreview.classList.remove("hidden");
  cameraActions.classList.remove("hidden");
  captureImageButton.disabled = false;
  switchCameraButton.disabled = false;
  const usesRearCamera = cameraFacingMode === "environment";
  switchCameraButton.textContent = usesRearCamera ? "Ganti ke kamera depan" : "Ganti ke kamera belakang";
  switchCameraButton.setAttribute("aria-label", switchCameraButton.textContent);
}

switchCameraButton?.addEventListener("click", async () => {
  const previousFacingMode = cameraFacingMode;
  const nextFacingMode = previousFacingMode === "environment" ? "user" : "environment";
  switchCameraButton.disabled = true;
  captureImageButton.disabled = true;
  try {
    await openCamera(nextFacingMode);
    hideError();
  } catch (_error) {
    try {
      await openCamera(previousFacingMode);
    } catch (_restoreError) {
      stopCameraStream();
    }
    showCameraError("Kamera yang dipilih tidak tersedia pada perangkat ini.");
  }
});

captureImageButton?.addEventListener("click", () => {
  if (!cameraPreview.videoWidth || !cameraPreview.videoHeight) {
    showError("Pratinjau kamera belum siap.");
    return;
  }

  const captureTimeMs = Date.now();
  const captureId = `cap_${captureTimeMs}_${crypto.randomUUID?.() || Math.random().toString(16).slice(2)}`;
  selectedCaptureMeta = {
    capture_id: captureId,
    capture_time_ms: captureTimeMs,
    camera_facing_mode: cameraFacingMode,
  };
  captureCanvas.width = cameraPreview.videoWidth;
  captureCanvas.height = cameraPreview.videoHeight;
  const context = captureCanvas.getContext("2d");
  context.drawImage(cameraPreview, 0, 0, captureCanvas.width, captureCanvas.height);
  captureCanvas.toBlob((blob) => {
    if (!blob) {
      showError("Pengambilan gambar gagal.");
      return;
    }

    selectedBlob = new File([blob], "gambar-kamera.jpg", { type: "image/jpeg" });
    showPreview(selectedBlob);
    setActionAvailability(true);
    hideError();
  }, "image/jpeg", 0.9);
});

const helpPopover = createHelpPopover();
let activeHelpButton = null;
let helpCloseTimer = null;

document.querySelectorAll(".help-dot").forEach((button) => {
  button.addEventListener("mouseenter", () => {
    showHelpPopover(button, "hover");
  });
  button.addEventListener("mouseleave", scheduleHelpClose);
  button.addEventListener("focus", () => {
    showHelpPopover(button, "focus");
  });
  button.addEventListener("blur", scheduleHelpClose);
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (
      activeHelpButton === button &&
      button.getAttribute("data-help-opened-by") === "click" &&
      !helpPopover.classList.contains("hidden")
    ) {
      hideHelpPopover();
      return;
    }

    showHelpPopover(button, "click");
  });
});

helpPopover.addEventListener("mouseenter", cancelHelpClose);
helpPopover.addEventListener("mouseleave", scheduleHelpClose);

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }

  if (helpPopover.contains(target) || activeHelpButton?.contains(target)) {
    return;
  }

  hideHelpPopover();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    hideHelpPopover();
  }
});

window.addEventListener("resize", () => {
  if (activeHelpButton && !helpPopover.classList.contains("hidden")) {
    positionHelpPopover(activeHelpButton);
  }
});

function createHelpPopover() {
  const popover = document.createElement("aside");
  popover.id = "help-popover";
  popover.className = "help-popover hidden";
  popover.setAttribute("role", "tooltip");
  popover.setAttribute("aria-hidden", "true");
  popover.innerHTML = `
    <strong id="help-popover-title"></strong>
    <p id="help-popover-text"></p>
  `;
  document.body.appendChild(popover);
  return popover;
}

function showHelpPopover(button, source) {
  cancelHelpClose();

  const title = button.getAttribute("data-help-title") || button.getAttribute("aria-label") || "Detail";
  const text = button.getAttribute("data-help-text") || "Informasi tambahan untuk membaca hasil eksperimen.";
  const titleOutput = helpPopover.querySelector("#help-popover-title");
  const textOutput = helpPopover.querySelector("#help-popover-text");

  titleOutput.textContent = title;
  textOutput.textContent = text;
  activeHelpButton?.setAttribute("aria-expanded", "false");
  activeHelpButton?.removeAttribute("aria-describedby");
  activeHelpButton?.removeAttribute("data-help-opened-by");
  activeHelpButton = button;
  activeHelpButton.setAttribute("aria-expanded", "true");
  activeHelpButton.setAttribute("aria-describedby", "help-popover");
  activeHelpButton.setAttribute("data-help-opened-by", source);
  helpPopover.classList.remove("hidden");
  helpPopover.setAttribute("aria-hidden", "false");
  positionHelpPopover(button);
}

function positionHelpPopover(button) {
  const rect = button.getBoundingClientRect();
  const popoverRect = helpPopover.getBoundingClientRect();
  const gap = 10;
  const margin = 16;
  const topCandidate = rect.bottom + gap;
  const top = topCandidate + popoverRect.height > window.innerHeight - margin
    ? Math.max(margin, rect.top - popoverRect.height - gap)
    : topCandidate;
  const left = Math.min(
    window.innerWidth - popoverRect.width - margin,
    Math.max(margin, rect.right - popoverRect.width),
  );

  helpPopover.style.top = `${Math.round(top)}px`;
  helpPopover.style.left = `${Math.round(left)}px`;
}

function scheduleHelpClose() {
  cancelHelpClose();
  helpCloseTimer = window.setTimeout(hideHelpPopover, 120);
}

function cancelHelpClose() {
  if (helpCloseTimer) {
    window.clearTimeout(helpCloseTimer);
    helpCloseTimer = null;
  }
}

function renderFinalDescription(data, finalSections) {
  const segments = Array.isArray(data.display?.provenance_segments)
    ? data.display.provenance_segments
    : [];
  finalDescription.innerHTML = segments.length > 0
    ? buildProvenanceDescription(segments)
    : `<p>${escapeHtml(buildFinalSummary(data, finalSections))}</p>`;

  finalSystemNote.textContent = finalSections.system_note
    || data.display?.system_note
    || "Hasil eksperimen dari mode inferensi yang dipilih.";
}

function buildProvenanceDescription(segments) {
  const visibleSegments = segments
    .filter((segment) => segment?.text)
    .map((segment) => `
      <span class="provenance-segment source-${escapeHtml(segment.source || "template")}">${escapeHtml(segment.text)}</span>
    `)
    .join(" ");

  const legend = Object.entries(PROVENANCE_LABELS)
    .map(([source, label]) => `
      <span class="legend-item">
        <i class="source-${escapeHtml(source)}" aria-hidden="true"></i>
        ${escapeHtml(label)}
      </span>
    `)
    .join("");

  return `
    <p class="provenance-text">${visibleSegments}</p>
    <div class="provenance-legend" aria-label="Legenda sumber informasi deskripsi">
      ${legend}
    </div>
  `;
}

function buildFinalSummary(data, finalSections) {
  const visual = finalSections.visual_description || data.gemma_description || data.description_gemma || "";
  const depth = data.depth_summary || {};
  const areaLabel = formatArea(depth.nearest_region);
  const openArea = finalSections.open_area || "";
  const distanceCategory = formatCategory(depth.distance_category);
  const summary = [];

  if (visual) {
    summary.push(limitSentences(visual, 1));
  }

  if (areaLabel !== "tidak diketahui" && !isEmptyDisplayValue(distanceCategory)) {
    summary.push(`Estimasi kedalaman relatif membaca area ${areaLabel} sebagai area terdekat dengan kategori ${distanceCategory}.`);
  } else if (finalSections.depth_insight) {
    summary.push(limitSentences(finalSections.depth_insight, 1));
  }

  if (openArea && !openArea.includes("belum dapat ditentukan")) {
    summary.push(openArea);
  }

  return summary.slice(0, 3).join(" ") || data.final_description || "-";
}

function limitSentences(text, maxSentences) {
  const parts = String(text)
    .replaceAll("?", ".")
    .replaceAll("!", ".")
    .split(".")
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length === 0) {
    return String(text || "").trim();
  }
  return `${parts.slice(0, maxSentences).join(". ")}.`;
}

function hideHelpPopover() {
  cancelHelpClose();
  activeHelpButton?.setAttribute("aria-expanded", "false");
  activeHelpButton?.removeAttribute("aria-describedby");
  activeHelpButton?.removeAttribute("data-help-opened-by");
  activeHelpButton = null;
  helpPopover.classList.add("hidden");
  helpPopover.setAttribute("aria-hidden", "true");
}

async function refreshHealth() {
  if (!systemStatusSummary) {
    return;
  }

  try {
    const response = await fetch("/health");
    const data = await response.json();
    renderSystemStatus({
      backend: data.backend,
      gemma: data.gemma,
      depth: data.depth_model,
    });
  } catch (error) {
    renderSystemStatus({
      backend: "tidak_tersedia",
      gemma: "tidak_diketahui",
      depth: "tidak_diketahui",
    });
  }
}

function renderSystemStatus(status) {
  const backendReady = isReadyStatus(status.backend);
  const gemmaReady = isReadyStatus(status.gemma);
  const depthReady = isReadyStatus(status.depth);
  const allReady = backendReady && gemmaReady && depthReady;

  systemStatusSummary.textContent = allReady ? "Semua sistem aktif" : "Periksa sistem";
  systemStatusCaption.textContent = allReady ? "SEMUA SISTEM AKTIF" : "PERIKSA SISTEM";
  setStatusValue(backendStatusOutput, status.backend, backendReady);
  setStatusValue(gemmaStatusOutput, status.gemma, gemmaReady);
  setStatusValue(depthRuntimeStatusOutput, status.depth, depthReady);
  systemStatusToggle?.classList.toggle("is-warning", !allReady);
  systemStatusPanel?.classList.toggle("is-warning", !allReady);
}

function setStatusValue(element, value, isReady) {
  if (!element) {
    return;
  }

  element.textContent = isReady ? "SIAP" : formatSystemStatus(value);
  element.parentElement?.classList.toggle("is-warning", !isReady);
}

function isReadyStatus(value) {
  const normalized = String(value || "").toLowerCase();
  return ["ok", "ready", "loaded", "online", "true", "available"].some((token) => normalized.includes(token));
}

function formatSystemStatus(value) {
  if (value === undefined || value === null || value === "") {
    return "TIDAK DIKETAHUI";
  }

  const normalized = String(value).toLowerCase();
  const labels = {
    unavailable: "TIDAK TERSEDIA",
    tidak_tersedia: "TIDAK TERSEDIA",
    unknown: "TIDAK DIKETAHUI",
    tidak_diketahui: "TIDAK DIKETAHUI",
    mock: "SIMULASI",
    error: "GALAT",
    disabled: "NONAKTIF",
  };

  return labels[normalized] || String(value).replaceAll("_", " ").toUpperCase();
}

async function analyzeMode(mode, saveResult) {
  if (!captureClock) {
    await syncCaptureClock();
  }
  const formData = new FormData();
  formData.append("image", selectedBlob, selectedBlob.name || "gambar-kamera.jpg");
  formData.append("mode", mode);
  formData.append("save_result", saveResult ? "true" : "false");
  if (selectedCaptureMeta) {
    formData.append("capture_id", selectedCaptureMeta.capture_id);
    formData.append("capture_time_ms", String(selectedCaptureMeta.capture_time_ms));
    formData.append("camera_facing_mode", selectedCaptureMeta.camera_facing_mode);
  }
  if (captureClock) {
    formData.append("clock_offset_ms", String(captureClock.offset_ms));
    formData.append("clock_rtt_ms", String(captureClock.rtt_ms));
  }

  if (!window.AnalysisJobClient) {
    throw new Error("Klien antrean analisis tidak tersedia.");
  }
  return window.AnalysisJobClient.analyze(formData);
}

async function compareModes() {
  if (!captureClock) {
    await syncCaptureClock();
  }
  const formData = new FormData();
  formData.append("image", selectedBlob, selectedBlob.name || "gambar-kamera.jpg");
  if (selectedCaptureMeta) {
    formData.append("capture_id", selectedCaptureMeta.capture_id);
    formData.append("capture_time_ms", String(selectedCaptureMeta.capture_time_ms));
    formData.append("camera_facing_mode", selectedCaptureMeta.camera_facing_mode);
  }
  if (captureClock) {
    formData.append("clock_offset_ms", String(captureClock.offset_ms));
    formData.append("clock_rtt_ms", String(captureClock.rtt_ms));
  }
  return window.AnalysisJobClient.compare(formData);
}

async function syncCaptureClock() {
  const samples = [];
  for (let index = 0; index < 3; index += 1) {
    const startedAt = performance.now();
    const clientBeforeMs = Date.now();
    const response = await fetch(`/time-sync?sample=${index}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Sinkronisasi waktu backend gagal.");
    }
    const payload = await response.json();
    const clientAfterMs = Date.now();
    const rttMs = Math.max(0, Math.round(performance.now() - startedAt));
    const midpointMs = (clientBeforeMs + clientAfterMs) / 2;
    samples.push({ offset_ms: Math.round(payload.server_time_ms - midpointMs), rtt_ms: rttMs });
  }
  samples.sort((left, right) => left.rtt_ms - right.rtt_ms);
  captureClock = samples[0] || null;
  return captureClock;
}

function setSelectedImage(file) {
  if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
    showError("Format file belum didukung. Gunakan JPG, PNG, atau WebP.");
    return;
  }

  selectedBlob = file;
  selectedCaptureMeta = null;
  if (activeSource === "upload") {
    stopCameraStream();
  }
  showPreview(file);
  setActionAvailability(true);
  hideError();
}

function showPreview(file) {
  const previewUrl = URL.createObjectURL(file);
  imagePreview.src = previewUrl;
  imagePreview.onload = () => URL.revokeObjectURL(previewUrl);
  selectedFileName.textContent = file.name || "Gambar hasil kamera";
  uploadLabel.textContent = "Ganti gambar";
  uploadDropzone?.classList.add("has-image");
  selectedPreview.classList.remove("hidden");
}

function clearSelectedImage() {
  selectedBlob = null;
  selectedCaptureMeta = null;
  imageInput.value = "";
  imagePreview.removeAttribute("src");
  selectedFileName.textContent = "Gambar terpilih";
  uploadLabel.textContent = "Unggah gambar dalam ruangan";
  uploadDropzone?.classList.remove("has-image", "is-dragging");
  dragDepth = 0;
  selectedPreview.classList.add("hidden");
  setActionAvailability(false);
}

function renderResult(data) {
  resultShell.classList.remove("hidden");

  const depth = data.depth_summary || {};
  const latency = data.latency || {};
  const nearestRegion = depth.nearest_region || "tidak_diketahui";
  const openArea = data.display?.safe_direction || depth.safe_direction || "tidak_diketahui";
  const distanceCategory = depth.distance_category || "tidak_diketahui";
  const formattedDistanceCategory = formatCategory(distanceCategory);
  const formattedNearestRegion = formatRegion(nearestRegion);
  const latencyStages = getLatencyStageRuns(data.mode);
  const finalSections = data.display?.final_sections || {};

  renderCapturedSensorEvidence(data.sensor_evidence);

  renderFinalDescription(data, finalSections);
  gemmaDescription.textContent = finalSections.visual_description || data.gemma_description || data.description_gemma || "-";
  depthSummary.textContent = JSON.stringify(depth, null, 2);
  modeOutput.textContent = MODE_LABELS[data.mode] || data.mode || "-";
  distanceCategoryOutput.textContent = formattedDistanceCategory;
  nearestRegionOutput.textContent = formattedNearestRegion;
  totalLatencyOutput.textContent = formatMs(latency.total_ms);
  gemmaLatencyOutput.textContent = formatStageMs(latency.gemma_ms, latencyStages.gemma);
  depthLatencyOutput.textContent = formatStageMs(latency.depth_ms, latencyStages.depth);
  fusionLatencyOutput.textContent = formatStageMs(latency.fusion_ms, latencyStages.fusion);
  mainObjectOutput.textContent = formatSummaryValue(data.gemma_structured?.main_object);
  objectPositionOutput.textContent = formatSummaryValue(data.gemma_structured?.object_position);
  sceneTypeOutput.textContent = formatSceneType(data.gemma_structured?.scene_type);
  depthStatusOutput.innerHTML = buildDepthInsightList(depth, finalSections);
  openAreaOutput.textContent = finalSections.open_area || (openArea !== "tidak_diketahui"
    ? `Area relatif lapang: ${formatDirection(openArea)}`
    : "Area relatif lapang tidak tersedia.");
  depthContribution.textContent = buildDepthContribution(data, finalSections);
  latencyOutput.textContent = hasLatencyValue(latency.total_ms)
    ? `Gemma ${formatStageMs(latency.gemma_ms, latencyStages.gemma)}, Kedalaman ${formatStageMs(latency.depth_ms, latencyStages.depth)}, Fusi ${formatStageMs(latency.fusion_ms, latencyStages.fusion)}, Total ${formatMs(latency.total_ms)}`
    : "Output mentah model dan metadata waktu proses disembunyikan secara default agar antarmuka tetap fokus.";
  renderMetricExplanations(data, depth, latency, formattedDistanceCategory, formattedNearestRegion);

  if (data.depth_map_url) {
    depthMapPreview.src = data.depth_map_url;
    depthMapGridWrap?.classList.remove("hidden");
    highlightDepthRegion(nearestRegion);
  } else {
    depthMapPreview.removeAttribute("src");
    depthMapGridWrap?.classList.add("hidden");
    highlightDepthRegion("tidak_diketahui");
  }

  if (data.error) {
    showError(data.error);
  }
}

function highlightDepthRegion(region) {
  if (!depthRegionGrid) {
    return;
  }

  depthRegionGrid.querySelectorAll("[data-region]").forEach((cell) => {
    cell.classList.toggle("is-nearest", cell.getAttribute("data-region") === region);
  });
}

function renderSingleModeComparison(data) {
  if (!comparisonStatus || !comparisonOutput) {
    return;
  }

  comparisonStatus.textContent = "Mode aktif";
  comparisonOutput.innerHTML = `
    <div class="comparison-finding">Mode ${escapeHtml(MODE_LABELS[data.mode] || data.mode || "terpilih")} sudah dianalisis. Jalankan perbandingan backend untuk melihat Gemma Baseline, Gemma + Depth, dan IoT-assisted pada evidence yang sama.</div>
  `;
}

function renderModeComparison(gemmaOnly, gemmaDepth, iotAssisted) {
  comparisonStatus.textContent = "Selesai";
  const addsDepth = gemmaDepth.depth_summary?.nearest_region;
  comparisonOutput.innerHTML = `
    ${buildComparisonTable(gemmaOnly, gemmaDepth, iotAssisted)}
    <div class="comparison-finding">
      ${addsDepth
        ? "Ketiga mode berasal dari satu inferensi Gemma dan satu inferensi depth. Kolom IoT menambahkan referensi sensor frontal hanya saat evidence valid."
        : "Kontribusi kedalaman belum terlihat pada data respons. Periksa JSON mentah dan status waktu proses model."}
    </div>
  `;
}

function buildComparisonTable(gemmaOnly, gemmaDepth, iotAssisted) {
  const depthSummary = gemmaDepth.depth_summary || {};
  const sensor = iotAssisted.sensor_contribution || {};
  const rows = [
    {
      aspect: "Deskripsi visual",
      gemma: summarizeVisual(gemmaOnly),
      gemmaDepth: summarizeVisual(gemmaDepth),
      iot: summarizeVisual(iotAssisted),
      contribution: "Semantik visual berasal dari inferensi Gemma yang sama.",
    },
    {
      aspect: "Area terdekat",
      gemma: depthMetadataUnavailable(),
      gemmaDepth: formatArea(depthSummary.nearest_region),
      iot: formatArea(iotAssisted.depth_summary?.nearest_region),
      contribution: "Berasal dari estimasi kedalaman relatif, bukan identitas objek pasti.",
    },
    {
      aspect: "Referensi sensor frontal",
      gemma: "Tidak digunakan",
      gemmaDepth: "Tidak digunakan",
      iot: sensor.description || `Tidak tersedia: ${sensor.reason_code || "tanpa evidence"}`,
      contribution: "Sensor tidak mengidentifikasi objek dan konflik tidak dirata-ratakan.",
    },
    {
      aspect: "Kategori kedalaman relatif",
      gemma: depthMetadataUnavailable(),
      gemmaDepth: formatCategory(depthSummary.distance_category),
      iot: formatCategory(iotAssisted.depth_summary?.distance_category),
      contribution: "Ditambahkan dari threshold depth yang belum dikalibrasi sebagai meter presisi.",
    },
    {
      aspect: "Latensi",
      gemma: formatMs(gemmaOnly.latency?.total_ms),
      gemmaDepth: formatMs(gemmaDepth.latency?.total_ms),
      iot: formatMs(iotAssisted.latency?.total_ms),
      contribution: buildLatencyDelta(gemmaOnly.latency?.total_ms, iotAssisted.latency?.total_ms),
    },
  ];

  return `
    <div class="comparison-table-wrap">
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Aspek</th>
            <th>Gemma Baseline</th>
            <th>Gemma + Depth</th>
            <th>IoT-assisted</th>
            <th>Kontribusi</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <th scope="row">${escapeHtml(row.aspect)}</th>
              <td data-label="Gemma Baseline">${escapeHtml(row.gemma)}</td>
              <td data-label="Gemma + Depth">${escapeHtml(row.gemmaDepth)}</td>
              <td data-label="IoT-assisted">${escapeHtml(row.iot)}</td>
              <td data-label="Kontribusi">${escapeHtml(row.contribution)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function buildDepthInsightList(depth, finalSections) {
  const rows = [
    ["Area UI", formatArea(depth.nearest_region)],
    ["Region teknis", formatTechnicalRegion(depth.nearest_region)],
    ["Kategori kedalaman relatif", formatCategory(depth.distance_category)],
    ["Interpretasi", summarizeText(finalSections.depth_insight || "Insight kedalaman tidak tersedia.")],
  ];

  return `
    <dl class="depth-facts">
      ${rows.map(([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(value)}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}

function setLoading(isLoading) {
  loadingState.classList.toggle("hidden", !isLoading);
  analyzeButton.disabled = isLoading || !selectedBlob;
  compareButton.disabled = isLoading || !selectedBlob;

  if (isLoading) {
    startLoadingSteps();
    return;
  }

  stopLoadingSteps();
}

function setComparisonLoading(isLoading) {
  comparisonStatus.textContent = isLoading ? "Membandingkan..." : comparisonStatus.textContent;
  compareButton.disabled = isLoading || !selectedBlob;
  analyzeButton.disabled = isLoading || !selectedBlob;
  if (isLoading) {
    comparisonOutput.innerHTML = `
      <div class="comparison-finding">Menjalankan baseline dan depth-only secara berurutan, lalu membentuk late fusion terkontrol pada gambar yang dipilih...</div>
    `;
  }
}

function startLoadingSteps() {
  stopLoadingSteps();
  loadingIndex = 0;
  markLoadingStep();
  loadingTimer = window.setInterval(() => {
    loadingIndex = (loadingIndex + 1) % loadingSteps.length;
    markLoadingStep();
  }, 1050);
}

function stopLoadingSteps() {
  if (loadingTimer) {
    window.clearInterval(loadingTimer);
    loadingTimer = null;
  }
  loadingSteps.forEach((step, index) => {
    step.classList.toggle("is-active", index === 0);
  });
}

function markLoadingStep() {
  loadingSteps.forEach((step, index) => {
    step.classList.toggle("is-active", index === loadingIndex);
  });
}

function setActionAvailability(isAvailable) {
  analyzeButton.disabled = !isAvailable;
  compareButton.disabled = !isAvailable;
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.remove("hidden");
}

function hideError() {
  errorMessage.textContent = "";
  errorMessage.classList.add("hidden");
}

function buildDepthContribution(data, finalSections = {}) {
  const depth = data.depth_summary || {};
  if (!depth.distance_category && !depth.nearest_region) {
    return "Interpretasi kedalaman bersifat kategoris dan eksperimental.";
  }
  return finalSections.potential_obstacle
    || `Observasi berbasis kedalaman: kategori ${formatCategory(depth.distance_category)}, area terdekat ${formatArea(depth.nearest_region)}, dan indikasi area relatif lebih terbuka ${formatDirection(depth.safe_direction)}.`;
}

function formatMs(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  const numericValue = Number(value);
  if (Number.isFinite(numericValue) && numericValue === 0) {
    return "<1 ms";
  }
  return `${value} ms`;
}

function formatStageMs(value, didRun) {
  if (!didRun) {
    return "Tidak dijalankan";
  }
  return formatMs(value);
}

function hasLatencyValue(value) {
  return value !== undefined && value !== null && value !== "";
}

function getLatencyStageRuns(mode) {
  return {
    gemma: mode === "gemma_only" || mode === "gemma_depth",
    depth: mode === "depth_only" || mode === "gemma_depth",
    fusion: mode === "gemma_only" || mode === "depth_only" || mode === "gemma_depth",
  };
}

function formatRegion(value) {
  return REGION_LABELS[value] || value || "-";
}

function formatArea(value) {
  const label = formatRegion(value);
  return label === "-" ? "tidak diketahui" : label;
}

function formatTechnicalRegion(value) {
  return value || "tidak_diketahui";
}

function formatCategory(value) {
  return value ? value.replaceAll("_", " ") : "-";
}

function formatFusionStrategy(value) {
  const labels = {
    late_rule_based_fusion_controlled: "Late fusion kontrol",
    late_rule_based_fusion: "Late rule-based fusion",
    evidence_constrained_regional_late_fusion: "Fusi regional berbatas bukti",
    legacy_verbose_late_fusion: "Late fusion verbose (kontrol lama)",
    depth_only_summary: "Depth summary",
    gemma_visual_spatial_baseline: "Gemma visual-spatial baseline",
    gemma_only: "Gemma-only",
  };
  return labels[value] || value || "-";
}

function isEmptyDisplayValue(value) {
  return !value || value === "-" || value === "tidak diketahui" || value === "tidak_diketahui";
}

function summarizeVisual(data) {
  const sections = data.display?.final_sections || {};
  const visual = sections.visual_description || data.gemma_description || data.description_gemma || data.final_description;
  return summarizeText(visual);
}

function summarizeText(value) {
  if (!value) {
    return "Tidak tersedia";
  }
  return limitSentences(value, 1);
}

function depthMetadataUnavailable() {
  return "Tidak diekstrak sebagai metadata depth.";
}

function sumLatency(firstValue, secondValue) {
  const first = Number(firstValue);
  const second = Number(secondValue);
  if (!Number.isFinite(first) || !Number.isFinite(second)) {
    return undefined;
  }
  return first + second;
}

function buildLatencyDelta(gemmaOnlyValue, gemmaDepthValue) {
  const gemmaOnly = Number(gemmaOnlyValue);
  const gemmaDepth = Number(gemmaDepthValue);
  if (!Number.isFinite(gemmaOnly) || !Number.isFinite(gemmaDepth)) {
    return "Selisih belum tersedia.";
  }
  const delta = gemmaDepth - gemmaOnly;
  if (delta === 0) {
    return "Latensi sama pada sampel ini.";
  }
  const direction = delta > 0 ? "lebih lambat" : "lebih cepat";
  return `${Math.abs(delta)} ms ${direction} pada sampel ini.`;
}

function formatSummaryValue(value) {
  return value ? value.replaceAll("_", " ") : "-";
}

function formatSceneType(value) {
  return SCENE_LABELS[value] || formatSummaryValue(value);
}

function formatDirection(value) {
  return REGION_LABELS[value] || value || "-";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
