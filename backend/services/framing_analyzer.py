import re

try:
    from transformers import pipeline as _hf_pipeline
except ImportError:  # pragma: no cover
    _hf_pipeline = None  # type: ignore[assignment]

_sentiment_pipe = None
_ner_pipe = None


def _get_sentiment_pipe():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = _hf_pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
        )
    return _sentiment_pipe


def _get_ner_pipe():
    global _ner_pipe
    if _ner_pipe is None:
        _ner_pipe = _hf_pipeline(
            "token-classification",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
        )
    return _ner_pipe


# Emotionally charged / loaded language patterns
_LOADED_PATTERNS = [
    r"\b(regime|thug|terrorist|extremist|radical|far-left|far-right)\b",
    r"\b(elites?|globalist|socialist|fascist|communist|marxist)\b",
    r"\b(destroy|devastate|catastrophic|explode|slam|blast|crush|obliterate|decimate)\b",
    r"\b(fake news|hoax|propaganda|lies?|misinformation|disinformation)\b",
    r"\b(outrage|scandal(?:ous)?|disgraceful|shocking|appalling|horrifying)\b",
    r"\b(freedom fighter|patriot|traitor|enemy of the people)\b",
    r"\b(invasion|flood|swarm|horde|mob)\b",
    r"\b(woke|snowflake|libtard|rino|deep state|witch hunt)\b",
    r"\b(crisis|catastrophe|disaster|collapse|meltdown|implosion)\b",
]

# Hedge/qualifier words that may signal balanced framing
_HEDGE_PATTERNS = [
    r"\baccording to\b",
    r"\ballegedly\b",
    r"\bclaimed?\b",
    r"\breported(?:ly)?\b",
    r"\bsaid to be\b",
    r"\bapparently\b",
]


def preload_models() -> None:
    _get_sentiment_pipe()
    _get_ner_pipe()


def analyze_framing(text: str) -> dict:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]

    # Loaded language detection
    all_loaded: list[str] = []
    for pattern in _LOADED_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        all_loaded.extend(m.lower() for m in matches)

    loaded_score = min(len(all_loaded) / max(len(sentences), 1) * 2.5, 1.0)

    # Hedge frequency (signals more balanced reporting)
    hedge_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in _HEDGE_PATTERNS)
    hedge_ratio = round(min(hedge_count / max(len(sentences), 1), 1.0), 3)

    # Opening tone (first 3 sentences — sets narrative frame)
    opening_tone = _classify_tone(" ".join(sentences[:3]))

    # Entity sentiment analysis
    entity_sentiments = _analyze_entity_sentiments(text, sentences)

    return {
        "loaded_language_score": round(loaded_score, 3),
        "loaded_words": sorted(set(all_loaded))[:12],
        "hedge_ratio": hedge_ratio,
        "opening_tone": opening_tone,
        "entity_sentiments": entity_sentiments,
        "sentence_count": len(sentences),
    }


def _classify_tone(text: str) -> str:
    if not text.strip():
        return "neutral"
    try:
        pipe = _get_sentiment_pipe()
        result = pipe(text[:512])[0]
        label = result["label"].upper()
        if label == "POSITIVE":
            return "positive"
        if label == "NEGATIVE":
            return "negative"
        return "neutral"
    except Exception:
        return "neutral"


def _analyze_entity_sentiments(text: str, sentences: list[str]) -> dict:
    results: dict = {}
    try:
        ner_pipe = _get_ner_pipe()
        sample = " ".join(sentences[:20])[:1200]
        entities = ner_pipe(sample)

        sent_pipe = _get_sentiment_pipe()
        seen: set[str] = set()
        for ent in entities:
            if ent["entity_group"] not in ("PER", "ORG"):
                continue
            name = ent["word"].strip()
            if len(name) < 3 or name in seen:
                continue
            seen.add(name)

            context = _entity_context(text, name)
            if not context:
                continue

            sentiment = sent_pipe(context[:512])[0]
            results[name] = {
                "sentiment": sentiment["label"].lower(),
                "score": round(sentiment["score"], 3),
                "type": ent["entity_group"],
            }
            if len(results) >= 8:
                break
    except Exception:
        pass
    return results


def _entity_context(text: str, entity: str, window: int = 200) -> str:
    idx = text.find(entity)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(entity) + window)
    return text[start:end]
