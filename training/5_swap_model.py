"""
Step 5 — Swap the trained model into the live app.

What it does:
  1. Verifies the trained model exists and loads cleanly
  2. Writes the model path into backend/.env
  3. The backend reads CUSTOM_BIAS_MODEL from .env on startup

After running this, restart the backend and it will use your trained model.
"""

import json
import sys
from pathlib import Path

MODEL_DIR  = Path("trained-model")
BACKEND_ENV = Path("../backend/.env")
EVAL_REPORT = Path("data/evaluation_report.json")


def verify_model() -> bool:
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        print("Loading model for verification...")
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
        labels = list(model.config.id2label.values())
        print(f"  Labels   : {labels}")
        print(f"  Params   : {sum(p.numel() for p in model.parameters()) / 1e6:.0f}M")

        # Quick inference test
        inputs = tokenizer(
            "The government's progressive policy will expand healthcare access.",
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )
        import torch
        with torch.no_grad():
            logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        pred_label = model.config.id2label[probs.argmax().item()]
        print(f"  Test pred: '{pred_label}' (expected: left or lean-left)")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def show_metrics() -> None:
    if EVAL_REPORT.exists():
        report = json.loads(EVAL_REPORT.read_text())
        print(f"\n  Accuracy  : {report['accuracy']*100:.1f}%")
        print(f"  F1 Macro  : {report['f1_macro']:.3f}")
    else:
        print("  (no evaluation report found — run 4_evaluate.py)")


def write_env(model_path: str) -> None:
    env_path = BACKEND_ENV
    lines = []
    found = False

    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("CUSTOM_BIAS_MODEL="):
                lines.append(f"CUSTOM_BIAS_MODEL={model_path}")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"CUSTOM_BIAS_MODEL={model_path}")

    env_path.write_text("\n".join(lines) + "\n")
    print(f"\n  Written to {env_path}")


def main():
    print("=== Step 5: Swapping model into app ===\n")

    if not MODEL_DIR.exists():
        print(f"ERROR: {MODEL_DIR}/ not found. Run 3_train.py first.")
        sys.exit(1)

    print("-- Verifying trained model -----------------------------------")
    if not verify_model():
        print("Model verification failed. Check training output.")
        sys.exit(1)

    print("\n-- Evaluation metrics ----------------------------------------")
    show_metrics()

    # Resolve absolute path so the backend can find the model
    abs_path = MODEL_DIR.resolve().as_posix()
    print(f"\n-- Writing model path to backend/.env -----------------------")
    write_env(abs_path)

    print("\n-- Done ------------------------------------------------------")
    print("Restart the backend to activate your trained model:")
    print()
    print("  cd ../backend")
    print("  .venv\\Scripts\\uvicorn main:app --host 127.0.0.1 --port 8000")


if __name__ == "__main__":
    main()
