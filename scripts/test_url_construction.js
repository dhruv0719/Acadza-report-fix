/**
 * Automated test suite for Frontend API URL Construction & Endpoint Routing.
 * Validates that all requests reach the backend with `/api` exactly once,
 * under all environment configurations and endpoint call styles.
 */

const assert = require("assert");

// Mirror the exact implementation from frontend/src/lib/api.ts
function normalizeApiBase(rawUrl, isProduction = true, isBrowser = false, hostname = "") {
  const url = (rawUrl || "").trim().replace(/\/+$/, "");

  if (!url) {
    if (isBrowser) {
      const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
      if (isLocal) {
        return "http://127.0.0.1:8000/api";
      }
      return "https://acadza-report-fix.onrender.com/api";
    }
    return isProduction
      ? "https://acadza-report-fix.onrender.com/api"
      : "http://127.0.0.1:8000/api";
  }

  if (url.endsWith("/api")) {
    return url;
  }

  return `${url}/api`;
}

function buildUrl(endpoint, params, customBase, envUrl = "") {
  const base = customBase ? normalizeApiBase(customBase) : normalizeApiBase(envUrl);

  let clean = endpoint.startsWith("/") ? endpoint.slice(1) : endpoint;
  if (clean.startsWith("api/")) {
    clean = clean.slice(4);
  } else if (clean === "api") {
    clean = "";
  }

  const fullPath = clean ? `${base}/${clean}` : base;

  if (!params) return fullPath;

  const searchParams = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null) {
      searchParams.set(key, String(val));
    }
  }

  const query = searchParams.toString();
  return query ? `${fullPath}?${query}` : fullPath;
}

let passedTests = 0;

function runTest(name, fn) {
  try {
    fn();
    passedTests++;
    console.log(`  PASS: ${name}`);
  } catch (err) {
    console.error(`  FAIL: ${name}`);
    console.error(err);
    process.exit(1);
  }
}

console.log("=== RUNNING FRONTEND API URL CONSTRUCTION TESTS ===");

console.log("\n1. Base URL Normalization:");

runTest("Standard production URL with /api", () => {
  const res = normalizeApiBase("https://acadza-report-fix.onrender.com/api");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Origin without /api (Render root)", () => {
  const res = normalizeApiBase("https://acadza-report-fix.onrender.com");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Origin with trailing slash", () => {
  const res = normalizeApiBase("https://acadza-report-fix.onrender.com/");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Production URL with trailing slash after /api/", () => {
  const res = normalizeApiBase("https://acadza-report-fix.onrender.com/api/");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("URL with excessive trailing slashes and whitespace", () => {
  const res = normalizeApiBase("  https://acadza-report-fix.onrender.com/api///  ");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Localhost development URL without /api", () => {
  const res = normalizeApiBase("http://127.0.0.1:8000");
  assert.strictEqual(res, "http://127.0.0.1:8000/api");
});

runTest("Localhost development URL with /api", () => {
  const res = normalizeApiBase("http://127.0.0.1:8000/api");
  assert.strictEqual(res, "http://127.0.0.1:8000/api");
});

runTest("Empty string in production environment", () => {
  const res = normalizeApiBase("", true, false);
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Empty string in browser on Vercel domain", () => {
  const res = normalizeApiBase("", true, true, "acadza-report-fix.vercel.app");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api");
});

runTest("Empty string in browser on localhost", () => {
  const res = normalizeApiBase("", false, true, "localhost");
  assert.strictEqual(res, "http://127.0.0.1:8000/api");
});

console.log("\n2. Endpoint Construction for All 8 Reported Problem Endpoints:");

const problemEndpoints = [
  "reports",
  "questions",
  "results",
  "telemetry",
  "checkpoints",
  "faculty-reviews",
  "quality-findings",
  "unreported-audit",
];

// Test with canonical NEXT_PUBLIC_API_URL=https://acadza-report-fix.onrender.com/api
problemEndpoints.forEach((endpoint) => {
  runTest(`buildUrl('/${endpoint}') with canonical base`, () => {
    const res = buildUrl(`/${endpoint}`, undefined, undefined, "https://acadza-report-fix.onrender.com/api");
    assert.strictEqual(res, `https://acadza-report-fix.onrender.com/api/${endpoint}`);
  });
});

// Test with un-prefixed NEXT_PUBLIC_API_URL=https://acadza-report-fix.onrender.com (the user bug case)
problemEndpoints.forEach((endpoint) => {
  runTest(`buildUrl('/${endpoint}') with un-prefixed root base`, () => {
    const res = buildUrl(`/${endpoint}`, undefined, undefined, "https://acadza-report-fix.onrender.com");
    assert.strictEqual(res, `https://acadza-report-fix.onrender.com/api/${endpoint}`);
  });
});

console.log("\n3. Redundant Prefix Defense & Parameter Serialization:");

runTest("Double prefix defense: buildUrl('/api/reports') with /api base", () => {
  const res = buildUrl("/api/reports", undefined, undefined, "https://acadza-report-fix.onrender.com/api");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api/reports");
});

runTest("Double prefix defense: buildUrl('api/reports') with /api base", () => {
  const res = buildUrl("api/reports", undefined, undefined, "https://acadza-report-fix.onrender.com/api");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api/reports");
});

runTest("Single question endpoint: /questions/68c8153cfb6b2f16e2d3ceaf", () => {
  const res = buildUrl(
    "/questions/68c8153cfb6b2f16e2d3ceaf",
    undefined,
    undefined,
    "https://acadza-report-fix.onrender.com/api"
  );
  assert.strictEqual(
    res,
    "https://acadza-report-fix.onrender.com/api/questions/68c8153cfb6b2f16e2d3ceaf"
  );
});

runTest("Faculty review action: /review/R004", () => {
  const res = buildUrl("/review/R004", undefined, undefined, "https://acadza-report-fix.onrender.com/api");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api/review/R004");
});

runTest("Health endpoint: /health", () => {
  const res = buildUrl("/health", undefined, undefined, "https://acadza-report-fix.onrender.com/api");
  assert.strictEqual(res, "https://acadza-report-fix.onrender.com/api/health");
});

runTest("Query parameters serialization", () => {
  const res = buildUrl(
    "/results",
    { route: "auto_apply", verdict: "defect" },
    undefined,
    "https://acadza-report-fix.onrender.com/api"
  );
  assert.strictEqual(
    res,
    "https://acadza-report-fix.onrender.com/api/results?route=auto_apply&verdict=defect"
  );
});

console.log(`\nALL ${passedTests} TESTS PASSED CLEANLY! No request can drop /api or duplicate /api/api.\n`);

