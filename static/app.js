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
const startCameraButton = document.querySelector("#start-camera");
const captureImageButton = document.querySelector("#capture-image");
const cameraPreview = document.querySelector("#camera-preview");
const cameraActions = document.querySelector("#camera-actions");
const captureCanvas = document.querySelector("#capture-canvas");

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
  gemma_depth_prompted: "Depth-to-Spatial Prompting",
};

const PROVENANCE_LABELS = {
  gemma: "Gemma",
  depth: "Depth",
  inference: "Inferensi",
  template: "Template",
  prompted_gemma: "Gemma + Depth Prompt",
  guardrail: "Batasan",
};

const SCENE_LABELS = {
  indoor: "dalam ruangan",
  non_indoor: "luar ruangan",
  tidak_diketahui: "tidak diketahui",
};

let selectedBlob = null;
let cameraStream = null;
let loadingTimer = null;
let loadingIndex = 0;
let dragDepth = 0;

const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

refreshHealth();

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
  if (mode === "gemma_depth_prompted") {
    return "Depth masuk ke prompt Gemma.";
  }
  if (mode === "gemma_depth") {
    return "Visual + depth late fusion.";
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
  if (mode === "gemma_depth_prompted") {
    return "Mode ini menjalankan estimasi kedalaman lebih dulu, lalu metadata region dan kategori kedalaman relatif dimasukkan ke prompt Gemma sebelum deskripsi akhir dibuat.";
  }
  if (mode === "gemma_depth") {
    return "Mode ini menjalankan deskripsi visual Gemma dan ringkasan peta kedalaman secara terpisah, lalu menggabungkannya di tahap late fusion berbasis aturan.";
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
    const data = await analyzeMode(modeSelect?.value || "gemma_depth_prompted", true);
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
    const gemmaOnly = await analyzeMode("gemma_only", false);
    const depthOnly = await analyzeMode("depth_only", false);
    const prompted = await analyzeMode("gemma_depth_prompted", false);
    const gemmaDepth = buildControlledLateFusion(gemmaOnly, depthOnly);
    renderResult(prompted);
    renderModeComparison(gemmaOnly, depthOnly, gemmaDepth, prompted);
  } catch (error) {
    comparisonStatus.textContent = "Gagal";
    showError(error.message || "Perbandingan mode gagal.");
  } finally {
    setComparisonLoading(false);
  }
});

startCameraButton?.addEventListener("click", async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    showError("Peramban tidak mendukung akses kamera.");
    return;
  }

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraPreview.srcObject = cameraStream;
    cameraPreview.classList.remove("hidden");
    cameraActions.classList.remove("hidden");
    captureImageButton.disabled = false;
    hideError();
  } catch (error) {
    showError("Kamera tidak dapat diakses. Unggah gambar tetap dapat digunakan.");
  }
});

captureImageButton?.addEventListener("click", () => {
  if (!cameraPreview.videoWidth || !cameraPreview.videoHeight) {
    showError("Pratinjau kamera belum siap.");
    return;
  }

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
  const formData = new FormData();
  formData.append("image", selectedBlob, selectedBlob.name || "gambar-kamera.jpg");
  formData.append("mode", mode);
  formData.append("save_result", saveResult ? "true" : "false");

  const response = await fetch("/analyze", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.error || "Analisis gagal.");
  }
  return data;
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
    <div class="comparison-finding">Mode ${escapeHtml(MODE_LABELS[data.mode] || data.mode || "terpilih")} sudah dianalisis. Jalankan perbandingan untuk melihat Gemma Baseline, depth-only, late fusion kontrol, dan Depth-to-Spatial Prompting pada gambar yang sama.</div>
  `;
}

function renderModeComparison(gemmaOnly, depthOnly, gemmaDepth, prompted) {
  comparisonStatus.textContent = "Selesai";
  const addsDepth = prompted.depth_summary?.distance_category || gemmaDepth.depth_summary?.nearest_region;
  comparisonOutput.innerHTML = `
    ${buildComparisonTable(gemmaOnly, depthOnly, gemmaDepth, prompted)}
    <div class="comparison-finding">
      ${addsDepth
        ? "Kontribusi depth tersedia sebagai metadata region/kategori pada depth-only, sebagai kalimat tambahan pada late fusion kontrol, dan sebagai konteks prompt pada Depth-to-Spatial Prompting. Kolom Gemma Baseline membaca relasi spasial visual tanpa metadata depth eksplisit."
        : "Kontribusi kedalaman belum terlihat pada data respons. Periksa JSON mentah dan status waktu proses model."}
    </div>
  `;
}

function buildComparisonTable(gemmaOnly, depthOnly, gemmaDepth, prompted) {
  const depthOnlySummary = depthOnly.depth_summary || {};
  const lateDepth = gemmaDepth.depth_summary || {};
  const promptedDepth = prompted.depth_summary || {};
  const lateSections = gemmaDepth.display?.final_sections || {};
  const promptedSections = prompted.display?.final_sections || {};
  const rows = [
    {
      aspect: "Deskripsi visual",
      gemma: summarizeVisual(gemmaOnly),
      depthOnly: "Tidak membaca semantik objek; hanya metadata depth.",
      lateFusion: summarizeVisual(gemmaDepth),
      prompted: summarizeVisual(prompted),
      contribution: "Gemma Baseline memakai gambar saja; prompted mode memberi konteks depth sejak awal.",
    },
    {
      aspect: "Area terdekat",
      gemma: depthMetadataUnavailable(),
      depthOnly: formatArea(depthOnlySummary.nearest_region),
      lateFusion: formatArea(lateDepth.nearest_region),
      prompted: formatArea(promptedDepth.nearest_region),
      contribution: "Berasal dari estimasi kedalaman relatif, bukan identitas objek pasti.",
    },
    {
      aspect: "Strategi fusi",
      gemma: formatFusionStrategy(gemmaOnly.display?.fusion_strategy),
      depthOnly: "Depth summary",
      lateFusion: formatFusionStrategy(gemmaDepth.display?.fusion_strategy),
      prompted: formatFusionStrategy(prompted.display?.fusion_strategy),
      contribution: "Membedakan depth-only, post-processing, dan prompt-level fusion.",
    },
    {
      aspect: "Kategori kedalaman relatif",
      gemma: depthMetadataUnavailable(),
      depthOnly: formatCategory(depthOnlySummary.distance_category),
      lateFusion: formatCategory(lateDepth.distance_category),
      prompted: formatCategory(promptedDepth.distance_category),
      contribution: "Ditambahkan dari threshold depth yang belum dikalibrasi sebagai meter presisi.",
    },
    {
      aspect: "Potensi halangan visual",
      gemma: summarizeText(gemmaOnly.display?.final_sections?.potential_obstacle),
      depthOnly: summarizeText(depthOnly.display?.final_sections?.potential_obstacle),
      lateFusion: summarizeText(lateSections.potential_obstacle),
      prompted: summarizeText(promptedSections.potential_obstacle),
      contribution: "Gemma dapat menyebut hambatan yang tampak; depth memberi indikator region relatif.",
    },
    {
      aspect: "Area relatif lapang",
      gemma: summarizeText(gemmaOnly.display?.final_sections?.open_area),
      depthOnly: summarizeText(depthOnly.display?.final_sections?.open_area),
      lateFusion: summarizeText(lateSections.open_area),
      prompted: summarizeText(promptedSections.open_area),
      contribution: "Area relatif lapang bukan jalur aman.",
    },
    {
      aspect: "Latensi",
      gemma: formatMs(gemmaOnly.latency?.total_ms),
      depthOnly: formatMs(depthOnly.latency?.total_ms),
      lateFusion: formatMs(gemmaDepth.latency?.total_ms),
      prompted: formatMs(prompted.latency?.total_ms),
      contribution: buildLatencyDelta(gemmaOnly.latency?.total_ms, prompted.latency?.total_ms),
    },
  ];

  return `
    <div class="comparison-table-wrap">
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Aspek</th>
            <th>Gemma Baseline</th>
            <th>Depth-only</th>
            <th>Late Fusion</th>
            <th>Prompted</th>
            <th>Kontribusi</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((row) => `
            <tr>
              <th scope="row">${escapeHtml(row.aspect)}</th>
              <td data-label="Gemma Baseline">${escapeHtml(row.gemma)}</td>
              <td data-label="Depth-only">${escapeHtml(row.depthOnly)}</td>
              <td data-label="Late Fusion">${escapeHtml(row.lateFusion)}</td>
              <td data-label="Prompted">${escapeHtml(row.prompted)}</td>
              <td data-label="Kontribusi">${escapeHtml(row.contribution)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function buildControlledLateFusion(gemmaOnly, depthOnly) {
  const depthSections = depthOnly.display?.final_sections || {};
  const latency = {
    gemma_ms: gemmaOnly.latency?.gemma_ms || 0,
    depth_ms: depthOnly.latency?.depth_ms || depthOnly.latency?.total_ms || 0,
    fusion_ms: 0,
    total_ms: sumLatency(gemmaOnly.latency?.total_ms, depthOnly.latency?.total_ms),
  };

  return {
    mode: "gemma_depth",
    gemma_description: gemmaOnly.gemma_description || gemmaOnly.description_gemma || summarizeVisual(gemmaOnly),
    depth_summary: depthOnly.depth_summary || {},
    final_description: `${summarizeVisual(gemmaOnly)} ${summarizeText(depthSections.depth_insight)}`.trim(),
    latency,
    display: {
      fusion_strategy: "late_rule_based_fusion_controlled",
      final_sections: {
        visual_description: summarizeVisual(gemmaOnly),
        depth_insight: depthSections.depth_insight || "Informasi kedalaman tidak tersedia.",
        potential_obstacle: depthSections.potential_obstacle || "Potensi halangan visual belum dapat ditentukan.",
        open_area: depthSections.open_area || "Area relatif lapang belum dapat ditentukan.",
      },
    },
  };
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
      <div class="comparison-finding">Menjalankan baseline, depth-only, late fusion, dan Depth-to-Spatial Prompting secara berurutan pada gambar yang dipilih...</div>
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
    gemma: mode === "gemma_only" || mode === "gemma_depth" || mode === "gemma_depth_prompted",
    depth: mode === "depth_only" || mode === "gemma_depth" || mode === "gemma_depth_prompted",
    fusion: mode === "gemma_only" || mode === "depth_only" || mode === "gemma_depth" || mode === "gemma_depth_prompted",
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
    depth_to_spatial_prompting: "Depth-to-Spatial Prompting",
    late_rule_based_fusion_controlled: "Late fusion kontrol",
    late_rule_based_fusion: "Late rule-based fusion",
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
