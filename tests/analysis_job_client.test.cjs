const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "..", "static", "analysis-job-client.js"),
  "utf8",
);

function loadClient(fetchImplementation) {
  const window = { fetch: fetchImplementation, setTimeout };
  const context = vm.createContext({ fetch: fetchImplementation, window });
  vm.runInContext(source, context);
  return window.AnalysisJobClient;
}

function response(status, payload) {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => payload,
  };
}

test("network failure is reported as a backend connection problem", async () => {
  const client = loadClient(async () => {
    throw new TypeError("Failed to fetch");
  });

  await assert.rejects(
    client.analyze({}, { timeoutMs: 50 }),
    /Tidak dapat menghubungi backend/,
  );
});

test("capture saves through the capture endpoint without creating an analysis job", async () => {
  const requests = [];
  const client = loadClient(async (url, options) => {
    requests.push({ url, method: options.method });
    return response(201, {
      capture: { capture_id: "capture-1", status: "captured" },
      capture_count: 1,
    });
  });

  const result = await client.capture({});

  assert.equal(result.capture.status, "captured");
  assert.deepEqual(requests, [{ url: "/captures", method: "POST" }]);
});

test("temporary polling failure does not discard a running analysis", async () => {
  let requestCount = 0;
  const client = loadClient(async () => {
    requestCount += 1;
    if (requestCount === 1) {
      return response(202, { poll_url: "/analysis-jobs/job-1" });
    }
    if (requestCount === 2) {
      throw new TypeError("Failed to fetch");
    }
    return response(200, {
      status: "completed",
      result: { success: true, final_description: "Kursi terlihat di depan meja." },
    });
  });

  const result = await client.analyze({}, { pollIntervalMs: 1, timeoutMs: 100 });

  assert.equal(result.success, true);
  assert.equal(requestCount, 3);
});
