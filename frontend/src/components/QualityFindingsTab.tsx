"use client";

import React, { useState } from "react";
import { AlertCircle, AlertTriangle, CheckCircle, Filter, Layers, Search } from "lucide-react";
import { QualityFinding } from "@/types";

interface QualityFindingsTabProps {
  findings: QualityFinding[];
}

export default function QualityFindingsTab({ findings }: QualityFindingsTabProps) {
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterField, setFilterField] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  const filtered = findings.filter((f) => {
    if (filterSeverity !== "all" && f.severity !== filterSeverity) return false;
    if (filterField !== "all" && f.field !== filterField) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        f.question_id.toLowerCase().includes(q) ||
        f.description.toLowerCase().includes(q) ||
        f.issue_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "critical":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
            Critical
          </span>
        );
      case "high":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            High
          </span>
        );
      case "medium":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
            Medium
          </span>
        );
      case "low":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200">
            Low
          </span>
        );
      default:
        return <span>{severity}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <AlertTriangle className="w-5 h-5 text-purple-600" />
              <h2 className="text-lg font-bold text-slate-900">
                14 Intrinsic Corpus Content Defects
              </h2>
            </div>
            <p className="text-xs text-slate-500 max-w-3xl leading-relaxed">
              These defects exist intrinsically in the Acadza question bank. They were isolated
              independently of whether a student reported them accurately. Addressing these ensures
              complete question bank integrity across exams.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-purple-50 text-purple-800 font-semibold border border-purple-200">
              Total Isolated: {findings.length}
            </span>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by question ID, defect type, or keyword..."
            className="flex-1 min-w-[240px] px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800"
          />
          <div className="flex items-center space-x-2">
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-medium"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filterField}
              onChange={(e) => setFilterField(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-medium"
            >
              <option value="all">All Fields</option>
              <option value="answer">answer</option>
              <option value="question">question</option>
              <option value="solution">solution</option>
              <option value="options">options</option>
            </select>
          </div>
        </div>
      </div>

      {/* Findings List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((item, idx) => (
          <div
            key={idx}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                  {item.question_id}
                </span>
                <div className="flex items-center space-x-1.5">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                    {item.field}
                  </span>
                  {getSeverityBadge(item.severity)}
                </div>
              </div>
              <h4 className="text-xs font-semibold text-slate-800 mb-1.5">
                Issue: <span className="font-mono text-purple-700">{item.issue_type}</span>
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">{item.description}</p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
              <span>Independent of Student Reports</span>
              <span className="text-slate-600 font-medium">Corpus Finding #{idx + 1}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

