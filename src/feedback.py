import csv
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDBACK_PATH = os.path.join(BASE_DIR, "data", "user_feedback.csv")

FEEDBACK_COLUMNS = [
    "timestamp",
    "message",
    "predicted_action",
    "predicted_verdict",
    "user_rating",
    "correct_label",
    "source",
]


def _ensure_feedback_file():
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    if not os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FEEDBACK_COLUMNS)
            writer.writeheader()


def save_feedback(
    message: str,
    predicted_action: str,
    predicted_verdict: str,
    user_rating: str,
    correct_label: str | None = None,
    source: str = "api",
):
    _ensure_feedback_file()

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message.strip(),
        "predicted_action": predicted_action,
        "predicted_verdict": predicted_verdict,
        "user_rating": user_rating,
        "correct_label": correct_label or "",
        "source": source,
    }

    with open(FEEDBACK_PATH, "a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEEDBACK_COLUMNS)
        writer.writerow(row)

    return row
