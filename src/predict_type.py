import joblib
import os
from functools import lru_cache


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPE_MODEL_PATH = os.path.join(BASE_DIR, "models", "scam_type_model.pkl")


@lru_cache(maxsize=1)
def load_type_model():
    if not os.path.exists(TYPE_MODEL_PATH):
        raise FileNotFoundError(
            f"Scam type model not found at {TYPE_MODEL_PATH}. "
            "Please run: python src/train_type_model.py"
        )

    return joblib.load(TYPE_MODEL_PATH)


def predict_scam_type(message):
    model = load_type_model()

    scam_type = model.predict([message])[0]
    probabilities = model.predict_proba([message])[0]

    class_labels = model.classes_
    probability_dict = dict(zip(class_labels, probabilities))

    confidence = round(max(probabilities) * 100, 2)

    return {
        "scam_type": scam_type,
        "confidence": confidence,
        "probabilities": probability_dict
    }