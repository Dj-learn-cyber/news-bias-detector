import type { Framing } from "../types";

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2 bg-gray-800 rounded-full overflow-hidden w-full">
      <div
        className={`h-full rounded-full transition-all duration-700 ${color}`}
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

interface Props {
  data: Framing;
}

export default function FramingAnalysis({ data }: Props) {
  const sentimentEntries = Object.entries(data.entity_sentiments);

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 space-y-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
        Framing Analysis
      </h2>

      {/* Opening tone */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400 w-32 shrink-0">Opening tone</span>
        <span
          className={`px-2 py-0.5 rounded text-xs font-semibold ${
            data.opening_tone === "positive"
              ? "bg-green-900 text-green-300"
              : data.opening_tone === "negative"
              ? "bg-red-900 text-red-300"
              : "bg-gray-700 text-gray-300"
          }`}
        >
          {data.opening_tone.charAt(0).toUpperCase() + data.opening_tone.slice(1)}
        </span>
      </div>

      {/* Loaded language */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">Loaded language</span>
          <span
            className={`font-semibold ${
              data.loaded_language_score > 0.6
                ? "text-red-400"
                : data.loaded_language_score > 0.3
                ? "text-yellow-400"
                : "text-green-400"
            }`}
          >
            {data.loaded_language_score > 0.6
              ? "High"
              : data.loaded_language_score > 0.3
              ? "Moderate"
              : "Low"}{" "}
            ({(data.loaded_language_score * 100).toFixed(0)}%)
          </span>
        </div>
        <ScoreBar
          value={data.loaded_language_score}
          color={
            data.loaded_language_score > 0.6
              ? "bg-red-500"
              : data.loaded_language_score > 0.3
              ? "bg-yellow-500"
              : "bg-green-500"
          }
        />
        {data.loaded_words.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {data.loaded_words.map((word) => (
              <span
                key={word}
                className="px-2 py-0.5 bg-red-950 text-red-300 text-xs rounded border border-red-900"
              >
                {word}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Hedge ratio */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">Attribution / hedging</span>
          <span
            className={`font-semibold ${
              data.hedge_ratio > 0.3
                ? "text-green-400"
                : data.hedge_ratio > 0.1
                ? "text-yellow-400"
                : "text-gray-400"
            }`}
          >
            {(data.hedge_ratio * 100).toFixed(0)}%
          </span>
        </div>
        <ScoreBar
          value={Math.min(data.hedge_ratio * 3, 1)}
          color="bg-blue-500"
        />
        <p className="text-xs text-gray-600 mt-1">
          Phrases like "according to", "reportedly", "allegedly" signal attributed sourcing.
        </p>
      </div>

      {/* Entity sentiments */}
      {sentimentEntries.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            How entities are portrayed
          </h3>
          <div className="space-y-2">
            {sentimentEntries.map(([name, info]) => (
              <div key={name} className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded font-mono shrink-0 ${
                      info.type === "PER"
                        ? "bg-purple-900 text-purple-300"
                        : "bg-orange-900 text-orange-300"
                    }`}
                  >
                    {info.type}
                  </span>
                  <span className="text-sm text-gray-200 truncate">{name}</span>
                </div>
                <span
                  className={`text-xs font-semibold shrink-0 ${
                    info.sentiment === "positive"
                      ? "text-green-400"
                      : info.sentiment === "negative"
                      ? "text-red-400"
                      : "text-gray-400"
                  }`}
                >
                  {info.sentiment} ({(info.score * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-gray-600 pt-1 border-t border-gray-800">
        Article analyzed: {data.sentence_count} sentences
      </div>
    </div>
  );
}
