export type QuestionType = "scq" | "mcq" | "integerQuestion";

export type ReportSource = "android" | "ios" | "web";

export type TriageRoute = "auto_apply" | "faculty_review" | "no_change";

export type NavTab = "triage" | "live_groq" | "quality_findings" | "unreported" | "telemetry";

export interface ErrorHistoryEntry {
  actor: string;
  at: string;
  note: string;
  type: string;
}

export interface ParsedOption {
  key: string;
  html: string;
  text: string;
  is_blank?: boolean;
  has_mathml?: boolean;
}

export interface NormalizedQuestion {
  id: string;
  qid?: string | null;
  question_type: QuestionType;
  subject: string;
  chapter: string;
  concept?: string | null;
  sub_concept?: string | null;
  level?: string | number | null;
  updated_at?: string | null;
  error_flag: number;
  error_history: ErrorHistoryEntry[];
  raw_question_html: string;
  raw_solution_html: string;
  stem_html: string;
  stem_text: string;
  solution_text: string;
  options: ParsedOption[];
  raw_answer: any;
  normalized_answer: string | string[];
  answer_anomalies: string[];
  parser_warnings: string[];
  ques_images: any[];
  solution_images: any[];
  has_mathml: boolean;
  has_figure_reference: boolean;
  report_ids: string[];
}

export interface ReportRecord {
  reportId: string;
  questionId: string;
  studentId: string;
  source: ReportSource;
  reportedAt: string;
  comment: string;
}

export interface ReportGroup {
  questionId: string;
  report_count: number;
  reports: ReportRecord[];
  sources: string[];
  comments: string[];
}

export interface RepairDefinition {
  fields: string[];
  auto: boolean;
  label: string;
}

export interface TaxonomyData {
  _about?: string;
  verdicts: Record<string, string>;
  repairs: Record<string, RepairDefinition>;
}

export interface ProposedEdit {
  field: string;
  find?: string | null;
  replace: any;
}

export interface ResultItem {
  reportId: string;
  questionId: string;
  verdict: string;
  repair?: string | null;
  edit?: ProposedEdit | null;
  route: TriageRoute;
  confidence: number;
  evidence: string;
  student_reply: string;
}

export interface QualityFinding {
  question_id: string;
  field: string;
  issue_type: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  independent_of_reports: boolean;
}

export interface UnreportedFinding {
  field: string;
  issue_type: string;
  description: string;
  severity: string;
  is_genuine_defect: boolean;
}

export interface UnreportedQuestionAudit {
  question_id: string;
  subject: string;
  chapter: string;
  question_type: QuestionType;
  stem_text: string;
  stored_answer: any;
  solution_text: string;
  options: any[];
  has_figures: boolean;
  scientific_status: "sound" | "defective";
  findings: UnreportedFinding[];
  scientific_derivation: string;
}

export interface TelemetrySummary {
  total_calls: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_reasoning_tokens: number;
  total_tokens: number;
  total_latency_seconds: number;
  average_latency_ms: number;
  primary_model: string;
  provider: string;
}

export interface TelemetryLog {
  timestamp: string;
  model: string;
  stage: string;
  question_id: string;
  prompt_tokens: number;
  completion_tokens: number;
  reasoning_tokens: number;
  total_tokens: number;
  latency_ms: number;
  status_code: number;
  request_id?: string;
}

export interface TelemetryData {
  summary: TelemetrySummary;
  logs: TelemetryLog[];
}

export interface InvestigationCheckpoint {
  question_id: string;
  blind_solve?: {
    derived_answer: any;
    is_solvable: boolean;
    confidence: number;
    step_by_step_reasoning: string;
    detected_question_defects?: string[];
    is_sound?: boolean;
    unsound_reason?: string;
  };
  answer_verification?: {
    stored_answer_matches: boolean;
    verification_status: "passed" | "failed" | "inconclusive" | "not_required";
    solution_is_consistent: boolean;
    solution_defects: string[];
    quality_findings?: QualityFinding[];
    deterministic_proof?: string;
  };
  report_assessments?: Array<{
    reportId: string;
    verdict: string;
    repair?: string | null;
    edit?: ProposedEdit | null;
    final_route: TriageRoute;
    confidence: number;
    evidence: string;
    student_reply: string;
    is_prompt_injection?: boolean;
    verification_status?: string;
  }>;
}

export interface FacultyReviewRequest {
  action: "approve" | "reject" | "modify";
  reviewer_notes?: string;
  modified_edit?: ProposedEdit;
  custom_reply?: string;
  reviewer_name?: string;
}

export interface FacultyReviewRecord {
  report_id: string;
  action: string;
  reviewer_name: string;
  reviewed_at: string;
  reviewer_notes?: string;
  modified_edit?: ProposedEdit;
  custom_reply?: string;
  status: "approved" | "rejected" | "modified";
}
