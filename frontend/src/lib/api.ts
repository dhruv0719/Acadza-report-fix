import {
  FacultyReviewRecord,
  FacultyReviewRequest,
  InvestigationCheckpoint,
  NormalizedQuestion,
  QualityFinding,
  ReportGroup,
  ReportRecord,
  ResultItem,
  TaxonomyData,
  TelemetryData,
  UnreportedQuestionAudit,
} from "@/types";

/**
 * Normalizes an API base URL so that it always ends with `/api` exactly once.
 * Handles:
 * - "https://acadza-report-fix.onrender.com/api"  -> "https://acadza-report-fix.onrender.com/api"
 * - "https://acadza-report-fix.onrender.com"      -> "https://acadza-report-fix.onrender.com/api"
 * - "https://acadza-report-fix.onrender.com/"     -> "https://acadza-report-fix.onrender.com/api"
 * - "https://acadza-report-fix.onrender.com/api/" -> "https://acadza-report-fix.onrender.com/api"
 * - "http://127.0.0.1:8000"                      -> "http://127.0.0.1:8000/api"
 * - "http://127.0.0.1:8000/api"                  -> "http://127.0.0.1:8000/api"
 * - "/api"                                       -> "/api"
 */
export function normalizeApiBase(rawUrl?: string): string {
  const url = (rawUrl || "").trim().replace(/\/+$/, "");

  if (!url) {
    // In browser or local dev, fallback to local backend if on localhost
    if (typeof window !== "undefined") {
      const isLocal =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1";
      if (isLocal) {
        return "http://127.0.0.1:8000/api";
      }
      return "https://acadza-report-fix.onrender.com/api";
    }
    return process.env.NODE_ENV === "production"
      ? "https://acadza-report-fix.onrender.com/api"
      : "http://127.0.0.1:8000/api";
  }

  // If already ends with /api, return as is
  if (url.endsWith("/api")) {
    return url;
  }

  // Otherwise append /api exactly once
  return `${url}/api`;
}

/**
 * Returns the active API base URL.
 * Prioritizes NEXT_PUBLIC_API_URL environment variable.
 */
export function getApiBase(customBase?: string): string {
  if (customBase) {
    return normalizeApiBase(customBase);
  }
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  return normalizeApiBase(envUrl);
}

/**
 * Constructs a fully qualified or relative API endpoint URL.
 * Guarantees:
 * 1. Base URL has `/api` prefix exactly once.
 * 2. Endpoint does not duplicate `/api` if passed with or without it.
 * 3. Correct query parameter serialization.
 */
export function buildUrl(
  endpoint: string,
  params?: Record<string, string | boolean | number | undefined>,
  customBase?: string
): string {
  const base = getApiBase(customBase);

  // Normalize endpoint: strip leading slash and redundant "api/" prefix if caller provided it
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

async function handleResponse<T>(res: Response, endpointUrl: string, method: string = "GET"): Promise<T> {
  if (!res.ok) {
    let errorDetail = "";
    try {
      const errBody = await res.json();
      errorDetail = errBody.detail || errBody.message || JSON.stringify(errBody);
    } catch {
      errorDetail = await res.text().catch(() => "");
    }
    throw new Error(
      `[API Error ${res.status}] ${method} ${endpointUrl}: ${errorDetail || res.statusText || "Request failed"}`
    );
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(baseUrl?: string): Promise<{
  status: string;
  questions_count: number;
  reports_count: number;
  results_count: number;
  verdicts_count: number;
  repairs_count: number;
}> {
  const url = buildUrl("/health", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchTaxonomy(baseUrl?: string): Promise<TaxonomyData> {
  const url = buildUrl("/taxonomy", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchQuestions(
  params?: {
    question_type?: string;
    reported_only?: boolean;
  },
  baseUrl?: string
): Promise<NormalizedQuestion[]> {
  const url = buildUrl("/questions", params, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchQuestion(id: string, baseUrl?: string): Promise<NormalizedQuestion> {
  const url = buildUrl(`/questions/${id}`, undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchReports(
  params?: {
    question_id?: string;
    source?: string;
  },
  baseUrl?: string
): Promise<ReportRecord[]> {
  const url = buildUrl("/reports", params, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchReport(reportId: string, baseUrl?: string): Promise<ReportRecord> {
  const url = buildUrl(`/reports/${reportId}`, undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchGroupedReports(baseUrl?: string): Promise<Record<string, ReportGroup>> {
  const url = buildUrl("/reports/grouped", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchResults(
  params?: {
    route?: string;
    verdict?: string;
    question_id?: string;
  },
  baseUrl?: string
): Promise<ResultItem[]> {
  const url = buildUrl("/results", params, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchResult(reportId: string, baseUrl?: string): Promise<ResultItem> {
  const url = buildUrl(`/results/${reportId}`, undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchQualityFindings(baseUrl?: string): Promise<QualityFinding[]> {
  const url = buildUrl("/quality-findings", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchUnreportedAudit(baseUrl?: string): Promise<UnreportedQuestionAudit[]> {
  const url = buildUrl("/unreported-audit", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchTelemetry(baseUrl?: string): Promise<TelemetryData> {
  const url = buildUrl("/telemetry", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchCheckpoints(baseUrl?: string): Promise<Record<string, InvestigationCheckpoint>> {
  const url = buildUrl("/checkpoints", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchQuestionCheckpoint(
  questionId: string,
  baseUrl?: string
): Promise<InvestigationCheckpoint> {
  const url = buildUrl(`/checkpoints/${questionId}`, undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function fetchFacultyReviews(baseUrl?: string): Promise<Record<string, FacultyReviewRecord>> {
  const url = buildUrl("/faculty-reviews", undefined, baseUrl);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, url, "GET");
}

export async function submitFacultyReview(
  reportId: string,
  review: FacultyReviewRequest,
  baseUrl?: string
): Promise<FacultyReviewRecord> {
  const url = buildUrl(`/review/${reportId}`, undefined, baseUrl);
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(review),
    cache: "no-store",
  });
  return handleResponse(res, url, "POST");
}
