"""
Merge user feedback corrections into the training dataset.

Usage:
    python scripts/merge_feedback.py
    python src/train_model.py
"""

import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "user_feedback.csv")
LOCAL_DATA_PATH = os.path.join(BASE_DIR, "data", "local_sri_lankan_scam_dataset.csv")


def merge_feedback():
    if not os.path.exists(FEEDBACK_PATH):
        print("No feedback file yet. Use the app thumbs-up/down buttons first.")
        return 0

    corrections = []
    with open(FEEDBACK_PATH, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("user_rating") != "wrong":
                continue
            label = (row.get("correct_label") or "").strip().lower()
            message = (row.get("message") or "").strip()
            if label in {"safe", "suspicious", "scam"} and message:
                corrections.append((message, label))

    if not corrections:
        print("No correction feedback to merge (only 'wrong' rows with a label count).")
        return 0

    existing = set()
    if os.path.exists(LOCAL_DATA_PATH):
        with open(LOCAL_DATA_PATH, encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                existing.add(row["message"].strip())

    added = 0
    with open(LOCAL_DATA_PATH, "a", encoding="utf-8", newline="") as handle:
        for message, label in corrections:
            if message in existing:
                continue
            scam_type = "normal" if label == "safe" else f"{label} feedback"
            line = (
                f'"{message.replace(chr(34), chr(39))}",{label},{scam_type},'
                f"Mixed,WhatsApp,user_feedback,User correction from feedback UI\n"
            )
            handle.write(line)
            existing.add(message)
            added += 1

    print(f"Merged {added} new correction(s) into {LOCAL_DATA_PATH}")
    return added


if __name__ == "__main__":
    merge_feedback()
