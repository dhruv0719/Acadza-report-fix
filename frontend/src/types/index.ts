export type QuestionType = "scq" | "mcq" | "integerQuestion";

export type ReportSource = "android" | "ios" | "web";

export type TriageRoute = "auto_apply" | "faculty_review" | "no_change";

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
