"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, ExternalLink, RefreshCw, Sparkles } from "lucide-react";
import {
  FacultyReviewRecord,
  InvestigationCheckpoint,
  NavTab,
  NormalizedQuestion,
  ProposedEdit,
  QualityFinding,
  ReportRecord,
  ResultItem,
  TelemetryData,
  UnreportedQuestionAudit,
} from "@/types";
import {
  fetchCheckpoints,
  fetchFacultyReviews,
  fetchQualityFindings,
  fetchQuestions,
  fetchReports,
  fetchResults,
  fetchTelemetry,
  fetchUnreportedAudit,
  getApiBase,
  submitFacultyReview,
} from "@/lib/api";
import LiveGroqTab from "@/components/LiveGroqTab";
import Navbar from "@/components/Navbar";
import QualityFindingsTab from "@/components/QualityFindingsTab";
import ReportDetailModal from "@/components/ReportDetailModal";
import StatsCards from "@/components/StatsCards";
import TelemetryTab from "@/components/TelemetryTab";
import TriageTable from "@/components/TriageTable";
import UnreportedQuestionsTab from "@/components/UnreportedQuestionsTab";

export default function FacultyConsoleApp() {
  const [activeTab, setActiveTab] = useState<NavTab>("triage");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Core Data
  const [results, setResults] = useState<ResultItem[]>([]);
  const [questionsMap, setQuestionsMap] = useState<Record<string, NormalizedQuestion>>({});
  const [reportsMap, setReportsMap] = useState<Record<string, ReportRecord>>({});
  const [qualityFindings, setQualityFindings] = useState<QualityFinding[]>([]);
  const [unreported, setUnreported] = useState<UnreportedQuestionAudit[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [checkpoints, setCheckpoints] = useState<Record<string, InvestigationCheckpoint>>({});
  const [facultyReviews, setFacultyReviews] = useState<Record<string, FacultyReviewRecord>>({});

  // Active Report Modal
  const [selectedResult, setSelectedResult] = useState<ResultItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        resData,
        qData,
        repData,
        qfData,
        unrepData,
        teleData,
        cpData,
        revData,
      ] = await Promise.all([
        fetchResults(),
        fetchQuestions(),
        fetchReports(),
        fetchQualityFindings(),
        fetchUnreportedAudit(),
        fetchTelemetry(),
        fetchCheckpoints(),
        fetchFacultyReviews(),
      ]);

      setResults(resData);

      const qMap: Record<string, NormalizedQuestion> = {};
      qData.forEach((q) => (qMap[q.id] = q));
      setQuestionsMap(qMap);

      const rMap: Record<string, ReportRecord> = {};
      repData.forEach((r) => (rMap[r.reportId] = r));
      setReportsMap(rMap);

      setQualityFindings(qfData);
      setUnreported(unrepData);
      setTelemetry(teleData);
      setCheckpoints(cpData);
      setFacultyReviews(revData);
    } catch (err: any) {
      console.error("Failed to load backend data:", err);
      const apiBase = getApiBase();
      const isLocal = apiBase.includes("localhost") || apiBase.includes("127.0.0.1");
      const defaultMsg = isLocal
        ? `Unable to connect to local FastAPI backend at ${apiBase}. Ensure the backend server is running.`
        : `Unable to connect to Acadza backend at ${apiBase}. Render free-tier instances may take ~50–90 seconds to wake up from sleep.`;
      setError(err?.message || defaultMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleSelectReport = (resItem: ResultItem) => {
    setSelectedResult(resItem);
    setIsModalOpen(true);
  };

  const handleReviewSubmit = async (
    reportId: string,
    action: "approve" | "reject" | "modify",
    notes?: string,
    customEdit?: ProposedEdit,
    customReply?: string
  ) => {
    const updated = await submitFacultyReview(reportId, {
      action,
      reviewer_notes: notes,
      modified_edit: customEdit,
      custom_reply: customReply,
      reviewer_name: "Acadza Faculty Reviewer",
    });

    setFacultyReviews((prev) => ({
      ...prev,
      [reportId]: updated,
    }));
  };

  // Metrics
  const totalReports = results.length;
  const totalQuestions = Object.keys(questionsMap).length;
  const defectsCount = results.filter((r) => r.verdict === "defect").length;
  const autoApplyCount = results.filter((r) => r.route === "auto_apply").length;
  const facultyReviewCount = results.filter((r) => r.route === "faculty_review").length;
  const noChangeCount = results.filter((r) => r.route === "no_change").length;

  return (
    <div className="min-h-screen bg-slate-100/70 text-slate-900 flex flex-col font-sans">
      {/* Navbar */}
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        autoApplyCount={autoApplyCount}
        facultyReviewCount={facultyReviewCount}
        qualityFindingsCount={qualityFindings.length}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Loading Spinner */}
        {loading && (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
            <p className="text-sm text-slate-500 font-medium">
              Loading Acadza triage corpus and Groq checkpoints...
            </p>
          </div>
        )}

        {/* Failed Connection / Disconnected Hero View */}
        {!loading && error && results.length === 0 && (
          <div className="py-10 max-w-3xl mx-auto">
            <div className="bg-white border border-red-200 rounded-2xl shadow-sm p-6 sm:p-8">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-red-100 rounded-xl text-red-600 shrink-0">
                  <AlertCircle className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-slate-900">
                      Backend Service Unavailable
                    </h2>
                    <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-red-100 text-red-700 border border-red-200">
                      Connection Failed
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                    The faculty console could not connect to the Acadza triage API backend. Zero counts are not being displayed because this is an active connection issue, not empty database records.
                  </p>

                  {/* Diagnostic Box */}
                  <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <div>
                      <span className="font-semibold text-slate-700">Target API Base: </span>
                      <code className="text-blue-700 font-mono bg-blue-50 px-1.5 py-0.5 rounded">
                        {getApiBase()}
                      </code>
                    </div>
                    <div>
                      <span className="font-semibold text-slate-700">Error Details: </span>
                      <code className="text-red-700 font-mono break-all">{error}</code>
                    </div>
                  </div>

                  {/* Contextual Guidance */}
                  <div className="mt-4 space-y-2 text-xs text-slate-500">
                    <p className="font-semibold text-slate-700">Troubleshooting:</p>
                    <ul className="list-disc pl-5 space-y-1">
                      {getApiBase().includes("onrender.com") && (
                        <li>
                          <strong className="text-slate-700">Render Free-Tier Spin-up:</strong> Inactive Render instances sleep automatically. Cold starts take ~50–90 seconds. Please wait a moment and click Retry.
                        </li>
                      )}
                      <li>
                        <strong className="text-slate-700">Vercel Environment Variable:</strong> Ensure <code className="bg-slate-100 px-1 rounded">NEXT_PUBLIC_API_URL</code> is set to <code className="bg-slate-100 px-1 rounded">https://acadza-report-fix.onrender.com/api</code> in your Vercel Project Settings.
                      </li>
                      {(getApiBase().includes("localhost") || getApiBase().includes("127.0.0.1")) && (
                        <li>
                          <strong className="text-slate-700">Local Dev:</strong> Start the backend with <code className="bg-slate-100 px-1 rounded">py -3.9 -m uvicorn app.main:app --app-dir backend --port 8000</code>.
                        </li>
                      )}
                    </ul>
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-6 flex flex-wrap items-center gap-3">
                    <button
                      onClick={loadAllData}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg flex items-center space-x-2 transition-colors shadow-xs"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Retry Connection</span>
                    </button>
                    <a
                      href={`${getApiBase()}/health`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold rounded-lg flex items-center space-x-1.5 transition-colors border border-slate-300"
                    >
                      <span>Check Health Endpoint</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Content (shown when not loading and either no error or previously loaded data exists) */}
        {!loading && (results.length > 0 || !error) && (
          <>
            {/* Top Warning Banner if data exists but a subsequent refresh failed */}
            {error && (
              <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start justify-between shadow-xs">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <h3 className="font-semibold text-amber-900 text-sm">
                      Backend Sync Warning (Displaying Cached Records)
                    </h3>
                    <p className="text-xs text-amber-700 mt-0.5 leading-relaxed">{error}</p>
                  </div>
                </div>
                <button
                  onClick={loadAllData}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry</span>
                </button>
              </div>
            )}

            {/* Top Metric Cards (shown in triage tab) */}
            {activeTab === "triage" && (
              <StatsCards
                totalReports={totalReports}
                totalQuestions={totalQuestions}
                defectsCount={defectsCount}
                autoApplyCount={autoApplyCount}
                facultyReviewCount={facultyReviewCount}
                noChangeCount={noChangeCount}
                qualityFindingsCount={qualityFindings.length}
                activeFilter={activeFilter}
                onFilterRoute={(filter) => setActiveFilter(filter)}
              />
            )}

            {/* Tab Views */}
            {activeTab === "triage" && (
              <TriageTable
                results={results}
                questionsMap={questionsMap}
                reportsMap={reportsMap}
                facultyReviewsMap={facultyReviews}
                onSelectReport={handleSelectReport}
                activeFilter={activeFilter}
                onFilterChange={(filter) => setActiveFilter(filter)}
              />
            )}

            {activeTab === "live_groq" && <LiveGroqTab />}

            {activeTab === "quality_findings" && (
              <QualityFindingsTab findings={qualityFindings} />
            )}

            {activeTab === "unreported" && (
              <UnreportedQuestionsTab unreported={unreported} />
            )}

            {activeTab === "telemetry" && <TelemetryTab telemetry={telemetry} />}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400 mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-2">
          <span>Acadza AI Report → Fix Loop System</span>
          <span className="font-mono text-[11px]">
            Groq gpt-oss-120b • Strict JSON Schema • Safe Academic Router
          </span>
          <span>43 Questions • 44 Reports • 14 Intrinsic Defects</span>
        </div>
      </footer>

      {/* Report Detail Modal */}
      <ReportDetailModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        result={selectedResult}
        question={selectedResult ? questionsMap[selectedResult.questionId] || null : null}
        report={selectedResult ? reportsMap[selectedResult.reportId] || null : null}
        checkpoint={
          selectedResult ? checkpoints[selectedResult.questionId] || null : null
        }
        facultyReview={
          selectedResult ? facultyReviews[selectedResult.reportId] || null : null
        }
        onReviewSubmit={handleReviewSubmit}
      />
    </div>
  );
}
