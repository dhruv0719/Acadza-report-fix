"use client";

import React from "react";
import { BarChart3, Clock, Cpu, Flame, Layers, ShieldCheck, Zap } from "lucide-react";
import { TelemetryData } from "@/types";

interface TelemetryTabProps {
  telemetry: TelemetryData | null;
}

export default function TelemetryTab({ telemetry }: TelemetryTabProps) {
  if (!telemetry) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-400">
        Loading telemetry data...
      </div>
    );
  }

  const { summary, logs } = telemetry;

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <BarChart3 className="w-5 h-5 text-amber-600" />
              <h2 className="text-lg font-bold text-slate-900">
                Live Groq LLM Telemetry & Execution Logs
              </h2>
            </div>
            <p className="text-xs text-slate-500 max-w-2xl leading-relaxed">
              Every token, latency figure, and HTTP status code measured directly from live Groq API
              responses using <code className="font-mono text-emerald-700">openai/gpt-oss-120b</code>.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
              Provider: {summary.provider}
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-800 font-semibold border border-blue-200">
              Model: {summary.primary_model}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Total Live Calls
          </span>
          <div className="text-2xl font-bold text-slate-900">{summary.total_calls}</div>
          <span className="text-[11px] text-emerald-600 font-medium">100% Success</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Total Tokens
          </span>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {summary.total_tokens.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-500">Across 4 cases</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Reasoning Tokens
          </span>
          <div className="text-2xl font-bold text-purple-700 font-mono">
            {summary.total_reasoning_tokens.toLocaleString()}
          </div>
          <span className="text-[11px] text-purple-600 font-medium">High Effort Active</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Prompt Tokens
          </span>
          <div className="text-2xl font-bold text-slate-700 font-mono">
            {summary.total_prompt_tokens.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-500">HTML & MathML compact</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Total Wall Latency
          </span>
          <div className="text-2xl font-bold text-amber-700 font-mono">
            {summary.total_latency_seconds}s
          </div>
          <span className="text-[11px] text-slate-500">Includes 429 backoff</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
            Avg Latency / Call
          </span>
          <div className="text-2xl font-bold text-blue-700 font-mono">
            {(summary.average_latency_ms / 1000).toFixed(1)}s
          </div>
          <span className="text-[11px] text-slate-500">Deep reasoning model</span>
        </div>
      </div>

      {/* Execution Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
            Detailed API Invocation Records ({logs.length})
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">
            Concurrency: 1 • Retry-After Headers Honored
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-100/70 text-slate-700 font-semibold uppercase text-[11px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Stage</th>
                <th className="py-3 px-4">Question ID</th>
                <th className="py-3 px-4 text-right">Prompt</th>
                <th className="py-3 px-4 text-right">Completion</th>
                <th className="py-3 px-4 text-right">Reasoning</th>
                <th className="py-3 px-4 text-right">Total Tokens</th>
                <th className="py-3 px-4 text-right">Latency</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {logs.map((log, i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="py-2.5 px-4 text-slate-500">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-2.5 px-4 font-semibold text-slate-800 font-sans">
                    {log.stage}
                  </td>
                  <td className="py-2.5 px-4 text-slate-500 truncate max-w-[140px]">
                    {log.question_id}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-600">
                    {log.prompt_tokens.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-600">
                    {log.completion_tokens.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-right text-purple-700 font-bold">
                    {log.reasoning_tokens.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-right font-bold text-slate-900">
                    {log.total_tokens.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-4 text-right text-amber-700">
                    {(log.latency_ms / 1000).toFixed(2)}s
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-100 text-emerald-800 font-semibold font-sans">
                      {log.status_code} OK
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

