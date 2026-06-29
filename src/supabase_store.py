import logging
import os
from functools import lru_cache

logger = logging.getLogger("scamshield.supabase")

VALID_LABELS = {"safe", "suspicious", "scam"}


def is_supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and get_supabase_key())


def get_supabase_key() -> str | None:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )


@lru_cache(maxsize=1)
def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = get_supabase_key()
    if not url or not key:
        raise RuntimeError("Supabase is not configured.")

    from supabase import create_client

    return create_client(url, key)


def insert_feedback(row: dict) -> dict:
    client = get_supabase_client()
    payload = {
        "message": row["message"],
        "predicted_action": row["predicted_action"],
        "predicted_verdict": row["predicted_verdict"],
        "user_rating": row["user_rating"],
        "correct_label": row.get("correct_label") or None,
        "source": row.get("source", "api"),
        "merged": False,
    }
    response = client.table("feedback").insert(payload).execute()
    if not response.data:
        raise RuntimeError("Supabase insert returned no data.")
    return response.data[0]


def fetch_unmerged_corrections():
    client = get_supabase_client()
    response = (
        client.table("feedback")
        .select("id, message, correct_label")
        .eq("merged", False)
        .eq("user_rating", "wrong")
        .execute()
    )

    rows = response.data or []
    corrections = []
    valid_rows = []

    for row in rows:
        label = (row.get("correct_label") or "").strip().lower()
        message = (row.get("message") or "").strip()
        if label in VALID_LABELS and message:
            corrections.append((message, label))
            valid_rows.append(row)

    return corrections, valid_rows


def mark_feedback_merged(row_ids: list[str]) -> int:
    if not row_ids:
        return 0

    client = get_supabase_client()
    updated = 0

    chunk_size = 100
    for index in range(0, len(row_ids), chunk_size):
        chunk = row_ids[index : index + chunk_size]
        response = (
            client.table("feedback")
            .update({"merged": True})
            .in_("id", chunk)
            .execute()
        )
        updated += len(response.data or [])

    return updated


def save_feedback_to_supabase(row: dict) -> dict:
    try:
        saved = insert_feedback(row)
        logger.info("Feedback saved to Supabase (id=%s).", saved.get("id"))
        return saved
    except Exception as exc:
        logger.exception("Supabase feedback save failed: %s", exc)
        raise
