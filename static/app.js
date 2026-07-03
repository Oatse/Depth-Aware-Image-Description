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
  gemma_only: "Gemma",
  depth_only: "Kedalaman Saja",
  gemma_depth: "Gemma + Kedalaman",
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
  const modeReason = buildModeExplanation(data.mode);
  const distanceReason = buildDistanceCategoryExplanation(distanceCategory, nearestRegion);
  const regionReason = buildNearestRegionExplanation(nearestRegion, distanceCategory);
  const latencyReason = buildLatencyExplanation(latency, data.mode);

  modeHelperOutput.textContent = modeReason;
  distanceCategoryHelperOutput.textContent = distanceReason;
  nearestRegionHelperOutput.textContent = regionReason;
  latencyHelperOutput.textContent = latencyReason;

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
    "Region Terdekat",
    `${regionReason} Region ini menunjukkan area grid, bukan identitas objek yang pasti.`,
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

function buildModeExplanation(mode) {
  if (mode === "gemma_depth") {
    return "Mode ini aktif karena sistem menjalankan deskripsi visual Gemma dan ringkasan peta kedalaman, lalu menggabungkannya di tahap fusi.";
  }
  if (mode === "gemma_only") {
    return "Mode ini hanya memakai deskripsi visual Gemma, sehingga kontribusi peta kedalaman tidak dihitung pada hasil akhir.";
  }
  if (mode === "depth_only") {
    return "Mode ini memakai ringkasan peta kedalaman saja untuk membaca struktur jarak relatif tanpa deskripsi visual Gemma.";
  }
  return "Mode inferensi berasal dari pilihan analisis saat gambar diproses.";
}

function buildDistanceCategoryExplanation(distanceCategory, nearestRegion) {
  if (!distanceCategory || distanceCategory === "-" || distanceCategory === "tidak diketahui") {
    return "Kategori belum cukup terbaca karena depth summary tidak menyediakan kategori jarak relatif.";
  }
  return `Nilai ${distanceCategory} muncul karena skor kedalaman pada region ${nearestRegion} masuk ke threshold internal kategori ${distanceCategory}.`;
}

function buildNearestRegionExplanation(nearestRegion, distanceCategory) {
  if (!nearestRegion || nearestRegion === "-" || nearestRegion === "tidak diketahui") {
    return "Region terdekat belum dapat ditentukan dari peta kedalaman.";
  }
  return `Region ${nearestRegion} dipilih karena area grid tersebut memiliki skor kedalaman terdekat; kategorinya terbaca ${distanceCategory}.`;
}

function buildLatencyExplanation(latency, mode) {
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
    const gemmaOnly = await analyzeMode("gemma_only", true);
    const gemmaDepth = await analyzeMode("gemma_depth", true);
    renderResult(gemmaDepth);
    renderModeComparison(gemmaOnly, gemmaDepth);
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
  const rows = [
    ["Deskripsi Visual", finalSections.visual_description],
    ["Insight Kedalaman", finalSections.depth_insight],
    ["Potensi Halangan", finalSections.potential_obstacle],
    ["Area Relatif Lapang", finalSections.open_area],
  ].filter(([, value]) => value);

  if (rows.length === 0) {
    finalDescription.innerHTML = `<p>${escapeHtml(data.final_description || "-")}</p>`;
  } else {
    finalDescription.innerHTML = rows
      .map(([title, value]) => `
        <section class="final-section">
          <strong>${escapeHtml(title)}</strong>
          <p>${escapeHtml(value)}</p>
        </section>
      `)
      .join("");
  }

  finalSystemNote.textContent = finalSections.system_note
    || data.display?.system_note
    || "Hasil eksperimen dari mode inferensi yang dipilih.";
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
  depthStatusOutput.textContent = finalSections.depth_insight || data.display?.depth_status || depth.warning || "Insight kedalaman tidak tersedia untuk percobaan ini.";
  openAreaOutput.textContent = finalSections.open_area || (openArea !== "tidak_diketahui"
    ? `Indikasi area lebih terbuka: ${formatDirection(openArea)}`
    : "Indikasi area lebih terbuka tidak tersedia.");
  depthContribution.textContent = finalSections.potential_obstacle || buildDepthContribution(data);
  latencyOutput.textContent = hasLatencyValue(latency.total_ms)
    ? `Gemma ${formatStageMs(latency.gemma_ms, latencyStages.gemma)}, Kedalaman ${formatStageMs(latency.depth_ms, latencyStages.depth)}, Fusi ${formatStageMs(latency.fusion_ms, latencyStages.fusion)}, Total ${formatMs(latency.total_ms)}`
    : "Output mentah model dan metadata waktu proses disembunyikan secara default agar antarmuka tetap fokus.";
  renderMetricExplanations(data, depth, latency, formattedDistanceCategory, formattedNearestRegion);

  if (data.depth_map_url) {
    depthMapPreview.src = data.depth_map_url;
    depthMapPreview.classList.remove("hidden");
  } else {
    depthMapPreview.removeAttribute("src");
    depthMapPreview.classList.add("hidden");
  }

  if (data.error) {
    showError(data.error);
  }
}

function renderSingleModeComparison(data) {
  if (!comparisonStatus || !comparisonOutput) {
    return;
  }

  comparisonStatus.textContent = "Mode aktif";
  comparisonOutput.innerHTML = `
    <article class="comparison-card">
      <span>${MODE_LABELS[data.mode] || data.mode || "Mode"}</span>
      <p>${escapeHtml(data.final_description || "Hasil belum tersedia.")}</p>
      <strong>${formatMs(data.latency?.total_ms)}</strong>
    </article>
    <p class="comparison-hint">Gunakan mode perbandingan untuk memeriksa kontribusi kedalaman pada gambar yang sama.</p>
  `;
}

function formatComparisonBody(data) {
  const sections = data.display?.final_sections || {};
  const rows = [
    ["Visual", sections.visual_description],
    ["Kedalaman", sections.depth_insight],
    ["Halangan", sections.potential_obstacle],
    ["Area Lapang", sections.open_area],
  ].filter(([, value]) => value);

  if (rows.length === 0) {
    return `<p>${escapeHtml(data.final_description || data.gemma_description || "Tidak tersedia.")}</p>`;
  }

  return `
    <div class="comparison-section-list">
      ${rows.map(([title, value]) => `
        <p><strong>${escapeHtml(title)}: </strong><span>${escapeHtml(value)}</span></p>
      `).join("")}
    </div>
  `;
}

function renderModeComparison(gemmaOnly, gemmaDepth) {
  comparisonStatus.textContent = "Selesai";
  const addsDepth = gemmaDepth.depth_summary?.distance_category || gemmaDepth.depth_summary?.nearest_region;
  comparisonOutput.innerHTML = `
    <article class="comparison-card">
      <span>Gemma</span>
      ${formatComparisonBody(gemmaOnly)}
      <strong>${formatMs(gemmaOnly.latency?.total_ms)}</strong>
    </article>
    <article class="comparison-card highlighted">
      <span>Gemma + Kedalaman</span>
      ${formatComparisonBody(gemmaDepth)}
      <strong>${formatMs(gemmaDepth.latency?.total_ms)}</strong>
    </article>
    <div class="comparison-finding">
      ${addsDepth
        ? "Kontribusi kedalaman terdeteksi: output fusi memuat kategori jarak, region terdekat, atau observasi area yang relatif lebih terbuka."
        : "Kontribusi kedalaman belum terlihat pada data respons. Periksa JSON mentah dan status waktu proses model."}
    </div>
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
      <div class="comparison-finding">Menjalankan Gemma dan Gemma + Kedalaman pada gambar yang dipilih...</div>
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

function buildDepthContribution(data) {
  const depth = data.depth_summary || {};
  if (!depth.distance_category && !depth.nearest_region) {
    return "Interpretasi kedalaman bersifat kategoris dan eksperimental.";
  }
  return `Observasi berbasis kedalaman: kategori ${formatCategory(depth.distance_category)}, region terdekat ${formatRegion(depth.nearest_region)}, dan indikasi area relatif lebih terbuka ${formatDirection(depth.safe_direction)}.`;
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

function formatCategory(value) {
  return value ? value.replaceAll("_", " ") : "-";
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
