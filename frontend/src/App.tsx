import { useState } from "react";
import ArticleInput from "./components/ArticleInput";
import BiasReport from "./components/BiasReport";
import { analyzeArticle } from "./api";
import type { AnalyzeResponse } from "./types";

export default function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(payload: { text?: string; url?: string }) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeArticle(payload);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-sm">
            B
          </div>
          <div>
            <h1 className="text-base font-bold text-white leading-none">News Bias Detector</h1>
            <p className="text-xs text-gray-500 mt-0.5">AI-powered political lean, credibility &amp; framing analysis</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Left column: input */}
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Analyze an Article</h2>
              <p className="text-sm text-gray-500 mt-1">
                Paste article text or enter a URL. The AI will detect political lean,
                source credibility, and framing patterns.
              </p>
            </div>

            <ArticleInput onSubmit={handleSubmit} loading={loading} />

            {error && (
              <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-sm text-red-300">
                {error}
              </div>
            )}

            {/* How it works */}
            {!result && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3 text-sm">
                <h3 className="font-semibold text-gray-300">How it works</h3>
                <ul className="space-y-2 text-gray-500">
                  <li className="flex gap-2">
                    <span className="text-blue-400 shrink-0">1.</span>
                    <span>
                      <span className="text-gray-300">Political lean</span> — zero-shot RoBERTa
                      classifies the text as left, center, or right.
                    </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-blue-400 shrink-0">2.</span>
                    <span>
                      <span className="text-gray-300">Source credibility</span> — outlet is
                      looked up against a curated AllSides/MBFC-derived database.
                    </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-blue-400 shrink-0">3.</span>
                    <span>
                      <span className="text-gray-300">Framing</span> — loaded language patterns,
                      hedge ratio, and entity-level sentiment via NER + DistilBERT.
                    </span>
                  </li>
                </ul>
              </div>
            )}
          </div>

          {/* Right column: results */}
          <div>
            {loading && (
              <div className="flex flex-col items-center justify-center py-20 text-gray-500 space-y-3">
                <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span className="text-sm">Running analysis&hellip;</span>
                <span className="text-xs text-gray-600">First run may take ~30s to load models</span>
              </div>
            )}

            {result && !loading && <BiasReport data={result} />}

            {!result && !loading && (
              <div className="flex flex-col items-center justify-center py-20 text-gray-700 text-sm">
                <div className="text-4xl mb-3">&#128240;</div>
                <p>Your analysis will appear here</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
