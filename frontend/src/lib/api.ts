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

const DEFAULT_API_BASE = "http://127.0.0.1:8000/api";

function getApiBase(): string {
  const url = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE;
  return url.replace(/\/+$/, "");
}

function buildUrl(endpoint: string, params?: Record<string, string | boolean | number | undefined>): string {
  const base = getApiBase();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const fullPath = `${base}${cleanEndpoint}`;

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

async function handleResponse<T>(res: Response, context: string): Promise<T> {
  if (!res.ok) {
    let errorDetail = "";
    try {
      const errBody = await res.json();
      errorDetail = errBody.detail || errBody.message || JSON.stringify(errBody);
    } catch {
      errorDetail = await res.text().catch(() => "");
    }
    throw new Error(
      `[API Error] ${context} failed (${res.status} ${res.statusText}): ${errorDetail || "Unknown error"}`
    );
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{
  status: string;
  questions_count: number;
  reports_count: number;
  results_count: number;
  verdicts_count: number;
  repairs_count: number;
}> {
  const url = buildUrl("/health");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /health");
}

export async function fetchTaxonomy(): Promise<TaxonomyData> {
  const url = buildUrl("/taxonomy");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /taxonomy");
}

export async function fetchQuestions(params?: {
  question_type?: string;
  reported_only?: boolean;
}): Promise<NormalizedQuestion[]> {
  const url = buildUrl("/questions", params);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /questions");
}

export async function fetchQuestion(id: string): Promise<NormalizedQuestion> {
  const url = buildUrl(`/questions/${id}`);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, `GET /questions/${id}`);
}

export async function fetchReports(params?: {
  question_id?: string;
  source?: string;
}): Promise<ReportRecord[]> {
  const url = buildUrl("/reports", params);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /reports");
}

export async function fetchReport(reportId: string): Promise<ReportRecord> {
  const url = buildUrl(`/reports/${reportId}`);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, `GET /reports/${reportId}`);
}

export async function fetchGroupedReports(): Promise<Record<string, ReportGroup>> {
  const url = buildUrl("/reports/grouped");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /reports/grouped");
}

export async function fetchResults(params?: {
  route?: string;
  verdict?: string;
  question_id?: string;
}): Promise<ResultItem[]> {
  const url = buildUrl("/results", params);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /results");
}

export async function fetchResult(reportId: string): Promise<ResultItem> {
  const url = buildUrl(`/results/${reportId}`);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, `GET /results/${reportId}`);
}

export async function fetchQualityFindings(): Promise<QualityFinding[]> {
  const url = buildUrl("/quality-findings");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /quality-findings");
}

export async function fetchUnreportedAudit(): Promise<UnreportedQuestionAudit[]> {
  const url = buildUrl("/unreported-audit");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /unreported-audit");
}

export async function fetchTelemetry(): Promise<TelemetryData> {
  const url = buildUrl("/telemetry");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /telemetry");
}

export async function fetchCheckpoints(): Promise<Record<string, InvestigationCheckpoint>> {
  const url = buildUrl("/checkpoints");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /checkpoints");
}

export async function fetchQuestionCheckpoint(
  questionId: string
): Promise<InvestigationCheckpoint> {
  const url = buildUrl(`/checkpoints/${questionId}`);
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, `GET /checkpoints/${questionId}`);
}

export async function fetchFacultyReviews(): Promise<Record<string, FacultyReviewRecord>> {
  const url = buildUrl("/faculty-reviews");
  const res = await fetch(url, { cache: "no-store" });
  return handleResponse(res, "GET /faculty-reviews");
}

export async function submitFacultyReview(
  reportId: string,
  review: FacultyReviewRequest
): Promise<FacultyReviewRecord> {
  const url = buildUrl(`/review/${reportId}`);
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(review),
    cache: "no-store",
  });
  return handleResponse(res, `POST /review/${reportId}`);
}
