"use client";

import React from "react";

interface HtmlRendererProps {
  html: string;
  className?: string;
}

export default function HtmlRenderer({ html, className = "" }: HtmlRendererProps) {
  if (!html) return <span className="text-slate-400 italic">No content</span>;

  return (
    <div
      className={`prose prose-slate max-w-none text-sm leading-relaxed ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

