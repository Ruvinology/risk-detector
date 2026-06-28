import joblib
import os
from functools import lru_cache


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "scam_detector_model.pkl")


@lru_cache(maxsize=1)
def load_model():
    """
    Loads the trained model only once and reuses it.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please run: python src/train_model.py"
        )

    return joblib.load(MODEL_PATH)


def predict_message(message):
    model = load_model()

    prediction = model.predict([message])[0]
    probabilities = model.predict_proba([message])[0]

    class_labels = model.classes_
    probability_dict = dict(zip(class_labels, probabilities))

    scam_probability = probability_dict.get("scam", 0)
    suspicious_probability = probability_dict.get("suspicious", 0)

    # Scam contributes 100%, suspicious contributes 60%
    risk_score = round((scam_probability * 100) + (suspicious_probability * 60), 2)

    if risk_score >= 75:
        risk_level = "High Risk"
    elif risk_score >= 45:
        risk_level = "Medium Risk"
    else:
        risk_level = "Low Risk"

    return {
        "prediction": prediction,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "probabilities": probability_dict
    }