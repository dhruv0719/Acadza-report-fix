"use client";

import React, { useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowUpDown,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  Filter,
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import {
  FacultyReviewRecord,
  NormalizedQuestion,
  ReportRecord,
  ResultItem,
} from "@/types";

interface TriageTableProps {
  results: ResultItem[];
  questionsMap: Record<string, NormalizedQuestion>;
  reportsMap: Record<string, ReportRecord>;
  facultyReviewsMap: Record<string, FacultyReviewRecord>;
  onSelectReport: (result: ResultItem) => void;
  activeFilter?: string;
  onFilterChange?: (filter: string) => void;
}

export default function TriageTable({
  results,
  questionsMap,
  reportsMap,
  facultyReviewsMap,
  onSelectReport,
  activeFilter = "all",
  onFilterChange,
}: TriageTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRoute, setSelectedRoute] = useState<string>(activeFilter);
  const [selectedVerdict, setSelectedVerdict] = useState<string>("all");
  const [selectedSubject, setSelectedSubject] = useState<string>("all");
  const [sortField, setSortField] = useState<"reportId" | "confidence" | "route">("reportId");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Sync selectedRoute when activeFilter changes from parent stats cards
  React.useEffect(() => {
    if (activeFilter) {
      setSelectedRoute(activeFilter);
    }
  }, [activeFilter]);

  const subjects = useMemo(() => {
    const set = new Set<string>();
    Object.values(questionsMap).forEach((q) => {
      if (q.subject) set.add(q.subject);
    });
    return Array.from(set).sort();
  }, [questionsMap]);

  const filteredResults = useMemo(() => {
    return results.filter((item) => {
      const question = questionsMap[item.questionId];
      const report = reportsMap[item.reportId];

      // Route filter
      if (selectedRoute === "auto_apply" && item.route !== "auto_apply") return false;
      if (selectedRoute === "faculty_review" && item.route !== "faculty_review") return false;
      if (selectedRoute === "no_change" && item.route !== "no_change") return false;
      if (selectedRoute === "defects" && item.verdict !== "defect") return false;

      // Verdict filter
      if (selectedVerdict !== "all" && item.verdict !== selectedVerdict) return false;

      // Subject filter
      if (selectedSubject !== "all" && question?.subject !== selectedSubject) return false;

      // Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const rId = item.reportId.toLowerCase();
        const qId = item.questionId.toLowerCase();
        const comment = (report?.comment || "").toLowerCase();
        const subject = (question?.subject || "").toLowerCase();
        const chapter = (question?.chapter || "").toLowerCase();
        const verdict = item.verdict.toLowerCase();

        if (
          !rId.includes(query) &&
          !qId.includes(query) &&
          !comment.includes(query) &&
          !subject.includes(query) &&
          !chapter.includes(query) &&
          !verdict.includes(query)
        ) {
          return false;
        }
      }

      return true;
    });
  }, [
    results,
    questionsMap,
    reportsMap,
    selectedRoute,
    selectedVerdict,
    selectedSubject,
    searchQuery,
  ]);

  const sortedResults = useMemo(() => {
    return [...filteredResults].sort((a, b) => {
      let comparison = 0;
      if (sortField === "reportId") {
        comparison = a.reportId.localeCompare(b.reportId, undefined, { numeric: true });
      } else if (sortField === "confidence") {
        comparison = a.confidence - b.confidence;
      } else if (sortField === "route") {
        comparison = a.route.localeCompare(b.route);
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredResults, sortField, sortDirection]);

  const toggleSort = (field: "reportId" | "confidence" | "route") => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const renderRouteBadge = (route: string) => {
    switch (route) {
      case "auto_apply":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
            <Sparkles className="w-3 h-3 mr-1 text-emerald-600" />
            Auto Apply
          </span>
        );
      case "faculty_review":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
            <Clock className="w-3 h-3 mr-1 text-amber-600" />
            Faculty Review
          </span>
        );
      case "no_change":
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
            <CheckCircle2 className="w-3 h-3 mr-1 text-blue-600" />
            No Change
          </span>
        );
      default:
        return <span>{route}</span>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Control Bar: Search & Filters */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[260px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search report ID (R004), question ID, comment, or topic..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-blue-500 text-slate-800"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Route Filter */}
          <select
            value={selectedRoute}
            onChange={(e) => {
              setSelectedRoute(e.target.value);
              if (onFilterChange) onFilterChange(e.target.value);
            }}
            className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-700 font-medium focus:outline-hidden focus:border-blue-500"
          >
            <option value="all">All Routes (44)</option>
            <option value="auto_apply">Auto Apply (17)</option>
            <option value="faculty_review">Faculty Review (10)</option>
            <option value="no_change">No Change (17)</option>
            <option value="defects">All Defects (27)</option>
          </select>

          {/* Subject Filter */}
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-700 font-medium focus:outline-hidden focus:border-blue-500"
          >
            <option value="all">All Subjects</option>
            {subjects.map((sub) => (
              <option key={sub} value={sub}>
                {sub}
              </option>
            ))}
          </select>

          {/* Verdict Filter */}
          <select
            value={selectedVerdict}
            onChange={(e) => setSelectedVerdict(e.target.value)}
            className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-700 font-medium focus:outline-hidden focus:border-blue-500"
          >
            <option value="all">All Verdicts</option>
            <option value="defect">defect</option>
            <option value="no_error">no_error</option>
            <option value="not_actionable">not_actionable</option>
            <option value="duplicate">duplicate</option>
            <option value="already_fixed">already_fixed</option>
            <option value="out_of_scope">out_of_scope</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-600">
          <thead className="bg-slate-100/70 text-slate-700 font-semibold uppercase text-[11px] tracking-wider border-b border-slate-200">
            <tr>
              <th
                onClick={() => toggleSort("reportId")}
                className="py-3 px-4 cursor-pointer hover:bg-slate-200/50 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Report ID</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-3 px-4">Subject & Question ID</th>
              <th className="py-3 px-4">Student Comment</th>
              <th className="py-3 px-4">Verdict & Repair</th>
              <th className="py-3 px-4">Proposed Edit</th>
              <th
                onClick={() => toggleSort("route")}
                className="py-3 px-4 cursor-pointer hover:bg-slate-200/50 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Route</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                onClick={() => toggleSort("confidence")}
                className="py-3 px-4 cursor-pointer hover:bg-slate-200/50 transition-colors"
              >
                <div className="flex items-center space-x-1">
                  <span>Conf</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-3 px-4 text-center">Faculty Review</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sortedResults.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-400 italic">
                  No reports match the active filters.
                </td>
              </tr>
            ) : (
              sortedResults.map((item) => {
                const question = questionsMap[item.questionId];
                const report = reportsMap[item.reportId];
                const review = facultyReviewsMap[item.reportId];
                const isPromptInjection =
                  report?.comment.toLowerCase().includes("ignore") ||
                  report?.comment.toLowerCase().includes("instruction");

                return (
                  <tr
                    key={item.reportId}
                    className="hover:bg-blue-50/30 transition-colors cursor-pointer group"
                    onClick={() => onSelectReport(item)}
                  >
                    {/* Report ID */}
                    <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <span>{item.reportId}</span>
                        {isPromptInjection && (
                          <span title="Adversarial Prompt Injection Defended">
                            <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Subject & Question ID */}
                    <td className="py-3 px-4">
                      <div className="flex flex-col">
                        <span className="font-medium text-slate-800">
                          {question?.subject || "Unknown"}
                        </span>
                        <span className="font-mono text-[10px] text-slate-400 truncate max-w-[140px]">
                          {item.questionId}
                        </span>
                      </div>
                    </td>

                    {/* Student Comment */}
                    <td className="py-3 px-4 max-w-[220px]">
                      <p className="text-slate-600 line-clamp-2 italic text-[11px]">
                        "{report?.comment || "No comment"}"
                      </p>
                    </td>

                    {/* Verdict & Repair */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <span
                          className={`font-semibold ${
                            item.verdict === "defect" ? "text-red-600" : "text-slate-700"
                          }`}
                        >
                          {item.verdict}
                        </span>
                        {item.repair && (
                          <span className="text-[10px] text-purple-700 font-mono">
                            {item.repair}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Proposed Edit */}
                    <td className="py-3 px-4 max-w-[160px]">
                      {item.edit ? (
                        <div className="font-mono text-[11px] truncate bg-slate-50 p-1 rounded border border-slate-200">
                          <span className="text-slate-500">{item.edit.field}: </span>
                          {item.edit.find && (
                            <span className="line-through text-red-600 mr-1">
                              {item.edit.find}
                            </span>
                          )}
                          <span className="text-emerald-600 font-bold">
                            {String(item.edit.replace)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-[11px]">None</span>
                      )}
                    </td>

                    {/* Route */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {renderRouteBadge(item.route)}
                    </td>

                    {/* Confidence */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-semibold text-slate-700">
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </td>

                    {/* Faculty Review Status */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {review ? (
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            review.status === "approved"
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              : review.status === "rejected"
                              ? "bg-red-100 text-red-800 border border-red-300"
                              : "bg-blue-100 text-blue-800 border border-blue-300"
                          }`}
                        >
                          {review.status.toUpperCase()}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px] italic">Pending</span>
                      )}
                    </td>

                    {/* Action Button */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectReport(item);
                        }}
                        className="p-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white transition-colors group-hover:bg-blue-600 group-hover:text-white"
                        title="Inspect report details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
        <span>
          Showing <strong>{sortedResults.length}</strong> of <strong>{results.length}</strong> reports
        </span>
        <span className="text-[11px]">Click any row to open the complete investigation trace & faculty console.</span>
      </div>
    </div>
  );
}

