export type PoliticalLabel = "far-left" | "left" | "lean-left" | "center" | "lean-right" | "right" | "far-right";

export interface PoliticalLean {
  label: PoliticalLabel;
  confidence: number;
  scores: { left: number; center: number; right: number };
  fallback?: boolean;
}

export interface SourceCredibility {
  outlet: string | null;
  score: number | null;
  bias_label: string | null;
  factual_reporting: string | null;
  found: boolean;
}

export interface EntitySentiment {
  sentiment: string;
  score: number;
  type: "PER" | "ORG";
}

export interface Framing {
  loaded_language_score: number;
  loaded_words: string[];
  hedge_ratio: number;
  opening_tone: "positive" | "negative" | "neutral";
  entity_sentiments: Record<string, EntitySentiment>;
  sentence_count: number;
}

export interface AnalyzeResponse {
  political_lean: PoliticalLean;
  source_credibility: SourceCredibility;
  framing: Framing;
  summary: string;
  article_title: string | null;
  source_domain: string | null;
  word_count: number;
}
