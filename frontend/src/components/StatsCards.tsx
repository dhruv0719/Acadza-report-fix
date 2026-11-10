"use client";

import React from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileQuestion,
  Layers,
  Sparkles,
} from "lucide-react";

interface StatsCardsProps {
  totalReports: number;
  totalQuestions: number;
  defectsCount: number;
  autoApplyCount: number;
  facultyReviewCount: number;
  noChangeCount: number;
  qualityFindingsCount: number;
  onFilterRoute?: (route: string) => void;
  activeFilter?: string;
}

export default function StatsCards({
  totalReports,
  totalQuestions,
  defectsCount,
  autoApplyCount,
  facultyReviewCount,
  noChangeCount,
  qualityFindingsCount,
  onFilterRoute,
  activeFilter,
}: StatsCardsProps) {
  const cards = [
    {
      label: "Total Reports",
      value: totalReports,
      subtext: "Across 39 question groups",
      icon: Layers,
      color: "border-slate-300 text-slate-800 bg-white",
      iconColor: "text-slate-600 bg-slate-100",
      filterKey: "all",
    },
    {
      label: "Defects Identified",
      value: defectsCount,
      subtext: `${Math.round((defectsCount / totalReports) * 100)}% of submitted reports`,
      icon: AlertCircle,
      color: "border-red-200 text-red-900 bg-red-50/40",
      iconColor: "text-red-600 bg-red-100",
      filterKey: "defects",
    },
    {
      label: "Staged Auto-Apply",
      value: autoApplyCount,
      subtext: "Calculations & proofs verified",
      icon: Sparkles,
      color: "border-emerald-200 text-emerald-900 bg-emerald-50/40",
      iconColor: "text-emerald-600 bg-emerald-100",
      filterKey: "auto_apply",
    },
    {
      label: "Faculty Review Queue",
      value: facultyReviewCount,
      subtext: "Ambiguous or missing assets",
      icon: Clock,
      color: "border-amber-200 text-amber-900 bg-amber-50/40",
      iconColor: "text-amber-600 bg-amber-100",
      filterKey: "faculty_review",
    },
    {
      label: "No Change / Rejected",
      value: noChangeCount,
      subtext: "Includes prompt injection defenses",
      icon: CheckCircle,
      color: "border-blue-200 text-blue-900 bg-blue-50/40",
      iconColor: "text-blue-600 bg-blue-100",
      filterKey: "no_change",
    },
    {
      label: "Intrinsic Quality Defects",
      value: qualityFindingsCount,
      subtext: "Isolated independent of reports",
      icon: AlertTriangle,
      color: "border-purple-200 text-purple-900 bg-purple-50/40",
      iconColor: "text-purple-600 bg-purple-100",
      filterKey: "intrinsic",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((card) => {
        const Icon = card.icon;
        const isSelected = activeFilter === card.filterKey;

        return (
          <button
            key={card.label}
            onClick={() => onFilterRoute && onFilterRoute(card.filterKey)}
            className={`p-3.5 rounded-xl border text-left transition-all shadow-xs hover:shadow-sm ${
              card.color
            } ${
              isSelected
                ? "ring-2 ring-blue-600 ring-offset-1 shadow-sm font-medium"
                : "hover:border-slate-400"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                {card.label}
              </span>
              <div className={`p-1.5 rounded-lg ${card.iconColor}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold tracking-tight mb-0.5">{card.value}</div>
            <div className="text-[11px] text-slate-500 truncate">{card.subtext}</div>
          </button>
        );
      })}
    </div>
  );
}

