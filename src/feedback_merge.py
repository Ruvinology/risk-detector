import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DATA_PATH = os.path.join(BASE_DIR, "data", "local_sri_lankan_scam_dataset.csv")


def merge_corrections(corrections: list[tuple[str, str]]) -> int:
    if not corrections:
        return 0

    existing = set()
    if os.path.exists(LOCAL_DATA_PATH):
        import csv

        with open(LOCAL_DATA_PATH, encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                message = (row.get("message") or "").strip()
                if message:
                    existing.add(message)

    added = 0
    with open(LOCAL_DATA_PATH, "a", encoding="utf-8", newline="") as handle:
        for message, label in corrections:
            if message in existing:
                continue
            if label == "safe":
                scam_type = "normal"
            elif label == "suspicious":
                scam_type = "cold contact scam"
            else:
                scam_type = "other"
            line = (
                f'"{message.replace(chr(34), chr(39))}",{label},{scam_type},'
                f"Mixed,WhatsApp,user_feedback,User correction from feedback UI\n"
            )
            handle.write(line)
            existing.add(message)
            added += 1

    return added
