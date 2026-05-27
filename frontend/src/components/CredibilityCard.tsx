import type { SourceCredibility } from "../types";

function ScoreDots({ score }: { score: number }) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: 10 }).map((_, i) => (
        <div
          key={i}
          className={`h-2 w-2 rounded-full ${
            i < score
              ? score >= 8
                ? "bg-green-400"
                : score >= 5
                ? "bg-yellow-400"
                : "bg-red-400"
              : "bg-gray-700"
          }`}
        />
      ))}
    </div>
  );
}

const BIAS_COLOR: Record<string, string> = {
  "far-left": "bg-blue-900 text-blue-300",
  left: "bg-blue-800 text-blue-200",
  "lean-left": "bg-blue-900/60 text-blue-300",
  center: "bg-gray-700 text-gray-300",
  "lean-right": "bg-red-900/60 text-red-300",
  right: "bg-red-800 text-red-200",
  "far-right": "bg-red-900 text-red-300",
};

interface Props {
  data: SourceCredibility;
}

export default function CredibilityCard({ data }: Props) {
  if (!data.found) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
          Source Credibility
        </h2>
        <div className="text-gray-500 text-sm">
          {data.outlet
            ? `"${data.outlet}" not found in our source database.`
            : "No source URL provided — paste a URL to get source credibility."}
        </div>
      </div>
    );
  }

  const biasClass =
    data.bias_label && BIAS_COLOR[data.bias_label]
      ? BIAS_COLOR[data.bias_label]
      : "bg-gray-700 text-gray-300";

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
        Source Credibility
      </h2>

      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-xl font-bold text-white">{data.outlet}</div>
          {data.bias_label && (
            <span
              className={`mt-1 inline-block px-2 py-0.5 rounded text-xs font-medium ${biasClass}`}
            >
              {data.bias_label.replace("-", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          )}
        </div>
        {data.score !== null && (
          <div className="text-right">
            <div
              className={`text-3xl font-black ${
                data.score >= 8
                  ? "text-green-400"
                  : data.score >= 5
                  ? "text-yellow-400"
                  : "text-red-400"
              }`}
            >
              {data.score}
              <span className="text-base text-gray-500">/10</span>
            </div>
            <div className="text-xs text-gray-500">credibility</div>
          </div>
        )}
      </div>

      {data.score !== null && (
        <div className="mb-4">
          <ScoreDots score={data.score} />
        </div>
      )}

      {data.factual_reporting && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Factual reporting:</span>
          <span
            className={`font-medium ${
              data.factual_reporting === "very high" || data.factual_reporting === "high"
                ? "text-green-400"
                : data.factual_reporting === "mostly factual"
                ? "text-yellow-300"
                : data.factual_reporting === "mixed"
                ? "text-orange-400"
                : "text-red-400"
            }`}
          >
            {data.factual_reporting.charAt(0).toUpperCase() + data.factual_reporting.slice(1)}
          </span>
        </div>
      )}
    </div>
  );
}
