import re

from src.predict import predict_message
from src.predict_type import predict_scam_type
from src.explanation import generate_explanation, generate_safety_advice
from src.url_features import analyze_urls_in_message


MAX_MESSAGE_LENGTH = 10_000

WEAK_EXPLANATION_HINTS = (
    "No major scam indicators were detected",
    "Encourages clicking a link",
    "Uses suspicious cold-contact greeting patterns",
)


def calculate_final_risk(message_risk_score, url_results):
    """
    Combines message-based AI risk and URL-based risk.
    Message model = 70%, URL analyzer = 30%.
    Untrusted URLs contribute fully; trusted URLs are ignored in the blend.
    """
    untrusted_scores = [
        item["url_risk_score"]
        for item in url_results
        if not item.get("trusted", False)
    ]

    max_url_risk = max(untrusted_scores) if untrusted_scores else 0

    final_risk_score = round((message_risk_score * 0.7) + (max_url_risk * 0.3), 2)

    if final_risk_score >= 75:
        final_risk_level = "High Risk"
    elif final_risk_score >= 45:
        final_risk_level = "Medium Risk"
    else:
        final_risk_level = "Low Risk"

    return final_risk_score, final_risk_level


def _count_strong_scam_signals(explanation):
    strong = 0
    for item in explanation:
        if any(hint in item for hint in WEAK_EXPLANATION_HINTS):
            continue
        strong += 1
    return strong


def _urls_are_trusted(url_results):
    if not url_results:
        return True
    return all(item.get("trusted", False) for item in url_results)


def _max_untrusted_url_risk(url_results):
    untrusted = [
        item["url_risk_score"]
        for item in url_results
        if not item.get("trusted", False)
    ]
    return max(untrusted) if untrusted else 0


def _is_benign_greeting(message):
    """Short everyday greetings should not be flagged in chat demos."""
    normalized = message.strip().lower()
    greeting_pattern = r"^(hi|hello|hey|hii|heyy|ok|thanks|thank you|good morning|good afternoon|good evening)([!.\s]*)$"
    return bool(re.match(greeting_pattern, normalized))


def resolve_delivery_decision(message_result, url_results, explanation, final_risk_score, message=""):
    """
    Combines ML output, URL trust, and rule signals to reduce false positives
    on legitimate links while keeping obvious scams blocked.
    """
    if _is_benign_greeting(message):
        return "Likely Safe", "allow"

    prediction = message_result["prediction"]
    probs = message_result["probabilities"]
    scam_pct = probs.get("scam", 0)
    safe_pct = probs.get("safe", 0)
    suspicious_pct = probs.get("suspicious", 0)

    strong_signals = _count_strong_scam_signals(explanation)
    trusted_urls = _urls_are_trusted(url_results)
    untrusted_url_risk = _max_untrusted_url_risk(url_results)
    has_risky_urls = bool(url_results) and not trusted_urls

    # URL layer can block even when the text model is uncertain.
    if untrusted_url_risk >= 45:
        return "Scam / High Suspicion", "block"

    if has_risky_urls and untrusted_url_risk >= 30 and (strong_signals >= 1 or scam_pct >= 40):
        return "Scam / High Suspicion", "block"

    if (
        final_risk_score >= 75
        or (prediction == "scam" and scam_pct >= 58 and strong_signals >= 1)
        or (prediction == "scam" and has_risky_urls and untrusted_url_risk >= 25)
        or (strong_signals >= 2 and scam_pct >= 45)
    ):
        return "Scam / High Suspicion", "block"

    if prediction == "scam":
        if has_risky_urls and untrusted_url_risk >= 25:
            return "Scam / High Suspicion", "block"
        # Without rule or URL evidence, require higher ML confidence to block.
        if strong_signals == 0 and not has_risky_urls and scam_pct < 58:
            return "Likely Safe", "allow"
        if strong_signals <= 1 and not has_risky_urls and scam_pct < 58:
            return "Likely Safe", "allow"
        return "Scam / High Suspicion", "block"

    if prediction == "suspicious":
        if any("cold-contact" in item for item in explanation):
            return "Suspicious", "warn"
        if strong_signals == 0 and safe_pct >= 25 and not has_risky_urls:
            return "Likely Safe", "allow"
        if suspicious_pct >= 70 and strong_signals >= 1:
            return "Suspicious", "warn"
        if strong_signals == 0 and not has_risky_urls:
            return "Likely Safe", "allow"
        return "Suspicious", "warn"

    if final_risk_score >= 45 and strong_signals >= 1:
        return "Suspicious", "warn"

    return "Likely Safe", "allow"


def _format_probabilities(probability_dict):
    return {
        label: round(float(probability * 100), 2)
        for label, probability in probability_dict.items()
    }


def warm_models():
    """Load both ML models once at startup to avoid first-request latency."""
    predict_message("warmup")
    predict_scam_type("warmup")


def analyze_message(message: str) -> dict:
    """
    Full analysis pipeline used by both the API and Streamlit demo.
    """
    text = message.strip()

    if not text:
        raise ValueError("Message cannot be empty.")

    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters."
        )

    message_result = predict_message(text)
    type_result = predict_scam_type(text)
    explanation = generate_explanation(text)
    url_results = analyze_urls_in_message(text)

    final_risk_score, final_risk_level = calculate_final_risk(
        message_result["risk_score"],
        url_results,
    )

    verdict, delivery_action = resolve_delivery_decision(
        {
            "prediction": message_result["prediction"],
            "probabilities": _format_probabilities(message_result["probabilities"]),
        },
        url_results,
        explanation,
        final_risk_score,
        text,
    )

    if delivery_action == "block":
        final_risk_level = "High Risk"
    elif delivery_action == "warn":
        final_risk_level = "Medium Risk"
    else:
        final_risk_level = "Low Risk"

    advice = generate_safety_advice(
        "scam" if delivery_action == "block" else (
            "suspicious" if delivery_action == "warn" else "safe"
        ),
        "High Risk" if delivery_action == "block" else (
            "Medium Risk" if delivery_action == "warn" else "Low Risk"
        ),
    )

    return {
        "verdict": verdict,
        "delivery_action": delivery_action,
        "final_risk_score": final_risk_score,
        "final_risk_level": final_risk_level,
        "message_analysis": {
            "prediction": message_result["prediction"],
            "risk_score": message_result["risk_score"],
            "risk_level": message_result["risk_level"],
            "probabilities": _format_probabilities(message_result["probabilities"]),
        },
        "scam_type": {
            "scam_type": type_result["scam_type"],
            "confidence": type_result["confidence"],
            "probabilities": _format_probabilities(type_result["probabilities"]),
        },
        "explanation": explanation,
        "url_analysis": url_results,
        "safety_advice": advice,
        "meta": {
            "models": "locally trained (TF-IDF + Logistic Regression)",
            "external_ai_apis": False,
        },
    }
