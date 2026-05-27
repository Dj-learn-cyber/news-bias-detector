import { useState } from "react";

type Mode = "text" | "url";

interface Props {
  onSubmit: (payload: { text?: string; url?: string }) => void;
  loading: boolean;
}

export default function ArticleInput({ onSubmit, loading }: Props) {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "text" && text.trim().length >= 80) {
      onSubmit({ text: text.trim() });
    } else if (mode === "url" && url.trim()) {
      onSubmit({ url: url.trim() });
    }
  }

  const canSubmit =
    !loading &&
    (mode === "text" ? text.trim().length >= 80 : url.trim().length > 0);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Mode tabs */}
      <div className="flex bg-gray-800 rounded-xl p-1 w-fit">
        {(["text", "url"] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`px-5 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === m
                ? "bg-gray-600 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {m === "text" ? "Paste Text" : "Article URL"}
          </button>
        ))}
      </div>

      {mode === "text" ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste the full article text here (minimum 80 characters)..."
          rows={10}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      ) : (
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      )}

      <button
        type="submit"
        disabled={!canSubmit}
        className="w-full py-3 rounded-xl font-semibold text-sm transition-all bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Analyzing...
          </span>
        ) : (
          "Analyze Article"
        )}
      </button>
    </form>
  );
}
