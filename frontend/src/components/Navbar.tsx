"use client";

import React from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Cpu,
  FileCheck2,
  FileText,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export type NavTab = "triage" | "live_groq" | "quality_findings" | "unreported" | "telemetry";

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  autoApplyCount: number;
  facultyReviewCount: number;
  qualityFindingsCount: number;
}

export default function Navbar({
  activeTab,
  onTabChange,
  autoApplyCount,
  facultyReviewCount,
  qualityFindingsCount,
}: NavbarProps) {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md">
              A
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">
                  Acadza AI Report → Fix
                </span>
                <span className="bg-blue-500/20 text-blue-300 text-xs px-2 py-0.5 rounded font-mono font-medium border border-blue-500/30">
                  Faculty Console
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Automated JEE/NEET Question Defect Triage & Verification Engine
              </p>
            </div>
          </div>

          {/* Engine Status Badge */}
          <div className="hidden lg:flex items-center space-x-3 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/60 text-xs">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-slate-300 font-medium">Groq Live</span>
            <span className="text-slate-500">|</span>
            <span className="text-emerald-400 font-mono">openai/gpt-oss-120b</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">Concurrency: 1</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 border-t border-slate-800/60 pt-1 -mb-px overflow-x-auto">
          <button
            onClick={() => onTabChange("triage")}
            className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "triage"
                ? "border-blue-500 text-blue-400 bg-slate-800/40"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Triage Queue (44)</span>
            {facultyReviewCount > 0 && (
              <span className="ml-1.5 bg-amber-500/20 text-amber-300 text-xs px-1.5 py-0.5 rounded-full border border-amber-500/30">
                {facultyReviewCount} Review
              </span>
            )}
          </button>

          <button
            onClick={() => onTabChange("live_groq")}
            className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "live_groq"
                ? "border-emerald-500 text-emerald-400 bg-slate-800/40"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Live Groq Verification (4 Cases)</span>
            <span className="ml-1.5 bg-emerald-500/20 text-emerald-300 text-xs px-1.5 py-0.5 rounded-full border border-emerald-500/30">
              Verified
            </span>
          </button>

          <button
            onClick={() => onTabChange("quality_findings")}
            className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "quality_findings"
                ? "border-purple-500 text-purple-400 bg-slate-800/40"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Intrinsic Defects ({qualityFindingsCount})</span>
          </button>

          <button
            onClick={() => onTabChange("unreported")}
            className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "unreported"
                ? "border-sky-500 text-sky-400 bg-slate-800/40"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <FileCheck2 className="w-4 h-4" />
            <span>Unreported Questions (4)</span>
          </button>

          <button
            onClick={() => onTabChange("telemetry")}
            className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "telemetry"
                ? "border-amber-500 text-amber-400 bg-slate-800/40"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>LLM Telemetry & Logs</span>
          </button>
        </div>
      </div>
    </header>
  );
}

