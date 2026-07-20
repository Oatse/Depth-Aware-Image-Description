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

  async function compare(formData, options = {}) {
    return submitAndPoll("/analysis-comparisons", formData, options);
  }

  async function submitAndPoll(endpoint, formData, options = {}) {
    const pollIntervalMs = options.pollIntervalMs || 400;
    const timeoutMs = options.timeoutMs || 300000;
    const startedAt = Date.now();
    const acceptedResponse = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });
    const accepted = await parseJson(acceptedResponse);
    if (acceptedResponse.status !== 202) {
      throw new Error(accepted.error || "Pekerjaan analisis gagal dibuat.");
    }

    while (Date.now() - startedAt < timeoutMs) {
      const statusResponse = await fetch(accepted.poll_url);
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

  global.AnalysisJobClient = Object.freeze({ analyze, compare });
})(window);
