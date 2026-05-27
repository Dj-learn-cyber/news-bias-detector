"""
Step 3 — Fine-tune DistilBERT for political bias classification.

Hardware target: RTX 5080 16GB GDDR7 (Blackwell, CUDA 12.8)
Base model:     distilbert-base-uncased
Expected time:  ~5 min for 1,800 samples / 8 epochs

Output: trained-model/  (drop-in replacement for the app)
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import torch
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(0.875)  # cap at 14 GB of 16 GB
from datasets import Dataset
from sklearn.metrics import f1_score, accuracy_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_MODEL  = "distilbert-base-uncased"
DATA_DIR    = Path("data")
OUTPUT_DIR  = Path("trained-model")
MAX_LENGTH  = 512
BATCH_SIZE  = 32
GRAD_ACCUM  = 1
EPOCHS      = 8
LR          = 3e-5
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 1.0
# ─────────────────────────────────────────────────────────────────────────────

LABELS   = ["left", "center", "right"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for i, l in enumerate(LABELS)}


def load_split(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def to_hf_dataset(records: list[dict], tokenizer) -> Dataset:
    texts  = [r["text"] for r in records]
    labels = [LABEL2ID[r["label"]] for r in records]

    tok = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LENGTH,
        padding=False,
    )
    tok["labels"] = labels
    return Dataset.from_dict(tok)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy":  round(accuracy_score(labels, preds), 4),
        "f1_macro":  round(f1_score(labels, preds, average="macro"), 4),
        "f1_weighted": round(f1_score(labels, preds, average="weighted"), 4),
    }


def main():
    for path in [DATA_DIR / "train.jsonl", DATA_DIR / "val.jsonl"]:
        if not path.exists():
            print(f"ERROR: {path} not found. Run 2_prepare_dataset.py first.")
            raise SystemExit(1)

    print(f"Base model : {BASE_MODEL}")
    print(f"Device     : {'CUDA — ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (slow!)'}")
    print(f"VRAM       : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB\n" if torch.cuda.is_available() else "")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model     = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABELS),
        label2id=LABEL2ID,
        id2label=ID2LABEL,
        ignore_mismatched_sizes=True,
    )

    train_records = load_split(DATA_DIR / "train.jsonl")
    val_records   = load_split(DATA_DIR / "val.jsonl")
    print(f"Train: {len(train_records)} | Val: {len(val_records)}\n")

    train_ds = to_hf_dataset(train_records, tokenizer)
    val_ds   = to_hf_dataset(val_records,   tokenizer)

    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR / "checkpoints"),
        num_train_epochs=EPOCHS,

        # Batch size + gradient accumulation
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE * 2,
        gradient_accumulation_steps=GRAD_ACCUM,

        # Optimizer
        learning_rate=LR,
        warmup_steps=45,
        weight_decay=WEIGHT_DECAY,
        max_grad_norm=MAX_GRAD_NORM,
        optim="adamw_torch",

        # fp32 — safe and fast enough for DistilBERT
        bf16=False,
        tf32=True,

        # Eval + checkpointing
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=2,

        # Speed (0 workers avoids Windows multiprocessing issues)
        dataloader_num_workers=0,

        report_to="none",
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8),
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("-- Training ------------------------------------------")
    trainer.train()

    print("\n-- Saving model --------------------------------------")
    OUTPUT_DIR.mkdir(exist_ok=True)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print(f"\nModel saved to ./{OUTPUT_DIR}/")
    print("Run 4_evaluate.py next to see full metrics.")


if __name__ == "__main__":
    main()
