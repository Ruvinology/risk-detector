"""
Fetch unmerged Supabase corrections, retrain when threshold is met,
and mark processed rows as merged.

Usage:
    python scripts/retrain_from_supabase.py

Environment:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY   (required for read + mark merged)
    RETRAIN_MIN_CORRECTIONS     (default: 10)
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.feedback_merge import LOCAL_DATA_PATH, merge_corrections
from src.supabase_store import (
    fetch_unmerged_corrections,
    is_supabase_configured,
    mark_feedback_merged,
)

DEFAULT_MIN_CORRECTIONS = 10


def _min_corrections() -> int:
    raw = os.getenv("RETRAIN_MIN_CORRECTIONS", str(DEFAULT_MIN_CORRECTIONS))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_MIN_CORRECTIONS


def _run_training():
    subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "src", "train_model.py")],
        check=True,
    )
    subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "src", "train_type_model.py")],
        check=True,
    )


def _missing_supabase_env() -> list[str]:
    missing = []
    if not os.getenv("SUPABASE_URL"):
        missing.append("SUPABASE_URL")
    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    return missing


def main() -> int:
    missing = _missing_supabase_env()
    if missing:
        print("Supabase is not configured. Missing:", ", ".join(missing))
        print(
            "For GitHub Actions: Settings → Secrets and variables → Actions → "
            "add repository secrets SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
        return 1

    if not is_supabase_configured():
        print("Supabase is not configured. Set SUPABASE_URL and a Supabase API key.")
        return 1

    min_corrections = _min_corrections()
    corrections, rows = fetch_unmerged_corrections()
    pending_count = len(corrections)

    print(f"Unmerged corrections ready for training: {pending_count}")
    print(f"Retrain threshold: {min_corrections}")

    if pending_count < min_corrections:
        print("Below threshold — skipping retrain.")
        return 0

    added = merge_corrections(corrections)
    print(f"Merged {added} new correction(s) into {LOCAL_DATA_PATH}")

    print("Training scam detector model...")
    _run_training()

    row_ids = [row["id"] for row in rows if row.get("id")]
    marked = mark_feedback_merged(row_ids)
    print(f"Marked {marked} feedback row(s) as merged in Supabase.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
