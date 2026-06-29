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

from src.feedback_merge import LOCAL_DATA_PATH, merge_corrections

FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "user_feedback.csv")


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

    added = merge_corrections(corrections)
    print(f"Merged {added} new correction(s) into {LOCAL_DATA_PATH}")
    return added


if __name__ == "__main__":
    merge_feedback()
