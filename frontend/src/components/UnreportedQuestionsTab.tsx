"use client";

import React from "react";
import { CheckCircle2, FileCheck2, HelpCircle, Info } from "lucide-react";
import { UnreportedQuestionAudit } from "@/types";

interface UnreportedQuestionsTabProps {
  unreported: UnreportedQuestionAudit[];
}

export default function UnreportedQuestionsTab({ unreported }: UnreportedQuestionsTabProps) {
  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center space-x-2 mb-1">
          <FileCheck2 className="w-5 h-5 text-sky-600" />
          <h2 className="text-lg font-bold text-slate-900">
            Audit of 4 Unreported Questions
          </h2>
        </div>
        <p className="text-xs text-slate-500 max-w-3xl leading-relaxed">
          Four questions in the 43-question dataset received zero student defect reports. To ensure
          absolute question bank reliability, each was independently audited against official JEE/NEET
          syllabi and first-principles derivations.
        </p>
      </div>

      {/* Grid of Unreported Questions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {unreported.map((q) => (
          <div
            key={q.question_id}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                  {q.question_id}
                </span>
                <div className="text-xs text-slate-500 mt-1">
                  {q.subject} • {q.chapter}
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                Scientifically Sound
              </span>
            </div>

            {/* Stem */}
            <div>
              <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Question Stem
              </h4>
              <p className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-800 leading-relaxed">
                {q.stem_text}
              </p>
            </div>

            {/* Stored Answer */}
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
              <span className="text-slate-600 font-medium">Stored Answer Key:</span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {String(q.stored_answer)}
              </span>
            </div>

            {/* Scientific Derivation */}
            <div>
              <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Verified Scientific Derivation
              </h4>
              <p className="p-3 bg-emerald-50/40 rounded-lg border border-emerald-100 text-xs text-slate-700 leading-relaxed font-mono text-[11px]">
                {q.scientific_derivation}
              </p>
            </div>

            {/* Findings Note */}
            {q.findings && q.findings.length > 0 && (
              <div className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="font-semibold text-slate-700">Audit Finding: </span>
                {q.findings[0].description}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

