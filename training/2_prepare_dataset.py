"""
Step 2 — Clean, balance, and split the raw collected articles.

Input:  data/raw_articles.jsonl
Output: data/train.jsonl, data/val.jsonl, data/test.jsonl
        data/label_counts.json  (class distribution report)

Strategy:
  - Merge far-left → left and far-right → right (too few far-* samples)
  - Target 3,000 samples per class via undersampling majority classes
  - Split 75% train / 12.5% val / 12.5% test, stratified
"""

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

INPUT  = Path("data/raw_articles.jsonl")
OUTDIR = Path("data")

LABEL_MERGE = {
    "far-left":  "left",
    "left":      "left",
    "lean-left": "left",
    "center":    "center",
    "lean-right":"right",
    "right":     "right",
    "far-right": "right",
}

FINAL_LABELS = ["left", "center", "right"]
TARGET_PER_CLASS = 800   # max samples per class (undersampling)
MIN_WORDS = 15
MAX_WORDS = 600            # truncate very long articles at word level


def load_raw() -> list[dict]:
    records = []
    seen_texts: set[str] = set()

    with open(INPUT, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            label = LABEL_MERGE.get(obj.get("label", ""))
            if label not in FINAL_LABELS:
                continue

            words = obj["text"].split()
            if len(words) < MIN_WORDS:
                continue

            # Truncate and deduplicate on first 120 chars
            text = " ".join(words[:MAX_WORDS])
            key = text[:120].lower()
            if key in seen_texts:
                continue
            seen_texts.add(key)

            records.append({
                "text": text,
                "label": label,
                "source": obj.get("source", ""),
            })

    return records


def balance(records: list[dict]) -> list[dict]:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_label[r["label"]].append(r)

    print("\n-- Before balancing --")
    for lbl in FINAL_LABELS:
        print(f"  {lbl:<12} {len(by_label[lbl]):>5}")

    balanced = []
    for lbl in FINAL_LABELS:
        items = by_label[lbl]
        random.shuffle(items)
        balanced.extend(items[:TARGET_PER_CLASS])

    random.shuffle(balanced)

    print("\n-- After balancing --")
    after: dict[str, int] = defaultdict(int)
    for r in balanced:
        after[r["label"]] += 1
    for lbl in FINAL_LABELS:
        print(f"  {lbl:<12} {after[lbl]:>5}")

    return balanced


def split(records: list[dict]) -> tuple[list, list, list]:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_label[r["label"]].append(r)

    train, val, test = [], [], []
    for items in by_label.values():
        random.shuffle(items)
        n = len(items)
        n_test = max(1, int(n * 0.125))
        n_val  = max(1, int(n * 0.125))
        test  += items[:n_test]
        val   += items[n_test:n_test + n_val]
        train += items[n_test + n_val:]

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    return train, val, test


def save(records: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print("=== Step 2: Preparing dataset ===\n")

    if not INPUT.exists():
        print(f"ERROR: {INPUT} not found. Run 1_collect_data.py first.")
        raise SystemExit(1)

    records = load_raw()
    print(f"Loaded {len(records)} usable articles")

    records = balance(records)
    train, val, test = split(records)

    save(train, OUTDIR / "train.jsonl")
    save(val,   OUTDIR / "val.jsonl")
    save(test,  OUTDIR / "test.jsonl")

    counts = {"train": len(train), "val": len(val), "test": len(test)}
    (OUTDIR / "label_counts.json").write_text(json.dumps(counts, indent=2))

    print(f"\n-- Splits --")
    print(f"  Train : {len(train)}")
    print(f"  Val   : {len(val)}")
    print(f"  Test  : {len(test)}")
    print(f"\nSaved to {OUTDIR}/")
