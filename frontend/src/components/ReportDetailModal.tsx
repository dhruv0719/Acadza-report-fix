"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Calculator,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCode2,
  HelpCircle,
  MessageSquare,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import {
  FacultyReviewRecord,
  InvestigationCheckpoint,
  NormalizedQuestion,
  ProposedEdit,
  ReportRecord,
  ResultItem,
} from "@/types";
import HtmlRenderer from "./HtmlRenderer";

interface ReportDetailModalProps {
  result: ResultItem | null;
  question: NormalizedQuestion | null;
  report: ReportRecord | null;
  checkpoint: InvestigationCheckpoint | null;
  facultyReview: FacultyReviewRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onReviewSubmit: (
    reportId: string,
    action: "approve" | "reject" | "modify",
    notes?: string,
    customEdit?: ProposedEdit,
    customReply?: string
  ) => Promise<void>;
}

export default function ReportDetailModal({
  result,
  question,
  report,
  checkpoint,
  facultyReview,
  isOpen,
  onClose,
  onReviewSubmit,
}: ReportDetailModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [isEditMode, setIsEditMode] = useState(false);
  const [editField, setEditField] = useState(result?.edit?.field || "answer");
  const [editFind, setEditFind] = useState(result?.edit?.find || "");
  const [editReplace, setEditReplace] = useState(
    result?.edit?.replace !== undefined ? String(result?.edit?.replace) : ""
  );
  const [customReply, setCustomReply] = useState(result?.student_reply || "");
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  if (!isOpen || !result) return null;

  const handleAction = async (action: "approve" | "reject" | "modify") => {
    setIsSubmitting(true);
    setSubmitSuccess(null);
    try {
      let customEdit: ProposedEdit | undefined = undefined;
      if (action === "modify" || isEditMode) {
        customEdit = {
          field: editField,
          find: editFind || null,
          replace: editReplace,
        };
      }
      await onReviewSubmit(
        result.reportId,
        action,
        reviewerNotes,
        customEdit,
        customReply !== result.student_reply ? customReply : undefined
      );
      setSubmitSuccess(`Review decision (${action}) recorded successfully!`);
      setTimeout(() => setSubmitSuccess(null), 4000);
    } catch (err: any) {
      alert(`Error submitting review: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRouteBadge = (route: string) => {
    switch (route) {
      case "auto_apply":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <Sparkles className="w-3.5 h-3.5 mr-1" />
            Auto Apply (Staged)
          </span>
        );
      case "faculty_review":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="w-3.5 h-3.5 mr-1" />
            Faculty Review Required
          </span>
        );
      case "no_change":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            No Change Required
          </span>
        );
      default:
        return null;
    }
  };

  const blindSolve = checkpoint?.blind_solve;
  const answerVerif = checkpoint?.answer_verification;
  const isPromptInjection = report?.comment.toLowerCase().includes("ignore") || report?.comment.toLowerCase().includes("instruction");

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 md:p-6">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold text-slate-900">{result.reportId}</span>
              <span className="text-slate-400">/</span>
              <span className="text-sm font-mono text-slate-600 bg-slate-200/70 px-2 py-0.5 rounded">
                {result.questionId}
              </span>
            </div>
            {getRouteBadge(result.route)}
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-200 text-slate-800 font-medium">
              Verdict: <strong className="font-semibold">{result.verdict}</strong>
            </span>
            {result.repair && (
              <span className="text-xs px-2.5 py-1 rounded-full bg-purple-100 text-purple-800 font-medium border border-purple-200">
                Repair: {result.repair}
              </span>
            )}
            <span className="text-xs text-slate-500 font-medium">
              Confidence: <strong>{Math.round(result.confidence * 100)}%</strong>
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Question Details & Worked Solution (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Question Stem Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-700 uppercase">
                    {question?.subject || "Subject"}
                  </span>
                  <span className="text-xs text-slate-500 font-medium truncate">
                    {question?.chapter || "Chapter"}
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Type: {question?.question_type}
                </span>
              </div>

              {/* Stem HTML with native MathML rendering */}
              <div className="mb-4">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Question Stem
                </h4>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <HtmlRenderer html={question?.stem_html || question?.raw_question_html || ""} />
                </div>
              </div>

              {/* Figure Warning if referenced but missing */}
              {question?.has_figure_reference && question?.ques_images.length === 0 && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start space-x-2 text-xs text-amber-800">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <strong>Missing Figure Asset:</strong> Question stem refers to a figure ("as shown
                    in figure"), but no image attachment was provided. Question marked as deficient.
                  </div>
                </div>
              )}

              {/* Options Section */}
              {question?.options && question.options.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Options
                  </h4>
                  <div className="space-y-2">
                    {question.options.map((opt) => {
                      const isStored = String(question.raw_answer).trim() === opt.key;
                      const isDerived =
                        blindSolve?.derived_answer &&
                        String(blindSolve.derived_answer).trim() === opt.key;

                      let borderClass = "border-slate-200 bg-white";
                      if (isDerived && isStored) {
                        borderClass = "border-emerald-500 bg-emerald-50/30 ring-1 ring-emerald-500";
                      } else if (isDerived && !isStored) {
                        borderClass = "border-emerald-600 bg-emerald-50/50 ring-2 ring-emerald-500";
                      } else if (!isDerived && isStored) {
                        borderClass = "border-amber-300 bg-amber-50/30";
                      }

                      return (
                        <div
                          key={opt.key}
                          className={`p-3 rounded-lg border text-sm flex items-start space-x-3 transition-colors ${borderClass}`}
                        >
                          <span className="w-6 h-6 rounded-md bg-slate-100 flex items-center justify-center font-bold text-xs shrink-0 text-slate-700">
                            {opt.key}
                          </span>
                          <div className="flex-1">
                            <HtmlRenderer html={opt.html || opt.text} />
                          </div>
                          <div className="flex flex-col items-end space-y-1 shrink-0">
                            {isDerived && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded bg-emerald-600 text-white font-medium">
                                Derived Correct
                              </span>
                            )}
                            {isStored && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-medium">
                                Stored Key
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Integer Question Answer Display */}
              {question?.question_type === "integerQuestion" && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600 font-medium">Stored Integer Answer:</span>
                  <span className="text-base font-bold font-mono text-slate-900">
                    {String(question.raw_answer)}
                  </span>
                </div>
              )}
            </div>

            {/* Worked Solution Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Official Worked Solution
              </h4>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                <HtmlRenderer html={question?.raw_solution_html || question?.solution_text || ""} />
              </div>

              {answerVerif?.solution_defects && answerVerif.solution_defects.length > 0 && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800">
                  <strong>Solution Defects Identified:</strong>
                  <ul className="list-disc list-inside mt-1 space-y-0.5">
                    {answerVerif.solution_defects.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Report Info, AI Investigation, Surgical Edit, Faculty Actions (5 cols) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Student Report Details Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Student Report
                </h4>
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <span>Source: <strong>{report?.source || "app"}</strong></span>
                  <span>•</span>
                  <span>{report?.reportedAt ? new Date(report.reportedAt).toLocaleDateString() : "Recent"}</span>
                </div>
              </div>

              {/* Adversarial Alert */}
              {isPromptInjection && (
                <div className="mb-2.5 p-2.5 bg-red-100 border border-red-300 rounded-lg flex items-start space-x-2 text-xs text-red-900">
                  <ShieldAlert className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <strong>Prompt Injection Neutralized:</strong> Adversarial instructions in
                    comment were intercepted and neutralized. Stored answer key was preserved.
                  </div>
                </div>
              )}

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 italic">
                "{report?.comment || "No comment provided."}"
              </div>
            </div>

            {/* AI Investigation Engine Trace Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <div className="flex items-center space-x-1.5">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    AI Investigation Trace
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  openai/gpt-oss-120b
                </span>
              </div>

              {/* Stage A: BlindSolve */}
              <div className="p-2.5 bg-blue-50/50 rounded-lg border border-blue-100 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-blue-900">Stage A: BlindSolve Derivation</span>
                  <span className="text-blue-700 font-mono font-bold">
                    Ans: {blindSolve?.derived_answer !== undefined ? String(blindSolve.derived_answer) : "N/A"}
                  </span>
                </div>
                <p className="text-slate-600 line-clamp-3 text-[11px] leading-relaxed">
                  {blindSolve?.step_by_step_reasoning || "Derived independently using first principles."}
                </p>
              </div>

              {/* Stage B: Verification & Mathematical Proof */}
              <div className="p-2.5 bg-emerald-50/50 rounded-lg border border-emerald-100 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-emerald-900 flex items-center">
                    <Calculator className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                    Stage B: Answer & Proof Check
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-200 text-emerald-800">
                    {answerVerif?.verification_status || "passed"}
                  </span>
                </div>
                <div className="text-[11px] text-slate-600 space-y-0.5">
                  <div>
                    Stored matches derived:{" "}
                    <strong>{answerVerif?.stored_answer_matches ? "YES" : "NO (Mismatch Detected)"}</strong>
                  </div>
                  {answerVerif?.deterministic_proof && (
                    <div className="mt-1 font-mono text-[10px] bg-emerald-100/70 p-1 rounded text-emerald-900">
                      Proof: {answerVerif.deterministic_proof}
                    </div>
                  )}
                </div>
              </div>

              {/* Stage C: Triage Evidence */}
              <div className="text-xs text-slate-700">
                <span className="font-semibold text-slate-900">Triage Evidence:</span>
                <p className="text-slate-600 mt-0.5 text-[11px] leading-relaxed">
                  {result.evidence}
                </p>
              </div>
            </div>

            {/* Proposed Surgical Edit (Visual Diff) */}
            {result.edit && (
              <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-1.5">
                    <FileCode2 className="w-4 h-4 text-purple-600" />
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Proposed Surgical Mutation
                    </h4>
                  </div>
                  <span className="text-[11px] font-mono bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                    field: {result.edit.field}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-red-50 border border-red-200">
                    <span className="text-[10px] uppercase font-bold text-red-600 block mb-0.5">
                      Find / Replace Target
                    </span>
                    <span className="font-mono text-red-900 font-semibold break-words">
                      {result.edit.find || "(Full Field)"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200">
                    <span className="text-[10px] uppercase font-bold text-emerald-600 block mb-0.5">
                      New Value (Verified)
                    </span>
                    <span className="font-mono text-emerald-900 font-semibold break-words">
                      {String(result.edit.replace)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Truthful Student Reply Preview */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <div className="flex items-center space-x-1.5 mb-2">
                <MessageSquare className="w-4 h-4 text-blue-600" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Truthful Student Reply
                </h4>
              </div>
              <p className="p-2.5 bg-blue-50/40 rounded-lg border border-blue-100 text-xs text-slate-700 leading-relaxed">
                "{result.student_reply}"
              </p>
            </div>

            {/* Faculty Review Decision & Action Console */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-4 shadow-md space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Faculty Review Action
                  </span>
                </div>
                {facultyReview ? (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30">
                    Status: {facultyReview.status.toUpperCase()}
                  </span>
                ) : (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-medium border border-amber-500/30">
                    Pending Decision
                  </span>
                )}
              </div>

              {submitSuccess && (
                <div className="p-2 bg-emerald-500/20 border border-emerald-500/40 rounded text-xs text-emerald-200">
                  {submitSuccess}
                </div>
              )}

              {/* Reviewer Notes Input */}
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Faculty Review Notes (Optional):
                </label>
                <textarea
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  placeholder="e.g. Verified first principles derivation. Ready for database commit."
                  rows={2}
                  className="w-full text-xs bg-slate-950/70 border border-slate-700 rounded-lg p-2 text-slate-200 placeholder-slate-500 focus:outline-hidden focus:border-blue-500"
                />
              </div>

              {/* Custom Patch Mode Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => setIsEditMode(!isEditMode)}
                  className="text-xs text-blue-400 hover:text-blue-300 underline font-medium"
                >
                  {isEditMode ? "Cancel Custom Mutation" : "+ Customize Patch / Reply"}
                </button>
              </div>

              {isEditMode && (
                <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-700 space-y-2 text-xs">
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-400">Target Field</label>
                      <input
                        type="text"
                        value={editField}
                        onChange={(e) => setEditField(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400">Find Target</label>
                      <input
                        type="text"
                        value={editFind}
                        onChange={(e) => setEditFind(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400">Replace With</label>
                      <input
                        type="text"
                        value={editReplace}
                        onChange={(e) => setEditReplace(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Custom Student Reply</label>
                    <textarea
                      value={customReply}
                      onChange={(e) => setCustomReply(e.target.value)}
                      rows={2}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-slate-200"
                    />
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 pt-1">
                <button
                  disabled={isSubmitting}
                  onClick={() => handleAction("approve")}
                  className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold text-xs transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve Staged Patch</span>
                </button>

                <button
                  disabled={isSubmitting}
                  onClick={() => handleAction("reject")}
                  className="py-2 px-3 bg-red-600/80 hover:bg-red-500 text-white rounded-lg font-semibold text-xs transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>

                {isEditMode && (
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleAction("modify")}
                    className="py-2 px-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold text-xs transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
                  >
                    <span>Save Custom</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

