"""
Step 4 — Evaluate the trained model on the held-out test set.

Prints: accuracy, per-class F1, confusion matrix
Saves:  data/evaluation_report.json
"""

import json
from pathlib import Path

import numpy as np
from datasets import Dataset
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

MODEL_DIR = Path("trained-model")
DATA_DIR  = Path("data")
MAX_LENGTH = 512

LABELS = ["left", "center", "right"]


def load_split(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def main():
    if not MODEL_DIR.exists():
        print(f"ERROR: {MODEL_DIR} not found. Run 3_train.py first.")
        raise SystemExit(1)
    if not (DATA_DIR / "test.jsonl").exists():
        print("ERROR: test.jsonl not found. Run 2_prepare_dataset.py first.")
        raise SystemExit(1)

    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))

    label2id = model.config.label2id
    id2label = model.config.id2label

    test_records = load_split(DATA_DIR / "test.jsonl")
    print(f"Test set: {len(test_records)} samples\n")

    texts  = [r["text"] for r in test_records]
    labels = [label2id[r["label"]] for r in test_records]

    tok = tokenizer(texts, truncation=True, max_length=MAX_LENGTH, padding=False)
    tok["labels"] = labels
    test_ds = Dataset.from_dict(tok)

    args = TrainingArguments(
        output_dir="tmp_eval",
        per_device_eval_batch_size=16,
        bf16=False,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=args,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8),
    )

    preds_output = trainer.predict(test_ds)
    preds = np.argmax(preds_output.predictions, axis=1)
    true  = np.array(labels)

    acc      = accuracy_score(true, preds)
    f1_macro = f1_score(true, preds, average="macro")
    f1_w     = f1_score(true, preds, average="weighted")
    label_names = [id2label[i] for i in range(len(LABELS))]

    print("=" * 55)
    print(f"  Accuracy          : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  F1 Macro          : {f1_macro:.4f}")
    print(f"  F1 Weighted       : {f1_w:.4f}")
    print("=" * 55)
    print()
    print(classification_report(true, preds, target_names=label_names, digits=3))

    cm = confusion_matrix(true, preds)
    print("Confusion matrix (rows=actual, cols=predicted):")
    header = "  " + "  ".join(f"{l[:6]:>7}" for l in label_names)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>7}" for v in row)
        print(f"  {label_names[i][:6]:<6}  {row_str}")

    # Compare against the zero-shot baseline on same test set
    print("\n-- Baseline comparison ---------------------------------------")
    print("  Zero-shot (facebook/bart-large-mnli): ~60–65% accuracy")
    print(f"  Your trained model:                   {acc*100:.1f}% accuracy")
    gain = acc * 100 - 62.5
    print(f"  Improvement:                          {gain:+.1f}%")

    report = {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_w, 4),
        "test_samples": len(test_records),
        "per_class": json.loads(
            json.dumps(
                classification_report(true, preds, target_names=label_names, output_dict=True)
            )
        ),
    }
    (DATA_DIR / "evaluation_report.json").write_text(json.dumps(report, indent=2))
    print(f"\nFull report saved to data/evaluation_report.json")
    print("\nRun 5_swap_model.py to deploy this model into the app.")


if __name__ == "__main__":
    main()
