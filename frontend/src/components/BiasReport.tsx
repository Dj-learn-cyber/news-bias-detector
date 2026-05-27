import { useState } from "react";
import type { AnalyzeResponse } from "../types";
import PoliticalMeter from "./PoliticalMeter";
import CredibilityCard from "./CredibilityCard";
import FramingAnalysis from "./FramingAnalysis";

interface Props {
  data: AnalyzeResponse;
}

export default function BiasReport({ data }: Props) {
  const [copied, setCopied] = useState(false);

  function copyResults() {
    const lines = [
      "── News Bias Analysis ──",
      data.article_title ? `Article: ${data.article_title}` : null,
      `Political lean: ${data.political_lean.label} (${(data.political_lean.confidence * 100).toFixed(0)}% confidence)`,
      data.source_credibility.found
        ? `Source: ${data.source_credibility.outlet} — credibility ${data.source_credibility.score}/10`
        : null,
      `Opening tone: ${data.framing.opening_tone}`,
      `Loaded language: ${(data.framing.loaded_language_score * 100).toFixed(0)}%`,
      `Word count: ${data.word_count}`,
      "",
      data.summary,
    ]
      .filter((l) => l !== null)
      .join("\n");

    navigator.clipboard.writeText(lines).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="space-y-4">
      {/* Summary banner */}
      <div className="bg-gray-800 border border-gray-700 rounded-2xl p-4">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="min-w-0">
            {data.article_title && (
              <div className="text-xs text-gray-500 mb-1">Analyzed article</div>
            )}
            {data.article_title && (
              <div className="text-sm font-medium text-gray-200 mb-2 line-clamp-2">
                {data.article_title}
              </div>
            )}
          </div>
          <button
            onClick={copyResults}
            className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">{data.summary}</p>
        <div className="mt-2 text-xs text-gray-600">{data.word_count.toLocaleString()} words</div>
      </div>

      <PoliticalMeter data={data.political_lean} />
      <CredibilityCard data={data.source_credibility} />
      <FramingAnalysis data={data.framing} />
    </div>
  );
}
