(function attachAnalysisJobClient(global) {
  const TERMINAL_STATES = new Set(["completed", "failed"]);

  function wait(milliseconds) {
    return new Promise((resolve) => global.setTimeout(resolve, milliseconds));
  }

  async function parseJson(response) {
    try {
      return await response.json();
    } catch (_error) {
      return {};
    }
  }

  async function analyze(formData, options = {}) {
    return submitAndPoll("/analysis-jobs", formData, options);
  }

  async function fetchBackend(url, options, attempts = 1, retryDelayMs = 0) {
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      try {
        return await global.fetch(url, options);
      } catch (_error) {
        if (attempt < attempts) {
          await wait(retryDelayMs);
        }
      }
    }
    throw new Error(
      "Tidak dapat menghubungi backend. Pastikan halaman dibuka dari URL server yang aktif dan koneksi Wi-Fi tetap tersambung.",
    );
  }

  async function submitAndPoll(endpoint, formData, options = {}) {
    const pollIntervalMs = options.pollIntervalMs || 400;
    const timeoutMs = options.timeoutMs || 300000;
    const startedAt = Date.now();
    const acceptedResponse = await fetchBackend(endpoint, {
      method: "POST",
      body: formData,
    });
    const accepted = await parseJson(acceptedResponse);
    if (acceptedResponse.status !== 202) {
      throw new Error(accepted.error || "Pekerjaan analisis gagal dibuat.");
    }

    while (Date.now() - startedAt < timeoutMs) {
      const statusResponse = await fetchBackend(accepted.poll_url, undefined, 3, pollIntervalMs);
      const status = await parseJson(statusResponse);
      if (!statusResponse.ok) {
        throw new Error(status.error || "Status analisis tidak dapat dibaca.");
      }
      if (TERMINAL_STATES.has(status.status)) {
        if (status.status === "failed") {
          throw new Error(status.error || "Analisis gagal.");
        }
        return status.result;
      }
      await wait(pollIntervalMs);
    }
    throw new Error("Analisis melewati batas tunggu lima menit.");
  }

  global.AnalysisJobClient = Object.freeze({ analyze });
})(window);
