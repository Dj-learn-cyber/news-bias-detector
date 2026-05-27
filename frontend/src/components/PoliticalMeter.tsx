import type { PoliticalLean } from "../types";

const LABEL_DISPLAY: Record<string, string> = {
  "far-left": "Far Left",
  left: "Left",
  "lean-left": "Lean Left",
  center: "Center",
  "lean-right": "Lean Right",
  right: "Right",
  "far-right": "Far Right",
};

const LABEL_COLOR: Record<string, string> = {
  "far-left": "text-blue-300",
  left: "text-blue-400",
  "lean-left": "text-blue-300",
  center: "text-gray-300",
  "lean-right": "text-red-300",
  right: "text-red-400",
  "far-right": "text-red-300",
};

// Position on a 0-100 spectrum (left=0, center=50, right=100)
function leanPosition(lean: PoliticalLean): number {
  const { scores } = lean;
  // Weighted position: left=0, center=50, right=100
  return Math.round(scores.left * 0 + scores.center * 50 + scores.right * 100);
}

interface Props {
  data: PoliticalLean;
}

export default function PoliticalMeter({ data }: Props) {
  const pos = leanPosition(data);
  const displayLabel = LABEL_DISPLAY[data.label] ?? data.label;
  const labelColor = LABEL_COLOR[data.label] ?? "text-gray-300";

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
        Political Lean
      </h2>

      <div className="flex items-center justify-between mb-3">
        <span className={`text-2xl font-bold ${labelColor}`}>{displayLabel}</span>
        <span className="text-sm text-gray-500">
          {(data.confidence * 100).toFixed(0)}% confidence
          {data.fallback && (
            <span className="ml-2 text-xs text-yellow-500">(keyword analysis)</span>
          )}
        </span>
      </div>

      {/* Gradient spectrum bar */}
      <div className="relative h-4 rounded-full overflow-hidden mb-2"
        style={{
          background:
            "linear-gradient(to right, #1d4ed8, #3b82f6, #93c5fd, #6b7280, #fca5a5, #ef4444, #b91c1c)",
        }}
      >
        {/* Indicator */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-white rounded-full shadow-lg transition-all duration-700"
          style={{ left: `calc(${pos}% - 2px)` }}
        />
      </div>

      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>Left</span>
        <span>Center</span>
        <span>Right</span>
      </div>

      {/* Score breakdown */}
      <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-blue-400 font-semibold">
            {(data.scores.left * 100).toFixed(0)}%
          </div>
          <div className="text-gray-500 text-xs">Left</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-gray-300 font-semibold">
            {(data.scores.center * 100).toFixed(0)}%
          </div>
          <div className="text-gray-500 text-xs">Center</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-2">
          <div className="text-red-400 font-semibold">
            {(data.scores.right * 100).toFixed(0)}%
          </div>
          <div className="text-gray-500 text-xs">Right</div>
        </div>
      </div>
    </div>
  );
}
