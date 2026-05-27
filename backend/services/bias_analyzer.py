import os
import re
from typing import Optional

_zero_shot_pipe = None
_custom_pipe = None

# Set CUSTOM_BIAS_MODEL in backend/.env to use your fine-tuned model instead
_CUSTOM_MODEL_PATH = os.getenv("CUSTOM_BIAS_MODEL", "").strip()


def _get_custom_pipe():
    global _custom_pipe
    if _custom_pipe is None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        _tok = AutoTokenizer.from_pretrained(_CUSTOM_MODEL_PATH)
        _model = AutoModelForSequenceClassification.from_pretrained(_CUSTOM_MODEL_PATH)
        _model.eval()
        _custom_pipe = (_model, _tok)
    return _custom_pipe


def _get_zero_shot_pipe():
    global _zero_shot_pipe
    if _zero_shot_pipe is None:
        from transformers import pipeline
        _zero_shot_pipe = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
    return _zero_shot_pipe


# Keyword lists derived from AllSides and MBFC research
_LEFT_SIGNALS = [
    "progressive", "social justice", "systemic racism", "climate crisis",
    "universal healthcare", "income inequality", "gun control", "lgbtq rights",
    "reproductive rights", "defund the police", "marginalized communities",
    "intersectional", "white privilege", "living wage", "green new deal",
    "healthcare for all", "immigration reform", "voter suppression",
]

_RIGHT_SIGNALS = [
    "traditional values", "border security", "second amendment", "free market",
    "big government", "illegal aliens", "mainstream media", "deep state",
    "law and order", "religious freedom", "parental rights", "election integrity",
    "woke", "cancel culture", "anti-woke", "constitution", "founding fathers",
    "small government", "energy independence", "pro-life",
]


def preload_models() -> None:
    if _CUSTOM_MODEL_PATH:
        _get_custom_pipe()
    else:
        _get_zero_shot_pipe()


def _five_level_label(scores: dict) -> tuple[str, float]:
    """Map left/center/right probability scores to a 5-level label."""
    left = scores["left"]
    right = scores["right"]
    net = right - left  # negative = leans left, positive = leans right
    top_score = max(scores.values())
    if net <= -0.30:
        label = "left"
    elif net <= -0.08:
        label = "lean-left"
    elif net >= 0.30:
        label = "right"
    elif net >= 0.08:
        label = "lean-right"
    else:
        label = "center"
    return label, round(top_score, 4)


def _analyze_with_custom_model(text: str) -> dict:
    import torch
    model, tok = _get_custom_pipe()
    inputs = tok(text[:1500], return_tensors="pt", truncation=True, max_length=512)
    inputs.pop("token_type_ids", None)  # DistilBERT has no segment embeddings
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0].tolist()
    id2label = model.config.id2label
    scores_raw = {id2label[i]: p for i, p in enumerate(probs)}
    top_label = max(scores_raw, key=scores_raw.get)
    label, confidence = _five_level_label(scores_raw)
    return {
        "label": label,
        "confidence": round(scores_raw[top_label], 4),
        "scores": {k: round(v, 4) for k, v in scores_raw.items()},
    }


def analyze_political_bias(text: str) -> dict:
    try:
        if _CUSTOM_MODEL_PATH:
            return _analyze_with_custom_model(text)

        pipe = _get_zero_shot_pipe()
        sample = text[:1500]
        result = pipe(
            sample,
            candidate_labels=[
                "left-leaning political bias",
                "right-leaning political bias",
                "politically neutral or centrist",
            ],
        )
        label_map = {
            "left-leaning political bias": "left",
            "right-leaning political bias": "right",
            "politically neutral or centrist": "center",
        }
        scores = {label_map[l]: s for l, s in zip(result["labels"], result["scores"])}
        label, confidence = _five_level_label(scores)
        return {"label": label, "confidence": confidence, "scores": scores}
    except Exception:
        return _keyword_bias(text)


def _keyword_bias(text: str) -> dict:
    lower = text.lower()
    left = sum(lower.count(kw) for kw in _LEFT_SIGNALS)
    right = sum(lower.count(kw) for kw in _RIGHT_SIGNALS)
    total = left + right + 1
    net = (right - left) / total

    if net >= 0.25:
        label, conf = "right", min(0.5 + net * 0.5, 0.85)
    elif net >= 0.08:
        label, conf = "lean-right", min(0.45 + net * 0.5, 0.72)
    elif net <= -0.25:
        label, conf = "left", min(0.5 + abs(net) * 0.5, 0.85)
    elif net <= -0.08:
        label, conf = "lean-left", min(0.45 + abs(net) * 0.5, 0.72)
    else:
        label, conf = "center", 0.55

    l_score = left / total
    r_score = right / total
    c_score = max(0.0, 1.0 - l_score - r_score)
    return {
        "label": label,
        "confidence": round(conf, 4),
        "scores": {
            "left": round(l_score, 4),
            "center": round(c_score, 4),
            "right": round(r_score, 4),
        },
        "fallback": True,
    }
